#!/bin/bash
set -euo pipefail
# Telegram Bot Launcher for macOS
# Usage: bash start_bot.sh
# Or make executable: chmod +x start_bot.sh && ./start_bot.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Check for required env vars
if [ -z "${TELEGRAM_TOKEN:-}" ]; then
    echo "ERROR: TELEGRAM_TOKEN 环境变量未设置"
    echo "请在 ~/.zshrc 或 ~/.bash_profile 中添加："
    echo "  export TELEGRAM_TOKEN=\"你的Token\""
    exit 1
fi

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    echo "ERROR: DEEPSEEK_API_KEY 环境变量未设置"
    echo "请在 ~/.zshrc 或 ~/.bash_profile 中添加："
    echo "  export DEEPSEEK_API_KEY=\"sk-你的Key\""
    exit 1
fi

python3 tgbot.py
