#!/bin/bash
# 每周同步：爬取大型 Skill 集合 → 云仓库 → 更新页面
set -e

MUNDO_DIR="$HOME/.hermes/mundo-agent"
CLOUD_DIR="$HOME/Desktop/lihongwei-cn/mundo-cloud"
STORE_DIR="$HOME/Desktop/lihongwei-cn/skill-store"

echo "[weekly-sync] 开始每周 Skill 集合同步..."

# 1. 更新 antigravity-awesome-skills 仓库
SOURCE_DIR="/tmp/antigravity-awesome-skills"
if [ -d "$SOURCE_DIR" ]; then
    cd "$SOURCE_DIR" && git pull
else
    git clone --depth 1 https://github.com/sickn33/antigravity-awesome-skills.git "$SOURCE_DIR"
fi

# 2. 运行整理脚本
cd "$MUNDO_DIR"
python3 organize_skills.py

# 3. 生成 skill-store 页面
python3 generate_store_page.py

# 4. Git 提交云仓库
cd "$CLOUD_DIR"
git add -A
if git diff --cached --quiet; then
    echo "[weekly-sync] 云仓库无变更"
else
    git commit -m "chore: weekly skill sync $(date +%Y-%m-%d)"
fi

# 5. Git 提交 skill-store
cd "$STORE_DIR"
git add -A
if git diff --cached --quiet; then
    echo "[weekly-sync] skill-store 无变更"
else
    git commit -m "chore: update skill store page $(date +%Y-%m-%d)"
fi

# 6. Push 所有更改
cd "$CLOUD_DIR/.."
git push origin main 2>/dev/null || echo "[weekly-sync] push 失败"

echo "[weekly-sync] 完成"
