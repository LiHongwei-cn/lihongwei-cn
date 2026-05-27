@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: {{PROJECT_NAME}} 一键启动器 (Windows)
:: 用法：双击 .bat 文件

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "LAUNCHER_URL={{LAUNCHER_URL}}"

echo ========================================
echo   {{PROJECT_TITLE}}
echo ========================================
echo.

:: 检测应用安装
set "APP="
{{APP_DETECTION_BLOCK}}

if "%APP%"=="" goto :no_app

echo [OK] {{APP_NAME}}: %APP%
echo.

:menu
echo 请选择：
echo   1) {{MENU_OPTION_1}}
echo   2) {{MENU_OPTION_2}}
echo   3) {{MENU_OPTION_3}}
echo   4) 查看帮助
echo   5) 退出
set /p "CHOICE=选项 [1-5]: "

if "%CHOICE%"=="1" goto :action1
if "%CHOICE%"=="2" goto :action2
if "%CHOICE%"=="3" goto :action3
if "%CHOICE%"=="4" goto :help
if "%CHOICE%"=="5" goto :end
goto :menu

:action1
{{ACTION_1}}
goto :end

:action2
{{ACTION_2}}
goto :end

:action3
{{ACTION_3}}
goto :end

:help
echo {{HELP_TEXT}}
pause
goto :menu

:no_app
echo [X] 未检测到 {{APP_NAME}} 安装
echo.
echo   1) 打开启动器网页
echo   2) 手动操作说明
echo   3) 退出
set /p "CHOICE_NM=选项 [1-3]: "
if "%CHOICE_NM%"=="1" start "" "%LAUNCHER_URL%"
if "%CHOICE_NM%"=="2" echo {{MANUAL_INSTRUCTIONS}}

:end
endlocal
