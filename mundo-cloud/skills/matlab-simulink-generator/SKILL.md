---
name: matlab-simulink-generator
description: 自动生成 Simulink 模型（.slx 文件）。使用场景：用户要求生成 Simulink 模型、搭建仿真模型、创建控制系统模型时自动触发。兼容 R2016b。
---

# Simulink 模型自动生成器

根据用户提供的精确参数，自动生成 Simulink 模型文件（.slx）。

## 核心原则

1. **R2016b 兼容**：使用 `add_block`、`add_line` 等基础 API
2. **参数精确**：用户提供的每个数值都必须精确设置到模块参数中
3. **自动连线**：根据模块类型自动连接信号线
4. **仿真就绪**：生成后可直接运行

## 触发条件

当用户消息包含以下关键词时自动触发：
- Simulink 模型 / 搭建模型 / 生成模型
- 控制系统 / 反馈系统 / 闭环系统
- 传递函数 / 状态空间 / 框图

## 工作流程

### Step 1: 收集模型信息

向用户询问以下信息：

**必填信息：**
- 模型类型（控制系统/动力学/信号处理/自定义）
- 模块组成（输入源、被控对象、控制器、输出等）
- 各模块的精确参数值
- 仿真时间范围和步长

**可选信息：**
- 模型名称
- 是否需要 Scope 显示
- 是否需要数据导出到 Workspace

### Step 2: 生成 Simulink 模型脚本

使用 MATLAB 脚本自动创建 Simulink 模型：

```matlab
%% 自动生成 Simulink 模型
% MATLAB R2016b 兼容
% 生成时间: [日期]

modelName = '[模型名称]';

% 检查并关闭已打开的模型
if bdIsLoaded(modelName)
    close_system(modelName, 0);
end

% 创建新模型
new_system(modelName);
open_system(modelName);

% ========== 添加模块 ==========

% 输入源
add_block('simulink/Sources/Step', [modelName '/Reference']);
set_param([modelName '/Reference'], ...
    'Time', '[用户值]', ...
    'Before', '[用户值]', ...
    'After', '[用户值]');

% 控制器
add_block('simulink/Continuous/Transfer Fcn', [modelName '/Controller']);
set_param([modelName '/Controller'], ...
    'Numerator', '[用户值]', ...
    'Denominator', '[用户值]');

% 被控对象
add_block('simulink/Continuous/Transfer Fcn', [modelName '/Plant']);
set_param([modelName '/Plant'], ...
    'Numerator', '[用户值]', ...
    'Denominator', '[用户值]');

% 输出
add_block('simulink/Sinks/Scope', [modelName '/Scope']);
add_block('simulink/Sinks/To Workspace', [modelName '/ToWorkspace']);
set_param([modelName '/ToWorkspace'], ...
    'VariableName', 'simout', ...
    'SaveFormat', 'Timeseries');

% ========== 连接信号线 ==========

% 参考输入 -> 求和点
add_line(modelName, 'Reference/1', 'Sum/1');

% 求和点 -> 控制器
add_line(modelName, 'Sum/1', 'Controller/1');

% 控制器 -> 被控对象
add_line(modelName, 'Controller/1', 'Plant/1');

% 被控对象 -> 输出
add_line(modelName, 'Plant/1', 'Scope/1');
add_line(modelName, 'Plant/1', 'ToWorkspace/1');

% 反馈回路
add_line(modelName, 'Plant/1', 'Sum/2');

% ========== 仿真参数 ==========

set_param(modelName, ...
    'StopTime', '[用户值]', ...
    'FixedStep', '[用户值]', ...
    'Solver', 'ode4', ...
    'SimulationMode', 'Normal');

% ========== 保存并运行 ==========

save_system(modelName);
fprintf('模型已生成: %s.slx\n', modelName);

% 运行仿真
sim(modelName);
fprintf('仿真完成\n');
```

### Step 3: 常用模块库

#### 输入源模块

| 模块 | 库路径 | 用途 |
|------|--------|------|
| Step | simulink/Sources/Step | 阶跃输入 |
| Ramp | simulink/Sources/Ramp | 斜坡输入 |
| Sine Wave | simulink/Sources/Sine Wave | 正弦输入 |
| Clock | simulink/Sources/Clock | 时间信号 |
| From Workspace | simulink/Sources/From Workspace | 从 MATLAB 工作区读取 |

#### 连续系统模块

| 模块 | 库路径 | 用途 |
|------|--------|------|
| Transfer Fcn | simulink/Continuous/Transfer Fcn | 传递函数 |
| State-Space | simulink/Continuous/State-Space | 状态空间 |
| Integrator | simulink/Continuous/Integrator | 积分器 |
| Derivative | simulink/Continuous/Derivative | 微分器 |
| PID Controller | simulink/Continuous/PID Controller | PID 控制器 |

#### 离散系统模块

| 模块 | 库路径 | 用途 |
|------|--------|------|
| Discrete Transfer Fcn | simulink/Discrete/Discrete Transfer Fcn | 离散传递函数 |
| Discrete State-Space | simulink/Discrete/Discrete State-Space | 离散状态空间 |
| Unit Delay | simulink/Discrete/Unit Delay | 单位延迟 |

#### 数学运算模块

| 模块 | 库路径 | 用途 |
|------|--------|------|
| Sum | simulink/Math Operations/Sum | 求和 |
| Gain | simulink/Math Operations/Gain | 增益 |
| Product | simulink/Math Operations/Product | 乘积 |
| Math Function | simulink/Math Operations/Math Function | 数学函数 |

#### 输出模块

| 模块 | 库路径 | 用途 |
|------|--------|------|
| Scope | simulink/Sinks/Scope | 示波器 |
| Display | simulink/Sinks/Display | 数值显示 |
| To Workspace | simulink/Sinks/To Workspace | 输出到工作区 |
| To File | simulink/Sinks/To File | 输出到文件 |

### Step 4: 常见模型模板

#### 1. 闭环控制系统

```matlab
% 模型结构: Reference -> Sum -> Controller -> Plant -> Output
%                                 <- Feedback <-

modelName = 'closed_loop_control';

% 添加模块
add_block('simulink/Sources/Step', [modelName '/Ref']);
add_block('simulink/Math Operations/Sum', [modelName '/Sum']);
add_block('simulink/Continuous/Transfer Fcn', [modelName '/Controller']);
add_block('simulink/Continuous/Transfer Fcn', [modelName '/Plant']);
add_block('simulink/Sinks/Scope', [modelName '/Scope']);

% 设置求和点
set_param([modelName '/Sum'], 'Inputs', '+-');

% 连线
add_line(modelName, 'Ref/1', 'Sum/1');
add_line(modelName, 'Sum/1', 'Controller/1');
add_line(modelName, 'Controller/1', 'Plant/1');
add_line(modelName, 'Plant/1', 'Scope/1');
add_line(modelName, 'Plant/1', 'Sum/2');  % 反馈
```

#### 2. 电机控制系统

```matlab
% 模型结构: Speed Ref -> Speed PI -> Current PI -> Motor -> Output
%                               <- Speed Feedback <
%                          <- Current Feedback <

modelName = 'motor_control';

% 添加模块
add_block('simulink/Sources/Step', [modelName '/SpeedRef']);
add_block('simulink/Continuous/PID Controller', [modelName '/SpeedPI']);
add_block('simulink/Continuous/PID Controller', [modelName '/CurrentPI']);
add_block('simulink/Continuous/Transfer Fcn', [modelName '/Motor']);
add_block('simulink/Sinks/Scope', [modelName '/Scope']);

% 设置 PID 参数
set_param([modelName '/SpeedPI'], 'P', '[用户值]', 'I', '[用户值]');
set_param([modelName '/CurrentPI'], 'P', '[用户值]', 'I', '[用户值]');

% 设置电机参数
set_param([modelName '/Motor'], ...
    'Numerator', '[用户值]', ...
    'Denominator', '[用户值]');

% 连线
add_line(modelName, 'SpeedRef/1', 'SpeedPI/1');
add_line(modelName, 'SpeedPI/1', 'CurrentPI/1');
add_line(modelName, 'CurrentPI/1', 'Motor/1');
add_line(modelName, 'Motor/1', 'Scope/1');
add_line(modelName, 'Motor/1', 'SpeedPI/2');  % 速度反馈
```

#### 3. 电池 SOC 模型

```matlab
% 模型结构: Current -> Battery Model -> Voltage
%                    -> SOC Estimator -> SOC

modelName = 'battery_soc';

% 添加模块
add_block('simulink/Sources/From Workspace', [modelName '/Current']);
add_block('simulink/Continuous/Integrator', [modelName '/SOC_Integrator']);
add_block('simulink/Math Operations/Gain', [modelName '/Capacity_Gain']);
add_block('simulink/Sinks/Scope', [modelName '/Scope']);

% 设置参数
set_param([modelName '/Current'], 'VariableName', 'I_load');
set_param([modelName '/Capacity_Gain'], 'Gain', '1/[用户值]');  % 1/Q_nom

% 连线
add_line(modelName, 'Current/1', 'Capacity_Gain/1');
add_line(modelName, 'Capacity_Gain/1', 'SOC_Integrator/1');
add_line(modelName, 'SOC_Integrator/1', 'Scope/1');
```

### Step 5: R2016b 兼容性

**必须使用的 API：**
- `new_system` / `open_system` / `save_system`
- `add_block` / `add_line`
- `set_param` / `get_param`
- `bdIsLoaded` / `close_system`

**禁止使用的 API：**
- `Simulink.ModelAdvisor` (R2018a+)
- `sltest.testmanager` (R2017a+)
- `Simulink.sdi` 某些方法 (R2017a+)

### Step 6: 验证与测试

生成模型后，自动执行以下验证：

```matlab
% 验证模型是否正确加载
assert(bdIsLoaded(modelName), '模型未正确加载');

% 验证模块是否存在
assert(~isempty(find_system(modelName, 'Name', 'Reference')), 'Reference 模块缺失');

% 验证连线是否完整
lineCount = length(find_system(modelName, 'FindAll', 'on', 'Type', 'line'));
assert(lineCount > 0, '模型无连线');

% 运行仿真验证
try
    sim(modelName);
    fprintf('仿真运行成功\n');
catch ME
    fprintf('仿真失败: %s\n', ME.message);
end
```

## R2016b 兼容性参考

详细兼容性速查表见 `matlab-ai-generator` skill 的 `references/r2016b-compatibility.md`。

## 常见问题

### 1. 模块找不到

**问题：** `add_block` 报错找不到模块

**解决：** 使用完整库路径，如 `simulink/Sources/Step` 而非 `Step`

### 2. 参数设置失败

**问题：** `set_param` 报错参数不存在

**解决：** 使用 `get_param(block, 'DialogParameters')` 查看可用参数

### 3. 连线失败

**问题：** `add_line` 报错端口不存在

**解决：** 使用 `get_param(block, 'PortHandles')` 查看端口句柄

### 4. 仿真失败

**问题：** 仿真运行报错

**解决：** 检查模块参数是否正确，特别是传递函数的分子分母

## 输出格式

生成的文件：

```
[模型名称].m      % 生成脚本（可重复运行）
[模型名称].slx    % Simulink 模型文件
```

## 使用示例

**用户输入：**
```
生成一个 PID 控制的电机调速 Simulink 模型：
- 电机传递函数: 1/(0.003s + 0.0001)
- PID 参数: Kp=10, Ki=100, Kd=0
- 仿真时间: 1s
- 步长: 0.001s
```

**AI 输出：**
```matlab
%% 自动生成 Simulink 模型: motor_pid_control
% MATLAB R2016b 兼容

modelName = 'motor_pid_control';

% 创建模型
new_system(modelName);
open_system(modelName);

% 添加模块
add_block('simulink/Sources/Step', [modelName '/SpeedRef']);
set_param([modelName '/SpeedRef'], 'Time', '0', 'Before', '0', 'After', '1000');

add_block('simulink/Math Operations/Sum', [modelName '/Sum']);
set_param([modelName '/Sum'], 'Inputs', '+-');

add_block('simulink/Continuous/PID Controller', [modelName '/PID']);
set_param([modelName '/PID'], 'P', '10', 'I', '100', 'D', '0');

add_block('simulink/Continuous/Transfer Fcn', [modelName '/Motor']);
set_param([modelName '/Motor'], 'Numerator', '1', 'Denominator', '[0.003 0.0001]');

add_block('simulink/Sinks/Scope', [modelName '/Scope']);

% 连线
add_line(modelName, 'SpeedRef/1', 'Sum/1');
add_line(modelName, 'Sum/1', 'PID/1');
add_line(modelName, 'PID/1', 'Motor/1');
add_line(modelName, 'Motor/1', 'Scope/1');
add_line(modelName, 'Motor/1', 'Sum/2');

% 仿真参数
set_param(modelName, 'StopTime', '1', 'FixedStep', '0.001', 'Solver', 'ode4');

% 保存并运行
save_system(modelName);
sim(modelName);
```

## 参考文件

- 参见 `matlab-ai-generator` skill 的 `references/r2016b-compatibility.md` 获取 R2016b 兼容性速查表
- `references/carsim-project-template.md` — CarSim 仿真项目模板（目录结构、文件格式、API）

## 注意事项

1. **模块库路径必须完整** - 使用 `simulink/Sources/Step` 而非 `Step`
2. **参数名必须正确** - 使用 `get_param` 查看可用参数
3. **连线顺序重要** - 先添加所有模块，再连线
4. **仿真前保存** - 使用 `save_system` 保存模型
5. **错误处理** - 使用 `try-catch` 捕获仿真错误
