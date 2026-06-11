# MATLAB AI 仿真工具包

AI 生成 MATLAB/Simulink 仿真代码，一键运行。R2016b 兼容。

## 支持的仿真类型

| 仿真 | 说明 |
|------|------|
| `vehicle_dynamics` | 车辆纵向动力学 |
| `motor_control` | PMSM 永磁同步电机 FOC 控制 |
| `dc_motor_pwm` | 直流电机 PWM 调速 |
| `ev_dynamics_simple` | 电动汽车完整仿真（能耗 + SOC） |
| `battery_soc_ekf` | 电池 SOC 估算（EKF vs 安时积分） |
| `driving_cycle_analysis` | 驾驶循环能耗分析 |
| `energy_management` | 增程式能量管理策略 |
| `generate_cruise_model` | 定速巡航 Simulink 模型 |
| `dc_motor_simulink` | 直流电机 Simulink 模型 |

## 快速开始

### Windows

```
1. git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
2. 双击 matlab.bat
3. 在 MATLAB Command Window 输入仿真命令
```

### macOS

```bash
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cd lihongwei-cn/matlab
matlab -r "startup_setup"
```

## 工具函数

| 函数 | 说明 |
|------|------|
| `fft_analysis` | FFT 频谱分析 |
| `lowpass_filter` | 一阶低通滤波 |
| `rms_calculation` | RMS 有效值计算 |

## 系统要求

- MATLAB R2016b+
- Windows 7/10/11 或 macOS

## 许可证

MIT License — 完全免费开源
