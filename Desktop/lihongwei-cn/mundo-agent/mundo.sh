#!/bin/bash
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8

cd ~/.hermes/mundo-agent
rm -rf __pycache__

VER=$(cat version.txt 2>/dev/null || echo 'unknown')
echo ""
echo "  MUNDO — THE EMPEROR v${VER}"
echo "  ════════════════════════"
echo ""
echo "  启动蒙多..."
echo ""

export PYTHONDONTWRITEBYTECODE=1
python3 mundo.py
