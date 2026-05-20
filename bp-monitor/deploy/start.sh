#!/bin/bash
# 血压监测助手 - 生产启动脚本
set -e

cd "$(dirname "$0")/.."

# 检查环境变量
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "[错误] 请设置环境变量 DEEPSEEK_API_KEY"
    exit 1
fi
if [ -z "$CRON_SECRET_TOKEN" ]; then
    echo "[错误] 请设置环境变量 CRON_SECRET_TOKEN"
    exit 1
fi
if [ "${BP_DEV_MODE:-0}" != "1" ]; then
    if [ -z "$WECHAT_APPID" ] || [ -z "$WECHAT_SECRET" ]; then
        echo "[错误] 非开发模式需要设置 WECHAT_APPID 和 WECHAT_SECRET"
        echo "       本地测试请设置 BP_DEV_MODE=1"
        exit 1
    fi
fi

echo "[启动] 血压监测助手 API 服务..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8080 --workers 2
