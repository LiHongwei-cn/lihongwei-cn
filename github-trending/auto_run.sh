#!/bin/bash
# GitHub Trending 自动运行脚本（供 launchd 定时任务调用）
# 此脚本会加载用户的 shell 环境变量，然后运行爬虫并提交到 GitHub

set -e

# 加载 shell 环境变量（包括 DEEPSEEK_API_KEY）
if [ -f "$HOME/.zshrc" ]; then
    source "$HOME/.zshrc" 2>/dev/null || true
elif [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc" 2>/dev/null || true
fi
if [ -f "$HOME/.bash_profile" ]; then
    source "$HOME/.bash_profile" 2>/dev/null || true
fi

PROJECT_DIR="$HOME/Desktop/lihongwei-cn"
TRENDING_DIR="$PROJECT_DIR/github-trending"

cd "$TRENDING_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始每日热点爬取..."

# 运行爬虫
/usr/bin/python3 crawl.py 2>&1

# 提交到 GitHub
cd "$PROJECT_DIR"
/usr/bin/git add github-trending/index.html

if /usr/bin/git diff --cached --quiet; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 无变化，跳过提交"
else
    /usr/bin/git commit -m "chore: 自动更新 GitHub 每日热点报告"
    /usr/bin/git push
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 已提交并推送"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完成"
