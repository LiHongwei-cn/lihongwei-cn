# Safety Mechanisms and Patterns for ISO 26262

Comprehensive catalog of safety mechanisms for ASIL-D automotive systems, including redundancy patterns, diagnostic coverage techniques, watchdogs, memory protection, CRC/checksums, plausibility checks, and safe state management.

## Safety Mechanism Categories

### Detection Mechanisms
- Identify faults before they cause failures
- Achieve diagnostic coverage targets
- Enable transition to safe state within FTTI

### Control Mechanisms
- Manage system behavior during faults
- Implement redundancy and voting
- Provide graceful degradation paths

### Warning Mechanisms
- Alert driver/system to faults
- Trigger DTC storage
- Activate warning lamps/signals

## Redundancy Patterns

### 1. Homogeneous Redundancy (1oo2)

**One-out-of-Two Configuration:**

```
┌──────────┐
│ Sensor A │─────┐
└──────────┘     │      ┌────────┐     ┌──────────┐
                 ├─────>│ Voter  │────>│ Actuator │
┌──────────┐     │      └────────┘     └──────────┘
│ Sensor B │─────┘
└──────────┘
```

**Characteristics:**
- Two identical channels (same design, same component)
- Any one channel can drive the system
- ASIL decomposition: ASIL-D(D) = ASIL-B(D) + ASIL-B(D)
- Requires dependent failure analysis (common cause)

**C Implementation:**
```c
// 1oo2 redundant sensor processing
typedef struct {
    float sensor_a_value;
    float sensor_b_value;
    bool sensor_a_valid;
    bool sensor_b_valid;
    uint32_t fault_counter_a;
    uint32_t fault_counter_b;
} RedundantSensor_t;

typedef enum {
    VOTER_OUTPUT_VALID,
    VOTER_OUTPUT_DEGRADED,
    VOTER_OUTPUT_FAULT
} VoterStatus_t;

VoterStatus_t ProcessRedundantSensors(
    RedundantSensor_t *sensors,
    float *output_value
) {
    const float TOLERANCE = 0.05f;  // 5% agreement tolerance
    const uint32_t FAULT_THRESHOLD = 3;

    // Range check both sensors
    if (!RangeCheck(sensors->sensor_a_value, 0.0f, 100.0f)) {
        sensors->sensor_a_valid = false;
        sensors->fault_counter_a++;
    } else {
        sensors->sensor_a_valid = true;
    }

    if (!RangeCheck(sensors->sensor_b_value, 0.0f, 100.0f)) {
        sensors->sensor_b_valid = false;
        sensors->fault_counter_b++;
    } else {
        sensors->sensor_b_valid = true;
    }

    // Both sensors valid - check agreement
    if (sensors->sensor_a_valid && sensors->sensor_b_valid) {
        float difference = fabsf(sensors->sensor_a_value - sensors->sensor_b_value);
        float average = (sensors->sensor_a_value + sensors->sensor_b_value) / 2.0f;

        if (difference / average < TOLERANCE) {
            // Sensors agree - use average
            *output_value = average;
            return VOTER_OUTPUT_VALID;
        } else {
            // Sensors disagree - both might be faulty
            // Use most conservative value
            *output_value = fmaxf(sensors->sensor_a_value, sensors->sensor_b_value);
            return VOTER_OUTPUT_DEGRADED;
        }
    }

    // Only sensor A valid
    if (sensors->sensor_a_valid && !sensors->sensor_b_valid) {
        if (sensors->fault_counter_b < FAULT_THRESHOLD) {
            *output_value = sensors->sensor_a_value;
            return VOTER_OUTPUT_DEGRADED;
        } else {
            return VOTER_OUTPUT_FAULT;
        }
    }

    // Only sensor B valid
    if (!sensors->sensor_a_valid && sensors->sensor_b_valid) {
        if (sensors->fault_counter_a < FAULT_THRESHOLD) {
            *output_value = sensors->sensor_b_value;
            return VOTER_OUTPUT_DEGRADED;
        } else {
            return VOTER_OUTPUT_FAULT;
        }
    }

    // Both sensors invalid
    return VOTER_OUTPUT_FAULT;
}
```

### 2. Heterogeneous Redundancy

**Different Physical Principles:**

```
┌────────────┐
│   Radar    │────┐
└────────────┘    │     ┌─────────┐      ┌──────────┐
                  ├────>│ Fusion  │─────>│ Decision │
┌────────────┐    │     └─────────┘      └──────────┘
│   Camera   │────┘
└────────────┘
```

**Benefits:**
- Better independence (different failure modes)
- Common cause failures less likely
- Easier ASIL decomposition justification

**Example - Vehicle Speed Estimation:**
```c
// Heterogeneous speed measurement
typedef struct {
    float wheel_speed_fl;      // Front-left wheel speed sensor
    float wheel_speed_fr;      // Front-right wheel speed sensor
    float accelerometer_speed; // Integrated from accelerometer
    float gps_speed;           // GPS-based speed
} SpeedSources_t;

float FuseSpeedMeasurements(SpeedSources_t *sources) {
    const float WHEEL_WEIGHT = 0.7f;
    const float ACCEL_WEIGHT = 0.2f;
    const float GPS_WEIGHT = 0.1f;

    // Primary: Average of wheel speeds
    float wheel_speed_avg = (sources->wheel_speed_fl + sources->wheel_speed_fr) / 2.0f;

    // Plausibility check: compare wheel speed to accelerometer
    float speed_delta = fabsf(wheel_speed_avg - sources->accelerometer_speed);

    if (speed_delta < 5.0f) {  // Within 5 km/h
        // All sources agree - weighted fusion
        float fused_speed = (wheel_speed_avg * WHEEL_WEIGHT) +
                            (sources->accelerometer_speed * ACCEL_WEIGHT) +
                            (sources->gps_speed * GPS_WEIGHT);
        return fused_speed;
    } else {
        // Potential wheel slip - rely more on accelerometer
        return sources->accelerometer_speed;
    }
}
```

### 3. Dual-Core Lockstep

**Hardware-Level Redundancy:**

```
┌──────────────┐
│   Core 0     │──┐
│ (Leading)    │  │   ┌───────────────┐
└──────────────┘  ├──>│   Comparator  │──> Fault Signal
                  │   └───────────────┘
┌──────────────┐  │
│   Core 1     │──┘
│ (Trailing)   │
└──────────────┘
```

**Characteristics:**
- Two CPU cores execute identical instructions
- Outputs compared cycle-by-cycle
- Any mismatch triggers fault reaction
- ASIL-D without software redundancy

**Lockstep Monitor (Conceptual):**
```c
// This is typically implemented in hardware, but shown for understanding
typedef struct {
    uint32_t core0_output;
    uint32_t core1_output;
    uint32_t mismatch_counter;
    bool lockstep_fault;
} LockstepMonitor_t;

void CheckLockstep(LockstepMonitor_t *monitor) {
    const uint32_t MISMATCH_THRESHOLD = 1;  // Zero tolerance for lockstep

    if (monitor->core0_output != monitor->core1_output) {
        monitor->mismatch_counter++;

        if (monitor->mismatch_counter >= MISMATCH_THRESHOLD) {
            monitor->lockstep_fault = true;
            // Trigger immediate safe state
            EnterSafeState();
            // Generate DTC
            SetDTC(DTC_LOCKSTEP_FAULT);
            // Activate warning lamp
            ActivateWarningLamp(WARNING_LAMP_ENGINE);
        }
    } else {
        // Reset counter if outputs match
        monitor->mismatch_counter = 0;
    }
}
```

### 4. 2oo3 Voting (Two-out-of-Three)

**Triple Modular Redundancy:**

```
┌──────────┐
│ Channel A│───┐
└──────────┘   │
               │    ┌────────────┐      ┌──────────┐
┌──────────┐   ├───>│ 2oo3 Voter │─────>│ Actuator │
│ Channel B│───┤    └────────────┘      └──────────┘
└──────────┘   │
               │
┌──────────┐   │
│ Channel C│───┘
└──────────┘
```

**Voter Logic:**
```c
// 2oo3 voting for critical safety function
typedef struct {
    float channel_a;
    float channel_b;
    float channel_c;
    bool channel_a_fault;
    bool channel_b_fault;
    bool channel_c_fault;
} TripleChannels_t;

bool Vote2oo3(TripleChannels_t *channels, float *output) {
    const float VOTE_TOLERANCE = 0.02f;  // 2% agreement

    int valid_count = 0;
    if (!channels->channel_a_fault) valid_count++;
    if (!channels->channel_b_fault) valid_count++;
    if (!channels->channel_c_fault) valid_count++;

    // Need at least 2 valid channels
    if (valid_count < 2) {
        return false;
    }

    // Check agreement between pairs
    bool ab_agree = fabsf(channels->channel_a - channels->channel_b) /
                    channels->channel_a < VOTE_TOLERANCE;
    bool ac_agree = fabsf(channels->channel_a - channels->channel_c) /
                    channels->channel_a < VOTE_TOLERANCE;
    bool bc_agree = fabsf(channels->channel_b - channels->channel_c) /
                    channels->channel_b < VOTE_TOLERANCE;

    // A and B agree
    if (ab_agree && !channels->channel_a_fault && !channels->channel_b_fault) {
        *output = (channels->channel_a + channels->channel_b) / 2.0f;
        if (!ac_agree && !channels->channel_c_fault) {
            // C is outlier - mark as faulty
            channels->channel_c_fault = true;
        }
        return true;
    }

    // A and C agree
    if (ac_agree && !channels->channel_a_fault && !channels->channel_c_fault) {
        *output = (channels->channel_a + channels->channel_c) / 2.0f;
        if (!ab_agree && !channels->channel_b_fault) {
            channels->channel_b_fault = true;
        }
        return true;
    }

    // B and C agree
    if (bc_agree && !channels->channel_b_fault && !channels->channel_c_fault) {
        *output = (channels->channel_b + channels->channel_c) / 2.0f;
        if (!ab_agree && !channels->channel_a_fault) {
            channels->channel_a_fault = true;
        }
        return true;
    }

    // No agreement among any pair
    return false;
}
```

## Watchdog Mechanisms

### 1. Window Watchdog

**Timing Constraints:**
```c
// Window watchdog - must refresh within time window
typedef struct {
    uint32_t window_min_ms;  // Minimum time before refresh allowed
    uint32_t window_max_ms;  // Maximum time before timeout
    uint32_t last_refresh_time;
    bool watchdog_fault;
} WindowWatchdog_t;

void InitWindowWatchdog(WindowWatchdog_t *wdt, uint32_t min_ms, uint32_t max_ms) {
    wdt->window_min_ms = min_ms;
    wdt->window_max_ms = max_ms;
    wdt->last_refresh_time = GetSystemTimeMs();
    wdt->watchdog_fault = false;
}

void RefreshWindowWatchdog(WindowWatchdog_t *wdt) {
    uint32_t current_time = GetSystemTimeMs();
    uint32_t elapsed = current_time - wdt->last_refresh_time;

    // Check if refresh is too early
    if (elapsed < wdt->window_min_ms) {
        wdt->watchdog_fault = true;
        SetDTC(DTC_WATCHDOG_EARLY_REFRESH);
        EnterSafeState();
        return;
    }

    // Check if refresh is too late
    if (elapsed > wdt->window_max_ms) {
        wdt->watchdog_fault = true;
        SetDTC(DTC_WATCHDOG_TIMEOUT);
        EnterSafeState();
        return;
    }

    // Valid refresh - update timestamp
    wdt->last_refresh_time = current_time;
    wdt->watchdog_fault = false;

    // Refresh hardware watchdog
    HW_WDT_Refresh();
}

// Monitor task - checks watchdog status
void WatchdogMonitorTask(void) {
    WindowWatchdog_t *wdt = GetSystemWatchdog();

    uint32_t current_time = GetSystemTimeMs();
    uint32_t elapsed = current_time - wdt->last_refresh_time;

    if (elapsed > wdt->window_max_ms) {
        // Watchdog expired - enter safe state
        wdt->watchdog_fault = true;
        EnterSafeState();
    }
}
```

### 2. Logical Program Flow Monitoring

**Checkpoints and Sequence Validation:**

```c
// Program flow monitor - detects unexpected execution paths
typedef enum {
    CHECKPOINT_INIT = 0x01,
    CHECKPOINT_SENSOR_READ = 0x02,
    CHECKPOINT_CALCULATION = 0x04,
    CHECKPOINT_OUTPUT = 0x08,
    CHECKPOINT_END = 0x10
} Checkpoint_t;

typedef struct {
    uint32_t expected_sequence;
    uint32_t actual_sequence;
    uint32_t sequence_errors;
} ProgramFlowMonitor_t;

static ProgramFlowMonitor_t flow_monitor;

void InitProgramFlowMonitor(void) {
    flow_monitor.expected_sequence = CHECKPOINT_INIT |
                                     CHECKPOINT_SENSOR_READ |
                                     CHECKPOINT_CALCULATION |
                                     CHECKPOINT_OUTPUT |
                                     CHECKPOINT_END;
    flow_monitor.actual_sequence = 0;
    flow_monitor.sequence_errors = 0;
}

void RecordCheckpoint(Checkpoint_t checkpoint) {
    flow_monitor.actual_sequence |= checkpoint;
}

void ValidateProgramFlow(void) {
    if (flow_monitor.actual_sequence != flow_monitor.expected_sequence) {
        flow_monitor.sequence_errors++;

        if (flow_monitor.sequence_errors > 3) {
            SetDTC(DTC_PROGRAM_FLOW_ERROR);
            EnterSafeState();
        }
    } else {
        // Reset error counter on successful execution
        flow_monitor.sequence_errors = 0;
    }

    // Reset for next cycle
    flow_monitor.actual_sequence = 0;
}

// Critical function with flow monitoring
void SafetyFunction_Example(void) {
    RecordCheckpoint(CHECKPOINT_INIT);

    // Initialize
    InitializeInputs();

    RecordCheckpoint(CHECKPOINT_SENSOR_READ);

    // Read sensors
    float sensor_value = ReadSensor();

    RecordCheckpoint(CHECKPOINT_CALCULATION);

    // Perform calculation
    float result = ProcessSensorData(sensor_value);

    RecordCheckpoint(CHECKPOINT_OUTPUT);

    // Output result
    WriteActuator(result);

    RecordCheckpoint(CHECKPOINT_END);

    // Validate execution path
    ValidateProgramFlow();
}
```

## CRC and Checksum Mechanisms

### 1. CRC-16 for Message Integrity

```c
// CRC-16-CCITT (polynomial 0x1021)
uint16_t CalculateCRC16(const uint8_t *data, uint16_t length) {
    uint16_t crc = 0xFFFF;  // Initial value
    const uint16_t polynomial = 0x1021;

    for (uint16_t i = 0; i < length; i++) {
        crc ^= (uint16_t)(data[i] << 8);

        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ polynomial;
            } else {
                crc <<= 1;
            }
        }
    }

    return crc;
}

// CAN message with E2E protection
typedef struct {
    uint32_t message_id;
    uint8_t data[8];
    uint8_t data_length;
    uint16_t crc;
    uint8_t alive_counter;
} SafetyMessage_t;

bool ValidateSafetyMessage(SafetyMessage_t *msg) {
    // Calculate expected CRC (exclude CRC field itself)
    uint16_t calculated_crc = CalculateCRC16(msg->data, msg->data_length);

    // Verify CRC
    if (calculated_crc != msg->crc) {
        SetDTC(DTC_CRC_MISMATCH);
        return false;
    }

    // Verify alive counter (detects message loss/repetition)
    static uint8_t last_counter[256] = {0};  // Per message ID
    uint8_t expected_counter = (last_counter[msg->message_id] + 1) & 0x0F;

    if (msg->alive_counter != expected_counter) {
        SetDTC(DTC_ALIVE_COUNTER_ERROR);
        return false;
    }

    last_counter[msg->message_id] = msg->alive_counter;
    return true;
}
```

### 2. AUTOSAR E2E Protection

```c
// AUTOSAR E2E Profile 1 (for 8-byte CAN messages)
typedef struct {
    uint8_t Counter;    // 4-bit alive counter
    uint8_t DataID;     // Data identifier
    uint16_t CRC;       // 16-bit CRC
} E2E_P01_Header_t;

typedef enum {
    E2E_P01STATUS_OK,
    E2E_P01STATUS_NONEWDATA,
    E2E_P01STATUS_WRONGCRC,
    E2E_P01STATUS_REPEATED,
    E2E_P01STATUS_WRONGSEQUENCE
} E2E_P01Status_t;

E2E_P01Status_t E2E_P01Check(
    const uint8_t *data,
    uint8_t length,
    uint8_t *last_counter
) {
    E2E_P01_Header_t *header = (E2E_P01_Header_t *)data;

    // 1. Verify CRC
    uint16_t calculated_crc = CalculateCRC16(data + 2, length - 2);
    if (calculated_crc != header->CRC) {
        return E2E_P01STATUS_WRONGCRC;
    }

    // 2. Check counter sequence
    uint8_t expected_counter = (*last_counter + 1) & 0x0F;
    if (header->Counter == *last_counter) {
        return E2E_P01STATUS_REPEATED;
    } else if (header->Counter != expected_counter) {
        return E2E_P01STATUS_WRONGSEQUENCE;
    }

    // 3. Update counter
    *last_counter = header->Counter;

    return E2E_P01STATUS_OK;
}
```

## Memory Protection

### 1. RAM Test Patterns

```c
// March test for RAM integrity
typedef enum {
    MARCH_TEST_PASS,
    MARCH_TEST_FAIL_WRITE,
    MARCH_TEST_FAIL_READ
} MarchTestResult_t;

MarchTestResult_t MarchTest(volatile uint32_t *ram_start, uint32_t size_words) {
    uint32_t i;

    // Phase 1: Write 0 (ascending)
    for (i = 0; i < size_words; i++) {
        ram_start[i] = 0x00000000;
    }

    // Phase 2: Read 0, Write 1 (ascending)
    for (i = 0; i < size_words; i++) {
        if (ram_start[i] != 0x00000000) {
            return MARCH_TEST_FAIL_READ;
        }
        ram_start[i] = 0xFFFFFFFF;
    }

    // Phase 3: Read 1, Write 0 (descending)
    for (i = size_words; i > 0; i--) {
        if (ram_start[i-1] != 0xFFFFFFFF) {
            return MARCH_TEST_FAIL_READ;
        }
        ram_start[i-1] = 0x00000000;
    }

    // Phase 4: Read 0 (descending)
    for (i = size_words; i > 0; i--) {
        if (ram_start[i-1] != 0x00000000) {
            return MARCH_TEST_FAIL_READ;
        }
    }

    return MARCH_TEST_PASS;
}

// Background RAM test (runs incrementally)
typedef struct {
    uint32_t *ram_start;
    uint32_t ram_size_words;
    uint32_t current_block;
    uint32_t blocks_per_cycle;
} BackgroundRAMTest_t;

void InitBackgroundRAMTest(
    BackgroundRAMTest_t *test,
    uint32_t *ram_start,
    uint32_t size_words,
    uint32_t blocks_per_cycle
) {
    test->ram_start = ram_start;
    test->ram_size_words = size_words;
    test->current_block = 0;
    test->blocks_per_cycle = blocks_per_cycle;
}

void RunBackgroundRAMTestCycle(BackgroundRAMTest_t *test) {
    uint32_t words_per_block = test->ram_size_words / test->blocks_per_cycle;
    uint32_t start_offset = test->current_block * words_per_block;

    MarchTestResult_t result = MarchTest(
        &test->ram_start[start_offset],
        words_per_block
    );

    if (result != MARCH_TEST_PASS) {
        SetDTC(DTC_RAM_TEST_FAILURE);
        EnterSafeState();
    }

    // Move to next block
    test->current_block = (test->current_block + 1) % test->blocks_per_cycle;
}
```

### 2. Stack Overflow Detection

```c
// Stack canary pattern
#define STACK_CANARY_PATTERN 0xDEADBEEF

typedef struct {
    uint32_t *stack_start;
    uint32_t *stack_end;
    uint32_t canary_value;
} StackMonitor_t;

void InitStackMonitor(
    StackMonitor_t *monitor,
    uint32_t *stack_start,
    uint32_t *stack_end
) {
    monitor->stack_start = stack_start;
    monitor->stack_end = stack_end;
    monitor->canary_value = STACK_CANARY_PATTERN;

    // Place canary at stack boundary
    *stack_end = STACK_CANARY_PATTERN;
}

bool CheckStackOverflow(StackMonitor_t *monitor) {
    if (*monitor->stack_end != STACK_CANARY_PATTERN) {
        SetDTC(DTC_STACK_OVERFLOW);
        return true;
    }
    return false;
}

// Call in task or periodic interrupt
void StackMonitorTask(void) {
    StackMonitor_t *monitor = GetStackMonitor();

    if (CheckStackOverflow(monitor)) {
        EnterSafeState();
    }
}
```

## Plausibility Checks

### 1. Sensor Range Checks

```c
// Multi-level range checking with hysteresis
typedef struct {
    float min_physical;     // Physical sensor limit
    float max_physical;
    float min_operational;  // Normal operating range
    float max_operational;
    float hysteresis;       // Debounce tolerance
    uint32_t fault_counter;
    uint32_t fault_threshold;
} RangeLimits_t;

typedef enum {
    RANGE_VALID,
    RANGE_WARNING,
    RANGE_FAULT
} RangeStatus_t;

RangeStatus_t CheckSensorRange(float value, RangeLimits_t *limits) {
    // Check physical limits (hard fault)
    if (value < limits->min_physical || value > limits->max_physical) {
        limits->fault_counter++;

        if (limits->fault_counter >= limits->fault_threshold) {
            SetDTC(DTC_SENSOR_RANGE_PHYSICAL);
            return RANGE_FAULT;
        }
    }

    // Check operational limits with hysteresis
    if (value < (limits->min_operational - limits->hysteresis) ||
        value > (limits->max_operational + limits->hysteresis)) {

        limits->fault_counter++;

        if (limits->fault_counter >= limits->fault_threshold) {
            SetDTC(DTC_SENSOR_RANGE_OPERATIONAL);
            return RANGE_WARNING;
        }
    } else {
        // Value in range - reset counter
        if (limits->fault_counter > 0) {
            limits->fault_counter--;
        }
    }

    return RANGE_VALID;
}

// Example: Battery temperature sensor
RangeLimits_t battery_temp_limits = {
    .min_physical = -40.0f,      // Physical sensor limit
    .max_physical = 125.0f,
    .min_operational = -20.0f,   // Normal operating range
    .max_operational = 60.0f,
    .hysteresis = 2.0f,          // 2°C hysteresis
    .fault_counter = 0,
    .fault_threshold = 3         // 3 consecutive faults
};
```

### 2. Signal Gradient Checks

```c
// Detect unrealistic rate of change
typedef struct {
    float last_value;
    uint32_t last_timestamp_ms;
    float max_gradient;  // Maximum rate of change per second
    uint32_t fault_counter;
} GradientMonitor_t;

bool CheckSignalGradient(
    float current_value,
    uint32_t current_timestamp_ms,
    GradientMonitor_t *monitor
) {
    uint32_t delta_time_ms = current_timestamp_ms - monitor->last_timestamp_ms;

    if (delta_time_ms > 0) {
        float delta_value = current_value - monitor->last_value;
        float gradient = (delta_value * 1000.0f) / (float)delta_time_ms;  // per second

        if (fabsf(gradient) > monitor->max_gradient) {
            monitor->fault_counter++;

            if (monitor->fault_counter >= 3) {
                SetDTC(DTC_SIGNAL_GRADIENT_FAULT);
                return false;
            }
        } else {
            monitor->fault_counter = 0;
        }
    }

    // Update history
    monitor->last_value = current_value;
    monitor->last_timestamp_ms = current_timestamp_ms;

    return true;
}

// Example: Vehicle speed gradient check
GradientMonitor_t speed_gradient = {
    .last_value = 0.0f,
    .last_timestamp_ms = 0,
    .max_gradient = 10.0f,  // 10 m/s² max acceleration/deceleration
    .fault_counter = 0
};
```

### 3. Cross-Signal Plausibility

```c
// Verify consistency between related signals
typedef struct {
    float wheel_speed_fl;
    float wheel_speed_fr;
    float wheel_speed_rl;
    float wheel_speed_rr;
    float vehicle_speed;
    float accelerometer_speed;
} SpeedPlausibility_t;

bool CheckSpeedPlausibility(SpeedPlausibility_t *speeds) {
    const float MAX_WHEEL_DELTA = 20.0f;  // km/h max difference between wheels
    const float MAX_ACCEL_DELTA = 10.0f;  // km/h max difference with accelerometer

    // Check consistency between front wheels
    float fl_fr_delta = fabsf(speeds->wheel_speed_fl - speeds->wheel_speed_fr);
    if (fl_fr_delta > MAX_WHEEL_DELTA) {
        SetDTC(DTC_WHEEL_SPEED_IMPLAUSIBLE);
        return false;
    }

    // Check consistency between rear wheels
    float rl_rr_delta = fabsf(speeds->wheel_speed_rl - speeds->wheel_speed_rr);
    if (rl_rr_delta > MAX_WHEEL_DELTA) {
        SetDTC(DTC_WHEEL_SPEED_IMPLAUSIBLE);
        return false;
    }

    // Check vehicle speed vs accelerometer integration
    float accel_delta = fabsf(speeds->vehicle_speed - speeds->accelerometer_speed);
    if (accel_delta > MAX_ACCEL_DELTA) {
        SetDTC(DTC_SPEED_ACCEL_MISMATCH);
        return false;
    }

    return true;
}
```

## Safe State Management

### 1. Safe State Transition

```c
// Safe state state machine
typedef enum {
    STATE_NORMAL_OPERATION,
    STATE_DEGRADED_MODE,
    STATE_SAFE_STATE,
    STATE_EMERGENCY_SHUTDOWN
} SystemState_t;

typedef struct {
    SystemState_t current_state;
    uint32_t fault_mask;
    uint32_t warning_mask;
    uint32_t transition_timestamp;
    bool safe_state_locked;
} SafeStateManager_t;

void TransitionToSafeState(
    SafeStateManager_t *manager,
    uint32_t fault_code
) {
    // Record fault
    manager->fault_mask |= fault_code;
    manager->transition_timestamp = GetSystemTimeMs();

    switch (manager->current_state) {
        case STATE_NORMAL_OPERATION:
            // Evaluate severity
            if (IsCriticalFault(fault_code)) {
                manager->current_state = STATE_SAFE_STATE;
                EnterSafeStateActions();
            } else {
                manager->current_state = STATE_DEGRADED_MODE;
                EnterDegradedModeActions();
            }
            break;

        case STATE_DEGRADED_MODE:
            // Any additional fault → safe state
            manager->current_state = STATE_SAFE_STATE;
            EnterSafeStateActions();
            break;

        case STATE_SAFE_STATE:
            // Check if emergency shutdown required
            if (IsEmergencyCondition(fault_code)) {
                manager->current_state = STATE_EMERGENCY_SHUTDOWN;
                EmergencyShutdownActions();
            }
            break;

        case STATE_EMERGENCY_SHUTDOWN:
            // Terminal state - stay here
            break;
    }

    // Log state transition
    LogStateTransition(manager->current_state, fault_code);

    // Activate warning lamp
    UpdateWarningLamp(manager->current_state);

    // Store DTC
    SetDTC(fault_code);
}

void EnterSafeStateActions(void) {
    // Disable safety-critical outputs
    DisableActuators();

    // Switch to fail-safe values
    SetFailSafeOutputs();

    // Maintain basic functions (e.g., manual braking)
    EnableManualControl();

    // Activate warning indicators
    ActivateWarningLamp(WARNING_LAMP_SYSTEM_FAULT);

    // Log event in NVM
    StoreEventInNonVolatileMemory();

    // Notify other ECUs via CAN
    SendSafeStateNotification();
}
```

### 2. Graceful Degradation

```c
// Multi-level degradation strategy
typedef enum {
    PERFORMANCE_FULL,        // 100% capability
    PERFORMANCE_REDUCED_1,   // 80% capability
    PERFORMANCE_REDUCED_2,   // 50% capability
    PERFORMANCE_MINIMAL,     // 20% capability (safety only)
    PERFORMANCE_DISABLED     // 0% (safe state)
} PerformanceLevel_t;

typedef struct {
    PerformanceLevel_t current_level;
    uint32_t redundancy_available;
    uint32_t faults_detected;
} DegradationManager_t;

void UpdatePerformanceLevel(DegradationManager_t *manager) {
    // Determine performance level based on fault state
    if (manager->faults_detected == 0) {
        manager->current_level = PERFORMANCE_FULL;
    } else if (manager->redundancy_available >= 2) {
        manager->current_level = PERFORMANCE_REDUCED_1;
    } else if (manager->redundancy_available == 1) {
        manager->current_level = PERFORMANCE_REDUCED_2;
    } else if (manager->redundancy_available == 0 && manager->faults_detected == 1) {
        manager->current_level = PERFORMANCE_MINIMAL;
    } else {
        manager->current_level = PERFORMANCE_DISABLED;
    }

    // Apply performance limits
    ApplyPerformanceLimits(manager->current_level);

    // Notify driver
    UpdateDriverDisplay(manager->current_level);
}

void ApplyPerformanceLimits(PerformanceLevel_t level) {
    switch (level) {
        case PERFORMANCE_FULL:
            SetMaxTorque(100.0f);  // 100% torque
            SetMaxSpeed(200.0f);   // 200 km/h
            break;

        case PERFORMANCE_REDUCED_1:
            SetMaxTorque(80.0f);   // 80% torque
            SetMaxSpeed(160.0f);   // 160 km/h
            break;

        case PERFORMANCE_REDUCED_2:
            SetMaxTorque(50.0f);   // 50% torque
            SetMaxSpeed(100.0f);   // 100 km/h
            break;

        case PERFORMANCE_MINIMAL:
            SetMaxTorque(20.0f);   // 20% torque (limp home)
            SetMaxSpeed(50.0f);    // 50 km/h
            break;

        case PERFORMANCE_DISABLED:
            SetMaxTorque(0.0f);
            SetMaxSpeed(0.0f);
            EnterSafeState();
            break;
    }
}
```

## Diagnostic Coverage Metrics

### ASIL-D Target Coverage

```c
// Diagnostic coverage calculation
typedef struct {
    uint32_t total_failure_modes;
    uint32_t detected_single_point_faults;
    uint32_t detected_latent_faults;
    uint32_t detected_residual_faults;
} DiagnosticCoverage_t;

float CalculateSPFM(DiagnosticCoverage_t *coverage) {
    // Single-Point Fault Metric
    // ASIL-D target: > 99%
    return ((float)coverage->detected_single_point_faults /
            (float)coverage->total_failure_modes) * 100.0f;
}

float CalculateLFM(DiagnosticCoverage_t *coverage) {
    // Latent Fault Metric
    // ASIL-D target: > 90%
    return ((float)coverage->detected_latent_faults /
            (float)coverage->total_failure_modes) * 100.0f;
}
```

## Production Checklist

- [ ] Redundancy pattern selected and justified
- [ ] Diagnostic coverage calculated (SPFM > 99%, LFM > 90% for ASIL-D)
- [ ] Watchdog configuration verified
- [ ] CRC/checksum implementation validated
- [ ] Memory protection tested
- [ ] Plausibility checks defined for all sensors
- [ ] Safe state defined and tested
- [ ] FTTI verified through fault injection
- [ ] Warning lamp activation tested
- [ ] DTC storage verified
- [ ] Independent safety assessment completed

## References

- ISO 26262-5:2018 - Hardware Development
- ISO 26262-6:2018 - Software Development
- ISO 26262-9:2018 - ASIL-Oriented Analyses
- IEC 61508 - Functional Safety (general industry)
- AUTOSAR E2E Protocol Specification

## Related Skills

- ISO 26262 Overview
- FMEA/FTA Analysis
- Hardware Safety Requirements
- Software Safety Requirements
- Safety Verification and Validation
