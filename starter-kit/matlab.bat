@echo off
cd /d %USERPROFILE%\Desktop\YOUR_REPO_NAME
echo 正在获取最新代码...
git pull
cd matlab
start matlab.exe
echo MATLAB 已启动
echo 工作目录自动设为 matlab/
echo.
echo 首次使用请在 Command Window 输入: startup_setup
echo 然后可直接运行: vehicle_dynamics
pause
