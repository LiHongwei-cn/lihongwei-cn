%% 永磁同步电机矢量控制仿真
% MATLAB R2016b 兼容

clc; close all;

pmsm.Rs = 0.958; pmsm.Ld = 0.00525; pmsm.Lq = 0.00525;
pmsm.psi = 0.1827; pmsm.P = 4; pmsm.J = 0.003; pmsm.B = 0.0001;

Ts = 1e-4; T = 0.5; t = 0:Ts:T; n = length(t);
Kp_i = 100; Ki_i = 2000; Kp_s = 0.5; Ki_s = 10;

w_ref = 0*(t<0.1) + 1000*(t>=0.1 & t<0.3) + 2000*(t>=0.3);
TL = 0.5*(t>0.4);

id = 0; iq = 0; wm = 0; id_ref = 0;
ei_d = 0; ei_q = 0; ew = 0;
id_log = zeros(1,n); iq_log = zeros(1,n); wm_log = zeros(1,n);
vd_log = zeros(1,n); vq_log = zeros(1,n); Te_log = zeros(1,n);

for k = 1:n
    e = (w_ref(k) - wm*30/pi)*(pi/30);
    ew = ew + e*Ts;
    iq_ref = max(min(Kp_s*e + Ki_s*ew, 10), -10);
    ei_d = ei_d + (id_ref-id)*Ts;
    vd = Kp_i*(id_ref-id) + Ki_i*ei_d;
    ei_q = ei_q + (iq_ref-iq)*Ts;
    vq = Kp_i*(iq_ref-iq) + Ki_i*ei_q;
    vd = vd - pmsm.Lq*pmsm.P*wm*iq;
    vq = vq + pmsm.psi*pmsm.P*wm + pmsm.Ld*pmsm.P*wm*id;
    id = id + (vd - pmsm.Rs*id + pmsm.Lq*pmsm.P*wm*iq)/pmsm.Ld*Ts;
    iq = iq + (vq - pmsm.Rs*iq - pmsm.psi*pmsm.P*wm - pmsm.Ld*pmsm.P*wm*id)/pmsm.Lq*Ts;
    Te = 1.5*pmsm.P*(pmsm.psi*iq + (pmsm.Ld-pmsm.Lq)*id*iq);
    wm = wm + (Te - pmsm.B*wm - TL(k))/pmsm.J*Ts;
    id_log(k)=id; iq_log(k)=iq; wm_log(k)=wm*30/pi;
    vd_log(k)=vd; vq_log(k)=vq; Te_log(k)=Te;
end

figure('Position', [100 100 900 700]);
subplot(3,2,1); plot(t, w_ref, 'r--', t, wm_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('转速 (rpm)'); legend('参考','实际'); grid on; title('转速响应');
subplot(3,2,2); plot(t, Te_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('转矩 (Nm)'); grid on; title('电磁转矩');
subplot(3,2,3); plot(t, id_log, 'r-', t, iq_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('电流 (A)'); legend('id','iq'); grid on; title('dq轴电流');
subplot(3,2,4); plot(t, vd_log, 'r-', t, vq_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('电压 (V)'); legend('vd','vq'); grid on; title('dq轴电压');
subplot(3,2,5:6); plot(t, w_ref, 'r--', t, wm_log, 'b-', 'LineWidth', 1.2);
xlim([0.38 0.5]); xlabel('时间 (s)'); ylabel('转速 (rpm)');
legend('参考','实际'); grid on; title('阶跃响应局部放大');

fprintf('===== 矢量控制结果 =====\n');
fprintf('转速误差: %.2f rpm\n', abs(wm_log(end)-w_ref(end)));
fprintf('峰值转矩: %.3f Nm\n', max(Te_log));
