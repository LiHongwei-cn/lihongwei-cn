% 车辆纵向动力学模型
%
% 功能：根据油门/制动指令计算车辆的纵向运动状态更新
% 原理：驱动力 - 制动力 - 风阻 - 滚阻 = 合力，合力/质量 = 加速度
%       采用前向欧拉法进行数值积分
%
% 输入参数：
%   throttle      - 油门指令 [0-1]
%   brake         - 制动指令 [0-1]
%   vel_cur       - 当前速度 [m/s]
%   pos_cur       - 当前位置 [m]
%   params        - 车辆参数结构体（由主脚本传入）
%   dt            - 仿真步长 [s]
%
% 输出参数：
%   acc_new       - 更新后的加速度 [m/s^2]
%   vel_new       - 更新后的速度 [m/s]
%   pos_new       - 更新后的位置 [m]
%
% 兼容版本：MATLAB R2016b

function [acc_new, vel_new, pos_new] = vehicle_model(...
    throttle, brake, vel_cur, pos_cur, params, dt)

    % 驱动力：油门开度 * 最大驱动力
    F_engine = throttle * params.F_max_engine;    % [N]

    % 制动力：制动踏板行程 * 最大制动力
    F_brake = brake * params.F_max_brake;          % [N]

    % 空气阻力：F = 0.5 * rho * Cd * Af * v^2
    F_aero = 0.5 * params.rho * params.Cd * params.Af * vel_cur * vel_cur;

    % 滚动阻力：F = Cr * m * g
    F_roll = params.Cr * params.m * params.g;

    % 合力 = 驱动力 - 制动力 - 空气阻力 - 滚动阻力
    F_net = F_engine - F_brake - F_aero - F_roll;

    % 加速度 = 合力 / 质量
    acc_new = F_net / params.m;                     % [m/s^2]

    % 前向欧拉法积分
    vel_new = vel_cur + acc_new * dt;               % [m/s]
    pos_new = pos_cur + vel_cur * dt;               % [m]

    % 物理约束：车速不能为负（不能倒车）
    if vel_new < 0
        vel_new = 0;
        acc_new = 0;
    end

    % 物理约束：车速不超过最高车速
    if vel_new > params.v_max
        vel_new = params.v_max;
    end

end
