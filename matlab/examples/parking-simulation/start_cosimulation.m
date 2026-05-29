%% START_COSIMULATION - CarSim+Simulink倒车入库联合仿真启动脚本
% 兼容版本：MATLAB R2016b
% 功能：自动配置路径、检查依赖、启动联合仿真
%
% 作者：LiHongwei
% 日期：2026-05-29

clear; clc; close all;

fprintf('============================================================\n');
fprintf('  CarSim 2019.0 + MATLAB R2016b 倒车入库联合仿真\n');
fprintf('============================================================\n\n');

%% ==================== 步骤1：配置路径 ====================

fprintf('[步骤1/6] 配置路径...\n');

% 获取脚本所在目录
script_dir = fileparts(mfilename('fullpath'));
if isempty(script_dir)
    script_dir = pwd;
end
cd(script_dir);
fprintf('  工作目录: %s\n', pwd);

% CarSim S-Function路径
carsim_mex_dir = 'C:\Program Files (x86)\CarSim2019.0_Prog\Programs\vs_connect';
carsim_solvers_dir = 'C:\Program Files (x86)\CarSim2019.0_Prog\Programs\vs_connect';

% 添加路径
if exist(carsim_mex_dir, 'dir')
    addpath(carsim_mex_dir);
    fprintf('  [OK] CarSim S-Function路径已添加\n');
else
    fprintf('  [警告] CarSim S-Function目录不存在: %s\n', carsim_mex_dir);
end

addpath(pwd);
fprintf('  [OK] 工作目录已添加到MATLAB路径\n');
fprintf('\n');

%% ==================== 步骤2：检查依赖文件 ====================

fprintf('[步骤2/6] 检查依赖文件...\n');

% 检查CPAR文件
if exist('Parking_Reversing.cpar', 'file')
    fprintf('  [OK] Parking_Reversing.cpar\n');
else
    fprintf('  [错误] Parking_Reversing.cpar 未找到！\n');
    fprintf('  请先运行配置生成脚本\n');
    return;
end

% 检查S-Function
sfunc_found = false;
if exist('vs_connect_sf2.mexw64', 'file')
    fprintf('  [OK] vs_connect_sf2.mexw64 (本地副本)\n');
    sfunc_found = true;
elseif exist(fullfile(carsim_mex_dir, 'vs_connect_sf2.mexw64'), 'file')
    fprintf('  [OK] vs_connect_sf2.mexw64 (CarSim目录)\n');
    sfunc_found = true;
end

if ~sfunc_found
    fprintf('  [错误] S-Function MEX文件未找到！\n');
    fprintf('  请从CarSim导出S-Function或复制到工作目录\n');
    return;
end

% 检查Simulink模型
if exist('parking_reverse_control.slx', 'file')
    fprintf('  [OK] parking_reverse_control.slx\n');
else
    fprintf('  [信息] Simulink模型将在运行时自动创建\n');
end

fprintf('\n');

%% ==================== 步骤3：检查CarSim连接 ====================

fprintf('[步骤3/6] 检查CarSim连接...\n');

carsim_connected = false;
try
    % 尝试通过COM接口连接CarSim
    h = actxserver('CarSim.Application');
    fprintf('  [OK] CarSim COM接口已连接\n');
    carsim_connected = true;

    % 尝试导入CPAR文件
    fprintf('  正在导入CPAR配置文件...\n');
    cpar_file = fullfile(pwd, 'Parking_Reversing.cpar');
    if exist(cpar_file, 'file')
        try
            h.ImportDataset(cpar_file);
            fprintf('  [OK] CPAR文件导入成功\n');
        catch ME
            fprintf('  [警告] CPAR导入失败: %s\n', ME.message);
            fprintf('  请在CarSim中手动导入: File > Import Dataset\n');
        end
    end

    % 释放COM对象
    h.release;
catch ME
    fprintf('  [信息] CarSim COM接口不可用: %s\n', ME.message);
    fprintf('  这是正常的，CarSim可能未打开或未配置COM接口\n');
    fprintf('  请确保CarSim已打开并导入了Parking_Reversing.cpar\n');
end
fprintf('\n');

%% ==================== 步骤4：显示系统状态 ====================

fprintf('[步骤4/6] 系统状态\n');
fprintf('  ┌─────────────────────────────────────────────────────────┐\n');
fprintf('  │  CarSim + Simulink 倒车入库联合仿真                    │\n');
fprintf('  ├─────────────────────────────────────────────────────────┤\n');
fprintf('  │  MATLAB R2016b: 已连接                                  │\n');

if carsim_connected
    fprintf('  │  CarSim 2019.0: 已连接 (COM)                           │\n');
else
    fprintf('  │  CarSim 2019.0: 等待连接 (请确保CarSim已打开)         │\n');
end

fprintf('  │                                                         │\n');
fprintf('  │  场景参数:                                              │\n');
fprintf('  │    - 道路: 50m x 6m                                    │\n');
fprintf('  │    - 车位: 10个 (5m x 2.5m)                           │\n');
fprintf('  │    - 目标: 第5个车位 (空置)                           │\n');
fprintf('  │    - 初始位置: X=45, Y=3                               │\n');
fprintf('  │    - 初始速度: 5 km/h                                  │\n');
fprintf('  │    - 仿真时间: 60秒                                    │\n');
fprintf('  └─────────────────────────────────────────────────────────┘\n');
fprintf('\n');

%% ==================== 步骤5：显示操作指引 ====================

if ~carsim_connected
    fprintf('[步骤5/6] 操作指引\n\n');
    fprintf('  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    fprintf('  请在CarSim中完成以下操作：\n');
    fprintf('  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    fprintf('\n');
    fprintf('  1. 导入数据集：\n');
    fprintf('     File > Import Dataset\n');
    fprintf('     选择: %s\\Parking_Reversing.cpar\n', pwd);
    fprintf('     点击 OK 确认导入\n');
    fprintf('\n');
    fprintf('  2. 导出S-Function：\n');
    fprintf('     Settings > Simulink / MATLAB\n');
    fprintf('     点击 "Export S-Function"\n');
    fprintf('     保存到: %s\\\n', pwd);
    fprintf('\n');
    fprintf('  3. 确认仿真设置：\n');
    fprintf('     - 仿真时间 >= 60秒\n');
    fprintf('     - Simulink接口已启用\n');
    fprintf('\n');
    fprintf('  完成上述操作后，重新运行此脚本或直接运行:\n');
    fprintf('     run_parking_simulation\n');
    fprintf('\n');
else
    fprintf('[步骤5/6] CarSim已连接，准备就绪\n\n');
end

%% ==================== 步骤6：询问是否运行仿真 ====================

fprintf('[步骤6/6] 准备运行仿真\n\n');

if carsim_connected
    answer = input('CarSim已连接，是否立即运行联合仿真？(y/n): ', 's');
    if strcmpi(answer, 'y') || strcmpi(answer, 'yes')
        fprintf('\n正在启动联合仿真...\n\n');
        try
            run_parking_simulation;
            fprintf('\n✓ 联合仿真完成！\n');
        catch ME
            fprintf('\n✗ 仿真运行失败: %s\n', ME.message);
            fprintf('详细错误:\n');
            disp(ME);
        end
    else
        fprintf('\n已取消。手动运行: run_parking_simulation\n');
    end
else
    fprintf('请先在CarSim中完成配置，然后运行:\n');
    fprintf('  run_parking_simulation\n\n');
    fprintf('或重新运行此脚本:\n');
    fprintf('  start_cosimulation\n\n');
end

fprintf('============================================================\n');
fprintf('  启动脚本执行完成\n');
fprintf('============================================================\n');
