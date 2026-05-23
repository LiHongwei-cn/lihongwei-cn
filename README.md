# LiHongwei 项目仓库

MATLAB 仿真 · AI 工具开发

---

<div align="center">

# ⬇️ 立即下载安装包

**MATLAB-AI 启动器** — 新能源汽车仿真工具包。车辆动力学、PMSM 电机 FOC、电池 SOC 估算、能量管理策略。AI 辅助生成代码，一键运行。

[📦 下载安装包（ZIP）](matlab-tool/matlab-ai-starter.zip) ｜ [📖 查看操作说明](matlab-tool/guide.txt) ｜ [🌐 项目详情页](https://lihongwei-cn.github.io/lihongwei-cn/matlab-ai/)

*ZIP 压缩包 · 11 KB · 包含 16 个文件 · 免费开源*

---

</div>

```
1/
├── matlab-tool/           项目入口页面 + 安装包下载
├── vpn-guide/             免费 VPN 自建指南
├── starter-kit/           通用安装包源码（开源模板）
├── bot/                   Telegram 机器人（DeepSeek 直接回复）
├── tools/                 工具脚本（Claude Code.app 启动器、自动保存）
├── matlab/                MATLAB/Simulink 仿真代码 (R2016b)
│   ├── examples/          可运行示例脚本
│   ├── carsim/            CarSim 联合仿真模型
│   └── utils/             工具函数
├── docs/                  论文、实验报告、文档
├── hermes-launcher/        Hermes Agent 一键启动器
├── hermes-guide/           Hermes Agent 完整指南
├── mundo/                  蒙多跨界学习引擎
├── index.html             个人主页（GitHub Pages）
│
├── .claude/               Claude Code 配置
├── .gitignore
└── README.md
```

## MATLAB 使用

所有代码兼容 **MATLAB R2016b**。CarSim 联合仿真由用户自行操作。

启动后运行 `startup_setup.m` 添加路径，然后直接运行：
- `vehicle_dynamics` — 车辆纵向动力学仿真
- `motor_control` — PMSM 电机 FOC 控制仿真
- `generate_cruise_model` — 生成定速巡航 Simulink 模型
- `build_carsim_model` — 生成 CarSim 联合仿真模型（用户自行在 CarSim 中加载）

## 通用安装包（Starter Kit）

任何人都可以免费下载使用此工具：

1. 下载 [matlab-ai-starter.zip](matlab-tool/matlab-ai-starter.zip)
2. 创建自己的 GitHub 仓库
3. 解压后将远程仓库改为你自己的地址
4. 在笔记本上 `git clone` 你的仓库 → 双击 `matlab.bat` → 运行

完整操作指南见 [项目页面](https://lihongwei-cn.github.io/matlab-tool/)。

## 免费 VPN 自建指南

基于 Cloudflare 免费套餐自建 VPN 的完整教程。

两种方法 + 全平台客户端配置：
- **方法 A**：Cloudflare Zero Trust + WARP + MASQUE 协议（推荐新手，全程无需梯子）
- **方法 B**：Cloudflare Pages + edgetunnel（进阶，配合 Clash 分流使用）
- **客户端**：Windows / Mac / Android / iOS 全平台详细配置

🔗 [查看完整教程](https://lihongwei-cn.github.io/vpn-guide/)

## Hermes Agent 一键启动器

Nous Research 开源 AI Agent，Win / Mac 双击即用。支持 OpenRouter / OpenAI / Anthropic / DeepSeek 等多模型后端。

- **Windows**：[下载 hermes-start.bat](https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/tools/hermes-start.bat)
- **macOS**：[下载 hermes-desktop.command](https://raw.githubusercontent.com/LiHongwei-cn/lihongwei-cn/main/tools/hermes-desktop.command)

🔗 [Hermes 启动器项目页面](https://lihongwei-cn.github.io/lihongwei-cn/hermes-launcher/) ｜ [README](hermes-launcher/README.md)

## 蒙多 · 跨界学习引擎

遇到瓶颈自动变身的 AI Skill。多 AI 模型 + GitHub + Stack Overflow + 掘金多渠道并行搜索，四维对比选最佳方案。

- 触发关键词：卡住了 / 搞不定 / 没思路 / 蒙多
- Claude Code / Hermes Agent 通用 Skill

🔗 [蒙多项目页面](https://lihongwei-cn.github.io/lihongwei-cn/mundo/) ｜ [README](mundo/README.md)

## 项目规范

本仓库使用 [CLAUDE.md](CLAUDE.md) 定义代码规范和 AI 行为准则。所有 MATLAB 代码兼容 R2016b，Python 代码从环境变量读取密钥，Git 提交遵循 conventional commits 格式。

## 笔记本操作流程

```bash
# 1. 首次拉取代码
cd Desktop
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git

# 2. 后续更新
cd lihongwei-cn
git pull
```

用完删除整个文件夹即可。
