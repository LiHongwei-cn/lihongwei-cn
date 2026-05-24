%% 仿真结果可视化脚本
% MATLAB R2016b 兼容
% 可视化高架桥仿真结果

function visualize_results(params, results)
    % visualize_results 可视化仿真结果
    %
    % 输入参数：
    %   params  - 仿真参数
    %   results - 分析结果

    fprintf('生成可视化结果...\n');

    %% 创建图形窗口
    figure('Position', [100, 100, 1200, 800], 'Name', '高架桥仿真结果');

    %% 子图1：车辆轨迹（俯视图）
    subplot(2, 3, 1);
    plot_vehicle_trajectory(params, results);
    title('车辆轨迹（俯视图）');
    xlabel('X 位置 [m]');
    ylabel('Y 位置 [m]');
    legend('前驱车', '四驱车', 'Location', 'best');
    grid on;

    %% 子图2：高度变化（侧视图）
    subplot(2, 3, 2);
    plot_height_profile(params, results);
    title('高度变化（侧视图）');
    xlabel('X 位置 [m]');
    ylabel('Z 高度 [m]');
    legend('前驱车', '四驱车', 'Location', 'best');
    grid on;

    %% 子图3：速度变化
    subplot(2, 3, 3);
    plot_velocity_profile(params, results);
    title('速度变化');
    xlabel('时间 [s]');
    ylabel('纵向速度 [m/s]');
    legend('前驱车', '四驱车', 'Location', 'best');
    grid on;

    %% 子图4：轮滑移率
    subplot(2, 3, 4);
    plot_wheel_slip(params, results);
    title('车轮滑移率');
    xlabel('时间 [s]');
    ylabel('滑移率');
    legend('前驱-前轮', '前驱-后轮', '四驱-前轮', '四驱-后轮', 'Location', 'best');
    grid on;

    %% 子图5：爬坡能力对比
    subplot(2, 3, 5);
    plot_climbing_comparison(params, results);
    title('爬坡能力对比');
    ylabel('距离/高度');
    grid on;

    %% 子图6：动画预览
    subplot(2, 3, 6);
    plot_animation_preview(params, results);
    title('动画预览');
    xlabel('X 位置 [m]');
    ylabel('Z 高度 [m]');
    grid on;

    %% 保存图形
    output_file = fullfile(params.output_dir, 'simulation_results.png');
    saveas(gcf, output_file, 'png');
    fprintf('可视化结果已保存: %s\n', output_file);
end

function plot_vehicle_trajectory(params, results)
    % plot_vehicle_trajectory 绘制车辆轨迹

    hold on;

    % 绘制高架桥轮廓
    bridge_x = [0, params.bridge_length, params.bridge_length, 0, 0];
    bridge_y = [-params.bridge_width/2, -params.bridge_width/2, ...
                params.bridge_width/2, params.bridge_width/2, ...
                -params.bridge_width/2];
    fill(bridge_x, bridge_y, [0.8, 0.8, 0.8], 'EdgeColor', 'k', 'FaceAlpha', 0.3);

    % 绘制护栏
    plot([0, params.bridge_length], [params.bridge_width/2, params.bridge_width/2], ...
        'k-', 'LineWidth', 2);
    plot([0, params.bridge_length], [-params.bridge_width/2, -params.bridge_width/2], ...
        'k-', 'LineWidth', 2);

    % 绘制前驱车轨迹
    if ~isempty(results.fwd)
        plot(results.fwd.x, zeros(size(results.fwd.x)), 'b-', 'LineWidth', 2);
    end

    % 绘制四驱车轨迹
    if ~isempty(results.awd)
        plot(results.awd.x, zeros(size(results.awd.x)), 'r-', 'LineWidth', 2);
    end

    hold off;
end

function plot_height_profile(params, results)
    % plot_height_profile 绘制高度剖面

    hold on;

    % 绘制高架桥剖面
    bridge_x = [0, params.bridge_length];
    bridge_z = [0, params.bridge_length * tan(params.slope_angle * pi / 180)];
    plot(bridge_x, bridge_z, 'k--', 'LineWidth', 1);

    % 绘制前驱车高度
    if ~isempty(results.fwd)
        plot(results.fwd.x, results.fwd.z, 'b-', 'LineWidth', 2);
    end

    % 绘制四驱车高度
    if ~isempty(results.awd)
        plot(results.awd.x, results.awd.z, 'r-', 'LineWidth', 2);
    end

    hold off;
end

function plot_velocity_profile(params, results)
    % plot_velocity_profile 绘制速度剖面

    hold on;

    % 绘制前驱车速度
    if ~isempty(results.fwd)
        plot(results.fwd.time, results.fwd.vx, 'b-', 'LineWidth', 2);
    end

    % 绘制四驱车速度
    if ~isempty(results.awd)
        plot(results.awd.time, results.awd.vx, 'r-', 'LineWidth', 2);
    end

    hold off;
end

function plot_wheel_slip(params, results)
    % plot_wheel_slip 绘制车轮滑移率

    hold on;

    % 绘制前驱车滑移率
    if ~isempty(results.fwd)
        % 前轮平均滑移率
        fwd_front_slip = mean(results.fwd.wheel_slip(:, 1:2), 2);
        % 后轮平均滑移率
        fwd_rear_slip = mean(results.fwd.wheel_slip(:, 3:4), 2);

        plot(results.fwd.time, fwd_front_slip, 'b-', 'LineWidth', 1.5);
        plot(results.fwd.time, fwd_rear_slip, 'b--', 'LineWidth', 1.5);
    end

    % 绘制四驱车滑移率
    if ~isempty(results.awd)
        % 前轮平均滑移率
        awd_front_slip = mean(results.awd.wheel_slip(:, 1:2), 2);
        % 后轮平均滑移率
        awd_rear_slip = mean(results.awd.wheel_slip(:, 3:4), 2);

        plot(results.awd.time, awd_front_slip, 'r-', 'LineWidth', 1.5);
        plot(results.awd.time, awd_rear_slip, 'r--', 'LineWidth', 1.5);
    end

    hold off;
end

function plot_climbing_comparison(params, results)
    % plot_climbing_comparison 绘制爬坡能力对比

    if isempty(results.fwd) || isempty(results.awd)
        text(0.5, 0.5, '无数据', 'HorizontalAlignment', 'center');
        return;
    end

    % 准备数据
    categories = {'最大距离', '最大高度', '平均滑移率'};
    fwd_values = [results.fwd.max_distance, results.fwd.max_height, results.fwd.avg_slip * 100];
    awd_values = [results.awd.max_distance, results.awd.max_height, results.awd.avg_slip * 100];

    % 归一化
    max_vals = max([fwd_values; awd_values]);
    fwd_norm = fwd_values ./ max_vals;
    awd_norm = awd_values ./ max_vals;

    % 绘制柱状图
    x = 1:length(categories);
    width = 0.35;

    bar(x - width/2, fwd_norm, width, 'b', 'FaceAlpha', 0.7);
    hold on;
    bar(x + width/2, awd_norm, width, 'r', 'FaceAlpha', 0.7);
    hold off;

    set(gca, 'XTick', x);
    set(gca, 'XTickLabel', categories);
    legend('前驱车', '四驱车', 'Location', 'best');
end

function plot_animation_preview(params, results)
    % plot_animation_preview 绘制动画预览

    hold on;

    % 绘制高架桥
    bridge_x = [0, params.bridge_length];
    bridge_z = [0, params.bridge_length * tan(params.slope_angle * pi / 180)];
    fill([bridge_x, fliplr(bridge_x)], [bridge_z, fliplr(bridge_z) * 0], ...
        [0.8, 0.8, 0.8], 'EdgeColor', 'k', 'FaceAlpha', 0.3);

    % 绘制护栏
    plot(bridge_x, bridge_z + 0.8, 'k-', 'LineWidth', 2);

    % 绘制车辆位置（前驱车 - 蓝色）
    if ~isempty(results.fwd)
        % 取中间时刻的位置
        idx = round(length(results.fwd.time) / 2);
        fwd_x = results.fwd.x(idx);
        fwd_z = results.fwd.z(idx);

        % 绘制车辆（简化为矩形）
        vehicle_length = 4.5;
        vehicle_height = 1.5;
        rectangle('Position', [fwd_x - vehicle_length/2, fwd_z, vehicle_length, vehicle_height], ...
            'FaceColor', 'b', 'EdgeColor', 'k');
    end

    % 绘制车辆位置（四驱车 - 红色）
    if ~isempty(results.awd)
        % 取中间时刻的位置
        idx = round(length(results.awd.time) / 2);
        awd_x = results.awd.x(idx);
        awd_z = results.awd.z(idx);

        % 绘制车辆（简化为矩形）
        rectangle('Position', [awd_x - vehicle_length/2, awd_z, vehicle_length, vehicle_height], ...
            'FaceColor', 'r', 'EdgeColor', 'k');
    end

    hold off;
end

function result = conditional(condition, true_val, false_val)
    % conditional 条件选择函数
    if condition
        result = true_val;
    else
        result = false_val;
    end
end
