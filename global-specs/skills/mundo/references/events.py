"""蒙多事件系统 v1.4.0 — 皇帝的耳目

事件驱动架构。所有组件通过事件通信，零耦合。
事件可持久化、可回放、可过滤。

设计哲学：
- 发布者不知道订阅者是谁
- 事件是不可变的事实记录
- 优先级决定处理顺序
- 异步友好但同步可用
"""

import time
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Callable, Any
from pathlib import Path
from collections import defaultdict
from datetime import datetime


# ═══════════════════════════════════════════════
# 事件类型 — 皇帝关注的一切
# ═══════════════════════════════════════════════

class EventType(Enum):
    # 生命周期
    SESSION_START = auto()
    SESSION_END = auto()
    TURN_START = auto()
    TURN_END = auto()

    # LLM
    LLM_REQUEST = auto()
    LLM_RESPONSE = auto()
    LLM_STREAM_START = auto()
    LLM_STREAM_CHUNK = auto()
    LLM_STREAM_END = auto()
    LLM_ERROR = auto()

    # 工具
    TOOL_CALL = auto()
    TOOL_RESULT = auto()
    TOOL_ERROR = auto()

    # 策略
    POLICY_CHECK = auto()
    POLICY_ALLOW = auto()
    POLICY_DENY = auto()
    POLICY_ASK = auto()

    # 上下文
    CONTEXT_COMPRESS = auto()
    CONTEXT_INJECT = auto()
    CONTEXT_OVERFLOW = auto()

    # 记忆
    MEMORY_STORE = auto()
    MEMORY_RECALL = auto()
    MEMORY_EXTRACT = auto()

    # 委托
    DELEGATE_START = auto()
    DELEGATE_END = auto()
    DELEGATE_ERROR = auto()

    # 系统
    ERROR = auto()
    WARNING = auto()
    INFO = auto()
    DEBUG = auto()


class Priority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


# ═══════════════════════════════════════════════
# 事件 — 不可变的事实
# ═══════════════════════════════════════════════

@dataclass(frozen=True)
class Event:
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    priority: Priority = Priority.NORMAL
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.name,
            "source": self.source,
            "priority": self.priority.name,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "data": self.data,
        }

    def __str__(self) -> str:
        ts = datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")
        return f"[{ts}] {self.type.name} from={self.source} {self.data}"


# ═══════════════════════════════════════════════
# 订阅 — 谁在监听
# ═══════════════════════════════════════════════

@dataclass
class Subscription:
    id: str
    event_type: EventType
    handler: Callable[[Event], None]
    source_filter: str = ""
    priority: Priority = Priority.NORMAL
    once: bool = False

    def matches(self, event: Event) -> bool:
        if event.type != self.event_type:
            return False
        if self.source_filter and event.source != self.source_filter:
            return False
        return True


# ═══════════════════════════════════════════════
# EventBus — 皇帝的耳目网络
# ═══════════════════════════════════════════════

class EventBus:
    """发布-订阅事件总线，支持优先级、过滤、持久化"""

    def __init__(self, persist_path: Optional[Path] = None):
        self._subscriptions: Dict[EventType, List[Subscription]] = defaultdict(list)
        self._history: List[Event] = []
        self._max_history = 500
        self._persist_path = persist_path
        self._stats = {"published": 0, "handled": 0, "errors": 0}

    def on(self, event_type: EventType, handler: Callable[[Event], None],
           source: str = "", priority: Priority = Priority.NORMAL,
           once: bool = False) -> str:
        sub = Subscription(
            id=uuid.uuid4().hex[:8],
            event_type=event_type,
            handler=handler,
            source_filter=source,
            priority=priority,
            once=once,
        )
        self._subscriptions[event_type].append(sub)
        self._subscriptions[event_type].sort(
            key=lambda s: s.priority.value, reverse=True
        )
        return sub.id

    def off(self, sub_id: str) -> bool:
        for etype, subs in self._subscriptions.items():
            before = len(subs)
            self._subscriptions[etype] = [s for s in subs if s.id != sub_id]
            if len(self._subscriptions[etype]) < before:
                return True
        return False

    def emit(self, event: Event) -> int:
        self._stats["published"] += 1
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        if self._persist_path:
            self._persist_event(event)

        handled = 0
        to_remove = []
        subs = self._subscriptions.get(event.type, [])

        for sub in subs:
            if sub.matches(event):
                try:
                    sub.handler(event)
                    handled += 1
                    self._stats["handled"] += 1
                except Exception as e:
                    self._stats["errors"] += 1
                    self.emit(Event(
                        type=EventType.ERROR,
                        data={"error": str(e), "handler": sub.id},
                        source="event_bus",
                    ))
                if sub.once:
                    to_remove.append(sub.id)

        for sid in to_remove:
            self.off(sid)

        return handled

    def publish(self, event_type: EventType, data: Dict = None,
                source: str = "", priority: Priority = Priority.NORMAL,
                session_id: str = "") -> int:
        event = Event(
            type=event_type,
            data=data or {},
            source=source,
            priority=priority,
            session_id=session_id,
        )
        return self.emit(event)

    def history(self, event_type: Optional[EventType] = None,
                source: str = "", limit: int = 20) -> List[Event]:
        events = self._history
        if event_type:
            events = [e for e in events if e.type == event_type]
        if source:
            events = [e for e in events if e.source == source]
        return events[-limit:]

    def stats(self) -> Dict:
        return {
            **self._stats,
            "subscriptions": sum(len(s) for s in self._subscriptions.values()),
            "history_size": len(self._history),
        }

    def _persist_event(self, event: Event) -> None:
        try:
            line = json.dumps(event.to_dict(), ensure_ascii=False) + "\n"
            with open(self._persist_path, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            pass


# 全局单例
_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        persist_path = Path.home() / ".hermes" / "mundo-agent" / "events.jsonl"
        _bus = EventBus(persist_path=persist_path)
    return _bus
