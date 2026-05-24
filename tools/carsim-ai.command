#!/bin/bash
# CarSim-AI 一键启动器 (macOS)
# 用法：双击 .command 文件，或在终端运行 bash carsim-ai.command

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CARSIM_AI_DIR="$PROJECT_DIR/carsim-ai"
LAUNCHER_URL="https://lihongwei-cn.github.io/lihongwei-cn/carsim-ai/"

echo "========================================"
echo "  CarSim-AI 通用仿真工具"
echo "  CarSim 2019.0 兼容"
echo "========================================"
echo ""
echo "项目目录: $PROJECT_DIR"
echo "CarSim-AI 目录: $CARSIM_AI_DIR"
echo ""

# 检测 MATLAB 安装
MATLAB=""
for candidate in \
  "/Applications/MATLAB_R2024b.app/bin/matlab" \
  "/Applications/MATLAB_R2023b.app/bin/matlab" \
  "/Applications/MATLAB_R2022b.app/bin/matlab" \
  "/Applications/MATLAB_R2021b.app/bin/matlab" \
  "/Applications/MATLAB_R2020b.app/bin/matlab" \
  "/Applications/MATLAB_R2019b.app/bin/matlab" \
  "/Applications/MATLAB_R2018b.app/bin/matlab" \
  "/Applications/MATLAB_R2017b.app/bin/matlab" \
  "/Applications/MATLAB_R2016b.app/bin/matlab" \
  "/usr/local/bin/matlab"; do
  if [ -f "$candidate" ]; then
    MATLAB="$candidate"
    break
  fi
done

if [ -z "$MATLAB" ]; then
  echo "[X] 未检测到 MATLAB 安装"
  echo ""
  echo "请选择操作："
  echo "  1) 打开 CarSim-AI 项目网页"
  echo "  2) 手动输入 MATLAB 命令"
  echo "  3) 退出"
  echo ""
  read -p "输入选项 [1-3]: " choice

  case $choice in
    1)
      open "$LAUNCHER_URL"
      echo "已打开项目网页"
      ;;
    2)
      echo ""
      echo "请在 MATLAB 中依次执行："
      echo "  cd('$CARSIM_AI_DIR/examples')"
      echo "  % 设置参数"
      echo "  params.scene_type = 'bridge_slope';"
      echo "  params.bridge_length = 100;"
      echo "  params.output_dir = '../output';"
      echo "  % 运行仿真"
      echo "  run_simulation(params);"
      ;;
    *) echo "已退出" ;;
  esac
  exit 0
fi

echo "[OK] MATLAB: $MATLAB"
echo ""

# 显示菜单
echo "请选择启动模式："
echo "  1) 打开 MATLAB + 设置 CarSim-AI 环境"
echo "  2) 运行高架桥爬坡仿真（作业示例）"
echo "  3) 运行通用仿真工具"
echo "  4) 打开项目网页"
echo "  5) 查看可用仿真场景"
echo "  6) 退出"
echo ""
read -p "输入选项 [1-6]: " choice

case $choice in
  1)
    echo ""
    echo "启动 MATLAB 并设置 CarSim-AI 环境..."
    "$MATLAB" -nosplash -r "cd('$CARSIM_AI_DIR/examples'); disp('CarSim-AI 环境就绪'); disp('可用场景: bridge_slope, cornering, obstacle_avoidance, braking, acceleration'); disp('使用方法: run_simulation(params)');" &
    ;;
  2)
    echo ""
    echo "运行高架桥爬坡仿真..."
    "$MATLAB" -nosplash -r "cd('$CARSIM_AI_DIR/examples'); params.scene_type='bridge_slope'; params.bridge_length=100; params.bridge_width=8; params.slope_angle=15; params.friction=0.2; params.fwd_power=100; params.awd_power=100; params.output_dir='../output'; run_simulation(params);" &
    ;;
  3)
    echo ""
    echo "启动通用仿真工具..."
    "$MATLAB" -nosplash -r "cd('$CARSIM_AI_DIR/examples'); disp('CarSim-AI 通用仿真工具'); disp('请设置参数后调用 run_simulation(params)'); disp('示例:'); disp('  params.scene_type = ''bridge_slope'';'); disp('  params.bridge_length = 100;'); disp('  run_simulation(params);');" &
    ;;
  4)
    open "$LAUNCHER_URL"
    echo "已打开项目网页: $LAUNCHER_URL"
    ;;
  5)
    echo ""
    echo "可用仿真场景："
    echo "  bridge_slope          高架桥爬坡仿真"
    echo "    参数: bridge_length, bridge_width, slope_angle, friction"
    echo "    车辆: fwd_power, rwd_power, awd_power"
    echo ""
    echo "  cornering             弯道操控仿真"
    echo "    参数: curve_radius, curve_angle, road_width, vehicle_speed"
    echo ""
    echo "  obstacle_avoidance    紧急避障仿真"
    echo "    参数: obstacle_position, obstacle_width, lane_width, vehicle_speed"
    echo ""
    echo "  braking               制动性能仿真"
    echo "    参数: initial_speed, brake_distance, friction, vehicle_mass"
    echo ""
    echo "  acceleration          加速性能仿真"
    echo "    参数: target_speed, acceleration_distance, engine_power, vehicle_mass"
    echo ""
    echo "使用方法："
    echo "  params.scene_type = '场景名称';"
    echo "  params.参数名 = 值;"
    echo "  run_simulation(params);"
    echo ""
    read -p "按任意键返回菜单..."
    exec "$0"
    ;;
  *) echo "已退出" ;;
esac
