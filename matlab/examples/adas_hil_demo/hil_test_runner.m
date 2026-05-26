% HIL 测试验证脚本
%
% 功能：对仿真结果执行 5 项测试，报告通过/失败结果
%
% 兼容版本：MATLAB R2016b

function results = hil_test_runner(t, veh_vel, veh_pos, lat_pos, ...
    fcw_flag, aeb_flag, ldw_flag, radar_rng)

    N = length(t);
    results = struct('name', {}, 'passed', {}, 'detail', {});

    %% 测试1：正常行驶 - 前0.5秒不应触发任何警告
    dt = t(2) - t(1);
    idx_0_5s = round(0.5 / dt);
    tc1_fcw = any(fcw_flag(1:idx_0_5s));
    tc1_aeb = any(aeb_flag(1:idx_0_5s));
    tc1_pass = ~tc1_fcw && ~tc1_aeb;
    results(1).name   = '正常行驶 (前0.5秒无警告)';
    results(1).passed = tc1_pass;
    results(1).detail = sprintf('FCW=%d AEB=%d (期望 0, 0)', tc1_fcw, tc1_aeb);

    %% 测试2：障碍物接近 - 应触发 FCW
    tc2_pass = any(fcw_flag);
    results(2).name   = '障碍物接近触发FCW';
    results(2).passed = tc2_pass;
    results(2).detail = sprintf('FCW 触发=%d', tc2_pass);

    %% 测试3：超近距离 - 应触发 AEB
    tc3_pass = any(aeb_flag);
    results(3).name   = '近距离触发AEB';
    results(3).passed = tc3_pass;
    results(3).detail = sprintf('AEB 触发=%d', tc3_pass);

    %% 测试4：车道偏离 - 应触发 LDW
    tc4_pass = any(ldw_flag);
    results(4).name   = '车道偏移触发LDW';
    results(4).passed = tc4_pass;
    results(4).detail = sprintf('LDW 触发=%d, 最大偏移=%.3f m', ...
                        tc4_pass, max(abs(lat_pos)));

    %% 测试5：传感器失效 - 系统应优雅降级
    tc5_pass = ~any(isnan(veh_vel));
    results(5).name   = '传感器失效优雅降级';
    results(5).passed = tc5_pass;
    results(5).detail = sprintf('速度含 NaN=%d (期望 0)', any(isnan(veh_vel)));

end
