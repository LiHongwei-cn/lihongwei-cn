# CarSim-AI 高架桥仿真工具

基于 CarSim 2019.0 的 AI 仿真工具，用于模拟不同驱动类型车辆在冰雪路面上的爬坡能力。

## 场景描述

模拟南京燕子矶高架桥场景：
- **路面条件**：下雪天，路面湿滑结冰，摩擦系数 0.1-0.3
- **道路特征**：高架桥上坡路段
- **车辆配置**：
  - 前驱车/后驱车：在低摩擦路面上打滑，无法成功爬坡
  - 四驱车：成功爬坡，不撞护栏

## 核心特性

- **精确参数输入**：用户可自定义高架桥、车辆、路面参数
- **CarSim 2019.0 兼容**：使用 CarSim 标准 API 和文件格式
- **自动生成场景**：高架桥、护栏、低摩擦路面
- **车辆动力学仿真**：前驱/后驱/四驱车辆对比
- **结果可视化**：轨迹、速度、滑移率等

## 目录结构

```
carsim-ai/
├── examples/                    示例脚本
│   └── run_bridge_simulation.m  高架桥仿真主脚本
├── utils/                       工具函数
│   ├── generate_bridge_scenario.m  高架桥场景生成器
│   ├── configure_vehicle.m         车辆参数配置器
│   └── visualize_results.m         结果可视化
├── templates/                   模板文件
│   └── simulation_template.par     CarSim 仿真模板
├── docs/                        文档
│   └── user_guide.md              用户指南
├── README.md                    本文件
└── index.html                   项目网页
```

## 快速开始

### 方式一：MATLAB 命令行

```matlab
% 1. 切换到 carsim-ai 目录
cd('path/to/lihongwei-cn/carsim-ai/examples')

% 2. 设置仿真参数
params.bridge_length = 100;    % 高架桥长度 [m]
params.bridge_width = 8;       % 高架桥宽度 [m]
params.slope_angle = 15;       % 坡度角度 [deg]
params.friction = 0.2;         % 路面摩擦系数
params.fwd_power = 100;        % 前驱车功率 [kW]
params.awd_power = 100;        % 四驱车功率 [kW]
params.output_dir = '../output'; % 输出目录

% 3. 运行仿真
run_bridge_simulation(params);
```

### 方式二：桌面快捷启动

- **macOS**：双击 `tools/carsim-ai.command`
- **Windows**：双击 `tools/carsim-ai.bat`

## 参数说明

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

### 驱动类型

- **FWD (前驱)**：前轮驱动，适合城市道路，爬坡能力一般
- **RWD (后驱)**：后轮驱动，操控性好，爬坡能力一般
- **AWD (四驱)**：四轮驱动，爬坡能力强，适合恶劣路况

## 输出结果

仿真完成后，输出目录包含：

### 场景文件

- `bridge_road.road` - 高架桥道路定义
- `bridge_friction.tir` - 路面摩擦定义
- `bridge_guardrail.par` - 护栏定义

### 车辆文件

- `vehicle_FWD.par` - 前驱车参数
- `vehicle_AWD.par` - 四驱车参数

### 仿真文件

- `simulation_FWD.par` - 前驱车仿真配置
- `simulation_AWD.par` - 四驱车仿真配置
- `run_batch.bat` - 批处理脚本

### 结果文件

- `results_FWD.csv` - 前驱车仿真结果
- `results_AWD.csv` - 四驱车仿真结果
- `simulation_results.png` - 可视化结果

## 仿真流程

1. **场景生成**：创建高架桥、护栏、低摩擦路面
2. **车辆配置**：设置前驱/四驱车辆参数
3. **仿真运行**：在 CarSim 中运行两个仿真
4. **结果分析**：分析爬坡距离、高度、滑移率
5. **可视化**：生成轨迹、速度、滑移率图表

## 预期结果

### 前驱车/后驱车

- 在低摩擦路面上打滑
- 爬坡失败，滑回起点
- 车轮滑移率高

### 四驱车

- 成功爬坡
- 不撞护栏
- 车轮滑移率低

## 依赖

- MATLAB R2016b+
- CarSim 2019.0+
- Simulink（可选，用于联合仿真）

## 常见问题

### Q1: CarSim 版本兼容性

**A**: 本工具兼容 CarSim 2019.0 及以上版本。使用标准 API 和文件格式。

### Q2: 如何调整摩擦系数？

**A**: 修改 `params.friction` 参数。范围 0.1-0.3，值越小路面越滑。

### Q3: 如何添加更多车辆？

**A**: 修改 `run_bridge_simulation.m`，添加更多 `configure_vehicle` 调用。

### Q4: 仿真失败怎么办？

**A**: 检查 CarSim 是否正确安装，确保文件路径正确。

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
