"""蒙多核心引擎 v3.0.0 — Agentic Loop

融合精华：
- Hermes Agent：工具注册表、事件总线、策略引擎
- Claude Code：reasoning_effort分级、上下文压缩
- Codex CLI：沙箱隔离、并行工具执行、循环防护
- MiMo Code：模型智能路由、任务规划

v3.0.0 改进：
- 断路器集成（从llm.py）
- 模型适配器集成（国产模型优化）
- 并行工具执行改进
- 上下文压缩优化
- 流式输出稳定性提升
"""

import sys
import json
import time
import signal
from typing import List, Dict, Optional, Callable, Tuple
from llm import LLMClient, repair_json, _is_timeout_error, get_adapter
from constants import (
    VERSION, CHAR_TO_TOKEN,
    CONTEXT_MAX_TOKENS, CONTEXT_COMPRESS_THRESHOLD, CONTEXT_KEEP_RECENT,
    BUDGET_MAX_PROMPT, BUDGET_MAX_COMPLETION, BUDGET_WARN_THRESHOLD,
    STUCK_THRESHOLD, MAX_RETRY, RETRY_DELAY,
    MAX_ITERATIONS, TOOL_MAX_OUTPUT, STREAM_MAX_WAIT,
)


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
# 错误分类
# ═══════════════════════════════════════════════

def _classify_error(error: Exception, raw_msg: str) -> Dict:
    msg = raw_msg.lower()
    result = {"category": "unknown", "retryable": False, "user_tip": ""}

    if isinstance(error, (ConnectionResetError, ConnectionRefusedError, BrokenPipeError)):
        result.update(category="connection", retryable=True, user_tip="连接被中断，正在重试…")
        return result
    if any(kw in msg for kw in ["reset", "broken pipe", "eof"]):
        result.update(category="connection", retryable=True, user_tip="连接被中断，正在重试…")
        return result
    if "dns" in msg or "connection refused" in msg:
        result.update(category="network", retryable=True, user_tip="无法连接到模型服务")
        return result
    if _is_timeout_error(error) or "timeout" in msg:
        result.update(category="timeout", retryable=True, user_tip="请求超时，正在重试…")
        return result
    if any(kw in msg for kw in ["401", "unauthorized", "api key"]):
        result.update(category="auth", user_tip="API key 无效。运行 /setup 更新。")
        return result
    if any(kw in msg for kw in ["429", "rate limit"]):
        result.update(category="rate_limit", retryable=True, user_tip="请求过于频繁")
        return result
    if any(kw in msg for kw in ["500", "502", "503", "504"]):
        result.update(category="server", retryable=True, user_tip="模型服务暂时不可用")
        return result
    return result


# ═══════════════════════════════════════════════
# 引擎
# ═══════════════════════════════════════════════

class MundoEngine:

    def __init__(self, provider="deepseek", model=None):
        if model is None:
            from setup import PROVIDERS
            model = PROVIDERS.get(provider, {}).get("model", "deepseek-chat")
        self.client = LLMClient(provider=provider, model=model)
        self.provider = provider
        self.model_name = model
        self._adapter = get_adapter(provider, model)
        self.messages: List[Dict] = []
        self.max_tokens_override = 4096
        self.stats = TaskStats()
        self.budget = IterationBudget()
        self._use_streaming = self._adapter.supports_streaming
        self._interrupted = False
        self._consecutive_errors = 0

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
        return {"role": "system", "content": "你是蒙多，一个AI智能编排系统。"}

    def _model_display(self):
        return f"{self.provider}/{self.model_name}"

    def _auto_compress(self):
        if len(self.messages) < 20:
            return
        total_chars = sum(len((m.get("content") or "")) for m in self.messages)
        if total_chars < CONTEXT_MAX_TOKENS * CHAR_TO_TOKEN * CONTEXT_COMPRESS_THRESHOLD:
            return
        system_msg = self.messages[0] if self.messages[0].get("role") == "system" else None
        recent = self.messages[-CONTEXT_KEEP_RECENT:]
        old_msgs = self.messages[1:-CONTEXT_KEEP_RECENT] if len(self.messages) > CONTEXT_KEEP_RECENT + 1 else []
        summary_parts = []
        for msg in old_msgs:
            content = (msg.get("content") or "")[:100]
            if content:
                summary_parts.append(content)
        summary = " | ".join(summary_parts[-10:]) if summary_parts else "(早期对话已省略)"
        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        new_messages.append({"role": "system", "content": f"[上下文压缩] {summary[:500]}"})
        new_messages.extend(recent)
        old_count = len(self.messages)
        self.messages = new_messages
        if self.on_compress:
            self.on_compress(old_count, len(self.messages), total_chars,
                            sum(len((m.get("content") or "")) for m in self.messages))

    def _detect_reasoning_effort(self) -> Optional[str]:
        if not self._adapter.supports_reasoning:
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
                raise RuntimeError(f"流式累积超时")
            last_activity = time.time()

            delta = LLMClient.extract_stream_delta(chunk)

            if delta["content"]:
                content_parts.append(delta["content"])
                if self.on_stream_text:
                    self.on_stream_text(delta["content"])

            for tc_delta in delta["tool_calls"]:
                idx = tc_delta.get("index", 0)
                if idx not in tool_calls_map:
                    tool_calls_map[idx] = {"id": "", "type": "function",
                                           "function": {"name": "", "arguments": ""}}
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
                stream = self.client.chat_stream(messages, tools=tool_schemas,
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
            time.sleep(RETRY_DELAY * (2 ** attempt))
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

        if len(calls) > 1:
            # 并行执行独立工具调用
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=min(len(calls), 4)) as executor:
                futures = {}
                for tc, name, args in calls:
                    if self._interrupted:
                        break
                    futures[executor.submit(self._exec_single, tc, name, args, tool_module)] = (tc, name, args)
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        pass
        else:
            for tc, name, args in calls:
                if self._interrupted:
                    break
                self._exec_single(tc, name, args, tool_module)

    def _exec_single(self, tc, name: str, args: dict, tool_module):
        if self.on_tool_call:
            self.on_tool_call(name, args, self.stats)

        tool_start = time.time()
        LONG_TIMEOUT_TOOLS = {"delegate_agent"}
        timeout = 600 if name in LONG_TIMEOUT_TOOLS else 30

        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(tool_module.execute_tool, name, args)
                try:
                    output = future.result(timeout=timeout)
                except FutureTimeout:
                    output = f"[工具 {name} 执行超时]"
                    future.cancel()

            duration = (time.time() - tool_start) * 1000
            self.stats.tool_time += duration / 1000
            self.stats.tool_calls_count += 1

            is_error = isinstance(output, str) and output.startswith("[") and "错误" in output
            if self.on_tool_output:
                self.on_tool_output(name, output, is_error)

            self.messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": str(output)[:TOOL_MAX_OUTPUT],
            })

        except Exception as e:
            self.messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": f"[工具执行异常: {e}]",
            })

    def run(self, user_input: str) -> str:
        self._interrupted = False
        self._use_streaming = self._adapter.supports_streaming

        if not self.messages:
            self.messages.append(self._build_system_message())
        self.messages.append({"role": "user", "content": user_input})

        for iteration in range(MAX_ITERATIONS):
            if self._interrupted or self.budget.exhausted:
                break

            if self.on_turn_start:
                self.on_turn_start(self.stats.turns, self.stats)

            self._auto_compress()

            llm_start = time.time()
            response = self._call_llm()
            self.stats.llm_time += time.time() - llm_start

            if not response:
                break

            self.stats.turns += 1
            self.messages.append(response)
            self._update_token_stats(response)

            if self.on_turn_end:
                self.on_turn_end(self.stats.turns, self.stats)

            tool_calls = response.get("tool_calls", [])
            tool_calls = self._filter_tool_calls(tool_calls)

            if tool_calls:
                self._execute_tool_calls(tool_calls)
            else:
                content = response.get("content", "")
                if self.on_task_done:
                    self.on_task_done(content, self.stats)
                return content

        # 超出迭代限制，提取最后一条有内容的回复
        for msg in reversed(self.messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                return msg["content"]
        return "[任务未完成]"
