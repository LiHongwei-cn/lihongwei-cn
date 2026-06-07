#!/bin/bash
# MUNDO Agent — macOS 双击启动器
# 启动前自动版本同步
clear

SRC="$HOME/Desktop/lihongwei-cn/mundo-agent"
DST="$HOME/.hermes/mundo-agent"

if [ -f "$SRC/version.txt" ] && [ -f "$DST/version.txt" ]; then
    SRC_VER=$(cat "$SRC/version.txt" | tr -d '[:space:]')
    DST_VER=$(cat "$DST/version.txt" | tr -d '[:space:]')
    
    if [ "$SRC_VER" != "$DST_VER" ]; then
        echo "  🔄 版本脱节，自动同步..."
        for f in mundo.py core.py llm.py setup.py tools.py approval.py display.py memory.py memory_import.py models.py agents.py delegation.py cloud_sync.py; do
            [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DST/$f"
        done
        cp "$SRC/version.txt" "$DST/version.txt"
        echo "  ✅ $DST_VER → $SRC_VER"
    fi
fi

cd "$HOME/.hermes/mundo-agent"
exec python3 mundo.py "$@"
