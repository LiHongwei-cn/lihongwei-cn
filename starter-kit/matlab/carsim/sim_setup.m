%% CarSim-Simulink 联合仿真配置
% MATLAB R2016b 兼容
% 运行此脚本配置联合仿真环境

function sim_setup()
    fprintf('===== CarSim-Simulink 联合仿真配置 =====\n\n');

    % 获取当前目录
    currentDir = fileparts(mfilename('fullpath'));

    % 检查 CarSim 是否已安装
    carsimDirs = {
        'C:\Program Files\CarSim2019.0'
        'C:\CarSim2019.0'
    };

    found = false;
    for i = 1:length(carsimDirs)
        if exist(carsimDirs{i}, 'dir')
            fprintf('发现 CarSim 安装目录: %s\n', carsimDirs{i});

            % 检查 Simulink 接口文件
            simDir = fullfile(carsimDirs{i}, 'Simulink');
            if exist(simDir, 'dir')
                addpath(simDir);
                fprintf('已添加 Simulink 接口路径\n');
            end
            found = true;
        end
    end

    if ~found
        fprintf('警告: 未找到 CarSim 安装目录\n');
        fprintf('请手动定位 CarSim 安装路径\n');
    end

    % 添加工具路径
    addpath(currentDir);
    addpath(fullfile(currentDir, '..', 'utils'));
    addpath(fullfile(currentDir, '..', 'examples'));

    fprintf('\n配置完成。\n');
    fprintf('使用步骤：\n');
    fprintf('1. 在 CarSim 中配置车辆参数\n');
    fprintf('2. 点击 Send to Simulink 导出模型\n');
    fprintf('3. 在 MATLAB 中打开生成的 .mdl 文件\n');
    fprintf('4. 运行仿真\n');
end
