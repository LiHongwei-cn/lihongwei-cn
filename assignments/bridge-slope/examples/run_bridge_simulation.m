%% 高架桥仿真 - 燕子矶场景（CarSim 2019.0 兼容）
% MATLAB R2016b 兼容
% 通过 CarSim 的 Send to Simulink 接口运行
%
% 使用方法：
%   1. 在 CarSim 中创建新数据集
%   2. 运行本脚本生成 Simulink 模型
%   3. 在 CarSim 中点击 Run 运行仿真

function run_bridge_simulation(params)
    % run_bridge_simulation 运行高架桥仿真
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
    fprintf('  高架桥仿真 - 燕子矶场景\n');
    fprintf('  CarSim 2019.0 兼容版本\n');
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

    %% 生成 CarSim 参数文件（供手动导入）
    fprintf('>>> 步骤 1: 生成 CarSim 参数文件...\n');
    generate_carsim_params(params);

    %% 生成 Simulink 模型（用于与 CarSim 联合仿真）
    fprintf('\n>>> 步骤 2: 生成 Simulink 模型...\n');
    generate_simulink_model(params);

    %% 生成 MATLAB 分析脚本
    fprintf('\n>>> 步骤 3: 生成分析脚本...\n');
    generate_analysis_script(params);

    %% 输出使用说明
    fprintf('\n============================================================\n');
    fprintf('  文件已生成!\n');
    fprintf('============================================================\n\n');
    fprintf('请按以下步骤在 CarSim 中运行仿真:\n\n');
    fprintf('1. 打开 CarSim 2019.0\n');
    fprintf('2. 创建新数据集或打开现有数据集\n');
    fprintf('3. 在 CarSim 中设置以下参数:\n');
    fprintf('   - Road: 设置坡度为 %.1f deg\n', params.slope_angle);
    fprintf('   - Tire: 设置摩擦系数为 %.2f\n', params.friction);
    fprintf('   - Vehicle: 根据需要选择前驱或四驱\n');
    fprintf('4. 点击 Send to Simulink 按钮\n');
    fprintf('5. 在 Simulink 中运行仿真\n');
    fprintf('6. 使用 analyze_results.m 分析结果\n\n');
    fprintf('生成的文件:\n');
    fprintf('  - %s/carsim_params_FWD.m: 前驱车参数\n', params.output_dir);
    fprintf('  - %s/carsim_params_AWD.m: 四驱车参数\n', params.output_dir);
    fprintf('  - %s/bridge_slope_model.slx: Simulink 模型\n', params.output_dir);
    fprintf('  - %s/analyze_results.m: 结果分析脚本\n', params.output_dir);
end

function generate_carsim_params(params)
    % generate_carsim_params 生成 CarSim 参数文件
    %
    % 生成可在 CarSim 中手动输入的参数

    % 前驱车参数
    fwd_file = fullfile(params.output_dir, 'carsim_params_FWD.m');
    fid = fopen(fwd_file, 'w');

    if fid == -1
        error('无法创建文件: %s', fwd_file);
    end

    fprintf(fid, '%% CarSim 参数 - 前驱车\n');
    fprintf(fid, '%% 在 CarSim 中手动输入这些参数\n\n');

    fprintf(fid, '%% 车辆参数\n');
    fprintf(fid, 'params.vehicle.mass = 1500;           %% 整车质量 [kg]\n');
    fprintf(fid, 'params.vehicle.wheelbase = 2.7;       %% 轴距 [m]\n');
    fprintf(fid, 'params.vehicle.cg_height = 0.5;       %% 重心高度 [m]\n');
    fprintf(fid, 'params.vehicle.drive_type = ''FWD'';    %% 驱动类型: 前驱\n\n');

    fprintf(fid, '%% 发动机参数\n');
    fprintf(fid, 'params.engine.power = %.1f;            %% 发动机功率 [kW]\n', params.fwd_power);
    fprintf(fid, 'params.engine.max_torque = %.1f;       %% 最大扭矩 [Nm]\n', params.fwd_power * 1000 / (5000 * pi / 30));
    fprintf(fid, 'params.engine.max_rpm = 6000;          %% 最大转速 [rpm]\n\n');

    fprintf(fid, '%% 轮胎参数\n');
    fprintf(fid, 'params.tire.friction = %.2f;           %% 路面摩擦系数\n', params.friction);
    fprintf(fid, 'params.tire.radius = 0.31;             %% 轮胎半径 [m]\n\n');

    fprintf(fid, '%% 道路参数\n');
    fprintf(fid, 'params.road.slope = %.1f;              %% 坡度角度 [deg]\n', params.slope_angle);
    fprintf(fid, 'params.road.length = %.1f;             %% 高架桥长度 [m]\n', params.bridge_length);

    fclose(fid);
    fprintf('  已生成: %s\n', fwd_file);

    % 四驱车参数
    awd_file = fullfile(params.output_dir, 'carsim_params_AWD.m');
    fid = fopen(awd_file, 'w');

    if fid == -1
        error('无法创建文件: %s', awd_file);
    end

    fprintf(fid, '%% CarSim 参数 - 四驱车\n');
    fprintf(fid, '%% 在 CarSim 中手动输入这些参数\n\n');

    fprintf(fid, '%% 车辆参数\n');
    fprintf(fid, 'params.vehicle.mass = 1500;           %% 整车质量 [kg]\n');
    fprintf(fid, 'params.vehicle.wheelbase = 2.7;       %% 轴距 [m]\n');
    fprintf(fid, 'params.vehicle.cg_height = 0.5;       %% 重心高度 [m]\n');
    fprintf(fid, 'params.vehicle.drive_type = ''AWD'';    %% 驱动类型: 四驱\n\n');

    fprintf(fid, '%% 发动机参数\n');
    fprintf(fid, 'params.engine.power = %.1f;            %% 发动机功率 [kW]\n', params.awd_power);
    fprintf(fid, 'params.engine.max_torque = %.1f;       %% 最大扭矩 [Nm]\n', params.awd_power * 1000 / (5000 * pi / 30));
    fprintf(fid, 'params.engine.max_rpm = 6000;          %% 最大转速 [rpm]\n\n');

    fprintf(fid, '%% 四驱系统参数\n');
    fprintf(fid, 'params.awd.center_diff_ratio = 0.5;   %% 中央差速器分配比例\n');
    fprintf(fid, 'params.awd.front_diff_type = ''OPEN'';  %% 前差速器类型\n');
    fprintf(fid, 'params.awd.rear_diff_type = ''OPEN'';   %% 后差速器类型\n\n');

    fprintf(fid, '%% 轮胎参数\n');
    fprintf(fid, 'params.tire.friction = %.2f;           %% 路面摩擦系数\n', params.friction);
    fprintf(fid, 'params.tire.radius = 0.31;             %% 轮胎半径 [m]\n\n');

    fprintf(fid, '%% 道路参数\n');
    fprintf(fid, 'params.road.slope = %.1f;              %% 坡度角度 [deg]\n', params.slope_angle);
    fprintf(fid, 'params.road.length = %.1f;             %% 高架桥长度 [m]\n', params.bridge_length);

    fclose(fid);
    fprintf('  已生成: %s\n', awd_file);
end

function generate_simulink_model(params)
    % generate_simulink_model 生成 Simulink 模型
    %
    % 创建用于 CarSim 联合仿真的 Simulink 模型

    modelName = 'bridge_slope_model';
    model_file = fullfile(params.output_dir, [modelName '.slx']);

    % 检查是否已加载
    if bdIsLoaded(modelName)
        close_system(modelName, 0);
    end

    % 创建新模型
    new_system(modelName);
    open_system(modelName);

    % 添加 CarSim S-Function 块（需要 CarSim 已安装）
    % 注意：这需要 CarSim 的 Simulink 接口已正确安装

    % 添加输入块（油门和制动）
    add_block('simulink/Sources/Step', [modelName '/Throttle']);
    set_param([modelName '/Throttle'], ...
        'Time', '0.5', ...
        'Before', '0', ...
        'After', '1', ...
        'Position', [100, 100, 130, 130]);

    add_block('simulink/Sources/Constant', [modelName '/Brake']);
    set_param([modelName '/Brake'], ...
        'Value', '0', ...
        'Position', [100, 200, 130, 230]);

    % 添加合并块
    add_block('simulink/Signal Routing/Mux', [modelName '/InputMux']);
    set_param([modelName '/InputMux'], ...
        'Inputs', '2', ...
        'Position', [200, 130, 210, 220]);

    % 添加 CarSim S-Function 块（占位符）
    add_block('simulink/User-Defined Functions/S-Function', [modelName '/CarSim']);
    set_param([modelName '/CarSim'], ...
        'FunctionName', 'vs_main', ...
        'Position', [300, 130, 400, 220]);

    % 添加输出块（Scope）
    add_block('simulink/Sinks/Scope', [modelName '/Scope']);
    set_param([modelName '/Scope'], ...
        'Position', [500, 130, 530, 170]);

    % 添加 To Workspace 块
    add_block('simulink/Sinks/To Workspace', [modelName '/ToWorkspace']);
    set_param([modelName '/ToWorkspace'], ...
        'VariableName', 'simout', ...
        'SaveFormat', 'Timeseries', ...
        'Position', [500, 200, 530, 230]);

    % 连线
    add_line(modelName, 'Throttle/1', 'InputMux/1');
    add_line(modelName, 'Brake/1', 'InputMux/2');
    add_line(modelName, 'InputMux/1', 'CarSim/1');
    add_line(modelName, 'CarSim/1', 'Scope/1');
    add_line(modelName, 'CarSim/1', 'ToWorkspace/1');

    % 设置仿真参数
    set_param(modelName, ...
        'StopTime', '30', ...
        'FixedStep', '0.001', ...
        'Solver', 'ode4');

    % 保存模型
    save_system(modelName, model_file);

    fprintf('  已生成: %s\n', model_file);
    fprintf('  注意: 需要 CarSim 已安装才能运行此模型\n');
end

function generate_analysis_script(params)
    % generate_analysis_script 生成结果分析脚本

    script_file = fullfile(params.output_dir, 'analyze_results.m');
    fid = fopen(script_file, 'w');

    if fid == -1
        error('无法创建文件: %s', script_file);
    end

    fprintf(fid, '%% 仿真结果分析脚本\n');
    fprintf(fid, '%% 在 CarSim 仿真运行后执行此脚本\n\n');

    fprintf(fid, 'clear; clc; close all;\n\n');

    fprintf(fid, '%% 参数设置\n');
    fprintf(fid, 'bridge_length = %.1f;    %% 高架桥长度 [m]\n', params.bridge_length);
    fprintf(fid, 'slope_angle = %.1f;      %% 坡度角度 [deg]\n', params.slope_angle);
    fprintf(fid, 'friction = %.2f;         %% 路面摩擦系数\n', params.friction);
    fprintf(fid, 'bridge_height = bridge_length * tan(slope_angle * pi / 180);\n\n');

    fprintf(fid, '%% 读取 CarSim 输出数据\n');
    fprintf(fid, '%% 假设数据已保存在 workspace 中（simout 变量）\n');
    fprintf(fid, 'if exist(''simout'', ''var'')\n');
    fprintf(fid, '    time = simout.Time;\n');
    fprintf(fid, '    x = simout.Data(:, 1);    %% X 位置\n');
    fprintf(fid, '    z = simout.Data(:, 2);    %% Z 位置（高度）\n');
    fprintf(fid, '    vx = simout.Data(:, 3);   %% 纵向速度\n');
    fprintf(fid, 'else\n');
    fprintf(fid, '    error(''未找到仿真数据，请先运行 CarSim 仿真'');\n');
    fprintf(fid, 'end\n\n');

    fprintf(fid, '%% 计算统计量\n');
    fprintf(fid, 'max_distance = max(x);\n');
    fprintf(fid, 'max_height = max(z);\n');
    fprintf(fid, 'avg_speed = mean(vx);\n\n');

    fprintf(fid, '%% 判断是否成功爬坡\n');
    fprintf(fid, 'success = max_height >= bridge_height * 0.9;\n\n');

    fprintf(fid, '%% 输出结果\n');
    fprintf(fid, 'fprintf(''===== 仿真结果 =====\\n'');\n');
    fprintf(fid, 'fprintf(''最大距离: %.1f m\\n'', max_distance);\n');
    fprintf(fid, 'fprintf(''最大高度: %.1f m\\n'', max_height);\n');
    fprintf(fid, 'fprintf(''目标高度: %.1f m\\n'', bridge_height);\n');
    fprintf(fid, 'fprintf(''平均速度: %.1f m/s\\n'', avg_speed);\n');
    fprintf(fid, 'if success\n');
    fprintf(fid, '    fprintf(''爬坡结果: 成功\\n'');\n');
    fprintf(fid, 'else\n');
    fprintf(fid, '    fprintf(''爬坡结果: 失败（打滑）\\n'');\n');
    fprintf(fid, 'end\n\n');

    fprintf(fid, '%% 绘图\n');
    fprintf(fid, 'figure(''Position'', [100, 100, 1200, 800]);\n\n');

    fprintf(fid, '%% 子图1: 轨迹（侧视图）\n');
    fprintf(fid, 'subplot(2, 2, 1);\n');
    fprintf(fid, 'plot(x, z, ''b-'', ''LineWidth'', 2);\n');
    fprintf(fid, 'hold on;\n');
    fprintf(fid, 'plot([0, bridge_length], [0, bridge_height], ''r--'', ''LineWidth'', 1);\n');
    fprintf(fid, 'xlabel(''X 位置 [m]'');\n');
    fprintf(fid, 'ylabel(''Z 高度 [m]'');\n');
    fprintf(fid, 'title(''车辆轨迹'');\n');
    fprintf(fid, 'legend(''实际轨迹'', ''高架桥坡面'', ''Location'', ''best'');\n');
    fprintf(fid, 'grid on;\n\n');

    fprintf(fid, '%% 子图2: 速度变化\n');
    fprintf(fid, 'subplot(2, 2, 2);\n');
    fprintf(fid, 'plot(time, vx * 3.6, ''b-'', ''LineWidth'', 2);\n');
    fprintf(fid, 'xlabel(''时间 [s]'');\n');
    fprintf(fid, 'ylabel(''速度 [km/h]'');\n');
    fprintf(fid, 'title(''速度变化'');\n');
    fprintf(fid, 'grid on;\n\n');

    fprintf(fid, '%% 子图3: 高度变化\n');
    fprintf(fid, 'subplot(2, 2, 3);\n');
    fprintf(fid, 'plot(time, z, ''b-'', ''LineWidth'', 2);\n');
    fprintf(fid, 'hold on;\n');
    fprintf(fid, 'plot([0, max(time)], [bridge_height, bridge_height], ''r--'', ''LineWidth'', 1);\n');
    fprintf(fid, 'xlabel(''时间 [s]'');\n');
    fprintf(fid, 'ylabel(''高度 [m]'');\n');
    fprintf(fid, 'title(''高度变化'');\n');
    fprintf(fid, 'legend(''实际高度'', ''目标高度'', ''Location'', ''best'');\n');
    fprintf(fid, 'grid on;\n\n');

    fprintf(fid, '%% 子图4: 结果摘要\n');
    fprintf(fid, 'subplot(2, 2, 4);\n');
    fprintf(fid, 'text(0.5, 0.7, sprintf(''最大距离: %.1f m'', max_distance), ...\n');
    fprintf(fid, '    ''HorizontalAlignment'', ''center'', ''FontSize'', 14);\n');
    fprintf(fid, 'text(0.5, 0.5, sprintf(''最大高度: %.1f m'', max_height), ...\n');
    fprintf(fid, '    ''HorizontalAlignment'', ''center'', ''FontSize'', 14);\n');
    fprintf(fid, 'text(0.5, 0.3, sprintf(''爬坡结果: %s'', ...\n');
    fprintf(fid, '    conditional(success, ''成功'', ''失败'')), ...\n');
    fprintf(fid, '    ''HorizontalAlignment'', ''center'', ''FontSize'', 14, ...\n');
    fprintf(fid, '    ''Color'', conditional(success, ''g'', ''r''));\n');
    fprintf(fid, 'axis off;\n');
    fprintf(fid, 'title(''结果摘要'');\n\n');

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
