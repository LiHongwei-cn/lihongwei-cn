%% RUN_PARKING_SIMULATION - 倒车入库CarSim/Simulink联合仿真主脚本
% 兼容版本：MATLAB R2016b
% 功能：配置并运行倒车入库仿真场景
%
% 场景描述：
%   - 50m长的道路
%   - 右侧有一排车位，只剩一个空位
%   - 其他车位停满了车
%   - 目标车辆需要倒车入库
%
% 作者：LiHongwei
% 日期：2026-05-29

clear; clc; close all;

fprintf('========================================\n');
fprintf('  倒车入库CarSim/Simulink联合仿真\n');
fprintf('========================================\n\n');

%% ==================== 仿真参数配置 ====================

% 仿真时间参数
sim_params.sim_time = 60;          % 总仿真时间 [s]
sim_params.dt = 0.01;              % 仿真步长 [s]

% 道路参数
road_params.length = 50;           % 道路长度 [m]
road_params.width = 6;             % 行车道宽度 [m]
road_params.num_parking_spots = 10; % 车位数量
road_params.parking_spot_length = 5; % 车位长度（沿道路方向） [m]
road_params.parking_spot_width = 2.5; % 车位宽度（纵深） [m]
road_params.parking_spot_depth = 2.5; % 车位深度 [m]

% 车位布局（1=占用，0=空闲）
% 目标车位是第5个车位（从1开始计数）
road_params.parking_occupancy = [1, 1, 1, 1, 0, 1, 1, 1, 1, 1];
road_params.target_spot_index = 5; % 目标车位索引

% 车辆初始状态
vehicle_params.initial_x = 45;     % 初始x位置 [m]
vehicle_params.initial_y = 3;      % 初始y位置 [m]（道路中间）
vehicle_params.initial_yaw = 0;    % 初始航向角 [rad]
vehicle_params.initial_speed = 5;  % 初始速度 [km/h]
vehicle_params.initial_steer = 0;  % 初始转向角 [deg]

% 车辆尺寸参数
vehicle_params.length = 4.5;       % 车长 [m]
vehicle_params.width = 1.8;        % 车宽 [m]
vehicle_params.wheelbase = 2.7;    % 轴距 [m]

% 控制参数
control_params.kp_lateral = 2.5;   % 横向控制P增益
control_params.ki_lateral = 0.1;   % 横向控制I增益
control_params.kd_lateral = 0.5;   % 横向控制D增益

control_params.kp_longitudinal = 1.8; % 纵向控制P增益
control_params.ki_longitudinal = 0.05; % 纵向控制I增益
control_params.kd_longitudinal = 0.3; % 纵向控制D增益

% 目标速度参数
control_params.cruise_speed = 5;   % 巡航速度 [km/h]
control_params.reverse_speed = 2;  % 倒车速度 [km/h]
control_params.stop_threshold = 0.1; % 停车阈值 [m]

fprintf('[1/5] 仿真参数配置完成\n');

%% ==================== 生成参考路径 ====================

% 计算目标车位位置
target_spot_center_x = (road_params.target_spot_index - 0.5) * road_params.parking_spot_length;
target_spot_center_y = -road_params.parking_spot_depth / 2;

% 生成倒车入库参考路径
% 路径包含：接近段 + 转弯段 + 入库段
ref_path = generate_parking_path(vehicle_params, road_params, target_spot_center_x, target_spot_center_y);

fprintf('[2/5] 参考路径生成完成，共 %d 个路径点\n', size(ref_path, 1));

%% ==================== 创建Simulink模型 ====================

% 如果模型不存在则创建
if ~exist('parking_reverse_control.slx', 'file')
    create_parking_simulink_model();
    fprintf('[3/5] Simulink模型创建完成\n');
else
    fprintf('[3/5] Simulink模型已存在，跳过创建\n');
end

%% ==================== 配置CarSim接口 ====================

% CarSim S-Function参数配置
carsim_config = configure_carsim_interface(vehicle_params, road_params);

fprintf('[4/5] CarSim接口配置完成\n');

%% ==================== 运行仿真 ====================

fprintf('[5/5] 开始运行仿真...\n');
fprintf('仿真时间: %.1f 秒\n\n', sim_params.sim_time);

try
    % 加载模型
    load_system('parking_reverse_control');

    % 设置仿真参数
    set_param('parking_reverse_control', 'StopTime', num2str(sim_params.sim_time));
    set_param('parking_reverse_control', 'FixedStep', num2str(sim_params.dt));

    % 运行仿真
    sim_output = sim('parking_reverse_control');

    fprintf('\n仿真完成！\n');

    %% ==================== 分析仿真结果 ====================

    analyze_simulation_results(sim_output, ref_path, road_params, vehicle_params);

catch ME
    fprintf('\n仿真运行错误: %s\n', ME.message);
    fprintf('请检查CarSim配置和S-Function路径\n');
    fprintf('详细错误信息:\n');
    disp(ME);
end

%% ==================== 辅助函数 ====================

function ref_path = generate_parking_path(vehicle_params, road_params, target_x, target_y)
% GENERATE_PARKING_PATH - 生成倒车入库参考路径
% 使用多项式曲线生成平滑路径

    % 路径点数量
    num_points = 200;

    % 接近段（直线接近目标车位）
    approach_start_x = vehicle_params.initial_x;
    approach_end_x = target_x + 5;  % 在车位前方5米开始转弯
    approach_y = road_params.width / 2;  % 道路中间

    % 转弯段（使用五次多项式）
    turn_start_x = approach_end_x;
    turn_end_x = target_x;
    turn_start_y = approach_y;
    turn_end_y = 0;  % 道路边沿

    % 入库段（倒车入库）
    entry_start_x = turn_end_x;
    entry_end_x = target_x;
    entry_start_y = 0;
    entry_end_y = target_y;

    % 生成路径点
    path_x = zeros(num_points, 1);
    path_y = zeros(num_points, 1);
    path_yaw = zeros(num_points, 1);

    % 第一阶段：接近（40%的路径点）
    n1 = round(0.4 * num_points);
    t1 = linspace(0, 1, n1);
    path_x(1:n1) = approach_start_x + (approach_end_x - approach_start_x) * t1;
    path_y(1:n1) = approach_y * ones(1, n1);

    % 第二阶段：转弯（30%的路径点）
    n2 = round(0.3 * num_points);
    t2 = linspace(0, 1, n2);
    % 使用五次多项式保证曲率连续
    s = t2;
    poly = 10*s.^3 - 15*s.^4 + 6*s.^5;
    path_x(n1+1:n1+n2) = turn_start_x + (turn_end_x - turn_start_x) * s;
    path_y(n1+1:n1+n2) = turn_start_y + (turn_end_y - turn_start_y) * poly;

    % 第三阶段：入库（30%的路径点）
    n3 = num_points - n1 - n2;
    t3 = linspace(0, 1, n3);
    path_x(n1+n2+1:end) = entry_end_x * ones(1, n3);
    path_y(n1+n2+1:end) = entry_start_y + (entry_end_y - entry_start_y) * t3;

    % 计算航向角（数值微分）
    for i = 2:num_points-1
        dx = path_x(i+1) - path_x(i-1);
        dy = path_y(i+1) - path_y(i-1);
        path_yaw(i) = atan2(dy, dx);
    end
    path_yaw(1) = path_yaw(2);
    path_yaw(end) = path_yaw(end-1);

    % 组合路径
    ref_path = [path_x, path_y, path_yaw];

end

function carsim_config = configure_carsim_interface(vehicle_params, road_params)
% CONFIGURE_CARSIM_INTERFACE - 配置CarSim接口参数

    % CarSim DLL路径（CarSim 2019.0实际安装路径）
    carsim_config.dll_path = 'C:\Program Files (x86)\CarSim2019.0_Prog\Programs\vs_connect\vs_connect_sf2.mexw64';

    % CarSim数据集名称
    carsim_config.dataset_name = 'Parking_Reversing';

    % 输入信号映射（Simulink -> CarSim）
    carsim_config.input_channels = {
        'IMP_STEER_SW',    % 方向盘转角 [deg]
        'IMP_PBK_CON',     % 制动主缸压力 [kPa]
        'IMP_THROTTLE',    % 油门开度 [%]
        'IMP_GEARCHANGE'   % 档位（-1=倒档）
    };

    % 输出信号映射（CarSim -> Simulink）
    carsim_config.output_channels = {
        'XCG',             % 车辆X位置 [m]
        'YCG',             % 车辆Y位置 [m]
        'YAW',             % 航向角 [rad]
        'VX',              % 纵向速度 [km/h]
        'VY',              % 横向速度 [km/h]
        'AVZ',             % 横摆角速度 [deg/s]
        'STEER_L1',        % 左前轮转角 [deg]
        'STEER_R1'         % 右前轮转角 [deg]
    };

    % 保存配置到工作空间
    assignin('base', 'carsim_config', carsim_config);

end

function analyze_simulation_results(sim_output, ref_path, road_params, vehicle_params)
% ANALYZE_SIMULATION_RESULTS - 分析并可视化仿真结果

    fprintf('\n==================== 仿真结果分析 ====================\n');

    try
        % 提取仿真数据
        if isfield(sim_output, 'vehicle_state_log')
            vehicle_data = sim_output.vehicle_state_log;
        else
            fprintf('警告: 未找到车辆状态日志数据\n');
            return;
        end

        % 提取时间序列
        time = vehicle_data.Time;
        x_pos = vehicle_data.Data(:, 1);
        y_pos = vehicle_data.Data(:, 2);
        yaw = vehicle_data.Data(:, 3);
        speed = vehicle_data.Data(:, 4);

        % 计算最终位置误差
        target_x = ref_path(end, 1);
        target_y = ref_path(end, 2);
        final_x = x_pos(end);
        final_y = y_pos(end);

        position_error = sqrt((final_x - target_x)^2 + (final_y - target_y)^2);

        fprintf('最终位置: (%.2f, %.2f) m\n', final_x, final_y);
        fprintf('目标位置: (%.2f, %.2f) m\n', target_x, target_y);
        fprintf('位置误差: %.3f m\n', position_error);

        if position_error < 0.5
            fprintf('✓ 停车精度良好\n');
        elseif position_error < 1.0
            fprintf('△ 停车精度一般\n');
        else
            fprintf('✗ 停车精度不足\n');
        end

        % ==================== 绘图 ====================

        figure('Name', '倒车入库仿真结果', 'Position', [100, 100, 1200, 800]);

        % 子图1：车辆轨迹
        subplot(2, 2, 1);
        plot(ref_path(:,1), ref_path(:,2), 'r--', 'LineWidth', 2);
        hold on;
        plot(x_pos, y_pos, 'b-', 'LineWidth', 1.5);
        plot(final_x, final_y, 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g');
        plot(target_x, target_y, 'rx', 'MarkerSize', 15, 'MarkerWidth', 3);

        % 绘制道路和车位
        draw_road_and_parking(road_params);

        xlabel('X [m]');
        ylabel('Y [m]');
        title('车辆轨迹');
        legend('参考路径', '实际轨迹', '最终位置', '目标位置', 'Location', 'best');
        grid on;
        axis equal;

        % 子图2：位置随时间变化
        subplot(2, 2, 2);
        plot(time, x_pos, 'b-', 'LineWidth', 1.5);
        hold on;
        plot(time, y_pos, 'r-', 'LineWidth', 1.5);
        xlabel('时间 [s]');
        ylabel('位置 [m]');
        title('车辆位置');
        legend('X位置', 'Y位置', 'Location', 'best');
        grid on;

        % 子图3：速度随时间变化
        subplot(2, 2, 3);
        plot(time, speed, 'b-', 'LineWidth', 1.5);
        xlabel('时间 [s]');
        ylabel('速度 [km/h]');
        title('车辆速度');
        grid on;

        % 子图4：航向角随时间变化
        subplot(2, 2, 4);
        plot(time, rad2deg(yaw), 'b-', 'LineWidth', 1.5);
        xlabel('时间 [s]');
        ylabel('航向角 [deg]');
        title('车辆航向角');
        grid on;

        % 保存图片
        saveas(gcf, 'parking_simulation_results.png');
        fprintf('\n结果图片已保存: parking_simulation_results.png\n');

    catch ME
        fprintf('结果分析错误: %s\n', ME.message);
    end

end

function draw_road_and_parking(road_params)
% DRAW_ROAD_AND_PARKING - 绘制道路、车位线和车辆

    hold on;

    % ==================== 绘制道路边界 ====================
    plot([0, road_params.length], [0, 0], 'k-', 'LineWidth', 2);
    plot([0, road_params.length], [road_params.width, road_params.width], 'k-', 'LineWidth', 2);

    % 绘制道路中心虚线（可选）
    for x = 0:4:road_params.length
        plot([x, min(x+2, road_params.length)], [road_params.width/2, road_params.width/2], ...
            'k--', 'LineWidth', 1);
    end

    % ==================== 绘制车位和车位线 ====================
    for i = 1:road_params.num_parking_spots
        % 车位边界
        spot_x_start = (i-1) * road_params.parking_spot_length;
        spot_x_end = i * road_params.parking_spot_length;
        spot_y_start = -road_params.parking_spot_depth;
        spot_y_end = 0;

        % 绘制车位边框（白色车位线）
        rectangle('Position', [spot_x_start, spot_y_start, ...
            road_params.parking_spot_length, road_params.parking_spot_depth], ...
            'EdgeColor', 'w', 'LineWidth', 2, 'LineStyle', '-');

        % 绘制车位内部标线（斜线表示车位）
        line_x = linspace(spot_x_start + 0.3, spot_x_end - 0.3, 5);
        for lx = line_x
            plot([lx, lx], [spot_y_start + 0.3, spot_y_end - 0.3], ...
                'w-', 'LineWidth', 1);
        end

        % 绘制车位编号
        text(spot_x_start + road_params.parking_spot_length/2, ...
            spot_y_start - 0.3, ...
            sprintf('%d', i), 'HorizontalAlignment', 'center', ...
            'FontSize', 10, 'Color', 'k');

        % ==================== 绘制车辆 ====================
        if road_params.parking_occupancy(i) == 1
            % 车辆主体（矩形）
            car_x = spot_x_start + 0.25;
            car_y = spot_y_start + 0.25;
            car_width = road_params.parking_spot_length - 0.5;
            car_height = road_params.parking_spot_depth - 0.5;

            % 车身
            rectangle('Position', [car_x, car_y, car_width, car_height], ...
                'FaceColor', [0.6, 0.6, 0.8], ...  % 浅蓝色车身
                'EdgeColor', 'k', 'LineWidth', 1.5);

            % 车窗（前窗和后窗）
            % 前窗
            window_front_x = car_x + car_width * 0.6;
            window_front_y = car_y + car_height * 0.2;
            window_front_w = car_width * 0.25;
            window_front_h = car_height * 0.6;
            rectangle('Position', [window_front_x, window_front_y, ...
                window_front_w, window_front_h], ...
                'FaceColor', [0.7, 0.9, 1], ...  % 浅蓝色车窗
                'EdgeColor', 'k', 'LineWidth', 1);

            % 后窗
            window_rear_x = car_x + car_width * 0.15;
            window_rear_y = car_y + car_height * 0.25;
            window_rear_w = car_width * 0.2;
            window_rear_h = car_height * 0.5;
            rectangle('Position', [window_rear_x, window_rear_y, ...
                window_rear_w, window_rear_h], ...
                'FaceColor', [0.7, 0.9, 1], ...
                'EdgeColor', 'k', 'LineWidth', 1);

            % 车轮（四个轮子）
            wheel_radius = 0.15;
            wheel_width = 0.1;

            % 左前轮
            rectangle('Position', [car_x + car_width*0.7 - wheel_radius, ...
                car_y - wheel_radius, wheel_radius*2, wheel_radius*2], ...
                'Curvature', [1, 1], 'FaceColor', [0.2, 0.2, 0.2], 'EdgeColor', 'k');

            % 右前轮
            rectangle('Position', [car_x + car_width*0.7 - wheel_radius, ...
                car_y + car_height - wheel_radius, wheel_radius*2, wheel_radius*2], ...
                'Curvature', [1, 1], 'FaceColor', [0.2, 0.2, 0.2], 'EdgeColor', 'k');

            % 左后轮
            rectangle('Position', [car_x + car_width*0.2 - wheel_radius, ...
                car_y - wheel_radius, wheel_radius*2, wheel_radius*2], ...
                'Curvature', [1, 1], 'FaceColor', [0.2, 0.2, 0.2], 'EdgeColor', 'k');

            % 右后轮
            rectangle('Position', [car_x + car_width*0.2 - wheel_radius, ...
                car_y + car_height - wheel_radius, wheel_radius*2, wheel_radius*2], ...
                'Curvature', [1, 1], 'FaceColor', [0.2, 0.2, 0.2], 'EdgeColor', 'k');

            % 车灯（前灯和后灯）
            % 前灯
            rectangle('Position', [car_x + car_width - 0.15, car_y + 0.15, 0.1, 0.2], ...
                'FaceColor', [1, 1, 0.8], 'EdgeColor', 'k');  % 黄色前灯
            rectangle('Position', [car_x + car_width - 0.15, car_y + car_height - 0.35, 0.1, 0.2], ...
                'FaceColor', [1, 1, 0.8], 'EdgeColor', 'k');

            % 后灯
            rectangle('Position', [car_x + 0.05, car_y + 0.15, 0.1, 0.2], ...
                'FaceColor', [1, 0.2, 0.2], 'EdgeColor', 'k');  % 红色后灯
            rectangle('Position', [car_x + 0.05, car_y + car_height - 0.35, 0.1, 0.2], ...
                'FaceColor', [1, 0.2, 0.2], 'EdgeColor', 'k');

        else
            % 空车位标记
            rectangle('Position', [spot_x_start + 0.1, spot_y_start + 0.1, ...
                road_params.parking_spot_length - 0.2, road_params.parking_spot_depth - 0.2], ...
                'FaceColor', [0.9, 1, 0.9], ...  % 浅绿色背景
                'EdgeColor', 'g', 'LineWidth', 2, 'LineStyle', '--');

            % 空车位标记文字
            text(spot_x_start + road_params.parking_spot_length/2, ...
                spot_y_start + road_params.parking_spot_depth/2, ...
                '空', 'HorizontalAlignment', 'center', ...
                'FontSize', 16, 'FontWeight', 'bold', 'Color', [0, 0.6, 0]);
        end
    end

    % ==================== 绘制道路边缘标记 ====================
    % 道路边缘实线
    plot([0, road_params.length], [0, 0], 'w-', 'LineWidth', 3);
    plot([0, road_params.length], [road_params.width, road_params.width], 'w-', 'LineWidth', 3);

    % ==================== 设置坐标轴 ====================
    xlim([-2, road_params.length + 2]);
    ylim([-road_params.parking_spot_depth - 2, road_params.width + 2]);

    % 设置背景色（道路颜色）
    set(gca, 'Color', [0.4, 0.4, 0.4]);  % 灰色道路背景

end
