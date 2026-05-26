%% adas_controller.m — ADAS Decision Controller (R2016b compatible)
%  Implements FCW, AEB, and LDW logic.
%  No arguments block, no string types.
%
%  Inputs:
%    sens        — sensor data struct from sensor_model()
%    veh_speed   — current vehicle speed [m/s]
%    lat_offset  — current lateral offset [m]
%
%  Output:
%    ctrl        — struct with .fcw_warning, .aeb_warning, .ldw_warning,
%                  .throttle, .brake

function ctrl = adas_controller(sens, veh_speed, lat_offset)

    %% ========== Default Outputs ==========
    ctrl.fcw_warning = false;
    ctrl.aeb_warning = false;
    ctrl.ldw_warning = false;
    ctrl.throttle    = 0.5;     % default cruise throttle
    ctrl.brake       = 0;       % no braking

    %% ========== Time-to-Collision (TTC) Computation ==========
    % TTC = range / closing_speed  (only when closing)
    if sens.radar.valid && sens.radar.range > 0
        closing_speed = -sens.radar.rate;   % positive when approaching
        if closing_speed > 0.1
            ttc = sens.radar.range / closing_speed;   % [s]
        else
            ttc = Inf;   % not closing
        end
    else
        ttc = Inf;   % radar unavailable — no warning
    end

    %% ========== FCW Logic: TTC < 2.5 s ==========
    if ttc < 2.5
        ctrl.fcw_warning = true;
    end

    %% ========== AEB Logic: TTC < 1.0 s ==========
    if ttc < 1.0
        ctrl.aeb_warning = true;
        ctrl.brake       = 1.0;    % full braking
        ctrl.throttle    = 0;      % cut throttle
    end

    %% ========== LDW Logic: Lateral Offset > 0.3 m ==========
    if sens.camera.valid
        if abs(sens.camera.lane_offset) > 0.3
            ctrl.ldw_warning = true;
        end
    end

end
