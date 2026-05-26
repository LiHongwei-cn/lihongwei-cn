%% Simple EV Dynamics Simulation
% MATLAB R2016b Compatible

clc; close all;

m = 1600; Cd = 0.28; Af = 2.1; rho = 1.225;
f = 0.012; g = 9.81; rw = 0.33;
T_max = 250; n_base = 3800; eta_motor = 0.90;
V_bat = 350; Q_bat = 100; SOC_init = 0.95;

dt = 0.05; T = 60; t = 0:dt:T; n = length(t);
V_CRUISE = 80/3.6; T_ACCEL = 15; T_CRUISE = 45;
v_target = V_CRUISE*min(t/T_ACCEL,1).*(t<=T_CRUISE) ...
         + V_CRUISE*max(1-(t-T_CRUISE)/T_ACCEL,0).*(t>T_CRUISE);

v = zeros(1,n); s = zeros(1,n); T_m = zeros(1,n);
P_m = zeros(1,n); E_cons = zeros(1,n); SOC = SOC_init*ones(1,n);

for i = 2:n
    a_req = max(-3, min(3, 2.0*(v_target(i-1)-v(i-1))));
    Fr = 0.5*rho*Cd*Af*v(i-1)^2 + f*m*g;
    mrpm = v(i-1)*60/(2*pi*rw);
    Ta = T_max * min(1, n_base/max(mrpm,1));
    Tw = max(-Ta*0.5, min(Ta, (m*a_req+Fr)*rw));
    T_m(i) = Tw;
    v(i) = max(0, v(i-1) + (Tw/rw - Fr)/m*dt);
    s(i) = s(i-1) + v(i)*dt;
    P_m(i) = Tw*(mrpm*2*pi/60);
    Pb = P_m(i) / (eta_motor*(P_m(i)>=0) + 0.6*(P_m(i)<0));
    E_cons(i) = E_cons(i-1) + Pb*dt/3600;
    SOC(i) = SOC(i-1) - Pb*dt/(V_bat*Q_bat*3600);
end

figure('Position', [100 100 900 650]);
subplot(3,2,1); plot(t, v*3.6, 'b-', t, v_target*3.6, 'r--', 'LineWidth', 1.5);
ylabel('Speed (km/h)'); grid on; legend('Actual','Target'); title('Speed Tracking');
subplot(3,2,2); plot(t, T_m, 'g-', 'LineWidth', 1.5);
ylabel('Torque (Nm)'); grid on; title('Motor Torque');
subplot(3,2,3); plot(t, s/1000, 'b-', 'LineWidth', 1.5);
ylabel('Distance (km)'); grid on; title('Cumulative Distance');
subplot(3,2,4); plot(t, P_m/1000, 'r-', 'LineWidth', 1.5);
ylabel('Power (kW)'); grid on; title('Motor Power');
subplot(3,2,5); plot(t, E_cons, 'm-', 'LineWidth', 1.5);
xlabel('Time (s)'); ylabel('Energy (Wh)'); grid on; title('Cumulative Energy');
subplot(3,2,6); plot(t, SOC*100, 'b-', 'LineWidth', 1.5);
xlabel('Time (s)'); ylabel('SOC (%)'); grid on; title('Battery SOC');

fprintf('===== EV Dynamics Results =====\n');
fprintf('Max speed: %.1f km/h\n', max(v)*3.6);
fprintf('Distance: %.2f km\n', s(end)/1000);
fprintf('Energy: %.1f kWh/100km\n', E_cons(end)/(s(end)/1000)/10);
fprintf('SOC remaining: %.1f%%\n', SOC(end)*100);
fprintf('Range: %.0f km\n', s(end)*SOC_init/(SOC_init-SOC(end)+0.001));
