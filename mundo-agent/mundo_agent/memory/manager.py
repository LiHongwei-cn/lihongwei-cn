"""蒙多记忆系统管理器 — 数据库连接池和优化"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Generator
from ..utils.logging import get_memory_logger
from ..utils.errors import MemoryError

logger = get_memory_logger()


class DatabaseManager:
    """数据库连接管理器 — 连接池和优化"""

    _instance: Optional['DatabaseManager'] = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls, db_path: Optional[Path] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[Path] = None):
        if self._initialized:
            return

        if db_path is None:
            db_path = Path.home() / ".hermes" / "mundo-agent" / "memory.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        self._init_connection()

    def _init_connection(self):
        """初始化数据库连接"""
        try:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30
            )
            # 性能优化
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=NORMAL")
            self._connection.execute("PRAGMA cache_size=10000")
            self._connection.execute("PRAGMA temp_store=MEMORY")
            logger.debug(f"数据库连接已建立: {self.db_path}")
        except sqlite3.Error as e:
            raise MemoryError(f"数据库连接失败: {e}", "init")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接（上下文管理器）"""
        if self._connection is None:
            self._init_connection()
        try:
            yield self._connection
        except sqlite3.Error as e:
            logger.error(f"数据库操作失败: {e}")
            raise MemoryError(f"数据库操作失败: {e}", "query")
        finally:
            # 不关闭连接，保持连接池
            pass

    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """获取数据库游标"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cursor.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行查询"""
        with self.get_cursor() as cursor:
            return cursor.execute(query, params)

    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """执行批量查询"""
        with self.get_cursor() as cursor:
            return cursor.executemany(query, params_list)

    def executescript(self, script: str):
        """执行 SQL 脚本"""
        with self.get_connection() as conn:
            try:
                conn.executescript(script)
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise MemoryError(f"SQL 脚本执行失败: {e}", "script")

    def fetchone(self, query: str, params: tuple = ()):
        """获取单行结果"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()):
        """获取所有结果"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def close(self):
        """关闭数据库连接"""
        if self._connection:
            try:
                self._connection.close()
                logger.debug("数据库连接已关闭")
            except sqlite3.Error as e:
                logger.warning(f"关闭数据库连接时出错: {e}")
            finally:
                self._connection = None

    def __del__(self):
        self.close()


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(db_path: Optional[Path] = None) -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def close_db_manager():
    """关闭全局数据库管理器"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None