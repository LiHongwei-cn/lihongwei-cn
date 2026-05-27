---
name: matlab-ai-generator
description: 根据用户提供的精确参数生成 MATLAB/Simulink 仿真代码。使用场景：用户要求生成 MATLAB 脚本、Simulink 模型、仿真代码，或要求修改现有仿真参数时自动触发。
---

# MATLAB-AI 代码生成器

根据用户提供的精确数值参数，生成兼容 R2016b 的 MATLAB/Simulink 仿真代码。

## 核心原则

1. **参数精确性**：用户提供的每个数值都必须精确使用，不允许 AI 自行假设或修改
2. **R2016b 兼容**：禁止使用 2017+ 函数（如 `rms`、`arguments`、`string`）
3. **向量化优先**：能用向量化操作的不用循环
4. **前向欧拉法**：数值积分使用显式欧拉法，不依赖隐式求解器

## 触发条件

当用户消息包含以下关键词时自动触发：
- 生成 MATLAB / 生成仿真 / 写一个 MATLAB 脚本
- Simulink 模型 / 搭建模型 / 自动生成模型
- 修改参数 / 调整参数 / 优化参数
- 仿真 / 仿真代码 / 仿真脚本

## 工作流程

### Step 1: 收集参数

向用户询问以下信息（如果用户未提供）：

**必填参数：**
- 仿真类型（动力学/电机控制/电池管理/能量管理/自定义）
- 关键物理参数（质量、电阻、电感、电容等）及其精确数值
- 仿真时间范围和步长
- 输入信号定义（阶跃/斜坡/正弦/自定义）

**可选参数：**
- 输出要求（绘图类型、数据导出格式）
- 性能指标要求（超调量、调节时间等）
- 特殊约束（R2016b 兼容、不含 Simulink 等）

### Step 2: 参数验证

在生成代码前，验证参数的物理合理性：

```matlab
% 参数验证示例
assert(param.m > 0, '质量必须为正数');
assert(param.Rs > 0, '电阻必须为正数');
assert(dt > 0 && dt < T, '步长必须在 (0, T) 范围内');
```

### Step 3: 生成代码

#### MATLAB 脚本模板

```matlab
%% [仿真名称]
% MATLAB R2016b 兼容
% 生成时间: [日期]
% 参数来源: 用户精确输入

clear; clc; close all;

%% 参数定义（用户精确值）
% [根据用户输入填充]

%% 仿真设置
dt = [用户值];    % 步长 [s]
T  = [用户值];    % 总时长 [s]
t  = 0:dt:T;
n  = length(t);

%% 初始化
% [根据仿真类型初始化状态变量]

%% 主仿真循环（前向欧拉法）
for i = 2:n
    % [状态更新方程]
end

%% 绘图
figure('Position', [100 100 800 600]);
% [根据用户要求绘图]

%% 输出结果
fprintf('===== 仿真结果 =====\n');
% [输出关键指标]
```

#### Simulink 模型生成模板

```matlab
%% 自动生成 Simulink 模型
% MATLAB R2016b 兼容

modelName = '[模型名称]';

% 检查是否已加载
if bdIsLoaded(modelName)
    close_system(modelName, 0);
end

% 创建新模型
new_system(modelName);
open_system(modelName);

% 添加模块
add_block('simulink/Sources/Step', [modelName '/Step']);
add_block('simulink/Continuous/Transfer Fcn', [modelName '/Plant']);
add_block('simulink/Sinks/Scope', [modelName '/Scope']);

% 设置参数（使用用户精确值）
set_param([modelName '/Step'], 'Value', '[用户值]');
set_param([modelName '/Plant'], 'Numerator', '[用户值]');
set_param([modelName '/Plant'], 'Denominator', '[用户值]');

% 连线
add_line(modelName, 'Step/1', 'Plant/1');
add_line(modelName, 'Plant/1', 'Scope/1');

% 仿真参数
set_param(modelName, 'StopTime', '[用户值]');
set_param(modelName, 'FixedStep', '[用户值]');

% 保存并运行
save_system(modelName);
sim(modelName);
```

## R2016b 兼容性

生成代码前必须检查兼容性。完整速查表见 `references/r2016b-compatibility.md`。

**禁止使用的函数：**
- `rms` → 使用 `sqrt(mean(x.^2))`
- `arguments` 块 → 使用 `nargin` 检查
- `string` 类型 → 使用 `char` 类型
- `tiledlayout` / `nexttile` → 使用 `subplot`
- `readtable` / `writetable` → 使用 `csvread` / `csvwrite`
- `datetime` → 使用 `datenum` / `datestr`
- `eval` / `evalc` / `evalin` → 使用动态字段名 `s.(name)`

**禁止使用的语法：**
- 隐式展开（R2016b+ 支持，但为兼容性避免）
- `arguments` 验证块
- 嵌套函数中的 `end` 关键字（某些情况）

**R2016b 图表渲染坑（用户踩过的坑，已验证）：**
- `%% ==========` 长分隔线注释会导致图表上出现垃圾文字 → 用短注释 `%% 节标题` 替代
- 多个独立 figure 不如一个 figure + subplot 整洁 → 相关图表合并到一张图
- figure 的 `'Name'` 属性不要用特殊字符

**图表标签规范（红线 — 用户明确要求）：**
- 所有 xlabel/ylabel/title/legend 必须用中文 — 用户原话："输出后的内容能使用中文的地方全部使用中文"
- 控制台输出（fprintf）同样用中文
- 代码注释也用中文
**文件编码红线（用户踩过的坑，已验证）：**
- 所有 .m 文件必须保存为 UTF-8 — GBK 编码在 macOS 上显示乱码
- UTF-8 在 Windows R2016b（中文 locale）上正常显示中文
- 如果从 Windows MATLAB 编辑器保存的文件是 GBK，需要用 `iconv -f GBK -t UTF-8` 转换
- macOS 终端 `grep` 无法正确显示 GBK 中文，用 `read_file` 工具读取
- **已验证**：17 个 .m 文件统一为 UTF-8 中文，在 Windows R2016b 上全部正常
- 示例：`xlabel('时间 [s]');` `ylabel('车速 [km/h]');` `title('纵向轨迹');` `legend('车辆','障碍物');`
- 控制台示例：`fprintf('===== 仿真结果 =====\n');` `fprintf('最高车速: %.1f km/h\n', max(v)*3.6);`
- **已验证**：所有 9 个仿真脚本 + ADAS HIL Demo 已统一为 UTF-8 中文输出，在 Windows R2016b 上正常显示

### Step 5: 输出格式

生成的代码文件结构：

```
[项目目录]/
├── [仿真名称].m           % 主仿真脚本
├── [仿真名称]_params.m    % 参数文件（可选）
├── [仿真名称]_simulink.slx % Simulink 模型（如需要）
└── README.md              % 使用说明
```

## 常用仿真类型模板

### 1. 纵向动力学

```matlab
%% 车辆纵向动力学仿真
% 参数
param.m   = [用户值];    % 整车质量 [kg]
param.Cd  = [用户值];    % 风阻系数
param.Af  = [用户值];    % 迎风面积 [m^2]
param.rho = 1.225;       % 空气密度 [kg/m^3]
param.f   = [用户值];    % 滚动阻力系数
param.g   = 9.81;        % 重力加速度 [m/s^2]

% 阻力计算函数
function Fresist = calcResist(v, param)
    Fair = 0.5 * param.rho * param.Cd * param.Af * v^2;
    Froll = param.f * param.m * param.g;
    Fresist = Fair + Froll;
end
```

### 2. 电机 FOC 控制

```matlab
%% PMSM FOC 控制仿真
% 电机参数
pmsm.Rs  = [用户值];    % 定子电阻 [Ohm]
pmsm.Ld  = [用户值];    % d轴电感 [H]
pmsm.Lq  = [用户值];    % q轴电感 [H]
pmsm.psi = [用户值];    % 永磁磁链 [Wb]
pmsm.P   = [用户值];    % 极对数
pmsm.J   = [用户值];    % 转动惯量 [kg.m^2]

% PI 参数
Kp_i = [用户值];        % 电流环比例增益
Ki_i = [用户值];        % 电流环积分增益
Kp_s = [用户值];        % 速度环比例增益
Ki_s = [用户值];        % 速度环积分增益
```

### 3. 电池 SOC 估算

```matlab
%% 电池 SOC 估算（EKF）
% 电池参数
battery.Vnom  = [用户值];  % 标称电压 [V]
battery.Qnom  = [用户值];  % 标称容量 [Ah]
battery.R0    = [用户值];  % 欧姆内阻 [Ohm]
battery.R1    = [用户值];  % 极化内阻 [Ohm]
battery.C1    = [用户值];  % 极化电容 [F]

% EKF 参数
ekf.Q = [用户值];          % 过程噪声协方差
ekf.R = [用户值];          % 测量噪声协方差
ekf.P0 = [用户值];         % 初始状态协方差
```

### 4. 能量管理策略

```matlab
%% 能量管理策略仿真
% 整车参数
param.m = [用户值];        % 整车质量 [kg]
param.P_motor = [用户值];  % 驱动电机功率 [kW]
param.P_rex = [用户值];    % 增程器功率 [kW]
param.Q_batt = [用户值];   % 电池容量 [Ah]
param.V_batt = [用户值];   % 电池电压 [V]

% 策略参数
SOC_min = [用户值];        % SOC 下限
SOC_max = [用户值];        % SOC 上限
P_rex_on = [用户值];       % 增程器开启阈值
P_rex_off = [用户值];      % 增程器关闭阈值
```

## 错误处理

### 常见错误及解决方案

1. **参数单位错误**
   - 检查单位一致性（如 kW vs W，rpm vs rad/s）
   - 提供单位转换函数

2. **数值不稳定**
   - 减小步长 dt
   - 检查状态方程是否正确
   - 添加数值限幅

3. **R2016b 不兼容**
   - 替换为兼容函数
   - 使用 `nargin` 替代 `arguments`
   - 使用 `subplot` 替代 `tiledlayout`

## 使用示例

**用户输入：**
```
生成一个电机 FOC 控制仿真，参数如下：
- 定子电阻 Rs = 0.958 Ohm
- d轴电感 Ld = 5.25 mH
- q轴电感 Lq = 5.25 mH
- 永磁磁链 ψ = 0.1827 Wb
- 极对数 P = 4
- 转动惯量 J = 0.003 kg.m^2
- 仿真时间 0.5s，步长 0.0001s
- 速度环 Kp=0.5, Ki=10
- 电流环 Kp=100, Ki=2000
```

**AI 输出：**
```matlab
%% PMSM 永磁同步电机 FOC 控制仿真
% MATLAB R2016b 兼容
% 参数来源: 用户精确输入

clear; clc; close all;

%% 电机参数（用户精确值）
pmsm.Rs  = 0.958;      % 定子电阻 [Ohm]
pmsm.Ld  = 0.00525;    % d轴电感 [H] (5.25 mH)
pmsm.Lq  = 0.00525;    % q轴电感 [H] (5.25 mH)
pmsm.psi = 0.1827;     % 永磁磁链 [Wb]
pmsm.P   = 4;          % 极对数
pmsm.J   = 0.003;      % 转动惯量 [kg.m^2]

%% 控制参数（用户精确值）
Ts = 0.0001;           % 仿真步长 [s] (10kHz)
T  = 0.5;              % 总时长 [s]
t  = 0:Ts:T;
n  = length(t);

% PI 参数 (电流环)
Kp_i = 100;
Ki_i = 2000;

% PI 参数 (速度环)
Kp_s = 0.5;
Ki_s = 10;

% ... [后续代码]
```

## 铁律（用户多次纠正）

1. **全中文输出**：所有 xlabel/ylabel/title/legend/fprintf 必须中文。代码注释必须中文。英文只允许在代码变量名中。
2. **单图布局**：所有子图合并到一张 figure，用 `subplot(M,N,n)` 排列，不生成多个独立 figure。
3. **批量修复**：用户说"修复这个文件的中文"时，必须检查并修复所有同目录下的 .m 文件，不只修被提到的那一个。
4. **UTF-8 编码**：所有 .m 文件必须 UTF-8。Windows MATLAB R2016b 保存的 GBK 文件需重写为 UTF-8。用 `file xxx.m` 验证编码。
5. **参数集中**：所有仿真参数定义在主脚本顶部，函数通过 struct 接收参数，不在函数内部硬编码。

## 编码陷阱（pitfall）

Windows MATLAB R2016b 默认用 GBK 编码保存中文。macOS 上 `file` 命令显示 `ISO-8859 text`。在 macOS 上编辑后需确认编码为 `UTF-8 text`。Claude Code 重写文件时自动使用 UTF-8。

## Claude Code 委托注意事项

- 大批量文件重写（>5 个 .m 文件）容易超时（600s 限制）
- 拆分为每批 4-5 个文件，分多次调用
- 用 `file *.m` 验证所有文件编码一致性

## References

- `references/r2016b-compatibility.md`

## 参考文件

- `references/r2016b-compatibility.md` — R2016b 兼容性速查表（禁止函数、替代方案、Simulink API）
- `references/project-deletion-checklist.md` — 删除项目时的全量清理清单（grep 全仓库、验证零残留）
- `references/matlab-project-structure.md` — 仿真项目结构规范（文件组织、参数传递、绘图、测试用例、编码）
- `references/hil-demo-architecture.md` — ADAS HIL 测试 Demo 架构参考（文件结构、参数传递、测试用例模板）
- `references/project-consolidation.md` — 多项目合并指南（合并决策、引用清理、真实案例）
- `references/matlab-encoding.md` — 文件编码规范（UTF-8 vs GBK，跨平台兼容）
- `references/matlab-chinese-output.md` — 全中文输出规范（标签速查、报告模板、图表合并）

## 相关技能

- `matlab-simulink-generator` — Simulink 模型自动生成

## 注意事项

1. **绝不修改用户提供的参数值** - 即使用户提供的参数可能导致仿真不稳定，也应按原值生成代码，同时给出警告
2. **保持代码简洁** - 不添加用户未要求的功能
3. **注释清晰** - 每个参数都标注单位和物理意义
4. **输出完整** - 包含绘图和结果输出
5. **文件命名** - 使用 `snake_case.m` 格式
6. **多图合并** — 相关图表用 subplot 合并到一个 figure，不单独弹窗。已验证：ADAS HIL Demo 8 个子图合并为 1 张大图（4行2列），用户明确要求"所有的图表内容放在一起"
7. **参数集中** — 所有仿真参数集中在主脚本顶部，通过 struct 传入函数，不在函数内部硬编码
8. **跨函数参数传递** — 函数签名统一为 `函数名(数据, 参数结构体)`，参数结构体在主脚本定义
