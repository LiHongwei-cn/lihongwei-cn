import asyncio
import base64
import logging
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.error import Conflict
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from openai import AsyncOpenAI

from config import get_env

load_dotenv(Path(__file__).with_name(".env"))

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tgbot")

TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = get_env("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = "deepseek-v4-pro"
TELEGRAM_MSG_LIMIT = 4096

SYSTEM_PROMPT_FILE = Path(__file__).with_name("SYSTEM_PROMPT.md")
CHAT_ID_FILE = Path(__file__).parent / "chat_id.txt"

MUNDO_KEYWORDS = re.compile(
    r"蒙多|mundo|卡住了|搞不定|遇到瓶颈|报错|没思路|"
    r"有没有更好的方案|学习一下|参考一下|查一下别人怎么做的",
    re.IGNORECASE,
)

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=60.0,
)

http_client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)


def _load_system_prompt() -> str:
    if SYSTEM_PROMPT_FILE.exists():
        return SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()
    return "你是一个 AI 编程助手。"


SYSTEM_PROMPT = _load_system_prompt()

MUNDO_BANNER = (
    "╔══════════════════════════════════════╗\n"
    "║    🟣 我是蒙多！蒙多想去哪就去哪！  ║\n"
    "╚══════════════════════════════════════╝"
)


# ─── 网络搜索（蒙多学习引擎核心） ───


async def _search_github(query: str) -> str:
    """搜索 GitHub 代码和仓库"""
    try:
        resp = await http_client.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "per_page": 5, "sort": "stars"},
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        if resp.status_code != 200:
            return ""
        data = resp.json()
        results = []
        for repo in data.get("items", [])[:5]:
            stars = repo.get("stargazers_count", 0)
            desc = (repo.get("description") or "")[:80]
            results.append(f"- ⭐{stars} {repo['full_name']}: {desc}")
        if results:
            return "GitHub 热门仓库：\n" + "\n".join(results)
    except Exception as e:
        logger.debug(f"GitHub 搜索失败: {e}")
    return ""


async def _search_stackoverflow(query: str) -> str:
    """搜索 Stack Overflow 问答"""
    try:
        resp = await http_client.get(
            "https://api.stackexchange.com/2.3/search/advanced",
            params={
                "order": "desc",
                "sort": "relevance",
                "q": query,
                "site": "stackoverflow",
                "pagesize": 5,
            },
        )
        if resp.status_code != 200:
            return ""
        data = resp.json()
        results = []
        for item in data.get("items", [])[:5]:
            title = item.get("title", "")
            score = item.get("score", 0)
            answers = item.get("answer_count", 0)
            link = item.get("link", "")
            results.append(f"- [{score}票/{answers}答] {title}\n  {link}")
        if results:
            return "Stack Overflow 相关问答：\n" + "\n".join(results)
    except Exception as e:
        logger.debug(f"SO 搜索失败: {e}")
    return ""


async def _mundo_search(query: str) -> str:
    """蒙多并行搜索：GitHub + Stack Overflow"""
    github_task = _search_github(query)
    so_task = _search_stackoverflow(query)
    github_results, so_results = await asyncio.gather(github_task, so_task)

    parts = []
    if github_results:
        parts.append(github_results)
    if so_results:
        parts.append(so_results)
    return "\n\n".join(parts) if parts else ""


# ─── DeepSeek 调用 ───


async def _call_deepseek(messages: list[dict]) -> str:
    try:
        response = await client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"DeepSeek API 错误: {e}")
        return "请求出错了，稍等片刻再试。"


async def _reply_with_typing(update: Update, context, chat_id: int, reply: str):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    except Exception:
        pass
    for chunk in _split_long_msg(reply):
        await update.message.reply_text(chunk)


def _split_long_msg(text: str) -> list[str]:
    if len(text) <= TELEGRAM_MSG_LIMIT:
        return [text]
    chunks = []
    while len(text) > TELEGRAM_MSG_LIMIT:
        split_at = text.rfind("\n", 0, TELEGRAM_MSG_LIMIT)
        if split_at == -1:
            split_at = TELEGRAM_MSG_LIMIT
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks


def _save_chat_id(chat_id: int):
    if not CHAT_ID_FILE.exists():
        CHAT_ID_FILE.write_text(str(chat_id))
        logger.info(f"已保存 chat_id={chat_id} 到 {CHAT_ID_FILE}")


# ─── 命令处理 ───


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"/start 来自 chat_id={chat_id}")
    _save_chat_id(chat_id)
    await update.message.reply_text(
        "Danking Bot 已就绪。\n\n"
        "直接发消息即可，支持文字和图片。\n\n"
        "命令：\n"
        "/start — 启动\n"
        "/mundo <问题> — 蒙多学习模式\n"
        "/help — 帮助"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Danking Bot — 蒙多 AI 助手\n\n"
        "用法：\n"
        "• 直接发文字 — AI 回复\n"
        "• 发图片（可加描述）— AI 分析图片\n"
        "• /mundo <问题> — 蒙多学习模式\n"
        "  自动搜索 GitHub + Stack Overflow\n"
        "  多源对比，给出最优方案\n"
        "• 说「蒙多」「卡住了」「报错」自动触发\n"
        "• /start — 启动\n"
        "• /help — 本帮助\n\n"
        "后端：DeepSeek V4 Pro\n"
        "兼容：MATLAB R2016b"
    )


async def mundo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """蒙多学习模式：搜索 + 分析 + 给方案"""
    query = " ".join(context.args) if context.args else ""
    chat_id = update.effective_chat.id
    _save_chat_id(chat_id)

    if not query:
        await update.message.reply_text(
            f"{MUNDO_BANNER}\n\n"
            "用法: /mundo <你的问题>\n\n"
            "示例:\n"
            "/mundo Python 爬虫被 403 怎么办\n"
            "/mundo React 列表渲染优化方案\n"
            "/mundo MATLAB R2016b 中文乱码"
        )
        return

    logger.info(f"/mundo 来自 chat_id={chat_id}: {query[:80]}")

    # 发送搜索中提示
    await update.message.reply_text(
        f"{MUNDO_BANNER}\n\n蒙多正在搜索: {query}\n搜索 GitHub + Stack Overflow..."
    )

    # 并行搜索
    search_results = await _mundo_search(query)

    # 构建带搜索结果的 prompt
    user_content = f"问题: {query}"
    if search_results:
        user_content += f"\n\n以下是蒙多搜索到的参考资料：\n{search_results}\n\n请基于以上资料，给出最优方案。如果没有参考资料，直接给出你的方案。"

    reply = await _call_deepseek([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ])
    await _reply_with_typing(update, context, chat_id, reply)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"收到消息 chat_id={chat_id}: {user_msg[:80]}")
    _save_chat_id(chat_id)

    # 检测蒙多关键词，自动激活学习模式
    is_mundo = bool(MUNDO_KEYWORDS.search(user_msg))

    if is_mundo:
        await update.message.reply_text(MUNDO_BANNER)
        search_results = await _mundo_search(user_msg)
        if search_results:
            user_msg += f"\n\n参考资料：\n{search_results}"

    reply = await _call_deepseek([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])
    await _reply_with_typing(update, context, chat_id, reply)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or ""
    chat_id = update.effective_chat.id
    _save_chat_id(chat_id)
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    base64_image = base64.b64encode(photo_bytes).decode("utf-8")

    ext = Path(file.file_path).suffix.lstrip(".") if file.file_path else "jpg"
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "gif": "gif"}
    mime_type = mime_map.get(ext, "jpeg")
    data_url = f"data:image/{mime_type};base64,{base64_image}"

    user_content = [{"type": "image_url", "image_url": {"url": data_url}}]
    if caption:
        user_content.insert(0, {"type": "text", "text": caption})

    reply = await _call_deepseek([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ])
    await _reply_with_typing(update, context, chat_id, reply)


async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("未知命令。发 /help 查看帮助。")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    if isinstance(err, Conflict):
        logger.error("另一 bot 实例正在运行，本实例退出。请先停止其他设备上的 bot。")
        await context.application.stop()
        return
    logger.error(f"处理消息时异常: {err}", exc_info=err)


def _main() -> None:
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("mundo", mundo_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))
    app.add_error_handler(error_handler)

    logger.info("Bot 启动中...")
    print("Bot 已启动，按 Ctrl+C 停止")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    try:
        _main()
    except KeyboardInterrupt:
        logger.info("用户停止 Bot")
    except Exception as e:
        logger.error(f"Bot 崩溃: {e}")
        sys.exit(1)
