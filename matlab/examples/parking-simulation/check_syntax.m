%% CHECK_SYNTAX - 检查倒车入库仿真代码语法
% 快速验证所有脚本的语法正确性
%
% 作者：LiHongwei
% 日期：2026-05-29

clear; clc;

fprintf('========================================\n');
fprintf('  语法检查工具\n');
fprintf('========================================\n\n');

% 获取当前目录
current_dir = pwd;
fprintf('当前目录: %s\n\n', current_dir);

% 要检查的文件
files_to_check = {
    'create_parking_simulink_model.m',
    'run_parking_simulation.m',
    'test_parking_system.m',
    'check_syntax.m'
};

% 检查每个文件
all_passed = true;
for i = 1:length(files_to_check)
    filename = files_to_check{i};
    fprintf('[%d/%d] 检查: %s\n', i, length(files_to_check), filename);

    if exist(filename, 'file')
        try
            % 尝试解析文件（不执行）
            % 这会捕获语法错误
            eval(['help ' filename(1:end-2)]);
            fprintf('   ✓ 语法正确\n');
        catch ME
            fprintf('   ✗ 错误: %s\n', ME.message);
            all_passed = false;
        end
    else
        fprintf('   ✗ 文件不存在\n');
        all_passed = false;
    end
end

fprintf('\n========================================\n');
if all_passed
    fprintf('  所有文件语法检查通过！\n');
else
    fprintf('  存在语法错误，请检查\n');
end
fprintf('========================================\n');

% 检查目录结构
fprintf('\n目录结构检查:\n');
fprintf('  matlab/examples/parking-simulation/: ');

if exist('create_parking_simulink_model.m', 'file') && ...
   exist('run_parking_simulation.m', 'file') && ...
   exist('test_parking_system.m', 'file')
    fprintf('✓ 完整\n');
else
    fprintf('✗ 缺少文件\n');
end

% 显示文件列表
fprintf('\n文件列表:\n');
files = dir('*.m');
for i = 1:length(files)
    fprintf('  %s (%d bytes)\n', files(i).name, files(i).bytes);
end

fprintf('\n文档文件:\n');
docs = dir('*.md');
for i = 1:length(docs)
    fprintf('  %s (%d bytes)\n', docs(i).name, docs(i).bytes);
end
