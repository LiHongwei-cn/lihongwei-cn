%% 启动脚本——添加 MATLAB 搜索路径
% 功能：将 matlab/ 目录下的工具函数和示例脚本添加到 MATLAB 搜索路径
% 兼容版本：MATLAB R2016b
% 使用方式：运行一次，或由 matlab.bat 自动调用

fprintf('正在添加 matlab 工具目录到搜索路径...\n');

scriptPath = fileparts(mfilename('fullpath'));

addpath(scriptPath);                              % matlab/ 根目录
addpath(fullfile(scriptPath, 'examples'));         % 示例脚本
addpath(fullfile(scriptPath, 'utils'));            % 工具函数

try
    savepath;
catch
    fprintf('(路径未保存到磁盘，下次启动时重新添加)\n');
end

fprintf('完成。可用命令: vehicle_dynamics motor_control test_all ...\n');
