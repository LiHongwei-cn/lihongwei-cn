# MATLAB 仿真工具包

MATLAB R2016b 兼容。支持用户精确参数输入，AI 自动生成 MATLAB/Simulink 代码。

## 核心特性

- **精确参数输入**：用户提供精确数值，AI 严格按照参数生成代码
- **R2016b 兼容**：禁止使用 2017+ 函数，确保最大兼容性
- **Simulink 自动生成**：根据用户参数自动生成 .slx 模型文件
- **向量化优先**：能用向量化操作的不用循环
- **前向欧拉法**：数值积分使用显式欧拉法

## 目录

```
matlab/
├── examples/               示例脚本（可直接运行）
│   ├── vehicle_dynamics.m           纵向动力学（加速-匀速-制动）
│   ├── motor_control.m              FOC 矢量控制仿真
│   ├── dc_motor_pwm.m               直流电机 PWM 调速（PI 闭环）
│   ├── dc_motor_simulink.m          直流电机 Simulink 模型自动搭建
│   ├── ev_dynamics_simple.m         整车动力学仿真（含能耗、SOC、续航）
│   ├── battery_soc_ekf.m            电池 SOC 估算（安时积分 vs EKF）
│   ├── driving_cycle_analysis.m     驾驶循环能耗分析（类 WLTC）
│   ├── energy_management.m          能量管理策略（恒温器 vs 功率跟随）
│   └── generate_cruise_model.m      定速巡航 Simulink 模型自动生成
├── carsim/                 联合仿真
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

### 方式二：AI 精确生成（新功能）

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

### 方式三：命令行

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

### 方式四：桌面快捷启动

- **macOS**：双击 `tools/matlab-ai.command`
- **Windows**：双击 `tools/matlab-ai.bat`

## AI 生成代码规范

### 参数精确性原则

1. **绝不修改用户参数值** - 即使参数可能导致仿真不稳定，也应按原值生成代码，同时给出警告
2. **单位标注清晰** - 每个参数都标注单位（如 `[Ohm]`、`[H]`、`[Wb]`）
3. **参数验证** - 生成代码后验证参数的物理合理性

### R2016b 兼容性

**禁止使用的函数：**
- `rms` → 使用 `sqrt(mean(x.^2))`
- `arguments` 块 → 使用 `nargin` 检查
- `string` 类型 → 使用 `char` 类型
- `tiledlayout` / `nexttile` → 使用 `subplot`
- `readtable` / `writetable` → 使用 `csvread` / `csvwrite`
- `datetime` → 使用 `datenum` / `datestr`

**禁止使用的语法：**
- 隐式展开（R2016b+ 支持，但为兼容性避免）
- `arguments` 验证块
- 嵌套函数中的 `end` 关键字（某些情况）

### Simulink 模型生成

**必须使用的 API：**
- `new_system` / `open_system` / `save_system`
- `add_block` / `add_line`
- `set_param` / `get_param`
- `bdIsLoaded` / `close_system`

**禁止使用的 API：**
- `Simulink.ModelAdvisor` (R2018a+)
- `sltest.testmanager` (R2017a+)
- `Simulink.sdi` 某些方法 (R2017a+)

## 常用仿真类型

### 1. 纵向动力学

```matlab
% 用户提供参数
param.m   = 1500;      % 整车质量 [kg]
param.Cd  = 0.32;      % 风阻系数
param.Af  = 2.2;       % 迎风面积 [m^2]
param.rho = 1.225;     % 空气密度 [kg/m^3]
param.f   = 0.015;     % 滚动阻力系数
param.g   = 9.81;      % 重力加速度 [m/s^2]

% AI 生成代码，严格使用用户提供的数值
```

### 2. 电机 FOC 控制

```matlab
% 用户提供参数
pmsm.Rs  = 0.958;      % 定子电阻 [Ohm]
pmsm.Ld  = 0.00525;    % d轴电感 [H]
pmsm.Lq  = 0.00525;    % q轴电感 [H]
pmsm.psi = 0.1827;     % 永磁磁链 [Wb]
pmsm.P   = 4;          % 极对数
pmsm.J   = 0.003;      % 转动惯量 [kg.m^2]

% PI 参数
Kp_i = 100;            % 电流环比例增益
Ki_i = 2000;           % 电流环积分增益
Kp_s = 0.5;            % 速度环比例增益
Ki_s = 10;             % 速度环积分增益
```

### 3. 电池 SOC 估算

```matlab
% 用户提供参数
battery.Vnom  = 3.7;   % 标称电压 [V]
battery.Qnom  = 50;    % 标称容量 [Ah]
battery.R0    = 0.01;  % 欧姆内阻 [Ohm]
battery.R1    = 0.015; % 极化内阻 [Ohm]
battery.C1    = 2000;  % 极化电容 [F]

% EKF 参数
ekf.Q = 1e-6;          % 过程噪声协方差
ekf.R = 1e-4;          % 测量噪声协方差
ekf.P0 = 0.01;         % 初始状态协方差
```

### 4. 能量管理策略

```matlab
% 用户提供参数
param.m = 2000;        % 整车质量 [kg]
param.P_motor = 120;   % 驱动电机功率 [kW]
param.P_rex = 60;      % 增程器功率 [kW]
param.Q_batt = 40;     % 电池容量 [Ah]
param.V_batt = 350;    % 电池电压 [V]

% 策略参数
SOC_min = 0.25;        % SOC 下限
SOC_max = 0.85;        % SOC 上限
P_rex_on = 0.3;        % 增程器开启阈值
P_rex_off = 0.7;       % 增程器关闭阈值
```

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
- **参数精确性**：用户提供的每个数值都必须精确使用，不允许 AI 自行假设或修改
