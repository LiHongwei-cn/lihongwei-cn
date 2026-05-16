#!/bin/bash
# Claude Code Desktop Launcher for macOS
# Double-click to launch Claude Code in Terminal
# Or run: chmod +x claude-desktop.command && open claude-desktop.command

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

export CLAUDE_CODE_ENTRYPOINT=cli

cd "$WORK_DIR" || exit 1

# Check if claude is available
if ! command -v claude &> /dev/null; then
    echo "ERROR: 'claude' command not found."
    echo "Install Claude Code first: brew install claude-code"
    echo "Or: npm install -g @anthropic-ai/claude-code"
    read -p "Press Enter to close..."
    exit 1
fi

claude --dangerously-skip-permissions --no-chrome
