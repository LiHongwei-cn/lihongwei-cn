%% 电池 SOC 估算 — 扩展卡尔曼滤波 (EKF)
% MATLAB R2016b 兼容
% 一阶 RC 等效电路模型 + EKF 状态估计
% 演示：真实 SOC vs 安时积分 vs EKF 估计

clc; close all;

% 自动添加工具路径
scriptPath = fileparts(mfilename('fullpath'));
addpath(fullfile(scriptPath, '..', 'utils'));

%% 电池参数（锂离子电池 3.7V 标称）
Q_nom  = 50;        % 额定容量 [Ah]
V_oc   = @(soc) 3.2 + 0.9*soc + 0.1*soc.^2 - 0.05*soc.^3;  % OCV-SOC 曲线
R0     = 0.01;      % 欧姆内阻 [Ohm]
R1     = 0.015;     % 极化内阻 [Ohm]
C1     = 2000;      % 极化电容 [F]
tau1   = R1 * C1;   % 时间常数 [s]

%% 仿真设置
dt = 1.0;           % 采样时间 [s]
T  = 2000;          % 总时长 [s]
t  = 0:dt:T;
n  = length(t);

%% 生成负载电流（模拟 WLTC-like 工况）
I_base = 2.5 + 2*sin(2*pi*t/200) + 1.5*sin(2*pi*t/80);
I_load = I_base + 0.5*randn(size(t));   % 加测量噪声

%% 真实状态（参考值）
soc_true = zeros(1, n);
v1_true  = zeros(1, n);
soc = 0.9;  % 初始 SOC
v1  = 0;

for k = 1:n
    soc_true(k) = soc;
    v1_true(k)  = v1;
    v1 = v1 + dt * (-v1/tau1 + I_load(k)/C1);
    soc = soc - dt * I_load(k) / (Q_nom * 3600);
end

%% 测量电压（OCV - R0*I - V1 + 噪声）
R_meas = 0.002;     % 电压测量噪声标准差
V_term = V_oc(soc_true) - R0 * I_load - v1_true + R_meas*randn(size(t));

%% 安时积分法（开环，有漂移）
soc_ah = zeros(1, n);
soc_ah(1) = 0.88;   % 初始估计有偏差
for k = 2:n
    soc_ah(k) = soc_ah(k-1) - dt * I_load(k-1) / (Q_nom * 3600);
end

%% EKF 估计
soc_ekf = zeros(1, n);
soc_ekf(1) = 0.88;

x = [0.88; 0];
P = diag([0.01^2, 0.001^2]);
Q_w = diag([1e-6, 1e-6]);
R_v = R_meas^2;

for k = 2:n
    Ik = I_load(k-1);
    dt_eff = dt;

    soc_pred = x(1) - dt_eff * Ik / (Q_nom * 3600);
    v1_pred  = x(2) + dt_eff * (-x(2)/tau1 + Ik/C1);
    x_pred = [soc_pred; v1_pred];

    A = [1, 0; 0, 1 - dt_eff/tau1];
    P_pred = A * P * A' + Q_w;

    V_pred = V_oc(soc_pred) - R0 * Ik - v1_pred;

    dOCV = 0.9 + 0.2*soc_pred - 0.15*soc_pred^2;
    C = [dOCV, -1];

    K = P_pred * C' / (C * P_pred * C' + R_v);

    x = x_pred + K * (V_term(k) - V_pred);
    P = (eye(2) - K * C) * P_pred;

    soc_ekf(k) = x(1);
end

%% 绘图
figure('Position', [100 100, 850, 600]);

subplot(3,1,1);
plot(t, I_load, 'b-', 'LineWidth', 1);
xlabel('时间 (s)'); ylabel('电流 (A)');
grid on; title('负载电流');

subplot(3,1,2);
plot(t, V_term, 'b-', 'LineWidth', 1);
xlabel('时间 (s)'); ylabel('端电压 (V)');
grid on; title('电池端电压');

subplot(3,1,3);
plot(t, soc_true*100, 'k-', 'LineWidth', 1.5); hold on;
plot(t, soc_ah*100, 'r--', 'LineWidth', 1.2);
plot(t, soc_ekf*100, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('SOC (%)');
legend('真实值', '安时积分', 'EKF', 'Location', 'best');
grid on; title('SOC 估算对比');

%% 误差统计
err_ah  = soc_ah - soc_true;
err_ekf = soc_ekf - soc_true;

fprintf('===== SOC 估算结果 =====\n');
fprintf('安时积分 RMS 误差: %.3f %%\n', rms_calculation(err_ah)*100);
fprintf('EKF RMS 误差: %.3f %%\n', rms_calculation(err_ekf)*100);
fprintf('安时积分终值误差: %.3f %%\n', abs(soc_ah(end)-soc_true(end))*100);
fprintf('EKF 终值误差: %.3f %%\n', abs(soc_ekf(end)-soc_true(end))*100);
