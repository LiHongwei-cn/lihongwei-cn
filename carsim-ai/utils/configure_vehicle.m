%% 车辆参数配置器 - 支持前驱/后驱/四驱
% MATLAB R2016b 兼容
% 用于 CarSim 2019.0
% 配置不同驱动类型的车辆参数

function vehicle_params = configure_vehicle(drive_type, engine_power)
    % configure_vehicle 配置车辆参数
    %
    % 输入参数：
    %   drive_type   - 驱动类型: 'FWD' (前驱), 'RWD' (后驱), 'AWD' (四驱)
    %   engine_power - 发动机功率 [kW]
    %
    % 输出参数：
    %   vehicle_params - 车辆参数结构体

    %% 验证输入
    valid_types = {'FWD', 'RWD', 'AWD'};
    if ~ismember(drive_type, valid_types)
        error('无效的驱动类型: %s。有效类型: FWD, RWD, AWD', drive_type);
    end

    if engine_power <= 0
        error('发动机功率必须为正数');
    end

    %% 基础车辆参数（通用）
    vehicle_params.drive_type = drive_type;
    vehicle_params.engine_power = engine_power;

    % 车辆尺寸
    vehicle_params.length = 4.5;           % 车长 [m]
    vehicle_params.width = 1.8;            % 车宽 [m]
    vehicle_params.height = 1.5;           % 车高 [m]
    vehicle_params.wheelbase = 2.7;        % 轴距 [m]

    % 质量参数
    vehicle_params.mass = 1500;            % 整车质量 [kg]
    vehicle_params.front_axle_load = 0.5;  % 前轴载荷比例
    vehicle_params.rear_axle_load = 0.5;   % 后轴载荷比例

    % 轮胎参数
    vehicle_params.tire_radius = 0.31;     % 轮胎半径 [m]
    vehicle_params.tire_width = 0.225;     % 轮胎宽度 [m]
    vehicle_params.tire_stiffness = 200000; % 轮胎刚度 [N/m]

    % 发动机参数
    vehicle_params.max_torque = engine_power * 1000 / (5000 * pi / 30);  % 最大扭矩 [Nm]
    vehicle_params.max_rpm = 6000;         % 最大转速 [rpm]
    vehicle_params.idle_rpm = 800;         % 怠速转速 [rpm]

    % 变速箱参数
    vehicle_params.gear_ratios = [3.5, 2.1, 1.4, 1.0, 0.7];  % 5档变速箱
    vehicle_params.final_drive = 3.5;      % 主减速比
    vehicle_params.transmission_efficiency = 0.92;  % 传动效率

    % 悬架参数
    vehicle_params.front_spring_rate = 25000;   % 前弹簧刚度 [N/m]
    vehicle_params.rear_spring_rate = 22000;    % 后弹簧刚度 [N/m]
    vehicle_params.front_damper_rate = 3000;    % 前阻尼系数 [N·s/m]
    vehicle_params.rear_damper_rate = 2800;     % 后阻尼系数 [N·s/m]

    %% 根据驱动类型调整参数
    switch drive_type
        case 'FWD'
            % 前驱车：前轴载荷更大
            vehicle_params.front_axle_load = 0.6;
            vehicle_params.rear_axle_load = 0.4;
            vehicle_params.drive_wheels = 'FRONT';
            vehicle_params.description = '前驱车';

        case 'RWD'
            % 后驱车：后轴载荷更大
            vehicle_params.front_axle_load = 0.45;
            vehicle_params.rear_axle_load = 0.55;
            vehicle_params.drive_wheels = 'REAR';
            vehicle_params.description = '后驱车';

        case 'AWD'
            % 四驱车：载荷均匀分布
            vehicle_params.front_axle_load = 0.5;
            vehicle_params.rear_axle_load = 0.5;
            vehicle_params.drive_wheels = 'ALL';
            vehicle_params.description = '四驱车';

            % 四驱系统参数
            vehicle_params.center_diff_ratio = 0.5;  % 中央差速器分配比例
            vehicle_params.front_diff_type = 'OPEN'; % 前差速器类型
            vehicle_params.rear_diff_type = 'OPEN';  % 后差速器类型
    end

    %% 计算派生参数
    % 转动惯量
    vehicle_params.Iz = vehicle_params.mass * vehicle_params.wheelbase^2 / 12;  % 横摆转动惯量 [kg·m^2]
    vehicle_params.Iw = 1.5;  % 车轮转动惯量 [kg·m^2]

    % 空气动力学参数
    vehicle_params.Cd = 0.32;              % 风阻系数
    vehicle_params.Af = 2.2;               % 迎风面积 [m^2]
    vehicle_params.Cl = 0.1;               % 升力系数

    % 制动参数
    vehicle_params.front_brake_torque = 2000;  % 前制动扭矩 [Nm]
    vehicle_params.rear_brake_torque = 1500;   % 后制动扭矩 [Nm]

    %% 输出配置信息
    fprintf('===== 车辆配置 =====\n');
    fprintf('驱动类型: %s\n', vehicle_params.description);
    fprintf('发动机功率: %.1f kW\n', engine_power);
    fprintf('整车质量: %.0f kg\n', vehicle_params.mass);
    fprintf('前轴载荷: %.0f%%\n', vehicle_params.front_axle_load * 100);
    fprintf('后轴载荷: %.0f%%\n', vehicle_params.rear_axle_load * 100);
    fprintf('最大扭矩: %.1f Nm\n', vehicle_params.max_torque);
    fprintf('====================\n');
end

function save_vehicle_to_carsim(vehicle_params, output_dir)
    % save_vehicle_to_carsim 保存车辆参数到 CarSim 格式
    %
    % 输入参数：
    %   vehicle_params - 车辆参数结构体
    %   output_dir     - 输出目录

    % 生成车辆参数文件
    filename = fullfile(output_dir, sprintf('vehicle_%s.par', vehicle_params.drive_type));
    fid = fopen(filename, 'w');

    if fid == -1
        error('无法创建文件: %s', filename);
    end

    % 文件头
    fprintf(fid, '! CarSim Vehicle Parameters\n');
    fprintf(fid, '! 驱动类型: %s\n', vehicle_params.description);
    fprintf(fid, '! 生成时间: %s\n', datestr(now));
    fprintf(fid, '\n');

    % 车辆尺寸
    fprintf(fid, 'VEHICLE_DIMENSIONS\n');
    fprintf(fid, '  LENGTH = %.2f\n', vehicle_params.length);
    fprintf(fid, '  WIDTH = %.2f\n', vehicle_params.width);
    fprintf(fid, '  HEIGHT = %.2f\n', vehicle_params.height);
    fprintf(fid, '  WHEELBASE = %.2f\n', vehicle_params.wheelbase);
    fprintf(fid, 'END_VEHICLE_DIMENSIONS\n');
    fprintf(fid, '\n');

    % 质量参数
    fprintf(fid, 'MASS_PROPERTIES\n');
    fprintf(fid, '  TOTAL_MASS = %.1f\n', vehicle_params.mass);
    fprintf(fid, '  FRONT_AXLE_LOAD_RATIO = %.2f\n', vehicle_params.front_axle_load);
    fprintf(fid, '  REAR_AXLE_LOAD_RATIO = %.2f\n', vehicle_params.rear_axle_load);
    fprintf(fid, '  IZ = %.1f\n', vehicle_params.Iz);
    fprintf(fid, '  IW = %.2f\n', vehicle_params.Iw);
    fprintf(fid, 'END_MASS_PROPERTIES\n');
    fprintf(fid, '\n');

    % 驱动系统
    fprintf(fid, 'DRIVETRAIN\n');
    fprintf(fid, '  DRIVE_TYPE = %s\n', vehicle_params.drive_wheels);
    fprintf(fid, '  ENGINE_POWER = %.1f\n', vehicle_params.engine_power);
    fprintf(fid, '  MAX_TORQUE = %.1f\n', vehicle_params.max_torque);
    fprintf(fid, '  MAX_RPM = %.0f\n', vehicle_params.max_rpm);
    fprintf(fid, '  IDLE_RPM = %.0f\n', vehicle_params.idle_rpm);
    fprintf(fid, '  GEAR_RATIOS = %.2f, %.2f, %.2f, %.2f, %.2f\n', ...
        vehicle_params.gear_ratios(1), vehicle_params.gear_ratios(2), ...
        vehicle_params.gear_ratios(3), vehicle_params.gear_ratios(4), ...
        vehicle_params.gear_ratios(5));
    fprintf(fid, '  FINAL_DRIVE = %.2f\n', vehicle_params.final_drive);
    fprintf(fid, '  TRANSMISSION_EFFICIENCY = %.2f\n', vehicle_params.transmission_efficiency);
    fprintf(fid, 'END_DRIVETRAIN\n');
    fprintf(fid, '\n');

    % 四驱系统参数（仅四驱车）
    if strcmp(vehicle_params.drive_type, 'AWD')
        fprintf(fid, 'AWD_SYSTEM\n');
        fprintf(fid, '  CENTER_DIFF_RATIO = %.2f\n', vehicle_params.center_diff_ratio);
        fprintf(fid, '  FRONT_DIFF_TYPE = %s\n', vehicle_params.front_diff_type);
        fprintf(fid, '  REAR_DIFF_TYPE = %s\n', vehicle_params.rear_diff_type);
        fprintf(fid, 'END_AWD_SYSTEM\n');
        fprintf(fid, '\n');
    end

    % 轮胎参数
    fprintf(fid, 'TIRE_PARAMETERS\n');
    fprintf(fid, '  RADIUS = %.2f\n', vehicle_params.tire_radius);
    fprintf(fid, '  WIDTH = %.3f\n', vehicle_params.tire_width);
    fprintf(fid, '  STIFFNESS = %.0f\n', vehicle_params.tire_stiffness);
    fprintf(fid, 'END_TIRE_PARAMETERS\n');
    fprintf(fid, '\n');

    % 悬架参数
    fprintf(fid, 'SUSPENSION\n');
    fprintf(fid, '  FRONT_SPRING_RATE = %.0f\n', vehicle_params.front_spring_rate);
    fprintf(fid, '  REAR_SPRING_RATE = %.0f\n', vehicle_params.rear_spring_rate);
    fprintf(fid, '  FRONT_DAMPER_RATE = %.0f\n', vehicle_params.front_damper_rate);
    fprintf(fid, '  REAR_DAMPER_RATE = %.0f\n', vehicle_params.rear_damper_rate);
    fprintf(fid, 'END_SUSPENSION\n');
    fprintf(fid, '\n');

    % 空气动力学参数
    fprintf(fid, 'AERODYNAMICS\n');
    fprintf(fid, '  CD = %.2f\n', vehicle_params.Cd);
    fprintf(fid, '  AF = %.2f\n', vehicle_params.Af);
    fprintf(fid, '  CL = %.2f\n', vehicle_params.Cl);
    fprintf(fid, 'END_AERODYNAMICS\n');
    fprintf(fid, '\n');

    % 制动参数
    fprintf(fid, 'BRAKES\n');
    fprintf(fid, '  FRONT_BRAKE_TORQUE = %.0f\n', vehicle_params.front_brake_torque);
    fprintf(fid, '  REAR_BRAKE_TORQUE = %.0f\n', vehicle_params.rear_brake_torque);
    fprintf(fid, 'END_BRAKES\n');

    fclose(fid);

    fprintf('车辆参数已保存: %s\n', filename);
end
