#!/bin/bash
# MUNDO Agent v2.2.3 — macOS .app 启动脚本
# 带同步逻辑，确保启动的是最新版蒙多
# v2.2.4: 修复 PATH 环境变量 + 更好的错误处理

# 确保 PATH 包含常用目录（.app 启动时 PATH 可能不完整）
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 获取路径
MUNDO_COMMAND="$HOME/Desktop/lihongwei-cn/MUNDO.command"
MUNDO_DST="$HOME/.hermes/mundo-agent"

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
    show_error "找不到蒙多安装目录！\n\n路径: $MUNDO_DST\n\n请先运行 MUNDO.command 完成初始化。"
fi

# 检查 mundo.py 是否存在
if [ ! -f "$MUNDO_DST/mundo.py" ]; then
    show_error "找不到 mundo.py 文件！\n\n路径: $MUNDO_DST/mundo.py\n\n请先运行 MUNDO.command 完成初始化。"
fi

# 使用 osascript 打开 Terminal 并执行 MUNDO.command
osascript <<'EOF'
tell application "Terminal"
    activate
    do script "bash \"$HOME/Desktop/lihongwei-cn/MUNDO.command\""
end tell
EOF

# 退出 MUNDO.app
exit 0
