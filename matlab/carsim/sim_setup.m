%% CarSim-Simulink 联合仿真环境配置
% MATLAB R2016b + CarSim 2019.0 兼容
% 运行此脚本配置联合仿真环境，运行一次即可

function sim_setup()
    fprintf('===== CarSim-Simulink 联合仿真配置 =====\n\n');

    currentDir = fileparts(mfilename('fullpath'));

    csProg = 'C:\Program Files (x86)\CarSim2019.0_Prog';
    csData = 'C:\Users\Public\Documents\CarSim2019.0_Data';

    if ~exist(csProg, 'dir')
        fprintf('[X] 未找到 CarSim 2019.0 安装目录\n');
        fprintf('   预期路径: %s\n', csProg);
        fprintf('   如路径不同请修改本脚本 csProg 变量\n');
        return;
    end

    fprintf('[OK] CarSim 安装目录: %s\n', csProg);
    fprintf('[OK] CarSim 数据目录: %s\n', csData);

    % 添加 Programs 目录 (RunMatlab.dll)
    progDir = fullfile(csProg, 'Programs');
    if exist(progDir, 'dir')
        addpath(progDir);
        fprintf('[OK] 已添加路径: %s\n', progDir);
    end

    % 添加 Solver 目录 (Simulink S-Function)
    solverDir = fullfile(csProg, 'Programs', 'solvers', 'Matlab84+');
    if exist(solverDir, 'dir')
        addpath(solverDir);
        fprintf('[OK] 已添加 Solver: %s\n', solverDir);
    end

    addpath(currentDir);
    addpath(fullfile(currentDir, '..', 'utils'));
    addpath(fullfile(currentDir, '..', 'examples'));

    savepath;
    fprintf('\n配置完成。运行 build_carsim_model 创建联合仿真模型。\n');
end
