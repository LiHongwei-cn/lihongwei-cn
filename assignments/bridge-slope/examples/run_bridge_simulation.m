%% 高架桥仿真 - 燕子矶场景（纯 CarSim 2019.0）
% MATLAB R2016b 兼容
% 本脚本仅用于生成参数和分析结果
% 仿真完全在 CarSim 内部运行
%
% 使用方法：
%   1. 运行本脚本生成参数文件
%   2. 在 CarSim 中手动输入参数
%   3. 在 CarSim 中点击 Run 运行仿真
%   4. 导出结果后运行 analyze_results.m 分析

function run_bridge_simulation(params)
    % run_bridge_simulation 生成高架桥仿真参数
    %
    % 输入参数：
    %   params.bridge_length    - 高架桥长度 [m]
    %   params.slope_angle      - 坡度角度 [deg]
    %   params.friction         - 路面摩擦系数 (0.1-0.3)
    %   params.fwd_power        - 前驱车功率 [kW]
    %   params.awd_power        - 四驱车功率 [kW]
    %   params.output_dir       - 输出目录

    %% 参数验证
    if ~isfield(params, 'bridge_length'), params.bridge_length = 100; end
    if ~isfield(params, 'slope_angle'), params.slope_angle = 15; end
    if ~isfield(params, 'friction'), params.friction = 0.2; end
    if ~isfield(params, 'fwd_power'), params.fwd_power = 100; end
    if ~isfield(params, 'awd_power'), params.awd_power = 100; end
    if ~isfield(params, 'output_dir'), params.output_dir = './output'; end

    %% 创建输出目录
    if ~exist(params.output_dir, 'dir')
        mkdir(params.output_dir);
    end

    fprintf('============================================================\n');
    fprintf('  高架桥仿真 - 燕子矶场景（纯 CarSim）\n');
    fprintf('============================================================\n\n');

    %% 计算坡度参数
    slope_rad = params.slope_angle * pi / 180;
    bridge_height = params.bridge_length * tan(slope_rad);
    slope_length = params.bridge_length / cos(slope_rad);

    fprintf('场景参数:\n');
    fprintf('  高架桥长度: %.1f m\n', params.bridge_length);
    fprintf('  坡度角度: %.1f deg\n', params.slope_angle);
    fprintf('  路面摩擦: %.2f\n', params.friction);
    fprintf('  坡面长度: %.1f m\n', slope_length);
    fprintf('  高度提升: %.1f m\n', bridge_height);
    fprintf('\n');

    %% 生成 CarSim 参数说明文件
    fprintf('>>> 步骤 1: 生成 CarSim 参数说明...\n');
    generate_carsim_instructions(params);

    %% 生成结果分析脚本
    fprintf('\n>>> 步骤 2: 生成结果分析脚本...\n');
    generate_analysis_script(params);

    %% 输出使用说明
    fprintf('\n============================================================\n');
    fprintf('  文件已生成!\n');
    fprintf('============================================================\n\n');
    fprintf('请按以下步骤在 CarSim 中运行仿真:\n\n');
    fprintf('【前驱车仿真】\n');
    fprintf('1. 打开 CarSim 2019.0\n');
    fprintf('2. 创建新数据集，命名为 ''FWD_bridge_slope''\n');
    fprintf('3. 设置参数（见 output/carsim_instructions_FWD.txt）\n');
    fprintf('4. 点击 Run 运行仿真\n');
    fprintf('5. 导出结果到 CSV 文件\n\n');
    fprintf('【四驱车仿真】\n');
    fprintf('1. 创建新数据集，命名为 ''AWD_bridge_slope''\n');
    fprintf('2. 设置参数（见 output/carsim_instructions_AWD.txt）\n');
    fprintf('3. 点击 Run 运行仿真\n');
    fprintf('4. 导出结果到 CSV 文件\n\n');
    fprintf('【分析结果】\n');
    fprintf('1. 将导出的 CSV 文件放到 output 目录\n');
    fprintf('2. 在 MATLAB 中运行 analyze_results.m\n\n');
end

function generate_carsim_instructions(params)
    % generate_carsim_instructions 生成 CarSim 参数说明文件

    % 前驱车参数说明
    fwd_file = fullfile(params.output_dir, 'carsim_instructions_FWD.txt');
    fid = fopen(fwd_file, 'w');

    if fid == -1
        error('无法创建文件: %s', fwd_file);
    end

    fprintf(fid, '============================================================\n');
    fprintf(fid, '  CarSim 参数设置说明 - 前驱车\n');
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
    fprintf(fid, '    - Wheel Slip FL/FR/RL/RR (车轮滑移率)\n');
    fprintf(fid, '    - Drive Torque FL/FR/RL/RR (驱动扭矩)\n\n');

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
    fprintf(fid, '  CarSim 参数设置说明 - 四驱车\n');
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
    fprintf(fid, '    - Wheel Slip FL/FR/RL/RR (车轮滑移率)\n');
    fprintf(fid, '    - Drive Torque FL/FR/RL/RR (驱动扭矩)\n\n');

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
    fprintf(fid, 'bridge_length = %.1f;    %% 高架桥长度 [m]\n', params.bridge_length);
    fprintf(fid, 'slope_angle = %.1f;      %% 坡度角度 [deg]\n', params.slope_angle);
    fprintf(fid, 'friction = %.2f;         %% 路面摩擦系数\n', params.friction);
    fprintf(fid, 'bridge_height = bridge_length * tan(slope_angle * pi / 180);\n\n');

    fprintf(fid, '%% 读取 CarSim 导出的 CSV 文件\n');
    fprintf(fid, '%% 请确保 results_FWD.csv 和 results_AWD.csv 在当前目录\n\n');

    fprintf(fid, '%% 读取前驱车结果\n');
    fprintf(fid, 'if exist(''results_FWD.csv'', ''file'')\n');
    fprintf(fid, '    fwd_data = csvread(''results_FWD.csv'', 1, 0);  %% 跳过标题行\n');
    fprintf(fid, '    fwd.time = fwd_data(:, 1);\n');
    fprintf(fid, '    fwd.x = fwd_data(:, 2);\n');
    fprintf(fid, '    fwd.z = fwd_data(:, 3);\n');
    fprintf(fid, '    fwd.vx = fwd_data(:, 4);\n');
    fprintf(fid, '    fwd.max_distance = max(fwd.x);\n');
    fprintf(fid, '    fwd.max_height = max(fwd.z);\n');
    fprintf(fid, '    fwd.success = fwd.max_height >= bridge_height * 0.9;\n');
    fprintf(fid, '    fprintf(''前驱车: 最大距离 %.1f m, 最大高度 %.1f m, 结果: %%s\\n'', ...\n');
    fprintf(fid, '        conditional(fwd.success, ''成功'', ''失败''));\n');
    fprintf(fid, 'else\n');
    fprintf(fid, '    warning(''未找到 results_FWD.csv'');\n');
    fprintf(fid, '    fwd = [];\n');
    fprintf(fid, 'end\n\n');

    fprintf(fid, '%% 读取四驱车结果\n');
    fprintf(fid, 'if exist(''results_AWD.csv'', ''file'')\n');
    fprintf(fid, '    awd_data = csvread(''results_AWD.csv'', 1, 0);\n');
    fprintf(fid, '    awd.time = awd_data(:, 1);\n');
    fprintf(fid, '    awd.x = awd_data(:, 2);\n');
    fprintf(fid, '    awd.z = awd_data(:, 3);\n');
    fprintf(fid, '    awd.vx = awd_data(:, 4);\n');
    fprintf(fid, '    awd.max_distance = max(awd.x);\n');
    fprintf(fid, '    awd.max_height = max(awd.z);\n');
    fprintf(fid, '    awd.success = awd.max_height >= bridge_height * 0.9;\n');
    fprintf(fid, '    fprintf(''四驱车: 最大距离 %.1f m, 最大高度 %.1f m, 结果: %%s\\n'', ...\n');
    fprintf(fid, '        conditional(awd.success, ''成功'', ''失败''));\n');
    fprintf(fid, 'else\n');
    fprintf(fid, '    warning(''未找到 results_AWD.csv'');\n');
    fprintf(fid, '    awd = [];\n');
    fprintf(fid, 'end\n\n');

    fprintf(fid, '%% 绘图\n');
    fprintf(fid, 'figure(''Position'', [100, 100, 1200, 800]);\n\n');

    fprintf(fid, '%% 子图1: 轨迹对比（侧视图）\n');
    fprintf(fid, 'subplot(2, 2, 1);\n');
    fprintf(fid, 'hold on;\n');
    fprintf(fid, 'if ~isempty(fwd)\n');
    fprintf(fid, '    plot(fwd.x, fwd.z, ''b-'', ''LineWidth'', 2);\n');
    fprintf(fid, 'end\n');
    fprintf(fid, 'if ~isempty(awd)\n');
    fprintf(fid, '    plot(awd.x, awd.z, ''r-'', ''LineWidth'', 2);\n');
    fprintf(fid, 'end\n');
    fprintf(fid, 'plot([0, bridge_length], [0, bridge_height], ''k--'', ''LineWidth'', 1);\n');
    fprintf(fid, 'xlabel(''X 位置 [m]'');\n');
    fprintf(fid, 'ylabel(''Z 高度 [m]'');\n');
    fprintf(fid, 'title(''车辆轨迹对比'');\n');
    fprintf(fid, 'legend(''前驱车'', ''四驱车'', ''高架桥坡面'', ''Location'', ''best'');\n');
    fprintf(fid, 'grid on;\n\n');

    fprintf(fid, '%% 子图2: 速度对比\n');
    fprintf(fid, 'subplot(2, 2, 2);\n');
    fprintf(fid, 'hold on;\n');
    fprintf(fid, 'if ~isempty(fwd)\n');
    fprintf(fid, '    plot(fwd.time, fwd.vx * 3.6, ''b-'', ''LineWidth'', 2);\n');
    fprintf(fid, 'end\n');
    fprintf(fid, 'if ~isempty(awd)\n');
    fprintf(fid, '    plot(awd.time, awd.vx * 3.6, ''r-'', ''LineWidth'', 2);\n');
    fprintf(fid, 'end\n');
    fprintf(fid, 'xlabel(''时间 [s]'');\n');
    fprintf(fid, 'ylabel(''速度 [km/h]'');\n');
    fprintf(fid, 'title(''速度变化'');\n');
    fprintf(fid, 'legend(''前驱车'', ''四驱车'', ''Location'', ''best'');\n');
    fprintf(fid, 'grid on;\n\n');

    fprintf(fid, '%% 子图3: 高度变化\n');
    fprintf(fid, 'subplot(2, 2, 3);\n');
    fprintf(fid, 'hold on;\n');
    fprintf(fid, 'if ~isempty(fwd)\n');
    fprintf(fid, '    plot(fwd.time, fwd.z, ''b-'', ''LineWidth'', 2);\n');
    fprintf(fid, 'end\n');
    fprintf(fid, 'if ~isempty(awd)\n');
    fprintf(fid, '    plot(awd.time, awd.z, ''r-'', ''LineWidth'', 2);\n');
    fprintf(fid, 'end\n');
    fprintf(fid, 'plot([0, 30], [bridge_height, bridge_height], ''k--'', ''LineWidth'', 1);\n');
    fprintf(fid, 'xlabel(''时间 [s]'');\n');
    fprintf(fid, 'ylabel(''高度 [m]'');\n');
    fprintf(fid, 'title(''高度变化'');\n');
    fprintf(fid, 'legend(''前驱车'', ''四驱车'', ''目标高度'', ''Location'', ''best'');\n');
    fprintf(fid, 'grid on;\n\n');

    fprintf(fid, '%% 子图4: 结果摘要\n');
    fprintf(fid, 'subplot(2, 2, 4);\n');
    fprintf(fid, 'hold on;\n');
    fprintf(fid, 'y_pos = 0.8;\n');
    fprintf(fid, 'text(0.5, y_pos, ''仿真结果摘要'', ...\n');
    fprintf(fid, '    ''HorizontalAlignment'', ''center'', ''FontSize'', 16, ''FontWeight'', ''bold'');\n');
    fprintf(fid, 'y_pos = y_pos - 0.15;\n\n');

    fprintf(fid, 'if ~isempty(fwd)\n');
    fprintf(fid, '    text(0.5, y_pos, sprintf(''前驱车: %%s (%%.1f m)'', ...\n');
    fprintf(fid, '        conditional(fwd.success, ''成功'', ''失败''), fwd.max_height), ...\n');
    fprintf(fid, '        ''HorizontalAlignment'', ''center'', ''FontSize'', 14, ...\n');
    fprintf(fid, '        ''Color'', conditional(fwd.success, [0 0.7 0], [0.8 0 0]));\n');
    fprintf(fid, '    y_pos = y_pos - 0.1;\n');
    fprintf(fid, 'end\n\n');

    fprintf(fid, 'if ~isempty(awd)\n');
    fprintf(fid, '    text(0.5, y_pos, sprintf(''四驱车: %%s (%%.1f m)'', ...\n');
    fprintf(fid, '        conditional(awd.success, ''成功'', ''失败''), awd.max_height), ...\n');
    fprintf(fid, '        ''HorizontalAlignment'', ''center'', ''FontSize'', 14, ...\n');
    fprintf(fid, '        ''Color'', conditional(awd.success, [0 0.7 0], [0.8 0 0]));\n');
    fprintf(fid, '    y_pos = y_pos - 0.1;\n');
    fprintf(fid, 'end\n\n');

    fprintf(fid, 'text(0.5, y_pos, sprintf(''目标高度: %.1f m'', bridge_height), ...\n');
    fprintf(fid, '    ''HorizontalAlignment'', ''center'', ''FontSize'', 12);\n');
    fprintf(fid, 'text(0.5, y_pos-0.08, sprintf(''路面摩擦: %.2f'', friction), ...\n');
    fprintf(fid, '    ''HorizontalAlignment'', ''center'', ''FontSize'', 12);\n');
    fprintf(fid, 'axis off;\n\n');

    fprintf(fid, '%% 保存图形\n');
    fprintf(fid, 'saveas(gcf, ''simulation_results.png'', ''png'');\n');
    fprintf(fid, 'fprintf(''结果已保存: simulation_results.png\\n'');\n\n');

    fprintf(fid, '%% 辅助函数\n');
    fprintf(fid, 'function result = conditional(condition, true_val, false_val)\n');
    fprintf(fid, '    if condition\n');
    fprintf(fid, '        result = true_val;\n');
    fprintf(fid, '    else\n');
    fprintf(fid, '        result = false_val;\n');
    fprintf(fid, '    end\n');
    fprintf(fid, 'end\n');

    fclose(fid);
    fprintf('  已生成: %s\n', script_file);
end
