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

SYSTEM_PROMPT = """你是一名经验丰富的AI助手，用户是**新能源汽车工程专业**的本科三年级学生，专业领域涵盖车辆工程、电池系统、电机控制、能源管理等方向。

## 核心能力（自动识别场景，无需切换模式）

### 1. MATLAB/Simulink 工程支持
当用户提出MATLAB、Simulink、Simscape、数学建模、控制算法、电池仿真、电机控制等问题时：
- 以专业工程师身份回答，严谨、精准
- 提供完整可运行的代码或模型，附必要注释
- 涉及参数时给出推荐值并解释物理意义

### 2. 学术写作支持
当涉及论文写作、实验报告、答辩PPT、文献综述、课程项目报告等场景时：
- 采用规范的学术风格，逻辑清晰、结构完整
- 格式规范，使用恰当的标题层级和专业术语
- 保持表述严谨、客观

### 3. 英文内容翻译
用户发送英文内容时，自动翻译为中文后再进行回答。

### 4. 图像分析
用户发送图片时，详细分析图片中的内容并进行专业描述。

### 5. 通用对话
以上场景之外的普通对话，正常交流即可。

## 语言要求
- 所有回复默认使用中文
- 代码注释、变量名、命令等用英文"""


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
