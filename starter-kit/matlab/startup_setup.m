%% Startup script - add MATLAB search paths
% R2016b compatible
% Run once, or auto-run from matlab.bat

fprintf('Adding matlab tool directories to search path...\n');

scriptPath = fileparts(mfilename('fullpath'));

addpath(scriptPath);
addpath(fullfile(scriptPath, 'examples'));
addpath(fullfile(scriptPath, 'utils'));
addpath(fullfile(scriptPath, 'carsim'));

try
    savepath;
catch
    fprintf('(path not saved to disk, will re-apply next launch)\n');
end

fprintf('Done. Commands: vehicle_dynamics motor_control test_all ...\n');
