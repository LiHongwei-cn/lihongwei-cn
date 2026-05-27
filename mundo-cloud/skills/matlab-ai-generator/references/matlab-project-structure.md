# MATLAB 仿真项目结构规范

## 文件结构

```
matlab/examples/
├── [仿真名].m                    单文件仿真（简单场景）
├── [仿真名]_demo/                多文件仿真（复杂场景如 ADAS HIL）
│   ├── main_[仿真名].m           主脚本（参数+循环+报告+调用绘图）
│   ├── [模块1].m                 独立功能模块
│   ├── [模块2].m
│   ├── visualize_results.m       绘图（所有图合并到一个 figure）
│   └── README.md                 使用说明
├── utils/                        工具函数（FFT、滤波、RMS）
├── startup_setup.m               路径初始化
└── test_all.m                    批量自测
```

## 主脚本规范

参数集中在脚本顶部，不在函数内部硬编码：
```matlab
%% 参数定义
m = 1500;       % 整车质量 [kg]
Cd = 0.32;      % 风阻系数
dt = 0.01;      % 步长 [s]
T = 5;          % 总时长 [s]
```

函数通过 struct 接收参数，不读取 workspace：
```matlab
params.m = m; params.Cd = Cd;
[out1, out2] = my_function(input, params, dt);
```

## 绘图规范

- 所有图合并到一个 figure：`figure('Name','结果','NumberTitle','off','Units','normalized','Position',[0.05 0.05 0.9 0.85])`
- 用 `subplot(m,n,idx)` 排列
- 标签全部中文：`xlabel('时间 [s]')`、`ylabel('车速 [km/h]')`
- 不用 `%% ==========` 分隔线（R2016b 渲染问题）

## 测试用例规范

HIL 测试框架结构：
```matlab
results = struct('name', {}, 'passed', {}, 'detail', {});
results(1).name = '正常行驶 (前0.5秒无警告)';
results(1).passed = ~any(early_warnings);
results(1).detail = sprintf('FCW=%d AEB=%d', fcw, aeb);
```

控制台报告：
```matlab
fprintf('===== 测试报告 =====\n');
fprintf('  测试%d  %-30s [%s]\n', i, results(i).name, status);
fprintf('  结果: %d/%d 通过\n', n_pass, n_total);
```

## 编码规范

- 文件编码：UTF-8（不使用 GBK）
- 注释语言：中文
- 输出语言：中文（xlabel/ylabel/title/legend/fprintf）
- 命名：snake_case
- R2016b 兼容：无 rms/arguments/string/tiledlayout
