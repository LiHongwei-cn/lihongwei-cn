#!/bin/bash
# macOS 双击启动 — 调用 start_bot.sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec bash "$SCRIPT_DIR/start_bot.sh"
