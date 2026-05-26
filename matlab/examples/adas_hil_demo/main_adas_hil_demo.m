%% main_adas_hil_demo.m — ADAS HIL Test Demo (R2016b compatible)
%  Runs a closed-loop simulation of FCW/AEB/LDW at 80 km/h.
%  Compatibility: R2016b — no rms(), no arguments block, no string types.

clear; clc; close all;

%% ========== Scenario Parameters ==========
v0_kmh    = 80;                  % initial vehicle speed [km/h]
v0        = v0_kmh / 3.6;       % initial vehicle speed [m/s]
x0        = 0;                   % initial vehicle position [m]
obs_dist  = 60;                  % obstacle distance from start [m]
obs_speed = 0;                   % obstacle speed (stationary) [m/s]
lat_offset0 = 0;                 % initial lateral offset [m]

%% ========== Sensor Configuration ==========
sensor_cfg.radar_max_range   = 150;   % [m]
sensor_cfg.radar_range_std   = 0.5;   % [m]
sensor_cfg.radar_rate_std    = 0.1;   % [m/s]
sensor_cfg.radar_azimuth_std = 0.02;  % [rad]
sensor_cfg.camera_det_prob   = 0.95;  % detection probability
sensor_cfg.camera_lane_std   = 0.05;  % [m]
sensor_cfg.ultrasonic_range  = 5;     % [m]

%% ========== Simulation Settings ==========
dt    = 0.01;    % time step [s]
t_end = 5;       % total simulation time [s]
t     = 0:dt:t_end;
N     = length(t);

%% ========== Preallocate Storage ==========
veh_pos       = zeros(1, N);   % longitudinal position [m]
veh_vel       = zeros(1, N);   % longitudinal velocity [m/s]
veh_acc       = zeros(1, N);   % longitudinal acceleration [m/s^2]
veh_lat_pos   = zeros(1, N);   % lateral offset [m]
throttle_cmd  = zeros(1, N);   % throttle command [0-1]
brake_cmd     = zeros(1, N);   % brake command [0-1]
fcw_flag      = false(1, N);   % forward collision warning
aeb_flag      = false(1, N);   % automatic emergency braking
ldw_flag      = false(1, N);   % lane departure warning
radar_range   = zeros(1, N);   % radar range measurement [m]
camera_lane   = zeros(1, N);   % camera lane offset [m]

%% ========== Initial Conditions ==========
veh_pos(1)     = x0;
veh_vel(1)     = v0;
veh_lat_pos(1) = lat_offset0;

%% ========== Main Simulation Loop ==========
for k = 1:N
    % --- Sensor Model ---
    obs_range     = obs_dist - veh_pos(k);              % true range [m]
    obs_range_rate = obs_speed - veh_vel(k);             % true range rate [m/s]
    sens = sensor_model(obs_range, obs_range_rate, veh_lat_pos(k), sensor_cfg);

    % --- ADAS Controller ---
    ctrl = adas_controller(sens, veh_vel(k), veh_lat_pos(k));

    % --- Vehicle Model ---
    [acc_new, vel_new, pos_new] = vehicle_model(...
        ctrl.throttle, ctrl.brake, veh_vel(k), veh_pos(k));

    % --- Lateral dynamics (simple drift model for LDW demo) ---
    if ctrl.ldw_warning
        lat_new = veh_lat_pos(k);   % hold if warning issued
    else
        % slow lateral drift toward +0.5 m over 5 s
        lat_new = veh_lat_pos(k) + 0.1 * dt;
    end

    % --- Store Results ---
    veh_acc(k)      = acc_new;
    if k < N
        veh_vel(k+1)     = vel_new;
        veh_pos(k+1)     = pos_new;
        veh_lat_pos(k+1) = lat_new;
    end
    throttle_cmd(k) = ctrl.throttle;
    brake_cmd(k)    = ctrl.brake;
    fcw_flag(k)     = ctrl.fcw_warning;
    aeb_flag(k)     = ctrl.aeb_warning;
    ldw_flag(k)     = ctrl.ldw_warning;
    radar_range(k)  = sens.radar.range;
    camera_lane(k)  = sens.camera.lane_offset;
end

%% ========== Test Validation ==========
test_results = hil_test_runner(t, veh_vel, veh_pos, veh_lat_pos, ...
    fcw_flag, aeb_flag, ldw_flag, radar_range);

%% ========== Generate Report ==========
fprintf('\n========================================\n');
fprintf('  ADAS HIL Test Report\n');
fprintf('  Date: %s\n', datestr(now));
fprintf('  Scenario: v0=%.0f km/h, obstacle at %.0f m\n', v0_kmh, obs_dist);
fprintf('========================================\n');
for i = 1:length(test_results)
    if test_results(i).passed
        status = 'PASS';
    else
        status = 'FAIL';
    end
    fprintf('  TC%d %-30s [%s]\n', i, test_results(i).name, status);
end
fprintf('========================================\n');
n_pass = sum([test_results.passed]);
fprintf('  Result: %d/%d passed\n', n_pass, length(test_results));
fprintf('========================================\n\n');

%% ========== Visualization ==========
visualize_results(t, veh_pos, veh_vel, veh_acc, veh_lat_pos, ...
    radar_range, camera_lane, fcw_flag, aeb_flag, ldw_flag, ...
    throttle_cmd, brake_cmd, obs_dist);
