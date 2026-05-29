%% TEST_PARKING_SYSTEM - 倒车入库系统测试脚本
% 兼容版本：MATLAB R2016b
% 功能：测试路径规划和控制算法，无需CarSim
%
% 作者：LiHongwei
% 日期：2026-05-29

clear; clc; close all;

fprintf('========================================\n');
fprintf('  倒车入库系统测试（无CarSim模式）\n');
fprintf('========================================\n\n');

%% ==================== 测试路径规划算法 ====================

fprintf('[1/3] 测试路径规划算法...\n');

% 道路参数
road.length = 50;
road.width = 7;
road.parking_spot_length = 5;
road.parking_spot_depth = 5.5;
road.target_spot_index = 5;

% 计算目标车位位置
target_x = (road.target_spot_index - 0.5) * road.parking_spot_length;
target_y = -road.parking_spot_depth / 2;

% 车辆初始位置
veh_x0 = 45;
veh_y0 = 3.5;

% 生成参考路径
num_points = 200;
ref_path = generate_test_path(veh_x0, veh_y0, target_x, target_y, num_points);

fprintf('   路径点数量: %d\n', size(ref_path, 1));
fprintf('   起始位置: (%.2f, %.2f)\n', ref_path(1,1), ref_path(1,2));
fprintf('   目标位置: (%.2f, %.2f)\n', ref_path(end,1), ref_path(end,2));

% 绘制路径
figure('Name', '路径规划测试', 'Position', [100, 100, 1000, 600]);

subplot(1, 2, 1);
plot(ref_path(:,1), ref_path(:,2), 'b-', 'LineWidth', 2);
hold on;
plot(ref_path(1,1), ref_path(1,2), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g');
plot(ref_path(end,1), ref_path(end,2), 'rx', 'MarkerSize', 15, 'MarkerWidth', 3);

% 绘制道路和车位
draw_test_road(road);

xlabel('X [m]');
ylabel('Y [m]');
title('参考路径');
legend('参考路径', '起始点', '目标点', 'Location', 'best');
grid on;
axis equal;

subplot(1, 2, 2);
plot(ref_path(:,3), 'b-', 'LineWidth', 1.5);
xlabel('路径点索引');
ylabel('航向角 [rad]');
title('航向角变化');
grid on;

fprintf('[1/3] 路径规划测试完成\n\n');

%% ==================== 测试控制器 ====================

fprintf('[2/3] 测试PID控制器...\n');

% 模拟车辆状态
dt = 0.01;
time = 0:dt:30;
n_steps = length(time);

% 初始化状态
x = zeros(n_steps, 1);
y = zeros(n_steps, 1);
yaw = zeros(n_steps, 1);
v = zeros(n_steps, 1);

x(1) = veh_x0;
y(1) = veh_y0;
yaw(1) = 0;
v(1) = 5 / 3.6;  % 5 km/h -> m/s

% 控制参数
Kp_lat = 2.5;
Ki_lat = 0.1;
Kd_lat = 0.5;

Kp_lon = 1.8;
Ki_lon = 0.05;
Kd_lon = 0.3;

% 误差积分
e_lat_int = 0;
e_lon_int = 0;
e_lat_prev = 0;
e_lon_prev = 0;

% 控制记录
steer_cmd = zeros(n_steps, 1);
brake_cmd = zeros(n_steps, 1);
lateral_error = zeros(n_steps, 1);
speed_error = zeros(n_steps, 1);

% 找到最近的参考路径点
[~, idx] = min(sqrt((ref_path(:,1) - x(1)).^2 + (ref_path(:,2) - y(1)).^2));

fprintf('   开始仿真...\n');

for i = 2:n_steps
    % 找到最近的参考路径点
    [~, idx] = min(sqrt((ref_path(:,1) - x(i-1)).^2 + (ref_path(:,2) - y(i-1)).^2));

    % 提取参考值
    x_ref = ref_path(idx, 1);
    y_ref = ref_path(idx, 2);
    yaw_ref = ref_path(idx, 3);

    % 计算横向误差
    dx = x_ref - x(i-1);
    dy = y_ref - y(i-1);
    e_lat = dy * cos(yaw(i-1)) - dx * sin(yaw(i-1));

    % 计算航向误差
    e_yaw = yaw_ref - yaw(i-1);
    e_yaw = mod(e_yaw + pi, 2*pi) - pi;

    % 计算速度误差（倒车速度2 km/h）
    v_ref = -2 / 3.6;  % 2 km/h -> m/s，负号表示倒车
    e_lon = v_ref - v(i-1);

    % PID控制 - 横向
    e_lat_int = e_lat_int + e_lat * dt;
    e_lat_der = (e_lat - e_lat_prev) / dt;
    steer = Kp_lat * e_lat + Ki_lat * e_lat_int + Kd_lat * e_lat_der;
    steer = max(min(steer, 540), -540);  % 限幅
    e_lat_prev = e_lat;

    % PID控制 - 纵向
    e_lon_int = e_lon_int + e_lon * dt;
    e_lon_der = (e_lon - e_lon_prev) / dt;
    brake = Kp_lon * e_lon + Ki_lon * e_lon_int + Kd_lon * e_lon_der;
    brake = max(min(brake, 1), -1);  % 限幅到[-1, 1]
    e_lon_prev = e_lon;

    % 记录控制命令
    steer_cmd(i) = steer;
    brake_cmd(i) = brake;
    lateral_error(i) = e_lat;
    speed_error(i) = e_lon;

    % 简化的车辆模型（自行车模型）
    L = 2.7;  % 轴距
    delta = steer * pi / 180;  % 转换为弧度

    % 状态更新
    x(i) = x(i-1) + v(i-1) * cos(yaw(i-1)) * dt;
    y(i) = y(i-1) + v(i-1) * sin(yaw(i-1)) * dt;
    yaw(i) = yaw(i-1) + v(i-1) / L * tan(delta) * dt;
    v(i) = v(i-1) + brake * 2 * dt;  % 简化的加速度模型
    v(i) = max(min(v(i), 5/3.6), -5/3.6);  % 速度限幅

    % 检查是否到达目标
    dist_to_target = sqrt((x(i) - target_x)^2 + (y(i) - target_y)^2);
    if dist_to_target < 0.3 && abs(v(i)) < 0.1
        fprintf('   到达目标！用时 %.1f 秒\n', time(i));
        x = x(1:i);
        y = y(1:i);
        time = time(1:i);
        break;
    end
end

fprintf('   最终位置: (%.2f, %.2f)\n', x(end), y(end));
fprintf('   位置误差: %.3f m\n', sqrt((x(end) - target_x)^2 + (y(end) - target_y)^2));

% 绘制结果
figure('Name', '控制器测试', 'Position', [100, 100, 1200, 800]);

subplot(2, 2, 1);
plot(ref_path(:,1), ref_path(:,2), 'r--', 'LineWidth', 2);
hold on;
plot(x, y, 'b-', 'LineWidth', 1.5);
plot(x(end), y(end), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g');
plot(target_x, target_y, 'rx', 'MarkerSize', 15, 'MarkerWidth', 3);
draw_test_road(road);
xlabel('X [m]');
ylabel('Y [m]');
title('车辆轨迹');
legend('参考路径', '实际轨迹', '最终位置', '目标位置', 'Location', 'best');
grid on;
axis equal;

subplot(2, 2, 2);
plot(time, x, 'b-', 'LineWidth', 1.5);
hold on;
plot(time, y, 'r-', 'LineWidth', 1.5);
xlabel('时间 [s]');
ylabel('位置 [m]');
title('车辆位置');
legend('X位置', 'Y位置', 'Location', 'best');
grid on;

subplot(2, 2, 3);
plot(time, v * 3.6, 'b-', 'LineWidth', 1.5);
xlabel('时间 [s]');
ylabel('速度 [km/h]');
title('车辆速度');
grid on;

subplot(2, 2, 4);
plot(time, steer_cmd, 'b-', 'LineWidth', 1.5);
xlabel('时间 [s]');
ylabel('转向角 [deg]');
title('转向命令');
grid on;

fprintf('[2/3] 控制器测试完成\n\n');

%% ==================== 性能分析 ====================

fprintf('[3/3] 性能分析...\n');

% 计算性能指标
max_lateral_error = max(abs(lateral_error));
final_position_error = sqrt((x(end) - target_x)^2 + (y(end) - target_y)^2);
simulation_time = time(end);

fprintf('   最大横向误差: %.3f m\n', max_lateral_error);
fprintf('   最终位置误差: %.3f m\n', final_position_error);
fprintf('   仿真用时: %.1f 秒\n', simulation_time);

if final_position_error < 0.5
    fprintf('   ✓ 停车精度: 优秀\n');
elseif final_position_error < 1.0
    fprintf('   △ 停车精度: 良好\n');
else
    fprintf('   ✗ 停车精度: 需要改进\n');
end

fprintf('\n========================================\n');
fprintf('  测试完成！\n');
fprintf('========================================\n');

%% ==================== 辅助函数 ====================

function ref_path = generate_test_path(x0, y0, x_target, y_target, num_points)
% 生成测试用的参考路径

    % 路径点
    path_x = zeros(num_points, 1);
    path_y = zeros(num_points, 1);
    path_yaw = zeros(num_points, 1);

    % 第一阶段：接近（40%）
    n1 = round(0.4 * num_points);
    t1 = linspace(0, 1, n1);
    path_x(1:n1) = x0 + (x_target + 5 - x0) * t1;
    path_y(1:n1) = y0 * ones(1, n1);

    % 第二阶段：转弯（30%）
    n2 = round(0.3 * num_points);
    t2 = linspace(0, 1, n2);
    s = t2;
    poly = 10*s.^3 - 15*s.^4 + 6*s.^5;
    path_x(n1+1:n1+n2) = (x_target + 5) + (x_target - (x_target + 5)) * s;
    path_y(n1+1:n1+n2) = y0 + (0 - y0) * poly;

    % 第三阶段：入库（30%）
    n3 = num_points - n1 - n2;
    t3 = linspace(0, 1, n3);
    path_x(n1+n2+1:end) = x_target * ones(1, n3);
    path_y(n1+n2+1:end) = 0 + (y_target - 0) * t3;

    % 计算航向角
    for i = 2:num_points-1
        dx = path_x(i+1) - path_x(i-1);
        dy = path_y(i+1) - path_y(i-1);
        path_yaw(i) = atan2(dy, dx);
    end
    path_yaw(1) = path_yaw(2);
    path_yaw(end) = path_yaw(end-1);

    ref_path = [path_x, path_y, path_yaw];

end

function draw_test_road(road)
% 绘制测试用的道路和车位

    hold on;

    % 绘制道路边界
    plot([0, road.length], [0, 0], 'k-', 'LineWidth', 2);
    plot([0, road.length], [road.width, road.width], 'k-', 'LineWidth', 2);

    % 绘制车位
    for i = 1:10
        spot_x_start = (i-1) * road.parking_spot_length;
        spot_x_end = i * road.parking_spot_length;
        spot_y_start = -road.parking_spot_depth;
        spot_y_end = 0;

        % 车位边框
        rectangle('Position', [spot_x_start, spot_y_start, ...
            road.parking_spot_length, road.parking_spot_depth], ...
            'EdgeColor', 'k', 'LineWidth', 1.5);

        % 如果是目标车位，标记为空
        if i == road.target_spot_index
            rectangle('Position', [spot_x_start + 0.2, spot_y_start + 0.2, ...
                road.parking_spot_length - 0.4, road.parking_spot_depth - 0.4], ...
                'FaceColor', [0.9, 1, 0.9], 'EdgeColor', 'g', 'LineWidth', 2);
            text(spot_x_start + road.parking_spot_length/2, ...
                spot_y_start + road.parking_spot_depth/2, ...
                '目标', 'HorizontalAlignment', 'center', 'FontSize', 12, 'Color', 'g');
        else
            % 绘制占用的车辆
            rectangle('Position', [spot_x_start + 0.2, spot_y_start + 0.2, ...
                road.parking_spot_length - 0.4, road.parking_spot_depth - 0.4], ...
                'FaceColor', [0.7, 0.7, 0.7], 'EdgeColor', 'k', 'LineWidth', 1);
        end
    end

    % 设置坐标轴范围
    xlim([-5, road.length + 5]);
    ylim([-road.parking_spot_depth - 2, road.width + 2]);

end
