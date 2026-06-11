"""蒙多自进化系统 v2.2.0 — 融合 MiMo-Code 的 Dream & Distill

核心功能：
- Dream: 从会话轨迹中提取持久知识，自动沉淀到项目记忆
- Distill: 发现重复工作流，打包成可复用的 skill/agent/command
- Compaction: 压缩对话历史，保持上下文窗口
- 自进化: 基于使用反馈持续学习与优化
"""

import os
import json
import sqlite3
import time
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════
# 常量定义
# ═══════════════════════════════════════════════

MUNDO_HOME = Path.home() / ".hermes" / "mundo-agent"
TRAJECTORY_DB = MUNDO_HOME / "timeline.db"
MEMORY_DIR = MUNDO_HOME / "memory"
SKILLS_DIR = MUNDO_HOME / "skills"

# 默认时间窗口
DREAM_WINDOW_DAYS = 7
DISTILL_WINDOW_DAYS = 30


# ═══════════════════════════════════════════════
# Dream 系统 — 记忆整合
# ═══════════════════════════════════════════════

class DreamSystem:
    """Dream 系统 — 从会话轨迹中提取持久知识

    实现 MiMo-Code 的 Dream 功能：
    1. 扫描近期会话轨迹
    2. 提取值得跨会话持久化的知识
    3. 整合到项目记忆中
    """

    def __init__(self, memory_db_path: Path = None):
        self.memory_db_path = memory_db_path or (MUNDO_HOME / "memory.db")
        self.trajectory_db_path = TRAJECTORY_DB

    def _get_trajectory_conn(self) -> Optional[sqlite3.Connection]:
        """获取轨迹数据库连接"""
        if not self.trajectory_db_path.exists():
            return None
        try:
            conn = sqlite3.connect(str(self.trajectory_db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    def _get_memory_conn(self) -> Optional[sqlite3.Connection]:
        """获取记忆数据库连接"""
        if not self.memory_db_path.exists():
            return None
        try:
            conn = sqlite3.connect(str(self.memory_db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    def scan_recent_sessions(self, days: int = DREAM_WINDOW_DAYS) -> List[Dict]:
        """扫描近期会话"""
        conn = self._get_trajectory_conn()
        if not conn:
            return []

        try:
            cutoff = time.time() - (days * 86400)
            cursor = conn.execute(
                """SELECT DISTINCT session_id, MAX(timestamp) as last_time
                   FROM events WHERE timestamp > ?
                   GROUP BY session_id ORDER BY last_time DESC""",
                (cutoff,)
            )
            return [{"session_id": row["session_id"], "last_time": row["last_time"]}
                    for row in cursor.fetchall()]
        except Exception:
            return []
        finally:
            conn.close()

    def extract_knowledge_from_events(self, session_id: str) -> List[Dict]:
        """从会话事件中提取知识"""
        conn = self._get_trajectory_conn()
        if not conn:
            return []

        try:
            cursor = conn.execute(
                """SELECT data FROM events
                   WHERE session_id = ?
                   ORDER BY timestamp""",
                (session_id,)
            )
            events = [json.loads(row["data"]) for row in cursor.fetchall() if row["data"]]
        except Exception:
            return []
        finally:
            conn.close()

        knowledge = []

        for event in events:
            # 提取用户明确陈述的规则
            if event.get("role") == "user":
                content = event.get("content", "")
                # 检测规则关键词
                rule_patterns = [
                    r"总是|一直|永远|不要|禁止|必须|一定要",
                    r"always|never|must|don't|should",
                    r"记住|remember|注意|note",
                ]
                for pattern in rule_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        knowledge.append({
                            "type": "rule",
                            "content": content[:200],
                            "source": session_id,
                        })
                        break

            # 提取设计决策
            if event.get("role") == "assistant":
                content = event.get("content", "")
                decision_patterns = [
                    r"决定|选择|采用|使用|decided|chose|adopted",
                    r"因为|由于|原因|because|reason",
                    r"tradeoff|权衡|取舍",
                ]
                for pattern in decision_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        knowledge.append({
                            "type": "architecture",
                            "content": content[:200],
                            "source": session_id,
                        })
                        break

        return knowledge

    def consolidate(self, llm_client, days: int = DREAM_WINDOW_DAYS) -> Dict:
        """执行 Dream 整合"""
        sessions = self.scan_recent_sessions(days)
        if not sessions:
            return {"success": True, "message": "无近期会话可整合", "extracted": 0}

        all_knowledge = []
        for session in sessions[:10]:  # 最多处理 10 个会话
            knowledge = self.extract_knowledge_from_events(session["session_id"])
            all_knowledge.extend(knowledge)

        if not all_knowledge:
            return {"success": True, "message": "无新知识可提取", "extracted": 0}

        # 使用 LLM 分析并去重
        prompt = f"""分析以下从会话轨迹中提取的知识，去重并整合。

提取的知识：
{json.dumps(all_knowledge[:20], ensure_ascii=False, indent=2)}

请以 JSON 格式返回整合后的知识列表：
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
                max_tokens=2000,
            )
            content = result.get("content", "[]")
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group())
                saved = self._save_to_memory(items)
                return {"success": True, "extracted": saved}
            return {"success": True, "extracted": 0}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _save_to_memory(self, items: List[Dict]) -> int:
        """保存知识到记忆数据库"""
        conn = self._get_memory_conn()
        if not conn:
            return 0

        try:
            saved = 0
            for item in items:
                try:
                    conn.execute(
                        """INSERT INTO memory (scope, scope_id, type, content, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        ("project", "default", item.get("type", "fact"),
                         item.get("content", ""), time.time(), time.time())
                    )
                    saved += 1
                except Exception:
                    continue
            conn.commit()
            return saved
        except Exception:
            return 0
        finally:
            conn.close()


# ═══════════════════════════════════════════════
# Distill 系统 — 工作流打包
# ═══════════════════════════════════════════════

class DistillSystem:
    """Distill 系统 — 发现重复工作流并打包成可复用资产

    实现 MiMo-Code 的 Distill 功能：
    1. 扫描近期会话轨迹
    2. 发现重复的工作流
    3. 打包成 skill/agent/command
    """

    def __init__(self, skills_dir: Path = None):
        self.skills_dir = skills_dir or SKILLS_DIR
        self.trajectory_db_path = TRAJECTORY_DB

    def _get_trajectory_conn(self) -> Optional[sqlite3.Connection]:
        """获取轨迹数据库连接"""
        if not self.trajectory_db_path.exists():
            return None
        try:
            conn = sqlite3.connect(str(self.trajectory_db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except Exception:
            return None

    def find_repeated_workflows(self, days: int = DISTILL_WINDOW_DAYS) -> List[Dict]:
        """发现重复工作流"""
        conn = self._get_trajectory_conn()
        if not conn:
            return []

        try:
            cutoff = time.time() - (days * 86400)
            # 查找重复的工具调用
            cursor = conn.execute(
                """SELECT tool_name, COUNT(*) as count
                   FROM events
                   WHERE timestamp > ? AND tool_name IS NOT NULL
                   GROUP BY tool_name
                   HAVING count >= 2
                   ORDER BY count DESC
                   LIMIT 20""",
                (cutoff,)
            )
            repeated_tools = [{"tool": row["tool_name"], "count": row["count"]}
                              for row in cursor.fetchall()]

            # 查找重复的命令序列
            cursor = conn.execute(
                """SELECT data, COUNT(*) as count
                   FROM events
                   WHERE timestamp > ? AND event_type = 'command'
                   GROUP BY data
                   HAVING count >= 2
                   ORDER BY count DESC
                   LIMIT 20""",
                (cutoff,)
            )
            repeated_commands = [{"command": row["data"], "count": row["count"]}
                                 for row in cursor.fetchall()]

            return {
                "repeated_tools": repeated_tools,
                "repeated_commands": repeated_commands,
            }
        except Exception:
            return {"repeated_tools": [], "repeated_commands": []}
        finally:
            conn.close()

    def analyze_workflow_patterns(self, llm_client, days: int = DISTILL_WINDOW_DAYS) -> List[Dict]:
        """分析工作流模式"""
        workflows = self.find_repeated_workflows(days)
        if not workflows.get("repeated_tools") and not workflows.get("repeated_commands"):
            return []

        prompt = f"""分析以下重复的工作流模式，识别可以打包成可复用资产的工作流。

重复的工具调用：
{json.dumps(workflows.get("repeated_tools", [])[:10], ensure_ascii=False)}

重复的命令：
{json.dumps(workflows.get("repeated_commands", [])[:10], ensure_ascii=False)}

请以 JSON 格式返回发现的工作流候选：
[
  {{
    "name": "workflow-name",
    "description": "工作流描述",
    "type": "skill",
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
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception:
            return []

    def create_skill(self, name: str, description: str, steps: List[str]) -> bool:
        """创建 skill 文件"""
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_content = f"""---
name: {name}
description: {description}
---

# {name}

{description}

## 步骤

"""
        for i, step in enumerate(steps, 1):
            skill_content += f"{i}. {step}\n"

        skill_file = skill_dir / "SKILL.md"
        try:
            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(skill_content)
            return True
        except Exception:
            return False

    def distill(self, llm_client, days: int = DISTILL_WINDOW_DAYS) -> Dict:
        """执行 Distill"""
        workflows = self.analyze_workflow_patterns(llm_client, days)
        if not workflows:
            return {"success": True, "message": "未发现可复用的工作流", "created": 0}

        created = 0
        for workflow in workflows:
            if workflow.get("type") == "skill":
                if self.create_skill(
                    workflow.get("name", "unnamed"),
                    workflow.get("description", ""),
                    workflow.get("steps", [])
                ):
                    created += 1

        return {"success": True, "created": created, "candidates": len(workflows)}


# ═══════════════════════════════════════════════
# Compaction 系统 — 上下文压缩
# ═══════════════════════════════════════════════

class CompactionSystem:
    """Compaction 系统 — 压缩对话历史以保持上下文窗口

    实现 MiMo-Code 的 Compaction 功能：
    1. 检测上下文窗口接近上限
    2. 压缩旧的对话历史
    3. 保留关键信息
    """

    MAX_TOKENS = 128000
    COMPACT_THRESHOLD = 0.7  # 70% 时触发压缩

    def __init__(self):
        pass

    def estimate_tokens(self, text: str) -> int:
        """估算 token 数量（中英文混合约 2.5 字符/token）"""
        return int(len(text) * 0.4)

    def should_compact(self, messages: List[Dict]) -> bool:
        """判断是否需要压缩"""
        total_tokens = sum(self.estimate_tokens(json.dumps(m, ensure_ascii=False))
                           for m in messages)
        return total_tokens > (self.MAX_TOKENS * self.COMPACT_THRESHOLD)

    def compact(self, messages: List[Dict], llm_client) -> List[Dict]:
        """压缩对话历史"""
        if not self.should_compact(messages):
            return messages

        # 保留系统消息和最近的消息
        system_messages = [m for m in messages if m.get("role") == "system"]
        recent_messages = messages[-10:]  # 保留最近 10 条
        old_messages = messages[len(system_messages):-10]

        if not old_messages:
            return messages

        # 使用 LLM 压缩旧消息
        old_text = json.dumps(old_messages, ensure_ascii=False)
        prompt = f"""压缩以下对话历史，保留关键信息：

{old_text[:5000]}

请以 JSON 格式返回压缩后的摘要：
{{"summary": "对话摘要", "key_points": ["关键点1", "关键点2"]}}

只返回 JSON，不要其他内容。"""

        try:
            result = llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            content = result.get("content", "{}")
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                summary = json.loads(json_match.group())
                # 创建压缩后的消息
                compacted_message = {
                    "role": "system",
                    "content": f"[历史摘要] {summary.get('summary', '')}\n" +
                               "\n".join(f"- {p}" for p in summary.get("key_points", []))
                }
                return system_messages + [compacted_message] + recent_messages
        except Exception:
            pass

        return messages


# ═══════════════════════════════════════════════
# 自进化系统 — 统一接口
# ═══════════════════════════════════════════════

class EvolutionSystem:
    """自进化系统 — 基于使用反馈持续学习与优化

    实现 MiMo-Code 的自进化功能：
    1. Dream: 从会话轨迹中提取持久知识
    2. Distill: 发现重复工作流并打包成可复用资产
    3. Compaction: 压缩对话历史以保持上下文窗口
    """

    def __init__(self):
        self.dream = DreamSystem()
        self.distill = DistillSystem()
        self.compaction = CompactionSystem()

    def evolve(self, llm_client, days: int = 7) -> Dict:
        """执行自进化"""
        results = {
            "dream": None,
            "distill": None,
            "timestamp": time.time(),
        }

        # 执行 Dream
        results["dream"] = self.dream.consolidate(llm_client, days)

        # 执行 Distill
        results["distill"] = self.distill.distill(llm_client, days * 4)

        return results

    def get_evolution_status(self) -> Dict:
        """获取自进化状态"""
        return {
            "trajectory_db_exists": TRAJECTORY_DB.exists(),
            "memory_dir_exists": MEMORY_DIR.exists(),
            "skills_dir_exists": SKILLS_DIR.exists(),
            "trajectory_db_size": TRAJECTORY_DB.stat().st_size if TRAJECTORY_DB.exists() else 0,
        }


# 全局实例
_evolution_system: Optional[EvolutionSystem] = None


def get_evolution_system() -> EvolutionSystem:
    """获取全局自进化系统实例"""
    global _evolution_system
    if _evolution_system is None:
        _evolution_system = EvolutionSystem()
    return _evolution_system
