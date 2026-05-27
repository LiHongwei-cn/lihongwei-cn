%% 直流电机 PWM 调速仿真
% 功能：直流电机 PWM 驱动 + PI 转速闭环控制
% 兼容版本：MATLAB R2016b

clc; close all;

%% 电机参数
Ra = 0.5;                    % 电枢电阻 [Ohm]
La = 0.003;                  % 电枢电感 [H]
Ke = 0.05;                   % 反电动势系数 [V*s/rad]
Kt = 0.05;                   % 转矩系数 [Nm/A]
J = 0.01;                    % 转动惯量 [kg*m^2]
B = 0.001;                   % 摩擦系数 [Nm*s/rad]
Vdc = 48;                    % 直流母线电压 [V]

%% 仿真参数
Ts = 0.0005;                 % 仿真步长 [s]
T = 2.0;                     % 仿真时长 [s]
t = 0:Ts:T;                  % 时间向量
n = length(t);

%% PI 控制器参数
Kp = 0.8;                    % 比例增益
Ki = 5.0;                    % 积分增益

%% 参考转速和负载
w_ref = 0*(t<0.3) + 100*(t>=0.3 & t<0.8) + 200*(t>=0.8 & t<1.4) + 150*(t>=1.4);   % [rad/s]
TL = 1.0*(t>1.0 & t<1.8);                                                               % 负载转矩 [Nm]

%% 状态变量初始化
w = 0; ia = 0; ei = 0;

%% 日志预分配
w_log = zeros(1,n); ia_log = zeros(1,n);
va_log = zeros(1,n); duty_log = zeros(1,n);

%% 仿真主循环
for k = 1:n
    % PI 控制器
    e = w_ref(k) - w;
    ei = ei + e*Ts;
    duty = max(min(Kp*e + Ki*ei, 1), -1);

    % PWM 驱动
    Va = duty*Vdc;                                % 电枢电压 [V]
    Ea = Ke*w;                                    % 反电动势 [V]

    % 电流更新（前向欧拉法）
    ia = ia + (Va - Ra*ia - Ea)/La*Ts;           % 电枢电流 [A]

    % 转速更新（前向欧拉法）
    w = w + (Kt*ia - B*w - TL(k))/J*Ts;          % 角速度 [rad/s]

    % 记录日志
    w_log(k)=w*30/pi; ia_log(k)=ia; va_log(k)=Va; duty_log(k)=duty;
end

%% 绘图
figure('Position', [100 100 900 650]);

subplot(3,2,1);
plot(t, w_ref*30/pi, 'r--', t, w_log, 'b-', 'LineWidth', 1.5);
xlabel('时间 (s)'); ylabel('转速 (rpm)');
legend('参考', '实际'); grid on; title('转速响应');

subplot(3,2,2);
plot(t, w_log, 'b-', 'LineWidth', 1.2); xlim([0.75 0.9]);
xlabel('时间 (s)'); ylabel('转速 (rpm)');
grid on; title('速度跟踪（局部放大）');

subplot(3,2,3);
plot(t, ia_log, 'r-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('电流 (A)');
grid on; title('电枢电流');

subplot(3,2,4);
plot(t, TL, 'r-', t, Kt*ia_log, 'b-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('转矩 (Nm)');
legend('负载', '电磁'); grid on; title('转矩');

subplot(3,2,5);
plot(t, va_log, 'g-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('电压 (V)');
grid on; title('电枢电压');

subplot(3,2,6);
plot(t, duty_log*100, 'm-', 'LineWidth', 1.2);
xlabel('时间 (s)'); ylabel('占空比 (%)');
grid on; title('PWM 占空比');

%% 输出结果
fprintf('===== 直流电机调速仿真结果 =====\n');
fprintf('转速误差: %.1f rpm\n', abs(w_log(end)-w_ref(end)*30/pi));
fprintf('峰值电流: %.2f A\n', max(abs(ia_log)));
