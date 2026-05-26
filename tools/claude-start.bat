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

if not defined ANTHROPIC_API_KEY (
    for /f "tokens=2,*" %%a in ('reg query HKCU\Environment /v ANTHROPIC_API_KEY 2^>nul ^| findstr "REG_"') do set "ANTHROPIC_API_KEY=%%b"
)
if not defined ANTHROPIC_API_KEY (
    if defined DEEPSEEK_API_KEY set "ANTHROPIC_API_KEY=%DEEPSEEK_API_KEY%"
)
if not defined ANTHROPIC_API_KEY (
    for /f "tokens=2,*" %%a in ('reg query HKCU\Environment /v DEEPSEEK_API_KEY 2^>nul ^| findstr "REG_"') do set "ANTHROPIC_API_KEY=%%b"
)
if not defined ANTHROPIC_BASE_URL set "ANTHROPIC_BASE_URL=http://127.0.0.1:3000"

where wt.exe >nul 2>&1
if %errorlevel% equ 0 (
    start "" wt.exe -d "%~dp0." cmd /k "claude --dangerously-skip-permissions --no-chrome"
    exit /b
)

claude --dangerously-skip-permissions --no-chrome
