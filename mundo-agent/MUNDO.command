#!/bin/bash
# MUNDO Agent — macOS 双击启动器
# 清屏隐藏 "Last login" 消息
clear
cd "$HOME/.hermes/mundo-agent"
source venv/bin/activate
exec python3 mundo.py "$@"
