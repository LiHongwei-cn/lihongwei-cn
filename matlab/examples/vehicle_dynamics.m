%% 电动汽车纵向动力学仿真
% 功能：仿真电动汽车在不同车速下的阻力平衡、能耗和续航
% 兼容版本：MATLAB R2016b

clc; close all;

%% 参数集中声明
params.m = 1600;              % 整车质量 [kg]
params.Cd = 0.28;             % 风阻系数
params.Af = 2.1;              % 迎风面积 [m^2]
params.rho = 1.225;           % 空气密度 [kg/m^3]
params.f = 0.012;             % 滚动阻力系数
params.g = 9.81;              % 重力加速度 [m/s^2]
params.rw = 0.33;             % 车轮半径 [m]
params.T_max = 250;           % 电机最大转矩 [Nm]
params.n_base = 3800;         % 电机基速 [rpm]
params.eta_motor = 0.90;      % 电机效率
params.eta_regen = 0.60;      % 回馈制动效率
params.V_bat = 350;           % 电池电压 [V]
params.Q_bat = 100;           % 电池容量 [Ah]
params.SOC_init = 0.95;       % 初始SOC

%% 工况定义
v_target_kmh = 0:1:200;                        % 目标车速 [km/h]
v_target = v_target_kmh / 3.6;                  % 目标车速 [m/s]
nn = length(v_target);

%% 预分配
F_aero = zeros(1, nn);
F_roll = zeros(1, nn);
F_total = zeros(1, nn);
P_motor = zeros(1, nn);
P_bat = zeros(1, nn);

%% 计算各车速下的阻力和功率
for i = 1:nn
    v = v_target(i);
    F_aero(i) = 0.5 * params.rho * params.Cd * params.Af * v^2;   % 空气阻力 [N]
    F_roll(i) = params.f * params.m * params.g;                     % 滚动阻力 [N]
    F_total(i) = F_aero(i) + F_roll(i);                            % 总阻力 [N]
    P_motor(i) = F_total(i) * v;                                    % 电机功率 [W]
    P_bat(i) = P_motor(i) / params.eta_motor;                       % 电池功率 [W]
end

%% 计算最高车速（阻力功率 = 电机最大功率）
P_max = params.T_max * params.n_base * pi / 30;   % 电机最大功率 [W]
[~, idx_max] = min(abs(P_bat - P_max));
v_max_kmh = v_target_kmh(idx_max);

%% 计算等速巡航能耗和续航
v_cruise_kmh = 60;                                 % 巡航车速 [km/h]
v_cruise = v_cruise_kmh / 3.6;                     % [m/s]
F_cruise = 0.5 * params.rho * params.Cd * params.Af * v_cruise^2 ...
         + params.f * params.m * params.g;         % 巡航总阻力 [N]
P_cruise = F_cruise * v_cruise;                     % 巡航功率 [W]
E_100km = P_cruise * (100000 / v_cruise) / 3600;   % 百公里能耗 [Wh]
range_km = params.V_bat * params.Q_bat * params.SOC_init * 1000 ...
         / E_100km;                                 % 续航里程 [km]

%% 绘图
figure('Position', [100 100 900 650]);

subplot(2,2,1);
plot(v_target_kmh, F_aero, 'r-', v_target_kmh, F_roll, 'b--', ...
     v_target_kmh, F_total, 'k-', 'LineWidth', 1.5);
xlabel('车速 (km/h)'); ylabel('阻力 (N)');
legend('空气阻力', '滚动阻力', '总阻力');
grid on; title('行驶阻力');

subplot(2,2,2);
plot(v_target_kmh, P_motor/1000, 'b-', v_target_kmh, P_bat/1000, 'r--', 'LineWidth', 1.5);
xlabel('车速 (km/h)'); ylabel('功率 (kW)');
legend('电机输出', '电池消耗');
grid on; title('功率需求');

subplot(2,2,3);
plot(v_target_kmh, E_100km*ones(1,nn)/1000, 'b-', 'LineWidth', 1.5);
xlabel('车速 (km/h)'); ylabel('能耗 (kWh/100km)');
grid on; title('等速巡航能耗');

subplot(2,2,4);
bar([v_max_kmh, range_km]);
set(gca, 'XTickLabel', {'最高车速', '续航里程'});
ylabel('数值'); grid on; title('关键指标');

%% 输出结果
fprintf('===== 电动汽车纵向动力学仿真 =====\n');
fprintf('最高车速: %.0f km/h\n', v_max_kmh);
fprintf('60km/h 等速续航里程: %.0f km\n', range_km);
fprintf('60km/h 百公里能耗: %.2f kWh\n', E_100km/1000);
