@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo =========================================
echo   GitHub Trending 每日热点爬虫
echo =========================================

:: 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 未找到 python，请先安装 Python 3
    pause
    exit /b 1
)

:: 检查依赖
python -c "import requests" >nul 2>nul
if %errorlevel% neq 0 (
    echo 📦 安装依赖...
    pip install -r requirements.txt
)

:: 检查 API Key
if "%DEEPSEEK_API_KEY%"=="" (
    echo ⚠ 未设置 DEEPSEEK_API_KEY 环境变量
    echo   英文区描述将保持原文（不翻译）
    echo   设置方式: set DEEPSEEK_API_KEY=你的密钥
    echo.
)

echo.
python crawl.py

echo.
echo ✅ 完成！报告文件: %cd%\index.html
pause
