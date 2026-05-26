# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Skill 自动调用（红线）

所有已安装 Skill 自动识别匹配，绝不手动输入 `/skill-name`：

- **论文/实验报告/学术写作** → 自动调用 `nature-writing` + `nature-polishing`
- **画图/做图/Figure/配图** → 自动调用 `nature-figure`
- **引用/参考文献/CNS引用** → 自动调用 `nature-citation`
- **数据声明/FAIR/数据仓库** → 自动调用 `nature-data`
- **审稿回复/Reviewer** → 自动调用 `nature-response`
- **PPT/组会/答辩/幻灯片** → 自动调用 `nature-paper2ppt`
- **论文翻译/文献精读** → 自动调用 `nature-reader`
- **查文献/搜索论文** → 自动调用 `nature-academic-search`
- **卡住/报错/没思路** → 自动调用 `蒙多`
- **写完代码** → 自动调用 `code-tidy`
- **阶段结束/收尾** → 自动调用 `neat-freak`
- **新增项目页面** → 自动调用 `homepage-layout`

## 关键信息

- GitHub 仓库：`https://github.com/LiHongwei-cn/lihongwei-cn`
- 网站地址：`https://lihongwei-cn.github.io/lihongwei-cn/`
- Telegram Bot：`bot/tgbot.py`（Token/Key 从环境变量读取，启动脚本 `bot/start_bot.sh`）

## 项目概览

MATLAB 仿真工具包 + 家庭血压监测微信小程序。Claude Code 直接生成 Simulink 模型和仿真代码。

## 技术栈

- **MATLAB/Simulink** R2016b 兼容（动力学、电机控制、能量管理）
- **Python** 3.12 + FastAPI（Telegram 机器人、血压监测后端、自动化脚本）
- **HTML/CSS**（GitHub Pages 静态页面）
- **微信小程序**（WXML/WXSS/JS，bp-monitor 前端）
- **Shell/Batch**（启动脚本、Git 自动化）

## 目录架构

```
1/
├── matlab/                MATLAB 仿真代码（R2016b 兼容）
│   ├── examples/          可运行示例脚本
│   └── utils/             工具函数（FFT、滤波、RMS）
├── bot/                   Telegram 机器人（DeepSeek 直接回复）
├── matlab-tool/           安装包发布页面
├── starter-kit/           通用模板（开源）
├── bp-monitor/            家庭血压监测小程序（FastAPI + SQLite + DeepSeek）
├── tools/                 自动化脚本
├── docs/                  论文、实验报告
├── vpn-guide/             VPN 教程页面
├── win-optimize/          Windows 优化教程
├── claude-code-tutorial/  Claude Code 入门教程
├── index.html             GitHub Pages 主页
└── CLAUDE.md              项目规范（本文件）
```

## MATLAB 规范

- 兼容性底线：**R2016b**（不使用 2017+ 的函数，如 `rms`）
- 文件命名：`snake_case.m`
- 函数命名：`snake_case`
- 每个脚本开头注释说明用途和兼容版本
- 仿真参数集中声明，使用有意义的常量名
- 禁止 `eval`、`feval` 等动态执行
- 前向欧拉法写清楚注释，不使用隐式求解器
- Simulink 模型生成脚本需检查 `bdIsLoaded` 防止重复
- 数值单位在注释中标注（如 `[Ohm]`, `[rad/s]`, `[rpm]`）

## Python 规范

- `scripts/` 使用独立的虚拟环境
- 密钥从环境变量读取，严禁硬编码
- 错误处理：捕获具体异常，不裸露 `except`
- 日志优先于 `print`

## Git 规范

- commit message: `<type>: <description>`（feat, fix, refactor, docs, chore）
- 先 diff 再 commit，不提交 `.env`、密钥、`__pycache__`
- 每次代码修改后自动 push 到 GitHub

## 代码质量

- MATLAB 函数保持 <200 行
- Python 函数保持 <50 行
- 复用优先：utils/ 里的函数不要在各 example 里重写
- 参数验证：公共函数入口检查参数合法性

## 安全红线

- **绝不硬编码密钥**（API Key、Token、密码）
- 所有密钥从环境变量读取
- `.env` 不提交到 Git
- 已泄露的密钥立即在对应平台撤销并重新生成
- 外部输入（用户消息、API 响应）在显示/执行前验证

## 常用命令

```bash
# 启动 Telegram 机器人（直接回复，不走任务队列）
python bot/tgbot.py

# 发送通知
python bot/notify.py "任务描述"

# 启动自动保存
python tools/autosave.py

# MATLAB（通过启动脚本）
matlab.bat

# bp-monitor 后端启动
cd bp-monitor && bash deploy/start.sh        # macOS/Linux
cd bp-monitor && deploy\setup-windows.bat     # Windows 首次部署
cd bp-monitor && deploy\start.bat            # Windows 日常启动

# bp-monitor 测试
cd bp-monitor/backend && python -m pytest tests/ -v
```

## 页面开发

子目录页面的视觉风格保持一致：
- 深色主题，CSS 变量 `:root`
- 卡片式的链接导航
- sans-serif 字体栈（含中文回退）
- 响应式 `max-width` 布局
- 不引入外部 CSS/JS 框架，纯手写

## 任务拆分原则

- 复杂任务拆分为独立子任务
- 每个子任务产出单一文件
- 独立任务可并行执行
- 不提前设计用不到的功能

## 跨平台要求（红线）

- 所有工具、脚本、教程必须同时覆盖 Windows 和 macOS
- 新增脚本时同时提供 .bat/.ps1（Win）和 .sh/.command（Mac）
- 教程页面必须包含两种系统的操作步骤

## 开源同步（红线）

- 网址内所有项目及内容必须在 GitHub 仓库中可找到，供所有人阅读、下载、使用
- 完全免费开源，每次改动后自动同步到 GitHub
- 网址内容与仓库代码保持一一对应，不允许网址有但仓库没有的内容

## 任务收尾（红线）

每次代码修改后：
1. `git add` + `git commit` + `git push` 同步到 GitHub
2. 检查 `bot/` 目录是否需要同步更新（系统提示词、启动脚本等）
3. 确认 GitHub Pages 网址内容与代码一致

## 全局规范同步（红线）

每次修改全局规范文件（`~/.claude/CLAUDE.md`、`rules/`、`skills/`、`settings.json`）后，必须自动同步到 `global-specs/`：
- `~/.claude/CLAUDE.md` → `global-specs/CLAUDE.md`
- `~/.claude/rules/*.md` → `global-specs/rules/*.md`
- 新增/修改的 skills → `global-specs/skills/`
- 配置变更 → `global-specs/settings.json` / `settings.local.json`
- 更新 `global-specs/README.md` 中受影响的说明

## 全站校验（红线）

每次新增项目页面后：
1. 逐一验证所有页面的内部链接、外部链接、安装包下载链接
2. 确保工具在 Windows 和 macOS 上均可运行
3. 发现 404、空内容、链接错误、平台兼容问题时自行搜索并修复

**增量校验原则**：已校验通过且未改动过的页面、链接、安装包，不重复校验。只校验新增或修改过的部分。

## Scrapling 爬虫（红线）

所有网页抓取任务**必须使用 Scrapling**，禁止裸写 requests/BeautifulSoup。

```bash
pip install "scrapling[all]" && scrapling install
```

快速用法：

```python
from scrapling.fetchers import Fetcher, StealthyFetcher

# 普通页面
page = Fetcher.get('https://example.com')
data = page.css('.item::text').getall()

# 受保护页面（Cloudflare）
page = StealthyFetcher.fetch('https://example.com', headless=True)
```

详见全局规范 `~/.claude/CLAUDE.md` 中 Scrapling 章节。
