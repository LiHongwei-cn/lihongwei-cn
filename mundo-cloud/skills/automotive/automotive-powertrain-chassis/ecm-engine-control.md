# ECM/PCM Engine Control Module Skill

## Overview
Expert skill in Engine Control Module (ECM) / Powertrain Control Module (PCM) development for internal combustion engines. Covers fuel injection timing, ignition control, air-fuel ratio optimization, turbo boost control, variable valve timing (VVT), emissions control, and OBD-II diagnostics.

## Core Competencies

### 1. Fuel Injection Control
- **Multi-point Fuel Injection (MPFI)**: Sequential, batch, simultaneous injection strategies
- **Direct Injection (GDI/TFSI)**: High-pressure rail control, split injection, stratified/homogeneous modes
- **Injection Timing**: Crank angle-based timing, compensation for temperature, altitude
- **Pulse Width Modulation**: Injector driver control with dead-time compensation

### 2. Ignition System Control
- **Spark Timing Optimization**: MBT (Minimum advance for Best Torque) vs knock limit
- **Knock Detection**: Piezoelectric sensor processing, frequency domain analysis
- **Coil-on-Plug (COP)**: Individual coil dwell time control, energy optimization
- **Misfire Detection**: Crankshaft acceleration monitoring, OBD-II readiness

### 3. Air-Fuel Ratio (AFR) Management
- **Lambda Control**: Closed-loop with wideband O2 sensor (LSU 4.9 Bosch)
- **Stoichiometric Operation**: λ=1.0 for three-way catalyst efficiency
- **Lean Burn**: λ=1.3-1.5 for fuel economy (requires NOx aftertreatment)
- **Rich Operation**: λ=0.85-0.95 for maximum power, component protection

### 4. Turbocharger/Supercharger Control
- **Wastegate Control**: Electronic wastegate actuator, boost pressure regulation
- **Overboost Protection**: Pressure limiting, fuel cut-off, ignition retard
- **Compressor Surge Prevention**: Anti-surge valve control
- **Turbo Lag Mitigation**: Launch control, anti-lag systems

### 5. Variable Valve Timing (VVT)
- **Cam Phasing**: Hydraulic/electric cam phasers, intake/exhaust timing
- **Valve Lift Control**: Discrete multi-step or continuous variable lift
- **Optimization**: Torque curve shaping, emissions reduction, fuel economy
- **Cylinder Deactivation**: Selective cylinder shut-off for light load

### 6. Emissions Control Systems
- **Exhaust Gas Recirculation (EGR)**: Cooled/uncooled EGR valve control, NOx reduction
- **Three-Way Catalyst (TWC)**: Light-off temperature management, oxygen storage
- **Secondary Air Injection**: Cold-start emissions reduction
- **Evaporative Emissions (EVAP)**: Purge control, leak detection

### 7. OBD-II Diagnostics
- **Readiness Monitors**: Catalyst, EGR, EVAP, O2 sensor, misfire, fuel system
- **Freeze Frame Data**: Snapshot at DTC trigger
- **Malfunction Indicator Lamp (MIL)**: Illumination logic, two-trip detection
- **In-Use Performance Ratio (IUPR)**: Denominator/numerator tracking per SAE J1979

## Control Algorithms

### Fuel Injection Pulse Width Calculation
```c
// Fuel injection pulse width calculation
typedef struct {
    float base_pulse_ms;      // Base pulse from VE table
    float lambda_target;      // Target AFR (1.0 = stoich)
    float lambda_actual;      // Measured AFR from O2 sensor
    float temp_correction;    // Coolant/intake temp correction
    float transient_comp;     // Wall-wetting compensation
    float battery_correction; // Voltage compensation
} FuelCalc_t;

float ECM_CalculateInjectionPulse(FuelCalc_t *calc, float maf_gs, float rpm) {
    // Volumetric efficiency lookup (3D map: RPM x MAP)
    float ve = VE_Table_Lookup(rpm, manifold_pressure);

    // Stoichiometric fuel mass required (14.7:1 for gasoline)
    float fuel_mass_mg = (maf_gs * 1000.0f) / (14.7f * calc->lambda_target);

    // Convert to pulse width (injector flow rate)
    float pulse_width = (fuel_mass_mg / injector_flow_rate_cc) + injector_dead_time;

    // Apply corrections
    pulse_width *= calc->temp_correction;
    pulse_width *= calc->battery_correction;
    pulse_width += calc->transient_comp;  // Wall-wetting

    // Lambda closed-loop correction
    float lambda_error = calc->lambda_target - calc->lambda_actual;
    static float lambda_integral = 0.0f;
    lambda_integral += lambda_error * KI_LAMBDA * DT;
    lambda_integral = CLAMP(lambda_integral, -0.2f, 0.2f);

    float lambda_correction = 1.0f + (KP_LAMBDA * lambda_error) + lambda_integral;
    pulse_width *= lambda_correction;

    return CLAMP(pulse_width, 0.5f, 20.0f);  // Pulse limits in ms
}
```

### Ignition Timing with Knock Control
```c
// Spark advance calculation with knock detection
typedef struct {
    float base_advance_deg;   // Base timing from map
    float knock_retard_deg;   // Accumulated knock retard
    float coolant_adv_deg;    // Coolant temp advance
    float altitude_adv_deg;   // Barometric compensation
} IgnitionTiming_t;

float ECM_CalculateSparkAdvance(IgnitionTiming_t *ign, float rpm, float load) {
    // Base timing from 3D map (RPM x Load)
    float spark_adv = SparkMap_Lookup(rpm, load);

    // Knock detection and retard
    if (Knock_Detected()) {
        ign->knock_retard_deg += KNOCK_RETARD_STEP_DEG;  // 2-3° per event
        ign->knock_retard_deg = CLAMP(ign->knock_retard_deg, 0.0f, 15.0f);
    } else {
        // Slowly recover advance (0.5°/second)
        ign->knock_retard_deg -= KNOCK_RECOVERY_RATE * DT;
        ign->knock_retard_deg = MAX(ign->knock_retard_deg, 0.0f);
    }

    // Apply corrections
    spark_adv += ign->coolant_adv_deg;    // Cold engine needs more advance
    spark_adv += ign->altitude_adv_deg;   // High altitude needs more advance
    spark_adv -= ign->knock_retard_deg;   // Subtract knock retard

    // Safety limits
    return CLAMP(spark_adv, -10.0f, 45.0f);
}

// Knock detection using FFT on sensor signal
bool Knock_Detected(void) {
    // Read knock sensor (piezoelectric accelerometer)
    float knock_signal[128];
    ADC_ReadKnockSensor(knock_signal, 128);

    // Bandpass filter (5-15 kHz typical knock frequency)
    BandpassFilter(knock_signal, 128, 5000, 15000);

    // FFT magnitude at knock frequency
    float knock_magnitude = FFT_Magnitude(knock_signal, 128, KNOCK_FREQ_HZ);

    // Compare against calibrated threshold
    return (knock_magnitude > KNOCK_THRESHOLD);
}
```

### Turbo Boost Control (PID)
```c
// Electronic wastegate control for boost pressure
typedef struct {
    float kp;           // Proportional gain
    float ki;           // Integral gain
    float kd;           // Derivative gain
    float integral;     // Integral accumulator
    float prev_error;   // Previous error for derivative
} PID_Controller_t;

float Turbo_BoostControl(float target_boost_kPa, float actual_boost_kPa,
                          PID_Controller_t *pid, float dt) {
    float error = target_boost_kPa - actual_boost_kPa;

    // PID terms
    float p_term = pid->kp * error;

    pid->integral += error * dt;
    pid->integral = CLAMP(pid->integral, -50.0f, 50.0f);  // Anti-windup
    float i_term = pid->ki * pid->integral;

    float derivative = (error - pid->prev_error) / dt;
    float d_term = pid->kd * derivative;
    pid->prev_error = error;

    // Wastegate duty cycle (0-100%)
    float wastegate_duty = p_term + i_term + d_term;
    wastegate_duty = CLAMP(wastegate_duty, 0.0f, 100.0f);

    // Overboost protection
    if (actual_boost_kPa > OVERBOOST_LIMIT_KPA) {
        wastegate_duty = 100.0f;  // Fully open wastegate
        Fault_SetDTC(DTC_OVERBOOST);
    }

    return wastegate_duty;
}
```

### EGR Control
```c
// Exhaust Gas Recirculation control for NOx reduction
float EGR_CalculatePosition(float rpm, float load, float coolant_temp) {
    // EGR disabled during cold start
    if (coolant_temp < EGR_MIN_TEMP_CELSIUS) {
        return 0.0f;
    }

    // Lookup desired EGR rate from map (RPM x Load)
    float egr_target_percent = EGR_Map_Lookup(rpm, load);

    // EGR valve position to achieve target dilution
    // Uses MAF sensor feedback to measure actual EGR flow
    float maf_no_egr = VE_Table_Lookup(rpm, manifold_pressure) * rpm;
    float maf_actual = MAF_ReadFlowRate();
    float egr_actual_percent = (1.0f - (maf_actual / maf_no_egr)) * 100.0f;

    // PI controller for EGR valve
    static float egr_integral = 0.0f;
    float egr_error = egr_target_percent - egr_actual_percent;
    egr_integral += egr_error * KI_EGR * DT;

    float egr_position = (KP_EGR * egr_error) + egr_integral;
    return CLAMP(egr_position, 0.0f, 100.0f);
}
```

## State Machine: Cold Start Sequence

```c
typedef enum {
    COLD_START_CRANK,
    COLD_START_PRIME,
    COLD_START_FIRST_FIRE,
    COLD_START_WARMUP,
    COLD_START_CATALYST_HEAT,
    COLD_START_NORMAL
} ColdStartState_t;

void ECM_ColdStartStateMachine(void) {
    static ColdStartState_t state = COLD_START_CRANK;

    switch (state) {
    case COLD_START_CRANK:
        // Fuel prime pulse (3x normal)
        FuelPulse_Multiplier = 3.0f;
        SparkAdvance_Offset = 5.0f;  // Extra advance when cold

        if (RPM_Get() > 400) {
            state = COLD_START_FIRST_FIRE;
        }
        break;

    case COLD_START_FIRST_FIRE:
        // Rich mixture for first combustion cycles
        Lambda_Target = 0.90f;

        if (Combustion_Stable() && RPM_Get() > 600) {
            state = COLD_START_WARMUP;
        }
        break;

    case COLD_START_WARMUP:
        // Elevated idle for faster warmup
        IdleSpeed_Target = 1200;

        // Secondary air injection for catalyst heating
        SecondaryAir_Enable();

        if (Coolant_Temp > 40.0f) {
            state = COLD_START_CATALYST_HEAT;
        }
        break;

    case COLD_START_CATALYST_HEAT:
        // Retard spark to increase exhaust temp
        SparkAdvance_Offset = -5.0f;
        Lambda_Target = 0.95f;  // Slightly rich

        if (Catalyst_Temp > 300.0f) {  // Light-off temp
            state = COLD_START_NORMAL;
            OBD_SetReadiness(CATALYST_MONITOR, READY);
        }
        break;

    case COLD_START_NORMAL:
        // Normal operation
        IdleSpeed_Target = 750;
        Lambda_Target = 1.00f;
        SparkAdvance_Offset = 0.0f;
        SecondaryAir_Disable();
        break;
    }
}
```

## Calibration Tables

### Volumetric Efficiency (VE) Map
```c
// 16x16 VE map: RPM (rows) x MAP (columns)
const float VE_Table[16][16] = {
    // MAP:  20   30   40   50   60   70   80   90  100  110  120  130  140  150  160  170 kPa
    /*  500*/ {20, 25, 30, 35, 40, 45, 50, 55, 60, 62, 63, 64, 65, 65, 65, 65},
    /* 1000*/ {30, 35, 40, 50, 60, 70, 75, 78, 80, 81, 82, 83, 83, 83, 83, 83},
    /* 1500*/ {35, 42, 52, 62, 72, 80, 85, 88, 90, 91, 92, 92, 92, 92, 92, 92},
    /* 2000*/ {40, 50, 60, 70, 80, 88, 92, 94, 95, 96, 96, 96, 96, 96, 96, 96},
    /* 2500*/ {42, 53, 64, 75, 85, 92, 96, 98, 99, 99, 99, 99, 99, 99, 99, 99},
    /* 3000*/ {44, 55, 66, 77, 87, 94, 97, 99,100,100,100,100,100,100,100,100},
    /* 3500*/ {45, 56, 67, 78, 88, 95, 98,100,101,101,101,100,100,100,100,100},
    /* 4000*/ {45, 56, 67, 78, 88, 95, 98,100,101,101,100, 99, 99, 98, 98, 98},
    /* 4500*/ {44, 55, 66, 77, 87, 94, 97, 99,100,100, 99, 98, 97, 96, 95, 95},
    /* 5000*/ {43, 54, 65, 76, 86, 93, 96, 98, 99, 98, 97, 96, 95, 94, 93, 92},
    /* 5500*/ {42, 53, 64, 75, 85, 92, 95, 97, 97, 96, 95, 94, 92, 91, 90, 89},
    /* 6000*/ {40, 51, 62, 73, 83, 90, 93, 95, 95, 94, 92, 91, 89, 88, 86, 85},
    /* 6500*/ {38, 49, 60, 71, 81, 88, 91, 92, 92, 91, 89, 87, 85, 83, 81, 80},
    /* 7000*/ {35, 46, 57, 68, 78, 85, 88, 89, 88, 87, 85, 83, 80, 78, 76, 74},
    /* 7500*/ {32, 43, 54, 65, 75, 82, 84, 85, 84, 82, 80, 78, 75, 72, 70, 68},
    /* 8000*/ {28, 39, 50, 61, 71, 78, 80, 80, 79, 77, 75, 72, 69, 66, 63, 61}
};
```

### Spark Timing Map (Base Advance)
```c
// 16x16 Spark map: RPM (rows) x Load (columns)
// Values in degrees BTDC (Before Top Dead Center)
const float SparkMap[16][16] = {
    // Load:  10   20   30   40   50   60   70   80   90  100  110  120  130  140  150  160 %
    /*  500*/ {15, 18, 20, 22, 24, 25, 26, 26, 26, 25, 24, 23, 22, 21, 20, 19},
    /* 1000*/ {18, 22, 25, 28, 30, 32, 33, 33, 32, 31, 30, 28, 27, 26, 25, 24},
    /* 1500*/ {20, 25, 28, 32, 35, 37, 38, 38, 37, 36, 34, 32, 30, 29, 28, 27},
    /* 2000*/ {22, 27, 31, 35, 38, 40, 41, 41, 40, 38, 36, 34, 32, 31, 30, 29},
    /* 2500*/ {24, 29, 33, 37, 40, 42, 43, 42, 41, 39, 37, 35, 33, 32, 31, 30},
    /* 3000*/ {25, 30, 34, 38, 41, 43, 43, 42, 41, 39, 37, 35, 33, 32, 31, 30},
    /* 3500*/ {26, 31, 35, 39, 41, 42, 42, 41, 40, 38, 36, 34, 32, 31, 30, 29},
    /* 4000*/ {27, 31, 35, 38, 40, 41, 41, 40, 39, 37, 35, 33, 31, 30, 29, 28},
    /* 4500*/ {27, 31, 34, 37, 39, 40, 40, 39, 37, 35, 33, 31, 29, 28, 27, 26},
    /* 5000*/ {26, 30, 33, 36, 38, 39, 38, 37, 35, 33, 31, 29, 27, 26, 25, 24},
    /* 5500*/ {25, 29, 32, 35, 36, 37, 36, 35, 33, 31, 29, 27, 25, 24, 23, 22},
    /* 6000*/ {24, 28, 31, 33, 34, 35, 34, 33, 31, 29, 27, 25, 23, 22, 21, 20},
    /* 6500*/ {23, 27, 29, 31, 32, 32, 31, 30, 28, 26, 24, 22, 20, 19, 18, 17},
    /* 7000*/ {22, 25, 27, 29, 29, 29, 28, 27, 25, 23, 21, 19, 17, 16, 15, 14},
    /* 7500*/ {20, 23, 25, 26, 26, 26, 25, 24, 22, 20, 18, 16, 14, 13, 12, 11},
    /* 8000*/ {18, 21, 22, 23, 23, 23, 22, 21, 19, 17, 15, 13, 11, 10,  9,  8}
};
```

## OBD-II Readiness Monitors

```c
// OBD-II Monitor Status
typedef struct {
    bool misfire_monitor_complete;
    bool fuel_system_monitor_complete;
    bool components_monitor_complete;
    bool catalyst_monitor_complete;
    bool heated_catalyst_monitor_complete;
    bool evap_system_monitor_complete;
    bool secondary_air_monitor_complete;
    bool oxygen_sensor_monitor_complete;
    bool oxygen_sensor_heater_monitor_complete;
    bool egr_system_monitor_complete;
} OBD_MonitorStatus_t;

void OBD_UpdateReadinessMonitors(void) {
    // Misfire Monitor (continuous)
    if (Misfire_TestComplete() && Drive_Cycle_Conditions_Met()) {
        monitors.misfire_monitor_complete = true;
    }

    // Catalyst Monitor (requires closed-loop, specific load/speed)
    if (Catalyst_Test_Entry_Conditions()) {
        float lambda_switch_count = O2_Downstream_SwitchCount();
        float catalyst_efficiency = lambda_switch_count / lambda_upstream_switches;

        if (catalyst_efficiency < CATALYST_EFFICIENCY_THRESHOLD) {
            Fault_SetDTC(DTC_P0420_CATALYST_EFFICIENCY);
        } else {
            monitors.catalyst_monitor_complete = true;
        }
    }

    // EVAP Monitor (fuel tank pressure decay test)
    if (EVAP_Test_Entry_Conditions()) {
        float pressure_decay_rate = EVAP_RunPressureTest();

        if (pressure_decay_rate > EVAP_LEAK_THRESHOLD) {
            Fault_SetDTC(DTC_P0442_EVAP_LEAK_SMALL);
        } else {
            monitors.evap_system_monitor_complete = true;
        }
    }

    // EGR Monitor (position sensor vs expected flow)
    if (EGR_Test_Entry_Conditions()) {
        float egr_expected_flow = EGR_Map_Lookup(rpm, load);
        float egr_actual_flow = MAF_MeasureEGR();

        if (fabs(egr_expected_flow - egr_actual_flow) > EGR_TOLERANCE) {
            Fault_SetDTC(DTC_P0401_EGR_INSUFFICIENT_FLOW);
        } else {
            monitors.egr_system_monitor_complete = true;
        }
    }
}

// MIL Illumination Logic (Two-trip fault detection)
void OBD_MIL_Logic(uint16_t dtc) {
    static uint8_t fault_count[256] = {0};

    if (DTC_IsPending(dtc)) {
        fault_count[dtc]++;

        if (fault_count[dtc] >= 2) {  // Two consecutive trips
            MIL_Illuminate();
            DTC_StoreConfirmed(dtc);
            DTC_StoreFreezeFrame(dtc);
        }
    } else {
        fault_count[dtc] = 0;  // Reset if fault not present
    }
}
```

## AUTOSAR Integration

```c
// AUTOSAR Runnable for ECM main control (10ms cyclic)
FUNC(void, ECM_CODE) ECM_MainFunction(void) {
    // Read sensors via AUTOSAR RTE
    Rte_Read_SensorCluster_EngineSpeed(&rpm);
    Rte_Read_SensorCluster_ThrottlePosition(&throttle_pos);
    Rte_Read_SensorCluster_MAP(&manifold_pressure);
    Rte_Read_SensorCluster_CoolantTemp(&coolant_temp);
    Rte_Read_SensorCluster_IntakeAirTemp(&iat);
    Rte_Read_SensorCluster_LambdaSensor(&lambda_actual);

    // Calculate fuel injection pulse
    FuelCalc_t fuel_calc = {
        .lambda_target = 1.0f,
        .lambda_actual = lambda_actual,
        .temp_correction = Temp_Correction(coolant_temp, iat),
        .transient_comp = WallWetting_Compensation(throttle_rate),
        .battery_correction = Battery_Compensation(battery_voltage)
    };

    float injection_pulse_ms = ECM_CalculateInjectionPulse(&fuel_calc, maf_gs, rpm);

    // Calculate spark timing
    IgnitionTiming_t ign_timing = {
        .coolant_adv_deg = Coolant_AdvanceCurve(coolant_temp),
        .altitude_adv_deg = Altitude_Compensation(barometric_pressure)
    };

    float spark_advance_deg = ECM_CalculateSparkAdvance(&ign_timing, rpm, load);

    // Calculate turbo boost (if equipped)
    float boost_target_kPa = BoostMap_Lookup(rpm, throttle_pos);
    float wastegate_duty = Turbo_BoostControl(boost_target_kPa, boost_actual_kPa,
                                               &boost_pid, 0.01f);

    // Calculate EGR position
    float egr_position = EGR_CalculatePosition(rpm, load, coolant_temp);

    // Write actuators via AUTOSAR RTE
    Rte_Write_ActuatorCluster_InjectionPulse(injection_pulse_ms);
    Rte_Write_ActuatorCluster_SparkAdvance(spark_advance_deg);
    Rte_Write_ActuatorCluster_WastegatePosition(wastegate_duty);
    Rte_Write_ActuatorCluster_EGR_Position(egr_position);

    // Update OBD-II monitors
    OBD_UpdateReadinessMonitors();
}
```

## HIL Test Scenarios

### Test Case 1: Cold Start Emissions
```yaml
test_id: ECM_001_COLD_START
objective: Validate cold start emissions and catalyst light-off time
preconditions:
  - Coolant temperature: -7°C (EPA cold start spec)
  - Fuel tank: 50% full
  - Battery voltage: 12.6V

test_steps:
  1. Crank engine (starter engaged)
  2. Monitor time to first fire (<1.0 seconds)
  3. Monitor idle speed stabilization (<5 seconds to 1200 RPM)
  4. Monitor catalyst light-off time (<60 seconds to 300°C)
  5. Measure HC/CO/NOx emissions during first 120 seconds

pass_criteria:
  - Time to first fire: <1.0s
  - Idle stabilization: <5s
  - Catalyst light-off: <60s
  - HC emissions: <1.5 g/km (FTP-75 cycle)
  - CO emissions: <4.2 g/km
  - NOx emissions: <0.06 g/km (Tier 3 Bin 30)
```

### Test Case 2: Wide Open Throttle (WOT) Performance
```yaml
test_id: ECM_002_WOT_PERFORMANCE
objective: Validate max power delivery and knock control
preconditions:
  - Engine at operating temperature (90°C)
  - Fuel: 91 AKI (octane rating)
  - Ambient: 25°C, 1013 mbar

test_steps:
  1. Start at 1500 RPM, light load
  2. Apply 100% throttle
  3. Monitor power curve from 1500-7000 RPM
  4. Monitor for knock events
  5. Verify boost control (turbo engines)

pass_criteria:
  - Peak power: Within 5% of calibration target
  - Peak torque: Within 5% of calibration target
  - No sustained knock events (transient knock OK)
  - Boost pressure: ±5 kPa of target throughout RPM range
  - AFR: 0.85-0.90 lambda during WOT
```

### Test Case 3: Emissions Durability (OBD-II)
```yaml
test_id: ECM_003_OBD_READINESS
objective: Verify OBD-II monitors complete within EPA drive cycle
preconditions:
  - Clear all DTCs
  - Perform key-off/key-on cycle

test_steps:
  1. Execute FTP-75 drive cycle
  2. Monitor readiness status for all monitors
  3. Verify no false DTCs triggered

pass_criteria:
  - Misfire monitor: Complete
  - Fuel system monitor: Complete
  - Catalyst monitor: Complete
  - EVAP monitor: Complete (requires tank temp conditions)
  - EGR monitor: Complete
  - O2 sensor monitors: Complete
  - No false DTCs stored
```

## ISO 26262 Safety Concept

### ASIL Decomposition for ECM

| Function | ASIL | Decomposition | Rationale |
|----------|------|---------------|-----------|
| Fuel injection | ASIL-D | ASIL-B(B) + ASIL-B(B) | Split into pulse calculation (B) and driver control (B) |
| Ignition timing | ASIL-D | ASIL-C(C) + ASIL-A(A) | Knock control (C), base timing (A) |
| Throttle monitoring | ASIL-D | ASIL-C(C) + ASIL-B(B) | Dual-channel position sensors |
| Boost control | ASIL-C | No decomposition | Overspeed protection via mechanical wastegate |

### Safety Mechanisms

1. **Plausibility Checks**: Cross-check TPS vs MAP (should correlate at steady-state)
2. **Limp-Home Mode**: Fixed ignition timing, reduced power if critical sensor fails
3. **Cylinder Cutoff**: Disable fuel to cylinder if misfire detected (prevents catalyst damage)
4. **Independent Watchdog**: External watchdog monitors ECM task execution
5. **RAM/ROM Tests**: Periodic memory checks (ISO 26262 Part 5)

## CAN Signal Definitions (DBC)

```dbc
BO_ 256 ECM_Status: 8 ECM
 SG_ EngineSpeed : 0|16@1+ (0.25,0) [0|16383.75] "rpm" PCM,TCM,ESC
 SG_ EngineTorque : 16|16@1+ (0.5,-500) [-500|32267.5] "Nm" PCM,TCM
 SG_ ThrottlePosition : 32|8@1+ (0.4,0) [0|102] "%" PCM,TCM,ESC
 SG_ CoolantTemp : 40|8@1- (1,-40) [-40|215] "degC" PCM,HMI
 SG_ Lambda : 48|8@1+ (0.01,0) [0|2.55] "lambda" PCM
 SG_ BoostPressure : 56|8@1+ (2,0) [0|510] "kPa" PCM,HMI

BO_ 257 ECM_Faults: 8 ECM
 SG_ MIL_Status : 0|2@1+ (1,0) [0|3] "" PCM,HMI
 SG_ DTC_Count : 2|6@1+ (1,0) [0|63] "" PCM,HMI
 SG_ Misfire_Cylinder1 : 8|1@1+ (1,0) [0|1] "" PCM
 SG_ Misfire_Cylinder2 : 9|1@1+ (1,0) [0|1] "" PCM
 SG_ Misfire_Cylinder3 : 10|1@1+ (1,0) [0|1] "" PCM
 SG_ Misfire_Cylinder4 : 11|1@1+ (1,0) [0|1] "" PCM
 SG_ Knock_Detected : 12|1@1+ (1,0) [0|1] "" PCM
 SG_ Catalyst_Efficiency : 13|1@1+ (1,0) [0|1] "" PCM
```

## Tools and Calibration

- **INCA/CANape**: A2L-based calibration, live tuning on dyno
- **ATI Vision**: ECU flashing, bootloader programming
- **MATLAB/Simulink**: Model-based development, automatic code generation
- **TargetLink**: Production code generation with ISO 26262 certificate
- **Polyspace**: Static analysis for MISRA-C compliance
- **Vector CANoe**: Virtual ECU testing, residual bus simulation

## References
- ISO 15031 (OBD-II Communication)
- SAE J1979 (E/E Diagnostic Test Modes)
- ISO 26262 (Functional Safety)
- SAE J2534 (Pass-Thru Programming)
- EPA Tier 3 Emissions Standards
- CARB LEV III Standards
