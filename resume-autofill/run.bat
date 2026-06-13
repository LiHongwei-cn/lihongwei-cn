@echo off
REM 简历投递系统 — Windows 启动脚本
cd /d "%~dp0"

REM 创建虚拟环境
if not exist "venv" (
    echo 首次运行，正在安装...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    playwright install chromium
) else (
    call venv\Scripts\activate.bat
)

python app.py
pause
