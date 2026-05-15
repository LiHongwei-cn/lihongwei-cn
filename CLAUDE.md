# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## 项目概览

新能源汽车工程专业 MATLAB 仿真工具包。AI 生成代码 → Git 同步 → 任何电脑一键运行。

## 技术栈

- **MATLAB/Simulink** R2016b 兼容（车辆动力学、电机控制、FOC、能量管理）
- **CarSim** 2019.0 联合仿真
- **Python** 3.12（Telegram 机器人、自动化脚本）
- **HTML/CSS**（GitHub Pages 静态页面）
- **Shell/Batch**（启动脚本、Git 自动化）

## 目录架构

```
1/
├── matlab/                MATLAB 仿真代码（R2016b 兼容）
│   ├── examples/          可运行示例脚本
│   ├── carsim/            CarSim-Simulink 联合仿真
│   └── utils/             工具函数（FFT、滤波、RMS）
├── bot/                   Telegram 机器人
├── matlab-tool/           安装包发布页面
├── starter-kit/           通用模板（开源）
├── tools/                 自动化脚本
├── docs/                  论文、实验报告
├── vpn-guide/             VPN 教程页面
├── win-optimize/          Windows 优化教程
├── claude-code-tutorial/  Claude Code 入门教程
├── tasks/                 机器人任务队列
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
- tasks/ 目录下的任务文件正常提交

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
# 启动 Telegram 机器人
python bot/tgbot.py

# 发送任务完成通知
python bot/notify.py "任务描述"

# 启动自动保存
python tools/autosave.py

# MATLAB（通过启动脚本）
matlab.bat
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
