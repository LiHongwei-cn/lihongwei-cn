"""蒙多上下文压缩器 — 重构版

改进：
- 更智能的压缩策略
- 性能优化
- 可配置
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class CompressionConfig:
    """压缩配置"""
    char_to_token_ratio: float = 0.4  # 中英文混合约 2.5 字符/token
    max_messages_before_compress: int = 8
    target_tokens: int = 60000
    warn_threshold_tokens: int = 70000
    keep_recent_messages: int = 8
    max_summary_length: int = 600
    max_tool_content_length: int = 500


class ContextCompressor:
    """智能上下文压缩器"""

    def __init__(self, config: Optional[CompressionConfig] = None):
        self.config = config or CompressionConfig()

    def estimate_tokens(self, messages: List[Dict]) -> int:
        """估算 token 数量"""
        total_chars = 0

        for m in messages:
            # content
            total_chars += len(m.get("content") or "")

            # tool_calls 的 arguments
            for tc in (m.get("tool_calls") or []):
                args = tc.get("function", {}).get("arguments", "")
                total_chars += len(args)

        return int(total_chars * self.config.char_to_token_ratio)

    def should_compress(self, messages: List[Dict]) -> bool:
        """检查是否需要压缩"""
        return self.estimate_tokens(messages) > self.config.warn_threshold_tokens

    def compress(self, messages: List[Dict]) -> List[Dict]:
        """智能压缩：优先压缩 tool 输出，保留对话"""
        if len(messages) <= self.config.max_messages_before_compress:
            return messages

        current_tokens = self.estimate_tokens(messages)
        if current_tokens <= self.config.target_tokens:
            return messages

        # 分离 system 消息
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
            if len(content) > self.config.max_tool_content_length:
                new_content = (
                    content[:200] +
                    f"\n... ({len(content)} 字符，已压缩) ...\n" +
                    content[-100:]
                )
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

        # 保留最近 N 条消息完整，其余压缩
        if len(all_msgs) > self.config.keep_recent_messages:
            old = all_msgs[:-self.config.keep_recent_messages]
            recent = all_msgs[-self.config.keep_recent_messages:]

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
                result.append({
                    "role": "system",
                    "content": f"[历史摘要] {summary[:self.config.max_summary_length]}"
                })

            result.extend(recent)
        else:
            result.extend(all_msgs)

        return result