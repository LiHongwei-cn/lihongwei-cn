%% 通用 CarSim 仿真主脚本
% MATLAB R2016b 兼容
% 支持多种仿真场景：高架桥爬坡、弯道操控、紧急避障等

function run_simulation(params)
    % run_simulation 运行通用 CarSim 仿真
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
    fprintf('  CarSim-AI 通用仿真工具\n');
    fprintf('  场景类型: %s\n', params.scene_type);
    fprintf('============================================================\n\n');

    %% 根据场景类型生成参数
    fprintf('>>> 步骤 1: 生成场景参数...\n');
    params = generate_scenario(params);

    %% 生成场景文件
    fprintf('\n>>> 步骤 2: 生成场景文件...\n');
    generate_scenario_files(params);

    %% 配置车辆
    fprintf('\n>>> 步骤 3: 配置车辆参数...\n');
    configure_vehicles(params);

    %% 创建仿真脚本
    fprintf('\n>>> 步骤 4: 创建仿真脚本...\n');
    create_simulation_scripts(params);

    %% 运行仿真
    fprintf('\n>>> 步骤 5: 运行仿真...\n');
    run_carsim_simulation(params);

    %% 分析结果
    fprintf('\n>>> 步骤 6: 分析仿真结果...\n');
    results = analyze_results(params);

    %% 生成可视化
    fprintf('\n>>> 步骤 7: 生成可视化结果...\n');
    visualize_results(params, results);

    %% 输出总结
    fprintf('\n============================================================\n');
    fprintf('  仿真完成!\n');
    fprintf('  结果目录: %s\n', params.output_dir);
    fprintf('============================================================\n');
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

function generate_scenario_files(params)
    % generate_scenario_files 生成场景文件

    switch params.scene_type
        case 'bridge_slope'
            generate_bridge_scenario(params);
        case 'cornering'
            generate_cornering_scenario(params);
        case 'obstacle_avoidance'
            generate_obstacle_avoidance_scenario(params);
        case 'braking'
            generate_braking_scenario(params);
        case 'acceleration'
            generate_acceleration_scenario(params);
    end
end

function configure_vehicles(params)
    % configure_vehicles 配置车辆参数

    % 根据场景类型配置车辆
    if isfield(params, 'fwd_power')
        fwd_vehicle = configure_vehicle('FWD', params.fwd_power);
        save_vehicle_to_carsim(fwd_vehicle, params.output_dir);
    end

    if isfield(params, 'rwd_power')
        rwd_vehicle = configure_vehicle('RWD', params.rwd_power);
        save_vehicle_to_carsim(rwd_vehicle, params.output_dir);
    end

    if isfield(params, 'awd_power')
        awd_vehicle = configure_vehicle('AWD', params.awd_power);
        save_vehicle_to_carsim(awd_vehicle, params.output_dir);
    end

    % 默认车辆（如果没有指定功率）
    if ~isfield(params, 'fwd_power') && ~isfield(params, 'rwd_power') && ~isfield(params, 'awd_power')
        default_vehicle = configure_vehicle('FWD', 100);
        save_vehicle_to_carsim(default_vehicle, params.output_dir);
    end
end

function create_simulation_scripts(params)
    % create_simulation_scripts 创建仿真脚本

    % 根据车辆类型创建仿真脚本
    if isfield(params, 'fwd_power')
        create_vehicle_simulation_script(params, 'FWD');
    end

    if isfield(params, 'rwd_power')
        create_vehicle_simulation_script(params, 'RWD');
    end

    if isfield(params, 'awd_power')
        create_vehicle_simulation_script(params, 'AWD');
    end

    % 默认车辆
    if ~isfield(params, 'fwd_power') && ~isfield(params, 'rwd_power') && ~isfield(params, 'awd_power')
        create_vehicle_simulation_script(params, 'FWD');
    end
end

function create_vehicle_simulation_script(params, drive_type)
    % create_vehicle_simulation_script 创建单车辆仿真脚本

    filename = fullfile(params.output_dir, sprintf('simulation_%s.par', drive_type));
    fid = fopen(filename, 'w');

    if fid == -1
        error('无法创建文件: %s', filename);
    end

    % 文件头
    fprintf(fid, '! CarSim Simulation File\n');
    fprintf(fid, '! 场景: %s\n', params.scene_type);
    fprintf(fid, '! 车辆: %s\n', drive_type);
    fprintf(fid, '! 生成时间: %s\n', datestr(now));
    fprintf(fid, '\n');

    % 仿真参数
    fprintf(fid, 'SIMULATION_PARAMETERS\n');
    fprintf(fid, '  STOP_TIME = 30.0\n');
    fprintf(fid, '  TIME_STEP = 0.001\n');
    fprintf(fid, '  SOLVER = EULER\n');
    fprintf(fid, 'END_SIMULATION_PARAMETERS\n');
    fprintf(fid, '\n');

    % 初始条件
    fprintf(fid, 'INITIAL_CONDITIONS\n');
    fprintf(fid, '  X = 0.0\n');
    fprintf(fid, '  Y = 0.0\n');
    fprintf(fid, '  Z = 0.0\n');
    fprintf(fid, '  YAW = 0.0\n');
    fprintf(fid, '  VX = 5.0\n');
    fprintf(fid, '  VY = 0.0\n');
    fprintf(fid, '  VZ = 0.0\n');
    fprintf(fid, 'END_INITIAL_CONDITIONS\n');
    fprintf(fid, '\n');

    % 文件引用
    fprintf(fid, 'ROAD_FILE\n');
    fprintf(fid, '  FILENAME = scenario_road.road\n');
    fprintf(fid, 'END_ROAD_FILE\n');
    fprintf(fid, '\n');

    fprintf(fid, 'VEHICLE_FILE\n');
    fprintf(fid, '  FILENAME = vehicle_%s.par\n', drive_type);
    fprintf(fid, 'END_VEHICLE_FILE\n');
    fprintf(fid, '\n');

    fprintf(fid, 'TIRE_FILE\n');
    fprintf(fid, '  FILENAME = scenario_tire.tir\n');
    fprintf(fid, 'END_TIRE_FILE\n');
    fprintf(fid, '\n');

    % 输入控制
    fprintf(fid, 'INPUT_CONTROL\n');
    fprintf(fid, '  ! 时间 [s], 油门开度 [0-1]\n');
    fprintf(fid, '  0.0, 0.0\n');
    fprintf(fid, '  0.5, 0.5\n');
    fprintf(fid, '  1.0, 1.0\n');
    fprintf(fid, '  30.0, 1.0\n');
    fprintf(fid, 'END_INPUT_CONTROL\n');
    fprintf(fid, '\n');

    % 输出变量
    fprintf(fid, 'OUTPUT_VARIABLES\n');
    fprintf(fid, '  TIME\n');
    fprintf(fid, '  X\n');
    fprintf(fid, '  Y\n');
    fprintf(fid, '  Z\n');
    fprintf(fid, '  VX\n');
    fprintf(fid, '  VY\n');
    fprintf(fid, '  VZ\n');
    fprintf(fid, '  YAW\n');
    fprintf(fid, '  WHEEL_SLIP_FL\n');
    fprintf(fid, '  WHEEL_SLIP_FR\n');
    fprintf(fid, '  WHEEL_SLIP_RL\n');
    fprintf(fid, '  WHEEL_SLIP_RR\n');
    fprintf(fid, 'END_OUTPUT_VARIABLES\n');

    fclose(fid);
end

function run_carsim_simulation(params)
    % run_carsim_simulation 运行 CarSim 仿真

    fprintf('正在准备 CarSim 仿真...\n');
    fprintf('请在 CarSim 中加载以下文件:\n');

    if isfield(params, 'fwd_power')
        fprintf('  - simulation_FWD.par (前驱车)\n');
    end
    if isfield(params, 'rwd_power')
        fprintf('  - simulation_RWD.par (后驱车)\n');
    end
    if isfield(params, 'awd_power')
        fprintf('  - simulation_AWD.par (四驱车)\n');
    end

    fprintf('\n');

    % 生成批处理脚本
    batch_file = fullfile(params.output_dir, 'run_batch.bat');
    create_batch_script(batch_file, params);

    fprintf('批处理脚本已生成: %s\n', batch_file);
end

function create_batch_script(filename, params)
    % create_batch_script 创建批处理脚本

    fid = fopen(filename, 'w');

    if fid == -1
        error('无法创建文件: %s', filename);
    end

    fprintf(fid, '@echo off\n');
    fprintf(fid, 'echo ========================================\n');
    fprintf(fid, 'echo  CarSim-AI 仿真批处理脚本\n');
    fprintf(fid, 'echo  场景: %s\n', params.scene_type);
    fprintf(fid, 'echo ========================================\n');
    fprintf(fid, 'echo.\n');

    if isfield(params, 'fwd_power')
        fprintf(fid, 'echo 运行前驱车仿真...\n');
        fprintf(fid, 'CarSim.exe -run simulation_FWD.par\n');
        fprintf(fid, 'echo.\n');
    end

    if isfield(params, 'rwd_power')
        fprintf(fid, 'echo 运行后驱车仿真...\n');
        fprintf(fid, 'CarSim.exe -run simulation_RWD.par\n');
        fprintf(fid, 'echo.\n');
    end

    if isfield(params, 'awd_power')
        fprintf(fid, 'echo 运行四驱车仿真...\n');
        fprintf(fid, 'CarSim.exe -run simulation_AWD.par\n');
        fprintf(fid, 'echo.\n');
    end

    fprintf(fid, 'echo 仿真完成!\n');
    fprintf(fid, 'pause\n');

    fclose(fid);
end

function results = analyze_results(params)
    % analyze_results 分析仿真结果

    fprintf('分析仿真结果...\n');

    % 初始化结果
    results = struct();

    % 尝试读取各车辆结果
    if isfield(params, 'fwd_power')
        fwd_file = fullfile(params.output_dir, 'results_FWD.csv');
        if exist(fwd_file, 'file')
            results.fwd = read_vehicle_results(fwd_file);
        end
    end

    if isfield(params, 'rwd_power')
        rwd_file = fullfile(params.output_dir, 'results_RWD.csv');
        if exist(rwd_file, 'file')
            results.rwd = read_vehicle_results(rwd_file);
        end
    end

    if isfield(params, 'awd_power')
        awd_file = fullfile(params.output_dir, 'results_AWD.csv');
        if exist(awd_file, 'file')
            results.awd = read_vehicle_results(awd_file);
        end
    end

    % 输出分析结果
    fprintf('\n===== 仿真结果分析 =====\n');

    if isfield(results, 'fwd')
        fprintf('前驱车:\n');
        fprintf('  最大距离: %.1f m\n', results.fwd.max_distance);
        fprintf('  最大高度: %.1f m\n', results.fwd.max_height);
        fprintf('  平均滑移率: %.2f%%\n', results.fwd.avg_slip * 100);
    end

    if isfield(results, 'rwd')
        fprintf('后驱车:\n');
        fprintf('  最大距离: %.1f m\n', results.rwd.max_distance);
        fprintf('  最大高度: %.1f m\n', results.rwd.max_height);
        fprintf('  平均滑移率: %.2f%%\n', results.rwd.avg_slip * 100);
    end

    if isfield(results, 'awd')
        fprintf('四驱车:\n');
        fprintf('  最大距离: %.1f m\n', results.awd.max_distance);
        fprintf('  最大高度: %.1f m\n', results.awd.max_height);
        fprintf('  平均滑移率: %.2f%%\n', results.awd.avg_slip * 100);
    end
end

function results = read_vehicle_results(filename)
    % read_vehicle_results 读取单车辆仿真结果

    data = csvread(filename, 1, 0);  % 跳过标题行

    results.time = data(:, 1);
    results.x = data(:, 2);
    results.y = data(:, 3);
    results.z = data(:, 4);
    results.vx = data(:, 5);
    results.vy = data(:, 6);
    results.vz = data(:, 7);
    results.yaw = data(:, 8);
    results.wheel_slip = data(:, 9:12);

    % 计算统计量
    results.max_distance = max(results.x);
    results.max_height = max(results.z);
    results.avg_slip = mean(results.wheel_slip(:));
end

%% 场景生成函数

function params = bridge_slope_scenario(params)
    % bridge_slope_scenario 高架桥爬坡场景

    % 设置默认值
    if ~isfield(params, 'bridge_length')
        params.bridge_length = 100;
    end
    if ~isfield(params, 'bridge_width')
        params.bridge_width = 8;
    end
    if ~isfield(params, 'slope_angle')
        params.slope_angle = 15;
    end
    if ~isfield(params, 'friction')
        params.friction = 0.2;
    end
    if ~isfield(params, 'guardrail_height')
        params.guardrail_height = 0.8;
    end

    % 验证参数
    assert(params.bridge_length > 0, '高架桥长度必须为正数');
    assert(params.bridge_width > 0, '高架桥宽度必须为正数');
    assert(params.slope_angle > 0 && params.slope_angle < 45, '坡度角度应在 0-45 度之间');
    assert(params.friction > 0 && params.friction <= 1, '摩擦系数应在 0-1 之间');
end

function params = cornering_scenario(params)
    % cornering_scenario 弯道操控场景

    % 设置默认值
    if ~isfield(params, 'curve_radius')
        params.curve_radius = 50;
    end
    if ~isfield(params, 'curve_angle')
        params.curve_angle = 90;
    end
    if ~isfield(params, 'road_width')
        params.road_width = 7;
    end
    if ~isfield(params, 'vehicle_speed')
        params.vehicle_speed = 60;
    end

    % 验证参数
    assert(params.curve_radius > 0, '弯道半径必须为正数');
    assert(params.curve_angle > 0 && params.curve_angle <= 360, '弯道角度应在 0-360 度之间');
    assert(params.road_width > 0, '道路宽度必须为正数');
    assert(params.vehicle_speed > 0, '车速必须为正数');
end

function params = obstacle_avoidance_scenario(params)
    % obstacle_avoidance_scenario 紧急避障场景

    % 设置默认值
    if ~isfield(params, 'obstacle_position')
        params.obstacle_position = 50;
    end
    if ~isfield(params, 'obstacle_width')
        params.obstacle_width = 2;
    end
    if ~isfield(params, 'lane_width')
        params.lane_width = 3.5;
    end
    if ~isfield(params, 'vehicle_speed')
        params.vehicle_speed = 80;
    end

    % 验证参数
    assert(params.obstacle_position > 0, '障碍物位置必须为正数');
    assert(params.obstacle_width > 0, '障碍物宽度必须为正数');
    assert(params.lane_width > 0, '车道宽度必须为正数');
    assert(params.vehicle_speed > 0, '车速必须为正数');
end

function params = braking_scenario(params)
    % braking_scenario 制动性能场景

    % 设置默认值
    if ~isfield(params, 'initial_speed')
        params.initial_speed = 100;
    end
    if ~isfield(params, 'brake_distance')
        params.brake_distance = 50;
    end
    if ~isfield(params, 'friction')
        params.friction = 0.8;
    end
    if ~isfield(params, 'vehicle_mass')
        params.vehicle_mass = 1500;
    end

    % 验证参数
    assert(params.initial_speed > 0, '初始速度必须为正数');
    assert(params.brake_distance > 0, '制动距离必须为正数');
    assert(params.friction > 0 && params.friction <= 1, '摩擦系数应在 0-1 之间');
    assert(params.vehicle_mass > 0, '车辆质量必须为正数');
end

function params = acceleration_scenario(params)
    % acceleration_scenario 加速性能场景

    % 设置默认值
    if ~isfield(params, 'target_speed')
        params.target_speed = 100;
    end
    if ~isfield(params, 'acceleration_distance')
        params.acceleration_distance = 200;
    end
    if ~isfield(params, 'engine_power')
        params.engine_power = 150;
    end
    if ~isfield(params, 'vehicle_mass')
        params.vehicle_mass = 1500;
    end

    % 验证参数
    assert(params.target_speed > 0, '目标速度必须为正数');
    assert(params.acceleration_distance > 0, '加速距离必须为正数');
    assert(params.engine_power > 0, '发动机功率必须为正数');
    assert(params.vehicle_mass > 0, '车辆质量必须为正数');
end
