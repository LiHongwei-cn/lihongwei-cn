@echo off
cd /d "%~dp0"
echo 正在获取最新代码...
git pull
cd matlab
start matlab.exe
echo MATLAB R2016b 已启动
echo 工作目录自动设为 matlab/
echo.
echo 首次使用: startup_setup（配路径）
echo 可用命令: vehicle_dynamics / motor_control / run_carsim
