%% 直流电机PWM调速仿真
% MATLAB R2016b 兼容

clc; close all;

Ra = 0.5; La = 0.003; Ke = 0.05; Kt = 0.05;
J = 0.01; B = 0.001; Vdc = 48;
Ts = 0.0005; T = 2.0; t = 0:Ts:T; n = length(t);
Kp = 0.8; Ki = 5.0;

w_ref = 0*(t<0.3) + 100*(t>=0.3 & t<0.8) + 200*(t>=0.8 & t<1.4) + 150*(t>=1.4);
TL = 1.0*(t>1.0 & t<1.8);

w = 0; ia = 0; ei = 0;
w_log = zeros(1,n); ia_log = zeros(1,n);
va_log = zeros(1,n); duty_log = zeros(1,n);

for k = 1:n
    e = w_ref(k) - w; ei = ei + e*Ts;
    duty = max(min(Kp*e + Ki*ei, 1), -1);
    Va = duty*Vdc; Ea = Ke*w;
    ia = ia + (Va - Ra*ia - Ea)/La*Ts;
    w = w + (Kt*ia - B*w - TL(k))/J*Ts;
    w_log(k)=w*30/pi; ia_log(k)=ia; va_log(k)=Va; duty_log(k)=duty;
end

figure('Position', [100 100 900 650]);
subplot(3,2,1); plot(t, w_ref*30/pi, 'r--', t, w_log, 'b-', 'LineWidth', 1.5);
xlabel('时间 (s)'); ylabel('转速 (rpm)'); legend('参考','实际'); grid on; title('转速响应');
subplot(3,2,2); plot(t, w_log, 'b-', 'LineWidth', 1.2); xlim([0.75 0.9]);
xlabel('时间 (s)'); ylabel('转速 (rpm)'); grid on; title('速度跟踪（局部放大）');
subplot(3,2,3); plot(t, ia_log, 'r-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('电流 (A)'); grid on; title('电枢电流');
subplot(3,2,4); plot(t, TL, 'r-', t, Kt*ia_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('转矩 (Nm)'); legend('负载','电磁'); grid on; title('转矩');
subplot(3,2,5); plot(t, va_log, 'g-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('电压 (V)'); grid on; title('电枢电压');
subplot(3,2,6); plot(t, duty_log*100, 'm-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('占空比 (%)'); grid on; title('PWM占空比');

fprintf('===== 直流电机仿真结果 =====\n');
fprintf('转速误差: %.1f rpm\n', abs(w_log(end)-w_ref(end)*30/pi));
fprintf('峰值电流: %.2f A\n', max(abs(ia_log)));
