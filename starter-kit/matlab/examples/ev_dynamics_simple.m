%% 简单电动汽车动力学仿真
% MATLAB R2016b 兼容
% 包含：电机转矩特性 + 纵向动力学 + 能耗估算

clear; clc; close all;

%% 车辆参数
m  = 1600;       % 整车质量 [kg]
Cd = 0.28;       % 风阻系数
Af = 2.1;        % 迎风面积 [m^2]
rho = 1.225;     % 空气密度 [kg/m^3]
f  = 0.012;      % 滚动阻力系数
g  = 9.81;       % 重力加速度 [m/s^2]
rw = 0.33;       % 车轮半径 [m]

%% 电机参数（永磁同步电机简化模型）
P_max  = 100000; % 峰值功率 [W]
T_max  = 250;    % 峰值转矩 [Nm]
n_base = 3800;   % 基速 [rpm]（恒转矩区上限）
n_max  = 9000;   % 最高转速 [rpm]
eta_motor = 0.90; % 电机平均效率

%% 电池参数
V_bat = 350;     % 电池标称电压 [V]
Q_bat = 100;     % 电池容量 [Ah]
SOC_init = 0.95; % 初始 SOC

%% 仿真设置
dt = 0.05;       % 步长 [s]
T  = 60;         % 总仿真时间 [s]
t  = 0:dt:T;
n  = length(t);

%% 目标车速曲线（加速-匀速-减速）- 向量化
V_CRUISE = 80 / 3.6;          % 巡航速度 [m/s]
T_ACCEL = 15; T_CRUISE = 45;  % 时间节点 [s]
v_target = V_CRUISE * min(t / T_ACCEL, 1) ...
         .* (t <= T_CRUISE) ...
         + V_CRUISE * max(1 - (t - T_CRUISE) / T_ACCEL, 0) ...
           .* (t > T_CRUISE);

%% 仿真
v = zeros(1, n);     % 实际车速 [m/s]
s = zeros(1, n);     % 位移 [m]
T_m = zeros(1, n);   % 电机转矩 [Nm]
P_m = zeros(1, n);   % 电机功率 [W]
E_cons = zeros(1, n);% 累计能耗 [Wh]
SOC = SOC_init * ones(1, n);

for i = 2:n
    % 简单驾驶员模型：PID 跟踪目标车速
    v_err = v_target(i-1) - v(i-1);
    a_req = 2.0 * v_err;  % P 控制
    a_req = max(-3, min(3, a_req));  % 限制加速度范围

    % 阻力
    F_air = 0.5 * rho * Cd * Af * v(i-1)^2;
    F_roll = f * m * g;
    F_resist = F_air + F_roll;

    % 需求驱动力
    F_req = m * a_req + F_resist;

    % 电机转矩限制
    motor_rpm = v(i-1) * 60 / (2 * pi * rw);
    if motor_rpm <= n_base
        T_avail = T_max;  % 恒转矩区
    else
        T_avail = T_max * n_base / motor_rpm;  % 恒功率区
    end
    T_avail = max(0, T_avail);

    T_wheel = F_req * rw;
    T_wheel = max(-T_avail*0.5, min(T_avail, T_wheel));  % 限制在电机能力内
    T_m(i) = T_wheel;

    % 车辆动力学
    F_trac = T_wheel / rw;
    a = (F_trac - F_resist) / m;
    v(i) = v(i-1) + a * dt;
    v(i) = max(0, v(i));
    s(i) = s(i-1) + v(i) * dt;

    % 功率和能耗
    P_m(i) = T_m(i) * (motor_rpm * 2 * pi / 60);
    if P_m(i) > 0
        P_bat = P_m(i) / eta_motor;
    else
        P_bat = P_m(i) * 0.6;  % 回馈制动（简化）
    end
    E_cons(i) = E_cons(i-1) + P_bat * dt / 3600;  % Wh

    SOC(i) = SOC(i-1) - P_bat * dt / (V_bat * Q_bat * 3600);
end

%% 绘图
figure('Position', [100 100, 900, 650]);

subplot(3,2,1);
plot(t, v*3.6, 'b-', 'LineWidth', 1.5); hold on;
plot(t, v_target*3.6, 'r--', 'LineWidth', 1);
ylabel('车速 (km/h)'); grid on;
legend('实际', '目标', 'Location', 'best');
title('车速跟踪');

subplot(3,2,2);
plot(t, T_m, 'g-', 'LineWidth', 1.5);
ylabel('电机转矩 (Nm)'); grid on;
title('电机输出转矩');

subplot(3,2,3);
plot(t, s/1000, 'b-', 'LineWidth', 1.5);
ylabel('行驶距离 (km)'); grid on;
title('累计行驶距离');

subplot(3,2,4);
plot(t, P_m/1000, 'r-', 'LineWidth', 1.5);
ylabel('电机功率 (kW)'); grid on;
title('电机功率');

subplot(3,2,5);
plot(t, E_cons, 'm-', 'LineWidth', 1.5);
xlabel('时间 (s)'); ylabel('累计能耗 (Wh)'); grid on;
title('累计能耗');

subplot(3,2,6);
plot(t, SOC*100, 'b-', 'LineWidth', 1.5);
xlabel('时间 (s)'); ylabel('SOC (%)'); grid on;
title('电池 SOC');

%% 输出
fprintf('===== 仿真结果 =====\n');
fprintf('最高车速: %.1f km/h\n', max(v)*3.6);
fprintf('总行驶距离: %.2f km\n', s(end)/1000);
fprintf('累计能耗: %.1f Wh\n', E_cons(end));
fprintf('百公里能耗: %.1f kWh/100km\n', E_cons(end) / (s(end)/1000) / 10);
fprintf('剩余 SOC: %.1f%%\n', SOC(end)*100);
fprintf('估算续航: %.0f km\n', s(end) * SOC_init / (SOC_init - SOC(end) + 0.001));
