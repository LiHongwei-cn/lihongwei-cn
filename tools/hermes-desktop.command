#!/bin/bash
# Hermes Agent 一键启动器 (macOS)
# 放到任意目录，双击即可启动 Hermes Agent 对话

echo "⚕ Hermes Agent 启动中..."
echo ""

# 检查 hermes 命令
if ! command -v hermes &> /dev/null; then
    if [ -f "$HOME/.local/bin/hermes" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    else
        echo "❌ Hermes Agent 未安装"
        echo ""
        echo "请先运行安装命令："
        echo "  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
        echo ""
        read -p "按回车退出..."
        exit 1
    fi
fi

# 检查配置文件
if [ ! -f "$HOME/.hermes/.env" ]; then
    echo "⚠ 未检测到 API Key 配置"
    echo ""
    echo "请先运行配置向导："
    echo "  hermes setup"
    echo ""
    read -p "按回车退出..."
    exit 1
fi

echo "✓ Hermes Agent v$(hermes --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"
echo "✓ 配置文件已就绪"
echo ""

cd "$HOME"
hermes chat
