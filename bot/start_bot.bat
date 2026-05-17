@echo off
cd /d "%~dp0"

if "%TELEGRAM_TOKEN%"=="" (
    echo ERROR: TELEGRAM_TOKEN 环境变量未设置
    echo 请在终端设置: setx TELEGRAM_TOKEN "你的Token"
    pause
    exit /b 1
)
if "%DEEPSEEK_API_KEY%"=="" (
    echo ERROR: DEEPSEEK_API_KEY 环境变量未设置
    echo 请在终端设置: setx DEEPSEEK_API_KEY "sk-你的Key"
    pause
    exit /b 1
)

python tgbot.py
pause
