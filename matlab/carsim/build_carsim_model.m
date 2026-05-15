%% 构建 CarSim-Simulink 联合仿真模型
% MATLAB R2016b + CarSim 2019.0
% 生成 carsim_cruise_ctrl.slx（定速巡航控制器）

function build_carsim_model()
    modelName = 'carsim_cruise_ctrl';

    % 固定输出目录为本脚本所在目录
    outDir = fileparts(mfilename('fullpath'));
    slxPath = fullfile(outDir, [modelName '.slx']);

    fprintf('[1/5] 初始化...\n');
    fprintf('     输出目录: %s\n', outDir);

    [hasLicense, errMsg] = license('checkout', 'Simulink');
    if ~hasLicense
        fprintf('[X] Simulink 许可证不可用: %s\n', errMsg);
        return;
    end

    try
        load_system('simulink');
    catch
        fprintf('[X] 无法加载 Simulink 库，请确认 Simulink 已安装\n');
        return;
    end

    % 关闭已载入的同名模型
    if bdIsLoaded(modelName)
        close_system(modelName, 0);
    end

    % 删除旧文件
    if exist(slxPath, 'file'), delete(slxPath); end
    if exist(fullfile(outDir, [modelName '.mdl']), 'file')
        delete(fullfile(outDir, [modelName '.mdl']));
    end
    % 清理 slprj 缓存
    slprjDir = fullfile(outDir, 'slprj');
    if exist(slprjDir, 'dir'), rmdir(slprjDir, 's'); end

    % 切换工作目录，防止 Simulink 在别处生成文件
    prevDir = pwd;
    cd(outDir);
    cleanup = onCleanup(@() cd(prevDir));

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

    % --- 输入端口（CarSim → Simulink）---
    % 实际车速 km/h
    ok = ok && add_block_safe('simulink/Sources/In1', [modelName '/Vx_kmh']);
    set_param_safe([modelName '/Vx_kmh'], 'Position', [50,30,80,50]);

    % 纵向加速度 g
    ok = ok && add_block_safe('simulink/Sources/In1', [modelName '/Ax_g']);
    set_param_safe([modelName '/Ax_g'], 'Position', [50,90,80,110]);

    % 发动机转速 rpm
    ok = ok && add_block_safe('simulink/Sources/In1', [modelName '/EngineRPM']);
    set_param_safe([modelName '/EngineRPM'], 'Position', [50,150,80,170]);

    % --- 目标车速 ---
    ok = ok && add_block_safe('simulink/Sources/Constant', [modelName '/Target_Speed_kmh']);
    set_param_safe([modelName '/Target_Speed_kmh'], 'Value', '100', 'Position', [50,210,120,240]);

    % --- PI 控制器 ---
    ok = ok && add_block_safe('simulink/Math Operations/Sum', [modelName '/Speed_Error']);
    set_param_safe([modelName '/Speed_Error'], 'Inputs', '+-', 'Position', [160,30,190,100]);

    ok = ok && add_block_safe('simulink/Math Operations/Gain', [modelName '/Kp']);
    set_param_safe([modelName '/Kp'], 'Gain', '0.8', 'Position', [240,25,280,65]);

    ok = ok && add_block_safe('simulink/Math Operations/Gain', [modelName '/Ki']);
    set_param_safe([modelName '/Ki'], 'Gain', '2.0', 'Position', [240,95,280,135]);

    ok = ok && add_block_safe('simulink/Continuous/Integrator', [modelName '/Integrator']);
    set_param_safe([modelName '/Integrator'], 'Position', [330,95,370,135]);

    ok = ok && add_block_safe('simulink/Math Operations/Sum', [modelName '/PI_Sum']);
    set_param_safe([modelName '/PI_Sum'], 'Inputs', '++', 'Position', [420,50,450,120]);

    % --- 节气门输出通道 ---
    ok = ok && add_block_safe('simulink/Commonly Used Blocks/Saturation', [modelName '/Throttle_Limit']);
    set_param_safe([modelName '/Throttle_Limit'], 'UpperLimit', '1', 'LowerLimit', '0', ...
        'Position', [500,20,540,60]);

    ok = ok && add_block_safe('simulink/Sinks/Out1', [modelName '/Throttle']);
    set_param_safe([modelName '/Throttle'], 'Position', [590,25,620,55]);

    % --- 制动输出通道 ---
    ok = ok && add_block_safe('simulink/Math Operations/Gain', [modelName '/Brake_Gain']);
    set_param_safe([modelName '/Brake_Gain'], 'Gain', '5', 'Position', [500,95,540,135]);

    ok = ok && add_block_safe('simulink/Commonly Used Blocks/Saturation', [modelName '/Brake_Limit']);
    set_param_safe([modelName '/Brake_Limit'], 'UpperLimit', '15', 'LowerLimit', '0', ...
        'Position', [550,95,590,135]);

    ok = ok && add_block_safe('simulink/Sinks/Out1', [modelName '/Brake_MPa']);
    set_param_safe([modelName '/Brake_MPa'], 'Position', [640,100,670,130]);

    % --- 电机扭矩输出通道（CarSim 要求 3 个输出口）---
    ok = ok && add_block_safe('simulink/Sources/Constant', [modelName '/MotorTorque_Zero']);
    set_param_safe([modelName '/MotorTorque_Zero'], 'Value', '0', 'Position', [500,170,560,200]);

    ok = ok && add_block_safe('simulink/Sinks/Out1', [modelName '/MotorTorque']);
    set_param_safe([modelName '/MotorTorque'], 'Position', [590,175,620,205]);

    % --- Scope ---
    ok = ok && add_block_safe('simulink/Sinks/Scope', [modelName '/Scope']);
    set_param_safe([modelName '/Scope'], 'NumInputPorts', '4', 'Position', [700,30,950,350]);

    if ~ok
        fprintf('[X] 部分模块添加失败，请检查 Simulink 安装\n');
        save_system(modelName);
        return;
    end
    fprintf('[OK] 所有模块已添加\n');

    %% ===== 连线 =====
    fprintf('[3/5] 连线...\n');

    % Target → Error(+)  Vx → Error(-)
    add_line_safe(modelName, 'Target_Speed_kmh/1', 'Speed_Error/1');
    add_line_safe(modelName, 'Vx_kmh/1', 'Speed_Error/2');

    % Error → Kp   Error → Ki
    add_line_safe(modelName, 'Speed_Error/1', 'Kp/1');
    add_line_safe(modelName, 'Speed_Error/1', 'Ki/1');

    % Ki → Integrator
    add_line_safe(modelName, 'Ki/1', 'Integrator/1');

    % Kp → PI_Sum(+)   Integrator → PI_Sum(+)
    add_line_safe(modelName, 'Kp/1', 'PI_Sum/1');
    add_line_safe(modelName, 'Integrator/1', 'PI_Sum/2');

    % PI_Sum → Throttle_Limit → Throttle
    add_line_safe(modelName, 'PI_Sum/1', 'Throttle_Limit/1');
    add_line_safe(modelName, 'Throttle_Limit/1', 'Throttle/1');

    % PI_Sum → Brake_Gain → Brake_Limit → Brake_MPa
    add_line_safe(modelName, 'PI_Sum/1', 'Brake_Gain/1');
    add_line_safe(modelName, 'Brake_Gain/1', 'Brake_Limit/1');
    add_line_safe(modelName, 'Brake_Limit/1', 'Brake_MPa/1');

    % MotorTorque → 0
    add_line_safe(modelName, 'MotorTorque_Zero/1', 'MotorTorque/1');

    % Mux: Vx, Target, PI_Sum, Ax → Scope
    muxOk = add_block_safe('simulink/Signal Routing/Mux', [modelName '/Mux']);
    if muxOk
        set_param_safe([modelName '/Mux'], 'Inputs', '4', 'Position', [660,60,670,130]);
        add_line_safe(modelName, 'Vx_kmh/1', 'Mux/1');
        add_line_safe(modelName, 'Target_Speed_kmh/1', 'Mux/2');
        add_line_safe(modelName, 'PI_Sum/1', 'Mux/3');
        add_line_safe(modelName, 'Ax_g/1', 'Mux/4');
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
        fprintf('[OK] 模型已保存: %s\n', slxPath);
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
    fprintf('\n===== CarSim I/O 通道映射 =====\n');
    fprintf('Export (Simulink → CarSim):\n');
    fprintf('  1. Throttle      [节气门开度 0~1]\n');
    fprintf('  2. Brake_MPa      [制动主缸压力 MPa]\n');
    fprintf('  3. MotorTorque    [电机扭矩 N·m]\n');
    fprintf('Import (CarSim → Simulink):\n');
    fprintf('  1. Vx_kmh         [纵向车速 km/h]\n');
    fprintf('  2. Ax_g           [纵向加速度 g]\n');
    fprintf('  3. EngineRPM      [发动机转速 rpm]\n');
    fprintf('================================\n');
end
