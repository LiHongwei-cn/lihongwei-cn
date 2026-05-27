#!/usr/bin/env bash
# daily_evolve.sh — Daily cron entry point for Mundo cloud sync.
#
# Usage:
#   bash scripts/daily_evolve.sh
#
# Cron example (run daily at 03:00):
#   0 3 * * * /path/to/mundo-cloud/scripts/daily_evolve.sh >> /tmp/mundo-evolve.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "=== Mundo Daily Evolve ==="
echo "Start: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Repo:  $REPO_ROOT"

# Step 1: Pull latest from cloud
echo ""
echo "--- git pull ---"
git pull --rebase --autostash 2>&1 || echo "WARN: git pull failed (maybe no remote)"

# Step 2: Sync skills to local
echo ""
echo "--- sync_local ---"
SYNC_RESULT=$(python3 "$SCRIPT_DIR/sync_local.py" 2>&1)
echo "$SYNC_RESULT"

SYNCED=$(echo "$SYNC_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('synced',0))" 2>/dev/null || echo "0")

# Step 3: Commit and push if there are changes
echo ""
echo "--- git status ---"
git add -A
if git diff --cached --quiet; then
    echo "No changes to commit."
else
    git commit -m "chore: daily evolve — synced $SYNCED skill(s)" 2>&1
    echo "--- git push ---"
    git push 2>&1 || echo "WARN: git push failed"
fi

echo ""
echo "End: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=== Done ==="
