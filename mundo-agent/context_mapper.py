"""蒙多上下文分块映射 v2.0.8 — 皇帝的奏折管理

智能上下文窗口管理。不是简单的截断，是语义感知的分块。
每个消息块有优先级、类型、新鲜度。淘汰时按优先级排序。

设计哲学：
- 用户消息 > assistant 回复 > tool 输出 > 系统消息
- 新消息 > 旧消息
- 有标记的 > 无标记的
- 压缩 tool 输出，保留对话
"""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Tuple, Any


class ChunkType(Enum):
    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()
    TOOL_CALL = auto()
    TOOL_RESULT = auto()
    SUMMARY = auto()
    INJECTED = auto()  # 注入的记忆/上下文


class EvictionPriority(Enum):
    """淘汰优先级，值越大越容易被淘汰"""
    KEEP_FOREVER = 0      # system prompt
    KEEP_RECENT = 10      # 最近的对话
    COMPRESS_FIRST = 20   # tool 输出，先压缩
    EVICT_FIRST = 30      # 旧的注入内容，先淘汰


@dataclass
class Chunk:
    content: str
    chunk_type: ChunkType
    token_estimate: int = 0
    priority: EvictionPriority = EvictionPriority.EVICT_FIRST
    turn_id: str = ""
    timestamp: float = field(default_factory=time.time)
    compressed: bool = False
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if self.token_estimate == 0:
            self.token_estimate = self._estimate_tokens(self.content)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return int(len(text) * 0.4)


@dataclass
class ContextBudget:
    max_tokens: int = 128000
    system_reserve: int = 4000
    response_reserve: int = 8000
    safety_margin: int = 2000

    @property
    def usable_tokens(self) -> int:
        return max(1000, self.max_tokens - self.system_reserve - self.response_reserve - self.safety_margin)


class ContextMapper:
    """语义感知的上下文分块管理器"""

    def __init__(self, budget: Optional[ContextBudget] = None):
        self._budget = budget or ContextBudget()
        self._chunks: List[Chunk] = []
        self._compress_threshold = 0.7

    @property
    def total_tokens(self) -> int:
        return sum(c.token_estimate for c in self._chunks)

    @property
    def usage_ratio(self) -> float:
        return self.total_tokens / self._budget.usable_tokens

    def add(self, content: str, chunk_type: ChunkType,
            priority: EvictionPriority = EvictionPriority.EVICT_FIRST,
            turn_id: str = "", metadata: Dict = None) -> Chunk:
        chunk = Chunk(
            content=content,
            chunk_type=chunk_type,
            priority=priority,
            turn_id=turn_id,
            metadata=metadata or {},
        )
        self._chunks.append(chunk)
        return chunk

    def add_user(self, content: str, turn_id: str = "") -> Chunk:
        return self.add(content, ChunkType.USER, EvictionPriority.KEEP_RECENT, turn_id)

    def add_assistant(self, content: str, turn_id: str = "") -> Chunk:
        return self.add(content, ChunkType.ASSISTANT, EvictionPriority.KEEP_RECENT, turn_id)

    def add_tool_result(self, content: str, tool_name: str = "",
                        turn_id: str = "") -> Chunk:
        return self.add(content, ChunkType.TOOL_RESULT, EvictionPriority.COMPRESS_FIRST,
                        turn_id, {"tool": tool_name})

    def add_system(self, content: str) -> Chunk:
        return self.add(content, ChunkType.SYSTEM, EvictionPriority.KEEP_FOREVER)

    def inject(self, content: str, source: str = "") -> Chunk:
        return self.add(content, ChunkType.INJECTED, EvictionPriority.EVICT_FIRST,
                        metadata={"source": source})

    def should_compress(self) -> bool:
        return self.usage_ratio > self._compress_threshold

    def compress(self, target_ratio: float = 0.5) -> Tuple[int, int]:
        """智能压缩：先压缩 tool 输出，再淘汰旧注入内容"""
        old_tokens = self.total_tokens
        target_tokens = int(self._budget.usable_tokens * target_ratio)

        if self.total_tokens <= target_tokens:
            return old_tokens, self.total_tokens

        # 策略1：压缩 tool 输出
        for chunk in self._chunks:
            if chunk.compressed:
                continue
            if chunk.chunk_type == ChunkType.TOOL_RESULT and chunk.token_estimate > 200:
                original = chunk.content
                chunk.content = (
                    original[:200]
                    + f"\n... ({len(original)} 字符，已压缩) ...\n"
                    + original[-100:]
                )
                chunk.token_estimate = Chunk._estimate_tokens(chunk.content)
                chunk.compressed = True
                chunk.priority = EvictionPriority.EVICT_FIRST
                if self.total_tokens <= target_tokens:
                    return old_tokens, self.total_tokens

        # 策略2：淘汰旧的注入内容
        self._chunks = [
            c for c in self._chunks
            if not (c.chunk_type == ChunkType.INJECTED and c.priority == EvictionPriority.EVICT_FIRST)
        ]
        if self.total_tokens <= target_tokens:
            return old_tokens, self.total_tokens

        # 策略3：摘要旧对话
        recent_chunks = self._get_recent(8)
        old_chunks = [c for c in self._chunks if c not in recent_chunks]
        if old_chunks:
            summary_parts = []
            for c in old_chunks:
                if c.chunk_type in (ChunkType.USER, ChunkType.ASSISTANT):
                    summary_parts.append(f"[{c.chunk_type.name}] {c.content[:80]}")
            if summary_parts:
                summary = " | ".join(summary_parts[-10:])
                summary_chunk = Chunk(
                    content=f"[历史摘要] {summary[:600]}",
                    chunk_type=ChunkType.SUMMARY,
                    priority=EvictionPriority.EVICT_FIRST,
                )
                self._chunks = [summary_chunk] + recent_chunks

        return old_tokens, self.total_tokens

    def to_messages(self) -> List[Dict[str, str]]:
        """转换为 LLM 消息格式"""
        messages = []
        for chunk in self._chunks:
            role_map = {
                ChunkType.SYSTEM: "system",
                ChunkType.USER: "user",
                ChunkType.ASSISTANT: "assistant",
                ChunkType.TOOL_RESULT: "tool",
                ChunkType.TOOL_CALL: "assistant",
                ChunkType.SUMMARY: "system",
                ChunkType.INJECTED: "system",
            }
            role = role_map.get(chunk.chunk_type, "system")
            messages.append({"role": role, "content": chunk.content})
        return messages

    def _get_recent(self, count: int) -> List[Chunk]:
        return self._chunks[-count:] if len(self._chunks) > count else self._chunks

    def snapshot(self) -> Dict:
        by_type = {}
        for c in self._chunks:
            t = c.chunk_type.name
            if t not in by_type:
                by_type[t] = {"count": 0, "tokens": 0}
            by_type[t]["count"] += 1
            by_type[t]["tokens"] += c.token_estimate

        return {
            "total_chunks": len(self._chunks),
            "total_tokens": self.total_tokens,
            "usage_ratio": f"{self.usage_ratio:.1%}",
            "by_type": by_type,
        }
