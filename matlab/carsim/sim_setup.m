%% CarSim-Simulink 联合仿真环境配置
% MATLAB R2016b + CarSim 2019.0 兼容
% 运行一次即可，自动检测 CarSim 安装路径

function sim_setup()
    fprintf('===== CarSim-Simulink 联合仿真配置 =====\n\n');

    [~, csDir] = find_carsim();
    if isempty(csDir)
        fprintf('[X] 未找到 CarSim 安装目录\n');
        fprintf('   搜索路径: C:\\Program Files (x86)\\CarSim* 和 C:\\Program Files\\CarSim*\n');
        return;
    end

    fprintf('[OK] 检测到 CarSim: %s\n', csDir);

    progDir = fullfile(csDir, 'Programs');
    if exist(progDir, 'dir')
        addpath(progDir);
        fprintf('[OK] 已添加: %s\n', progDir);
    end

    solverDir = fullfile(csDir, 'Programs', 'solvers', 'Matlab84+');
    if exist(solverDir, 'dir')
        addpath(solverDir);
        fprintf('[OK] 已添加 Solver: %s\n', solverDir);
    end

    currentDir = fileparts(mfilename('fullpath'));
    addpath(currentDir);
    addpath(fullfile(currentDir, '..', 'utils'));
    addpath(fullfile(currentDir, '..', 'examples'));

    savepath;
    fprintf('\n配置完成。运行 build_carsim_model 创建联合仿真模型。\n');
end

