# Active Suspension Control Skill

## Overview
Expert skill in active and semi-active suspension systems. Covers adaptive damping, air suspension control, ride height adjustment, active roll/pitch control, road preview systems, and comfort/sport mode tuning.

## Core Competencies

### 1. Adaptive Damping (Semi-Active)
- **Magnetorheological (MR) Dampers**: Variable damping via magnetic field
- **Continuously Variable Damping (CVD)**: Adjustable orifice valves
- **Skyhook Control**: Minimize body motion by damping to virtual sky reference
- **Mode Selection**: Comfort (soft), Normal, Sport (stiff)

### 2. Air Suspension Control
- **Ride Height Adjustment**: Lower at highway speed, raise for off-road
- **Load Leveling**: Maintain constant height regardless of passenger/cargo load
- **Compressor Management**: On-demand air supply, pressure reservoir
- **Leak Detection**: Monitor air loss, warn driver

### 3. Active Roll/Pitch Control
- **Anti-Roll Bars**: Active stabilizers with electric/hydraulic actuators
- **Roll Angle Limitation**: <3° body roll in 0.8g lateral acceleration
- **Pitch Suppression**: Reduce dive/squat during braking/acceleration
- **Actuator Bandwidth**: 10-20 Hz for responsive control

### 4. Road Preview (Camera/Lidar)
- **Surface Detection**: Identify potholes, speed bumps ahead
- **Predictive Damping**: Pre-adjust suspension before impact
- **Preview Distance**: 10-30 meters at highway speed
- **Vertical Velocity Compensation**: Minimize wheel displacement

### 5. Comfort vs Sport Tuning
- **Comfort**: Soft damping, maximize isolation, minimize body acceleration
- **Sport**: Stiff damping, minimize body roll, maximize grip
- **Adaptive**: Dynamic tuning based on road surface, driver input

## Control Algorithms

### Skyhook Damping Control
```c
// Minimize body motion by damping to virtual inertial reference
typedef struct {
    float body_velocity;       // Vertical velocity of sprung mass (m/s)
    float wheel_velocity;      // Vertical velocity of unsprung mass (m/s)
    float damping_coeff_max;   // Maximum damping (N·s/m)
    float damping_coeff_min;   // Minimum damping (N·s/m)
} Skyhook_Controller_t;

float Skyhook_CalculateDamping(Skyhook_Controller_t *sky) {
    // Relative velocity (suspension deflection rate)
    float rel_velocity = sky->body_velocity - sky->wheel_velocity;

    // Skyhook control law
    // If body moving up and suspension compressing: high damping
    // If body moving down and suspension extending: high damping
    // Otherwise: low damping (for ride comfort)

    float damping_force;

    if ((sky->body_velocity * rel_velocity) > 0) {
        // Body and relative velocity same sign: high damping
        damping_force = sky->damping_coeff_max * sky->body_velocity;
    } else {
        // Opposite signs: minimal damping
        damping_force = sky->damping_coeff_min * rel_velocity;
    }

    return damping_force;
}

// Convert damping force to MR damper current
float MR_Damper_Current(float damping_force_target) {
    // Magnetorheological damper: current controls viscosity
    // Typical: 0-2A for damping range 500-3000 N·s/m

    float current = (damping_force_target - 500.0f) / 1250.0f;  // N·s/m → A
    return CLAMP(current, 0.0f, 2.0f);
}
```

### Air Suspension Load Leveling
```c
typedef struct {
    float target_height_mm;
    float current_height_mm;
    float load_mass_kg;
    float air_pressure_bar[4];  // Per corner
} AirSuspension_t;

void AirSuspension_LoadLeveling(AirSuspension_t *air, float dt) {
    // Measure current ride height
    air->current_height_mm = Ultrasonic_ReadHeight();

    // Estimate load from suspension deflection
    float height_error = air->target_height_mm - air->current_height_mm;

    // PI controller for height
    static float height_integral = 0.0f;
    height_integral += height_error * dt;
    height_integral = CLAMP(height_integral, -50.0f, 50.0f);

    float pressure_adjust = (KP_HEIGHT * height_error) + (KI_HEIGHT * height_integral);

    // Distribute pressure to all four corners (equal distribution)
    for (int i = 0; i < 4; i++) {
        air->air_pressure_bar[i] += pressure_adjust;
        air->air_pressure_bar[i] = CLAMP(air->air_pressure_bar[i], 3.0f, 12.0f);

        // Command air valves
        if (air->air_pressure_bar[i] > Sensor_ReadPressure(i)) {
            AirValve_Inflate(i);
        } else {
            AirValve_Deflate(i);
        }
    }

    // Activate compressor if reservoir low
    if (Reservoir_Pressure < 10.0f) {
        Compressor_Enable();
    }
}

// Speed-dependent ride height
float AirSuspension_SpeedDependentHeight(float vehicle_speed_kph) {
    // Lower vehicle at high speed for aerodynamics and stability
    if (vehicle_speed_kph > 120.0f) {
        return TARGET_HEIGHT_SPORT;  // -20mm
    } else if (vehicle_speed_kph > 80.0f) {
        return TARGET_HEIGHT_NORMAL; // 0mm
    } else {
        return TARGET_HEIGHT_COMFORT; // +10mm
    }
}
```

### Active Anti-Roll Control
```c
// Electric/hydraulic active stabilizer bars
typedef struct {
    float lateral_accel;
    float roll_angle_deg;
    float target_roll_angle_deg;
    float actuator_torque_nm[2];  // Front and rear
} ActiveRoll_Controller_t;

void ActiveRoll_Control(ActiveRoll_Controller_t *roll, float dt) {
    // Target roll angle based on lateral acceleration
    // Allow some roll for driver feedback, but limit excessive lean
    roll->target_roll_angle_deg = roll->lateral_accel / GRAVITY * 1.5f;  // degrees
    roll->target_roll_angle_deg = CLAMP(roll->target_roll_angle_deg, -3.0f, 3.0f);

    // PID controller for roll angle
    float roll_error = roll->target_roll_angle_deg - roll->roll_angle_deg;

    static float roll_integral = 0.0f, roll_prev_error = 0.0f;
    roll_integral += roll_error * dt;
    float roll_derivative = (roll_error - roll_prev_error) / dt;
    roll_prev_error = roll_error;

    float roll_torque = (KP_ROLL * roll_error) + (KI_ROLL * roll_integral) + (KD_ROLL * roll_derivative);

    // Distribute torque front/rear (60/40 split typical)
    roll->actuator_torque_nm[FRONT] = roll_torque * 0.60f;
    roll->actuator_torque_nm[REAR] = roll_torque * 0.40f;

    // Command actuators
    ActiveStabilizer_SetTorque(FRONT, roll->actuator_torque_nm[FRONT]);
    ActiveStabilizer_SetTorque(REAR, roll->actuator_torque_nm[REAR]);
}
```

### Road Preview with Camera
```c
typedef struct {
    float preview_distance_m;
    float obstacle_height_mm;
    float time_to_impact_s;
    bool pothole_detected;
} RoadPreview_t;

void RoadPreview_PredictiveDamping(RoadPreview_t *preview, float vehicle_speed) {
    // Camera/lidar detects road surface ahead
    preview->pothole_detected = Camera_DetectPothole(&preview->obstacle_height_mm);

    if (preview->pothole_detected) {
        preview->time_to_impact_s = preview->preview_distance_m / vehicle_speed;

        // Pre-adjust damping before impact
        if (preview->time_to_impact_s < 1.0f) {
            // Soften damping to absorb impact
            for (int wheel = 0; wheel < 4; wheel++) {
                MR_Damper_SetCurrent(wheel, DAMPING_SOFT);
            }

            // After impact (100ms delay), return to normal
            static float post_impact_timer = 0.0f;
            post_impact_timer += DT;

            if (post_impact_timer > 0.1f) {
                for (int wheel = 0; wheel < 4; wheel++) {
                    MR_Damper_SetCurrent(wheel, DAMPING_NORMAL);
                }
                post_impact_timer = 0.0f;
                preview->pothole_detected = false;
            }
        }
    }
}
```

## Mode Selection State Machine

```c
typedef enum {
    SUSP_MODE_COMFORT,
    SUSP_MODE_NORMAL,
    SUSP_MODE_SPORT,
    SUSP_MODE_OFFROAD
} SuspensionMode_t;

void Suspension_ModeSelection(SuspensionMode_t mode) {
    switch (mode) {
    case SUSP_MODE_COMFORT:
        // Soft damping, high ride height, minimal body control
        MR_Damper_SetCoefficient(1000.0f);   // N·s/m (soft)
        AirSuspension_SetHeight(TARGET_HEIGHT_COMFORT);
        ActiveRoll_SetGain(0.5f);  // Allow some roll
        break;

    case SUSP_MODE_NORMAL:
        // Balanced damping, standard height
        MR_Damper_SetCoefficient(2000.0f);   // N·s/m (medium)
        AirSuspension_SetHeight(TARGET_HEIGHT_NORMAL);
        ActiveRoll_SetGain(1.0f);
        break;

    case SUSP_MODE_SPORT:
        // Stiff damping, low height, maximum body control
        MR_Damper_SetCoefficient(3000.0f);   // N·s/m (stiff)
        AirSuspension_SetHeight(TARGET_HEIGHT_SPORT);
        ActiveRoll_SetGain(1.5f);  // Minimize roll aggressively
        break;

    case SUSP_MODE_OFFROAD:
        // Soft damping, maximum height, long travel
        MR_Damper_SetCoefficient(800.0f);    // N·s/m (very soft)
        AirSuspension_SetHeight(TARGET_HEIGHT_OFFROAD);  // +40mm
        ActiveRoll_Disable();  // Allow articulation
        break;
    }
}
```

## AUTOSAR Integration

```c
FUNC(void, SUSP_CODE) Suspension_MainFunction(void) {
    // Read sensors (100Hz task)
    Rte_Read_IMU_RollAngle(&roll_angle);
    Rte_Read_IMU_PitchAngle(&pitch_angle);
    Rte_Read_IMU_VerticalAccel(&vertical_accel);
    Rte_Read_HeightSensors_FL(&height_fl);
    Rte_Read_HMI_SuspensionMode(&mode);

    // Estimate body/wheel velocities
    static float body_pos_prev = 0.0f;
    float body_pos = (height_fl + height_fr + height_rl + height_rr) / 4.0f;
    float body_velocity = (body_pos - body_pos_prev) / DT;
    body_pos_prev = body_pos;

    // Skyhook damping control
    Skyhook_Controller_t sky = {.body_velocity = body_velocity};
    float damping_force = Skyhook_CalculateDamping(&sky);

    // Mode-dependent gain
    switch (mode) {
    case SUSP_MODE_COMFORT: damping_force *= 0.6f; break;
    case SUSP_MODE_SPORT: damping_force *= 1.2f; break;
    }

    // Apply to dampers
    for (int i = 0; i < 4; i++) {
        float current = MR_Damper_Current(damping_force);
        Rte_Write_MR_Damper_Current(i, current);
    }

    // Air suspension load leveling
    AirSuspension_t air;
    air.target_height_mm = AirSuspension_SpeedDependentHeight(vehicle_speed);
    AirSuspension_LoadLeveling(&air, DT);

    // Active roll control
    ActiveRoll_Controller_t roll_ctrl = {.lateral_accel = lateral_accel, .roll_angle_deg = roll_angle};
    ActiveRoll_Control(&roll_ctrl, DT);
}
```

## HIL Test Scenarios

### Test Case 1: Comfort Mode on Rough Road
```yaml
test_id: SUSP_001_COMFORT_ROUGH
objective: Maximize isolation in comfort mode
preconditions:
  - Suspension mode: Comfort
  - Road: Belgian paving (high frequency bumps)
  - Vehicle speed: 60 kph

pass_criteria:
  - Body vertical acceleration: <0.5 g RMS
  - Damping force: 500-1200 N (soft)
  - Passenger comfort rating: >7/10
```

### Test Case 2: Sport Mode Cornering
```yaml
test_id: SUSP_002_SPORT_CORNERING
objective: Minimize body roll in sport mode
preconditions:
  - Suspension mode: Sport
  - Skidpad cornering: 0.9g lateral
  - Vehicle speed: 80 kph

pass_criteria:
  - Body roll angle: <2.5 degrees
  - Active roll actuator torque: 1500-2500 Nm
  - Damping force: 2500-3500 N (stiff)
```

## References
- ISO 26262 (Safety for active systems)
- SAE J2877 (Suspension test procedures)
