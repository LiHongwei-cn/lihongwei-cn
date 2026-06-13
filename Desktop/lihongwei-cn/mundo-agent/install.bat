@echo off
REM MUNDO Agent — Windows 安装脚本

set MUNDO_HOME=%USERPROFILE%\.hermes\mundo-agent

echo.
echo   MUNDO Agent 安装程序
echo.

REM 检查 Python
set PYTHON_CMD=
for %%c in (python3.12 python3.11 python3.10 python3 python) do (
    where %%c >nul 2>&1 && (
        set PYTHON_CMD=%%c
        goto :found_python
    )
)
echo 错误: 需要 Python 3.10+
echo   winget install Python.Python.3.12
exit /b 1

:found_python
echo 使用 %PYTHON_CMD%

REM 创建虚拟环境
if not exist "%MUNDO_HOME%\venv" (
    echo 创建虚拟环境...
    %PYTHON_CMD% -m venv "%MUNDO_HOME%\venv"
)

REM 安装依赖
echo 安装依赖...
call "%MUNDO_HOME%\venv\Scripts\pip.exe" install --quiet requests beautifulsoup4 prompt_toolkit rich
echo 依赖就绪

echo.
echo 安装完成！
echo 启动: mundo.bat
echo.
