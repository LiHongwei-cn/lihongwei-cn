# 高架桥仿真作业 - 燕子矶场景

纯 CarSim 2019.0 仿真实例：不同驱动类型车辆在冰雪路面上的爬坡能力对比。

## 场景

- 地点：南京燕子矶高架桥
- 条件：下雪天，路面湿滑结冰，摩擦系数 0.1-0.3
- 车辆：前驱车打滑失败，四驱车成功爬坡

## 使用方法

### 步骤 1: 运行 MATLAB 脚本生成参数说明

```matlab
% 在 MATLAB 中运行
params.bridge_length = 100;    % 高架桥长度 [m]
params.slope_angle = 15;       % 坡度角度 [deg]
params.friction = 0.2;         % 路面摩擦系数
params.fwd_power = 100;        % 前驱车功率 [kW]
params.awd_power = 100;        % 四驱车功率 [kW]
params.output_dir = './output';

run_bridge_simulation(params);
```

### 步骤 2: 在 CarSim 中设置前驱车仿真

1. 打开 CarSim 2019.0
2. 创建新数据集，命名为 `FWD_bridge_slope`
3. 按照 `output/carsim_instructions_FWD.txt` 设置参数
4. 点击 **Run** 运行仿真
5. 导出结果：Export > CSV，保存为 `results_FWD.csv`

### 步骤 3: 在 CarSim 中设置四驱车仿真

1. 创建新数据集，命名为 `AWD_bridge_slope`
2. 按照 `output/carsim_instructions_AWD.txt` 设置参数
3. 点击 **Run** 运行仿真
4. 导出结果：Export > CSV，保存为 `results_AWD.csv`

### 步骤 4: 分析结果

```matlab
% 将 results_FWD.csv 和 results_AWD.csv 复制到 output 目录
% 然后在 MATLAB 中运行
cd output
analyze_results
```

## 生成的文件

运行 `run_bridge_simulation` 后，会生成以下文件：

- `carsim_instructions_FWD.txt` - 前驱车参数设置说明
- `carsim_instructions_AWD.txt` - 四驱车参数设置说明
- `analyze_results.m` - 结果分析脚本

## CarSim 参数设置要点

### 车辆设置

| 参数 | 前驱车 | 四驱车 |
|------|--------|--------|
| 驱动类型 | FWD | AWD |
| 整车质量 | 1500 kg | 1500 kg |
| 轴距 | 2.7 m | 2.7 m |
| 重心高度 | 0.5 m | 0.5 m |

### 发动机设置

| 参数 | 前驱车 | 四驱车 |
|------|--------|--------|
| 最大功率 | 100 kW | 100 kW |
| 最大扭矩 | 19.1 Nm | 19.1 Nm |
| 最大转速 | 6000 rpm | 6000 rpm |

### 道路设置

| 参数 | 值 |
|------|-----|
| 坡度角度 | 15 deg |
| 路面摩擦 | 0.2 |
| 道路宽度 | 8.0 m |
| 护栏高度 | 0.8 m |

### 仿真设置

| 参数 | 值 |
|------|-----|
| 仿真时长 | 30 s |
| 时间步长 | 0.001 s |
| 初始速度 | 5 m/s (18 km/h) |

## 预期结果

### 前驱车

- 在低摩擦路面上打滑
- 爬坡失败，滑回起点
- 车轮滑移率高

### 四驱车

- 成功爬坡
- 不撞护栏
- 车轮滑移率低

## 依赖

- CarSim 2019.0+
- MATLAB R2016b+（仅用于分析结果）

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

### Q3: 如何调整仿真参数？

**A**: 修改 `run_bridge_simulation` 函数的输入参数，然后重新运行。

### Q4: 结果分析脚本报错怎么办？

**A**: 
1. 确认 CSV 文件格式正确
2. 检查文件是否在正确目录
3. 确认 MATLAB 版本兼容

## 文件结构

```
bridge-slope/
├── examples/
│   └── run_bridge_simulation.m   参数生成脚本
├── utils/
│   └── configure_vehicle.m       车辆配置器
├── output/                       生成的文件（运行后创建）
│   ├── carsim_instructions_FWD.txt  前驱车参数说明
│   ├── carsim_instructions_AWD.txt  四驱车参数说明
│   └── analyze_results.m            结果分析脚本
└── README.md                     本文件
```

## 注意事项

1. **纯 CarSim 仿真** - 本作业不依赖 Simulink，完全在 CarSim 内部运行
2. **参数手动输入** - 需要在 CarSim GUI 中手动输入参数
3. **结果手动导出** - 仿真完成后需要手动导出 CSV 文件
4. **MATLAB 仅用于分析** - 结果分析使用 MATLAB，但仿真本身不依赖

## 提取方法

将整个 `bridge-slope/` 目录复制到目标电脑即可使用。确保目标电脑已安装：
- CarSim 2019.0+
- MATLAB R2016b+（仅用于分析结果）
