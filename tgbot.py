import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

TELEGRAM_TOKEN = "8868453528:AAFFdqlRUG48wo0nMnOm4xsUKhNTCbvpwVk"
DEEPSEEK_API_KEY = "sk-ba9970676c074a5e9a7c87c67639ba8e"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
    {"role": "system", "content": "请用中文回答所有问题"},
    {"role": "user", "content": user_message}
]

    )
    reply = response.choices[0].message.content
    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
