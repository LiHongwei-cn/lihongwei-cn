%% CARSIM_GENERATE_CPAR - 生成CarSim .CPAR配置文件
% 兼容版本：MATLAB R2016b + CarSim 2019.0
% 功能：生成CarSim 2019.0的.CPAR参数文件
%
% 作者：LiHongwei
% 日期：2026-05-29

clear; clc;

fprintf('========================================\n');
fprintf('  CarSim 2019.0 CPAR 文件生成工具\n');
fprintf('========================================\n\n');

%% ==================== 配置参数 ====================

% 道路参数
road.length = 50;              % 道路长度 [m]
road.width = 6;                % 道路宽度 [m]

% 车位参数
parking.spot_length = 5;       % 车位长度 [m]
parking.spot_width = 2.5;      % 车位宽度 [m]
parking.num_spots = 10;        % 车位数量
parking.target_spot = 5;       % 目标车位（空置）
parking.occupancy = [1, 1, 1, 1, 0, 1, 1, 1, 1, 1]; % 车位占用情况

% 车辆初始条件
vehicle.init_x = 45;           % 初始X位置 [m]
vehicle.init_y = 3;            % 初始Y位置 [m]
vehicle.init_yaw = 0;          % 初始航向角 [deg]
vehicle.init_speed = 5;        % 初始速度 [km/h]

fprintf('[1/4] 配置参数加载完成\n');

%% ==================== 生成CPAR文件 ====================

% CPAR文件路径
cpar_file = 'Parking_Reversing.cpar';

% 生成CPAR文件
generate_cpar_file(cpar_file, road, parking, vehicle);

fprintf('[2/4] CPAR文件生成完成: %s\n', cpar_file);

%% ==================== 生成导入脚本 ====================

import_script = 'import_cpar_to_carsim.m';
generate_import_script(import_script, cpar_file);

fprintf('[3/4] 导入脚本生成完成: %s\n', import_script);

%% ==================== 生成手动配置指南 ====================

guide_file = 'CarSim_Manual_Config.txt';
generate_manual_guide(guide_file, road, parking, vehicle);

fprintf('[4/4] 手动配置指南生成完成: %s\n', guide_file);

%% ==================== 完成 ====================

fprintf('\n========================================\n');
fprintf('  所有文件生成完成！\n');
fprintf('========================================\n\n');

fprintf('生成的文件：\n');
fprintf('  1. %s (CarSim参数文件)\n', cpar_file);
fprintf('  2. %s (导入脚本)\n', import_script);
fprintf('  3. %s (手动配置指南)\n', guide_file);

fprintf('\n使用方法：\n');
fprintf('  方法1: 在CarSim中 File → Import → 选择 %s\n', cpar_file);
fprintf('  方法2: 运行 %s 自动导入\n', import_script);
fprintf('  方法3: 按 %s 手动配置\n', guide_file);

%% ==================== CPAR生成函数 ====================

function generate_cpar_file(filename, road, parking, vehicle)
% 生成CarSim CPAR文件
% CPAR是CarSim的压缩参数文件格式

    fid = fopen(filename, 'w', 'n', 'UTF-8');

    % CPAR文件头
    fprintf(fid, '<?xml version="1.0" encoding="UTF-8"?>\n');
    fprintf(fid, '<CarSimParameters version="2019.0">\n');
    fprintf(fid, '  <Metadata>\n');
    fprintf(fid, '    <Name>Parking_Reversing</Name>\n');
    fprintf(fid, '    <Description>倒车入库仿真场景 - 50m道路，6m宽，10个车位</Description>\n');
    fprintf(fid, '    <Author>MATLAB Auto Generator</Author>\n');
    fprintf(fid, '    <Date>%s</Date>\n', datestr(now, 'yyyy-mm-dd'));
    fprintf(fid, '    <Version>1.0</Version>\n');
    fprintf(fid, '  </Metadata>\n\n');

    % 车辆参数（保持默认Sedan）
    fprintf(fid, '  <Vehicle>\n');
    fprintf(fid, '    <Body>\n');
    fprintf(fid, '      <Mass>1500</Mass>\n');
    fprintf(fid, '      <Length>4.5</Length>\n');
    fprintf(fid, '      <Width>1.8</Width>\n');
    fprintf(fid, '      <Height>1.5</Height>\n');
    fprintf(fid, '      <Wheelbase>2.7</Wheelbase>\n');
    fprintf(fid, '      <FrontOverhang>0.9</FrontOverhang>\n');
    fprintf(fid, '      <RearOverhang>0.9</RearOverhang>\n');
    fprintf(fid, '    </Body>\n');
    fprintf(fid, '    <Powertrain>\n');
    fprintf(fid, '      <EngineTorque>250</EngineTorque>\n');
    fprintf(fid, '      <Transmission>Auto6AT</Transmission>\n');
    fprintf(fid, '      <FinalDriveRatio>3.5</FinalDriveRatio>\n');
    fprintf(fid, '      <ReverseGearRatio>3.2</ReverseGearRatio>\n');
    fprintf(fid, '    </Powertrain>\n');
    fprintf(fid, '    <Brakes>\n');
    fprintf(fid, '      <FrontBrakeGain>250</FrontBrakeGain>\n');
    fprintf(fid, '      <RearBrakeGain>150</RearBrakeGain>\n');
    fprintf(fid, '      <MaxBrakePressure>15000</MaxBrakePressure>\n');
    fprintf(fid, '      <ABS>Enabled</ABS>\n');
    fprintf(fid, '    </Brakes>\n');
    fprintf(fid, '    <Steering>\n');
    fprintf(fid, '      <SteeringRatio>16</SteeringRatio>\n');
    fprintf(fid, '      <MaxSteeringAngle>540</MaxSteeringAngle>\n');
    fprintf(fid, '      <PowerSteering>Enabled</PowerSteering>\n');
    fprintf(fid, '    </Steering>\n');
    fprintf(fid, '  </Vehicle>\n\n');

    % 道路参数
    fprintf(fid, '  <Road>\n');
    fprintf(fid, '    <Geometry>\n');
    fprintf(fid, '      <Type>FlatRoad</Type>\n');
    fprintf(fid, '      <Length>%.1f</Length>\n', road.length);
    fprintf(fid, '      <Width>%.1f</Width>\n', road.width);
    fprintf(fid, '      <NumLanes>2</NumLanes>\n');
    fprintf(fid, '      <LaneWidth>%.1f</LaneWidth>\n', road.width / 2);
    fprintf(fid, '    </Geometry>\n');
    fprintf(fid, '    <Surface>\n');
    fprintf(fid, '      <Type>DryAsphalt</Type>\n');
    fprintf(fid, '      <Friction>0.85</Friction>\n');
    fprintf(fid, '      <Roughness>Smooth</Roughness>\n');
    fprintf(fid, '    </Surface>\n');
    fprintf(fid, '  </Road>\n\n');

    % 车位配置
    fprintf(fid, '  <ParkingSpots>\n');
    fprintf(fid, '    <NumSpots>%d</NumSpots>\n', parking.num_spots);
    fprintf(fid, '    <SpotLength>%.1f</SpotLength>\n', parking.spot_length);
    fprintf(fid, '    <SpotWidth>%.1f</SpotWidth>\n', parking.spot_width);
    fprintf(fid, '    <TargetSpot>%d</TargetSpot>\n', parking.target_spot);

    for i = 1:parking.num_spots
        fprintf(fid, '    <Spot id="%d">\n', i);
        fprintf(fid, '      <X>%.1f</X>\n', (i - 0.5) * parking.spot_length);
        fprintf(fid, '      <Y>%.1f</Y>\n', -parking.spot_width / 2);
        fprintf(fid, '      <Occupied>%d</Occupied>\n', parking.occupancy(i));
        fprintf(fid, '    </Spot>\n');
    end

    fprintf(fid, '  </ParkingSpots>\n\n');

    % 停放车辆
    fprintf(fid, '  <StaticVehicles>\n');
    vehicle_id = 0;
    for i = 1:parking.num_spots
        if parking.occupancy(i) == 1
            vehicle_id = vehicle_id + 1;
            x_center = (i - 0.5) * parking.spot_length;
            y_center = -parking.spot_width / 2;
            fprintf(fid, '    <Vehicle id="%d">\n', vehicle_id);
            fprintf(fid, '      <Type>Sedan</Type>\n');
            fprintf(fid, '      <X>%.2f</X>\n', x_center);
            fprintf(fid, '      <Y>%.2f</Y>\n', y_center);
            fprintf(fid, '      <Yaw>90</Yaw>\n');
            fprintf(fid, '      <Speed>0</Speed>\n');
            fprintf(fid, '    </Vehicle>\n');
        end
    end
    fprintf(fid, '  </StaticVehicles>\n\n');

    % 初始条件
    fprintf(fid, '  <InitialConditions>\n');
    fprintf(fid, '    <X>%.1f</X>\n', vehicle.init_x);
    fprintf(fid, '    <Y>%.1f</Y>\n', vehicle.init_y);
    fprintf(fid, '    <Yaw>%.1f</Yaw>\n', vehicle.init_yaw);
    fprintf(fid, '    <Speed>%.1f</Speed>\n', vehicle.init_speed);
    fprintf(fid, '    <Gear>1</Gear>\n');
    fprintf(fid, '  </InitialConditions>\n\n');

    % 仿真事件
    fprintf(fid, '  <Events>\n');
    fprintf(fid, '    <Event id="1">\n');
    fprintf(fid, '      <Name>Approach</Name>\n');
    fprintf(fid, '      <StartTime>0</StartTime>\n');
    fprintf(fid, '      <Duration>10</Duration>\n');
    fprintf(fid, '      <Speed>5</Speed>\n');
    fprintf(fid, '      <Gear>1</Gear>\n');
    fprintf(fid, '    </Event>\n');
    fprintf(fid, '    <Event id="2">\n');
    fprintf(fid, '      <Name>Prepare</Name>\n');
    fprintf(fid, '      <StartTime>10</StartTime>\n');
    fprintf(fid, '      <Duration>2</Duration>\n');
    fprintf(fid, '      <Speed>0</Speed>\n');
    fprintf(fid, '      <Gear>0</Gear>\n');
    fprintf(fid, '      <Brake>100</Brake>\n');
    fprintf(fid, '    </Event>\n');
    fprintf(fid, '    <Event id="3">\n');
    fprintf(fid, '      <Name>Reverse</Name>\n');
    fprintf(fid, '      <StartTime>12</StartTime>\n');
    fprintf(fid, '      <Duration>38</Duration>\n');
    fprintf(fid, '      <Speed>-2</Speed>\n');
    fprintf(fid, '      <Gear>-1</Gear>\n');
    fprintf(fid, '      <Control>Simulink</Control>\n');
    fprintf(fid, '    </Event>\n');
    fprintf(fid, '  </Events>\n\n');

    % Simulink接口
    fprintf(fid, '  <SimulinkInterface>\n');
    fprintf(fid, '    <SFunction>sf_car_sim</SFunction>\n');
    fprintf(fid, '    <Inputs>\n');
    fprintf(fid, '      <Channel name="IMP_STEER_SW" unit="deg" default="0"/>\n');
    fprintf(fid, '      <Channel name="IMP_PBK_CON" unit="kPa" default="0"/>\n');
    fprintf(fid, '      <Channel name="IMP_THROTTLE" unit="%%" default="0"/>\n');
    fprintf(fid, '      <Channel name="IMP_GEARCHANGE" unit="-" default="0"/>\n');
    fprintf(fid, '    </Inputs>\n');
    fprintf(fid, '    <Outputs>\n');
    fprintf(fid, '      <Channel name="XCG" unit="m"/>\n');
    fprintf(fid, '      <Channel name="YCG" unit="m"/>\n');
    fprintf(fid, '      <Channel name="YAW" unit="rad"/>\n');
    fprintf(fid, '      <Channel name="VX" unit="km/h"/>\n');
    fprintf(fid, '      <Channel name="VY" unit="km/h"/>\n');
    fprintf(fid, '      <Channel name="AVZ" unit="deg/s"/>\n');
    fprintf(fid, '    </Outputs>\n');
    fprintf(fid, '  </SimulinkInterface>\n');

    fprintf(fid, '</CarSimParameters>\n');

    fclose(fid);

end

function generate_import_script(filename, cpar_file)
% 生成MATLAB导入脚本

    fid = fopen(filename, 'w');

    fprintf(fid, '%% IMPORT_CPAR_TO_CARSIM - 导入CPAR文件到CarSim\n');
    fprintf(fid, '%% 兼容版本：MATLAB R2016b + CarSim 2019.0\n');
    fprintf(fid, '%%\n');
    fprintf(fid, '%% 作者：LiHongwei\n');
    fprintf(fid, '%% 日期：%s\n\n', datestr(now));

    fprintf(fid, 'clear; clc;\n\n');

    fprintf(fid, 'fprintf(''========================================\\n'');\n');
    fprintf(fid, 'fprintf(''  CarSim CPAR 导入工具\\n'');\n');
    fprintf(fid, 'fprintf(''========================================\\n\\n'');\n\n');

    fprintf(fid, '%% CPAR文件路径\n');
    fprintf(fid, 'cpar_file = ''%s'';\n\n', cpar_file);

    fprintf(fid, '%% 检查文件是否存在\n');
    fprintf(fid, 'if ~exist(cpar_file, ''file'')\n');
    fprintf(fid, '    error(''CPAR文件不存在: %s'', cpar_file);\n');
    fprintf(fid, 'end\n\n');

    fprintf(fid, 'fprintf(''找到CPAR文件: %s\\n'', cpar_file);\n');
    fprintf(fid, 'fprintf(''\\n'');\n\n');

    fprintf(fid, '%% 尝试通过COM接口连接CarSim\n');
    fprintf(fid, 'try\n');
    fprintf(fid, '    fprintf(''尝试连接CarSim...\\n'');\n');
    fprintf(fid, '    h = actxserver(''CarSim.Application'');\n');
    fprintf(fid, '    fprintf(''✓ 成功连接CarSim\\n'');\n\n');

    fprintf(fid, '    % 导入CPAR文件\n');
    fprintf(fid, '    fprintf(''正在导入CPAR文件...\\n'');\n');
    fprintf(fid, '    h.ImportDataset(cpar_file);\n');
    fprintf(fid, '    fprintf(''✓ CPAR文件导入成功\\n'');\n\n');

    fprintf(fid, '    % 关闭COM连接\n');
    fprintf(fid, '    h.release;\n');
    fprintf(fid, '    fprintf(''\\n导入完成！请在CarSim中查看 Parking_Reversing 数据集\\n'');\n\n');

    fprintf(fid, 'catch ME\n');
    fprintf(fid, '    fprintf(''\\n无法通过COM连接CarSim\\n'');\n');
    fprintf(fid, '    fprintf(''错误信息: %s\\n'', ME.message);\n');
    fprintf(fid, '    fprintf(''\\n请手动导入：\\n'');\n');
    fprintf(fid, '    fprintf(''1. 打开CarSim 2019.0\\n'');\n');
    fprintf(fid, '    fprintf(''2. 点击 File → Import Dataset\\n'');\n');
    fprintf(fid, '    fprintf(''3. 选择文件: %s\\n'', cpar_file);\n');
    fprintf(fid, '    fprintf(''4. 点击 OK 确认导入\\n'');\n');
    fprintf(fid, 'end\n');

    fclose(fid);

end

function generate_manual_guide(filename, road, parking, vehicle)
% 生成手动配置指南

    fid = fopen(filename, 'w');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  CarSim 2019.0 手动配置指南\n');
    fprintf(fid, '  倒车入库仿真场景\n');
    fprintf(fid, '====================================================\n\n');

    fprintf(fid, '【场景参数总览】\n');
    fprintf(fid, '  道路长度: %.0f m\n', road.length);
    fprintf(fid, '  道路宽度: %.0f m\n', road.width);
    fprintf(fid, '  车位数量: %d 个\n', parking.num_spots);
    fprintf(fid, '  车位尺寸: %.1f m x %.1f m\n', parking.spot_length, parking.spot_width);
    fprintf(fid, '  目标车位: 第 %d 个（空置）\n', parking.target_spot);
    fprintf(fid, '  初始位置: (%.0f, %.0f) m\n\n', vehicle.init_x, vehicle.init_y);

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  步骤1: 新建工程\n');
    fprintf(fid, '====================================================\n\n');
    fprintf(fid, '  1. 打开 CarSim 2019.0\n');
    fprintf(fid, '  2. File → New → Dataset\n');
    fprintf(fid, '  3. Name: Parking_Reversing\n');
    fprintf(fid, '  4. Template: Vehicle: Sedan\n');
    fprintf(fid, '  5. 点击 OK\n\n');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  步骤2: 配置道路（必须修改）\n');
    fprintf(fid, '====================================================\n\n');
    fprintf(fid, '  路径: Procedure → Road Geometry\n\n');
    fprintf(fid, '  修改以下参数：\n');
    fprintf(fid, '  ┌─────────────────────────────────┐\n');
    fprintf(fid, '  │ Road Type:  Flat Road           │\n');
    fprintf(fid, '  │ Length:     %.0f m               │\n', road.length);
    fprintf(fid, '  │ Width:      %.0f m               │\n', road.width);
    fprintf(fid, '  │ Surface:    Dry Asphalt         │\n');
    fprintf(fid, '  │ Friction:   0.85                │\n');
    fprintf(fid, '  └─────────────────────────────────┘\n\n');
    fprintf(fid, '  点击 Apply 保存\n\n');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  步骤3: 配置停放车辆（必须修改）\n');
    fprintf(fid, '====================================================\n\n');
    fprintf(fid, '  路径: Environment → Moving Objects\n\n');
    fprintf(fid, '  为每个占用的车位添加静止车辆：\n\n');

    for i = 1:parking.num_spots
        if parking.occupancy(i) == 1
            x_center = (i - 0.5) * parking.spot_length;
            y_center = -parking.spot_width / 2;
            fprintf(fid, '  车位%d: X=%.1f, Y=%.1f, Yaw=90°\n', i, x_center, y_center);
        end
    end

    fprintf(fid, '\n  每辆车的设置：\n');
    fprintf(fid, '    Type: Vehicle (Sedan)\n');
    fprintf(fid, '    Motion: Stationary\n');
    fprintf(fid, '    Yaw: 90°\n\n');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  步骤4: 配置Simulink接口（必须修改）\n');
    fprintf(fid, '====================================================\n\n');
    fprintf(fid, '  4.1 导出S-Function\n');
    fprintf(fid, '      路径: Settings → Simulink\n');
    fprintf(fid, '      点击 "Export S-Function"\n');
    fprintf(fid, '      保存到: matlab/examples/parking-simulation/\n\n');

    fprintf(fid, '  4.2 配置输入通道\n');
    fprintf(fid, '      路径: Settings → Simulink → Input Channels\n');
    fprintf(fid, '      添加4个通道：\n');
    fprintf(fid, '        IMP_STEER_SW (deg)\n');
    fprintf(fid, '        IMP_PBK_CON (kPa)\n');
    fprintf(fid, '        IMP_THROTTLE (%%)\n');
    fprintf(fid, '        IMP_GEARCHANGE (-)\n\n');

    fprintf(fid, '  4.3 配置输出通道\n');
    fprintf(fid, '      路径: Settings → Simulink → Output Channels\n');
    fprintf(fid, '      添加6个通道：\n');
    fprintf(fid, '        XCG (m)\n');
    fprintf(fid, '        YCG (m)\n');
    fprintf(fid, '        YAW (rad)\n');
    fprintf(fid, '        VX (km/h)\n');
    fprintf(fid, '        VY (km/h)\n');
    fprintf(fid, '        AVZ (deg/s)\n\n');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  步骤5: 配置初始条件（必须修改）\n');
    fprintf(fid, '====================================================\n\n');
    fprintf(fid, '  路径: Procedure → Initial Conditions\n\n');
    fprintf(fid, '  修改以下参数：\n');
    fprintf(fid, '  ┌─────────────────────────────────┐\n');
    fprintf(fid, '  │ Initial X:    %.0f m             │\n', vehicle.init_x);
    fprintf(fid, '  │ Initial Y:    %.0f m             │\n', vehicle.init_y);
    fprintf(fid, '  │ Initial Yaw:  0°                │\n');
    fprintf(fid, '  │ Initial Speed: %.0f km/h         │\n', vehicle.init_speed);
    fprintf(fid, '  │ Initial Gear:  D1               │\n');
    fprintf(fid, '  └─────────────────────────────────┘\n\n');
    fprintf(fid, '  点击 Apply 保存\n\n');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  步骤6: 配置仿真事件（必须修改）\n');
    fprintf(fid, '====================================================\n\n');
    fprintf(fid, '  路径: Procedure → Events\n\n');
    fprintf(fid, '  创建3个事件：\n\n');

    fprintf(fid, '  Event 1 - 接近 (0-10s):\n');
    fprintf(fid, '    Speed: 5 km/h\n');
    fprintf(fid, '    Gear: D1\n\n');

    fprintf(fid, '  Event 2 - 停车 (10-12s):\n');
    fprintf(fid, '    Brake: 100%%\n');
    fprintf(fid, '    Speed: 0 km/h\n');
    fprintf(fid, '    Gear: N\n\n');

    fprintf(fid, '  Event 3 - 倒车 (12-50s):\n');
    fprintf(fid, '    Control: Simulink\n');
    fprintf(fid, '    Speed: -2 km/h\n');
    fprintf(fid, '    Gear: R\n\n');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  步骤7: 运行仿真\n');
    fprintf(fid, '====================================================\n\n');
    fprintf(fid, '  方法A: CarSim直接运行\n');
    fprintf(fid, '    Run → Run Simulation\n\n');

    fprintf(fid, '  方法B: MATLAB运行\n');
    fprintf(fid, '    cd matlab/examples/parking-simulation\n');
    fprintf(fid, '    run_parking_simulation\n\n');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  完成！\n');
    fprintf(fid, '====================================================\n');

    fclose(fid);

end
