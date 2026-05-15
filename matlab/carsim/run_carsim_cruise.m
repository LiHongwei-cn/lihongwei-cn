%% 一键运行 CarSim-Simulink 定速巡航联合仿真
% MATLAB R2016b + CarSim 2019.0 兼容
% 用途：运行此脚本 → 自动生成模型 → 启动 CarSim → 运行仿真
% 如果自动启动失败，会打印详细的手动步骤

function run_carsim_cruise()
    fprintf('===== CarSim 定速巡航联合仿真 =====\n\n');

    %% 步骤1：找到 CarSim 安装目录
    carsimDir = '';
    candidates = {
        'C:\Program Files\CarSim2019.0'
        'C:\CarSim2019.0'
        'C:\Program Files (x86)\CarSim2019.0'
    };
    for i = 1:length(candidates)
        if exist(candidates{i}, 'dir')
            carsimDir = candidates{i};
            fprintf('[OK] 找到 CarSim: %s\n', carsimDir);
            break;
        end
    end
    if isempty(carsimDir)
        fprintf('[X] 未找到 CarSim 安装目录\n');
        fprintf('    请修改本脚本中的 candidates 列表\n');
        return;
    end

    %% 步骤2：生成 Simulink 模型
    fprintf('[..] 生成 Simulink 模型...\n');
    build_carsim_model();
    modelPath = fullfile(fileparts(mfilename('fullpath')), 'carsim_cruise_ctrl.slx');

    %% 步骤3：尝试 COM 自动化
    cs = [];
    comNames = {'CarSim.Simulator', 'CarSim.Simulator.1', ...
                'CarSim.Application', 'MechanicalSimulation.CarSim'};
    for i = 1:length(comNames)
        try
            cs = actxserver(comNames{i});
            fprintf('[OK] CarSim COM 连接成功 (%s)\n', comNames{i});
            break;
        catch
        end
    end

    if isempty(cs)
        %% COM 不可用 → 打印手动步骤
        fprintf('\n[!] 无法自动启动 CarSim，请按下面步骤手动操作：\n');
        print_manual_steps(carsimDir, modelPath);
        return;
    end

    %% 步骤4：查找示例车辆
    vehicleFile = find_example_vehicle(carsimDir);
    if isempty(vehicleFile)
        fprintf('[!] 未找到示例车辆文件\n');
    else
        fprintf('[OK] 车辆: %s\n', vehicleFile);
    end

    %% 步骤5：创建仿真文件
    simFile = fullfile(fileparts(mfilename('fullpath')), '_carsim_temp.sim');
    create_sim_file(simFile, modelPath, vehicleFile);

    %% 步骤6：加载并运行
    try
        cs.LoadSimFile(simFile);
        fprintf('[..] 正在运行仿真...\n');
        cs.Run();
        fprintf('[OK] 仿真完成。查看 CarSim 动画和曲线窗口。\n');
    catch e
        fprintf('[X] COM 运行失败: %s\n', e.message);
        fprintf('    回退到手动模式:\n');
        print_manual_steps(carsimDir, modelPath);
    end
end

function vehicleFile = find_example_vehicle(carsimDir)
    vehicleFile = '';
    dataDir = fullfile(carsimDir, 'Data');
    if ~exist(dataDir, 'dir'), return; end

    % 递归搜索常见示例车辆
    patterns = {'*B-Class*', '*Hatchback*', '*Sedan*', '*SUV*', ...
                '*Ind_Ind*', '*example*', '*.veh'};
    for i = 1:length(patterns)
        results = dir(fullfile(dataDir, '**', patterns{i}));
        if ~isempty(results)
            vehicleFile = fullfile(results(1).folder, results(1).name);
            return;
        end
    end
end

function create_sim_file(path, modelPath, vehicleFile)
    fid = fopen(path, 'w');
    fprintf(fid, 'TSTOP = 30\n');
    fprintf(fid, 'TSTEP = 0.001\n');
    fprintf(fid, 'MODEL = SIMULINK\n');
    fprintf(fid, 'SIMFILE = %s\n', strrep(modelPath, '\', '\\'));
    if ~isempty(vehicleFile)
        fprintf(fid, 'VEHICLE = %s\n', strrep(vehicleFile, '\', '\\'));
    end
    fclose(fid);
end

function print_manual_steps(carsimDir, modelPath)
    fprintf('\n------------------------------------------------\n');
    fprintf('  手动操作步骤 (CarSim 2019.0)\n');
    fprintf('------------------------------------------------\n\n');
    fprintf('1. 打开 CarSim 2019.0\n');
    fprintf('   方法A: 双击桌面 CarSim 图标（蓝色小车图标）\n');
    fprintf('   方法B: 开始菜单搜索 CarSim → 点击 CarSim 2019.0\n');
    fprintf('   方法C: 直接双击这个文件夹:\n');
    fprintf('         %s\n', carsimDir);
    fprintf('         里面的 CarSim.exe 或 CarSim 快捷方式\n\n');
    fprintf('2. 软件打开后看顶部\n');
    fprintf('   菜单栏下方有一排大按钮/标签，按顺序是:\n');
    fprintf('   [车辆参数] → [工况设置] → [Run Control] → [结果]\n');
    fprintf('   点击 "Run Control"（中间那个，可能有播放图标 ▶）\n\n');
    fprintf('   如果看不到这些按钮:\n');
    fprintf('   - 点菜单栏 View → 勾选 Toolbar\n');
    fprintf('   - 点菜单栏 View → 勾选 Navigation Panel\n\n');
    fprintf('3. Run Control 页面左侧找到 Models 区域\n');
    fprintf('   下拉框从 "Internal" 改为 "Simulink"\n');
    fprintf('   点旁边的 "..." 浏览按钮，选:\n');
    fprintf('   %s\n\n', modelPath);
    fprintf('4. 点 I/O Channels 按钮:\n');
    fprintf('   Export 栏: Throttle / Brake / MotorTorque\n');
    fprintf('   Import 栏: Vx / Ax / EngineRPM\n\n');
    fprintf('5. Time Step = 0.001, Stop Time = 30\n');
    fprintf('   点绿色 Run 按钮 ▶\n');
    fprintf('------------------------------------------------\n');
end
