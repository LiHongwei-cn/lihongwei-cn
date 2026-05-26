@echo off
cd /d "%~dp0"

echo ============================================
echo   MATLAB AI Simulation Toolkit
echo ============================================
echo.

echo [1/3] git pull...
git pull 2>nul
if errorlevel 1 echo       (offline, skipped)

echo.
echo [2/3] Auto-detecting MATLAB installation...

set MATLAB_EXE=
set MATLAB_VER=

:: Scan Program Files for MATLAB, pick newest (R2016b+)
for /f "delims=" %%d in ('dir /b /on "C:\Program Files\MATLAB\R20*" 2^>nul') do (
    if exist "C:\Program Files\MATLAB\%%d\bin\matlab.exe" (
        set MATLAB_EXE=C:\Program Files\MATLAB\%%d\bin\matlab.exe
        set MATLAB_VER=%%d
    )
)

:: Fallback: try PATH
if not defined MATLAB_EXE (
    where matlab >nul 2>nul
    if not errorlevel 1 (
        for /f "delims=" %%i in ('where matlab 2^>nul') do set MATLAB_EXE=%%i
    )
)

if not defined MATLAB_EXE (
    echo [ERROR] MATLAB not found.
    echo         Please install MATLAB R2016b or newer.
    echo         Expected: C:\Program Files\MATLAB\R20xx\bin\matlab.exe
    pause
    exit /b 1
)

echo          Found: %MATLAB_VER%  (%MATLAB_EXE%)

cd matlab
echo.
echo [3/3] Starting MATLAB...
echo       Paths auto-configured on launch.
echo.

start "" "%MATLAB_EXE%" -r "addpath('%~dp0matlab');startup_setup"

echo MATLAB is starting...
echo.
echo Available commands:
echo   vehicle_dynamics        motor_control
echo   dc_motor_pwm            ev_dynamics_simple
echo   battery_soc_ekf         driving_cycle_analysis
echo   energy_management
echo   test_all
echo.
echo.
pause
