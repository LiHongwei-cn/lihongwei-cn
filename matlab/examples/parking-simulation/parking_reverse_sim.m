%% PARKING_REVERSE_SIM - 倒车入库纯MATLAB仿真
% 兼容版本：MATLAB R2016b
% 蒙多版：使用固定航向目标 + 倒车P控制
% 关键洞察：atan2归一化在大角度差时选择较短路径（54°），
%          但实际需要的是较长路径（306°顺时针）。
%          解决方案：不用atan2跟踪，直接用固定航向目标。

clear; clc; close all;

fprintf('============================================================\n');
fprintf('  倒车入库仿真 (蒙多版)\n');
fprintf('============================================================\n\n');

%% ==================== 参数 ====================
dt = 0.01;
N = 10000;

road.length = 50; road.width = 6;
road.num_spots = 10; road.spot_len = 5; road.spot_wid = 2.5;
road.occupancy = [1 1 1 1 0 1 1 1 1 1]; road.target = 5;

car.L = 4.5; car.W = 1.8; car.wheelbase = 2.7;
car.max_steer = 30 * pi / 180;

target_x = (road.target - 0.5) * road.spot_len;
target_y = -road.spot_wid / 2;

wp1 = [30; 3];
wp2 = [target_x; 0];
wp3 = [target_x; target_y];

% 参考路径（可视化用）
n_seg = 100;
p1x = linspace(45, wp1(1), n_seg); p1y = ones(1, n_seg) * 3;
s = linspace(0, 1, n_seg); poly = 10*s.^3 - 15*s.^4 + 6*s.^5;
p2x = wp1(1) + (wp2(1) - wp1(1)) * s;
p2y = wp1(2) + (wp2(2) - wp1(2)) * poly;
p3x = wp2(1) * ones(1, n_seg); p3y = linspace(wp2(2), wp3(2), n_seg);
ref_x = [p1x p2x p3x]; ref_y = [p1y p2y p3y];

%% ==================== 仿真 ====================
states = zeros(N, 4);
states(1,:) = [45, 3, pi, 5/3.6];

phase = 1;
sub_phase = 0;
fixed_yaw = 0;
fprintf('开始仿真...\n');

for k = 1:N-1
    x = states(k,1); y = states(k,2);
    yaw = states(k,3); v = states(k,4);

    % === 阶段1: 前进接近 ===
    if phase == 1
        goal = wp1; v_target = 5/3.6;
        err = wrap_angle(atan2(goal(2)-y, goal(1)-x) - yaw);
        steer = 0.8 * err;
        steer = max(-car.max_steer, min(car.max_steer, steer));
        if x <= wp1(1) + 0.3
            phase = 2;
            fprintf('  t=%.1fs: 阶段2\n', k*dt);
        end

    % === 阶段2: 前进转弯 ===
    elseif phase == 2
        goal = wp2; v_target = 2/3.6;
        err = wrap_angle(atan2(goal(2)-y, goal(1)-x) - yaw);
        steer = 0.8 * err;
        steer = max(-car.max_steer, min(car.max_steer, steer));
        d2 = sqrt((x-wp2(1))^2 + (y-wp2(2))^2);
        if d2 < 0.3
            phase = 3; sub_phase = 0;
            % 固定目标航向：从入口到车位中心
            fixed_yaw = atan2(wp3(2)-y, wp3(1)-x);
            fprintf('  t=%.1fs: 阶段3, yaw=%.0f target=%.0f\n', k*dt, yaw*180/pi, fixed_yaw*180/pi);
        end

    % === 阶段3: 倒车入库 ===
    else
        if sub_phase == 0
            % 子阶段0: 低速前进，旋转到固定航向
            v_target = 1.0/3.6;
            err = wrap_angle(fixed_yaw - yaw);
            steer = 0.8 * err;
            steer = max(-car.max_steer, min(car.max_steer, steer));
            if abs(err) < 3 * pi / 180
                sub_phase = 1;
                fprintf('  t=%.1fs: 旋转完成, yaw=%.0f\n', k*dt, yaw*180/pi);
            end
        else
            % 子阶段1: 倒车直线入库
            % 此时航向已对准车位，倒车时只需微调
            v_target = -1.0/3.6;
            desired = atan2(wp3(2)-y, wp3(1)-x);
            err = wrap_angle(desired - yaw);
            % 倒车时 yaw_rate = v*tan(steer)/L, v<0 所以效果反转
            % 需要 steer = err（不是 -err）来产生正确的旋转方向
            steer = 1.0 * err;
            steer = max(-car.max_steer, min(car.max_steer, steer));
            d3 = sqrt((x-wp3(1))^2 + (y-wp3(2))^2);
            if d3 < 0.2
                fprintf('  t=%.1fs: 到达！误差=%.3fm\n', k*dt, d3);
                break;
            end
        end
    end

    % === 速度控制 ===
    acc = 2.0 * (v_target - v);
    acc = max(-3, min(3, acc));

    % === 运动学 ===
    states(k+1,1) = x + v * cos(yaw) * dt;
    states(k+1,2) = y + v * sin(yaw) * dt;
    states(k+1,3) = yaw + v * tan(steer) / car.wheelbase * dt;
    states(k+1,4) = max(-5/3.6, min(8/3.6, v + acc * dt));
end

valid = min(k, N);
states = states(1:valid,:);
time = (0:valid-1)' * dt;
fprintf('仿真完成，%.1f 秒\n\n', time(end));

%% ==================== 结果 ====================
fx = states(end,1); fy = states(end,2);
pos_err = sqrt((fx-target_x)^2 + (fy-target_y)^2);
fprintf('============================================================\n');
fprintf('  最终位置: (%.2f, %.2f)\n', fx, fy);
fprintf('  目标位置: (%.2f, %.2f)\n', target_x, target_y);
fprintf('  位置误差: %.3f m\n', pos_err);
fprintf('  最终航向: %.1f deg\n', mod(states(end,3)*180/pi+360, 360));
if pos_err < 0.3, fprintf('  精度: 优秀\n');
elseif pos_err < 0.5, fprintf('  精度: 良好\n');
elseif pos_err < 1.0, fprintf('  精度: 一般\n');
else, fprintf('  精度: 需改进\n');
end
fprintf('============================================================\n');

%% ==================== 可视化 ====================
fprintf('\n绘制结果...\n');
figure('Name','倒车入库','Position',[50 50 1400 900],'Color','w');

subplot(2,2,[1,3]); hold on;
fill([0 road.length road.length 0],[0 0 road.width road.width],[.7 .7 .7]);
plot([0 road.length],[0 0],'w-','LineWidth',3);
plot([0 road.length],[road.width road.width],'w-','LineWidth',3);
for i = 1:road.num_spots
    sx = (i-1)*road.spot_len; sy = -road.spot_wid;
    if road.occupancy(i)==1
        fill([sx sx+road.spot_len sx+road.spot_len sx],[sy sy sy+road.spot_wid sy+road.spot_wid],[.5 .5 .6]);
        rectangle('Position',[sx+.25 sy+.25 road.spot_len-.5 road.spot_wid-.5],'FaceColor',[.3 .3 .7],'EdgeColor','k');
    else
        fill([sx sx+road.spot_len sx+road.spot_len sx],[sy sy sy+road.spot_wid sy+road.spot_wid],[.85 1 .85],'EdgeColor',[0 .6 0],'LineWidth',2,'LineStyle','--');
        text(sx+road.spot_len/2,sy+road.spot_wid/2,'空','HorizontalAlignment','center','FontSize',14,'FontWeight','bold','Color',[0 .5 0]);
    end
end
plot(ref_x(1:100),ref_y(1:100),'g--','LineWidth',1.5);
plot(ref_x(101:200),ref_y(101:200),'y--','LineWidth',1.5);
plot(ref_x(201:300),ref_y(201:300),'r--','LineWidth',1.5);
plot(states(:,1),states(:,2),'b-','LineWidth',2);
draw_car(45,3,pi,car,[.8 .8 .8],.5);
draw_car(fx,fy,states(end,3),car,[0 .8 0],.8);
plot(45,3,'go','MarkerSize',12,'MarkerFaceColor','g');
plot(fx,fy,'rs','MarkerSize',12,'MarkerFaceColor','r');
plot(target_x,target_y,'mx','MarkerSize',15,'LineWidth',3);
xlabel('X [m]'); ylabel('Y [m]'); title('倒车入库');
legend('道路','','','','接近','转弯','入库','轨迹','起始','终点','目标','Location','ne');
grid on; axis equal; xlim([-2 road.length+2]); ylim([-road.spot_wid-2 road.width+2]);

subplot(2,2,2);
plot(time,states(:,4)*3.6,'b-','LineWidth',1.5);
xlabel('时间 [s]'); ylabel('速度 [km/h]'); title('速度'); grid on;

subplot(2,2,4);
plot(time,states(:,3)*180/pi,'b-','LineWidth',1.5);
xlabel('时间 [s]'); ylabel('航向 [deg]'); title('航向'); grid on;

saveas(gcf,'parking_simulation_results.png');
fprintf('图片已保存\n\n完成！\n');

%% ==================== 辅助函数 ====================
function a = wrap_angle(a)
    a = mod(a + pi, 2*pi) - pi;
end

function draw_car(x,y,yaw,car,color,fa)
    c=[car.L/2 car.W/2;car.L/2 -car.W/2;-car.L/2 -car.W/2;-car.L/2 car.W/2;car.L/2 car.W/2];
    R=[cos(yaw) -sin(yaw);sin(yaw) cos(yaw)];
    r=(R*c')';
    fill(r(:,1)+x,r(:,2)+y,color,'FaceAlpha',fa,'EdgeColor','k');
end
