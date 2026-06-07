"""预算控制单元测试"""

import pytest
from mundo_agent.core.budget import IterationBudget


class TestIterationBudget:
    """IterationBudget 测试"""

    def test_default_values(self):
        """测试默认值"""
        budget = IterationBudget()
        assert budget.max_prompt_tokens == 500000
        assert budget.max_completion_tokens == 200000
        assert budget.max_turns == 0
        assert budget.warn_threshold == 0.7
        assert budget.prompt_tokens_used == 0
        assert budget.completion_tokens_used == 0
        assert budget.turns_used == 0

    def test_custom_values(self):
        """测试自定义值"""
        budget = IterationBudget(
            max_prompt_tokens=100000,
            max_completion_tokens=50000,
            max_turns=10,
            warn_threshold=0.8
        )
        assert budget.max_prompt_tokens == 100000
        assert budget.max_completion_tokens == 50000
        assert budget.max_turns == 10
        assert budget.warn_threshold == 0.8

    def test_remaining(self):
        """测试剩余 tokens"""
        budget = IterationBudget(max_prompt_tokens=1000)
        assert budget.remaining == 1000

        budget.prompt_tokens_used = 300
        assert budget.remaining == 700

        budget.prompt_tokens_used = 1000
        assert budget.remaining == 0

        budget.prompt_tokens_used = 1500
        assert budget.remaining == 0  # 不应该为负数

    def test_usage_ratio(self):
        """测试使用率"""
        budget = IterationBudget(max_prompt_tokens=1000)
        assert budget.usage_ratio == 0

        budget.prompt_tokens_used = 500
        assert budget.usage_ratio == 0.5

        budget.prompt_tokens_used = 1000
        assert budget.usage_ratio == 1.0

    def test_usage_ratio_zero_max(self):
        """测试最大值为 0 时的使用率"""
        budget = IterationBudget(max_prompt_tokens=0)
        assert budget.usage_ratio == 0

    def test_should_warn(self):
        """测试是否应该警告"""
        budget = IterationBudget(max_prompt_tokens=1000, warn_threshold=0.7)

        budget.prompt_tokens_used = 500
        assert budget.should_warn is False

        budget.prompt_tokens_used = 700
        assert budget.should_warn is True

        # 标记已警告后不再警告
        budget.mark_warned()
        assert budget.should_warn is False

    def test_exhausted_by_prompt_tokens(self):
        """测试 prompt tokens 耗尽"""
        budget = IterationBudget(max_prompt_tokens=1000)

        budget.prompt_tokens_used = 500
        assert budget.exhausted is False

        budget.prompt_tokens_used = 1000
        assert budget.exhausted is True

    def test_exhausted_by_completion_tokens(self):
        """测试 completion tokens 耗尽"""
        budget = IterationBudget(max_completion_tokens=100)

        budget.completion_tokens_used = 50
        assert budget.exhausted is False

        budget.completion_tokens_used = 100
        assert budget.exhausted is True

    def test_exhausted_by_turns(self):
        """测试轮次耗尽"""
        budget = IterationBudget(max_turns=3)

        budget.turns_used = 2
        assert budget.exhausted is False

        budget.turns_used = 3
        assert budget.exhausted is True

    def test_exhausted_no_turn_limit(self):
        """测试无轮次限制"""
        budget = IterationBudget(max_turns=0)

        budget.turns_used = 100
        assert budget.exhausted is False

    def test_update(self):
        """测试更新"""
        budget = IterationBudget()

        budget.update(100, 50)
        assert budget.prompt_tokens_used == 100
        assert budget.completion_tokens_used == 50
        assert budget.turns_used == 1

        budget.update(200, 100)
        assert budget.prompt_tokens_used == 300
        assert budget.completion_tokens_used == 150
        assert budget.turns_used == 2

    def test_reset(self):
        """测试重置"""
        budget = IterationBudget()

        budget.update(100, 50)
        budget.mark_warned()

        budget.reset()

        assert budget.prompt_tokens_used == 0
        assert budget.completion_tokens_used == 0
        assert budget.turns_used == 0
        assert budget.should_warn is False