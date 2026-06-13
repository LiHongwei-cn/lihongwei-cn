#!/bin/bash
# MUNDO Agent 启动脚本
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "首次运行，正在安装..."
    bash install.sh
fi

exec ./venv/bin/python3 mundo.py "$@"
