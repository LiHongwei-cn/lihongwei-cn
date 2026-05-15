@echo off
set MATLAB_EXE=C:\Program Files\MATLAB\R2016b\bin\matlab.exe
cd /d "%~dp0"
echo 正在获取最新代码...
git pull
if not exist "%MATLAB_EXE%" (
    echo [错误] 未找到 MATLAB R2016b
    echo 请修改本脚本中的 MATLAB_EXE 变量指向正确路径
    pause
    exit /b 1
)
cd matlab
start "" "%MATLAB_EXE%"
echo MATLAB R2016b 已启动
echo 工作目录自动设为 matlab/
echo.
echo 首次使用: startup_setup
echo 可用命令: vehicle_dynamics / motor_control / run_carsim
