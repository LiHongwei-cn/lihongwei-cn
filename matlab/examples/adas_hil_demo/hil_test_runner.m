% HIL 测试验证脚本
%
% 功能：对仿真结果执行 5 项测试，返回通过/失败结果
%
% 兼容版本：MATLAB R2016b

function results = hil_test_runner(t, veh_vel, veh_pos, lat_pos, ...
    fcw_flag, aeb_flag, ldw_flag, radar_rng)

    N = length(t);
    results = struct('name', {}, 'passed', {}, 'detail', {});

    %% 测试1：正常行驶——前0.5秒不应触发任何预警
    dt = t(2) - t(1);
    idx_0_5s = round(0.5 / dt);
    tc1_fcw = any(fcw_flag(1:idx_0_5s));
    tc1_aeb = any(aeb_flag(1:idx_0_5s));
    tc1_pass = ~tc1_fcw && ~tc1_aeb;
    results(1).name   = 'Normal driving (no warning first 0.5s)';
    results(1).passed = tc1_pass;
    results(1).detail = sprintf('FCW=%d AEB=%d (expect 0, 0)', tc1_fcw, tc1_aeb);

    %% 测试2：障碍物接近——应触发 FCW
    tc2_pass = any(fcw_flag);
    results(2).name   = 'Obstacle approach triggers FCW';
    results(2).passed = tc2_pass;
    results(2).detail = sprintf('FCW triggered=%d', tc2_pass);

    %% 测试3：紧急制动——应触发 AEB
    tc3_pass = any(aeb_flag);
    results(3).name   = 'Emergency braking triggers AEB';
    results(3).passed = tc3_pass;
    results(3).detail = sprintf('AEB triggered=%d', tc3_pass);

    %% 测试4：车道偏移——应触发 LDW
    tc4_pass = any(ldw_flag);
    results(4).name   = 'Lane departure triggers LDW';
    results(4).passed = tc4_pass;
    results(4).detail = sprintf('LDW triggered=%d, max offset=%.3f m', ...
                        tc4_pass, max(abs(lat_pos)));

    %% 测试5：传感器失效——系统应优雅降级
    tc5_pass = ~any(isnan(veh_vel));
    results(5).name   = 'Sensor failure graceful degradation';
    results(5).passed = tc5_pass;
    results(5).detail = sprintf('Vel has NaN=%d (expect 0)', any(isnan(veh_vel)));

end
