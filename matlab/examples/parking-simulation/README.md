# 倒车入库 CarSim/Simulink 联合仿真

## 概述

本项目实现了一个完整的倒车入库仿真系统，使用CarSim进行车辆动力学仿真，Simulink进行控制逻辑实现。

**场景特点：**
- 50m长的道路，右侧一排车位
- 只剩一个空位，其他停满车
- 自动路径规划和制动控制
- CarSim/Simulink联合仿真

---

## 快速开始

### 前置要求

- MATLAB R2016b 或更高版本
- Simulink
- CarSim 2020.0 或更高版本
- Windows 64位操作系统

### 安装步骤

1. **克隆或下载项目**
   ```bash
   git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
   ```

2. **打开MATLAB**
   - 启动MATLAB
   - 导航到 `matlab/examples/parking-simulation/` 目录

3. **配置CarSim路径**
   - 打开 `run_parking_simulation.m`
   - 修改第85行的CarSim DLL路径：
   ```matlab
   carsim_config.dll_path = 'C:\Program Files\CarSim 2020.0\Programs\sf_car_sim.dll';
   ```

4. **运行仿真**
   ```matlab
   >> run_parking_simulation
   ```

---

## 项目结构

```
parking-simulation/
├── README.md                          # 本文档
├── CarSim_Setup_Guide.md              # CarSim详细配置指南
├── create_parking_simulink_model.m    # Simulink模型生成脚本
├── run_parking_simulation.m           # 仿真主脚本
├── parking_reverse_control.slx        # Simulink模型（运行后生成）
└── parking_simulation_results.png     # 仿真结果图片（运行后生成）
```

---

## 功能特性

### 1. 智能路径规划

- **三阶段路径生成：**
  - 接近段：直线接近目标车位
  - 转弯段：五次多项式曲线，保证曲率连续
  - 入库段：垂直倒车入库

- **路径特点：**
  - 平滑过渡，无突变
  - 自动计算航向角
  - 适应不同车位位置

### 2. 精确制动控制

- **纵向控制：**
  - PID控制器调节制动压力
  - 低速倒车控制（2 km/h）
  - 精确停车（误差<0.5m）

- **制动特性：**
  - 最大制动压力：15 MPa
  - ABS防抱死保护
  - 平滑制动曲线

### 3. CarSim/Simulink联合仿真

- **CarSim提供：**
  - 精确的车辆动力学模型
  - 真实的轮胎力学
  - 3D可视化动画

- **Simulink提供：**
  - 控制算法实现
  - 信号处理
  - 数据记录

---

## 使用指南

### 基本使用

1. **运行仿真**
   ```matlab
   >> run_parking_simulation
   ```

2. **查看结果**
   - 仿真自动生成结果图片
   - 显示车辆轨迹、速度、航向角等

3. **调整参数**
   - 修改 `run_parking_simulation.m` 中的参数
   - 重新运行仿真

### 高级使用

#### 修改车位布局

```matlab
% 在 run_parking_simulation.m 中修改
road_params.parking_occupancy = [1, 1, 0, 1, 1, 1, 1, 1, 1, 1];
road_params.target_spot_index = 3;  % 修改目标车位
```

#### 调整控制参数

```matlab
% 横向控制参数
control_params.kp_lateral = 3.0;  % 增大P增益，响应更快
control_params.ki_lateral = 0.15;
control_params.kd_lateral = 0.6;

% 纵向控制参数
control_params.kp_longitudinal = 2.0;
control_params.ki_longitudinal = 0.08;
control_params.kd_longitudinal = 0.4;
```

#### 修改车辆参数

```matlab
vehicle_params.length = 4.8;      % 更长的车辆
vehicle_params.width = 1.9;       % 更宽的车辆
vehicle_params.wheelbase = 2.8;   % 不同的轴距
```

---

## CarSim 配置

详细配置步骤请参考 **CarSim_Setup_Guide.md**

### 关键配置点

1. **车辆参数**
   - 确保车辆尺寸与MATLAB脚本一致
   - 配置正确的传动系统参数

2. **道路环境**
   - 创建50m长的道路
   - 配置车位和周围车辆

3. **Simulink接口**
   - 导出S-Function
   - 配置输入输出通道

4. **仿真控制**
   - 设置初始条件
   - 配置仿真事件

---

## 结果分析

### 仿真输出

仿真完成后，系统会显示：

1. **轨迹图**
   - 参考路径（红色虚线）
   - 实际轨迹（蓝色实线）
   - 最终位置和目标位置

2. **性能指标**
   - 最终位置误差
   - 最大横向偏差
   - 平均速度

3. **时间历程**
   - X/Y位置变化
   - 速度变化
   - 航向角变化

### 典型结果

| 指标 | 典型值 | 说明 |
|------|--------|------|
| 位置误差 | <0.5m | 停车精度 |
| 仿真时间 | 40-50s | 完成入库时间 |
| 最大速度 | 5 km/h | 接近段速度 |
| 倒车速度 | 2 km/h | 入库段速度 |

---

## 故障排除

### 问题1：S-Function连接失败

**症状：** 仿真报错 "S-Function not found"

**解决：**
1. 检查CarSim DLL路径
2. 确认CarSim版本与MATLAB兼容
3. 重新导出S-Function

### 问题2：仿真发散

**症状：** 车辆轨迹不收敛或剧烈振荡

**解决：**
1. 降低仿真步长（0.001s）
2. 减小PID增益
3. 检查路径规划算法

### 问题3：制动不响应

**症状：** 制动命令无法执行

**解决：**
1. 检查制动压力单位（kPa）
2. 确认档位设置为倒档（-1）
3. 检查CarSim制动系统配置

### 问题4：转向过度/不足

**症状：** 转向角度与预期不符

**解决：**
1. 检查转向比设置
2. 调整方向盘转角限幅
3. 确认单位一致（deg）

---

## 扩展功能

### 1. 添加传感器模拟

```matlab
% 在Simulink模型中添加传感器模块
% 超声波传感器
% 摄像头
% 激光雷达
```

### 2. 实现避障功能

```matlab
% 添加障碍物检测
% 实现紧急制动
% 路径重新规划
```

### 3. 多车位选择

```matlab
% 实现车位检测算法
% 自动选择最优车位
% 多目标路径规划
```

### 4. 真实场景导入

```matlab
% 导入真实停车场地图
% 使用GPS坐标
% 集成高精地图
```

---

## 技术细节

### 控制算法

**横向控制（PID）：**
```
u_lateral = Kp * e_lateral + Ki * ∫e_lateral + Kd * (de_lateral/dt)
```

**纵向控制（PID）：**
```
u_longitudinal = Kp * e_speed + Ki * ∫e_speed + Kd * (de_speed/dt)
```

**路径规划（五次多项式）：**
```
s(t) = 10t³ - 15t⁴ + 6t⁵
```

### CarSim接口

**输入信号：**
- `IMP_STEER_SW`：方向盘转角 [deg]
- `IMP_PBK_CON`：制动主缸压力 [kPa]
- `IMP_THROTTLE`：油门开度 [%]
- `IMP_GEARCHANGE`：档位命令 [-1=R, 0=N, 1-6=D]

**输出信号：**
- `XCG`, `YCG`：车辆位置 [m]
- `YAW`：航向角 [rad]
- `VX`, `VY`：速度 [km/h]
- `AVZ`：横摆角速度 [deg/s]

---

## 参考资料

- [CarSim官方文档](https://www.carsim.com/)
- [MATLAB Simulink文档](https://www.mathworks.com/help/simulink/)
- [车辆动力学基础](https://en.wikipedia.org/wiki/Vehicle_dynamics)
- [PID控制器原理](https://en.wikipedia.org/wiki/PID_controller)

---

## 许可证

本项目为开源项目，遵循 MIT 许可证。

---

## 作者

**LiHongwei**
- GitHub: [LiHongwei-cn](https://github.com/LiHongwei-cn)
- Website: [lihongwei-cn.github.io](https://lihongwei-cn.github.io/lihongwei-cn/)

---

## 更新日志

### v1.0 (2026-05-29)
- 初始版本发布
- 实现基本倒车入库功能
- CarSim/Simulink联合仿真
- 完整的文档和使用指南
