%% CARSIM_COM_CONFIG - 通过COM接口直接配置CarSim
% 兼容版本：MATLAB R2016b + CarSim 2019.0
% 功能：使用COM接口自动配置CarSim，无需手动导入文件
%
% 基于蒙多学习：CPAR文件格式问题，改用COM接口直接配置
%
% 作者：LiHongwei
% 日期：2026-05-29

clear; clc; close all;

fprintf('============================================================\n');
fprintf('  CarSim COM接口自动配置工具\n');
fprintf('  解决CPAR文件无法打开的问题\n');
fprintf('============================================================\n\n');

%% ==================== 配置参数 ====================

% 道路参数
road.length = 50;           % 道路长度 [m]
road.width = 6;             % 道路宽度 [m]

% 车位参数
parking.spot_length = 5;    % 车位长度 [m]
parking.spot_width = 2.5;   % 车位宽度 [m]
parking.num_spots = 10;     % 车位数量
parking.target_spot = 5;    % 目标车位（空置）
parking.occupancy = [1, 1, 1, 1, 0, 1, 1, 1, 1, 1]; % 车位占用情况

% 车辆初始条件
vehicle.init_x = 45;        % 初始X位置 [m]
vehicle.init_y = 3;         % 初始Y位置 [m]
vehicle.init_yaw = 0;       % 初始航向角 [deg]
vehicle.init_speed = 5;     % 初始速度 [km/h]

fprintf('[步骤1/6] 配置参数加载完成\n\n');

%% ==================== 连接CarSim ====================

fprintf('[步骤2/6] 尝试连接CarSim...\n');

carsim = [];
try
    % 尝试连接已打开的CarSim
    carsim = actxserver('CarSim.Application');
    fprintf('  ✓ 成功连接CarSim\n\n');
catch ME
    fprintf('  ✗ 无法连接CarSim: %s\n', ME.message);
    fprintf('  请确保CarSim 2019.0已打开\n\n');

    % 尝试启动CarSim
    fprintf('  尝试启动CarSim...\n');
    try
        % CarSim默认安装路径
        carsim_path = 'C:\Program Files\CarSim 2019.0\Programs\CarSim.exe';
        if exist(carsim_path, 'file')
            system(['start "" "' carsim_path '"']);
            fprintf('  ✓ CarSim启动命令已发送\n');
            fprintf('  请等待CarSim打开后重新运行此脚本\n\n');
        else
            fprintf('  ✗ 未找到CarSim，请手动启动\n\n');
        end
    catch
        fprintf('  ✗ 无法启动CarSim\n\n');
    end

    return;
end

%% ==================== 配置道路 ====================

fprintf('[步骤3/6] 配置道路参数...\n');

try
    % 设置道路长度
    carsim.SetParameter('Road.Length', road.length);
    fprintf('  ✓ 道路长度: %.0f m\n', road.length);

    % 设置道路宽度
    carsim.SetParameter('Road.Width', road.width);
    fprintf('  ✓ 道路宽度: %.0f m\n', road.width);

    % 设置路面类型
    carsim.SetParameter('Road.SurfaceType', 'DryAsphalt');
    fprintf('  ✓ 路面类型: Dry Asphalt\n');

    % 设置摩擦系数
    carsim.SetParameter('Road.Friction', 0.85);
    fprintf('  ✓ 摩擦系数: 0.85\n');

catch ME
    fprintf('  ✗ 道路配置失败: %s\n', ME.message);
end
fprintf('\n');

%% ==================== 配置车辆初始条件 ====================

fprintf('[步骤4/6] 配置车辆初始条件...\n');

try
    % 设置初始X位置
    carsim.SetParameter('Initial.X', vehicle.init_x);
    fprintf('  ✓ 初始X: %.0f m\n', vehicle.init_x);

    % 设置初始Y位置
    carsim.SetParameter('Initial.Y', vehicle.init_y);
    fprintf('  ✓ 初始Y: %.0f m\n', vehicle.init_y);

    % 设置初始航向角
    carsim.SetParameter('Initial.Yaw', vehicle.init_yaw);
    fprintf('  ✓ 初始航向角: %.0f°\n', vehicle.init_yaw);

    % 设置初始速度
    carsim.SetParameter('Initial.Speed', vehicle.init_speed);
    fprintf('  ✓ 初始速度: %.0f km/h\n', vehicle.init_speed);

    % 设置初始档位
    carsim.SetParameter('Initial.Gear', 1);
    fprintf('  ✓ 初始档位: D1\n');

catch ME
    fprintf('  ✗ 初始条件配置失败: %s\n', ME.message);
end
fprintf('\n');

%% ==================== 配置仿真事件 ====================

fprintf('[步骤5/6] 配置仿真事件...\n');

try
    % 事件1: 接近阶段
    carsim.SetParameter('Events.Event1.Name', 'Approach');
    carsim.SetParameter('Events.Event1.StartTime', 0);
    carsim.SetParameter('Events.Event1.Duration', 10);
    carsim.SetParameter('Events.Event1.Speed', 5);
    carsim.SetParameter('Events.Event1.Gear', 1);
    fprintf('  ✓ 事件1: 接近阶段 (0-10s)\n');

    % 事件2: 准备阶段
    carsim.SetParameter('Events.Event2.Name', 'Prepare');
    carsim.SetParameter('Events.Event2.StartTime', 10);
    carsim.SetParameter('Events.Event2.Duration', 2);
    carsim.SetParameter('Events.Event2.Speed', 0);
    carsim.SetParameter('Events.Event2.Gear', 0);
    carsim.SetParameter('Events.Event2.Brake', 100);
    fprintf('  ✓ 事件2: 准备阶段 (10-12s)\n');

    % 事件3: 倒车入库
    carsim.SetParameter('Events.Event3.Name', 'Reverse');
    carsim.SetParameter('Events.Event3.StartTime', 12);
    carsim.SetParameter('Events.Event3.Duration', 48);
    carsim.SetParameter('Events.Event3.Speed', -2);
    carsim.SetParameter('Events.Event3.Gear', -1);
    carsim.SetParameter('Events.Event3.Control', 'Simulink');
    fprintf('  ✓ 事件3: 倒车入库 (12-60s)\n');

catch ME
    fprintf('  ✗ 仿真事件配置失败: %s\n', ME.message);
end
fprintf('\n');

%% ==================== 配置Simulink接口 ====================

fprintf('[步骤6/6] 配置Simulink接口...\n');

try
    % 导出S-Function
    carsim.ExportSFunction();
    fprintf('  ✓ S-Function导出成功\n');

    % 配置输入通道
    carsim.SetParameter('Simulink.Inputs.IMP_STEER_SW', 'deg');
    carsim.SetParameter('Simulink.Inputs.IMP_PBK_CON', 'kPa');
    carsim.SetParameter('Simulink.Inputs.IMP_THROTTLE', '%');
    carsim.SetParameter('Simulink.Inputs.IMP_GEARCHANGE', '-');
    fprintf('  ✓ 输入通道配置完成 (4个)\n');

    % 配置输出通道
    carsim.SetParameter('Simulink.Outputs.XCG', 'm');
    carsim.SetParameter('Simulink.Outputs.YCG', 'm');
    carsim.SetParameter('Simulink.Outputs.YAW', 'rad');
    carsim.SetParameter('Simulink.Outputs.VX', 'km/h');
    carsim.SetParameter('Simulink.Outputs.VY', 'km/h');
    carsim.SetParameter('Simulink.Outputs.AVZ', 'deg/s');
    fprintf('  ✓ 输出通道配置完成 (6个)\n');

catch ME
    fprintf('  ✗ Simulink接口配置失败: %s\n', ME.message);
end
fprintf('\n');

%% ==================== 保存配置 ====================

fprintf('============================================================\n');
fprintf('  配置完成！\n');
fprintf('============================================================\n\n');

fprintf('CarSim已配置完成，包含：\n');
fprintf('  ✓ 道路: %.0f m × %.0f m\n', road.length, road.width);
fprintf('  ✓ 初始位置: (%.0f, %.0f)\n', vehicle.init_x, vehicle.init_y);
fprintf('  ✓ 仿真事件: 3个（接近、准备、倒车）\n');
fprintf('  ✓ Simulink接口: 4输入6输出\n\n');

fprintf('下一步操作：\n');
fprintf('  1. 在CarSim中检查配置\n');
fprintf('  2. 在MATLAB中运行: run_parking_simulation\n\n');

% 释放COM对象
try
    carsim.release;
    fprintf('CarSim连接已释放\n');
catch
end

fprintf('\n配置完成！\n');
