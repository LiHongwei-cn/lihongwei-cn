%% 行驶工况能耗分析
% 功能：WLTC 类工况下的能耗、SOC、回馈制动分析
% 兼容版本：MATLAB R2016b

clc; close all;

%% 工况定义（WLTC 风格分段加速/巡航/减速）
dt = 1;                      % 仿真步长 [s]
T = 1800;                    % 仿真时长 [s]
t = (0:dt:T)';               % 时间向量

% 构建车速曲线 [km/h]
v_kmh = zeros(size(t));
v_kmh(t<=300) = 50*(t(t<=300)/300).^0.5;
v_kmh(t>300 & t<=800) = 50 + 30*(t(t>300 & t<=800)-300)/500;
v_kmh(t>800 & t<=1300) = 80 + 40*sin(pi*(t(t>800 & t<=1300)-800)/1000);
v_kmh(t>1300 & t<=1600) = 120 + 10*(t(t>1300 & t<=1600)-1300)/300;
v_kmh(t>1600) = max(130 - 40*(t(t>1600)-1600)/200, 0);
v_ms = v_kmh/3.6;            % [m/s]

%% 车辆参数
m = 1800;                    % 整车质量 [kg]
Cd = 0.30;                   % 风阻系数
Af = 2.2;                    % 迎风面积 [m^2]
rho = 1.225;                 % 空气密度 [kg/m^3]
f = 0.012;                   % 滚动阻力系数
g = 9.81;                    % 重力加速度 [m/s^2]
rw = 0.33;                   % 车轮半径 [m]
T_max = 280;                 % 电机最大转矩 [Nm]
n_base = 3500;               % 电机基速 [rpm]
eta_m = 0.92;                % 电机驱动效率
eta_r = 0.85;                % 回馈制动效率
Q_bat = 60;                  % 电池容量 [Ah]
V_bat = 380;                 % 电池电压 [V]
SOC_0 = 0.95;                % 初始SOC

%% 仿真计算
nn = length(t);
a = zeros(nn,1); P_mot = zeros(nn,1); P_bat = zeros(nn,1);
E_con = zeros(nn,1); SOC = SOC_0*ones(nn,1);

for i = 2:nn
    a(i) = (v_ms(i)-v_ms(i-1))/dt;                             % 加速度 [m/s^2]
    F = 0.5*rho*Cd*Af*v_ms(i)^2 + f*m*g + m*a(i);             % 总阻力 [N]
    mrpm = v_ms(i)/rw*30/pi;                                    % 电机转速 [rpm]
    Ta = T_max * min(1, n_base/max(mrpm,1));                    % 电机转矩 [Nm]
    P_mot(i) = F*rw * v_ms(i)/rw;                               % 电机功率 [W]
    P_bat(i) = P_mot(i)/(eta_m*(P_mot(i)>=0) + eta_r*(P_mot(i)<0));   % 电池功率 [W]
    E_con(i) = E_con(i-1) + P_bat(i)*dt/3600;                  % 累计能耗 [Wh]
    SOC(i) = SOC(i-1) - P_bat(i)*dt/(V_bat*Q_bat*3600);        % SOC
end

drv = P_mot>0; reg = P_mot<0;

%% 绘图
figure('Position', [50 50 950 700]);

subplot(3,2,1);
plot(t/60, v_kmh, 'b-', 'LineWidth', 1.2);
xlabel('Time (min)'); ylabel('Speed (km/h)');
grid on; title('Driving Cycle');

subplot(3,2,2);
yyaxis left; plot(t/60, P_mot/1000, 'b-'); ylabel('Power (kW)');
yyaxis right; plot(t/60, E_con/1000, 'r-', 'LineWidth', 1.5); ylabel('Energy (kWh)');
xlabel('Time (min)'); grid on; title('Power & Energy');

subplot(3,2,3);
histogram(P_mot(drv)/1000, 30, 'FaceColor', 'b'); hold on;
lgd = {'Drive'};
if any(reg), histogram(abs(P_mot(reg))/1000, 30, 'FaceColor', 'g'); lgd{end+1} = 'Regen'; end
xlabel('Power (kW)'); ylabel('Count'); legend(lgd); grid on; title('Power Distribution');

subplot(3,2,4);
plot(t/60, a, 'r-', 'LineWidth', 1);
xlabel('Time (min)'); ylabel('Accel (m/s^2)');
grid on; title('Acceleration');

subplot(3,2,5);
plot(t/60, SOC*100, 'b-', 'LineWidth', 1.2);
xlabel('Time (min)'); ylabel('SOC (%)');
grid on; title('Battery SOC');

subplot(3,2,6);
E_drv = sum(P_bat(drv)*dt/3600); E_reg = sum(abs(P_bat(reg))*dt/3600);
if E_reg>0, pie([E_drv, E_reg], {'Drive (Wh)', 'Regen (Wh)'}); end
title('Energy Distribution');

%% 输出结果
dist = sum(v_ms*dt)/1000;
fprintf('===== Driving Cycle Energy Analysis =====\n');
fprintf('Distance: %.2f km\n', dist);
fprintf('Energy: %.1f kWh/100km\n', E_con(end)/dist*100/1000);
fprintf('SOC change: %.1f%%\n', (SOC_0-SOC(end))*100);
fprintf('Range: %.0f km\n', dist*SOC_0/(SOC_0-SOC(end)+0.001));
fprintf('Regen energy ratio: %.1f%%\n', sum(abs(P_bat(reg)))/max(sum(abs(P_bat)),1e-6)*100);
