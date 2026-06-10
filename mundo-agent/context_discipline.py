"""上下文纪律 — 从 Codex 上下文管理提炼

硬限制规则：
1. 每项注入 ≤ MAX_ITEM_TOKENS（默认10K）
2. 总注入项数 ≤ MAX_ITEMS
3. 历史不可重写（只追加）
4. 超限项自动截断或丢弃
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


MAX_ITEM_TOKENS = 10000
MAX_ITEMS = 50
CHAR_TO_TOKEN = 3.5  # 中文约3.5字符/token


class ChunkType(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MEMORY = "memory"
    CONTEXT = "context"


@dataclass
class ContextItem:
    content: str
    chunk_type: ChunkType
    source: str = ""
    priority: int = 50
    tokens: int = 0
    truncated: bool = False

    def __post_init__(self):
        if self.tokens == 0:
            self.tokens = int(len(self.content) / CHAR_TO_TOKEN)


@dataclass
class DisciplineReport:
    total_items: int = 0
    accepted: int = 0
    truncated: int = 0
    dropped: int = 0
    total_tokens: int = 0
    warnings: List[str] = field(default_factory=list)


class ContextDiscipline:
    """上下文纪律执行器"""

    def __init__(
        self,
        max_item_tokens: int = MAX_ITEM_TOKENS,
        max_items: int = MAX_ITEMS,
    ):
        self._max_item_tokens = max_item_tokens
        self._max_items = max_items
        self._history_hash: Optional[str] = None

    def enforce(self, items: List[ContextItem]) -> Tuple[List[ContextItem], DisciplineReport]:
        """对注入项执行纪律检查，返回（合规项，报告）"""
        report = DisciplineReport(total_items=len(items))
        accepted = []

        for item in items:
            # 规则1：单项token限制
            if item.tokens > self._max_item_tokens:
                item = self._truncate_item(item)
                report.truncated += 1
                report.warnings.append(
                    f"[上下文纪律] {item.source or item.chunk_type.value} 超限截断：{item.tokens}→{self._max_item_tokens} tokens"
                )

            # 规则2：总项数限制
            if len(accepted) >= self._max_items:
                report.dropped += 1
                report.warnings.append(
                    f"[上下文纪律] 丢弃 {item.source or item.chunk_type.value}（超出{self._max_items}项限制）"
                )
                continue

            accepted.append(item)
            report.total_tokens += item.tokens

        report.accepted = len(accepted)
        return accepted, report

    def validate_no_rewrite(self, old_messages: List[Dict], new_messages: List[Dict]) -> bool:
        """验证历史未被重写（只追加原则）

        old_messages 必须是 new_messages 的前缀。
        """
        if not old_messages:
            return True
        if len(new_messages) < len(old_messages):
            return False
        for i, old_msg in enumerate(old_messages):
            new_msg = new_messages[i]
            if old_msg.get("role") != new_msg.get("role"):
                return False
            if old_msg.get("content") != new_msg.get("content"):
                return False
        return True

    def check_history_integrity(self, messages: List[Dict]) -> bool:
        """检查消息历史完整性（无空洞、角色交替合理）"""
        if not messages:
            return True
        for i, msg in enumerate(messages):
            if not msg.get("role"):
                return False
            # system 只能在开头
            if msg["role"] == "system" and i > 0:
                return False
        return True

    def _truncate_item(self, item: ContextItem) -> ContextItem:
        """截断超限项到 max_item_tokens"""
        max_chars = int(self._max_item_tokens * CHAR_TO_TOKEN)
        truncated_content = item.content[:max_chars] + "\n[...截断...]"
        return ContextItem(
            content=truncated_content,
            chunk_type=item.chunk_type,
            source=item.source,
            priority=item.priority,
            tokens=self._max_item_tokens,
            truncated=True,
        )

    def estimate_tokens(self, text: str) -> int:
        return int(len(text) / CHAR_TO_TOKEN)

    def budget_report(self, items: List[ContextItem]) -> Dict[str, Any]:
        """生成预算报告"""
        by_type = {}
        for item in items:
            key = item.chunk_type.value
            by_type.setdefault(key, {"count": 0, "tokens": 0})
            by_type[key]["count"] += 1
            by_type[key]["tokens"] += item.tokens

        total = sum(v["tokens"] for v in by_type.values())
        return {
            "total_tokens": total,
            "total_items": len(items),
            "by_type": by_type,
            "max_item_tokens": self._max_item_tokens,
            "max_items": self._max_items,
            "utilization_pct": len(items) / self._max_items * 100 if self._max_items else 0,
        }
