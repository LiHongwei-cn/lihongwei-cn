#!/bin/bash
# Wrapper script for daily journal learning with virtual environment

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CLOUD_DIR="$PROJECT_DIR/mundo-cloud"
VENV_DIR="$CLOUD_DIR/venv"
REQUIREMENTS="$CLOUD_DIR/requirements.txt"

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

# 运行每日期刊学习脚本
cd "$CLOUD_DIR"
bash "$CLOUD_DIR/scripts/daily_journal.sh"