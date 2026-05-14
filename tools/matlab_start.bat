@echo off
chcp 65001 >nul
cd /d %USERPROFILE%\Desktop\lihongwei-ch\matlab
echo MATLAB 工作目录已设为: %CD%
echo.
echo 请在 MATLAB 的 Command Window 中运行:
echo   startup_setup
echo.
start matlab.exe
