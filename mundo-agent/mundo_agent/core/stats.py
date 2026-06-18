"""蒙多任务统计 — 重构版

改进：
- 使用 dataclass
- 更清晰的接口
- 性能优化
"""

import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class TaskStats:
    """任务统计数据"""

    # 时间
    start_time: float = field(default_factory=time.time)

    # 轮次和 token
    turns: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    # 工具调用
    tool_calls_count: int = 0
    _active_tools: List[str] = field(default_factory=list, repr=False)

    # 时间统计
    llm_time: float = 0.0
    tool_time: float = 0.0

    # 错误统计
    errors_count: int = 0
    retries_count: int = 0

    @property
    def elapsed(self) -> float:
        """已用时间（秒）"""
        return time.time() - self.start_time

    @property
    def elapsed_str(self) -> str:
        """格式化的已用时间"""
        s = self.elapsed
        if s < 60:
            return f"{int(s)}s"
        m = int(s // 60)
        return f"{m}m{int(s - m*60)}s"

    def reset(self):
        """重置统计"""
        self.start_time = time.time()
        self.turns = 0
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.tool_calls_count = 0
        self._active_tools = []
        self.llm_time = 0.0
        self.tool_time = 0.0
        self.errors_count = 0
        self.retries_count = 0

    def update_tokens(self, prompt: int = 0, completion: int = 0):
        """更新 token 统计"""
        if prompt > 0:
            self.prompt_tokens += prompt
        if completion > 0:
            self.completion_tokens += completion
        self.total_tokens = self.prompt_tokens + self.completion_tokens

    def add_tool_call(self, tool_name: str):
        """记录工具调用"""
        self.tool_calls_count += 1
        self._active_tools.append(tool_name)

    def add_error(self):
        """记录错误"""
        self.errors_count += 1

    def add_retry(self):
        """记录重试"""
        self.retries_count += 1