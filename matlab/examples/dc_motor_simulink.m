%% 直流电机 PWM 调速 Simulink 模型（自动搭建完整版）
% 功能：自动生成直流电机 PI 转速闭环 Simulink 模型
% 兼容版本：MATLAB R2016b + Simulink
% 运行本脚本自动创建并搭建完整的仿真模型

clc; close all;

model = 'dc_motor_speed_control';

if bdIsLoaded(model)
    close_system(model, 0);
end

new_system(model);
open_system(model);

%% 电机参数
Ra = 0.5;                    % 电枢电阻 [Ohm]
La = 0.003;                  % 电枢电感 [H]
Ke = 0.05;                   % 反电动势系数 [V*s/rad]
Kt = 0.05;                   % 转矩系数 [Nm/A]
J = 0.01;                    % 转动惯量 [kg*m^2]
B = 0.001;                   % 摩擦系数 [Nm*s/rad]
Vdc = 48;                    % 直流母线电压 [V]

%% PI 控制器参数
Kp = 0.8;                    % 比例增益
Ki = 5.0;                    % 积分增益

%% ========== 搭建模型 ==========

% 转速参考输入
add_block('simulink/Sources/Step', [model '/Speed Ref']);
set_param([model '/Speed Ref'], 'Time', '0.3', 'Before', '0', 'After', '100');

% PI 控制器模块
add_block('simulink/Commonly Used Blocks/Gain', [model '/Kp']);
set_param([model '/Kp'], 'Gain', 'Kp');

add_block('simulink/Commonly Used Blocks/Gain', [model '/Ki Gain']);
set_param([model '/Ki Gain'], 'Gain', 'Ki');

add_block('simulink/Commonly Used Blocks/Integrator', [model '/Ki Integrator']);

add_block('simulink/Commonly Used Blocks/Sum', [model '/PI Sum']);
set_param([model '/PI Sum'], 'Inputs', '|++');

add_block('simulink/Commonly Used Blocks/Sum', [model '/Speed Error']);
set_param([model '/Speed Error'], 'Inputs', '|+-');

add_block('simulink/Commonly Used Blocks/Saturation', [model '/Duty Limit']);
set_param([model '/Duty Limit'], 'UpperLimit', '1', 'LowerLimit', '-1');

% 电气子系统
add_block('simulink/Commonly Used Blocks/Gain', [model '/Vdc']);
set_param([model '/Vdc'], 'Gain', 'Vdc');

add_block('simulink/Continuous/Transfer Fcn', [model '/Electrical']);
set_param([model '/Electrical'], 'Numerator', '[1]', 'Denominator', '[La Ra]');

% 机械子系统
add_block('simulink/Commonly Used Blocks/Gain', [model '/Kt']);
set_param([model '/Kt'], 'Gain', 'Kt');

add_block('simulink/Sources/Constant', [model '/Load Torque']);
set_param([model '/Load Torque'], 'Value', '0');

add_block('simulink/Commonly Used Blocks/Sum', [model '/Torque Sum']);
set_param([model '/Torque Sum'], 'Inputs', '|+-');

add_block('simulink/Continuous/Transfer Fcn', [model '/Mechanical']);
set_param([model '/Mechanical'], 'Numerator', '[1]', 'Denominator', '[J B]');

% 反馈回路
add_block('simulink/Commonly Used Blocks/Gain', [model '/Ke']);
set_param([model '/Ke'], 'Gain', 'Ke');

add_block('simulink/Commonly Used Blocks/Gain', [model '/rpm']);
set_param([model '/rpm'], 'Gain', '30/pi');

% 示波器
add_block('simulink/Sinks/Scope', [model '/Scope']);
set_param([model '/Scope'], 'NumInputPorts', '3', 'Position', [700 100 950 400]);

%% 布局
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
add_line(model, 'Speed Ref/1', 'Speed Error/1');
add_line(model, 'Mechanical/1', 'Speed Error/2');
add_line(model, 'Speed Error/1', 'Kp/1');
add_line(model, 'Speed Error/1', 'Ki Gain/1');
add_line(model, 'Ki Gain/1', 'Ki Integrator/1');
add_line(model, 'Kp/1', 'PI Sum/1');
add_line(model, 'Ki Integrator/1', 'PI Sum/2');
add_line(model, 'PI Sum/1', 'Duty Limit/1');
add_line(model, 'Duty Limit/1', 'Vdc/1');
add_line(model, 'Vdc/1', 'Electrical/1');

add_line(model, 'Mechanical/1', 'Ke/1');

delete_line(model, 'Vdc/1', 'Electrical/1');

add_block('simulink/Commonly Used Blocks/Sum', [model '/Back EMF']);
set_param([model '/Back EMF'], 'Inputs', '|+-');
set_param([model '/Back EMF'], 'Position', [580 150 610 190]);

add_line(model, 'Vdc/1', 'Back EMF/1');
add_line(model, 'Ke/1', 'Back EMF/2');
add_line(model, 'Back EMF/1', 'Electrical/1');

add_line(model, 'Electrical/1', 'Kt/1');
add_line(model, 'Kt/1', 'Torque Sum/1');
add_line(model, 'Load Torque/1', 'Torque Sum/2');
add_line(model, 'Torque Sum/1', 'Mechanical/1');
add_line(model, 'Mechanical/1', 'rpm/1');

add_block('simulink/Signal Routing/Mux', [model '/Mux']);
set_param([model '/Mux'], 'Inputs', '3');
set_param([model '/Mux'], 'Position', [950 160 970 210]);

add_line(model, 'Speed Ref/1', 'Mux/1');
add_line(model, 'rpm/1', 'Mux/2');
add_line(model, 'Electrical/1', 'Mux/3');
add_line(model, 'Mux/1', 'Scope/1');

%% 求解器设置并保存
set_param(model, 'Solver', 'ode45', 'StopTime', '2');
set_param(model, 'StartTime', '0.0');
save_system(model);

%% 输出结果
fprintf('===== Simulink 模型自动生成完成 =====\n');
fprintf('模型名称: %s\n', model);
fprintf('双击 Scope 查看: 转速参考 / 实际转速 (rpm) / 电枢电流 (A)\n');
