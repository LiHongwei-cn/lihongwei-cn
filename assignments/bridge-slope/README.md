# 高架桥仿真作业 - 燕子矶场景

CarSim 2019.0 仿真实例：不同驱动类型车辆在冰雪路面上的爬坡能力对比。

## 场景

- 地点：南京燕子矶高架桥
- 条件：下雪天，路面湿滑结冰，摩擦系数 0.1-0.3
- 车辆：前驱车打滑失败，四驱车成功爬坡

## 文件结构

```
bridge-slope/
├── examples/
│   └── run_bridge_simulation.m   仿真主脚本
├── utils/
│   ├── generate_bridge_scenario.m 场景生成器
│   ├── configure_vehicle.m        车辆配置器
│   └── visualize_results.m        结果可视化
└── README.md                      本文件
```

## 使用方法

```matlab
% 1. 设置参数
params.bridge_length = 100;    % 高架桥长度 [m]
params.bridge_width = 8;       % 高架桥宽度 [m]
params.slope_angle = 15;       % 坡度角度 [deg]
params.friction = 0.2;         % 路面摩擦系数
params.fwd_power = 100;        % 前驱车功率 [kW]
params.awd_power = 100;        % 四驱车功率 [kW]
params.output_dir = './output';

% 2. 运行仿真
run_bridge_simulation(params);
```

## 依赖

- MATLAB R2016b+
- CarSim 2019.0+

## 提取方法

将整个 `bridge-slope/` 目录复制到目标电脑即可使用。
