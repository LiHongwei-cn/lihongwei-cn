% HIL 测试用例验证
%
% 功能：对仿真结果运行 5 个测试用例，输出通过/失败结果
%
% 输入参数：
%   t          - 时间向量 [s]
%   veh_vel    - 速度历史 [m/s]
%   veh_pos    - 位置历史 [m]
%   lat_pos    - 横向偏移历史 [m]
%   fcw_flag   - 每个时间步的 FCW 预警标志
%   aeb_flag   - 每个时间步的 AEB 预警标志
%   ldw_flag   - 每个时间步的 LDW 预警标志
%   radar_rng  - 雷达测距历史 [m]
%
% 输出参数：
%   results    - 结构体数组，每个元素包含：
%                .name    - 测试用例名称
%                .passed  - 是否通过
%                .detail  - 详细信息
%
% 兼容版本：MATLAB R2016b

function results = hil_test_runner(t, veh_vel, veh_pos, lat_pos, ...
    fcw_flag, aeb_flag, ldw_flag, radar_rng)

    N = length(t);
    results = struct('name', {}, 'passed', {}, 'detail', {});

    %% 测试用例1：正常行驶 - 前0.5秒不应触发任何警告
    % 场景：障碍物距离较远，系统应保持巡航状态
    dt = t(2) - t(1);
    idx_0_5s = round(0.5 / dt);
    tc1_fcw = any(fcw_flag(1:idx_0_5s));
    tc1_aeb = any(aeb_flag(1:idx_0_5s));
    tc1_pass = ~tc1_fcw && ~tc1_aeb;
    results(1).name   = 'Normal driving (no warn in first 0.5s)';
    results(1).passed = tc1_pass;
    results(1).detail = sprintf('FCW=%d AEB=%d (expect 0, 0)', tc1_fcw, tc1_aeb);

    %% 测试用例2：障碍物接近 - 应触发 FCW
    % 场景：车辆接近静止障碍物，TTC 降至 2.5 秒以下时应触发 FCW
    tc2_pass = any(fcw_flag);
    results(2).name   = 'Obstacle approach triggers FCW';
    results(2).passed = tc2_pass;
    results(2).detail = sprintf('FCW triggered=%d', tc2_pass);

    %% 测试用例3：非常接近 - 应触发 AEB
    % 场景：TTC 降至 1.0 秒以下时应触发自动紧急制动
    tc3_pass = any(aeb_flag);
    results(3).name   = 'Close range triggers AEB';
    results(3).passed = tc3_pass;
    results(3).detail = sprintf('AEB triggered=%d', tc3_pass);

    %% 测试用例4：车道偏移 - 应触发 LDW
    % 场景：车辆横向偏移超过 0.3 米时应触发车道偏离预警
    tc4_pass = any(ldw_flag);
    results(4).name   = 'Lane drift triggers LDW';
    results(4).passed = tc4_pass;
    results(4).detail = sprintf('LDW triggered=%d, max offset=%.3f m', ...
                        tc4_pass, max(abs(lat_pos)));

    %% 测试用例5：传感器失效 - 系统应优雅降级
    % 场景：模拟 t=3s 时雷达丢失，验证系统不会崩溃
    % 判断标准：速度向量中无 NaN（系统正常运行）
    tc5_pass = ~any(isnan(veh_vel));
    results(5).name   = 'Sensor failure graceful degradation';
    results(5).passed = tc5_pass;
    results(5).detail = sprintf('NaN in velocity=%d (expect 0)', any(isnan(veh_vel)));

end
