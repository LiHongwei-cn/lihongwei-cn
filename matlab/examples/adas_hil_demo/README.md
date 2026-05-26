# ADAS 硬件在环仿真演示

高级驾驶辅助系统（ADAS）硬件在环（HIL）仿真测试演示，兼容 MATLAB R2016b。

## 功能说明

- **车辆模型** — 纵向动力学，含空气阻力和滚动阻力，前向欧拉法积分
- **传感器模型** — 雷达（测距/测速/方位角）、摄像头（检测概率+车道偏移）、超声波（短距离）
- **ADAS 控制器** — FCW（TTC<2.5s）、AEB（TTC<1.0s）、LDW（偏移>0.3m）
- **HIL 测试** — 5 个自动化测试用例，输出中文通过/失败报告
- **可视化** — 车辆轨迹、速度曲线、传感器数据、控制器输出

## 文件说明

| 文件 | 功能 |
|------|------|
| `main_adas_hil_demo.m` | 主脚本：参数定义、仿真循环、测试报告 |
| `vehicle_model.m` | 车辆纵向动力学模型 |
| `sensor_model.m` | 多传感器融合模型（雷达+摄像头+超声波） |
| `adas_controller.m` | ADAS 决策控制器（FCW/AEB/LDW） |
| `hil_test_runner.m` | 测试用例验证（5个用例） |
| `visualize_results.m` | 仿真结果可视化（4张图表） |

## 使用方法

1. 打开 MATLAB（R2016b 或更高版本）
2. 将当前目录切换到 `matlab/examples/adas_hil_demo/`
3. 打开 `main_adas_hil_demo.m`
4. 按 **F5** 运行

```matlab
cd matlab/examples/adas_hil_demo
main_adas_hil_demo
```

## 参数修改指南

所有参数在 `main_adas_hil_demo.m` 文件顶部统一定义，可按需修改：

### 车辆参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `vehicle_params.m` | 1500 kg | 整车质量 |
| `vehicle_params.Cd` | 0.32 | 风阻系数 |
| `vehicle_params.Af` | 2.2 m^2 | 迎风面积 |
| `vehicle_params.Cr` | 0.015 | 滚动阻力系数 |

### 传感器参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `sensor_cfg.radar_max_range` | 150 m | 雷达最大探测距离 |
| `sensor_cfg.radar_range_std` | 0.5 m | 雷达测距噪声 |
| `sensor_cfg.camera_det_prob` | 0.95 | 摄像头检测概率 |

### 场景参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `v0_kmh` | 80 km/h | 初始车速 |
| `obs_dist` | 60 m | 障碍物距离 |
| `t_end` | 5 s | 仿真总时长 |
| `dt` | 0.01 s | 仿真步长 |

### 典型场景配置

**城市低速场景**：`v0_kmh = 40; obs_dist = 30; t_end = 4;`

**高速场景**：`v0_kmh = 120; obs_dist = 100; t_end = 5;`

**紧急制动场景**：`v0_kmh = 60; obs_dist = 20; t_end = 3;`

## 输出说明

### 控制台输出
运行结束后在命令窗口输出测试报告，显示每个测试用例的通过/失败状态。

### 图表输出
| 图表 | 内容 |
|------|------|
| 图1 车辆轨迹 | 上：纵向位置与障碍物距离 / 下：横向偏移与LDW阈值 |
| 图2 速度曲线 | 上：车速变化 / 下：加速度变化 |
| 图3 传感器数据 | 上：雷达测距 / 下：摄像头车道偏移 |
| 图4 控制器输出 | 油门指令 / 制动指令 / 预警标志（FCW/AEB/LDW） |

## R2016b 兼容性

- 不使用 `rms()` 函数
- 不使用 `arguments` 代码块
- 不使用 `string` 类型（使用 `char` 数组）
- 不使用 `tiledlayout`（使用 `subplot`）
- 前向欧拉法积分
- 参数通过函数输入传递，不从工作空间读取
