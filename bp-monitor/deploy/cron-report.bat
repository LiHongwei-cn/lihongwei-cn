@echo off
chcp 65001 >nul
REM 每周一生成健康报告 — 用 Windows 任务计划程序触发
REM 创建任务：taskschd.msc → 创建基本任务 → 触发器：每周一 8:00 → 操作：启动程序 → 选此 bat

set "SERVER_URL=http://localhost:8080"
set "CRON_TOKEN=你的CRON_SECRET_TOKEN"

curl -s -X POST "%SERVER_URL%/api/reports/generate?all_users=true" -H "X-Cron-Token: %CRON_TOKEN%" -H "Content-Type: application/json"
echo.
echo 报告生成请求已发送
