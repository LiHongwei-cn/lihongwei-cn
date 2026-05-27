@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: MATLAB 仿真工具包一键启动器 (Windows)
:: 用法：双击 matlab.bat

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "MATLAB_DIR=%PROJECT_DIR%\matlab"
set "LAUNCHER_URL=https://lihongwei-cn.github.io/lihongwei-cn/matlab/"

echo ========================================
echo   MATLAB 仿真工具包
echo ========================================
echo.
echo 项目目录: %PROJECT_DIR%
echo MATLAB 目录: %MATLAB_DIR%
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
echo   1) 初始化环境 + 打开 MATLAB
echo   2) 批量测试所有脚本
echo   3) 打开启动器网页
echo   4) 查看可用脚本列表
echo   5) 退出
echo.
set /p "CHOICE=输入选项 [1-5]: "

if "%CHOICE%"=="1" goto :init
if "%CHOICE%"=="2" goto :test
if "%CHOICE%"=="3" goto :web
if "%CHOICE%"=="4" goto :list
if "%CHOICE%"=="5" goto :end
goto :menu

:init
echo.
echo 启动 MATLAB 并自动初始化...
start "" "%MATLAB%" -nosplash -r "cd('%MATLAB_DIR:\=\\%'); startup_setup; disp('环境就绪，输入任意脚本名运行（如 motor_control）');"
goto :end

:test
echo.
echo 运行批量测试...
start "" "%MATLAB%" -nosplash -nodesktop -r "cd('%MATLAB_DIR:\=\\%'); startup_setup; test_all"
goto :end

:web
start "" "%LAUNCHER_URL%"
echo 已打开启动器网页: %LAUNCHER_URL%
goto :end

:list
echo.
echo 可用脚本：
echo   电机控制:
echo     motor_control         PMSM FOC 矢量控制
echo     dc_motor_pwm          直流电机 PWM 调速
echo     dc_motor_simulink     直流电机 Simulink 模型
echo   车辆动力学:
echo     vehicle_dynamics      纵向动力学仿真
echo     ev_dynamics_simple    电动汽车完整仿真
echo     driving_cycle_analysis 驾驶循环能耗分析
echo     generate_cruise_model 定速巡航 Simulink 模型
echo   电池 ^& 能量:
echo     battery_soc_ekf       SOC 估算（EKF）
echo     energy_management     增程式能量管理
echo   ADAS:
echo     adas_hil_demo/main_adas_hil_demo  ADAS HIL 综合演示
echo   工具:
echo     rms_calculation       RMS 有效值
echo     fft_analysis          FFT 频谱分析
echo     lowpass_filter        低通滤波器
echo.
pause
goto :menu

:no_matlab
echo [X] 未检测到 MATLAB 安装
echo.
echo 请选择操作：
echo   1) 打开 MATLAB 启动器网页
echo   2) 手动输入 MATLAB 命令
echo   3) 退出
echo.
set /p "CHOICE_NM=输入选项 [1-3]: "

if "%CHOICE_NM%"=="1" (
    start "" "%LAUNCHER_URL%"
    echo 已打开启动器网页
)
if "%CHOICE_NM%"=="2" (
    echo.
    echo 请在 MATLAB 中依次执行：
    echo   cd('%MATLAB_DIR:\=\\%')
    echo   startup_setup
    echo   %% 然后运行任意示例脚本
)
echo.

:end
endlocal
