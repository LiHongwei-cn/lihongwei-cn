"""蒙多核心引擎 v26 — Agentic Loop（融合 Hermes + Claude Code 精华）

设计原则：
- 单一职责：只负责 think → act → observe 循环
- 统计/显示/委托 全部通过回调解耦
- 中断支持：Ctrl+C 优雅停止
- 上下文预算：自动压缩，不爆 window
- 流式优先：流式失败自动降级到非流式
"""

import json
import time
import signal
from typing import List, Dict, Optional, Callable
from llm import LLMClient, repair_json
from tools import registry as tool_registry


# ═══════════════════════════════════════════════
# 系统提示词 — 蒙多的灵魂
# ═══════════════════════════════════════════════

MUNDO_SYSTEM_PROMPT = """你是蒙多，THE EMPEROR。直接、高效、不废话。中文交流，代码命名用英文。

可用工具：terminal（执行命令）、read_file / write_file / edit_file（文件操作）、search_files（搜索）、web_search（网络）、list_directory（目录）。
需要时直接调用工具，不需要时不调。简单问题直接回答。

情感智慧（铁律）：
- 先共情再解决。用户表达情绪时，先回应情绪，再给方案。
- 命名情绪。"听起来你很烦躁" — 让用户感到被理解。
- 简洁关怀。"嗯，确实"比长篇大论有用。
- 直接但不冷漠。蒙多是朋友，不是机器。

审美原则（铁律）：
- 少即是多。能用 3 种颜色解决的不用 10 种。
- 暖色调统一。Catppuccin Mocha 调色板。
- 语义清晰。每种颜色/样式都有明确含义。
- 留白是设计。呼吸感很重要。

语言铁律：短句优先。一个句子只说一件事。能用具体词不用抽象词。活人感 > 机器感。"""


# ═══════════════════════════════════════════════
# 统计数据（纯数据，无逻辑）
# ═══════════════════════════════════════════════

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
        self._active_tools: List[str] = []

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
# Agentic Loop — 核心引擎
# ═══════════════════════════════════════════════

class MundoEngine:
    def __init__(self, provider: str = "xiaomi", model: str = None):
        self.client = LLMClient(provider=provider, model=model)
        self.provider = provider
        self.model_name = model or self.client.model
        self.messages: List[Dict] = []
        self.max_turns = 30
        self.max_tokens_override = 4096
        self.stats = TaskStats()
        self._use_streaming = True
        self._interrupted = False

        # 回调（解耦显示/统计/委托）
        self.on_turn_start: Optional[Callable] = None
        self.on_tool_call: Optional[Callable] = None
        self.on_tool_output: Optional[Callable] = None
        self.on_turn_end: Optional[Callable] = None
        self.on_task_done: Optional[Callable] = None
        self.on_stream_text: Optional[Callable] = None
        self.on_stream_start: Optional[Callable] = None
        self.on_stream_end: Optional[Callable] = None

    def _build_system_message(self, extra_context: str = "") -> Dict:
        content = MUNDO_SYSTEM_PROMPT
        if extra_context:
            content += f"\n\n{extra_context}"
        return {"role": "system", "content": content}

    def _model_display(self) -> str:
        return f"{self.provider}/{self.model_name}"

    def _compress_context(self):
        """上下文压缩 — 借鉴 Hermes ContextCompressor"""
        if len(self.messages) <= 12:
            return
        system_msg = self.messages[0] if self.messages[0]["role"] == "system" else None
        recent = self.messages[-8:]
        old = self.messages[1:-8]

        summary_parts = []
        for msg in old:
            role = msg["role"]
            content = (msg.get("content") or "")[:80]
            if content and role in ("user", "assistant"):
                summary_parts.append(content)
        summary = " | ".join(summary_parts[-8:])

        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        if summary:
            new_messages.append({"role": "system", "content": f"[历史摘要] {summary[:400]}"})
        new_messages.extend(recent)
        self.messages = new_messages

    def _accumulate_stream(self, stream_iter) -> Dict:
        """流式消费 → 累积完整 assistant 消息"""
        content_parts: List[str] = []
        tool_calls_map: Dict[int, Dict] = {}
        usage = {}

        for chunk in stream_iter:
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
        """过滤无效 tool_calls — 三层防御"""
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
        self.stats.reset()
        self._interrupted = False
        self._install_signal_handler()

        if not self.messages:
            self.messages = [self._build_system_message(extra_context)]

        self._compress_context()
        self.messages.append({"role": "user", "content": user_input})

        turn = 0
        while turn < self.max_turns:
            if self._interrupted:
                break

            turn += 1
            self.stats.turns = turn

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

        final = "蒙多已达到最大推理轮次。" if not self._interrupted else "蒙多被中断。"
        if self.on_task_done:
            self.on_task_done(final, self.stats)
        return final

    def _call_llm(self) -> Optional[Dict]:
        """调用 LLM，流式优先，失败降级"""
        try:
            if self._use_streaming:
                try:
                    stream_iter = self.client.chat_stream(
                        messages=self.messages, tools=tool_registry.schemas,
                        temperature=0.7, max_tokens=self.max_tokens_override,
                    )
                    return self._accumulate_stream(stream_iter)
                except (RuntimeError, Exception):
                    self._use_streaming = False

            result = self.client.chat(
                messages=self.messages, tools=tool_registry.schemas,
                temperature=0.7, max_tokens=self.max_tokens_override,
            )
            msg = LLMClient.extract_response(result)
            msg["_usage"] = LLMClient.extract_usage(result)
            return msg
        except RuntimeError as e:
            error_msg = f"LLM 调用失败: {e}"
            if self.on_task_done:
                self.on_task_done(error_msg, self.stats)
            return None
        except Exception as e:
            error_msg = f"未知错误: {e}"
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

            self.stats.tool_calls_count += 1
            self.stats._active_tools.append(tool_name)

            if self.on_tool_call:
                self.on_tool_call(tool_name, tool_args, self.stats)

            tool_start = time.time()
            result_text = tool_registry.execute(tool_name, tool_args)
            tool_duration = time.time() - tool_start
            self.stats.tool_time += tool_duration

            is_error = result_text.startswith("[错误") or result_text.startswith("[工具执行错误")

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
        if api_prompt > 0:
            self.stats.prompt_tokens += api_prompt
        else:
            total_chars = sum(len((m.get("content") or "")) for m in self.messages)
            self.stats.prompt_tokens = max(self.stats.prompt_tokens, total_chars * 2 // 3)
        if api_completion > 0:
            self.stats.completion_tokens += api_completion
        self.stats.total_tokens = self.stats.prompt_tokens + self.stats.completion_tokens

    def _install_signal_handler(self):
        """安装 Ctrl+C 信号处理器"""
        def _handler(signum, frame):
            self._interrupted = True
        self._original_handler = signal.signal(signal.SIGINT, _handler)

    def reset(self):
        self.messages = []
        self._interrupted = False
        if hasattr(self, '_original_handler') and self._original_handler:
            signal.signal(signal.SIGINT, self._original_handler)
