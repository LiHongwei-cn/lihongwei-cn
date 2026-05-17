#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR" || exit 1

if ! command -v claude &>/dev/null; then
    osascript -e 'display dialog "claude 命令未找到，请先安装：npm install -g @anthropic-ai/claude-code" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

export CLAUDE_CODE_ENTRYPOINT=cli
claude --dangerously-skip-permissions --no-chrome
