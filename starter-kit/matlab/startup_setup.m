%% 启动脚本 - 添加 MATLAB 搜索路径
% R2016b 兼容
% 运行一次即可，或在 MATLAB 启动脚本中添加

fprintf('添加 matlab 工具目录到搜索路径...\n');

% 获取当前脚本所在目录
scriptPath = fileparts(mfilename('fullpath'));

% 添加子目录
addpath(fullfile(scriptPath, 'examples'));
addpath(fullfile(scriptPath, 'utils'));
addpath(fullfile(scriptPath, 'carsim'));

% 保存路径（下次自动生效）
savepath;

fprintf('完成。\n');
