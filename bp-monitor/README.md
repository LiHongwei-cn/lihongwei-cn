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

**macOS / Linux：**

```bash
bash deploy/start.sh
```

**Windows：**

```bash
# 首次部署（安装依赖 + 配置 .env + 启动）
deploy\setup-windows.bat

# 日常启动
deploy\start.bat
```

> Windows 详细部署说明见 [`deploy/README-windows.md`](deploy/README-windows.md)。

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

## 项目结构

```
bp-monitor/
├── backend/
│   ├── main.py              # FastAPI 应用入口，5 组路由
│   ├── config.py            # 环境变量读取
│   ├── database.py          # SQLite 初始化 + Token 认证
│   ├── models.py            # Pydantic 数据模型
│   ├── requirements.txt     # Python 依赖
│   ├── .env.example         # 环境变量模板
│   ├── routes/              # API 路由
│   │   ├── auth.py          # 微信登录 / Token 验证
│   │   ├── users.py         # 用户信息读写
│   │   ├── readings.py      # 血压记录 CRUD + 统计 + 趋势
│   │   ├── reports.py       # 周报列表 / 生成
│   │   └── ai.py            # AI 重新分析
│   ├── services/            # 业务逻辑
│   │   ├── analyzer.py      # 读数分析（含紧急判断）
│   │   ├── report_gen.py    # 周报生成
│   │   ├── wechat.py        # 微信 code2session
│   │   ├── deepseek.py      # DeepSeek API 客户端
│   │   └── medical.py       # 血压分级 / 紧急指征
│   ├── prompts/             # AI 提示词模板
│   │   ├── system_prompt.py # 系统提示词（含完整指南知识）
│   │   ├── reading_analysis.py
│   │   └── weekly_report.py
│   └── tests/
│       ├── test_medical.py  # 血压分级 / 紧急判断测试
│       └── test_readings.py # 读数逻辑测试
├── miniprogram/             # 微信小程序前端
│   ├── app.js / app.json
│   ├── utils/api.js / auth.js
│   └── pages/ (index, record, history, report, profile)
├── deploy/                  # 部署脚本
│   ├── start.sh / start.bat
│   ├── setup-windows.bat
│   ├── cron-report.sh / cron-report.bat
│   └── nginx.conf.example
└── index.html               # GitHub Pages 项目页
```

## API 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 微信登录（code → token + user） |
| GET | `/api/auth/check` | Token 有效性检查 |
| GET | `/api/users/me` | 获取当前用户信息 |
| PUT | `/api/users/me` | 更新用户信息（年龄/性别/用药等） |
| POST | `/api/readings` | 提交血压读数（自动触发 AI 分析） |
| GET | `/api/readings` | 读数列表（分页 + 日期筛选） |
| GET | `/api/readings/stats` | 统计摘要（均值/趋势/极值） |
| GET | `/api/readings/trends` | 趋势数据（30 天日平均） |
| GET | `/api/readings/{id}` | 单条读数详情 |
| GET | `/api/reports` | 周报列表（最近 52 周） |
| GET | `/api/reports/latest` | 最新周报 |
| GET | `/api/reports/{id}` | 指定周报详情 |
| POST | `/api/reports/generate` | 生成周报（支持 all_users 批量） |
| POST | `/api/ai/analyze/{id}` | 重新分析指定读数 |
| GET | `/api/health` | 健康检查 |

所有读写接口（除 `/api/health` 和 cron 批量生成）均需 Bearer Token。

## 环境变量

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `WECHAT_APPID` | 微信小程序 AppID |
| `WECHAT_SECRET` | 微信小程序 AppSecret |
| `CRON_SECRET_TOKEN` | 定时任务鉴权 Token |

## 运行测试

```bash
cd backend
python -m pytest tests/ -v
```

## 技术栈

- 前端：微信小程序（WXML/WXSS/JS）
- 后端：Python 3.12 + FastAPI
- 数据库：SQLite（WAL 模式，4 张表：users / readings / reports / ai_feedback）
- AI：DeepSeek API（deepseek-v4-pro）
