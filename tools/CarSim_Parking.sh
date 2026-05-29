#!/bin/bash
# CarSim + Simulink Parking Simulation
# Based on Bilibili Tutorial: BV1xk4y1b7y8
# macOS version

set -e

echo "============================================================"
echo "  CarSim + Simulink Parking Simulation"
echo "  Based on Bilibili Tutorial: BV1xk4y1b7y8"
echo "============================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../matlab/examples/parking-simulation" && pwd)"
echo "Working Directory: $PROJECT_DIR"
echo ""

# Step 1: Find MATLAB
echo "[Step 1/4] Checking MATLAB..."
MATLAB_CMD=""

if command -v matlab &>/dev/null; then
    MATLAB_CMD="matlab"
    echo "  - MATLAB found in PATH"
elif [ -f "/Applications/MATLAB_R2016b.app/bin/matlab" ]; then
    MATLAB_CMD="/Applications/MATLAB_R2016b.app/bin/matlab"
    echo "  - MATLAB R2016b found"
elif [ -f "/Applications/MATLAB_R2024a.app/bin/matlab" ]; then
    MATLAB_CMD="/Applications/MATLAB_R2024a.app/bin/matlab"
    echo "  - MATLAB R2024a found"
elif [ -f "/Applications/MATLAB_R2023b.app/bin/matlab" ]; then
    MATLAB_CMD="/Applications/MATLAB_R2023b.app/bin/matlab"
    echo "  - MATLAB R2023b found"
else
    echo "  - ERROR: MATLAB not found!"
    echo "  - Please install MATLAB or add it to PATH"
    exit 1
fi
echo ""

# Step 2: Run MATLAB script
echo "[Step 2/4] Generating CarSim configuration files..."
echo "  - Running: carsim_ap_auto_import"
"$MATLAB_CMD" -r "cd('$PROJECT_DIR'); try, carsim_ap_auto_import, fprintf('Success!\n'), catch e, fprintf('Error: %s\n', e.message), end; exit"
echo ""

# Step 3: Verify output
echo "[Step 3/4] Verifying output files..."
if [ -f "$PROJECT_DIR/Parking_Reversing.cpar" ]; then
    echo "  - CPAR file generated: Parking_Reversing.cpar"
elif [ -f "$PROJECT_DIR/Parking_Reversing.par" ]; then
    echo "  - PAR file generated: Parking_Reversing.par"
else
    echo "  - WARNING: No configuration file found!"
    echo "  - Check MATLAB output for errors"
    exit 1
fi
echo ""

# Step 4: Open CarSim
echo "[Step 4/4] Opening CarSim..."
if [ -d "/Applications/CarSim20190.app" ]; then
    open "/Applications/CarSim20190.app"
    echo "  - CarSim started"
elif [ -d "/Applications/CarSim.app" ]; then
    open "/Applications/CarSim.app"
    echo "  - CarSim started"
else
    echo "  - CarSim not found at default path"
    echo "  - Please open CarSim manually"
fi
echo ""

echo "============================================================"
echo "  ALL DONE! Next steps:"
echo "============================================================"
echo ""
echo "  1. In CarSim: File > Import Dataset"
echo "     Select: $PROJECT_DIR/Parking_Reversing.cpar"
echo ""
echo "  2. In CarSim: Settings > Simulink > Export S-Function"
echo "     Save to: $PROJECT_DIR/"
echo ""
echo "  3. In MATLAB: run parking_simulation"
echo "     cd '$PROJECT_DIR'"
echo "     run_parking_simulation"
echo ""
echo "============================================================"
