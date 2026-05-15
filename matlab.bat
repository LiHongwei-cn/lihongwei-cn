@echo off
chcp 65001 >nul
set MATLAB_EXE=C:\Program Files\MATLAB\R2016b\bin\matlab.exe
set CARSim_EXE=C:\Program Files (x86)\CarSim2019.0_Prog\CarSim.exe
cd /d "%~dp0"

echo ============================================
echo   MATLAB AI 仿真工具包
echo ============================================
echo.

echo [1/3] 拉取最新代码...
git pull 2>nul
if errorlevel 1 echo     (离线或 git 未安装，跳过)

if not exist "%MATLAB_EXE%" (
    echo [错误] 未找到 MATLAB R2016b
    echo 预期路径: %MATLAB_EXE%
    pause
    exit /b 1
)

cd matlab
echo.
echo [2/3] 启动 MATLAB R2016b...
start "" "%MATLAB_EXE%" -r "addpath(pwd);startup_setup"

echo [2/3] MATLAB 正在启动（路径自动配置）...

if exist "%CARSim_EXE%" (
    echo [3/3] 启动 CarSim 2019.0...
    start "" "%CARSim_EXE%"
) else (
    echo [3/3] CarSim 未找到，跳过
)

echo.
echo 全部可用命令:
echo   vehicle_dynamics         motor_control
echo   dc_motor_pwm             ev_dynamics_simple
echo   battery_soc_ekf          driving_cycle_analysis
echo   energy_management        run_carsim
echo   test_all
echo.
pause
