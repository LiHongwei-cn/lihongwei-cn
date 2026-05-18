#!/bin/bash
# 每 15 分钟同步 counterapi.dev → stats.json
# 供 launchd 定时调用
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

PAGES="home matlab-tool desktop-launcher claude-code-tutorial vpn-guide win-optimize github-trending ccs-launcher global-specs"

echo "{" > stats.json
FIRST=true
for page in $PAGES; do
  count=$(curl -sL "https://api.counterapi.dev/v1/lihongwei-cn/${page}/" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo 0)
  if [ "$FIRST" = true ]; then FIRST=false; else echo "," >> stats.json; fi
  printf '  "%s": %s' "$page" "$count" >> stats.json
done
echo "" >> stats.json
echo "}" >> stats.json

if git diff --quiet stats.json; then
  exit 0
fi

git add stats.json
git commit -m "chore: 同步访问计数 stats.json" 2>/dev/null || true
git push 2>/dev/null || true
