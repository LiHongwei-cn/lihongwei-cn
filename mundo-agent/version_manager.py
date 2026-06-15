"""蒙多版本管理系统 v1.0

自动版本递增规则：
- patch: 末尾十进制递增（v1.0.0 → v1.0.1）
- minor: 升级10个patch后递增（v1.0.9 → v1.1.0）
- major: 升级100个minor后递增（v1.99.0 → v2.0.0）

版本号格式：v{major}.{minor}.{patch}
"""

import json
import sqlite3
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime


class VersionManager:
    """版本管理器 — 自动递增版本号"""

    def __init__(self, db_path: Path = None):
        from constants import MUNDO_HOME
        self.db_path = db_path or (MUNDO_HOME / "version.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化版本数据库"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS version_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    major INTEGER NOT NULL,
                    minor INTEGER NOT NULL,
                    patch INTEGER NOT NULL,
                    release_date TEXT NOT NULL,
                    release_notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            
            # 如果没有版本记录，初始化为 v2.1.1
            cursor = conn.execute("SELECT COUNT(*) FROM version_history")
            if cursor.fetchone()[0] == 0:
                now = datetime.now().isoformat()
                conn.execute(
                    "INSERT INTO version_history (version, major, minor, patch, release_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("v2.1.1", 2, 1, 1, now, now)
                )

    def get_current_version(self) -> Tuple[int, int, int]:
        """获取当前版本号"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT major, minor, patch FROM version_history ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return row[0], row[1], row[2]
            return 2, 1, 1  # 默认版本

    def get_version_string(self) -> str:
        """获取版本字符串"""
        major, minor, patch = self.get_current_version()
        return f"v{major}.{minor}.{patch}"

    def increment_patch(self, release_notes: str = "") -> str:
        """递增 patch 版本"""
        major, minor, patch = self.get_current_version()
        patch += 1
        
        # 检查是否需要递增 minor
        if patch >= 10:
            patch = 0
            minor += 1
            
            # 检查是否需要递增 major
            if minor >= 100:
                minor = 0
                major += 1
        
        return self._save_version(major, minor, patch, release_notes)

    def increment_minor(self, release_notes: str = "") -> str:
        """递增 minor 版本"""
        major, minor, patch = self.get_current_version()
        minor += 1
        patch = 0
        
        # 检查是否需要递增 major
        if minor >= 100:
            minor = 0
            major += 1
        
        return self._save_version(major, minor, patch, release_notes)

    def increment_major(self, release_notes: str = "") -> str:
        """递增 major 版本"""
        major, minor, patch = self.get_current_version()
        major += 1
        minor = 0
        patch = 0
        
        return self._save_version(major, minor, patch, release_notes)

    def _save_version(self, major: int, minor: int, patch: int, release_notes: str = "") -> str:
        """保存新版本"""
        version = f"v{major}.{minor}.{patch}"
        now = datetime.now().isoformat()
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT INTO version_history (version, major, minor, patch, release_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (version, major, minor, patch, now, now)
            )
        
        # 更新 constants.py 中的版本号
        self._update_constants_version(version)
        
        return version

    def _update_constants_version(self, version: str):
        """更新 constants.py 中的版本号"""
        constants_path = Path(__file__).parent / "constants.py"
        if not constants_path.exists():
            return
        
        content = constants_path.read_text()
        
        # 替换版本号
        import re
        pattern = r'VERSION\s*=\s*["\'][^"\']+["\']'
        replacement = f'VERSION = "{version}"'
        
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            constants_path.write_text(new_content)

    def get_version_history(self, limit: int = 10) -> list:
        """获取版本历史"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT version, release_date, release_notes FROM version_history ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return [{"version": row[0], "date": row[1], "notes": row[2]} for row in cursor.fetchall()]


# 全局版本管理器实例
_version_manager = None


def get_version_manager() -> VersionManager:
    """获取全局版本管理器"""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager


def get_current_version() -> str:
    """获取当前版本字符串"""
    return get_version_manager().get_version_string()


def increment_version(level: str = "patch", release_notes: str = "") -> str:
    """递增版本号
    
    Args:
        level: 递增级别 ("patch", "minor", "major")
        release_notes: 发布说明
    
    Returns:
        新版本号字符串
    """
    manager = get_version_manager()
    
    if level == "patch":
        return manager.increment_patch(release_notes)
    elif level == "minor":
        return manager.increment_minor(release_notes)
    elif level == "major":
        return manager.increment_major(release_notes)
    else:
        raise ValueError(f"无效的版本递增级别: {level}")


def auto_increment_on_changes(changes: list) -> str:
    """根据变更自动递增版本号
    
    Args:
        changes: 变更列表，每个变更是一个字典，包含 type 和 description
    
    Returns:
        新版本号字符串
    """
    # 分析变更类型
    has_breaking = any(c.get("type") == "breaking" for c in changes)
    has_feature = any(c.get("type") == "feature" for c in changes)
    has_fix = any(c.get("type") == "fix" for c in changes)
    
    # 决定递增级别
    if has_breaking:
        level = "major"
    elif has_feature:
        level = "minor"
    else:
        level = "patch"
    
    # 生成发布说明
    notes = []
    for change in changes:
        if change.get("description"):
            notes.append(f"- {change['description']}")
    
    release_notes = "\n".join(notes) if notes else ""
    
    return increment_version(level, release_notes)