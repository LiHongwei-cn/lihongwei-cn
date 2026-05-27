%% 混合动力能量管理策略对比
% 功能：恒温器策略 vs 功率跟随策略的油耗、SOC、发电次数对比
% 兼容版本：MATLAB R2016b

clc; close all;

%% 车辆参数
m = 2000;                    % 整车质量 [kg]
Cd = 0.32;                   % 风阻系数
Af = 2.3;                    % 迎风面积 [m^2]
rho = 1.225;                 % 空气密度 [kg/m^3]
f = 0.012;                   % 滚动阻力系数
g = 9.81;                    % 重力加速度 [m/s^2]
rw = 0.33;                   % 车轮半径 [m]

%% 动力系统参数
P_mot_max = 120000;          % 电机最大功率 [W]
P_gen_max = 60000;           % 发电机最大功率 [W]
Q_bat = 40;                  % 电池容量 [Ah]
V_bat = 350;                 % 电池电压 [V]
SOC_min = 0.25;              % SOC下限
SOC_max = 0.85;              % SOC上限
SOC_init = 0.50;             % 初始SOC

%% 工况定义
dt = 1.0;                    % 仿真步长 [s]
Tt = 2400;                   % 仿真时长 [s]
t = (0:dt:Tt)';              % 时间向量
nn = length(t);

% 需求功率工况
v_ms = max(15 + 10*sin(2*pi*t/600) + 5*sin(2*pi*t/200) + 3*sin(2*pi*t/80), 0);

%% 计算需求功率
P_dem = zeros(nn,1);
for i = 1:nn
    ai = (i>1)*(v_ms(i)-v_ms(max(i-1,1)))/dt;
    P_dem(i) = max((0.5*rho*Cd*Af*v_ms(i)^2 + f*m*g + m*ai)*rw * v_ms(i)/rw, -P_mot_max);
end

%% 策略1：恒温器策略
P_gen1 = zeros(nn,1); SOC1 = SOC_init*ones(nn,1);

%% 策略2：功率跟随策略
P_gen2 = zeros(nn,1); SOC2 = SOC_init*ones(nn,1);
SOC_c = 0.55;                % 目标SOC中心
SOC_b = 0.05;                % SOC死区宽度

%% 仿真主循环
for i = 2:nn
    % 策略1：恒温器——SOC低于下限时开启发电机，高于上限时关闭
    if SOC1(i-1)<SOC_min, P_gen1(i)=P_gen_max;
    elseif SOC1(i-1)>SOC_max, P_gen1(i)=0;
    else, P_gen1(i)=P_gen1(i-1); end
    SOC1(i) = SOC1(i-1) + (P_gen1(i)-P_dem(i-1))*dt/(V_bat*Q_bat*3600);
    SOC1(i) = max(0.05, min(0.95, SOC1(i)));

    % 策略2：功率跟随——根据SOC和需求功率动态调整发电功率
    if SOC2(i-1)<SOC_c-SOC_b, Ps = P_dem(i-1)+0.3*P_gen_max;
    elseif SOC2(i-1)>SOC_c+SOC_b, Ps = max(0, P_dem(i-1)*0.5);
    else, Ps = P_dem(i-1); end
    Ps = max(0, min(Ps, P_gen_max));
    if Ps>0 && Ps<15000, Ps = 15000; end    % 最小发电功率阈值
    P_gen2(i) = Ps;
    SOC2(i) = SOC2(i-1) + (P_gen2(i)-P_dem(i-1))*dt/(V_bat*Q_bat*3600);
    SOC2(i) = max(0.05, min(0.95, SOC2(i)));
end

%% 计算油耗
fuel_rate = 0.23;            % 发电机燃油消耗率 [L/kWh]
f1 = sum(P_gen1)*dt/3600/1000*fuel_rate;
f2 = sum(P_gen2)*dt/3600/1000*fuel_rate;
dist = sum(v_ms*dt)/1000;

%% 输出结果
fprintf('===== 混合动力能量管理策略对比 =====\n');
fprintf('行驶距离: %.1f km\n', dist);
fprintf('%-18s %-15s %-15s\n', '指标', '恒温器策略', '功率跟随策略');
fprintf('%-18s %-15.1f %-15.1f\n', '油耗/100km (L)', f1/dist*100, f2/dist*100);
fprintf('%-18s %-15.2f %-15.2f\n', '终止SOC', SOC1(end), SOC2(end));
fprintf('%-18s %-15d %-15d\n', '发电次数', sum(diff(P_gen1>0)~=0), sum(diff(P_gen2>0)~=0));

%% 绘图
figure('Position', [50 50 1000 700]);

subplot(4,2,1);
plot(t/60, v_ms*3.6, 'b-');
xlabel('时间 (min)'); ylabel('车速 (km/h)');
grid on; title('行驶工况');

subplot(4,2,2);
plot(t/60, P_dem/1000, 'b-');
xlabel('时间 (min)'); ylabel('功率 (kW)');
grid on; title('需求功率');

subplot(4,2,3);
yyaxis left; plot(t/60, SOC1*100, 'b-'); ylabel('SOC (%)');
yyaxis right; plot(t/60, P_gen1/1000, 'r-'); ylabel('发电机功率 (kW)');
xlabel('时间 (min)'); grid on; title('恒温器策略');

subplot(4,2,4);
yyaxis left; plot(t/60, SOC2*100, 'b-'); ylabel('SOC (%)');
yyaxis right; plot(t/60, P_gen2/1000, 'r-'); ylabel('发电机功率 (kW)');
xlabel('时间 (min)'); grid on; title('功率跟随策略');

subplot(4,2,5);
plot(t/60, cumsum(P_gen1)*dt/3600/1000, 'r-', t/60, cumsum(P_gen2)*dt/3600/1000, 'b-');
xlabel('时间 (min)'); ylabel('累计发电量 (kWh)');
legend('恒温器', '功率跟随'); grid on; title('累计发电量');

subplot(4,2,6);
scatter(P_dem/1000, P_gen1/1000, 3, 'r'); hold on;
scatter(P_dem/1000, P_gen2/1000, 3, 'b');
xlabel('需求功率 (kW)'); ylabel('发电机功率 (kW)');
legend('恒温器', '功率跟随'); grid on; title('功率分布');

subplot(4,2,7:8);
bar([f1, f2; f1/dist*100, f2/dist*100]');
set(gca, 'XTickLabel', {'恒温器', '功率跟随'});
legend('总油耗 (L)', '百公里油耗'); title('油耗对比');
