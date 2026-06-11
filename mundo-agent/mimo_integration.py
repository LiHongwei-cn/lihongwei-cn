"""蒙多 MiMo 集成 v2.1.0 — 融合 MiMo-Code 核心特性

整合自小米开源的 MiMo-Code：
- 跨会话记忆系统（SQLite FTS5 + BM25 评分）
- 智能上下文管理（检查点 + 预算化注入 + 上下文重建）
- 任务追踪系统（树状任务 + 进度持久化）
- Goal/停止条件（防止"乐观停止"）
- Dream & Distill（自动学习和技能提取）
"""

import os
import json
import sqlite3
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# ═══════════════════════════════════════════════
# 常量定义
# ═══════════════════════════════════════════════

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
CHECKPOINT_DB = MUNDO_HOME / "checkpoint.db"
MEMORY_DB = MUNDO_HOME / "memory.db"
TASKS_DIR = MUNDO_HOME / "tasks"

# Checkpoint 模板（11 个 section）
CHECKPOINT_SECTIONS = [
    "§1 Active intent",
    "§2 Next concrete action",
    "§3 Directives (this session)",
    "§4 Task tree",
    "§5 Current work",
    "§6 Files and code sections",
    "§7 Discovered knowledge (cross-task)",
    "§8 Errors and fixes",
    "§9 Live resources",
    "§10 Design decisions and discussion outcomes",
    "§11 Open notes",
]

# Memory 模板（4 个 section）
MEMORY_SECTIONS = [
    "Project context",
    "Rules",
    "Architecture decisions",
    "Discovered durable knowledge",
]

# 每个 section 的 token 预算
CHECKPOINT_SECTION_BUDGETS = {
    "§1 Active intent": 500,
    "§2 Next concrete action": 1000,
    "§3 Directives (this session)": 800,
    "§4 Task tree": 1000,
    "§5 Current work": 2000,
    "§6 Files and code sections": 1500,
    "§7 Discovered knowledge (cross-task)": 2000,
    "§8 Errors and fixes": 1500,
    "§9 Live resources": 1000,
    "§10 Design decisions and discussion outcomes": 3000,
    "§11 Open notes": 800,
}

MEMORY_SECTION_BUDGETS = {
    "Project context": 1000,
    "Rules": 2000,
    "Architecture decisions": 3000,
    "Discovered durable knowledge": 4000,
}


# ═══════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════

@dataclass
class Checkpoint:
    """会话检查点"""
    session_id: str
    timestamp: float
    sections: Dict[str, str] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Task:
    """树状任务"""
    id: str
    title: str
    status: str = "open"  # open / in_progress / blocked / done / abandoned
    parent_id: Optional[str] = None
    progress_file: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class Goal:
    """停止条件"""
    session_id: str
    condition: str
    judge_model: Optional[str] = None
    created_at: float = field(default_factory=time.time)


# ═══════════════════════════════════════════════
# Checkpoint 管理器
# ═══════════════════════════════════════════════

class CheckpointManager:
    """会话检查点管理器 — 实现 MiMo-Code 的 11-section checkpoint 系统"""

    def __init__(self, db_path: Path = CHECKPOINT_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                sections_json TEXT NOT NULL,
                metadata_json TEXT,
                UNIQUE(session_id, timestamp)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_session
            ON checkpoints(session_id, timestamp DESC)
        """)
        conn.commit()
        conn.close()

    def save(self, checkpoint: Checkpoint) -> bool:
        """保存检查点"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                """INSERT OR REPLACE INTO checkpoints
                   (session_id, timestamp, sections_json, metadata_json)
                   VALUES (?, ?, ?, ?)""",
                (
                    checkpoint.session_id,
                    checkpoint.timestamp,
                    json.dumps(checkpoint.sections, ensure_ascii=False),
                    json.dumps(checkpoint.metadata, ensure_ascii=False),
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[Checkpoint 保存失败] {e}")
            return False

    def load_latest(self, session_id: str) -> Optional[Checkpoint]:
        """加载最新的检查点"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute(
                """SELECT timestamp, sections_json, metadata_json
                   FROM checkpoints WHERE session_id = ?
                   ORDER BY timestamp DESC LIMIT 1""",
                (session_id,),
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return Checkpoint(
                    session_id=session_id,
                    timestamp=row[0],
                    sections=json.loads(row[1]),
                    metadata=json.loads(row[2]) if row[2] else {},
                )
            return None
        except Exception as e:
            print(f"[Checkpoint 加载失败] {e}")
            return None

    def list_sessions(self, limit: int = 10) -> List[str]:
        """列出最近的会话 ID"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute(
                """SELECT DISTINCT session_id FROM checkpoints
                   ORDER BY MAX(timestamp) DESC LIMIT ?""",
                (limit,),
            )
            sessions = [row[0] for row in cursor.fetchall()]
            conn.close()
            return sessions
        except Exception as e:
            print(f"[Checkpoint 列表失败] {e}")
            return []

    def format_checkpoint(self, checkpoint: Checkpoint) -> str:
        """格式化检查点为可读文本"""
        lines = [f"# Session checkpoint ({datetime.fromtimestamp(checkpoint.timestamp)})\n"]
        for section in CHECKPOINT_SECTIONS:
            content = checkpoint.sections.get(section, "(none yet)")
            lines.append(f"## {section}\n{content}\n")
        return "\n".join(lines)


# ═══════════════════════════════════════════════
# Memory 管理器（SQLite FTS5）
# ═══════════════════════════════════════════════

class MemoryManager:
    """项目记忆管理器 — 实现 MiMo-Code 的 FTS5 全文搜索"""

    def __init__(self, db_path: Path = MEMORY_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化 FTS5 数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        # FTS5 虚拟表用于全文搜索
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                content, scope, scope_id, type,
                content='memory',
                content_rowid='id'
            )
        """)
        # 触发器保持 FTS 索引同步
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON memory BEGIN
                INSERT INTO memory_fts(rowid, content, scope, scope_id, type)
                VALUES (new.id, new.content, new.scope, new.scope_id, new.type);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memory_ad AFTER DELETE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, content, scope, scope_id, type)
                VALUES ('delete', old.id, old.content, old.scope, old.scope_id, old.type);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memory_au AFTER UPDATE ON memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, content, scope, scope_id, type)
                VALUES ('delete', old.id, old.content, old.scope, old.scope_id, old.type);
                INSERT INTO memory_fts(rowid, content, scope, scope_id, type)
                VALUES (new.id, new.content, new.scope, new.scope_id, new.type);
            END
        """)
        conn.commit()
        conn.close()

    def add(self, scope: str, scope_id: str, type: str, content: str) -> bool:
        """添加记忆条目"""
        try:
            now = time.time()
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                """INSERT INTO memory (scope, scope_id, type, content, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (scope, scope_id, type, content, now, now),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[Memory 添加失败] {e}")
            return False

    def search(self, query: str, scope: Optional[str] = None,
               scope_id: Optional[str] = None, type: Optional[str] = None,
               limit: int = 10) -> List[Dict]:
        """全文搜索记忆"""
        try:
            # 构建 FTS5 查询
            fts_query = self._build_fts_query(query)
            if not fts_query:
                return []

            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            # 构建过滤条件
            conditions = []
            params = []
            if scope:
                conditions.append("memory_fts.scope = ?")
                params.append(scope)
            if scope_id:
                conditions.append("memory_fts.scope_id = ?")
                params.append(scope_id)
            if type:
                conditions.append("memory_fts.type = ?")
                params.append(type)

            where_clause = f"AND {' AND '.join(conditions)}" if conditions else ""

            # 执行搜索（使用 BM25 评分）
            cursor = conn.execute(
                f"""SELECT memory.*, bm25(memory_fts) as score
                    FROM memory_fts
                    JOIN memory ON memory.id = memory_fts.rowid
                    WHERE memory_fts MATCH ? {where_clause}
                    ORDER BY score
                    LIMIT ?""",
                [fts_query] + params + [limit],
            )

            results = []
            rows = cursor.fetchall()
            if rows:
                # 使用相对阈值过滤噪声
                max_score = abs(rows[0]["score"])
                threshold = max_score * 0.15

                for row in rows:
                    if abs(row["score"]) >= threshold or len(results) == 0:
                        results.append({
                            "id": row["id"],
                            "scope": row["scope"],
                            "scope_id": row["scope_id"],
                            "type": row["type"],
                            "content": row["content"],
                            "score": row["score"],
                            "created_at": row["created_at"],
                        })

            conn.close()
            return results
        except Exception as e:
            print(f"[Memory 搜索失败] {e}")
            return []

    def _build_fts_query(self, query: str) -> str:
        """构建 FTS5 查询（token 级别，短语引用）"""
        import re
        # 提取字母数字 token
        tokens = re.findall(r'[a-zA-Z0-9\u4e00-\u9fff]+', query)
        if not tokens:
            return ""
        # 每个 token 用双引号包裹，OR 连接
        return " OR ".join(f'"{t}"' for t in tokens)

    def update(self, memory_id: int, content: str) -> bool:
        """更新记忆条目"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                """UPDATE memory SET content = ?, updated_at = ?
                   WHERE id = ?""",
                (content, time.time(), memory_id),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[Memory 更新失败] {e}")
            return False

    def delete(self, memory_id: int) -> bool:
        """删除记忆条目"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("DELETE FROM memory WHERE id = ?", (memory_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[Memory 删除失败] {e}")
            return False


# ═══════════════════════════════════════════════
# 任务追踪系统
# ═══════════════════════════════════════════════

class TaskTracker:
    """树状任务追踪系统 — 实现 MiMo-Code 的任务管理"""

    def __init__(self, tasks_dir: Path = TASKS_DIR):
        self.tasks_dir = tasks_dir
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def create(self, task_id: str, title: str, parent_id: Optional[str] = None) -> Task:
        """创建任务"""
        task = Task(
            id=task_id,
            title=title,
            parent_id=parent_id,
            progress_file=str(self.tasks_dir / f"{task_id}" / "progress.md"),
        )
        # 保存任务元数据
        task_dir = self.tasks_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        with open(task_dir / "task.json", "w", encoding="utf-8") as f:
            json.dump({
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "parent_id": task.parent_id,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }, f, ensure_ascii=False, indent=2)
        # 创建进度文件
        with open(task.progress_file, "w", encoding="utf-8") as f:
            f.write(f"# Task {task_id}: {title}\n\n## Progress\n\n(none yet)\n")
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        task_dir = self.tasks_dir / task_id
        json_file = task_dir / "task.json"
        if not json_file.exists():
            return None
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Task(**data)

    def update_status(self, task_id: str, status: str) -> bool:
        """更新任务状态"""
        task = self.get(task_id)
        if not task:
            return False
        task.status = status
        task.updated_at = time.time()
        task_dir = self.tasks_dir / task_id
        with open(task_dir / "task.json", "w", encoding="utf-8") as f:
            json.dump({
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "parent_id": task.parent_id,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }, f, ensure_ascii=False, indent=2)
        return True

    def add_progress(self, task_id: str, content: str) -> bool:
        """添加进度记录"""
        task = self.get(task_id)
        if not task:
            return False
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(task.progress_file, "a", encoding="utf-8") as f:
            f.write(f"\n### [{timestamp}]\n{content}\n")
        return True

    def list_tasks(self, parent_id: Optional[str] = None) -> List[Task]:
        """列出任务"""
        tasks = []
        for task_dir in self.tasks_dir.iterdir():
            if task_dir.is_dir():
                task = self.get(task_dir.name)
                if task and task.parent_id == parent_id:
                    tasks.append(task)
        return sorted(tasks, key=lambda t: t.created_at)

    def format_tree(self, parent_id: Optional[str] = None, indent: int = 0) -> str:
        """格式化任务树"""
        tasks = self.list_tasks(parent_id)
        lines = []
        for task in tasks:
            status_icon = {
                "open": "🔵",
                "in_progress": "🔄",
                "blocked": "🟡",
                "done": "✅",
                "abandoned": "❌",
            }.get(task.status, "❓")
            prefix = "  " * indent
            lines.append(f"{prefix}{status_icon} {task.id}: {task.title}")
            # 递归显示子任务
            children = self.format_tree(task.id, indent + 1)
            if children:
                lines.append(children)
        return "\n".join(lines)


# ═══════════════════════════════════════════════
# Goal 系统（防止"乐观停止"）
# ═══════════════════════════════════════════════

class GoalManager:
    """Goal/停止条件管理器 — 实现 MiMo-Code 的防乐观停止机制"""

    def __init__(self, db_path: Path = CHECKPOINT_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                condition TEXT NOT NULL,
                judge_model TEXT,
                created_at REAL NOT NULL,
                UNIQUE(session_id)
            )
        """)
        conn.commit()
        conn.close()

    def set_goal(self, session_id: str, condition: str, judge_model: Optional[str] = None) -> bool:
        """设置停止条件"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(
                """INSERT OR REPLACE INTO goals
                   (session_id, condition, judge_model, created_at)
                   VALUES (?, ?, ?, ?)""",
                (session_id, condition, judge_model, time.time()),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[Goal 设置失败] {e}")
            return False

    def get_goal(self, session_id: str) -> Optional[Goal]:
        """获取停止条件"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute(
                """SELECT condition, judge_model, created_at
                   FROM goals WHERE session_id = ?""",
                (session_id,),
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return Goal(
                    session_id=session_id,
                    condition=row[0],
                    judge_model=row[1],
                    created_at=row[2],
                )
            return None
        except Exception as e:
            print(f"[Goal 获取失败] {e}")
            return None

    def check_goal(self, session_id: str, conversation: str, llm_client) -> Tuple[bool, str]:
        """检查是否满足停止条件（使用裁判模型）"""
        goal = self.get_goal(session_id)
        if not goal:
            return False, "未设置停止条件"

        # 使用裁判模型评估
        judge_model = goal.judge_model or "deepseek-chat"
        prompt = f"""你是一个裁判。请评估以下对话是否满足停止条件。

停止条件：{goal.condition}

对话内容：
{conversation[:2000]}

请只回复：
- "SATISFIED" - 如果条件已满足
- "NOT_SATISFIED" - 如果条件未满足
- "PARTIALLY" - 如果部分满足

然后简要说明原因。"""

        try:
            result = llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100,
            )
            content = result.get("content", "")
            if "SATISFIED" in content and "NOT" not in content:
                return True, content
            return False, content
        except Exception as e:
            return False, f"[裁判评估失败] {e}"


# ═══════════════════════════════════════════════
# Dream & Distill 系统
# ═══════════════════════════════════════════════

class DreamDistill:
    """Dream & Distill 系统 — 实现 MiMo-Code 的自动学习和技能提取"""

    def __init__(self, memory_mgr: MemoryManager, checkpoint_mgr: CheckpointManager):
        self.memory_mgr = memory_mgr
        self.checkpoint_mgr = checkpoint_mgr

    def dream(self, session_id: str, llm_client) -> Dict:
        """Dream — 扫描近期会话轨迹，提取持久知识"""
        # 加载最新的 checkpoint
        checkpoint = self.checkpoint_mgr.load_latest(session_id)
        if not checkpoint:
            return {"success": False, "error": "无可用 checkpoint"}

        # 提取 §7 Discovered knowledge
        discovered = checkpoint.sections.get("§7 Discovered knowledge (cross-task)", "(none yet)")
        if discovered == "(none yet)":
            return {"success": True, "extracted": 0, "message": "无新知识可提取"}

        # 使用 LLM 分析并提取值得持久化的知识
        prompt = f"""分析以下会话中发现的知识，提取值得跨会话持久化的事实。

发现的知识：
{discovered}

请以 JSON 格式返回要保存的知识列表：
[
  {{"type": "fact", "content": "事实描述"}},
  {{"type": "rule", "content": "规则描述"}},
  {{"type": "architecture", "content": "架构决策"}}
]

只返回 JSON，不要其他内容。"""

        try:
            result = llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            content = result.get("content", "[]")
            # 解析 JSON
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group())
                saved = 0
                for item in items:
                    if self.memory_mgr.add(
                        scope="project",
                        scope_id="default",
                        type=item.get("type", "fact"),
                        content=item.get("content", ""),
                    ):
                        saved += 1
                return {"success": True, "extracted": saved}
            return {"success": True, "extracted": 0}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def distill(self, session_id: str, llm_client) -> Dict:
        """Distill — 发现重复工作流，打包成可复用的 skill"""
        # 加载最新的 checkpoint
        checkpoint = self.checkpoint_mgr.load_latest(session_id)
        if not checkpoint:
            return {"success": False, "error": "无可用 checkpoint"}

        # 分析 §5 Current work 和 §8 Errors and fixes
        current_work = checkpoint.sections.get("§5 Current work", "")
        errors_fixes = checkpoint.sections.get("§8 Errors and fixes", "")

        prompt = f"""分析以下工作内容，发现可以打包成可复用 skill 的重复工作流。

当前工作：
{current_work}

错误和修复：
{errors_fixes}

请以 JSON 格式返回发现的 skill 候选：
[
  {{
    "name": "skill-name",
    "description": "skill 描述",
    "trigger": "触发条件",
    "steps": ["步骤1", "步骤2"]
  }}
]

只返回 JSON，不要其他内容。"""

        try:
            result = llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
            )
            content = result.get("content", "[]")
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                skills = json.loads(json_match.group())
                return {"success": True, "candidates": skills}
            return {"success": True, "candidates": []}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════
# 预算化注入系统
# ═══════════════════════════════════════════════

class BudgetedInjector:
    """预算化注入系统 — 实现 MiMo-Code 的上下文管理"""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """估算 token 数量（中英文混合约 2.5 字符/token）"""
        return int(len(text) * 0.4)

    @staticmethod
    def truncate_to_budget(text: str, budget_tokens: int) -> Tuple[str, bool]:
        """截断文本到指定 token 预算"""
        estimated = BudgetedInjector.estimate_tokens(text)
        if estimated <= budget_tokens:
            return text, False

        # 按比例截断
        ratio = budget_tokens / estimated
        truncated = text[:int(len(text) * ratio * 0.95)]
        # 在最后一个换行符处截断
        last_newline = truncated.rfind("\n")
        if last_newline > 0:
            truncated = truncated[:last_newline]

        hint = f"\n\n⚠️ 已截断至约 {budget_tokens} token。原文约 {estimated} token。"
        return truncated + hint, True

    @staticmethod
    def inject_checkpoint(checkpoint: Checkpoint, total_budget: int = 11000) -> str:
        """按预算注入 checkpoint 内容"""
        lines = [f"# Session checkpoint\n"]
        remaining_budget = total_budget

        for section in CHECKPOINT_SECTIONS:
            content = checkpoint.sections.get(section, "(none yet)")
            section_budget = CHECKPOINT_SECTION_BUDGETS.get(section, 500)

            # 从剩余预算中分配
            actual_budget = min(section_budget, remaining_budget)
            if actual_budget <= 0:
                break

            truncated, was_truncated = BudgetedInjector.truncate_to_budget(content, actual_budget)
            remaining_budget -= BudgetedInjector.estimate_tokens(truncated)

            lines.append(f"## {section}\n{truncated}\n")

        return "\n".join(lines)

    @staticmethod
    def inject_memory(memory_entries: List[Dict], total_budget: int = 10000) -> str:
        """按预算注入 memory 内容"""
        lines = ["# Project memory\n"]
        remaining_budget = total_budget

        for entry in memory_entries:
            content = entry.get("content", "")
            entry_budget = min(500, remaining_budget)
            if entry_budget <= 0:
                break

            truncated, _ = BudgetedInjector.truncate_to_budget(content, entry_budget)
            remaining_budget -= BudgetedInjector.estimate_tokens(truncated)

            lines.append(f"- [{entry.get('type', 'fact')}] {truncated}\n")

        return "\n".join(lines)


# ═══════════════════════════════════════════════
# 统一接口
# ═══════════════════════════════════════════════

class MiMoIntegration:
    """MiMo 集成统一接口"""

    def __init__(self):
        self.checkpoint_mgr = CheckpointManager()
        self.memory_mgr = MemoryManager()
        self.task_tracker = TaskTracker()
        self.goal_mgr = GoalManager()
        self.dream_distill = DreamDistill(self.memory_mgr, self.checkpoint_mgr)
        self.budgeted_injector = BudgetedInjector()

    def save_checkpoint(self, session_id: str, sections: Dict[str, str],
                        metadata: Optional[Dict] = None) -> bool:
        """保存检查点"""
        checkpoint = Checkpoint(
            session_id=session_id,
            timestamp=time.time(),
            sections=sections,
            metadata=metadata or {},
        )
        return self.checkpoint_mgr.save(checkpoint)

    def load_checkpoint(self, session_id: str) -> Optional[Checkpoint]:
        """加载检查点"""
        return self.checkpoint_mgr.load_latest(session_id)

    def search_memory(self, query: str, **kwargs) -> List[Dict]:
        """搜索记忆"""
        return self.memory_mgr.search(query, **kwargs)

    def add_memory(self, content: str, type: str = "fact",
                   scope: str = "project", scope_id: str = "default") -> bool:
        """添加记忆"""
        return self.memory_mgr.add(scope, scope_id, type, content)

    def create_task(self, task_id: str, title: str, **kwargs) -> Task:
        """创建任务"""
        return self.task_tracker.create(task_id, title, **kwargs)

    def set_goal(self, session_id: str, condition: str, **kwargs) -> bool:
        """设置停止条件"""
        return self.goal_mgr.set_goal(session_id, condition, **kwargs)

    def check_goal(self, session_id: str, conversation: str, llm_client) -> Tuple[bool, str]:
        """检查停止条件"""
        return self.goal_mgr.check_goal(session_id, conversation, llm_client)

    def dream(self, session_id: str, llm_client) -> Dict:
        """执行 Dream（提取持久知识）"""
        return self.dream_distill.dream(session_id, llm_client)

    def distill(self, session_id: str, llm_client) -> Dict:
        """执行 Distill（发现可复用 skill）"""
        return self.dream_distill.distill(session_id, llm_client)

    def get_context(self, session_id: str, memory_query: Optional[str] = None,
                    checkpoint_budget: int = 11000,
                    memory_budget: int = 10000) -> str:
        """获取上下文（预算化注入）"""
        parts = []

        # 1. 注入 checkpoint
        checkpoint = self.load_checkpoint(session_id)
        if checkpoint:
            checkpoint_text = self.budgeted_injector.inject_checkpoint(checkpoint, checkpoint_budget)
            parts.append(checkpoint_text)

        # 2. 注入相关 memory
        if memory_query:
            memory_entries = self.search_memory(memory_query, limit=10)
            if memory_entries:
                memory_text = self.budgeted_injector.inject_memory(memory_entries, memory_budget)
                parts.append(memory_text)

        return "\n\n---\n\n".join(parts)


# 全局实例
_mimo_integration: Optional[MiMoIntegration] = None


def get_mimo_integration() -> MiMoIntegration:
    """获取全局 MiMo 集成实例"""
    global _mimo_integration
    if _mimo_integration is None:
        _mimo_integration = MiMoIntegration()
    return _mimo_integration
