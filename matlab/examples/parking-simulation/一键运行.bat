@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title CarSim + Simulink 联合仿真 - 一键运行

echo.
echo  ██████╗ █████╗ ██████╗ ███████╗██╗███╗   ███╗
echo ██╔════╝██╔══██╗██╔══██╗██╔════╝██║████╗ ████║
echo ██║     ███████║██████╔╝███████╗██║██╔████╔██║
echo ██║     ██╔══██║██╔══██╗╚════██║██║██║╚██╔╝██║
echo ╚██████╗██║  ██║██║  ██║███████║██║██║ ╚═╝ ██║
echo  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝     ╚═╝
echo.
echo ============================================================
echo   CarSim + Simulink 倒车入库联合仿真
echo   基于B站教程: BV1xk4y1b7y8
echo ============================================================
echo.

cd /d "%~dp0"
echo 工作目录: %CD%
echo.

echo [步骤 1/4] 检查环境...
echo ─────────────────────────────────────────────────────────────

:: 检查MATLAB
set "MATLAB_PATH="
if exist "C:\Program Files\MATLAB\R2016b\bin\matlab.exe" (
    echo   ✓ MATLAB R2016b: 已安装
    set "MATLAB_PATH=C:\Program Files\MATLAB\R2016b\bin\matlab.exe"
) else if exist "C:\Program Files\MATLAB\R2024a\bin\matlab.exe" (
    echo   ✓ MATLAB R2024a: 已安装
    set "MATLAB_PATH=C:\Program Files\MATLAB\R2024a\bin\matlab.exe"
) else if exist "C:\Program Files\MATLAB\R2023b\bin\matlab.exe" (
    echo   ✓ MATLAB R2023b: 已安装
    set "MATLAB_PATH=C:\Program Files\MATLAB\R2023b\bin\matlab.exe"
) else if exist "C:\Program Files\MATLAB\R2021b\bin\matlab.exe" (
    echo   ✓ MATLAB R2021b: 已安装
    set "MATLAB_PATH=C:\Program Files\MATLAB\R2021b\bin\matlab.exe"
) else (
    echo   ✗ 未找到MATLAB
    echo   请安装MATLAB后重试
    pause
    exit /b 1
)

:: 检查CarSim
set "CARSIM_PATH="
if exist "C:\Program Files (x86)\CarSim2019.0_Prog\CarSim.exe" (
    echo   ✓ CarSim 2019.0: 已安装
    set "CARSIM_PATH=C:\Program Files (x86)\CarSim2019.0_Prog\CarSim.exe"
) else if exist "C:\Program Files\CarSim 2019.0\Programs\CarSim.exe" (
    echo   ✓ CarSim 2019.0: 已安装
    set "CARSIM_PATH=C:\Program Files\CarSim 2019.0\Programs\CarSim.exe"
) else (
    echo   ⚠ CarSim 2019.0: 未找到默认路径
    echo   请确保CarSim已安装
)
echo.

echo [步骤 2/4] 生成配置文件...
echo ─────────────────────────────────────────────────────────────
"!MATLAB_PATH!" -r "try, run('carsim_ap_auto_import.m'), fprintf('\n✓ 配置文件生成成功\n'), catch e, fprintf('\n✗ 错误: %s\n', e.message), end; exit"
echo.

echo [步骤 3/4] 检查生成的文件...
echo ─────────────────────────────────────────────────────────────
if exist "Parking_Reversing.cpar" (
    echo   ✓ Parking_Reversing.cpar
) else (
    echo   ✗ Parking_Reversing.cpar 未生成
)

if exist "import_to_carsim_auto.m" (
    echo   ✓ import_to_carsim_auto.m
) else (
    echo   ⚠ import_to_carsim_auto.m 未生成
)
echo.

echo [步骤 4/4] 启动CarSim...
echo ─────────────────────────────────────────────────────────────
if defined CARSIM_PATH (
    echo   正在启动CarSim...
    start "" "!CARSIM_PATH!"
    timeout /t 3 >nul
    echo   ✓ CarSim已启动
) else (
    echo   请手动启动CarSim
)
echo.

echo ============================================================
echo   配置完成！请在CarSim中完成以下操作：
echo ============================================================
echo.
echo   1. 导入配置文件:
echo      File → Import Dataset
echo      选择: %CD%\Parking_Reversing.cpar
echo.
echo   2. 导出S-Function:
echo      Settings → Simulink → Export S-Function
echo      保存到: %CD%\
echo.
echo   3. 运行仿真:
echo      方法A: Run → Run Simulation (在CarSim中)
echo      方法B: 在MATLAB中运行 run_parking_simulation
echo.
echo ============================================================
echo.
echo 按任意键打开MATLAB运行仿真...
pause >nul

:: 启动MATLAB并运行仿真
echo.
echo 正在启动MATLAB...
start "" "!MATLAB_PATH!" -desktop
timeout /t 5 >nul

echo.
echo 请在MATLAB中运行以下命令:
echo.
echo   cd '%CD%'
echo   run_parking_simulation
echo.
echo 或运行:
echo   auto_run_all
echo.
pause
