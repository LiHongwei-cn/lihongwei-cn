% ADAS 仿真结果可视化
%
% 功能：生成四张图表展示仿真结果
%   图1：车辆轨迹（纵向上方 + 横向下方）
%   图2：速度曲线（速度上方 + 加速度下方）
%   图3：传感器数据（雷达距离上方 + 摄像头车道偏移下方）
%   图4：控制器输出（油门 + 制动 + 预警标志）
%
% 使用 subplot 实现，不使用 tiledlayout（兼容 R2016b）
% 所有标签和图例使用中文
%
% 兼容版本：MATLAB R2016b

function visualize_results(t, veh_pos, veh_vel, veh_acc, lat_pos, ...
    radar_range, camera_lane, fcw_flag, aeb_flag, ldw_flag, ...
    throttle_cmd, brake_cmd, obs_dist)

    %% 图1：车辆轨迹
    figure('Name', 'ADAS HIL - 车辆轨迹', 'NumberTitle', 'off');

    % 上图：纵向位置
    subplot(2, 1, 1);
    plot(t, veh_pos, 'b-', 'LineWidth', 1.5);
    hold on;
    plot(t, obs_dist * ones(size(t)), 'r--', 'LineWidth', 1.0);
    xlabel('时间 [s]');
    ylabel('纵向位置 [m]');
    title('纵向轨迹');
    legend('车辆位置', '障碍物位置', 'Location', 'northwest');
    grid on;

    % 下图：横向偏移
    subplot(2, 1, 2);
    plot(t, lat_pos, 'b-', 'LineWidth', 1.5);
    hold on;
    plot(t, 0.3 * ones(size(t)), 'r--', 'LineWidth', 1.0);
    plot(t, -0.3 * ones(size(t)), 'r--', 'LineWidth', 1.0);
    xlabel('时间 [s]');
    ylabel('横向偏移 [m]');
    title('横向位置');
    legend('偏移量', 'LDW 阈值', 'Location', 'northwest');
    grid on;

    %% 图2：速度曲线
    figure('Name', 'ADAS HIL - 速度曲线', 'NumberTitle', 'off');

    % 上图：车速
    subplot(2, 1, 1);
    plot(t, veh_vel * 3.6, 'b-', 'LineWidth', 1.5);
    xlabel('时间 [s]');
    ylabel('车速 [km/h]');
    title('车速变化');
    grid on;

    % 下图：加速度
    subplot(2, 1, 2);
    plot(t, veh_acc, 'b-', 'LineWidth', 1.5);
    xlabel('时间 [s]');
    ylabel('加速度 [m/s^2]');
    title('加速度变化');
    grid on;

    %% 图3：传感器数据
    figure('Name', 'ADAS HIL - 传感器数据', 'NumberTitle', 'off');

    % 上图：雷达测距
    subplot(2, 1, 1);
    plot(t, radar_range, 'b-', 'LineWidth', 1.0);
    xlabel('时间 [s]');
    ylabel('距离 [m]');
    title('雷达测距');
    grid on;

    % 下图：摄像头车道偏移
    subplot(2, 1, 2);
    plot(t, camera_lane, 'b-', 'LineWidth', 1.0);
    xlabel('时间 [s]');
    ylabel('车道偏移 [m]');
    title('摄像头车道偏移');
    grid on;

    %% 图4：控制器输出
    figure('Name', 'ADAS HIL - 控制器输出', 'NumberTitle', 'off');

    % 上图：油门指令
    subplot(3, 1, 1);
    plot(t, throttle_cmd, 'g-', 'LineWidth', 1.0);
    xlabel('时间 [s]');
    ylabel('油门 [0-1]');
    title('油门指令');
    ylim([-0.1, 1.1]);
    grid on;

    % 中图：制动指令
    subplot(3, 1, 2);
    plot(t, brake_cmd, 'r-', 'LineWidth', 1.0);
    xlabel('时间 [s]');
    ylabel('制动 [0-1]');
    title('制动指令');
    ylim([-0.1, 1.1]);
    grid on;

    % 下图：预警标志
    subplot(3, 1, 3);
    hold on;
    plot(t, double(fcw_flag), 'y-', 'LineWidth', 1.5);
    plot(t, double(aeb_flag), 'r-', 'LineWidth', 1.5);
    plot(t, double(ldw_flag), 'm-', 'LineWidth', 1.5);
    xlabel('时间 [s]');
    ylabel('预警状态');
    title('ADAS 预警标志');
    legend('FCW 前碰撞预警', 'AEB 自动紧急制动', 'LDW 车道偏离预警', ...
           'Location', 'east');
    ylim([-0.1, 1.3]);
    grid on;

end
