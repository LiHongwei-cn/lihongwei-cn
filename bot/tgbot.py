import asyncio
import base64
import os
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ============ 配置 ============
def _get_env(key: str) -> str:
    val = os.environ.get(key)
    if val:
        return val
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as reg:
            val, _ = winreg.QueryValueEx(reg, key)
        os.environ[key] = val
        return val
    except Exception:
        raise KeyError(f"{key} 未设置，请在系统环境变量中配置")

TELEGRAM_TOKEN = _get_env("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = _get_env("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT = """## 身份
用户是新能源汽车工程专业大三学生。具备车辆工程、电池系统、电机控制、能源管理等专业背景。
你能直接生成 MATLAB/Simulink 仿真代码，用户自己会用 CarSim 软件。

## 回复原则
1. 极度简洁，直接给结论，零废话
2. 不说"好的""当然""我来帮你""你可以……"等废话
3. 不重复用户的问题
4. 代码直给，不解释；除非用户明确要求解释
5. 不输出"有需要随时问我"等结束语
6. MATLAB/Simulink 代码兼容 R2016b

## 语言
- 默认中文，代码、变量名用英文"""


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    reply = response.choices[0].message.content
    await update.message.reply_text(reply)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or ""

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    base64_image = base64.b64encode(photo_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{base64_image}"

    user_content = [{"type": "image_url", "image_url": {"url": data_url}}]
    if caption:
        user_content.insert(0, {"type": "text", "text": caption})

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"出错: {e}"
    await update.message.reply_text(reply)


LOG_FILE = Path(__file__).with_suffix(".log")

def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

if __name__ == "__main__":
    _log("Bot 启动...")
    try:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        print("Bot 已启动")
        _log("Bot 运行中")
        app.run_polling()
    except Exception as e:
        _log(f"致命错误: {e}")
        raise
