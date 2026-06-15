#!/bin/bash
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 检查 hermes 命令
if ! command -v hermes &> /dev/null; then
    if [ -f "$HOME/.local/bin/hermes" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    else
        echo "❌ Hermes Agent 未安装"
        echo "  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
        read -p "按回车退出..."
        exit 1
    fi
fi

# 检查配置
if [ ! -f "$HOME/.hermes/.env" ]; then
    echo "⚠ 未检测到 API Key，请先运行: hermes setup"
    read -p "按回车退出..."
    exit 1
fi

cd "$HOME"
hermes chat
