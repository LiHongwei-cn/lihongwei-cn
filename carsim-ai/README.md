# CarSim-AI 通用仿真工具

基于 CarSim 2019.0 的 AI 仿真工具，支持用户精确参数输入，自动生成各类仿真场景。

## 核心特性

- **精确参数输入**：用户提供精确数值，AI 严格按参数生成代码
- **CarSim 2019.0 兼容**：使用 CarSim 标准 API 和文件格式
- **通用场景生成**：支持各类仿真场景（高架桥、弯道、紧急避障等）
- **车辆参数配置**：支持前驱/后驱/四驱车辆配置
- **结果可视化**：自动生成仿真结果图表

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
│   ├── generate_scenario.m      通用场景生成器
│   ├── configure_vehicle.m      车辆参数配置器
│   ├── visualize_results.m      结果可视化
│   └── scenarios/               场景模板
│       ├── bridge_slope.m       高架桥爬坡
│       ├── cornering.m          弯道操控
│       ├── obstacle_avoidance.m 紧急避障
│       ├── braking.m            制动性能
│       └── acceleration.m       加速性能
├── templates/                   模板文件
│   └── simulation_template.par  CarSim 仿真模板
├── docs/                        文档
│   └── user_guide.md            用户指南
├── README.md                    本文件
└── index.html                   项目网页
```

## 快速开始

### 方式一：桌面启动器（推荐）

- **macOS**：双击 `tools/carsim-ai.command`
- **Windows**：双击 `tools/carsim-ai.bat`

启动器功能：
- 自动检测 MATLAB 安装
- 一键运行高架桥爬坡仿真（作业示例）
- 打开通用仿真工具
- 查看可用仿真场景列表

### 方式二：MATLAB 命令行

```matlab
% 1. 切换到 carsim-ai 目录
cd('path/to/lihongwei-cn/carsim-ai/examples')

% 2. 设置仿真参数
params.scene_type = 'bridge_slope';
params.bridge_length = 100;
params.bridge_width = 8;
params.slope_angle = 15;
params.friction = 0.2;
params.fwd_power = 100;
params.awd_power = 100;
params.output_dir = '../output';

% 3. 运行仿真
run_simulation(params);
```

### 方式二：桌面快捷启动

- **macOS**：双击 `tools/carsim-ai.command`
- **Windows**：双击 `tools/carsim-ai.bat`

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
| bridge_width | 高架桥宽度 | 8 | m |
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

### 场景文件

- `*.road` - 道路定义
- `*.tir` - 路面摩擦定义
- `*.par` - 场景参数

### 车辆文件

- `vehicle_*.par` - 车辆配置

### 仿真文件

- `simulation_*.par` - 仿真配置
- `run_batch.bat` - 批处理脚本

### 结果文件

- `results_*.csv` - 仿真结果
- `simulation_results.png` - 可视化结果

## 添加新场景

### 1. 创建场景模板

在 `utils/scenarios/` 目录下创建新的场景文件：

```matlab
function params = my_custom_scenario(params)
    % my_custom_scenario 自定义场景参数
    %
    % 输入：params - 用户参数
    % 输出：params - 完整参数（包含默认值）

    % 设置默认值
    if ~isfield(params, 'my_param')
        params.my_param = 100;  % 默认值
    end

    % 验证参数
    assert(params.my_param > 0, '参数必须为正数');
end
```

### 2. 注册场景

在 `utils/generate_scenario.m` 中添加新场景：

```matlab
case 'my_custom'
    params = my_custom_scenario(params);
```

### 3. 使用新场景

```matlab
params.scene_type = 'my_custom';
params.my_param = 150;
run_simulation(params);
```

## 依赖

- MATLAB R2016b+
- CarSim 2019.0+
- Simulink（可选，用于联合仿真）

## 常见问题

### Q1: CarSim 版本兼容性

**A**: 本工具兼容 CarSim 2019.0 及以上版本。使用标准 API 和文件格式。

### Q2: 如何添加更多车辆？

**A**: 修改 `run_simulation.m`，添加更多 `configure_vehicle` 调用。

### Q3: 仿真失败怎么办？

**A**: 检查 CarSim 是否正确安装，确保文件路径正确。

### Q4: 如何自定义场景？

**A**: 参考"添加新场景"章节，创建新的场景模板。

## 开发规范

- 兼容性底线 R2016b：不使用 `rms()`、`arguments` 等新版函数
- 文件名/函数名：`snake_case`
- 数值单位标注在注释中：`[m]`、`[deg]`、`[kW]`
- 前向欧拉法显式迭代，不依赖隐式求解器
- 函数保持 <200 行

## 许可证

MIT License

## 链接

- [项目主页](https://lihongwei-cn.github.io/lihongwei-cn/)
- [GitHub 仓库](https://github.com/LiHongwei-cn/lihongwei-cn)
- [CarSim 官网](https://www.carsim.com/)
