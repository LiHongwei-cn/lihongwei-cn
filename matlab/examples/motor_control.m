%% PMSM 永磁同步电机 FOC 控制仿真
% MATLAB R2016b 兼容
% 演示：矢量控制（FOC）基本算法
% 电流环 PI 调节 + SVPWM

clear; clc; close all;

%% 电机参数
pmsm.Rs  = 0.958;      % 定子电阻 [Ohm]
pmsm.Ld  = 0.00525;    % d轴电感 [H]
pmsm.Lq  = 0.00525;    % q轴电感 [H]
pmsm.psi = 0.1827;     % 永磁磁链 [Wb]
pmsm.P   = 4;          % 极对数
pmsm.J   = 0.003;      % 转动惯量 [kg.m^2]
pmsm.B   = 0.0001;     % 阻尼系数

%% 控制参数
Ts = 1e-4;             % 仿真步长 [s] (10kHz)
T  = 0.5;              % 总时长 [s]
t  = 0:Ts:T;
n  = length(t);

% PI 参数 (电流环)
Kp_i = 100;
Ki_i = 2000;

% PI 参数 (速度环)
Kp_s = 0.5;
Ki_s = 10;

%% 参考输入（向量化）
w_ref = 0 * (t < 0.1) ...
      + 1000 * (t >= 0.1 & t < 0.3) ...
      + 2000 * (t >= 0.3);
TL = 0.5 * (t > 0.4);

%% 初始化状态
id = 0; iq = 0; wm = 0; theta = 0;
id_ref = 0;             % id=0 控制

% 积分累积
ei_sum_d = 0;
ei_sum_q = 0;
ew_sum   = 0;

% 存储
id_log = zeros(1, n);
iq_log = zeros(1, n);
wm_log = zeros(1, n);
vd_log = zeros(1, n);
vq_log = zeros(1, n);
Te_log = zeros(1, n);

%% 主仿真循环
for k = 1:n
    % 速度环 PI
    ew = (w_ref(k) - wm * 30/pi) * (pi/30);  % rpm -> rad/s
    ew_sum = ew_sum + ew * Ts;
    iq_ref = Kp_s * ew + Ki_s * ew_sum;
    iq_ref = max(min(iq_ref, 10), -10);       % 限幅

    % 电流环 PI (d轴)
    ed = id_ref - id;
    ei_sum_d = ei_sum_d + ed * Ts;
    vd = Kp_i * ed + Ki_i * ei_sum_d;

    % 电流环 PI (q轴)
    eq = iq_ref - iq;
    ei_sum_q = ei_sum_q + eq * Ts;
    vq = Kp_i * eq + Ki_i * ei_sum_q;

    % 解耦补偿
    vd = vd - pmsm.Lq * pmsm.P * wm * iq;
    vq = vq + pmsm.psi * pmsm.P * wm + pmsm.Ld * pmsm.P * wm * id;

    % 电机模型（前向欧拉）
    did_dt = (vd - pmsm.Rs * id + pmsm.Lq * pmsm.P * wm * iq) / pmsm.Ld;
    diq_dt = (vq - pmsm.Rs * iq - pmsm.psi * pmsm.P * wm - pmsm.Ld * pmsm.P * wm * id) / pmsm.Lq;

    id = id + did_dt * Ts;
    iq = iq + diq_dt * Ts;

    % 电磁转矩
    Te = 1.5 * pmsm.P * (pmsm.psi * iq + (pmsm.Ld - pmsm.Lq) * id * iq);

    % 机械方程
    dwm_dt = (Te - pmsm.B * wm - TL(k)) / pmsm.J;
    wm = wm + dwm_dt * Ts;
    theta = theta + wm * Ts;

    % 记录
    id_log(k) = id;
    iq_log(k) = iq;
    wm_log(k) = wm * 30 / pi;   % rad/s -> rpm
    vd_log(k) = vd;
    vq_log(k) = vq;
    Te_log(k) = Te;
end

%% 绘图
figure('Position', [100 100 900 700]);

subplot(3,2,1);
plot(t, w_ref, 'r--', t, wm_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('转速 (rpm)');
legend('参考值', '实际值'); grid on; title('转速响应');

subplot(3,2,2);
plot(t, Te_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('电磁转矩 (Nm)');
grid on; title('转矩输出');

subplot(3,2,3);
plot(t, id_log, 'r-', t, iq_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('电流 (A)');
legend('i_d', 'i_q'); grid on; title('d-q 轴电流');

subplot(3,2,4);
plot(t, vd_log, 'r-', t, vq_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('电压 (V)');
legend('v_d', 'v_q'); grid on; title('d-q 轴电压');

subplot(3,2,5:6);
plot(t, w_ref, 'r--', t, wm_log, 'b-', 'LineWidth', 1.2);
xlim([0.38 0.5]);
xlabel('时间 (s)'); ylabel('转速 (rpm)');
legend('参考值', '实际值'); grid on; title('负载响应（局部放大）');

%% 性能指标
fprintf('===== 电机控制仿真结果 =====\n');
fprintf('稳态转速误差: %.2f rpm\n', abs(wm_log(end) - w_ref(end)));
fprintf('峰值转矩: %.3f Nm\n', max(Te_log));
fprintf('q轴稳态电流: %.3f A\n', iq_log(end));
