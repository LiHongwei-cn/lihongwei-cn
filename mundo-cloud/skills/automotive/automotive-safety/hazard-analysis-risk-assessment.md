# Hazard Analysis and Risk Assessment (HARA)

Comprehensive guidance on performing ISO 26262-compliant Hazard Analysis and Risk Assessment (HARA) for automotive E/E systems, including hazard identification, situation analysis, severity/exposure/controllability classification, and ASIL determination.

## HARA Overview

### Purpose and Scope

**Objectives:**
- Identify potential hazards from malfunctioning behavior
- Assess risk level of each hazardous event
- Determine Automotive Safety Integrity Level (ASIL)
- Define safety goals to mitigate unacceptable risks

**When to Perform HARA:**
- Concept phase (Part 3 of ISO 26262)
- New vehicle/system development
- Major system modifications
- Changes to operational context
- New use cases or operational scenarios

### HARA Process Flow

```
┌────────────────────────────────┐
│   1. Item Definition           │
│   • Boundaries                 │
│   • Functions                  │
│   • Interfaces                 │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│   2. Hazard Identification     │
│   • Malfunctioning behavior    │
│   • Hazard types               │
│   • Brainstorming sessions     │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│   3. Situation Analysis        │
│   • Operating scenarios        │
│   • Driving conditions         │
│   • Vehicle states             │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│   4. Risk Classification       │
│   • Severity (S0-S3)           │
│   • Exposure (E0-E4)           │
│   • Controllability (C0-C3)    │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│   5. ASIL Determination        │
│   • Apply ASIL table           │
│   • Document rationale         │
│   • Define safety goals        │
└────────────────────────────────┘
```

## Severity Classification (S)

### S0: No Injuries

**Definition:** No injuries occur

**Examples:**
- Infotainment system freeze (no impact on driving)
- Interior courtesy light failure
- Seat warmer malfunction
- Radio reception loss
- USB charging port failure

**Typical Systems:**
- Entertainment systems
- Comfort features (non-critical)
- Aesthetic lighting

### S1: Light and Moderate Injuries

**Definition:** Light and moderate injuries including at least one person with moderate injuries

**Injury Examples:**
- Whiplash
- Minor bone fractures
- Mild concussion
- Bruises and contusions
- Soft tissue injuries

**Hazard Examples:**
- Cruise control failure to disengage immediately (delay < 2s)
- Parking sensor false negative at very low speed (< 5 km/h)
- Window regulator unexpected movement during adjustment
- Seat adjuster unintended movement while parked
- HVAC blower maximum speed in hot conditions

**Typical ASIL:** QM or ASIL A (depending on E and C)

### S2: Severe and Life-Threatening Injuries

**Definition:** Severe and life-threatening injuries (survival probable) to at least one person

**Injury Examples:**
- Severe bone fractures
- Internal injuries
- Severe head trauma (but survivable)
- Multiple rib fractures
- Spinal injuries (non-fatal)

**Hazard Examples:**
- Unintended acceleration (< 50 km/h, short duration)
- Steering system increased friction/resistance
- Active suspension failure causing vehicle instability
- Lane keeping assist unintended steering intervention
- Automatic emergency braking false activation at moderate speed
- Airbag non-deployment in moderate-speed collision

**Typical ASIL:** ASIL B or C (depending on E and C)

### S3: Life-Threatening and Fatal Injuries

**Definition:** Life-threatening injuries (survival uncertain) or fatal injuries to at least one person

**Injury Examples:**
- Severe head trauma (likely fatal)
- Multiple severe internal injuries
- Severe burns
- Fatal collision impact
- Ejection from vehicle

**Hazard Examples:**
- Total brake system failure at highway speed
- Unintended full acceleration at highway speed
- Complete steering loss
- Airbag inadvertent deployment while driving
- Electronic stability control (ESC) unintended strong intervention
- Electric vehicle high-voltage shock to occupants
- Autonomous emergency steering wrong direction into oncoming traffic

**Typical ASIL:** ASIL C or D (depending on E and C)

## Exposure Classification (E)

### E0: Incredibly Unlikely

**Definition:** Operational situation occurs less than 0.1% of average operating time

**Examples:**
- Manufacturing test mode only
- Service/diagnostic mode (dealer access)
- Valet parking mode with specific conditions
- Trailer tow mode on vehicles rarely towing
- Extreme weather mode (desert/arctic) for temperate regions

**Annual Occurrence:** Less than 1 hour per year

### E1: Very Low Probability

**Definition:** 0.1% to 1% of average operating time

**Examples:**
- Parallel parking maneuvers
- Reverse gear operation
- Hill start scenarios
- Car wash mode
- Off-road driving (for on-road vehicles)
- Mountain driving with steep grades

**Annual Occurrence:** 10 to 100 hours per year

### E2: Low Probability

**Definition:** 1% to 10% of average operating time

**Examples:**
- City/urban driving
- Stop-and-go traffic
- Residential area driving
- Parking lot navigation
- School zone driving
- Weather: rain/snow conditions

**Annual Occurrence:** 100 to 1000 hours per year

### E3: Medium Probability

**Definition:** 10% to 50% of average operating time

**Examples:**
- Rural road driving
- Suburban driving
- Two-lane highways
- Curved roads
- Night driving
- Mixed traffic conditions

**Annual Occurrence:** 1000 to 5000 hours per year

### E4: High Probability

**Definition:** More than 50% of average operating time

**Examples:**
- Highway/motorway cruising
- Straight road driving
- High-speed driving (> 100 km/h)
- Daytime driving
- Normal weather conditions
- Multiple occupants in vehicle

**Annual Occurrence:** More than 5000 hours per year

**Note:** Average vehicle operation ~10,000 hours over 10-year life

## Controllability Classification (C)

### C0: Controllable in General

**Definition:** More than 99% of all drivers can act to prevent harm in at least 99% of situations

**Characteristics:**
- Very obvious to driver
- Ample time to react
- Simple corrective action
- Multiple sensory cues
- Minimal skill required

**Examples:**
- Single windshield wiper stops (one still works)
- Headlight intensity reduction (not complete failure)
- Fuel gauge inaccuracy (range warning still works)
- Seat heater temperature slightly off target
- Radio volume sudden change

**Driver Action Required:** Simple compensation, obvious detection

### C1: Simply Controllable

**Definition:** At least 99% of all drivers can act to prevent harm in at least 99% of situations

**Characteristics:**
- Easily noticeable
- Adequate time to react (> 5 seconds)
- Straightforward corrective action
- Clear sensory feedback
- Average driver skill sufficient

**Examples:**
- ABS degradation (single wheel)
- Power steering assist reduction (not loss)
- Cruise control requiring multiple attempts to cancel
- Automatic transmission delayed shift (< 2s)
- Tire pressure monitoring false warning
- Parking brake electronic release delay

**Driver Action Required:** Simple reaction, average skill level

### C2: Normally Controllable

**Definition:** At least 90% of all drivers can act to prevent harm in at least 90% of situations

**Characteristics:**
- Noticeable with attention
- Limited time to react (1-5 seconds)
- Requires skilled driver response
- May need trained reaction
- Familiar driving maneuver needed

**Examples:**
- Power steering complete loss (at speed)
- ABS complete failure (manual braking only)
- ESC degraded performance (reduced intervention)
- Traction control sporadic operation
- Engine power reduction (not total loss)
- Automatic transmission stuck in gear
- Regenerative braking unexpected increase

**Driver Action Required:** Skilled driving, immediate attention

### C3: Difficult to Control or Uncontrollable

**Definition:** Less than 90% of all drivers can act to prevent harm in less than 90% of situations

**Characteristics:**
- May not be noticeable immediately
- Very short reaction time (< 1 second)
- Requires expert driver skill
- Counterintuitive response needed
- Physical limitations (strength/reflex)
- Multiple simultaneous failures

**Examples:**
- Total brake failure (all systems)
- Steering complete lockup at highway speed
- Unintended full acceleration at highway speed
- ESC unintended strong braking intervention in curve
- Airbag inadvertent deployment while driving
- All-wheel drive unintended torque split causing spin
- Autonomous steering wrong direction at highway speed
- Suspension sudden complete collapse

**Driver Action Required:** Expert skill, may be uncontrollable

## ASIL Determination Matrix

### Complete ASIL Table

```
┌─────────┬──────────────────────────────────────────────────────────────┐
│         │                    Controllability                           │
│Severity │     C0                  C1                  C2        C3     │
├─────────┼──────────────────────────────────────────────────────────────┤
│   S1    │                                                              │
│  E4     │     QM                  QM                  QM        A      │
│  E3     │     QM                  QM                  QM        A      │
│  E2     │     QM                  QM                  QM        QM     │
│  E1     │     QM                  QM                  QM        QM     │
├─────────┼──────────────────────────────────────────────────────────────┤
│   S2    │                                                              │
│  E4     │     QM                  A                   B         C      │
│  E3     │     QM                  A                   B         C      │
│  E2     │     QM                  QM                  A         B      │
│  E1     │     QM                  QM                  QM        A      │
├─────────┼──────────────────────────────────────────────────────────────┤
│   S3    │                                                              │
│  E4     │     A                   B                   C         D      │
│  E3     │     A                   B                   C         D      │
│  E2     │     QM                  A                   B         C      │
│  E1     │     QM                  QM                  A         B      │
└─────────┴──────────────────────────────────────────────────────────────┘
```

## HARA Worksheet Template

### Electronic Stability Control (ESC) Example

```yaml
hara_id: "HARA-ESC-001"
item: "Electronic Stability Control System"
date: "2024-03-19"
version: "1.0"
analyst: "Functional Safety Team"

item_definition:
  description: "Electronic Stability Control (ESC) system that stabilizes the vehicle by applying individual wheel braking and reducing engine torque during oversteer/understeer conditions"
  boundaries:
    - ESC_ECU
    - Wheel_speed_sensors (4x)
    - Yaw_rate_sensor
    - Lateral_acceleration_sensor
    - Steering_angle_sensor
    - Hydraulic_modulator_unit
  operating_modes:
    - ESC_active_mode
    - ESC_off_mode (driver disabled)
    - ABS_only_mode (ESC degraded)
  assumptions:
    - Driver_input_available
    - Vehicle_in_motion
    - Tire_grip_conditions_normal

hazards:
  - hazard_id: "H-ESC-001"
    malfunctioning_behavior: "Unintended ESC activation"
    description: "ESC applies asymmetric braking when not needed"

    hazardous_events:
      - event_id: "HE-ESC-001-A"
        situation: "Highway driving in straight line at high speed"
        operational_situation:
          - Vehicle_speed: "> 100 km/h"
          - Road_condition: "Dry, straight highway"
          - Traffic: "Dense traffic, nearby vehicles"
          - Driver_activity: "Cruising, minimal steering input"

        severity: "S3"
        severity_rationale: |
          Unintended braking at one wheel at highway speed causes sudden
          vehicle rotation. Driver and passengers face life-threatening
          injuries from:
          - Loss of control leading to collision with barriers
          - Vehicle rollover potential
          - Rear-end collision from following vehicles

        exposure: "E4"
        exposure_rationale: |
          Highway driving accounts for > 50% of vehicle operating time for
          typical usage. Straight-line cruising is the primary highway mode.
          Estimated exposure: 60% of total driving time.

        controllability: "C3"
        controllability_rationale: |
          At high speed (> 100 km/h), sudden asymmetric braking creates:
          - Immediate yaw rotation (< 500ms to loss of control)
          - Counterintuitive response needed (accelerate to regain control)
          - Physical limitation (steering correction requires high torque)
          - < 90% of drivers can successfully recover
          - Professional driver training required for recovery

        asil: "ASIL-D"

        safety_goal:
          sg_id: "SG-ESC-001"
          description: "Prevent unintended ESC activation"
          safe_state: "ESC disabled, manual control"
          ftti: "150 ms"
          verification:
            - Fault_injection_testing
            - Vehicle_dynamics_simulation
            - Proving_ground_testing

      - event_id: "HE-ESC-001-B"
        situation: "Low-speed parking maneuver"
        operational_situation:
          - Vehicle_speed: "< 10 km/h"
          - Location: "Parking lot"
          - Maneuver: "Tight turn, sharp steering"

        severity: "S1"
        severity_rationale: |
          At low speed, unintended braking causes minor vehicle movement.
          Potential for light injuries from sudden stop (whiplash).
          Low collision energy.

        exposure: "E1"
        exposure_rationale: |
          Parking maneuvers occur < 1% of operating time.
          Estimated: 50 hours per year.

        controllability: "C1"
        controllability_rationale: |
          Low speed provides ample reaction time.
          Simple corrective action: release accelerator, re-apply carefully.
          99% of drivers can handle this situation.

        asil: "QM"

        safety_goal:
          sg_id: "None (QM)"
          description: "Managed through quality management"

  - hazard_id: "H-ESC-002"
    malfunctioning_behavior: "ESC failure to activate"
    description: "ESC does not intervene when vehicle is losing stability"

    hazardous_events:
      - event_id: "HE-ESC-002-A"
        situation: "Cornering on wet highway exit ramp"
        operational_situation:
          - Vehicle_speed: "70 km/h"
          - Road_condition: "Wet, curved ramp (radius 50m)"
          - Weather: "Rain, reduced tire grip"
          - Lateral_acceleration: "> 0.7g"

        severity: "S3"
        severity_rationale: |
          Without ESC intervention, vehicle enters uncontrolled oversteer:
          - Spin into barrier or oncoming traffic
          - Rollover potential for SUVs
          - Life-threatening collision likely

        exposure: "E3"
        exposure_rationale: |
          Highway exit ramps used in 10-50% of trips.
          Wet conditions occur 15-20% of driving time.
          Combined exposure: ~20% of operating time.

        controllability: "C2"
        controllability_rationale: |
          Skilled driver can recover from initial oversteer:
          - Counter-steer + throttle modulation
          - Requires advanced car control knowledge
          - 90% of drivers can recover if trained
          - However, typical driver (no training) success rate < 70%
          - Conservative assessment: C2

        asil: "ASIL-C"

        safety_goal:
          sg_id: "SG-ESC-002"
          description: "ESC shall activate when vehicle stability is compromised"
          safe_state: "N/A (function must remain available)"
          ftti: "50 ms"
          verification:
            - Skidpad_testing
            - Wet_handling_course
            - Professional_driver_evaluation

  - hazard_id: "H-ESC-003"
    malfunctioning_behavior: "Delayed ESC response"
    description: "ESC intervention delayed by > 500ms"

    hazardous_events:
      - event_id: "HE-ESC-003-A"
        situation: "Emergency lane change at highway speed"
        operational_situation:
          - Vehicle_speed: "120 km/h"
          - Maneuver: "Double lane change (obstacle avoidance)"
          - Road_condition: "Dry highway"

        severity: "S2"
        severity_rationale: |
          Delayed ESC allows vehicle to exceed stability limits before
          intervention. Results in:
          - Severe over-rotation
          - Adjacent lane encroachment
          - Severe injuries probable, but typically survivable

        exposure: "E2"
        exposure_rationale: |
          Emergency maneuvers occur infrequently: 1-10% of operating time.
          Estimate: 200 hours per year across all driving.

        controllability: "C2"
        controllability_rationale: |
          Delayed ESC reduces effectiveness but some correction provided.
          Skilled driver can compensate with reduced ESC authority.
          ~85% success rate with trained drivers.

        asil: "ASIL-B"

        safety_goal:
          sg_id: "SG-ESC-003"
          description: "ESC response time shall be < 100ms from instability detection"
          safe_state: "Graceful degradation to ABS-only"
          ftti: "100 ms"
          verification:
            - Real-time_latency_measurement
            - HIL_testing_with_vehicle_dynamics_model

summary:
  total_hazards: 3
  total_hazardous_events: 5
  asil_distribution:
    asil_d: 1
    asil_c: 1
    asil_b: 1
    asil_a: 0
    qm: 2
  highest_asil: "ASIL-D"
  safety_goals_required: 3
```

## Advanced HARA Techniques

### Situation Analysis Matrix

**Multi-Dimensional Situation Space:**

```
Dimension 1: Vehicle Speed
├── 0-10 km/h (parking)
├── 10-50 km/h (urban)
├── 50-100 km/h (rural)
└── > 100 km/h (highway)

Dimension 2: Road Conditions
├── Dry
├── Wet
├── Snow/Ice
└── Off-road

Dimension 3: Traffic Density
├── No traffic
├── Light traffic
├── Dense traffic
└── Traffic jam

Dimension 4: Driver State
├── Attentive
├── Distracted
├── Drowsy
└── Impaired (medical emergency)

Dimension 5: Time of Day
├── Day (good visibility)
├── Dusk/dawn (reduced visibility)
└── Night (limited visibility)
```

**Coverage Matrix Example:**
```
Speed vs Road Conditions:

         │ Dry │ Wet │Snow │ Ice │
─────────┼─────┼─────┼─────┼─────┤
0-10km/h │  ✓  │  ✓  │  ✓  │  ✓  │
10-50    │  ✓  │  ✓  │  ✓  │  ✓  │
50-100   │  ✓  │  ✓  │  ✓  │  -  │
>100km/h │  ✓  │  ✓  │  -  │  -  │

✓ = Situation analyzed
- = Situation not applicable (speed limits)
```

### Controllability Assessment Methods

**Method 1: Expert Judgment**
- Panel of experienced drivers
- Simulator testing with representative population
- Statistical analysis of crash avoidance rates

**Method 2: Accident Statistics**
- Historical crash data analysis
- Similar malfunction scenarios
- Injury severity correlation

**Method 3: Simulator Studies**
```python
# Controllability test protocol
test_setup = {
    'participants': 100,  # Diverse driver population
    'age_range': (18, 75),
    'experience_range': (1, 50),  # years driving
    'scenarios': 20,  # per hazardous event
    'success_criteria': 'No collision AND vehicle stable'
}

# Classification
if success_rate > 0.99:
    controllability = "C0"
elif success_rate >= 0.99:
    controllability = "C1"
elif success_rate >= 0.90:
    controllability = "C2"
else:
    controllability = "C3"
```

### Exposure Data Collection

**Data Sources:**
1. **Naturalistic Driving Studies**
   - Real-world driving data
   - GPS logging
   - CAN bus data collection
   - 100+ vehicles over 1+ years

2. **Fleet Telemetry**
   - Connected vehicle data
   - Aggregate usage patterns
   - Scenario frequency statistics

3. **Statistical Databases**
   - NHTSA (US)
   - GIDAS (Germany)
   - STATS19 (UK)

**Exposure Calculation Example:**
```python
# Calculate exposure for "highway driving > 100 km/h"
def calculate_exposure(telemetry_data):
    total_hours = sum(trip.duration for trip in telemetry_data)
    highway_hours = sum(
        trip.duration
        for trip in telemetry_data
        if trip.speed > 100 and trip.road_type == 'highway'
    )

    exposure_percentage = (highway_hours / total_hours) * 100

    # Map to E-class
    if exposure_percentage < 0.1:
        return "E0"
    elif exposure_percentage < 1:
        return "E1"
    elif exposure_percentage < 10:
        return "E2"
    elif exposure_percentage < 50:
        return "E3"
    else:
        return "E4"

# Example data
telemetry = [
    {'duration': 120, 'speed': 110, 'road_type': 'highway'},  # 2 hours
    {'duration': 30, 'speed': 40, 'road_type': 'urban'},      # 0.5 hours
    {'duration': 50, 'speed': 80, 'road_type': 'rural'},      # 0.83 hours
    # ... 1000s more trips
]

exposure_class = calculate_exposure(telemetry)
```

## HARA Documentation

### Safety Case Integration

```markdown
# Safety Case Section: HARA Evidence

## 1. Completeness Argument

**Claim:** All relevant hazards have been identified for the ESC system.

**Evidence:**
- E1: HARA workshop with cross-functional team (attendees: safety engineer,
      system engineer, test engineer, domain expert)
- E2: Review of similar system hazards from database (23 ESC systems analyzed)
- E3: Historical accident data review (GIDAS database, 1000+ ESC-related incidents)
- E4: FMEA results cross-checked with HARA hazard list
- E5: Independent safety assessment review confirmation

**Sub-Claim 1.1:** Malfunction types cover all failure modes
**Sub-Claim 1.2:** Operating situations cover representative vehicle usage

## 2. Classification Accuracy Argument

**Claim:** Severity, Exposure, and Controllability classifications are justified.

**Evidence:**
- E6: Severity based on MAIS (Maximum Abbreviated Injury Scale) correlation
- E7: Exposure derived from 500-vehicle naturalistic driving study (12 months)
- E8: Controllability validated through driving simulator study (N=120 drivers)
- E9: Expert panel review of all classifications (unanimous agreement)

## 3. ASIL Determination Argument

**Claim:** ASIL assignments correctly follow ISO 26262-3 table.

**Evidence:**
- E10: ASIL determination matrix applied consistently to all hazardous events
- E11: Independent verification of ASIL assignments (0 discrepancies)
- E12: Traceability from S/E/C to ASIL documented in HARA database
```

### Review Checklist

**HARA Quality Review:**

- [ ] Item definition complete and approved
- [ ] All operating modes considered
- [ ] Hazards derived from malfunctioning behavior (not internal faults)
- [ ] Operational situations representative and complete
- [ ] Severity classification justified with injury mechanism
- [ ] Exposure based on quantitative data (not assumptions)
- [ ] Controllability assessed with driver population consideration
- [ ] ASIL determination traceable to S/E/C
- [ ] Safety goals defined for all ASIL hazards
- [ ] Safe state specified for each safety goal
- [ ] FTTI specified and justified
- [ ] Cross-check with FMEA/FTA performed
- [ ] Independent review completed
- [ ] All findings from reviews addressed
- [ ] HARA approved by functional safety manager

## Production-Ready Templates

### HARA Database Schema (SQL)

```sql
-- Items table
CREATE TABLE Items (
    item_id VARCHAR(50) PRIMARY KEY,
    item_name VARCHAR(200),
    description TEXT,
    version VARCHAR(20),
    status VARCHAR(20),
    created_date DATE,
    updated_date DATE
);

-- Hazards table
CREATE TABLE Hazards (
    hazard_id VARCHAR(50) PRIMARY KEY,
    item_id VARCHAR(50) REFERENCES Items(item_id),
    malfunctioning_behavior TEXT,
    description TEXT,
    identified_by VARCHAR(100),
    identified_date DATE
);

-- Hazardous Events table
CREATE TABLE HazardousEvents (
    event_id VARCHAR(50) PRIMARY KEY,
    hazard_id VARCHAR(50) REFERENCES Hazards(hazard_id),
    situation_description TEXT,
    operational_situation JSONB,
    severity VARCHAR(2),
    severity_rationale TEXT,
    exposure VARCHAR(2),
    exposure_rationale TEXT,
    controllability VARCHAR(2),
    controllability_rationale TEXT,
    asil VARCHAR(6),
    review_status VARCHAR(20),
    reviewer VARCHAR(100),
    review_date DATE
);

-- Safety Goals table
CREATE TABLE SafetyGoals (
    sg_id VARCHAR(50) PRIMARY KEY,
    event_id VARCHAR(50) REFERENCES HazardousEvents(event_id),
    description TEXT,
    safe_state TEXT,
    ftti_ms INT,
    asil VARCHAR(6),
    status VARCHAR(20),
    approved_by VARCHAR(100),
    approved_date DATE
);

-- Exposure Data table (for evidence)
CREATE TABLE ExposureData (
    data_id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) REFERENCES HazardousEvents(event_id),
    data_source VARCHAR(200),
    measurement_value DECIMAL,
    measurement_unit VARCHAR(50),
    collection_date DATE,
    sample_size INT,
    notes TEXT
);

-- Query: Generate HARA report for ASIL-D events
SELECT
    h.hazard_id,
    h.malfunctioning_behavior,
    he.event_id,
    he.situation_description,
    he.severity,
    he.exposure,
    he.controllability,
    he.asil,
    sg.description AS safety_goal,
    sg.ftti_ms
FROM Hazards h
JOIN HazardousEvents he ON h.hazard_id = he.hazard_id
JOIN SafetyGoals sg ON he.event_id = sg.event_id
WHERE he.asil = 'ASIL-D'
ORDER BY h.hazard_id;
```

### Excel HARA Template

```
Sheet 1: Item Definition
├── A: Item ID
├── B: Item Name
├── C: Description
├── D: Boundaries
├── E: Operating Modes
└── F: Assumptions

Sheet 2: HARA Worksheet
├── A: Hazard ID
├── B: Malfunctioning Behavior
├── C: Hazardous Event ID
├── D: Operational Situation
├── E: Severity (dropdown: S0-S3)
├── F: Severity Rationale
├── G: Exposure (dropdown: E0-E4)
├── H: Exposure Rationale
├── I: Controllability (dropdown: C0-C3)
├── J: Controllability Rationale
├── K: ASIL (formula: =VLOOKUP(...))
└── L: Safety Goal ID

Sheet 3: ASIL Lookup Table
└── Automated ASIL determination matrix

Sheet 4: Safety Goals
├── A: Safety Goal ID
├── B: Safety Goal Description
├── C: Safe State
├── D: FTTI (ms)
└── E: Verification Methods

Sheet 5: Evidence
├── A: Event ID
├── B: Evidence Type (S/E/C)
├── C: Data Source
├── D: Reference Document
└── E: Attachment
```

## References

- ISO 26262-3:2018 - Concept Phase
- SAE J2980 - Considerations for ISO 26262 ASIL Hazard Classification
- ISO/TR 4804 - Safety and cybersecurity for automated driving systems
- GIDAS (German In-Depth Accident Study)
- NHTSA CIREN (Crash Injury Research Engineering Network)

## Related Skills

- ISO 26262 Overview
- Safety Mechanisms and Patterns
- FMEA/FTA Analysis
- Safety Verification and Validation
- Functional Safety Concept Development
