%% 电池SOC估算 - 扩展卡尔曼滤波
% 功能：安时法 vs EKF 对比估算电池SOC
% 兼容版本：MATLAB R2016b

clc; close all;
scriptPath = fileparts(mfilename('fullpath'));
addpath(fullfile(scriptPath, '..', 'utils'));

%% 电池参数
Q_nom = 50;                  % 标称容量 [Ah]
R0 = 0.01;                   % 欧姆内阻 [Ohm]
R1 = 0.015;                  % 极化内阻 [Ohm]
C1 = 2000;                   % 极化电容 [F]
tau1 = R1*C1;                % 极化时间常数 [s]

% 开路电压-SOC曲线
V_oc = @(soc) 3.2 + 0.9*soc + 0.1*soc.^2 - 0.05*soc.^3;

%% 仿真参数
dt = 1.0;                    % 仿真步长 [s]
T = 2000;                    % 仿真时长 [s]
t = 0:dt:T;                  % 时间向量
n = length(t);

%% 生成负载电流（含多频扰动）
I_load = 2.5 + 2*sin(2*pi*t/200) + 1.5*sin(2*pi*t/80) + 0.5*randn(size(t));

%% 真值仿真（一阶RC等效电路模型）
soc_true = zeros(1,n); v1_true = zeros(1,n);
soc = 0.9; v1 = 0;
for k = 1:n
    soc_true(k)=soc; v1_true(k)=v1;
    v1 = v1 + dt*(-v1/tau1 + I_load(k)/C1);
    soc = soc - dt*I_load(k)/(Q_nom*3600);
end

% 端电压 = OCV - 欧姆压降 - 极化压降 + 测量噪声
V_term = V_oc(soc_true) - R0*I_load - v1_true + 0.002*randn(size(t));

%% 安时法估算
soc_ah = zeros(1,n); soc_ah(1) = 0.88;
for k = 2:n
    soc_ah(k) = soc_ah(k-1) - dt*I_load(k-1)/(Q_nom*3600);
end

%% EKF 估算
soc_ekf = zeros(1,n); soc_ekf(1) = 0.88;
x = [0.88; 0];                              % 状态：[SOC, 极化电压]
P = diag([0.01^2, 0.001^2]);                % 初始协方差
Q_w = diag([1e-6, 1e-6]);                   % 过程噪声
R_v = 0.002^2;                              % 观测噪声

for k = 2:n
    Ik = I_load(k-1);

    % 预测
    sp = x(1) - dt*Ik/(Q_nom*3600);
    v1p = x(2) + dt*(-x(2)/tau1 + Ik/C1);
    A = [1, 0; 0, 1-dt/tau1];
    Pp = A*P*A' + Q_w;

    % 观测预测
    Vp = V_oc(sp) - R0*Ik - v1p;
    dOCV = 0.9 + 0.2*sp - 0.15*sp^2;
    C = [dOCV, -1];

    % 卡尔曼增益
    K = Pp*C'/(C*Pp*C' + R_v);

    % 状态更新
    x = [sp; v1p] + K*(V_term(k) - Vp);
    P = (eye(2) - K*C)*Pp;
    soc_ekf(k) = x(1);
end

%% 绘图
figure('Position', [100 100 850 600]);

subplot(3,1,1);
plot(t, I_load, 'b-', 'LineWidth', 1);
xlabel('时间 (s)'); ylabel('电流 (A)');
grid on; title('负载电流');

subplot(3,1,2);
plot(t, V_term, 'b-', 'LineWidth', 1);
xlabel('时间 (s)'); ylabel('电压 (V)');
grid on; title('端电压');

subplot(3,1,3);
plot(t, soc_true*100, 'k-', t, soc_ah*100, 'r--', t, soc_ekf*100, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('SOC (%)');
legend('真实值', '安时法', 'EKF'); grid on; title('SOC 估算对比');

%% 输出结果
err_ah = soc_ah - soc_true;
err_ekf = soc_ekf - soc_true;
fprintf('===== SOC 估算结果 =====\n');
fprintf('安时法 RMS误差: %.3f%%\n', rms_calculation(err_ah)*100);
fprintf('EKF RMS误差: %.3f%%\n', rms_calculation(err_ekf)*100);
fprintf('安时法终值误差: %.3f%%\n', abs(soc_ah(end)-soc_true(end))*100);
fprintf('EKF终值误差: %.3f%%\n', abs(soc_ekf(end)-soc_true(end))*100);
