"""蒙多核心引擎 v29 — Agentic Loop（融合 Hermes + Claude Code 精华）

v27 改进（vs v26）：
- IterationBudget：per-turn + 总量 token 预算控制（借鉴 Hermes）
- 智能上下文压缩：优先压缩 tool 输出，保留 user/assistant 对话
- 错误重试：LLM 调用失败自动重试 + 指数退避
- 自动压缩触发：上下文 >70% 时自动压缩
- 工具失败反馈：错误信息包含修复建议
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

工具使用原则：
- 读文件前先 search_files 定位，不要盲目读大文件
- terminal 命令失败时，先分析错误信息再重试，不要重复同样的命令
- 多个独立操作可以并行执行（在同一个 response 中调用多个工具）
- 工具输出过大时，用更精确的参数缩小范围

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
# IterationBudget — 借鉴 Hermes 预算控制
# ═══════════════════════════════════════════════

class IterationBudget:
    """Token 预算控制 — 防止无限循环和资源浪费"""

    def __init__(self, max_prompt_tokens: int = 100000,
                 max_completion_tokens: int = 50000,
                 max_turns: int = 30,
                 warn_threshold: float = 0.7):
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
        if self.max_prompt_tokens == 0:
            return 0
        return self.prompt_tokens_used / self.max_prompt_tokens

    @property
    def should_warn(self) -> bool:
        return self.usage_ratio >= self.warn_threshold and not self._warned

    @property
    def exhausted(self) -> bool:
        return (self.prompt_tokens_used >= self.max_prompt_tokens or
                self.completion_tokens_used >= self.max_completion_tokens or
                self.turns_used >= self.max_turns)

    def update(self, prompt_tokens: int = 0, completion_tokens: int = 0):
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
        self.errors_count = 0
        self.retries_count = 0

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
# 上下文压缩器 — 智能压缩（借鉴 Hermes ContextCompressor）
# ═══════════════════════════════════════════════

class ContextCompressor:
    """智能上下文压缩 — 优先压缩 tool 输出，保留对话"""

    # 上下文窗口估算（字符 → token 比率）
    CHAR_TO_TOKEN = 0.4  # 中英文混合约 2.5 字符/token

    @staticmethod
    def estimate_tokens(messages: List[Dict]) -> int:
        total_chars = sum(len(m.get("content") or "") for m in messages)
        # tool_calls 的 arguments 也占 token
        for m in messages:
            for tc in (m.get("tool_calls") or []):
                args = tc.get("function", {}).get("arguments", "")
                total_chars += len(args)
        return int(total_chars * ContextCompressor.CHAR_TO_TOKEN)

    @staticmethod
    def compress(messages: List[Dict], target_tokens: int = 60000) -> List[Dict]:
        """智能压缩：优先压缩 tool 输出，保留 user/assistant 对话"""
        if len(messages) <= 8:
            return messages

        current_tokens = ContextCompressor.estimate_tokens(messages)
        if current_tokens <= target_tokens:
            return messages

        system_msg = None
        rest = []
        for m in messages:
            if m["role"] == "system" and system_msg is None:
                system_msg = m
            else:
                rest.append(m)

        # 分类消息（保留原始索引）
        indexed_rest = list(enumerate(rest))
        user_msgs = [(i, m) for i, m in indexed_rest if m["role"] == "user"]
        assistant_msgs = [(i, m) for i, m in indexed_rest if m["role"] == "assistant"]
        tool_msgs = [(i, m) for i, m in indexed_rest if m["role"] == "tool"]

        # 策略1：压缩 tool 输出（最大收益）
        compressed_tools = []
        for idx, m in tool_msgs:
            content = m.get("content") or ""
            if len(content) > 500:
                new_content = content[:200] + f"\n... ({len(content)} 字符，已压缩) ...\n" + content[-100:]
                compressed_tools.append((idx, {**m, "content": new_content}))
            else:
                compressed_tools.append((idx, m))

        # 合并所有消息并按原始索引排序
        all_indexed = user_msgs + assistant_msgs + compressed_tools
        all_indexed.sort(key=lambda x: x[0])
        all_msgs = [m for _, m in all_indexed]

        # 重建消息列表
        result = []
        if system_msg:
            result.append(system_msg)

        # 保留最近 8 条消息完整，其余压缩
        if len(all_msgs) > 8:
            old = all_msgs[:-8]
            recent = all_msgs[-8:]

            # 从旧消息中提取摘要
            summary_parts = []
            for m in old:
                role = m["role"]
                content = (m.get("content") or "")[:100]
                if content and role in ("user", "assistant"):
                    summary_parts.append(f"[{role}] {content}")
                elif content and role == "tool":
                    summary_parts.append(f"[tool:{m.get('tool_call_id', '?')[:8]}] {content[:60]}")

            if summary_parts:
                summary = " | ".join(summary_parts[-10:])
                result.append({"role": "system", "content": f"[历史摘要] {summary[:600]}"})

            result.extend(recent)
        else:
            result.extend(all_msgs)

        return result

    @staticmethod
    def should_compress(messages: List[Dict], threshold_tokens: int = 70000) -> bool:
        """检查是否需要压缩"""
        return ContextCompressor.estimate_tokens(messages) > threshold_tokens


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
        self.budget = IterationBudget(max_turns=self.max_turns)
        self._use_streaming = True
        self._interrupted = False
        self._consecutive_errors = 0  # 连续工具错误计数
        self._last_error_tool = ""  # 上一次出错的工具名
        self._same_error_streak = 0  # 同一工具连续错误次数
        self._stuck_threshold = 3  # 连续 3 次同样错误 → 强制跳出
        self._last_activity_time = time.time()  # 最后活动时间
        self._idle_timeout = 300  # 5 分钟无活动 → 警告

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

    def _build_system_message(self) -> Dict:
        """构建系统消息 — 保持稳定以提高缓存命中率"""
        return {"role": "system", "content": MUNDO_SYSTEM_PROMPT}

    def _model_display(self) -> str:
        return f"{self.provider}/{self.model_name}"

    def _auto_compress(self):
        """自动压缩 — 借鉴 Hermes，在接近窗口限制时自动触发"""
        if not ContextCompressor.should_compress(self.messages):
            return

        old_count = len(self.messages)
        old_tokens = ContextCompressor.estimate_tokens(self.messages)

        self.messages = ContextCompressor.compress(self.messages)

        new_count = len(self.messages)
        new_tokens = ContextCompressor.estimate_tokens(self.messages)

        if self.on_compress:
            self.on_compress(old_count, new_count, old_tokens, new_tokens)

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
                raise RuntimeError(f"流式累积超时（{ACCUMULATE_TIMEOUT}s）")
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
        self.budget.reset()
        self._interrupted = False
        self._use_streaming = True  # 每次任务重新尝试流式
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
        while turn < self.max_turns:
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

        if self._interrupted:
            final = "蒙多被中断。"
        elif self._consecutive_errors >= 5:
            final = "蒙多遇到连续错误，无法继续。请检查任务描述或换个方式提问。"
        else:
            final = "蒙多已达到最大推理轮次。"
        if self.on_task_done:
            self.on_task_done(final, self.stats)
        return final

    def _call_llm(self, max_retries: int = 2) -> Optional[Dict]:
        """调用 LLM，流式优先，失败降级，自动重试（含总超时）"""
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
                            messages=self.messages, tools=tool_registry.schemas,
                            temperature=0.7, max_tokens=self.max_tokens_override,
                        )
                        return self._accumulate_stream(stream_iter)
                    except (RuntimeError, Exception) as e:
                        if attempt == 0:
                            self._use_streaming = False
                            last_error = str(e)
                            # 静默降级，不打扰用户
                            continue
                        raise

                result = self.client.chat(
                    messages=self.messages, tools=tool_registry.schemas,
                    temperature=0.7, max_tokens=self.max_tokens_override,
                )
                msg = LLMClient.extract_response(result)
                msg["_usage"] = LLMClient.extract_usage(result)
                return msg

            except RuntimeError as e:
                last_error = str(e)
                # 上下文溢出 → 自动压缩重试
                if "context" in last_error.lower() or "too long" in last_error.lower():
                    self.messages = ContextCompressor.compress(
                        self.messages, target_tokens=40000
                    )
                    self.stats.retries_count += 1
                    continue
                # 429/5xx → 重试
                if any(code in last_error for code in ["429", "500", "502", "503"]):
                    time.sleep(2 ** attempt)
                    self.stats.retries_count += 1
                    continue
                break
            except Exception as e:
                last_error = str(e)
                break

        if last_error is None:
            last_error = "LLM 返回空响应"
        error_msg = f"LLM 调用失败: {last_error}"
        self.stats.errors_count += 1
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

            if is_error:
                self.stats.errors_count += 1

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
        """更新 token 统计 — 提取 cached_tokens"""
        usage = assistant_msg.get("_usage") or {}
        api_prompt = usage.get("prompt_tokens", 0)
        api_completion = usage.get("completion_tokens", 0)

        # 提取缓存命中 tokens（OpenAI 格式：usage.prompt_tokens_details.cached_tokens）
        cached_tokens = 0
        details = usage.get("prompt_tokens_details") or usage.get("prompt_tokens")
        if isinstance(details, dict):
            cached_tokens = details.get("cached_tokens", 0)
        # 某些 provider 直接放在 usage 顶层
        if not cached_tokens:
            cached_tokens = usage.get("cache_read_input_tokens", 0) or usage.get("cached_tokens", 0)

        if api_prompt > 0:
            self.stats.prompt_tokens += api_prompt
        else:
            total_chars = sum(len((m.get("content") or "")) for m in self.messages)
            self.stats.prompt_tokens = max(self.stats.prompt_tokens, total_chars * 2 // 3)
        if api_completion > 0:
            self.stats.completion_tokens += api_completion
        self.stats.total_tokens = self.stats.prompt_tokens + self.stats.completion_tokens

        # 更新预算
        self.budget.update(api_prompt, api_completion)

        # 通知 UI 层 token 统计
        if self.on_llm_stats:
            total_context = ContextCompressor.estimate_tokens(self.messages)
            self.on_llm_stats(api_prompt, api_completion, cached_tokens, total_context)

    def _install_signal_handler(self):
        """安装 Ctrl+C 信号处理器"""
        def _handler(signum, frame):
            self._interrupted = True
        self._original_handler = signal.signal(signal.SIGINT, _handler)

    def reset(self):
        self.messages = []
        self._interrupted = False
        self.budget.reset()
        if hasattr(self, '_original_handler') and self._original_handler:
            signal.signal(signal.SIGINT, self._original_handler)
