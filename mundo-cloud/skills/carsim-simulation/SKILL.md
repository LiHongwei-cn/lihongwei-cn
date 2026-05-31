---
name: carsim-simulation
description: "CarSim 联合仿真开发：场景生成、车辆配置、结果分析。触发词：CarSim、carsim、联合仿真、车辆仿真、道路仿真、高架桥仿真、弯道仿真、制动仿真。兼容 CarSim 2019.0+。"
---

# CarSim 联合仿真开发

CarSim 是高精度车辆动力学仿真软件。本技能覆盖 MATLAB 脚本生成 CarSim 场景、车辆配置、仿真运行、结果可视化的完整流程。

> **扩展资源**: 本技能可与 `references/automotive-skills-guide.md` 中的汽车电子skills生态配合使用。完整的HIL测试、ECU开发、ADAS测试skills库见蒙多云仓库 `mundo-cloud/skills/automotive/`。

## 触发条件

- 用户要求 CarSim 仿真、车辆动力学仿真
- 生成道路场景、弯道、高架桥、坡道
- 配置前驱/后驱/四驱车辆
- 分析仿真结果（轨迹、速度、滑移率）

## 核心原则

1. **纯 CarSim** - 仿真完全在 CarSim GUI 内部运行，不依赖 Simulink（除非用户明确要求）
2. **手动参数输入** - CarSim 使用专有格式，不能通过自定义文本文件导入
3. **结果导出分析** - 仿真结果导出为 CSV，用 MATLAB 分析

## 工作流

```
1. 生成参数说明文件（MATLAB 脚本）
   ↓
2. 在 CarSim GUI 中手动输入参数
   ↓
3. 在 CarSim 中点击 Run 运行仿真
   ↓
4. 导出结果为 CSV 文件
   ↓
5. 用 MATLAB 分析结果（可选）
```

## CarSim 文件格式

**重要**：CarSim 使用专有二进制格式，不能通过自定义文本文件（.par, .road, .tir）导入。

### 正确做法：生成参数说明文件

```matlab
% 正确：生成人类可读的参数说明
fprintf(fid, '【道路设置】\n');
fprintf(fid, '  Road > Road Model = 3D Road\n');
fprintf(fid, '  Road > Friction = %.2f\n', params.friction);
fprintf(fid, '  Road > Width = 8.0 m\n');
```

用户在 CarSim GUI 中按照说明手动输入参数。

### 错误做法：生成自定义文件格式

```matlab
% 错误：CarSim 不认识这些自定义格式
fprintf(fid, 'ROAD_FILE\n');
fprintf(fid, '  FILENAME = bridge_road.road\n');
fprintf(fid, 'END_ROAD_FILE\n');
```

## 场景生成模式

### 1. 高架桥爬坡 (bridge_slope)

```matlab
% 参数
params.bridge_length = 100;    % 长度 [m]
params.bridge_width = 8;       % 宽度 [m]
params.slope_angle = 15;       % 坡度 [deg]
params.friction = 0.2;         % 摩擦系数
params.guardrail_height = 0.8; % 护栏高度 [m]

% 坡度计算
slope_rad = params.slope_angle * pi / 180;
height_gain = params.bridge_length * tan(slope_rad);
```

### 2. 弯道操控 (cornering)

```matlab
params.curve_radius = 50;      % 弯道半径 [m]
params.curve_angle = 90;       % 弯道角度 [deg]
params.road_width = 7;         % 道路宽度 [m]
```

### 3. 紧急避障 (obstacle_avoidance)

```matlab
params.obstacle_position = 50; % 障碍物位置 [m]
params.obstacle_width = 2;     % 障碍物宽度 [m]
params.lane_width = 3.5;       % 车道宽度 [m]
```

### 4. 制动性能 (braking)

```matlab
params.initial_speed = 100;    % 初始速度 [km/h]
params.brake_distance = 50;    % 制动距离 [m]
params.friction = 0.8;         % 路面摩擦系数
```

## 车辆配置模式

### 驱动类型

| 类型 | 代码 | 前轴载荷 | 后轴载荷 | 适用场景 |
|------|------|----------|----------|----------|
| 前驱 | FWD | 60% | 40% | 城市道路，爬坡一般 |
| 后驱 | RWD | 45% | 55% | 操控性好，爬坡一般 |
| 四驱 | AWD | 50% | 50% | 恶劣路况，爬坡强 |

### 参数计算

```matlab
% 最大扭矩 = 功率(kW) * 1000 / (最大转速(rpm) * pi/30)
max_torque = engine_power * 1000 / (max_rpm * pi / 30);

% 横摆转动惯量 = 质量 * 轴距^2 / 12
Iz = mass * wheelbase^2 / 12;
```

## 仿真运行模式

### 纯 CarSim 运行（推荐）

1. 在 CarSim GUI 中设置参数
2. 点击 Run Control > Run
3. 等待仿真完成
4. 导出结果：Export > CSV

### MATLAB 辅助分析

```matlab
% 读取 CarSim 导出的 CSV 文件
data = csvread('results.csv', 1, 0);  % 跳过标题行
time = data(:, 1);
x = data(:, 2);
z = data(:, 3);
vx = data(:, 4);

% 绘图分析
figure;
subplot(2, 2, 1); plot(x, z); title('轨迹'); grid on;
subplot(2, 2, 2); plot(time, vx); title('速度'); grid on;
subplot(2, 2, 3); plot(time, z); title('高度'); grid on;
```

## 结果分析

### 输出变量

| 变量 | 说明 | 单位 |
|------|------|------|
| TIME | 时间 | s |
| X, Y, Z | 位置 | m |
| VX, VY, VZ | 速度 | m/s |
| YAW | 横摆角 | deg |
| WHEEL_SLIP_* | 车轮滑移率 | - |
| ENGINE_TORQUE | 发动机扭矩 | Nm |

### 可视化

```matlab
% 轨迹图（俯视图）
plot(results.x, results.y);

% 高度剖面（侧视图）
plot(results.x, results.z);

% 速度变化
plot(results.time, results.vx);

% 滑移率
plot(results.time, results.wheel_slip);
```

## R2016b 兼容性

**禁止使用的函数：**
- `rms` → `sqrt(mean(x.^2))`
- `arguments` 块 → `nargin` 检查
- `string` 类型 → `char` 类型
- `tiledlayout` / `nexttile` → `subplot`

**纯 CarSim 项目不使用 Simulink API。** MATLAB 仅用于生成参数说明文件和分析 CSV 结果。

## 模板文件

- `references/configure_vehicle_template.m` — 车辆参数配置器模板（前驱/后驱/四驱）
- `references/bridge_scenario_template.m` — 高架桥场景生成器模板（道路+摩擦+护栏）
- `references/carsim-errors.md` — 常见错误及解决方案

复制后修改参数即可使用。

## 项目结构模式

### 通用工具 + 作业分离

当用户需要一个具体仿真实例（如燕子矶高架）作为作业，同时保留通用工具时：

```
carsim-ai/                    通用工具
├── examples/
│   └── run_simulation.m      通用主脚本（支持多种场景）
├── utils/
│   ├── generate_scenario.m   通用场景生成器
│   ├── configure_vehicle.m   车辆配置器
│   └── visualize_results.m   结果可视化
└── README.md

assignments/                  作业/独立示例
└── bridge-slope/             可直接复制到其他电脑
    ├── examples/
    │   └── run_bridge_simulation.m
    ├── utils/                从通用工具复制
    └── README.md             独立使用说明
```

**关键：** 作业目录必须包含完整代码和 README，用户复制整个目录即可在其他电脑运行。

### 桌面启动器

CarSim-AI 工具需要像 MATLAB-AI 一样的启动器：

- `tools/carsim-ai.command` (macOS)
- `tools/carsim-ai.bat` (Windows)

启动器菜单应包含：
1. 打开 MATLAB + 设置环境
2. 一键运行特定场景（如高架桥爬坡）
3. 打开通用仿真工具
4. 打开项目网页
5. 查看可用场景列表

详见 `references/carsim-launcher-template.md`

## Pitfalls

- **CarSim 不接受自定义文本文件** - 不能通过 .par/.road/.tir 文件导入参数，必须在 GUI 中手动输入
- CarSim 仅支持 Windows，macOS 需虚拟机或远程桌面
- 道路文件中 Z 坐标必须随坡度连续变化，不能跳变
- 轮胎摩擦系数低于 0.1 会导致仿真不稳定
- 四驱系统需要额外的中央差速器参数
- 仿真结果必须手动导出为 CSV，不能自动保存
- 作业目录没有独立 README → 用户无法提取使用
- 重构为通用工具后忘记删除旧的具体示例代码 → 目录冗余
- **不要引入 Simulink 依赖** - 除非用户明确要求联合仿真，否则保持纯 CarSim
