import base64
import logging
import sys
from pathlib import Path

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

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=60.0,
)

SYSTEM_PROMPT = """## 身份
用户是新能源汽车工程专业大三学生。车辆工程、电池系统、电机控制、能源管理方向。
你能直接生成 MATLAB/Simulink 仿真代码，用户自行操作 CarSim。

## 回复原则
1. 结论先行，再给理由。不铺垫
2. 不说"好的""当然""我来帮你"等废话。不夸想法、不开头加"当然可以"
3. 不重复用户问题
4. 代码直给不解释，除非明确要求
5. 不输出结束语（"有需要随时问我"等）
6. 方案有问题直接指出，给真实判断
7. MATLAB/Simulink 兼容 R2016b

## 代码质量
- MATLAB < 200 行/文件，< 50 行/函数
- 数值参数用命名常量，不用魔法数字
- 不写无意义注释（代码自解释）

## 安全红线
- 绝不硬编码密钥、Token、密码
- 所有密钥从环境变量读取

## 语言
- 默认中文，代码、变量名用英文"""

DEEPSEEK_MODEL = "deepseek-v4-pro"
TELEGRAM_MSG_LIMIT = 4096


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
    chat_id_file = Path(__file__).parent / "chat_id.txt"
    if not chat_id_file.exists():
        chat_id_file.write_text(str(chat_id))
        logger.info(f"已保存 chat_id={chat_id} 到 {chat_id_file}")


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"/start 来自 chat_id={chat_id}")
    _save_chat_id(chat_id)
    await update.message.reply_text(
        "Danking Bot 已就绪。直接发消息即可，支持文字和图片。"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"收到消息 chat_id={chat_id}: {user_msg[:80]}")
    _save_chat_id(chat_id)

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
    await update.message.reply_text("未知命令。直接发消息即可。")


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
