#!/bin/bash
# MATLAB-AI 一键启动器 (macOS)
# 用法：双击 .command 文件，或在终端运行 bash matlab-ai.command

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MATLAB_DIR="$PROJECT_DIR/matlab"
LAUNCHER_URL="https://lihongwei-cn.github.io/lihongwei-cn/matlab-ai/"

echo "========================================"
echo "  MATLAB-AI 新能源汽车仿真工具包"
echo "========================================"
echo ""
echo "项目目录: $PROJECT_DIR"
echo "MATLAB 目录: $MATLAB_DIR"
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
  echo "  1) 打开 MATLAB-AI 启动器网页（可视化选择脚本）"
  echo "  2) 手动输入 MATLAB 命令"
  echo "  3) 退出"
  echo ""
  read -p "输入选项 [1-3]: " choice

  case $choice in
    1)
      open "$LAUNCHER_URL"
      echo "已打开启动器网页"
      ;;
    2)
      echo ""
      echo "请在 MATLAB 中依次执行："
      echo "  cd('$MATLAB_DIR')"
      echo "  startup_setup"
      echo "  % 然后运行任意示例脚本，如："
      echo "  motor_control"
      echo "  vehicle_dynamics"
      echo "  battery_soc_ekf"
      ;;
    *) echo "已退出" ;;
  esac
  exit 0
fi

echo "[OK] MATLAB: $MATLAB"
echo ""

# 显示菜单
echo "请选择启动模式："
echo "  1) 初始化环境 + 打开 MATLAB"
echo "  2) 批量测试所有脚本"
echo "  3) 打开启动器网页"
echo "  4) 查看可用脚本列表"
echo "  5) 退出"
echo ""
read -p "输入选项 [1-5]: " choice

case $choice in
  1)
    echo ""
    echo "启动 MATLAB 并自动初始化..."
    "$MATLAB" -nosplash -r "cd('$MATLAB_DIR'); startup_setup; disp('环境就绪，输入任意脚本名运行（如 motor_control）');" &
    ;;
  2)
    echo ""
    echo "运行批量测试..."
    "$MATLAB" -nosplash -nodesktop -r "cd('$MATLAB_DIR'); startup_setup; test_all" &
    ;;
  3)
    open "$LAUNCHER_URL"
    echo "已打开启动器网页: $LAUNCHER_URL"
    ;;
  4)
    echo ""
    echo "可用脚本："
    echo "  电机控制:"
    echo "    motor_control         PMSM FOC 矢量控制"
    echo "    dc_motor_pwm          直流电机 PWM 调速"
    echo "    dc_motor_simulink     直流电机 Simulink 模型"
    echo "  车辆动力学:"
    echo "    vehicle_dynamics      纵向动力学仿真"
    echo "    ev_dynamics_simple    电动汽车完整仿真"
    echo "    driving_cycle_analysis 驾驶循环能耗分析"
    echo "    generate_cruise_model 定速巡航 Simulink 模型"
    echo "  电池 & 能量:"
    echo "    battery_soc_ekf       SOC 估算（EKF）"
    echo "    energy_management     增程式能量管理"
    echo "  工具:"
    echo "    rms_calculation       RMS 有效值"
    echo "    fft_analysis          FFT 频谱分析"
    echo "    lowpass_filter        低通滤波器"
    echo "    find_carsim           CarSim 路径检测"
    echo ""
    read -p "按任意键返回菜单..."
    exec "$0"
    ;;
  *) echo "已退出" ;;
esac
