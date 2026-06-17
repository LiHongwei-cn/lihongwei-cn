#!/bin/bash
# MUNDO Agent v2.2.6 — Terminal 启动脚本
cd "$HOME/.hermes/mundo-agent"
source venv/bin/activate 2>/dev/null
exec python3 mundo.py "$@"
