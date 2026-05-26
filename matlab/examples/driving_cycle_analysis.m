%% 工况能耗分析
% MATLAB R2016b 兼容

clc; close all;

dt = 1; T = 1800; t = (0:dt:T)';
v_kmh = zeros(size(t));
v_kmh(t<=300) = 50*(t(t<=300)/300).^0.5;
v_kmh(t>300 & t<=800) = 50 + 30*(t(t>300 & t<=800)-300)/500;
v_kmh(t>800 & t<=1300) = 80 + 40*sin(pi*(t(t>800 & t<=1300)-800)/1000);
v_kmh(t>1300 & t<=1600) = 120 + 10*(t(t>1300 & t<=1600)-1300)/300;
v_kmh(t>1600) = max(130 - 40*(t(t>1600)-1600)/200, 0);
v_ms = v_kmh/3.6;

m = 1800; Cd = 0.30; Af = 2.2; rho = 1.225; f = 0.012; g = 9.81; rw = 0.33;
T_max = 280; n_base = 3500; eta_m = 0.92; eta_r = 0.85;
Q_bat = 60; V_bat = 380; SOC_0 = 0.95;

nn = length(t);
a = zeros(nn,1); P_mot = zeros(nn,1); P_bat = zeros(nn,1);
E_con = zeros(nn,1); SOC = SOC_0*ones(nn,1);

for i = 2:nn
    a(i) = (v_ms(i)-v_ms(i-1))/dt;
    F = 0.5*rho*Cd*Af*v_ms(i)^2 + f*m*g + m*a(i);
    mrpm = v_ms(i)/rw*30/pi;
    Ta = T_max * min(1, n_base/max(mrpm,1));
    P_mot(i) = F*rw * v_ms(i)/rw;
    P_bat(i) = P_mot(i)/(eta_m*(P_mot(i)>=0) + eta_r*(P_mot(i)<0));
    E_con(i) = E_con(i-1) + P_bat(i)*dt/3600;
    SOC(i) = SOC(i-1) - P_bat(i)*dt/(V_bat*Q_bat*3600);
end

drv = P_mot>0; reg = P_mot<0;

figure('Position', [50 50 950 700]);
subplot(3,2,1); plot(t/60, v_kmh, 'b-', 'LineWidth', 1.2);
xlabel('时间 (min)'); ylabel('车速 (km/h)'); grid on; title('行驶工况');
subplot(3,2,2); yyaxis left; plot(t/60, P_mot/1000, 'b-'); ylabel('功率 (kW)');
yyaxis right; plot(t/60, E_con/1000, 'r-', 'LineWidth', 1.5); ylabel('能量 (kWh)');
xlabel('时间 (min)'); grid on; title('功率与能耗');
subplot(3,2,3); histogram(P_mot(drv)/1000, 30, 'FaceColor', 'b'); hold on;
lgd = {'驱动'};
if any(reg), histogram(abs(P_mot(reg))/1000, 30, 'FaceColor', 'g'); lgd{end+1} = '再生'; end
xlabel('功率 (kW)'); ylabel('频次'); legend(lgd); grid on; title('功率分布');
subplot(3,2,4); plot(t/60, a, 'r-', 'LineWidth', 1);
xlabel('时间 (min)'); ylabel('加速度 (m/s^2)'); grid on; title('加速度');
subplot(3,2,5); plot(t/60, SOC*100, 'b-', 'LineWidth', 1.2);
xlabel('时间 (min)'); ylabel('SOC (%)'); grid on; title('电池SOC');
subplot(3,2,6);
E_drv = sum(P_bat(drv)*dt/3600); E_reg = sum(abs(P_bat(reg))*dt/3600);
if E_reg>0, pie([E_drv, E_reg], {'驱动 (Wh)','再生 (Wh)'}); end
title('能量流向');

dist = sum(v_ms*dt)/1000;
fprintf('===== 工况能耗分析 =====\n');
fprintf('行驶距离: %.2f km\n', dist);
fprintf('能耗: %.1f kWh/100km\n', E_con(end)/dist*100/1000);
fprintf('SOC消耗: %.1f%%\n', (SOC_0-SOC(end))*100);
fprintf('续航里程: %.0f km\n', dist*SOC_0/(SOC_0-SOC(end)+0.001));
fprintf('再生比例: %.1f%%\n', sum(abs(P_bat(reg)))/max(sum(abs(P_bat)),1e-6)*100);
