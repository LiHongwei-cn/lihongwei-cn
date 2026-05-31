# -*- coding: utf-8 -*-
"""简单的滑动窗口速率限制器"""
import time
from collections import defaultdict, deque


class RateLimiter:
    """每个用户每分钟最多 N 次请求"""

    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[int, deque] = defaultdict(deque)

    def is_allowed(self, user_id: int) -> bool:
        """检查是否允许请求，同时记录请求"""
        now = time.time()
        q = self._requests[user_id]
        # 清理窗口外的记录
        while q and q[0] < now - self.window:
            q.popleft()
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True

    def remaining(self, user_id: int) -> int:
        now = time.time()
        q = self._requests[user_id]
        while q and q[0] < now - self.window:
            q.popleft()
        return max(0, self.max_requests - len(q))
