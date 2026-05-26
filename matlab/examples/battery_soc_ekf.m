%% 电池SOC估计 - 扩展卡尔曼滤波
% MATLAB R2016b 兼容

clc; close all;
scriptPath = fileparts(mfilename('fullpath'));
addpath(fullfile(scriptPath, '..', 'utils'));

Q_nom = 50; R0 = 0.01; R1 = 0.015; C1 = 2000; tau1 = R1*C1;
V_oc = @(soc) 3.2 + 0.9*soc + 0.1*soc.^2 - 0.05*soc.^3;

dt = 1.0; T = 2000; t = 0:dt:T; n = length(t);
I_load = 2.5 + 2*sin(2*pi*t/200) + 1.5*sin(2*pi*t/80) + 0.5*randn(size(t));

soc_true = zeros(1,n); v1_true = zeros(1,n);
soc = 0.9; v1 = 0;
for k = 1:n
    soc_true(k)=soc; v1_true(k)=v1;
    v1 = v1 + dt*(-v1/tau1 + I_load(k)/C1);
    soc = soc - dt*I_load(k)/(Q_nom*3600);
end

V_term = V_oc(soc_true) - R0*I_load - v1_true + 0.002*randn(size(t));

soc_ah = zeros(1,n); soc_ah(1) = 0.88;
for k = 2:n
    soc_ah(k) = soc_ah(k-1) - dt*I_load(k-1)/(Q_nom*3600);
end

soc_ekf = zeros(1,n); soc_ekf(1) = 0.88;
x = [0.88; 0]; P = diag([0.01^2, 0.001^2]);
Q_w = diag([1e-6, 1e-6]); R_v = 0.002^2;

for k = 2:n
    Ik = I_load(k-1);
    sp = x(1) - dt*Ik/(Q_nom*3600);
    v1p = x(2) + dt*(-x(2)/tau1 + Ik/C1);
    A = [1, 0; 0, 1-dt/tau1];
    Pp = A*P*A' + Q_w;
    Vp = V_oc(sp) - R0*Ik - v1p;
    dOCV = 0.9 + 0.2*sp - 0.15*sp^2;
    C = [dOCV, -1];
    K = Pp*C'/(C*Pp*C' + R_v);
    x = [sp; v1p] + K*(V_term(k) - Vp);
    P = (eye(2) - K*C)*Pp;
    soc_ekf(k) = x(1);
end

figure('Position', [100 100 850 600]);
subplot(3,1,1); plot(t, I_load, 'b-', 'LineWidth', 1);
xlabel('时间 (s)'); ylabel('电流 (A)'); grid on; title('负载电流');
subplot(3,1,2); plot(t, V_term, 'b-', 'LineWidth', 1);
xlabel('时间 (s)'); ylabel('电压 (V)'); grid on; title('端电压');
subplot(3,1,3);
plot(t, soc_true*100, 'k-', t, soc_ah*100, 'r--', t, soc_ekf*100, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('SOC (%)');
legend('真实值','安时法','EKF'); grid on; title('SOC估计');

err_ah = soc_ah - soc_true; err_ekf = soc_ekf - soc_true;
fprintf('===== SOC估计结果 =====\n');
fprintf('安时法RMS误差: %.3f%%\n', rms_calculation(err_ah)*100);
fprintf('EKF RMS误差: %.3f%%\n', rms_calculation(err_ekf)*100);
fprintf('安时法终值误差: %.3f%%\n', abs(soc_ah(end)-soc_true(end))*100);
fprintf('EKF终值误差: %.3f%%\n', abs(soc_ekf(end)-soc_true(end))*100);
