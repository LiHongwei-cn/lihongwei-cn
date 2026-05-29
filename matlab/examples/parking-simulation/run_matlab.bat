@echo off
echo ========================================
echo   CarSim CPAR 生成工具
echo ========================================
echo.

cd /d "%~dp0"
echo 当前目录: %CD%

echo.
echo 正在运行MATLAB...
"C:\Program Files\MATLAB\R2016b\bin\matlab.exe" -r "run('carsim_generate_cpar.m'); exit"

echo.
echo 运行完成！
pause
