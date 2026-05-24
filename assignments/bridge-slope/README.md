# 高架桥仿真作业 - 燕子矶场景

CarSim 2019.0 仿真实例：不同驱动类型车辆在冰雪路面上的爬坡能力对比。

## 场景

- 地点：南京燕子矶高架桥
- 条件：下雪天，路面湿滑结冰，摩擦系数 0.1-0.3
- 车辆：前驱车打滑失败，四驱车成功爬坡

## 使用方法

### 步骤 1: 运行 MATLAB 脚本生成参数

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

### 步骤 2: 在 CarSim 中设置参数

1. 打开 CarSim 2019.0
2. 创建新数据集
3. 设置以下参数：
   - **Road**: 设置坡度为 15 deg
   - **Tire**: 设置摩擦系数为 0.2
   - **Vehicle**: 根据需要选择前驱或四驱
4. 点击 **Send to Simulink** 按钮

### 步骤 3: 在 Simulink 中运行仿真

1. 在 Simulink 中打开生成的模型
2. 点击 **Run** 按钮运行仿真
3. 仿真完成后，数据会保存到 workspace

### 步骤 4: 分析结果

```matlab
% 在 MATLAB 中运行
analyze_results
```

## 生成的文件

运行 `run_bridge_simulation` 后，会生成以下文件：

- `carsim_params_FWD.m` - 前驱车参数（供 CarSim 手动输入）
- `carsim_params_AWD.m` - 四驱车参数（供 CarSim 手动输入）
- `bridge_slope_model.slx` - Simulink 模型（需要 CarSim 已安装）
- `analyze_results.m` - 结果分析脚本

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

- MATLAB R2016b+
- Simulink
- CarSim 2019.0+（必须已安装）

## 常见问题

### Q1: 为什么 CarSim 打不开？

**A**: 确保 CarSim 2019.0 已正确安装，并且 MATLAB/Simulink 接口已配置。检查 CarSim 的安装路径是否正确。

### Q2: 如何配置 CarSim 与 MATLAB 的接口？

**A**: 
1. 打开 CarSim
2. 进入 Settings → MATLAB/Simulink Interface
3. 设置 MATLAB 路径
4. 测试连接

### Q3: 仿真失败怎么办？

**A**: 
1. 检查 CarSim 是否正确安装
2. 确认 Simulink 模型已正确生成
3. 检查参数设置是否正确
4. 查看 CarSim 的错误日志

### Q4: 如何调整仿真参数？

**A**: 修改 `run_bridge_simulation` 函数的输入参数，然后重新运行。

## 注意事项

1. **CarSim 必须已安装** - 本作业需要 CarSim 2019.0 或更高版本
2. **Simulink 接口必须配置** - CarSim 需要与 MATLAB/Simulink 正确连接
3. **参数手动输入** - 生成的参数文件需要在 CarSim 中手动输入
4. **仿真结果依赖 CarSim** - 实际仿真结果取决于 CarSim 的求解器

## 文件结构

```
bridge-slope/
├── examples/
│   └── run_bridge_simulation.m   仿真主脚本
├── utils/
│   ├── generate_bridge_scenario.m 场景生成器
│   ├── configure_vehicle.m        车辆配置器
│   └── visualize_results.m        结果可视化
├── output/                        生成的文件（运行后创建）
│   ├── carsim_params_FWD.m        前驱车参数
│   ├── carsim_params_AWD.m        四驱车参数
│   ├── bridge_slope_model.slx     Simulink 模型
│   └── analyze_results.m          结果分析脚本
└── README.md                      本文件
```

## 提取方法

将整个 `bridge-slope/` 目录复制到目标电脑即可使用。确保目标电脑已安装：
- MATLAB R2016b+
- Simulink
- CarSim 2019.0+
