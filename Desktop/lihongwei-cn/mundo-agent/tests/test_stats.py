"""任务统计单元测试"""

import time
import pytest
from mundo_agent.core.stats import TaskStats


class TestTaskStats:
    """TaskStats 测试"""

    def test_default_values(self):
        """测试默认值"""
        stats = TaskStats()
        assert stats.turns == 0
        assert stats.total_tokens == 0
        assert stats.prompt_tokens == 0
        assert stats.completion_tokens == 0
        assert stats.tool_calls_count == 0
        assert stats.llm_time == 0.0
        assert stats.tool_time == 0.0
        assert stats.errors_count == 0
        assert stats.retries_count == 0

    def test_elapsed(self):
        """测试已用时间"""
        stats = TaskStats()
        time.sleep(0.1)
        assert stats.elapsed > 0

    def test_elapsed_str_seconds(self):
        """测试格式化时间（秒）"""
        stats = TaskStats()
        stats.start_time = time.time() - 30
        assert "30s" in stats.elapsed_str or "29s" in stats.elapsed_str

    def test_elapsed_str_minutes(self):
        """测试格式化时间（分钟）"""
        stats = TaskStats()
        stats.start_time = time.time() - 150
        assert "2m" in stats.elapsed_str

    def test_reset(self):
        """测试重置"""
        stats = TaskStats()

        # 修改一些值
        stats.turns = 5
        stats.total_tokens = 1000
        stats.prompt_tokens = 800
        stats.completion_tokens = 200
        stats.tool_calls_count = 3
        stats.llm_time = 10.0
        stats.tool_time = 5.0
        stats.errors_count = 2
        stats.retries_count = 1

        # 重置
        stats.reset()

        assert stats.turns == 0
        assert stats.total_tokens == 0
        assert stats.prompt_tokens == 0
        assert stats.completion_tokens == 0
        assert stats.tool_calls_count == 0
        assert stats.llm_time == 0.0
        assert stats.tool_time == 0.0
        assert stats.errors_count == 0
        assert stats.retries_count == 0

    def test_update_tokens(self):
        """测试更新 token"""
        stats = TaskStats()

        stats.update_tokens(prompt=100, completion=50)
        assert stats.prompt_tokens == 100
        assert stats.completion_tokens == 50
        assert stats.total_tokens == 150

        stats.update_tokens(prompt=200, completion=100)
        assert stats.prompt_tokens == 300
        assert stats.completion_tokens == 150
        assert stats.total_tokens == 450

    def test_update_tokens_zero(self):
        """测试更新零 token"""
        stats = TaskStats()

        stats.update_tokens(prompt=0, completion=0)
        assert stats.prompt_tokens == 0
        assert stats.completion_tokens == 0
        assert stats.total_tokens == 0

    def test_add_tool_call(self):
        """测试添加工具调用"""
        stats = TaskStats()

        stats.add_tool_call("terminal")
        assert stats.tool_calls_count == 1
        assert "terminal" in stats._active_tools

        stats.add_tool_call("read_file")
        assert stats.tool_calls_count == 2
        assert "read_file" in stats._active_tools

    def test_add_error(self):
        """测试添加错误"""
        stats = TaskStats()

        stats.add_error()
        assert stats.errors_count == 1

        stats.add_error()
        assert stats.errors_count == 2

    def test_add_retry(self):
        """测试添加重试"""
        stats = TaskStats()

        stats.add_retry()
        assert stats.retries_count == 1

        stats.add_retry()
        assert stats.retries_count == 2

    def test_integration(self):
        """集成测试：模拟完整任务流程"""
        stats = TaskStats()

        # 模拟任务执行
        stats.turns = 1
        stats.update_tokens(prompt=1000, completion=500)
        stats.add_tool_call("terminal")
        stats.add_tool_call("read_file")
        stats.llm_time = 2.5
        stats.tool_time = 1.0

        # 验证状态
        assert stats.turns == 1
        assert stats.total_tokens == 1500
        assert stats.tool_calls_count == 2
        assert stats.llm_time == 2.5
        assert stats.tool_time == 1.0
        assert stats.errors_count == 0
        assert stats.retries_count == 0

        # 模拟第二轮
        stats.turns = 2
        stats.update_tokens(prompt=2000, completion=1000)
        stats.add_tool_call("web_search")
        stats.add_error()

        # 验证累积状态
        assert stats.turns == 2
        assert stats.total_tokens == 4500
        assert stats.tool_calls_count == 3
        assert stats.errors_count == 1