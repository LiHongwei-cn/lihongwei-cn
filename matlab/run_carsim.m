%% 一键入口：CarSim 定速巡航联合仿真
% 用法：MATLAB 命令行输入 run_carsim

scriptDir = fileparts(mfilename('fullpath'));
carsimDir = fullfile(scriptDir, 'carsim');
if isempty(which('run_carsim_cruise'))
    addpath(carsimDir);
end
if isempty(which('find_carsim'))
    addpath(fullfile(scriptDir, 'utils'));
end
run_carsim_cruise;
