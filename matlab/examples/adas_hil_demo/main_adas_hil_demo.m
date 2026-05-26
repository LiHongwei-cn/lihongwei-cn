% ADAS 硬件在环仿真演示
%
% 功能：模拟三种辅助驾驶功能
%   FCW（前碰撞预警）：TTC < 2.5 秒
%   AEB（自动紧急制动）：TTC < 1.0 秒
%   LDW（车道偏离预警）：横向偏移 > 0.3 米
%
% 兼容版本：MATLAB R2016b

clc; close all;

%% 车辆参数
vehicle_params.m   = 1500;
vehicle_params.Cd  = 0.32;
vehicle_params.Af  = 2.2;
vehicle_params.Cr  = 0.015;
vehicle_params.g   = 9.81;
vehicle_params.rho = 1.225;
vehicle_params.F_max_engine = 4000;
vehicle_params.F_max_brake  = 8000;
vehicle_params.v_max = 200 / 3.6;

%% 传感器参数
sensor_cfg.radar_max_range   = 150;
sensor_cfg.radar_range_std   = 0.5;
sensor_cfg.radar_rate_std    = 0.1;
sensor_cfg.radar_azimuth_std = 0.02;
sensor_cfg.camera_det_prob   = 0.95;
sensor_cfg.camera_lane_std   = 0.05;
sensor_cfg.ultrasonic_range  = 5;

%% 场景参数
v0_kmh      = 80;
v0          = v0_kmh / 3.6;
x0          = 0;
obs_dist    = 60;
obs_speed   = 0;
lat_offset0 = 0;

%% 仿真参数
dt    = 0.01;
t_end = 5;
t     = 0:dt:t_end;
N     = length(t);

%% 预分配
veh_pos      = zeros(1, N);
veh_vel      = zeros(1, N);
veh_acc      = zeros(1, N);
veh_lat_pos  = zeros(1, N);
throttle_cmd = zeros(1, N);
brake_cmd    = zeros(1, N);
fcw_flag     = false(1, N);
aeb_flag     = false(1, N);
ldw_flag     = false(1, N);
radar_range  = zeros(1, N);
camera_lane  = zeros(1, N);

%% 初始条件
veh_pos(1)     = x0;
veh_vel(1)     = v0;
veh_lat_pos(1) = lat_offset0;

%% 主仿真循环
for k = 1:N
    obs_range      = obs_dist - veh_pos(k);
    obs_range_rate = obs_speed - veh_vel(k);

    sens = sensor_model(obs_range, obs_range_rate, ...
                        veh_lat_pos(k), sensor_cfg);

    ctrl = adas_controller(sens, veh_vel(k), veh_lat_pos(k));

    vehicle_dt = dt;
    [acc_new, vel_new, pos_new] = vehicle_model(...
        ctrl.throttle, ctrl.brake, veh_vel(k), veh_pos(k), ...
        vehicle_params, vehicle_dt);

    if ctrl.ldw_warning
        lat_new = veh_lat_pos(k);
    else
        lat_new = veh_lat_pos(k) + 0.1 * dt;
    end

    veh_acc(k) = acc_new;
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

%% 测试验证
test_results = hil_test_runner(t, veh_vel, veh_pos, veh_lat_pos, ...
    fcw_flag, aeb_flag, ldw_flag, radar_range);

%% 测试报告
fprintf('\n');
fprintf('========================================\n');
fprintf('  ADAS 硬件在环仿真测试报告\n');
fprintf('  日期: %s\n', datestr(now));
fprintf('  场景: 初始速度 %d km/h, 障碍物距离 %d m\n', v0_kmh, obs_dist);
fprintf('========================================\n');
for i = 1:length(test_results)
    if test_results(i).passed
        status = '通过';
    else
        status = '失败';
    end
    fprintf('  测试%d  %-30s [%s]\n', i, test_results(i).name, status);
end
fprintf('========================================\n');
n_pass = sum([test_results.passed]);
fprintf('  结果: %d / %d 通过\n', n_pass, length(test_results));
fprintf('========================================\n');
fprintf('\n');

%% 可视化
visualize_results(t, veh_pos, veh_vel, veh_acc, veh_lat_pos, ...
    radar_range, camera_lane, fcw_flag, aeb_flag, ldw_flag, ...
    throttle_cmd, brake_cmd, obs_dist);
