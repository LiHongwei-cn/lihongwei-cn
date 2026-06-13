"""蒙多核心引擎 v3.0.0 — 脱胎换骨

v3.0.0 架构升级（基于 AI Agent/网安/RAG 专业知识）：
- 反射循环：先思考→再执行→再检查→再修复
- 安全强化：输入验证/输出消毒/注入防护
- 智能错误恢复：根据错误类型自适应策略
- RAG 知识检索：语义级知识召回
- 工作流集成：复杂任务自动分解为阶段

不是堆功能。是让蒙多学会"三思而后行"。
"""

import sys
import json
import time
import signal
import hashlib
from typing import List, Dict, Optional, Callable, Tuple
from llm import LLMClient, repair_json, _is_timeout_error
from constants import (
    VERSION, CHAR_TO_TOKEN,
    CONTEXT_MAX_TOKENS, CONTEXT_COMPRESS_THRESHOLD, CONTEXT_KEEP_RECENT,
    BUDGET_MAX_PROMPT, BUDGET_MAX_COMPLETION, BUDGET_WARN_THRESHOLD,
    STUCK_THRESHOLD, IDLE_TIMEOUT, MAX_RETRY, RETRY_DELAY,
    MAX_ITERATIONS, TOOL_MAX_OUTPUT, STREAM_MAX_WAIT,
    REFLECTION_MAX_TURNS, KNOWLEDGE_MAX_CONTEXT_CHARS,
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
from reflection_engine import (
    get_reflection_engine, get_strategy_selector,
    Phase as ReflectionPhase, ReflectionVerdict, ReflectionEntry,
)
from security_hardening import get_security
from intelligent_recovery import (
    get_recovery, get_compressor,
    ErrorCategory, RecoveryStrategy,
)
from knowledge_retriever import get_knowledge_retriever
from workflow import WorkflowEngine, PhaseStatus


# ═══════════════════════════════════════════════
# 错误分类
# ═══════════════════════════════════════════════

def _classify_error(error: Exception, raw_msg: str) -> Dict:
    msg = raw_msg.lower()
    result = {"category": "unknown", "retryable": False, "user_tip": "", "log_detail": raw_msg}

    if isinstance(error, (ConnectionResetError, ConnectionRefusedError, BrokenPipeError)):
        result.update(category="connection", retryable=True, user_tip="连接被中断，正在重试…")
        return result
    if any(kw in msg for kw in ["reset", "broken pipe", "eof", "远程主机"]):
        result.update(category="connection", retryable=True, user_tip="连接被中断，正在重试…")
        return result

    if "dns" in msg or "connection refused" in msg:
        result.update(category="network", retryable=True, user_tip="无法连接到模型服务。请检查网络。")
        return result

    if _is_timeout_error(error) or "timeout" in msg or "超时" in raw_msg:
        result.update(category="timeout", retryable=True, user_tip="请求超时。模型可能繁忙，正在重试…")
        return result

    if any(kw in msg for kw in ["401", "unauthorized", "invalid api key", "api key"]):
        result.update(category="auth", user_tip="API key 无效或已过期。运行 /setup 更新。")
        return result

    if any(kw in msg for kw in ["429", "rate limit", "too many"]):
        result.update(category="rate_limit", retryable=True, user_tip="请求过于频繁，稍后重试…")
        return result

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
        self.reflection_count = 0
        self.recovery_count = 0

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
    """蒙多核心引擎 v3.0.0 — 脱胎换骨"""

    def __init__(self, provider="deepseek", model=None):
        if model is None:
            model = SmartModelSelector.select_model(provider, TaskType.GENERAL)

        self.client = LLMClient(provider=provider, model=model)
        self.provider = provider
        self.model_name = model or self.client.model

        self.adapter = get_model_adapter(self.model_name)
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

        # 工具循环防护
        self.tool_guard = ToolGuardController()

        # 上下文映射器
        self._context = ContextMapper(ContextBudget(max_tokens=CONTEXT_MAX_TOKENS))

        # v3.0.0: 新模块
        self.reflection = get_reflection_engine()
        self.security = get_security()
        self.recovery = get_recovery()
        self.compressor = get_compressor()
        self.knowledge = get_knowledge_retriever()
        self.workflow = WorkflowEngine()

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
        task_type = SmartModelSelector.detect_task_type(task_description)
        optimal_model = SmartModelSelector.select_model(self.provider, task_type)
        if optimal_model and optimal_model != self.model_name:
            self.model_name = optimal_model
            self.adapter = get_model_adapter(optimal_model)
            self.max_tokens_override = self.adapter.profile.max_tokens_default
            return True
        return False

    def _auto_compress(self):
        if not self._context.should_compress():
            return
        old_tokens = self._context.total_tokens
        new_tokens = self._context.compress()[1]
        if self.on_compress:
            self.on_compress(len(self._context._chunks), len(self._context._chunks), old_tokens, new_tokens)

    def _detect_reasoning_effort(self) -> Optional[str]:
        if not self.adapter.profile.supports_reasoning:
            return None
        if self.stats.tool_calls_count == 0:
            return "low"
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

        import tools as tool_module
        tool_schemas = tool_module.registry.schemas if hasattr(tool_module, 'registry') else []

        effort = self._detect_reasoning_effort()

        if self._use_streaming:
            try:
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
        elif classified.get("category") == "auth":
            # 只有认证错误才是真正的致命错误
            self._interrupted = True
        else:
            # 非致命错误：记录但不中断，让 _run_loop 决定是否继续
            self.stats.retries_count += 1

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

        dispatch_calls = [
            DispatchToolCall(id=tc.get("id", ""), name=name, args=args)
            for tc, name, args in calls
        ]

        def _executor(name: str, args: dict) -> str:
            return tool_module.execute_tool(name, args)

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
        """执行单个工具调用 — v3.0.0 集成安全检查和智能恢复"""

        # v3.0.0: 安全检查
        security_result = self.security.validate_tool_call(name, args)
        if not security_result.is_valid:
            self.messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": f"[安全拒绝] {', '.join(security_result.threats)}"
            })
            return

        # 策略检查
        policy_result = self.policy.evaluate_tool(name, args)
        if policy_result.is_denied:
            self.messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": f"[策略拒绝] {policy_result.reason}"
            })
            return

        if self.on_tool_call:
            self.on_tool_call(name, args, self.stats)

        tool_start = time.time()
        LONG_TIMEOUT_TOOLS = {"delegate_agent"}
        TOOL_TIMEOUT = 600 if name in LONG_TIMEOUT_TOOLS else 30

        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool_module.execute_tool, name, args)
                try:
                    output = future.result(timeout=TOOL_TIMEOUT)
                except FutureTimeout:
                    output = f"[工具 {name} 执行超时（{TOOL_TIMEOUT}s）]"
                    future.cancel()

            duration = (time.time() - tool_start) * 1000

            guard_decision = self.tool_guard.observe(name, args, str(output), is_error=False)
            if guard_decision.action == GuardAction.HALT:
                # v3.0.1: HALT 不再直接中断引擎，降级为警告 + 注入提示
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": guard_decision.message + "\n[提示] 工具循环防护建议换策略，但蒙多可以继续执行。"
                })
                return
            if guard_decision.action in (GuardAction.WARN, GuardAction.BLOCK):
                if self.on_tool_output:
                    self.on_tool_output("guard", guard_decision.message, True)

            # v3.0.0: 输出消毒
            sanitized_output = self.security.sanitize_output(str(output))
            self._handle_tool_result(tc, name, args, sanitized_output, False, duration)

        except Exception as e:
            duration = (time.time() - tool_start) * 1000
            guard_decision = self.tool_guard.observe(name, args, str(e), is_error=True)
            if guard_decision.action == GuardAction.HALT:
                # v3.0.1: 错误 HALT 也不中断引擎
                pass

            # v3.0.0: 智能错误恢复
            self._handle_tool_error_with_recovery(tc, name, args, e, duration)

    def _handle_tool_result(self, tc, name: str, args: dict, output: str, is_error: bool, duration: float):
        if is_error:
            self._handle_tool_error(tc, name, args, Exception(output), duration)
            return

        self.stats.tool_calls_count += 1
        self.stats.tool_time += duration / 1000
        self._consecutive_errors = 0
        self._same_error_streak = 0

        self.messages.append({
            "role": "tool",
            "tool_call_id": tc.get("id", ""),
            "content": str(output)[:TOOL_MAX_OUTPUT]
        })
        if self.on_tool_output:
            self.on_tool_output(name, str(output)[:500], False)

        self.timeline.record_tool(name, args, str(output)[:1000], duration)
        self.events.publish(EventType.TOOL_RESULT, {"tool": name, "duration_ms": duration}, "engine")

    def _handle_tool_error(self, tc, name: str, args: dict, error: Exception, duration: float):
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

    def _handle_tool_error_with_recovery(self, tc, name: str, args: dict, error: Exception, duration: float):
        """v3.0.0: 智能错误恢复"""
        self._consecutive_errors += 1
        self.stats.errors_count += 1
        self.stats.recovery_count += 1

        if name == self._last_error_tool:
            self._same_error_streak += 1
        else:
            self._same_error_streak = 1
            self._last_error_tool = name

        # 分析错误类型
        category, confidence = self.recovery.analyze_error(error, str(error))

        # 获取恢复计划
        plan = self.recovery.get_recovery_plan(category, self._same_error_streak)

        # 记录错误
        error_record = {
            "tool": name,
            "category": category.name,
            "strategy": plan.strategy.value,
            "confidence": confidence,
        }

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
        self.reflection.reset()
        self._interrupted = False
        self._use_streaming = self.adapter.profile.supports_streaming
        self._slack_count = 0
        self._install_signal_handler()

        # v3.0.0: 安全验证
        is_safe, sanitized_input, warnings = self.security.validate_and_sanitize(user_input)
        if warnings:
            for warning in warnings:
                if self.on_tool_output:
                    self.on_tool_output("security", f"安全提示: {warning}", False)

        # 快速响应检测
        if is_simple_query(sanitized_input):
            self._use_reasoning_effort = "low"

        # 智能模型切换
        self.switch_model_for_task(sanitized_input)

        if not self.messages:
            self.messages = [self._build_system_message()]

        # 智能消息压缩
        self.messages = MessageCompressor.compress_messages(self.messages)
        self._auto_compress()

        # v3.0.0: RAG 知识检索
        knowledge_context = self.knowledge.get_context_for_query(sanitized_input)
        if knowledge_context:
            self.messages.append({
                "role": "system",
                "content": f"[相关知识]\n{knowledge_context}"
            })

        if extra_context:
            self.messages.append({"role": "system", "content": f"[记忆上下文]\n{extra_context}"})
        self.messages.append({"role": "user", "content": sanitized_input})

        turn_id = self.timeline.start_turn(sanitized_input)
        self.events.publish(EventType.TURN_START, {"input": sanitized_input[:200]}, "engine")

        result = self._run_loop()

        self.timeline.end_turn(turn_id, result[:500])
        self.events.publish(EventType.TURN_END, {"result": result[:200], "tokens": self.stats.total_tokens}, "engine")

        if self.on_task_done:
            self.on_task_done(result, self.stats)
        return result

    def _run_loop(self) -> str:
        """v3.0.0: 反射循环 — 先思考→再执行→再检查→再修复"""
        from constants import LONG_TASK_THRESHOLD, TASK_ABANDON_TIMEOUT, PROGRESS_CHECK_INTERVAL

        turn = 0
        last_progress_time = time.time()
        last_output_hash = ""
        total_tool_calls = 0
        total_tools_across_all_turns = 0

        while turn < MAX_ITERATIONS:
            if self._interrupted or self.budget.exhausted:
                break

            turn += 1
            self.stats.turns = turn

            # 长任务提醒
            if turn == LONG_TASK_THRESHOLD:
                if self.on_tool_output:
                    self.on_tool_output("mundo", "⚡ 任务复杂，蒙多加大力度。", False)

            # 进度检查
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
                # v3.0.1: LLM 返回 None 不直接放弃，尝试恢复
                if self._consecutive_errors < 5:
                    time.sleep(2)
                    continue  # 再试一轮
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

                # v3.0.0: 反射检查 — 检查输出质量
                verdict = self.reflection.analyze_output(final_text)
                self.reflection.record_reflection(ReflectionEntry(
                    turn=turn,
                    phase=ReflectionPhase.REFLECT,
                    thought="检查最终输出质量",
                    action="output_analysis",
                    result=final_text[:500],
                    verdict=verdict,
                    lessons=[],
                ))

                # 反摸鱼检测（最多触发 3 次，避免死循环）
                if total_tools_across_all_turns == 0 and len(final_text.strip()) < 50:
                    slack_count = getattr(self, '_slack_count', 0)
                    if slack_count >= 3:
                        return final_text or "蒙多执行完毕。"
                    self._slack_count = slack_count + 1
                    self.messages.append({"role": "assistant", "content": final_text})
                    self.messages.append({
                        "role": "system",
                        "content": "【帝皇斥责】蒙多，你在摸鱼！用户给了你任务，你没有调用任何工具就试图结束。"
                                   "现在立刻开始执行：分析任务需求，调用合适的工具完成它。不允许空回复。"
                    })
                    if self.on_tool_output:
                        self.on_tool_output("mundo", "⚡ 摸鱼检测触发：强制继续执行", False)
                    total_tool_calls = 0
                    continue

                # 如果反射判定为失败，继续执行
                if verdict == ReflectionVerdict.FAILURE and self.reflection.should_continue():
                    self.messages.append({"role": "assistant", "content": final_text})
                    hint = self.reflection.get_strategy_hint()
                    self.messages.append({
                        "role": "system",
                        "content": f"【反射修正】上次结果不合格。{hint}\n请重新执行任务。"
                    })
                    self.stats.reflection_count += 1
                    continue

                self.messages.append({"role": "assistant", "content": final_text})
                return final_text

            self.messages.append({
                "role": "assistant",
                "content": assistant_msg.get("content") or "",
                "tool_calls": tool_calls,
            })
            self._execute_tool_calls(tool_calls)
            total_tool_calls += len(tool_calls)
            total_tools_across_all_turns += len(tool_calls)

            if self._same_error_streak >= STUCK_THRESHOLD:
                if self.on_tool_output:
                    self.on_tool_output("mundo", f"工具 {self._last_error_tool} 卡住，蒙多换路。", True)
                self._same_error_streak = 0
                self._last_error_tool = ""
                continue

            self._auto_compress()

        return self._handle_loop_end(turn)

    def _force_complete(self) -> str:
        tool_outputs = []
        for msg in self.messages[-10:]:
            if msg.get("role") == "tool":
                tool_outputs.append(msg.get("content", "")[:500])
        summary = "\n".join(tool_outputs[-5:]) if tool_outputs else "任务执行中..."
        return f"任务执行结果：\n{summary}"

    def _get_recent_output_hash(self) -> str:
        recent = [m.get("content", "") for m in self.messages[-5:] if m.get("role") == "tool"]
        return hashlib.md5("".join(recent).encode()).hexdigest()

    def _handle_loop_end(self, turns: int = 0) -> str:
        """帝皇汇报 — v3.0.1 无条件输出已完成的工作"""
        if self._interrupted:
            # 即使被中断，也输出已完成的工作
            tool_outputs = []
            for msg in self.messages[-10:]:
                if msg.get("role") == "tool":
                    tool_outputs.append(msg.get("content", "")[:500])
            if tool_outputs:
                return "蒙多被中断，但已完成的部分：\n" + "\n".join(tool_outputs[-5:])
            return "蒙多被中断。"
        if self._same_error_streak >= STUCK_THRESHOLD:
            return f"工具 {self._last_error_tool} 连续失败 {self._same_error_streak} 次。蒙多已尽力，建议检查工具可用性。"
        if self._consecutive_errors >= 5:
            return "蒙多遇到连续错误，无法继续。已完成的部分如上所示。"

        # v3.0.0: 生成反射总结
        reflection_summary = self.reflection.get_reflection_summary()

        if turns >= 20:
            self.messages.append({
                "role": "user",
                "content": f"请详细总结你刚才完成的所有工作。\n\n反射总结: {reflection_summary}"
            })
        else:
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
        self.reflection.reset()
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


# 向后兼容别名
MundoAgent = MundoEngine
