#!/bin/bash
# MUNDO Agent — 一键安装脚本（macOS / Linux）
set -e

echo ""
echo "    ╔══════════════════════════════════════════╗"
echo "    ║         👑 MUNDO Agent 安装程序          ║"
echo "    ╚══════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "✗ 未找到 Python 3。请先安装："
    echo "  macOS:  brew install python"
    echo "  Linux:  sudo apt install python3 python3-pip"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]); then
    echo "✗ Python 版本太低: $PY_VER（需要 3.10+）"
    echo "  brew install python@3.12  # macOS"
    echo "  sudo apt install python3.12  # Linux"
    exit 1
fi
echo "✓ Python $PY_VER"

# 检查 Git
if ! command -v git &>/dev/null; then
    echo "✗ 未找到 Git。请先安装："
    echo "  macOS:  brew install git"
    echo "  Linux:  sudo apt install git"
    exit 1
fi
echo "✓ Git $(git --version | awk '{print $3}')"

# 安装目录
MUNDO_DIR="$HOME/.hermes/mundo-agent"
mkdir -p "$MUNDO_DIR"

# 下载文件
REPO_URL="https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/mundo-agent"
echo ""
echo "下载蒙多 Agent 文件..."

for f in mundo.py engine.py llm.py tools.py agents.py delegation.py approval.py cloud_sync.py setup.py mundo.sh MUNDO.command; do
    curl -fsSL "$REPO_URL/$f" -o "$MUNDO_DIR/$f" 2>/dev/null || true
    echo "  ✓ $f"
done

chmod +x "$MUNDO_DIR/mundo.py" "$MUNDO_DIR/mundo.sh" "$MUNDO_DIR/MUNDO.command" 2>/dev/null

# 创建全局命令
BIN_DIR="$HOME/bin"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/mundo" << 'SCRIPT'
#!/bin/bash
exec python3 "$HOME/.hermes/mundo-agent/mundo.py" "$@"
SCRIPT
chmod +x "$BIN_DIR/mundo"

# 检查 PATH
if ! echo "$PATH" | grep -q "$HOME/bin"; then
    SHELL_RC="$HOME/.zshrc"
    [ -f "$HOME/.bashrc" ] && SHELL_RC="$HOME/.bashrc"
    echo 'export PATH="$HOME/bin:$PATH"' >> "$SHELL_RC"
    export PATH="$HOME/bin:$PATH"
    echo "✓ 已添加 ~/bin 到 PATH"
fi

# 从云仓库拉取 Skills 和全局规范
echo ""
echo "从云仓库拉取 Skills 和全局规范..."
REPO_TMP="/tmp/mundo-repo-$$"
git clone --depth=1 https://github.com/LiHongwei-cn/lihongwei-cn.git "$REPO_TMP" 2>/dev/null

if [ -d "$REPO_TMP/global-specs/skills" ]; then
    SKILLS_DIR="$HOME/.hermes/skills"
    mkdir -p "$SKILLS_DIR"
    cp_count=0
    for d in "$REPO_TMP/global-specs/skills"/*/; do
        name=$(basename "$d")
        if [ -f "$d/SKILL.md" ]; then
            mkdir -p "$SKILLS_DIR/$name"
            cp "$d/SKILL.md" "$SKILLS_DIR/$name/SKILL.md"
            cp_count=$((cp_count + 1))
        fi
    done
    echo "  ✓ 已部署 $cp_count 个 Skills"
fi

if [ -d "$REPO_TMP/global-specs/rules" ]; then
    RULES_DIR="$HOME/.hermes/rules"
    mkdir -p "$RULES_DIR"
    cp "$REPO_TMP/global-specs/rules/"*.md "$RULES_DIR/" 2>/dev/null
    echo "  ✓ 已部署全局规范"
fi

# 保存仓库缓存供后续同步
mkdir -p "$MUNDO_DIR/repo_cache"
cp -r "$REPO_TMP/.git" "$MUNDO_DIR/repo_cache/" 2>/dev/null
rm -rf "$REPO_TMP"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         👑 安装完成！                    ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "已部署内容："
echo "  • MUNDO Agent 引擎（9 个 Python 模块）"
echo "  • Skills（从云仓库自动拉取）"
echo "  • 全局规范（从云仓库自动拉取）"
echo ""
echo "启动蒙多："
echo "  mundo              # 交互模式"
echo "  mundo -q '问题'    # 单次查询"
echo ""
echo "首次启动会引导你选择 AI 模型并输入 API Key。"
echo "Key 仅保存在本地，不会上传。"
echo ""
