#!/bin/bash
set -e

echo ""
echo "  Claude Code 全局规范 · 一键部署"
echo "  ================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── 1. 检查 Claude Code ──
if ! command -v claude &>/dev/null; then
    echo "  [!] claude 未安装"
    echo "  安装命令: brew install claude-code"
    echo "  或: npm install -g @anthropic-ai/claude-code"
    echo ""
fi

# ── 2. 创建目录 ──
mkdir -p ~/.claude/rules
mkdir -p ~/.claude/skills

# ── 3. 部署全局指令 ──
echo "  [1/5] 全局 CLAUDE.md"
cp "$SCRIPT_DIR/CLAUDE.md" ~/.claude/CLAUDE.md
echo "    ✓ ~/.claude/CLAUDE.md"

# ── 4. 部署规范 ──
echo "  [2/5] 规范文件"
for f in "$SCRIPT_DIR/rules/"*.md; do
    cp "$f" ~/.claude/rules/
    echo "    ✓ ~/.claude/rules/$(basename "$f")"
done

# ── 5. 部署 Skills ──
echo "  [3/5] Skills"
for skill_dir in "$SCRIPT_DIR/skills/"*/; do
    skill_name=$(basename "$skill_dir")
    mkdir -p ~/.claude/skills/"$skill_name"
    cp -r "$skill_dir"* ~/.claude/skills/"$skill_name"/
    echo "    ✓ ~/.claude/skills/$skill_name/"
done

# ── 6. 部署配置文件 ──
echo "  [4/5] 配置文件"
if [ ! -f ~/.claude/settings.json ]; then
    cp "$SCRIPT_DIR/settings.json" ~/.claude/settings.json
    echo "    ✓ ~/.claude/settings.json (新建，请编辑填入 API Key)"
else
    echo "    ! ~/.claude/settings.json 已存在，跳过（如需覆盖请手动操作）"
fi

if [ ! -f ~/.claude/settings.local.json ]; then
    cp "$SCRIPT_DIR/settings.local.json" ~/.claude/settings.local.json
    echo "    ✓ ~/.claude/settings.local.json (新建)"
else
    echo "    ! ~/.claude/settings.local.json 已存在，跳过"
fi

# ── 7. 完成 ──
echo "  [5/5] 完成"
echo ""
echo "  ═══════════════════════════════════"
echo "  部署完成！"
echo "  ═══════════════════════════════════"
echo ""
echo "  后续步骤:"
echo "  1. 编辑 ~/.claude/settings.json 填入你的 API Key"
echo "  2. 运行 claude 进入对话"
echo "  3. 输入 /neat 测试 skill 是否正常加载"
echo ""
