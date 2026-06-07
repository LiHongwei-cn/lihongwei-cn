#!/bin/bash
# Wrapper script for daily AI hotspot crawling with virtual environment

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/tools/venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

# 创建虚拟环境（如果不存在）
if [ ! -d "$VENV_DIR" ]; then
    echo "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 安装依赖（如果需要）
if [ -f "$REQUIREMENTS" ]; then
    echo "检查并安装依赖..."
    pip install -r "$REQUIREMENTS" -q
fi

# 运行每日AI热点脚本
cd "$PROJECT_DIR"
bash "$SCRIPT_DIR/daily-ai-hotspot.sh"