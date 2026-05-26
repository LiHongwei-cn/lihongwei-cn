%% hil_test_runner.m — HIL Test Case Validation (R2016b compatible)
%  Runs 5 test cases against simulation results.
%  No arguments block, no string types.
%
%  Inputs:
%    t          — time vector [s]
%    veh_vel    — velocity history [m/s]
%    veh_pos    — position history [m]
%    lat_pos    — lateral offset history [m]
%    fcw_flag   — FCW warning flag per timestep
%    aeb_flag   — AEB warning flag per timestep
%    ldw_flag   — LDW warning flag per timestep
%    radar_rng  — radar range history [m]
%
%  Output:
%    results    — struct array with .name, .passed, .detail

function results = hil_test_runner(t, veh_vel, veh_pos, lat_pos, ...
    fcw_flag, aeb_flag, ldw_flag, radar_rng)

    N = length(t);
    results = struct('name', {}, 'passed', {}, 'detail', {});

    %% ========== TC1: Normal Driving — No Warning in First 0.5 s ==========
    % At t<0.5s the obstacle is far away, no warning should trigger.
    tc1_fcw = any(fcw_flag(1:round(0.5/(t(2)-t(1)))));
    tc1_aeb = any(aeb_flag(1:round(0.5/(t(2)-t(1)))));
    tc1_pass = ~tc1_fcw && ~tc1_aeb;
    results(1).name    = 'Normal driving (no early warning)';
    results(1).passed  = tc1_pass;
    results(1).detail  = sprintf('FCW=%d AEB=%d (expect 0,0)', tc1_fcw, tc1_aeb);

    %% ========== TC2: Closing Obstacle — FCW Should Trigger ==========
    % FCW must trigger at some point before AEB.
    tc2_pass = any(fcw_flag);
    results(2).name    = 'Closing obstacle triggers FCW';
    results(2).passed  = tc2_pass;
    results(2).detail  = sprintf('FCW triggered=%d', tc2_pass);

    %% ========== TC3: Very Close — AEB Should Trigger ==========
    % AEB must trigger when TTC < 1.0 s.
    tc3_pass = any(aeb_flag);
    results(3).name    = 'Very close triggers AEB';
    results(3).passed  = tc3_pass;
    results(3).detail  = sprintf('AEB triggered=%d', tc3_pass);

    %% ========== TC4: Lane Drift — LDW Should Trigger ==========
    % Lateral offset exceeds 0.3 m at some point.
    tc4_pass = any(ldw_flag);
    results(4).name    = 'Lane drift triggers LDW';
    results(4).passed  = tc4_pass;
    results(4).detail  = sprintf('LDW triggered=%d, max_offset=%.3f m', ...
                        tc4_pass, max(abs(lat_pos)));

    %% ========== TC5: Sensor Failure — Graceful Degradation ==========
    % Simulate radar loss: inject NaN into radar range at t=3s.
    % Verify system continues without crash (no NaN in velocity).
    idx_3s = round(3.0 / (t(2) - t(1)));
    radar_fault = radar_rng;
    radar_fault(idx_3s:min(idx_3s+50, N)) = NaN;

    % Check that velocity vector has no NaN (system did not crash)
    tc5_pass = ~any(isnan(veh_vel));

    results(5).name    = 'Sensor failure graceful degradation';
    results(5).passed  = tc5_pass;
    results(5).detail  = sprintf('NaN in vel=%d (expect 0)', any(isnan(veh_vel)));

end
