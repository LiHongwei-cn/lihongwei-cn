"""记忆系统单元测试"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from mundo_agent.memory.manager import DatabaseManager
from mundo_agent.memory.mundo_memory import MundoMemory


class TestDatabaseManager:
    """DatabaseManager 测试"""

    def setup_method(self):
        """每个测试前重置单例"""
        DatabaseManager._instance = None
        DatabaseManager._connection = None

    def test_singleton(self, tmp_path):
        """测试单例模式"""
        db_path = tmp_path / "test.db"
        manager1 = DatabaseManager(db_path)
        manager2 = DatabaseManager(db_path)
        assert manager1 is manager2

    def test_connection(self, tmp_path):
        """测试数据库连接"""
        db_path = tmp_path / "test.db"
        manager = DatabaseManager(db_path)

        with manager.get_connection() as conn:
            assert conn is not None

    def test_execute(self, tmp_path):
        """测试执行查询"""
        db_path = tmp_path / "test.db"
        manager = DatabaseManager(db_path)

        manager.executescript("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                name TEXT
            );
        """)

        manager.execute("INSERT INTO test (name) VALUES (?)", ("test",))
        result = manager.fetchone("SELECT name FROM test WHERE id = 1")
        assert result[0] == "test"

    def test_fetchall(self, tmp_path):
        """测试获取所有结果"""
        db_path = tmp_path / "test.db"
        manager = DatabaseManager(db_path)

        manager.executescript("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                name TEXT
            );
        """)

        manager.execute("INSERT INTO test (name) VALUES (?)", ("test1",))
        manager.execute("INSERT INTO test (name) VALUES (?)", ("test2",))

        results = manager.fetchall("SELECT name FROM test ORDER BY id")
        assert len(results) == 2
        assert results[0][0] == "test1"
        assert results[1][0] == "test2"

    def test_close(self, tmp_path):
        """测试关闭连接"""
        db_path = tmp_path / "test.db"
        manager = DatabaseManager(db_path)
        manager.close()
        assert manager._connection is None


class TestMundoMemory:
    """MundoMemory 测试"""

    def test_init(self, tmp_path):
        """测试初始化"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)
        assert memory.db is not None

    def test_remember_and_recall(self, tmp_path):
        """测试记住和回忆"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)

        # 记住
        mid = memory.remember("测试内容", category="fact", importance=7)
        assert mid > 0

        # 回忆
        result = memory.recall("测试", max_items=5)
        assert "测试内容" in result

    def test_remember_fact(self, tmp_path):
        """测试记住事实"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)

        memory.remember_fact("name", "mundo")
        result = memory.recall_key("name")
        assert result == "mundo"

    def test_remember_preference(self, tmp_path):
        """测试记住偏好"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)

        memory.remember_preference("theme", "dark")
        profile = memory.get_profile()
        assert profile.get("theme") == "dark"

    def test_forget(self, tmp_path):
        """测试遗忘"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)

        memory.remember_fact("temp", "value")
        memory.forget("temp")
        result = memory.recall_key("temp")
        assert result is None

    def test_get_stats(self, tmp_path):
        """测试获取统计"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)

        memory.remember("记忆1", category="fact")
        memory.remember("记忆2", category="preference")

        stats = memory.get_stats()
        assert stats["total_memories"] >= 2
        assert "fact" in stats["by_category"]
        assert "preference" in stats["by_category"]

    def test_auto_extract(self, tmp_path):
        """测试自动提取"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)

        # 测试提取"记住"
        extracted = memory.auto_extract("记住我的邮箱是 test@example.com", "")
        assert len(extracted) > 0

        # 测试提取"我喜欢"
        extracted = memory.auto_extract("我喜欢用 VS Code", "")
        assert len(extracted) > 0

    def test_save_conversation(self, tmp_path):
        """测试保存对话"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)

        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"},
        ]

        memory.save_conversation(
            conv_id="test_123",
            title="测试对话",
            summary="测试摘要",
            messages=messages
        )

        results = memory.search_conversations("测试")
        assert len(results) > 0
        assert results[0]["title"] == "测试对话"

    def test_consolidate(self, tmp_path):
        """测试记忆整理"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)

        # 添加重复记忆
        memory.remember("重复内容", category="fact")
        memory.remember("重复内容", category="fact")

        result = memory.consolidate()
        assert "duplicates_removed" in result
        assert "expired_removed" in result

    def test_get_context_budget(self, tmp_path):
        """测试获取上下文预算"""
        db_path = tmp_path / "test.db"
        memory = MundoMemory(db_path)

        memory.remember_fact("name", "mundo")
        memory.remember_preference("theme", "dark")

        context = memory.get_context_budget("你好")
        assert context  # 应该返回一些内容