%% sensor_model.m — Multi-Sensor Fusion Model (R2016b compatible)
%  Simulates radar, camera, and ultrasonic sensors with Gaussian noise.
%  No arguments block, no string types.
%
%  Inputs:
%    true_range      — true range to obstacle [m]
%    true_range_rate — true closing speed [m/s]
%    true_lat_offset — true lateral offset [m]
%    cfg             — sensor configuration struct
%
%  Output:
%    sens            — struct with .radar, .camera, .ultrasonic fields

function sens = sensor_model(true_range, true_range_rate, true_lat_offset, cfg)

    %% ========== Radar Sensor ==========
    % Range measurement with Gaussian noise
    range_meas = true_range + cfg.radar_range_std * randn();

    % Range rate (closing speed) with noise
    rate_meas = true_range_rate + cfg.radar_rate_std * randn();

    % Azimuth angle (small for nearly head-on scenario)
    azimuth_meas = atan2(true_lat_offset, max(true_range, 0.1)) ...
                   + cfg.radar_azimuth_std * randn();

    % Validity: within max range and positive range
    radar_valid = (true_range > 0) && (true_range < cfg.radar_max_range);

    sens.radar.range   = range_meas;      % [m]
    sens.radar.rate    = rate_meas;        % [m/s]
    sens.radar.azimuth = azimuth_meas;     % [rad]
    sens.radar.valid   = radar_valid;

    %% ========== Camera Sensor ==========
    % Probabilistic detection
    camera_detected = rand() < cfg.camera_det_prob;

    % Lane offset measurement with noise
    lane_meas = true_lat_offset + cfg.camera_lane_std * randn();

    sens.camera.detected    = camera_detected;
    sens.camera.lane_offset = lane_meas;   % [m]
    sens.camera.valid       = camera_detected;

    %% ========== Ultrasonic Sensor ==========
    % Short-range only (parking / low speed)
    ultra_valid = (true_range > 0) && (true_range < cfg.ultrasonic_range);

    if ultra_valid
        ultra_range = true_range + 0.05 * randn();   % [m], low noise at close range
    else
        ultra_range = NaN;   % not available
    end

    sens.ultrasonic.range = ultra_range;   % [m]
    sens.ultrasonic.valid = ultra_valid;

end
