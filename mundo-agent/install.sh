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

echo "安装完成！"
echo "运行: ./run.sh"
