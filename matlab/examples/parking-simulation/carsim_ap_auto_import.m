%% CARSIM_AP_AUTO_IMPORT - CarSim自动泊车自动导入脚本
% 基于B站教程: BV1xk4y1b7y8
% 兼容版本：CarSim 2019.0 + MATLAB 2021b (兼容R2016b)
% 功能：自动生成并导入CarSim数据文件，配置自动泊车仿真
%
% 作者：LiHongwei
% 日期：2026-05-29

clear; clc; close all;

fprintf('============================================================\n');
fprintf('  CarSim 2019 自动泊车 - 自动导入工具\n');
fprintf('  基于B站教程: BV1xk4y1b7y8\n');
fprintf('============================================================\n\n');

%% ==================== 获取脚本所在目录 ====================

% 自动切换到脚本所在目录（解决MATLAB工作目录问题）
script_dir = fileparts(mfilename('fullpath'));
if ~isempty(script_dir)
    cd(script_dir);
end
fprintf('当前工作目录: %s\n\n', pwd);

%% ==================== 配置参数 ====================

fprintf('[步骤1/8] 加载配置参数...\n');

% 场景参数
config.scene_name = 'Parking_Reversing';
config.description = '倒车入库APA自动泊车仿真';

% 道路参数
config.road.length = 50;           % 道路长度 [m]
config.road.width = 6;             % 道路宽度 [m]
config.road.lane_width = 3;        % 单车道宽度 [m]

% 车位参数
config.parking.spot_length = 5;    % 车位长度 [m]
config.parking.spot_width = 2.5;   % 车位宽度 [m]
config.parking.num_spots = 10;     % 车位数量
config.parking.target_spot = 5;    % 目标车位（空置）
config.parking.occupancy = [1, 1, 1, 1, 0, 1, 1, 1, 1, 1];

% 车辆初始条件
config.vehicle.init_x = 45;       % 初始X位置 [m]
config.vehicle.init_y = 3;        % 初始Y位置 [m]
config.vehicle.init_yaw = 0;      % 初始航向角 [deg]
config.vehicle.init_speed = 5;    % 初始速度 [km/h]

% 仿真参数
config.sim.total_time = 60;       % 总仿真时间 [s]
config.sim.dt = 0.001;            % 仿真步长 [s]

fprintf('   ✓ 配置参数加载完成\n');

%% ==================== 生成CarSim数据集文件 ====================

fprintf('[步骤2/8] 生成CarSim数据集文件...\n');

% 生成多种格式的数据文件
generate_carsim_dataset_files(config);

fprintf('   ✓ 数据集文件生成完成\n');

%% ==================== 生成道路几何文件 ====================

fprintf('[步骤3/8] 生成道路几何文件...\n');

generate_road_geometry_file(config);

fprintf('   ✓ 道路几何文件生成完成\n');

%% ==================== 生成障碍物文件 ====================

fprintf('[步骤4/8] 生成车位障碍物文件...\n');

generate_obstacles_file(config);

fprintf('   ✓ 障碍物文件生成完成\n');

%% ==================== 生成车辆参数文件 ====================

fprintf('[步骤5/8] 生成车辆参数文件...\n');

generate_vehicle_params_file(config);

fprintf('   ✓ 车辆参数文件生成完成\n');

%% ==================== 生成仿真控制文件 ====================

fprintf('[步骤6/8] 生成仿真控制文件...\n');

generate_sim_control_file(config);

fprintf('   ✓ 仿真控制文件生成完成\n');

%% ==================== 生成Simulink接口文件 ====================

fprintf('[步骤7/8] 生成Simulink接口配置文件...\n');

generate_simulink_interface_file(config);

fprintf('   ✓ Simulink接口文件生成完成\n');

%% ==================== 生成自动导入脚本 ====================

fprintf('[步骤8/8] 生成自动导入脚本...\n');

generate_auto_import_scripts(config);

fprintf('   ✓ 自动导入脚本生成完成\n');

%% ==================== 显示生成的文件列表 ====================

fprintf('\n============================================================\n');
fprintf('  所有文件生成完成！\n');
fprintf('============================================================\n\n');

fprintf('生成的文件列表：\n');
fprintf('─────────────────────────────────────────────────────────────\n');

files = dir('*.cpar');
for i = 1:length(files)
    fprintf('  📄 %s (%d bytes)\n', files(i).name, files(i).bytes);
end

files = dir('*.m');
for i = 1:length(files)
    if contains(files(i).name, 'import') || contains(files(i).name, 'auto')
        fprintf('  📄 %s (%d bytes)\n', files(i).name, files(i).bytes);
    end
end

files = dir('*.txt');
for i = 1:length(files)
    fprintf('  📄 %s (%d bytes)\n', files(i).name, files(i).bytes);
end

fprintf('\n============================================================\n');
fprintf('  使用方法\n');
fprintf('============================================================\n\n');

fprintf('【方法1】在CarSim中手动导入（推荐）\n');
fprintf('  1. 打开 CarSim 2019.0\n');
fprintf('  2. File → Import Dataset\n');
fprintf('  3. 选择 Parking_Reversing.cpar\n');
fprintf('  4. 点击 OK 确认导入\n\n');

fprintf('【方法2】使用MATLAB自动导入\n');
fprintf('  1. 确保CarSim 2019.0已打开\n');
fprintf('  2. 在MATLAB中运行: import_to_carsim_auto\n');
fprintf('  3. 等待自动导入完成\n\n');

fprintf('【方法3】双击批处理文件（Windows）\n');
fprintf('  双击运行: run_import.bat\n\n');

fprintf('============================================================\n');
fprintf('  导入后配置检查\n');
fprintf('============================================================\n\n');

fprintf('导入完成后，在CarSim中检查：\n');
fprintf('  ✓ Procedure → Road Geometry: 道路50m × 6m\n');
fprintf('  ✓ Environment → Moving Objects: 9辆停放车辆\n');
fprintf('  ✓ Procedure → Initial Conditions: X=45, Y=3\n');
fprintf('  ✓ Settings → Simulink: 输入输出通道\n');
fprintf('  ✓ Procedure → Events: 3个仿真事件\n\n');

fprintf('配置检查通过后，运行仿真：\n');
fprintf('  方法A: Run → Run Simulation (CarSim中)\n');
fprintf('  方法B: run_parking_simulation (MATLAB中)\n\n');

%% ==================== 辅助函数 ====================

function generate_carsim_dataset_files(config)
% 生成CarSim数据集文件

    % 主CPAR文件
    cpar_file = [config.scene_name '.cpar'];
    fid = fopen(cpar_file, 'w', 'n', 'UTF-8');

    fprintf(fid, '<?xml version="1.0" encoding="UTF-8"?>\n');
    fprintf(fid, '<CarSimParameters version="2019.0">\n');
    fprintf(fid, '  <Metadata>\n');
    fprintf(fid, '    <Name>%s</Name>\n', config.scene_name);
    fprintf(fid, '    <Description>%s</Description>\n', config.description);
    fprintf(fid, '    <Author>MATLAB Auto Generator</Author>\n');
    fprintf(fid, '    <Date>%s</Date>\n', datestr(now, 'yyyy-mm-dd'));
    fprintf(fid, '    <Version>1.0</Version>\n');
    fprintf(fid, '  </Metadata>\n\n');

    % 车辆参数
    fprintf(fid, '  <Vehicle>\n');
    fprintf(fid, '    <Body>\n');
    fprintf(fid, '      <Mass>1500</Mass>\n');
    fprintf(fid, '      <Length>4.5</Length>\n');
    fprintf(fid, '      <Width>1.8</Width>\n');
    fprintf(fid, '      <Height>1.5</Height>\n');
    fprintf(fid, '      <Wheelbase>2.7</Wheelbase>\n');
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
    fprintf(fid, '      <Length>%.1f</Length>\n', config.road.length);
    fprintf(fid, '      <Width>%.1f</Width>\n', config.road.width);
    fprintf(fid, '      <NumLanes>2</NumLanes>\n');
    fprintf(fid, '      <LaneWidth>%.1f</LaneWidth>\n', config.road.lane_width);
    fprintf(fid, '    </Geometry>\n');
    fprintf(fid, '    <Surface>\n');
    fprintf(fid, '      <Type>DryAsphalt</Type>\n');
    fprintf(fid, '      <Friction>0.85</Friction>\n');
    fprintf(fid, '    </Surface>\n');
    fprintf(fid, '  </Road>\n\n');

    % 车位配置
    fprintf(fid, '  <ParkingSpots>\n');
    fprintf(fid, '    <NumSpots>%d</NumSpots>\n', config.parking.num_spots);
    fprintf(fid, '    <SpotLength>%.1f</SpotLength>\n', config.parking.spot_length);
    fprintf(fid, '    <SpotWidth>%.1f</SpotWidth>\n', config.parking.spot_width);
    fprintf(fid, '    <TargetSpot>%d</TargetSpot>\n', config.parking.target_spot);

    for i = 1:config.parking.num_spots
        fprintf(fid, '    <Spot id="%d">\n', i);
        fprintf(fid, '      <X>%.1f</X>\n', (i - 0.5) * config.parking.spot_length);
        fprintf(fid, '      <Y>%.1f</Y>\n', -config.parking.spot_width / 2);
        fprintf(fid, '      <Occupied>%d</Occupied>\n', config.parking.occupancy(i));
        fprintf(fid, '    </Spot>\n');
    end
    fprintf(fid, '  </ParkingSpots>\n\n');

    % 停放车辆
    fprintf(fid, '  <StaticVehicles>\n');
    vehicle_id = 0;
    for i = 1:config.parking.num_spots
        if config.parking.occupancy(i) == 1
            vehicle_id = vehicle_id + 1;
            x_center = (i - 0.5) * config.parking.spot_length;
            y_center = -config.parking.spot_width / 2;
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
    fprintf(fid, '    <X>%.1f</X>\n', config.vehicle.init_x);
    fprintf(fid, '    <Y>%.1f</Y>\n', config.vehicle.init_y);
    fprintf(fid, '    <Yaw>%.1f</Yaw>\n', config.vehicle.init_yaw);
    fprintf(fid, '    <Speed>%.1f</Speed>\n', config.vehicle.init_speed);
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
    fprintf(fid, '      <Duration>48</Duration>\n');
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

function generate_road_geometry_file(config)
% 生成道路几何配置文件

    filename = 'road_geometry.txt';
    fid = fopen(filename, 'w');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  CarSim 道路几何配置\n');
    fprintf(fid, '====================================================\n\n');

    fprintf(fid, '【道路参数】\n');
    fprintf(fid, '  道路类型: Flat Road (平直道路)\n');
    fprintf(fid, '  道路长度: %.0f m\n', config.road.length);
    fprintf(fid, '  道路宽度: %.0f m\n', config.road.width);
    fprintf(fid, '  车道数量: 2\n');
    fprintf(fid, '  单车道宽度: %.0f m\n', config.road.lane_width);
    fprintf(fid, '  路面类型: Dry Asphalt\n');
    fprintf(fid, '  摩擦系数: 0.85\n\n');

    fprintf(fid, '【CarSim设置步骤】\n');
    fprintf(fid, '  1. 路径: Procedure → Road Geometry\n');
    fprintf(fid, '  2. 设置道路类型: Flat Road\n');
    fprintf(fid, '  3. 设置长度: %.0f m\n', config.road.length);
    fprintf(fid, '  4. 设置宽度: %.0f m\n', config.road.width);
    fprintf(fid, '  5. 设置路面: Dry Asphalt\n');
    fprintf(fid, '  6. 点击 Apply 保存\n');

    fclose(fid);

end

function generate_obstacles_file(config)
% 生成障碍物配置文件

    filename = 'obstacles_config.txt';
    fid = fopen(filename, 'w');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  CarSim 车位障碍物配置\n');
    fprintf(fid, '====================================================\n\n');

    fprintf(fid, '【车位参数】\n');
    fprintf(fid, '  车位数量: %d\n', config.parking.num_spots);
    fprintf(fid, '  车位长度: %.1f m\n', config.parking.spot_length);
    fprintf(fid, '  车位宽度: %.1f m\n', config.parking.spot_width);
    fprintf(fid, '  目标车位: 第 %d 个\n\n', config.parking.target_spot);

    fprintf(fid, '【障碍物设置】\n');
    fprintf(fid, '  类型: Barrier (护栏)\n');
    fprintf(fid, '  宽度: 0.15 m\n');
    fprintf(fid, '  高度: 0.05 m\n');
    fprintf(fid, '  颜色: White\n\n');

    fprintf(fid, '【车位位置坐标】\n');

    for i = 1:config.parking.num_spots
        x_start = (i - 1) * config.parking.spot_length;
        x_end = i * config.parking.spot_length;
        y_start = -config.parking.spot_width;
        y_end = 0;

        fprintf(fid, '\n车位 %d:\n', i);
        fprintf(fid, '  起始X: %.1f m\n', x_start);
        fprintf(fid, '  结束X: %.1f m\n', x_end);
        fprintf(fid, '  上边Y: %.1f m\n', y_start);
        fprintf(fid, '  下边Y: %.1f m\n', y_end);
        fprintf(fid, '  状态: %s\n', iif(config.parking.occupancy(i) == 1, '占用', '空置'));
    end

    fclose(fid);

end

function generate_vehicle_params_file(config)
% 生成车辆参数文件

    filename = 'vehicle_params.txt';
    fid = fopen(filename, 'w');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  CarSim 车辆参数配置\n');
    fprintf(fid, '====================================================\n\n');

    fprintf(fid, '【车辆基本参数】\n');
    fprintf(fid, '  类型: Sedan (轿车)\n');
    fprintf(fid, '  质量: 1500 kg\n');
    fprintf(fid, '  车长: 4.5 m\n');
    fprintf(fid, '  车宽: 1.8 m\n');
    fprintf(fid, '  车高: 1.5 m\n');
    fprintf(fid, '  轴距: 2.7 m\n\n');

    fprintf(fid, '【传动系统】\n');
    fprintf(fid, '  发动机扭矩: 250 Nm\n');
    fprintf(fid, '  变速箱: 6速自动\n');
    fprintf(fid, '  主减速比: 3.5\n');
    fprintf(fid, '  倒档速比: 3.2\n\n');

    fprintf(fid, '【制动系统】\n');
    fprintf(fid, '  前制动增益: 250 Nm/MPa\n');
    fprintf(fid, '  后制动增益: 150 Nm/MPa\n');
    fprintf(fid, '  最大制动压力: 15 MPa\n');
    fprintf(fid, '  ABS: 启用\n\n');

    fprintf(fid, '【转向系统】\n');
    fprintf(fid, '  转向比: 16\n');
    fprintf(fid, '  最大转向角: 540°\n');
    fprintf(fid, '  助力转向: 启用\n\n');

    fprintf(fid, '【初始条件】\n');
    fprintf(fid, '  初始X: %.0f m\n', config.vehicle.init_x);
    fprintf(fid, '  初始Y: %.0f m\n', config.vehicle.init_y);
    fprintf(fid, '  初始航向角: %.0f°\n', config.vehicle.init_yaw);
    fprintf(fid, '  初始速度: %.0f km/h\n', config.vehicle.init_speed);
    fprintf(fid, '  初始档位: D1 (前进1档)\n');

    fclose(fid);

end

function generate_sim_control_file(config)
% 生成仿真控制文件

    filename = 'sim_control.txt';
    fid = fopen(filename, 'w');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  CarSim 仿真控制配置\n');
    fprintf(fid, '====================================================\n\n');

    fprintf(fid, '【仿真参数】\n');
    fprintf(fid, '  总仿真时间: %.0f s\n', config.sim.total_time);
    fprintf(fid, '  仿真步长: %.3f s\n', config.sim.dt);
    fprintf(fid, '  求解器: Fixed Step\n');
    fprintf(fid, '  输出频率: 100 Hz\n\n');

    fprintf(fid, '【仿真事件序列】\n\n');

    fprintf(fid, '事件1 - 接近阶段 (0-10s):\n');
    fprintf(fid, '  速度: 5 km/h\n');
    fprintf(fid, '  档位: D1 (前进1档)\n');
    fprintf(fid, '  转向: 直行\n\n');

    fprintf(fid, '事件2 - 准备阶段 (10-12s):\n');
    fprintf(fid, '  制动: 100%% (全力制动)\n');
    fprintf(fid, '  速度: 0 km/h (停车)\n');
    fprintf(fid, '  档位: N (空档)\n\n');

    fprintf(fid, '事件3 - 倒车入库 (12-60s):\n');
    fprintf(fid, '  控制模式: Simulink\n');
    fprintf(fid, '  初始速度: -2 km/h (倒车)\n');
    fprintf(fid, '  档位: R (倒档)\n');
    fprintf(fid, '  转向: Simulink控制\n');
    fprintf(fid, '  制动: Simulink控制\n\n');

    fprintf(fid, '【CarSim设置步骤】\n');
    fprintf(fid, '  1. 路径: Procedure → Initial Conditions\n');
    fprintf(fid, '     设置初始位置和速度\n');
    fprintf(fid, '  2. 路径: Procedure → Events\n');
    fprintf(fid, '     创建3个事件（接近、准备、倒车）\n');
    fprintf(fid, '  3. 路径: Settings → Simulation\n');
    fprintf(fid, '     设置仿真时间和步长\n');

    fclose(fid);

end

function generate_simulink_interface_file(config)
% 生成Simulink接口配置文件

    filename = 'simulink_interface.txt';
    fid = fopen(filename, 'w');

    fprintf(fid, '====================================================\n');
    fprintf(fid, '  CarSim Simulink接口配置\n');
    fprintf(fid, '====================================================\n\n');

    fprintf(fid, '【S-Function导出】\n');
    fprintf(fid, '  路径: Settings → Simulink\n');
    fprintf(fid, '  点击: Export S-Function\n');
    fprintf(fid, '  文件名: sf_car_sim.mexw64\n');
    fprintf(fid, '  保存位置: matlab/examples/parking-simulation/\n\n');

    fprintf(fid, '【输入通道配置】\n');
    fprintf(fid, '  路径: Settings → Simulink → Input Channels\n\n');
    fprintf(fid, '  通道1:\n');
    fprintf(fid, '    名称: IMP_STEER_SW\n');
    fprintf(fid, '    单位: deg (度)\n');
    fprintf(fid, '    默认值: 0\n');
    fprintf(fid, '    说明: 方向盘转角\n\n');

    fprintf(fid, '  通道2:\n');
    fprintf(fid, '    名称: IMP_PBK_CON\n');
    fprintf(fid, '    单位: kPa (千帕)\n');
    fprintf(fid, '    默认值: 0\n');
    fprintf(fid, '    说明: 制动主缸压力\n\n');

    fprintf(fid, '  通道3:\n');
    fprintf(fid, '    名称: IMP_THROTTLE\n');
    fprintf(fid, '    单位: %% (百分比)\n');
    fprintf(fid, '    默认值: 0\n');
    fprintf(fid, '    说明: 油门开度\n\n');

    fprintf(fid, '  通道4:\n');
    fprintf(fid, '    名称: IMP_GEARCHANGE\n');
    fprintf(fid, '    单位: - (无单位)\n');
    fprintf(fid, '    默认值: 0\n');
    fprintf(fid, '    说明: 档位命令 (-1=R, 0=N, 1-6=D)\n\n');

    fprintf(fid, '【输出通道配置】\n');
    fprintf(fid, '  路径: Settings → Simulink → Output Channels\n\n');
    fprintf(fid, '  通道1: XCG (m) - X位置\n');
    fprintf(fid, '  通道2: YCG (m) - Y位置\n');
    fprintf(fid, '  通道3: YAW (rad) - 航向角\n');
    fprintf(fid, '  通道4: VX (km/h) - 纵向速度\n');
    fprintf(fid, '  通道5: VY (km/h) - 横向速度\n');
    fprintf(fid, '  通道6: AVZ (deg/s) - 横摆角速度\n\n');

    fprintf(fid, '【验证步骤】\n');
    fprintf(fid, '  1. 确认S-Function已导出\n');
    fprintf(fid, '  2. 确认输入通道4个\n');
    fprintf(fid, '  3. 确认输出通道6个\n');
    fprintf(fid, '  4. 点击 Apply 保存\n');

    fclose(fid);

end

function generate_auto_import_scripts(config)
% 生成自动导入脚本

    % MATLAB自动导入脚本
    import_script = 'import_to_carsim_auto.m';
    fid = fopen(import_script, 'w');

    fprintf(fid, '%% IMPORT_TO_CARSIM_AUTO - 自动导入配置到CarSim\n');
    fprintf(fid, '%% 基于B站教程: BV1xk4y1b7y8\n');
    fprintf(fid, '%% 兼容版本：CarSim 2019.0 + MATLAB R2016b\n');
    fprintf(fid, '%%\n');
    fprintf(fid, '%% 作者：LiHongwei\n');
    fprintf(fid, '%% 日期：%s\n\n', datestr(now));

    fprintf(fid, 'clear; clc;\n\n');

    fprintf(fid, '%% 切换到脚本所在目录\n');
    fprintf(fid, 'script_dir = fileparts(mfilename(''fullpath''));\n');
    fprintf(fid, 'if ~isempty(script_dir)\n');
    fprintf(fid, '    cd(script_dir);\n');
    fprintf(fid, 'end\n\n');

    fprintf(fid, 'fprintf(''============================================================\\n'');\n');
    fprintf(fid, 'fprintf(''  CarSim 自动导入工具\\n'');\n');
    fprintf(fid, 'fprintf(''============================================================\\n\\n'');\n\n');

    fprintf(fid, '%% CPAR文件路径\n');
    fprintf(fid, 'cpar_file = ''%s.cpar'';\n\n', config.scene_name);

    fprintf(fid, '%% 检查文件是否存在\n');
    fprintf(fid, 'if ~exist(cpar_file, ''file'')\n');
    fprintf(fid, '    error(''CPAR文件不存在: %s\\n请先运行 carsim_ap_auto_import.m 生成配置文件'', cpar_file);\n');
    fprintf(fid, 'end\n\n');

    fprintf(fid, 'fprintf(''找到CPAR文件: %s\\n'', cpar_file);\n\n');

    fprintf(fid, '%% 尝试通过COM接口连接CarSim\n');
    fprintf(fid, 'try\n');
    fprintf(fid, '    fprintf(''\\n尝试连接CarSim...\\n'');\n');
    fprintf(fid, '    h = actxserver(''CarSim.Application'');\n');
    fprintf(fid, '    fprintf(''✓ 成功连接CarSim\\n'');\n\n');

    fprintf(fid, '    %% 导入CPAR文件\n');
    fprintf(fid, '    fprintf(''正在导入CPAR文件...\\n'');\n');
    fprintf(fid, '    h.ImportDataset(fullfile(pwd, cpar_file));\n');
    fprintf(fid, '    fprintf(''✓ CPAR文件导入成功\\n'');\n\n');

    fprintf(fid, '    %% 关闭COM连接\n');
    fprintf(fid, '    h.release;\n');
    fprintf(fid, '    fprintf(''\\n✓ 导入完成！\\n'');\n');
    fprintf(fid, '    fprintf(''请在CarSim中查看 Parking_Reversing 数据集\\n'');\n\n');

    fprintf(fid, 'catch ME\n');
    fprintf(fid, '    fprintf(''\\n无法通过COM连接CarSim\\n'');\n');
    fprintf(fid, '    fprintf(''错误信息: %s\\n'', ME.message);\n');
    fprintf(fid, '    fprintf(''\\n请手动导入：\\n'');\n');
    fprintf(fid, '    fprintf(''1. 打开CarSim 2019.0\\n'');\n');
    fprintf(fid, '    fprintf(''2. 点击 File → Import Dataset\\n'');\n');
    fprintf(fid, '    fprintf(''3. 选择文件: %s\\n'', fullfile(pwd, cpar_file));\n');
    fprintf(fid, '    fprintf(''4. 点击 OK 确认导入\\n'');\n');
    fprintf(fid, 'end\n');

    fclose(fid);

    % Windows批处理脚本
    bat_script = 'run_import.bat';
    fid = fopen(bat_script, 'w');

    fprintf(fid, '@echo off\n');
    fprintf(fid, 'echo ============================================================\n');
    fprintf(fid, 'echo   CarSim 自动导入工具\n');
    fprintf(fid, 'echo ============================================================\n');
    fprintf(fid, 'echo.\n');

    fprintf(fid, 'cd /d "%%~dp0"\n');
    fprintf(fid, 'echo 当前目录: %%CD%%\n');
    fprintf(fid, 'echo.\n');

    fprintf(fid, 'echo 正在运行MATLAB导入脚本...\n');
    fprintf(fid, '"C:\\Program Files\\MATLAB\\R2016b\\bin\\matlab.exe" -batch "run(''import_to_carsim_auto.m'')"\n');
    fprintf(fid, 'echo.\n');

    fprintf(fid, 'echo 导入完成！\n');
    fprintf(fid, 'pause\n');

    fclose(fid);

end

function result = iif(condition, true_val, false_val)
% 条件判断函数
    if condition
        result = true_val;
    else
        result = false_val;
    end
end
