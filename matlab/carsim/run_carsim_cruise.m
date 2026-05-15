%% 一键运行 CarSim-Simulink 定速巡航
% MATLAB R2016b + CarSim 2019.0
% 输入 run_carsim 调用此脚本

function run_carsim_cruise()
    fprintf('===== CarSim 定速巡航联合仿真 =====\n\n');

    myDir = fileparts(mfilename('fullpath'));
    if isempty(which('build_carsim_model'))
        addpath(myDir);
    end

    %% 步骤1: 生成 Simulink 模型
    fprintf('--- 步骤1: 生成 Simulink 模型 ---\n');
    try
        build_carsim_model();
    catch e
        fprintf('[X] 模型生成异常: %s\n', e.message);
        fprintf('    请检查:\n');
        fprintf('    - Simulink 是否已安装 (在 MATLAB 输入 ver 查看)\n');
        fprintf('    - 是否有 Simulink 许可证\n');
        return;
    end

    %% 步骤2: 查找 CarSim
    fprintf('\n--- 步骤2: 查找 CarSim ---\n');
    carsimDir = find_carsim();
    if isempty(carsimDir)
        fprintf('[!] 未找到 CarSim 安装，跳过自动启动\n');
    end

    %% 步骤3: 尝试启动 CarSim
    if ~isempty(carsimDir)
        fprintf('\n--- 步骤3: 尝试启动 CarSim ---\n');
        started = try_launch_carsim(carsimDir);
        if started
            fprintf('[OK] CarSim 已启动。请在 CarSim 中:\n');
            print_carsim_steps();
            return;
        end
    end

    %% 手动步骤
    fprintf('\n===== 请按以下步骤手动操作 =====\n');
    print_carsim_steps();
end

function csDir = find_carsim()
    csDir = '';
    candidates = {
        'C:\Program Files\CarSim2019.0', ...
        'C:\CarSim2019.0', ...
        'C:\Program Files (x86)\CarSim2019.0'
    };
    for i = 1:length(candidates)
        if exist(candidates{i}, 'dir')
            csDir = candidates{i};
            fprintf('[OK] CarSim 路径: %s\n', csDir);
            return;
        end
    end
end

function ok = try_launch_carsim(carsimDir)
    ok = false;
    % 查找可能的 exe 文件名
    exeNames = {'CarSim.exe', 'CarSim2019.exe', 'CarSim_2019.0.exe'};
    programsDir = fullfile(carsimDir, 'Programs');
    for i = 1:length(exeNames)
        exePath = fullfile(programsDir, exeNames{i});
        if exist(exePath, 'file')
            try
                system(['start "" "' exePath '"']);
                ok = true;
                return;
            catch
            end
        end
    end
    % 如果 Programs 子目录里找不到，尝试根目录
    for i = 1:length(exeNames)
        exePath = fullfile(carsimDir, exeNames{i});
        if exist(exePath, 'file')
            try
                system(['start "" "' exePath '"']);
                ok = true;
                return;
            catch
            end
        end
    end
end

function print_carsim_steps()
    fprintf('\n------------------------------------------------\n');
    fprintf('1. 打开 CarSim 2019.0\n');
    fprintf('   方法A: 双击桌面蓝色小车图标\n');
    fprintf('   方法B: 开始菜单搜索 CarSim\n\n');
    fprintf('2. 软件顶部一排大按钮，点击 Run Control（第3个，有播放图标）\n\n');
    fprintf('3. 左侧 Models 区域，下拉框从 Internal 改为 Simulink\n');
    fprintf('   点浏览按钮(...)选 carsim_cruise_ctrl.slx\n\n');
    fprintf('4. 点 I/O Channels 按钮:\n');
    fprintf('   Export(Simulink->CarSim): Throttle / Brake / MotorTorque\n');
    fprintf('   Import(CarSim->Simulink): Vx / Ax / EngineRPM\n\n');
    fprintf('5. Time Step=0.001  Stop Time=30\n');
    fprintf('   点绿色 Run 按钮\n');
    fprintf('------------------------------------------------\n');
end
