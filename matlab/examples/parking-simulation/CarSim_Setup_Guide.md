# CarSim 倒车入库仿真配置指南

## 概述

本指南详细说明如何在CarSim中配置倒车入库仿真场景，并与Simulink联合仿真。

**场景参数：**
- 道路长度：50m
- 道路宽度：7m
- 车位数量：10个
- 车位尺寸：5m x 2.5m x 5.5m
- 目标车位：第5个车位
- 初始位置：道路上方中间位置

---

## 一、CarSim 工程配置

### 1.1 新建工程

1. 打开 CarSim
2. 点击 `File` → `New` → `Dataset`
3. 输入工程名称：`Parking_Reversing`
4. 选择基础模板：`Vehicle: Sedan` 或 `Small SUV`

### 1.2 车辆参数设置

**路径：** `Vehicle: Assembly` → `Vehicle Body`

| 参数 | 值 | 说明 |
|------|-----|------|
| Mass | 1500 kg | 整备质量 |
| Length | 4.5 m | 车长 |
| Width | 1.8 m | 车宽 |
| Height | 1.5 m | 车高 |
| Wheelbase | 2.7 m | 轴距 |
| Front overhang | 0.9 m | 前悬 |
| Rear overhang | 0.9 m | 后悬 |

**路径：** `Vehicle: Assembly` → `Sprung Mass`

- 设置质心位置：前轴后方 1.2m，地面以上 0.5m

### 1.3 传动系统配置

**路径：** `Vehicle: Assembly` → `Powertrain`

| 参数 | 值 | 说明 |
|------|-----|------|
| Engine torque | 250 Nm | 最大扭矩 |
| Transmission | Automatic 6AT | 变速箱类型 |
| Final drive ratio | 3.5 | 主减速比 |
| Reverse gear ratio | 3.2 | 倒档速比 |

### 1.4 制动系统配置

**路径：** `Vehicle: Assembly` → `Brakes`

| 参数 | 值 | 说明 |
|------|-----|------|
| Front brake gain | 250 Nm/MPa | 前制动增益 |
| Rear brake gain | 150 Nm/MPa | 后制动增益 |
| Max brake pressure | 15 MPa | 最大制动压力 |
| ABS | Enabled | 启用ABS |

### 1.5 转向系统配置

**路径：** `Vehicle: Assembly` → `Steering`

| 参数 | 值 | 说明 |
|------|-----|------|
| Steering ratio | 16 | 转向比 |
| Max steering wheel angle | 540° | 方向盘最大转角 |
| Power steering | Enabled | 启用助力转向 |

---

## 二、道路环境配置

### 2.1 创建道路几何

**路径：** `Procedure` → `Road Geometry`

1. **道路类型选择**
   - 选择 `Flat Road` (平直道路)
   - 长度：50m
   - 宽度：7m

2. **路面属性**
   - 路面类型：`Dry Asphalt` (干燥沥青)
   - 摩擦系数：0.85
   - 路面平整度：`Smooth` (平滑)

### 2.2 配置车位区域

**路径：** `Environment` → `3D Road` → `Custom Road`

由于CarSim原生不支持停车位，需要通过以下方式模拟：

**方法一：使用障碍物模拟**

1. **路径：** `Environment` → `Obstacles`
2. 创建10个障碍物代表车位边界
3. 障碍物参数：
   - 类型：`Barrier` (护栏)
   - 长度：5m
   - 宽度：0.2m
   - 高度：0.5m
   - 位置：按照车位布局排列

**方法二：自定义道路模型（推荐）**

1. 使用3D建模软件创建道路和车位模型
2. 导出为 `.obj` 或 `.3ds` 格式
3. 在CarSim中导入：
   - `Environment` → `3D World` → `Import Geometry`
   - 选择导出的3D模型文件

### 2.3 配置周围车辆（占用的车位）

**路径：** `Environment` → `Moving Objects`

为每个被占用的车位添加一辆静止车辆：

| 参数 | 值 |
|------|-----|
| Object Type | Vehicle: Sedan |
| Motion | Stationary (静止) |
| Initial X | 车位中心X坐标 |
| Initial Y | 车位中心Y坐标 |
| Initial Yaw | 90° (垂直于道路) |

**车位位置计算：**

```matlab
for i = 1:10
    % 车位中心X坐标
    spot_center_x = (i - 0.5) * 5;  % 车位长度5m

    % 车位中心Y坐标
    spot_center_y = -5.5 / 2;  % 车位深度5.5m，位于道路下方

    % 如果车位被占用，添加静止车辆
    if occupancy(i) == 1
        % 在CarSim中设置Moving Object
        % X = spot_center_x
        % Y = spot_center_y
        % Yaw = 90°
    end
end
```

---

## 三、Simulink 接口配置

### 3.1 导出Simulink S-Function

1. **路径：** `Settings` → `Simulink`
2. 点击 `Export S-Function`
3. 选择导出路径：`matlab/examples/parking-simulation/`
4. 文件名：`sf_car_sim.mexw64`

### 3.2 配置输入通道

**路径：** `Settings` → `Simulink` → `Input Channels`

| 通道名称 | 说明 | 单位 |
|----------|------|------|
| IMP_STEER_SW | 方向盘转角 | deg |
| IMP_PBK_CON | 制动主缸压力 | kPa |
| IMP_THROTTLE | 油门开度 | % |
| IMP_GEARCHANGE | 档位命令 | - |

**档位设置：**
- `-1` = 倒档 (R)
- `0` = 空档 (N)
- `1-6` = 前进档 (D1-D6)

### 3.3 配置输出通道

**路径：** `Settings` → `Simulink` → `Output Channels`

| 通道名称 | 说明 | 单位 |
|----------|------|------|
| XCG | 车辆X位置 | m |
| YCG | 车辆Y位置 | m |
| YAW | 航向角 | rad |
| VX | 纵向速度 | km/h |
| VY | 横向速度 | km/h |
| AVZ | 横摆角速度 | deg/s |
| STEER_L1 | 左前轮转角 | deg |
| STEER_R1 | 右前轮转角 | deg |

---

## 四、仿真控制配置

### 4.1 仿真事件设置

**路径：** `Procedure` → `Events`

创建以下事件序列：

**Event 1: 接近阶段 (0-10s)**
| 参数 | 值 |
|------|-----|
| Duration | 10 s |
| Initial Speed | 5 km/h |
| Target | Maintain speed |
| Gear | D1 (前进1档) |

**Event 2: 准备倒车 (10-12s)**
| 参数 | 值 |
|------|-----|
| Duration | 2 s |
| Action | Stop vehicle |
| Brake | Full brake |
| Gear | N (空档) |

**Event 3: 倒车入库 (12-50s)**
| 参数 | 值 |
|------|-----|
| Duration | 38 s |
| Control | Simulink controlled |
| Initial Speed | 2 km/h (倒车) |
| Gear | R (倒档) |

### 4.2 初始条件设置

**路径：** `Procedure` → `Initial Conditions`

| 参数 | 值 |
|------|-----|
| Initial X | 45 m |
| Initial Y | 3.5 m |
| Initial Yaw | 0° |
| Initial Speed | 5 km/h |
| Initial Gear | D1 |

---

## 五、仿真运行

### 5.1 验证配置

1. 点击 `Run` → `Check Settings`
2. 确保所有参数无误
3. 检查S-Function连接状态

### 5.2 运行仿真

**方法一：在CarSim中运行**
1. 点击 `Run` → `Run Simulation`
2. 等待仿真完成
3. 查看结果动画

**方法二：在MATLAB/Simulink中运行**
1. 打开MATLAB
2. 运行 `run_parking_simulation.m`
3. 仿真将通过S-Function控制CarSim

### 5.3 结果查看

**CarSim结果：**
- `Results` → `Plot` → 选择变量绘制
- `Results` → `Animation` → 查看3D动画

**MATLAB结果：**
- 仿真自动生成结果图片
- 数据保存在工作空间变量中

---

## 六、常见问题

### 6.1 S-Function连接失败

**问题：** 仿真报错 "S-Function not found"

**解决：**
1. 检查CarSim DLL路径是否正确
2. 确认CarSim和MATLAB版本匹配
3. 重新导出S-Function

### 6.2 仿真发散

**问题：** 车辆轨迹不收敛

**解决：**
1. 降低仿真步长（如0.001s）
2. 调整PID参数
3. 检查路径规划算法

### 6.3 制动不响应

**问题：** 制动命令无法执行

**解决：**
1. 检查制动压力单位（应为kPa）
2. 确认ABS未过度干预
3. 检查制动系统参数配置

### 6.4 转向过度/不足

**问题：** 转向角度与预期不符

**解决：**
1. 检查转向比设置
2. 确认方向盘转角单位（deg）
3. 调整转向系统参数

---

## 七、参数调优建议

### 7.1 控制器参数

**横向控制（方向盘）：**
- P增益：2.0-3.0（起始值2.5）
- I增益：0.05-0.2（起始值0.1）
- D增益：0.3-0.8（起始值0.5）

**纵向控制（制动）：**
- P增益：1.5-2.5（起始值1.8）
- I增益：0.02-0.1（起始值0.05）
- D增益：0.2-0.5（起始值0.3）

### 7.2 路径规划参数

- 倒车速度：1-3 km/h（推荐2 km/h）
- 转弯半径：根据车位宽度调整
- 安全距离：周围车辆0.3-0.5m

---

## 八、文件清单

| 文件名 | 说明 |
|--------|------|
| `create_parking_simulink_model.m` | Simulink模型生成脚本 |
| `run_parking_simulation.m` | 仿真主脚本 |
| `CarSim_Setup_Guide.md` | 本文档 |
| `README.md` | 使用说明 |

---

## 九、技术支持

如有问题，请参考：
- CarSim 官方文档：`Help` → `Documentation`
- MATLAB/Simulink 文档：`doc simulink`
- 项目Issues：GitHub LiHongwei-cn

---

**作者：** LiHongwei
**日期：** 2026-05-29
**版本：** 1.0
