# ISO 26262 Overview - Functional Safety in Automotive

Comprehensive guidance on ISO 26262 standard for functional safety of electrical/electronic (E/E) systems in road vehicles, covering all 12 parts, V-model lifecycle, ASIL determination, and safety concept development.

## ISO 26262 Standard Structure

### 12 Parts Overview

**Part 1: Vocabulary**
- Defines 200+ terms used throughout the standard
- Key terms: ASIL, safety goal, fault, failure, safe state, FTTI, PMHF

**Part 2: Management of Functional Safety**
- Safety lifecycle management
- Safety culture and organizational structure
- Competence management and training
- Quality management integration

**Part 3: Concept Phase**
- Item definition
- Hazard Analysis and Risk Assessment (HARA)
- Functional safety concept
- Safety goals and ASIL determination

**Part 4: Product Development at System Level**
- Technical safety concept
- System design and architecture
- Verification and validation planning
- Safety requirements allocation

**Part 5: Product Development at Hardware Level**
- Hardware safety requirements
- Hardware design and implementation
- Hardware architectural metrics
- Random hardware failures (PMHF calculation)

**Part 6: Product Development at Software Level**
- Software safety requirements
- Software architectural design
- Software unit design and implementation
- Software testing (unit, integration, system)

**Part 7: Production, Operation, Service, Decommissioning**
- Production planning and control
- Field monitoring and customer support
- Safety-related maintenance
- Decommissioning procedures

**Part 8: Supporting Processes**
- Configuration management
- Change management
- Verification methods
- Documentation standards
- Confidence in use (reuse of components)

**Part 9: ASIL-Oriented and Safety-Oriented Analyses**
- Dependent failure analysis (DFA)
- FMEA/FMEDA methodologies
- FTA (Fault Tree Analysis)
- Safety analysis methods

**Part 10: Guidelines**
- Informative guidance on applying the standard
- Examples and best practices
- Interpretation clarifications

**Part 11: Semiconductors**
- Safety requirements for semiconductor components
- Random hardware failures in ICs
- Systematic capability
- Safety manual requirements

**Part 12: Motorcycles**
- Adaptation of standard for motorcycles
- Specific hazard scenarios
- Controllability considerations for two-wheeled vehicles

## V-Model Safety Lifecycle

### Left Side (Decomposition)

```
┌─────────────────────────────────────────────┐
│         Concept Phase (Part 3)              │
│  • Item Definition                          │
│  • HARA → Safety Goals → ASIL               │
│  • Functional Safety Concept                │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    System Design (Part 4)                   │
│  • Technical Safety Concept                 │
│  • System Architecture                      │
│  • Safety Requirements Allocation           │
└────────┬──────────────────┬─────────────────┘
         │                  │
         ▼                  ▼
┌──────────────────┐  ┌──────────────────────┐
│  HW Design       │  │  SW Design           │
│  (Part 5)        │  │  (Part 6)            │
│  • HW Safety Req │  │  • SW Safety Req     │
│  • HW Arch       │  │  • SW Arch           │
│  • HW Design     │  │  • SW Unit Design    │
└────────┬─────────┘  └──────────┬───────────┘
         │                       │
         ▼                       ▼
┌──────────────────┐  ┌──────────────────────┐
│  HW Implement    │  │  SW Implement        │
│  • PCB Design    │  │  • Coding            │
│  • Component     │  │  • Unit Testing      │
└────────┬─────────┘  └──────────┬───────────┘
         │                       │
         └───────────┬───────────┘
                     │
```

### Right Side (Integration & Verification)

```
                     │
                     ▼
┌─────────────────────────────────────────────┐
│    HW/SW Integration (Part 6)               │
│  • Integration Testing                      │
│  • Interface Verification                   │
│  • Safety Mechanism Testing                 │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    System Integration (Part 4)              │
│  • System Testing                           │
│  • Safety Validation                        │
│  • FTTI Verification                        │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    Vehicle Integration (Part 4)             │
│  • Vehicle-level Testing                    │
│  • Safety Goal Verification                 │
│  • Release for Production                   │
└─────────────────────────────────────────────┘
```

## ASIL Determination

### Hazard Classification Parameters

**Severity (S) - Impact of hazardous event**

| Class | Description | Example |
|-------|-------------|---------|
| S0 | No injuries | Minor annoyance (wiper malfunction) |
| S1 | Light/moderate injuries | Airbag non-deployment in low-speed collision |
| S2 | Severe/life-threatening injuries | Unintended braking at highway speed |
| S3 | Life-threatening/fatal injuries | Total brake failure at highway speed |

**Exposure (E) - Probability of operational situation**

| Class | Description | Probability | Example |
|-------|-------------|-------------|---------|
| E0 | Incredibly unlikely | < 0.1% of operating time | Test mode only |
| E1 | Very low probability | 0.1% to 1% | Parking maneuvers |
| E2 | Low probability | 1% to 10% | City driving |
| E3 | Medium probability | 10% to 50% | Rural roads |
| E4 | High probability | > 50% | Highway cruising |

**Controllability (C) - Driver's ability to avoid harm**

| Class | Description | Driver Action | Example |
|-------|-------------|---------------|---------|
| C0 | Controllable in general | Simple avoidance | Single wiper inoperative |
| C1 | Simply controllable | 99% can avoid | ABS degradation (one wheel) |
| C2 | Normally controllable | 90% can avoid | Power steering assist loss |
| C3 | Difficult/uncontrollable | < 90% can avoid | Total brake failure |

### ASIL Determination Table

```
Severity │  Exposure    Controllability
    S    │  E4 E3 E2 E1 │  C1    C2    C3
─────────┼──────────────┼────────────────────
   S1    │  A  A  QM QM │  QM    QM    A
   S2    │  B  B  A  A  │  A     B     C
   S3    │  C  C  B  B  │  B     C     D
```

Legend:
- **QM**: Quality Management only (no ASIL required)
- **ASIL A**: Lowest safety integrity
- **ASIL B**: Medium-low safety integrity
- **ASIL C**: Medium-high safety integrity
- **ASIL D**: Highest safety integrity

### ASIL Requirements Summary

| Aspect | ASIL QM | ASIL A | ASIL B | ASIL C | ASIL D |
|--------|---------|--------|--------|--------|--------|
| Software Unit Testing | Recommended | + (some coverage) | ++ (branch coverage) | +++ (MC/DC) | +++ (MC/DC + boundary) |
| Static Code Analysis | Optional | + | ++ | +++ | +++ |
| Code Reviews | Basic | + | ++ | +++ | +++ |
| FMEA | Optional | + | ++ | +++ | +++ |
| FTA | Not required | Optional | + | ++ | +++ |
| Hardware Diagnostic Coverage | None | > 60% | > 80% | > 90% | > 99% |
| PMHF Target | N/A | < 1000 FIT | < 100 FIT | < 100 FIT | < 10 FIT |

## Safety Goal Development

### Item Definition Template

```yaml
item_name: "Electronic Stability Control (ESC)"
item_id: "ESC-001"
boundaries:
  physical:
    - ECU_ESC_main
    - Wheel_speed_sensors x4
    - Steering_angle_sensor
    - Yaw_rate_sensor
    - Lateral_acceleration_sensor
    - Hydraulic_modulator
  functional:
    - Vehicle_dynamics_control
    - Brake_pressure_modulation
    - Engine_torque_reduction
  interfaces:
    - CAN_powertrain (500 kbps)
    - CAN_chassis (500 kbps)
    - LIN_sensors (19.2 kbps)
    - Brake_pressure_lines (hydraulic)
assumptions:
  - Tire_grip_coefficient > 0.3
  - Sensor_supply_voltage: 5V ± 0.25V
  - Operating_temperature: -40°C to +85°C
  - Vehicle_speed: 0 to 200 km/h
dependencies:
  - ABS_system (provides wheel speed data)
  - Engine_control (accepts torque reduction commands)
  - Brake_system (hydraulic pressure supply)
```

### Safety Goal Template

```yaml
safety_goal_id: "SG-ESC-001"
item: "ESC-001"
hazard: "Unintended ESC activation causing loss of vehicle control"
hazardous_event: "ESC applies asymmetric braking while cornering at highway speed"
asil: "ASIL-D"
asil_derivation:
  severity: "S3"  # Life-threatening
  exposure: "E4"  # Highway driving > 50% of time
  controllability: "C3"  # Difficult to control at high speed
safety_state: "ESC_disabled_safe_mode"
ftti: "150 ms"  # Fault Tolerant Time Interval
safe_state_description: |
  ESC system transitions to disabled state where:
  - No brake pressure modulation occurs
  - Driver has full manual braking control
  - Warning lamp illuminated
  - DTC stored for service
  - Base ABS functionality maintained
verification_criteria:
  - No_unintended_ESC_activation_in_1000_test_runs
  - FTTI_verified_through_fault_injection
  - Safe_state_reached_within_150ms
  - Warning_lamp_activation_confirmed
```

## Functional Safety Concept

### Safety Requirements Allocation

**Functional Safety Requirement (FSR) Example:**

```yaml
fsr_id: "FSR-ESC-001.1"
safety_goal: "SG-ESC-001"
description: "Detect yaw rate sensor plausibility failure"
rationale: "Invalid yaw rate data can cause false ESC activation"
allocation: "System-level (ESC ECU)"
asil: "ASIL-D"
verification_method:
  - Software_unit_test
  - Hardware-in-loop (HIL) test
  - Fault_injection_test
safety_mechanism: "SM-ESC-YAW-001 (Yaw rate plausibility check)"
```

**Safety Mechanism Types:**

1. **Detection**: Identify faults
   - Range checks
   - Plausibility checks
   - Watchdogs
   - CRC/checksum

2. **Control**: Transition to safe state
   - Redundant channels
   - Voting mechanisms
   - Graceful degradation
   - Fail-silent/fail-operational

3. **Warning**: Alert driver/system
   - Warning lamps
   - Acoustic signals
   - Haptic feedback
   - DTC logging

## Technical Safety Concept

### Safety Architecture Patterns

**1. Homogeneous Redundancy (1oo2)**
```
Sensor A ──┐
           ├──> Voter ──> Actuator
Sensor B ──┘
```
- Identical sensors
- ASIL-B each → ASIL-D combined
- Common cause failure analysis required

**2. Heterogeneous Redundancy**
```
Radar ────┐
          ├──> Fusion ──> Decision
Camera ───┘
```
- Different physical principles
- Better independence
- ASIL decomposition possible

**3. Monitoring Architecture (1oo1D)**
```
Main Channel ────────> Actuator
                        ^
                        │
                    Monitor
```
- Main channel + diagnostic coverage
- ASIL decomposition: ASIL-D(D) → ASIL-B(D) + ASIL-A(D)

## ASIL Decomposition

### Decomposition Rules

**Valid ASIL-D Decomposition:**
- ASIL-D(D) = ASIL-C(D) + ASIL-A(D)
- ASIL-D(D) = ASIL-B(D) + ASIL-B(D)
- ASIL-D(D) = ASIL-B(D) + ASIL-A(D) [with additional safety mechanisms]

**Requirements:**
1. Elements must be sufficiently independent
2. Both elements monitored for failures
3. Dependent failures analyzed (DFA)
4. Common cause failures addressed
5. No single point of failure

**Example - Brake-by-Wire ASIL-D Decomposition:**

```yaml
safety_requirement: "Brake_command_processing"
original_asil: "ASIL-D(D)"
decomposition:
  element_1:
    function: "Primary_brake_command_path"
    asil: "ASIL-B(D)"
    implementation: "Microcontroller_core_0"
    safety_mechanisms:
      - Program_flow_monitoring
      - RAM_test
      - CRC_on_commands
  element_2:
    function: "Secondary_brake_command_path"
    asil: "ASIL-B(D)"
    implementation: "Microcontroller_core_1"
    safety_mechanisms:
      - Dual_core_lockstep
      - Cross_comparison
      - Watchdog
independence_measures:
  - Separate_memory_partitions
  - Separate_power_supplies
  - Different_code_implementations
  - Independent_watchdogs
dependent_failure_analysis:
  - EMI_susceptibility_analyzed
  - Common_power_rail_protected
  - Temperature_effects_mitigated
```

## Safety Validation

### Validation Methods by ASIL

| Method | ASIL A | ASIL B | ASIL C | ASIL D |
|--------|--------|--------|--------|--------|
| Requirements review | + | ++ | ++ | +++ |
| Design review | + | ++ | +++ | +++ |
| Simulation testing | + | ++ | +++ | +++ |
| Prototype testing | ++ | +++ | +++ | +++ |
| Field testing | ++ | +++ | +++ | +++ |
| Fault injection | Optional | + | ++ | +++ |
| Back-to-back comparison | Optional | + | ++ | +++ |

### Safety Case Structure

```
Safety Case Document
├── 1. Item Definition
│   ├── System boundaries
│   ├── Assumptions
│   └── Dependencies
├── 2. Hazard Analysis (HARA)
│   ├── Hazard identification
│   ├── Risk assessment (S, E, C)
│   └── ASIL determination
├── 3. Safety Goals
│   ├── Safety goal definition
│   ├── Safe state definition
│   └── FTTI specification
├── 4. Functional Safety Concept
│   ├── Functional safety requirements
│   ├── Safety mechanisms
│   └── Requirement allocation
├── 5. Technical Safety Concept
│   ├── Safety architecture
│   ├── Technical safety requirements
│   └── HW/SW allocation
├── 6. Safety Analysis
│   ├── FMEA/FMEDA results
│   ├── FTA results
│   ├── DFA results
│   └── PMHF calculation
├── 7. Verification Evidence
│   ├── Test results
│   ├── Review records
│   └── Analysis reports
├── 8. Validation Evidence
│   ├── Safety goal verification
│   ├── FTTI verification
│   └── Field data
└── 9. Confirmation Measures
    ├── Functional safety audit
    ├── Independent assessment
    └── Confirmation review
```

## Key Metrics and Targets

### Hardware Metrics

**Single-Point Fault Metric (SPFM)**
```
SPFM = (1 - ΣλSPF / ΣλTotal) × 100%

Target:
- ASIL B: > 90%
- ASIL C: > 97%
- ASIL D: > 99%
```

**Latent Fault Metric (LFM)**
```
LFM = (1 - ΣλLF / (ΣλLF + ΣλRF + ΣλDet)) × 100%

Target:
- ASIL B: > 60%
- ASIL C: > 80%
- ASIL D: > 90%
```

**Probabilistic Metric for random Hardware Failures (PMHF)**
```
PMHF = Σ(λi × failure_rate) FIT

Target:
- ASIL B: < 100 FIT
- ASIL C: < 100 FIT
- ASIL D: < 10 FIT

FIT = Failures In Time (1 FIT = 1 failure in 10⁹ hours)
```

### Software Metrics

**MC/DC Coverage (Modified Condition/Decision Coverage)**
- ASIL D requirement: 100% MC/DC coverage
- Critical software units only
- Tool qualification required

**Cyclomatic Complexity**
- ASIL D recommendation: < 10 per function
- Rationale: Testability and maintainability

## ISO 26262:2018 Updates

### Changes from 2011 Edition

1. **Semicond uctors** (New Part 11)
   - Specific requirements for IC suppliers
   - Safety Element out of Context (SEooC)
   - Systematic capability determination

2. **Motorcycles** (New Part 12)
   - Adapted controllability classes
   - Motorcycle-specific hazards
   - Two-wheeler dynamics considerations

3. **SOTIF Integration** (ISO 21448)
   - Performance limitations
   - Reasonably foreseeable misuse
   - Validation of non-fault scenarios

4. **Cybersecurity** (ISO 21434)
   - Security interface with safety
   - Threat analysis
   - Secure development lifecycle

5. **Agile Development**
   - Guidance on iterative methods
   - Sprint-based V-model
   - Continuous integration considerations

## Production Checklist

### Phase Gate Criteria

**Concept Phase Exit:**
- [ ] Item definition approved
- [ ] HARA completed and reviewed
- [ ] Safety goals confirmed with ASIL
- [ ] Functional safety concept defined
- [ ] Safety plan approved

**System Development Exit:**
- [ ] Technical safety concept complete
- [ ] System architecture defined
- [ ] Safety requirements allocated to HW/SW
- [ ] Verification plan approved
- [ ] Preliminary FMEA conducted

**HW/SW Development Exit:**
- [ ] Detailed design complete
- [ ] Implementation verified (unit tests)
- [ ] Integration testing passed
- [ ] Safety mechanisms validated
- [ ] Code/design reviews complete

**Integration Exit:**
- [ ] System integration testing complete
- [ ] Safety validation performed
- [ ] FTTI verified through testing
- [ ] Hardware metrics achieved (SPFM, LFM, PMHF)
- [ ] Functional safety assessment passed

**Production Release:**
- [ ] Safety case complete
- [ ] Independent safety assessment passed
- [ ] Safety manual released
- [ ] Production quality procedures established
- [ ] Field monitoring plan in place

## Tools and Compliance

### Tool Qualification (ISO 26262-8)

**Tool Confidence Levels (TCL)**

| TCL | Tool Impact | Examples |
|-----|-------------|----------|
| TCL1 | No impact on safety | Documentation editors |
| TCL2 | Can introduce errors | Compilers without verification |
| TCL3 | High risk of undetected errors | Code generators, static analyzers |

**Qualification Methods:**
1. Increased confidence from use
2. Validation of tool outputs
3. Development per recognized standard
4. Evaluation of tool development process

### Recommended Tools

**ASIL-D Qualified:**
- MATLAB/Simulink (with IEC Certification Kit)
- SCADE Suite (qualified per ISO 26262)
- TargetLink (qualified code generator)
- Polyspace (static analyzer)
- LDRA (unit test + coverage)
- Vector CANoe/CANalyzer (HIL testing)

## References

- ISO 26262-1:2018 to ISO 26262-12:2018 (full standard)
- ISO/PAS 21448:2019 (SOTIF - Safety of the Intended Functionality)
- ISO/SAE 21434:2021 (Cybersecurity for road vehicles)
- ASPICE 3.1 (Automotive SPICE)
- MISRA C:2012 / MISRA C++:2008 (coding guidelines)
- SEooC (Safety Element out of Context) guidelines

## Related Skills

- Hazard Analysis and Risk Assessment (HARA)
- Safety Mechanisms and Patterns
- FMEA/FTA Analysis
- Software Safety Requirements
- Safety Verification and Validation
