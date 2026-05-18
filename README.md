# LiHongwei 项目仓库

MATLAB 仿真 · AI 工具开发

---

<div align="center">

# ⬇️ 立即下载安装包

**MATLAB AI 仿真工具包** — Claude Code 直接生成 Simulink 模型和仿真代码。车辆动力学、电机控制、定速巡航仿真。

[📦 下载安装包（ZIP）](matlab-tool/matlab-ai-starter.zip) ｜ [📖 查看操作说明](matlab-tool/guide.txt) ｜ [🌐 项目详情页](https://lihongwei-cn.github.io/matlab-tool/)

*ZIP 压缩包 · 11 KB · 包含 16 个文件 · 免费开源*

---

</div>

```
1/
├── matlab-tool/           项目入口页面 + 安装包下载
├── vpn-guide/             免费 VPN 自建指南（零度解说教程）
├── starter-kit/           通用安装包源码（开源模板）
├── bot/                   Telegram 机器人（DeepSeek 直接回复）
├── tools/                 工具脚本（自动保存、启动脚本等）
├── matlab/                MATLAB/Simulink 仿真代码 (R2016b)
│   ├── examples/          可运行示例脚本
│   ├── carsim/            CarSim 联合仿真模型
│   └── utils/             工具函数
├── docs/                  论文、实验报告、文档
├── win-optimize/           Windows 优化工具教程（WinUtil + WinHance）
├── claude-code-tutorial/   Claude Code 小白教程（安装+模型+Telegram bot）
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

基于 Cloudflare 免费套餐自建 VPN 的完整教程，参考 YouTube 博主 **零度解说** 的 2026 年教程整理。

两种方法 + 全平台客户端配置：
- **方法 A**：Cloudflare Zero Trust + WARP + MASQUE 协议（推荐新手，全程无需梯子）
- **方法 B**：Cloudflare Pages + edgetunnel（进阶，配合 Clash 分流使用）
- **客户端**：Windows / Mac / Android / iOS 全平台详细配置

🔗 [查看完整教程](https://lihongwei-cn.github.io/vpn-guide/)

## Windows 系统优化教程

一行命令启动 WinUtil（Chris Titus Windows Utility），完成系统优化、更新控制、故障修复、制作纯净系统安装盘。

- **WinUtil**：PowerShell 输入 `irm "https://christitus.com/win" | iex` 即可启动
- **WinHance**：零度解说推荐的图形化优化工具，纯界面操作

涵盖系统瘦身、隐私保护、更新控制、WSL/Hyper-V 一键启用、MicroWin 纯净 ISO 制作 + Ventoy 启动盘。

🔗 [查看完整教程](https://lihongwei-cn.github.io/win-optimize/)

## Claude Code 从零入门教程

Claude Code 的完整入门教程。Mac / Windows 双平台，有魔法没魔法都有对应方案。

- **安装 Claude Code**：Mac（官方命令 / Homebrew）+ Windows（官方命令 / WinGet）
- **接入国产模型**：DeepSeek API 直连，不需要 Claude 账号、不需要魔法
- **CLAUDE.md 规范**：全局 + 项目级约束体系配置
- **桌面快捷方式**：Windows 双击启动脚本
- **Telegram 机器人**：DeepSeek 驱动的 AI 机器人完整搭建

🔗 [查看完整教程](https://lihongwei-cn.github.io/claude-code-tutorial/)

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
