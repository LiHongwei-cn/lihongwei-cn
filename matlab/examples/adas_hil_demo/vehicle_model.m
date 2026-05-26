%% vehicle_model.m — Single-Track Longitudinal Vehicle Model (R2016b)
%  Forward Euler integration. No arguments block.
%
%  Inputs:
%    throttle   — throttle command [0-1]
%    brake      — brake command [0-1]
%    vel_cur    — current velocity [m/s]
%    pos_cur    — current position [m]
%
%  Outputs:
%    acc_new    — new acceleration [m/s^2]
%    vel_new    — new velocity [m/s]
%    pos_new    — new position [m]

function [acc_new, vel_new, pos_new] = vehicle_model(throttle, brake, vel_cur, pos_cur)

    %% ========== Vehicle Parameters ==========
    m   = 1500;    % vehicle mass [kg]
    Cd  = 0.32;    % aerodynamic drag coefficient [-]
    Af  = 2.2;     % frontal area [m^2]
    Cr  = 0.015;   % rolling resistance coefficient [-]
    g   = 9.81;    % gravitational acceleration [m/s^2]
    rho = 1.225;   % air density [kg/m^3]
    dt  = 0.01;    % time step [s]

    %% ========== Force Calculations ==========
    % Engine / braking force
    F_engine = throttle * 4000;    % max engine force [N]
    F_brake  = brake * 8000;       % max braking force [N]

    % Aerodynamic drag: F_aero = 0.5 * rho * Cd * Af * v^2
    F_aero = 0.5 * rho * Cd * Af * vel_cur * vel_cur;

    % Rolling resistance: F_roll = Cr * m * g
    F_roll = Cr * m * g;

    %% ========== Net Force and Acceleration ==========
    F_net = F_engine - F_brake - F_aero - F_roll;
    acc_new = F_net / m;           % [m/s^2]

    %% ========== Forward Euler Integration ==========
    vel_new = vel_cur + acc_new * dt;    % [m/s]
    pos_new = pos_cur + vel_cur * dt;    % [m]

    %% ========== Physical Constraints ==========
    % Vehicle cannot go backwards
    if vel_new < 0
        vel_new = 0;
        acc_new = 0;
    end

    % Clamp to max speed ~200 km/h = 55.6 m/s
    if vel_new > 55.6
        vel_new = 55.6;
    end

end
