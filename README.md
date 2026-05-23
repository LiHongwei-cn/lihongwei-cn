# ⚡ LiHongwei

<p align="center">
  <strong>新能源汽车工程 · MATLAB 仿真 · AI 工具开发</strong>
</p>

<p align="center">
  <a href="https://github.com/LiHongwei-cn/lihongwei-cn/releases"><img src="https://img.shields.io/github/v/release/LiHongwei-cn/lihongwei-cn?include_prereleases&style=for-the-badge" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
</p>

---

[📦 安装包下载](https://github.com/LiHongwei-cn/lihongwei-cn/releases/tag/packages) · [🌐 项目主页](https://lihongwei-cn.github.io/lihongwei-cn/) · [📖 MATLAB 使用](https://lihongwei-cn.github.io/lihongwei-cn/matlab-ai/) · [🧩 Skills 市场](https://lihongwei-cn.github.io/lihongwei-cn/skills/)

---

## Highlights

**[MATLAB-AI 启动器](https://lihongwei-cn.github.io/lihongwei-cn/matlab-ai/)**
新能源汽车仿真工具包。车辆动力学、PMSM 电机 FOC、电池 SOC 估算、能量管理策略。AI 辅助生成代码，一键运行。
→ [下载 matlab-ai-starter.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/matlab-ai-starter.zip)

**[Claude Code 桌面快捷启动](https://lihongwei-cn.github.io/lihongwei-cn/desktop-launcher/)**
Win / Mac 一键创建 Claude Code 桌面快捷方式，双击即开即用，无需每次打开终端输命令。
→ [Windows .bat](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/claude-desktop.bat) · [macOS .app.zip](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/Claude-Code.app.zip)

**[Hermes Agent 一键启动器](https://lihongwei-cn.github.io/lihongwei-cn/hermes-launcher/)**
Nous Research 开源 AI Agent，支持 OpenRouter / OpenAI / Anthropic / DeepSeek 等多模型后端。Win / Mac 双击即用。
→ [Windows .bat](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/hermes-start.bat) · [macOS .command](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/hermes-desktop.command)

**[蒙多 · 跨界学习引擎](https://lihongwei-cn.github.io/lihongwei-cn/skills/)**
遇到瓶颈自动变身的 AI Skill。多 AI 模型 + GitHub + Stack Overflow + 掘金多渠道并行搜索，四维对比选最佳方案。Claude Code / Hermes Agent 通用。
触发词：卡住了 / 搞不定 / 没思路 / 蒙多

**[全局规范部署包](https://lihongwei-cn.github.io/lihongwei-cn/global-specs/)**
Claude Code 全套配置（CLAUDE.md + rules + skills），新电脑一条命令部署。

**[Hermes Agent 完整指南](https://lihongwei-cn.github.io/lihongwei-cn/hermes-guide/)**
从零安装到 Telegram 接入，所有踩坑解决。DeepSeek 模型配置 + Gateway 服务。

**[Telegram AI 机器人](https://lihongwei-cn.github.io/lihongwei-cn/telegram-bot/)**
DeepSeek 驱动的 Telegram 机器人，文字 + 图片回复，一键部署。

## 安装包

所有安装包统一在 [GitHub Releases](https://github.com/LiHongwei-cn/lihongwei-cn/releases/tag/packages)：

| 文件 | 说明 | 平台 |
|------|------|------|
| `matlab-ai-starter.zip` | MATLAB 仿真工具包 | Win / Mac |
| `claude-desktop.bat` | Claude Code 桌面启动脚本 | Windows |
| `Claude-Code.app.zip` | Claude Code 桌面启动器 | macOS |
| `hermes-start.bat` | Hermes Agent 一键启动 | Windows |
| `hermes-desktop.command` | Hermes Agent 一键启动 | macOS |

## MATLAB 使用

兼容 **MATLAB R2016b**。CarSim 联合仿真由用户自行操作。

```matlab
startup_setup    % 添加路径（首次运行）
vehicle_dynamics         % 车辆纵向动力学
motor_control            % PMSM FOC 矢量控制
battery_soc_ekf          % EKF SOC 估计
energy_management        % 增程式能量管理
generate_cruise_model    % 定速巡航 Simulink
run_carsim               % CarSim 联合仿真
test_all                 % 批量测试
```

## 笔记本操作

```bash
cd Desktop
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cd lihongwei-cn

# Windows: 双击 matlab.bat
# macOS:   chmod +x matlab.sh && ./matlab.sh

# 后续更新
git pull
```

## 项目结构

```
├── matlab/                MATLAB 仿真代码 (R2016b)
│   ├── examples/          仿真脚本
│   ├── carsim/            CarSim 联合仿真
│   └── utils/             工具函数
├── matlab-tool/           安装包发布页面
├── matlab-ai/             MATLAB-AI 启动器页面
├── bot/                   Telegram 机器人
├── tools/                 启动脚本集合
├── skills/                Skills 市场（含蒙多等 14 个 Skill）
├── global-specs/          全局规范部署包
├── hermes-launcher/       Hermes Agent 启动器
├── hermes-guide/          Hermes Agent 指南
├── desktop-launcher/      Claude Code 桌面启动
├── telegram-bot/          Telegram 机器人项目页
├── starter-kit/           通用模板
└── index.html             GitHub Pages 主页
```

## 项目规范

本仓库使用 [CLAUDE.md](CLAUDE.md) 定义代码规范和 AI 行为准则。所有 MATLAB 代码兼容 R2016b，Python 代码从环境变量读取密钥，Git 提交遵循 conventional commits 格式。MIT 协议开源。
