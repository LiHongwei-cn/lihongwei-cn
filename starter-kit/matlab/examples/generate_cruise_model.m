%% 生成定速巡航 Simulink 模型
% MATLAB R2016b 兼容
% 运行此脚本 -> 自动生成 cruise_control.slx 文件

function generate_cruise_model()
    modelName = 'cruise_control';

    % 如果模型已存在则关闭
    if bdIsLoaded(modelName)
        close_system(modelName, 0);
    end

    % 创建新模型
    new_system(modelName);

    %% 添加模块

    % ---------- 输入 ----------
    add_block('simulink/Sources/Step', [modelName '/Speed_Ref'], ...
        'Position', [50 100 130 130], ...
        'Time', '5', ...
        'Before', '0', ...
        'After', '30');

    add_block('simulink/Sources/Step', [modelName '/Load_Torque'], ...
        'Position', [50 250 130 280], ...
        'Time', '20', ...
        'Before', '0', ...
        'After', '200');

    % ---------- PI 控制器 ----------
    add_block('simulink/Continuous/Integrator', [modelName '/Integrator'], ...
        'Position', [250 95 280 125], ...
        'InitialCondition', '0');

    add_block('simulink/Math Operations/Gain', [modelName '/Kp'], ...
        'Position', [250 140 280 170], ...
        'Gain', '500');

    add_block('simulink/Math Operations/Gain', [modelName '/Ki'], ...
        'Position', [250 80 280 110], ...
        'Gain', '50');

    add_block('simulink/Math Operations/Sum', [modelName '/Error_Sum'], ...
        'Position', [190 100 220 150], ...
        'Inputs', '+-');

    add_block('simulink/Math Operations/Sum', [modelName '/PI_Sum'], ...
        'Position', [320 100 350 150], ...
        'Inputs', '++');

    % ---------- 车辆模型 ----------
    add_block('simulink/Continuous/Integrator', [modelName '/Vehicle_Dynamics'], ...
        'Position', [450 100 490 140], ...
        'InitialCondition', '0', ...
        'OutMin', '0');

    add_block('simulink/Math Operations/Gain', [modelName '/1_over_M'], ...
        'Position', [400 110 430 140], ...
        'Gain', '1/1500');

    % ---------- 输出 ----------
    add_block('simulink/Sinks/Scope', [modelName '/Scope'], ...
        'Position', [540 100 570 130]);

    add_block('simulink/Sinks/Out1', [modelName '/Speed_Out'], ...
        'Position', [540 170 570 200]);

    add_block('simulink/Sinks/Out1', [modelName '/Torque_Out'], ...
        'Position', [540 230 570 260]);

    % ---------- 负载 ----------
    add_block('simulink/Math Operations/Sum', [modelName '/Force_Sum'], ...
        'Position', [360 100 390 160], ...
        'Inputs', '+-');

    %% 连接信号
    add_line(modelName, 'Speed_Ref/1', 'Error_Sum/1');
    add_line(modelName, 'Vehicle_Dynamics/1', 'Error_Sum/2');

    add_line(modelName, 'Error_Sum/1', 'Kp/1');
    add_line(modelName, 'Error_Sum/1', 'Integrator/1');

    add_line(modelName, 'Kp/1', 'PI_Sum/1');
    add_line(modelName, 'Integrator/1', 'PI_Sum/2');

    add_line(modelName, 'PI_Sum/1', 'Force_Sum/1');
    add_line(modelName, 'Load_Torque/1', 'Force_Sum/2');

    add_line(modelName, 'Force_Sum/1', '1_over_M/1');
    add_line(modelName, '1_over_M/1', 'Vehicle_Dynamics/1');

    add_line(modelName, 'Vehicle_Dynamics/1', 'Scope/1');
    add_line(modelName, 'Vehicle_Dynamics/1', 'Speed_Out/1');
    add_line(modelName, 'Force_Sum/1', 'Torque_Out/1');

    %% 模型配置
    set_param(modelName, 'StopTime', '30');
    set_param(modelName, 'Solver', 'ode4');
    set_param(modelName, 'FixedStep', '0.001');

    %% 保存并打开
    save_system(modelName);
    open_system(modelName);

    fprintf('模型 %s.slx 已生成并打开\n', modelName);
end
