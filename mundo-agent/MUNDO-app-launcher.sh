#!/bin/bash
# MUNDO Agent v2.2.2 — macOS .app 启动脚本
# 带同步逻辑，确保启动的是最新版蒙多

# 设置错误处理
set -e

# 获取路径
MUNDO_COMMAND="$HOME/Desktop/lihongwei-cn/MUNDO.command"
MUNDO_DST="$HOME/.hermes/mundo-agent"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 错误处理函数
show_error() {
    osascript -e "display dialog \"$1\" buttons {\"确定\"} default button \"确定\" with icon stop with title \"MUNDO 错误\""
    exit 1
}

# 检查 MUNDO.command 是否存在
if [ ! -f "$MUNDO_COMMAND" ]; then
    show_error "找不到 MUNDO.command 文件！\n\n路径: $MUNDO_COMMAND\n\n请检查蒙多是否正确安装。"
fi

# 检查目标目录是否存在
if [ ! -d "$MUNDO_DST" ]; then
    show_error "找不到蒙多安装目录！\n\n路径: $MUNDO_DST\n\n请检查蒙多是否正确安装。"
fi

# 检查 mundo.py 是否存在
if [ ! -f "$MUNDO_DST/mundo.py" ]; then
    show_error "找不到 mundo.py 文件！\n\n路径: $MUNDO_DST/mundo.py\n\n请检查蒙多是否正确安装。"
fi

# 使用 osascript 打开 Terminal 并执行 MUNDO.command
osascript <<EOF
tell application "Terminal"
    activate
    do script "bash '$MUNDO_COMMAND'"
end tell
EOF

# 退出 MUNDO.app
exit 0
