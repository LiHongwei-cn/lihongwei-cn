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
from task_analyzer import get_task_analyzer


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
    def remaining(self) -> int:
        return max(0, self.max_prompt_tokens - self.prompt_tokens_used)

    @property
    def usage_ratio(self) -> float:
        return self.prompt_tokens_used / self.max_prompt_tokens if self.max_prompt_tokens else 0

    @property
    def should_warn(self) -> bool:
        return self.usage_ratio >= self.warn_threshold and not self._warned

    @property
    def exhausted(self) -> bool:
        if self.prompt_tokens_used >= self.max_prompt_tokens:
            return True
        if self.completion_tokens_used >= self.max_completion_tokens:
            return True
        if self.max_turns > 0 and self.turns_used >= self.max_turns:
            return True
        return False

    def update(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        self.prompt_tokens_used += prompt_tokens
        self.completion_tokens_used += completion_tokens
        self.turns_used += 1

    def mark_warned(self) -> None:
        self._warned = True

    def reset(self) -> None:
        self.prompt_tokens_used = 0
        self.completion_tokens_used = 0
        self.turns_used = 0
        self._warned = False


class TaskStats:
    def __init__(self):
        self.reset()

    def reset(self) -> None:
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
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def elapsed_str(self) -> str:
        s = self.elapsed
        if s < 60:
            return f"{s:.1f}s"
        m = int(s // 60)
        return f"{m}m{s - m*60:.0f}s"


# ═══════════════════════════════════════════════
# 引擎
# ═══════════════════════════════════════════════

class MundoEngine:
    """蒙多核心引擎 v3.0.0 — 脱胎换骨

    v2.2.0 改进：
    - 添加上下文管理器协议（__enter__/__exit__）
    - 使用 threading.Event 替代 bool 标志
    - 保留和恢复信号处理器
    - 修复 is_safe 检查
    - 修复 dead code (_use_reasoning_effort)
    - 修复 _slack_count 初始化
    - 修复 _auto_compress chunk 计数
    - 修复 cache key 包含 knowledge_context
    - 修复 progress hash 包含 assistant 消息
    """

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
        self._use_reasoning_effort: Optional[str] = None  # v2.2.0: 初始化
        self._slack_count: int = 0  # v2.2.0: 初始化到 __init__
        self._consecutive_errors = 0
        self._last_error_tool = ""
        self._same_error_streak = 0
        self._last_activity_time = time.time()

        # v2.2.0: 使用 threading.Event 替代 bool（线程安全）
        import threading
        self._interrupted = threading.Event()
        self._old_signal_handler = None  # 保存旧的信号处理器

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

        # v2.2.0: 共享线程池（避免每次工具调用创建新线程池）
        from concurrent.futures import ThreadPoolExecutor
        self._tool_executor = ThreadPoolExecutor(max_workers=2)

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

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口 — 清理资源"""
        self.close()
        return False

    def close(self) -> None:
        """清理资源：关闭线程池，恢复信号处理器"""
        if hasattr(self, '_tool_executor') and self._tool_executor:
            self._tool_executor.shutdown(wait=False)
        # 恢复旧的信号处理器
        if self._old_signal_handler is not None:
            import signal
            signal.signal(signal.SIGINT, self._old_signal_handler)
            self._old_signal_handler = None

    def analyze_task(self, task: str) -> Dict:
        """分析任务复杂度和类型"""
        from task_analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer()
        return analyzer.analyze(task)

    def execute_task(self, task: str, **kwargs) -> str:
        """执行任务（快捷方法）"""
        return self.chat(task, **kwargs)

    def reflect(self, conversation: List[Dict] = None) -> Dict:
        """反思对话，提取教训和改进点"""
        conv = conversation or self.messages
        if not conv:
            return {"status": "no_conversation", "lessons": []}
        return self.reflection.reflect(conv)

    def _build_system_message(self, memory_context: str = "", knowledge_context: str = "") -> Dict:
        """构建 system message — 模块化组装 + 缓存优化

        v2.2.0: 将内存上下文和知识上下文合并到主 system message 中，
        避免绕过前缀缓存。
        """
        cache = get_cache()
        # v2.2.0: 缓存键包含 memory + knowledge hash，确保缓存失效正确
        combined = f"{memory_context}:{knowledge_context}"
        context_hash = hashlib.md5(combined.encode()).hexdigest()[:12] if combined.strip() else ""
        cache_key = f"{self.provider}/{self.model_name}/{context_hash}"

        content = cache.get_system_prompt(
            self.provider, cache_key,
            lambda: build_system_prompt(
                model_adapter=self.adapter,
                quark_optimizer=True,
                provider=self.provider,
                model_name=self.model_name,
            )
        )

        # 合并内存上下文和知识上下文
        if memory_context or knowledge_context:
            parts = [content]
            if knowledge_context:
                parts.append(f"\n[相关知识]\n{knowledge_context}")
            if memory_context:
                parts.append(f"\n[记忆上下文]\n{memory_context}")
            content = "\n".join(parts)

        return {"role": "system", "content": content}

    def _model_display(self):
        return f"{self.provider}/{self.model_name}"

    def switch_model_for_task(self, task_description: str) -> bool:
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
        # v2.2.0: 修复 chunk 计数 — 在压缩前捕获旧数量
        old_chunks = self._context.chunk_count
        new_tokens = self._context.compress()[1]
        new_chunks = self._context.chunk_count
        if self.on_compress:
            self.on_compress(old_chunks, new_chunks, old_tokens, new_tokens)

    def _detect_reasoning_effort(self) -> Optional[str]:
        if not self.adapter.profile.supports_reasoning:
            return None
        # v2.2.0: 读取 _use_reasoning_effort（之前设置但从未读取）
        if self._use_reasoning_effort:
            return self._use_reasoning_effort
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
                self._interrupted.set()  # v2.2.0: 使用 threading.Event
                return None
            except Exception as e:
                self._handle_llm_error(e, attempt)
                if self._interrupted.is_set():  # v2.2.0: 使用 threading.Event
                    return None
        return None

    def _try_call_llm(self, attempt: int) -> Optional[Dict]:
        # v3.2.0: LLM 调用速率限制
        if not self.security.check_rate_limit(f"llm:{self.provider}", max_per_minute=30):
            return None

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
                # v2.2.0: 修复 streaming fallback — 递增 attempt 防止无限递归
                if attempt == 0:
                    self._use_streaming = False
                    self.stats.retries_count += 1
                    return self._try_call_llm(attempt + 1)  # 递增 attempt
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
            # 认证错误：致命，立即中断
            self._interrupted.set()  # v2.2.0: 使用 threading.Event
        else:
            # 非致命错误：添加退避睡眠，连续5次后中断
            self.stats.retries_count += 1
            if self._consecutive_errors >= 5:
                self._interrupted.set()  # v2.2.0: 使用 threading.Event
            else:
                # 退避睡眠：连续错误越多，等待越久
                backoff = min(RETRY_DELAY * (2 ** self._consecutive_errors), 30.0)
                time.sleep(backoff)

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
            if self._interrupted.is_set():  # v2.2.0: 使用 threading.Event
                break
            fn = tc.get("function", {})
            name = fn.get("name", "")
            raw_args = fn.get("arguments", "{}")
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                # v2.2.7: 尝试 repair_json 修复不完整 JSON
                args = repair_json(raw_args)
                if args is None:
                    if self.on_tool_output:
                        self.on_tool_output("warning", f"工具参数 JSON 解析失败: {raw_args[:100]}", True)
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
                if self._interrupted.is_set():  # v2.2.0: 使用 threading.Event
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

        # v3.2.0: 速率限制
        if not self.security.check_rate_limit(f"tool:{name}", max_per_minute=60):
            self.messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": "[速率限制] 该工具调用过于频繁，请稍后再试。"
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
            from concurrent.futures import TimeoutError as FutureTimeout
            future = self._tool_executor.submit(tool_module.execute_tool, name, args)
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

            self._handle_tool_error(tc, name, args, e, duration, use_recovery=True)

    def _handle_tool_result(self, tc: Dict, name: str, args: dict, output: str, is_error: bool, duration: float) -> None:
        if is_error:
            self._handle_tool_error(tc, name, args, Exception(output), duration, use_recovery=False)
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

    def _handle_tool_error(self, tc, name: str, args: dict, error: Exception, duration: float,
                           use_recovery: bool = True):
        """统一的工具错误处理 — v3.2.0 合并两个重复方法

        Args:
            use_recovery: True 时启用智能错误恢复（分析类型 + 获取恢复计划）
        """
        self._consecutive_errors += 1
        self.stats.errors_count += 1

        if name == self._last_error_tool:
            self._same_error_streak += 1
        else:
            self._same_error_streak = 1
            self._last_error_tool = name

        # 智能错误恢复（可选）
        if use_recovery:
            self.stats.recovery_count += 1
            category, confidence = self.recovery.analyze_error(error, str(error))
            self.recovery.get_recovery_plan(category, self._same_error_streak)

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
        self._interrupted.clear()  # v2.2.0: 使用 threading.Event
        self._use_streaming = self.adapter.profile.supports_streaming
        self._use_reasoning_effort = None  # v2.2.0: 重置
        self._slack_count = 0
        self._install_signal_handler()

        # v3.0.0: 安全验证
        is_safe, sanitized_input, warnings = self.security.validate_and_sanitize(user_input)
        if warnings:
            for warning in warnings:
                if self.on_tool_output:
                    self.on_tool_output("security", f"安全提示: {warning}", False)

        # v2.2.0: 检查 is_safe 标志（之前被忽略）
        if not is_safe:
            return "[安全警告] 输入包含潜在不安全内容，已使用净化版本继续处理。"

        # v2.2.7: 任务分析 — 先理解再执行
        task_analysis = None
        if not is_simple_query(sanitized_input):
            try:
                analyzer = get_task_analyzer()
                task_analysis = analyzer.analyze(sanitized_input)
            except Exception:
                task_analysis = None

        # 快速响应检测
        if is_simple_query(sanitized_input):
            self._use_reasoning_effort = "low"

        # 智能模型切换（结合任务分析结果）
        if task_analysis:
            self.switch_model_for_task(sanitized_input + " " + task_analysis.task_type.value)
        else:
            self.switch_model_for_task(sanitized_input)

        # v2.2.0: RAG 知识检索（结合任务分析关键词）
        query_for_rag = sanitized_input
        if task_analysis and task_analysis.keywords:
            query_for_rag = sanitized_input + " " + " ".join(task_analysis.keywords[:5])
        knowledge_context = self.knowledge.get_context_for_query(query_for_rag)

        # 构建系统消息（注入任务分析上下文）
        task_context = ""
        if task_analysis:
            task_context = task_analysis.to_prompt_context()

        merged_context = "\n\n".join(filter(None, [extra_context, task_context]))

        if not self.messages:
            self.messages = [self._build_system_message(
                memory_context=merged_context,
                knowledge_context=knowledge_context,
            )]
        else:
            # 如果已有消息，更新系统消息（合并上下文）
            if self.messages and self.messages[0].get("role") == "system":
                self.messages[0] = self._build_system_message(
                    memory_context=merged_context,
                    knowledge_context=knowledge_context,
                )

        # 智能消息压缩
        self.messages = MessageCompressor.compress_messages(self.messages)
        self._auto_compress()

        self.messages.append({"role": "user", "content": sanitized_input})

        turn_id = self.timeline.start_turn(sanitized_input)
        self.events.publish(EventType.TURN_START, {"input": sanitized_input[:200]}, "engine")

        result = self._run_loop()

        self.timeline.end_turn(turn_id, result[:500])
        self.events.publish(EventType.TURN_END, {"result": result[:200], "tokens": self.stats.total_tokens}, "engine")

        if self.on_task_done:
            self.on_task_done(result, self.stats)
        return result

    # ── _run_loop 子方法 ────────────────────────────

    def _check_long_task(self, turn: int):
        """长任务提醒"""
        from constants import LONG_TASK_THRESHOLD
        if turn == LONG_TASK_THRESHOLD and self.on_tool_output:
            self.on_tool_output("mundo", "⚡ 任务复杂，蒙多加大力度。", False)

    def _check_progress(self, turn: int, last_time: float, last_hash: str):
        """进度检查 — 返回 (should_break, last_hash, last_time)"""
        from constants import PROGRESS_CHECK_INTERVAL, TASK_ABANDON_TIMEOUT
        if turn % PROGRESS_CHECK_INTERVAL != 0:
            return False, last_hash, last_time
        current = self._get_recent_output_hash()
        if current == last_hash and time.time() - last_time > TASK_ABANDON_TIMEOUT:
            if self.on_tool_output:
                self.on_tool_output("mundo", "⚠️ 30分钟无进展，蒙多换策略。", True)
            return True, current, last_time
        if current != last_hash:
            return False, current, time.time()
        return False, last_hash, last_time

    def _notify_budget(self):
        """预算警告通知"""
        if self.budget.should_warn and self.on_budget_warn:
            self.on_budget_warn(self.budget)
            self.budget.mark_warned()

    def _emit_turn_events(self, turn: int):
        """发送回合开始事件"""
        if self.on_turn_start:
            self.on_turn_start(turn, self.stats)
        if self.on_stream_start:
            self.on_stream_start(turn)

    def _emit_turn_end_events(self, turn: int):
        """发送回合结束事件"""
        if self.on_stream_end:
            self.on_stream_end(turn)
        if self.on_turn_end:
            self.on_turn_end(turn, self.stats)

    def _try_llm_with_recovery(self) -> Optional[Dict]:
        """调用 LLM，失败时尝试恢复"""
        llm_start = time.time()
        result = self._call_llm()
        if result is not None:
            self.stats.llm_time += time.time() - llm_start
            return result
        # LLM 返回 None — 连续错误未达阈值则等待后返回 None（让调用方 continue）
        if self._consecutive_errors < 5:
            time.sleep(2)
        return None

    def _handle_no_tools_response(self, final_text: str, turn: int,
                                   tools_used_so_far: int) -> Tuple[str, bool]:
        """处理无工具调用的回复 — 返回 (结果或None, 是否continue)

        返回值：
        - (final_result, False) — 最终答案，循环结束
        - (None, True) — 需要继续循环（摸鱼/反射触发）
        """
        # 反射检查
        verdict = self.reflection.analyze_output(final_text)
        self.reflection.record_reflection(ReflectionEntry(
            turn=turn, phase=ReflectionPhase.REFLECT,
            thought="检查最终输出质量", action="output_analysis",
            result=final_text[:500], verdict=verdict, lessons=[],
        ))

        # 反摸鱼检测
        slack_result = self._check_slack(final_text, tools_used_so_far)
        if slack_result is not None:
            return slack_result, True

        # 反射失败 → 继续
        if verdict == ReflectionVerdict.FAILURE and self.reflection.should_continue():
            self.messages.append({"role": "assistant", "content": final_text})
            self.messages.append({
                "role": "system",
                "content": f"【反射修正】上次结果不合格。{self.reflection.get_strategy_hint()}\n请重新执行任务。"
            })
            self.stats.reflection_count += 1
            return None, True

        self.messages.append({"role": "assistant", "content": final_text})
        return final_text, False

    def _check_slack(self, final_text: str, tools_used_so_far: int) -> Optional[str]:
        """反摸鱼检测 — 返回 None 表示非摸鱼，返回 str 表示最终结果"""
        if tools_used_so_far > 0 or len(final_text.strip()) >= 50:
            return None
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
        return None

    def _record_assistant_tool_msg(self, assistant_msg: Dict, tool_calls: list):
        """记录 assistant 的工具调用消息"""
        self.messages.append({
            "role": "assistant",
            "content": assistant_msg.get("content") or "",
            "tool_calls": tool_calls,
        })

    def _handle_stuck_tool(self):
        """卡住工具处理 — 重置错误计数，提示换路"""
        if self.on_tool_output:
            self.on_tool_output("mundo", f"工具 {self._last_error_tool} 卡住，蒙多换路。", True)
        self._same_error_streak = 0
        self._last_error_tool = ""

    # ── 主循环 ─────────────────────────────────────

    def _run_loop(self) -> str:
        """v3.0.0: 反射循环 — 先思考→再执行→再检查→再修复

        v3.2.0: 拆分为子方法，每个方法 <30 行，职责单一。
        """
        turn = 0
        last_time = time.time()
        last_hash = ""
        tools_this_turn = 0
        tools_all_turns = 0

        while turn < MAX_ITERATIONS:
            if self._interrupted.is_set() or self.budget.exhausted:
                break

            turn += 1
            self.stats.turns = turn

            self._check_long_task(turn)

            should_break, last_hash, last_time = self._check_progress(turn, last_time, last_hash)
            if should_break:
                break

            self._notify_budget()
            self._emit_turn_events(turn)

            assistant_msg = self._try_llm_with_recovery()
            if assistant_msg is None:
                if self._consecutive_errors >= 5:
                    break
                continue

            self._update_token_stats(assistant_msg)
            self._emit_turn_end_events(turn)

            tool_calls = self._filter_tool_calls(assistant_msg.get("tool_calls", []))

            if not tool_calls:
                final_text = assistant_msg.get("content") or ""
                result, should_continue = self._handle_no_tools_response(
                    final_text, turn, tools_all_turns)
                tools_this_turn = 0
                if not should_continue:
                    return result
                continue

            self._record_assistant_tool_msg(assistant_msg, tool_calls)
            self._execute_tool_calls(tool_calls)
            tools_this_turn += len(tool_calls)
            tools_all_turns += len(tool_calls)

            if self._same_error_streak >= STUCK_THRESHOLD:
                self._handle_stuck_tool()
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
        # v2.2.0: 包含 assistant 消息，避免只检查 tool 输出导致误判
        recent = [m.get("content", "") for m in self.messages[-5:]
                  if m.get("role") in ("tool", "assistant") and m.get("content")]
        return hashlib.md5("".join(recent).encode()).hexdigest()

    def _handle_loop_end(self, turns: int = 0) -> str:
        """帝皇汇报 — v3.0.1 无条件输出已完成的工作"""
        if self._interrupted.is_set():  # v2.2.0: 使用 threading.Event
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
        except Exception as e:
            # v2.2.0: 记录异常而不是静默忽略
            if self.on_tool_output:
                self.on_tool_output("error", f"总结生成失败: {str(e)[:100]}", True)
        return "蒙多执行完毕。用 /status 查看详情。"

    def _install_signal_handler(self):
        """安装信号处理器 — v2.2.0: 保留旧处理器"""
        def handler(signum, frame):
            self._interrupted.set()  # v2.2.0: 使用 threading.Event
        # 保存旧的信号处理器，以便后续恢复
        self._old_signal_handler = signal.signal(signal.SIGINT, handler)

    def reset(self) -> None:
        self.messages = []
        self.stats.reset()
        self.budget.reset()
        self.tool_guard.reset()
        self.reflection.reset()
        self._context = ContextMapper(ContextBudget(max_tokens=CONTEXT_MAX_TOKENS))

    def compact(self) -> Optional[tuple]:
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
