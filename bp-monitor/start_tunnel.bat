@echo off
echo Starting BP Monitor tunnel daemon...
cd /d "%~dp0"
python tunnel_daemon.py
pause
