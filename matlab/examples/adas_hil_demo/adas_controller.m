% ADAS 决策控制器
%
% 功能：根据传感器数据和车辆状态，做出三种辅助驾驶决策
%   - FCW（前碰撞预警）：碰撞时间 TTC < 2.5 秒时发出警告
%   - AEB（自动紧急制动）：碰撞时间 TTC < 1.0 秒时全力制动
%   - LDW（车道偏离预警）：横向偏移超过 0.3 米时发出警告
%
% 输入参数：
%   sens        - 传感器数据结构体（来自 sensor_model）
%   veh_speed   - 当前车速 [m/s]
%   lat_offset  - 当前横向偏移 [m]
%
% 输出参数：
%   ctrl        - 结构体，包含：
%                 .fcw_warning  - FCW 预警标志
%                 .aeb_warning  - AEB 预警标志
%                 .ldw_warning  - LDW 预警标志
%                 .throttle     - 油门指令 [0-1]
%                 .brake        - 制动指令 [0-1]
%
% 兼容版本：MATLAB R2016b

function ctrl = adas_controller(sens, veh_speed, lat_offset)

    %% 默认输出：巡航状态，无预警
    ctrl.fcw_warning = false;
    ctrl.aeb_warning = false;
    ctrl.ldw_warning = false;
    ctrl.throttle    = 0.5;     % 默认巡航油门
    ctrl.brake       = 0;       % 默认不制动

    %% 碰撞时间 TTC 计算
    % TTC = 距离 / 接近速度（仅在接近时有效）
    if sens.radar.valid && sens.radar.range > 0
        closing_speed = -sens.radar.rate;   % 接近速度为正值
        if closing_speed > 0.1
            ttc = sens.radar.range / closing_speed;   % [s]
        else
            ttc = Inf;   % 未在接近，不计算 TTC
        end
    else
        ttc = Inf;   % 雷达不可用，不触发预警
    end

    %% FCW 逻辑：TTC < 2.5 秒
    if ttc < 2.5
        ctrl.fcw_warning = true;
    end

    %% AEB 逻辑：TTC < 1.0 秒
    if ttc < 1.0
        ctrl.aeb_warning = true;
        ctrl.brake       = 1.0;    % 全力制动
        ctrl.throttle    = 0;      % 切断油门
    end

    %% LDW 逻辑：横向偏移 > 0.3 米
    if sens.camera.valid
        if abs(sens.camera.lane_offset) > 0.3
            ctrl.ldw_warning = true;
        end
    end

end
