# MATLAB 全中文输出规范

## 用户铁律

> "输出后的内容能使用中文的地方全部使用中文，代码部分保留正常格式"

## 中文输出清单

| 输出类型 | 中文示例 | 英文禁止 |
|---------|---------|---------|
| xlabel | `xlabel('时间 (s)')` | ~~`xlabel('Time [s]')`~~ |
| ylabel | `ylabel('车速 (km/h)')` | ~~`ylabel('Speed [km/h]')`~~ |
| title | `title('纵向轨迹')` | ~~`title('Longitudinal Trajectory')`~~ |
| legend | `legend('车辆','障碍物')` | ~~`legend('Vehicle','Obstacle')`~~ |
| fprintf | `fprintf('最高车速: %.1f km/h\n', ...)` | ~~`fprintf('Max speed: ...')`~~ |
| 注释 | `% 前向欧拉积分` | ~~`% Forward Euler`~~ |

## 不使用中文的地方

- 变量名、函数名、文件名 → 保持英文
- 单位符号 → 国际标准（s, m, km/h, Nm, A, V）

## 常用中文标签速查

| 物理量 | ylabel 写法 |
|--------|-----------|
| 时间 | `xlabel('时间 (s)')` 或 `xlabel('时间 (min)')` |
| 车速 | `ylabel('车速 (km/h)')` |
| 转速 | `ylabel('转速 (rpm)')` |
| 转矩 | `ylabel('转矩 (Nm)')` |
| 电流 | `ylabel('电流 (A)')` |
| 电压 | `ylabel('电压 (V)')` |
| 功率 | `ylabel('功率 (kW)')` |
| 能耗 | `ylabel('能耗 (Wh)')` 或 `ylabel('能耗 (kWh)')` |
| SOC | `ylabel('SOC (%)')` |
| 位置 | `ylabel('位置 (m)')` |
| 距离 | `ylabel('距离 (m)')` |
| 偏移 | `ylabel('偏移 (m)')` |
| 加速度 | `ylabel('加速度 (m/s^2)')` |

## 图表合并规范

用户明确要求："所有的图表内容放在一起"

- 相关图表用 subplot 合并到一个 figure
- 不单独弹窗
- 已验证：ADAS HIL Demo 8 个子图合并为 1 张大图（4行2列）

## 控制台报告模板

```matlab
fprintf('\n');
fprintf('========================================\n');
fprintf('  [仿真名称] 仿真结果\n');
fprintf('  日期: %s\n', datestr(now));
fprintf('========================================\n');
fprintf('  最高车速: %.1f km/h\n', max(v)*3.6);
fprintf('  行驶距离: %.2f km\n', s(end)/1000);
fprintf('  能耗: %.1f kWh/100km\n', E_cons(end)/(s(end)/1000)/10);
fprintf('  剩余SOC: %.1f%%\n', SOC(end)*100);
fprintf('========================================\n');
```
