# ADAS HIL 测试 Demo 架构参考

已验证的 HIL 仿真项目结构，可作为新 HIL 项目的模板。

## 文件结构

```
adas_hil_demo/
├── main_adas_hil_demo.m     主脚本（参数定义 + 仿真循环 + 报告 + 调用绘图）
├── vehicle_model.m          车辆动力学模型（输入: 参数struct+dt → 输出: 加速度/速度/位置）
├── sensor_model.m           传感器模型（输入: 真实值+配置struct → 输出: 测量值struct）
├── adas_controller.m        控制器（输入: 传感器数据+车速+偏移 → 输出: 控制指令struct）
├── hil_test_runner.m        测试框架（输入: 仿真结果 → 输出: PASS/FAIL struct数组）
└── visualize_results.m      可视化（输入: 所有数据 → 输出: 1张大图含8个子图）
```

## 设计原则

1. **参数传递**: 主脚本定义所有参数 → 通过 struct 传入函数 → 函数不读取 workspace
2. **数据流**: 传感器模型 → 控制器 → 车辆模型 → 存储 → 下一时间步
3. **测试验证**: 5 个测试用例覆盖正常/异常/降级场景
4. **输出语言**: 所有 xlabel/ylabel/title/legend/fprintf 用中文，代码注释用中文
5. **编码**: UTF-8，不用 GBK

## 参数 struct 示例

```matlab
% 在主脚本顶部定义
vehicle_params.m = 1500;    % 质量 [kg]
vehicle_params.Cd = 0.32;   % 风阻系数
vehicle_params.Af = 2.2;    % 迎风面积 [m^2]

sensor_cfg.radar_max_range = 150;  % [m]
sensor_cfg.camera_det_prob = 0.95;

% 传入函数
[acc, vel, pos] = vehicle_model(throttle, brake, vel_cur, pos_cur, vehicle_params, dt);
```

## 测试用例模板

```matlab
% TC1: 正常场景 → 不应触发警告
% TC2: 边界场景 → 应触发预警
% TC3: 危险场景 → 应触发紧急响应
% TC4: 传感器故障 → 系统应优雅降级
% TC5: 极端参数 → 系统不应崩溃
```
