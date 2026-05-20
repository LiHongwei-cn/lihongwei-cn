#!/bin/bash
# 血压监测助手 - 启动脚本（macOS / Linux）
set -e

cd "$(dirname "$0")/.."

# 从 .env 文件加载环境变量（如果存在）
if [ -f "backend/.env" ]; then
    while IFS='=' read -r key value; do
        key=$(echo "$key" | xargs)
        case "$key" in
            ''|\#*) continue ;;
            *) value=$(echo "$value" | sed 's/^"//;s/"$//;s/^'"'"'//;s/'"'"'$//'); export "$key=$value" ;;
        esac
    done < backend/.env
fi

# 检查必填环境变量
if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "sk-your-deepseek-api-key" ]; then
    echo "[错误] 请在 backend/.env 中设置真实的 DEEPSEEK_API_KEY"
    exit 1
fi
if [ -z "$CRON_SECRET_TOKEN" ] || [ "$CRON_SECRET_TOKEN" = "your-cron-secret-token" ]; then
    echo "[错误] 请在 backend/.env 中设置 CRON_SECRET_TOKEN（自己编一个随机字符串）"
    exit 1
fi
if [ "${BP_DEV_MODE:-1}" != "1" ]; then
    if [ -z "$WECHAT_APPID" ] || [ "$WECHAT_APPID" = "wx-your-appid" ]; then
        echo "[错误] 非开发模式需要设置真实的 WECHAT_APPID 和 WECHAT_SECRET"
        echo "       本地测试请设置 BP_DEV_MODE=1"
        exit 1
    fi
fi

echo "[启动] 血压监测助手 API 服务..."
echo "       模式：$([ "${BP_DEV_MODE:-1}" = "1" ] && echo '开发模式（免微信登录）' || echo '生产模式')"
echo "       地址：http://localhost:8080"
echo ""
exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8080
