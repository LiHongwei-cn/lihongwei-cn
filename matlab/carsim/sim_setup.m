%% CarSim-Simulink 联合仿真环境配置
% MATLAB R2016b + CarSim 2019.0 兼容
% 运行此脚本配置联合仿真环境，运行一次即可

function sim_setup()
    fprintf('===== CarSim-Simulink 联合仿真配置 =====\n\n');

    currentDir = fileparts(mfilename('fullpath'));

    % CarSim 常见安装路径
    carsimDirs = {
        'C:\Program Files\CarSim2019.0'
        'C:\CarSim2019.0'
        'C:\Program Files (x86)\CarSim2019.0'
    };

    found = false;
    for i = 1:length(carsimDirs)
        if exist(carsimDirs{i}, 'dir')
            fprintf('发现 CarSim: %s\n', carsimDirs{i});
            simDir = fullfile(carsimDirs{i}, 'Simulink');
            if exist(simDir, 'dir')
                addpath(simDir);
                fprintf('已添加 Simulink 接口: %s\n', simDir);
            end
            % 添加 DLL 目录
            dllDir = fullfile(carsimDirs{i}, 'Programs');
            if exist(dllDir, 'dir')
                addpath(dllDir);
            end
            % 检查 S-Function 文件
            sfunFiles = dir(fullfile(simDir, 'carsim_sfun*'));
            if ~isempty(sfunFiles)
                fprintf('S-Function 已找到: %s\n', sfunFiles(1).name);
            end
            found = true;
        end
    end

    if ~found
        fprintf('未找到 CarSim 安装目录。\n');
        fprintf('请修改本脚本中的 carsimDirs 添加你的安装路径。\n');
    end

    addpath(currentDir);
    addpath(fullfile(currentDir, '..', 'utils'));
    addpath(fullfile(currentDir, '..', 'examples'));

    savepath;
    fprintf('\n配置完成。运行 build_carsim_model 创建联合仿真模型。\n');
end
