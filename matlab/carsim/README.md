# CarSim 2019.0 + MATLAB R2016b 联合仿真

## 配置步骤

### 1. CarSim 中设置 MATLAB 路径

1. 打开 CarSim，进入 **Send to Simulink** 界面
2. 在 **MATLAB path** 框中填入 MATLAB R2016b 的安装路径，例如：
   ```
   C:\Program Files\MATLAB\R2016b
   ```
3. 点击 **Verify** 确认连接成功

### 2. CarSim 导出 Simulink 模型

1. 在 CarSim 中配置好车辆参数和仿真工况
2. 点击 **Send to Simulink** 按钮
3. CarSim 会自动生成一个 `.mdl` 或 `.slx` 文件
4. 保存到本项目的 `matlab/carsim/` 目录

### 3. Simulink 中运行联合仿真

1. MATLAB 中 `cd` 到模型所在目录
2. 运行 `startup_setup.m` 添加路径
3. 打开 CarSim 生成的模型
4. 点击运行，CarSim S-Function 会自动调用 CarSim 求解器

### 4. 常见问题

| 问题 | 解决 |
|------|------|
| CarSim 找不到 MATLAB | 检查 Send to Simulink 中的路径是否正确 |
| Simulink 找不到 CarSim S-Function | 运行 CarSim 安装目录下的 `Simulink\Configure.m` |
| 模型版本不对 | R2016b 使用 `.mdl` 格式（不要用新版 `.slx`） |

### 5. 目录结构建议

```
matlab/carsim/
├── README.md             本文件
├── sim_setup.m           联合仿真配置脚本
├── my_simulation.par     CarSim 参数文件（.par）
└── results/              仿真结果输出
```

## 重要提醒

- CarSim 2019.0 与 MATLAB R2016b 兼容
- 在 CarSim 中配置仿真前，先在 MATLAB 中运行 `startup_setup.m`
- 联合仿真时，MATLAB 作为主控，CarSim 作为求解器后台运行
