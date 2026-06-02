"""蒙多记忆系统 v26 — 简化双层架构

改进（vs v25）：
- 三层(热/温/冷) → 双层(事实 + 摘要)，减少复杂度
- 不再每次对话都触发 LLM 提取（省 token）
- 关键词 + 标签双重检索
- 自动合并重复记忆
"""

import os
import re
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
MEMORY_DB = MUNDO_HOME / "memory.db"

MAX_MEMORY_TOKENS = 2000
MAX_FACTS_INJECT = 15
MAX_SUMMARIES_INJECT = 3


class MundoMemory:

    def __init__(self, db_path: Path = MEMORY_DB):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'fact',
                    source TEXT DEFAULT 'manual',
                    importance INTEGER DEFAULT 5,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    tokens INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '',
                    content_hash TEXT DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_category ON memories(category);
                CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance DESC);

                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    summary TEXT,
                    created_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    updated_at TEXT NOT NULL
                );
            """)

    # ═══════════════════════════════════════════════
    # 写入
    # ═══════════════════════════════════════════════

    def remember(self, content: str, category: str = "fact",
                 source: str = "manual", importance: int = 5,
                 tags: str = "") -> int:
        now = datetime.now().isoformat()
        tokens = len(content)
        c_hash = hashlib.md5(content.encode()).hexdigest()[:12]

        with sqlite3.connect(str(self.db_path)) as conn:
            existing = conn.execute(
                "SELECT id FROM memories WHERE content_hash = ? AND category = ?",
                (c_hash, category)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE memories SET content=?, importance=MAX(importance,?), updated_at=?, tokens=?, tags=? WHERE id=?",
                    (content, importance, now, tokens, tags, existing[0])
                )
                return existing[0]
            cursor = conn.execute(
                "INSERT INTO memories (content,category,source,importance,created_at,updated_at,tokens,tags,content_hash) VALUES (?,?,?,?,?,?,?,?,?)",
                (content, category, source, importance, now, now, tokens, tags, c_hash)
            )
            return cursor.lastrowid

    def remember_fact(self, key: str, value: str, importance: int = 5):
        self.remember(f"{key}: {value}", category="fact", importance=importance, tags=key)

    def remember_preference(self, key: str, value: str):
        self.remember(f"{key}: {value}", category="preference", importance=7, tags=key)
        now = datetime.now().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO user_profile (key,value,category,updated_at) VALUES (?,?,?,?) ON CONFLICT(key) DO UPDATE SET value=?,updated_at=?",
                (key, value, "preference", now, value, now)
            )

    def remember_lesson(self, lesson: str, importance: int = 8):
        self.remember(lesson, category="lesson", importance=importance, source="auto_extract")

    # ═══════════════════════════════════════════════
    # 读取：相关性检索
    # ═══════════════════════════════════════════════

    def recall(self, query: str, max_items: int = MAX_FACTS_INJECT) -> str:
        keywords = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
        if not keywords:
            return self._get_essential_facts(max_items=5)

        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT id, content, category, importance, access_count, tokens FROM memories ORDER BY importance DESC, access_count DESC LIMIT 200"
            ).fetchall()

        scored = []
        for mid, content, cat, imp, acc, tok in rows:
            content_lower = content.lower()
            keyword_score = sum(1 for kw in keywords if kw in content_lower)
            total_score = keyword_score * 2 + imp * 0.5 + min(acc, 10) * 0.2
            if total_score > 0:
                scored.append((total_score, mid, content, cat, tok))

        scored.sort(key=lambda x: -x[0])
        selected = []
        total_tokens = 0
        for score, mid, content, cat, tok in scored:
            if total_tokens + tok > MAX_MEMORY_TOKENS:
                break
            if len(selected) >= max_items:
                break
            selected.append((mid, content, cat))
            total_tokens += tok
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("UPDATE memories SET access_count = access_count + 1 WHERE id = ?", (mid,))

        if not selected:
            return self._get_essential_facts(max_items=5)
        return "\n".join(f"- [{cat}] {content}" for _, content, cat in selected)

    def _get_essential_facts(self, max_items: int = 5) -> str:
        with sqlite3.connect(str(self.db_path)) as conn:
            profiles = conn.execute(
                "SELECT key, value FROM user_profile ORDER BY updated_at DESC LIMIT ?",
                (max_items,)
            ).fetchall()
            facts = conn.execute(
                "SELECT content FROM memories WHERE importance >= 7 AND category IN ('fact','preference','lesson') ORDER BY importance DESC, access_count DESC LIMIT ?",
                (max_items,)
            ).fetchall()
        lines = [f"- [profile] {k}: {v}" for k, v in profiles]
        lines.extend(f"- [fact] {c}" for (c,) in facts)
        return "\n".join(lines[:max_items]) if lines else ""

    def get_context_budget(self, query: str) -> str:
        essentials = self._get_essential_facts(max_items=5)
        relevant = self.recall(query, max_items=MAX_FACTS_INJECT)
        all_lines = list(dict.fromkeys(
            (essentials + "\n" + relevant).strip().split("\n")
        ))
        result = []
        total = 0
        for line in all_lines:
            if total + len(line) > MAX_MEMORY_TOKENS:
                break
            result.append(line)
            total += len(line)
        return "\n".join(result) if result else ""

    # ═══════════════════════════════════════════════
    # 对话摘要
    # ═══════════════════════════════════════════════

    def compress_conversation(self, messages: List[Dict], conv_id: str) -> str:
        if len(messages) < 5:
            return ""
        user_msgs = [m for m in messages if m.get("role") == "user"]
        summary_parts = []
        for um in user_msgs[-5:]:
            content = (um.get("content") or "")[:200]
            summary_parts.append(f"用户: {content}")
        summary = " | ".join(summary_parts)
        if len(summary) > 500:
            summary = summary[:500] + "..."
        now = datetime.now().isoformat()
        safe_len = sum(len(m.get("content") or "") for m in messages)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO conversations (id,summary,created_at,message_count,total_tokens) VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET summary=?,message_count=?,total_tokens=?",
                (conv_id, summary, now, len(messages), safe_len,
                 summary, len(messages), safe_len)
            )
        return summary

    def get_recent_summaries(self, limit: int = MAX_SUMMARIES_INJECT) -> str:
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT summary, created_at FROM conversations WHERE summary IS NOT NULL ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        if not rows:
            return ""
        return "\n".join(f"- [{r[1][:10]}] {r[0][:150]}" for r in rows)

    # ═══════════════════════════════════════════════
    # 会话摘要生成（仅在会话结束时触发，不消耗额外 token）
    # ═══════════════════════════════════════════════

    def generate_session_summary(self, session_id: str, messages: List[Dict]):
        """从对话中提取摘要保存，不调用 LLM"""
        user_msgs = [m for m in messages if m.get("role") == "user"]
        if not user_msgs:
            return
        topics = []
        for um in user_msgs[:3]:
            content = (um.get("content") or "")[:100]
            if content:
                topics.append(content)
        summary = "; ".join(topics)
        if len(summary) > 200:
            summary = summary[:200] + "..."
        self.remember(
            content=summary, category="summary",
            source=f"session:{session_id}", importance=5, tags=session_id
        )

    # ═══════════════════════════════════════════════
    # 自动提取（仅在用户主动要求时触发）
    # ═══════════════════════════════════════════════

    def extract_from_conversation(self, messages: List[Dict], llm_client=None):
        if not llm_client or len(messages) < 3:
            return
        recent = messages[-6:]
        text = "\n".join(
            f"{m.get('role', '?')}: {m.get('content', '')[:300]}"
            for m in recent if m.get("content")
        )
        if len(text) < 50:
            return
        prompt = f"""从以下对话中提取关键信息，输出 JSON 数组。
每项: {{"content": "事实", "category": "fact/preference/decision/lesson", "importance": 1-10}}
只提取明确信息。最多 5 项。无则 []。纯 JSON，不要代码块。

对话：
{text[:2000]}"""
        try:
            result = llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=500
            )
            from llm import LLMClient as LC
            content = LC.extract_response(result).get("content", "[]").strip()
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            items = json.loads(content)
            if isinstance(items, list):
                for item in items[:5]:
                    if isinstance(item, dict) and "content" in item:
                        self.remember(
                            content=item["content"],
                            category=item.get("category", "fact"),
                            source="auto_extract",
                            importance=item.get("importance", 5)
                        )
        except Exception:
            pass

    # ═══════════════════════════════════════════════
    # 合并 + 查询
    # ═══════════════════════════════════════════════

    def consolidate(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            cutoff = (datetime.now() - timedelta(days=30)).isoformat()
            conn.execute(
                "DELETE FROM memories WHERE importance < 4 AND access_count = 0 AND created_at < ?",
                (cutoff,)
            )

    def all_facts(self, limit: int = 50) -> List[Tuple]:
        with sqlite3.connect(str(self.db_path)) as conn:
            return conn.execute(
                "SELECT content, category, importance FROM memories ORDER BY importance DESC, updated_at DESC LIMIT ?",
                (limit,)
            ).fetchall()

    def get_profile(self) -> Dict:
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute("SELECT key, value FROM user_profile").fetchall()
            return dict(rows)

    def get_stats(self) -> Dict:
        with sqlite3.connect(str(self.db_path)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            by_cat = conn.execute(
                "SELECT category, COUNT(*) FROM memories GROUP BY category"
            ).fetchall()
            convs = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            profiles = conn.execute("SELECT COUNT(*) FROM user_profile").fetchone()[0]
            total_tokens = conn.execute("SELECT COALESCE(SUM(tokens), 0) FROM memories").fetchone()[0]
        return {
            "total_memories": total,
            "total_tokens": total_tokens,
            "conversations": convs,
            "profile_keys": profiles,
            "by_category": dict(by_cat),
        }

    def recall_key(self, key: str) -> Optional[str]:
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT content FROM memories WHERE tags = ? ORDER BY updated_at DESC LIMIT 1",
                (key,)
            ).fetchone()
            if row:
                content = row[0]
                if ": " in content:
                    return content.split(": ", 1)[1]
                return content
        return None

    def forget(self, key: str):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM memories WHERE tags = ?", (key,))
            conn.execute("DELETE FROM user_profile WHERE key = ?", (key,))
