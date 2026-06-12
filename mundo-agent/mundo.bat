@echo off
chcp 65001 >nul 2>&1
title MUNDO Agent v2.2.0

echo.
echo   ╔══════════════════════════════════════╗
echo   ║        MUNDO Agent v2.2.0            ║
echo   ║        Windows 启动器                ║
echo   ╚══════════════════════════════════════╝
echo.

set MUNDO_HOME=%USERPROFILE%\.hermes\mundo-agent
set VENV_DIR=%MUNDO_HOME%\venv
set SCRIPT_DIR=%~dp0

:: 检查Python是否可用
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查虚拟环境
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [信息] 首次运行，正在创建虚拟环境...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    
    echo [信息] 安装依赖...
    "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
    if exist "%MUNDO_HOME%\requirements.txt" (
        "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%MUNDO_HOME%\requirements.txt"
    )
    echo [信息] 安装完成！
    echo.
)

:: 启动MUNDO
"%VENV_DIR%\Scripts\python.exe" "%SCRIPT_DIR%mundo.py" %*

:: 如果退出码非零，暂停显示错误
if errorlevel 1 (
    echo.
    echo [错误] MUNDO异常退出，错误码: %errorlevel%
    pause
)
