#!/bin/bash
# GitHub Trending 自动运行脚本（供 launchd 定时任务调用）
# 此脚本会加载用户的 shell 环境变量，然后运行爬虫并提交到 GitHub

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TRENDING_DIR="$SCRIPT_DIR"

# 环境变量由 launchd plist 的 EnvironmentVariables 注入，或从 shell RC 文件加载
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    echo "WARNING: DEEPSEEK_API_KEY 未设置，翻译功能将不可用"
fi

cd "$TRENDING_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始每日热点爬取..."

# 运行爬虫
/usr/bin/python3 crawl.py 2>&1

# 提交到 GitHub
cd "$PROJECT_DIR"
/usr/bin/git add github-trending/index.html stats.json

if /usr/bin/git diff --cached --quiet; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 无变化，跳过提交"
else
    /usr/bin/git commit -m "chore: 自动更新 GitHub 每日热点报告"
    /usr/bin/git push
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 已提交并推送"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完成"
