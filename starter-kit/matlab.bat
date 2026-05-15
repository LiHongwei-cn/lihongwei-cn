@echo off
set MATLAB_EXE=C:\Program Files\MATLAB\R2016b\bin\matlab.exe
cd /d "%~dp0"

echo ============================================
echo   MATLAB AI Simulation Toolkit
echo ============================================
echo.

echo [1/2] git pull...
git pull 2>nul
if errorlevel 1 echo       (offline, skipped)

if not exist "%MATLAB_EXE%" (
    echo [ERROR] MATLAB R2016b not found: %MATLAB_EXE%
    pause
    exit /b 1
)

cd matlab
echo [2/2] Starting MATLAB R2016b...
echo       Paths auto-configured on launch.
echo.

start "" "%MATLAB_EXE%" -r "addpath('%~dp0matlab');startup_setup"

echo MATLAB is starting...
echo.
echo Available commands:
echo   vehicle_dynamics        motor_control
echo   dc_motor_pwm            ev_dynamics_simple
echo   battery_soc_ekf         driving_cycle_analysis
echo   energy_management       run_carsim
echo   test_all
echo.
echo For CarSim: type run_carsim in MATLAB
echo (it will build the model and launch CarSim)
echo.
pause
