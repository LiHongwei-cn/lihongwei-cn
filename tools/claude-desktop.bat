@echo off
set WORK_DIR=%~dp0..
set CLAUDE_CODE_ENTRYPOINT=cli
cd /d "%WORK_DIR%"

where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: 'claude' 命令未找到
    echo 请先安装: npm install -g @anthropic-ai/claude-code
    pause
    exit /b 1
)

where wt.exe >nul 2>&1
if %errorlevel% equ 0 (
    start "" wt.exe -d "%WORK_DIR%" cmd /k "set CLAUDE_CODE_ENTRYPOINT=cli && claude --dangerously-skip-permissions --no-chrome"
    exit /b
)

claude --dangerously-skip-permissions --no-chrome
