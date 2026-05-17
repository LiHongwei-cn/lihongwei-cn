#!/bin/bash
# GitHub Trending 爬虫 — macOS/Linux 启动脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "  GitHub Trending 每日热点爬虫"
echo "========================================="

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3"
    exit 1
fi

# 检查依赖
if ! python3 -c "import requests" 2>/dev/null; then
    echo "📦 安装依赖..."
    pip3 install -r requirements.txt
fi

# 检查 API Key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠ 未设置 DEEPSEEK_API_KEY 环境变量"
    echo "  英文区描述将保持原文（不翻译）"
    echo "  设置方式: export DEEPSEEK_API_KEY=你的密钥"
    echo ""
fi

echo ""
python3 crawl.py

echo ""
echo "✅ 完成！报告文件: $(pwd)/index.html"
