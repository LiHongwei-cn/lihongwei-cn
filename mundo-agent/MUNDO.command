#!/bin/bash
# MUNDO Agent — macOS 双击启动器
clear
cd "$HOME/.hermes/mundo-agent"
exec python3 mundo.py "$@"
