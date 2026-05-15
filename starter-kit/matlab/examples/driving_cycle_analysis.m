%% 驾驶循环分析与能耗计算
% MATLAB R2016b 兼容
% 基于 WLTC Class 3 速度曲线 + 电动汽车能耗模型
% 可替换为自定义驾驶循环数据

clear; clc; close all;

%% 生成 WLTC-like 速度曲线（简化）
% 实际项目中可替换为 wltc_data = readtable('WLTC.csv');
dt = 1;              % [s]
T  = 1800;           % 总时长 30 min
t  = (0:dt:T)';

% 分段构造速度曲线 [km/h]
v_kmh = zeros(size(t));
% 低速段 0-300s: 0→50 km/h
i1 = t<=300;
v_kmh(i1) = 50 * (t(i1)/300).^0.5;
% 中速段 300-800s: 50→80 km/h
i2 = t>300 & t<=800;
v_kmh(i2) = 50 + 30 * (t(i2)-300)/500;
% 高速段 800-1300s: 80→120 km/h
i3 = t>800 & t<=1300;
v_kmh(i3) = 80 + 40 * sin(pi*(t(i3)-800)/1000);
% 超高速段 1300-1600s: 120→130 km/h
i4 = t>1300 & t<=1600;
v_kmh(i4) = 120 + 10 * (t(i4)-1300)/300;
% 减速段 1600-1800s
i5 = t>1600;
v_kmh(i5) = max(130 - 40*(t(i5)-1600)/200, 0);

v_ms = v_kmh / 3.6;  % m/s

%% 车辆参数
m  = 1800;           % 质量 [kg]
Cd = 0.30;           % 风阻系数
Af = 2.2;            % 迎风面积 [m^2]
rho = 1.225;         % 空气密度 [kg/m^3]
f  = 0.012;          % 滚动阻力系数
g  = 9.81;
rw = 0.33;           % 车轮半径 [m]

%% 电机参数
P_max  = 120000;     % 峰值功率 [W]
T_max  = 280;        % 峰值转矩 [Nm]
n_base = 3500;       % 基速 [rpm]
eta_m  = 0.92;       % 电机效率
eta_r  = 0.85;       % 回馈效率

%% 电池参数
Q_bat = 60;          % [Ah]
V_bat = 380;         % [V]
SOC_0 = 0.95;

%% 计算需求功率和能耗
n = length(t);
a     = zeros(n, 1);  % 加速度 [m/s^2]
F_trac= zeros(n, 1);  % 驱动力 [N]
P_mot = zeros(n, 1);  % 电机功率 [W]
P_bat = zeros(n, 1);  % 电池功率 [W]
E_con = zeros(n, 1);  % 累计能耗 [Wh]
SOC   = SOC_0 * ones(n, 1);
mode  = cell(n, 1);   % 工作模式

for i = 2:n
    % 加速度
    a(i) = (v_ms(i) - v_ms(i-1)) / dt;

    % 行驶阻力
    F_air  = 0.5 * rho * Cd * Af * v_ms(i)^2;
    F_roll = f * m * g;
    F_acc  = m * a(i);

    F_trac(i) = F_air + F_roll + F_acc;

    % 车轮转矩和转速
    omega_w = v_ms(i) / rw;          % [rad/s]
    T_wheel = F_trac(i) * rw;        % [Nm]

    motor_rpm = omega_w * 30 / pi;

    % 电机转矩限制
    if motor_rpm <= n_base
        T_avail = T_max;
    else
        T_avail = T_max * n_base / motor_rpm;
    end

    % 电机功率
    P_mot(i) = T_wheel * omega_w;

    if P_mot(i) >= 0  % 驱动
        P_bat(i) = P_mot(i) / eta_m;
        mode{i} = '驱动';
    else              % 回馈制动
        P_bat(i) = P_mot(i) * eta_r;
        mode{i} = '回馈';
    end

    E_con(i) = E_con(i-1) + P_bat(i) * dt / 3600;  % [Wh]
    SOC(i) = SOC(i-1) - P_bat(i) * dt / (V_bat * Q_bat * 3600);
end

%% 驱动/回馈统计
drv_mask = P_mot > 0;
reg_mask = P_mot < 0;

%% 绘图
figure('Position', [50 50, 950, 700]);

subplot(3,2,1);
plot(t/60, v_kmh, 'b-', 'LineWidth', 1.2);
xlabel('时间 (min)'); ylabel('车速 (km/h)');
grid on; title('驾驶循环 — WLTC-like');

subplot(3,2,2);
yyaxis left;
plot(t/60, P_mot/1000, 'b-', 'LineWidth', 1);
ylabel('电机功率 (kW)');
yyaxis right;
plot(t/60, E_con/1000, 'r-', 'LineWidth', 1.5);
ylabel('累计能耗 (kWh)');
xlabel('时间 (min)'); grid on;
title('功率与能耗');

subplot(3,2,3);
histogram(P_mot(drv_mask)/1000, 30, 'FaceColor', 'b', 'EdgeAlpha', 0.3); hold on;
histogram(abs(P_mot(reg_mask))/1000, 30, 'FaceColor', 'g', 'EdgeAlpha', 0.3);
xlabel('功率 (kW)'); ylabel('频次');
legend('驱动', '回馈'); grid on;
title('功率分布直方图');

subplot(3,2,4);
plot(t/60, a, 'r-', 'LineWidth', 1);
xlabel('时间 (min)'); ylabel('加速度 (m/s^2)');
grid on; title('加速度曲线');

subplot(3,2,5);
plot(t/60, SOC*100, 'b-', 'LineWidth', 1.2);
xlabel('时间 (min)'); ylabel('SOC (%)');
grid on; title('电池 SOC 变化');

subplot(3,2,6);
pie_data = [sum(P_bat(drv_mask)*dt/3600), sum(abs(P_bat(reg_mask))*dt/3600)];
pie(pie_data, {'驱动能耗 (Wh)', '回馈回收 (Wh)'});
title('能量流向');

%% 结果汇总
dist_km = sum(v_ms * dt) / 1000;
E_100km = E_con(end) / dist_km * 100 / 1000;  % kWh/100km

fprintf('===== 驾驶循环分析 =====\n');
fprintf('总行驶距离: %.2f km\n', dist_km);
fprintf('累计能耗: %.1f kWh\n', E_con(end)/1000);
fprintf('百公里能耗: %.1f kWh/100km\n', E_100km);
fprintf('SOC 消耗: %.1f %%\n', (SOC_0 - SOC(end))*100);
fprintf('有效续航: %.0f km\n', dist_km * SOC_0 / (SOC_0 - SOC(end) + 0.001));
fprintf('回馈能量占比: %.1f %%\n', sum(abs(P_bat(reg_mask))) / sum(abs(P_bat)) * 100);
