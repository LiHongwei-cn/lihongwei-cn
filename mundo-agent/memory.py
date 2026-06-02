"""蒙多记忆系统 v2 — 借鉴 mem0/Letta/Cognee/Supermemory 核心能力

三层架构：
  热记忆 (Hot)   — 当前对话上下文，直接注入 prompt
  温记忆 (Warm)  — 近期对话摘要，按相关性检索注入
  冷记忆 (Cold)  — 持久化事实/用户画像/技能知识，按需检索

核心策略：
  1. 自动提取：对话结束后自动提取事实、偏好、决策
  2. 记忆压缩：对话摘要替代原始消息，大幅减少 token
  3. 相关性检索：只注入与当前任务相关的记忆，不全量注入
  4. 自动合并：重复/矛盾记忆自动合并更新
  5. 上下文预算：严格控制记忆注入的 token 数量
"""

import os
import re
import json
import time
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
MEMORY_DB = MUNDO_HOME / "memory.db"

# Token 预算（字符数近似，1 中文字 ≈ 2 token）
MAX_MEMORY_TOKENS = 2000      # 记忆注入上限（字符数）
MAX_FACTS_INJECT = 15          # 最多注入 15 条事实
MAX_SUMMARIES_INJECT = 3       # 最多注入 3 条对话摘要
SUMMARY_COMPRESS_THRESHOLD = 5  # 对话超过 5 轮时压缩为摘要


@dataclass
class MemoryItem:
    id: int
    content: str
    category: str       # fact / preference / lesson / decision / profile / summary
    source: str         # conversation_id / manual / auto_extract
    importance: int     # 1-10
    created_at: str
    updated_at: str
    access_count: int
    tokens: int         # 字符数（近似 token）
    tags: str           # 逗号分隔的标签


class MundoMemoryV2:
    """蒙多记忆系统 v2 — 三层架构 + 压缩 + 检索"""

    def __init__(self, db_path: Path = MEMORY_DB):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._hot_cache: List[Dict] = []  # 热记忆缓存

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
                    embedding_hash TEXT DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_category ON memories(category);
                CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance DESC);
                CREATE INDEX IF NOT EXISTS idx_source ON memories(source);

                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    summary TEXT,
                    facts_extracted INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    confidence REAL DEFAULT 0.8,
                    updated_at TEXT NOT NULL
                );
            """)

    # ═══════════════════════════════════════════════
    # 写入：自动提取 + 去重 + 合并
    # ═══════════════════════════════════════════════

    def remember(self, content: str, category: str = "fact",
                 source: str = "manual", importance: int = 5,
                 tags: str = "") -> int:
        """写入记忆。自动去重，重复则更新。返回 ID。"""
        now = datetime.now().isoformat()
        tokens = len(content)
        emb_hash = hashlib.md5(content.encode()).hexdigest()[:12]

        with sqlite3.connect(str(self.db_path)) as conn:
            # 检查是否有高度相似的记忆（相同 hash 前缀）
            existing = conn.execute(
                "SELECT id, content FROM memories WHERE embedding_hash = ? AND category = ?",
                (emb_hash, category)
            ).fetchone()

            if existing:
                # 更新已有记忆
                conn.execute(
                    "UPDATE memories SET content=?, importance=MAX(importance,?), updated_at=?, tokens=?, tags=? WHERE id=?",
                    (content, importance, now, tokens, tags, existing[0])
                )
                return existing[0]

            # 新增
            cursor = conn.execute(
                "INSERT INTO memories (content, category, source, importance, created_at, updated_at, tokens, tags, embedding_hash) VALUES (?,?,?,?,?,?,?,?,?)",
                (content, category, source, importance, now, now, tokens, tags, emb_hash)
            )
            return cursor.lastrowid

    def remember_fact(self, key: str, value: str, importance: int = 5):
        """记住一个结构化事实"""
        self.remember(f"{key}: {value}", category="fact", importance=importance, tags=key)

    def remember_preference(self, key: str, value: str):
        """记住用户偏好"""
        self.remember(f"{key}: {value}", category="preference", importance=7, tags=key)
        # 同时更新 user_profile
        now = datetime.now().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO user_profile (key, value, category, updated_at) VALUES (?,?,?,?) ON CONFLICT(key) DO UPDATE SET value=?, updated_at=?",
                (key, value, "preference", now, value, now)
            )

    def remember_lesson(self, lesson: str, importance: int = 8):
        """记住经验教训（高重要性）"""
        self.remember(lesson, category="lesson", importance=importance, source="auto_extract")

    # ═══════════════════════════════════════════════
    # 读取：相关性检索 + token 预算控制
    # ═══════════════════════════════════════════════

    def recall(self, query: str, max_items: int = MAX_FACTS_INJECT) -> str:
        """检索与 query 相关的记忆，注入到 prompt。返回格式化字符串。"""
        keywords = set(re.findall(r'[\w\u4e00-\u9fff]+', query.lower()))
        if not keywords:
            return self._get_essential_facts(max_items=5)

        with sqlite3.connect(str(self.db_path)) as conn:
            # 获取所有记忆，按相关性打分
            rows = conn.execute(
                "SELECT id, content, category, importance, access_count, tokens FROM memories ORDER BY importance DESC, access_count DESC LIMIT 200"
            ).fetchall()

        scored = []
        for row in rows:
            mid, content, cat, imp, acc, tok = row
            content_lower = content.lower()
            # 关键词匹配得分
            keyword_score = sum(1 for kw in keywords if kw in content_lower)
            # 综合得分：关键词匹配 × 2 + 重要性 + 访问频率
            total_score = keyword_score * 2 + imp * 0.5 + min(acc, 10) * 0.2
            if total_score > 0:
                scored.append((total_score, mid, content, cat, tok))

        # 按得分排序，截取到 token 预算内
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
            # 更新访问计数
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("UPDATE memories SET access_count = access_count + 1 WHERE id = ?", (mid,))

        if not selected:
            return self._get_essential_facts(max_items=5)

        # 格式化输出
        lines = []
        for mid, content, cat in selected:
            lines.append(f"- [{cat}] {content}")
        return "\n".join(lines)

    def _get_essential_facts(self, max_items: int = 5) -> str:
        """获取最基础的事实（高重要性 + 用户画像）"""
        with sqlite3.connect(str(self.db_path)) as conn:
            # 用户画像
            profiles = conn.execute(
                "SELECT key, value FROM user_profile ORDER BY updated_at DESC LIMIT ?",
                (max_items,)
            ).fetchall()
            # 高重要性事实
            facts = conn.execute(
                "SELECT content FROM memories WHERE importance >= 7 AND category IN ('fact','preference','lesson') ORDER BY importance DESC, access_count DESC LIMIT ?",
                (max_items,)
            ).fetchall()

        lines = []
        for key, value in profiles:
            lines.append(f"- [profile] {key}: {value}")
        for (content,) in facts:
            lines.append(f"- [fact] {content}")
        return "\n".join(lines[:max_items]) if lines else ""

    def get_context_budget(self, query: str) -> str:
        """获取适合注入到 system prompt 的记忆上下文（严格控制 token）"""
        essentials = self._get_essential_facts(max_items=5)
        relevant = self.recall(query, max_items=MAX_FACTS_INJECT)

        # 合并去重
        all_lines = list(dict.fromkeys(
            (essentials + "\n" + relevant).strip().split("\n")
        ))
        # 截断到预算
        result = []
        total = 0
        for line in all_lines:
            if total + len(line) > MAX_MEMORY_TOKENS:
                break
            result.append(line)
            total += len(line)

        return "\n".join(result) if result else ""

    # ═══════════════════════════════════════════════
    # 对话摘要压缩（借鉴 mem0 压缩引擎）
    # ═══════════════════════════════════════════════

    def compress_conversation(self, messages: List[Dict], conv_id: str) -> str:
        """将对话历史压缩为摘要 + 关键事实。大幅减少 token。"""
        if len(messages) < SUMMARY_COMPRESS_THRESHOLD:
            return ""

        user_msgs = [m for m in messages if m.get("role") == "user"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]

        summary_parts = []
        for um in user_msgs[-5:]:
            content = (um.get("content") or "")[:200]
            summary_parts.append(f"用户: {content}")

        summary = " | ".join(summary_parts)
        if len(summary) > 500:
            summary = summary[:500] + "..."

        now = datetime.now().isoformat()
        # content 可能为 None（tool_calls 消息），必须 or ""
        safe_len = sum(len(m.get("content") or "") for m in messages)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO conversations (id, summary, created_at, message_count, total_tokens) VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET summary=?, message_count=?, total_tokens=?",
                (conv_id, summary, now, len(messages), safe_len,
                 summary, len(messages), safe_len)
            )

        return summary

    def get_recent_summaries(self, limit: int = MAX_SUMMARIES_INJECT) -> str:
        """获取最近对话摘要"""
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT summary, created_at FROM conversations WHERE summary IS NOT NULL ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        if not rows:
            return ""
        lines = [f"- [{r[1][:10]}] {r[0][:150]}" for r in rows]
        return "\n".join(lines)

    # ═══════════════════════════════════════════════
    # 工具观察记录（借鉴 claude-mem）
    # ═══════════════════════════════════════════════

    def log_tool_observation(self, tool_name: str, tool_args: dict,
                              result_preview: str, session_id: str = ""):
        """自动记录工具使用观察（claude-mem 核心思想）

        不需要 LLM 提取，直接结构化记录：
        - 用了什么工具
        - 参数是什么
        - 结果预览
        """
        # 构建观察内容
        if tool_name == "terminal":
            cmd = tool_args.get("command", "")[:100]
            observation = f"执行命令: {cmd}"
            if result_preview and not result_preview.startswith("["):
                # 提取关键结果（前 100 字符）
                obs_result = result_preview[:100].replace("\n", " ")
                observation += f" → {obs_result}"
        elif tool_name in ("read_file", "write_file"):
            path = tool_args.get("path", "")
            action = "读取" if tool_name == "read_file" else "写入"
            observation = f"{action}文件: {path}"
        elif tool_name == "search_files":
            pattern = tool_args.get("pattern", "")
            observation = f"搜索: {pattern}"
        elif tool_name == "web_search":
            query = tool_args.get("query", "")
            observation = f"网络搜索: {query}"
        else:
            observation = f"工具调用: {tool_name}"

        # 保存为低重要性观察（不注入 prompt，但可被检索）
        self.remember(
            content=observation,
            category="observation",
            source=f"tool:{session_id}",
            importance=3,
            tags=f"{tool_name},{session_id}"
        )

    # ═══════════════════════════════════════════════
    # 会话摘要生成（借鉴 claude-mem）
    # ═══════════════════════════════════════════════

    def generate_session_summary(self, session_id: str, llm_client=None) -> str:
        """根据本次会话的工具观察，生成结构化摘要

        claude-mem 的核心：不是从对话提取，而是从工具操作提取。
        """
        # 获取本次会话的所有工具观察
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT content FROM memories WHERE source = ? AND category = 'observation' ORDER BY created_at DESC LIMIT 30",
                (f"tool:{session_id}",)
            ).fetchall()

        if not rows:
            return ""

        observations = [r[0] for r in rows]

        # 如果有 LLM，用它生成更好的摘要
        if llm_client and len(observations) >= 3:
            obs_text = "\n".join(f"- {o}" for o in observations[:20])
            prompt = f"""用一句话总结这次会话做了什么（不超过 50 字）。

操作记录：
{obs_text}"""
            try:
                result = llm_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1, max_tokens=100
                )
                from llm import LLMClient as LC
                summary = LC.extract_response(result).get("content") or "".strip()
                if summary:
                    # 保存为会话摘要
                    self.remember(
                        content=summary,
                        category="summary",
                        source=f"session:{session_id}",
                        importance=6,
                        tags=session_id
                    )
                    return summary
            except Exception:  # 操作失败静默跳过
                pass

        # Fallback: 直接拼接
        summary = "; ".join(observations[:5])
        if len(summary) > 200:
            summary = summary[:200] + "..."
        self.remember(
            content=summary,
            category="summary",
            source=f"session:{session_id}",
            importance=5,
            tags=session_id
        )
        return summary

    # ═══════════════════════════════════════════════
    # 自动提取（借鉴 Supermemory/Cognee）
    # ═══════════════════════════════════════════════

    def extract_from_conversation(self, messages: List[Dict], llm_client=None):
        """从对话中自动提取事实、偏好、决策。"""
        if not llm_client or len(messages) < 3:
            return

        # 构建提取 prompt
        recent = messages[-6:]  # 最近 6 条消息
        text = "\n".join(
            f"{m.get('role', 'unknown')}: {m.get('content', '')[:300]}"
            for m in recent if m.get("content")
        )

        if len(text) < 50:
            return

        extract_prompt = f"""从以下对话中提取关键信息，输出 JSON 数组。
每项格式: {{"content": "事实描述", "category": "fact/preference/decision/lesson", "importance": 1-10}}
只提取明确提到的信息，不推测。最多 5 项。无则输出空数组 []。

对话：
{text[:2000]}"""

        try:
            from llm import LLMClient
            result = llm_client.chat(
                messages=[{"role": "user", "content": extract_prompt}],
                temperature=0.1, max_tokens=500
            )
            from llm import LLMClient as LC
            content = LC.extract_response(result).get("content", "[]").strip()
            # 提取 JSON
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
            pass  # 提取失败静默跳过

    # ═══════════════════════════════════════════════
    # 记忆合并（借鉴 mem0 consolidation）
    # ═══════════════════════════════════════════════

    def consolidate(self):
        """合并重复/过时记忆，释放空间。"""
        with sqlite3.connect(str(self.db_path)) as conn:
            # 删除低重要性且从未被访问的过时记忆（30天前）
            cutoff = (datetime.now() - timedelta(days=30)).isoformat()
            conn.execute(
                "DELETE FROM memories WHERE importance < 4 AND access_count = 0 AND created_at < ?",
                (cutoff,)
            )
            # 合并同 category 同 tags 的重复记忆
            duplicates = conn.execute("""
                SELECT tags, category, COUNT(*) as cnt
                FROM memories
                WHERE tags != ''
                GROUP BY tags, category
                HAVING cnt > 1
            """).fetchall()
            for tags, cat, cnt in duplicates:
                # 保留最新的，删除旧的
                rows = conn.execute(
                    "SELECT id FROM memories WHERE tags=? AND category=? ORDER BY updated_at DESC",
                    (tags, cat)
                ).fetchall()
                if len(rows) > 1:
                    ids_to_delete = [r[0] for r in rows[1:]]
                    conn.execute(
                        f"DELETE FROM memories WHERE id IN ({','.join('?' * len(ids_to_delete))})",
                        ids_to_delete
                    )

    # ═══════════════════════════════════════════════
    # 查询接口
    # ═══════════════════════════════════════════════

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
            conv_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            profile_count = conn.execute("SELECT COUNT(*) FROM user_profile").fetchone()[0]
            total_tokens = conn.execute("SELECT COALESCE(SUM(tokens), 0) FROM memories").fetchone()[0]
        return {
            "total_memories": total,
            "by_category": dict(by_cat),
            "conversations": conv_count,
            "profile_keys": profile_count,
            "total_tokens": total_tokens,
        }

    def forget(self, key: str):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM memories WHERE content LIKE ?", (f"{key}:%",))
            conn.execute("DELETE FROM user_profile WHERE key = ?", (key,))

    def recall_key(self, key: str) -> Optional[str]:
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute("SELECT value FROM user_profile WHERE key = ?", (key,)).fetchone()
            if row:
                return row[0]
            row = conn.execute(
                "SELECT content FROM memories WHERE content LIKE ? LIMIT 1",
                (f"{key}:%",)
            ).fetchone()
            if row:
                return row[0].split(":", 1)[1].strip()
            return None
