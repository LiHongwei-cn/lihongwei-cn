@echo off
echo Running MATLAB to generate .par files...
cd /d "%~dp0"
"C:\Program Files\MATLAB\R2016b\bin\matlab.exe" -r "generate_par_files; exit"
echo.
echo Done!
pause
