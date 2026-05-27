%% 永磁同步电机矢量控制仿真
% 功能：PMSM id=0 矢量控制，含转速环和电流环 PI 控制
% 兼容版本：MATLAB R2016b

clc; close all;

%% 电机参数
pmsm.Rs = 0.958;             % 定子电阻 [Ohm]
pmsm.Ld = 0.00525;           % d轴电感 [H]
pmsm.Lq = 0.00525;           % q轴电感 [H]
pmsm.psi = 0.1827;           % 永磁体磁链 [Wb]
pmsm.P = 4;                  % 极对数
pmsm.J = 0.003;              % 转动惯量 [kg*m^2]
pmsm.B = 0.0001;             % 摩擦系数 [Nm*s/rad]

%% 仿真参数
Ts = 1e-4;                   % 仿真步长 [s]
T = 0.5;                     % 仿真时长 [s]
t = 0:Ts:T;                  % 时间向量
n = length(t);

%% PI 控制器参数
Kp_i = 100;                  % 电流环比例增益
Ki_i = 2000;                 % 电流环积分增益
Kp_s = 0.5;                  % 转速环比例增益
Ki_s = 10;                   % 转速环积分增益

%% 参考信号和负载
w_ref = 0*(t<0.1) + 1000*(t>=0.1 & t<0.3) + 2000*(t>=0.3);   % 转速参考 [rpm]
TL = 0.5*(t>0.4);                                               % 负载转矩 [Nm]

%% 状态变量初始化
id = 0; iq = 0; wm = 0; id_ref = 0;
ei_d = 0; ei_q = 0; ew = 0;

%% 日志预分配
id_log = zeros(1,n); iq_log = zeros(1,n); wm_log = zeros(1,n);
vd_log = zeros(1,n); vq_log = zeros(1,n); Te_log = zeros(1,n);

%% 仿真主循环
for k = 1:n
    % 转速环 PI
    e = (w_ref(k) - wm*30/pi)*(pi/30);
    ew = ew + e*Ts;
    iq_ref = max(min(Kp_s*e + Ki_s*ew, 10), -10);

    % d轴电流环 PI
    ei_d = ei_d + (id_ref-id)*Ts;
    vd = Kp_i*(id_ref-id) + Ki_i*ei_d;

    % q轴电流环 PI
    ei_q = ei_q + (iq_ref-iq)*Ts;
    vq = Kp_i*(iq_ref-iq) + Ki_i*ei_q;

    % 前馈解耦
    vd = vd - pmsm.Lq*pmsm.P*wm*iq;
    vq = vq + pmsm.psi*pmsm.P*wm + pmsm.Ld*pmsm.P*wm*id;

    % 电流更新（前向欧拉法）
    id = id + (vd - pmsm.Rs*id + pmsm.Lq*pmsm.P*wm*iq)/pmsm.Ld*Ts;
    iq = iq + (vq - pmsm.Rs*iq - pmsm.psi*pmsm.P*wm - pmsm.Ld*pmsm.P*wm*id)/pmsm.Lq*Ts;

    % 电磁转矩
    Te = 1.5*pmsm.P*(pmsm.psi*iq + (pmsm.Ld-pmsm.Lq)*id*iq);

    % 机械方程
    wm = wm + (Te - pmsm.B*wm - TL(k))/pmsm.J*Ts;

    % 记录日志
    id_log(k)=id; iq_log(k)=iq; wm_log(k)=wm*30/pi;
    vd_log(k)=vd; vq_log(k)=vq; Te_log(k)=Te;
end

%% 绘图
figure('Position', [100 100 900 700]);

subplot(3,2,1);
plot(t, w_ref, 'r--', t, wm_log, 'b-', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Speed (rpm)');
legend('Ref', 'Actual'); grid on; title('Speed Response');

subplot(3,2,2);
plot(t, Te_log, 'b-', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Torque (Nm)');
grid on; title('Electromagnetic Torque');

subplot(3,2,3);
plot(t, id_log, 'r-', t, iq_log, 'b-', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Current (A)');
legend('id', 'iq'); grid on; title('dq Current');

subplot(3,2,4);
plot(t, vd_log, 'r-', t, vq_log, 'b-', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Voltage (V)');
legend('vd', 'vq'); grid on; title('dq Voltage');

subplot(3,2,5:6);
plot(t, w_ref, 'r--', t, wm_log, 'b-', 'LineWidth', 1.2);
xlim([0.38 0.5]); xlabel('Time (s)'); ylabel('Speed (rpm)');
legend('Ref', 'Actual'); grid on; title('Step Response Detail');

%% 输出结果
fprintf('===== PMSM FOC Results =====\n');
fprintf('Speed error: %.2f rpm\n', abs(wm_log(end)-w_ref(end)));
fprintf('Peak torque: %.3f Nm\n', max(Te_log));
