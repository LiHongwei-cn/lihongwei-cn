@echo off
chcp 65001 >nul
cd /d "%~dp0.."

echo 启动血压监测 API 服务...
echo 地址：http://localhost:8080
echo 按 Ctrl+C 停止
echo.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080
pause
