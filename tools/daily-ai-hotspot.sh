#!/bin/bash
# AI 热点每日抓取 + 蒙多学习

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SCRIPT_DIR/venv"

# 激活虚拟环境
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "错误: 虚拟环境不存在: $VENV_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

echo "========================================"
echo "AI 热点每日抓取 + 蒙多学习"
echo "========================================"

# 先同步远程更改
echo "[0/3] 同步远程更改..."
if git pull --rebase --autostash 2>&1; then
    echo "同步成功"
else
    echo "警告: 同步失败，继续执行..."
fi

echo "[1/3] 抓取今日热点..."
python3 "$SCRIPT_DIR/ai-hotspot-crawler.py"

echo "[2/3] 蒙多分析学习..."
python3 "$SCRIPT_DIR/ai-hotspot-analyzer.py"

echo "[3/3] 同步到 GitHub..."
git add docs/ai-hotspots/ tools/ai-hotspot-*.py
git commit -m "docs: AI 热点日报 $(date +%Y-%m-%d)" || echo "没有变更需要提交"
git push

echo "========================================"
echo "完成！热点已保存并同步"
echo "========================================"
