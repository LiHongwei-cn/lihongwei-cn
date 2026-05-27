#!/usr/bin/env bash
# full_sync.sh — Bidirectional sync: local→cloud then cloud→local.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Mundo Full Sync ==="
echo "Start: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# Step 1: Local → Cloud (upload new/changed skills)
echo ""
echo "--- Step 1: Local → Cloud ---"
python3 "$SCRIPT_DIR/batch_upload.py"

# Step 2: Score all skills
echo ""
echo "--- Step 2: Quality Scoring ---"
for skill_dir in skills/*/SKILL.md; do
    name="$(basename "$(dirname "$skill_dir")")"
    score_json="$(python3 "$SCRIPT_DIR/quality_scorer.py" "$skill_dir" 2>/dev/null || echo '{}')"
    score="$(echo "$score_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total',0))" 2>/dev/null || echo "0")"
    # update registry score
    python3 -c "
import json
from pathlib import Path
r = json.loads(Path('$REPO_ROOT/sync/registry.json').read_text())
if '$name' in r['skills']:
    r['skills']['$name']['score'] = $score
    Path('$REPO_ROOT/sync/registry.json').write_text(json.dumps(r, ensure_ascii=False, indent=2) + chr(10))
" 2>/dev/null || true
done
echo "Scoring complete."

# Step 3: Git commit
echo ""
echo "--- Step 3: Git ---"
cd "$REPO_ROOT/.."
git add -A
if git diff --cached --quiet; then
    echo "No changes to commit."
else
    git commit -m "chore: mundo full sync — $(date '+%Y-%m-%d')" 2>&1
    git push 2>&1 || echo "WARN: git push failed"
fi

echo ""
echo "=== Done ==="
