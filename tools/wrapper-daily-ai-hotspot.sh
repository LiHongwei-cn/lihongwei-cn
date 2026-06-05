#!/bin/bash
# Wrapper script for daily AI hotspot crawling with virtual environment

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment
source "$PROJECT_DIR/tools/venv/bin/activate"

# Run the daily AI hotspot script
cd "$PROJECT_DIR"
bash "$SCRIPT_DIR/daily-ai-hotspot.sh"