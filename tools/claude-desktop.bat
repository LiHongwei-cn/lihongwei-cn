@echo off
set WORK_DIR=%~dp0..
cd /d "%WORK_DIR%"

set CLAUDE_CODE_ENTRYPOINT=cli

where wt.exe >nul 2>&1
if %errorlevel% equ 0 (
    start "" wt.exe -d "%WORK_DIR%" cmd /k "set CLAUDE_CODE_ENTRYPOINT=cli && claude --dangerously-skip-permissions --no-chrome"
    exit /b
)

claude --dangerously-skip-permissions --no-chrome