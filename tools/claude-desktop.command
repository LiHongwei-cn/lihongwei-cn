#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

export CLAUDE_CODE_ENTRYPOINT=cli

cd "$WORK_DIR" || exit 1

if ! command -v claude &> /dev/null; then
    echo "ERROR: 'claude' 命令未找到"
    echo "安装方法: brew install claude-code"
    echo "或: npm install -g @anthropic-ai/claude-code"
    read -p "按 Enter 关闭..."
    exit 1
fi

claude --dangerously-skip-permissions --no-chrome
