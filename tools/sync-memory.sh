#!/bin/bash
# 双向同步：Hermes 记忆 ↔ Claude Code CLAUDE.md
# 用法：bash sync-memory.sh [hermes→claude | claude→hermes | check]

HERMES_PROFILE="$HOME/.hermes/memory/profile/user-profile.md"
CLAUDE_MD="$HOME/Desktop/lihongwei-cn/CLAUDE.md"

if [ ! -f "$HERMES_PROFILE" ] || [ ! -f "$CLAUDE_MD" ]; then
    echo "错误：记忆文件不存在"
    exit 1
fi

HERMES_MTIME=$(stat -f %m "$HERMES_PROFILE" 2>/dev/null || stat -c %Y "$HERMES_PROFILE" 2>/dev/null)
CLAUDE_MTIME=$(stat -f %m "$CLAUDE_MD" 2>/dev/null || stat -c %Y "$CLAUDE_MD" 2>/dev/null)

case "${1:-check}" in
    check)
        echo "Hermes 记忆修改时间: $(date -r $HERMES_MTIME 2>/dev/null || date -d @$HERMES_MTIME 2>/dev/null)"
        echo "CLAUDE.md 修改时间:  $(date -r $CLAUDE_MTIME 2>/dev/null || date -d @$CLAUDE_MTIME 2>/dev/null)"
        if [ "$HERMES_MTIME" -gt "$CLAUDE_MTIME" ]; then
            echo "建议方向: hermes→claude"
        elif [ "$CLAUDE_MTIME" -gt "$HERMES_MTIME" ]; then
            echo "建议方向: claude→hermes"
        else
            echo "两边一致，无需同步"
        fi
        ;;
    hermes-to-claude)
        echo "同步方向: Hermes 记忆 → CLAUDE.md"
        echo "请用 Hermes Agent 执行：读取 user-profile.md 内容，更新 CLAUDE.md 对应章节"
        ;;
    claude-to-hermes)
        echo "同步方向: CLAUDE.md → Hermes 记忆"
        echo "请用 Hermes Agent 执行：读取 CLAUDE.md 变更，更新 user-profile.md"
        ;;
esac
