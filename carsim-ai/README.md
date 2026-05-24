# CarSim-AI 通用仿真工具

纯 CarSim 2019.0 仿真工具，支持用户精确参数输入，自动生成各类仿真场景的参数说明。

## 核心特性

- **纯 CarSim 仿真**：不依赖 Simulink，完全在 CarSim 内部运行
- **精确参数输入**：用户提供精确数值，生成对应的 CarSim 参数说明
- **CarSim 2019.0 兼容**：使用 CarSim 标准 GUI 操作
- **通用场景生成**：支持各类仿真场景（高架桥爬坡、弯道操控、紧急避障等）
- **车辆参数配置**：支持前驱/后驱/四驱车辆配置
- **结果分析**：提供 MATLAB 分析脚本

## 支持的仿真场景

### 1. 高架桥爬坡仿真

模拟不同驱动类型车辆在冰雪路面上的爬坡能力。

```matlab
params.scene_type = 'bridge_slope';
params.bridge_length = 100;    % 高架桥长度 [m]
params.slope_angle = 15;       % 坡度角度 [deg]
params.friction = 0.2;         % 路面摩擦系数
params.fwd_power = 100;        % 前驱车功率 [kW]
params.awd_power = 100;        % 四驱车功率 [kW]
```

### 2. 弯道操控仿真

测试车辆在不同半径弯道上的操控性能。

```matlab
params.scene_type = 'cornering';
params.curve_radius = 50;      % 弯道半径 [m]
params.curve_angle = 90;       % 弯道角度 [deg]
params.road_width = 7;         % 道路宽度 [m]
params.vehicle_speed = 60;     % 车速 [km/h]
```

### 3. 紧急避障仿真

模拟车辆紧急避障性能。

```matlab
params.scene_type = 'obstacle_avoidance';
params.obstacle_position = 50; % 障碍物位置 [m]
params.obstacle_width = 2;     % 障碍物宽度 [m]
params.lane_width = 3.5;       % 车道宽度 [m]
params.vehicle_speed = 80;     % 车速 [km/h]
```

### 4. 制动性能仿真

测试车辆在不同路面上的制动性能。

```matlab
params.scene_type = 'braking';
params.initial_speed = 100;    % 初始速度 [km/h]
params.brake_distance = 50;    % 制动距离 [m]
params.friction = 0.8;         % 路面摩擦系数
params.vehicle_mass = 1500;    % 车辆质量 [kg]
```

### 5. 加速性能仿真

测试车辆加速性能。

```matlab
params.scene_type = 'acceleration';
params.target_speed = 100;     % 目标速度 [km/h]
params.acceleration_distance = 200; % 加速距离 [m]
params.engine_power = 150;     % 发动机功率 [kW]
params.vehicle_mass = 1500;    % 车辆质量 [kg]
```

## 文件结构

```
carsim-ai/
├── examples/                    示例脚本
│   └── run_simulation.m         通用仿真主脚本
├── utils/                       工具函数
│   └── configure_vehicle.m      车辆参数配置器
├── README.md                    本文件
└── index.html                   项目网页
```

## 快速开始

### 方式一：桌面启动器（推荐）

- **macOS**：双击 `tools/carsim-ai.command`
- **Windows**：双击 `tools/carsim-ai.bat`

### 方式二：MATLAB 命令行

```matlab
% 1. 切换到 carsim-ai 目录
cd('path/to/lihongwei-cn/carsim-ai/examples')

% 2. 设置仿真参数
params.scene_type = 'bridge_slope';
params.bridge_length = 100;
params.slope_angle = 15;
params.friction = 0.2;
params.fwd_power = 100;
params.awd_power = 100;
params.output_dir = '../output';

% 3. 运行仿真（生成参数说明）
run_simulation(params);
```

### 方式三：在 CarSim 中操作

1. 运行 MATLAB 脚本生成参数说明
2. 打开 CarSim 2019.0
3. 按照生成的说明文件设置参数
4. 点击 Run 运行仿真
5. 导出结果后用 MATLAB 分析

## 工作流程

```
1. 运行 MATLAB 脚本生成参数说明
   ↓
2. 在 CarSim 中手动输入参数
   ↓
3. 在 CarSim 中点击 Run 运行仿真
   ↓
4. 导出结果后用 MATLAB 分析
```

## 参数说明

### 通用参数

| 参数 | 说明 | 单位 |
|------|------|------|
| scene_type | 场景类型 | 字符串 |
| output_dir | 输出目录 | 字符串 |

### 高架桥参数

| 参数 | 说明 | 默认值 | 单位 |
|------|------|--------|------|
| bridge_length | 高架桥长度 | 100 | m |
| slope_angle | 坡度角度 | 15 | deg |
| friction | 路面摩擦系数 | 0.2 | - |

### 车辆参数

| 参数 | 说明 | 默认值 | 单位 |
|------|------|--------|------|
| fwd_power | 前驱车功率 | 100 | kW |
| awd_power | 四驱车功率 | 100 | kW |
| rwd_power | 后驱车功率 | 100 | kW |

## 输出结果

仿真完成后，输出目录包含：

### 参数说明文件

- `carsim_instructions_FWD.txt` - 前驱车参数设置说明
- `carsim_instructions_AWD.txt` - 四驱车参数设置说明

### 分析脚本

- `analyze_results.m` - 结果分析脚本

### 仿真结果（手动导出）

- `results_FWD.csv` - 前驱车仿真结果
- `results_AWD.csv` - 四驱车仿真结果

## 依赖

- CarSim 2019.0+
- MATLAB R2016b+（仅用于生成参数和分析结果）

## 常见问题

### Q1: CarSim 打不开怎么办？

**A**: 
1. 确认 CarSim 2019.0 已正确安装
2. 检查 CarSim 许可证是否有效
3. 尝试以管理员身份运行 CarSim

### Q2: 仿真失败怎么办？

**A**: 
1. 检查参数设置是否正确
2. 确认初始条件合理
3. 查看 CarSim 的错误日志

### Q3: 如何添加新场景？

**A**: 
1. 在 `run_simulation.m` 中添加新的场景函数
2. 参考现有场景的实现
3. 生成对应的参数说明文件

## 开发规范

- 兼容性底线 R2016b
- 文件名/函数名：`snake_case`
- 数值单位标注在注释中：`[m]`、`[deg]`、`[kW]`
- 函数保持 <200 行

## 许可证

MIT License

## 链接

- [项目主页](https://lihongwei-cn.github.io/lihongwei-cn/)
- [GitHub 仓库](https://github.com/LiHongwei-cn/lihongwei-cn)
- [CarSim 官网](https://www.carsim.com/)
