"""蒙多上下文压缩器 — 高效版

改进：
- 单次遍历分类（不重复迭代）
- token 估算缓存（脏标记）
- 最小化内存分配
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
        self._cached_tokens: int = 0
        self._cache_dirty: bool = True

    def _count_chars(self, messages: List[Dict]) -> int:
        """单次遍历计算总字符数"""
        total = 0
        for m in messages:
            total += len(m.get("content") or "")
            for tc in (m.get("tool_calls") or []):
                total += len(tc.get("function", {}).get("arguments", ""))
        return total

    def estimate_tokens(self, messages: List[Dict]) -> int:
        """估算 token 数量（脏标记缓存）"""
        if self._cache_dirty:
            self._cached_tokens = int(
                self._count_chars(messages) * self.config.char_to_token_ratio
            )
            self._cache_dirty = False
        return self._cached_tokens

    def invalidate_cache(self):
        """手动失效缓存"""
        self._cache_dirty = True

    def should_compress(self, messages: List[Dict]) -> bool:
        """检查是否需要压缩"""
        self._cache_dirty = True  # 每次检查都刷新
        return self.estimate_tokens(messages) > self.config.warn_threshold_tokens

    def compress(self, messages: List[Dict]) -> List[Dict]:
        """智能压缩：单次遍历分类，优先压缩 tool 输出"""
        cfg = self.config
        if len(messages) <= cfg.max_messages_before_compress:
            return messages

        current_tokens = self.estimate_tokens(messages)
        if current_tokens <= cfg.target_tokens:
            return messages

        # 单次遍历分类
        system_msg = None
        user_msgs = []
        assistant_msgs = []
        tool_msgs = []
        system_seen = False

        for i, m in enumerate(messages):
            role = m["role"]
            if role == "system" and not system_seen:
                system_msg = m
                system_seen = True
            elif role == "user":
                user_msgs.append((i, m))
            elif role == "assistant":
                assistant_msgs.append((i, m))
            elif role == "tool":
                tool_msgs.append((i, m))

        # 策略1：压缩 tool 输出（最大收益）
        compressed_tools = []
        for idx, m in tool_msgs:
            content = m.get("content") or ""
            if len(content) > cfg.max_tool_content_length:
                m = {**m, "content": content[:200] + f"\n... ({len(content)} 字符，已压缩) ...\n" + content[-200:]}
            compressed_tools.append((idx, m))

        # 重新组装
        result = []
        if system_msg:
            result.append(system_msg)

        # 收集所有非 system 消息，按原始索引排序
        all_msgs = user_msgs + assistant_msgs + compressed_tools
        all_msgs.sort(key=lambda x: x[0])

        # 保留最近的消息
        if len(all_msgs) > cfg.keep_recent_messages:
            old_msgs = all_msgs[:-cfg.keep_recent_messages]
            recent_msgs = all_msgs[-cfg.keep_recent_messages:]

            # 旧消息：只保留 user 和 assistant，tool 跳过
            for idx, m in old_msgs:
                if m["role"] in ("user", "assistant"):
                    result.append(m)
            result.extend(m for _, m in recent_msgs)
        else:
            result.extend(m for _, m in all_msgs)

        self._cache_dirty = True
        return result
