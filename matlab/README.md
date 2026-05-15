# MATLAB 仿真代码

MATLAB R2016b 兼容。Simulink + CarSim 2019.0 联合仿真。

## 目录

- `examples/`       示例脚本（可直接运行）
  - `motor_control.m`            PMSM 永磁同步电机 FOC 控制
  - `vehicle_dynamics.m`         车辆纵向动力学（加速-匀速-制动）
  - `dc_motor_pwm.m`             直流电机 PWM 调速
  - `dc_motor_simulink.m`        直流电机 Simulink 模型（自动搭建）
  - `ev_dynamics_simple.m`       电动汽车完整仿真（含能耗、SOC）
  - `generate_cruise_model.m`    定速巡航 Simulink 模型
  - `battery_soc_ekf.m`          电池 SOC 估算（安时积分 + EKF 对比）
  - `driving_cycle_analysis.m`   驾驶循环能耗分析
  - `energy_management.m`        增程式能量管理策略（恒温器 vs 功率跟随）
- `carsim/`         CarSim-Simulink 联合仿真配置
  - `sim_setup.m`                环境配置
  - `build_carsim_model.m`       搭建联合仿真模型
  - `run_carsim_cruise.m`        一键运行定速巡航
- `utils/`          工具函数
  - `rms_calculation.m`          RMS 有效值（R2016b 无内置 rms）
  - `fft_analysis.m`             FFT 频谱分析
  - `lowpass_filter.m`           一阶低通滤波器

## 使用

1. 启动 MATLAB，cd 到此目录
2. 运行 `startup_setup.m`（自动添加路径）
3. 运行 examples/ 下的任意脚本
4. 批量测试：`test_all`

## 注意

- 所有代码兼容 R2016b
- `run_carsim` 需先通过 CarSim 界面配置 Simulink 模型
