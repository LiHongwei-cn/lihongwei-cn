@echo off
cd /d "%~dp0.."

rem Check for required env vars
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

rem Optional proxy - uncomment and set port if needed
rem set HTTPS_PROXY=http://127.0.0.1:7897

start /min python tools/autosave.py
start /min python bot/tgbot.py
