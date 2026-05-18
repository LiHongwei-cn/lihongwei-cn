@echo off
chcp 65001 >nul
cd /d "%~dp0.."

echo ========================================
echo   启动后端 + HTTPS 隧道
echo ========================================
echo.

echo [启动] API 服务 (localhost:8080)...
start "bp-backend" cmd /c "uvicorn backend.main:app --host 0.0.0.0 --port 8080"

echo [启动] HTTPS 隧道 (localhost.run)...
echo 隧道地址会显示在下方，复制 https://xxx.lhr.life 使用
echo.
ssh -o StrictHostKeyChecking=no -R 80:localhost:8080 nokey@localhost.run

pause
