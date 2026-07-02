#!/bin/bash
# MUNDO Agent v2.3.1 — macOS .app 启动脚本
# 调用统一同步脚本，确保程序坞启动器始终运行最新版

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 程序坞/Finder 启动时 HOME 可能未设置
if [ -z "${HOME:-}" ]; then
    USER_NAME="$(/usr/bin/id -un 2>/dev/null || echo "")"
    if [ -n "$USER_NAME" ] && [ -d "/Users/$USER_NAME" ]; then
        export HOME="/Users/$USER_NAME"
    else
        export HOME="$(/usr/bin/eval echo "~$USER_NAME")"
    fi
fi

show_error() {
    osascript -e "display dialog \"$1\" buttons {\"确定\"} default button \"确定\" with icon stop with title \"MUNDO 错误\""
    exit 1
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/mundo-sync.sh"

if [ ! -f "$SYNC_SCRIPT" ]; then
    show_error "找不到 mundo-sync.sh！\\n\\n路径: $SYNC_SCRIPT\\n\\n请重新安装蒙多 Agent。"
fi

if ! bash "$SYNC_SCRIPT"; then
    show_error "蒙多同步失败！\\n\\n请确认源码目录存在且可访问。"
fi

MUNDO_HERMES="$HOME/.hermes/mundo-agent"
mkdir -p "$HOME/.hermes"

cat > "$HOME/.hermes/MUNDO.command" << 'COMMAND'
#!/bin/bash
cd "$HOME/.hermes/mundo-agent"
source venv/bin/activate 2>/dev/null
export PYTHONDONTWRITEBYTECODE=1
exec python3 mundo.py "$@"
COMMAND
chmod +x "$HOME/.hermes/MUNDO.command"

osascript <<'EOF'
tell application "Terminal"
    activate
    do script "bash ~/.hermes/MUNDO.command"
    set custom title of front window to "MUNDO - THE EMPEROR"
end tell
EOF

exit 0
