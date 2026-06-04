#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "首次运行，正在安装..."
    /Users/huangpeng/.local/bin/python3.11 -m venv venv
fi

source venv/bin/activate
python "$@"
