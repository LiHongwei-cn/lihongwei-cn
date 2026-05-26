% 多传感器融合模型
%
% 功能：模拟三种传感器的测量过程
%   - 雷达：测距、测速、方位角，带高斯噪声
%   - 摄像头：概率性检测 + 车道偏移测量
%   - 超声波：仅短距离有效（泊车场景）
%
% 输入参数：
%   true_range      - 真实距离 [m]
%   true_range_rate - 真实接近速度 [m/s]
%   true_lat_offset - 真实横向偏移 [m]
%   cfg             - 传感器配置结构体（由主脚本传入）
%
% 输出参数：
%   sens            - 结构体，包含 .radar、.camera、.ultrasonic 三个子结构
%
% 兼容版本：MATLAB R2016b

function sens = sensor_model(true_range, true_range_rate, true_lat_offset, cfg)

    %% 雷达传感器
    % 测距：真实距离 + 高斯噪声
    range_meas = true_range + cfg.radar_range_std * randn();

    % 测速：真实接近速度 + 高斯噪声
    rate_meas = true_range_rate + cfg.radar_rate_std * randn();

    % 方位角：基于横向偏移和距离计算，加高斯噪声
    azimuth_meas = atan2(true_lat_offset, max(true_range, 0.1)) ...
                   + cfg.radar_azimuth_std * randn();

    % 有效性判断：距离为正且在最大探测范围内
    radar_valid = (true_range > 0) && (true_range < cfg.radar_max_range);

    sens.radar.range   = range_meas;      % [m]
    sens.radar.rate    = rate_meas;        % [m/s]
    sens.radar.azimuth = azimuth_meas;     % [rad]
    sens.radar.valid   = radar_valid;

    %% 摄像头传感器
    % 概率性检测：按检测概率随机判断是否检测到目标
    camera_detected = rand() < cfg.camera_det_prob;

    % 车道偏移测量：真实偏移 + 高斯噪声
    lane_meas = true_lat_offset + cfg.camera_lane_std * randn();

    sens.camera.detected    = camera_detected;
    sens.camera.lane_offset = lane_meas;   % [m]
    sens.camera.valid       = camera_detected;

    %% 超声波传感器
    % 仅在短距离内有效（泊车辅助场景）
    ultra_valid = (true_range > 0) && (true_range < cfg.ultrasonic_range);

    if ultra_valid
        ultra_range = true_range + 0.05 * randn();   % [m]，近距离噪声小
    else
        ultra_range = NaN;   % 超出探测范围，返回无效值
    end

    sens.ultrasonic.range = ultra_range;   % [m]
    sens.ultrasonic.valid = ultra_valid;

end
