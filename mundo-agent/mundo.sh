#!/bin/bash
# MUNDO Agent — macOS/Linux 启动器
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "首次运行，正在安装..."
    bash install.sh
fi

source venv/bin/activate

case "${1:-}" in
    -h|--help)
        echo "用法: mundo [选项]"
        echo ""
        echo "  (无参数)     启动蒙多 CLI 交互模式"
        echo "  -q TEXT      单次查询模式"
        echo "  -h           显示帮助"
        echo ""
        ;;
    *)
        exec python3 mundo.py "$@"
        ;;
esac
