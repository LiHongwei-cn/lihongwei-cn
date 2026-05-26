@echo off
chcp 65001 >nul
set CLAUDE_CODE_ENTRYPOINT=cli
cd /d "%~dp0"

where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo claude 命令未找到，请先安装: npm install -g @anthropic-ai/claude-code
    pause
    exit /b 1
)

where wt.exe >nul 2>&1
if %errorlevel% equ 0 (
    start "" wt.exe -d "%~dp0." cmd /k "claude --dangerously-skip-permissions --no-chrome"
    exit /b
)

claude --dangerously-skip-permissions --no-chrome
