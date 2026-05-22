@echo off
chcp 65001 >nul
title Hermes Agent

echo ⚕ Hermes Agent 启动中...
echo.

REM 检查 hermes 命令
where hermes >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%USERPROFILE%\.local\bin\hermes.cmd" (
        set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    ) else (
        echo ❌ Hermes Agent 未安装
        echo.
        echo 请在 PowerShell 中运行安装命令：
        echo   iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
        echo.
        pause
        exit /b 1
    )
)

REM 检查配置文件
if not exist "%USERPROFILE%\.hermes\.env" (
    echo ⚠ 未检测到 API Key 配置
    echo.
    echo 请先运行配置向导：
    echo   hermes setup
    echo.
    pause
    exit /b 1
)

echo ✓ Hermes Agent 已就绪
echo.

cd /d "%USERPROFILE%"
hermes chat
