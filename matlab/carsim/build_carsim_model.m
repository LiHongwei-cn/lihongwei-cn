%% 构建 CarSim-Simulink 联合仿真模型
% MATLAB R2016b + CarSim 2019.0 兼容
% 运行前先执行 sim_setup 配置路径
%
% 使用方式：
%   1. 运行本脚本生成 .slx 文件
%   2. 打开 CarSim → Run Control → Models → 选择 Simulink
%   3. 浏览选择生成的 .slx 文件
%   4. 在 CarSim 中配置 I/O 通道映射（脚本会自动打印映射表）
%   5. CarSim 中点击 Run，会自动调用 Simulink 模型

function build_carsim_model()
    modelName = 'carsim_cruise_ctrl';

    if bdIsLoaded(modelName)
        close_system(modelName, 0);
    end

    new_system(modelName);
    open_system(modelName);

    %% 仿真参数
    STEP_SIZE = 0.001;   % 固定步长，需与 CarSim 一致
    STOP_TIME = 30;

    %% ========== CarSim 输入端口（CarSim → Simulink） ==========
    % CarSim 会将车辆状态发送到这些 Import 端口
    % 端口编号对应 CarSim 中 I/O Channel 的顺序

    % Import 1: 车速 Vx [km/h] — CarSim Export Channel #1
    add_block('simulink/Sources/In1', [modelName '/Vx_kmh']);
    set_param([modelName '/Vx_kmh'], 'Position', [50, 80, 80, 100]);

    % Import 2: 纵向加速度 Ax [g] — CarSim Export Channel #2
    add_block('simulink/Sources/In1', [modelName '/Ax_g']);
    set_param([modelName '/Ax_g'], 'Position', [50, 150, 80, 170]);

    % Import 3: 发动机转速 [rpm] — CarSim Export Channel #3（可选）
    add_block('simulink/Sources/In1', [modelName '/EngineRPM']);
    set_param([modelName '/EngineRPM'], 'Position', [50, 220, 80, 240]);

    %% ========== 目标车速设置 ==========
    add_block('simulink/Sources/Constant', [modelName '/Target_Speed_kmh']);
    set_param([modelName '/Target_Speed_kmh'], ...
        'Value', '100', ...
        'Position', [50, 330, 120, 360]);

    %% ========== PI 速度控制器 ==========
    % 速度误差 = 目标车速 - 实际车速
    add_block('simulink/Math Operations/Sum', [modelName '/Speed_Error']);
    set_param([modelName '/Speed_Error'], ...
        'Inputs', '+-', ...
        'Position', [180, 80, 210, 130]);

    % Kp 比例增益
    Kp = 0.8;
    add_block('simulink/Math Operations/Gain', [modelName '/Kp']);
    set_param([modelName '/Kp'], ...
        'Gain', 'Kp', ...
        'Position', [260, 80, 300, 120]);

    % Ki 积分增益 + Integrator
    Ki = 2.0;
    add_block('simulink/Math Operations/Gain', [modelName '/Ki']);
    set_param([modelName '/Ki'], ...
        'Gain', 'Ki', ...
        'Position', [260, 150, 300, 190]);

    add_block('simulink/Continuous/Integrator', [modelName '/Integrator']);
    set_param([modelName '/Integrator'], ...
        'Position', [350, 150, 390, 190]);

    % PI 输出求和
    add_block('simulink/Math Operations/Sum', [modelName '/PI_Out']);
    set_param([modelName '/PI_Out'], ...
        'Inputs', '++', ...
        'Position', [430, 90, 460, 150]);

    %% ========== 输出限幅 & 端口（Simulink → CarSim） ==========
    % Outport 1: 节气门开度 [0-1] — CarSim Import Channel #1
    add_block('simulink/Commonly Used Blocks/Saturation', [modelName '/Throttle_Limit']);
    set_param([modelName '/Throttle_Limit'], ...
        'UpperLimit', '1', 'LowerLimit', '0', ...
        'Position', [510, 80, 550, 120]);
    add_block('simulink/Sinks/Out1', [modelName '/Throttle']);
    set_param([modelName '/Throttle'], 'Position', [610, 80, 640, 100]);

    % Outport 2: 制动力 [MPa] — CarSim Import Channel #2
    BRAKE_GAIN = 5;  % PI 输出转为制动压力
    add_block('simulink/Math Operations/Gain', [modelName '/Brake_Gain']);
    set_param([modelName '/Brake_Gain'], ...
        'Gain', 'BRAKE_GAIN', ...
        'Position', [510, 160, 550, 200]);
    add_block('simulink/Commonly Used Blocks/Saturation', [modelName '/Brake_Limit']);
    set_param([modelName '/Brake_Limit'], ...
        'UpperLimit', '15', 'LowerLimit', '0', ...
        'Position', [560, 160, 600, 200]);
    add_block('simulink/Sinks/Out1', [modelName '/Brake_MPa']);
    set_param([modelName '/Brake_MPa'], 'Position', [610, 160, 640, 180]);

    %% ========== 电流环参考显示（可选：FOC 电机控制接口） ==========
    % Outport 3: 电机目标转矩 [Nm]
    add_block('simulink/Sinks/Out1', [modelName '/Motor_Torque_Nm']);
    set_param([modelName '/Motor_Torque_Nm'], 'Position', [610, 300, 640, 320]);

    %% ========== 信号记录 ==========
    add_block('simulink/Sinks/Scope', [modelName '/Scope']);
    set_param([modelName '/Scope'], ...
        'NumInputPorts', '3', ...
        'Position', [700, 50, 950, 350]);

    add_block('simulink/Signal Routing/Mux', [modelName '/Mux']);
    set_param([modelName '/Mux'], ...
        'Inputs', '3', ...
        'Position', [660, 60, 670, 120]);

    %% ========== 连线 ==========
    % 速度误差
    add_line(modelName, 'Target_Speed_kmh/1', 'Speed_Error/1');
    add_line(modelName, 'Vx_kmh/1', 'Speed_Error/2');

    % PI 控制器
    add_line(modelName, 'Speed_Error/1', 'Kp/1');
    add_line(modelName, 'Speed_Error/1', 'Ki/1');
    add_line(modelName, 'Ki/1', 'Integrator/1');
    add_line(modelName, 'Kp/1', 'PI_Out/1');
    add_line(modelName, 'Integrator/1', 'PI_Out/2');

    % 输出到 CarSim
    add_line(modelName, 'PI_Out/1', 'Throttle_Limit/1');
    add_line(modelName, 'Throttle_Limit/1', 'Throttle/1');

    add_line(modelName, 'PI_Out/1', 'Brake_Gain/1');
    add_line(modelName, 'Brake_Gain/1', 'Brake_Limit/1');
    add_line(modelName, 'Brake_Limit/1', 'Brake_MPa/1');

    % 电机转矩接口（从 PI 输出派生）
    add_line(modelName, 'PI_Out/1', 'Motor_Torque_Nm/1');

    % Scope
    add_line(modelName, 'Vx_kmh/1', 'Mux/1');
    add_line(modelName, 'Target_Speed_kmh/1', 'Mux/2');
    add_line(modelName, 'PI_Out/1', 'Mux/3');
    add_line(modelName, 'Mux/1', 'Scope/1');

    %% ========== 模型配置 ==========
    set_param(modelName, 'Solver', 'ode4');
    set_param(modelName, 'FixedStep', num2str(STEP_SIZE));
    set_param(modelName, 'StopTime', num2str(STOP_TIME));
    set_param(modelName, 'StartTime', '0.0');

    save_system(modelName);
    fprintf('模型 %s.slx 已生成。\n', modelName);
    print_io_mapping();
end

function print_io_mapping()
    fprintf('\n========== CarSim I/O 通道映射 ==========\n');
    fprintf('在 CarSim 中按如下顺序配置 I/O Channels:\n\n');
    fprintf('  CarSim → Simulink (Import):\n');
    fprintf('    1. Vx         (车速 km/h)\n');
    fprintf('    2. Ax         (纵向加速度 g)\n');
    fprintf('    3. EngRPM     (发动机转速 rpm)\n\n');
    fprintf('  Simulink → CarSim (Export):\n');
    fprintf('    1. Throttle   (节气门 0-1)\n');
    fprintf('    2. Brake      (制动压力 MPa)\n');
    fprintf('    3. MotorTrq   (电机转矩 Nm，EV 模式用)\n\n');
    fprintf('配置步骤:\n');
    fprintf('  1. CarSim → Run Control → Models → 选 Simulink\n');
    fprintf('  2. 浏览选择 carsim_cruise_ctrl.slx\n');
    fprintf('  3. 点击 I/O Channels 按上表配置映射\n');
    fprintf('  4. 设置 Step Size 为 %.3f s\n', 0.001);
    fprintf('  5. 点击 Run\n');
    fprintf('==========================================\n');
end
