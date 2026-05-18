# MATLAB AI 仿真代码生成工具

AI 生成 MATLAB 仿真代码 → 提交 GitHub → 笔记本上一键运行

车辆动力学、电机控制、能量管理等仿真场景。

---

## 快速开始

```bash
# 克隆到你自己的仓库
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名

# 双击 matlab.bat 启动 MATLAB
# 在 Command Window 输入:
startup_setup     # 仅首次，配置路径
vehicle_dynamics  # 运行车辆动力学仿真
```

## 目录

```
├── matlab/
│   ├── examples/          可运行示例脚本
│   │   ├── vehicle_dynamics.m      车辆纵向动力学
│   │   ├── motor_control.m         PMSM 电机 FOC 控制
│   │   └── generate_cruise_model.m 生成定速巡航 Simulink 模型
│   ├── carsim/            CarSim 联合仿真
│   │   └── sim_setup.m              联合仿真配置
│   └── utils/             工具函数
│       ├── fft_analysis.m          FFT 频谱分析
│       ├── lowpass_filter.m        一阶低通滤波
│       └── rms_calculation.m       RMS 计算
├── docs/
│   └── 操作说明.md              使用指南
├── matlab.bat              一键启动脚本
├── .gitignore
└── README.md
```

## 使用方式

### AI 生成代码

配合 Claude Code 或任意 AI 工具，用自然语言描述仿真需求，
AI 直接生成可运行的 MATLAB 脚本，保存到 `matlab/examples/`。

### 笔记本运行

1. 在笔记本上 `git pull` 获取最新代码
2. 双击 `matlab.bat` 启动 MATLAB
3. 在 Command Window 输入脚本名运行

### CarSim 联合仿真

运行 `sim_setup` 自动配置联合仿真环境。

## 兼容性

- MATLAB R2016b 及以上
- CarSim 2019.0

## 将此模板连接到你的 GitHub

先找到你的准确信息：
1. **用户名**：打开 github.com 登录 → 点右上角头像 → Signed in as 后面就是用户名
2. **仓库名**：点进你刚创建的仓库 → 浏览器地址栏 `github.com/用户名/仓库名`

例如地址栏是 `github.com/zhangsan/matlab-project`，用户名 = `zhangsan`，仓库名 = `matlab-project`。

然后在项目文件夹右键 → Git Bash Here，执行（把中文替换掉）：

```bash
git remote set-url origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

---

项目基于 [LiHongwei/matlab-ai-tool](https://github.com/LiHongwei-cn/lihongwei-cn) 模板生成。
