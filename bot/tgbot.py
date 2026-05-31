# -*- coding: utf-8 -*-
"""Danking Bot — 蒙多 AI 助手（优化版）
主要改进：
- 对话历史记忆（/clear 清除）
- 速率限制（每用户 15 次/分钟）
- DeepSeek API 自动重试
- 资源正确清理
"""
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
from chat_history import ChatHistory
from rate_limiter import RateLimiter

load_dotenv(Path(__file__).with_name(".env"))

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tgbot")

# ─── 配置 ───

TELEGRAM_TOKEN = get_env("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = get_env("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = "deepseek-chat"
TELEGRAM_MSG_LIMIT = 4096
MAX_RETRIES = 2

SYSTEM_PROMPT_FILE = Path(__file__).with_name("SYSTEM_PROMPT.md")
CHAT_ID_FILE = Path(__file__).parent / "chat_id.txt"

MUNDO_KEYWORDS = re.compile(
    r"蒙多|mundo|卡住了|搞不定|遇到瓶颈|报错|没思路|"
    r"有没有更好的方案|学习一下|参考一下|查一下别人怎么做的",
    re.IGNORECASE,
)

# ─── 全局实例 ───

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=60.0,
)
http_client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
chat_history = ChatHistory()
rate_limiter = RateLimiter(max_requests=15, window_seconds=60)

# ─── 工具函数 ───


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
        CHAT_ID_FILE.write_text(str(chat_id), encoding="utf-8")
        logger.info(f"已保存 chat_id={chat_id}")


# ─── 网络搜索 ───


async def _search_github(query: str) -> str:
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
    except httpx.HTTPError as e:
        logger.warning(f"GitHub 搜索失败: {e}")
    return ""


async def _search_stackoverflow(query: str) -> str:
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
    except httpx.HTTPError as e:
        logger.warning(f"SO 搜索失败: {e}")
    return ""


async def _mundo_search(query: str) -> str:
    github_task = _search_github(query)
    so_task = _search_stackoverflow(query)
    github_results, so_results = await asyncio.gather(
        github_task, so_task, return_exceptions=True
    )
    parts = []
    if isinstance(github_results, str) and github_results:
        parts.append(github_results)
    if isinstance(so_results, str) and so_results:
        parts.append(so_results)
    return "\n\n".join(parts) if parts else ""


# ─── DeepSeek 调用（带重试） ───


async def _call_deepseek(messages: list[dict], retries: int = MAX_RETRIES) -> str:
    for attempt in range(retries + 1):
        try:
            response = await client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            if attempt < retries:
                wait = 2 ** attempt
                logger.warning(f"DeepSeek 调用失败（{attempt+1}/{retries+1}），{wait}s 后重试: {e}")
                await asyncio.sleep(wait)
            else:
                logger.error(f"DeepSeek API 最终失败: {e}")
                return "服务暂时不可用，请稍后再试。"


async def _reply_with_typing(update: Update, context, chat_id: int, reply: str):
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    except Exception:
        pass
    for chunk in _split_long_msg(reply):
        await update.message.reply_text(chunk)


# ─── 命令处理 ───


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    _save_chat_id(chat_id)
    chat_history.clear(chat_id)
    logger.info(f"/start chat_id={chat_id}")
    await update.message.reply_text(
        "Danking Bot 已就绪。\n\n"
        "直接发消息即可，支持文字和图片（有对话记忆）。\n\n"
        "命令：\n"
        "/start — 启动\n"
        "/mundo <问题> — 蒙多学习模式\n"
        "/clear — 清除对话历史\n"
        "/help — 帮助"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Danking Bot — 蒙多 AI 助手\n\n"
        "用法：\n"
        "• 直接发文字 — AI 回复（支持多轮对话）\n"
        "• 发图片（可加描述）— AI 分析图片\n"
        "• /mundo <问题> — 蒙多学习模式\n"
        "  自动搜索 GitHub + Stack Overflow\n"
        "  多源对比，给出最优方案\n"
        "• 说「蒙多」「卡住了」「报错」自动触发\n"
        "• /clear — 清除对话历史\n"
        "• /start — 启动\n"
        "• /help — 本帮助\n\n"
        "后端：DeepSeek Chat\n"
        "速率：15 次/分钟"
    )


async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_history.clear(chat_id)
    logger.info(f"/clear chat_id={chat_id}")
    await update.message.reply_text("对话历史已清除。")


async def mundo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else ""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    _save_chat_id(chat_id)

    if not rate_limiter.is_allowed(user_id):
        remaining = rate_limiter.remaining(user_id)
        await update.message.reply_text(f"请求过于频繁，剩余 {remaining} 次/分钟。")
        return

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

    logger.info(f"/mundo chat_id={chat_id}: {query[:80]}")

    await update.message.reply_text(
        f"{MUNDO_BANNER}\n\n蒙多正在搜索: {query}\n搜索 GitHub + Stack Overflow..."
    )

    search_results = await _mundo_search(query)

    user_content = f"问题: {query}"
    if search_results:
        user_content += f"\n\n以下是蒙多搜索到的参考资料：\n{search_results}\n\n请基于以上资料，给出最优方案。如果没有参考资料，直接给出你的方案。"

    # 添加用户消息到历史
    chat_history.add(chat_id, "user", user_content)

    # 构建完整消息（system + 历史）
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history.get(chat_id))

    reply = await _call_deepseek(messages)

    # 保存 AI 回复到历史
    chat_history.add(chat_id, "assistant", reply)

    await _reply_with_typing(update, context, chat_id, reply)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    _save_chat_id(chat_id)

    if not rate_limiter.is_allowed(user_id):
        remaining = rate_limiter.remaining(user_id)
        await update.message.reply_text(f"请求过于频繁，剩余 {remaining} 次/分钟。")
        return

    logger.info(f"消息 chat_id={chat_id}: {user_msg[:80]}")

    # 检测蒙多关键词
    is_mundo = bool(MUNDO_KEYWORDS.search(user_msg))

    if is_mundo:
        await update.message.reply_text(MUNDO_BANNER)
        search_results = await _mundo_search(user_msg)
        if search_results:
            user_msg += f"\n\n参考资料：\n{search_results}"

    # 添加用户消息到历史
    chat_history.add(chat_id, "user", user_msg)

    # 构建完整消息
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_history.get(chat_id))

    reply = await _call_deepseek(messages)

    # 保存 AI 回复到历史
    chat_history.add(chat_id, "assistant", reply)

    await _reply_with_typing(update, context, chat_id, reply)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or ""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    _save_chat_id(chat_id)

    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text("请求过于频繁，请稍后再试。")
        return

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

    # 图片不存历史（太大），只存描述
    chat_history.add(chat_id, "user", f"[发送图片] {caption}" if caption else "[发送图片]")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": user_content})

    reply = await _call_deepseek(messages)
    chat_history.add(chat_id, "assistant", reply)

    await _reply_with_typing(update, context, chat_id, reply)


async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("未知命令。发 /help 查看帮助。")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    if isinstance(err, Conflict):
        logger.error("另一 bot 实例正在运行，本实例退出。")
        await context.application.stop()
        return
    logger.error(f"处理消息时异常: {err}", exc_info=err)


# ─── 启动 ───


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
    app.add_handler(CommandHandler("clear", clear_cmd))
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
