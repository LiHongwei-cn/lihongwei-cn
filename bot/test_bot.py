"""
端到端测试：直接调用 handler 函数，验证 bot 核心逻辑
运行: python3 -m pytest test_bot.py -v
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("TELEGRAM_TOKEN", "PLACEHOLDER_TELEGRAM_TOKEN")
os.environ.setdefault("DEEPSEEK_API_KEY", "PLACEHOLDER_DEEPSEEK_KEY")

from tgbot import start_cmd, handle_message, handle_photo, error_handler, _split_long_msg


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


def make_mock_context() -> AsyncMock:
    ctx = AsyncMock()
    ctx.bot = AsyncMock()
    ctx.bot.send_chat_action = AsyncMock()
    ctx.args = []
    return ctx


# ─── 长消息分段 ───


def test_split_short_message():
    chunks = _split_long_msg("短消息")
    assert len(chunks) == 1
    assert chunks[0] == "短消息"


def test_split_long_ascii():
    chunks = _split_long_msg("A" * 5000)
    assert len(chunks) > 1
    assert all(len(c) <= 4096 for c in chunks)
    assert "".join(chunks) == "A" * 5000


def test_split_exact_boundary():
    chunks = _split_long_msg("B" * 4096)
    assert len(chunks) == 1


# ─── /start 命令 ───


@pytest.mark.asyncio
async def test_start_command():
    update = make_mock_update("/start")
    ctx = make_mock_context()

    await start_cmd(update, ctx)

    ctx.bot.send_chat_action.assert_not_called()  # /start 不需要 typing
    update.message.reply_text.assert_called_once()
    args = update.message.reply_text.call_args[0]
    assert "就绪" in args[0] or "Bot" in args[0]


# ─── 文字消息 ───


@pytest.mark.integration
@pytest.mark.asyncio
async def test_handle_message_success():
    """真实调用 DeepSeek API — 跳过: pytest -m 'not integration'"""
    update = make_mock_update("什么是FOC控制？一句话回答")
    ctx = make_mock_context()

    await handle_message(update, ctx)

    ctx.bot.send_chat_action.assert_called_once_with(
        chat_id=update.effective_chat.id, action="typing"
    )
    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert len(reply) > 5
    print(f"\n  DeepSeek 回复: {reply[:100]}...")


@pytest.mark.asyncio
async def test_handle_message_api_error():
    """模拟 API 错误时给用户友好提示"""
    update = make_mock_update("测试错误处理")
    ctx = make_mock_context()

    with patch("tgbot.client.chat.completions.create", AsyncMock(side_effect=Exception("网络错误"))):
        await handle_message(update, ctx)

    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert "出错" in reply or "再试" in reply
    print(f"\n  错误提示: {reply}")


@pytest.mark.asyncio
async def test_handle_message_long_reply():
    """模拟长回复分段发送"""
    update = make_mock_update("写一篇5000字的论文")
    ctx = make_mock_context()

    long_reply = "内容" * 2500  # 5000 字符
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = long_reply
    mock_create = AsyncMock(return_value=mock_resp)

    with patch("tgbot.client.chat.completions.create", mock_create):
        await handle_message(update, ctx)

    call_count = update.message.reply_text.call_count
    print(f"\n  分段发送次数: {call_count}")
    assert call_count > 1


# ─── 图片消息 ───


@pytest.mark.asyncio
async def test_handle_photo():
    """测试图片处理（mock 掉 API 和 Telegram 文件下载）"""
    update = AsyncMock()
    update.effective_user = FakeUser()
    update.effective_chat = FakeChat()
    update.message.caption = "分析这张图"
    update.message.message_id = 2

    photo_mock = MagicMock()
    photo_mock.file_id = "fake_file_id"
    update.message.photo = [photo_mock]

    ctx = make_mock_context()
    file_mock = MagicMock()
    file_mock.file_path = "photos/file_0.jpg"
    file_mock.download_as_bytearray = AsyncMock(return_value=b"\xff\xd8\xff")
    ctx.bot.get_file = AsyncMock(return_value=file_mock)

    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = "图片分析结果"
    with patch("tgbot.client.chat.completions.create", AsyncMock(return_value=mock_resp)):
        await handle_photo(update, ctx)

    ctx.bot.send_chat_action.assert_called_once()
    update.message.reply_text.assert_called_once_with("图片分析结果")


@pytest.mark.asyncio
async def test_handle_photo_error():
    """测试图片处理错误"""
    update = AsyncMock()
    update.effective_user = FakeUser()
    update.effective_chat = FakeChat()
    update.message.caption = ""
    update.message.message_id = 3

    photo_mock = MagicMock()
    photo_mock.file_id = "fake_file_id"
    update.message.photo = [photo_mock]

    ctx = make_mock_context()
    file_mock = MagicMock()
    file_mock.file_path = "photos/file_0.png"
    file_mock.download_as_bytearray = AsyncMock(return_value=b"\x89PNG")
    ctx.bot.get_file = AsyncMock(return_value=file_mock)

    with patch("tgbot.client.chat.completions.create", AsyncMock(side_effect=Exception("API 超时"))):
        await handle_photo(update, ctx)

    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert "出错" in reply or "再试" in reply


# ─── 错误处理 ───


@pytest.mark.asyncio
async def test_error_handler():
    update = object()
    ctx = MagicMock()
    ctx.error = ValueError("测试错误")

    with patch("tgbot.logger") as mock_logger:
        await error_handler(update, ctx)

    mock_logger.error.assert_called_once()
