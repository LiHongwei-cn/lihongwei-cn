%% 直流电机 PWM 调速 Simulink 模型（自动搭建，独立版）
% MATLAB R2016b + Simulink 兼容
% 运行此脚本自动生成并打开模型
% 注意：此模型使用简化电机+负载模型（Transfer Fcn）

clear; clc;

model = 'dc_motor_speed_control';

% 关闭已存在的同名模型
if bdIsLoaded(model)
    close_system(model, 0);
end

new_system(model);
open_system(model);

%% 电机参数（脚本变量，供初始化回调使用）
Ra = 0.5;      % 电枢电阻 [Ohm]
La = 0.003;    % 电枢电感 [H]
Ke = 0.05;     % 反电动势系数 [V/(rad/s)]
Kt = 0.05;     % 转矩系数 [Nm/A]
J  = 0.01;     % 转动惯量 [kg.m^2]
B  = 0.001;    % 阻尼系数 [Nm/(rad/s)]
Vdc = 48;      % 直流母线电压 [V]

%% PI 参数
Kp = 0.8;
Ki = 5.0;

%% ========== 搭建模型 ==========

% --- 速度参考（Step：0-0.3s 为 0，之后跳到 100 rad/s）---
add_block('simulink/Sources/Step', [model '/Speed Ref']);
set_param([model '/Speed Ref'], ...
    'Time', '0.3', ...
    'Before', '0', ...
    'After', '100');

% --- PI 控制器 ---
% 比例
add_block('simulink/Commonly Used Blocks/Gain', [model '/Kp']);
set_param([model '/Kp'], 'Gain', 'Kp');
% 积分增益
add_block('simulink/Commonly Used Blocks/Gain', [model '/Ki Gain']);
set_param([model '/Ki Gain'], 'Gain', 'Ki');
% 积分器
add_block('simulink/Commonly Used Blocks/Integrator', [model '/Ki Integrator']);
% PI 求和
add_block('simulink/Commonly Used Blocks/Sum', [model '/PI Sum']);
set_param([model '/PI Sum'], 'Inputs', '|++');

% --- 速度误差（参考 - 实际）---
add_block('simulink/Commonly Used Blocks/Sum', [model '/Speed Error']);
set_param([model '/Speed Error'], 'Inputs', '|+-');

% --- 饱和限幅（占空比限幅）---
add_block('simulink/Commonly Used Blocks/Saturation', [model '/Duty Limit']);
set_param([model '/Duty Limit'], 'UpperLimit', '1', 'LowerLimit', '-1');

% --- PWM 增益（占空比 → 电压）---
add_block('simulink/Commonly Used Blocks/Gain', [model '/Vdc']);
set_param([model '/Vdc'], 'Gain', 'Vdc');

% --- 电枢电气环节 1/(La*s + Ra) ---
add_block('simulink/Continuous/Transfer Fcn', [model '/Electrical']);
set_param([model '/Electrical'], ...
    'Numerator', '[1]', ...
    'Denominator', '[La Ra]');

% --- 转矩常数 Kt ---
add_block('simulink/Commonly Used Blocks/Gain', [model '/Kt']);
set_param([model '/Kt'], 'Gain', 'Kt');

% --- 负载转矩（Constant，初始为 0）---
add_block('simulink/Sources/Constant', [model '/Load Torque']);
set_param([model '/Load Torque'], 'Value', '0');

% --- 净转矩（电磁 - 负载）---
add_block('simulink/Commonly Used Blocks/Sum', [model '/Torque Sum']);
set_param([model '/Torque Sum'], 'Inputs', '|+-');

% --- 机械环节 1/(J*s + B) ---
add_block('simulink/Continuous/Transfer Fcn', [model '/Mechanical']);
set_param([model '/Mechanical'], ...
    'Numerator', '[1]', ...
    'Denominator', '[J B]');

% --- 反电动势 Ke ---
add_block('simulink/Commonly Used Blocks/Gain', [model '/Ke']);
set_param([model '/Ke'], 'Gain', 'Ke');

% --- 转速显示（rad/s → rpm）---
add_block('simulink/Commonly Used Blocks/Gain', [model '/rpm']);
set_param([model '/rpm'], 'Gain', '30/pi');

% --- 示波器 ---
add_block('simulink/Sinks/Scope', [model '/Scope']);
set_param([model '/Scope'], ...
    'NumInputPorts', '3', ...
    'Position', [700 100 950 400]);

% --- 布局 ---
set_param([model '/Speed Ref'],     'Position', [30  180 70  210]);
set_param([model '/Speed Error'],   'Position', [130 180 170 220]);
set_param([model '/Kp'],            'Position', [230 130 270 170]);
set_param([model '/Ki Gain'],       'Position', [230 190 270 230]);
set_param([model '/Ki Integrator'], 'Position', [330 200 370 240]);
set_param([model '/PI Sum'],        'Position', [330 150 370 210]);
set_param([model '/Duty Limit'],    'Position', [430 160 470 200]);
set_param([model '/Vdc'],           'Position', [530 160 570 200]);
set_param([model '/Electrical'],    'Position', [630 155 690 205]);
set_param([model '/Kt'],            'Position', [560 310 600 350]);
set_param([model '/Load Torque'],   'Position', [560 390 600 430]);
set_param([model '/Torque Sum'],    'Position', [660 340 700 380]);
set_param([model '/Mechanical'],    'Position', [760 328 820 372]);
set_param([model '/Ke'],            'Position', [860 260 900 300]);
set_param([model '/rpm'],           'Position', [860 360 900 400]);
set_param([model '/Scope'],         'Position', [700 100 950 400]);

%% ========== 连线 ==========

% Speed Ref → Error (+)
add_line(model, 'Speed Ref/1', 'Speed Error/1');

% 机械输出 → Error (-)
add_line(model, 'Mechanical/1', 'Speed Error/2');

% Error → Kp & Ki Gain
add_line(model, 'Speed Error/1', 'Kp/1');
add_line(model, 'Speed Error/1', 'Ki Gain/1');
add_line(model, 'Ki Gain/1', 'Ki Integrator/1');

% Kp, Ki Integrator → PI Sum
add_line(model, 'Kp/1', 'PI Sum/1');
add_line(model, 'Ki Integrator/1', 'PI Sum/2');

% PI Sum → Duty Limit → Vdc
add_line(model, 'PI Sum/1', 'Duty Limit/1');
add_line(model, 'Duty Limit/1', 'Vdc/1');

% Vdc → Electrical → Kt
add_line(model, 'Vdc/1', 'Electrical/1');

% 转速 → Ke (反馈用)
add_line(model, 'Mechanical/1', 'Ke/1');
% Ke 反馈到 Electrical 输入端 —— 用 Sum 做减法
% 在 Electrical 前插入反电动势减法 == 把 Ke 输出作为负反馈
% 简化：直接用 Sum
delete_line(model, 'Vdc/1', 'Electrical/1');

add_block('simulink/Commonly Used Blocks/Sum', [model '/Back EMF']);
set_param([model '/Back EMF'], 'Inputs', '|+-');
set_param([model '/Back EMF'], 'Position', [580 150 610 190]);

add_line(model, 'Vdc/1', 'Back EMF/1');
add_line(model, 'Ke/1', 'Back EMF/2');
add_line(model, 'Back EMF/1', 'Electrical/1');

% Electrical 输出 → 电流分支
add_line(model, 'Electrical/1', 'Kt/1');

% Kt → Torque Sum (+), Load Torque → Torque Sum (-)
add_line(model, 'Kt/1', 'Torque Sum/1');
add_line(model, 'Load Torque/1', 'Torque Sum/2');

% Torque Sum → Mechanical
add_line(model, 'Torque Sum/1', 'Mechanical/1');

% Mechanical → rpm
add_line(model, 'Mechanical/1', 'rpm/1');

% 到 Scope：速度参考、实际转速(rpm)、电流
add_block('simulink/Signal Routing/Mux', [model '/Mux']);
set_param([model '/Mux'], 'Inputs', '3');
set_param([model '/Mux'], 'Position', [950 160 970 210]);

add_line(model, 'Speed Ref/1', 'Mux/1');
add_line(model, 'rpm/1', 'Mux/2');
add_line(model, 'Electrical/1', 'Mux/3');
add_line(model, 'Mux/1', 'Scope/1');

%% 配置 & 保存
set_param(model, 'Solver', 'ode45', 'StopTime', '2');
set_param(model, 'StartTime', '0.0');
save_system(model);

fprintf('===== Simulink Model Generated =====\n');
fprintf('Model name: %s\n', model);
fprintf('Double-click Scope to view: speed ref / actual speed (rpm) / armature current (A)\n');
fprintf('Modify PI params: double-click Kp, Ki Integrator blocks\n');
