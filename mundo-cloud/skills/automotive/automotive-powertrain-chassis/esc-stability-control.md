# ESC Electronic Stability Control Skill

## Overview
Expert skill in Electronic Stability Control (ESC) system development for vehicle stability management. Covers yaw rate control, slip angle estimation, selective brake intervention, understeer/oversteer detection, traction control (TCS), hill hold assist, and integration with ABS/EPS systems.

## Core Competencies

### 1. Yaw Rate Control
- **Reference Model**: Ideal yaw rate based on steering angle, vehicle speed, tire characteristics
- **Feedback Control**: PI/PID controller to minimize yaw rate error
- **Brake Intervention**: Selective brake force distribution to generate corrective yaw moment
- **Torque Reduction**: Coordinated engine torque cut for stability

### 2. Slip Angle Estimation
- **Kinematic Observer**: Estimate vehicle sideslip angle β from lateral acceleration, yaw rate
- **Kalman Filter**: Fuse IMU sensors (gyro, accelerometer) with wheel speed sensors
- **GPS/INS Integration**: High-accuracy β estimation for ADAS/autonomous vehicles
- **Cornering Stiffness Adaptation**: Real-time tire model parameter identification

### 3. Brake Intervention Strategy
- **Understeer Correction**: Brake inner rear wheel to induce yaw-in moment
- **Oversteer Correction**: Brake outer front wheel to induce yaw-out moment
- **Pressure Modulation**: Rapid hydraulic pressure cycling (10-20 Hz) via ABS valves
- **Coordination with ABS**: Brake force limited by wheel slip constraints

### 4. Understeer/Oversteer Detection
- **Understeer**: Actual yaw rate < desired yaw rate (vehicle turns less than intended)
- **Oversteer**: Actual yaw rate > desired yaw rate (vehicle turns more than intended)
- **Neutral Steer**: Actual ≈ desired (stable cornering)
- **Threshold Tuning**: Speed-dependent thresholds to avoid false triggers

### 5. Traction Control (TCS)
- **Drive Wheel Slip Control**: Limit slip ratio to 10-15% for maximum traction
- **Engine Torque Reduction**: Spark retard, fuel cut, throttle close
- **Brake-Based TCS**: Apply brake to spinning wheel (open differential vehicles)
- **Torque Vectoring**: Differential brake force for enhanced cornering (EBD)

### 6. Hill Hold Assist (HHA)
- **Gradient Detection**: Estimate road slope from longitudinal accelerometer
- **Brake Pressure Hold**: Maintain brake pressure for 2 seconds after brake release
- **Smooth Release**: Gradual pressure reduction as driver applies throttle
- **Rollback Prevention**: <1% grade rollback allowed on 15% slope

## Control Algorithms

### Reference Yaw Rate Calculation (Bicycle Model)
```c
// Calculate desired yaw rate based on driver input and vehicle dynamics
typedef struct {
    float steering_angle_deg;   // Steering wheel angle
    float vehicle_speed_mps;    // Longitudinal velocity
    float wheelbase_m;          // Distance between front and rear axles
    float understeer_gradient;  // Characteristic understeer gradient (K)
} VehicleModel_t;

float ESC_CalculateReferenceYawRate(VehicleModel_t *model) {
    // Convert steering wheel angle to road wheel angle
    float road_wheel_angle = model->steering_angle_deg / STEERING_RATIO;
    float delta_rad = road_wheel_angle * DEG_TO_RAD;

    // Understeer gradient (rad/g)
    float K = model->understeer_gradient;  // Typical: 0.002-0.005 for understeer

    // Lateral acceleration at current speed and steering
    float lat_accel = (model->vehicle_speed_mps * model->vehicle_speed_mps * delta_rad) / model->wheelbase_m;

    // Reference yaw rate (rad/s) with understeer compensation
    float yaw_rate_ref = model->vehicle_speed_mps * delta_rad / (model->wheelbase_m * (1.0f + K * lat_accel / GRAVITY));

    // Saturation limits (vehicle physical limits)
    float yaw_rate_max = 0.85f * GRAVITY / model->vehicle_speed_mps;  // ~0.85g lateral limit
    return CLAMP(yaw_rate_ref, -yaw_rate_max, yaw_rate_max);
}
```

### Slip Angle Estimation (Kinematic Observer)
```c
// Estimate vehicle sideslip angle β using sensor fusion
typedef struct {
    float yaw_rate;           // Measured from gyro (rad/s)
    float lat_accel;          // Measured from accelerometer (m/s²)
    float longitudinal_vel;   // From wheel speeds (m/s)
    float beta_estimate;      // Estimated sideslip angle (rad)
} SlipAngleEstimator_t;

void ESC_EstimateSideslipAngle(SlipAngleEstimator_t *est, float dt) {
    // Kinematic relationship: dβ/dt = ay/vx - ψ̇
    // where β = sideslip angle, ay = lateral accel, vx = longitudinal vel, ψ̇ = yaw rate

    float beta_dot = (est->lat_accel / est->longitudinal_vel) - est->yaw_rate;

    // Integrate to get sideslip angle
    est->beta_estimate += beta_dot * dt;

    // Low-pass filter to remove noise (cutoff 1 Hz)
    static float beta_filtered = 0.0f;
    float alpha = dt / (dt + 1.0f / (2.0f * PI * 1.0f));  // RC filter
    beta_filtered = alpha * est->beta_estimate + (1.0f - alpha) * beta_filtered;
    est->beta_estimate = beta_filtered;

    // Clamp to physical limits (±15 degrees)
    est->beta_estimate = CLAMP(est->beta_estimate, -0.26f, 0.26f);  // radians
}
```

### Yaw Stability Controller
```c
typedef enum {
    ESC_STABLE,
    ESC_UNDERSTEER,
    ESC_OVERSTEER,
    ESC_CRITICAL
} ESC_State_t;

typedef struct {
    float kp_yaw;             // Proportional gain for yaw rate error
    float ki_yaw;             // Integral gain
    float yaw_rate_error;     // Reference - actual yaw rate
    float integral_yaw;       // Integral accumulator
    ESC_State_t state;        // Current stability state
} ESC_Controller_t;

float ESC_YawController(ESC_Controller_t *ctrl, float yaw_ref, float yaw_actual, float dt) {
    ctrl->yaw_rate_error = yaw_ref - yaw_actual;

    // Dead-zone to prevent unnecessary intervention (±0.05 rad/s)
    if (fabs(ctrl->yaw_rate_error) < 0.05f) {
        ctrl->integral_yaw = 0.0f;
        ctrl->state = ESC_STABLE;
        return 0.0f;  // No intervention needed
    }

    // PI controller for corrective yaw moment
    float p_term = ctrl->kp_yaw * ctrl->yaw_rate_error;

    ctrl->integral_yaw += ctrl->yaw_rate_error * dt;
    ctrl->integral_yaw = CLAMP(ctrl->integral_yaw, -2.0f, 2.0f);  // Anti-windup
    float i_term = ctrl->ki_yaw * ctrl->integral_yaw;

    // Desired corrective yaw moment (N⋅m)
    float yaw_moment = p_term + i_term;

    // Classify state based on error magnitude
    if (ctrl->yaw_rate_error > 0.1f) {
        ctrl->state = ESC_UNDERSTEER;
    } else if (ctrl->yaw_rate_error < -0.1f) {
        ctrl->state = ESC_OVERSTEER;
    } else {
        ctrl->state = ESC_STABLE;
    }

    return yaw_moment;
}
```

### Brake Force Distribution (Understeer/Oversteer Correction)
```c
typedef struct {
    float FL_brake_force;  // Front-left brake force (N)
    float FR_brake_force;  // Front-right
    float RL_brake_force;  // Rear-left
    float RR_brake_force;  // Rear-right
} BrakeForces_t;

void ESC_CalculateBrakeForces(ESC_Controller_t *ctrl, float yaw_moment_desired,
                               BrakeForces_t *brakes, float vehicle_speed) {
    // Track width (distance between left and right wheels)
    const float TRACK_WIDTH_M = 1.6f;

    // Required brake force to generate yaw moment: F = M / (track_width / 2)
    float brake_force_single_wheel = fabs(yaw_moment_desired) / (TRACK_WIDTH_M / 2.0f);

    // Limit brake force based on vehicle speed (lower at high speed for comfort)
    float max_brake_force = 8000.0f - (vehicle_speed * 50.0f);  // N
    brake_force_single_wheel = CLAMP(brake_force_single_wheel, 0.0f, max_brake_force);

    // Initialize all brakes to zero
    memset(brakes, 0, sizeof(BrakeForces_t));

    switch (ctrl->state) {
    case ESC_UNDERSTEER:
        // Vehicle understeers (yaw rate too low, not turning enough)
        // Brake INNER REAR wheel to create yaw-in moment
        if (ctrl->yaw_rate_error > 0) {
            brakes->RL_brake_force = brake_force_single_wheel;  // Turning right, brake left rear
        } else {
            brakes->RR_brake_force = brake_force_single_wheel;  // Turning left, brake right rear
        }
        break;

    case ESC_OVERSTEER:
        // Vehicle oversteers (yaw rate too high, turning too much, tail sliding out)
        // Brake OUTER FRONT wheel to create yaw-out moment
        if (ctrl->yaw_rate_error < 0) {
            brakes->FL_brake_force = brake_force_single_wheel;  // Turning right, brake left front
        } else {
            brakes->FR_brake_force = brake_force_single_wheel;  // Turning left, brake right front
        }
        break;

    case ESC_STABLE:
        // No intervention
        break;

    case ESC_CRITICAL:
        // Extreme instability: brake all wheels and reduce throttle aggressively
        float panic_brake = max_brake_force * 0.6f;
        brakes->FL_brake_force = panic_brake;
        brakes->FR_brake_force = panic_brake;
        brakes->RL_brake_force = panic_brake * 0.8f;  // Rear lighter for rotation control
        brakes->RR_brake_force = panic_brake * 0.8f;

        // Request full engine torque cut
        CAN_Send_TorqueReduction(100.0f);
        break;
    }
}
```

### Traction Control System (TCS)
```c
// Limit drive wheel slip for maximum traction
typedef struct {
    float target_slip_ratio;  // Optimal slip ratio (10-15%)
    float kp_tcs;             // Proportional gain
    float ki_tcs;             // Integral gain
    float integral_tcs[4];    // Per-wheel integral term
} TCS_Controller_t;

void TCS_Control(TCS_Controller_t *tcs, float wheel_speeds[4], float vehicle_speed, float dt) {
    // Drive wheels (assume rear-wheel drive, indices 2 and 3)
    const uint8_t RL = 2;
    const uint8_t RR = 3;

    for (uint8_t i = RL; i <= RR; i++) {
        // Calculate slip ratio: λ = (vwheel - vvehicle) / vvehicle
        float slip_ratio = (wheel_speeds[i] - vehicle_speed) / vehicle_speed;

        // Slip ratio error
        float slip_error = slip_ratio - tcs->target_slip_ratio;

        // Only intervene if slip exceeds target (wheel spinning)
        if (slip_error > 0.02f) {  // 2% dead-zone
            // PI controller
            float p_term = tcs->kp_tcs * slip_error;

            tcs->integral_tcs[i] += slip_error * dt;
            tcs->integral_tcs[i] = CLAMP(tcs->integral_tcs[i], 0.0f, 5.0f);
            float i_term = tcs->ki_tcs * tcs->integral_tcs[i];

            // Torque reduction request (0-100%)
            float torque_reduction = p_term + i_term;
            torque_reduction = CLAMP(torque_reduction, 0.0f, 100.0f);

            // Send torque reduction to ECM
            CAN_Send_TorqueReduction(torque_reduction);

            // Optional: Brake-based TCS (apply brake to spinning wheel)
            if (slip_error > 0.3f) {  // Excessive slip (>30%)
                float brake_pressure = CLAMP(slip_error * 5000.0f, 0.0f, 8000.0f);  // N
                ABS_ApplyBrake(i, brake_pressure);
            }

            // Activate TCS indicator lamp
            HMI_SetTCS_Active(true);
        } else {
            tcs->integral_tcs[i] = 0.0f;  // Reset integral
        }
    }
}
```

### Hill Hold Assist
```c
typedef enum {
    HHA_IDLE,
    HHA_ACTIVE,
    HHA_RELEASING
} HHA_State_t;

typedef struct {
    HHA_State_t state;
    float hold_pressure_bar;
    float hold_timer;
    float gradient_percent;
} HillHoldAssist_t;

void HHA_Control(HillHoldAssist_t *hha, float brake_pedal, float throttle_pedal,
                 float longitudinal_accel, float dt) {
    // Estimate road gradient from accelerometer (when stationary)
    if (Vehicle_Speed < 0.5f) {
        hha->gradient_percent = longitudinal_accel / GRAVITY * 100.0f;
    }

    switch (hha->state) {
    case HHA_IDLE:
        // Activation: driver releases brake on slope >3%
        if (brake_pedal < 10.0f && fabs(hha->gradient_percent) > 3.0f && Vehicle_Speed < 0.5f) {
            // Capture current brake pressure
            hha->hold_pressure_bar = Hydraulic_GetBrakePressure();
            hha->hold_timer = 0.0f;
            hha->state = HHA_ACTIVE;
        }
        break;

    case HHA_ACTIVE:
        // Hold brake pressure to prevent rollback
        Hydraulic_SetBrakePressure(hha->hold_pressure_bar);

        // Increment timer
        hha->hold_timer += dt;

        // Release conditions: throttle applied or timeout (2 seconds)
        if (throttle_pedal > 10.0f || hha->hold_timer > 2.0f) {
            hha->state = HHA_RELEASING;
        }
        break;

    case HHA_RELEASING:
        // Gradually release brake pressure (linear ramp over 0.5 seconds)
        static float release_timer = 0.0f;
        release_timer += dt;

        float release_fraction = release_timer / 0.5f;
        float pressure = hha->hold_pressure_bar * (1.0f - release_fraction);
        Hydraulic_SetBrakePressure(pressure);

        if (release_fraction >= 1.0f || Vehicle_Speed > 2.0f) {
            hha->state = HHA_IDLE;
            release_timer = 0.0f;
        }
        break;
    }
}
```

## State Machine: ESC Intervention Levels

```c
typedef enum {
    ESC_OFF,
    ESC_MONITORING,
    ESC_INTERVENTION_LIGHT,
    ESC_INTERVENTION_HEAVY,
    ESC_PANIC_MODE
} ESC_InterventionLevel_t;

void ESC_StateMachine(void) {
    static ESC_InterventionLevel_t level = ESC_MONITORING;

    float yaw_error = fabs(yaw_ref - yaw_actual);
    float beta = Slip_Angle_Estimate;
    float lateral_accel = IMU_Read_LateralAccel();

    switch (level) {
    case ESC_OFF:
        // ESC disabled by driver (button press)
        // TCS remains active for safety
        if (ESC_Button_Pressed()) {
            level = ESC_MONITORING;
        }
        break;

    case ESC_MONITORING:
        // Normal driving: monitor but don't intervene
        if (yaw_error > 0.05f && fabs(beta) > 0.05f) {
            level = ESC_INTERVENTION_LIGHT;
        }
        break;

    case ESC_INTERVENTION_LIGHT:
        // Small yaw error: gentle brake intervention
        ESC_Controller_t ctrl = {.kp_yaw = 5000.0f, .ki_yaw = 1000.0f};
        float yaw_moment = ESC_YawController(&ctrl, yaw_ref, yaw_actual, DT);

        BrakeForces_t brakes;
        ESC_CalculateBrakeForces(&ctrl, yaw_moment, &brakes, Vehicle_Speed);

        // Apply brakes
        ABS_ApplyBrake(FL, brakes.FL_brake_force);
        ABS_ApplyBrake(FR, brakes.FR_brake_force);
        ABS_ApplyBrake(RL, brakes.RL_brake_force);
        ABS_ApplyBrake(RR, brakes.RR_brake_force);

        // Escalate if error grows
        if (yaw_error > 0.15f || fabs(beta) > 0.15f) {
            level = ESC_INTERVENTION_HEAVY;
        } else if (yaw_error < 0.03f) {
            level = ESC_MONITORING;
        }
        break;

    case ESC_INTERVENTION_HEAVY:
        // Large yaw error: aggressive brake + torque reduction
        ctrl.kp_yaw = 8000.0f;
        ctrl.ki_yaw = 2000.0f;
        yaw_moment = ESC_YawController(&ctrl, yaw_ref, yaw_actual, DT);

        ESC_CalculateBrakeForces(&ctrl, yaw_moment, &brakes, Vehicle_Speed);

        // Request engine torque reduction (30-50%)
        CAN_Send_TorqueReduction(50.0f);

        // Activate ESC warning lamp (flashing)
        HMI_SetESC_Lamp(LAMP_FLASHING);

        // Escalate to panic if critical
        if (fabs(lateral_accel) > 0.9f * GRAVITY || fabs(beta) > 0.22f) {
            level = ESC_PANIC_MODE;
        } else if (yaw_error < 0.08f) {
            level = ESC_INTERVENTION_LIGHT;
        }
        break;

    case ESC_PANIC_MODE:
        // Critical instability: maximum intervention
        ctrl.state = ESC_CRITICAL;
        ESC_CalculateBrakeForces(&ctrl, yaw_moment, &brakes, Vehicle_Speed);

        // Full torque cut
        CAN_Send_TorqueReduction(100.0f);

        // ESC lamp solid on
        HMI_SetESC_Lamp(LAMP_ON);

        // Return to monitoring after stabilization
        if (yaw_error < 0.05f && Vehicle_Speed < 10.0f) {
            level = ESC_MONITORING;
            HMI_SetESC_Lamp(LAMP_OFF);
        }
        break;
    }
}
```

## AUTOSAR Integration

```c
// AUTOSAR Runnable for ESC main control (10ms cyclic, high priority)
FUNC(void, ESC_CODE) ESC_MainFunction(void) {
    // Read sensors via AUTOSAR RTE
    Rte_Read_IMU_YawRate(&yaw_rate_actual);
    Rte_Read_IMU_LateralAccel(&lateral_accel);
    Rte_Read_IMU_LongitudinalAccel(&longitudinal_accel);
    Rte_Read_SensorCluster_SteeringAngle(&steering_angle);
    Rte_Read_SensorCluster_VehicleSpeed(&vehicle_speed);
    Rte_Read_WheelSpeedSensors_FL(&wheel_speed_fl);
    Rte_Read_WheelSpeedSensors_FR(&wheel_speed_fr);
    Rte_Read_WheelSpeedSensors_RL(&wheel_speed_rl);
    Rte_Read_WheelSpeedSensors_RR(&wheel_speed_rr);

    // Calculate reference yaw rate (ideal response)
    VehicleModel_t model = {
        .steering_angle_deg = steering_angle,
        .vehicle_speed_mps = vehicle_speed / 3.6f,
        .wheelbase_m = 2.7f,
        .understeer_gradient = 0.003f
    };
    float yaw_ref = ESC_CalculateReferenceYawRate(&model);

    // Estimate sideslip angle
    SlipAngleEstimator_t slip_est = {
        .yaw_rate = yaw_rate_actual,
        .lat_accel = lateral_accel,
        .longitudinal_vel = model.vehicle_speed_mps,
        .beta_estimate = beta_previous
    };
    ESC_EstimateSideslipAngle(&slip_est, 0.01f);

    // Yaw stability control
    ESC_Controller_t esc_ctrl = {.kp_yaw = 5000.0f, .ki_yaw = 1000.0f};
    float yaw_moment = ESC_YawController(&esc_ctrl, yaw_ref, yaw_rate_actual, 0.01f);

    // Calculate brake forces
    BrakeForces_t brake_forces;
    ESC_CalculateBrakeForces(&esc_ctrl, yaw_moment, &brake_forces, vehicle_speed);

    // Traction control
    float wheel_speeds[4] = {wheel_speed_fl, wheel_speed_fr, wheel_speed_rl, wheel_speed_rr};
    TCS_Controller_t tcs_ctrl = {.target_slip_ratio = 0.12f, .kp_tcs = 50.0f, .ki_tcs = 10.0f};
    TCS_Control(&tcs_ctrl, wheel_speeds, vehicle_speed, 0.01f);

    // Write outputs via AUTOSAR RTE
    Rte_Write_BrakeActuator_FL_Force(brake_forces.FL_brake_force);
    Rte_Write_BrakeActuator_FR_Force(brake_forces.FR_brake_force);
    Rte_Write_BrakeActuator_RL_Force(brake_forces.RL_brake_force);
    Rte_Write_BrakeActuator_RR_Force(brake_forces.RR_brake_force);
    Rte_Write_CAN_ESC_Active(esc_ctrl.state != ESC_STABLE);
    Rte_Write_CAN_TCS_Active(tcs_active);
}
```

## HIL Test Scenarios

### Test Case 1: Sine-with-Dwell Stability Test (FMVSS 126)
```yaml
test_id: ESC_001_SINE_DWELL
objective: Validate ESC performance per FMVSS 126 standard
preconditions:
  - Vehicle speed: 80 kph (50 mph)
  - Road surface: Dry asphalt (μ = 0.9)
  - Tire pressure: Nominal

test_steps:
  1. Apply sinusoidal steering input (0.7 Hz, ±270° amplitude)
  2. Dwell at maximum steering for 0.5 seconds
  3. Monitor yaw rate response
  4. Measure lateral displacement

pass_criteria:
  - Yaw rate overshoot: <35% of steady-state value
  - Vehicle remains stable (no spin-out)
  - Lateral displacement: <1.83 meters from lane center
  - ESC intervention time: <100ms from instability detection
```

### Test Case 2: Split-μ Braking
```yaml
test_id: ESC_002_SPLIT_MU_BRAKING
objective: Validate directional stability during braking on split friction surface
preconditions:
  - Vehicle speed: 100 kph
  - Left wheels on dry asphalt (μ = 0.9)
  - Right wheels on ice (μ = 0.2)

test_steps:
  1. Apply full brake pressure (ABS active)
  2. Monitor yaw rate and lateral deviation
  3. ESC should counter yaw moment from asymmetric braking

pass_criteria:
  - Yaw rate: <5 deg/s deviation from straight line
  - Lateral deviation: <1 meter over 50 meter braking distance
  - Vehicle remains in lane without driver steering correction
```

### Test Case 3: Traction Control on Loose Gravel
```yaml
test_id: ESC_003_TCS_GRAVEL
objective: Validate TCS prevents wheel spin on low-friction surface
preconditions:
  - Vehicle stationary on gravel (μ = 0.4)
  - Rear-wheel drive configuration

test_steps:
  1. Driver applies 100% throttle
  2. Monitor rear wheel speeds vs vehicle speed
  3. TCS should limit slip to 10-15%

pass_criteria:
  - Slip ratio: 10-15% maintained
  - 0-30 kph acceleration time: <6 seconds
  - No sustained wheel spin (>30% slip)
  - Engine torque reduction active during intervention
```

## ISO 26262 Safety Concept

### ASIL Decomposition for ESC

| Function | ASIL | Decomposition | Rationale |
|----------|------|---------------|-----------|
| Yaw rate sensing | ASIL-D | ASIL-C(C) + ASIL-B(B) | Dual IMU sensors with plausibility check |
| Brake intervention | ASIL-D | ASIL-C(C) + ASIL-B(B) | ESC ECU + ABS ECU redundancy |
| Stability control | ASIL-D | No decomposition | Single ESC ECU with internal diagnostics |
| TCS | ASIL-B | N/A | Lower safety criticality than ESC |

### Safety Mechanisms

1. **Sensor Plausibility**: Cross-check yaw rate gyro vs lateral accelerometer (kinematic consistency)
2. **Actuator Monitoring**: Pressure sensors verify commanded vs actual brake force
3. **Fail-Operational**: ESC degrades to ABS-only mode if yaw sensor fails
4. **Manual Override**: Driver can disable ESC (warning lamp), but TCS remains active
5. **Self-Test**: Power-on diagnostics, periodic runtime checks (watchdog, CRC)

## CAN Signal Definitions (DBC)

```dbc
BO_ 270 ESC_Status: 8 ESC
 SG_ ESC_Active : 0|1@1+ (1,0) [0|1] "" PCM,TCM,HMI
 SG_ TCS_Active : 1|1@1+ (1,0) [0|1] "" PCM,HMI
 SG_ HHA_Active : 2|1@1+ (1,0) [0|1] "" HMI
 SG_ YawRate : 8|16@1- (0.01,-327.68) [-327.68|327.67] "deg/s" ADAS,HMI
 SG_ LateralAccel : 24|16@1- (0.001,-32.768) [-32.768|32.767] "m/s2" ADAS,HMI
 SG_ SideslipAngle : 40|16@1- (0.001,-32.768) [-32.768|32.767] "rad" ADAS

BO_ 271 ESC_BrakeRequest: 8 ESC
 SG_ BrakeForce_FL : 0|16@1+ (1,0) [0|65535] "N" ABS
 SG_ BrakeForce_FR : 16|16@1+ (1,0) [0|65535] "N" ABS
 SG_ BrakeForce_RL : 32|16@1+ (1,0) [0|65535] "N" ABS
 SG_ BrakeForce_RR : 48|16@1+ (1,0) [0|65535] "N" ABS
```

## Tools and Calibration

- **IPG CarMaker**: Vehicle dynamics simulation, ESC algorithm validation
- **MATLAB/Simulink**: Model-based development, Kalman filter design
- **dSPACE ASM**: Vehicle dynamics testbed, ESC HIL testing
- **VI-grade**: Driving simulator for ESC tuning
- **Vector CANoe**: ESC CAN message verification

## References
- ISO 26262 (Functional Safety)
- FMVSS 126 (ESC regulation)
- UN ECE R13-H (ESC requirements)
- SAE J2564 (ESC test procedures)
