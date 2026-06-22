#!/bin/bash
# 每日同步：爬取 GitHub Skill → 云仓库
set -e

CRAWLER_DIR="$HOME/.hermes/mundo-agent"
CLOUD_DIR="$HOME/Desktop/lihongwei-cn/mundo-cloud"
STORE_DIR="$CRAWLER_DIR/skill_store"

echo "[sync] 开始每日 Skill 爬取与同步..."

# 1. 运行爬虫
cd "$CRAWLER_DIR"
python3 github_skill_crawler.py

# 2. 复制数据到云仓库
cp "$STORE_DIR/github_raw.json" "$CLOUD_DIR/sync/"
cp "$STORE_DIR/skills_index.json" "$CLOUD_DIR/sync/" 2>/dev/null || true

# 3. 生成 registry.json（技能索引）
python3 - << 'PYEOF'
import json
from pathlib import Path
from datetime import datetime

cloud = Path.home() / "Desktop/lihongwei-cn/mundo-cloud"
raw_file = cloud / "sync/github_raw.json"

if not raw_file.exists():
    print("[sync] 无爬取数据")
    exit(0)

data = json.loads(raw_file.read_text())
projects = data.get("projects", [])

registry = {
    "metadata": {
        "last_sync": datetime.utcnow().isoformat() + "Z",
        "total_projects": len(projects),
        "source": "github-search-api",
    },
    "projects": projects,
}

(cloud / "sync/registry.json").write_text(
    json.dumps(registry, ensure_ascii=False, indent=2)
)
print(f"[sync] registry.json 已更新: {len(projects)} 个项目")
PYEOF

# 4. Git 提交
cd "$CLOUD_DIR"
git add -A
if git diff --cached --quiet; then
    echo "[sync] 无变更，跳过提交"
else
    git commit -m "chore: daily skill crawl $(date +%Y-%m-%d)"
    git push origin main 2>/dev/null || echo "[sync] push 失败（可能无远程）"
fi

echo "[sync] 完成"
