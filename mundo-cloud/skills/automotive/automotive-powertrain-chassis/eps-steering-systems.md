# EPS Electric Power Steering Systems Skill

## Overview
Expert skill in Electric Power Steering (EPS) system development. Covers assist torque calculation, returnability, damping control, steering feel tuning, park assist integration, lane centering assist, driver hands-on detection, and ISO 26262 ASIL-D safety requirements.

## Core Competencies

### 1. Assist Torque Calculation
- **Speed-Dependent Assist**: High assist at low speed (parking), minimal assist at high speed (stability)
- **Torque Sensor Fusion**: Dual-sensor redundancy for ASIL-D compliance
- **Motor Control**: BLDC/PMSM field-oriented control (FOC), current mode control
- **Compensation**: Friction compensation, inertia compensation, KPI tuning

### 2. Returnability and Damping
- **Self-Centering**: Automatic steering wheel return to center after cornering
- **Damping Control**: Velocity-dependent damping to prevent oscillations
- **Hysteresis Compensation**: Eliminate mechanical friction dead-zone
- **Tuning**: Balance returnability (too strong = jerky) vs stability (too weak = wander)

### 3. Steering Feel Optimization
- **On-Center Feel**: Tight on-center for highway stability, wider for city comfort
- **Build-Up Gradient**: Torque vs angle relationship (linear, progressive, degressive)
- **Road Feedback**: Transmit road surface feel (driver preference: sporty vs comfort)
- **Driver Intent Recognition**: Detect parking vs highway vs emergency maneuver

### 4. Park Assist Integration
- **Automated Steering**: Follow path controller for parallel/perpendicular parking
- **Speed Limit**: Max 7 kph for park assist actuation
- **Driver Override**: Instant deactivation on driver torque >3 Nm
- **Fail-Safe**: Return control to driver on sensor fault

### 5. Lane Centering Assist (LCA)
- **Camera-Based Control**: Follow lane markings, gentle steering corrections
- **Hands-On Detection**: Capacitive steering wheel, torque threshold monitoring
- **Comfort Tuning**: Smooth intervention, avoid "ping-pong" effect
- **Takeover Request**: Escalating warnings if driver inattentive

### 6. ISO 26262 ASIL-D Safety
- **Redundant Torque Sensors**: Dual sensors with plausibility check
- **Motor Position Sensors**: Dual resolver/encoder with voting logic
- **Safe Torque Off (STO)**: Hardware safety switch to disable motor
- **End-of-Line Test**: Automated safety function verification

## Control Algorithms

### Assist Torque Calculation
```c
typedef struct {
    float driver_torque_nm;        // From torque sensor
    float vehicle_speed_kph;       // From CAN
    float motor_angle_deg;         // Steering column angle
    float motor_velocity_dps;      // Steering rate
} EPS_Input_t;

typedef struct {
    float base_assist_factor;      // Speed-dependent assist curve
    float damping_coefficient;     // Velocity damping
    float returnability_gain;      // Self-centering strength
    float friction_compensation;   // Static friction offset
} EPS_Parameters_t;

float EPS_CalculateAssistTorque(EPS_Input_t *input, EPS_Parameters_t *params) {
    // Speed-dependent assist curve (lookup table)
    // Low speed: 100% assist, High speed: 20% assist
    float assist_curve[8] = {1.0f, 0.95f, 0.80f, 0.60f, 0.40f, 0.30f, 0.25f, 0.20f};
    uint8_t speed_index = CLAMP((int)(input->vehicle_speed_kph / 20.0f), 0, 7);
    params->base_assist_factor = assist_curve[speed_index];

    // Base assist torque (proportional to driver input)
    float assist_torque = input->driver_torque_nm * params->base_assist_factor * 8.0f;

    // Friction compensation (overcome column friction)
    float friction_sign = (input->motor_velocity_dps > 0) ? 1.0f : -1.0f;
    assist_torque += friction_sign * params->friction_compensation;

    // Damping (velocity-dependent, prevent oscillation)
    float damping_torque = -params->damping_coefficient * input->motor_velocity_dps;
    assist_torque += damping_torque;

    // Returnability (self-centering spring)
    float return_torque = -params->returnability_gain * input->motor_angle_deg;
    assist_torque += return_torque;

    // Torque limits (motor capability)
    return CLAMP(assist_torque, -6.0f, 6.0f);  // Nm
}
```

### Motor Current Control (FOC)
```c
// Field-Oriented Control for BLDC motor
typedef struct {
    float id_target;      // d-axis current (field weakening)
    float iq_target;      // q-axis current (torque generation)
    float id_actual;
    float iq_actual;
    float motor_angle;    // Electrical angle (from resolver)
} FOC_Controller_t;

void EPS_FOC_CurrentControl(FOC_Controller_t *foc, float dt) {
    // Clarke transform: 3-phase ABC → 2-phase αβ
    float i_alpha = foc->ia;
    float i_beta = (foc->ia + 2.0f * foc->ib) / sqrtf(3.0f);

    // Park transform: αβ → dq (rotor-aligned frame)
    float cos_theta = cosf(foc->motor_angle);
    float sin_theta = sinf(foc->motor_angle);

    foc->id_actual = i_alpha * cos_theta + i_beta * sin_theta;
    foc->iq_actual = -i_alpha * sin_theta + i_beta * cos_theta;

    // PI controllers for d and q axis
    static float id_integral = 0.0f, iq_integral = 0.0f;

    float id_error = foc->id_target - foc->id_actual;
    id_integral += id_error * dt;
    float vd = KP_D * id_error + KI_D * id_integral;

    float iq_error = foc->iq_target - foc->iq_actual;
    iq_integral += iq_error * dt;
    float vq = KP_Q * iq_error + KI_Q * iq_integral;

    // Inverse Park: dq → αβ
    float v_alpha = vd * cos_theta - vq * sin_theta;
    float v_beta = vd * sin_theta + vq * cos_theta;

    // Inverse Clarke: αβ → ABC
    float va = v_alpha;
    float vb = -0.5f * v_alpha + (sqrtf(3.0f) / 2.0f) * v_beta;
    float vc = -0.5f * v_alpha - (sqrtf(3.0f) / 2.0f) * v_beta;

    // PWM modulation
    PWM_SetDutyCycle(PHASE_A, va);
    PWM_SetDutyCycle(PHASE_B, vb);
    PWM_SetDutyCycle(PHASE_C, vc);
}
```

### Lane Centering Assist
```c
typedef struct {
    float lane_offset_m;          // Distance from lane center
    float lane_heading_deg;       // Angle to lane center
    float kp_lateral;             // Proportional gain
    float kd_lateral;             // Derivative gain
    bool hands_on;                // Driver hands detected
    float intervention_torque;    // LCA torque overlay
} LCA_Controller_t;

float LCA_CalculateTorque(LCA_Controller_t *lca, float vehicle_speed, float dt) {
    // Disable if driver not holding wheel
    if (!lca->hands_on) {
        return 0.0f;
    }

    // PD controller for lane centering
    float lateral_error = lca->lane_offset_m;
    float heading_error = lca->lane_heading_deg * DEG_TO_RAD;

    // Predict future lateral error (preview control)
    float preview_time = 0.5f;  // seconds
    float predicted_error = lateral_error + vehicle_speed * sinf(heading_error) * preview_time;

    // PD control law
    float p_term = lca->kp_lateral * predicted_error;
    float d_term = lca->kd_lateral * heading_error;

    lca->intervention_torque = p_term + d_term;

    // Gentle intervention limits (comfort)
    lca->intervention_torque = CLAMP(lca->intervention_torque, -1.5f, 1.5f);  // Nm

    return lca->intervention_torque;
}

// Hands-on detection (capacitive + torque threshold)
bool LCA_HandsOnDetection(float driver_torque, float capacitive_level) {
    // Capacitive sensor detects hand contact
    if (capacitive_level > CAPACITIVE_THRESHOLD) {
        return true;
    }

    // Torque threshold as backup (driver applying force)
    if (fabs(driver_torque) > 1.0f) {  // 1 Nm
        return true;
    }

    return false;
}
```

### Fail-Safe State Machine
```c
typedef enum {
    EPS_NORMAL,
    EPS_DEGRADED,
    EPS_SAFE_TORQUE_OFF,
    EPS_FAULT
} EPS_SafetyState_t;

void EPS_SafetyStateMachine(void) {
    static EPS_SafetyState_t state = EPS_NORMAL;

    // Read dual torque sensors
    float torque_sensor_1 = ADC_ReadTorqueSensor1();
    float torque_sensor_2 = ADC_ReadTorqueSensor2();

    // Plausibility check (ASIL-D requirement)
    float torque_diff = fabs(torque_sensor_1 - torque_sensor_2);

    switch (state) {
    case EPS_NORMAL:
        // Full EPS functionality
        if (torque_diff > TORQUE_PLAUSIBILITY_THRESHOLD) {
            state = EPS_DEGRADED;
            Fault_SetDTC(DTC_EPS_TORQUE_SENSOR_MISMATCH);
        }
        break;

    case EPS_DEGRADED:
        // Use single sensor, reduce assist torque by 50%
        Assist_Multiplier = 0.5f;
        HMI_SetEPS_Warning(true);

        // Recovery: if both sensors agree again for 5 seconds
        if (torque_diff < TORQUE_PLAUSIBILITY_THRESHOLD * 0.5f) {
            static uint16_t recovery_count = 0;
            recovery_count++;
            if (recovery_count > 250) {  // 5 sec at 50Hz
                state = EPS_NORMAL;
                recovery_count = 0;
            }
        }

        // Escalate if motor position sensor fails
        if (Resolver_Fault_Detected()) {
            state = EPS_SAFE_TORQUE_OFF;
        }
        break;

    case EPS_SAFE_TORQUE_OFF:
        // Disable motor immediately (hardware safety switch)
        STO_ActivateSafetySwitch();
        HMI_SetEPS_Fault(true);
        state = EPS_FAULT;
        break;

    case EPS_FAULT:
        // Manual steering only (no EPS assist)
        // Requires vehicle restart to clear
        break;
    }
}
```

## Calibration Parameters

```c
// Speed-dependent assist curve (lookup table)
const float Assist_Curve_LUT[16] = {
    // Speed:   0   10   20   30   40   50   60   70   80   90  100  110  120  130  140  150 kph
    /*Assist*/ 1.0, 0.98, 0.92, 0.82, 0.68, 0.54, 0.42, 0.34, 0.28, 0.24, 0.22, 0.20, 0.20, 0.20, 0.20, 0.20
};

// Damping coefficient (Nm/(deg/s))
const float Damping_Curve_LUT[8] = {
    // Speed:   0   20   40   60   80  100  120  140 kph
    /*Damping*/ 0.01, 0.015, 0.020, 0.025, 0.030, 0.035, 0.040, 0.045
};

// Returnability gain (self-centering)
const float Returnability_LUT[8] = {
    // Speed:   0   20   40   60   80  100  120  140 kph
    /*Return*/  0.02, 0.025, 0.030, 0.032, 0.033, 0.034, 0.035, 0.035
};
```

## AUTOSAR Integration

```c
FUNC(void, EPS_CODE) EPS_MainFunction(void) {
    // Read inputs (1 kHz task for safety-critical control)
    Rte_Read_TorqueSensor_Primary(&driver_torque_1);
    Rte_Read_TorqueSensor_Secondary(&driver_torque_2);
    Rte_Read_ResolverPosition(&motor_angle);
    Rte_Read_ResolverVelocity(&motor_velocity);
    Rte_Read_CAN_VehicleSpeed(&vehicle_speed);

    // Plausibility check (ASIL-D)
    if (fabs(driver_torque_1 - driver_torque_2) < TORQUE_PLAUSIBILITY_THRESHOLD) {
        driver_torque = (driver_torque_1 + driver_torque_2) / 2.0f;
    } else {
        EPS_SafetyStateMachine();
    }

    // Calculate assist torque
    EPS_Input_t input = {driver_torque, vehicle_speed, motor_angle, motor_velocity};
    EPS_Parameters_t params;
    float assist_torque = EPS_CalculateAssistTorque(&input, &params);

    // Lane centering overlay (if active)
    if (ADAS_LCA_Active()) {
        LCA_Controller_t lca;
        Rte_Read_Camera_LaneOffset(&lca.lane_offset_m);
        Rte_Read_Camera_LaneHeading(&lca.lane_heading_deg);
        lca.hands_on = LCA_HandsOnDetection(driver_torque, Capacitive_Sensor_Read());

        float lca_torque = LCA_CalculateTorque(&lca, vehicle_speed, 0.001f);
        assist_torque += lca_torque;
    }

    // Motor current control (FOC)
    FOC_Controller_t foc = {.iq_target = assist_torque / MOTOR_TORQUE_CONSTANT};
    EPS_FOC_CurrentControl(&foc, 0.001f);

    // Write outputs
    Rte_Write_CAN_EPS_AssistTorque(assist_torque);
    Rte_Write_CAN_EPS_MotorCurrent(foc.iq_actual);
}
```

## HIL Test Scenarios

### Test Case 1: Park Assist Torque (ASIL-D)
```yaml
test_id: EPS_001_PARK_ASSIST
objective: Validate high assist torque at low speed
preconditions:
  - Vehicle speed: 5 kph
  - Driver torque: 5 Nm (parking maneuver)

test_steps:
  1. Apply driver torque sensor input
  2. Monitor motor assist torque
  3. Verify torque sensor redundancy

pass_criteria:
  - Assist torque: 35-45 Nm (8-9x amplification)
  - Dual torque sensors agree within ±0.5 Nm
  - Motor current: <100 A peak
  - Response time: <50 ms
```

### Test Case 2: Highway Stability (High Speed)
```yaml
test_id: EPS_002_HIGHWAY_STABILITY
objective: Minimal assist at high speed for stability
preconditions:
  - Vehicle speed: 120 kph
  - Driver torque: 2 Nm (lane change)

test_steps:
  1. Apply small steering input
  2. Verify low assist ratio
  3. Check damping prevents oscillation

pass_criteria:
  - Assist torque: 3-5 Nm (1.5-2.5x amplification)
  - No steering oscillation after lane change
  - Returnability: Wheel returns to center within 1.5 seconds
```

### Test Case 3: Sensor Fault Handling (ASIL-D)
```yaml
test_id: EPS_003_SENSOR_FAULT
objective: Graceful degradation on torque sensor failure
preconditions:
  - EPS in normal mode
  - Vehicle speed: 60 kph

test_steps:
  1. Inject fault: Torque sensor 1 reads +3 Nm, sensor 2 reads -2 Nm
  2. Monitor plausibility check
  3. Verify degraded mode activation
  4. Confirm driver warning

pass_criteria:
  - Plausibility fault detected within 10ms
  - Degraded mode: Use single sensor, 50% assist reduction
  - EPS warning lamp illuminated within 100ms
  - No loss of steering (fail-operational)
```

## ISO 26262 Safety Concept

### ASIL-D Requirements
- **Dual Torque Sensors**: Independent measurement chains, cross-check every 1ms
- **Dual Position Sensors**: Resolver + Hall sensor with voting logic
- **Safe Torque Off (STO)**: Hardware-enforced motor disable on critical fault
- **Diagnostic Coverage**: >99% for ASIL-D, watchdog, RAM/ROM test, sensor range checks

## CAN Signals (DBC)

```dbc
BO_ 280 EPS_Status: 8 EPS
 SG_ DriverTorque : 0|16@1- (0.01,-327.68) [-327.68|327.67] "Nm" ADAS,ESC
 SG_ AssistTorque : 16|16@1- (0.01,-327.68) [-327.68|327.67] "Nm" ADAS
 SG_ MotorAngle : 32|16@1- (0.1,-3276.8) [-3276.8|3276.7] "deg" ESC
 SG_ EPS_State : 48|2@1+ (1,0) [0|3] "" HMI
 SG_ HandsOn : 50|1@1+ (1,0) [0|1] "" ADAS
```

## References
- ISO 26262-6 (EPS software safety)
- ISO 26262-8 (EPS hardware safety)
- UN ECE R79 (Steering equipment)
- SAE J2874 (EPS test procedures)
