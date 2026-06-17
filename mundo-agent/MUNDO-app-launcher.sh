#!/bin/bash
# MUNDO Agent v2.2.6 — macOS .app 启动脚本
# 自包含版本：自动检测源码目录，确保启动最新版蒙多

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# ═══ 自动检测源码目录 ═══
# 优先级：脚本所在目录 > 桌面项目 > /tmp > ~/.hermes
find_source_dir() {
    # 候选目录列表
    for candidate in \
        "$HOME/Desktop/lihongwei-cn/mundo-agent" \
        "$HOME/Desktop/mundo-agent" \
        "/tmp/mundo-v210-windows/mundo-agent" \
        "$HOME/.hermes/mundo-agent"; do
        if [ -f "$candidate/version.txt" ] && [ -f "$candidate/mundo.py" ]; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# ═══ 错误处理 ═══
show_error() {
    osascript -e "display dialog \"$1\" buttons {\"确定\"} default button \"确定\" with icon stop with title \"MUNDO 错误\""
    exit 1
}

# ═══ 同步函数 ═══
sync_source_to_hermes() {
    local SRC="$1"
    local DST="$HOME/.hermes/mundo-agent"
    
    if [ ! -d "$DST" ]; then
        show_error "找不到蒙多安装目录！\n\n路径: $DST\n\n请先运行 MUNDO.command 完成初始化。"
    fi
    
    local SRC_VER=$(cat "$SRC/version.txt" 2>/dev/null | tr -d '[:space:]')
    local DST_VER=$(cat "$DST/version.txt" 2>/dev/null | tr -d '[:space:]')
    
    if [ "$SRC_VER" != "$DST_VER" ]; then
        echo "  🔄 同步 v$DST_VER → v$SRC_VER ..."
        # 同步所有 .py 文件
        for f in "$SRC"/*.py; do
            [ -f "$f" ] && cp "$f" "$DST/$(basename "$f")"
        done
        # 同步其他核心文件
        for f in version.txt requirements.txt pytest.ini; do
            [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DST/$f"
        done
        # 同步目录
        for dir in mundo_agent tests skills config docs examples skill_store; do
            if [ -d "$SRC/$dir" ]; then
                rsync -a --delete --exclude='__pycache__' "$SRC/$dir/" "$DST/$dir/"
            fi
        done
        # 同步配置
        [ -f "$SRC/pytest.ini" ] && cp "$SRC/pytest.ini" "$DST/pytest.ini"
        [ -f "$SRC/requirements.txt" ] && cp "$SRC/requirements.txt" "$DST/requirements.txt"
        echo "  ✅ 同步完成: v$SRC_VER"
    fi
}

# ═══ 主流程 ═══
SRC_DIR=$(find_source_dir)
if [ -z "$SRC_DIR" ]; then
    show_error "找不到蒙多源码目录！\n\n请确认以下目录之一存在：\n• ~/Desktop/lihongwei-cn/mundo-agent\n• ~/Desktop/mundo-agent\n• /tmp/mundo-v210-windows/mundo-agent"
fi

# 同步到 ~/.hermes
sync_source_to_hermes "$SRC_DIR"

# 创建并执行 MUNDO.command
MUNDO_HERMES="$HOME/.hermes/mundo-agent"
mkdir -p "$HOME/.hermes"

cat > "$HOME/.hermes/MUNDO.command" << 'COMMAND'
#!/bin/bash
cd "$HOME/.hermes/mundo-agent"
source venv/bin/activate 2>/dev/null
exec python3 mundo.py "$@"
COMMAND
chmod +x "$HOME/.hermes/MUNDO.command"

# 使用 osascript 打开 Terminal 并执行 ~/.hermes/MUNDO.command
osascript <<'EOF'
tell application "Terminal"
    activate
    do script "bash ~/.hermes/MUNDO.command"
end tell
EOF

exit 0
