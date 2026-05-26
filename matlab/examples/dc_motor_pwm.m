%% DC Motor PWM Speed Control
% MATLAB R2016b Compatible

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
xlabel('Time (s)'); ylabel('Speed (rpm)'); legend('Ref','Actual'); grid on; title('Speed Response');
subplot(3,2,2); plot(t, w_log, 'b-', 'LineWidth', 1.2); xlim([0.75 0.9]);
xlabel('Time (s)'); ylabel('Speed (rpm)'); grid on; title('Acceleration (Zoom)');
subplot(3,2,3); plot(t, ia_log, 'r-', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Current (A)'); grid on; title('Armature Current');
subplot(3,2,4); plot(t, TL, 'r-', t, Kt*ia_log, 'b-', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Torque (Nm)'); legend('Load','EM'); grid on; title('Torque');
subplot(3,2,5); plot(t, va_log, 'g-', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Voltage (V)'); grid on; title('Armature Voltage');
subplot(3,2,6); plot(t, duty_log*100, 'm-', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Duty (%)'); grid on; title('PWM Duty Cycle');

fprintf('===== DC Motor Results =====\n');
fprintf('Speed error: %.1f rpm\n', abs(w_log(end)-w_ref(end)*30/pi));
fprintf('Peak current: %.2f A\n', max(abs(ia_log)));
