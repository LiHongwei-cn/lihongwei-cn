#!/bin/bash
# MUNDO Agent 安装脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "安装 MUNDO Agent..."

# 检查Python版本
PYTHON_CMD=""
for cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" -c "import sys; print(sys.version_info[:2])" 2>/dev/null)
        if [[ "$version" =~ ^\(3\.(1[0-2]|[2-9][0-9]?)\) ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "错误: 需要 Python 3.10+"
    exit 1
fi

echo "使用 $PYTHON_CMD ($($PYTHON_CMD --version))"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    $PYTHON_CMD -m venv venv
fi

# 安装依赖
echo "安装依赖..."
source venv/bin/activate
pip install --quiet requests beautifulsoup4 prompt_toolkit rich

# 创建 macOS .app 启动器（如果在 macOS 上）
if [ "$(uname)" = "Darwin" ] && [ -d "macos-app" ]; then
    APP_DIR="$HOME/Applications/MUNDO.app"
    mkdir -p "$HOME/Applications"
    cp -R macos-app "$APP_DIR"
    chmod +x "$APP_DIR/Contents/MacOS/MUNDO"
    echo "已创建 Dock 启动器: $APP_DIR"
fi

echo ""
echo "安装完成！"
echo ""
echo "启动方式："
echo "  ./run.sh              # 终端启动"
echo "  双击 MUNDO.command    # macOS 双击启动"
echo "  双击 MUNDO.app        # macOS Dock 启动（需先安装）"
echo ""
