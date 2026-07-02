#!/bin/bash
# MUNDO Agent v2.3.1 — macOS 双击启动器
# 调用统一同步脚本，确保运行最新版

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 程序坞/Finder 启动时 HOME 可能未设置
if [ -z "${HOME:-}" ]; then
    USER_NAME="$(/usr/bin/id -un 2>/dev/null || echo "")"
    if [ -n "$USER_NAME" ] && [ -d "/Users/$USER_NAME" ]; then
        export HOME="/Users/$USER_NAME"
    else
        export HOME="$(/usr/bin/eval echo "~$USER_NAME")"
    fi
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/mundo-sync.sh"

if [ -f "$SYNC_SCRIPT" ]; then
    bash "$SYNC_SCRIPT"
else
    echo "❌ 找不到 mundo-sync.sh，请确认安装完整。"
    exit 1
fi

DST="$HOME/.hermes/mundo-agent"

# 确保 setup_complete 存在
if [ ! -f "$DST/.setup_complete" ] && [ -f "$DST/.env" ]; then
    if grep -q "API_KEY" "$DST/.env" 2>/dev/null; then
        echo "xiaomi
mimo-v2.5-pro" > "$DST/.setup_complete"
    fi
fi

cd "$DST"
export PYTHONDONTWRITEBYTECODE=1
exec python3 mundo.py "$@"
