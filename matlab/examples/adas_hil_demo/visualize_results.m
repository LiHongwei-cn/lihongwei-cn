%% visualize_results.m — ADAS Simulation Visualization (R2016b compatible)
%  Uses subplot (NOT tiledlayout). No string types.
%
%  Inputs:
%    t, veh_pos, veh_vel, veh_acc, lat_pos,
%    radar_range, camera_lane, fcw_flag, aeb_flag, ldw_flag,
%    throttle_cmd, brake_cmd, obs_dist

function visualize_results(t, veh_pos, veh_vel, veh_acc, lat_pos, ...
    radar_range, camera_lane, fcw_flag, aeb_flag, ldw_flag, ...
    throttle_cmd, brake_cmd, obs_dist)

    %% ========== Figure 1: Vehicle Trajectory ==========
    figure('Name', 'ADAS HIL — Trajectory', 'NumberTitle', 'off');

    subplot(2, 1, 1);
    plot(t, veh_pos, 'b-', 'LineWidth', 1.5); hold on;
    plot(t, obs_dist * ones(size(t)), 'r--', 'LineWidth', 1.0);
    xlabel('Time [s]');
    ylabel('Position [m]');
    title('Longitudinal Trajectory');
    legend('Vehicle', 'Obstacle', 'Location', 'northwest');
    grid on;

    subplot(2, 1, 2);
    plot(t, lat_pos, 'b-', 'LineWidth', 1.5); hold on;
    plot(t, 0.3 * ones(size(t)), 'r--', 'LineWidth', 1.0);
    plot(t, -0.3 * ones(size(t)), 'r--', 'LineWidth', 1.0);
    xlabel('Time [s]');
    ylabel('Lateral Offset [m]');
    title('Lateral Position');
    legend('Offset', 'LDW Threshold', 'Location', 'northwest');
    grid on;

    %% ========== Figure 2: Speed Profile ==========
    figure('Name', 'ADAS HIL — Speed', 'NumberTitle', 'off');

    subplot(2, 1, 1);
    plot(t, veh_vel * 3.6, 'b-', 'LineWidth', 1.5);
    xlabel('Time [s]');
    ylabel('Speed [km/h]');
    title('Vehicle Speed');
    grid on;

    subplot(2, 1, 2);
    plot(t, veh_acc, 'b-', 'LineWidth', 1.5);
    xlabel('Time [s]');
    ylabel('Acceleration [m/s^2]');
    title('Vehicle Acceleration');
    grid on;

    %% ========== Figure 3: Sensor Data ==========
    figure('Name', 'ADAS HIL — Sensors', 'NumberTitle', 'off');

    subplot(2, 1, 1);
    plot(t, radar_range, 'b-', 'LineWidth', 1.0);
    xlabel('Time [s]');
    ylabel('Range [m]');
    title('Radar Range Measurement');
    grid on;

    subplot(2, 1, 2);
    plot(t, camera_lane, 'b-', 'LineWidth', 1.0);
    xlabel('Time [s]');
    ylabel('Lane Offset [m]');
    title('Camera Lane Offset');
    grid on;

    %% ========== Figure 4: Controller Outputs ==========
    figure('Name', 'ADAS HIL — Controller', 'NumberTitle', 'off');

    subplot(3, 1, 1);
    plot(t, throttle_cmd, 'g-', 'LineWidth', 1.0);
    xlabel('Time [s]');
    ylabel('Throttle [0-1]');
    title('Throttle Command');
    ylim([-0.1, 1.1]);
    grid on;

    subplot(3, 1, 2);
    plot(t, brake_cmd, 'r-', 'LineWidth', 1.0);
    xlabel('Time [s]');
    ylabel('Brake [0-1]');
    title('Brake Command');
    ylim([-0.1, 1.1]);
    grid on;

    subplot(3, 1, 3);
    hold on;
    plot(t, double(fcw_flag), 'y-', 'LineWidth', 1.5);
    plot(t, double(aeb_flag), 'r-', 'LineWidth', 1.5);
    plot(t, double(ldw_flag), 'm-', 'LineWidth', 1.5);
    xlabel('Time [s]');
    ylabel('Warning State');
    title('ADAS Warning Flags');
    legend('FCW', 'AEB', 'LDW', 'Location', 'east');
    ylim([-0.1, 1.3]);
    grid on;

end
