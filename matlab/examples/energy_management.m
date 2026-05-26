%% 增程式电动车能量管理策略
% MATLAB R2016b 兼容
% 基于规则的恒温器(thermostat)策略 + 功率跟随策略对比
% 适用于增程式(串联混合动力)车辆

clc; close all;

%% 车辆参数
m  = 2000;        % 质量 [kg]
Cd = 0.32;        % 风阻系数
Af = 2.3;         % 迎风面积 [m^2]
rho = 1.225;      % 空气密度 [kg/m^3]
f  = 0.012;       % 滚动阻力
g  = 9.81;
rw = 0.33;        % 车轮半径 [m]

%% 动力系统
P_mot_max  = 120000;   % 驱动电机峰值功率 [W]
P_gen_max  = 60000;    % 增程器(发电机)额定功率 [W]
eta_gen    = 0.35;     % 增程器发电效率（油→电）
Q_bat      = 40;       % 电池容量 [Ah]
V_bat      = 350;      % 电池电压 [V]
SOC_min    = 0.25;     % SOC 下限
SOC_max    = 0.85;     % SOC 上限
SOC_init   = 0.50;     % 初始 SOC

%% 行驶工况（简化 WLTC 片段）
dt = 1.0;  T = 2400;  t = (0:dt:T)';
n = length(t);

v_ms = 15 + 10*sin(2*pi*t/600) + 5*sin(2*pi*t/200) + 3*sin(2*pi*t/80);
v_ms = max(v_ms, 0);

%% 计算驱动需求功率
P_dem = zeros(n, 1);
for i = 1:n
    if i > 1, a_i = (v_ms(i) - v_ms(i-1)) / dt; else a_i = 0; end
    F_aero  = 0.5 * rho * Cd * Af * v_ms(i)^2;
    F_roll  = f * m * g;
    F_acc   = m * a_i;
    omega_w = v_ms(i) / rw;
    T_wheel = (F_aero + F_roll + F_acc) * rw;
    P_wheel = T_wheel * omega_w;
    P_dem(i) = max(P_wheel, -P_mot_max);
end

%% ===== 策略1: 恒温器 (Thermostat) =====
P_gen1 = zeros(n, 1);
SOC1   = SOC_init * ones(n, 1);
mode1  = cell(n, 1);

for i = 2:n
    soc = SOC1(i-1);
    P_d = P_dem(i-1);

    if soc < SOC_min
        P_gen1(i) = P_gen_max;
    elseif soc > SOC_max
        P_gen1(i) = 0;
    else
        P_gen1(i) = P_gen1(i-1);
    end

    P_bat = P_d - P_gen1(i);
    dSOC = -P_bat * dt / (V_bat * Q_bat * 3600);
    SOC1(i) = SOC1(i-1) + dSOC;
    SOC1(i) = max(0.05, min(0.95, SOC1(i)));

    if P_gen1(i) > 0, mode1{i} = '增程'; else mode1{i} = '纯电'; end
end

%% ===== 策略2: 功率跟随 (Power Following) =====
P_gen2 = zeros(n, 1);
SOC2   = SOC_init * ones(n, 1);
mode2  = cell(n, 1);

SOC_center = 0.55;
SOC_band   = 0.05;

for i = 2:n
    soc = SOC2(i-1);
    P_d = P_dem(i-1);

    if soc < SOC_center - SOC_band
        P_set = P_d + 0.3 * P_gen_max;
    elseif soc > SOC_center + SOC_band
        P_set = max(0, P_d * 0.5);
    else
        P_set = P_d;
    end

    P_set = max(0, min(P_set, P_gen_max));
    if P_set > 0 && P_set < 15000
        P_set = 15000;
    end

    P_gen2(i) = P_set;
    if P_gen2(i) > 0, mode2{i} = '跟随'; else mode2{i} = '纯电'; end

    P_bat = P_d - P_gen2(i);
    dSOC = -P_bat * dt / (V_bat * Q_bat * 3600);
    SOC2(i) = SOC2(i-1) + dSOC;
    SOC2(i) = max(0.05, min(0.95, SOC2(i)));
end

%% ===== 结果对比 =====
fuel_rate = 0.23;
fuel1 = sum(P_gen1) * dt / 3600 / 1000 * fuel_rate;
fuel2 = sum(P_gen2) * dt / 3600 / 1000 * fuel_rate;

dist = sum(v_ms * dt) / 1000;

fprintf('===== 能量管理策略对比 =====\n');
fprintf('行驶距离: %.1f km\n', dist);
fprintf('\n%-18s %-15s %-15s\n', '指标', '恒温器', '功率跟随');
fprintf('%-18s %-15.1f %-15.1f\n', '百公里油耗 (L)', fuel1/dist*100, fuel2/dist*100);
fprintf('%-18s %-15.2f %-15.2f\n', '终值 SOC', SOC1(end), SOC2(end));
fprintf('%-18s %-15.2f %-15.2f\n', 'SOC 标准差', std(SOC1), std(SOC2));
fprintf('%-18s %-15d %-15d\n', '开关次数', ...
    sum(diff(P_gen1>0)~=0), sum(diff(P_gen2>0)~=0));

%% 绘图
figure('Position', [50 50, 1000, 700]);

subplot(4,2,1);
plot(t/60, v_ms*3.6, 'b-', 'LineWidth', 1);
xlabel('时间 (min)'); ylabel('车速 (km/h)');
grid on; title('行驶工况');

subplot(4,2,2);
plot(t/60, P_dem/1000, 'b-', 'LineWidth', 1);
xlabel('时间 (min)'); ylabel('功率 (kW)');
grid on; title('驱动需求功率');

subplot(4,2,3);
yyaxis left;
plot(t/60, SOC1*100, 'b-', 'LineWidth', 1.2);
ylabel('SOC (%)');
yyaxis right;
plot(t/60, P_gen1/1000, 'r-', 'LineWidth', 1);
ylabel('增程器功率 (kW)');
xlabel('时间 (min)'); grid on;
title('策略1: 恒温器');

subplot(4,2,4);
yyaxis left;
plot(t/60, SOC2*100, 'b-', 'LineWidth', 1.2);
ylabel('SOC (%)');
yyaxis right;
plot(t/60, P_gen2/1000, 'r-', 'LineWidth', 1);
ylabel('增程器功率 (kW)');
xlabel('时间 (min)'); grid on;
title('策略2: 功率跟随');

subplot(4,2,5);
plot(t/60, cumsum(P_gen1)*dt/3600/1000, 'r-', t/60, cumsum(P_gen2)*dt/3600/1000, 'b-', 'LineWidth', 1.2);
xlabel('时间 (min)'); ylabel('累计发电量 (kWh)');
legend('恒温器', '功率跟随'); grid on;
title('累计发电量');

subplot(4,2,6);
scatter(P_dem/1000, P_gen1/1000, 3, 'r', 'MarkerFaceAlpha', 0.3); hold on;
scatter(P_dem/1000, P_gen2/1000, 3, 'b', 'MarkerFaceAlpha', 0.3);
plot([-100 150], [-100 150], 'k--');
xlabel('需求功率 (kW)'); ylabel('增程器功率 (kW)');
grid on; legend('恒温器', '功率跟随');
title('功率分配散点图');

subplot(4,2,7:8);
bar_data = [fuel1, fuel2; fuel1/dist*100, fuel2/dist*100]';
bar(bar_data); set(gca, 'XTickLabel', {'恒温器', '功率跟随'});
legend('总油耗 (L)', '百公里油耗 (L/100km)', 'Location', 'northwest');
title('油耗对比');
