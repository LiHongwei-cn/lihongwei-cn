%% 构建 CarSim-Simulink 联合仿真模型
% MATLAB R2016b + CarSim 2019.0
% 生成 carsim_cruise_ctrl.slx（定速巡航控制器）

function build_carsim_model()
    modelName = 'carsim_cruise_ctrl';
    fprintf('[1/5] 初始化...\n');

    % 检查 Simulink 许可证
    [hasLicense, errMsg] = license('checkout', 'Simulink');
    if ~hasLicense
        fprintf('[X] Simulink 许可证不可用: %s\n', errMsg);
        return;
    end

    % 加载 Simulink 库
    try
        load_system('simulink');
    catch
        fprintf('[X] 无法加载 Simulink 库，请确认 Simulink 已安装\n');
        return;
    end

    % 关闭已存在的同名模型
    if bdIsLoaded(modelName)
        close_system(modelName, 0);
    end

    % 删除旧文件
    slxFile = [modelName '.slx'];
    mdlFile = [modelName '.mdl'];
    if exist(slxFile, 'file'), delete(slxFile); end
    if exist(mdlFile, 'file'), delete(mdlFile); end

    % 创建新模型
    try
        new_system(modelName);
    catch e
        fprintf('[X] 创建模型失败: %s\n', e.message);
        return;
    end
    fprintf('[OK] 模型 %s 已创建\n', modelName);

    %% ===== 添加模块 =====
    fprintf('[2/5] 添加模块...\n');
    ok = true;

    % 目标车速 (Constant)
    ok = ok && add_block_safe('simulink/Sources/Constant', [modelName '/Target_Speed_kmh']);
    set_param_safe([modelName '/Target_Speed_kmh'], 'Value', '100', 'Position', [50,30,120,60]);

    % 实际车速输入 (In1)
    ok = ok && add_block_safe('simulink/Sources/In1', [modelName '/Vx_kmh']);
    set_param_safe([modelName '/Vx_kmh'], 'Position', [50,100,80,120]);

    % 速度误差 (Sum: +-)
    ok = ok && add_block_safe('simulink/Math Operations/Sum', [modelName '/Speed_Error']);
    set_param_safe([modelName '/Speed_Error'], 'Inputs', '+-', 'Position', [160,60,190,110]);

    % PI: Kp
    ok = ok && add_block_safe('simulink/Math Operations/Gain', [modelName '/Kp']);
    set_param_safe([modelName '/Kp'], 'Gain', '0.8', 'Position', [240,30,280,70]);

    % PI: Ki
    ok = ok && add_block_safe('simulink/Math Operations/Gain', [modelName '/Ki']);
    set_param_safe([modelName '/Ki'], 'Gain', '2.0', 'Position', [240,100,280,140]);

    % 积分器
    ok = ok && add_block_safe('simulink/Continuous/Integrator', [modelName '/Integrator']);
    set_param_safe([modelName '/Integrator'], 'Position', [330,100,370,140]);

    % PI 求和
    ok = ok && add_block_safe('simulink/Math Operations/Sum', [modelName '/PI_Sum']);
    set_param_safe([modelName '/PI_Sum'], 'Inputs', '++', 'Position', [410,55,440,125]);

    % 节气门限幅
    ok = ok && add_block_safe('simulink/Commonly Used Blocks/Saturation', [modelName '/Throttle_Limit']);
    set_param_safe([modelName '/Throttle_Limit'], 'UpperLimit', '1', 'LowerLimit', '0', ...
        'Position', [500,40,540,80]);

    % 节气门输出 (Out1)
    ok = ok && add_block_safe('simulink/Sinks/Out1', [modelName '/Throttle']);
    set_param_safe([modelName '/Throttle'], 'Position', [590,45,620,75]);

    % 制动增益
    ok = ok && add_block_safe('simulink/Math Operations/Gain', [modelName '/Brake_Gain']);
    set_param_safe([modelName '/Brake_Gain'], 'Gain', '5', 'Position', [500,120,540,160]);

    % 制动限幅
    ok = ok && add_block_safe('simulink/Commonly Used Blocks/Saturation', [modelName '/Brake_Limit']);
    set_param_safe([modelName '/Brake_Limit'], 'UpperLimit', '15', 'LowerLimit', '0', ...
        'Position', [550,120,590,160]);

    % 制动输出 (Out1)
    ok = ok && add_block_safe('simulink/Sinks/Out1', [modelName '/Brake_MPa']);
    set_param_safe([modelName '/Brake_MPa'], 'Position', [640,125,670,155]);

    % 加速度输入 (In1)
    ok = ok && add_block_safe('simulink/Sources/In1', [modelName '/Ax_g']);
    set_param_safe([modelName '/Ax_g'], 'Position', [50,170,80,190]);

    % 发动机转速输入 (In1)
    ok = ok && add_block_safe('simulink/Sources/In1', [modelName '/EngineRPM']);
    set_param_safe([modelName '/EngineRPM'], 'Position', [50,240,80,260]);

    % Scope
    ok = ok && add_block_safe('simulink/Sinks/Scope', [modelName '/Scope']);
    set_param_safe([modelName '/Scope'], 'NumInputPorts', '3', 'Position', [700,30,950,350]);

    if ~ok
        fprintf('[X] 部分模块添加失败，请检查 Simulink 安装\n');
        save_system(modelName);
        return;
    end
    fprintf('[OK] 所有模块已添加\n');

    %% ===== 连线 =====
    fprintf('[3/5] 连线...\n');

    % Target → Error(+)
    add_line_safe(modelName, 'Target_Speed_kmh/1', 'Speed_Error/1');
    % Vx → Error(-)
    add_line_safe(modelName, 'Vx_kmh/1', 'Speed_Error/2');

    % Error → Kp & Ki
    add_line_safe(modelName, 'Speed_Error/1', 'Kp/1');
    add_line_safe(modelName, 'Speed_Error/1', 'Ki/1');

    % Ki → Integrator
    add_line_safe(modelName, 'Ki/1', 'Integrator/1');

    % Kp → PI_Sum(+), Integrator → PI_Sum(+)
    add_line_safe(modelName, 'Kp/1', 'PI_Sum/1');
    add_line_safe(modelName, 'Integrator/1', 'PI_Sum/2');

    % PI_Sum → Throttle_Limit → Throttle
    add_line_safe(modelName, 'PI_Sum/1', 'Throttle_Limit/1');
    add_line_safe(modelName, 'Throttle_Limit/1', 'Throttle/1');

    % PI_Sum → Brake_Gain → Brake_Limit → Brake_MPa
    add_line_safe(modelName, 'PI_Sum/1', 'Brake_Gain/1');
    add_line_safe(modelName, 'Brake_Gain/1', 'Brake_Limit/1');
    add_line_safe(modelName, 'Brake_Limit/1', 'Brake_MPa/1');

    % Mux: Vx, Target, PI_Sum → Scope
    muxOk = add_block_safe('simulink/Signal Routing/Mux', [modelName '/Mux']);
    if muxOk
        set_param_safe([modelName '/Mux'], 'Inputs', '3', 'Position', [660,60,670,120]);
        add_line_safe(modelName, 'Vx_kmh/1', 'Mux/1');
        add_line_safe(modelName, 'Target_Speed_kmh/1', 'Mux/2');
        add_line_safe(modelName, 'PI_Sum/1', 'Mux/3');
        add_line_safe(modelName, 'Mux/1', 'Scope/1');
    end

    fprintf('[OK] 连线完成\n');

    %% ===== 配置模型 =====
    fprintf('[4/5] 配置求解器...\n');
    set_param_safe(modelName, 'Solver', 'ode4');
    set_param_safe(modelName, 'FixedStep', '0.001');
    set_param_safe(modelName, 'StopTime', '30');
    set_param_safe(modelName, 'StartTime', '0.0');

    %% ===== 保存 =====
    fprintf('[5/5] 保存...\n');
    try
        save_system(modelName);
        open_system(modelName);
        fprintf('[OK] 模型已保存: %s.slx\n', modelName);
    catch e
        fprintf('[X] 保存失败: %s\n', e.message);
        return;
    end

    print_io_mapping();
end

%% ===== 工具函数 =====

function ok = add_block_safe(src, dest)
    try
        add_block(src, dest);
        ok = true;
    catch e
        fprintf('[X] 添加模块失败 %s: %s\n', dest, strrep(e.message, newline, ' '));
        ok = false;
    end
end

function set_param_safe(block, varargin)
    try
        set_param(block, varargin{:});
    catch e
        fprintf('[!] 设置参数失败 %s: %s\n', block, strrep(e.message, newline, ' '));
    end
end

function add_line_safe(model, src, dst)
    try
        add_line(model, src, dst);
    catch e
        fprintf('[!] 连线失败 %s -> %s: %s\n', src, dst, strrep(e.message, newline, ' '));
    end
end

function print_io_mapping()
    fprintf('\n===== CarSim 操作步骤 =====\n');
    fprintf('1. 打开 CarSim 2019.0\n');
    fprintf('2. 顶部点击 Run Control（第3个标签，有播放图标）\n');
    fprintf('3. 左侧 Models 下拉选 Simulink\n');
    fprintf('4. 浏览按钮选 carsim_cruise_ctrl.slx\n');
    fprintf('5. I/O Channels 按钮:\n');
    fprintf('   Export: Throttle / Brake / MotorTorque\n');
    fprintf('   Import: Vx / Ax / EngineRPM\n');
    fprintf('6. Time Step=0.001  Stop Time=30\n');
    fprintf('7. 点绿色 Run 按钮\n');
    fprintf('==========================\n');
end
