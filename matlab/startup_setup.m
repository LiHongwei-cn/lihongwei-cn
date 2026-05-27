%% 启动脚本——添加 MATLAB 搜索路径
% 功能：将 matlab/ 目录下的工具函数和示例脚本添加到 MATLAB 搜索路径
% 兼容版本：MATLAB R2016b
% 使用方式：运行一次，或由 matlab.bat 自动调用

fprintf('Adding matlab directories to path...\n');

scriptPath = fileparts(mfilename('fullpath'));

addpath(scriptPath);                              % matlab/ 根目录
addpath(fullfile(scriptPath, 'examples'));         % 示例脚本
addpath(fullfile(scriptPath, 'utils'));            % 工具函数

try
    savepath;
catch
    fprintf('(Path not saved to disk, will re-add on next startup)\n');
end

fprintf('Done. Commands: vehicle_dynamics motor_control test_all ...\n');
