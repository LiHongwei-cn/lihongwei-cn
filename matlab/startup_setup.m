%% 启动脚本 - 添加 MATLAB 搜索路径
% R2016b 兼容
% 运行一次即可，或在 MATLAB 启动脚本中添加

fprintf('添加 matlab 工具目录到搜索路径...\n');

scriptPath = fileparts(mfilename('fullpath'));

addpath(scriptPath);
addpath(fullfile(scriptPath, 'examples'));
addpath(fullfile(scriptPath, 'utils'));
addpath(fullfile(scriptPath, 'carsim'));

savepath;

fprintf('完成。test_all / vehicle_dynamics / motor_control 等均可直接使用。\n');
