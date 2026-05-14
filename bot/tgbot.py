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


def detect_intent(text: str) -> str:
    """自动识别用户意图"""
    text_lower = text.lower()

    # 代码生成关键词
    code_keywords = [
        'matlab', 'simulink', '.m', '代码', '仿真', 'carsim',
        '电机', '电池', 'soc', 'pmsm', 'foc', '车辆', '巡航',
        '滤波', 'fft', '控制策略', '能量管理', '写一个', '生成',
        '脚本', '模型', 'plot', 'figure', 'function'
    ]
    # 论文/报告关键词
    doc_keywords = [
        '论文', '报告', '实验报告', '答辩', '文章', '文档',
        '正文', '摘要', '引言', '结论', '参考文献', '写一篇',
        '绪论', 'word', 'doc'
    ]

    code_score = sum(1 for kw in code_keywords if kw in text_lower)
    doc_score = sum(1 for kw in doc_keywords if kw in text_lower)

    if code_score > 0:
        return 'code'
    elif doc_score > 0:
        return 'doc'
    else:
        return 'chat'


def save_and_push(filepath: Path, content: str, commit_msg: str) -> str:
    """保存文件并推送到 GitHub"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")

    try:
        subprocess.run(["git", "add", "-A"], cwd=REPO_PATH, check=True,
                       capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_PATH,
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "push"], cwd=REPO_PATH, check=True,
                       capture_output=True, text=True)
        return str(filepath.relative_to(REPO_PATH))
    except subprocess.CalledProcessError as e:
        print(f"Git push 失败: {e.stderr}")
        return str(filepath.relative_to(REPO_PATH))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    intent = detect_intent(user_message)

    if intent == 'code':
        await handle_code_gen(update, user_message)
    elif intent == 'doc':
        await handle_doc_gen(update, user_message)
    else:
        await handle_chat(update, user_message)


async def handle_code_gen(update: Update, user_message: str):
    msg = await update.message.reply_text("...")

    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 MATLAB/Simulink 代码生成器。根据用户需求输出完整可运行代码。\n\n"
                    "规则：\n"
                    "1. 第一行必须是: % FILENAME: xxx.m\n"
                    "2. 只输出代码，零解释，零废话\n"
                    "3. 兼容 MATLAB R2016b+\n"
                    "4. 参数给推荐值，用注释标注物理意义"
                )
            },
            {"role": "user", "content": user_message}
        ]
    )

    full = response.choices[0].message.content

    # 提取文件名
    m = re.search(r'% FILENAME:\s*(\S+\.m)', full)
    if m:
        filename = m.group(1)
    else:
        safe = re.sub(r'[^\w一-鿿]+', '_', user_message[:30]).strip('_')
        filename = f"{safe}.m" if safe else "script.m"

    # 清洗代码
    code = full
    code = re.sub(r'^```(?:matlab)?\s*\n?', '', code, flags=re.MULTILINE | re.IGNORECASE)
    code = re.sub(r'\n?```\s*$', '', code)
    code = re.sub(r'^% FILENAME:.*\n', '', code, count=1)
    code = code.strip()

    filepath = Path(REPO_PATH) / "matlab" / "examples" / filename
    rel = save_and_push(filepath, code, f"bot: {filename}")

    await msg.edit_text(f"{filename}")


async def handle_doc_gen(update: Update, user_message: str):
    msg = await update.message.reply_text("...")

    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是学术写作助手。用户是新能源汽车工程专业学生，需要论文或实验报告正文。\n\n"
                    "规则：\n"
                    '1. 直接输出正文内容，不要"以下是……"等说明\n'
                    "2. 学术规范，逻辑清晰，数据准确\n"
                    "3. 用户没要的章节不主动写\n"
                    "4. 不说废话，不寒暄"
                )
            },
            {"role": "user", "content": user_message}
        ]
    )

    content = response.choices[0].message.content

    # 保存到 docs/
    safe = re.sub(r'[^\w一-鿿]+', '_', user_message[:20]).strip('_')
    ts = datetime.now().strftime("%m%d_%H%M")
    filename = f"{safe}_{ts}.md"
    filepath = Path(REPO_PATH) / "docs" / filename
    rel = save_and_push(filepath, content, f"bot: doc {filename}")

    await msg.edit_text(f"{filename}")


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
    photo = update.message.photo[-1]
    caption = update.message.caption or ""

    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()

    base64_image = base64.b64encode(photo_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{base64_image}"

    user_content = [{"type": "image_url", "image_url": {"url": data_url}}]
    if caption:
        user_content.insert(0, {"type": "text", "text": caption})

    # 检查图片描述是否涉及代码/文档
    intent = detect_intent(caption)

    try:
        if intent == 'code':
            system = {
                "role": "system",
                "content": (
                    "这是用户发来的作业或实验要求图片。根据图片内容和文字说明，"
                    "输出完整 MATLAB 代码。第一行: % FILENAME: xxx.m，只输出代码，零解释。"
                )
            }
        elif intent == 'doc':
            system = {
                "role": "system",
                "content": "根据图片内容输出学术正文。直接给内容，零废话。"
            }
        else:
            system = {"role": "system", "content": CHAT_PROMPT}

        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                system,
                {"role": "user", "content": user_content}
            ]
        )
        reply = response.choices[0].message.content

        # 如果是代码，自动保存推送
        if intent == 'code':
            full = reply
            m = re.search(r'% FILENAME:\s*(\S+\.m)', full)
            if m:
                filename = m.group(1)
            else:
                filename = f"photo_script_{datetime.now().strftime('%H%M')}.m"

            code = full
            code = re.sub(r'^```(?:matlab)?\s*\n?', '', code, flags=re.MULTILINE | re.IGNORECASE)
            code = re.sub(r'\n?```\s*$', '', code)
            code = re.sub(r'^% FILENAME:.*\n', '', code, count=1)
            code = code.strip()

            filepath = Path(REPO_PATH) / "matlab" / "examples" / filename
            rel = save_and_push(filepath, code, f"bot: {filename} (from photo)")
            reply = f"{filename}"
        elif intent == 'doc':
            safe = re.sub(r'[^\w一-鿿]+', '_', (caption or 'photo')[:20]).strip('_')
            ts = datetime.now().strftime("%m%d_%H%M")
            filename = f"{safe}_{ts}.md"
            filepath = Path(REPO_PATH) / "docs" / filename
            rel = save_and_push(filepath, reply, f"bot: doc {filename}")
            reply = f"{filename}"

    except Exception as e:
        reply = f"出错: {e}"

    await update.message.reply_text(reply)


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
print("Bot 已启动（自动识别模式）")
app.run_polling()
