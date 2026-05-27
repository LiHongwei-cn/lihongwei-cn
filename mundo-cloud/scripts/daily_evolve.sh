#!/usr/bin/env bash
# daily_evolve.sh — Daily cron entry point for Mundo cloud sync.
#
# Usage:
#   bash scripts/daily_evolve.sh [--dry-run]
#
# Options:
#   --dry-run   Print what would be done, don't actually sync or commit.
#
# Cron example (run daily at 03:00):
#   0 3 * * * /path/to/mundo-cloud/scripts/daily_evolve.sh >> /tmp/mundo-evolve.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
    esac
done

cd "$REPO_ROOT"

SYNCED=0
SKIPPED=0
ERRORS=0

echo "=== Mundo Daily Evolve ==="
echo "Start: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "Repo:  $REPO_ROOT"
[ "$DRY_RUN" -eq 1 ] && echo "Mode:  DRY RUN (no changes will be made)"

# Step 1: Pull latest from cloud
echo ""
echo "--- git pull ---"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] Would run: git pull --rebase --autostash"
else
    git pull --rebase --autostash 2>&1 || echo "WARN: git pull failed (maybe no remote)"
fi

# Step 2: Sync skills to local
echo ""
echo "--- sync_local ---"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] Would run: python3 sync_local.py"
else
    if ! SYNC_RESULT=$(python3 "$SCRIPT_DIR/sync_local.py" 2>&1); then
        echo "ERROR: python3 sync_local.py failed"
        echo "$SYNC_RESULT"
        echo ""
        echo "=== Summary ==="
        echo "Synced:  0"
        echo "Skipped: 0"
        echo "Errors:  1 (sync_local.py failed)"
        echo "End: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
        exit 1
    fi
    echo "$SYNC_RESULT"

    SYNCED=$(echo "$SYNC_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('synced',0))" 2>/dev/null || echo "0")
    SKIPPED=$(echo "$SYNC_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('skipped',0))" 2>/dev/null || echo "0")
    ERRORS=$(echo "$SYNC_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('errors',0))" 2>/dev/null || echo "0")
fi

# Step 3: Commit and push if there are changes
echo ""
echo "--- git status ---"
if [ "$DRY_RUN" -eq 1 ]; then
    echo "[dry-run] Would check git status and commit if changes exist"
else
    git add -A
    if git diff --cached --quiet; then
        echo "No changes to commit."
    else
        git commit -m "chore: daily evolve — synced $SYNCED skill(s)" 2>&1
        echo "--- git push ---"
        git push 2>&1 || echo "WARN: git push failed"
    fi
fi

echo ""
echo "=== Summary ==="
echo "Synced:  $SYNCED"
echo "Skipped: $SKIPPED"
echo "Errors:  $ERRORS"
echo "End: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=== Done ==="
