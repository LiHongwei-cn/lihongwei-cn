function visualize_results(t, veh_pos, veh_vel, veh_acc, lat_pos, ...
    radar_range, camera_lane, fcw_flag, aeb_flag, ldw_flag, ...
    throttle_cmd, brake_cmd, obs_dist)

    figure('Name', 'ADAS HIL 仿真结果', 'NumberTitle', 'off', ...
           'Units', 'normalized', 'Position', [0.05 0.05 0.9 0.85]);

    subplot(4, 2, 1);
    plot(t, veh_pos, 'b-', 'LineWidth', 1.2); hold on;
    plot(t, obs_dist * ones(size(t)), 'r--', 'LineWidth', 1.0);
    xlabel('时间 [s]'); ylabel('位置 [m]');
    title('纵向轨迹');
    legend('车辆', '障碍物', 'Location', 'northwest');
    grid on;

    subplot(4, 2, 2);
    plot(t, lat_pos, 'b-', 'LineWidth', 1.2); hold on;
    plot(t, 0.3 * ones(size(t)), 'r--', 'LineWidth', 1.0);
    plot(t, -0.3 * ones(size(t)), 'r--', 'LineWidth', 1.0);
    xlabel('时间 [s]'); ylabel('横向偏移 [m]');
    title('横向位置');
    legend('偏移量', 'LDW阈值', 'Location', 'northwest');
    grid on;

    subplot(4, 2, 3);
    plot(t, veh_vel * 3.6, 'b-', 'LineWidth', 1.2);
    xlabel('时间 [s]'); ylabel('车速 [km/h]');
    title('车速曲线');
    grid on;

    subplot(4, 2, 4);
    plot(t, veh_acc, 'b-', 'LineWidth', 1.2);
    xlabel('时间 [s]'); ylabel('加速度 [m/s^2]');
    title('加速度');
    grid on;

    subplot(4, 2, 5);
    plot(t, radar_range, 'b-', 'LineWidth', 1.0);
    xlabel('时间 [s]'); ylabel('距离 [m]');
    title('雷达测距');
    grid on;

    subplot(4, 2, 6);
    plot(t, camera_lane, 'b-', 'LineWidth', 1.0);
    xlabel('时间 [s]'); ylabel('偏移 [m]');
    title('摄像头车道偏移');
    grid on;

    subplot(4, 2, 7);
    plot(t, throttle_cmd, 'g-', 'LineWidth', 1.0); hold on;
    plot(t, brake_cmd, 'r-', 'LineWidth', 1.0);
    xlabel('时间 [s]'); ylabel('指令 [0-1]');
    title('油门与制动');
    legend('油门', '制动', 'Location', 'east');
    ylim([-0.1, 1.1]);
    grid on;

    subplot(4, 2, 8);
    hold on;
    plot(t, double(fcw_flag), 'Color', [0.9 0.7 0], 'LineWidth', 1.5);
    plot(t, double(aeb_flag), 'r-', 'LineWidth', 1.5);
    plot(t, double(ldw_flag), 'm-', 'LineWidth', 1.5);
    xlabel('时间 [s]'); ylabel('状态');
    title('ADAS警告');
    legend('FCW', 'AEB', 'LDW', 'Location', 'east');
    ylim([-0.1, 1.3]);
    grid on;

end
