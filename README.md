<div align="center">

# ⚡ LiHongwei

**MATLAB 仿真 · AI 工具开发**

<a href="https://lihongwei-cn.github.io/lihongwei-cn/"><img src="https://img.shields.io/badge/🌐_Website-lihongwei--cn.github.io-818cf8?style=for-the-badge&logo=vercel&logoColor=white" /></a>
<a href="https://github.com/LiHongwei-cn/lihongwei-cn/releases"><img src="https://img.shields.io/github/v/release/LiHongwei-cn/lihongwei-cn?style=for-the-badge&logo=github&color=4ade80" /></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge&color=fbbf24" /></a>

<br>
<br>

> 🔗 更多项目详情、图文教程、安装包下载，请前往 **[lihongwei-cn.github.io](https://lihongwei-cn.github.io/lihongwei-cn/)**

</div>

---

## 🚀 项目一览

<table>
<tr>
<td width="50%" valign="top">

### ⚡ MATLAB-AI 启动器
MATLAB 仿真工具包。支持用户精确参数输入，AI 自动生成兼容 R2016b 的 MATLAB 脚本和 Simulink 模型。动力学、电机控制、电池管理、能量管理策略。

[📦 下载](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/matlab-ai-starter.zip) · [📖 详情](https://lihongwei-cn.github.io/lihongwei-cn/matlab-ai/)

</td>
<td width="50%" valign="top">

### 🚗 CarSim-AI 通用仿真工具
基于 CarSim 2019.0 的 AI 仿真工具，支持各类仿真场景（高架桥爬坡、弯道操控、紧急避障等）。精确参数输入，自动生成场景和车辆配置。

[📖 详情](https://lihongwei-cn.github.io/lihongwei-cn/carsim-ai/)

</td>
</tr>
<tr>
<td width="50%" valign="top">

### ⚕️ Hermes Agent 一键启动
Nous Research 开源 AI Agent。OpenRouter / DeepSeek 多模型后端，Win / Mac 双击即用。

[🪟 Windows](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/hermes-start.bat) · [🍎 macOS](https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/hermes-desktop.command) · [📖 详情](https://lihongwei-cn.github.io/lihongwei-cn/hermes-launcher/)

</td>
<td width="50%" valign="top">

### 🟣 蒙多 · 跨界学习引擎
遇到瓶颈自动变身！多 AI + GitHub + Stack Overflow + 掘金多渠道搜索，四维对比选最佳。Claude Code / Hermes Agent 通用 Skill。

触发词：`卡住了` `搞不定` `没思路` `蒙多`

[📖 详情](https://lihongwei-cn.github.io/lihongwei-cn/skills/)

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 📖 Claude Code 安装指南
从零入门：安装、国产模型接入、CLAUDE.md 规范配置、桌面快捷方式、Telegram 机器人搭建。Mac / Windows 双平台。

[📖 详情](https://lihongwei-cn.github.io/lihongwei-cn/claude-code-tutorial/)

</td>
<td width="50%" valign="top">

### 📘 Hermes Agent 完整指南
从零安装到 Telegram 接入，DeepSeek 模型配置 + Gateway 服务，全部踩坑解决。

[📖 详情](https://lihongwei-cn.github.io/lihongwei-cn/hermes-guide/)

</td>
</tr>
</table>

---

## 📥 安装包

<table align="center">
<tr align="center">
<td><b>📦 matlab-ai-starter.zip</b><br><sub>MATLAB 仿真工具包</sub></td>
<td><b>🪟 claude-desktop.bat</b><br><sub>Claude Code · Windows</sub></td>
<td><b>🍎 Claude-Code.app.zip</b><br><sub>Claude Code · macOS</sub></td>
<td><b>🪟 hermes-start.bat</b><br><sub>Hermes Agent · Windows</sub></td>
<td><b>🍎 hermes-desktop.command</b><br><sub>Hermes Agent · macOS</sub></td>
</tr>
<tr align="center">
<td><a href="https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/matlab-ai-starter.zip">⬇ 下载</a></td>
<td><a href="https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/claude-desktop.bat">⬇ 下载</a></td>
<td><a href="https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/Claude-Code.app.zip">⬇ 下载</a></td>
<td><a href="https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/hermes-start.bat">⬇ 下载</a></td>
<td><a href="https://github.com/LiHongwei-cn/lihongwei-cn/releases/download/packages/hermes-desktop.command">⬇ 下载</a></td>
</tr>
</table>

<p align="center"><sub>全部安装包 → <a href="https://github.com/LiHongwei-cn/lihongwei-cn/releases/tag/packages">GitHub Releases</a></sub></p>

---

## 🧮 MATLAB 使用

兼容 **R2016b**+。支持用户精确参数输入，AI 自动生成代码。

```matlab
startup_setup              % 添加路径（首次运行）
vehicle_dynamics           % 纵向动力学
motor_control              % 电机 FOC 矢量控制
battery_soc_ekf            % EKF SOC 估计
energy_management          % 能量管理策略
generate_cruise_model      % 定速巡航 Simulink
run_carsim                 % 联合仿真
test_all                   % 批量测试
```

### AI 精确生成（新功能）

使用 Claude Code / ChatGPT / Hermes Agent，提供精确参数，AI 自动生成代码：

```matlab
% 示例：用户提供精确参数
% "生成一个电机 FOC 控制仿真，参数如下：
%  - 定子电阻 Rs = 0.958 Ohm
%  - d轴电感 Ld = 5.25 mH
%  - q轴电感 Lq = 5.25 mH
%  - 永磁磁链 ψ = 0.1827 Wb
%  - 极对数 P = 4
%  - 转动惯量 J = 0.003 kg.m^2
%  - 仿真时间 0.5s，步长 0.0001s
%  - 速度环 Kp=0.5, Ki=10
%  - 电流环 Kp=100, Ki=2000"

% AI 会生成兼容 R2016b 的 MATLAB 脚本，所有参数值与用户提供的一致
```

### CarSim-AI 高架桥仿真（新功能）

基于 CarSim 2019.0 的 AI 仿真工具，模拟不同驱动类型车辆在冰雪路面上的爬坡能力：

```matlab
% 示例：燕子矶高架仿真
params.bridge_length = 100;    % 高架桥长度 [m]
params.bridge_width = 8;       % 高架桥宽度 [m]
params.slope_angle = 15;       % 坡度角度 [deg]
params.friction = 0.2;         % 路面摩擦系数
params.fwd_power = 100;        % 前驱车功率 [kW]
params.awd_power = 100;        % 四驱车功率 [kW]
params.output_dir = './output';

% 运行仿真
run_bridge_simulation(params);

% 预期结果：
% - 前驱车：打滑，爬坡失败
% - 四驱车：成功爬坡，不撞护栏
```

<details>
<summary>📂 项目结构</summary>

```
├── matlab/                MATLAB 仿真代码
│   ├── examples/          仿真脚本
│   ├── carsim/            联合仿真
│   └── utils/             工具函数
├── matlab-tool/           安装包发布页面
├── matlab-ai/             MATLAB-AI 启动器页面
├── carsim-ai/             CarSim-AI 通用仿真工具
├── assignments/           作业示例
│   └── bridge-slope/      高架桥爬坡仿真
├── bot/                   Telegram 机器人
├── tools/                 启动脚本集合
├── skills/                Skills 市场（14 个 Skill）
├── global-specs/          全局规范部署包
├── hermes-launcher/       Hermes Agent 启动器
├── hermes-guide/          Hermes Agent 指南
├── desktop-launcher/      Claude Code 桌面启动
├── telegram-bot/          Telegram 机器人项目页
├── starter-kit/           通用模板
└── index.html             GitHub Pages 主页
```

</details>

<details>
<summary>💻 笔记本操作</summary>

```bash
cd Desktop
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cd lihongwei-cn

# Windows: 双击 matlab.bat
# macOS:   chmod +x matlab.sh && ./matlab.sh
git pull   # 后续更新
```

</details>

---

<p align="center">
  <sub>MIT 协议开源 · <a href="CLAUDE.md">项目规范</a> · <a href="https://github.com/LiHongwei-cn/lihongwei-cn">GitHub</a></sub>
</p>
