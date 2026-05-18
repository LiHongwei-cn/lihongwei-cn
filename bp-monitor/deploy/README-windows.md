# Windows 部署指南

## 方式一：交给 AI（推荐）

在 Claude Code 中进入 `bp-monitor/` 目录，说：

> 帮我部署血压监测后端

AI 会自动执行 `deploy/setup-windows.bat`，完成安装依赖 → 配置 .env → 启动服务。

## 方式二：手动部署

### 1. 安装 Python

https://www.python.org/downloads/ → 下载 3.9+ → 安装时勾选「Add Python to PATH」

### 2. 首次部署（只需一次）

双击 `deploy/setup-windows.bat`，按提示操作。

### 3. 日常启动

双击 `deploy/start.bat`。

## HTTPS 公网访问

测试用 `http://localhost:8080` 即可。生产环境需要 HTTPS：

### 方案 A：Cloudflare Tunnel（最简单，免费）

```bash
# 下载 cloudflared
# https://github.com/cloudflare/cloudflared/releases

cloudflared tunnel --url http://localhost:8080
```

会得到一个 `https://xxx.trycloudflare.com` 地址，直接填到小程序后台的 request 域名。

### 方案 B：nginx for Windows + Let's Encrypt

1. 下载 nginx Windows 版：https://nginx.org/en/download.html
2. 参考 `deploy/nginx.conf.example` 配置
3. 用 win-acme 获取免费证书：https://www.win-acme.com/

## 设置每周自动生成报告

1. 打开 `deploy/cron-report.bat`，修改 `CRON_TOKEN`
2. Win+R → `taskschd.msc`
3. 创建基本任务 → 触发器：每周一 8:00 → 操作：启动程序 → 浏览选 `deploy/cron-report.bat`

## 验证服务

```bash
# 健康检查
curl http://localhost:8080/api/health

# 应返回：{"status":"ok","db":"connected"}
```
