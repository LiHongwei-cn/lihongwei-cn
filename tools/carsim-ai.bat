@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: CarSim-AI 一键启动器 (Windows)
:: 用法：双击 carsim-ai.bat

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "CARSIM_AI_DIR=%PROJECT_DIR%\carsim-ai"
set "LAUNCHER_URL=https://lihongwei-cn.github.io/lihongwei-cn/carsim-ai/"

echo ========================================
echo   CarSim-AI 通用仿真工具
echo   CarSim 2019.0 兼容
echo ========================================
echo.
echo 项目目录: %PROJECT_DIR%
echo CarSim-AI 目录: %CARSIM_AI_DIR%
echo.

:: 检测 MATLAB 安装
set "MATLAB="
for %%v in (R2024b R2023b R2022b R2021b R2020b R2019b R2018b R2017b R2016b) do (
    if exist "C:\Program Files\MATLAB\%%v\bin\matlab.exe" (
        set "MATLAB=C:\Program Files\MATLAB\%%v\bin\matlab.exe"
        goto :found
    )
)
for %%v in (R2024b R2023b R2022b R2021b R2020b R2019b R2018b R2017b R2016b) do (
    if exist "C:\Program Files (x86)\MATLAB\%%v\bin\matlab.exe" (
        set "MATLAB=C:\Program Files (x86)\MATLAB\%%v\bin\matlab.exe"
        goto :found
    )
)
goto :no_matlab

:found
echo [OK] MATLAB: %MATLAB%
echo.

:menu
echo 请选择启动模式：
echo   1) 打开 MATLAB + 设置 CarSim-AI 环境
echo   2) 运行高架桥爬坡仿真（作业示例）
echo   3) 运行通用仿真工具
echo   4) 打开项目网页
echo   5) 查看可用仿真场景
echo   6) 退出
echo.
set /p "CHOICE=输入选项 [1-6]: "

if "%CHOICE%"=="1" goto :init
if "%CHOICE%"=="2" goto :bridge
if "%CHOICE%"=="3" goto :general
if "%CHOICE%"=="4" goto :web
if "%CHOICE%"=="5" goto :list
if "%CHOICE%"=="6" goto :end
goto :menu

:init
echo.
echo 启动 MATLAB 并设置 CarSim-AI 环境...
start "" "%MATLAB%" -nosplash -r "cd('%CARSIM_AI_DIR:\\=\\%\\examples'); disp('CarSim-AI 环境就绪'); disp('可用场景: bridge_slope, cornering, obstacle_avoidance, braking, acceleration'); disp('使用方法: run_simulation(params)');"
goto :end

:bridge
echo.
echo 运行高架桥爬坡仿真...
start "" "%MATLAB%" -nosplash -r "cd('%CARSIM_AI_DIR:\\=\\%\\examples'); params.scene_type='bridge_slope'; params.bridge_length=100; params.bridge_width=8; params.slope_angle=15; params.friction=0.2; params.fwd_power=100; params.awd_power=100; params.output_dir='../output'; run_simulation(params);"
goto :end

:general
echo.
echo 启动通用仿真工具...
start "" "%MATLAB%" -nosplash -r "cd('%CARSIM_AI_DIR:\\=\\%\\examples'); disp('CarSim-AI 通用仿真工具'); disp('请设置参数后调用 run_simulation(params)'); disp('示例:'); disp('  params.scene_type = ''bridge_slope'';'); disp('  params.bridge_length = 100;'); disp('  run_simulation(params);');"
goto :end

:web
start "" "%LAUNCHER_URL%"
echo 已打开项目网页: %LAUNCHER_URL%
goto :end

:list
echo.
echo 可用仿真场景：
echo   bridge_slope          高架桥爬坡仿真
echo     参数: bridge_length, bridge_width, slope_angle, friction
echo     车辆: fwd_power, rwd_power, awd_power
echo.
echo   cornering             弯道操控仿真
echo     参数: curve_radius, curve_angle, road_width, vehicle_speed
echo.
echo   obstacle_avoidance    紧急避障仿真
echo     参数: obstacle_position, obstacle_width, lane_width, vehicle_speed
echo.
echo   braking               制动性能仿真
echo     参数: initial_speed, brake_distance, friction, vehicle_mass
echo.
echo   acceleration          加速性能仿真
echo     参数: target_speed, acceleration_distance, engine_power, vehicle_mass
echo.
echo 使用方法：
echo   params.scene_type = '场景名称';
echo   params.参数名 = 值;
echo   run_simulation(params);
echo.
pause
goto :menu

:no_matlab
echo [X] 未检测到 MATLAB 安装
echo.
echo 请选择操作：
echo   1) 打开 CarSim-AI 项目网页
echo   2) 手动输入 MATLAB 命令
echo   3) 退出
echo.
set /p "CHOICE_NM=输入选项 [1-3]: "

if "%CHOICE_NM%"=="1" (
    start "" "%LAUNCHER_URL%"
    echo 已打开项目网页
)
if "%CHOICE_NM%"=="2" (
    echo.
    echo 请在 MATLAB 中依次执行：
    echo   cd('%CARSIM_AI_DIR:\\=\\%\\examples')
    echo   %% 设置参数
    echo   params.scene_type = 'bridge_slope';
    echo   params.bridge_length = 100;
    echo   params.output_dir = '../output';
    echo   %% 运行仿真
    echo   run_simulation(params);
)
echo.

:end
endlocal
