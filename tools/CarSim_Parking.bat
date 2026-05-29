@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   CarSim + Simulink Parking Simulation
echo   Based on Bilibili Tutorial: BV1xk4y1b7y8
echo ============================================================
echo.

cd /d "%~dp0"
echo Working Directory: %CD%
echo.

REM === Step 1: Find MATLAB ===
echo [Step 1/4] Checking MATLAB...
set "MATLAB_CMD="
where matlab >nul 2>&1
if !errorlevel! equ 0 (
    set "MATLAB_CMD=matlab"
    echo   - MATLAB found in PATH
    goto :found_matlab
)

if exist "C:\Program Files\MATLAB\R2016b\bin\matlab.exe" (
    set "MATLAB_CMD=C:\Program Files\MATLAB\R2016b\bin\matlab.exe"
    echo   - MATLAB R2016b found at default path
    goto :found_matlab
)

if exist "C:\Program Files\MATLAB\R2024a\bin\matlab.exe" (
    set "MATLAB_CMD=C:\Program Files\MATLAB\R2024a\bin\matlab.exe"
    echo   - MATLAB R2024a found
    goto :found_matlab
)

if exist "C:\Program Files\MATLAB\R2023b\bin\matlab.exe" (
    set "MATLAB_CMD=C:\Program Files\MATLAB\R2023b\bin\matlab.exe"
    echo   - MATLAB R2023b found
    goto :found_matlab
)

echo   - ERROR: MATLAB not found!
echo   - Please install MATLAB or add it to PATH
pause
exit /b 1

:found_matlab
echo.

REM === Step 2: Run MATLAB script ===
echo [Step 2/4] Generating CarSim configuration files...
set "SCRIPT_DIR=C:/Users/HP/Desktop/lihongwei-cn/matlab/examples/parking-simulation"
set "MATLAB_CMD_STR=cd('%SCRIPT_DIR%'); try, carsim_ap_auto_import, fprintf('Success!\n'), catch e, fprintf('Error: %s\n', e.message), end"

echo   - Running: carsim_ap_auto_import
"!MATLAB_CMD!" -r "%MATLAB_CMD_STR%; exit"
echo.

REM === Step 3: Verify output ===
echo [Step 3/4] Verifying output files...
set "CPAR_FILE=C:\Users\HP\Desktop\lihongwei-cn\matlab\examples\parking-simulation\Parking_Reversing.cpar"
set "PAR_FILE=C:\Users\HP\Desktop\lihongwei-cn\matlab\examples\parking-simulation\Parking_Reversing.par"

if exist "%CPAR_FILE%" (
    echo   - CPAR file generated: Parking_Reversing.cpar
) else if exist "%PAR_FILE%" (
    echo   - PAR file generated: Parking_Reversing.par
) else (
    echo   - WARNING: No configuration file found!
    echo   - Check MATLAB output for errors
    pause
    exit /b 1
)
echo.

REM === Step 4: Open CarSim ===
echo [Step 4/4] Opening CarSim...
set "CARSIM_EXE=C:\Program Files (x86)\CarSim2019.0_Prog\CarSim.exe"

if exist "!CARSIM_EXE!" (
    start "" "!CARSIM_EXE!"
    echo   - CarSim 2019.0 started successfully
) else (
    echo   - CarSim not found at: !CARSIM_EXE!
    echo   - Please open CarSim manually
)
echo.

echo ============================================================
echo   ALL DONE! Next steps:
echo ============================================================
echo.
echo   1. In CarSim: File ^> Import Dataset
echo      Select: %CPAR_FILE%
echo.
echo   2. In CarSim: Settings ^> Simulink ^> Export S-Function
echo      Save to: C:\Users\HP\Desktop\lihongwei-cn\matlab\examples\parking-simulation\
echo.
echo   3. In MATLAB: run parking_simulation
echo      cd 'C:\Users\HP\Desktop\lihongwei-cn\matlab\examples\parking-simulation'
echo      run_parking_simulation
echo.
echo ============================================================
pause
