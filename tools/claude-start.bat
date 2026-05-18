@echo off
chcp 65001 >nul
title Claude Code · DeepSeek CCS

:: ── 工作目录 ──
cd /d "%~dp0"

echo.
echo   Claude Code + DeepSeek CCS 启动器
echo   =====================================

:: ── 1. 检查 claude ──
where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo   [X] claude 命令未找到
    echo   请先安装: npm install -g @anthropic-ai/claude-code
    pause
    exit /b 1
)

:: ── 2. 注册表读取 API Key ──
if not defined ANTHROPIC_API_KEY (
    for /f "tokens=2,*" %%a in ('reg query HKCU\Environment /v ANTHROPIC_API_KEY 2^>nul ^| findstr "REG_"') do (
        set "ANTHROPIC_API_KEY=%%b"
    )
)
if not defined ANTHROPIC_API_KEY (
    if defined DEEPSEEK_API_KEY set "ANTHROPIC_API_KEY=%DEEPSEEK_API_KEY%"
)
if not defined ANTHROPIC_API_KEY (
    for /f "tokens=2,*" %%a in ('reg query HKCU\Environment /v DEEPSEEK_API_KEY 2^>nul ^| findstr "REG_"') do (
        set "ANTHROPIC_API_KEY=%%b"
    )
)

:: ── 3. API 地址 ──
if not defined ANTHROPIC_BASE_URL (
    set "ANTHROPIC_BASE_URL=http://127.0.0.1:3000"
)

echo   API 端点: %ANTHROPIC_BASE_URL%

:: ── 4. 尝试探测并启动 CCS ──
curl -s -o nul --connect-timeout 2 "%ANTHROPIC_BASE_URL%" 2>&1
if errorlevel 1 (
    echo   [!] CCS 代理无响应，尝试启动...
    if exist "ccs\server.js" (
        start "CCS" /min cmd /c "cd /d %~dp0ccs && node server.js"
        echo   [OK] 已启动 ccs\server.js
    ) else if exist "ccs\index.js" (
        start "CCS" /min cmd /c "cd /d %~dp0ccs && node index.js"
        echo   [OK] 已启动 ccs\index.js
    ) else if exist "ccs\app.js" (
        start "CCS" /min cmd /c "cd /d %~dp0ccs && node app.js"
        echo   [OK] 已启动 ccs\app.js
    ) else (
        echo   [!] 未找到 ccs\ 目录下的入口文件
        echo   请确认 CCS 已安装到 %~dp0ccs\
    )
    echo   等待 4 秒...
    timeout /t 4 /nobreak >nul
)

:: ── 5. 检查 API key ──
if not defined ANTHROPIC_API_KEY (
    echo   [!] ANTHROPIC_API_KEY 未设置
    echo   在终端执行: setx ANTHROPIC_API_KEY "sk-你的deepseek-key"
    echo   或编辑本文件，在下面一行填入密钥:
    echo   set "ANTHROPIC_API_KEY=sk-xxx"
    echo.
)

:: ── 6. 启动 ──
set "CLAUDE_CODE_ENTRYPOINT=cli"
echo   正在启动 Claude Code...
echo.

where wt.exe >nul 2>&1
if %errorlevel% equ 0 (
    start "" wt.exe -d "%~dp0." cmd /k "claude --dangerously-skip-permissions --no-chrome"
    exit /b
)

claude --dangerously-skip-permissions --no-chrome
pause
