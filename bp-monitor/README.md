# 家庭血压监测助手

基于微信小程序 + 微信云开发 + DeepSeek AI 的家庭血压健康管理工具。

## 功能

- 微信一键登录，全家多人使用
- 每天多次记录血压（收缩压/舒张压/心率）
- 基于全球权威高血压指南的 AI 实时分析
- 长期数据趋势跟踪与病理画像
- 每周自动生成健康周报（用药、饮食、运动建议）
- 简洁大字体 UI，专为老年人设计

## 前置条件

1. **微信小程序 AppID** — 在 [微信公众平台](https://mp.weixin.qq.com) 注册
2. **开通微信云开发** — 在微信开发者工具中开通云开发环境
3. **DeepSeek API Key** — 在 [DeepSeek 开放平台](https://platform.deepseek.com) 获取

## 快速开始

### 1. 开通云开发

在微信开发者工具中打开本项目（打开 `bp-monitor/` 目录）：

1. 点击工具栏「云开发」按钮
2. 开通云开发环境，创建环境（建议命名 `prod`）
3. 在「设置 → 环境设置」中复制环境 ID

### 2. 配置环境 ID

修改 `miniprogram/app.js` 中的 `wx.cloud.init` 环境 ID：

```js
wx.cloud.init({
  env: '你的环境ID',
  traceUser: true
});
```

### 3. 创建数据库集合

在云开发控制台 → 数据库中创建以下集合：

| 集合名 | 说明 |
|--------|------|
| `users` | 用户信息 |
| `readings` | 血压记录 |
| `reports` | 周报 |
| `ai_feedback` | AI 分析日志 |

所有集合权限设置为「仅创建者可读写」。

### 4. 部署云函数

在微信开发者工具中，右键点击 `cloudfunctions/api` 目录 →「上传并部署：云端安装依赖」。

部署前在云函数配置中添加环境变量：
- `DEEPSEEK_API_KEY`：DeepSeek API 密钥

### 5. 设置定时周报

在云开发控制台 → 云函数 → 触发器，为 `api` 云函数添加定时触发器：

- 触发周期：每周一早 8:00
- Cron 表达式：`0 0 8 * * 1`

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
├── project.config.json      # 微信项目配置（miniprogramRoot + cloudfunctionRoot）
├── miniprogram/             # 微信小程序前端
│   ├── app.js / app.json   # 入口（含云开发初始化）
│   ├── utils/
│   │   ├── cloud.js         # 云函数调用封装
│   │   └── auth.js          # 登录/退出
│   ├── pages/
│   │   ├── index/           # 首页（最新读数 + 统计）
│   │   ├── record/          # 记录血压
│   │   ├── history/         # 历史记录
│   │   ├── report/          # 周报
│   │   └── profile/         # 健康档案
│   └── components/
│       ├── bp-card/         # 血压卡片
│       └── disclaimer/      # 免责声明
├── cloudfunctions/
│   └── api/                 # 云函数（登录、CRUD、AI 分析、周报生成）
│       ├── index.js         # 主入口（路由分发）
│       └── package.json     # 依赖（openai）
├── backend/                 # [已弃用] 旧 FastAPI 后端（保留参考）
│   ├── routes/
│   ├── services/
│   └── prompts/
├── deploy/                  # 部署脚本
└── index.html               # GitHub Pages 项目页
```

## API 说明

云函数通过 `action` 参数路由：

| action | 说明 |
|--------|------|
| `login` | 微信云开发登录（自动获取 openid） |
| `getUserProfile` | 获取用户健康档案 |
| `updateUserProfile` | 更新用户健康档案 |
| `addReading` | 提交血压读数（自动触发 AI 分析） |
| `getReadings` | 读数列表（分页 + 日期筛选） |
| `getStats` | 统计摘要（均值/趋势） |
| `generateReport` | 生成周报 |
| `getReports` | 周报列表 |

所有操作均由云开发自动鉴权（基于微信 openid）。

## 技术栈

- 前端：微信小程序（WXML/WXSS/JS）
- 后端：微信云开发（云函数 + 云数据库）
- 数据库：云数据库（NoSQL，4 个集合：users / readings / reports / ai_feedback）
- AI：DeepSeek API（deepseek-v4-pro）
