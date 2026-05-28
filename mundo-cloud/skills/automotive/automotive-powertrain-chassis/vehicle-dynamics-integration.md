# Vehicle Dynamics Integration Skill

## Overview
Expert skill in integrated chassis control systems coordinating ESC, ABS, EPS, suspension, torque vectoring, and all-wheel drive (AWD). Covers vehicle motion control, lateral/longitudinal dynamics models, torque distribution strategies, and multi-domain coordination.

## Core Competencies

### 1. Integrated Chassis Controller (ICC)
- **Central Coordination**: Single ECU arbitrates ESC, ABS, EPS, suspension requests
- **Priority Management**: Safety systems (ESC) override comfort systems (suspension)
- **Torque Budget**: Distribute available propulsion/braking torque optimally
- **State Estimation**: Fuse sensors for accurate vehicle state (β, ax, ay, ψ̇)

### 2. Torque Vectoring
- **Left-Right Distribution**: Differential brake force or motor torque for yaw control
- **Understeer Mitigation**: Send more torque to outside wheel in corner
- **Oversteer Correction**: Reduce inside wheel torque, increase outside
- **Performance Enhancement**: Faster corner entry/exit via active yaw moment

### 3. All-Wheel Drive (AWD) Control
- **Torque Split**: Front/rear distribution (50/50 default, dynamic adjustment)
- **Predictive Engagement**: Pre-engage rear axle before slip detected
- **Coupling Control**: Electro-mechanical clutch or active differential
- **Efficiency Mode**: Disconnect rear axle for FWD-only cruising (fuel economy)

### 4. Vehicle Motion Controller (VMC)
- **Reference Model**: Ideal vehicle response (bicycle model, single-track)
- **MIMO Control**: Multi-input (steering, throttle, brake) multi-output (ax, ay, ψ̇)
- **MPC (Model Predictive Control)**: Optimal control over prediction horizon
- **Cascaded Control**: High-level (trajectory) → mid-level (motion) → low-level (actuators)

### 5. Lateral/Longitudinal Dynamics
- **Bicycle Model**: 2-DOF model for lateral dynamics (yaw + sideslip)
- **Tire Models**: Pacejka Magic Formula, linear approximation for control
- **Load Transfer**: Vertical load changes affect lateral force capacity
- **Combined Slip**: Friction ellipse for simultaneous braking + cornering

## Control Algorithms

### Bicycle Model (Reference Yaw Rate)
```c
// 2-DOF bicycle model for vehicle lateral dynamics
typedef struct {
    float mass;              // Vehicle mass (kg)
    float yaw_inertia;       // Yaw moment of inertia (kg⋅m²)
    float wheelbase;         // Front to rear axle distance (m)
    float a, b;              // CG to front/rear axle (m)
    float cf, cr;            // Front/rear cornering stiffness (N/rad)
} BicycleModel_t;

void BicycleModel_Update(BicycleModel_t *model, float delta, float vx, float dt) {
    // State: [beta, psi_dot] (sideslip angle, yaw rate)
    static float beta = 0.0f, psi_dot = 0.0f;

    // Tire slip angles
    float alpha_f = delta - (beta + model->a * psi_dot / vx);
    float alpha_r = -(beta - model->b * psi_dot / vx);

    // Lateral tire forces (linear approximation)
    float Fyf = model->cf * alpha_f;
    float Fyr = model->cr * alpha_r;

    // Equations of motion
    float beta_dot = (Fyf + Fyr) / (model->mass * vx) - psi_dot;
    float psi_ddot = (model->a * Fyf - model->b * Fyr) / model->yaw_inertia;

    // Integrate
    beta += beta_dot * dt;
    psi_dot += psi_ddot * dt;

    // Output reference yaw rate
    ref_yaw_rate = psi_dot;
}
```

### Torque Vectoring Distribution
```c
typedef struct {
    float yaw_moment_desired;  // From ESC or driver intent (N⋅m)
    float total_torque;        // Available propulsion torque (N⋅m)
    float left_torque;         // Left wheels
    float right_torque;        // Right wheels
    float track_width;         // Left-right wheel distance (m)
} TorqueVectoring_t;

void TorqueVectoring_Distribute(TorqueVectoring_t *tv) {
    // Base torque split (50/50)
    float base_torque_per_side = tv->total_torque / 2.0f;

    // Additional torque difference to create yaw moment
    // Yaw moment = (T_right - T_left) * track_width / 2
    float torque_diff = tv->yaw_moment_desired / (tv->track_width / 2.0f);

    // Apply differential
    tv->left_torque = base_torque_per_side - torque_diff / 2.0f;
    tv->right_torque = base_torque_per_side + torque_diff / 2.0f;

    // Limit torque per side (motor/brake capability)
    tv->left_torque = CLAMP(tv->left_torque, -5000.0f, 5000.0f);
    tv->right_torque = CLAMP(tv->right_torque, -5000.0f, 5000.0f);

    // Send to drivetrain
    CAN_Send_LeftWheelTorque(tv->left_torque);
    CAN_Send_RightWheelTorque(tv->right_torque);
}
```

### AWD Torque Split Control
```c
typedef struct {
    float front_torque_percent;   // 0-100%
    float rear_torque_percent;    // 0-100%
    float front_slip;             // Front axle slip ratio
    float rear_slip;              // Rear axle slip ratio
    bool efficiency_mode;         // Disconnect rear for FWD
} AWD_Controller_t;

void AWD_TorqueSplit(AWD_Controller_t *awd, float total_torque) {
    // Default: 50/50 split for balanced traction
    awd->front_torque_percent = 50.0f;
    awd->rear_torque_percent = 50.0f;

    // Efficiency mode: FWD only (highway cruising)
    if (awd->efficiency_mode && total_torque < 500.0f) {
        awd->front_torque_percent = 100.0f;
        awd->rear_torque_percent = 0.0f;
        Clutch_DisconnectRear();
        return;
    } else {
        Clutch_EngageRear();
    }

    // Dynamic adjustment based on slip
    if (awd->front_slip > 0.15f) {
        // Front slipping: send more torque to rear
        awd->rear_torque_percent += 10.0f;
        awd->front_torque_percent -= 10.0f;
    } else if (awd->rear_slip > 0.15f) {
        // Rear slipping: send more torque to front
        awd->front_torque_percent += 10.0f;
        awd->rear_torque_percent -= 10.0f;
    }

    // Clamp percentages
    awd->front_torque_percent = CLAMP(awd->front_torque_percent, 0.0f, 100.0f);
    awd->rear_torque_percent = 100.0f - awd->front_torque_percent;

    // Apply torque split
    float front_torque = total_torque * awd->front_torque_percent / 100.0f;
    float rear_torque = total_torque * awd->rear_torque_percent / 100.0f;

    CAN_Send_FrontAxleTorque(front_torque);
    CAN_Send_RearAxleTorque(rear_torque);
}
```

### Integrated Chassis Controller (Priority Arbitration)
```c
typedef enum {
    ICC_PRIORITY_CRITICAL,   // ESC, ABS (safety)
    ICC_PRIORITY_HIGH,       // TCS, AWD
    ICC_PRIORITY_MEDIUM,     // Torque vectoring, EPS assist
    ICC_PRIORITY_LOW         // Suspension comfort
} ICC_Priority_t;

typedef struct {
    ICC_Priority_t priority;
    float torque_request;
    float brake_request;
    bool active;
} ICC_Request_t;

void ICC_Arbitrate(ICC_Request_t requests[], uint8_t count) {
    // Sort requests by priority
    qsort(requests, count, sizeof(ICC_Request_t), priority_comparator);

    // Highest priority request wins
    ICC_Request_t active_request = {0};

    for (int i = 0; i < count; i++) {
        if (requests[i].active && requests[i].priority >= active_request.priority) {
            active_request = requests[i];
        }
    }

    // Apply winning request
    switch (active_request.priority) {
    case ICC_PRIORITY_CRITICAL:
        // ESC/ABS: full control, override driver
        CAN_Send_TorqueRequest(active_request.torque_request);
        Brake_ApplyForce(active_request.brake_request);
        break;

    case ICC_PRIORITY_HIGH:
        // TCS/AWD: blend with driver input
        float blended_torque = (active_request.torque_request + driver_torque) / 2.0f;
        CAN_Send_TorqueRequest(blended_torque);
        break;

    case ICC_PRIORITY_MEDIUM:
    case ICC_PRIORITY_LOW:
        // Comfort systems: only if no higher priority active
        if (no_critical_systems_active) {
            Apply_ComfortFeatures();
        }
        break;
    }
}
```

### Vehicle State Estimator (Extended Kalman Filter)
```c
// Estimate vehicle state: [vx, vy, psi_dot, beta]
typedef struct {
    float state[4];         // State vector
    float P[4][4];          // Covariance matrix
    float Q[4][4];          // Process noise
    float R[4][4];          // Measurement noise
} EKF_StateEstimator_t;

void EKF_Update(EKF_StateEstimator_t *ekf, float measurements[4], float dt) {
    // Prediction step
    // State transition: x_k+1 = f(x_k, u_k)
    ekf->state[0] += ekf->state[1] * cosf(ekf->state[3]) * dt;  // vx
    ekf->state[1] += ekf->state[2] * ekf->state[0] * dt;        // vy
    ekf->state[2] = ekf->state[2];                               // psi_dot (measured)
    ekf->state[3] = atanf(ekf->state[1] / ekf->state[0]);       // beta

    // Jacobian of state transition
    float F[4][4] = {/* ... compute Jacobian ... */};

    // Predict covariance: P = F*P*F' + Q
    MatrixMultiply(F, ekf->P, 4, 4);
    MatrixAdd(ekf->P, ekf->Q, 4, 4);

    // Correction step
    // Innovation: y = z - h(x)
    float innovation[4];
    for (int i = 0; i < 4; i++) {
        innovation[i] = measurements[i] - ekf->state[i];
    }

    // Kalman gain: K = P*H' / (H*P*H' + R)
    float K[4][4] = {/* ... compute gain ... */};

    // Update state: x = x + K*y
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            ekf->state[i] += K[i][j] * innovation[j];
        }
    }

    // Update covariance: P = (I - K*H)*P
    // ... (simplified for brevity)
}
```

## AUTOSAR Integration

```c
// 10ms high-priority task for integrated chassis control
FUNC(void, ICC_CODE) ICC_MainFunction(void) {
    // Read all chassis sensor inputs
    Rte_Read_IMU_YawRate(&yaw_rate);
    Rte_Read_IMU_LateralAccel(&lat_accel);
    Rte_Read_SteeringAngle(&steering_angle);
    Rte_Read_WheelSpeeds(&wheel_speeds);
    Rte_Read_ECM_EngineTorque(&engine_torque);

    // State estimation (EKF)
    EKF_StateEstimator_t ekf;
    float measurements[4] = {wheel_speed_avg, lat_accel, yaw_rate, 0.0f};
    EKF_Update(&ekf, measurements, 0.01f);

    // Reference model (ideal vehicle response)
    BicycleModel_t model = {/* vehicle parameters */};
    BicycleModel_Update(&model, steering_angle, ekf.state[0], 0.01f);

    // Collect subsystem requests
    ICC_Request_t requests[5];
    requests[0] = ESC_GetRequest();
    requests[1] = ABS_GetRequest();
    requests[2] = TCS_GetRequest();
    requests[3] = TorqueVectoring_GetRequest();
    requests[4] = Suspension_GetRequest();

    // Arbitrate and apply
    ICC_Arbitrate(requests, 5);

    // AWD torque split
    AWD_Controller_t awd;
    AWD_TorqueSplit(&awd, engine_torque);

    // Torque vectoring
    TorqueVectoring_t tv = {.yaw_moment_desired = ref_yaw_rate - yaw_rate};
    TorqueVectoring_Distribute(&tv);
}
```

## HIL Test Scenarios

### Test Case 1: ESC + Torque Vectoring Coordination
```yaml
test_id: ICC_001_ESC_TV_COORD
objective: Coordinated yaw control via ESC braking and torque vectoring
preconditions:
  - Vehicle speed: 80 kph
  - Cornering: 0.7g lateral
  - Oversteer condition (yaw rate error >0.1 rad/s)

test_steps:
  1. Trigger oversteer via steering input
  2. ESC applies outer front brake
  3. Torque vectoring reduces inner wheel torque
  4. Monitor combined yaw moment

pass_criteria:
  - ESC and TV act simultaneously (no conflict)
  - Total yaw moment: ESC 60%, TV 40% contribution
  - Vehicle stabilized within 0.5 seconds
```

### Test Case 2: AWD Slip-Based Torque Transfer
```yaml
test_id: ICC_002_AWD_SLIP_TRANSFER
objective: Dynamic front/rear split based on wheel slip
preconditions:
  - Low-μ surface (μ = 0.3)
  - Acceleration from standstill
  - AWD 50/50 initial split

test_steps:
  1. Apply full throttle
  2. Monitor front/rear wheel slip
  3. AWD adjusts torque split
  4. Measure 0-60 kph time

pass_criteria:
  - Front slip detected: Rear torque increases to 70%
  - Rear slip detected: Front torque increases to 70%
  - 0-60 kph time: <8 seconds on ice
  - No sustained wheel spin (>20% slip)
```

## References
- Rajamani, "Vehicle Dynamics and Control" (bicycle model)
- ISO 26262 (Safety for integrated systems)
- SAE J2564 (ESC test procedures)
- Pacejka, "Tire and Vehicle Dynamics" (Magic Formula)
