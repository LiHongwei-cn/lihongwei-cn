# 家庭血压监测助手

基于微信小程序 + FastAPI + DeepSeek AI 的家庭血压健康管理工具。

## 功能

- 微信一键登录，全家多人使用
- 每天多次记录血压（收缩压/舒张压/心率）
- 基于全球权威高血压指南的 AI 实时分析
- 长期数据趋势跟踪与病理画像
- 每周自动生成健康周报（用药、饮食、运动建议）
- 简洁大字体 UI，专为老年人设计

## 前置条件

1. **微信小程序 AppID** — 在 [微信公众平台](https://mp.weixin.qq.com) 注册
2. **已备案 HTTPS 域名** — 微信 API 强制要求
3. **DeepSeek API Key** — 在 [DeepSeek 开放平台](https://platform.deepseek.com) 获取
4. **服务器** — VPS / 树莓派 / 家庭服务器均可

## 快速开始

### 1. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 填入真实的 Key
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动后端

```bash
# 开发模式
uvicorn main:app --reload --port 8080

# 或使用部署脚本
bash deploy/start.sh
```

### 4. 配置 Nginx HTTPS 反向代理

```bash
# 参考 deploy/nginx.conf.example
# 修改域名后复制到 /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 5. 配置微信小程序

1. 在微信开发者工具中打开 `miniprogram/` 目录
2. 修改 `app.js` 中的 `apiBase` 为你的 HTTPS 域名
3. 修改 `project.config.json` 中的 `appid` 为你的小程序 AppID

### 6. 设置定时周报

```bash
crontab -e
# 添加：
# 0 8 * * 1 /path/to/bp-monitor/deploy/cron-report.sh
```

## 医学知识来源

- WHO/ISH《全球高血压防治指南》
- ACC/AHA《美国心脏病学会/美国心脏协会高血压指南》
- ESC/ESH《欧洲心脏病学会/欧洲高血压学会动脉高血压管理指南》
- 《中国高血压防治指南》

## 免责声明

本程序提供的所有血压分析、趋势评估和建议均由 AI 生成，仅供参考。
不构成医疗诊断或处方。请以执业医师的诊断和治疗方案为准。
如有不适，请及时就医。

## 技术栈

- 前端：微信小程序（WXML/WXSS/JS）
- 后端：Python FastAPI
- 数据库：SQLite（WAL 模式）
- AI：DeepSeek API（deepseek-v4-pro）
