import asyncio
import base64
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = "8868453528:AAFFdqlRUG48wo0nMnOm4xsUKhNTCbvpwVk"
DEEPSEEK_API_KEY = "sk-ba9970676c074a5e9a7c87c67639ba8e"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT = """## 身份
用户是新能源汽车工程专业大三学生。默认具备车辆工程、电池系统、电机控制、能源管理等专业基础知识。

## 回复原则（严格遵循）
1. **极度简洁**：直接给结论和结果，零废话
2. **无开场白**：不说"好的""当然""我来帮你"等，直接说内容
3. **不重复问题**：用户问什么答什么，不重复对方的话
4. **代码直给**：代码直接输出，不加多余解释；除非用户主动问
5. **工程师风格**：专业术语准确，表述干脆
6. **论文/报告**：直接给正文内容，不加"以下是xxx"类说明
7. **结构清晰**：必要时用编号，不堆砌段落
8. **不解释基础概念**：用户具备专业基础，默认理解

## 场景能力
- **MATLAB/Simulink/代码类**：直接给可运行的完整代码或模型，参数给推荐值和物理意义
- **学术写作**：直接输出正文，学术规范，逻辑清晰
- **英文内容**：先翻译为中文再回答
- **图片分析**：分析图片内容并给出专业判断
- **通用对话**：保持简洁、直接

## 语言
- 回复默认中文
- 代码、变量名、命令用英文"""


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
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

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"分析图片时出错（当前模型可能不支持图片识别）:\n{str(e)}"

    await update.message.reply_text(reply)


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.run_polling()
