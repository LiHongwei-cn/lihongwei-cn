@echo off
set MATLAB_EXE=C:\Program Files\MATLAB\R2016b\bin\matlab.exe
set CARSim_EXE=C:\Program Files (x86)\CarSim2019.0_Prog\CarSim.exe
cd /d "%~dp0"

echo ============================================
echo   MATLAB AI Simulation Toolkit
echo ============================================
echo.

echo [1/3] git pull...
git pull 2>nul
if errorlevel 1 echo       (offline, skipped)

if not exist "%MATLAB_EXE%" (
    echo [ERROR] MATLAB R2016b not found: %MATLAB_EXE%
    pause
    exit /b 1
)

cd matlab
echo [2/3] Starting MATLAB R2016b...
echo       Paths will be auto-configured.
echo.

start "" "%MATLAB_EXE%" -r "addpath('%~dp0matlab');startup_setup"

if exist "%CARSim_EXE%" (
    echo [3/3] Starting CarSim 2019.0...
    start "" "%CARSim_EXE%"
) else (
    echo [3/3] CarSim not found, skipped.
)

echo.
echo Available commands:
echo   vehicle_dynamics        motor_control
echo   dc_motor_pwm            ev_dynamics_simple
echo   battery_soc_ekf         driving_cycle_analysis
echo   energy_management       run_carsim
echo   test_all
echo.
pause
