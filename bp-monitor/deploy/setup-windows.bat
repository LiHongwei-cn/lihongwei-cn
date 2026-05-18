@echo off
chcp 65001 >nul
cd /d "%~dp0.."

echo ========================================
echo   家庭健康记录助手 — Windows 部署
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 安装依赖
echo [1/3] 安装 Python 依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

:: 检查 .env
if not exist ".env" (
    echo [2/3] 创建 .env 配置文件...
    copy .env.example .env >nul
    echo.
    echo !!! 请编辑 backend\.env 填入真实的 Key !!!
    echo      DEEPSEEK_API_KEY=sk-你的密钥
    echo      WECHAT_APPID=wx你的AppID
    echo      WECHAT_SECRET=你的小程序密钥
    echo      CRON_SECRET_TOKEN=自己编一个随机字符串
    echo.
    start notepad .env
    echo 填写完成后按任意键继续...
    pause >nul
) else (
    echo [2/3] .env 已存在，跳过
)

:: 启动
echo [3/3] 启动 API 服务...
echo.
echo 服务地址：http://localhost:8080
echo 健康检查：http://localhost:8080/api/health
echo 按 Ctrl+C 停止服务
echo ========================================
uvicorn backend.main:app --host 0.0.0.0 --port 8080

pause
