%% AUTO_RUN_ALL - CarSim + Simulink 联合仿真全自动化脚本
% 基于B站教程: BV1xk4y1b7y8
% 功能：一键完成配置生成、导入、仿真运行
%
% 作者：LiHongwei
% 日期：2026-05-29

clear; clc; close all;

fprintf('============================================================\n');
fprintf('  CarSim + Simulink 联合仿真 - 全自动化运行\n');
fprintf('  基于B站教程: BV1xk4y1b7y8\n');
fprintf('============================================================\n\n');

%% ==================== 步骤1：切换到脚本目录 ====================

fprintf('[步骤1/7] 切换到工作目录...\n');

script_dir = fileparts(mfilename('fullpath'));
if ~isempty(script_dir)
    cd(script_dir);
end
fprintf('   工作目录: %s\n', pwd);
fprintf('   ✓ 完成\n\n');

%% ==================== 步骤2：生成配置文件 ====================

fprintf('[步骤2/7] 生成CarSim配置文件...\n');

try
    % 运行配置生成脚本
    carsim_ap_auto_import;
    fprintf('   ✓ 配置文件生成成功\n\n');
catch ME
    fprintf('   ✗ 配置文件生成失败: %s\n', ME.message);
    fprintf('   尝试使用备用方法...\n');
    try
        carsim_generate_cpar;
        fprintf('   ✓ 备用配置文件生成成功\n\n');
    catch ME2
        fprintf('   ✗ 备用方法也失败: %s\n', ME2.message);
    end
end

%% ==================== 步骤3：检查生成的文件 ====================

fprintf('[步骤3/7] 检查生成的文件...\n');

files_to_check = {
    'Parking_Reversing.cpar',
    'import_to_carsim_auto.m',
    'run_parking_simulation.m'
};

all_files_exist = true;
for i = 1:length(files_to_check)
    if exist(files_to_check{i}, 'file')
        fprintf('   ✓ %s\n', files_to_check{i});
    else
        fprintf('   ✗ %s (未找到)\n', files_to_check{i});
        all_files_exist = false;
    end
end

if ~all_files_exist
    fprintf('\n   警告：部分文件缺失，可能影响后续步骤\n');
end
fprintf('\n');

%% ==================== 步骤4：尝试连接CarSim ====================

fprintf('[步骤4/7] 尝试连接CarSim...\n');

carsim_connected = false;
try
    % 尝试通过COM接口连接CarSim
    h = actxserver('CarSim.Application');
    fprintf('   ✓ 成功连接CarSim\n');
    carsim_connected = true;

    % 尝试导入CPAR文件
    fprintf('   正在导入配置文件...\n');
    cpar_file = fullfile(pwd, 'Parking_Reversing.cpar');
    if exist(cpar_file, 'file')
        h.ImportDataset(cpar_file);
        fprintf('   ✓ 配置文件导入成功\n');
    else
        fprintf('   ✗ CPAR文件不存在\n');
    end

    % 释放COM对象
    h.release;
catch ME
    fprintf('   ✗ 无法连接CarSim: %s\n', ME.message);
    fprintf('   请手动导入配置文件\n');
end
fprintf('\n');

%% ==================== 步骤5：生成Simulink模型 ====================

fprintf('[步骤5/7] 生成Simulink模型...\n');

try
    create_parking_simulink_model;
    fprintf('   ✓ Simulink模型生成成功\n');
catch ME
    fprintf('   ✗ Simulink模型生成失败: %s\n', ME.message);
    fprintf('   将在运行时自动生成\n');
end
fprintf('\n');

%% ==================== 步骤6：显示状态总结 ====================

fprintf('[步骤6/7] 状态总结...\n\n');

fprintf('┌─────────────────────────────────────────────────────────────┐\n');
fprintf('│  配置状态                                                  │\n');
fprintf('├─────────────────────────────────────────────────────────────┤\n');

if exist('Parking_Reversing.cpar', 'file')
    fprintf('│  ✓ CPAR配置文件: 已生成                                   │\n');
else
    fprintf('│  ✗ CPAR配置文件: 未生成                                   │\n');
end

if exist('parking_reverse_control.slx', 'file')
    fprintf('│  ✓ Simulink模型: 已生成                                   │\n');
else
    fprintf('│  ○ Simulink模型: 待生成                                   │\n');
end

if carsim_connected
    fprintf('│  ✓ CarSim连接: 已连接                                     │\n');
else
    fprintf('│  ○ CarSim连接: 未连接（需要手动导入）                     │\n');
end

fprintf('│                                                             │\n');
fprintf('│  场景参数:                                                  │\n');
fprintf('│    - 道路: 50m × 6m                                        │\n');
fprintf('│    - 车位: 10个 (5m × 2.5m)                               │\n');
fprintf('│    - 目标: 第5个车位 (空置)                               │\n');
fprintf('│    - 初始位置: (45, 3)                                     │\n');
fprintf('└─────────────────────────────────────────────────────────────┘\n\n');

%% ==================== 步骤7：提供下一步操作指南 ====================

fprintf('[步骤7/7] 下一步操作指南\n\n');

if carsim_connected
    fprintf('✓ CarSim已连接并导入配置，可以直接运行仿真：\n\n');
    fprintf('  方法A: 在CarSim中点击 Run → Run Simulation\n\n');
    fprintf('  方法B: 在MATLAB中运行:\n');
    fprintf('         >> run_parking_simulation\n\n');
else
    fprintf('请手动完成以下步骤：\n\n');
    fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    fprintf('  步骤A: 在CarSim中导入配置\n');
    fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    fprintf('  1. 打开 CarSim 2019.0\n');
    fprintf('  2. File → Import Dataset\n');
    fprintf('  3. 选择: %s\\Parking_Reversing.cpar\n', pwd);
    fprintf('  4. 点击 OK 确认导入\n\n');

    fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    fprintf('  步骤B: 导出S-Function\n');
    fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    fprintf('  1. 在CarSim中: Settings → Simulink\n');
    fprintf('  2. 点击 Export S-Function\n');
    fprintf('  3. 保存到: %s\\\n', pwd);
    fprintf('  4. 文件名: sf_car_sim.mexw64\n\n');

    fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    fprintf('  步骤C: 运行联合仿真\n');
    fprintf('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
    fprintf('  1. 确保CarSim已打开并导入配置\n');
    fprintf('  2. 在MATLAB中运行:\n');
    fprintf('     >> run_parking_simulation\n\n');
end

fprintf('============================================================\n');
fprintf('  自动化脚本执行完成！\n');
fprintf('============================================================\n\n');

%% ==================== 询问是否立即运行仿真 ====================

if carsim_connected
    % 如果CarSim已连接，询问是否立即运行
    answer = input('是否立即运行仿真？(y/n): ', 's');
    if strcmpi(answer, 'y') || strcmpi(answer, 'yes')
        fprintf('\n正在运行仿真...\n');
        try
            run_parking_simulation;
            fprintf('\n✓ 仿真完成！\n');
        catch ME
            fprintf('\n✗ 仿真运行失败: %s\n', ME.message);
        end
    end
else
    fprintf('提示: 完成上述步骤后，运行 run_parking_simulation 开始仿真\n\n');
end
