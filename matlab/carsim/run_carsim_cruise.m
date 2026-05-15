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
        return;
    end

    %% 步骤2: 查找 CarSim 安装目录
    fprintf('\n--- 步骤2: 查找 CarSim ---\n');
    carsimDir = find_carsim_dir();

    %% 步骤3: 复制模型到 CarSim 目录
    if ~isempty(carsimDir)
        fprintf('\n--- 步骤3: 复制模型到 CarSim 目录 ---\n');
        copy_model_to_carsim(carsimDir);

        % 尝试清理 slprj
        slprjDir = fullfile(myDir, 'slprj');
        if exist(slprjDir, 'dir')
            try, rmdir(slprjDir, 's'); end
        end
    else
        fprintf('[!] 未找到 CarSim 安装目录\n');
    end

    %% 步骤4: 操作说明
    fprintf('\n===== 接下来的操作 =====\n');
    print_carsim_steps(carsimDir);
end

%% ===== 查找 CarSim 安装目录 =====

function csDir = find_carsim_dir()
    csDir = '';

    % 方法1: 注册表
    fprintf('[..] 搜索注册表...\n');
    keys = {
        'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', ...
        'HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall', ...
        'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
    };
    for k = 1:length(keys)
        [st, res] = system(['reg query "' keys{k} '" /s 2>nul']);
        if st ~= 0 || isempty(strtrim(res)), continue; end
        tokens = regexp(res, 'InstallLocation\s+REG\w+\s+(.*CarSim[^\r\n]*)', 'tokens');
        if isempty(tokens)
            tokens = regexp(res, 'DisplayIcon\s+REG\w+\s+(.*CarSim[^\r\n]*\.exe)', 'tokens');
        end
        for i = 1:length(tokens)
            p = strtrim(tokens{i}{1});
            p = regexprep(p, '["\\]+$', '');
            if exist(p, 'dir')
                csDir = p; fprintf('[OK] 注册表找到: %s\n', csDir); return;
            elseif exist(p, 'file')
                csDir = fileparts(p);
                fprintf('[OK] 注册表找到: %s\n', csDir); return;
            end
        end
    end

    % 方法2: 常见路径
    candidates = {
        'C:\Program Files (x86)\CarSim2019.0_Prog', ...
        'C:\Program Files\CarSim2019.0', ...
        'C:\CarSim2019.0', ...
        'C:\CarSim2019.0_Data', ...
        'C:\Program Files (x86)\CarSim2019.0'
    };
    for i = 1:length(candidates)
        if exist(candidates{i}, 'dir')
            csDir = candidates{i};
            fprintf('[OK] 路径: %s\n', csDir); return;
        end
    end

    % 方法3: 全盘搜索
    fprintf('[..] 搜索 C 盘（约 30 秒）...\n');
    [status, result] = system('where /r C:\ CarSim*.exe 2>nul');
    if status == 0 && ~isempty(strtrim(result))
        lines = strsplit(strtrim(result), '\n');
        csDir = fileparts(strtrim(lines{1}));
        fprintf('[OK] 找到: %s\n', csDir);
    end
end

%% ===== 复制模型到 CarSim 目录 =====

function copy_model_to_carsim(carsimDir)
    myDir = fileparts(mfilename('fullpath'));
    modelName = 'carsim_cruise_ctrl';

    src = fullfile(myDir, [modelName '.slx']);
    if ~exist(src, 'file')
        fprintf('[!] 源文件不存在: %s\n', src);
        return;
    end

    dst = fullfile(carsimDir, [modelName '.slx']);
    try
        copyfile(src, dst, 'f');
        fprintf('[OK] 模型已复制到: %s\n', dst);
    catch e
        fprintf('[!] 复制失败: %s\n', e.message);
    end

    % 打开 CarSim 目录
    fprintf('[..] 打开 CarSim 安装目录...\n');
    system(['explorer "' carsimDir '"']);
end

%% ===== 操作步骤 =====

function print_carsim_steps(carsimDir)
    fprintf('\n------------------------------------------------\n');
    fprintf('1. 在打开的文件夹中找到 CarSim 主程序，双击打开\n');
    fprintf('   （红色小车图标 CarSim.exe，不是 ERD Converter）\n\n');
    fprintf('2. 软件顶部一排大按钮 → 点 Run Control\n');
    fprintf('   （第 3 个标签，有 ▶ 播放图标）\n\n');
    fprintf('3. 左侧 Models 下拉框：Internal 改为 Simulink\n');
    fprintf('   → 点浏览按钮(...)选择 carsim_cruise_ctrl.slx\n');
    if ~isempty(carsimDir)
        fprintf('   （文件位置: %s）\n\n', carsimDir);
    end
    fprintf('4. 点 I/O Channels 按钮，设置通道:\n');
    fprintf('   Export(Simulink→CarSim): Throttle / Brake_MPa / MotorTorque\n');
    fprintf('   Import(CarSim→Simulink): Vx_kmh / Ax_g / EngineRPM\n\n');
    fprintf('5. Time Step = 0.001  Stop Time = 30\n');
    fprintf('   点绿色 Run 按钮 ▶\n');
    fprintf('------------------------------------------------\n');
end
