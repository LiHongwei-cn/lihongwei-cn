%% 车辆纵向动力学仿真
% MATLAB R2016b 兼容
% 演示：加速-匀速-制动工况
% 可扩展为 CarSim 输入的前处理

clear; clc; close all;

%% 车辆参数
param.m   = 1500;      % 整车质量 [kg]
param.Cd  = 0.32;      % 风阻系数
param.Af  = 2.2;       % 迎风面积 [m^2]
param.rho = 1.225;     % 空气密度 [kg/m^3]
param.f   = 0.015;     % 滚动阻力系数
param.g   = 9.81;      % 重力加速度 [m/s^2]
param.rw  = 0.31;      % 车轮半径 [m]
param.eta = 0.92;      % 传动效率

%% 仿真设置
dt = 0.01;             % 步长 [s]
T  = 30;               % 总时长 [s]
t  = 0:dt:T;           % 时间向量
n  = length(t);

%% 驱动/制动力输入 (N) —— 向量化
% 0-10s 加速，10-20s 匀速，20-30s 制动
V_CRUISE = 30 / 3.6;                            % 巡航速度 [m/s]
F_CRUISE = calcResist(V_CRUISE, param);          % 保持匀速所需驱动力 [N]
F_ACCEL_MAX = 3000;                              % 最大加速力 [N]
F_BRAKE = 2000;                                  % 制动力 [N]

F_drive = F_ACCEL_MAX * (t / 10) .* (t <= 10) ...
        + F_CRUISE .* (t > 10 & t <= 20);
F_brake = F_BRAKE .* (t > 20);

%% 仿真循环（前向欧拉法）
v = zeros(1, n);       % 速度 [m/s]
a = zeros(1, n);       % 加速度 [m/s^2]
s = zeros(1, n);       % 位移 [m]

for i = 2:n
    F_resist = calcResist(v(i-1), param);
    F_net = F_drive(i-1) - F_resist - F_brake(i-1);
    a(i) = F_net / param.m;
    v(i) = v(i-1) + a(i) * dt;
    v(i) = max(v(i), 0);  % 不倒车
    s(i) = s(i-1) + v(i) * dt;
end

%% 绘图
figure('Position', [100 100 800 600]);

subplot(3,1,1);
plot(t, v*3.6, 'b-', 'LineWidth', 1.5);
ylabel('速度 (km/h)');
grid on; title('车辆纵向动力学仿真');
legend('车速');

subplot(3,1,2);
plot(t, a, 'r-', 'LineWidth', 1.5);
ylabel('加速度 (m/s^2)');
grid on;

subplot(3,1,3);
plot(t, s, 'g-', 'LineWidth', 1.5);
xlabel('时间 (s)');
ylabel('位移 (m)');
grid on;

%% 输出结果
fprintf('===== 仿真结果 =====\n');
fprintf('最高车速: %.1f km/h\n', max(v)*3.6);
fprintf('最大加速度: %.2f m/s^2\n', max(a));
fprintf('总行驶距离: %.1f m\n', s(end));

%% 辅助函数
function Fresist = calcResist(v, param)
    % 计算总阻力（空气阻力 + 滚动阻力）
    % v - 车速 [m/s]
    Fair = 0.5 * param.rho * param.Cd * param.Af * v^2;
    Froll = param.f * param.m * param.g;
    Fresist = Fair + Froll;
end
