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
    carsimDir = find_carsim();
    if isempty(carsimDir)
        fprintf('[!] 未找到 CarSim 安装，跳过自动启动\n');
        print_manual_steps();
        return;
    end

    %% 步骤3: 扫描 exe 并启动主程序
    fprintf('\n--- 步骤3: 扫描可执行文件 ---\n');
    started = smart_launch(carsimDir);
    if started
        fprintf('[OK] CarSim 已启动。请在 CarSim 中:\n');
        print_carsim_steps();
    else
        fprintf('\n===== 自动启动失败，请手动操作 =====\n');
        print_manual_steps();
    end
end

%% ===== 查找 CarSim 安装目录 =====

function csDir = find_carsim()
    csDir = '';

    % 方法1: Windows 注册表（最精确）
    fprintf('[..] 搜索注册表...\n');
    csDir = find_from_registry();
    if ~isempty(csDir), return; end

    % 方法2: 全盘搜索 CarSim*.exe
    fprintf('[..] 搜索 C 盘 exe 文件（约 30 秒）...\n');
    [status, result] = system('where /r C:\ CarSim*.exe 2>nul');
    if status == 0 && ~isempty(strtrim(result))
        lines = strsplit(strtrim(result), '\n');
        firstExe = strtrim(lines{1});
        csDir = fileparts(firstExe);
        fprintf('[OK] 找到: %s\n', csDir);
        return;
    end

    % 方法3: 常见安装路径
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
end

function csDir = find_from_registry()
    csDir = '';
    keys = {
        'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall', ...
        'HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall', ...
        'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
    };
    for k = 1:length(keys)
        % 导出整个 Uninstall 分支，搜索含 CarSim 的值
        [st, res] = system(['reg query "' keys{k} '" /s 2>nul']);
        if st ~= 0 || isempty(strtrim(res)), continue; end

        % 查找 InstallLocation 值中路径含 CarSim 的行
        tokens = regexp(res, 'InstallLocation\s+REG\w+\s+(.*CarSim[^\r\n]*)', 'tokens');
        if isempty(tokens)
            % 退而求其次：DisplayIcon
            tokens = regexp(res, 'DisplayIcon\s+REG\w+\s+(.*CarSim[^\r\n]*\.exe)', 'tokens');
        end
        for i = 1:length(tokens)
            p = strtrim(tokens{i}{1});
            % 清理末尾反斜杠
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
end

%% ===== 智能启动 CarSim 主程序 =====

function ok = smart_launch(carsimDir)
    ok = false;

    % 扫描目录树所有 exe 文件
    exeList = scan_exe_tree(carsimDir);
    if isempty(exeList)
        fprintf('[!] 目录下没有 exe 文件\n');
        return;
    end

    fprintf('  找到 %d 个 exe:\n', length(exeList));
    for i = 1:length(exeList)
        fprintf('    [%d] %s  (%.1f MB)\n', ...
            i, exeList(i).name, exeList(i).bytes/1e6);
    end

    % 筛选并排序
    candidates = rank_exes(exeList, carsimDir);
    if isempty(candidates)
        fprintf('[!] 所有 exe 都被过滤，无候选\n');
        return;
    end

    fprintf('  候选主程序:\n');
    for i = 1:length(candidates)
        fprintf('    [%d] %s  (%.1f MB, 得分=%d)\n', ...
            i, candidates(i).name, candidates(i).bytes/1e6, candidates(i).score);
    end

    % 尝试启动得分最高的
    best = candidates(1);
    fprintf('[..] 启动: %s\n', best.fullpath);
    try
        system(['start "" "' best.fullpath '"']);
        ok = true;
    catch e
        fprintf('[!] 启动失败: %s\n', e.message);
    end
end

function exeList = scan_exe_tree(rootDir)
    % 用 PowerShell 递归扫描（dir /s 编码不可靠）
    exeList = [];
    psCmd = ['powershell -Command "Get-ChildItem -Path ''', ...
        strrep(rootDir, '\', '\\'), ...
        ''' -Recurse -Filter ''*.exe'' -ErrorAction SilentlyContinue | ', ...
        'Select-Object FullName, Length | ConvertTo-Csv -NoTypeInformation"'];
    [st, res] = system(psCmd);
    if st ~= 0 || isempty(strtrim(res)), return; end

    lines = strsplit(strtrim(res), '\n');
    count = 0;
    for i = 2:length(lines)  % 跳过 CSV 头
        parts = strsplit(strtrim(lines{i}), '","');
        if length(parts) < 2, continue; end
        fpath = strrep(parts{1}, '"', '');
        fsize = str2double(strrep(parts{2}, '"', ''));
        if isnan(fsize) || fsize < 1024, continue; end  % 跳过 <1KB 的文件
        [~, fname, fext] = fileparts(fpath);
        count = count + 1;
        exeList(count).fullpath = fpath;  %#ok<AGROW>
        exeList(count).name = [fname fext];  %#ok<AGROW>
        exeList(count).bytes = fsize;  %#ok<AGROW>
        exeList(count).folder = fileparts(fpath);  %#ok<AGROW>
    end
end

function candidates = rank_exes(exeList, rootDir)
    % 为每个 exe 打分，选出最可能是主程序的
    BL = {'ERDConverter', 'ERD', 'erdconv', 'Uninstall', 'unins', ...
          'setup', 'Setup', 'Installer', 'License', 'Register', ...
          'RegisterMSC', 'SendLog', 'vs', 'vc_redist', 'dotnet', ...
          'Windows', 'vcredist', 'dxsetup', 'solver', 'Solver'};

    n = length(exeList);
    scores = zeros(n, 1);

    % 正规化根目录路径
    rootDir = lower(strrep(rootDir, '\', '/'));

    for i = 1:n
        name = exeList(i).name;
        lowerName = lower(name);
        folder = lower(strrep(exeList(i).folder, '\', '/'));
        relFolder = strrep(folder, [rootDir '/'], '');
        depth = length(strfind(relFolder, '/'));

        % 黑名单检查
        blacklisted = false;
        for b = 1:length(BL)
            if ~isempty(strfind(lowerName, lower(BL{b})))
                blacklisted = true;
                break;
            end
        end

        % 路径中包含 tool/util/erd 等子目录，降权
        inToolDir = ~isempty(strfind(relFolder, 'tool')) || ...
                    ~isempty(strfind(relFolder, 'util')) || ...
                    ~isempty(strfind(relFolder, 'erd')) || ...
                    ~isempty(strfind(relFolder, 'redist')) || ...
                    ~isempty(strfind(relFolder, 'third'));

        s = 0;

        if blacklisted
            s = -1000;  % 直接排除
        else
            % 文件大小得分（越大越好，主程序通常 10-50 MB）
            szMB = exeList(i).bytes / 1e6;
            if szMB > 50, s = s + 30;
            elseif szMB > 10, s = s + 50;
            elseif szMB > 3, s = s + 20;
            else s = s + 5;
            end

            % 名称包含 CarSim（高权重）
            if ~isempty(strfind(lowerName, 'carsim'))
                s = s + 60;
            end

            % 名称包含 Gui / Main / Prog / App
            if ~isempty(strfind(lowerName, 'gui')) || ...
               ~isempty(strfind(lowerName, 'main')) || ...
               ~isempty(strfind(lowerName, 'prog'))
                s = s + 25;
            end

            % 不包含 Tool/Solver/Converter/Server
            if isempty(strfind(lowerName, 'tool')) && ...
               isempty(strfind(lowerName, 'converter')) && ...
               isempty(strfind(lowerName, 'server')) && ...
               isempty(strfind(lowerName, 'service'))
                s = s + 20;
            end

            % 深度惩罚（越深越不可能是主程序）
            if depth == 0, s = s + 30;
            elseif depth == 1, s = s + 15;
            else s = s - depth * 5;
            end

            % 在工具目录中
            if inToolDir, s = s - 40; end
        end

        scores(i) = s;
        exeList(i).score = s;
    end

    % 按得分降序排列
    [~, idx] = sort(scores, 'descend');
    candidates = exeList(idx);
    candidates = candidates([candidates.score] > 0);
end

%% ===== 手动步骤输出 =====

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

function print_manual_steps()
    fprintf('\n===== 手动操作步骤 =====\n');
    fprintf('1. 找到 CarSim 安装目录，双击主程序（蓝色小车图标）\n');
    fprintf('2. 如果找不到，开始菜单搜索 CarSim\n');
    print_carsim_steps();
end
