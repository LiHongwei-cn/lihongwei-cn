#!/bin/bash
# MATLAB AI Simulation Toolkit — Mac launcher
# Usage: chmod +x matlab.sh && ./matlab.sh

cd "$(dirname "$0")"

echo "============================================"
echo "  MATLAB AI Simulation Toolkit"
echo "============================================"
echo ""

echo "[1/3] git pull..."
git pull 2>/dev/null || echo "      (offline / skipped)"
echo ""

echo "[2/3] Auto-detecting MATLAB installation..."

MATLAB_BIN=""

# Scan /Applications for MATLAB
for dir in /Applications/MATLAB_R*.app; do
    if [ -f "$dir/bin/matlab" ]; then
        MATLAB_BIN="$dir/bin/matlab"
    fi
done

# Fallback: try PATH
if [ -z "$MATLAB_BIN" ]; then
    MATLAB_BIN=$(which matlab 2>/dev/null)
fi

if [ -z "$MATLAB_BIN" ]; then
    echo "[ERROR] MATLAB not found."
    echo "        Expected: /Applications/MATLAB_R20xx.app"
    echo "        Install MATLAB R2016b or newer for Mac."
    exit 1
fi

echo "         Found: $MATLAB_BIN"
echo ""

echo "[3/3] Starting MATLAB..."
echo "       Paths auto-configured on launch."
echo ""

"$MATLAB_BIN" -r "addpath('$(pwd)/matlab');startup_setup" &

echo "MATLAB is starting (may take a moment)..."
echo ""
echo "Available commands in MATLAB:"
echo "  vehicle_dynamics         motor_control"
echo "  dc_motor_pwm             ev_dynamics_simple"
echo "  battery_soc_ekf          driving_cycle_analysis"
echo "  energy_management        generate_cruise_model"
echo "  test_all"
echo ""
