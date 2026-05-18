@echo off
chcp 65001 >nul
title Claude Code · AI 对话
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════════
:: Claude Code + DeepSeek CCS 一键启动器
:: 下载后放到 F:\111 双击即可
:: ═══════════════════════════════════════════════

set "WORK_DIR=%~dp0"
set "WORK_DIR=%WORK_DIR:~0,-1%"
cd /d "%WORK_DIR%"

echo.
echo   Claude Code 启动中...

:: ── 1. 检查 claude 是否安装 ──
where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo   [错误] claude 未安装
    echo   请先运行: npm install -g @anthropic-ai/claude-code
    pause
    exit /b 1
)

:: ── 2. 从注册表读取 API Key（兼容 Windows 环境变量） ──
if not defined ANTHROPIC_API_KEY (
    for /f "tokens=2*" %%a in ('reg query HKCU\Environment /v ANTHROPIC_API_KEY 2^>nul ^| findstr ANTHROPIC_API_KEY') do (
        set "ANTHROPIC_API_KEY=%%b"
    )
)
if not defined DEEPSEEK_API_KEY (
    for /f "tokens=2*" %%a in ('reg query HKCU\Environment /v DEEPSEEK_API_KEY 2^>nul ^| findstr DEEPSEEK_API_KEY') do (
        set "DEEPSEEK_API_KEY=%%b"
    )
)

:: ── 3. 自动设置 ANTHROPIC_BASE_URL ──
if not defined ANTHROPIC_BASE_URL (
    :: 默认指向 CCS 本地代理
    set "ANTHROPIC_BASE_URL=http://127.0.0.1:3000"
)

:: ── 4. 检查 CCS 是否在运行 ──
curl -s -o nul "http://127.0.0.1:3000/v1/models" 2>&1
if %errorlevel% neq 0 (
    echo   CCS 未运行，尝试启动...
    :: 常见 CCS 启动路径
    if exist "%WORK_DIR%\ccs\server.js" (
        start "CCS" cmd /c "cd /d %WORK_DIR%\ccs && node server.js"
        timeout /t 3 /nobreak >nul
    ) else if exist "%WORK_DIR%\ccs\index.js" (
        start "CCS" cmd /c "cd /d %WORK_DIR%\ccs && node index.js"
        timeout /t 3 /nobreak >nul
    )
)

:: ── 5. 设置入口点 ──
set "CLAUDE_CODE_ENTRYPOINT=cli"

:: ── 6. 在 Windows Terminal 中启动 ──
where wt.exe >nul 2>&1
if %errorlevel% equ 0 (
    start "" wt.exe -d "%WORK_DIR%" cmd /k "set CLAUDE_CODE_ENTRYPOINT=cli && set ANTHROPIC_BASE_URL=%ANTHROPIC_BASE_URL% && set ANTHROPIC_API_KEY=%ANTHROPIC_API_KEY% && claude --dangerously-skip-permissions --no-chrome"
    exit /b
)

:: ── 7. 回退：普通终端启动 ──
claude --dangerously-skip-permissions --no-chrome
pause
