# FMEA/FTA/FMEDA Analysis for ISO 26262

Comprehensive guidance on Failure Mode and Effects Analysis (FMEA), Fault Tree Analysis (FTA), and Failure Modes, Effects, and Diagnostic Analysis (FMEDA) for automotive functional safety, including templates, calculation methods, and production-ready examples.

## Overview

### Analysis Types

**FMEA (Failure Mode and Effects Analysis)**
- Bottom-up analysis: component failure → system effect
- Identifies single-point and latent faults
- Calculates diagnostic coverage
- Required for all ASIL levels

**FTA (Fault Tree Analysis)**
- Top-down analysis: hazardous event → contributing faults
- Quantifies failure probability
- Validates ASIL decomposition
- Mandatory for ASIL C/D

**FMEDA (Failure Modes, Effects, and Diagnostic Analysis)**
- Extension of FMEA with quantitative metrics
- Calculates PMHF (Probabilistic Metric for random Hardware Failures)
- Determines SPFM and LFM
- Required for ASIL B/C/D hardware

## FMEA Methodology

### FMEA Process Flow

```
┌──────────────────────────┐
│ 1. Define System         │
│    Boundaries            │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ 2. Identify Components   │
│    and Functions         │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ 3. Identify Failure      │
│    Modes                 │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ 4. Analyze Effects       │
│    (Local/System/End)    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ 5. Classify Faults       │
│    (SPF/RF/LF)           │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ 6. Define Safety         │
│    Mechanisms            │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ 7. Calculate Diagnostic  │
│    Coverage (DC)         │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ 8. Verify Metrics        │
│    (SPFM/LFM/PMHF)       │
└──────────────────────────┘
```

### Fault Classifications

**Single-Point Fault (SPF)**
- Fault that directly leads to violation of safety goal
- No safety mechanism provides detection
- Must be minimized (SPFM > 99% for ASIL-D)

**Residual Fault (RF)**
- Fault detected by safety mechanism but coverage < 100%
- Contributes to PMHF calculation
- Example: CRC detects 99.998% of errors → 0.002% residual

**Latent Fault (LF)**
- Multi-point fault: not detected immediately
- Only becomes hazardous in combination with another fault
- Must be detected before second fault occurs (LFM > 90% for ASIL-D)

**Safe Fault (SF)**
- Fault detected with high coverage (> 99%)
- Transition to safe state within FTTI
- Does not contribute to PMHF

### FMEA Worksheet Template

```yaml
fmea_id: "FMEA-ESC-HW-001"
system: "Electronic Stability Control"
subsystem: "ESC ECU Hardware"
asil: "ASIL-D"
analyst: "HW Safety Engineer"
date: "2024-03-19"
version: "1.2"

components:
  - component_id: "C001"
    component_name: "Microcontroller (MCU)"
    part_number: "TMS570LC4357"
    function: "Main processing unit for ESC algorithms"

    failure_modes:
      - fm_id: "FM-C001-001"
        failure_mode: "MCU Core 0 stuck-at-high output"
        failure_rate_fit: 50  # Failures in 10^9 hours
        failure_cause: "Transistor latch-up, ESD damage"

        effects:
          local_effect: "Core 0 outputs invalid high logic"
          subsystem_effect: "Incorrect PWM output to brake modulator"
          system_effect: "Unintended brake actuation on one wheel"
          end_effect: "Vehicle instability, potential loss of control"

        severity: "S3"  # Life-threatening
        detection_method: "Dual-core lockstep comparison"
        detection_coverage_pct: 99.9

        fault_classification:
          before_sm: "SPF"  # Single-point fault without safety mechanism
          after_sm: "SF"    # Safe fault with lockstep detection
          diagnostic_coverage: 99.9  # DC = 99.9%

        safety_mechanism:
          sm_id: "SM-ESC-001"
          description: "Dual-core lockstep with cycle-by-cycle comparison"
          detection_time_ms: 0.1  # Detection within 100 μs
          reaction: "Immediate transition to safe state"
          ftti_ms: 150

        residual_failure_rate_fit: 0.05  # 50 * (1 - 0.999) = 0.05
        lambda_spf_fit: 0.05
        lambda_rf_fit: 0.05

      - fm_id: "FM-C001-002"
        failure_mode: "MCU RAM single-bit flip (SEU)"
        failure_rate_fit: 100
        failure_cause: "Cosmic ray, alpha particle"

        effects:
          local_effect: "Corrupted data in RAM"
          subsystem_effect: "Incorrect calculation results"
          system_effect: "Wrong ESC intervention decision"
          end_effect: "Delayed or incorrect stability control"

        severity: "S2"
        detection_method: "ECC (Error Correcting Code) on RAM"
        detection_coverage_pct: 99.99

        fault_classification:
          before_sm: "SPF"
          after_sm: "SF"
          diagnostic_coverage: 99.99

        safety_mechanism:
          sm_id: "SM-ESC-002"
          description: "ECC on safety-critical RAM sections"
          detection_time_ms: 0.01
          reaction: "Correct single-bit errors, flag multi-bit errors"

        residual_failure_rate_fit: 0.01
        lambda_spf_fit: 0.01
        lambda_rf_fit: 0.01

      - fm_id: "FM-C001-003"
        failure_mode: "MCU clock frequency drift"
        failure_rate_fit: 20
        failure_cause: "Oscillator aging, temperature stress"

        effects:
          local_effect: "Incorrect timing of operations"
          subsystem_effect: "ESC algorithm timing violated"
          system_effect: "Delayed ESC response (> 100 ms)"
          end_effect: "Reduced effectiveness of stability control"

        severity: "S2"
        detection_method: "External watchdog with window timing"
        detection_coverage_pct: 95.0

        fault_classification:
          before_sm: "SPF"
          after_sm: "RF"  # Residual fault (95% coverage)
          diagnostic_coverage: 95.0

        safety_mechanism:
          sm_id: "SM-ESC-003"
          description: "Window watchdog monitors timing"
          detection_time_ms: 50
          reaction: "Safe state transition if timing violated"

        residual_failure_rate_fit: 1.0  # 20 * (1 - 0.95) = 1.0
        lambda_spf_fit: 0
        lambda_rf_fit: 1.0

  - component_id: "C002"
    component_name: "Wheel Speed Sensor (Front Left)"
    part_number: "ABS-SENSOR-FL"
    function: "Measure front-left wheel rotational speed"

    failure_modes:
      - fm_id: "FM-C002-001"
        failure_mode: "Sensor output stuck-at-zero"
        failure_rate_fit: 150
        failure_cause: "Wiring short-to-ground, sensor damage"

        effects:
          local_effect: "Constant zero speed output"
          subsystem_effect: "ESC detects wheel as stationary"
          system_effect: "Incorrect vehicle dynamics calculation"
          end_effect: "ESC may fail to intervene when needed"

        severity: "S3"
        detection_method: "Plausibility check vs other wheel speeds"
        detection_coverage_pct: 90.0

        fault_classification:
          before_sm: "LF"  # Latent fault (multi-point failure)
          after_sm: "LF"   # Still latent but detected
          diagnostic_coverage: 90.0

        safety_mechanism:
          sm_id: "SM-ESC-004"
          description: "Cross-check wheel speeds for consistency"
          detection_time_ms: 200
          reaction: "Flag sensor as faulty, use 3-wheel calculation"

        residual_failure_rate_fit: 15.0  # 150 * (1 - 0.90) = 15.0
        lambda_lf_fit: 135.0  # 150 * 0.90 (detected latent)
        lambda_rf_fit: 15.0

metrics:
  total_failure_rate_fit: 320  # Sum of all component failure rates

  spf_metric:
    lambda_spf_total: 0.06  # Sum of all SPF contributions after SM
    lambda_total: 320
    spfm_percent: 99.98  # (1 - 0.06/320) * 100 = 99.98%
    target_asil_d: 99.0
    status: "PASS"

  lf_metric:
    lambda_lf_detected: 135.0
    lambda_lf_total: 150.0
    lfm_percent: 90.0  # (135/150) * 100 = 90.0%
    target_asil_d: 90.0
    status: "PASS"

  pmhf:
    lambda_spf: 0.06
    lambda_rf: 16.06
    pmhf_fit: 16.12  # SPF + RF = 0.06 + 16.06
    target_asil_d_fit: 10.0
    status: "FAIL - Requires design improvement"

conclusions:
  - SPFM meets ASIL-D target (99.98% > 99%)
  - LFM meets ASIL-D target (90.0% >= 90%)
  - PMHF exceeds ASIL-D target (16.12 > 10 FIT)
  - Recommendation: Improve sensor redundancy or diagnostic coverage

actions:
  - action_id: "ACT-001"
    description: "Add redundant wheel speed sensor (1oo2 configuration)"
    responsible: "HW Design Team"
    due_date: "2024-04-30"
    expected_pmhf_reduction: "50%"
```

## FTA Methodology

### Fault Tree Symbols

```
┌─────────────────────────────────────────┐
│ Event Symbols                           │
├─────────────────────────────────────────┤
│  ◯  Basic Event (failure)               │
│  □  Intermediate Event                  │
│  ◇  Undeveloped Event                   │
│  ⬡  External Event                      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Gate Symbols                            │
├─────────────────────────────────────────┤
│  ∧  AND Gate (all inputs required)      │
│  ∨  OR Gate (any input sufficient)      │
│  ⊕  XOR Gate (exclusive-or)             │
│  ≥K  K-out-of-N Gate                    │
└─────────────────────────────────────────┘
```

### FTA Example - Unintended ESC Activation

```
Top Event: Unintended ESC Activation (ASIL-D)
│
├─ OR ────────────────────────────────────┐
│                                          │
▼                                          ▼
[Spurious Brake Command]              [Sensor False Positive]
│                                          │
├─ OR ─────────────────┐                  ├─ OR ──────────────┐
│                      │                  │                   │
▼                      ▼                  ▼                   ▼
[MCU Fault]     [CAN Corruption]    [Yaw Sensor]      [Lateral Accel]
│                      │              Stuck-High       Sensor Stuck
├─ AND ───────┐        │
│             │        │
▼             ▼        ▼
[Core Fault] [Lockstep] [EMI]
◯ 50 FIT      Fails     ◯ 10 FIT
              ◯ 0.5 FIT
```

### Quantitative FTA

**Calculate Top Event Probability:**

```python
# FTA calculations
import math

# Basic event failure rates (FIT = failures in 10^9 hours)
failure_rates = {
    'mcu_core_fault': 50,
    'lockstep_failure': 0.5,
    'can_emi': 10,
    'yaw_sensor_stuck': 100,
    'lateral_accel_stuck': 80
}

# Mission time (hours)
mission_time = 10000  # 10,000 hours (typical vehicle lifetime)

# Convert FIT to probability
def fit_to_probability(fit, hours):
    """Convert FIT to probability over given hours"""
    lambda_per_hour = fit / 1e9
    return 1 - math.exp(-lambda_per_hour * hours)

# Calculate probabilities
prob = {}
for event, fit in failure_rates.items():
    prob[event] = fit_to_probability(fit, mission_time)
    print(f"{event}: {prob[event]:.6e}")

# AND gate: P(A AND B) = P(A) * P(B)
prob_mcu_undetected = prob['mcu_core_fault'] * prob['lockstep_failure']
print(f"\nMCU undetected fault: {prob_mcu_undetected:.6e}")

# OR gate: P(A OR B) = P(A) + P(B) - P(A)*P(B)
def or_gate(p1, p2):
    return p1 + p2 - (p1 * p2)

# Spurious brake command path
prob_spurious_brake = or_gate(prob_mcu_undetected, prob['can_emi'])
print(f"Spurious brake command: {prob_spurious_brake:.6e}")

# Sensor false positive path
prob_sensor_false = or_gate(prob['yaw_sensor_stuck'], prob['lateral_accel_stuck'])
print(f"Sensor false positive: {prob_sensor_false:.6e}")

# Top event
prob_top_event = or_gate(prob_spurious_brake, prob_sensor_false)
print(f"\nTop Event (Unintended ESC): {prob_top_event:.6e}")

# ASIL-D target: < 10 FIT = 1e-4 probability over 10,000 hours
asil_d_target = fit_to_probability(10, mission_time)
print(f"ASIL-D target (< 10 FIT): {asil_d_target:.6e}")

if prob_top_event < asil_d_target:
    print("✓ FTA meets ASIL-D requirement")
else:
    print("✗ FTA fails ASIL-D requirement")
    print(f"Risk reduction factor needed: {prob_top_event / asil_d_target:.1f}x")
```

### Cut Set Analysis

**Minimal Cut Sets:**

Cut sets are combinations of basic events that cause the top event.

```python
# Minimal cut sets for FTA
cut_sets = [
    ['mcu_core_fault', 'lockstep_failure'],  # AND gate
    ['can_emi'],                              # Single point
    ['yaw_sensor_stuck'],                     # Single point
    ['lateral_accel_stuck']                   # Single point
]

# Calculate cut set probabilities
print("Minimal Cut Sets:")
for i, cut_set in enumerate(cut_sets, 1):
    if len(cut_set) == 1:
        # Single-point fault
        prob_cut = prob[cut_set[0]]
        print(f"  Cut Set {i} (SPF): {cut_set} = {prob_cut:.6e}")
    else:
        # Multi-point fault (AND)
        prob_cut = 1.0
        for event in cut_set:
            prob_cut *= prob[event]
        print(f"  Cut Set {i} (AND): {cut_set} = {prob_cut:.6e}")

# Importance analysis - which events contribute most?
print("\nImportance Analysis:")
event_contributions = {}
for event in failure_rates:
    # Calculate top event probability with this event probability = 1
    test_prob = prob.copy()
    test_prob[event] = 1.0

    # Recalculate (simplified)
    if event in ['mcu_core_fault', 'lockstep_failure']:
        test_spurious = or_gate(test_prob['mcu_core_fault'] * test_prob['lockstep_failure'],
                                test_prob['can_emi'])
    else:
        test_spurious = prob_spurious_brake

    if event in ['yaw_sensor_stuck', 'lateral_accel_stuck']:
        test_sensor = or_gate(test_prob['yaw_sensor_stuck'], test_prob['lateral_accel_stuck'])
    else:
        test_sensor = prob_sensor_false

    test_top = or_gate(test_spurious, test_sensor)

    importance = test_top - prob_top_event
    event_contributions[event] = importance

# Sort by importance
sorted_events = sorted(event_contributions.items(), key=lambda x: x[1], reverse=True)
for event, importance in sorted_events:
    print(f"  {event}: {importance:.6e}")

print("\nRecommendation: Focus safety mechanisms on:", sorted_events[0][0])
```

## FMEDA Calculations

### Hardware Metrics Formulas

**1. Single-Point Fault Metric (SPFM)**

```
SPFM = (1 - (ΣλSPF / Σλ)) × 100%

Where:
  λSPF = failure rate of single-point faults (FIT)
  λ = total failure rate (FIT)

ASIL Targets:
  ASIL B: SPFM > 90%
  ASIL C: SPFM > 97%
  ASIL D: SPFM > 99%
```

**2. Latent Fault Metric (LFM)**

```
LFM = (1 - (ΣλLF,undetected / ΣλLF)) × 100%

Where:
  λLF,undetected = latent faults not detected (FIT)
  λLF = total latent fault rate (FIT)

ASIL Targets:
  ASIL B: LFM > 60%
  ASIL C: LFM > 80%
  ASIL D: LFM > 90%
```

**3. Probabilistic Metric for random Hardware Failures (PMHF)**

```
PMHF = ΣλSPF + ΣλRF

Where:
  λSPF = single-point fault rate (FIT)
  λRF = residual fault rate (FIT)

ASIL Targets (per safety goal):
  ASIL B: PMHF < 100 FIT
  ASIL C: PMHF < 100 FIT
  ASIL D: PMHF < 10 FIT

Note: 1 FIT = 1 failure in 10^9 hours
      10 FIT ≈ 1 failure per 11,400 years of operation
```

### Diagnostic Coverage Classes

| DC Class | Coverage Range | Examples |
|----------|---------------|----------|
| DC 0 | None (0%) | No diagnostic |
| DC 1 | Low (60-90%) | Plausibility checks |
| DC 2 | Medium (90-99%) | Watchdog, CRC |
| DC 3 | High (99-100%) | Dual-core lockstep, ECC |

### FMEDA Spreadsheet

```
Component: ESC ECU Microcontroller
Part Number: TMS570LC4357
ASIL: D

┌─────┬──────────────────┬──────┬──────┬──────┬────┬────┬────┬────┐
│ ID  │ Failure Mode     │  λ   │ DC%  │Class │SPF │ RF │ LF │ SF │
├─────┼──────────────────┼──────┼──────┼──────┼────┼────┼────┼────┤
│ FM1 │ Core stuck-at    │  50  │ 99.9 │ DC3  │ 0  │0.05│ 0  │49.95│
│ FM2 │ RAM bit-flip     │ 100  │ 99.99│ DC3  │ 0  │0.01│ 0  │99.99│
│ FM3 │ Clock drift      │  20  │ 95.0 │ DC2  │ 0  │ 1.0│ 0  │ 19.0│
│ FM4 │ Flash ECC fail   │  10  │ 100  │ DC3  │ 0  │ 0  │ 0  │ 10.0│
│ FM5 │ Watchdog fail    │   5  │  0   │ DC0  │ 5  │ 0  │ 0  │  0  │
│ FM6 │ ADC stuck        │  30  │ 85.0 │ DC1  │ 0  │ 4.5│ 0  │25.5 │
│ FM7 │ Power supply OV  │  15  │ 99.0 │ DC3  │ 0  │0.15│ 0  │14.85│
│ FM8 │ Temp sensor drift│  25  │ 90.0 │ DC2  │ 0  │ 2.5│ 0  │22.5 │
├─────┼──────────────────┼──────┼──────┼──────┼────┼────┼────┼────┤
│ SUM │                  │ 255  │      │      │ 5  │8.21│ 0  │241.79│
└─────┴──────────────────┴──────┴──────┴──────┴────┴────┴────┴────┘

Calculations:
  SPFM = (1 - 5/255) × 100% = 98.04%  ← FAIL (target: >99%)
  LFM = N/A (no latent faults)
  PMHF = 5 + 8.21 = 13.21 FIT  ← FAIL (target: <10 FIT)

Required Actions:
  1. Eliminate watchdog SPF (add redundant watchdog)
  2. Improve ADC diagnostic coverage (add cross-checks)
  3. Target: SPFM > 99%, PMHF < 10 FIT
```

## FMEA/FTA Integration

### Bidirectional Validation

**FMEA → FTA Validation:**

1. Each SPF in FMEA should appear as single basic event in FTA
2. Each latent fault should appear in AND gate (multi-point)
3. Safety mechanisms should reduce FTA cut set probabilities

**FTA → FMEA Validation:**

1. Each FTA basic event should have corresponding FMEA failure mode
2. FTA cut sets reveal dependent failures for DFA
3. FTA probability calculation validates PMHF

### Example Cross-Check

```python
# Validate FMEA and FTA consistency
fmea_failure_modes = {
    'mcu_core_fault': {'lambda': 50, 'dc': 99.9, 'spf': 0.05},
    'ram_bit_flip': {'lambda': 100, 'dc': 99.99, 'spf': 0.01},
    'sensor_stuck': {'lambda': 150, 'dc': 90.0, 'spf': 0}
}

fta_basic_events = {
    'mcu_core_fault': 50,
    'ram_bit_flip': 100,
    'sensor_stuck': 150
}

# Check consistency
print("FMEA/FTA Cross-Validation:")
for event in fmea_failure_modes:
    if event in fta_basic_events:
        fmea_lambda = fmea_failure_modes[event]['lambda']
        fta_lambda = fta_basic_events[event]

        if fmea_lambda == fta_lambda:
            print(f"✓ {event}: Consistent ({fmea_lambda} FIT)")
        else:
            print(f"✗ {event}: Mismatch (FMEA: {fmea_lambda}, FTA: {fta_lambda})")
    else:
        print(f"⚠ {event}: Missing in FTA")

for event in fta_basic_events:
    if event not in fmea_failure_modes:
        print(f"⚠ {event}: Missing in FMEA")
```

## Production-Ready Tools

### FMEA Database Schema (SQL)

```sql
CREATE TABLE Components (
    component_id VARCHAR(50) PRIMARY KEY,
    component_name VARCHAR(200),
    part_number VARCHAR(100),
    function TEXT,
    asil VARCHAR(10)
);

CREATE TABLE FailureModes (
    fm_id VARCHAR(50) PRIMARY KEY,
    component_id VARCHAR(50) REFERENCES Components(component_id),
    failure_mode TEXT,
    failure_rate_fit DECIMAL(10,2),
    failure_cause TEXT,
    local_effect TEXT,
    system_effect TEXT,
    end_effect TEXT,
    severity VARCHAR(2)
);

CREATE TABLE SafetyMechanisms (
    sm_id VARCHAR(50) PRIMARY KEY,
    fm_id VARCHAR(50) REFERENCES FailureModes(fm_id),
    description TEXT,
    detection_coverage_pct DECIMAL(5,2),
    detection_time_ms DECIMAL(10,2),
    reaction TEXT,
    ftti_ms DECIMAL(10,2)
);

CREATE TABLE FaultClassification (
    fc_id SERIAL PRIMARY KEY,
    fm_id VARCHAR(50) REFERENCES FailureModes(fm_id),
    before_sm VARCHAR(10),  -- SPF, RF, LF, SF
    after_sm VARCHAR(10),
    diagnostic_coverage DECIMAL(5,2),
    lambda_spf_fit DECIMAL(10,2),
    lambda_rf_fit DECIMAL(10,2),
    lambda_lf_fit DECIMAL(10,2),
    lambda_sf_fit DECIMAL(10,2)
);

-- Query: Calculate SPFM for a system
SELECT
    SUM(fc.lambda_spf_fit) AS total_spf,
    SUM(fm.failure_rate_fit) AS total_lambda,
    (1 - SUM(fc.lambda_spf_fit) / SUM(fm.failure_rate_fit)) * 100 AS spfm_percent
FROM FailureModes fm
JOIN FaultClassification fc ON fm.fm_id = fc.fm_id
WHERE fm.component_id IN (SELECT component_id FROM Components WHERE asil = 'ASIL-D');
```

### Python FMEDA Calculator

```python
#!/usr/bin/env python3
"""
ISO 26262 FMEDA Calculator
Calculates SPFM, LFM, and PMHF metrics
"""

class FMEDACalculator:
    def __init__(self, asil_level):
        self.asil_level = asil_level
        self.failure_modes = []
        self.targets = self._get_targets(asil_level)

    def _get_targets(self, asil):
        targets = {
            'ASIL-A': {'spfm': 0, 'lfm': 0, 'pmhf': 1000},
            'ASIL-B': {'spfm': 90, 'lfm': 60, 'pmhf': 100},
            'ASIL-C': {'spfm': 97, 'lfm': 80, 'pmhf': 100},
            'ASIL-D': {'spfm': 99, 'lfm': 90, 'pmhf': 10}
        }
        return targets.get(asil, targets['ASIL-D'])

    def add_failure_mode(self, name, lambda_fit, dc_percent):
        """
        Add a failure mode with diagnostic coverage
        """
        fm = {
            'name': name,
            'lambda': lambda_fit,
            'dc': dc_percent / 100.0,
            'lambda_detected': lambda_fit * (dc_percent / 100.0),
            'lambda_residual': lambda_fit * (1 - dc_percent / 100.0)
        }
        self.failure_modes.append(fm)

    def calculate_metrics(self):
        """
        Calculate SPFM, LFM, PMHF
        """
        lambda_total = sum(fm['lambda'] for fm in self.failure_modes)
        lambda_spf = sum(fm['lambda_residual'] for fm in self.failure_modes if fm['dc'] == 0)
        lambda_rf = sum(fm['lambda_residual'] for fm in self.failure_modes if 0 < fm['dc'] < 1)
        lambda_lf_detected = sum(fm['lambda_detected'] for fm in self.failure_modes)
        lambda_lf_total = lambda_total  # Simplified

        spfm = (1 - lambda_spf / lambda_total) * 100 if lambda_total > 0 else 0
        lfm = (lambda_lf_detected / lambda_lf_total) * 100 if lambda_lf_total > 0 else 0
        pmhf = lambda_spf + lambda_rf

        return {
            'spfm': spfm,
            'lfm': lfm,
            'pmhf': pmhf,
            'lambda_total': lambda_total,
            'lambda_spf': lambda_spf,
            'lambda_rf': lambda_rf
        }

    def check_compliance(self):
        """
        Check if metrics meet ASIL targets
        """
        metrics = self.calculate_metrics()

        compliance = {
            'spfm': metrics['spfm'] >= self.targets['spfm'],
            'lfm': metrics['lfm'] >= self.targets['lfm'],
            'pmhf': metrics['pmhf'] <= self.targets['pmhf']
        }

        return metrics, compliance

    def generate_report(self):
        """
        Generate compliance report
        """
        metrics, compliance = self.check_compliance()

        print(f"\n{'='*60}")
        print(f"FMEDA Report - {self.asil_level}")
        print(f"{'='*60}\n")

        print(f"{'Metric':<20} {'Value':<15} {'Target':<15} {'Status':<10}")
        print(f"{'-'*60}")

        print(f"{'SPFM':<20} {metrics['spfm']:>8.2f}% "
              f"{self.targets['spfm']:>8}% "
              f"{'PASS' if compliance['spfm'] else 'FAIL':<10}")

        print(f"{'LFM':<20} {metrics['lfm']:>8.2f}% "
              f"{self.targets['lfm']:>8}% "
              f"{'PASS' if compliance['lfm'] else 'FAIL':<10}")

        print(f"{'PMHF':<20} {metrics['pmhf']:>8.2f} FIT "
              f"{'<':>2}{self.targets['pmhf']:>5} FIT "
              f"{'PASS' if compliance['pmhf'] else 'FAIL':<10}")

        print(f"\n{'Detail':<20} {'Value':<15}")
        print(f"{'-'*35}")
        print(f"{'Total λ':<20} {metrics['lambda_total']:>8.2f} FIT")
        print(f"{'λ SPF':<20} {metrics['lambda_spf']:>8.2f} FIT")
        print(f"{'λ RF':<20} {metrics['lambda_rf']:>8.2f} FIT")

        overall = all(compliance.values())
        print(f"\n{'Overall Compliance:':<20} {'PASS' if overall else 'FAIL'}")

        return overall


# Example usage
if __name__ == "__main__":
    calc = FMEDACalculator('ASIL-D')

    # Add failure modes
    calc.add_failure_mode('MCU Core Fault', lambda_fit=50, dc_percent=99.9)
    calc.add_failure_mode('RAM Bit Flip', lambda_fit=100, dc_percent=99.99)
    calc.add_failure_mode('Clock Drift', lambda_fit=20, dc_percent=95.0)
    calc.add_failure_mode('Watchdog Fail', lambda_fit=5, dc_percent=0.0)  # SPF!
    calc.add_failure_mode('ADC Stuck', lambda_fit=30, dc_percent=85.0)

    # Generate report
    calc.generate_report()
```

## Production Checklist

- [ ] FMEA completed for all hardware/software components
- [ ] Failure modes identified at appropriate level (component/function)
- [ ] Effects analyzed at local/system/end level
- [ ] Safety mechanisms defined for all SPF/LF
- [ ] Diagnostic coverage calculated and validated
- [ ] SPFM/LFM/PMHF metrics calculated
- [ ] FTA performed for all ASIL C/D safety goals
- [ ] Cut sets identified and analyzed
- [ ] FMEA and FTA cross-validated
- [ ] Independent review completed
- [ ] Metrics meet ASIL targets

## References

- ISO 26262-5:2018 Annex D - FMEDA Method
- ISO 26262-9:2018 - ASIL-Oriented Analyses
- IEC 61025 - Fault Tree Analysis
- SAE J1739 - Potential Failure Mode and Effects Analysis (FMEA)
- AIAG/VDA FMEA Handbook

## Related Skills

- ISO 26262 Overview
- Safety Mechanisms and Patterns
- Hardware Safety Requirements
- Software Safety Requirements
- Dependent Failure Analysis (DFA)
