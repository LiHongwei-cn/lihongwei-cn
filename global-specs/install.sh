#!/bin/bash
set -e

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║  全局规范 · 通用多 Agent 一键部署         ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEPLOYED=0
SKIPPED=0

deploy() {
    local name="$1"
    local src="$2"
    local dst="$3"
    if [ -f "$src" ]; then
        mkdir -p "$(dirname "$dst")"
        if [ -f "$dst" ] && diff -q "$src" "$dst" >/dev/null 2>&1; then
            echo "  ○ $name (无变化，跳过)"
            SKIPPED=$((SKIPPED + 1))
        else
            cp "$src" "$dst"
            echo "  ✓ $name"
            DEPLOYED=$((DEPLOYED + 1))
        fi
    fi
}

# ═══════════════════════════════════════════
# 1. Claude Code
# ═══════════════════════════════════════════
echo "  ━━ Claude Code ━━"
if command -v claude &>/dev/null || [ -d ~/.claude ]; then
    mkdir -p ~/.claude/rules ~/.claude/skills
    deploy "全局 CLAUDE.md" "$SCRIPT_DIR/agents/claude-code/CLAUDE.md" ~/.claude/CLAUDE.md
    for f in "$SCRIPT_DIR/rules/"*.md; do
        [ -f "$f" ] && deploy "rules/$(basename "$f")" "$f" ~/.claude/rules/"$(basename "$f")"
    done
    for skill_dir in "$SCRIPT_DIR/skills/"*/; do
        [ -d "$skill_dir" ] || continue
        skill_name=$(basename "$skill_dir")
        mkdir -p ~/.claude/skills/"$skill_name"
        cp -r "$skill_dir"* ~/.claude/skills/"$skill_name"/ 2>/dev/null
        echo "  ✓ skills/$skill_name/"
    done
    [ -f ~/.claude/settings.json ] || { [ -f "$SCRIPT_DIR/settings.json" ] && cp "$SCRIPT_DIR/settings.json" ~/.claude/settings.json && echo "  ✓ settings.json (新建)"; }
else
    echo "  ⊘ Claude Code 未安装，跳过"
fi
echo ""

# ═══════════════════════════════════════════
# 2. Hermes Agent
# ═══════════════════════════════════════════
echo "  ━━ Hermes Agent ━━"
if command -v hermes &>/dev/null || [ -d ~/.hermes ]; then
    mkdir -p ~/.hermes/skills
    deploy "全局 SOUL.md" "$SCRIPT_DIR/agents/hermes/SOUL.md" ~/.hermes/SOUL.md
    for skill_dir in "$SCRIPT_DIR/skills/"*/; do
        [ -d "$skill_dir" ] || continue
        skill_name=$(basename "$skill_dir")
        mkdir -p ~/.hermes/skills/"$skill_name"
        cp -r "$skill_dir"* ~/.hermes/skills/"$skill_name"/ 2>/dev/null
        echo "  ✓ skills/$skill_name/"
    done
else
    echo "  ⊘ Hermes Agent 未安装，跳过"
fi
echo ""

# ═══════════════════════════════════════════
# 3. OpenAI Codex
# ═══════════════════════════════════════════
echo "  ━━ OpenAI Codex ━━"
if command -v codex &>/dev/null || [ -d ~/.codex ]; then
    deploy "AGENTS.md" "$SCRIPT_DIR/agents/codex/AGENTS.md" ~/.codex/AGENTS.md
else
    echo "  ⊘ Codex 未安装，跳过"
fi
echo ""

# ═══════════════════════════════════════════
# 4. Cursor
# ═══════════════════════════════════════════
echo "  ━━ Cursor ━━"
if [ -d "$HOME/Library/Application Support/Cursor" ] || [ -d "$HOME/.cursor" ]; then
    echo "  提示: Cursor 使用项目级 .cursorrules"
    echo "  请将 agents/cursor/.cursorrules 复制到你的项目根目录"
    echo "  或运行: cp $SCRIPT_DIR/agents/cursor/.cursorrules <你的项目>/"
else
    echo "  ⊘ Cursor 未安装，跳过"
fi
echo ""

# ═══════════════════════════════════════════
# 5. Windsurf
# ═══════════════════════════════════════════
echo "  ━━ Windsurf ━━"
if [ -d "$HOME/Library/Application Support/Windsurf" ] || [ -d "$HOME/.windsurf" ]; then
    echo "  提示: Windsurf 使用项目级 .windsurfrules"
    echo "  请将 agents/windsurf/.windsurfrules 复制到你的项目根目录"
    echo "  或运行: cp $SCRIPT_DIR/agents/windsurf/.windsurfrules <你的项目>/"
else
    echo "  ⊘ Windsurf 未安装，跳过"
fi
echo ""

# ═══════════════════════════════════════════
# 6. GitHub Copilot
# ═══════════════════════════════════════════
echo "  ━━ GitHub Copilot ━━"
echo "  提示: Copilot 使用项目级 .github/copilot-instructions.md"
echo "  请将 agents/copilot/.github/ 复制到你的项目根目录"
echo ""

# ═══════════════════════════════════════════
# 完成
# ═══════════════════════════════════════════
echo "  ═══════════════════════════════════════"
echo "  部署完成！已部署 $DEPLOYED 项，跳过 $SKIPPED 项"
echo "  ═══════════════════════════════════════"
echo ""
