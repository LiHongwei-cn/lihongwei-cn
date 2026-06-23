"""core.py 单元测试 — v3.2.0"""

import pytest
import time
from unittest.mock import MagicMock

# 测试 _classify_error
from core import _classify_error, IterationBudget, TaskStats


class TestClassifyError:
    """错误分类测试"""

    def test_connection_reset(self):
        result = _classify_error(ConnectionResetError(), "connection reset")
        assert result["category"] == "connection"
        assert result["retryable"] is True
        assert "重试" in result["user_tip"]

    def test_timeout_error(self):
        result = _classify_error(TimeoutError(), "timed out")
        assert result["category"] == "timeout"
        assert result["retryable"] is True

    def test_auth_401(self):
        result = _classify_error(RuntimeError("401"), "unauthorized")
        assert result["category"] == "auth"
        assert result["retryable"] is False
        assert "API key" in result["user_tip"]

    def test_rate_limit_429(self):
        result = _classify_error(RuntimeError("429"), "too many requests")
        assert result["category"] == "rate_limit"
        assert result["retryable"] is True

    def test_server_500(self):
        result = _classify_error(RuntimeError("500"), "internal server error")
        assert result["category"] == "server"
        assert result["retryable"] is True

    def test_unknown_error(self):
        result = _classify_error(ValueError("something weird"), "something weird")
        assert result["category"] == "unknown"
        assert result["retryable"] is False

    def test_dns_error(self):
        result = _classify_error(RuntimeError("dns"), "dns failure")
        assert result["category"] == "network"
        assert result["retryable"] is True

    def test_chinese_timeout_message(self):
        result = _classify_error(RuntimeError(""), "请求超时")
        assert result["category"] == "timeout"
        assert result["retryable"] is True


class TestIterationBudget:
    """预算管理测试"""

    def test_initial_state(self):
        b = IterationBudget(max_prompt_tokens=1000, max_completion_tokens=500)
        assert b.remaining == 1000
        assert b.usage_ratio == 0.0
        assert b.exhausted is False
        assert b.should_warn is False

    def test_update_and_remaining(self):
        b = IterationBudget(max_prompt_tokens=1000)
        b.update(prompt_tokens=400, completion_tokens=100)
        assert b.remaining == 600
        assert b.prompt_tokens_used == 400
        assert b.turns_used == 1

    def test_exhausted_by_prompt(self):
        b = IterationBudget(max_prompt_tokens=1000)
        b.update(prompt_tokens=1000)
        assert b.exhausted is True

    def test_exhausted_by_completion(self):
        b = IterationBudget(max_prompt_tokens=1000, max_completion_tokens=500)
        b.update(prompt_tokens=0, completion_tokens=500)
        assert b.exhausted is True

    def test_exhausted_by_turns(self):
        b = IterationBudget(max_turns=3)
        for _ in range(3):
            b.update()
        assert b.exhausted is True

    def test_warn_threshold(self):
        b = IterationBudget(max_prompt_tokens=1000, warn_threshold=0.5)
        b.update(prompt_tokens=600)
        assert b.should_warn is True
        assert b.exhausted is False

    def test_warn_once(self):
        b = IterationBudget(max_prompt_tokens=1000, warn_threshold=0.5)
        b.update(prompt_tokens=600)
        assert b.should_warn is True
        b.mark_warned()
        assert b.should_warn is False

    def test_reset(self):
        b = IterationBudget(max_prompt_tokens=1000)
        b.update(prompt_tokens=900)
        b.mark_warned()
        b.reset()
        assert b.remaining == 1000
        assert b.turns_used == 0
        assert b.should_warn is False

    def test_unlimited_turns(self):
        b = IterationBudget(max_turns=0)
        for _ in range(100):
            b.update()
        assert b.exhausted is False

    def test_usage_ratio(self):
        b = IterationBudget(max_prompt_tokens=1000)
        b.update(prompt_tokens=350)
        assert b.usage_ratio == 0.35


class TestTaskStats:
    """任务统计测试"""

    def test_initial_state(self):
        s = TaskStats()
        assert s.turns == 0
        assert s.total_tokens == 0
        assert s.errors_count == 0
        assert s.retries_count == 0

    def test_elapsed_increases(self):
        s = TaskStats()
        time.sleep(0.1)
        assert s.elapsed > 0

    def test_elapsed_str_format(self):
        s = TaskStats()
        result = s.elapsed_str
        assert "s" in result  # 刚创建，应该是秒

    def test_reset(self):
        s = TaskStats()
        s.turns = 10
        s.total_tokens = 5000
        s.errors_count = 3
        s.reset()
        assert s.turns == 0
        assert s.total_tokens == 0
        assert s.errors_count == 0
        assert s.start_time <= time.time()
