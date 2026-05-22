@echo off
cd /d "%~dp0"

REM Load .env if it exists
if exist .env (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        set "%%a=%%b"
    )
)

if "%TELEGRAM_TOKEN%"=="" (
    echo ERROR: TELEGRAM_TOKEN 未设置
    echo   方式1: setx TELEGRAM_TOKEN "你的Token"
    echo   方式2: 在 bot\.env 文件中写入 TELEGRAM_TOKEN=你的Token
    pause
    exit /b 1
)
if "%DEEPSEEK_API_KEY%"=="" (
    echo ERROR: DEEPSEEK_API_KEY 未设置
    echo   方式1: setx DEEPSEEK_API_KEY "sk-你的Key"
    echo   方式2: 在 bot\.env 文件中写入 DEEPSEEK_API_KEY=sk-你的Key
    pause
    exit /b 1
)

python tgbot.py
pause
