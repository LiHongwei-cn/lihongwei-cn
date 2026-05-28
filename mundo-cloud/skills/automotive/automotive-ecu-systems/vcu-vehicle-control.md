# VCU (Vehicle Control Unit) for Electric Vehicles

## Overview
The Vehicle Control Unit (VCU) is the central brain for electric vehicles, managing torque arbitration, drive modes, power distribution, regenerative braking, and traction control. This skill covers production-ready VCU development with AUTOSAR BSW integration.

## Core Responsibilities

### 1. Torque Arbitration
```c
/* vcu_torque_arbiter.c - Multi-source torque request arbitration */
#include "vcu_torque_arbiter.h"
#include "autosar_rte.h"
#include <stdint.h>
#include <stdbool.h>

#define MAX_TORQUE_NM 400
#define MIN_REGEN_TORQUE_NM -200
#define TORQUE_RATE_LIMIT_NM_PER_100MS 50

typedef enum {
    TORQUE_SOURCE_DRIVER = 0,
    TORQUE_SOURCE_CRUISE_CONTROL,
    TORQUE_SOURCE_TRACTION_CONTROL,
    TORQUE_SOURCE_STABILITY_CONTROL,
    TORQUE_SOURCE_POWER_LIMIT,
    TORQUE_SOURCE_THERMAL_LIMIT,
    TORQUE_SOURCE_COUNT
} TorqueSource_t;

typedef struct {
    int16_t requested_torque_nm;
    uint8_t priority;
    bool active;
    uint32_t timestamp_ms;
} TorqueRequest_t;

typedef struct {
    TorqueRequest_t requests[TORQUE_SOURCE_COUNT];
    int16_t arbitrated_torque_nm;
    int16_t previous_torque_nm;
    TorqueSource_t active_source;
} TorqueArbiter_t;

static TorqueArbiter_t g_torque_arbiter = {0};

/* Priority levels (higher number = higher priority) */
static const uint8_t TORQUE_PRIORITIES[TORQUE_SOURCE_COUNT] = {
    [TORQUE_SOURCE_DRIVER] = 1,
    [TORQUE_SOURCE_CRUISE_CONTROL] = 2,
    [TORQUE_SOURCE_TRACTION_CONTROL] = 5,  /* Safety critical */
    [TORQUE_SOURCE_STABILITY_CONTROL] = 6, /* Highest priority */
    [TORQUE_SOURCE_POWER_LIMIT] = 4,
    [TORQUE_SOURCE_THERMAL_LIMIT] = 3
};

void VCU_TorqueArbiter_Init(void) {
    memset(&g_torque_arbiter, 0, sizeof(TorqueArbiter_t));

    /* Initialize priorities */
    for (int i = 0; i < TORQUE_SOURCE_COUNT; i++) {
        g_torque_arbiter.requests[i].priority = TORQUE_PRIORITIES[i];
    }
}

void VCU_TorqueArbiter_SetRequest(TorqueSource_t source, int16_t torque_nm, bool active) {
    if (source >= TORQUE_SOURCE_COUNT) return;

    /* Clamp torque to physical limits */
    if (torque_nm > MAX_TORQUE_NM) torque_nm = MAX_TORQUE_NM;
    if (torque_nm < MIN_REGEN_TORQUE_NM) torque_nm = MIN_REGEN_TORQUE_NM;

    g_torque_arbiter.requests[source].requested_torque_nm = torque_nm;
    g_torque_arbiter.requests[source].active = active;
    g_torque_arbiter.requests[source].timestamp_ms = GetSystemTime_ms();
}

int16_t VCU_TorqueArbiter_Arbitrate(void) {
    int16_t result_torque = 0;
    uint8_t highest_priority = 0;
    TorqueSource_t active_source = TORQUE_SOURCE_DRIVER;

    /* Find highest priority active request */
    for (int i = 0; i < TORQUE_SOURCE_COUNT; i++) {
        if (g_torque_arbiter.requests[i].active &&
            g_torque_arbiter.requests[i].priority > highest_priority) {
            highest_priority = g_torque_arbiter.requests[i].priority;
            result_torque = g_torque_arbiter.requests[i].requested_torque_nm;
            active_source = (TorqueSource_t)i;
        }
    }

    /* Apply rate limiter for smoothness */
    int16_t delta = result_torque - g_torque_arbiter.previous_torque_nm;
    if (delta > TORQUE_RATE_LIMIT_NM_PER_100MS) {
        result_torque = g_torque_arbiter.previous_torque_nm + TORQUE_RATE_LIMIT_NM_PER_100MS;
    } else if (delta < -TORQUE_RATE_LIMIT_NM_PER_100MS) {
        result_torque = g_torque_arbiter.previous_torque_nm - TORQUE_RATE_LIMIT_NM_PER_100MS;
    }

    g_torque_arbiter.arbitrated_torque_nm = result_torque;
    g_torque_arbiter.previous_torque_nm = result_torque;
    g_torque_arbiter.active_source = active_source;

    /* Send to motor controller via CAN */
    Rte_Write_MotorTorqueCmd_torque(result_torque);

    return result_torque;
}
```

### 2. Drive Modes (Eco/Sport/Custom)
```c
/* vcu_drive_modes.c - Drive mode management */
#include "vcu_drive_modes.h"

typedef enum {
    DRIVE_MODE_ECO = 0,
    DRIVE_MODE_NORMAL,
    DRIVE_MODE_SPORT,
    DRIVE_MODE_CUSTOM
} DriveMode_t;

typedef struct {
    uint8_t max_power_percent;       /* 0-100% */
    uint8_t throttle_response;       /* 0-100%, sensitivity */
    uint8_t regen_strength;          /* 0-100%, aggressive regen */
    uint8_t ac_power_limit_percent;  /* HVAC power limit */
} DriveModeProfile_t;

static const DriveModeProfile_t DRIVE_MODE_PROFILES[] = {
    [DRIVE_MODE_ECO] = {
        .max_power_percent = 70,
        .throttle_response = 50,
        .regen_strength = 80,
        .ac_power_limit_percent = 50
    },
    [DRIVE_MODE_NORMAL] = {
        .max_power_percent = 90,
        .throttle_response = 70,
        .regen_strength = 60,
        .ac_power_limit_percent = 80
    },
    [DRIVE_MODE_SPORT] = {
        .max_power_percent = 100,
        .throttle_response = 100,
        .regen_strength = 40,
        .ac_power_limit_percent = 100
    },
    [DRIVE_MODE_CUSTOM] = {
        .max_power_percent = 85,
        .throttle_response = 75,
        .regen_strength = 65,
        .ac_power_limit_percent = 75
    }
};

static DriveMode_t g_active_mode = DRIVE_MODE_NORMAL;
static DriveModeProfile_t g_custom_profile;

void VCU_DriveMode_Set(DriveMode_t mode) {
    if (mode >= DRIVE_MODE_CUSTOM) return;
    g_active_mode = mode;

    /* Apply profile to power management */
    const DriveModeProfile_t* profile = &DRIVE_MODE_PROFILES[mode];

    VCU_PowerManagement_SetMaxPower(profile->max_power_percent);
    VCU_ThrottleMap_SetResponse(profile->throttle_response);
    VCU_RegenBraking_SetStrength(profile->regen_strength);
    VCU_HVAC_SetPowerLimit(profile->ac_power_limit_percent);

    /* Persist to EEPROM */
    NvM_WriteBlock(NVM_BLOCK_DRIVE_MODE, &mode);
}

DriveMode_t VCU_DriveMode_Get(void) {
    return g_active_mode;
}

/* Throttle pedal mapping with drive mode response curve */
int16_t VCU_ThrottleMap_ApplyResponse(uint8_t pedal_position_percent) {
    const DriveModeProfile_t* profile = &DRIVE_MODE_PROFILES[g_active_mode];

    /* Non-linear response curve: torque = (pedal^2) * response_factor */
    float normalized_pedal = pedal_position_percent / 100.0f;
    float response_factor = profile->throttle_response / 100.0f;

    /* Sport mode: more aggressive curve (pedal^1.5) */
    /* Eco mode: gentler curve (pedal^2.5) */
    float exponent = 2.0f;
    if (g_active_mode == DRIVE_MODE_SPORT) {
        exponent = 1.5f;
    } else if (g_active_mode == DRIVE_MODE_ECO) {
        exponent = 2.5f;
    }

    float torque_factor = powf(normalized_pedal, exponent) * response_factor;
    int16_t max_torque = (MAX_TORQUE_NM * profile->max_power_percent) / 100;

    return (int16_t)(torque_factor * max_torque);
}
```

### 3. Regenerative Braking Control
```c
/* vcu_regen_braking.c - Regenerative braking with blending */
#include "vcu_regen_braking.h"

#define MIN_VEHICLE_SPEED_KPH 5      /* Below this, friction only */
#define MAX_REGEN_POWER_KW 80
#define BATTERY_HIGH_SOC_LIMIT 95    /* Reduce regen above 95% SOC */
#define REGEN_BLEND_THRESHOLD_MS 200 /* Blend window for smooth transition */

typedef struct {
    uint8_t regen_strength_percent;
    int16_t regen_torque_nm;
    int16_t friction_brake_request_nm;
    bool regen_available;
    uint32_t last_blend_timestamp_ms;
} RegenBraking_t;

static RegenBraking_t g_regen_state = {0};

bool VCU_Regen_IsAvailable(void) {
    /* Check conditions for regen availability */
    uint8_t battery_soc = BMS_GetSOC_percent();
    uint8_t battery_temp_c = BMS_GetTemperature_C();
    uint16_t vehicle_speed_kph = VCU_GetVehicleSpeed_kph();

    /* No regen if: SOC too high, battery too cold, vehicle too slow */
    if (battery_soc > BATTERY_HIGH_SOC_LIMIT) return false;
    if (battery_temp_c < 0) return false;  /* Below 0°C, limit regen */
    if (vehicle_speed_kph < MIN_VEHICLE_SPEED_KPH) return false;

    /* Check motor controller readiness */
    if (!MCU_IsRegenReady()) return false;

    return true;
}

void VCU_Regen_CalculateBlending(uint8_t brake_pedal_percent,
                                  int16_t* regen_torque_out,
                                  int16_t* friction_brake_out) {
    *regen_torque_out = 0;
    *friction_brake_out = 0;

    if (!VCU_Regen_IsAvailable()) {
        /* Full friction braking */
        *friction_brake_out = (brake_pedal_percent * MAX_BRAKE_TORQUE_NM) / 100;
        return;
    }

    /* Calculate maximum regen torque based on battery limits */
    uint8_t battery_soc = BMS_GetSOC_percent();
    float soc_factor = 1.0f;
    if (battery_soc > 90) {
        soc_factor = (100.0f - battery_soc) / 10.0f;  /* Linear reduction 90-100% */
    }

    int16_t max_regen_torque = (MIN_REGEN_TORQUE_NM * g_regen_state.regen_strength_percent) / 100;
    max_regen_torque = (int16_t)(max_regen_torque * soc_factor);

    /* Apply regen based on brake pedal position */
    int16_t requested_brake_torque = (brake_pedal_percent * MAX_BRAKE_TORQUE_NM) / 100;

    if (abs(requested_brake_torque) <= abs(max_regen_torque)) {
        /* Regen can handle it all */
        *regen_torque_out = -requested_brake_torque;  /* Negative = regen */
        *friction_brake_out = 0;
    } else {
        /* Blend regen + friction */
        *regen_torque_out = max_regen_torque;
        *friction_brake_out = requested_brake_torque - abs(max_regen_torque);
    }

    g_regen_state.regen_torque_nm = *regen_torque_out;
    g_regen_state.friction_brake_request_nm = *friction_brake_out;
}

/* One-pedal driving mode (aggressive regen on throttle release) */
void VCU_Regen_OnePedalMode(uint8_t throttle_percent) {
    if (throttle_percent > 5) {
        g_regen_state.regen_torque_nm = 0;
        return;
    }

    /* Throttle released: apply regen proportional to vehicle speed */
    uint16_t speed_kph = VCU_GetVehicleSpeed_kph();
    float speed_factor = (speed_kph > 100) ? 1.0f : (speed_kph / 100.0f);

    int16_t one_pedal_regen = (int16_t)(MIN_REGEN_TORQUE_NM * 0.7f * speed_factor);

    VCU_TorqueArbiter_SetRequest(TORQUE_SOURCE_DRIVER, one_pedal_regen, true);
}
```

### 4. Traction Control Integration
```c
/* vcu_traction_control.c - Wheel slip detection and mitigation */
#include "vcu_traction_control.h"

#define WHEEL_SLIP_THRESHOLD_PERCENT 15  /* 15% slip triggers intervention */
#define TC_TORQUE_REDUCTION_STEP_NM 20
#define TC_RECOVERY_RATE_NM_PER_100MS 10

typedef struct {
    float wheel_speeds_kph[4];  /* FL, FR, RL, RR */
    float wheel_slip_percent[4];
    bool tc_active;
    int16_t torque_reduction_nm;
} TractionControl_t;

static TractionControl_t g_tc_state = {0};

void VCU_TractionControl_Update(void) {
    /* Read wheel speeds from ABS sensors via CAN */
    g_tc_state.wheel_speeds_kph[0] = ABS_GetWheelSpeed_kph(WHEEL_FL);
    g_tc_state.wheel_speeds_kph[1] = ABS_GetWheelSpeed_kph(WHEEL_FR);
    g_tc_state.wheel_speeds_kph[2] = ABS_GetWheelSpeed_kph(WHEEL_RL);
    g_tc_state.wheel_speeds_kph[3] = ABS_GetWheelSpeed_kph(WHEEL_RR);

    /* Calculate average driven wheel speed (RWD: rear wheels) */
    float driven_avg = (g_tc_state.wheel_speeds_kph[2] +
                        g_tc_state.wheel_speeds_kph[3]) / 2.0f;

    /* Calculate average non-driven wheel speed (reference) */
    float reference_avg = (g_tc_state.wheel_speeds_kph[0] +
                           g_tc_state.wheel_speeds_kph[1]) / 2.0f;

    if (reference_avg < 5.0f) {
        g_tc_state.tc_active = false;
        return;  /* Vehicle stopped */
    }

    /* Calculate slip percentage */
    float slip_percent = ((driven_avg - reference_avg) / reference_avg) * 100.0f;

    if (slip_percent > WHEEL_SLIP_THRESHOLD_PERCENT) {
        /* Excessive slip detected: reduce torque */
        g_tc_state.tc_active = true;
        g_tc_state.torque_reduction_nm += TC_TORQUE_REDUCTION_STEP_NM;

        /* Cap reduction at 80% of requested torque */
        int16_t driver_torque = VCU_TorqueArbiter_GetRequest(TORQUE_SOURCE_DRIVER);
        if (g_tc_state.torque_reduction_nm > driver_torque * 0.8f) {
            g_tc_state.torque_reduction_nm = (int16_t)(driver_torque * 0.8f);
        }

        /* Override driver request */
        int16_t limited_torque = driver_torque - g_tc_state.torque_reduction_nm;
        VCU_TorqueArbiter_SetRequest(TORQUE_SOURCE_TRACTION_CONTROL,
                                      limited_torque, true);
    } else {
        /* No slip: gradually restore torque */
        if (g_tc_state.torque_reduction_nm > 0) {
            g_tc_state.torque_reduction_nm -= TC_RECOVERY_RATE_NM_PER_100MS;
            if (g_tc_state.torque_reduction_nm < 0) {
                g_tc_state.torque_reduction_nm = 0;
                g_tc_state.tc_active = false;
                VCU_TorqueArbiter_SetRequest(TORQUE_SOURCE_TRACTION_CONTROL, 0, false);
            }
        }
    }
}
```

## AUTOSAR BSW Configuration

### VCU RTE Configuration (ARXML)
```xml
<!-- vcu_rte_configuration.arxml -->
<AUTOSAR xmlns="http://autosar.org/schema/r4.0">
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>VCU_ComponentTypes</SHORT-NAME>
      <ELEMENTS>
        <APPLICATION-SW-COMPONENT-TYPE>
          <SHORT-NAME>VCU_Controller</SHORT-NAME>
          <PORTS>
            <!-- Required Ports (inputs) -->
            <R-PORT-PROTOTYPE>
              <SHORT-NAME>ThrottlePedal</SHORT-NAME>
              <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
                /Interfaces/ThrottlePedal_IF
              </REQUIRED-INTERFACE-TREF>
            </R-PORT-PROTOTYPE>
            <R-PORT-PROTOTYPE>
              <SHORT-NAME>BrakePedal</SHORT-NAME>
              <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
                /Interfaces/BrakePedal_IF
              </REQUIRED-INTERFACE-TREF>
            </R-PORT-PROTOTYPE>
            <R-PORT-PROTOTYPE>
              <SHORT-NAME>BatteryStatus</SHORT-NAME>
              <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
                /Interfaces/BatteryStatus_IF
              </REQUIRED-INTERFACE-TREF>
            </R-PORT-PROTOTYPE>
            <R-PORT-PROTOTYPE>
              <SHORT-NAME>WheelSpeeds</SHORT-NAME>
              <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
                /Interfaces/WheelSpeeds_IF
              </REQUIRED-INTERFACE-TREF>
            </R-PORT-PROTOTYPE>

            <!-- Provided Ports (outputs) -->
            <P-PORT-PROTOTYPE>
              <SHORT-NAME>MotorTorqueCmd</SHORT-NAME>
              <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
                /Interfaces/MotorTorqueCmd_IF
              </PROVIDED-INTERFACE-TREF>
            </P-PORT-PROTOTYPE>
            <P-PORT-PROTOTYPE>
              <SHORT-NAME>BrakeRequest</SHORT-NAME>
              <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
                /Interfaces/BrakeRequest_IF
              </PROVIDED-INTERFACE-TREF>
            </P-PORT-PROTOTYPE>
            <P-PORT-PROTOTYPE>
              <SHORT-NAME>VehicleStatus</SHORT-NAME>
              <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
                /Interfaces/VehicleStatus_IF
              </PROVIDED-INTERFACE-TREF>
            </P-PORT-PROTOTYPE>
          </PORTS>

          <INTERNAL-BEHAVIORS>
            <SWC-INTERNAL-BEHAVIOR>
              <SHORT-NAME>VCU_InternalBehavior</SHORT-NAME>
              <RUNNABLES>
                <RUNNABLE-ENTITY>
                  <SHORT-NAME>VCU_Main_10ms</SHORT-NAME>
                  <MINIMUM-START-INTERVAL>0.01</MINIMUM-START-INTERVAL>
                  <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
                  <SYMBOL>VCU_Main_Runnable</SYMBOL>
                </RUNNABLE-ENTITY>
              </RUNNABLES>
              <EVENTS>
                <TIMING-EVENT>
                  <SHORT-NAME>TimingEvent_10ms</SHORT-NAME>
                  <START-ON-EVENT-REF DEST="RUNNABLE-ENTITY">
                    /VCU_ComponentTypes/VCU_Controller/VCU_InternalBehavior/VCU_Main_10ms
                  </START-ON-EVENT-REF>
                  <PERIOD>0.01</PERIOD>
                </TIMING-EVENT>
              </EVENTS>
            </SWC-INTERNAL-BEHAVIOR>
          </INTERNAL-BEHAVIORS>
        </APPLICATION-SW-COMPONENT-TYPE>
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>
```

## VCU CAN Database (DBC)
```
VERSION ""

NS_ :
    NS_DESC_
    CM_
    BA_DEF_
    BA_
    VAL_
    CAT_DEF_
    CAT_
    FILTER
    BA_DEF_DEF_
    EV_DATA_
    ENVVAR_DATA_
    SGTYPE_
    SGTYPE_VAL_
    BA_DEF_SGTYPE_
    BA_SGTYPE_
    SIG_TYPE_REF_
    VAL_TABLE_
    SIG_GROUP_
    SIG_VALTYPE_
    SIGTYPE_VALTYPE_
    BO_TX_BU_
    BA_DEF_REL_
    BA_REL_
    BA_SGTYPE_REL_
    SG_MUL_VAL_

BS_:

BU_: VCU MCU BMS BCM

/* VCU -> MCU: Motor Torque Command */
BO_ 256 VCU_MotorCmd: 8 VCU
 SG_ VCU_TorqueRequest : 0|16@1+ (-2000,0) [-2000|4000] "0.1Nm"  MCU
 SG_ VCU_SpeedLimit : 16|16@1+ (0,0) [0|18000] "0.1rpm"  MCU
 SG_ VCU_ControlMode : 32|8@1+ (0,0) [0|3] ""  MCU
 SG_ VCU_TorqueValid : 40|1@1+ (0,0) [0|1] ""  MCU
 SG_ VCU_TorqueSource : 41|3@1+ (0,0) [0|7] ""  MCU
 SG_ VCU_ChecksumTorque : 56|8@1+ (0,0) [0|255] ""  MCU

/* VCU -> BCM: Brake Request */
BO_ 257 VCU_BrakeCmd: 8 VCU
 SG_ VCU_FrictionBrake_FL : 0|16@1+ (0,0) [0|3000] "0.1Nm"  BCM
 SG_ VCU_FrictionBrake_FR : 16|16@1+ (0,0) [0|3000] "0.1Nm"  BCM
 SG_ VCU_FrictionBrake_RL : 32|16@1+ (0,0) [0|3000] "0.1Nm"  BCM
 SG_ VCU_FrictionBrake_RR : 48|16@1+ (0,0) [0|3000] "0.1Nm"  BCM

/* VCU -> CAN Bus: Vehicle Status */
BO_ 258 VCU_VehicleStatus: 8 VCU
 SG_ VCU_DriveMode : 0|8@1+ (0,0) [0|3] ""  BCM,MCU,BMS
 SG_ VCU_TractionControlActive : 8|1@1+ (0,0) [0|1] ""  BCM
 SG_ VCU_RegenAvailable : 9|1@1+ (0,0) [0|1] ""  BCM
 SG_ VCU_PowerLimitActive : 10|1@1+ (0,0) [0|1] ""  BCM
 SG_ VCU_VehicleReady : 11|1@1+ (0,0) [0|1] ""  BCM,MCU
 SG_ VCU_EstimatedRange_km : 16|16@1+ (0,0) [0|1000] "km"  BCM

VAL_ 256 VCU_ControlMode 0 "Torque_Mode" 1 "Speed_Mode" 2 "Power_Mode" 3 "Disabled";
VAL_ 256 VCU_TorqueSource 0 "Driver" 1 "CruiseControl" 2 "TractionControl" 3 "StabilityControl" 4 "PowerLimit" 5 "ThermalLimit";
VAL_ 258 VCU_DriveMode 0 "Eco" 1 "Normal" 2 "Sport" 3 "Custom";
```

## Power Distribution Strategy
```c
/* vcu_power_distribution.c - Energy management and power budgeting */
#include "vcu_power_management.h"

#define BATTERY_MAX_POWER_KW 150
#define HVAC_MAX_POWER_KW 6
#define DCDC_MAX_POWER_KW 3
#define AUXILIARY_MAX_POWER_KW 2

typedef struct {
    float available_battery_power_kw;
    float allocated_propulsion_kw;
    float allocated_hvac_kw;
    float allocated_auxiliary_kw;
    bool power_limit_active;
} PowerBudget_t;

static PowerBudget_t g_power_budget = {0};

void VCU_PowerManagement_Update(void) {
    /* Get battery discharge limit from BMS */
    g_power_budget.available_battery_power_kw = BMS_GetMaxDischargePower_kW();

    /* Propulsion has first priority */
    float requested_propulsion_kw = VCU_GetRequestedPropulsionPower_kW();

    /* HVAC second priority (can be reduced in power-limited situations) */
    float requested_hvac_kw = HVAC_GetRequestedPower_kW();

    /* Allocate power with priorities */
    float total_requested = requested_propulsion_kw + requested_hvac_kw +
                            DCDC_MAX_POWER_KW + AUXILIARY_MAX_POWER_KW;

    if (total_requested <= g_power_budget.available_battery_power_kw) {
        /* No power limiting needed */
        g_power_budget.allocated_propulsion_kw = requested_propulsion_kw;
        g_power_budget.allocated_hvac_kw = requested_hvac_kw;
        g_power_budget.power_limit_active = false;
    } else {
        /* Power limiting: reduce HVAC first, then propulsion */
        g_power_budget.power_limit_active = true;

        float available_for_hvac = g_power_budget.available_battery_power_kw -
                                    requested_propulsion_kw - DCDC_MAX_POWER_KW -
                                    AUXILIARY_MAX_POWER_KW;

        if (available_for_hvac >= requested_hvac_kw) {
            /* Can still power HVAC fully, limit propulsion */
            g_power_budget.allocated_hvac_kw = requested_hvac_kw;
            g_power_budget.allocated_propulsion_kw = g_power_budget.available_battery_power_kw -
                                                      requested_hvac_kw - DCDC_MAX_POWER_KW -
                                                      AUXILIARY_MAX_POWER_KW;
        } else {
            /* Limit HVAC */
            g_power_budget.allocated_hvac_kw = available_for_hvac > 0 ? available_for_hvac : 0;
            g_power_budget.allocated_propulsion_kw = requested_propulsion_kw;
        }

        /* Apply power limit to torque command */
        int16_t limited_torque = VCU_CalculateTorqueFromPower(
            g_power_budget.allocated_propulsion_kw);
        VCU_TorqueArbiter_SetRequest(TORQUE_SOURCE_POWER_LIMIT, limited_torque, true);
    }
}
```

## ISO 26262 Safety Mechanisms

### Torque Plausibility Check
```c
/* Safety monitor for torque command plausibility */
void VCU_Safety_TorquePlausibilityCheck(void) {
    int16_t commanded_torque = VCU_TorqueArbiter_GetArbitratedTorque();
    int16_t measured_torque = MCU_GetActualTorque();

    int16_t torque_error = abs(commanded_torque - measured_torque);

    if (torque_error > TORQUE_PLAUSIBILITY_THRESHOLD_NM) {
        /* Torque mismatch detected */
        g_safety_fault_counter++;

        if (g_safety_fault_counter > SAFETY_FAULT_THRESHOLD) {
            /* Enter safe state: zero torque request */
            VCU_EnterSafeState();
            DTC_SetFault(DTC_TORQUE_PLAUSIBILITY_FAULT);
        }
    } else {
        if (g_safety_fault_counter > 0) {
            g_safety_fault_counter--;
        }
    }
}
```

## Testing Requirements

### HIL Test Cases
```python
# vcu_hil_test.py - Hardware-in-the-Loop test suite
import can
import pytest
import time

class TestVCUTorqueArbiter:
    def test_driver_torque_request_normal(self, vcu_hil):
        """Verify driver torque request in normal conditions"""
        # Set throttle pedal to 50%
        vcu_hil.set_analog_input("ThrottlePedal", 2.5)  # 0-5V
        time.sleep(0.05)

        # Read CAN message VCU_MotorCmd
        msg = vcu_hil.can_bus.recv(timeout=0.1)
        assert msg.arbitration_id == 0x100  # 256 decimal

        torque_request = int.from_bytes(msg.data[0:2], 'little', signed=True) * 0.1
        assert 150 < torque_request < 250  # Expected range for 50% throttle in Normal mode

    def test_traction_control_intervention(self, vcu_hil):
        """Verify traction control reduces torque on wheel slip"""
        # Simulate wheel slip: driven wheels faster than reference
        vcu_hil.inject_can_message(0x220, [0x64, 0x00, 0x64, 0x00, 0xC8, 0x00, 0xC8, 0x00])
        # Front wheels: 100 kph, Rear wheels: 200 kph (100% slip)

        time.sleep(0.2)

        # Verify VCU_VehicleStatus shows TC active
        status_msg = vcu_hil.read_can_message(0x102)
        tc_active = (status_msg.data[1] & 0x01) == 0x01
        assert tc_active

        # Verify torque reduction
        torque_msg = vcu_hil.read_can_message(0x100)
        torque_source = (torque_msg.data[5] >> 1) & 0x07
        assert torque_source == 2  # TractionControl source
```

## References
- ISO 26262-6: Product development at the software level
- AUTOSAR Classic Platform R20-11: RTE Specification
- SAE J2735: Dedicated Short Range Communications (DSRC) Message Set Dictionary
- ECE R13: Uniform provisions concerning the approval of vehicles of categories M, N and O with regard to braking

## Common Issues
- Torque command jitter due to insufficient rate limiting
- Regen braking not blending smoothly with friction brakes
- Traction control oscillation from aggressive intervention
- Drive mode changes causing torque steps
- Power limiting not respecting HVAC comfort requirements
