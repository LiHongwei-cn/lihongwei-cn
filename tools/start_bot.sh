#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$WORK_DIR" || exit 1

if [ -z "${TELEGRAM_TOKEN:-}" ]; then
    echo "ERROR: TELEGRAM_TOKEN 环境变量未设置"
    echo '请在 ~/.zshrc 中添加: export TELEGRAM_TOKEN="你的Token"'
    exit 1
fi
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    echo "ERROR: DEEPSEEK_API_KEY 环境变量未设置"
    echo '请在 ~/.zshrc 中添加: export DEEPSEEK_API_KEY="sk-你的Key"'
    exit 1
fi

# Optional proxy - uncomment and set port if needed
# export HTTPS_PROXY="http://127.0.0.1:7897"

python3 tools/autosave.py &
python3 bot/tgbot.py &

echo "Bot 已在后台启动。"
echo "查看进程: ps aux | grep tgbot"
read -p "按 Enter 关闭..."
