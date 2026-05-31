# -*- coding: utf-8 -*-
"""对话历史管理器：为每个 chat 维护上下文记忆"""
import time
from collections import defaultdict
from typing import Optional


class ChatHistory:
    """管理多用户对话历史，自动清理过期记录"""

    MAX_MESSAGES = 20          # 每个 chat 最多保留的消息数
    EXPIRE_SECONDS = 3600      # 1 小时无活动自动清除

    def __init__(self):
        self._histories: dict[int, list[dict]] = defaultdict(list)
        self._last_active: dict[int, float] = {}

    def add(self, chat_id: int, role: str, content) -> None:
        """添加一条消息到历史"""
        self._histories[chat_id].append({"role": role, "content": content})
        self._last_active[chat_id] = time.time()
        # 超限时裁剪（保留 system prompt 在调用侧处理）
        if len(self._histories[chat_id]) > self.MAX_MESSAGES:
            self._histories[chat_id] = self._histories[chat_id][-self.MAX_MESSAGES:]

    def get(self, chat_id: int) -> list[dict]:
        """获取历史消息（不含 system prompt）"""
        self._cleanup_if_expired(chat_id)
        return list(self._histories.get(chat_id, []))

    def clear(self, chat_id: int) -> None:
        """清除指定 chat 的历史"""
        self._histories.pop(chat_id, None)
        self._last_active.pop(chat_id, None)

    def _cleanup_if_expired(self, chat_id: int) -> None:
        last = self._last_active.get(chat_id, 0)
        if last and (time.time() - last > self.EXPIRE_SECONDS):
            self.clear(chat_id)

    @property
    def active_chats(self) -> int:
        return len(self._histories)
