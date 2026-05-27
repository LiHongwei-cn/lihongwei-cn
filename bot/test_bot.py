"""端到端测试：直接调用 handler 函数，验证 bot 核心逻辑
运行: python -m pytest test_bot.py -v
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("TELEGRAM_TOKEN", "PLACEHOLDER_TELEGRAM_TOKEN")
os.environ.setdefault("DEEPSEEK_API_KEY", "PLACEHOLDER_DEEPSEEK_KEY")

from tgbot import (
    start_cmd, help_cmd, mundo_cmd, handle_message, handle_photo,
    error_handler, _split_long_msg, _load_system_prompt,
    _search_github, _search_stackoverflow, _mundo_search,
    MUNDO_KEYWORDS,
)


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
    assert "".join(chunks) == "A" * 5000


def test_split_exact_boundary():
    chunks = _split_long_msg("B" * 4096)
    assert len(chunks) == 1


# ─── /start 命令 ───


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
async def test_start_command(mock_save):
    update = make_mock_update("/start")
    ctx = make_mock_context()

    await start_cmd(update, ctx)

    mock_save.assert_called_once_with(update.effective_chat.id)
    update.message.reply_text.assert_called_once()
    args = update.message.reply_text.call_args[0]
    assert "就绪" in args[0]
    assert "/mundo" in args[0]


# ─── /help 命令 ───


@pytest.mark.asyncio
async def test_help_command():
    update = make_mock_update("/help")
    ctx = make_mock_context()

    await help_cmd(update, ctx)

    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert "蒙多" in reply
    assert "/mundo" in reply


# ─── /mundo 命令 ───


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
async def test_mundo_no_args(mock_save):
    """无参数时显示用法"""
    update = make_mock_update("/mundo")
    ctx = make_mock_context(args=[])

    await mundo_cmd(update, ctx)

    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert "蒙多" in reply
    assert "用法" in reply


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
@patch("tgbot._mundo_search", new_callable=AsyncMock, return_value="GitHub 搜索结果")
@patch("tgbot._call_deepseek", new_callable=AsyncMock, return_value="蒙多的回答")
async def test_mundo_with_query(mock_ai, mock_search, mock_save):
    """有参数时搜索 + AI 回复"""
    update = make_mock_update("/mundo Python 爬虫 403")
    ctx = make_mock_context(args=["Python", "爬虫", "403"])

    await mundo_cmd(update, ctx)

    mock_save.assert_called_once()
    mock_search.assert_called_once_with("Python 爬虫 403")
    # 两次回复：搜索中提示 + AI 回复
    assert update.message.reply_text.call_count == 2


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
@patch("tgbot._mundo_search", new_callable=AsyncMock, return_value="")
@patch("tgbot._call_deepseek", new_callable=AsyncMock, return_value="蒙多的回答")
async def test_mundo_no_search_results(mock_ai, mock_search, mock_save):
    """搜索无结果时仍给出 AI 回复"""
    update = make_mock_update("/mundo 非常冷门的问题")
    ctx = make_mock_context(args=["非常冷门的问题"])

    await mundo_cmd(update, ctx)

    assert update.message.reply_text.call_count == 2


# ─── 文字消息（蒙多关键词自动触发） ───


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
@patch("tgbot._mundo_search", new_callable=AsyncMock, return_value="搜索结果")
@patch("tgbot._call_deepseek", new_callable=AsyncMock, return_value="回复")
async def test_mundo_auto_trigger(mock_ai, mock_search, mock_save):
    """说「蒙多」自动激活学习模式"""
    update = make_mock_update("蒙多帮我看看这个bug")
    ctx = make_mock_context()

    await handle_message(update, ctx)

    mock_search.assert_called_once()
    # 有蒙多 banner + AI 回复
    assert update.message.reply_text.call_count == 2


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
@patch("tgbot._mundo_search", new_callable=AsyncMock, return_value="搜索结果")
@patch("tgbot._call_deepseek", new_callable=AsyncMock, return_value="回复")
async def test_mundo_trigger_stuck(mock_ai, mock_search, mock_save):
    """说「卡住了」自动激活"""
    update = make_mock_update("这个报错我卡住了")
    ctx = make_mock_context()

    await handle_message(update, ctx)

    mock_search.assert_called_once()


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
@patch("tgbot._mundo_search", new_callable=AsyncMock)
@patch("tgbot._call_deepseek", new_callable=AsyncMock, return_value="回复")
async def test_normal_message_no_mundo(mock_ai, mock_search, mock_save):
    """普通消息不触发蒙多"""
    update = make_mock_update("今天天气怎么样")
    ctx = make_mock_context()

    await handle_message(update, ctx)

    mock_search.assert_not_called()
    update.message.reply_text.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
async def test_handle_message_success(mock_save):
    """真实调用 DeepSeek API — 跳过: pytest -m 'not integration'"""
    update = make_mock_update("什么是FOC控制？一句话回答")
    ctx = make_mock_context()

    await handle_message(update, ctx)

    mock_save.assert_called_once()
    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert len(reply) > 5


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
async def test_handle_message_api_error(mock_save):
    """模拟 API 错误时给用户友好提示"""
    update = make_mock_update("测试错误处理")
    ctx = make_mock_context()

    with patch("tgbot.client.chat.completions.create", AsyncMock(side_effect=Exception("网络错误"))):
        await handle_message(update, ctx)

    update.message.reply_text.assert_called_once()
    reply = update.message.reply_text.call_args[0][0]
    assert "出错" in reply or "再试" in reply


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
async def test_handle_message_long_reply(mock_save):
    """模拟长回复分段发送"""
    update = make_mock_update("写一篇5000字的论文")
    ctx = make_mock_context()

    long_reply = "内容" * 2500
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = long_reply
    mock_create = AsyncMock(return_value=mock_resp)

    with patch("tgbot.client.chat.completions.create", mock_create):
        await handle_message(update, ctx)

    assert update.message.reply_text.call_count > 1


# ─── 图片消息 ───


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
async def test_handle_photo(mock_save):
    """测试图片处理"""
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

    mock_save.assert_called_once()
    update.message.reply_text.assert_called_once_with("图片分析结果")


@pytest.mark.asyncio
@patch("tgbot._save_chat_id")
async def test_handle_photo_error(mock_save):
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


# ─── 搜索函数 ───


@pytest.mark.asyncio
@patch("tgbot.http_client.get", new_callable=AsyncMock)
async def test_search_github_success(mock_get):
    """GitHub 搜索成功"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "items": [
            {"full_name": "user/repo", "stargazers_count": 100, "description": "测试仓库"},
        ]
    }
    mock_get.return_value = mock_resp

    result = await _search_github("python爬虫")
    assert "GitHub" in result
    assert "user/repo" in result


@pytest.mark.asyncio
@patch("tgbot.http_client.get", new_callable=AsyncMock)
async def test_search_github_error(mock_get):
    """GitHub 搜索失败时返回空"""
    mock_get.side_effect = Exception("网络错误")
    result = await _search_github("test")
    assert result == ""


@pytest.mark.asyncio
@patch("tgbot.http_client.get", new_callable=AsyncMock)
async def test_search_so_success(mock_get):
    """SO 搜索成功"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "items": [
            {"title": "How to fix 403", "score": 50, "answer_count": 3, "link": "https://so.com/q/1"},
        ]
    }
    mock_get.return_value = mock_resp

    result = await _search_stackoverflow("403 error")
    assert "Stack Overflow" in result
    assert "403" in result


@pytest.mark.asyncio
@patch("tgbot._search_github", new_callable=AsyncMock, return_value="GitHub 结果")
@patch("tgbot._search_stackoverflow", new_callable=AsyncMock, return_value="SO 结果")
async def test_mundo_search_parallel(mock_so, mock_gh):
    """蒙多搜索并行执行"""
    result = await _mundo_search("test query")
    assert "GitHub" in result
    assert "SO" in result
    mock_gh.assert_called_once()
    mock_so.assert_called_once()


# ─── 错误处理 ───


@pytest.mark.asyncio
async def test_error_handler():
    update = object()
    ctx = MagicMock()
    ctx.error = ValueError("测试错误")

    with patch("tgbot.logger") as mock_logger:
        await error_handler(update, ctx)

    mock_logger.error.assert_called_once()
