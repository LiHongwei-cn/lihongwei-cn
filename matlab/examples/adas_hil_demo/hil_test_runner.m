% HIL Test Runner
%
% Runs 5 test cases on simulation results, outputs pass/fail
%
% Compatible: MATLAB R2016b

function results = hil_test_runner(t, veh_vel, veh_pos, lat_pos, ...
    fcw_flag, aeb_flag, ldw_flag, radar_rng)

    N = length(t);
    results = struct('name', {}, 'passed', {}, 'detail', {});

    %% Test 1: Normal driving - no warnings in first 0.5s
    dt = t(2) - t(1);
    idx_0_5s = round(0.5 / dt);
    tc1_fcw = any(fcw_flag(1:idx_0_5s));
    tc1_aeb = any(aeb_flag(1:idx_0_5s));
    tc1_pass = ~tc1_fcw && ~tc1_aeb;
    results(1).name   = 'Normal driving (no warn <0.5s)';
    results(1).passed = tc1_pass;
    results(1).detail = sprintf('FCW=%d AEB=%d (expect 0, 0)', tc1_fcw, tc1_aeb);

    %% Test 2: Obstacle approach - FCW should trigger
    tc2_pass = any(fcw_flag);
    results(2).name   = 'Obstacle approach triggers FCW';
    results(2).passed = tc2_pass;
    results(2).detail = sprintf('FCW triggered=%d', tc2_pass);

    %% Test 3: Very close - AEB should trigger
    tc3_pass = any(aeb_flag);
    results(3).name   = 'Close range triggers AEB';
    results(3).passed = tc3_pass;
    results(3).detail = sprintf('AEB triggered=%d', tc3_pass);

    %% Test 4: Lane drift - LDW should trigger
    tc4_pass = any(ldw_flag);
    results(4).name   = 'Lane drift triggers LDW';
    results(4).passed = tc4_pass;
    results(4).detail = sprintf('LDW triggered=%d, max drift=%.3f m', ...
                        tc4_pass, max(abs(lat_pos)));

    %% Test 5: Sensor failure - graceful degradation
    tc5_pass = ~any(isnan(veh_vel));
    results(5).name   = 'Sensor failure graceful degradation';
    results(5).passed = tc5_pass;
    results(5).detail = sprintf('NaN in velocity=%d (expect 0)', any(isnan(veh_vel)));

end
