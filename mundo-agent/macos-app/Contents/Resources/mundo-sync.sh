#!/bin/bash
# MUNDO Agent — 统一源码同步脚本 v2.3.1
# 所有启动器（程序坞 .app / MUNDO.command / MUNDO-app-launcher.sh）均调用此脚本
# 确保 ~/.hermes/mundo-agent 始终运行最新版本

set -eo pipefail

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"

# 程序坞/Finder 启动时 HOME 可能未设置，必须先修复
if [ -z "${HOME:-}" ]; then
    USER_NAME="$(/usr/bin/id -un 2>/dev/null || echo "")"
    if [ -n "$USER_NAME" ] && [ -d "/Users/$USER_NAME" ]; then
        export HOME="/Users/$USER_NAME"
    else
        export HOME="$(/usr/bin/eval echo "~$USER_NAME")"
    fi
fi

DST="${MUNDO_INSTALL_DIR:-$HOME/.hermes/mundo-agent}"

# ═══ 候选源码目录（按优先级） ═══
CANDIDATES=(
    "$HOME/Desktop/MUNDO/mundo-agent"
    "$HOME/Desktop/lihongwei-cn/mundo-agent"
    "$HOME/Desktop/mundo-agent"
    "/tmp/mundo-v210-windows/mundo-agent"
)

# 脚本自身所在目录（含 version.txt + mundo.py 才算有效源码）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/version.txt" ] && [ -f "$SCRIPT_DIR/mundo.py" ]; then
    CANDIDATES=("$SCRIPT_DIR" "${CANDIDATES[@]}")
fi

# ═══ 解析版本号 ═══
parse_version() {
    local ver
    ver=$(cat "$1/version.txt" 2>/dev/null | tr -d '[:space:]' | sed 's/^v//')
    echo "${ver:-0.0.0}"
}

version_gt() {
    [ "$(printf '%s\n' "$2" "$1" | sort -V | head -1)" = "$2" ] && [ "$1" != "$2" ]
}

# ═══ 查找最新源码目录 ═══
find_newest_source() {
    local best="" best_ver="0.0.0" candidate ver
    for candidate in "${CANDIDATES[@]}"; do
        [ -f "$candidate/version.txt" ] && [ -f "$candidate/mundo.py" ] || continue
        ver=$(parse_version "$candidate")
        if [ -z "$best" ] || version_gt "$ver" "$best_ver"; then
            best="$candidate"
            best_ver="$ver"
        fi
    done
    echo "$best"
}

# ═══ 同步源码到安装目录 ═══
sync_to_install() {
    local SRC="$1"
    mkdir -p "$DST"

    local SRC_VER=$(parse_version "$SRC")
    local DST_VER=$(parse_version "$DST")

    echo "  📦 源码: $SRC (v$SRC_VER)"
    echo "  📂 安装: $DST (v$DST_VER)"

    # 同步所有 .py 文件
    for f in "$SRC"/*.py; do
        [ -f "$f" ] && cp -f "$f" "$DST/$(basename "$f")"
    done

    # 同步核心文件
    for f in version.txt requirements.txt pytest.ini Dockerfile docker-compose.yml README.md GLOBAL_SPEC.md; do
        [ -f "$SRC/$f" ] && cp -f "$SRC/$f" "$DST/$f"
    done

    # 同步目录
    for dir in mundo_agent tests skills config docs examples skill_store .github macos-app; do
        if [ -d "$SRC/$dir" ]; then
            rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' --exclude='*.backup' \
                "$SRC/$dir/" "$DST/$dir/"
        fi
    done

    # 同步启动脚本
    for f in mundo.sh MUNDO.command MUNDO-app-launcher.sh mundo-sync.sh; do
        [ -f "$SRC/$f" ] && cp -f "$SRC/$f" "$DST/$f" && chmod +x "$DST/$f" 2>/dev/null || true
    done

    # 写入同步标记
    echo "$SRC_VER" > "$DST/.sync_version"
    echo "$SRC" > "$DST/.sync_source"
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "$DST/.sync_time"

    # 同步 .app 到 Applications（程序坞启动器）
    if [ -d "$SRC/macos-app" ]; then
        for APP_DST in "/Applications/MUNDO.app" "$HOME/Applications/MUNDO.app"; do
            mkdir -p "$APP_DST/Contents/MacOS"
            mkdir -p "$APP_DST/Contents/Resources"
            rsync -a --delete "$SRC/macos-app/" "$APP_DST/" 2>/dev/null || true
            # 内置同步脚本到 Resources
            cp -f "$SRC/mundo-sync.sh" "$APP_DST/Contents/Resources/mundo-sync.sh" 2>/dev/null || true
            chmod +x "$APP_DST/Contents/MacOS/MUNDO" 2>/dev/null || true
            chmod +x "$APP_DST/Contents/Resources/mundo-sync.sh" 2>/dev/null || true
        done
    fi

    echo "  ✅ 同步完成: v$SRC_VER → $DST"
}

# ═══ 主流程 ═══
SRC_DIR=$(find_newest_source)
if [ -z "$SRC_DIR" ]; then
    echo "❌ 找不到蒙多源码目录！" >&2
    echo "请确认以下目录之一存在：" >&2
    for c in "${CANDIDATES[@]}"; do echo "  • $c" >&2; done
    exit 1
fi

sync_to_install "$SRC_DIR"

# 验证安装版本
INSTALLED_VER=$(parse_version "$DST")
SRC_VER=$(parse_version "$SRC_DIR")
if [ "$INSTALLED_VER" != "$SRC_VER" ]; then
    echo "❌ 版本验证失败: 安装 v$INSTALLED_VER != 源码 v$SRC_VER" >&2
    exit 1
fi

echo "  🔖 版本验证通过: v$INSTALLED_VER"
