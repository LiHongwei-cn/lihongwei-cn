@echo off
REM MUNDO Agent — Windows 启动器

set MUNDO_HOME=%USERPROFILE%\.hermes\mundo-agent
set MUNDO_SCRIPT=%MUNDO_HOME%\mundo.py

if not exist "%MUNDO_HOME%\venv" (
    echo 首次运行，正在安装...
    call "%MUNDO_HOME%\install.bat"
)

call "%MUNDO_HOME%\venv\Scripts\activate.bat"

if "%1"=="-h" goto :help
if "%1"=="--help" goto :help

python "%MUNDO_SCRIPT%" %*
goto :eof

:help
echo 用法: mundo [选项]
echo.
echo   (无参数)     启动蒙多 CLI 交互模式
echo   -q TEXT      单次查询模式
echo   -h           显示帮助
echo.
goto :eof
