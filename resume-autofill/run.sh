#!/bin/bash
# 简历投递系统 — macOS 启动脚本
cd "$(dirname "$0")"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "首次运行，正在安装..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
else
    source venv/bin/activate
fi

python3 app.py
