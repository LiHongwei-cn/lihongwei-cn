%% 高架桥仿真主脚本 - 燕子矶场景
% MATLAB R2016b 兼容
% 用于 CarSim 2019.0
% 两辆车同时上高架，四驱成功，前驱/后驱打滑失败

function run_bridge_simulation(params)
    % run_bridge_simulation 运行高架桥仿真
    %
    % 输入参数：
    %   params.bridge_length    - 高架桥长度 [m]
    %   params.bridge_width     - 高架桥宽度 [m]
    %   params.slope_angle      - 坡度角度 [deg]
    %   params.friction         - 路面摩擦系数
    %   params.fwd_power        - 前驱车功率 [kW]
    %   params.awd_power        - 四驱车功率 [kW]
    %   params.output_dir       - 输出目录

    %% 参数验证
    assert(params.bridge_length > 0, '高架桥长度必须为正数');
    assert(params.bridge_width > 0, '高架桥宽度必须为正数');
    assert(params.slope_angle > 0 && params.slope_angle < 45, '坡度角度应在 0-45 度之间');
    assert(params.friction > 0 && params.friction <= 1, '摩擦系数应在 0-1 之间');
    assert(params.fwd_power > 0, '前驱车功率必须为正数');
    assert(params.awd_power > 0, '四驱车功率必须为正数');

    %% 创建输出目录
    if ~exist(params.output_dir, 'dir')
        mkdir(params.output_dir);
    end

    fprintf('============================================================\n');
    fprintf('  高架桥仿真 - 燕子矶场景\n');
    fprintf('  两辆车同时上高架，测试不同驱动类型的爬坡能力\n');
    fprintf('============================================================\n\n');

    %% 生成场景文件
    fprintf('>>> 步骤 1: 生成高架桥场景...\n');
    bridge_params.bridge_length = params.bridge_length;
    bridge_params.bridge_width = params.bridge_width;
    bridge_params.slope_angle = params.slope_angle;
    bridge_params.guardrail_height = 0.8;
    bridge_params.friction = params.friction;
    bridge_params.output_dir = params.output_dir;
    generate_bridge_scenario(bridge_params);

    %% 配置前驱车
    fprintf('\n>>> 步骤 2: 配置前驱车...\n');
    fwd_vehicle = configure_vehicle('FWD', params.fwd_power);
    save_vehicle_to_carsim(fwd_vehicle, params.output_dir);

    %% 配置四驱车
    fprintf('\n>>> 步骤 3: 配置四驱车...\n');
    awd_vehicle = configure_vehicle('AWD', params.awd_power);
    save_vehicle_to_carsim(awd_vehicle, params.output_dir);

    %% 创建 CarSim 仿真脚本
    fprintf('\n>>> 步骤 4: 创建 CarSim 仿真脚本...\n');
    create_carsim_simulation_script(params, fwd_vehicle, awd_vehicle);

    %% 运行仿真
    fprintf('\n>>> 步骤 5: 运行 CarSim 仿真...\n');
    run_carsim_simulation(params);

    %% 分析结果
    fprintf('\n>>> 步骤 6: 分析仿真结果...\n');
    results = analyze_simulation_results(params);

    %% 生成可视化
    fprintf('\n>>> 步骤 7: 生成可视化结果...\n');
    visualize_results(params, results);

    %% 输出总结
    fprintf('\n============================================================\n');
    fprintf('  仿真完成!\n');
    fprintf('  结果目录: %s\n', params.output_dir);
    fprintf('============================================================\n');
end

function create_carsim_simulation_script(params, fwd_vehicle, awd_vehicle)
    % create_carsim_simulation_script 创建 CarSim 仿真脚本
    %
    % 生成 .par 文件用于 CarSim 运行

    % 前驱车仿真文件
    fwd_file = fullfile(params.output_dir, 'simulation_FWD.par');
    create_vehicle_simulation(fwd_file, fwd_vehicle, params, 'FWD');

    % 四驱车仿真文件
    awd_file = fullfile(params.output_dir, 'simulation_AWD.par');
    create_vehicle_simulation(awd_file, awd_vehicle, params, 'AWD');

    fprintf('仿真脚本已生成:\n');
    fprintf('  前驱车: %s\n', fwd_file);
    fprintf('  四驱车: %s\n', awd_file);
end

function create_vehicle_simulation(filename, vehicle_params, params, drive_type)
    % create_vehicle_simulation 创建单车辆仿真文件

    fid = fopen(filename, 'w');

    if fid == -1
        error('无法创建文件: %s', filename);
    end

    % 文件头
    fprintf(fid, '! CarSim Simulation File\n');
    fprintf(fid, '! 场景: 高架桥爬坡仿真\n');
    fprintf(fid, '! 车辆: %s\n', drive_type);
    fprintf(fid, '! 生成时间: %s\n', datestr(now));
    fprintf(fid, '\n');

    % 仿真参数
    fprintf(fid, 'SIMULATION_PARAMETERS\n');
    fprintf(fid, '  STOP_TIME = 30.0\n');      % 仿真时长 [s]
    fprintf(fid, '  TIME_STEP = 0.001\n');       % 时间步长 [s]
    fprintf(fid, '  SOLVER = EULER\n');          % 求解器（前向欧拉）
    fprintf(fid, 'END_SIMULATION_PARAMETERS\n');
    fprintf(fid, '\n');

    % 初始条件
    fprintf(fid, 'INITIAL_CONDITIONS\n');
    fprintf(fid, '  X = 0.0\n');                 % 初始 X 位置 [m]
    fprintf(fid, '  Y = 0.0\n');                 % 初始 Y 位置 [m]
    fprintf(fid, '  Z = 0.0\n');                 % 初始 Z 位置 [m]
    fprintf(fid, '  YAW = 0.0\n');               % 初始横摆角 [deg]
    fprintf(fid, '  VX = 5.0\n');                % 初始纵向速度 [m/s]
    fprintf(fid, '  VY = 0.0\n');                % 初始横向速度 [m/s]
    fprintf(fid, '  VZ = 0.0\n');                % 初始垂直速度 [m/s]
    fprintf(fid, 'END_INITIAL_CONDITIONS\n');
    fprintf(fid, '\n');

    % 道路文件引用
    fprintf(fid, 'ROAD_FILE\n');
    fprintf(fid, '  FILENAME = bridge_road.road\n');
    fprintf(fid, 'END_ROAD_FILE\n');
    fprintf(fid, '\n');

    % 车辆文件引用
    fprintf(fid, 'VEHICLE_FILE\n');
    fprintf(fid, '  FILENAME = vehicle_%s.par\n', drive_type);
    fprintf(fid, 'END_VEHICLE_FILE\n');
    fprintf(fid, '\n');

    % 轮胎摩擦文件引用
    fprintf(fid, 'TIRE_FILE\n');
    fprintf(fid, '  FILENAME = bridge_friction.tir\n');
    fprintf(fid, 'END_TIRE_FILE\n');
    fprintf(fid, '\n');

    % 护栏文件引用
    fprintf(fid, 'GUARDRAIL_FILE\n');
    fprintf(fid, '  FILENAME = bridge_guardrail.par\n');
    fprintf(fid, 'END_GUARDRAIL_FILE\n');
    fprintf(fid, '\n');

    % 输入控制（油门开度）
    fprintf(fid, 'INPUT_CONTROL\n');
    fprintf(fid, '  ! 时间 [s], 油门开度 [0-1]\n');
    fprintf(fid, '  0.0, 0.0\n');      % 初始：无油门
    fprintf(fid, '  0.5, 0.5\n');      % 0.5s：半油门
    fprintf(fid, '  1.0, 1.0\n');      % 1.0s：全油门
    fprintf(fid, '  30.0, 1.0\n');     % 保持全油门
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
    fprintf(fid, '  WHEEL_SLIP_FL\n');  % 前左轮滑移率
    fprintf(fid, '  WHEEL_SLIP_FR\n');  % 前右轮滑移率
    fprintf(fid, '  WHEEL_SLIP_RL\n');  % 后左轮滑移率
    fprintf(fid, '  WHEEL_SLIP_RR\n');  % 后右轮滑移率
    fprintf(fid, '  ENGINE_TORQUE\n');  % 发动机扭矩
    fprintf(fid, '  DRIVE_TORQUE_FL\n'); % 前左轮驱动扭矩
    fprintf(fid, '  DRIVE_TORQUE_FR\n'); % 前右轮驱动扭矩
    fprintf(fid, '  DRIVE_TORQUE_RL\n'); % 后左轮驱动扭矩
    fprintf(fid, '  DRIVE_TORQUE_RR\n'); % 后右轮驱动扭矩
    fprintf(fid, 'END_OUTPUT_VARIABLES\n');

    fclose(fid);
end

function run_carsim_simulation(params)
    % run_carsim_simulation 运行 CarSim 仿真
    %
    % 注意：此函数需要在 CarSim 环境中运行

    fprintf('正在运行 CarSim 仿真...\n');
    fprintf('请在 CarSim 中加载以下文件:\n');
    fprintf('  1. simulation_FWD.par (前驱车)\n');
    fprintf('  2. simulation_AWD.par (四驱车)\n');
    fprintf('\n');
    fprintf('或者使用 CarSim 的批处理功能同时运行两个仿真。\n');
    fprintf('\n');

    % 生成批处理脚本
    batch_file = fullfile(params.output_dir, 'run_batch.bat');
    create_batch_script(batch_file, params);

    fprintf('批处理脚本已生成: %s\n', batch_file);
end

function create_batch_script(filename, params)
    % create_batch_script 创建 CarSim 批处理脚本

    fid = fopen(filename, 'w');

    if fid == -1
        error('无法创建文件: %s', filename);
    end

    fprintf(fid, '@echo off\n');
    fprintf(fid, 'echo ========================================\n');
    fprintf(fid, 'echo  高架桥仿真批处理脚本\n');
    fprintf(fid, 'echo ========================================\n');
    fprintf(fid, 'echo.\n');
    fprintf(fid, 'echo 运行前驱车仿真...\n');
    fprintf(fid, 'CarSim.exe -run simulation_FWD.par\n');
    fprintf(fid, 'echo.\n');
    fprintf(fid, 'echo 运行四驱车仿真...\n');
    fprintf(fid, 'CarSim.exe -run simulation_AWD.par\n');
    fprintf(fid, 'echo.\n');
    fprintf(fid, 'echo 仿真完成!\n');
    fprintf(fid, 'pause\n');

    fclose(fid);
end

function results = analyze_simulation_results(params)
    % analyze_simulation_results 分析仿真结果
    %
    % 输出：
    %   results - 结构体，包含分析结果

    % 这里需要读取 CarSim 的输出文件
    % 假设 CarSim 输出 CSV 格式文件

    fprintf('分析仿真结果...\n');

    % 尝试读取前驱车结果
    fwd_file = fullfile(params.output_dir, 'results_FWD.csv');
    if exist(fwd_file, 'file')
        fwd_data = csvread(fwd_file, 1, 0);  % 跳过标题行
        results.fwd.time = fwd_data(:, 1);
        results.fwd.x = fwd_data(:, 2);
        results.fwd.z = fwd_data(:, 4);
        results.fwd.vx = fwd_data(:, 5);
        results.fwd.wheel_slip = fwd_data(:, 9:12);
    else
        fprintf('警告: 未找到前驱车结果文件\n');
        results.fwd = [];
    end

    % 尝试读取四驱车结果
    awd_file = fullfile(params.output_dir, 'results_AWD.csv');
    if exist(awd_file, 'file')
        awd_data = csvread(awd_file, 1, 0);
        results.awd.time = awd_data(:, 1);
        results.awd.x = awd_data(:, 2);
        results.awd.z = awd_data(:, 4);
        results.awd.vx = awd_data(:, 5);
        results.awd.wheel_slip = awd_data(:, 9:12);
    else
        fprintf('警告: 未找到四驱车结果文件\n');
        results.awd = [];
    end

    % 分析爬坡结果
    if ~isempty(results.fwd) && ~isempty(results.awd)
        % 计算最大爬坡距离
        results.fwd.max_distance = max(results.fwd.x);
        results.awd.max_distance = max(results.awd.x);

        % 计算最大高度
        results.fwd.max_height = max(results.fwd.z);
        results.awd.max_height = max(results.awd.z);

        % 判断是否成功爬坡
        bridge_height = params.bridge_length * tan(params.slope_angle * pi / 180);
        results.fwd.success = results.fwd.max_height >= bridge_height * 0.9;
        results.awd.success = results.awd.max_height >= bridge_height * 0.9;

        % 计算平均滑移率
        results.fwd.avg_slip = mean(results.fwd.wheel_slip(:));
        results.awd.avg_slip = mean(results.awd.wheel_slip(:));

        fprintf('\n===== 仿真结果分析 =====\n');
        fprintf('前驱车:\n');
        fprintf('  最大距离: %.1f m\n', results.fwd.max_distance);
        fprintf('  最大高度: %.1f m\n', results.fwd.max_height);
        fprintf('  平均滑移率: %.2f%%\n', results.fwd.avg_slip * 100);
        fprintf('  爬坡结果: %s\n', conditional(results.fwd.success, '成功', '失败（打滑）'));
        fprintf('\n');
        fprintf('四驱车:\n');
        fprintf('  最大距离: %.1f m\n', results.awd.max_distance);
        fprintf('  最大高度: %.1f m\n