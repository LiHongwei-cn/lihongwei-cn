%% Vehicle Longitudinal Dynamics Simulation
% MATLAB R2016b Compatible
% Demo: Acceleration - Cruise - Braking

clc; close all;

param.m = 1500; param.Cd = 0.32; param.Af = 2.2; param.rho = 1.225;
param.f = 0.015; param.g = 9.81; param.rw = 0.31; param.eta = 0.92;

dt = 0.01; T = 30; t = 0:dt:T; n = length(t);

V_CRUISE = 30/3.6;
F_CRUISE = calcResist(V_CRUISE, param);
F_drive = 3000*(t/10).*(t<=10) + F_CRUISE.*(t>10 & t<=20);
F_brake = 2000*(t>20);

v = zeros(1,n); a = zeros(1,n); s = zeros(1,n);
for i = 2:n
    Fr = calcResist(v(i-1), param);
    a(i) = (F_drive(i-1) - Fr - F_brake(i-1)) / param.m;
    v(i) = max(v(i-1) + a(i)*dt, 0);
    s(i) = s(i-1) + v(i)*dt;
end

figure('Position', [100 100 800 600]);
subplot(3,1,1); plot(t, v*3.6, 'b-', 'LineWidth', 1.5);
ylabel('Speed (km/h)'); grid on; title('Vehicle Dynamics'); legend('Speed');
subplot(3,1,2); plot(t, a, 'r-', 'LineWidth', 1.5);
ylabel('Accel (m/s^2)'); grid on;
subplot(3,1,3); plot(t, s, 'g-', 'LineWidth', 1.5);
xlabel('Time (s)'); ylabel('Distance (m)'); grid on;

fprintf('===== Vehicle Dynamics Results =====\n');
fprintf('Max speed: %.1f km/h\n', max(v)*3.6);
fprintf('Max accel: %.2f m/s^2\n', max(a));
fprintf('Total distance: %.1f m\n', s(end));

function F = calcResist(v, p)
    F = 0.5*p.rho*p.Cd*p.Af*v^2 + p.f*p.m*p.g;
end
