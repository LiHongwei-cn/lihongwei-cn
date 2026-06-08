#!/bin/bash
# sync_mundo.sh — 强制三合一同步
# 源码 ~/.hermes 安装版 + /Applications/MUNDO.app + ~/Applications/MUNDO.app
# 
# 用法：
#   bash sync_mundo.sh          # 同步
#   bash sync_mundo.sh --check  # 只检查不修复

set -e

SRC="$(cd "$(dirname "$0")" && pwd)"
DST="$HOME/.hermes/mundo-agent"
APPS=(
    "/Users/huangpeng/Applications/MUNDO.app"
)

# 从源码读版本
VERSION=$(grep '^VERSION' "$SRC/mundo.py" | head -1 | sed 's/.*"\(.*\)".*/\1/')

echo ""
echo "  ╔═══════════════════════════════╗"
echo "  ║   MUNDO Sync Engine v2.0      ║"
echo "  ╚═══════════════════════════════╝"
echo ""
echo "  源码版本: $VERSION"
echo ""

# ── 1. 源码 → ~/.hermes ──────────────────────────────
SYNCED=0
FILES="mundo.py core.py llm.py setup.py tools.py approval.py display.py memory.py memory_import.py models.py agents.py delegation.py cloud_sync.py claude_integration.py codex_integration.py hermes_integration.py"

echo "  [1/3] 源码 → 安装版"
for f in $FILES version.txt requirements.txt MUNDO.command; do
    if [ -f "$SRC/$f" ]; then
        if ! diff -q "$SRC/$f" "$DST/$f" >/dev/null 2>&1; then
            if [ "${1:-}" = "--check" ]; then
                echo "    ⚠️  $f 需要同步"
            else
                cp "$SRC/$f" "$DST/$f"
                echo "    ✏️  $f"
                SYNCED=$((SYNCED + 1))
            fi
        fi
    fi
done
[ $SYNCED -eq 0 ] && [ "${1:-}" != "--check" ] && echo "    ✅ 已是最新"

# ── 2. 更新所有 .app ──────────────────────────────────
echo ""
echo "  [2/3] 更新 Dock .app 版本"
for APP in "${APPS[@]}"; do
    if [ -d "$APP" ]; then
        PLIST="$APP/Contents/Info.plist"
        CUR_VER=$(grep -A1 'CFBundleShortVersionString' "$PLIST" | grep string | sed 's/.*<string>\(.*\)<\/string>.*/\1/')
        if [ "$VERSION" != "$CUR_VER" ]; then
            if [ "${1:-}" = "--check" ]; then
                echo "    ⚠️  $APP: $CUR_VER → $VERSION"
            else
                sed -i '' "s|<string>$CUR_VER</string>|<string>$VERSION</string>|g" "$PLIST"
                /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP" 2>/dev/null || true
                echo "    🔄 $CUR_VER → $VERSION"
            fi
        else
            echo "    ✅ $APP ($CUR_VER)"
        fi
    fi
done

# ── 3. 验证 ────────────────────────────────────────────
echo ""
echo "  [3/3] 三合一验证"
INSTALLED_VER=$(cat "$DST/version.txt" 2>/dev/null | tr -d '[:space:]')
APP_VER=$(grep -A1 'CFBundleShortVersionString' "${APPS[0]}/Contents/Info.plist" 2>/dev/null | grep string | sed 's/.*<string>\(.*\)<\/string>.*/\1/')

ALL_OK=true
if [ "$VERSION" = "$INSTALLED_VER" ]; then
    echo "    ✅ 源码($VERSION) = 安装版($INSTALLED_VER)"
else
    echo "    ❌ 源码($VERSION) ≠ 安装版($INSTALLED_VER)"
    ALL_OK=false
fi
if [ "$VERSION" = "$APP_VER" ]; then
    echo "    ✅ 源码($VERSION) = Dock .app($APP_VER)"
else
    echo "    ❌ 源码($VERSION) ≠ Dock .app($APP_VER)"
    ALL_OK=false
fi

echo ""
if $ALL_OK; then
    echo "  ═══ 全部同步 v$VERSION ✓ ═══"
else
    echo "  ═══ 存在脱节！请重新运行（不加 --check）═══"
fi
echo ""
