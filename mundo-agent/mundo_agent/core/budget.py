"""蒙多预算控制 — 重构版

改进：
- 更清晰的接口
- 性能优化
- 类型安全
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IterationBudget:
    """Token 预算控制"""

    max_prompt_tokens: int = 500000
    max_completion_tokens: int = 200000
    max_turns: int = 0  # 0 = 无限制
    warn_threshold: float = 0.7

    # 运行时状态
    prompt_tokens_used: int = 0
    completion_tokens_used: int = 0
    turns_used: int = 0
    _warned: bool = field(default=False, repr=False)

    @property
    def remaining(self) -> int:
        """剩余 prompt tokens"""
        return max(0, self.max_prompt_tokens - self.prompt_tokens_used)

    @property
    def usage_ratio(self) -> float:
        """使用率"""
        if self.max_prompt_tokens == 0:
            return 0
        return self.prompt_tokens_used / self.max_prompt_tokens

    @property
    def should_warn(self) -> bool:
        """是否应该警告"""
        return self.usage_ratio >= self.warn_threshold and not self._warned

    @property
    def exhausted(self) -> bool:
        """是否耗尽"""
        if self.prompt_tokens_used >= self.max_prompt_tokens:
            return True
        if self.completion_tokens_used >= self.max_completion_tokens:
            return True
        if self.max_turns > 0 and self.turns_used >= self.max_turns:
            return True
        return False

    def update(self, prompt_tokens: int = 0, completion_tokens: int = 0):
        """更新使用量"""
        self.prompt_tokens_used += prompt_tokens
        self.completion_tokens_used += completion_tokens
        self.turns_used += 1

    def mark_warned(self):
        """标记已警告"""
        self._warned = True

    def reset(self):
        """重置"""
        self.prompt_tokens_used = 0
        self.completion_tokens_used = 0
        self.turns_used = 0
        self._warned = False