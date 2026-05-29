@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
echo ============================================================
echo   CarSim + Simulink 联合仿真 - 全自动化脚本
echo   基于B站教程: BV1xk4y1b7y8
echo ============================================================
echo.

cd /d "%~dp0"
echo [1/5] 当前工作目录: %CD%
echo.

echo [2/5] 检查MATLAB安装...
set "MATLAB_CMD="
if exist "C:\Program Files\MATLAB\R2016b\bin\matlab.exe" (
    set "MATLAB_CMD=C:\Program Files\MATLAB\R2016b\bin\matlab.exe"
    echo   ✓ MATLAB R2016b 已安装
) else if exist "C:\Program Files\MATLAB\R2024a\bin\matlab.exe" (
    set "MATLAB_CMD=C:\Program Files\MATLAB\R2024a\bin\matlab.exe"
    echo   ✓ MATLAB R2024a 已安装
) else if exist "C:\Program Files\MATLAB\R2023b\bin\matlab.exe" (
    set "MATLAB_CMD=C:\Program Files\MATLAB\R2023b\bin\matlab.exe"
    echo   ✓ MATLAB R2023b 已安装
) else (
    echo   ✗ 未找到MATLAB，请先安装
    pause
    exit /b 1
)
echo.

echo [3/5] 生成CarSim配置文件...
"!MATLAB_CMD!" -r "try, run('carsim_ap_auto_import.m'), fprintf('配置文件生成成功！\n'), catch e, fprintf('错误: %s\n', e.message), end; exit"
echo.

echo [4/5] 检查生成的文件...
if exist "Parking_Reversing.cpar" (
    echo   ✓ Parking_Reversing.cpar 已生成
) else (
    echo   ✗ CPAR文件生成失败
)
echo.

echo [5/5] 尝试自动导入到CarSim...
echo.
echo ============================================================
echo   请手动完成以下步骤：
echo ============================================================
echo.
echo   1. 打开 CarSim 2019.0
echo.
echo   2. 导入配置文件：
echo      File → Import Dataset
echo      选择: %CD%\Parking_Reversing.cpar
echo.
echo   3. 导出S-Function：
echo      Settings → Simulink → Export S-Function
echo      保存到: %CD%\
echo.
echo   4. 运行仿真：
echo      方法A: Run → Run Simulation (CarSim中)
echo      方法B: 在MATLAB中运行 run_parking_simulation.m
echo.
echo ============================================================
echo   按任意键打开CarSim安装目录...
echo ============================================================
pause >nul

:: 尝试打开CarSim
if exist "C:\Program Files\CarSim 2019.0\Programs\CarSim.exe" (
    start "" "C:\Program Files\CarSim 2019.0\Programs\CarSim.exe"
    echo   ✓ CarSim 已启动
) else if exist "C:\Program Files (x86)\CarSim 2019.0\Programs\CarSim.exe" (
    start "" "C:\Program Files (x86)\CarSim 2019.0\Programs\CarSim.exe"
    echo   ✓ CarSim 已启动
) else (
    echo   ✗ 未找到CarSim，请手动启动
    echo   默认路径: C:\Program Files\CarSim 2019.0\
)

echo.
echo 按任意键退出...
pause >nul
