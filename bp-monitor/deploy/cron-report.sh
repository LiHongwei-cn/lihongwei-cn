#!/bin/bash
# 每周一 8:00 为所有用户生成上周健康报告
# crontab: 0 8 * * 1 /path/to/bp-monitor/deploy/cron-report.sh
set -e

SERVER_URL="${SERVER_URL:-https://your-domain.com}"
CRON_TOKEN="${CRON_SECRET_TOKEN}"

curl -s -X POST "$SERVER_URL/api/reports/generate?all_users=true" \
    -H "X-Cron-Token: $CRON_TOKEN" \
    -H "Content-Type: application/json" \
    -o /dev/null -w "Report generation: %{http_code}\n"
