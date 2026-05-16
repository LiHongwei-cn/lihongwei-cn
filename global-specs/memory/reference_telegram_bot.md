---
name: telegram-bot
description: Telegram 机器人 — 直接回复消息，支持文本和图片，使用 DeepSeek API
metadata: 
  node_type: memory
  type: reference
  originSessionId: 9aff14b9-9495-4733-b6e1-6645e86bd82f
---

## Telegram Bot 信息

- **用途**：接收消息 → DeepSeek API 回复，支持文本和图片
- **代码位置**：仓库 `bot/` 目录
- **主程序**：`bot/tgbot.py`
- **通知工具**：`bot/notify.py`（通过 chat_id.txt 发送消息到指定对话）

## 必需环境变量

- `TELEGRAM_TOKEN` — Bot Token（从 @BotFather 获取）
- `DEEPSEEK_API_KEY` — DeepSeek API Key

## 启动方式

```bash
# Windows
bot/start_bot.bat

# macOS
chmod +x bot/start_bot.sh && ./bot/start_bot.sh

# 直接运行
python bot/tgbot.py
```

## 开机自启

- **Windows**：运行 `bot/setup_startup.vbs`，会在启动文件夹创建快捷方式
- **macOS**：创建 LaunchAgent plist 放到 `~/Library/LaunchAgents/`

## Chat ID

`bot/chat_id.txt` 存放通知目标的 chat ID。获取方式：给 bot 发一条消息，然后访问 `https://api.telegram.org/bot<TOKEN>/getUpdates` 查看 `chat.id`。

## 依赖

```
python-telegram-bot>=20.0,<23.0
openai>=1.0,<3.0
```

安装：`pip install -r bot/requirements.txt`
