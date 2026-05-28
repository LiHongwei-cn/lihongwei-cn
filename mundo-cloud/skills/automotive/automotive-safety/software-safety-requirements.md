# Software Safety Requirements - ISO 26262 Part 6

Comprehensive guidance on ASIL-D software development per ISO 26262-6, including safety requirements specification, architectural design, unit implementation, MISRA C/C++ compliance, MC/DC testing, and software safety manual creation.

## Software Development V-Model

```
┌────────────────────────────────────────────────────────────┐
│         Software Safety Requirements (Part 6-6)            │
│  • Derived from Technical Safety Concept                   │
│  • ASIL classification                                     │
│  • Verification criteria                                   │
└───────────────┬────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────────┐
│         Software Architectural Design (Part 6-7)           │
│  • Hierarchical structure                                  │
│  • Component interfaces                                    │
│  • Resource constraints                                    │
└───────────────┬────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────────┐
│         Software Unit Design (Part 6-8)                    │
│  • Detailed design per unit                                │
│  • Algorithms and data structures                          │
│  • Static analysis                                         │
└───────────────┬────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────────┐
│         Software Unit Implementation (Part 6-9)            │
│  • Coding per MISRA guidelines                             │
│  • Code reviews                                            │
│  • Static analysis                                         │
└───────────────┬────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────────┐
│         Software Unit Testing (Part 6-10)                  │
│  • MC/DC coverage (ASIL-D)                                 │
│  • Requirements-based tests                                │
│  • Back-to-back testing                                    │
└───────────────┬────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────────┐
│         Software Integration Testing (Part 6-11)           │
│  • Interface testing                                       │
│  • Resource usage verification                             │
│  • Fault injection                                         │
└────────────────────────────────────────────────────────────┘
```

## Software Safety Requirements

### Requirement Structure

**Good Safety Requirement (SMART):**
- **Specific**: Unambiguous, single interpretation
- **Measurable**: Testable/verifiable
- **Achievable**: Technically feasible
- **Relevant**: Traceable to safety goal
- **Time-bound**: Response time specified

**Example Requirements:**

```yaml
swr_id: "SWR-ESC-001"
title: "Wheel Speed Sensor Range Check"
derived_from: "TSR-ESC-001"  # Technical Safety Requirement
asil: "ASIL-D"
safety_goal: "SG-ESC-001 (Prevent unintended ESC activation)"

description: |
  The software shall validate that each wheel speed sensor value is within
  the physically possible range before using it in vehicle dynamics calculations.

precondition: "Wheel speed sensor data received via CAN"

requirements:
  - id: "SWR-ESC-001.1"
    text: "The software SHALL reject wheel speed values < 0 km/h"
    rationale: "Negative speed is physically impossible"
    verification: "Unit test with negative input"

  - id: "SWR-ESC-001.2"
    text: "The software SHALL reject wheel speed values > 350 km/h"
    rationale: "Exceeds maximum vehicle speed by 50% margin"
    verification: "Unit test with excessive input"

  - id: "SWR-ESC-001.3"
    text: "The software SHALL set a fault flag if invalid speed detected"
    rationale: "Enable diagnostic monitoring"
    verification: "Verify flag state after invalid input"

  - id: "SWR-ESC-001.4"
    text: "The software SHALL use last valid speed value if current invalid"
    rationale: "Maintain functionality while rejecting invalid data"
    verification: "Integration test with fault injection"

  - id: "SWR-ESC-001.5"
    text: "The software SHALL transition to safe state if > 3 consecutive invalid readings"
    rationale: "Persistent fault indicates sensor failure"
    verification: "System test with sustained fault"

timing:
  execution_time_max_us: 50
  deadline_ms: 10
  period_ms: 10

safety_mechanism: "SM-ESC-004 (Range Check)"
interfaces:
  input: "CAN message ESC_WheelSpeeds (ID 0x200)"
  output: "Internal variable wheel_speed_fl_valid"

verification_methods:
  - Requirements-based test
  - Boundary value analysis
  - Fault injection test
  - MC/DC coverage

acceptance_criteria:
  - All requirements verified with tests
  - MC/DC coverage >= 100%
  - Static analysis: 0 violations
  - Code review: approved
```

### Requirements Traceability

```
Safety Goal (SG)
    │
    ├─> Functional Safety Requirement (FSR)
    │       │
    │       ├─> Technical Safety Requirement (TSR)
    │       │       │
    │       │       ├─> Software Safety Requirement (SWR)
    │       │       │       │
    │       │       │       ├─> Software Unit (SW-U)
    │       │       │       │       │
    │       │       │       │       └─> Unit Test Case (UTC)
    │       │       │       │
    │       │       │       └─> Integration Test Case (ITC)
    │       │       │
    │       │       └─> System Test Case (STC)
    │       │
    │       └─> Validation Test Case (VTC)
```

## Software Architecture

### ASIL-D Architecture Patterns

**1. Freedom from Interference**

```c
// Memory partitioning for ASIL-D
typedef struct {
    // ASIL-D partition (protected)
    uint8_t safety_data[1024] __attribute__((section(".safety_ram")));

    // QM partition (separate)
    uint8_t qm_data[4096] __attribute__((section(".qm_ram")));
} MemoryPartitions_t;

// MPU configuration (ARM Cortex-M)
void ConfigureMemoryProtection(void) {
    // Region 0: Safety-critical code (read-only, execute)
    MPU->RBAR = SAFETY_CODE_BASE | MPU_REGION_VALID | 0;
    MPU->RASR = MPU_RASR_ENABLE | MPU_RASR_XN_DISABLE |
                MPU_RASR_AP_RO | MPU_SIZE_64KB;

    // Region 1: Safety-critical data (read-write, no execute)
    MPU->RBAR = SAFETY_DATA_BASE | MPU_REGION_VALID | 1;
    MPU->RASR = MPU_RASR_ENABLE | MPU_RASR_XN_ENABLE |
                MPU_RASR_AP_RW | MPU_SIZE_16KB;

    // Region 2: QM code (separate partition)
    MPU->RBAR = QM_CODE_BASE | MPU_REGION_VALID | 2;
    MPU->RASR = MPU_RASR_ENABLE | MPU_RASR_XN_DISABLE |
                MPU_RASR_AP_RO | MPU_SIZE_128KB;

    // Enable MPU
    MPU->CTRL = MPU_CTRL_ENABLE | MPU_CTRL_PRIVDEFENA;
}
```

**2. Timing and Scheduling**

```c
// ASIL-D task configuration (AUTOSAR OS)
TASK(SafetyCriticalTask) {
    const uint32_t WCET_US = 500;  // Worst-Case Execution Time
    const uint32_t DEADLINE_MS = 10;

    uint32_t start_time = GetTimestamp_us();

    // Execute safety-critical function
    ESC_SafetyFunction();

    uint32_t execution_time = GetTimestamp_us() - start_time;

    // Verify timing constraints
    if (execution_time > WCET_US) {
        SetDTC(DTC_TIMING_VIOLATION);
        EnterSafeState();
    }

    TerminateTask();
}

// Task scheduling configuration
const TaskConfigType SafetyCriticalTaskConfig = {
    .priority = 255,  // Highest priority
    .activation = PERIODIC,
    .period_ms = 10,
    .deadline_ms = 10,
    .stack_size = 2048,
    .partition = SAFETY_PARTITION
};
```

**3. Software Component Structure**

```c
// Software component interface (AUTOSAR SWC)
typedef struct {
    // Inputs (ports)
    float wheel_speed_fl;
    float wheel_speed_fr;
    float wheel_speed_rl;
    float wheel_speed_rr;
    float yaw_rate;
    float lateral_accel;

    // Outputs (ports)
    float brake_pressure_fl;
    float brake_pressure_fr;
    float brake_pressure_rl;
    float brake_pressure_rr;
    bool esc_active;

    // Mode management
    ESC_ModeType operating_mode;

    // Fault status
    uint32_t fault_flags;
} ESC_Component_t;

// Runnable function
void ESC_MainFunction(void) {
    ESC_Component_t *component = GetESCComponent();

    // 1. Input validation
    if (!ValidateInputs(component)) {
        component->operating_mode = ESC_MODE_SAFE_STATE;
        SetSafeOutputs(component);
        return;
    }

    // 2. Mode management
    switch (component->operating_mode) {
        case ESC_MODE_NORMAL:
            ESC_NormalOperation(component);
            break;

        case ESC_MODE_DEGRADED:
            ESC_DegradedOperation(component);
            break;

        case ESC_MODE_SAFE_STATE:
            ESC_SafeState(component);
            break;

        default:
            // Invalid mode - enter safe state
            component->operating_mode = ESC_MODE_SAFE_STATE;
            SetDTC(DTC_INVALID_MODE);
            break;
    }

    // 3. Output validation
    ValidateOutputs(component);
}
```

## MISRA C/C++ Compliance

### MISRA C:2012 Critical Rules for ASIL-D

**Mandatory Rules (Must follow):**

```c
// Rule 1.3: No undefined behavior
// BAD: Integer overflow undefined
int32_t bad_add(int32_t a, int32_t b) {
    return a + b;  // ✗ May overflow
}

// GOOD: Check for overflow
int32_t safe_add(int32_t a, int32_t b, bool *overflow) {
    if ((b > 0) && (a > (INT32_MAX - b))) {
        *overflow = true;
        return INT32_MAX;
    }
    if ((b < 0) && (a < (INT32_MIN - b))) {
        *overflow = true;
        return INT32_MIN;
    }
    *overflow = false;
    return a + b;
}

// Rule 2.2: Dead code shall be removed
// BAD: Unreachable code
void bad_function(bool condition) {
    if (condition) {
        return;
    }
    DoSomething();  // ✗ Dead code if condition always true
    return;
}

// GOOD: No dead code
void good_function(bool condition) {
    if (!condition) {
        DoSomething();
    }
}

// Rule 8.13: Pointer should be const if not modified
// BAD: Missing const
void bad_process(uint8_t *data) {  // ✗ data not modified but not const
    uint8_t value = data[0];
    UseValue(value);
}

// GOOD: Const pointer
void good_process(const uint8_t *data) {
    uint8_t value = data[0];
    UseValue(value);
}

// Rule 9.1: Use before initialization
// BAD: Uninitialized variable
void bad_init(void) {
    uint32_t value;
    if (SomeCondition()) {
        value = 42;
    }
    UseValue(value);  // ✗ May be uninitialized
}

// GOOD: Always initialized
void good_init(void) {
    uint32_t value = 0;  // Default initialization
    if (SomeCondition()) {
        value = 42;
    }
    UseValue(value);
}

// Rule 21.3: malloc/free shall not be used
// BAD: Dynamic memory
void bad_alloc(void) {
    uint8_t *buffer = (uint8_t *)malloc(100);  // ✗ Not allowed
    free(buffer);
}

// GOOD: Static allocation
#define BUFFER_SIZE 100
void good_alloc(void) {
    uint8_t buffer[BUFFER_SIZE];  // Static allocation
    ProcessBuffer(buffer, BUFFER_SIZE);
}
```

### MISRA C++ Specific Rules

```cpp
// Rule A5-1-2: Use nullptr instead of NULL
// BAD: NULL macro
void bad_pointer(void) {
    int *ptr = NULL;  // ✗ Old C style
}

// GOOD: nullptr
void good_pointer(void) {
    int *ptr = nullptr;  // ✓ C++11 style
}

// Rule A10-0-2: Virtual destructor for base class
// BAD: Missing virtual destructor
class BadBase {  // ✗ No virtual destructor
public:
    void DoSomething();
};

// GOOD: Virtual destructor
class GoodBase {
public:
    virtual ~GoodBase() = default;  // ✓ Virtual destructor
    virtual void DoSomething();
};

// Rule A15-5-1: Exception specifications
// BAD: Throwing exceptions in safety code
void bad_exception(void) {
    throw std::runtime_error("Error");  // ✗ Exceptions not allowed ASIL-D
}

// GOOD: Error codes
enum class ErrorCode {
    SUCCESS,
    INVALID_INPUT,
    TIMEOUT
};

ErrorCode good_error_handling(void) {
    if (InvalidInput()) {
        return ErrorCode::INVALID_INPUT;
    }
    return ErrorCode::SUCCESS;
}
```

### Static Analysis Configuration

**.misra_config.txt (for PC-Lint/Flexelint):**
```
// MISRA C:2012 rules for ASIL-D
+misra(2012)

// Mandatory rules
-strong(AXJ)  // All rules from Advisory to Required to Mandatory

// Specific rule configuration
-esym(960, 1.3)   // Enable: No undefined behavior
-esym(960, 2.2)   // Enable: No dead code
-esym(960, 8.13)  // Enable: Pointer to const
-esym(960, 9.1)   // Enable: No uninitialized variables
-esym(960, 21.3)  // Enable: No dynamic memory

// Project-specific deviations (requires justification)
-elib(960)        // Suppress for library code
```

## Unit Testing - MC/DC Coverage

### Modified Condition/Decision Coverage (MC/DC)

**Definition:** Every condition in a decision independently affects the outcome.

**Example:**

```c
// Function to test
bool ESC_ShouldActivate(float yaw_rate, float lateral_accel, bool driver_input) {
    // Decision with 3 conditions (A, B, C)
    if ((yaw_rate > THRESHOLD_YAW) &&        // Condition A
        (lateral_accel > THRESHOLD_ACCEL) && // Condition B
        (!driver_input))                     // Condition C
    {
        return true;
    }
    return false;
}

// MC/DC Test Cases
void test_mcdc_coverage(void) {
    // Truth table with MC/DC coverage
    // TC | A | B | C | Result | Covers
    // ---+---+---+---+--------+--------
    //  1 | F | F | F |   F    | -
    //  2 | T | F | F |   F    | A (vs TC4)
    //  3 | F | T | F |   F    | B (vs TC4)
    //  4 | T | T | F |   T    | baseline
    //  5 | T | T | T |   F    | C (vs TC4)

    // Test Case 1: All false
    assert(ESC_ShouldActivate(0.0, 0.0, false) == false);

    // Test Case 2: Only A true (tests A independence)
    assert(ESC_ShouldActivate(10.0, 0.0, false) == false);

    // Test Case 3: Only B true (tests B independence)
    assert(ESC_ShouldActivate(0.0, 10.0, false) == false);

    // Test Case 4: A and B true, C false (baseline true)
    assert(ESC_ShouldActivate(10.0, 10.0, false) == true);

    // Test Case 5: All true but C negated (tests C independence)
    assert(ESC_ShouldActivate(10.0, 10.0, true) == false);

    // MC/DC coverage: 100% ✓
}
```

### Unit Test Framework (Unity)

```c
// test_esc_range_check.c
#include "unity.h"
#include "esc_sensor.h"

void setUp(void) {
    // Called before each test
    ESC_Init();
}

void tearDown(void) {
    // Called after each test
    ESC_Deinit();
}

// Test: Valid speed accepted
void test_valid_speed_accepted(void) {
    float speed = 100.0f;  // Valid: 0-350 km/h
    bool result = ESC_ValidateWheelSpeed(speed);
    TEST_ASSERT_TRUE(result);
}

// Test: Negative speed rejected
void test_negative_speed_rejected(void) {
    float speed = -10.0f;  // Invalid: < 0
    bool result = ESC_ValidateWheelSpeed(speed);
    TEST_ASSERT_FALSE(result);
}

// Test: Excessive speed rejected
void test_excessive_speed_rejected(void) {
    float speed = 400.0f;  // Invalid: > 350
    bool result = ESC_ValidateWheelSpeed(speed);
    TEST_ASSERT_FALSE(result);
}

// Test: Boundary value (low)
void test_boundary_low(void) {
    float speed = 0.0f;  // Boundary: exactly 0
    bool result = ESC_ValidateWheelSpeed(speed);
    TEST_ASSERT_TRUE(result);
}

// Test: Boundary value (high)
void test_boundary_high(void) {
    float speed = 350.0f;  // Boundary: exactly max
    bool result = ESC_ValidateWheelSpeed(speed);
    TEST_ASSERT_TRUE(result);
}

// Test: Fault flag set on invalid input
void test_fault_flag_on_invalid(void) {
    float speed = -10.0f;
    ESC_ValidateWheelSpeed(speed);
    TEST_ASSERT_TRUE(ESC_IsFaultFlagSet(FAULT_WHEEL_SPEED_INVALID));
}

// Test: Safe state after persistent faults
void test_safe_state_persistent_fault(void) {
    // Inject 4 consecutive invalid readings
    for (int i = 0; i < 4; i++) {
        ESC_ValidateWheelSpeed(-10.0f);
    }
    TEST_ASSERT_EQUAL(ESC_MODE_SAFE_STATE, ESC_GetMode());
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_valid_speed_accepted);
    RUN_TEST(test_negative_speed_rejected);
    RUN_TEST(test_excessive_speed_rejected);
    RUN_TEST(test_boundary_low);
    RUN_TEST(test_boundary_high);
    RUN_TEST(test_fault_flag_on_invalid);
    RUN_TEST(test_safe_state_persistent_fault);
    return UNITY_END();
}
```

### Coverage Report

```bash
# Run tests with coverage (gcov/lcov)
gcc -fprofile-arcs -ftest-coverage -o test_esc test_esc.c esc_sensor.c
./test_esc
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html

# Coverage report:
# File: esc_sensor.c
# Lines: 98.5% (65/66)
# Functions: 100% (8/8)
# Branches: 100% (24/24)  ← MC/DC coverage
# MC/DC: 100% ✓ (ASIL-D requirement met)
```

## Software Safety Manual

### Template

```markdown
# Software Safety Manual
# ESC Electronic Control Unit
# Version 1.0
# ASIL-D

## 1. Introduction

### 1.1 Scope
This Software Safety Manual describes the safety-related aspects of the
ESC (Electronic Stability Control) ECU software version 2.5.0, developed
in accordance with ISO 26262-6:2018 for ASIL-D integrity level.

### 1.2 Intended Use
The software is designed for use in passenger vehicles (M1 category) with:
- Maximum gross weight: 3500 kg
- Maximum speed: 200 km/h
- Operating temperature: -40°C to +85°C

## 2. Safety Concept

### 2.1 Safety Goals
- SG-ESC-001: Prevent unintended ESC activation (ASIL-D)
- SG-ESC-002: ESC shall activate when stability compromised (ASIL-C)
- SG-ESC-003: ESC response time < 100ms (ASIL-B)

### 2.2 Software Safety Requirements
See Section 5 for complete list (45 requirements, all verified).

## 3. Assumptions and Dependencies

### 3.1 Hardware Assumptions
- Dual-core lockstep microcontroller (TMS570LC4357)
- ECC-protected RAM (SECDED capable)
- Watchdog timer with window monitoring
- CAN controller with error detection

### 3.2 Integration Assumptions
- CAN bus operates at 500 kbps
- Wheel speed sensors provide updates every 10ms
- Supply voltage: 9V to 16V nominal

### 3.3 Environmental Assumptions
- Road surface friction coefficient: 0.1 to 1.0
- Vehicle speed: 0 to 200 km/h
- Tire pressure: 1.8 to 3.0 bar

## 4. Safety Mechanisms

### 4.1 Implemented Safety Mechanisms
| ID | Description | Coverage |
|----|-------------|----------|
| SM-ESC-001 | Dual-core lockstep | 99.9% |
| SM-ESC-002 | ECC on RAM | 99.99% |
| SM-ESC-003 | Window watchdog | 95.0% |
| SM-ESC-004 | Range checks | 90.0% |
| SM-ESC-005 | CRC on CAN | 99.998% |

### 4.2 Diagnostic Coverage
- SPFM: 99.2% (target: > 99%) ✓
- LFM: 92.5% (target: > 90%) ✓
- PMHF: 8.5 FIT (target: < 10 FIT) ✓

## 5. Known Limitations

### 5.1 Functional Limitations
- ESC disabled when vehicle speed < 10 km/h
- ESC functionality reduced with 1 failed wheel speed sensor
- ESC deactivated in reverse gear

### 5.2 Performance Limitations
- Maximum yaw rate: ±100°/s
- Maximum lateral acceleration: ±1.5g
- Response time: 50-100ms (depends on sensor update rate)

## 6. Safe States

### 6.1 Safe State Definition
- All brake modulation disabled
- Manual brake control available
- Warning lamp activated
- DTC stored in non-volatile memory

### 6.2 Transition Conditions
- Lockstep mismatch detected
- Persistent sensor failure (> 3 consecutive)
- Watchdog timeout
- Critical software error detected

## 7. Integration Guidelines

### 7.1 Configuration Parameters
```c
#define ESC_YAW_THRESHOLD_DEG_S     (15.0f)
#define ESC_LATERAL_ACCEL_THRESHOLD_G (0.4f)
#define ESC_FTTI_MS                 (150)
#define ESC_SENSOR_TIMEOUT_MS       (100)
```

### 7.2 Calibration Requirements
- Parameters must be calibrated for specific vehicle platform
- Validation testing required after calibration changes
- Safety-critical parameters protected by CRC

## 8. Verification Evidence

### 8.1 Testing Summary
- Unit tests: 487 test cases, 100% MC/DC coverage
- Integration tests: 125 test cases, all passed
- System tests: 45 test cases, all passed
- HIL testing: 1000 hours, 0 safety-critical failures

### 8.2 Static Analysis
- MISRA C:2012 compliance: 100% (0 deviations)
- Cyclomatic complexity: Max 8 (target: < 10)
- Code review: All modules approved

## 9. Maintenance and Support

### 9.1 Software Updates
- Updates require full regression testing
- Safety assessment required for any safety-critical change
- Version control: Git with signed commits

### 9.2 Field Monitoring
- DTC monitoring via diagnostic interface
- Software version readable via OBD-II
- Field failure data collection mandatory

## 10. References
- ISO 26262-6:2018 - Software Development
- MISRA C:2012 - Guidelines for C
- ESC_SWR_v2.5.pdf - Software Safety Requirements
- ESC_TestReport_v2.5.pdf - Verification Report
```

## Production Checklist

### ASIL-D Software Development

- [ ] Software safety requirements defined and reviewed
- [ ] Architecture designed with freedom from interference
- [ ] MISRA C/C++ compliance verified (100%)
- [ ] Static analysis performed (0 critical violations)
- [ ] Unit tests achieve MC/DC coverage (100%)
- [ ] Integration tests cover all interfaces
- [ ] Timing analysis performed (WCET verified)
- [ ] Memory usage analyzed (stack/heap within limits)
- [ ] Code reviews completed (all units)
- [ ] Back-to-back testing (model vs code) performed
- [ ] Software safety manual completed
- [ ] Tool qualification performed (compiler, static analyzer)
- [ ] Configuration management in place
- [ ] Independent software assessment passed

## References

- ISO 26262-6:2018 - Product Development at Software Level
- ISO 26262-8:2018 - Supporting Processes
- MISRA C:2012 - Guidelines for the Use of C
- MISRA C++:2008 - Guidelines for C++
- AUTOSAR Coding Guidelines
- DO-178C - Software Considerations in Airborne Systems (reference)

## Related Skills

- ISO 26262 Overview
- Safety Mechanisms and Patterns
- FMEA/FTA Analysis
- Safety Verification and Validation
- MISRA C Coding Guidelines
