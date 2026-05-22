#!/bin/bash
set -euo pipefail
# Telegram Bot Launcher
# Usage: bash start_bot.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Source .env if it exists (fallback when shell env vars not set)
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

if [ -z "${TELEGRAM_TOKEN:-}" ]; then
    echo "ERROR: TELEGRAM_TOKEN 未设置"
    echo "  方式1: export TELEGRAM_TOKEN=\"你的Token\""
    echo "  方式2: 在 bot/.env 文件中写入 TELEGRAM_TOKEN=你的Token"
    exit 1
fi

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    echo "ERROR: DEEPSEEK_API_KEY 未设置"
    echo "  方式1: export DEEPSEEK_API_KEY=\"sk-你的Key\""
    echo "  方式2: 在 bot/.env 文件中写入 DEEPSEEK_API_KEY=sk-你的Key"
    exit 1
fi

python3 tgbot.py
