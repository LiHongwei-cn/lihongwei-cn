function visualize_results(t, veh_pos, veh_vel, veh_acc, lat_pos, ...
    radar_range, camera_lane, fcw_flag, aeb_flag, ldw_flag, ...
    throttle_cmd, brake_cmd, obs_dist)

    figure('Name', 'ADAS HIL Results', 'NumberTitle', 'off', ...
           'Units', 'normalized', 'Position', [0.05 0.05 0.9 0.85]);

    subplot(4, 2, 1);
    plot(t, veh_pos, 'b-', 'LineWidth', 1.2); hold on;
    plot(t, obs_dist * ones(size(t)), 'r--', 'LineWidth', 1.0);
    xlabel('Time [s]'); ylabel('Position [m]');
    title('Longitudinal Trajectory');
    legend('Vehicle', 'Obstacle', 'Location', 'northwest');
    grid on;

    subplot(4, 2, 2);
    plot(t, lat_pos, 'b-', 'LineWidth', 1.2); hold on;
    plot(t, 0.3 * ones(size(t)), 'r--', 'LineWidth', 1.0);
    plot(t, -0.3 * ones(size(t)), 'r--', 'LineWidth', 1.0);
    xlabel('Time [s]'); ylabel('Offset [m]');
    title('Lateral Position');
    legend('Offset', 'LDW Threshold', 'Location', 'northwest');
    grid on;

    subplot(4, 2, 3);
    plot(t, veh_vel * 3.6, 'b-', 'LineWidth', 1.2);
    xlabel('Time [s]'); ylabel('Speed [km/h]');
    title('Vehicle Speed');
    grid on;

    subplot(4, 2, 4);
    plot(t, veh_acc, 'b-', 'LineWidth', 1.2);
    xlabel('Time [s]'); ylabel('Accel [m/s^2]');
    title('Vehicle Acceleration');
    grid on;

    subplot(4, 2, 5);
    plot(t, radar_range, 'b-', 'LineWidth', 1.0);
    xlabel('Time [s]'); ylabel('Range [m]');
    title('Radar Range');
    grid on;

    subplot(4, 2, 6);
    plot(t, camera_lane, 'b-', 'LineWidth', 1.0);
    xlabel('Time [s]'); ylabel('Offset [m]');
    title('Camera Lane Offset');
    grid on;

    subplot(4, 2, 7);
    plot(t, throttle_cmd, 'g-', 'LineWidth', 1.0); hold on;
    plot(t, brake_cmd, 'r-', 'LineWidth', 1.0);
    xlabel('Time [s]'); ylabel('Command [0-1]');
    title('Throttle & Brake');
    legend('Throttle', 'Brake', 'Location', 'east');
    ylim([-0.1, 1.1]);
    grid on;

    subplot(4, 2, 8);
    hold on;
    plot(t, double(fcw_flag), 'Color', [0.9 0.7 0], 'LineWidth', 1.5);
    plot(t, double(aeb_flag), 'r-', 'LineWidth', 1.5);
    plot(t, double(ldw_flag), 'm-', 'LineWidth', 1.5);
    xlabel('Time [s]'); ylabel('State');
    title('ADAS Warnings');
    legend('FCW', 'AEB', 'LDW', 'Location', 'east');
    ylim([-0.1, 1.3]);
    grid on;

end
