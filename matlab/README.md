# MATLAB 仿真工具包

MATLAB R2016b 兼容。新能源汽车工程：车辆动力学 + 电机控制 + 电池管理 + Simulink/CarSim 联合仿真。

## 目录

```
matlab/
├── examples/               示例脚本（可直接运行）
│   ├── vehicle_dynamics.m           车辆纵向动力学（加速-匀速-制动）
│   ├── motor_control.m              PMSM FOC 矢量控制仿真
│   ├── dc_motor_pwm.m               直流电机 PWM 调速（PI 闭环）
│   ├── dc_motor_simulink.m          直流电机 Simulink 模型自动搭建
│   ├── ev_dynamics_simple.m         电动汽车完整仿真（含能耗、SOC、续航）
│   ├── battery_soc_ekf.m            电池 SOC 估算（安时积分 vs EKF）
│   ├── driving_cycle_analysis.m     驾驶循环能耗分析（类 WLTC）
│   ├── energy_management.m          增程式能量管理（恒温器 vs 功率跟随）
│   └── generate_cruise_model.m      定速巡航 Simulink 模型自动生成
├── carsim/                 CarSim-Simulink 联合仿真
│   ├── sim_setup.m                  环境配置（自动检测 CarSim）
│   ├── build_carsim_model.m         搭建联合仿真模型
│   ├── run_carsim_cruise.m          一键定速巡航仿真
│   └── carsim_cruise_ctrl.slx       Simulink 模型文件
├── utils/                  工具函数
│   ├── rms_calculation.m            RMS 有效值（R2016b 兼容）
│   ├── fft_analysis.m               FFT 频谱分析
│   ├── lowpass_filter.m             一阶低通滤波器
│   └── find_carsim.m                CarSim 自动检测（Win/Mac）
├── startup_setup.m          路径初始化（首次运行）
├── run_carsim.m             一键启动 CarSim 联合仿真
├── test_all.m               批量自测
└── README.md                本文件
```

## 快速开始

### 方式一：MATLAB-AI 启动器（推荐）

打开 `matlab-ai/index.html`，可视化选择仿真脚本，一键启动。

### 方式二：命令行

```matlab
% 1. 切换到 matlab 目录
cd('path/to/lihongwei-cn/matlab')

% 2. 初始化路径（仅首次）
startup_setup

% 3. 运行任意示例
vehicle_dynamics
motor_control
battery_soc_ekf
energy_management

% 4. 批量测试
test_all
```

### 方式三：桌面快捷启动

- **macOS**：双击 `tools/matlab-ai.command`
- **Windows**：双击 `tools/matlab-ai.bat`

## 依赖

- MATLAB R2016b+（含 Simulink）
- CarSim 2019.0（仅 `carsim/` 需要）

## 开发规范

- 兼容性底线 R2016b：不使用 `rms()`、`arguments` 等新版函数
- 文件名/函数名：`snake_case`
- 数值单位标注在注释中：`[Ohm]`、`[rpm]`、`[Nm]`
- 前向欧拉法显式迭代，不依赖隐式求解器
- Simulink 模型生成前检查 `bdIsLoaded` 防止重复
- 函数保持 <200 行
