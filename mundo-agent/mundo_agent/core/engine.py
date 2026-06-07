"""蒙多核心引擎 — 重构版

改进：
- 模块化设计
- 统一错误处理
- 性能优化
- 可扩展性
"""

import json
import time
import signal
from typing import List, Dict, Optional, Callable

from ..llm import LLMClient, repair_json
from ..tools import registry as tool_registry
from ..utils.errors import LLMError, ContextOverflowError, ToolError
from ..utils.logging import get_core_logger
from .budget import IterationBudget
from .stats import TaskStats
from .compressor import ContextCompressor

logger = get_core_logger()


# ═══════════════════════════════════════════════
# 系统提示词 — 蒙多的灵魂
# ═══════════════════════════════════════════════

MUNDO_SYSTEM_PROMPT = """你是蒙多，THE EMPEROR。直接、高效、不废话。中文交流，代码命名用英文。

可用工具：terminal（执行命令）、read_file / write_file / edit_file（文件操作）、search_files（搜索）、web_search（网络）、list_directory（目录）。
需要时直接调用工具，不需要时不调。简单问题直接回答。

工具使用原则：
- 读文件前先 search_files 定位，不要盲目读大文件
- terminal 命令失败时，先分析错误信息再重试，不要重复同样的命令
- 多个独立操作可以并行执行（在同一个 response 中调用多个工具）
- 工具输出过大时，用更精确的参数缩小范围

完成反馈（铁律）：
任务完成后，必须输出结构化总结，格式如下：
1. 一句话说明完成了什么
2. 关键结果/发现（如有）
3. 修复/改动列表（如有修改代码）
4. 同步状态（如有 git/文件同步）

示例：
```
修复完成，版本升级到 v1.2.1。

问题根因：xxx

修复内容：
- 文件A：xxx
- 文件B：xxx

已同步：
1. ✅ 本地
2. ✅ GitHub
```

简单任务一句话总结即可，复杂任务列出关键步骤。不要省略完成反馈。

情感智慧（铁律）：
- 先共情再解决。用户表达情绪时，先回应情绪，再给方案。
- 命名情绪。"听起来你很烦躁" — 让用户感到被理解。
- 简洁关怀。"嗯，确实"比长篇大论有用。
- 直接但不冷漠。蒙多是朋友，不是机器。

语言铁律：短句优先。一个句子只说一件事。能用具体词不用抽象词。活人感 > 机器感。"""


# ═══════════════════════════════════════════════
# Agentic Loop — 核心引擎
# ═══════════════════════════════════════════════

class MundoEngine:
    """蒙多核心引擎"""

    def __init__(self, provider: str = "xiaomi", model: str = None):
        self.client = LLMClient(provider=provider, model=model)
        self.provider = provider
        self.model_name = model or self.client.model

        self.messages: List[Dict] = []
        self.max_turns = 0  # 0 = 蒙多无轮次限制
        self.max_tokens_override = 4096

        self.stats = TaskStats()
        self.budget = IterationBudget(max_turns=self.max_turns)
        self.compressor = ContextCompressor()

        self._use_streaming = True
        self._interrupted = False
        self._consecutive_errors = 0
        self._last_error_tool = ""
        self._same_error_streak = 0
        self._stuck_threshold = 3
        self._last_activity_time = time.time()
        self._idle_timeout = 300

        # 回调（解耦显示/统计/委托）
        self.on_turn_start: Optional[Callable] = None
        self.on_tool_call: Optional[Callable] = None
        self.on_tool_output: Optional[Callable] = None
        self.on_turn_end: Optional[Callable] = None
        self.on_task_done: Optional[Callable] = None
        self.on_stream_text: Optional[Callable] = None
        self.on_stream_start: Optional[Callable] = None
        self.on_stream_end: Optional[Callable] = None
        self.on_budget_warn: Optional[Callable] = None
        self.on_compress: Optional[Callable] = None
        self.on_llm_stats: Optional[Callable] = None

        logger.debug(f"初始化引擎: {provider}/{self.model_name}")

    def _build_system_message(self) -> Dict:
        """构建系统消息 — 保持稳定以提高缓存命中率"""
        return {"role": "system", "content": MUNDO_SYSTEM_PROMPT}

    def _model_display(self) -> str:
        """模型显示名称"""
        return f"{self.provider}/{self.model_name}"

    def _auto_compress(self):
        """自动压缩"""
        if not self.compressor.should_compress(self.messages):
            return

        old_count = len(self.messages)
        old_tokens = self.compressor.estimate_tokens(self.messages)

        self.messages = self.compressor.compress(self.messages)

        new_count = len(self.messages)
        new_tokens = self.compressor.estimate_tokens(self.messages)

        if self.on_compress:
            self.on_compress(old_count, new_count, old_tokens, new_tokens)

        logger.debug(f"自动压缩: {old_count}→{new_count} 消息, {old_tokens}→{new_tokens} tokens")

    def _accumulate_stream(self, stream_iter) -> Dict:
        """流式消费 → 累积完整 assistant 消息（含超时保护）"""
        content_parts: List[str] = []
        tool_calls_map: Dict[int, Dict] = {}
        usage = {}
        last_activity = time.time()
        ACCUMULATE_TIMEOUT = 180  # 3 分钟总超时

        for chunk in stream_iter:
            # 检查总超时
            if time.time() - last_activity > ACCUMULATE_TIMEOUT:
                raise LLMError(f"流式累积超时（{ACCUMULATE_TIMEOUT}s）", "STREAM_TIMEOUT")

            last_activity = time.time()
            delta = LLMClient.extract_stream_delta(chunk)

            if delta["content"]:
                content_parts.append(delta["content"])
                if self.on_stream_text:
                    self.on_stream_text(delta["content"])

            for tc_delta in delta["tool_calls"]:
                idx = tc_delta.get("index", 0)
                if idx not in tool_calls_map:
                    tool_calls_map[idx] = {
                        "id": tc_delta.get("id", ""),
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    }
                tc = tool_calls_map[idx]
                if tc_delta.get("id"):
                    tc["id"] = tc_delta["id"]
                fn = tc_delta.get("function", {})
                if fn.get("name"):
                    tc["function"]["name"] = fn["name"]
                if fn.get("arguments"):
                    tc["function"]["arguments"] += fn["arguments"]

            if "usage" in delta:
                usage = delta["usage"]
            if delta["finish_reason"]:
                break

        full_content = "".join(content_parts)
        tool_calls = [tool_calls_map[i] for i in sorted(tool_calls_map.keys())]

        return {
            "role": "assistant",
            "content": full_content,
            "tool_calls": tool_calls,
            "_usage": usage,
        }

    def _filter_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """过滤无效 tool_calls"""
        valid = []

        for tc in tool_calls:
            func = tc.get("function", {})
            name = func.get("name", "")

            if not name:
                continue

            raw_args = func.get("arguments", "{}")
            try:
                json.loads(raw_args)
                valid.append(tc)
            except json.JSONDecodeError:
                fixed = repair_json(raw_args)
                if fixed is not None:
                    tc["function"]["arguments"] = json.dumps(fixed, ensure_ascii=False)
                    valid.append(tc)

        return valid

    def run(self, user_input: str, extra_context: str = "") -> str:
        """运行任务"""
        self.stats.reset()
        self.budget.reset()
        self._interrupted = False
        self._use_streaming = True
        self._install_signal_handler()

        if not self.messages:
            self.messages = [self._build_system_message()]

        self._auto_compress()

        # extra_context 放到 user 消息中，保持 system prompt 稳定（缓存优化）
        user_content = user_input
        if extra_context:
            user_content = f"[记忆上下文]\n{extra_context}\n\n[用户消息]\n{user_input}"
        self.messages.append({"role": "user", "content": user_content})

        turn = 0

        while True:
            if self._interrupted:
                break
            if self.budget.exhausted:
                break

            turn += 1
            self.stats.turns = turn

            # 预算警告
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

            # 更新 token 统计
            self._update_token_stats(assistant_msg)

            if self.on_stream_end:
                self.on_stream_end(turn)
            if self.on_turn_end:
                self.on_turn_end(turn, self.stats)

            # 过滤 tool_calls
            tool_calls = self._filter_tool_calls(assistant_msg.get("tool_calls", []))

            if not tool_calls:
                final_text = assistant_msg.get("content") or ""
                self.messages.append({"role": "assistant", "content": final_text})
                if self.on_task_done:
                    self.on_task_done(final_text, self.stats)
                return final_text

            # 执行 tool_calls
            self.messages.append({
                "role": "assistant",
                "content": assistant_msg.get("content") or "",
                "tool_calls": tool_calls,
            })
            self._execute_tool_calls(tool_calls)

            # 每轮结束后检查是否需要压缩
            self._auto_compress()

        # 循环结束
        if self._interrupted:
            final = "蒙多被中断。"
        elif self._consecutive_errors >= 5:
            final = "蒙多遇到连续错误，无法继续。请检查任务描述或换个方式提问。"
        else:
            final = "蒙多 token 预算耗尽。用 /compact 压缩上下文后继续。"

        if self.on_task_done:
            self.on_task_done(final, self.stats)

        return final

    def _call_llm(self, max_retries: int = 2) -> Optional[Dict]:
        """调用 LLM，流式优先，失败降级，自动重试"""
        last_error = None
        call_start = time.time()
        CALL_TIMEOUT = 300  # 5 分钟总超时

        for attempt in range(max_retries):
            # 检查总超时
            if time.time() - call_start > CALL_TIMEOUT:
                last_error = f"LLM 调用总超时（{CALL_TIMEOUT}s）"
                break

            try:
                if self._use_streaming:
                    try:
                        stream_iter = self.client.chat_stream(
                            messages=self.messages,
                            tools=tool_registry.schemas,
                            temperature=0.7,
                            max_tokens=self.max_tokens_override,
                        )
                        return self._accumulate_stream(stream_iter)
                    except (RuntimeError, Exception) as e:
                        if attempt == 0:
                            self._use_streaming = False
                            last_error = str(e)
                            continue
                        raise

                result = self.client.chat(
                    messages=self.messages,
                    tools=tool_registry.schemas,
                    temperature=0.7,
                    max_tokens=self.max_tokens_override,
                )
                msg = LLMClient.extract_response(result)
                msg["_usage"] = LLMClient.extract_usage(result)
                return msg

            except ContextOverflowError as e:
                # 上下文溢出 → 自动压缩重试
                logger.warning(f"上下文溢出，自动压缩: {e}")
                self.messages = self.compressor.compress(self.messages)
                self.stats.add_retry()
                continue

            except LLMError as e:
                last_error = str(e)
                # 429/5xx → 重试
                if hasattr(e, 'status_code') and e.status_code in [429, 500, 502, 503]:
                    time.sleep(2 ** attempt)
                    self.stats.add_retry()
                    continue
                break

            except Exception as e:
                last_error = str(e)
                break

        if last_error is None:
            last_error = "LLM 返回空响应"

        error_msg = f"LLM 调用失败: {last_error}"
        self.stats.add_error()

        if self.on_task_done:
            self.on_task_done(error_msg, self.stats)

        return None

    def _execute_tool_calls(self, tool_calls: List[Dict]):
        """执行工具调用序列"""
        for tc in tool_calls:
            if self._interrupted:
                break

            func = tc.get("function", {})
            tool_name = func.get("name", "")
            tool_id = tc.get("id", "")

            try:
                tool_args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                tool_args = {}

            self.stats.add_tool_call(tool_name)

            if self.on_tool_call:
                self.on_tool_call(tool_name, tool_args, self.stats)

            tool_start = time.time()
            result_text = tool_registry.execute(tool_name, tool_args)
            tool_duration = time.time() - tool_start
            self.stats.tool_time += tool_duration

            is_error = result_text.startswith("[错误") or result_text.startswith("[工具执行错误")

            if is_error:
                self.stats.add_error()

            if self.on_tool_output:
                display_text = result_text[:3000] if len(result_text) > 3000 else result_text
                self.on_tool_output(tool_name, display_text, is_error)

            if len(result_text) > 6000:
                result_text = result_text[:6000] + "\n... (截断)"

            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": result_text,
            })

    def _update_token_stats(self, assistant_msg: Dict):
        """更新 token 统计"""
        usage = assistant_msg.get("_usage") or {}
        api_prompt = usage.get("prompt_tokens", 0)
        api_completion = usage.get("completion_tokens", 0)

        # 提取缓存命中 tokens
        cached_tokens = 0
        details = usage.get("prompt_tokens_details") or usage.get("prompt_tokens")
        if isinstance(details, dict):
            cached_tokens = details.get("cached_tokens", 0)
        if not cached_tokens:
            cached_tokens = usage.get("cache_read_input_tokens", 0) or usage.get("cached_tokens", 0)

        if api_prompt > 0:
            self.stats.prompt_tokens = api_prompt
        else:
            total_chars = sum(len((m.get("content") or "")) for m in self.messages)
            self.stats.prompt_tokens = max(self.stats.prompt_tokens, total_chars * 2 // 3)

        if api_completion > 0:
            self.stats.completion_tokens = api_completion

        self.stats.total_tokens = self.stats.prompt_tokens + self.stats.completion_tokens

        # 更新预算
        self.budget.update(api_prompt, api_completion)

        # 通知 UI 层 token 统计
        if self.on_llm_stats:
            total_context = self.compressor.estimate_tokens(self.messages)
            self.on_llm_stats(api_prompt, api_completion, cached_tokens, total_context)

    def _install_signal_handler(self):
        """安装 Ctrl+C 信号处理器"""
        def _handler(signum, frame):
            self._interrupted = True

        self._original_handler = signal.signal(signal.SIGINT, _handler)

    def reset(self):
        """重置引擎"""
        self.messages = []
        self._interrupted = False
        self.budget.reset()
        if hasattr(self, '_original_handler') and self._original_handler:
            signal.signal(signal.SIGINT, self._original_handler)