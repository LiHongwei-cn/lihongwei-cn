@echo off
set MATLAB_EXE=C:\Program Files\MATLAB\R2016b\bin\matlab.exe
set CARSim_EXE=C:\Program Files (x86)\CarSim2019.0_Prog\CarSim.exe
cd /d "%~dp0"

echo ============================================
echo   MATLAB AI 仿真工具包
echo ============================================
echo.

echo [1/2] 拉取最新代码...
git pull

if not exist "%MATLAB_EXE%" (
    echo [错误] 未找到 MATLAB R2016b
    echo 预期路径: %MATLAB_EXE%
    echo 请修改本脚本中的 MATLAB_EXE 变量
    pause
    exit /b 1
)

cd matlab
echo.
echo [2/3] 启动 MATLAB R2016b（自动配置路径）...
start "" "%MATLAB_EXE%" -r "addpath(pwd); startup_setup; disp(' '); disp('路径已配置。可用命令:'); disp('  vehicle_dynamics / motor_control / dc_motor_pwm'); disp('  ev_dynamics_simple / battery_soc_ekf'); disp('  driving_cycle_analysis / energy_management'); disp('  run_carsim'); disp('  test_all'); disp(' ');"

echo.
echo MATLAB 正在启动...
echo.

if exist "%CARSim_EXE%" (
    echo [3/3] 启动 CarSim 2019.0...
    start "" "%CARSim_EXE%"
    echo CarSim 已启动。
) else (
    echo [注意] 未找到 CarSim: %CARSim_EXE%
)
echo 全部可用命令:
echo   vehicle_dynamics         车辆纵向动力学
echo   motor_control            PMSM永磁同步电机FOC控制
echo   dc_motor_pwm             直流电机PWM调速
echo   ev_dynamics_simple       电动汽车完整仿真
echo   battery_soc_ekf          电池SOC估算(EKF)
echo   driving_cycle_analysis   驾驶循环能耗分析
echo   energy_management        增程式能量管理策略
echo   run_carsim               CarSim联合仿真
echo   test_all                 批量测试所有脚本
echo.
pause