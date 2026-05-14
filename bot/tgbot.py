import asyncio
import base64
import re
import subprocess
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ============ 配置 ============
TELEGRAM_TOKEN = "8868453528:AAFFdqlRUG48wo0nMnOm4xsUKhNTCbvpwVk"
DEEPSEEK_API_KEY = "sk-ba9970676c074a5e9a7c87c67639ba8e"
REPO_PATH = r"C:\Users\HP\Desktop\1"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

CHAT_PROMPT = """## 身份
用户是新能源汽车工程专业大三学生。具备车辆工程、电池系统、电机控制、能源管理等专业背景。

## 回复原则（严格遵守）
1. 极度简洁，直接给结论，零废话
2. 不说"好的""当然""我来帮你""你可以……"等废话
3. 不重复用户的问题
4. 代码直给，不解释；除非用户明确要求解释
5. 不输出"有需要随时问我"等结束语

## 语言
- 默认中文，代码、变量名用英文"""

TASKS_DIR = Path(REPO_PATH) / "tasks"


def detect_intent(text: str) -> str:
    text_lower = text.lower()
    fix_keywords = [
        '报错', '错误', '出错', '修复', '改一下', '不行',
        '有问题', '不运行', 'bug', 'fix', 'error', '改正',
        '改改', '修正', '改错', '不对'
    ]
    code_keywords = [
        'matlab', 'simulink', '.m', '代码', '仿真', 'carsim',
        '电机', '电池', 'soc', 'pmsm', 'foc', '车辆', '巡航',
        '滤波', 'fft', '控制策略', '能量管理', '写一个', '生成',
        '脚本', '模型', 'plot', 'figure', 'function'
    ]
    doc_keywords = [
        '论文', '报告', '实验报告', '答辩', '文章', '文档',
        '正文', '摘要', '引言', '结论', '参考文献', '写一篇',
        '绪论', 'word', 'doc'
    ]
    fix_score = sum(1 for kw in fix_keywords if kw in text_lower)
    code_score = sum(1 for kw in code_keywords if kw in text_lower)
    doc_score = sum(1 for kw in doc_keywords if kw in text_lower)
    if fix_score > 0:
        return 'fix'
    elif code_score > 0:
        return 'simulink'
    elif doc_score > 0:
        return 'doc'
    else:
        return 'chat'


CHAT_ID_FILE = Path(REPO_PATH) / "bot" / "chat_id.txt"


def save_chat_id(chat_id: int):
    CHAT_ID_FILE.write_text(str(chat_id))


def submit_task(intent: str, user_message: str, chat_id: int, has_photo: bool = False) -> str:
    """写任务文件并推送到 GitHub，等待 Claude Code 处理"""
    save_chat_id(chat_id)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"task_{ts}.txt"
    filepath = TASKS_DIR / filename

    TASKS_DIR.mkdir(parents=True, exist_ok=True)

    content = f"TYPE: {intent}\nTIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    if has_photo:
        content += "PHOTO: yes\n"
    content += f"---\n{user_message}\n"

    filepath.write_text(content, encoding="utf-8")

    try:
        subprocess.run(["git", "add", "-A"], cwd=REPO_PATH, check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", f"task: {intent} - {user_message[:40]}"],
                       cwd=REPO_PATH, check=True, capture_output=True, text=True)
        subprocess.run(["git", "push"], cwd=REPO_PATH, check=True,
                       capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Git push 失败: {e.stderr}")

    return filename


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    intent = detect_intent(user_message)

    if intent == 'fix':
        submit_task('fix', user_message, update.message.chat_id)
        await update.message.reply_text("已提交修复请求，处理中…")
    elif intent == 'simulink':
        submit_task('simulink', user_message, update.message.chat_id)
        await update.message.reply_text("已提交，处理中…")
    elif intent == 'doc':
        submit_task('doc', user_message, update.message.chat_id)
        await update.message.reply_text("已提交，处理中…")
    else:
        await handle_chat(update, user_message)


async def handle_chat(update: Update, user_message: str):
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": CHAT_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )
    reply = response.choices[0].message.content
    await update.message.reply_text(reply)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = update.message.caption or ""
    intent = detect_intent(caption)

    if intent in ('fix', 'simulink', 'doc'):
        fname = submit_task(intent, caption, update.message.chat_id, has_photo=True)
        await update.message.reply_text("已提交（含图片），处理中…")
    else:
        # 聊天模式的图片，仍用 DeepSeek 回答
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
                    {"role": "system", "content": CHAT_PROMPT},
                    {"role": "user", "content": user_content}
                ]
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"出错: {e}"
        await update.message.reply_text(reply)


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
print("Bot 已启动（Simulink 模式 — 代码类任务默认生成 Simulink 模型）")
app.run_polling()
