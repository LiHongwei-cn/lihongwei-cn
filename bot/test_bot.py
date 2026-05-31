# -*- coding: utf-8 -*-
"""端到端测试：验证 bot 核心逻辑（优化版）
运行: python -m pytest test_bot.py -v
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("TELEGRAM_TOKEN", "PLACEHOLDER_TELEGRAM_TOKEN")
os.environ.setdefault("DEEPSEEK_API_KEY", "PLACEHOLDER_DEEPSEEK_KEY")

from tgbot import (
    start_cmd, help_cmd, mundo_cmd, clear_cmd,
    handle_message, handle_photo, unknown_cmd,
    error_handler, _split_long_msg, _load_system_prompt,
    _search_github, _search_stackoverflow, _mundo_search,
    MUNDO_KEYWORDS,
)
from chat_history import ChatHistory
from rate_limiter import RateLimiter


class FakeUser:
    def __init__(self, uid=123456):
        self.id = uid


class FakeChat:
    def __init__(self, cid=123456):
        self.id = cid


def make_mock_update(text: str) -> AsyncMock:
    update = AsyncMock()
    update.effective_user = FakeUser()
    update.effective_chat = FakeChat()
    update.message.text = text
    update.message.message_id = 1
    return update


def make_mock_context(args=None) -> AsyncMock:
    ctx = AsyncMock()
    ctx.bot = AsyncMock()
    ctx.bot.send_chat_action = AsyncMock()
    ctx.args = args or []
    return ctx


# ─── 系统提示词 ───


def test_system_prompt_loaded():
    prompt = _load_system_prompt()
    assert len(prompt) > 50
    assert "蒙多" in prompt


def test_mundo_keywords_match():
    assert MUNDO_KEYWORDS.search("蒙多帮我看看")
    assert MUNDO_KEYWORDS.search("我卡住了")
    assert MUNDO_KEYWORDS.search("报错了怎么办")
    assert MUNDO_KEYWORDS.search("Mundo learn this")
    assert not MUNDO_KEYWORDS.search("今天天气不错")


# ─── 长消息分段 ───


def test_split_short_message():
    chunks = _split_long_msg("短消息")
    assert len(chunks) == 1
    assert chunks[0] == "短消息"


def test_split_long_ascii():
    chunks = _split_long_msg("A" * 5000)
    assert len(chunks) > 1
    assert all(len(c) <= 4096 for c in chunks)


def test_split_exact_boundary():
    chunks = _split_long_msg("B" * 4096)
    assert len(chunks) == 1


# ─── 对话历史 ───


class TestChatHistory:
    def setup_method(self):
        self.history = ChatHistory()

    def test_add_and_get(self):
        self.history.add(1, "user", "你好")
        self.history.add(1, "assistant", "你好！")
        msgs = self.history.get(1)
        assert len(msgs) == 2
        assert msgs[0]["content"] == "你好"

    def test_max_messages_limit(self):
        for i in range(30):
            self.history.add(1, "user", f"msg{i}")
        msgs = self.history.get(1)
        assert len(msgs) <= ChatHistory.MAX_MESSAGES

    def test_clear(self):
        self.history.add(1, "user", "你好")
        self.history.clear(1)
        assert len(self.history.get(1)) == 0

    def test_separate_chats(self):
        self.history.add(1, "user", "chat1")
        self.history.add(2, "user", "chat2")
        assert len(self.history.get(1)) == 1
        assert len(self.history.get(2)) == 1


# ─── 速率限制 ───


class TestRateLimiter:
    def setup_method(self):
        self.limiter = RateLimiter(max_requests=3, window_seconds=60)

    def test_under_limit(self):
        assert self.limiter.is_allowed(1)
        assert self.limiter.is_allowed(1)
        assert self.limiter.is_allowed(1)

    def test_over_limit(self):
        for _ in range(3):
            self.limiter.is_allowed(1)
        assert not self.limiter.is_allowed(1)

    def test_remaining(self):
        self.limiter.is_allowed(1)
        assert self.limiter.remaining(1) == 2


# ─── /start 命令 ───


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
async def test_start_command(mock_save):
    update = make_mock_update("/start")
    ctx = make_mock_context()
    await start_cmd(update, ctx)
    mock_save.assert_called_once()
    update.message.reply_text.assert_called_once()
    args = update.message.reply_text.call_args[0]
    assert "就绪" in args[0]


# ─── /clear 命令 ───


@pytest.mark.asyncio
async def test_clear_command():
    update = make_mock_update("/clear")
    ctx = make_mock_context()
    await clear_cmd(update, ctx)
    update.message.reply_text.assert_called_once()
    assert "清除" in update.message.reply_text.call_args[0][0]


# ─── /help 命令 ───


@pytest.mark.asyncio
async def test_help_command():
    update = make_mock_update("/help")
    ctx = make_mock_context()
    await help_cmd(update, ctx)
    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert "/mundo" in reply


# ─── /mundo 命令 ───


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
@patch("tgbot._mundo_search", new_callable=AsyncMock, return_value="GitHub 搜索结果")
@patch("tgbot._call_deepseek", new_callable=AsyncMock, return_value="蒙多的回答")
async def test_mundo_with_query(mock_ai, mock_search, mock_save):
    update = make_mock_update("/mundo Python 爬虫 403")
    ctx = make_mock_context(args=["Python", "爬虫", "403"])
    await mundo_cmd(update, ctx)
    mock_save.assert_called_once()
    mock_search.assert_called_once()
    assert update.message.reply_text.call_count == 2


# ─── 文字消息 ───


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
@patch("tgbot._mundo_search", new_callable=AsyncMock, return_value="搜索结果")
@patch("tgbot._call_deepseek", new_callable=AsyncMock, return_value="回复")
async def test_mundo_auto_trigger(mock_ai, mock_search, mock_save):
    update = make_mock_update("蒙多帮我看看这个bug")
    ctx = make_mock_context()
    await handle_message(update, ctx)
    mock_search.assert_called_once()
    assert update.message.reply_text.call_count == 2


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
@patch("tgbot._call_deepseek", new_callable=AsyncMock, return_value="普通回复")
async def test_normal_message(mock_ai, mock_save):
    update = make_mock_update("今天天气不错")
    ctx = make_mock_context()
    await handle_message(update, ctx)
    mock_ai.assert_called_once()
    update.message.reply_text.assert_called_once()


# ─── 未知命令 ───


@pytest.mark.asyncio
async def test_unknown_command():
    update = make_mock_update("/unknown")
    ctx = make_mock_context()
    await unknown_cmd(update, ctx)
    assert "未知" in update.message.reply_text.call_args[0][0]
