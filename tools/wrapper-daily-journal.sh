#!/bin/bash
# Wrapper script for daily journal learning with virtual environment

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CLOUD_DIR="$PROJECT_DIR/mundo-cloud"

# Activate virtual environment
source "$CLOUD_DIR/venv/bin/activate"

# Run the daily journal script
cd "$CLOUD_DIR"
bash "$CLOUD_DIR/scripts/daily_journal.sh"