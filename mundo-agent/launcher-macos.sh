#!/bin/bash
# MUNDO Agent v2.1.0 — macOS .app 启动脚本
# 薄壳模式：直接调用 ~/.hermes/mundo-agent/mundo.py，不做同步
# 版本更新由 mundo.py 内部的 /update 命令处理

MUNDO_HOME="$HOME/.hermes/mundo-agent"
LAUNCH_SCRIPT="/tmp/mundo-launch.sh"

cat > "$LAUNCH_SCRIPT" <<'SCRIPT'
#!/bin/bash
clear

MUNDO_HOME="$HOME/.hermes/mundo-agent"

# 检查蒙多是否安装
if [ ! -f "$MUNDO_HOME/mundo.py" ]; then
    echo "错误: 蒙多未安装。请先运行安装脚本。"
    echo "路径: $MUNDO_HOME/mundo.py"
    read -p "按回车退出..."
    exit 1
fi

# 启动蒙多
cd "$MUNDO_HOME"

# 检查虚拟环境
if [ -d "$MUNDO_HOME/venv" ]; then
    source "$MUNDO_HOME/venv/bin/activate" 2>/dev/null
fi

python3 mundo.py "$@"
SCRIPT

chmod +x "$LAUNCH_SCRIPT"

osascript <<EOF
tell application "Terminal"
    activate
    do script "$LAUNCH_SCRIPT"
    set custom title of front window to "MUNDO"
end tell
EOF
