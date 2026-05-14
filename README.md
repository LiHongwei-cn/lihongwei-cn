# LiHongwei 项目仓库

新能源汽车工程 · MATLAB · Python · Web

🌐 **项目入口页** → **[lihongwei-ch.github.io/matlab-tool](https://lihongwei-ch.github.io/matlab-tool/)**
📄 **操作指南** → **[guide.txt](matlab-tool/guide.txt)**

---

```
1/
├── matlab-tool/           项目入口页面 + 操作指南
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
