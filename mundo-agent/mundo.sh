#!/bin/bash
# MUNDO Agent v2.2.9 — 启动脚本（自动同步 + 编码修复）

# ── 终端编码修复（解决程序坞打开乱码） ──
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export TERM=${TERM:-xterm-256color}
export PYTHONDONTWRITEBYTECODE=1

MUNDO_HOME="$HOME/.hermes/mundo-agent"
SRC_REPO="$HOME/Desktop/lihongwei-cn/mundo-agent"

# ── 自动同步（从源码仓库拉取最新版） ──
sync_latest() {
    if [ ! -d "$SRC_REPO" ]; then
        return 0
    fi
    if [ ! -f "$SRC_REPO/version.txt" ] || [ ! -f "$SRC_REPO/mundo.py" ]; then
        return 0
    fi

    local src_ver=$(head -1 "$SRC_REPO/version.txt" 2>/dev/null | tr -d '[:space:]v')
    local dst_ver=$(head -1 "$MUNDO_HOME/version.txt" 2>/dev/null | tr -d '[:space:]v')

    if [ "$src_ver" = "$dst_ver" ]; then
        return 0
    fi

    printf "\033[33m  Syncing v%s -> v%s ...\033[0m\n" "$dst_ver" "$src_ver"

    # 同步所有 .py 文件
    cp "$SRC_REPO"/*.py "$MUNDO_HOME/" 2>/dev/null

    # 同步核心配置文件
    for f in version.txt requirements.txt mundo.sh; do
        [ -f "$SRC_REPO/$f" ] && cp "$SRC_REPO/$f" "$MUNDO_HOME/$f"
    done

    # 同步子目录
    for sub in tests skills config mundo_agent skill_store docs examples; do
        if [ -d "$SRC_REPO/$sub" ]; then
            mkdir -p "$MUNDO_HOME/$sub"
            rsync -a --delete --exclude='__pycache__' --exclude='*.pyc' \
                "$SRC_REPO/$sub/" "$MUNDO_HOME/$sub/" 2>/dev/null
        fi
    done

    printf "\033[32m  Done: v%s\033[0m\n" "$src_ver"
}

# ── 主流程 ──
cd "$MUNDO_HOME" || exit 1
rm -rf __pycache__ 2>/dev/null

sync_latest

VER=$(head -1 version.txt 2>/dev/null || echo "unknown")

printf "\n"
printf "  MUNDO  THE EMPEROR  %s\n" "$VER"
printf "  ========================\n"
printf "\n"

exec python3 mundo.py "$@"
