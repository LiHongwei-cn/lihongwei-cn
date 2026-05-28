# TCM Transmission Control Module Skill

## Overview
Expert skill in Transmission Control Module (TCM) development for automatic transmissions (AT), dual-clutch transmissions (DCT), and continuously variable transmissions (CVT). Covers gear shift strategy, shift quality optimization, torque converter lockup, adaptive learning, clutch control, and AUTOSAR integration.

## Core Competencies

### 1. Gear Shift Strategy
- **Shift Points**: Upshift/downshift based on throttle position, vehicle speed, driver intent
- **Kickdown**: Forced downshift for overtaking (throttle >80% pressed rapidly)
- **Skip Shifts**: Direct shift (e.g., 3rd→5th) for fuel economy
- **Grade Logic**: Hold lower gear on uphill, prevent hunting on downhill
- **Manual Mode**: Driver-selected gear hold, upshift/downshift on paddle command

### 2. Shift Quality Optimization
- **Shift Time**: Target 200-400ms for smooth shift, <200ms for performance mode
- **Torque Phase**: Reduce engine torque during clutch handover to minimize jerk
- **Inertia Phase**: Synchronize clutch engagement with gear ratio change
- **Fill Time Compensation**: Hydraulic delay compensation for temperature, wear
- **Shift Jerk Metric**: <10 m/s³ for comfort, <15 m/s³ for sport mode

### 3. Torque Converter Lockup (AT)
- **Partial Lockup**: Slip control (50-100 RPM slip) for vibration isolation
- **Full Lockup**: 100% mechanical coupling for efficiency (highway cruise)
- **Unlock Conditions**: Deceleration, gear shift, torque demand change
- **Shudder Mitigation**: Dither control to break stick-slip friction

### 4. Adaptive Shift Learning
- **Clutch Fill Learning**: Adapt hydraulic pressure for consistent shift timing
- **Clutch Wear Compensation**: Increase pressure as friction material wears
- **Driver Style Recognition**: Aggressive (sport shifts) vs economy (smooth shifts)
- **Altitude Adaptation**: Adjust for engine power loss at high altitude

### 5. Dual-Clutch Control (DCT)
- **Odd/Even Clutch Management**: Pre-select next gear before shift
- **Clutch Slip Control**: Modulate pressure for smooth engagement
- **Launch Control**: High-RPM clutch slip for maximum acceleration
- **Creep Mode**: Low-speed clutch modulation for stop-and-go traffic

### 6. CVT Control
- **Ratio Control**: Continuously variable primary/secondary pulley hydraulics
- **Belt Slip Prevention**: Clamp force management to prevent belt slippage
- **Simulated Gears**: Fixed ratio steps for driver feedback (virtual gears)
- **Manual Mode**: Hold fixed ratios mimicking 6-8 speed transmission

## Control Algorithms

### Shift Decision Logic (State Machine)
```c
typedef enum {
    GEAR_PARK,
    GEAR_REVERSE,
    GEAR_NEUTRAL,
    GEAR_DRIVE_1,
    GEAR_DRIVE_2,
    GEAR_DRIVE_3,
    GEAR_DRIVE_4,
    GEAR_DRIVE_5,
    GEAR_DRIVE_6,
    GEAR_MANUAL_MODE
} TransmissionGear_t;

typedef struct {
    float throttle_percent;
    float vehicle_speed_kph;
    float engine_rpm;
    float engine_torque_nm;
    bool kickdown_switch;
    bool manual_mode_active;
    uint8_t manual_gear_request;
} TCM_Input_t;

TransmissionGear_t TCM_ShiftLogic(TCM_Input_t *input, TransmissionGear_t current_gear) {
    // Manual mode: honor driver gear request
    if (input->manual_mode_active) {
        // Prevent over-rev: deny downshift if RPM would exceed limit
        float predicted_rpm = input->vehicle_speed_kph * GearRatio[input->manual_gear_request] * 60.0f / (TIRE_DIAMETER_M * PI * 3.6f);
        if (predicted_rpm > RPM_REDLINE) {
            return current_gear;  // Deny shift
        }
        return input->manual_gear_request;
    }

    // Kickdown: immediate downshift for max acceleration
    if (input->kickdown_switch && current_gear > GEAR_DRIVE_2) {
        return current_gear - 1;  // Drop one gear
    }

    // Lookup shift points from 3D map (Vehicle Speed x Throttle)
    uint8_t upshift_speed = ShiftMap_Upshift[current_gear][input->throttle_percent];
    uint8_t downshift_speed = ShiftMap_Downshift[current_gear][input->throttle_percent];

    // Upshift decision
    if (input->vehicle_speed_kph > upshift_speed && current_gear < GEAR_DRIVE_6) {
        // Check if skip-shift conditions met (light throttle, fuel economy mode)
        if (input->throttle_percent < 30.0f && Eco_Mode_Active) {
            if (current_gear == GEAR_DRIVE_3) {
                return GEAR_DRIVE_5;  // Skip 4th gear
            }
        }
        return current_gear + 1;
    }

    // Downshift decision
    if (input->vehicle_speed_kph < downshift_speed && current_gear > GEAR_DRIVE_1) {
        return current_gear - 1;
    }

    // Hold current gear
    return current_gear;
}
```

### Shift Execution Control
```c
typedef enum {
    SHIFT_IDLE,
    SHIFT_TORQUE_PHASE,
    SHIFT_INERTIA_PHASE,
    SHIFT_COMPLETE
} ShiftPhase_t;

typedef struct {
    uint16_t fill_time_ms;           // Pre-charge hydraulic clutch
    float torque_reduction_percent;  // Engine torque cut during shift
    float oncoming_clutch_pressure;  // Engaging clutch
    float offgoing_clutch_pressure;  // Releasing clutch
} ShiftControl_t;

void TCM_ExecuteShift(uint8_t target_gear, ShiftControl_t *ctrl, float dt) {
    static ShiftPhase_t phase = SHIFT_IDLE;
    static float phase_timer = 0.0f;

    switch (phase) {
    case SHIFT_IDLE:
        // Request torque reduction from ECM
        CAN_Send_TorqueReduction(ctrl->torque_reduction_percent);

        // Pre-fill oncoming clutch (rapid pressure rise, no engagement yet)
        Hydraulic_SetPressure(ONCOMING_CLUTCH, FILL_PRESSURE_BAR);

        phase_timer = ctrl->fill_time_ms / 1000.0f;  // Convert to seconds
        phase = SHIFT_TORQUE_PHASE;
        break;

    case SHIFT_TORQUE_PHASE:
        // Transfer torque from offgoing to oncoming clutch
        phase_timer -= dt;

        // Ramp up oncoming clutch pressure
        ctrl->oncoming_clutch_pressure += (TORQUE_PHASE_PRESSURE_RATE * dt);

        // Ramp down offgoing clutch pressure
        ctrl->offgoing_clutch_pressure -= (TORQUE_PHASE_PRESSURE_RATE * dt);

        Hydraulic_SetPressure(ONCOMING_CLUTCH, ctrl->oncoming_clutch_pressure);
        Hydraulic_SetPressure(OFFGOING_CLUTCH, ctrl->offgoing_clutch_pressure);

        // Torque phase complete when clutch slip speed crosses zero
        if (Clutch_SlipSpeed() < 10.0f) {  // RPM
            phase = SHIFT_INERTIA_PHASE;
        }
        break;

    case SHIFT_INERTIA_PHASE:
        // Synchronize transmission shaft speed to new gear ratio
        float target_shaft_speed = Input_Speed * GearRatio[target_gear];
        float actual_shaft_speed = Output_Speed;

        // PI controller for smooth synchronization
        static float inertia_integral = 0.0f;
        float speed_error = target_shaft_speed - actual_shaft_speed;
        inertia_integral += speed_error * KI_INERTIA * dt;

        float pressure_adjust = (KP_INERTIA * speed_error) + inertia_integral;
        ctrl->oncoming_clutch_pressure += pressure_adjust;

        Hydraulic_SetPressure(ONCOMING_CLUTCH, ctrl->oncoming_clutch_pressure);

        // Inertia phase complete when speed error <5 RPM
        if (fabs(speed_error) < 5.0f) {
            phase = SHIFT_COMPLETE;
        }
        break;

    case SHIFT_COMPLETE:
        // Full lockup of oncoming clutch
        Hydraulic_SetPressure(ONCOMING_CLUTCH, MAX_LINE_PRESSURE);
        Hydraulic_SetPressure(OFFGOING_CLUTCH, 0.0f);

        // Restore full engine torque
        CAN_Send_TorqueReduction(0.0f);

        // Update adaptive shift learning
        Adaptive_UpdateShiftQuality(target_gear, phase_timer);

        // Reset to idle
        phase = SHIFT_IDLE;
        break;
    }
}
```

### Torque Converter Lockup Control
```c
typedef enum {
    TC_UNLOCKED,
    TC_PARTIAL_LOCKUP,
    TC_FULL_LOCKUP
} TorqueConverter_State_t;

TorqueConverter_State_t TCM_TorqueConverterControl(float vehicle_speed_kph, float throttle_percent,
                                                     TransmissionGear_t gear, float coolant_temp) {
    // No lockup in 1st gear or during warmup
    if (gear == GEAR_DRIVE_1 || coolant_temp < 50.0f) {
        return TC_UNLOCKED;
    }

    // Unlock during heavy acceleration (torque multiplication benefit)
    if (throttle_percent > 70.0f) {
        return TC_UNLOCKED;
    }

    // Full lockup at highway cruise (>60 kph, light throttle)
    if (vehicle_speed_kph > 60.0f && throttle_percent < 40.0f) {
        return TC_FULL_LOCKUP;
    }

    // Partial lockup for efficiency while maintaining comfort
    if (vehicle_speed_kph > 30.0f && gear >= GEAR_DRIVE_2) {
        return TC_PARTIAL_LOCKUP;
    }

    return TC_UNLOCKED;
}

// Slip control for partial lockup (target 50 RPM slip)
void TCM_TorqueConverterSlipControl(float target_slip_rpm, float dt) {
    float engine_rpm = CAN_Read_EngineRPM();
    float turbine_rpm = Sensor_Read_TurbineSpeed();
    float actual_slip_rpm = engine_rpm - turbine_rpm;

    // PI controller
    static float slip_integral = 0.0f;
    float slip_error = target_slip_rpm - actual_slip_rpm;
    slip_integral += slip_error * KI_SLIP * dt;
    slip_integral = CLAMP(slip_integral, -5.0f, 5.0f);

    float clutch_pressure = LOCKUP_BASE_PRESSURE + (KP_SLIP * slip_error) + slip_integral;
    clutch_pressure = CLAMP(clutch_pressure, 2.0f, 15.0f);  // bar

    Hydraulic_SetPressure(TC_LOCKUP_CLUTCH, clutch_pressure);

    // Shudder mitigation: dither pressure ±0.5 bar at 10 Hz
    if (Shudder_Detected()) {
        float dither = 0.5f * sin(2.0f * PI * 10.0f * System_Time);
        Hydraulic_SetPressure(TC_LOCKUP_CLUTCH, clutch_pressure + dither);
    }
}
```

### Adaptive Shift Learning
```c
typedef struct {
    float fill_time_learned_ms[6];      // Learned fill time per gear
    float pressure_offset_bar[6];       // Clutch pressure offset per gear
    uint16_t shift_count[6];            // Number of shifts per gear
    float avg_shift_quality[6];         // Running average shift jerk
} AdaptiveData_t;

void Adaptive_UpdateShiftQuality(uint8_t gear, float shift_duration_s) {
    static AdaptiveData_t adapt = {0};

    // Measure shift jerk (longitudinal acceleration derivative)
    float accel_before = IMU_Read_LongitudinalAccel();
    Delay_ms(100);
    float accel_after = IMU_Read_LongitudinalAccel();
    float shift_jerk = fabs(accel_after - accel_before) / 0.1f;  // m/s³

    // Update running average
    adapt.avg_shift_quality[gear] = (adapt.avg_shift_quality[gear] * adapt.shift_count[gear] + shift_jerk) / (adapt.shift_count[gear] + 1);
    adapt.shift_count[gear]++;

    // If shift quality poor (jerk > 12 m/s³), adjust parameters
    if (shift_jerk > 12.0f) {
        // Too harsh: shift was too fast, increase fill time or reduce pressure
        if (shift_duration_s < 0.3f) {
            adapt.fill_time_learned_ms[gear] += 5;  // Add 5ms fill time
        } else {
            adapt.pressure_offset_bar[gear] -= 0.5f;  // Reduce pressure
        }
    } else if (shift_jerk < 5.0f && shift_duration_s > 0.5f) {
        // Too slow: shift was sluggish, decrease fill time or increase pressure
        adapt.fill_time_learned_ms[gear] -= 3;
        adapt.pressure_offset_bar[gear] += 0.3f;
    }

    // Clamp adaptive values to reasonable limits
    adapt.fill_time_learned_ms[gear] = CLAMP(adapt.fill_time_learned_ms[gear], 50, 300);
    adapt.pressure_offset_bar[gear] = CLAMP(adapt.pressure_offset_bar[gear], -3.0f, 3.0f);

    // Save to EEPROM every 50 shifts
    if (adapt.shift_count[gear] % 50 == 0) {
        EEPROM_Write_AdaptiveData(&adapt);
    }
}
```

### DCT Launch Control
```c
// Dual-Clutch Transmission launch control for max acceleration
typedef struct {
    float target_rpm;         // Launch RPM (e.g., 4000 RPM)
    float clutch_slip_rate;   // Target slip rate for smooth engagement
    bool launch_active;
} LaunchControl_t;

void DCT_LaunchControl(LaunchControl_t *launch, float brake_pedal, float throttle_pedal) {
    // Activation: brake + throttle pressed, vehicle stopped
    if (brake_pedal > 90.0f && throttle_pedal > 90.0f && Vehicle_Speed < 2.0f) {
        launch->launch_active = true;

        // Hold engine RPM at target by modulating clutch 1 (odd gears, 1st gear)
        float engine_rpm = CAN_Read_EngineRPM();
        float rpm_error = launch->target_rpm - engine_rpm;

        // PD controller for clutch pressure
        static float prev_error = 0.0f;
        float derivative = (rpm_error - prev_error) / DT;
        prev_error = rpm_error;

        float clutch_pressure = LAUNCH_BASE_PRESSURE + (KP_LAUNCH * rpm_error) + (KD_LAUNCH * derivative);
        clutch_pressure = CLAMP(clutch_pressure, 5.0f, 20.0f);

        Hydraulic_SetPressure(DCT_CLUTCH_1, clutch_pressure);

        // Pre-select 1st gear
        DCT_SelectGear(GEAR_DRIVE_1);
    }

    // Launch: brake released, control clutch slip rate
    if (launch->launch_active && brake_pedal < 10.0f) {
        float wheel_speed = Sensor_Read_WheelSpeed();
        float engine_speed = CAN_Read_EngineRPM() / GearRatio[GEAR_DRIVE_1];
        float slip_speed = engine_speed - wheel_speed;

        // Target slip decreases over time (500 RPM → 0 over 1 second)
        static float launch_timer = 0.0f;
        launch_timer += DT;
        float target_slip = 500.0f * (1.0f - launch_timer);

        if (target_slip < 0.0f) {
            target_slip = 0.0f;
            launch->launch_active = false;  // Launch complete
            launch_timer = 0.0f;
        }

        // Control clutch to achieve target slip
        float slip_error = target_slip - slip_speed;
        static float slip_integral = 0.0f;
        slip_integral += slip_error * KI_LAUNCH_SLIP * DT;

        float clutch_pressure = LAUNCH_BASE_PRESSURE + (KP_LAUNCH_SLIP * slip_error) + slip_integral;
        Hydraulic_SetPressure(DCT_CLUTCH_1, clutch_pressure);

        // Pre-select 2nd gear on even clutch for seamless 1→2 shift
        if (engine_rpm > 5000 || vehicle_speed > 30.0f) {
            DCT_SelectGear_Clutch2(GEAR_DRIVE_2);
        }
    }
}
```

## Calibration Tables

### Upshift Map (Vehicle Speed x Throttle)
```c
// Upshift speeds in kph (rows = current gear, cols = throttle %)
const uint8_t ShiftMap_Upshift[6][11] = {
    // Throttle:   0%  10%  20%  30%  40%  50%  60%  70%  80%  90% 100%
    /* 1st→2nd */ {15,  20,  25,  30,  35,  40,  45,  50,  55,  60,  65},
    /* 2nd→3rd */ {30,  35,  40,  45,  50,  55,  60,  65,  70,  75,  85},
    /* 3rd→4th */ {50,  55,  60,  65,  70,  75,  80,  85,  95, 105, 120},
    /* 4th→5th */ {70,  75,  80,  85,  90,  95, 100, 110, 120, 135, 150},
    /* 5th→6th */ {90, 100, 110, 115, 120, 125, 130, 140, 155, 170, 190},
    /* 6th      */ { 0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0}  // No upshift from 6th
};

// Downshift speeds in kph
const uint8_t ShiftMap_Downshift[6][11] = {
    // Throttle:   0%  10%  20%  30%  40%  50%  60%  70%  80%  90% 100%
    /* 1st      */ { 0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0},  // No downshift from 1st
    /* 2nd→1st */ {10,  12,  15,  18,  20,  22,  25,  28,  30,  32,  35},
    /* 3rd→2nd */ {25,  28,  32,  36,  40,  42,  45,  48,  50,  55,  60},
    /* 4th→3rd */ {45,  48,  52,  56,  60,  63,  66,  70,  75,  80,  90},
    /* 5th→4th */ {65,  68,  72,  76,  80,  83,  86,  92,  98, 105, 115},
    /* 6th→5th */ {85,  90,  95, 100, 105, 108, 112, 118, 125, 135, 145}
};
```

### Clutch Fill Time Map (Temperature Compensation)
```c
// Fill time in milliseconds (rows = gear, cols = ATF temp °C)
const uint16_t FillTimeMap[6][7] = {
    // ATF Temp:  -10°C  0°C  20°C  40°C  60°C  80°C  100°C
    /* 1st gear */ {250, 220, 180, 150, 130, 120, 110},
    /* 2nd gear */ {240, 210, 175, 145, 125, 115, 105},
    /* 3rd gear */ {230, 200, 170, 140, 120, 110, 100},
    /* 4th gear */ {225, 195, 165, 135, 118, 108,  98},
    /* 5th gear */ {220, 190, 160, 132, 115, 105,  95},
    /* 6th gear */ {215, 185, 158, 130, 112, 102,  93}
};
```

## State Machine: Transmission Mode Selection

```c
typedef enum {
    TRANS_MODE_PARK,
    TRANS_MODE_REVERSE,
    TRANS_MODE_NEUTRAL,
    TRANS_MODE_DRIVE_ECO,
    TRANS_MODE_DRIVE_NORMAL,
    TRANS_MODE_DRIVE_SPORT,
    TRANS_MODE_MANUAL
} TransmissionMode_t;

void TCM_ModeStateMachine(void) {
    static TransmissionMode_t mode = TRANS_MODE_PARK;

    // Gear selector input
    GearSelector_t selector = Read_GearSelector();

    switch (mode) {
    case TRANS_MODE_PARK:
        // Lock output shaft mechanically
        Engage_ParkingPawl();
        Allow_EngineStart = true;

        if (selector == SEL_REVERSE && Brake_Pressed()) {
            mode = TRANS_MODE_REVERSE;
        } else if (selector == SEL_NEUTRAL) {
            mode = TRANS_MODE_NEUTRAL;
        }
        break;

    case TRANS_MODE_REVERSE:
        Disengage_ParkingPawl();
        Engage_ReverseGear();
        Allow_EngineStart = false;

        if (selector == SEL_PARK && Vehicle_Speed < 2.0f) {
            mode = TRANS_MODE_PARK;
        }
        break;

    case TRANS_MODE_NEUTRAL:
        Disengage_AllGears();
        Allow_EngineStart = true;

        if (selector == SEL_DRIVE) {
            // Select drive mode based on driver preference
            if (EcoMode_Button_Pressed) {
                mode = TRANS_MODE_DRIVE_ECO;
            } else if (SportMode_Button_Pressed) {
                mode = TRANS_MODE_DRIVE_SPORT;
            } else {
                mode = TRANS_MODE_DRIVE_NORMAL;
            }
        }
        break;

    case TRANS_MODE_DRIVE_ECO:
        // Early upshifts, torque converter lockup, skip shifts
        Shift_Aggressiveness = 0.3f;
        Torque_Converter_Lockup_Threshold = 30.0f;  // kph
        Enable_SkipShifts = true;

        if (SportMode_Button_Pressed) {
            mode = TRANS_MODE_DRIVE_SPORT;
        }
        break;

    case TRANS_MODE_DRIVE_SPORT:
        // Late upshifts, hold gears longer, no lockup in low gears
        Shift_Aggressiveness = 0.8f;
        Torque_Converter_Lockup_Threshold = 60.0f;
        Enable_SkipShifts = false;

        if (EcoMode_Button_Pressed) {
            mode = TRANS_MODE_DRIVE_ECO;
        } else if (Manual_Paddle_Shift) {
            mode = TRANS_MODE_MANUAL;
        }
        break;

    case TRANS_MODE_MANUAL:
        // Driver controls shifts via paddle shifters
        Disable_AutomaticShifts();

        if (Upshift_Paddle_Pressed && Current_Gear < GEAR_DRIVE_6) {
            Request_Shift(Current_Gear + 1);
        } else if (Downshift_Paddle_Pressed && Current_Gear > GEAR_DRIVE_1) {
            Request_Shift(Current_Gear - 1);
        }

        // Timeout after 10 seconds with no paddle input → return to auto
        if (Paddle_Idle_Time > 10.0f) {
            mode = TRANS_MODE_DRIVE_NORMAL;
        }
        break;
    }
}
```

## AUTOSAR Integration

```c
// AUTOSAR Runnable for TCM main control (20ms cyclic)
FUNC(void, TCM_CODE) TCM_MainFunction(void) {
    // Read inputs via AUTOSAR RTE
    Rte_Read_SensorCluster_VehicleSpeed(&vehicle_speed_kph);
    Rte_Read_SensorCluster_ThrottlePosition(&throttle_percent);
    Rte_Read_SensorCluster_BrakePedal(&brake_pedal);
    Rte_Read_CAN_EngineSpeed(&engine_rpm);
    Rte_Read_CAN_EngineTorque(&engine_torque_nm);
    Rte_Read_SensorCluster_InputShaftSpeed(&input_shaft_rpm);
    Rte_Read_SensorCluster_OutputShaftSpeed(&output_shaft_rpm);
    Rte_Read_SensorCluster_ATF_Temperature(&atf_temp);
    Rte_Read_HMI_GearSelector(&gear_selector);
    Rte_Read_HMI_DriveMode(&drive_mode);

    // Shift decision logic
    TCM_Input_t input = {
        .throttle_percent = throttle_percent,
        .vehicle_speed_kph = vehicle_speed_kph,
        .engine_rpm = engine_rpm,
        .engine_torque_nm = engine_torque_nm,
        .kickdown_switch = (throttle_percent > 85.0f),
        .manual_mode_active = (drive_mode == DRIVE_MODE_MANUAL)
    };

    TransmissionGear_t target_gear = TCM_ShiftLogic(&input, current_gear);

    // Execute shift if target gear differs
    if (target_gear != current_gear) {
        ShiftControl_t shift_ctrl = {
            .fill_time_ms = FillTimeMap[target_gear][ATF_TempIndex(atf_temp)],
            .torque_reduction_percent = 30.0f
        };
        TCM_ExecuteShift(target_gear, &shift_ctrl, 0.02f);
    }

    // Torque converter lockup control
    TorqueConverter_State_t tc_state = TCM_TorqueConverterControl(vehicle_speed_kph, throttle_percent, current_gear, atf_temp);

    // Write outputs via AUTOSAR RTE
    Rte_Write_ActuatorCluster_CurrentGear(current_gear);
    Rte_Write_ActuatorCluster_TorqueConverterState(tc_state);
    Rte_Write_CAN_TorqueReductionRequest(shift_in_progress ? 30.0f : 0.0f);
}
```

## HIL Test Scenarios

### Test Case 1: Upshift Quality (2nd→3rd)
```yaml
test_id: TCM_001_UPSHIFT_QUALITY
objective: Validate shift smoothness and duration
preconditions:
  - ATF temperature: 80°C
  - Current gear: 2nd
  - Vehicle speed: 55 kph
  - Throttle: 40%

test_steps:
  1. Trigger upshift condition (speed exceeds upshift threshold)
  2. Monitor longitudinal acceleration during shift
  3. Measure shift duration (torque phase + inertia phase)
  4. Calculate shift jerk (derivative of acceleration)

pass_criteria:
  - Shift duration: 250-400 ms
  - Peak jerk: <10 m/s³
  - No audible clunk or harshness
  - Output shaft speed synchronized within 5 RPM
```

### Test Case 2: Launch Control (DCT)
```yaml
test_id: TCM_002_LAUNCH_CONTROL
objective: Validate launch control for 0-100 kph acceleration
preconditions:
  - Vehicle stationary
  - Engine warmed up
  - Sport mode active

test_steps:
  1. Driver presses brake + throttle 100%
  2. Monitor engine RPM held at target (4000 RPM)
  3. Driver releases brake
  4. Monitor clutch slip rate during launch
  5. Measure 0-100 kph time

pass_criteria:
  - Engine RPM held at 4000 ±50 RPM during launch prep
  - Clutch slip rate: 500→0 RPM over 1.0 second
  - No wheel spin (traction control coordinated)
  - 0-100 kph: <6.5 seconds (performance target)
  - 1→2 shift seamless (pre-selected on clutch 2)
```

### Test Case 3: Adaptive Learning Validation
```yaml
test_id: TCM_003_ADAPTIVE_LEARNING
objective: Verify adaptive shift quality improvement over drive cycles
preconditions:
  - Clear adaptive memory (factory reset)
  - ATF temperature: 60°C

test_steps:
  1. Perform 100 upshifts (2nd→3rd) at consistent conditions
  2. Record shift jerk for first 10 shifts (baseline)
  3. Record shift jerk for last 10 shifts (adapted)
  4. Compare learned fill time vs initial value

pass_criteria:
  - Shift jerk improvement: >20% reduction baseline→adapted
  - Fill time convergence: Within ±10ms of optimal
  - No false adaptations (stable parameters after convergence)
  - Adaptive data saved to EEPROM after 50 shifts
```

## ISO 26262 Safety Concept

### ASIL Decomposition for TCM

| Function | ASIL | Decomposition | Rationale |
|----------|------|---------------|-----------|
| Gear selection | ASIL-D | ASIL-C(C) + ASIL-B(B) | Position sensor redundancy (dual Hall sensors) |
| Clutch pressure control | ASIL-C | ASIL-B(B) + ASIL-A(A) | Hydraulic valve dual-coil design |
| Park lock | ASIL-D | No decomposition | Mechanical pawl failsafe (unpowered lock) |
| Launch control | QM | N/A | Performance feature, not safety-critical |

### Safety Mechanisms

1. **Gear Sensor Plausibility**: Compare input shaft speed vs vehicle speed for each gear (detect false neutral)
2. **Hydraulic Pressure Monitoring**: Pressure sensors on each clutch pack to verify commanded vs actual
3. **Park Lock Verification**: Microswitch confirms pawl engagement before allowing engine start
4. **Neutral Safety Switch**: Prevent engine start unless Park or Neutral selected
5. **Limp-Home Mode**: Default to 3rd gear if shift solenoids fail (mechanical valving)

## CAN Signal Definitions (DBC)

```dbc
BO_ 260 TCM_Status: 8 TCM
 SG_ CurrentGear : 0|4@1+ (1,0) [0|15] "" PCM,ESC,HMI
 SG_ TargetGear : 4|4@1+ (1,0) [0|15] "" PCM,ESC
 SG_ ShiftInProgress : 8|1@1+ (1,0) [0|1] "" PCM,ESC
 SG_ TorqueConverterLocked : 9|1@1+ (1,0) [0|1] "" PCM,HMI
 SG_ ManualModeActive : 10|1@1+ (1,0) [0|1] "" PCM,HMI
 SG_ ATF_Temperature : 16|8@1- (1,-40) [-40|215] "degC" PCM,HMI
 SG_ TransmissionTorque : 24|16@1+ (0.5,-500) [-500|32267.5] "Nm" PCM,ESC

BO_ 261 TCM_TorqueRequest: 4 TCM
 SG_ TorqueReduction : 0|8@1+ (0.5,0) [0|127.5] "%" PCM
 SG_ TorqueHoldRequest : 8|1@1+ (1,0) [0|1] "" PCM
 SG_ LaunchControlActive : 9|1@1+ (1,0) [0|1] "" PCM,ESC
```

## Tools and Calibration

- **INCA/CANape**: Transmission calibration, shift point tuning, hydraulic pressure optimization
- **dSPACE MicroAutoBox**: Rapid control prototyping, shift algorithm development
- **AVL InMotion**: Powertrain testbed, transmission dynamometer testing
- **Vector CANoe**: TCM simulation, CAN database management
- **ATI Vision**: TCM flashing, diagnostic trouble code management

## References
- SAE J2807 (Transmission Performance Standards)
- ISO 26262 (Functional Safety for TCM)
- AUTOSAR Transmission Manager specification
- SAE J1979 (OBD-II for TCM diagnostics)
