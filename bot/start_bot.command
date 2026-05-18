#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ -z "${TELEGRAM_TOKEN:-}" ]; then
    echo "ERROR: TELEGRAM_TOKEN 环境变量未设置"
    echo '请在 ~/.zshrc 中添加: export TELEGRAM_TOKEN="你的Token"'
    read -p "按 Enter 关闭..."
    exit 1
fi
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    echo "ERROR: DEEPSEEK_API_KEY 环境变量未设置"
    echo '请在 ~/.zshrc 中添加: export DEEPSEEK_API_KEY="sk-你的Key"'
    read -p "按 Enter 关闭..."
    exit 1
fi

python3 tgbot.py
