%% 通用 CarSim 仿真主脚本（纯 CarSim 版本）
% MATLAB R2016b 兼容
% 支持多种仿真场景：高架桥爬坡、弯道操控、紧急避障等
% 本脚本仅生成参数说明，仿真完全在 CarSim 内部运行

function run_simulation(params)
    % run_simulation 生成 CarSim 仿真参数说明
    %
    % 输入参数：
    %   params.scene_type   - 场景类型
    %   params.output_dir   - 输出目录
    %   其他参数取决于场景类型

    %% 参数验证
    assert(isfield(params, 'scene_type'), '必须指定场景类型');
    assert(isfield(params, 'output_dir'), '必须指定输出目录');

    %% 创建输出目录
    if ~exist(params.output_dir, 'dir')
        mkdir(params.output_dir);
    end

    fprintf('============================================================\n');
    fprintf('  CarSim-AI 通用仿真工具（纯 CarSim）\n');
    fprintf('  场景类型: %s\n', params.scene_type);
    fprintf('============================================================\n\n');

    %% 根据场景类型生成参数
    fprintf('>>> 步骤 1: 生成场景参数...\n');
    params = generate_scenario(params);

    %% 生成 CarSim 参数说明
    fprintf('\n>>> 步骤 2: 生成 CarSim 参数说明...\n');
    generate_carsim_instructions(params);

    %% 生成结果分析脚本
    fprintf('\n>>> 步骤 3: 生成结果分析脚本...\n');
    generate_analysis_script(params);

    %% 输出使用说明
    fprintf('\n============================================================\n');
    fprintf('  文件已生成!\n');
    fprintf('============================================================\n\n');
    fprintf('请按以下步骤在 CarSim 中运行仿真:\n\n');
    fprintf('1. 打开 CarSim 2019.0\n');
    fprintf('2. 创建新数据集\n');
    fprintf('3. 按照生成的说明文件设置参数\n');
    fprintf('4. 点击 Run 运行仿真\n');
    fprintf('5. 导出结果后用 MATLAB 分析\n\n');
    fprintf('生成的文件:\n');
    fprintf('  - %s/carsim_instructions_*.txt: 参数设置说明\n', params.output_dir);
    fprintf('  - %s/analyze_results.m: 结果分析脚本\n', params.output_dir);
end

function params = generate_scenario(params)
    % generate_scenario 根据场景类型生成完整参数

    switch params.scene_type
        case 'bridge_slope'
            params = bridge_slope_scenario(params);
        case 'cornering'
            params = cornering_scenario(params);
        case 'obstacle_avoidance'
            params = obstacle_avoidance_scenario(params);
        case 'braking'
            params = braking_scenario(params);
        case 'acceleration'
            params = acceleration_scenario(params);
        otherwise
            error('未知场景类型: %s', params.scene_type);
    end
end

function generate_carsim_instructions(params)
    % generate_carsim_instructions 生成 CarSim 参数说明文件

    switch params.scene_type
        case 'bridge_slope'
            generate_bridge_slope_instructions(params);
        case 'cornering'
            generate_cornering_instructions(params);
        case 'obstacle_avoidance'
            generate_obstacle_avoidance_instructions(params);
        case 'braking'
            generate_braking_instructions(params);
        case 'acceleration'
            generate_acceleration_instructions(params);
    end
end

function generate_bridge_slope_instructions(params)
    % generate_bridge_slope_instructions 生成高架桥爬坡参数说明

    % 计算坡度参数
    slope_rad = params.slope_angle * pi / 180;
    bridge_height = params.bridge_length * tan(slope_rad);

    % 前驱车参数说明
    fwd_file = fullfile(params.output_dir, 'carsim_instructions_FWD.txt');
    fid = fopen(fwd_file, 'w');

    if fid == -1
        error('无法创建文件: %s', fwd_file);
    end

    fprintf(fid, '============================================================\n');
    fprintf(fid, '  CarSim 参数设置说明 - 前驱车（高架桥爬坡）\n');
    fprintf(fid, '============================================================\n\n');

    fprintf(fid, '【车辆设置】\n');
    fprintf(fid, '  Vehicle > Assembly > 选择前驱车辆模型\n');
    fprintf(fid, '  Vehicle > Body > Mass = 1500 kg\n');
    fprintf(fid, '  Vehicle > Body > Wheelbase = 2.7 m\n');
    fprintf(fid, '  Vehicle > Body > CG Height = 0.5 m\n\n');

    fprintf(fid, '【发动机设置】\n');
    fprintf(fid, '  Powertrain > Engine > Max Power = %.1f kW\n', params.fwd_power);
    fprintf(fid, '  Powertrain > Engine > Max Torque = %.1f Nm\n', params.fwd_power * 1000 / (5000 * pi / 30));
    fprintf(fid, '  Powertrain > Engine > Max RPM = 6000\n\n');

    fprintf(fid, '【传动系统设置】\n');
    fprintf(fid, '  Powertrain > Transmission > Type = Automatic\n');
    fprintf(fid, '  Powertrain > Transmission > Gears = 5\n');
    fprintf(fid, '  Powertrain > Drivetrain > Type = FWD (前驱)\n\n');

    fprintf(fid, '【轮胎设置】\n');
    fprintf(fid, '  Tire > Tire Model = Internal\n');
    fprintf(fid, '  Tire > Tire Radius = 0.31 m\n\n');

    fprintf(fid, '【道路设置】\n');
    fprintf(fid, '  Road > Road Model = 3D Road\n');
    fprintf(fid, '  Road > Profile > 前 %.1f m: 水平路面\n', params.bridge_length * 0.1);
    fprintf(fid, '  Road > Profile > %.1f m ~ %.1f m: 上坡 %.1f deg\n', ...
        params.bridge_length * 0.1, params.bridge_length, params.slope_angle);
    fprintf(fid, '  Road > Friction = %.2f\n', params.friction);
    fprintf(fid, '  Road > Width = 8.0 m\n\n');

    fprintf(fid, '【护栏设置】\n');
    fprintf(fid, '  Road > Barriers > 左侧护栏: 开启\n');
    fprintf(fid, '  Road > Barriers > 右侧护栏: 开启\n');
    fprintf(fid, '  Road > Barriers > 护栏高度 = 0.8 m\n');
    fprintf(fid, '  Road > Barriers > 护栏刚度 = 1e6 N/m\n\n');

    fprintf(fid, '【仿真设置】\n');
    fprintf(fid, '  Simulation > Stop Time = 30 s\n');
    fprintf(fid, '  Simulation > Time Step = 0.001 s\n\n');

    fprintf(fid, '【初始条件】\n');
    fprintf(fid, '  Initial Conditions > X = 0 m\n');
    fprintf(fid, '  Initial Conditions > Y = 0 m\n');
    fprintf(fid, '  Initial Conditions > Speed = 5 m/s (18 km/h)\n\n');

    fprintf(fid, '【输出设置】\n');
    fprintf(fid, '  Output > 选择以下变量:\n');
    fprintf(fid, '    - Time\n');
    fprintf(fid, '    - X (纵向位置)\n');
    fprintf(fid, '    - Z (垂直位置)\n');
    fprintf(fid, '    - Vx (纵向速度)\n');
    fprintf(fid, '    - Wheel Slip FL/FR/RL/RR (车轮滑移率)\n\n');

    fprintf(fid, '【运行仿真】\n');
    fprintf(fid, '  1. 点击 Run Control > Run\n');
    fprintf(fid, '  2. 等待仿真完成\n');
    fprintf(fid, '  3. 导出结果: Export > CSV\n');
    fprintf(fid, '  4. 保存文件名: results_FWD.csv\n');

    fclose(fid);
    fprintf('  已生成: %s\n', fwd_file);

    % 四驱车参数说明
    awd_file = fullfile(params.output_dir, 'carsim_instructions_AWD.txt');
    fid = fopen(awd_file, 'w');

    if fid == -1
        error('无法创建文件: %s', awd_file);
    end

    fprintf(fid, '============================================================\n');
    fprintf(fid, '  CarSim 参数设置说明 - 四驱车（高架桥爬坡）\n');
    fprintf(fid, '============================================================\n\n');

    fprintf(fid, '【车辆设置】\n');
    fprintf(fid, '  Vehicle > Assembly > 选择四驱车辆模型\n');
    fprintf(fid, '  Vehicle > Body > Mass = 1500 kg\n');
    fprintf(fid, '  Vehicle > Body > Wheelbase = 2.7 m\n');
    fprintf(fid, '  Vehicle > Body > CG Height = 0.5 m\n\n');

    fprintf(fid, '【发动机设置】\n');
    fprintf(fid, '  Powertrain > Engine > Max Power = %.1f kW\n', params.awd_power);
    fprintf(fid, '  Powertrain > Engine > Max Torque = %.1f Nm\n', params.awd_power * 1000 / (5000 * pi / 30));
    fprintf(fid, '  Powertrain > Engine > Max RPM = 6000\n\n');

    fprintf(fid, '【传动系统设置】\n');
    fprintf(fid, '  Powertrain > Transmission > Type = Automatic\n');
    fprintf(fid, '  Powertrain > Transmission > Gears = 5\n');
    fprintf(fid, '  Powertrain > Drivetrain > Type = AWD (四驱)\n');
    fprintf(fid, '  Powertrain > Drivetrain > Center Diff Ratio = 0.5\n');
    fprintf(fid, '  Powertrain > Drivetrain > Front Diff Type = OPEN\n');
    fprintf(fid, '  Powertrain > Drivetrain > Rear Diff Type = OPEN\n\n');

    fprintf(fid, '【轮胎设置】\n');
    fprintf(fid, '  Tire > Tire Model = Internal\n');
    fprintf(fid, '  Tire > Tire Radius = 0.31 m\n\n');

    fprintf(fid, '【道路设置】\n');
    fprintf(fid, '  Road > Road Model = 3D Road\n');
    fprintf(fid, '  Road > Profile > 前 %.1f m: 水平路面\n', params.bridge_length * 0.1);
    fprintf(fid, '  Road > Profile > %.1f m ~ %.1f m: 上坡 %.1f deg\n', ...
        params.bridge_length * 0.1, params.bridge_length, params.slope_angle);
    fprintf(fid, '  Road > Friction = %.2f\n', params.friction);
    fprintf(fid, '  Road > Width = 8.0 m\n\n');

    fprintf(fid, '【护栏设置】\n');
    fprintf(fid, '  Road > Barriers > 左侧护栏: 开启\n');
    fprintf(fid, '  Road > Barriers > 右侧护栏: 开启\n');
    fprintf(fid, '  Road > Barriers > 护栏高度 = 0.8 m\n');
    fprintf(fid, '  Road > Barriers > 护栏刚度 = 1e6 N/m\n\n');

    fprintf(fid, '【仿真设置】\n');
    fprintf(fid, '  Simulation > Stop Time = 30 s\n');
    fprintf(fid, '  Simulation > Time Step = 0.001 s\n\n');

    fprintf(fid, '【初始条件】\n');
    fprintf(fid, '  Initial Conditions > X = 0 m\n');
    fprintf(fid, '  Initial Conditions > Y = 0 m\n');
    fprintf(fid, '  Initial Conditions > Speed = 5 m/s (18 km/h)\n\n');

    fprintf(fid, '【输出设置】\n');
    fprintf(fid, '  Output > 选择以下变量:\n');
    fprintf(fid, '    - Time\n');
    fprintf(fid, '    - X (纵向位置)\n');
    fprintf(fid, '    - Z (垂直位置)\n');
    fprintf(fid, '    - Vx (纵向速度)\n');
    fprintf(fid, '    - Wheel Slip FL/FR/RL/RR (车轮滑移率)\n\n');

    fprintf(fid, '【运行仿真】\n');
    fprintf(fid, '  1. 点击 Run Control > Run\n');
    fprintf(fid, '  2. 等待仿真完成\n');
    fprintf(fid, '  3. 导出结果: Export > CSV\n');
    fprintf(fid, '  4. 保存文件名: results_AWD.csv\n');

    fclose(fid);
    fprintf('  已生成: %s\n', awd_file);
end

function generate_analysis_script(params)
    % generate_analysis_script 生成结果分析脚本

    script_file = fullfile(params.output_dir, 'analyze_results.m');
    fid = fopen(script_file, 'w');

    if fid == -1
        error('无法创建文件: %s', script_file);
    end

    fprintf(fid, '%% 仿真结果分析脚本\n');
    fprintf(fid, '%% 在 CarSim 仿真运行并导出结果后执行\n\n');

    fprintf(fid, 'clear; clc; close all;\n\n');

    fprintf(fid, '%% 参数设置\n');
    switch params.scene_type
        case 'bridge_slope'
            fprintf(fid, 'bridge_length = %.1f;    %% 高架桥长度 [m]\n', params.bridge_length);
            fprintf(fid, 'slope_angle = %.1f;      %% 坡度角度 [deg]\n', params.slope_angle);
            fprintf(fid, 'friction = %.2f;         %% 路面摩擦系数\n', params.friction);
            fprintf(fid, 'target_height = bridge_length * tan(slope_angle * pi / 180);\n\n');
        case 'cornering'
            fprintf(fid, 'curve_radius = %.1f;     %% 弯道半径 [m]\n', params.curve_radius);
            fprintf(fid, 'curve_angle = %.1f;      %% 弯道角度 [deg]\n', params.curve_angle);
            fprintf(fid, 'target_speed = %.1f;     %% 目标车速 [km/h]\n', params.vehicle_speed);
            fprintf(fid, 'max_lateral_acc = 0.8;   %% 最大横向加速度 [g]\n\n');
        case 'obstacle_avoidance'
            fprintf(fid, 'obstacle_pos = %.1f;     %% 障碍物位置 [m]\n', params.obstacle_position);
            fprintf(fid, 'obstacle_width = %.1f;   %% 障碍物宽度 [m]\n', params.obstacle_width);
            fprintf(fid, 'lane_width = %.1f;       %% 车道宽度 [m]\n', params.lane_width);
            fprintf(fid, 'target_speed = %.1f;     %% 目标车速 [km/h]\n', params.vehicle_speed);
            fprintf(fid, 'success_distance = obstacle_pos + 10;  %% 成功通过距离 [m]\n\n');
        case 'braking'
            fprintf(fid, 'initial_speed = %.1f;    %% 初始速度 [km/h]\n', params.initial_speed);
            fprintf(fid, 'target_distance = %.1f;  %% 目标制动距离 [m]\n', params.brake_distance);
            fprintf(fid, 'friction = %.2f;         %% 路面摩擦系数\n', params.friction);
            fprintf(fid, 'theoretical_distance = (initial_speed/3.6)^2 / (2 * 9.81 * friction);\n\n');
        case 'acceleration'
            fprintf(fid, 'target_speed = %.1f;     %% 目标速度 [km/h]\n', params.target_speed);
            fprintf(fid, 'target_distance = %.1f;  %% 目标加速距离 [m]\n', params.acceleration_distance);
            fprintf(fid, 'engine_power = %.1f;     %% 发动机功率 [kW]\n', params.engine_power);
            fprintf(fid, 'theoretical_time = (target_speed/3.6) / (engine_power * 1000 / (1500 * (target_speed/3.6)));\n\n');
    end

    fprintf(fid, '%% 读取 CarSim 导出的 CSV 文件\n');
    fprintf(fid, '%% 请确保结果文件在当前目录\n\n');

    fprintf(fid, '%% 读取结果\n');
    fprintf(fid, 'if exist(''results.csv'', ''file'')\n');
    fprintf(fid, '    data = csvread(''results.csv'', 1, 0);  %% 跳过标题行\n');
    fprintf(fid, '    time = data(:, 1);\n');
    fprintf(fid, '    x = data(:, 2);\n');
    fprintf(fid, '    z = data(:, 3);\n');
    fprintf(fid, '    vx = data(:, 4);\n');
    fprintf(fid, '    max_distance = max(x);\n');
    fprintf(fid, '    max_height = max(z);\n');
    fprintf(fid, '    avg_speed = mean(vx) * 3.6;  %% 转换为 km/h\n\n');

    fprintf(fid, '    %% 输出结果\n');
    fprintf(fid, '    fprintf(''===== 仿真结果 =====\\n'');\n');
    fprintf(fid, '    fprintf(''最大距离: %.1f m\\n'', max_distance);\n');
    fprintf(fid, '    fprintf(''最大高度: %.1f m\\n'', max_height);\n');
    fprintf(fid, '    fprintf(''平均速度: %.1f km/h\\n'', avg_speed);\n\n');

    fprintf(fid, '    %% 绘图\n');
    fprintf(fid, '    figure(''Position'', [100, 100, 1200, 800]);\n\n');

    fprintf(fid, '    %% 子图1: 轨迹\n');
    fprintf(fid, '    subplot(2, 2, 1);\n');
    fprintf(fid, '    plot(x, z, ''b-'', ''LineWidth'', 2);\n');
    fprintf(fid, '    xlabel(''X 位置 [m]'');\n');
    fprintf(fid, '    ylabel(''Z 高度 [m]'');\n');
    fprintf(fid, '    title(''车辆轨迹'');\n');
    fprintf(fid, '    grid on;\n\n');

    fprintf(fid, '    %% 子图2: 速度变化\n');
    fprintf(fid, '    subplot(2, 2, 2);\n');
    fprintf(fid, '    plot(time, vx * 3.6, ''b-'', ''LineWidth'', 2);\n');
    fprintf(fid, '    xlabel(''时间 [s]'');\n');
    fprintf(fid, '    ylabel(''速度 [km/h]'');\n');
    fprintf(fid, '    title(''速度变化'');\n');
    fprintf(fid, '    grid on;\n\n');

    fprintf(fid, '    %% 子图3: 位置变化\n');
    fprintf(fid, '    subplot(2, 2, 3);\n');
    fprintf(fid, '    plot(time, x, ''b-'', ''LineWidth'', 2);\n');
    fprintf(fid, '    xlabel(''时间 [s]'');\n');
    fprintf(fid, '    ylabel(''X 位置 [m]'');\n');
    fprintf(fid, '    title(''纵向位置'');\n');
    fprintf(fid, '    grid on;\n\n');

    fprintf(fid, '    %% 子图4: 结果摘要\n');
    fprintf(fid, '    subplot(2, 2, 4);\n');
    fprintf(fid, '    text(0.5, 0.7, sprintf(''最大距离: %.1f m'', max_distance), ...\n');
    fprintf(fid, '        ''HorizontalAlignment'', ''center'', ''FontSize'', 14);\n');
    fprintf(fid, '    text(0.5, 0.5, sprintf(''最大高度: %.1f m'', max_height), ...\n');
    fprintf(fid, '        ''HorizontalAlignment'', ''center'', ''FontSize'', 14);\n');
    fprintf(fid, '    text(0.5, 0.3, sprintf(''平均速度: %.1f km/h'', avg_speed), ...\n');
    fprintf(fid, '        ''HorizontalAlignment'', ''center'', ''FontSize'', 14);\n');
    fprintf(fid, '    axis off;\n');
    fprintf(fid, '    title(''结果摘要'');\n\n');

    fprintf(fid, '    %% 保存图形\n');
    fprintf(fid, '    saveas(gcf, ''simulation_results.png'', ''png'');\n');
    fprintf(fid, '    fprintf(''结果已保存: simulation_results.png\\n'');\n');
    fprintf(fid, 'else\n');
    fprintf(fid, '    error(''未找到结果文件，请先运行 CarSim 仿真并导出结果'');\n');
    fprintf(fid, 'end\n');

    fclose(fid);
    fprintf('  已生成: %s\n', script_file);
end

%% 场景参数生成函数

function params = bridge_slope_scenario(params)
    % bridge_slope_scenario 高架桥爬坡场景

    if ~isfield(params, 'bridge_length'), params.bridge_length = 100; end
    if ~isfield(params, 'slope_angle'), params.slope_angle = 15; end
    if ~isfield(params, 'friction'), params.friction = 0.2; end
    if ~isfield(params, 'fwd_power'), params.fwd_power = 100; end
    if ~isfield(params, 'awd_power'), params.awd_power = 100; end

    assert(params.bridge_length > 0, '高架桥长度必须为正数');
    assert(params.slope_angle > 0 && params.slope_angle < 45, '坡度角度应在 0-45 度之间');
    assert(params.friction > 0 && params.friction <= 1, '摩擦系数应在 0-1 之间');
end

function params = cornering_scenario(params)
    % cornering_scenario 弯道操控场景

    if ~isfield(params, 'curve_radius'), params.curve_radius = 50; end
    if ~isfield(params, 'curve_angle'), params.curve_angle = 90; end
    if ~isfield(params, 'road_width'), params.road_width = 7; end
    if ~isfield(params, 'vehicle_speed'), params.vehicle_speed = 60; end

    assert(params.curve_radius > 0, '弯道半径必须为正数');
    assert(params.curve_angle > 0 && params.curve_angle <= 360, '弯道角度应在 0-360 度之间');
end

function params = obstacle_avoidance_scenario(params)
    % obstacle_avoidance_scenario 紧急避障场景

    if ~isfield(params, 'obstacle_position'), params.obstacle_position = 50; end
    if ~isfield(params, 'obstacle_width'), params.obstacle_width = 2; end
    if ~isfield(params, 'lane_width'), params.lane_width = 3.5; end
    if ~isfield(params, 'vehicle_speed'), params.vehicle_speed = 80; end

    assert(params.obstacle_position > 0, '障碍物位置必须为正数');
end

function params = braking_scenario(params)
    % braking_scenario 制动性能场景

    if ~isfield(params, 'initial_speed'), params.initial_speed = 100; end
    if ~isfield(params, 'brake_distance'), params.brake_distance = 50; end
    if ~isfield(params, 'friction'), params.friction = 0.8; end
    if ~isfield(params, 'vehicle_mass'), params.vehicle_mass = 1500; end

    assert(params.initial_speed > 0, '初始速度必须为正数');
end

function params = acceleration_scenario(params)
    % acceleration_scenario 加速性能场景

    if ~isfield(params, 'target_speed'), params.target_speed = 100; end
    if ~isfield(params, 'acceleration_distance'), params.acceleration_distance = 200; end
    if ~isfield(params, 'engine_power'), params.engine_power = 150; end
    if ~isfield(params, 'vehicle_mass'), params.vehicle_mass = 1500; end

    assert(params.target_speed > 0, '目标速度必须为正数');
end
