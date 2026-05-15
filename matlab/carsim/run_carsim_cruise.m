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
        'C:\CarSim2019.0_Data', ...
        'C:\Program Files (x86)\CarSim2019.0'
    };
    for i = 1:length(candidates)
        if exist(candidates{i}, 'dir')
            csDir = candidates{i};
            fprintf('[OK] CarSim 路径: %s\n', csDir);
            return;
        end
    end
    % 最后尝试搜索 C 盘
    fprintf('[..] 正在搜索 CarSim 安装目录...\n');
    try
        [status, result] = system('where /r C:\ CarSim*.exe 2>nul');
        if status == 0 && ~isempty(strtrim(result))
            lines = strsplit(strtrim(result), '\n');
            firstExe = strtrim(lines{1});
            csDir = fileparts(firstExe);
            fprintf('[OK] 找到: %s\n', csDir);
        end
    catch
    end
end

function ok = try_launch_carsim(carsimDir)
    ok = false;
    % 主程序名（按优先级排列）
    exeNames = {'CarSimGui', 'CarSim', 'CarSim2019', ...
                'CarSim_2019.0', 'CarSimEd', 'CarSimBatch'};
    % 排除的工具类 exe（ERDConverter、Uninstaller 等）
    blacklist = {'ERDConverter', 'ERD', 'Uninstall', 'setup', ...
                 'Setup', 'Installer', 'License', 'Register'};
    % 搜索子目录，按优先级
    searchDirs = {fullfile(carsimDir, 'bin'), ...
                  fullfile(carsimDir, 'Programs'), ...
                  fullfile(carsimDir, 'Programs', 'Solvers'), ...
                  carsimDir};

    for d = 1:length(searchDirs)
        if ~exist(searchDirs{d}, 'dir'), continue; end

        % 第一阶段：匹配已知主程序名
        for i = 1:length(exeNames)
            exePath = fullfile(searchDirs{d}, [exeNames{i} '.exe']);
            if exist(exePath, 'file')
                fprintf('[..] 启动: %s\n', exePath);
                try
                    system(['start "" "' exePath '"']);
                    ok = true;
                    return;
                catch e
                    fprintf('[!] 启动失败: %s\n', e.message);
                end
            end
        end

        % 第二阶段：搜索目录下所有 exe，排除工具类，选最大的（主程序通常最大）
        listing = dir(fullfile(searchDirs{d}, '*.exe'));
        candidates = {};
        for i = 1:length(listing)
            [~, name] = fileparts(listing(i).name);
            skip = false;
            for b = 1:length(blacklist)
                if ~isempty(strfind(lower(name), lower(blacklist{b})))
                    skip = true; break;
                end
            end
            if ~skip
                candidates{end+1} = listing(i); %#ok<AGROW>
            end
        end
        if ~isempty(candidates)
            % 按文件大小降序排列（主程序通常最大）
            sizes = [candidates.bytes];
            [~, idx] = sort(sizes, 'descend');
            best = candidates{idx(1)};
            exePath = fullfile(searchDirs{d}, best.name);
            fprintf('[..] 启动（自动选择，%.1f MB）: %s\n', best.bytes/1e6, exePath);
            try
                system(['start "" "' exePath '"']);
                ok = true;
                return;
            catch e
                fprintf('[!] 启动失败: %s\n', e.message);
            end
        end
    end
    if ~ok
        fprintf('[!] 在 %s 下未找到 CarSim 主程序\n', carsimDir);
        fprintf('    已搜索: bin/ Programs/ Programs/Solvers/ 根目录\n');
        fprintf('    请手动打开 CarSim，然后继续以下步骤\n');
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
