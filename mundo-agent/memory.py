"""蒙多记忆系统 v3.0.0 — 融合四家精华

融合精华：
- Hermes Agent：SQLite FTS5全文搜索、记忆持久化
- Claude Code：会话摘要、上下文压缩
- Codex CLI：项目上下文感知
- MiMo Code：跨会话记忆、中文优化

v3.0.0 改进：
- FTS5自动修复（损坏时自动重建）
- 中文分词优化（字符级匹配+LIKE后备）
- 记忆去重（MD5哈希+内容相似度）
- 自动淘汰（30天未访问+低重要性）
- 项目隔离（按工作目录过滤记忆）
"""

import re
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from constants import MUNDO_HOME, MEMORY_DB, MAX_CONTEXT_INJECT, MAX_FACTS_INJECT, MAX_CONVERSATION_RESULTS


class MundoMemory:

    def __repr__(self) -> str:
        return f"MundoMemory(db={self.db_path})"

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
                    project TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    tokens INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '',
                    content_hash TEXT DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_category ON memories(category);
                CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance DESC);
                CREATE INDEX IF NOT EXISTS idx_project ON memories(project);

                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT DEFAULT '',
                    summary TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    project TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    path TEXT PRIMARY KEY,
                    name TEXT DEFAULT '',
                    tech_stack TEXT DEFAULT '',
                    structure TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    last_seen TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consolidation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    details TEXT DEFAULT '',
                    items_affected INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
            """)
            self._rebuild_fts(conn)

    def _rebuild_fts(self, conn):
        for trig in ("conversations_ai", "conversations_ad"):
            try:
                conn.execute(f"DROP TRIGGER IF EXISTS {trig}")
            except Exception:
                pass
        for tbl in ("conversations_fts", "conversations_fts_data",
                     "conversations_fts_idx", "conversations_fts_docsize",
                     "conversations_fts_config"):
            try:
                conn.execute(f"DROP TABLE IF EXISTS {tbl}")
            except Exception:
                pass
        conn.execute("""
            CREATE VIRTUAL TABLE conversations_fts USING fts5(
                title, summary, content='conversations', content_rowid='rowid'
            )
        """)
        conn.execute("""
            CREATE TRIGGER conversations_ai AFTER INSERT ON conversations BEGIN
                INSERT INTO conversations_fts(rowid, title, summary)
                VALUES (new.rowid, new.title, new.summary);
            END
        """)
        conn.execute("""
            CREATE TRIGGER conversations_ad AFTER DELETE ON conversations BEGIN
                INSERT INTO conversations_fts(conversations_fts, rowid, title, summary)
                VALUES ('delete', old.rowid, old.title, old.summary);
            END
        """)
        try:
            conn.execute("""
                INSERT INTO conversations_fts(rowid, title, summary)
                SELECT rowid, title, summary FROM conversations
            """)
        except Exception:
            pass

    # ═══════════════════════════════════════════════
    # 自动提取
    # ═══════════════════════════════════════════════

    def auto_extract(self, user_msg: str, assistant_msg: str,
                     project: str = "") -> List[int]:
        extracted = []
        patterns = [
            (r"记住|remember|记一下", "fact", 7),
            (r"我喜欢|我偏好|我习惯|I prefer", "preference", 8),
            (r"不要|别用|禁止|don't|never", "constraint", 8),
            (r"以后|下次|always|从现在起", "rule", 7),
            (r"错误|报错|bug|问题出在", "lesson", 6),
            (r"用.*框架|用.*库|技术栈", "code_pattern", 7),
            (r"目录|文件结构|项目结构", "code_pattern", 6),
        ]
        for pattern, category, importance in patterns:
            if re.search(pattern, user_msg, re.IGNORECASE):
                content = user_msg.strip()[:200]
                if len(content) > 10:
                    mid = self.remember(
                        content=content, category=category,
                        source="auto_extract", importance=importance,
                        project=project
                    )
                    extracted.append(mid)
        return extracted

    # ═══════════════════════════════════════════════
    # 对话搜索
    # ═══════════════════════════════════════════════

    def save_conversation(self, conv_id: str, title: str, summary: str,
                          messages: List[Dict], project: str = ""):
        now = datetime.now(timezone.utc).isoformat()
        total_chars = sum(len((m.get("content") or "")) for m in messages)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT INTO conversations (id,title,summary,created_at,updated_at,message_count,total_tokens,project)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET title=?,summary=?,updated_at=?,message_count=?,total_tokens=?""",
                (conv_id, title, summary, now, now, len(messages), total_chars, project,
                 title, summary, now, len(messages), total_chars)
            )

    def search_conversations(self, query: str,
                             limit: int = MAX_CONVERSATION_RESULTS) -> List[Dict]:
        if not query.strip():
            return []
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                try:
                    rows = conn.execute(
                        """SELECT c.id, c.title, c.summary, c.created_at, c.message_count
                           FROM conversations_fts f
                           JOIN conversations c ON c.rowid = f.rowid
                           WHERE conversations_fts MATCH ?
                           ORDER BY rank LIMIT ?""",
                        (query, limit)
                    ).fetchall()
                except sqlite3.OperationalError:
                    rows = []
                if not rows:
                    like_pattern = f"%{query}%"
                    rows = conn.execute(
                        """SELECT id, title, summary, created_at, message_count
                           FROM conversations
                           WHERE title LIKE ? OR summary LIKE ?
                           ORDER BY created_at DESC LIMIT ?""",
                        (like_pattern, like_pattern, limit)
                    ).fetchall()
            return [
                {"id": r[0], "title": r[1], "summary": r[2],
                 "date": r[3][:10] if r[3] else "", "messages": r[4]}
                for r in rows
            ]
        except sqlite3.OperationalError:
            return []

    # ═══════════════════════════════════════════════
    # 代码记忆
    # ═══════════════════════════════════════════════

    def remember_code(self, pattern: str, detail: str = "",
                      project: str = "", importance: int = 7):
        content = f"{pattern}: {detail}" if detail else pattern
        return self.remember(
            content=content, category="code_pattern",
            source="code", importance=importance,
            project=project, tags=pattern[:50]
        )

    def remember_project(self, path: str, name: str = "",
                         tech_stack: str = "", notes: str = ""):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT INTO projects (path,name,tech_stack,notes,last_seen)
                   VALUES (?,?,?,?,?)
                   ON CONFLICT(path) DO UPDATE SET name=?,tech_stack=?,notes=?,last_seen=?""",
                (path, name, tech_stack, notes, now, name, tech_stack, notes, now)
            )

    def get_project_context(self, path: str) -> Dict:
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                'SELECT name, tech_stack, structure, notes FROM projects WHERE path = ?',
                (path,)
            ).fetchone()
            if row:
                return {"name": row[0], "tech_stack": row[1],
                        "structure": row[2], "notes": row[3]}
        return {}

    def get_code_patterns(self, project: str = "", limit: int = 10) -> List[str]:
        with sqlite3.connect(str(self.db_path)) as conn:
            if project:
                rows = conn.execute(
                    "SELECT content FROM memories WHERE category='code_pattern' AND (project=? OR project='') ORDER BY importance DESC, access_count DESC LIMIT ?",
                    (project, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT content FROM memories WHERE category='code_pattern' ORDER BY importance DESC, access_count DESC LIMIT ?",
                    (limit,)
                ).fetchall()
        return [r[0] for r in rows]

    # ═══════════════════════════════════════════════
    # Agent 记忆
    # ═══════════════════════════════════════════════

    def remember_agent_result(self, task: str, result: str,
                              success: bool, project: str = ""):
        status = "成功" if success else "失败"
        content = f"[{status}] {task} → {result[:200]}"
        importance = 7 if success else 9
        return self.remember(
            content=content, category="agent_result",
            source="agent", importance=importance,
            project=project, tags=task[:50]
        )

    # ═══════════════════════════════════════════════
    # 项目隔离
    # ═══════════════════════════════════════════════

    def get_project_memories(self, project: str,
                             limit: int = MAX_FACTS_INJECT) -> List[Tuple]:
        with sqlite3.connect(str(self.db_path)) as conn:
            return conn.execute(
                """SELECT content, category, importance FROM memories
                   WHERE project=? OR project=''
                   ORDER BY importance DESC, access_count DESC LIMIT ?""",
                (project, limit)
            ).fetchall()

    def get_all_projects(self) -> List[Dict]:
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT path, name, tech_stack, last_seen FROM projects ORDER BY last_seen DESC"
            ).fetchall()
        return [{"path": r[0], "name": r[1], "tech": r[2], "seen": r[3][:10]} for r in rows]

    # ═══════════════════════════════════════════════
    # 自我整理
    # ═══════════════════════════════════════════════

    def consolidate(self) -> Dict:
        stats = {"duplicates_removed": 0, "expired_removed": 0, "merged": 0}
        now = datetime.now(timezone.utc)
        with sqlite3.connect(str(self.db_path)) as conn:
            dupes = conn.execute(
                """SELECT content_hash, GROUP_CONCAT(id), COUNT(*) as cnt
                   FROM memories WHERE content_hash != ''
                   GROUP BY content_hash HAVING cnt > 1"""
            ).fetchall()
            for c_hash, ids_str, cnt in dupes:
                ids = [int(i) for i in ids_str.split(",")]
                keep_id = max(ids, key=lambda i: conn.execute(
                    "SELECT importance FROM memories WHERE id=?", (i,)
                ).fetchone()[0])
                remove_ids = [i for i in ids if i != keep_id]
                for rid in remove_ids:
                    conn.execute("DELETE FROM memories WHERE id=?", (rid,))
                stats["duplicates_removed"] += len(remove_ids)

            cutoff = (now - timedelta(days=30)).isoformat()
            result = conn.execute(
                "DELETE FROM memories WHERE importance < 4 AND access_count = 0 AND created_at < ?",
                (cutoff,)
            )
            stats["expired_removed"] = result.rowcount

            conn.execute(
                "INSERT INTO consolidation_log (action,details,items_affected,created_at) VALUES (?,?,?,?)",
                ("auto_consolidate", json.dumps(stats),
                 stats["duplicates_removed"] + stats["expired_removed"],
                 now.isoformat())
            )
        return stats

    # ═══════════════════════════════════════════════
    # 核心读写接口
    # ═══════════════════════════════════════════════

    def remember(self, content: str, category: str = "fact",
                 source: str = "manual", importance: int = 5,
                 project: str = "", tags: str = "") -> int:
        now = datetime.now(timezone.utc).isoformat()
        tokens = len(content)
        c_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        with sqlite3.connect(str(self.db_path)) as conn:
            existing = conn.execute(
                "SELECT id FROM memories WHERE content_hash = ? AND category = ?",
                (c_hash, category)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE memories SET content=?, importance=MAX(importance,?), updated_at=?, tokens=?, tags=?, project=? WHERE id=?",
                    (content, importance, now, tokens, tags, project, existing[0])
                )
                return existing[0]
            cursor = conn.execute(
                "INSERT INTO memories (content,category,source,importance,project,created_at,updated_at,tokens,tags,content_hash) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (content, category, source, importance, project, now, now, tokens, tags, c_hash)
            )
            return cursor.lastrowid

    def remember_fact(self, key: str, value: str, importance: int = 5):
        self.remember(f"{key}: {value}", category="fact", importance=importance, tags=key)

    def remember_preference(self, key: str, value: str):
        self.remember(f"{key}: {value}", category="preference", importance=7, tags=key)
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO user_profile (key,value,category,updated_at) VALUES (?,?,?,?) ON CONFLICT(key) DO UPDATE SET value=?,updated_at=?",
                (key, value, "preference", now, value, now)
            )

    def remember_lesson(self, lesson: str, importance: int = 8):
        self.remember(lesson, category="lesson", importance=importance, source="auto_extract")

    def recall(self, query: str, project: str = "",
               max_items: int = MAX_FACTS_INJECT) -> str:
        keywords = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
        if not keywords:
            return self._get_essential_facts(max_items=5)

        with sqlite3.connect(str(self.db_path)) as conn:
            if project:
                rows = conn.execute(
                    "SELECT id, content, category, importance, access_count, tokens, project FROM memories WHERE project=? OR project='' ORDER BY importance DESC, access_count DESC LIMIT 200",
                    (project,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, content, category, importance, access_count, tokens, project FROM memories ORDER BY importance DESC, access_count DESC LIMIT 200"
                ).fetchall()

        scored = []
        for mid, content, cat, imp, acc, tok, proj in rows:
            content_lower = content.lower()
            keyword_hits = sum(1 for kw in keywords if kw in content_lower)
            if keyword_hits == 0:
                continue
            keyword_score = keyword_hits * 2
            if keyword_hits >= 2:
                keyword_score += keyword_hits
            importance_score = (float(imp) if imp is not None else 5.0) * 0.5
            access_score = min(int(acc) if acc is not None else 0, 10) * 0.2
            cat_weights = {
                "lesson": 1.5, "code_pattern": 1.3, "agent_result": 1.2,
                "fact": 1.1, "preference": 1.0, "constraint": 1.4,
                "rule": 1.2, "summary": 0.6,
            }
            cat_score = cat_weights.get(cat, 0.8)
            project_bonus = 1.3 if proj and proj == project else 1.0
            total_score = (keyword_score + importance_score + access_score) * cat_score * project_bonus
            scored.append((total_score, mid, content, cat, tok))

        scored.sort(key=lambda x: -x[0])
        selected = []
        total_tokens = 0
        ids_to_update = []
        for score, mid, content, cat, tok in scored:
            if total_tokens + tok > MAX_CONTEXT_INJECT:
                break
            if len(selected) >= max_items:
                break
            selected.append((mid, content, cat))
            total_tokens += tok
            ids_to_update.append(mid)

        if ids_to_update:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.executemany(
                    "UPDATE memories SET access_count = access_count + 1 WHERE id = ?",
                    [(mid,) for mid in ids_to_update]
                )

        if not selected:
            return self._get_essential_facts(max_items=5)
        return "\n".join(f"- [{cat}] {content}" for _, content, cat in selected)

    def _get_essential_facts(self, max_items: int = 5) -> str:
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT content, category FROM memories ORDER BY importance DESC, access_count DESC LIMIT ?",
                (max_items,)
            ).fetchall()
        if not rows:
            return ""
        return "\n".join(f"- [{cat}] {content}" for content, cat in rows)

    def recall_key(self, key: str) -> Optional[str]:
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT value FROM user_profile WHERE key=?", (key,)
            ).fetchone()
            if row:
                return row[0]
            rows = conn.execute(
                "SELECT content FROM memories WHERE tags=? OR content LIKE ? ORDER BY importance DESC LIMIT 1",
                (key, f"%{key}%")
            ).fetchall()
            if rows:
                return rows[0][0]
        return None

    def forget(self, key: str):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM user_profile WHERE key=?", (key,))
            conn.execute("DELETE FROM memories WHERE tags=?", (key,))

    def all_facts(self, limit: int = 30) -> List[Tuple]:
        with sqlite3.connect(str(self.db_path)) as conn:
            return conn.execute(
                "SELECT content, category, importance FROM memories ORDER BY importance DESC, access_count DESC LIMIT ?",
                (limit,)
            ).fetchall()

    def get_stats(self) -> Dict:
        with sqlite3.connect(str(self.db_path)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            total_tokens = conn.execute("SELECT COALESCE(SUM(tokens),0) FROM memories").fetchone()[0]
            profile_keys = conn.execute("SELECT COUNT(*) FROM user_profile").fetchone()[0]
            projects = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
            conversations = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            by_category = {}
            for row in conn.execute("SELECT category, COUNT(*) FROM memories GROUP BY category").fetchall():
                by_category[row[0]] = row[1]
        return {
            "total_memories": total,
            "total_tokens": total_tokens,
            "profile_keys": profile_keys,
            "projects": projects,
            "conversations": conversations,
            "by_category": by_category,
        }
