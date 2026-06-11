"""蒙多核心引擎 v2.0.9 — Agentic Loop

v2.0.9 优化（学习 Hermes/Claude 精华）：
- 懒加载模块，减少启动时间
- 缓存系统提示词和工具 schema
- 并行执行独立工具调用
- 智能消息压缩
- 快速响应检测
"""

import sys
import json
import time
import signal
from typing import List, Dict, Optional, Callable, Tuple
from llm import LLMClient, repair_json, _is_timeout_error
from constants import (
    VERSION, CHAR_TO_TOKEN,
    CONTEXT_MAX_TOKENS, CONTEXT_COMPRESS_THRESHOLD, CONTEXT_KEEP_RECENT,
    BUDGET_MAX_PROMPT, BUDGET_MAX_COMPLETION, BUDGET_WARN_THRESHOLD,
    STUCK_THRESHOLD, IDLE_TIMEOUT, MAX_RETRY, RETRY_DELAY,
    MAX_ITERATIONS, TOOL_MAX_OUTPUT, STREAM_MAX_WAIT,
)
from policy import get_policy_engine, PolicyContext, Action
from events import get_event_bus, EventType, Priority
from timeline import get_timeline, EntryType
from context_mapper import ContextMapper, ContextBudget, ChunkType
from cache import get_cache_manager
from sandbox import get_sandbox
from runtime_config import get_config
from model_adapter import get_model_adapter, DeepSeekOptimizer
from quark_optimizer import ModelOptimizerFactory
from model_profiles import SmartModelSelector, AutoAdapter, TaskType, PROVIDER_DATABASE
from task_planner import TaskPlanner, MultiModelCoordinator, LATEST_MODELS, MODEL_RATINGS
from tool_guard import ToolGuardController, GuardAction
from dispatch import ToolCall as DispatchToolCall, dispatch
from prompt_assembler import build_system_prompt
from performance_optimizer import (
    get_cache, can_parallelize, execute_tools_parallel,
    MessageCompressor, is_simple_query, get_fast_response_config,
)


# ═══════════════════════════════════════════════
# System Prompt — 精简版，省 token
# ═══════════════════════════════════════════════

# System prompt 现在由 prompt_assembler.py 模块化组装
MUNDO_SYSTEM_PROMPT = None  # 已迁移到 prompt_assembler.build_system_prompt()


# ═══════════════════════════════════════════════
# 错误分类
# ═══════════════════════════════════════════════

def _classify_error(error: Exception, raw_msg: str) -> Dict:
    msg = raw_msg.lower()
    result = {"category": "unknown", "retryable": False, "user_tip": "", "log_detail": raw_msg}

    # 连接重置
    if isinstance(error, (ConnectionResetError, ConnectionRefusedError, BrokenPipeError)):
        result.update(category="connection", retryable=True, user_tip="连接被中断，正在重试…")
        return result
    if any(kw in msg for kw in ["reset", "broken pipe", "eof", "远程主机"]):
        result.update(category="connection", retryable=True, user_tip="连接被中断，正在重试…")
        return result

    # DNS/网络
    if "dns" in msg or "connection refused" in msg:
        result.update(category="network", retryable=True, user_tip="无法连接到模型服务。请检查网络。")
        return result

    # 超时
    if _is_timeout_error(error) or "timeout" in msg or "超时" in raw_msg:
        result.update(category="timeout", retryable=True, user_tip="请求超时。模型可能繁忙，正在重试…")
        return result

    # API key
    if any(kw in msg for kw in ["401", "unauthorized", "invalid api key", "api key"]):
        result.update(category="auth", user_tip="API key 无效或已过期。运行 /setup 更新。")
        return result

    # 限速
    if any(kw in msg for kw in ["429", "rate limit", "too many"]):
        result.update(category="rate_limit", retryable=True, user_tip="请求过于频繁，稍后重试…")
        return result

    # 服务器错误
    if any(kw in msg for kw in ["500", "502", "503", "504", "internal server"]):
        result.update(category="server", retryable=True, user_tip="模型服务暂时不可用，正在重试…")
        return result

    return result


# ═══════════════════════════════════════════════
# 预算和统计
# ═══════════════════════════════════════════════

class IterationBudget:
    def __init__(self, max_prompt_tokens=BUDGET_MAX_PROMPT,
                 max_completion_tokens=BUDGET_MAX_COMPLETION,
                 max_turns=0, warn_threshold=BUDGET_WARN_THRESHOLD):
        self.max_prompt_tokens = max_prompt_tokens
        self.max_completion_tokens = max_completion_tokens
        self.max_turns = max_turns
        self.warn_threshold = warn_threshold
        self.prompt_tokens_used = 0
        self.completion_tokens_used = 0
        self.turns_used = 0
        self._warned = False

    @property
    def remaining(self):
        return max(0, self.max_prompt_tokens - self.prompt_tokens_used)

    @property
    def usage_ratio(self):
        return self.prompt_tokens_used / self.max_prompt_tokens if self.max_prompt_tokens else 0

    @property
    def should_warn(self):
        return self.usage_ratio >= self.warn_threshold and not self._warned

    @property
    def exhausted(self):
        if self.prompt_tokens_used >= self.max_prompt_tokens:
            return True
        if self.completion_tokens_used >= self.max_completion_tokens:
            return True
        if self.max_turns > 0 and self.turns_used >= self.max_turns:
            return True
        return False

    def update(self, prompt_tokens=0, completion_tokens=0):
        self.prompt_tokens_used += prompt_tokens
        self.completion_tokens_used += completion_tokens
        self.turns_used += 1

    def mark_warned(self):
        self._warned = True

    def reset(self):
        self.prompt_tokens_used = 0
        self.completion_tokens_used = 0
        self.turns_used = 0
        self._warned = False


class TaskStats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start_time = time.time()
        self.turns = 0
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.tool_calls_count = 0
        self.llm_time = 0.0
        self.tool_time = 0.0
        self.errors_count = 0
        self.retries_count = 0

    @property
    def elapsed(self):
        return time.time() - self.start_time

    @property
    def elapsed_str(self):
        s = self.elapsed
        if s < 60:
            return f"{s:.1f}s"
        m = int(s // 60)
        return f"{m}m{s - m*60:.0f}s"


# ═══════════════════════════════════════════════
# 引擎
# ═══════════════════════════════════════════════

class MundoEngine:
    # 从 constants.py 读取，不再硬编码

    def __init__(self, provider="deepseek", model=None):
        # 智能模型选择：根据provider自动选择最优模型
        if model is None:
            model = SmartModelSelector.select_model(provider, TaskType.GENERAL)
        
        self.client = LLMClient(provider=provider, model=model)
        self.provider = provider
        self.model_name = model or self.client.model
        
        # 模型适配器 — 根据模型特性自动优化
        self.adapter = get_model_adapter(self.model_name)
        
        # 自动适配器
        self.auto_adapter = AutoAdapter()
        
        self.messages: List[Dict] = []
        self.max_tokens_override = self.adapter.profile.max_tokens_default
        self.stats = TaskStats()
        self.budget = IterationBudget()
        self._use_streaming = self.adapter.profile.supports_streaming
        self._interrupted = False
        self._consecutive_errors = 0
        self._last_error_tool = ""
        self._same_error_streak = 0
        self._last_activity_time = time.time()

        # 基础设施
        self.policy = get_policy_engine()
        self.events = get_event_bus()
        self.timeline = get_timeline()
        self.cache = get_cache_manager()
        self.sandbox = get_sandbox()
        self.config = get_config()

        # 工具循环防护（从 Hermes Agent 提炼）
        self.tool_guard = ToolGuardController()
        
        # 上下文映射器
        self._context = ContextMapper(ContextBudget(max_tokens=CONTEXT_MAX_TOKENS))

        # 回调
        self.on_turn_start = None
        self.on_tool_call = None
        self.on_tool_output = None
        self.on_turn_end = None
        self.on_task_done = None
        self.on_stream_text = None
        self.on_stream_start = None
        self.on_stream_end = None
        self.on_budget_warn = None
        self.on_compress = None
        self.on_llm_stats = None

    def _build_system_message(self):
        """构建 system message — 模块化组装 + 缓存优化"""
        cache = get_cache()
        content = cache.get_system_prompt(
            self.provider, self.model_name,
            lambda: build_system_prompt(
                model_adapter=self.adapter,
                quark_optimizer=True,
                provider=self.provider,
                model_name=self.model_name,
            )
        )
        return {"role": "system", "content": content}

    def _model_display(self):
        return f"{self.provider}/{self.model_name}"
    
    def switch_model_for_task(self, task_description: str):
        """根据任务描述智能切换模型"""
        task_type = SmartModelSelector.detect_task_type(task_description)
        optimal_model = SmartModelSelector.select_model(self.provider, task_type)
        
        if optimal_model and optimal_model != self.model_name:
            self.model_name = optimal_model
            self.adapter = get_model_adapter(optimal_model)
            self.max_tokens_override = self.adapter.profile.max_tokens_default
            return True
        return False
    
    def generate_task_plan(self, task_description: str) -> str:
        """生成任务执行计划文档"""
        plan = TaskPlanner.generate_plan(task_description, self.provider)
        return TaskPlanner.format_plan_document(plan)
    
    def get_optimal_model_for_step(self, step_info: Dict) -> Tuple[str, str]:
        """为执行步骤获取最优模型"""
        return MultiModelCoordinator.select_best_model(
            step_info.get("task_type", "general"),
            [self.provider],
        )

    def _auto_compress(self):
        if not self._context.should_compress():
            return
        old_tokens = self._context.total_tokens
        new_tokens = self._context.compress()[1]
        if self.on_compress:
            self.on_compress(len(self._context._chunks), len(self._context._chunks), old_tokens, new_tokens)

    def _detect_reasoning_effort(self) -> Optional[str]:
        """根据阶段自动选择推理深度

        策略：首轮 low 快速理解任务，执行阶段默认深度保质量
        """
        if not self.adapter.profile.supports_reasoning:
            return None

        # 首轮（还没执行过工具）→ low 快速理解
        if self.stats.tool_calls_count == 0:
            return "low"

        # 已开始执行工具 → 默认深度保证执行质量
        return None

    def _accumulate_stream(self, stream_iter) -> Dict:
        content_parts = []
        tool_calls_map = {}
        usage = {}
        last_activity = time.time()

        for chunk in stream_iter:
            if time.time() - last_activity > STREAM_MAX_WAIT:
                raise RuntimeError(f"流式累积超时（{STREAM_MAX_WAIT}s）")
            last_activity = time.time()

            delta = LLMClient.extract_stream_delta(chunk)

            if delta["content"]:
                content_parts.append(delta["content"])
                if self.on_stream_text:
                    self.on_stream_text(delta["content"])

            for tc_delta in delta["tool_calls"]:
                idx = tc_delta.get("index", 0)
                if idx not in tool_calls_map:
                    tool_calls_map[idx] = {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
                tc = tool_calls_map[idx]
                if tc_delta.get("id"):
                    tc["id"] = tc_delta["id"]
                fn = tc_delta.get("function", {})
                if fn.get("name"):
                    tc["function"]["name"] = fn["name"]
                if fn.get("arguments"):
                    tc["function"]["arguments"] += fn["arguments"]

            if "usage" in chunk and chunk["usage"]:
                usage = chunk["usage"]

        msg = {"role": "assistant", "content": "".join(content_parts)}
        if tool_calls_map:
            msg["tool_calls"] = [tool_calls_map[i] for i in sorted(tool_calls_map)]
        if usage:
            msg["_usage"] = usage
        return msg

    def _call_llm(self) -> Optional[Dict]:
        for attempt in range(MAX_RETRY):
            try:
                result = self._try_call_llm(attempt)
                if result:
                    self._consecutive_errors = 0
                    return result
            except KeyboardInterrupt:
                self._interrupted = True
                return None
            except Exception as e:
                self._handle_llm_error(e, attempt)
                if self._interrupted:
                    return None
        return None

    def _try_call_llm(self, attempt: int) -> Optional[Dict]:
        messages = self._prepare_messages()
        max_tokens = self.max_tokens_override
        
        # 获取工具 schema
        import tools as tool_module
        tool_schemas = tool_module.registry.schemas if hasattr(tool_module, 'registry') else []

        # 推理预算：简单任务用 low 减少推理 token
        effort = self._detect_reasoning_effort()

        if self._use_streaming:
            try:
                # 夸克级工具 schema 优化
                quark_schemas = ModelOptimizerFactory.optimize_tools(self.provider, tool_schemas)
                optimized_schemas = self.adapter.optimize_tool_schemas(quark_schemas)
                stream = self.client.chat_stream(messages, tools=optimized_schemas,
                                                  max_tokens=max_tokens, reasoning_effort=effort)
                if self.on_stream_start:
                    self.on_stream_start(self.stats.turns)
                result = self._accumulate_stream(stream)
                if self.on_stream_end:
                    self.on_stream_end(self.stats.turns)
                return result
            except Exception as e:
                if attempt == 0:
                    self._use_streaming = False
                    self.stats.retries_count += 1
                    return self._try_call_llm(attempt)
                raise
        else:
            return self.client.chat(messages, tools=tool_schemas,
                                    max_tokens=max_tokens, reasoning_effort=effort)

    def _prepare_messages(self) -> List[Dict]:
        messages = [m for m in self.messages if m.get("role") == "system" or m.get("content")]
        if self.budget.remaining < 10000:
            messages = messages[:1] + messages[-CONTEXT_KEEP_RECENT:]
        return messages

    def _handle_llm_error(self, error: Exception, attempt: int):
        self._consecutive_errors += 1
        self.stats.errors_count += 1
        classified = _classify_error(error, str(error))

        if self.on_tool_output:
            self.on_tool_output("llm", classified.get("user_tip", str(error)), True)

        if classified.get("retryable") and attempt < MAX_RETRY - 1:
            delay = RETRY_DELAY * (2 ** attempt)
            time.sleep(delay)
            self.stats.retries_count += 1
        else:
            self._interrupted = True

    def _update_token_stats(self, msg: Dict):
        usage = msg.get("_usage", {})
        prompt_tok = usage.get("prompt_tokens", 0)
        completion_tok = usage.get("completion_tokens", 0)
        cached = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)

        self.stats.prompt_tokens = prompt_tok
        self.stats.completion_tokens = completion_tok
        self.stats.total_tokens += prompt_tok + completion_tok
        self.budget.update(prompt_tok, completion_tok)

        if self.on_llm_stats:
            self.on_llm_stats(prompt_tok, completion_tok, cached, len(self.messages))

    def _filter_tool_calls(self, tool_calls: list) -> list:
        return [tc for tc in tool_calls if tc.get("function", {}).get("name")]

    def _execute_tool_calls(self, tool_calls: list):
        import tools as tool_module
        # 解析工具调用为 DispatchToolCall 格式
        calls = []
        for tc in tool_calls:
            if self._interrupted:
                break
            fn = tc.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            calls.append((tc, name, args))

        # 智能分发：并行或串行
        dispatch_calls = [
            DispatchToolCall(id=tc.get("id", ""), name=name, args=args)
            for tc, name, args in calls
        ]

        def _executor(name: str, args: dict) -> str:
            return tool_module.execute_tool(name, args)

        # 检查是否可以并行（多个工具调用时）
        if len(dispatch_calls) > 1:
            results = dispatch(dispatch_calls, _executor)
            for (tc, name, args), result in zip(calls, results):
                self._handle_tool_result(tc, name, args, result.output, result.is_error, result.elapsed)
        else:
            for tc, name, args in calls:
                if self._interrupted:
                    break
                self._execute_single_tool(tc, name, args, tool_module)

    def _execute_single_tool(self, tc, name: str, args: dict, tool_module):
        """执行单个工具调用（带策略检查+循环防护+超时保护）"""
        # 策略检查
        policy_result = self.policy.evaluate_tool(name, args)
        if policy_result.is_denied:
            self.messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": f"[策略拒绝] {policy_result.reason}"})
            return

        if self.on_tool_call:
            self.on_tool_call(name, args, self.stats)

        tool_start = time.time()
        TOOL_TIMEOUT = 30  # 单个工具超时：30秒

        try:
            # 使用线程池执行工具，添加超时保护
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool_module.execute_tool, name, args)
                try:
                    output = future.result(timeout=TOOL_TIMEOUT)
                except FutureTimeout:
                    output = f"[工具 {name} 执行超时（{TOOL_TIMEOUT}s）]"
                    future.cancel()

            duration = (time.time() - tool_start) * 1000

            # 工具循环防护检查
            guard_decision = self.tool_guard.observe(name, args, str(output), is_error=False)
            if guard_decision.action == GuardAction.HALT:
                self._interrupted = True
                self.messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": guard_decision.message})
                return
            if guard_decision.action in (GuardAction.WARN, GuardAction.BLOCK):
                if self.on_tool_output:
                    self.on_tool_output("guard", guard_decision.message, True)

            self._handle_tool_result(tc, name, args, str(output), False, duration)

        except Exception as e:
            duration = (time.time() - tool_start) * 1000
            # 工具循环防护检查（错误时）
            guard_decision = self.tool_guard.observe(name, args, str(e), is_error=True)
            if guard_decision.action == GuardAction.HALT:
                self._interrupted = True

            self._handle_tool_error(tc, name, args, e, duration)

    def _handle_tool_result(self, tc, name: str, args: dict, output: str, is_error: bool, duration: float):
        """统一处理工具结果"""
        if is_error:
            self._handle_tool_error(tc, name, args, Exception(output), duration)
            return

        self.stats.tool_calls_count += 1
        self.stats.tool_time += duration / 1000
        self._consecutive_errors = 0
        self._same_error_streak = 0

        self.messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": str(output)[:TOOL_MAX_OUTPUT]})
        if self.on_tool_output:
            self.on_tool_output(name, str(output)[:500], False)

        self.timeline.record_tool(name, args, str(output)[:1000], duration)
        self.events.publish(EventType.TOOL_RESULT, {"tool": name, "duration_ms": duration}, "engine")

    def _handle_tool_error(self, tc, name: str, args: dict, error: Exception, duration: float):
        """统一处理工具错误"""
        self._consecutive_errors += 1
        self.stats.errors_count += 1
        if name == self._last_error_tool:
            self._same_error_streak += 1
        else:
            self._same_error_streak = 1
            self._last_error_tool = name

        error_msg = f"[工具错误] {name}: {error}"
        self.messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": error_msg})
        if self.on_tool_output:
            self.on_tool_output(name, str(error), True)

        self.timeline.record_error(str(error), name)
        self.events.publish(EventType.TOOL_ERROR, {"tool": name, "error": str(error)}, "engine")

    def run(self, user_input: str, extra_context: str = "") -> str:
        self.stats.reset()
        self.budget.reset()
        self.tool_guard.reset()
        self._interrupted = False
        self._use_streaming = self.adapter.profile.supports_streaming
        self._install_signal_handler()

        # 快速响应检测：简单问题跳过工具调用和深度推理
        if is_simple_query(user_input):
            self._use_reasoning_effort = "low"

        # 智能模型切换：根据任务类型自动选择最优模型
        self.switch_model_for_task(user_input)

        if not self.messages:
            self.messages = [self._build_system_message()]

        # 智能消息压缩：使用 MessageCompressor
        self.messages = MessageCompressor.compress_messages(self.messages)

        self._auto_compress()

        if extra_context:
            self.messages.append({"role": "system", "content": f"[记忆上下文]\n{extra_context}"})
        self.messages.append({"role": "user", "content": user_input})

        turn_id = self.timeline.start_turn(user_input)
        self.events.publish(EventType.TURN_START, {"input": user_input[:200]}, "engine")

        result = self._run_loop()

        self.timeline.end_turn(turn_id, result[:500])
        self.events.publish(EventType.TURN_END, {"result": result[:200], "tokens": self.stats.total_tokens}, "engine")

        if self.on_task_done:
            self.on_task_done(result, self.stats)
        return result

    def _run_loop(self) -> str:
        """帝皇决心循环：不完成不罢休"""
        from constants import LONG_TASK_THRESHOLD, TASK_ABANDON_TIMEOUT, PROGRESS_CHECK_INTERVAL

        turn = 0
        last_progress_time = time.time()
        last_output_hash = ""
        task_start_time = time.time()
        total_tool_calls = 0
        TASK_TIMEOUT = 90  # 任务级超时：90秒

        while turn < MAX_ITERATIONS:
            # 任务级超时保护
            elapsed = time.time() - task_start_time
            if elapsed > TASK_TIMEOUT:
                if self.on_tool_output:
                    self.on_tool_output("mundo", f"⚠️ 任务超时（{TASK_TIMEOUT}s），蒙多强制完成。", True)
                return self._force_complete()

            if self._interrupted or self.budget.exhausted:
                break

            turn += 1
            self.stats.turns = turn

            # 长任务提醒
            if turn == LONG_TASK_THRESHOLD:
                if self.on_tool_output:
                    self.on_tool_output("mundo", "⚡ 任务复杂，蒙多加大力度。", False)

            # 进度检查：防止死循环
            if turn % PROGRESS_CHECK_INTERVAL == 0:
                current_output = self._get_recent_output_hash()
                if current_output == last_output_hash:
                    if time.time() - last_progress_time > TASK_ABANDON_TIMEOUT:
                        if self.on_tool_output:
                            self.on_tool_output("mundo", "⚠️ 30分钟无进展，蒙多换策略。", True)
                        break
                else:
                    last_output_hash = current_output
                    last_progress_time = time.time()

            if self.budget.should_warn and self.on_budget_warn:
                self.on_budget_warn(self.budget)
                self.budget.mark_warned()

            if self.on_turn_start:
                self.on_turn_start(turn, self.stats)
            if self.on_stream_start:
                self.on_stream_start(turn)

            llm_start = time.time()
            assistant_msg = self._call_llm()
            if assistant_msg is None:
                break
            self.stats.llm_time += time.time() - llm_start

            self._update_token_stats(assistant_msg)

            if self.on_stream_end:
                self.on_stream_end(turn)
            if self.on_turn_end:
                self.on_turn_end(turn, self.stats)

            tool_calls = self._filter_tool_calls(assistant_msg.get("tool_calls", []))

            if not tool_calls:
                final_text = assistant_msg.get("content") or ""
                self.messages.append({"role": "assistant", "content": final_text})
                return final_text

            self.messages.append({
                "role": "assistant",
                "content": assistant_msg.get("content") or "",
                "tool_calls": tool_calls,
            })
            self._execute_tool_calls(tool_calls)
            total_tool_calls += len(tool_calls)

            if self._same_error_streak >= STUCK_THRESHOLD:
                # 换策略而非放弃
                if self.on_tool_output:
                    self.on_tool_output("mundo", f"工具 {self._last_error_tool} 卡住，蒙多换路。", True)
                self._same_error_streak = 0
                self._last_error_tool = ""
                continue

            self._auto_compress()

        return self._handle_loop_end(turn)

    def _force_complete(self) -> str:
        """强制完成：当任务超时时，基于已有信息生成最终回复"""
        # 收集所有工具输出作为上下文
        tool_outputs = []
        for msg in self.messages[-10:]:
            if msg.get("role") == "tool":
                tool_outputs.append(msg.get("content", "")[:500])

        # 生成总结性回复
        summary = "\n".join(tool_outputs[-5:]) if tool_outputs else "任务执行中..."
        return f"任务执行结果：\n{summary}"

    def _get_recent_output_hash(self) -> str:
        """获取最近输出的哈希，用于进度检测"""
        import hashlib
        recent = [m.get("content", "") for m in self.messages[-5:] if m.get("role") == "tool"]
        return hashlib.md5("".join(recent).encode()).hexdigest()

    def _handle_loop_end(self, turns: int = 0) -> str:
        """帝皇汇报：完整呈现结果，不压缩不省略"""
        if self._interrupted:
            return "蒙多被中断。已完成的部分如上所示。"
        if self._same_error_streak >= STUCK_THRESHOLD:
            return f"工具 {self._last_error_tool} 连续失败 {self._same_error_streak} 次。蒙多已尽力，建议检查工具可用性。"
        if self._consecutive_errors >= 5:
            return "蒙多遇到连续错误，无法继续。已完成的部分如上所示。"

        # 长任务：追加详细总结
        if turns >= 20:
            self.messages.append({
                "role": "user",
                "content": "请详细总结你刚才完成的所有工作，包括：\n1. 完成了哪些任务\n2. 每个任务的结果\n3. 遇到的问题和解决方案\n4. 后续建议（如有）\n\n不要省略任何细节。"
            })
        else:
            # 短任务：一句话总结
            self.messages.append({"role": "user", "content": "请用一句话总结你刚才完成的工作。"})

        try:
            summary_msg = self._call_llm()
            if summary_msg and summary_msg.get("content"):
                final = summary_msg["content"]
                self.messages.append({"role": "assistant", "content": final})
                return final
        except Exception:
            pass
        return "蒙多执行完毕。用 /status 查看详情。"

    def _install_signal_handler(self):
        def handler(signum, frame):
            self._interrupted = True
        signal.signal(signal.SIGINT, handler)

    def reset(self):
        self.messages = []
        self.stats.reset()
        self.budget.reset()
        self.tool_guard.reset()
        self._context = ContextMapper(ContextBudget(max_tokens=CONTEXT_MAX_TOKENS))

    def compact(self):
        if not self.messages:
            return
        old_count = len(self.messages)
        system_msg = self.messages[0] if self.messages[0]["role"] == "system" else None
        recent = self.messages[-CONTEXT_KEEP_RECENT:]
        old = self.messages[1:-CONTEXT_KEEP_RECENT] if len(self.messages) > CONTEXT_KEEP_RECENT + 1 else []

        summary_parts = []
        for m in old:
            content = (m.get("content") or "")[:80]
            if content:
                summary_parts.append(content)

        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        if summary_parts:
            new_messages.append({"role": "system", "content": f"[上下文压缩] {' | '.join(summary_parts[-8:])}"})
        new_messages.extend(recent)

        self.messages = new_messages
        return old_count, len(self.messages)
