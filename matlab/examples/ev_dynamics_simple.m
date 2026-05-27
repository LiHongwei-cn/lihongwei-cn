%% 简单电动汽车动力学仿真
% 功能：完整 EV 模型——电机 + 电池 + 能耗 + SOC + 续航
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
params.eta_motor = 0.90;      % 电机驱动效率
params.eta_regen = 0.60;      % 回馈制动效率
params.V_bat = 350;           % 电池电压 [V]
params.Q_bat = 100;           % 电池容量 [Ah]
params.SOC_init = 0.95;       % 初始SOC

%% 工况定义
dt = 0.05;                    % 仿真步长 [s]
T = 60;                       % 仿真时长 [s]
t = 0:dt:T;                   % 时间向量
n = length(t);
V_CRUISE = 80/3.6;            % 巡航车速 [m/s]
T_ACCEL = 15;                 % 加速时间 [s]
T_CRUISE = 45;                % 巡航时间 [s]

% 目标车速曲线：加速 -> 巡航 -> 减速
v_target = V_CRUISE*min(t/T_ACCEL,1).*(t<=T_CRUISE) ...
         + V_CRUISE*max(1-(t-T_CRUISE)/T_ACCEL,0).*(t>T_CRUISE);

%% 状态变量初始化
v = zeros(1,n); s = zeros(1,n); T_m = zeros(1,n);
P_m = zeros(1,n); E_cons = zeros(1,n); SOC = params.SOC_init*ones(1,n);

%% 仿真主循环
for i = 2:n
    % 加速度限制
    a_req = max(-3, min(3, 2.0*(v_target(i-1)-v(i-1))));

    % 行驶阻力
    Fr = 0.5*params.rho*params.Cd*params.Af*v(i-1)^2 + params.f*params.m*params.g;

    % 电机转矩（恒转矩区 + 恒功率区）
    mrpm = v(i-1)*60/(2*pi*params.rw);
    Ta = params.T_max * min(1, params.n_base/max(mrpm,1));

    % 实际驱动转矩
    Tw = max(-Ta*0.5, min(Ta, (params.m*a_req+Fr)*params.rw));
    T_m(i) = Tw;

    % 车速更新（前向欧拉法）
    v(i) = max(0, v(i-1) + (Tw/params.rw - Fr)/params.m*dt);

    % 行驶距离
    s(i) = s(i-1) + v(i)*dt;

    % 电机功率
    P_m(i) = Tw*(mrpm*2*pi/60);

    % 电池功率（区分驱动和回馈）
    Pb = P_m(i) / (params.eta_motor*(P_m(i)>=0) + params.eta_regen*(P_m(i)<0));
    E_cons(i) = E_cons(i-1) + Pb*dt/3600;
    SOC(i) = SOC(i-1) - Pb*dt/(params.V_bat*params.Q_bat*3600);
end

%% 绘图
figure('Position', [100 100 900 650]);

subplot(3,2,1);
plot(t, v*3.6, 'b-', t, v_target*3.6, 'r--', 'LineWidth', 1.5);
ylabel('速度 (km/h)'); grid on; legend('实际', '目标'); title('速度跟踪');

subplot(3,2,2);
plot(t, T_m, 'g-', 'LineWidth', 1.5);
ylabel('转矩 (Nm)'); grid on; title('电机转矩');

subplot(3,2,3);
plot(t, s/1000, 'b-', 'LineWidth', 1.5);
ylabel('距离 (km)'); grid on; title('累计行驶距离');

subplot(3,2,4);
plot(t, P_m/1000, 'r-', 'LineWidth', 1.5);
ylabel('功率 (kW)'); grid on; title('电机功率');

subplot(3,2,5);
plot(t, E_cons, 'm-', 'LineWidth', 1.5);
xlabel('时间 (s)'); ylabel('能耗 (Wh)'); grid on; title('累计能耗');

subplot(3,2,6);
plot(t, SOC*100, 'b-', 'LineWidth', 1.5);
xlabel('时间 (s)'); ylabel('SOC (%)'); grid on; title('电池SOC');

%% 输出结果
fprintf('===== 简单电动汽车动力学仿真结果 =====\n');
fprintf('最高车速: %.1f km/h\n', max(v)*3.6);
fprintf('行驶距离: %.2f km\n', s(end)/1000);
fprintf('能耗: %.1f kWh/100km\n', E_cons(end)/(s(end)/1000)/10);
fprintf('剩余SOC: %.1f%%\n', SOC(end)*100);
fprintf('续航里程: %.0f km\n', s(end)*params.SOC_init/(params.SOC_init-SOC(end)+0.001));
