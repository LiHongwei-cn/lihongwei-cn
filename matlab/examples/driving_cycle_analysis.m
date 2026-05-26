%% 驾驶循环能耗分析
% MATLAB R2016b 兼容
% 构造类 WLTC 工况 + 电动汽车能耗模型

clear; clc; close all;

%% 生成类 WLTC 速度曲线 [km/h]
dt = 1;              % [s]
T  = 1800;           % 总计 30 min
t  = (0:dt:T)';

v_kmh = zeros(size(t));
i1 = t<=300;         v_kmh(i1) = 50 * (t(i1)/300).^0.5;
i2 = t>300 & t<=800;  v_kmh(i2) = 50 + 30 * (t(i2)-300)/500;
i3 = t>800 & t<=1300; v_kmh(i3) = 80 + 40 * sin(pi*(t(i3)-800)/1000);
i4 = t>1300 & t<=1600; v_kmh(i4) = 120 + 10 * (t(i4)-1300)/300;
i5 = t>1600;          v_kmh(i5) = max(130 - 40*(t(i5)-1600)/200, 0);

v_ms = v_kmh / 3.6;

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
eta_m  = 0.92;       % 电机驱动效率
eta_r  = 0.85;       % 回馈效率

%% 电池参数
Q_bat = 60;          % 电池容量 [Ah]
V_bat = 380;         % 电池电压 [V]
SOC_0 = 0.95;        % 初始 SOC

%% 仿真
n = length(t);
a      = zeros(n, 1);
F_trac = zeros(n, 1);
P_mot  = zeros(n, 1);
P_bat  = zeros(n, 1);
E_con  = zeros(n, 1);
SOC    = SOC_0 * ones(n, 1);

for i = 2:n
    a(i) = (v_ms(i) - v_ms(i-1)) / dt;

    F_air  = 0.5 * rho * Cd * Af * v_ms(i)^2;
    F_roll = f * m * g;
    F_acc  = m * a(i);
    F_trac(i) = F_air + F_roll + F_acc;

    omega_w = v_ms(i) / rw;
    T_wheel = F_trac(i) * rw;
    motor_rpm = omega_w * 30 / pi;

    if motor_rpm <= n_base
        T_avail = T_max;
    else
        T_avail = T_max * n_base / motor_rpm;
    end

    P_mot(i) = T_wheel * omega_w;

    if P_mot(i) >= 0
        P_bat(i) = P_mot(i) / eta_m;
    else
        P_bat(i) = P_mot(i) * eta_r;
    end

    E_con(i) = E_con(i-1) + P_bat(i) * dt / 3600;
    SOC(i) = SOC(i-1) - P_bat(i) * dt / (V_bat * Q_bat * 3600);
end

%% 分类标记
drv_mask = P_mot > 0;
reg_mask = P_mot < 0;

%% 绘图
figure('Position', [50 50, 950, 700]);

subplot(3,2,1);
plot(t/60, v_kmh, 'b-', 'LineWidth', 1.2);
xlabel('Time (min)'); ylabel('Speed (km/h)');
grid on; title('Driving Cycle (WLTC-like)');

subplot(3,2,2);
yyaxis left;
plot(t/60, P_mot/1000, 'b-', 'LineWidth', 1);
ylabel('Motor Power (kW)');
yyaxis right;
plot(t/60, E_con/1000, 'r-', 'LineWidth', 1.5);
ylabel('Cumulative Energy (kWh)');
xlabel('Time (min)'); grid on;
title('Power & Energy');

subplot(3,2,3);
histogram(P_mot(drv_mask)/1000, 30, 'FaceColor', 'b', 'EdgeAlpha', 0.3); hold on;
if any(reg_mask)
    histogram(abs(P_mot(reg_mask))/1000, 30, 'FaceColor', 'g', 'EdgeAlpha', 0.3);
end
xlabel('Power (kW)'); ylabel('Count');
legend('Driving', 'Regen'); grid on;
title('Power Distribution');

subplot(3,2,4);
plot(t/60, a, 'r-', 'LineWidth', 1);
xlabel('Time (min)'); ylabel('Acceleration (m/s^2)');
grid on; title('Acceleration');

subplot(3,2,5);
plot(t/60, SOC*100, 'b-', 'LineWidth', 1.2);
xlabel('Time (min)'); ylabel('SOC (%)');
grid on; title('Battery SOC');

subplot(3,2,6);
E_drv = sum(P_bat(drv_mask)*dt/3600);
E_reg = sum(abs(P_bat(reg_mask))*dt/3600);
if E_reg > 0
    pie([E_drv, E_reg], {'Driving (Wh)', 'Regen (Wh)'});
else
    pie(E_drv, {'Driving (Wh)'});
end
title('Energy Flow');

%% 结果输出
dist_km = sum(v_ms * dt) / 1000;
E_100km = E_con(end) / dist_km * 100 / 1000;

fprintf('===== Driving Cycle Analysis =====\n');
fprintf('Total distance: %.2f km\n', dist_km);
fprintf('Total energy: %.1f kWh\n', E_con(end)/1000);
fprintf('Energy consumption: %.1f kWh/100km\n', E_100km);
fprintf('SOC consumed: %.1f %%\n', (SOC_0 - SOC(end))*100);
fprintf('Estimated range: %.0f km\n', dist_km * SOC_0 / (SOC_0 - SOC(end) + 0.001));
fprintf('Regen ratio: %.1f %%\n', sum(abs(P_bat(reg_mask))) / max(sum(abs(P_bat)), 1e-6) * 100);
