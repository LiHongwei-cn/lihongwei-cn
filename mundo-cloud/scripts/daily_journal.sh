#!/usr/bin/env bash
# daily_journal.sh — 蒙多每日期刊学习脚本
#
# 功能：
#   1. 抓取Nature/Science/Cell等顶级期刊最新文章
#   2. 将文章转化为Mundo skill
#   3. 提交到云仓库
#
# 用法：
#   bash scripts/daily_journal.sh [--dry-run]
#
# Cron配置（每天早上6点执行）：
#   0 6 * * * /path/to/mundo-cloud/scripts/daily_journal.sh >> /tmp/mundo-journal.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DRY_RUN=0
MAX_PER_JOURNAL=3

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
    esac
done

cd "$REPO_ROOT"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          蒙多每日期刊学习系统                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "仓库路径: $REPO_ROOT"
[ "$DRY_RUN" -eq 1 ] && echo "模式: 干运行（不提交更改）"
echo ""

# Step 1: 抓取期刊文章
echo "━━━ 第一步：抓取期刊文章 ━━━"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "[干运行] 将抓取 $MAX_PER_JOURNAL 篇/期刊"
else
    CRAWL_RESULT=$(python3 "$SCRIPT_DIR/journal_crawler.py" "$MAX_PER_JOURNAL" 2>&1)
    echo "$CRAWL_RESULT"
    
    # 提取抓取数量
    TOTAL_CRAWLED=$(echo "$CRAWL_RESULT" | tail -1 | python3 -c "import sys,json; print(json.load(sys.stdin).get('total',0))" 2>/dev/null || echo "0")
    
    if [ "$TOTAL_CRAWLED" -eq 0 ]; then
        echo "没有发现新文章，退出"
        exit 0
    fi
fi

# Step 2: 转化为skill
echo ""
echo "━━━ 第二步：生成skill ━━━"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "[干运行] 将生成skill文件"
else
    SKILL_RESULT=$(python3 "$SCRIPT_DIR/journal_to_skill.py" 2>&1)
    echo "$SKILL_RESULT"
fi

# Step 3: 同步到本地Hermes skills
echo ""
echo "━━━ 第三步：同步到本地skills ━━━"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "[干运行] 将同步到 ~/.hermes/skills/"
else
    # 同步journal-learnings目录到本地
    LOCAL_SKILLS="$HOME/.hermes/skills/journal-learnings"
    mkdir -p "$LOCAL_SKILLS"
    
    if [ -d "$REPO_ROOT/skills/journal-learnings" ]; then
        rsync -av --delete \
            "$REPO_ROOT/skills/journal-learnings/" \
            "$LOCAL_SKILLS/" 2>&1 | tail -5
        echo "已同步到 $LOCAL_SKILLS"
    fi
fi

# Step 4: 提交到Git
echo ""
echo "━━━ 第四步：提交到云仓库 ━━━"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "[干运行] 将git commit + push"
else
    # 设置git用户信息（GitHub Actions环境需要）
    git config user.email "mundo@lihongwei-cn.github.io"
    git config user.name "Mundo Bot"
    
    git add -A
    
    if git diff --cached --quiet; then
        echo "没有变更需要提交"
    else
        DATE_STR=$(date '+%Y-%m-%d')
        git commit -m "feat: 蒙多期刊学习 $DATE_STR — 新增 $TOTAL_CRAWLED 篇论文知识" 2>&1
        echo "已提交"
        
        # 推送到远程
        if git push 2>&1; then
            echo "已推送到GitHub"
        else
            echo "警告: git push 失败"
        fi
    fi
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          完成！                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
