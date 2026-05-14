# LiHongwei 项目仓库

新能源汽车工程 · MATLAB · Python · Web

---

<div align="center">

# ⬇️ 立即下载安装包

**MATLAB AI 仿真工具包** — AI 生成代码 → Git 同步 → 任何电脑上一键运行

[📦 下载安装包（ZIP）](matlab-tool/matlab-ai-starter.zip) ｜ [📖 查看操作说明](matlab-tool/guide.txt) ｜ [🌐 项目详情页](https://lihongwei-ch.github.io/matlab-tool/)

*ZIP 压缩包 · 11 KB · 包含 16 个文件 · 免费开源*

---

</div>

```
1/
├── matlab-tool/           项目入口页面 + 安装包下载
├── vpn-guide/             免费 VPN 自建指南（零度解说教程）
├── starter-kit/           通用安装包源码（开源模板）
├── vote/                  米塔投票应用（网页）
├── bot/                   Telegram 机器人（DeepSeek 驱动）
├── tools/                 工具脚本（自动保存、启动脚本等）
├── matlab/                MATLAB/Simulink 仿真代码 (R2016b)
│   ├── examples/          可运行示例脚本
│   ├── carsim/            CarSim 联合仿真配置
│   └── utils/             工具函数
├── docs/                  论文、实验报告、文档
├── index.html             个人主页（GitHub Pages）
│
├── .claude/               Claude Code 配置
├── .gitignore
└── README.md
```

## MATLAB 使用

所有代码兼容 **MATLAB R2016b** + CarSim 2019.0。

启动后运行 `startup_setup.m` 添加路径，然后直接运行：
- `vehicle_dynamics` — 车辆纵向动力学仿真
- `motor_control` — PMSM 电机 FOC 控制仿真
- `generate_cruise_model` — 生成定速巡航 Simulink 模型

## 通用安装包（Starter Kit）

任何人都可以免费下载使用此工具：

1. 下载 [matlab-ai-starter.zip](matlab-tool/matlab-ai-starter.zip)
2. 创建自己的 GitHub 仓库
3. 解压后将远程仓库改为你自己的地址
4. 在笔记本上 `git clone` 你的仓库 → 双击 `matlab.bat` → 运行

完整操作指南见 [项目页面](https://lihongwei-ch.github.io/matlab-tool/)。

## 笔记本操作流程

```bash
# 1. 首次拉取代码
cd Desktop
git clone https://github.com/LiHongwei-ch/lihongwei-ch.git

# 2. 后续更新
cd lihongwei-ch
git pull
```

用完删除整个文件夹即可。
