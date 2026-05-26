% ADAS 硬件在环仿真演示
%
% 功能说明：
%   模拟高级驾驶辅助系统（ADAS）的三种核心功能：
%   - FCW（前碰撞预警）：TTC < 2.5 秒时发出警告
%   - AEB（自动紧急制动）：TTC < 1.0 秒时全力制动
%   - LDW（车道偏离预警）：横向偏移 > 0.3 米时发出警告
%
% 兼容版本：MATLAB R2016b
%   不使用 rms()、arguments 代码块、string 类型、tiledlayout
%
% 使用方法：在 MATLAB 中打开此文件，按 F5 运行

clc; close all;

%% 车辆参数
vehicle_params.m   = 1500;     % 整车质量 [kg]
vehicle_params.Cd  = 0.32;     % 风阻系数 [-]
vehicle_params.Af  = 2.2;      % 迎风面积 [m^2]
vehicle_params.Cr  = 0.015;    % 滚动阻力系数 [-]
vehicle_params.g   = 9.81;     % 重力加速度 [m/s^2]
vehicle_params.rho = 1.225;    % 空气密度 [kg/m^3]
vehicle_params.F_max_engine = 4000;  % 最大驱动力 [N]
vehicle_params.F_max_brake  = 8000;  % 最大制动力 [N]
vehicle_params.v_max = 200 / 3.6;    % 最高车速 [m/s]（约200km/h）

%% 传感器参数
sensor_cfg.radar_max_range   = 150;   % 雷达最大探测距离 [m]
sensor_cfg.radar_range_std   = 0.5;   % 雷达测距噪声标准差 [m]
sensor_cfg.radar_rate_std    = 0.1;   % 雷达测速噪声标准差 [m/s]
sensor_cfg.radar_azimuth_std = 0.02;  % 雷达方位角噪声标准差 [rad]
sensor_cfg.camera_det_prob   = 0.95;  % 摄像头检测概率 [-]
sensor_cfg.camera_lane_std   = 0.05;  % 摄像头车道偏移噪声标准差 [m]
sensor_cfg.ultrasonic_range  = 5;     % 超声波最大探测距离 [m]

%% 场景参数
v0_kmh      = 80;    % 初始车速 [km/h]
v0          = v0_kmh / 3.6;  % 初始车速 [m/s]
x0          = 0;     % 初始纵向位置 [m]
obs_dist    = 60;    % 障碍物距起点距离 [m]
obs_speed   = 0;     % 障碍物速度（静止）[m/s]
lat_offset0 = 0;     % 初始横向偏移 [m]

%% 仿真参数
dt    = 0.01;   % 仿真步长 [s]
t_end = 5;      % 仿真总时长 [s]
t     = 0:dt:t_end;
N     = length(t);

%% 预分配存储空间
veh_pos      = zeros(1, N);    % 纵向位置 [m]
veh_vel      = zeros(1, N);    % 纵向速度 [m/s]
veh_acc      = zeros(1, N);    % 纵向加速度 [m/s^2]
veh_lat_pos  = zeros(1, N);    % 横向偏移 [m]
throttle_cmd = zeros(1, N);    % 油门指令 [0-1]
brake_cmd    = zeros(1, N);    % 制动指令 [0-1]
fcw_flag     = false(1, N);    % 前碰撞预警标志
aeb_flag     = false(1, N);    % 自动紧急制动标志
ldw_flag     = false(1, N);    % 车道偏离预警标志
radar_range  = zeros(1, N);    % 雷达测距数据 [m]
camera_lane  = zeros(1, N);    % 摄像头车道偏移 [m]

%% 初始条件
veh_pos(1)     = x0;
veh_vel(1)     = v0;
veh_lat_pos(1) = lat_offset0;

%% 主仿真循环
for k = 1:N
    % 计算真实距离和接近速度
    obs_range      = obs_dist - veh_pos(k);           % 真实距离 [m]
    obs_range_rate = obs_speed - veh_vel(k);           % 真实接近速度 [m/s]

    % 传感器模型：添加噪声，模拟雷达/摄像头/超声波
    sens = sensor_model(obs_range, obs_range_rate, ...
                        veh_lat_pos(k), sensor_cfg);

    % ADAS 控制器：根据传感器数据做出决策
    ctrl = adas_controller(sens, veh_vel(k), veh_lat_pos(k));

    % 车辆模型：根据油门/制动指令更新运动状态
    vehicle_dt = dt;  % 传递步长给车辆模型
    [acc_new, vel_new, pos_new] = vehicle_model(...
        ctrl.throttle, ctrl.brake, veh_vel(k), veh_pos(k), ...
        vehicle_params, vehicle_dt);

    % 横向运动模型（简单的漂移模型，用于 LDW 演示）
    if ctrl.ldw_warning
        lat_new = veh_lat_pos(k);   % 发出预警后保持当前位置
    else
        lat_new = veh_lat_pos(k) + 0.1 * dt;  % 缓慢向右漂移
    end

    % 存储当前步结果
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

%% 输出测试报告
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
