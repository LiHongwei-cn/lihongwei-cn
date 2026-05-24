%% 车辆参数配置器 - CarSim 2019.0 兼容
% MATLAB R2016b 兼容
% 生成可在 CarSim 中手动输入的参数

function params = configure_vehicle(drive_type, engine_power)
    % configure_vehicle 配置车辆参数
    %
    % 输入参数：
    %   drive_type   - 驱动类型: 'FWD' (前驱), 'RWD' (后驱), 'AWD' (四驱)
    %   engine_power - 发动机功率 [kW]
    %
    % 输出参数：
    %   params - 车辆参数结构体

    %% 验证输入
    valid_types = {'FWD', 'RWD', 'AWD'};
    if ~ismember(drive_type, valid_types)
        error('无效的驱动类型: %s。有效类型: FWD, RWD, AWD', drive_type);
    end

    if engine_power <= 0
        error('发动机功率必须为正数');
    end

    %% 基础车辆参数
    params.drive_type = drive_type;
    params.engine_power = engine_power;

    % 车辆尺寸
    params.length = 4.5;           % 车长 [m]
    params.width = 1.8;            % 车宽 [m]
    params.height = 1.5;           % 车高 [m]
    params.wheelbase = 2.7;        % 轴距 [m]

    % 质量参数
    params.mass = 1500;            % 整车质量 [kg]
    params.front_axle_load = 0.5;  % 前轴载荷比例
    params.rear_axle_load = 0.5;   % 后轴载荷比例

    % 轮胎参数
    params.tire_radius = 0.31;     % 轮胎半径 [m]
    params.tire_width = 0.225;     % 轮胎宽度 [m]

    % 发动机参数
    params.max_torque = engine_power * 1000 / (5000 * pi / 30);  % 最大扭矩 [Nm]
    params.max_rpm = 6000;         % 最大转速 [rpm]
    params.idle_rpm = 800;         % 怠速转速 [rpm]

    % 变速箱参数
    params.gear_ratios = [3.5, 2.1, 1.4, 1.0, 0.7];  % 5档变速箱
    params.final_drive = 3.5;      % 主减速比

    %% 根据驱动类型调整参数
    switch drive_type
        case 'FWD'
            % 前驱车：前轴载荷更大
            params.front_axle_load = 0.6;
            params.rear_axle_load = 0.4;
            params.drive_wheels = 'FRONT';
            params.description = '前驱车';

        case 'RWD'
            % 后驱车：后轴载荷更大
            params.front_axle_load = 0.45;
            params.rear_axle_load = 0.55;
            params.drive_wheels = 'REAR';
            params.description = '后驱车';

        case 'AWD'
            % 四驱车：载荷均匀分布
            params.front_axle_load = 0.5;
            params.rear_axle_load = 0.5;
            params.drive_wheels = 'ALL';
            params.description = '四驱车';

            % 四驱系统参数
            params.center_diff_ratio = 0.5;  % 中央差速器分配比例
            params.front_diff_type = 'OPEN'; % 前差速器类型
            params.rear_diff_type = 'OPEN';  % 后差速器类型
    end

    %% 输出配置信息
    fprintf('===== 车辆配置 =====\n');
    fprintf('驱动类型: %s\n', params.description);
    fprintf('发动机功率: %.1f kW\n', engine_power);
    fprintf('整车质量: %.0f kg\n', params.mass);
    fprintf('前轴载荷: %.0f%%\n', params.front_axle_load * 100);
    fprintf('后轴载荷: %.0f%%\n', params.rear_axle_load * 100);
    fprintf('最大扭矩: %.1f Nm\n', params.max_torque);
    fprintf('====================\n');
end
