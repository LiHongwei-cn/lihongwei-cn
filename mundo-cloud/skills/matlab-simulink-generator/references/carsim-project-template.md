# CarSim 仿真项目模板

## 项目结构

```
carsim-项目名/
├── examples/                    示例脚本
│   └── run_xxx_simulation.m     主仿真脚本
├── utils/                       工具函数
│   ├── generate_scenario.m      场景生成器
│   ├── configure_vehicle.m      车辆配置器
│   └── visualize_results.m      结果可视化
├── templates/                   模板文件
│   └── simulation_template.par  CarSim 仿真模板
├── README.md                    使用说明
└── index.html                   项目网页
```

## CarSim 文件格式

### 道路文件 (.road)
```
ROAD_PARAMETERS
  LENGTH = 100.0
  WIDTH = 8.0
  SLOPE = 15.0
  FRICTION = 0.2
END_ROAD_PARAMETERS
```

### 车辆文件 (.par)
```
VEHICLE_DIMENSIONS
  LENGTH = 4.5
  WIDTH = 1.8
  HEIGHT = 1.5
  WHEELBASE = 2.7
END_VEHICLE_DIMENSIONS

MASS_PROPERTIES
  TOTAL_MASS = 1500
  FRONT_AXLE_LOAD_RATIO = 0.5
  REAR_AXLE_LOAD_RATIO = 0.5
END_MASS_PROPERTIES

DRIVETRAIN
  DRIVE_TYPE = ALL    % FRONT, REAR, ALL
  ENGINE_POWER = 100
  MAX_TORQUE = 200
END_DRIVETRAIN
```

### 仿真文件 (.par)
```
SIMULATION_PARAMETERS
  STOP_TIME = 30.0
  TIME_STEP = 0.001
  SOLVER = EULER
END_SIMULATION_PARAMETERS

INITIAL_CONDITIONS
  X = 0.0
  Y = 0.0
  Z = 0.0
  VX = 5.0
END_INITIAL_CONDITIONS
```

## CarSim 2019.0 API

### MATLAB 接口
```matlab
% 检查 CarSim 安装
carsim_path = find_carsim();

% 加载仿真
sim('simulation_model');

% 读取结果
data = csvread('results.csv', 1, 0);
```

### 批处理运行
```matlab
% 生成批处理脚本
fid = fopen('run_batch.bat', 'w');
fprintf(fid, 'CarSim.exe -run simulation_FWD.par\n');
fprintf(fid, 'CarSim.exe -run simulation_AWD.par\n');
fclose(fid);
```

## 常用仿真类型

1. **爬坡仿真**：测试不同驱动类型在低摩擦路面上的爬坡能力
2. **操稳仿真**：测试车辆在不同路面条件下的操控稳定性
3. **制动仿真**：测试紧急制动性能和 ABS 效果
4. **通过性仿真**：测试车辆在复杂地形下的通过能力
