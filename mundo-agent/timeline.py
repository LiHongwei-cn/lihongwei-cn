"""蒙多 Timeline v1.4.0 — 皇帝的起居注

记录每一次决策、每一次工具调用、每一次 LLM 交互。
可查询、可回放、可导出。不是日志，是结构化的执行轨迹。

设计哲学：
- 每条记录都是不可变的事实
- 支持嵌套：一个 turn 包含多个 tool calls
- 持久化到 SQLite，支持复杂查询
- 导出为 JSONL 用于分析
"""

import json
import time
import sqlite3
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime


class EntryType(Enum):
    TURN = auto()
    TOOL_CALL = auto()
    TOOL_RESULT = auto()
    LLM_REQUEST = auto()
    LLM_RESPONSE = auto()
    POLICY_CHECK = auto()
    COMPRESS = auto()
    DELEGATE = auto()
    ERROR = auto()
    MARK = auto()  # 用户手动标记


@dataclass
class TimelineEntry:
    type: EntryType
    data: Dict[str, Any] = field(default_factory=dict)
    turn_id: str = ""
    parent_id: str = ""
    duration_ms: float = 0
    timestamp: float = field(default_factory=time.time)
    id: str = ""

    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = uuid.uuid4().hex[:12]


class Timeline:
    """执行轨迹记录器 — SQLite 持久化"""

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or (Path.home() / ".hermes" / "mundo-agent" / "timeline.db")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self._current_turn: Optional[str] = None

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS timeline (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                turn_id TEXT,
                parent_id TEXT,
                data TEXT,
                duration_ms REAL DEFAULT 0,
                timestamp REAL NOT NULL,
                session_id TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_timeline_turn ON timeline(turn_id);
            CREATE INDEX IF NOT EXISTS idx_timeline_type ON timeline(type);
            CREATE INDEX IF NOT EXISTS idx_timeline_ts ON timeline(timestamp);
            CREATE INDEX IF NOT EXISTS idx_timeline_session ON timeline(session_id);
        """)
        self._conn.commit()

    def start_turn(self, user_input: str, session_id: str = "") -> str:
        import uuid
        turn_id = uuid.uuid4().hex[:12]
        self._current_turn = turn_id
        self._record(EntryType.TURN, {
            "user_input": user_input[:500],
            "status": "started",
        }, turn_id=turn_id, session_id=session_id)
        return turn_id

    def end_turn(self, turn_id: str, response: str = "", tokens: int = 0) -> None:
        self._record(EntryType.TURN, {
            "response": response[:500],
            "tokens": tokens,
            "status": "completed",
        }, turn_id=turn_id)

    def record_tool(self, tool_name: str, args: Dict, result: str = "",
                    duration_ms: float = 0, is_error: bool = False,
                    turn_id: str = "") -> str:
        entry_id = self._record(
            EntryType.TOOL_ERROR if is_error else EntryType.TOOL_CALL,
            {
                "tool": tool_name,
                "args": {k: str(v)[:200] for k, v in args.items()},
                "result": result[:1000],
                "is_error": is_error,
            },
            turn_id=turn_id or self._current_turn,
            duration_ms=duration_ms,
        )
        return entry_id

    def record_llm(self, prompt_tokens: int = 0, completion_tokens: int = 0,
                   cached: bool = False, model: str = "",
                   turn_id: str = "") -> str:
        return self._record(EntryType.LLM_RESPONSE, {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cached": cached,
            "model": model,
        }, turn_id=turn_id or self._current_turn)

    def record_policy(self, tool_name: str, action: str, rule: str = "",
                      reason: str = "", turn_id: str = "") -> str:
        return self._record(EntryType.POLICY_CHECK, {
            "tool": tool_name,
            "action": action,
            "rule": rule,
            "reason": reason,
        }, turn_id=turn_id or self._current_turn)

    def record_compress(self, old_count: int, new_count: int,
                        old_tokens: int, new_tokens: int,
                        turn_id: str = "") -> str:
        return self._record(EntryType.COMPRESS, {
            "old_msgs": old_count,
            "new_msgs": new_count,
            "old_tokens": old_tokens,
            "new_tokens": new_tokens,
            "saved_tokens": old_tokens - new_tokens,
        }, turn_id=turn_id or self._current_turn)

    def record_error(self, error: str, context: str = "",
                     turn_id: str = "") -> str:
        return self._record(EntryType.ERROR, {
            "error": error[:500],
            "context": context[:200],
        }, turn_id=turn_id or self._current_turn)

    def mark(self, label: str, data: Dict = None) -> str:
        return self._record(EntryType.MARK, {
            "label": label,
            **(data or {}),
        }, turn_id=self._current_turn)

    def query(self, turn_id: str = "", entry_type: Optional[EntryType] = None,
              limit: int = 50, since: float = 0) -> List[Dict]:
        conditions = []
        params = []
        if turn_id:
            conditions.append("turn_id = ?")
            params.append(turn_id)
        if entry_type:
            conditions.append("type = ?")
            params.append(entry_type.name)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since)

        where = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT * FROM timeline WHERE {where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_turn(self, turn_id: str) -> List[Dict]:
        return self.query(turn_id=turn_id, limit=100)

    def recent(self, limit: int = 20) -> List[Dict]:
        return self.query(limit=limit)

    def stats(self, session_id: str = "") -> Dict:
        if session_id:
            rows = self._conn.execute(
                "SELECT type, COUNT(*) as cnt FROM timeline WHERE session_id=? GROUP BY type",
                (session_id,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT type, COUNT(*) as cnt FROM timeline GROUP BY type"
            ).fetchall()
        return {r["type"]: r["cnt"] for r in rows}

    def export_jsonl(self, path: Path, since: float = 0) -> int:
        rows = self.query(limit=10000, since=since)
        with open(path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return len(rows)

    def _record(self, entry_type: EntryType, data: Dict,
                turn_id: str = "", duration_ms: float = 0,
                session_id: str = "") -> str:
        import uuid
        entry_id = uuid.uuid4().hex[:12]
        self._conn.execute(
            "INSERT INTO timeline (id, type, turn_id, parent_id, data, duration_ms, timestamp, session_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry_id,
                entry_type.name,
                turn_id,
                "",
                json.dumps(data, ensure_ascii=False),
                duration_ms,
                time.time(),
                session_id,
            ),
        )
        self._conn.commit()
        return entry_id

    def close(self) -> None:
        self._conn.close()


# 全局单例
_timeline: Optional[Timeline] = None


def get_timeline() -> Timeline:
    global _timeline
    if _timeline is None:
        _timeline = Timeline()
    return _timeline
