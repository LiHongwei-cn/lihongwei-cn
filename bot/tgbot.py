import asyncio
import base64
import os
import re
import subprocess
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ============ 配置 ============
TELEGRAM_TOKEN = "8868453528:AAFFdqlRUG48wo0nMnOm4xsUKhNTCbvpwVk"
DEEPSEEK_API_KEY = "sk-ba9970676c074a5e9a7c87c67639ba8e"
REPO_PATH = r"C:\Users\HP\Desktop\1"

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


def save_and_push(filename: str, code: str) -> str:
    """保存 MATLAB 代码到 examples 目录并推送到 GitHub"""
    examples_dir = Path(REPO_PATH) / "matlab" / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)

    filepath = examples_dir / filename
    filepath.write_text(code, encoding="utf-8")

    # git add + commit + push
    try:
        subprocess.run(["git", "add", "-A"], cwd=REPO_PATH, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", f"bot: auto-generate {filename}"],
            cwd=REPO_PATH, check=True, capture_output=True, text=True
        )
        subprocess.run(["git", "push"], cwd=REPO_PATH, check=True, capture_output=True, text=True)
        return str(filepath.relative_to(REPO_PATH))
    except subprocess.CalledProcessError as e:
        # 如果 push 失败（比如没网络），至少文件已保存
        filepath.write_text(code, encoding="utf-8")
        print(f"Git 操作失败: {e.stderr}")
        return str(filepath.relative_to(REPO_PATH))


# ============ /gen 命令：生成 MATLAB 代码并推送 GitHub ============
async def cmd_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    requirements = ' '.join(context.args) if context.args else ''
    if not requirements:
        await update.message.reply_text(
            "用法: /gen <作业要求>\n\n"
            "示例:\n"
            "/gen 写一个电池SOC安时积分法估算的MATLAB代码\n"
            "/gen 生成PMSM电机矢量控制Simulink模型"
        )
        return

    msg = await update.message.reply_text("正在生成代码，推送到 GitHub...")

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是 MATLAB/Simulink 仿真代码生成器。"
                        "根据用户需求生成完整可运行的 MATLAB (.m) 脚本。\n\n"
                        "输出格式要求：\n"
                        "1. 第一行必须用注释标注文件名，格式: % FILENAME: xxx.m\n"
                        "2. 代码完整可运行，包含所有必要的初始化、参数定义、计算和绘图\n"
                        "3. 参数给推荐值并注释物理意义\n"
                        "4. 兼容 MATLAB R2016b+\n"
                        "5. 最后一行注释标注: % END\n\n"
                        "只输出代码，不要任何解释文字。"
                    )
                },
                {"role": "user", "content": requirements}
            ]
        )

        full_response = response.choices[0].message.content

        # 从回复中提取文件名
        filename_match = re.search(r'% FILENAME:\s*(\S+\.m)', full_response)
        if filename_match:
            filename = filename_match.group(1)
        else:
            # 用需求关键词生成文件名
            safe_name = re.sub(r'[^\w一-鿿]+', '_', requirements[:30]).strip('_')
            filename = f"{safe_name}.m" if safe_name else "generated_script.m"

        # 提取代码体 (去掉 AI 可能的 markdown 包装和首尾注释标记)
        code = full_response
        code = re.sub(r'^```(?:matlab|MATLAB)?\s*\n?', '', code, flags=re.MULTILINE)
        code = re.sub(r'\n?```\s*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'\n?% END\s*$', '', code)
        code = re.sub(r'^% FILENAME:.*\n', '', code, count=1)
        code = code.strip()

        rel_path = save_and_push(filename, code)

        await msg.edit_text(
            f"已完成: {rel_path}\n"
            f"代码已推送到 GitHub，笔记本上打开 matlab.bat 即可运行。"
        )

    except Exception as e:
        await msg.edit_text(f"生成失败: {str(e)}")


# ============ /pull 命令：拉取最新代码 ============
async def cmd_pull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=REPO_PATH, check=True, capture_output=True, text=True
        )
        await update.message.reply_text(f"代码已更新:\n{result.stdout.strip() or '已是最新'}")
    except subprocess.CalledProcessError as e:
        await update.message.reply_text(f"拉取失败:\n{e.stderr}")


# ============ 普通消息处理 ============
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


# ============ 图片处理 ============
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
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ]
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"分析图片时出错（当前模型可能不支持图片识别）:\n{str(e)}"

    await update.message.reply_text(reply)


# ============ 启动 ============
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("gen", cmd_gen))
app.add_handler(CommandHandler("pull", cmd_pull))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
print("Bot 已启动: /gen 生成代码并推送, /pull 拉取最新")
app.run_polling()
