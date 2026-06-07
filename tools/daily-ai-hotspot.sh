#!/bin/bash
# AI 热点每日抓取 + 蒙多学习

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================"
echo "AI 热点每日抓取 + 蒙多学习"
echo "========================================"

echo "[1/3] 抓取今日热点..."
python3 "$SCRIPT_DIR/ai-hotspot-crawler.py"

echo "[2/3] 蒙多分析学习..."
python3 "$SCRIPT_DIR/ai-hotspot-analyzer.py"

echo "[3/3] 同步到 GitHub..."
git add docs/ai-hotspots/ tools/ai-hotspot-*.py
git commit -m "docs: AI 热点日报 $(date +%Y-%m-%d)"
git push

echo "========================================"
echo "完成！热点已保存并同步"
echo "========================================"
