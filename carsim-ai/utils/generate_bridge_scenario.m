%% 高架桥场景生成器 - 燕子矶高架仿真
% MATLAB R2016b 兼容
% 用于 CarSim 2019.0
% 生成高架桥道路场景，包含上坡、护栏、低摩擦路面

function generate_bridge_scenario(params)
    % generate_bridge_scenario 生成高架桥道路场景
    %
    % 输入参数：
    %   params.bridge_length  - 高架桥长度 [m]
    %   params.bridge_width   - 高架桥宽度 [m]
    %   params.slope_angle    - 坡度角度 [deg]
    %   params.guardrail_height - 护栏高度 [m]
    %   params.friction       - 路面摩擦系数
    %   params.output_dir     - 输出目录

    %% 参数验证
    assert(params.bridge_length > 0, '高架桥长度必须为正数');
    assert(params.bridge_width > 0, '高架桥宽度必须为正数');
    assert(params.slope_angle > 0 && params.slope_angle < 45, '坡度角度应在 0-45 度之间');
    assert(params.guardrail_height > 0, '护栏高度必须为正数');
    assert(params.friction > 0 && params.friction <= 1, '摩擦系数应在 0-1 之间');

    %% 计算坡度参数
    slope_rad = params.slope_angle * pi / 180;
    slope_length = params.bridge_length / cos(slope_rad);
    height_gain = params.bridge_length * tan(slope_rad);

    fprintf('===== 高架桥场景参数 =====\n');
    fprintf('长度: %.1f m\n', params.bridge_length);
    fprintf('宽度: %.1f m\n', params.bridge_width);
    fprintf('坡度: %.1f deg\n', params.slope_angle);
    fprintf('护栏高度: %.2f m\n', params.guardrail_height);
    fprintf('路面摩擦: %.2f\n', params.friction);
    fprintf('坡面长度: %.1f m\n', slope_length);
    fprintf('高度提升: %.1f m\n', height_gain);

    %% 生成道路数据文件
    road_file = fullfile(params.output_dir, 'bridge_road.road');
    generate_road_file(road_file, params);

    %% 生成路面摩擦文件
    friction_file = fullfile(params.output_dir, 'bridge_friction.tir');
    generate_friction_file(friction_file, params);

    %% 生成护栏文件
    guardrail_file = fullfile(params.output_dir, 'bridge_guardrail.par');
    generate_guardrail_file(guardrail_file, params);

    fprintf('\n===== 场景文件已生成 =====\n');
    fprintf('道路文件: %s\n', road_file);
    fprintf('摩擦文件: %s\n', friction_file);
    fprintf('护栏文件: %s\n', guardrail_file);
end

function generate_road_file(filename, params)
    % generate_road_file 生成道路定义文件
    %
    % CarSim 道路文件格式 (.road)

    fid = fopen(filename, 'w');
    if fid == -1
        error('无法创建文件: %s', filename);
    end

    % 文件头
    fprintf(fid, '! CarSim Road File - 高架桥场景\n');
    fprintf(fid, '! 生成时间: %s\n', datestr(now));
    fprintf(fid, '! 场景: 燕子矶高架仿真\n');
    fprintf(fid, '\n');

    % 道路参数
    fprintf(fid, 'ROAD_PARAMETERS\n');
    fprintf(fid, '  LENGTH = %.2f\n', params.bridge_length);
    fprintf(fid, '  WIDTH = %.2f\n', params.bridge_width);
    fprintf(fid, '  SLOPE = %.2f\n', params.slope_angle);
    fprintf(fid, '  FRICTION = %.2f\n', params.friction);
    fprintf(fid, 'END_ROAD_PARAMETERS\n');
    fprintf(fid, '\n');

    % 道路轮廓（上坡段）
    fprintf(fid, 'ROAD_PROFILE\n');
    fprintf(fid, '  ! X坐标 [m], Y坐标 [m], Z坐标 [m]\n');

    % 生成道路中心线
    num_points = 100;
    x = linspace(0, params.bridge_length, num_points);
    y = zeros(1, num_points);
    z = x * tan(params.slope_angle * pi / 180);

    for i = 1:num_points
        fprintf(fid, '  %.2f, %.2f, %.2f\n', x(i), y(i), z(i));
    end

    fprintf(fid, 'END_ROAD_PROFILE\n');
    fprintf(fid, '\n');

    % 路面摩擦分布
    fprintf(fid, 'FRICTION_DISTRIBUTION\n');
    fprintf(fid, '  ! 位置 [m], 摩擦系数\n');

    % 全路段低摩擦（模拟冰雪路面）
    num_friction = 50;
    x_friction = linspace(0, params.bridge_length, num_friction);
    for i = 1:num_friction
        fprintf(fid, '  %.2f, %.2f\n', x_friction(i), params.friction);
    end

    fprintf(fid, 'END_FRICTION_DISTRIBUTION\n');

    fclose(fid);
end

function generate_friction_file(filename, params)
    % generate_friction_file 生成路面摩擦定义文件
    %
    % CarSim 轮胎摩擦文件格式 (.tir)

    fid = fopen(filename, 'w');
    if fid == -1
        error('无法创建文件: %s', filename);
    end

    % 文件头
    fprintf(fid, '! CarSim Tire Friction File - 冰雪路面\n');
    fprintf(fid, '! 生成时间: %s\n', datestr(now));
    fprintf(fid, '\n');

    % 轮胎参数
    fprintf(fid, 'TIRE_PARAMETERS\n');
    fprintf(fid, '  FRICTION_COEFFICIENT = %.2f\n', params.friction);
    fprintf(fid, '  ROAD_CONDITION = ICE_SNOW\n');
    fprintf(fid, '  TEMPERATURE = -5.0\n');  % 模拟低温
    fprintf(fid, '  WETNESS = 0.8\n');       % 湿滑程度
    fprintf(fid, 'END_TIRE_PARAMETERS\n');
    fprintf(fid, '\n');

    % 摩擦系数曲线
    fprintf(fid, 'FRICTION_CURVE\n');
    fprintf(fid, '  ! 滑移率, 摩擦系数\n');

    % 生成魔术公式摩擦曲线
    slip_ratio = linspace(0, 1, 50);
    mu = params.friction * (1 - exp(-10 * slip_ratio));  % 简化的摩擦模型

    for i = 1:length(slip_ratio)
        fprintf(fid, '  %.4f, %.4f\n', slip_ratio(i), mu(i));
    end

    fprintf(fid, 'END_FRICTION_CURVE\n');

    fclose(fid);
end

function generate_guardrail_file(filename, params)
    % generate_guardrail_file 生成护栏定义文件
    %
    % CarSim 护栏参数文件格式 (.par)

    fid = fopen(filename, 'w');
    if fid == -1
        error('无法创建文件: %s', filename);
    end

    % 文件头
    fprintf(fid, '! CarSim Guardrail Parameters - 高架桥护栏\n');
    fprintf(fid, '! 生成时间: %s\n', datestr(now));
    fprintf(fid, '\n');

    % 护栏参数
    fprintf(fid, 'GUARDRAIL_PARAMETERS\n');
    fprintf(fid, '  HEIGHT = %.2f\n', params.guardrail_height);
    fprintf(fid, '  WIDTH = 0.3\n');        % 护栏宽度 [m]
    fprintf(fid, '  MATERIAL = CONCRETE\n'); % 材料类型
    fprintf(fid, '  STIFFNESS = 1e6\n');    % 刚度 [N/m]
    fprintf(fid, '  DAMPING = 1e4\n');      % 阻尼 [N·s/m]
    fprintf(fid, 'END_GUARDRAIL_PARAMETERS\n');
    fprintf(fid, '\n');

    % 左侧护栏位置
    fprintf(fid, 'LEFT_GUARDRAIL\n');
    fprintf(fid, '  ! X坐标 [m], Y坐标 [m], Z坐标 [m]\n');

    num_points = 100;
    x = linspace(0, params.bridge_length, num_points);
    y_left = ones(1, num_points) * (params.bridge_width / 2);
    z = x * tan(params.slope_angle * pi / 180);

    for i = 1:num_points
        fprintf(fid, '  %.2f, %.2f, %.2f\n', x(i), y_left(i), z(i));
    end

    fprintf(fid, 'END_LEFT_GUARDRAIL\n');
    fprintf(fid, '\n');

    % 右侧护栏位置
    fprintf(fid, 'RIGHT_GUARDRAIL\n');
    fprintf(fid, '  ! X坐标 [m], Y坐标 [m], Z坐标 [m]\n');

    y_right = ones(1, num_points) * (-params.bridge_width / 2);

    for i = 1:num_points
        fprintf(fid, '  %.2f, %.2f, %.2f\n', x(i), y_right(i), z(i));
    end

    fprintf(fid, 'END_RIGHT_GUARDRAIL\n');

    fclose(fid);
end
