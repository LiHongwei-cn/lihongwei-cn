#!/bin/bash
# MUNDO Agent — macOS 双击启动器
# 同步逻辑静默执行，Terminal 只显示蒙多

SRC="$HOME/Desktop/lihongwei-cn/mundo-agent"
DST="$HOME/.hermes/mundo-agent"

if [ -f "$SRC/version.txt" ] && [ -f "$DST/version.txt" ]; then
    SRC_VER=$(cat "$SRC/version.txt" | tr -d '[:space:]')
    DST_VER=$(cat "$DST/version.txt" | tr -d '[:space:]')

    if [ "$SRC_VER" != "$DST_VER" ]; then
        for f in mundo.py core.py llm.py setup.py tools.py approval.py display.py memory.py cloud_sync.py; do
            [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DST/$f"
        done
        cp "$SRC/version.txt" "$DST/version.txt"
        [ -f "$SRC/requirements.txt" ] && cp "$SRC/requirements.txt" "$DST/requirements.txt"
    fi
fi

cd "$HOME/.hermes/mundo-agent"
source venv/bin/activate
exec python3 mundo.py "$@"
