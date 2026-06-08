"""蒙多核心引擎 v1.4.1 — Agentic Loop

v1.4.1 优化：
- 消除 ContextCompressor 重复（使用 context_mapper.py）
- 统一使用 constants.py 常量
- 拆分 run() 为更小的函数
- 减少 token 使用：精简 system prompt
"""

import sys
import json
import time
import signal
from typing import List, Dict, Optional, Callable
from llm import LLMClient, repair_json, _is_timeout_error
from constants import (
    VERSION, CHAR_TO_TOKEN,
    CONTEXT_MAX_TOKENS, CONTEXT_COMPRESS_THRESHOLD, CONTEXT_KEEP_RECENT,
    BUDGET_MAX_PROMPT, BUDGET_MAX_COMPLETION, BUDGET_WARN_THRESHOLD,
    STUCK_THRESHOLD, IDLE_TIMEOUT, MAX_RETRY, STREAM_MAX_WAIT,
)
from policy import get_policy_engine, PolicyContext, Action
from events import get_event_bus, EventType, Priority
from timeline import get_timeline, EntryType
from context_mapper import ContextMapper, ContextBudget, ChunkType
from cache import get_cache_manager
from sandbox import get_sandbox
from runtime_config import get_config


# ═══════════════════════════════════════════════
# System Prompt — 精简版，省 token
# ═══════════════════════════════════════════════

MUNDO_SYSTEM_PROMPT = """你是蒙多，THE EMPEROR。直接、高效、不废话。中文交流，代码命名用英文。

工具：terminal/read_file/write_file/edit_file/search_files/web_search/list_directory。
需要时直接调用，不需要时不调。简单问题直接回答。
- 读文件前先 search_files 定位
- terminal 失败时分析错误再重试，不重复同样命令
- 多个独立操作可并行调用

完成反馈（最高优先级）：
最后一个 response 必须输出：一句话说明 + 关键结果 + 改动列表。
简单任务一句话即可。不要省略。

语言：短句优先。一个句子一件事。活人感 > 机器感。"""


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
    MAX_ITERATIONS = 50

    def __init__(self, provider="xiaomi", model=None):
        self.client = LLMClient(provider=provider, model=model)
        self.provider = provider
        self.model_name = model or self.client.model
        self.messages: List[Dict] = []
        self.max_tokens_override = 4096
        self.stats = TaskStats()
        self.budget = IterationBudget()
        self._use_streaming = True
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
        return {"role": "system", "content": MUNDO_SYSTEM_PROMPT}

    def _model_display(self):
        return f"{self.provider}/{self.model_name}"

    def _auto_compress(self):
        if not self._context.should_compress():
            return
        old_tokens = self._context.total_tokens
        new_tokens = self._context.compress()[1]
        if self.on_compress:
            self.on_compress(len(self._context._chunks), len(self._context._chunks), old_tokens, new_tokens)

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

        if self._use_streaming:
            try:
                stream = self.client.chat_stream(messages, max_tokens=max_tokens)
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
            return self.client.chat(messages, max_tokens=max_tokens)

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
        for tc in tool_calls:
            if self._interrupted:
                break
            fn = tc.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}

            # 策略检查
            policy_result = self.policy.evaluate_tool(name, args)
            if policy_result.is_denied:
                self.messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": f"[策略拒绝] {policy_result.reason}"})
                continue

            if self.on_tool_call:
                self.on_tool_call(name, args, self.stats)

            tool_start = time.time()
            try:
                output = tool_module.execute_tool(name, args)
                duration = (time.time() - tool_start) * 1000
                self.stats.tool_calls_count += 1
                self.stats.tool_time += duration / 1000
                self._consecutive_errors = 0
                self._same_error_streak = 0

                self.messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": str(output)[:5000]})
                if self.on_tool_output:
                    self.on_tool_output(name, str(output)[:500], False)

                self.timeline.record_tool(name, args, str(output)[:1000], duration)
                self.events.publish(EventType.TOOL_RESULT, {"tool": name, "duration_ms": duration}, "engine")

            except Exception as e:
                self._consecutive_errors += 1
                self.stats.errors_count += 1
                if name == self._last_error_tool:
                    self._same_error_streak += 1
                else:
                    self._same_error_streak = 1
                    self._last_error_tool = name

                error_msg = f"[工具错误] {name}: {e}"
                self.messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": error_msg})
                if self.on_tool_output:
                    self.on_tool_output(name, str(e), True)

                self.timeline.record_error(str(e), name)
                self.events.publish(EventType.TOOL_ERROR, {"tool": name, "error": str(e)}, "engine")

    def run(self, user_input: str, extra_context: str = "") -> str:
        self.stats.reset()
        self.budget.reset()
        self._interrupted = False
        self._use_streaming = True
        self._install_signal_handler()

        if not self.messages:
            self.messages = [self._build_system_message()]

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
        turn = 0
        while turn < self.MAX_ITERATIONS:
            if self._interrupted or self.budget.exhausted:
                break

            turn += 1
            self.stats.turns = turn

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

            if self._same_error_streak >= STUCK_THRESHOLD:
                break

            self._auto_compress()

        return self._handle_loop_end()

    def _handle_loop_end(self) -> str:
        if self._interrupted:
            return "蒙多被中断。"
        if self._same_error_streak >= STUCK_THRESHOLD:
            return f"工具 {self._last_error_tool} 连续失败 {self._same_error_streak} 次，蒙多卡住了。"
        if self._consecutive_errors >= 5:
            return "蒙多遇到连续错误，无法继续。"

        # 追加总结
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
