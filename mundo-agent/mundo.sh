#!/bin/bash
# MUNDO Agent v2.2.9 — 自动同步启动脚本
# 程序坞打开时自动从源码目录同步最新版，确保始终运行最新蒙多
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8

MUNDO_HOME="$HOME/.hermes/mundo-agent"

# ═══ 自动同步：从源码目录拉取最新版 ═══
auto_sync() {
    # 候选源码目录（按优先级）
    for src in \
        "$HOME/Desktop/lihongwei-cn/mundo-agent" \
        "$HOME/Desktop/mundo-agent"; do
        if [ -f "$src/version.txt" ] && [ -f "$src/mundo.py" ]; then
            local src_ver=$(cat "$src/version.txt" 2>/dev/null | tr -d '[:space:]v')
            local dst_ver=$(cat "$MUNDO_HOME/version.txt" 2>/dev/null | tr -d '[:space:]v')
            if [ "$src_ver" != "$dst_ver" ]; then
                echo "  🔄 检测到新版本 v$src_ver，正在同步..."
                cp "$src"/*.py "$MUNDO_HOME/" 2>/dev/null
                cp "$src"/version.txt "$MUNDO_HOME/" 2>/dev/null
                [ -f "$src/requirements.txt" ] && cp "$src/requirements.txt" "$MUNDO_HOME/" 2>/dev/null
                # 同步子目录
                for sub in tests skills config mundo_agent; do
                    [ -d "$src/$sub" ] && rsync -a --delete --exclude='__pycache__' "$src/$sub/" "$MUNDO_HOME/$sub/" 2>/dev/null
                done
                echo "  ✅ 同步完成: v$src_ver"
            fi
            break
        fi
    done
}

cd "$MUNDO_HOME"
rm -rf __pycache__

auto_sync

VER=$(cat version.txt 2>/dev/null || echo 'unknown')
echo ""
echo "  👑 MUNDO — THE EMPEROR ${VER}"
echo "  ═════════════════════════════"
echo ""

export PYTHONDONTWRITEBYTECODE=1
exec python3 mundo.py "$@"
