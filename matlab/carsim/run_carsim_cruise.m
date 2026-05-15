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

    %% 步骤2: 查找 CarSim 安装目录
    fprintf('\n--- 步骤2: 查找 CarSim ---\n');
    carsimDir = find_carsim_dir();

    %% 步骤3: 复制模型到 CarSim 目录
    if ~isempty(carsimDir)
        fprintf('\n--- 步骤3: 复制模型到 CarSim 目录 ---\n');
        copy_model_to_carsim(carsimDir);
        % 打开 CarSim 目录，方便用户找到主程序
        fprintf('[..] 打开 CarSim 安装目录...\n');
        system(['explorer "' carsimDir '"']);
    else
        fprintf('[!] 未找到 CarSim 安装目录\n');
    end

    %% 步骤4: 打印操作步骤
    fprintf('\n===== 接下来的操作 =====\n');
    print_carsim_steps();
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
                csDir = p;
                fprintf('[OK] 注册表找到: %s\n', csDir);
                return;
            elseif exist(p, 'file')
                csDir = fileparts(p);
                fprintf('[OK] 注册表找到: %s\n', csDir);
                return;
            end
        end
    end

    % 方法2: 常见路径
    candidates = {
        'C:\Program Files\CarSim2019.0', ...
        'C:\CarSim2019.0', ...
        'C:\CarSim2019.0_Data', ...
        'C:\Program Files (x86)\CarSim2019.0'
    };
    for i = 1:length(candidates)
        if exist(candidates{i}, 'dir')
            csDir = candidates{i};
            fprintf('[OK] 路径: %s\n', csDir);
            return;
        end
    end

    % 方法3: 全盘搜索
    fprintf('[..] 搜索 C 盘 exe 文件（约 30 秒）...\n');
    [status, result] = system('where /r C:\ CarSim*.exe 2>nul');
    if status == 0 && ~isempty(strtrim(result))
        lines = strsplit(strtrim(result), '\n');
        firstExe = strtrim(lines{1});
        csDir = fileparts(firstExe);
        fprintf('[OK] 找到: %s\n', csDir);
    end
end

%% ===== 复制模型到 CarSim 目录 =====

function copy_model_to_carsim(carsimDir)
    modelName = 'carsim_cruise_ctrl';
    src = [modelName '.slx'];
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
        return;
    end

    % 同时写一份说明
    readmePath = fullfile(carsimDir, '_carsim_simulink_说明.txt');
    try
        fid = fopen(readmePath, 'w', 'n', 'UTF-8');
        fprintf(fid, 'CarSim-Simulink 联合仿真说明\r\n');
        fprintf(fid, '================================\r\n\r\n');
        fprintf(fid, 'Simulink 模型: %s\r\n\r\n', dst);
        fprintf(fid, '操作步骤:\r\n');
        fprintf(fid, '1. 打开 CarSim 主程序（不是 ERD Converter）\r\n');
        fprintf(fid, '2. 顶部点击 Run Control（第3个标签，播放图标）\r\n');
        fprintf(fid, '3. 左侧 Models 下拉框改为 Simulink\r\n');
        fprintf(fid, '4. 点浏览按钮(...)选择:\r\n');
        fprintf(fid, '   %s\r\n\r\n', dst);
        fprintf(fid, '5. 点 I/O Channels 按钮，设置:\r\n');
        fprintf(fid, '   Export (Simulink → CarSim): Throttle / Brake / MotorTorque\r\n');
        fprintf(fid, '   Import (CarSim → Simulink): Vx / Ax / EngineRPM\r\n\r\n');
        fprintf(fid, '6. Time Step = 0.001, Stop Time = 30\r\n');
        fprintf(fid, '7. 点绿色 Run 按钮\r\n');
        fclose(fid);
    catch
    end
end

%% ===== 操作步骤 =====

function print_carsim_steps()
    fprintf('\n------------------------------------------------\n');
    fprintf('1. 在打开的文件夹中找到 CarSim 主程序（蓝色小车图标）\n');
    fprintf('   注意: 不是 ERD Converter！如不确定，找最大的 exe 文件\n\n');
    fprintf('2. 双击打开 CarSim → 顶部一排大按钮 → 点 Run Control\n');
    fprintf('   （第 3 个标签，有 ▶ 播放图标）\n\n');
    fprintf('3. 左侧 Models 区域 → 下拉框从 Internal 改为 Simulink\n');
    fprintf('   → 点浏览按钮(...)选 carsim_cruise_ctrl.slx\n');
    fprintf('   （已复制到 CarSim 安装目录里）\n\n');
    fprintf('4. 点 I/O Channels 按钮，设置通道:\n');
    fprintf('   Export (Simulink→CarSim): Throttle / Brake / MotorTorque\n');
    fprintf('   Import (CarSim→Simulink): Vx / Ax / EngineRPM\n\n');
    fprintf('5. Time Step=0.001  Stop Time=30\n');
    fprintf('   点绿色 Run 按钮 ▶\n');
    fprintf('------------------------------------------------\n');
end
