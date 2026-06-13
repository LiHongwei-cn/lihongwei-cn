#!/bin/bash
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
export PYTHONIOENCODING=utf-8
cd ~/.hermes/mundo-agent
rm -rf __pycache__
export PYTHONDONTWRITEBYTECODE=1
python3 mundo.py
