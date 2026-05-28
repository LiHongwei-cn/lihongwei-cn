# ABS/EBD Anti-lock Braking System Skill

## Overview
Expert skill in Anti-lock Braking System (ABS) and Electronic Brake-force Distribution (EBD) development. Covers wheel slip control, pressure modulation, EBD algorithms, brake-by-wire, regenerative braking coordination, and brake fade compensation.

## Core Competencies

### 1. Wheel Slip Control
- **Target Slip Ratio**: 10-20% for optimal braking (peak μ on most surfaces)
- **Slip Calculation**: λ = (vwheel - vvehicle) / vvehicle
- **Control Modes**: Build-up, Hold, Release phases
- **Surface Adaptation**: Adjust control aggressiveness for dry/wet/ice

### 2. Pressure Modulation
- **Hydraulic Valve Control**: Inlet/outlet solenoids, return pump
- **PWM Frequency**: 10-20 Hz typical ABS cycling
- **Pressure Estimation**: No direct sensor, estimate from valve timing
- **Pedal Feel**: Minimize pulsation feedback to driver

### 3. Electronic Brake-force Distribution (EBD)
- **Dynamic Load Transfer**: Front/rear brake bias based on deceleration
- **Proportioning**: Prevent rear wheel lockup (stability)
- **Empty vs Loaded**: Adjust distribution based on vehicle weight
- **Trailer Detection**: Modify EBD for towing conditions

### 4. Regenerative Braking Coordination
- **Blending Control**: Seamless transition hydraulic ↔ regenerative
- **Regen Priority**: Max energy recovery while meeting brake demand
- **Pedal Feel**: Maintain consistent deceleration feel
- **Safety Backup**: Full hydraulic if electric system fails

### 5. Brake-by-Wire (BBW)
- **Electro-Mechanical Brakes (EMB)**: Electric caliper actuators
- **Decoupled Pedal**: Pedal feel simulator, no direct hydraulic link
- **Redundancy**: Dual ECUs, backup hydraulic circuit
- **Latency**: <100ms brake request to force application

## Control Algorithms

### ABS Slip Control (Bang-Bang with Hysteresis)
```c
typedef enum {
    ABS_BUILD,      // Increase pressure
    ABS_HOLD,       // Maintain pressure
    ABS_RELEASE     // Decrease pressure
} ABS_Phase_t;

typedef struct {
    float wheel_speed_mps;
    float vehicle_speed_mps;
    float slip_ratio;
    ABS_Phase_t phase;
    uint16_t cycle_count;
} ABS_WheelController_t;

void ABS_WheelControl(ABS_WheelController_t *abs, float dt) {
    // Calculate slip ratio
    if (abs->vehicle_speed_mps > 0.1f) {
        abs->slip_ratio = (abs->vehicle_speed_mps - abs->wheel_speed_mps) / abs->vehicle_speed_mps;
    } else {
        abs->slip_ratio = 0.0f;
    }

    // State machine for pressure modulation
    switch (abs->phase) {
    case ABS_BUILD:
        // Normal braking: increase pressure
        Hydraulic_OpenInletValve();
        Hydraulic_CloseOutletValve();

        // Transition to HOLD if slip exceeds threshold
        if (abs->slip_ratio > SLIP_THRESHOLD_HIGH) {  // 20%
            abs->phase = ABS_HOLD;
        }
        break;

    case ABS_HOLD:
        // Hold current pressure
        Hydraulic_CloseInletValve();
        Hydraulic_CloseOutletValve();

        // Transition to RELEASE if slip still increasing
        if (abs->slip_ratio > SLIP_THRESHOLD_CRITICAL) {  // 25%
            abs->phase = ABS_RELEASE;
        } else if (abs->slip_ratio < SLIP_THRESHOLD_LOW) {  // 15%
            abs->phase = ABS_BUILD;
        }
        break;

    case ABS_RELEASE:
        // Decrease pressure to reduce slip
        Hydraulic_CloseInletValve();
        Hydraulic_OpenOutletValve();
        Hydraulic_ActivateReturnPump();

        abs->cycle_count++;

        // Transition to BUILD when slip decreases
        if (abs->slip_ratio < SLIP_THRESHOLD_LOW) {
            abs->phase = ABS_BUILD;
        }
        break;
    }
}
```

### EBD Front/Rear Distribution
```c
float EBD_CalculateRearBrakeBias(float deceleration, float vehicle_mass, float cg_height) {
    // Dynamic load transfer: Front axle load increases during braking
    const float WHEELBASE = 2.7f;         // m
    const float STATIC_FRONT_LOAD = 0.60f; // 60% front static

    // Load transfer to front axle
    float dynamic_front_load = STATIC_FRONT_LOAD + (deceleration * cg_height / (GRAVITY * WHEELBASE));
    dynamic_front_load = CLAMP(dynamic_front_load, 0.55f, 0.75f);

    // Rear brake bias (inverse of front load)
    float rear_bias = 1.0f - dynamic_front_load;

    // Additional safety margin to prevent rear lockup
    rear_bias *= 0.85f;

    return CLAMP(rear_bias, 0.20f, 0.40f);
}

void EBD_ApplyDistribution(float total_brake_force, float deceleration) {
    float rear_bias = EBD_CalculateRearBrakeBias(deceleration, VEHICLE_MASS, CG_HEIGHT);

    float front_force = total_brake_force * (1.0f - rear_bias);
    float rear_force = total_brake_force * rear_bias;

    // Apply to each wheel (split left/right equally)
    Hydraulic_SetPressure(WHEEL_FL, front_force / 2.0f);
    Hydraulic_SetPressure(WHEEL_FR, front_force / 2.0f);
    Hydraulic_SetPressure(WHEEL_RL, rear_force / 2.0f);
    Hydraulic_SetPressure(WHEEL_RR, rear_force / 2.0f);
}
```

### Regenerative Braking Blending
```c
typedef struct {
    float brake_pedal_force;      // Driver demand (N)
    float total_decel_target;     // Target deceleration (m/s²)
    float regen_decel_available;  // Max regen from motor (m/s²)
    float hydraulic_decel;        // Hydraulic brake component
    float regen_decel;            // Regen brake component
} RegenBlending_t;

void RegenBraking_Blend(RegenBlending_t *regen) {
    // Convert pedal force to deceleration demand
    regen->total_decel_target = regen->brake_pedal_force / 50.0f;  // N → m/s²

    // Prioritize regen for energy recovery
    regen->regen_decel = fmin(regen->total_decel_target, regen->regen_decel_available);

    // Hydraulic makes up the difference
    regen->hydraulic_decel = regen->total_decel_target - regen->regen_decel;

    // Seamless transition: ramp regen, compensate with hydraulic
    static float regen_prev = 0.0f;
    float regen_rate = (regen->regen_decel - regen_prev) / DT;

    if (fabs(regen_rate) > MAX_REGEN_RATE) {
        // Regen changing too fast, compensate with hydraulic
        regen->hydraulic_decel += regen_rate * 0.5f;
    }

    regen_prev = regen->regen_decel;

    // Send commands
    CAN_Send_RegenTorqueRequest(regen->regen_decel * VEHICLE_MASS * TIRE_RADIUS);
    Hydraulic_SetDeceleration(regen->hydraulic_decel);
}
```

### Brake Fade Compensation
```c
// Compensate for brake pad temperature effects
float BrakeFade_Compensation(float brake_temp_celsius) {
    // Friction coefficient drops at high temperature
    // Typical: μ = 0.40 at 20°C, μ = 0.30 at 500°C
    float mu_baseline = 0.40f;
    float mu_degraded = 0.30f;
    float temp_threshold = 300.0f;  // °C
    float temp_critical = 600.0f;

    if (brake_temp_celsius < temp_threshold) {
        return 1.0f;  // No compensation needed
    }

    // Linear fade model between threshold and critical
    float fade_factor = 1.0f - ((brake_temp_celsius - temp_threshold) / (temp_critical - temp_threshold)) * (1.0f - mu_degraded / mu_baseline);

    fade_factor = CLAMP(fade_factor, 0.6f, 1.0f);

    // Increase pedal pressure to maintain braking force
    float compensation = 1.0f / fade_factor;

    // Warning if severe fade detected
    if (fade_factor < 0.75f) {
        HMI_SetBrakeFadeWarning(true);
    }

    return compensation;
}
```

## HIL Test Scenarios

### Test Case 1: ABS on Ice (Low-μ Surface)
```yaml
test_id: ABS_001_ICE_BRAKING
objective: Prevent wheel lockup on slippery surface
preconditions:
  - Vehicle speed: 60 kph
  - Surface: Ice (μ = 0.15)
  - Full brake pedal application

test_steps:
  1. Apply 100% brake pressure
  2. Monitor wheel speeds vs vehicle speed
  3. Verify ABS cycling (10-15 Hz)
  4. Measure stopping distance

pass_criteria:
  - No wheel lockup (slip ratio <30%)
  - Steering control maintained
  - Stopping distance: <80 meters
  - ABS activation within 100ms of slip detection
```

### Test Case 2: Split-μ Braking Stability
```yaml
test_id: ABS_002_SPLIT_MU
objective: Maintain directional stability on asymmetric friction
preconditions:
  - Vehicle speed: 80 kph
  - Left wheels: Dry asphalt (μ = 0.9)
  - Right wheels: Wet asphalt (μ = 0.5)

test_steps:
  1. Apply full braking
  2. Monitor yaw rate (ESC coordinated)
  3. Verify individual wheel ABS control

pass_criteria:
  - Yaw rate: <3 deg/s deviation
  - Vehicle tracks straight (±0.5m lateral deviation)
  - Left wheels: Higher brake force than right
  - No driver steering input required
```

### Test Case 3: Regenerative Braking Blend
```yaml
test_id: ABS_003_REGEN_BLEND
objective: Seamless hydraulic-regen coordination
preconditions:
  - EV with regen capability
  - Vehicle speed: 50 kph
  - Battery SOC: 70% (regen available)

test_steps:
  1. Apply 50% brake pedal
  2. Monitor regen torque vs hydraulic pressure
  3. Verify deceleration consistency
  4. Simulate regen unavailable (low SOC)

pass_criteria:
  - Regen prioritized: 80% of braking from electric motor
  - Hydraulic makeup: Smooth transition if regen saturates
  - Pedal feel: Consistent throughout (no jerk)
  - Regen→hydraulic transition: <50ms
```

## ISO 26262 Safety (ASIL-D)

### Safety Mechanisms
- **Redundant Wheel Speed Sensors**: Dual-channel Hall sensors per wheel
- **Plausibility Checks**: Compare wheel speeds, detect sensor faults
- **Failsafe Brake**: Revert to manual hydraulic on ECU failure
- **Watchdog**: Independent external monitor, reset on timeout

## CAN Signals (DBC)

```dbc
BO_ 290 ABS_Status: 8 ABS
 SG_ ABS_Active : 0|1@1+ (1,0) [0|1] "" ESC,HMI
 SG_ WheelSpeed_FL : 8|16@1+ (0.01,0) [0|655.35] "m/s" ESC,PCM
 SG_ WheelSpeed_FR : 24|16@1+ (0.01,0) [0|655.35] "m/s" ESC,PCM
 SG_ WheelSpeed_RL : 40|16@1+ (0.01,0) [0|655.35] "m/s" ESC,PCM
 SG_ WheelSpeed_RR : 56|16@1+ (0.01,0) [0|655.35] "m/s" ESC,PCM
```

## References
- UN ECE R13-H (ABS regulation)
- ISO 26262 (Functional Safety)
- SAE J2909 (ABS test procedures)
