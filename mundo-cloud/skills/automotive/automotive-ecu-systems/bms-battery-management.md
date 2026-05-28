# BMS (Battery Management System) for EVs/HEVs

## Overview
The Battery Management System (BMS) monitors cell voltages, estimates SOC/SOH, performs cell balancing, manages thermal systems, controls contactors, and ensures ISO 26262 ASIL-D safety compliance for high-voltage battery packs.

## Core Responsibilities

### 1. Cell Voltage Monitoring
```c
/* bms_cell_monitoring.c - Multi-cell voltage acquisition */
#include "bms_cell_monitoring.h"

#define MAX_CELLS_PER_MODULE 12
#define MAX_MODULES 10
#define TOTAL_CELLS (MAX_CELLS_PER_MODULE * MAX_MODULES)

#define CELL_OVERVOLTAGE_MV 4200
#define CELL_UNDERVOLTAGE_MV 2500

typedef struct {
    uint16_t voltage_mv;
    int16_t temperature_c_x10;  /* 0.1°C resolution */
    bool balancing_active;
} CellData_t;

typedef struct {
    CellData_t cells[MAX_CELLS_PER_MODULE];
    uint8_t module_id;
    int16_t module_temperature_c_x10;
    bool communication_ok;
} ModuleData_t;

static ModuleData_t g_modules[MAX_MODULES];

/* LTC6811 Battery Monitor IC interface */
void BMS_CellMonitoring_Init(void) {
    /* Initialize SPI for LTC6811 daisy chain */
    SPI_Init(SPI_BMS, 1000000);  /* 1 MHz */

    /* Wake up all LTC6811 ICs */
    BMS_LTC6811_Wakeup();

    /* Configure cell measurement mode */
    uint8_t config[6] = {
        0xF8,  /* GPIO pull-downs off, REFON=1 */
        0x00,  /* Discharge switches off */
        0x00, 0x00, 0x00, 0x00
    };
    BMS_LTC6811_WriteConfig(config);
}

void BMS_CellMonitoring_Update(void) {
    /* Start cell voltage conversion (all cells, all modules) */
    BMS_LTC6811_StartCellConversion(ADC_MODE_NORMAL, ADC_FILTER_7KHZ);

    /* Wait for conversion (2.3ms for normal mode) */
    OsTask_Sleep(3);

    /* Read cell voltages from all modules */
    for (uint8_t module = 0; module < MAX_MODULES; module++) {
        uint16_t cell_voltages[MAX_CELLS_PER_MODULE];

        if (BMS_LTC6811_ReadCellVoltages(module, cell_voltages)) {
            for (uint8_t cell = 0; cell < MAX_CELLS_PER_MODULE; cell++) {
                g_modules[module].cells[cell].voltage_mv = cell_voltages[cell] / 10;  /* 100µV resolution */

                /* Check overvoltage/undervoltage */
                if (cell_voltages[cell] > CELL_OVERVOLTAGE_MV) {
                    BMS_Fault_SetOvervoltage(module, cell);
                }
                if (cell_voltages[cell] < CELL_UNDERVOLTAGE_MV) {
                    BMS_Fault_SetUndervoltage(module, cell);
                }
            }
            g_modules[module].communication_ok = true;
        } else {
            g_modules[module].communication_ok = false;
            BMS_Fault_SetCommunicationLoss(module);
        }
    }

    /* Read temperatures via GPIO (NTC thermistors) */
    BMS_LTC6811_ReadGPIO();
}

uint16_t BMS_GetMinCellVoltage_mV(void) {
    uint16_t min_voltage = 0xFFFF;

    for (uint8_t mod = 0; mod < MAX_MODULES; mod++) {
        for (uint8_t cell = 0; cell < MAX_CELLS_PER_MODULE; cell++) {
            if (g_modules[mod].cells[cell].voltage_mv < min_voltage) {
                min_voltage = g_modules[mod].cells[cell].voltage_mv;
            }
        }
    }

    return min_voltage;
}

uint16_t BMS_GetMaxCellVoltage_mV(void) {
    uint16_t max_voltage = 0;

    for (uint8_t mod = 0; mod < MAX_MODULES; mod++) {
        for (uint8_t cell = 0; cell < MAX_CELLS_PER_MODULE; cell++) {
            if (g_modules[mod].cells[cell].voltage_mv > max_voltage) {
                max_voltage = g_modules[mod].cells[cell].voltage_mv;
            }
        }
    }

    return max_voltage;
}
```

### 2. SOC/SOH Estimation (Coulomb Counting + Kalman Filter)
```c
/* bms_soc_estimation.c - State of Charge / State of Health algorithms */
#include "bms_soc_estimation.h"
#include <math.h>

#define BATTERY_CAPACITY_AH 75.0
#define COULOMB_EFFICIENCY 0.98  /* Charge efficiency */

typedef struct {
    float soc_percent;           /* 0-100% */
    float soh_percent;           /* 0-100%, degrades over time */
    float coulomb_count_ah;      /* Accumulated amp-hours */
    float ocv_voltage_v;         /* Open circuit voltage */
    uint32_t cycle_count;        /* Full charge/discharge cycles */
    float remaining_capacity_ah;
} SOCState_t;

static SOCState_t g_soc_state = {
    .soc_percent = 50.0,
    .soh_percent = 100.0,
    .coulomb_count_ah = BATTERY_CAPACITY_AH / 2.0,
    .remaining_capacity_ah = BATTERY_CAPACITY_AH
};

/* OCV-SOC lookup table (Open Circuit Voltage to SOC mapping) */
static const struct {
    float voltage_v;
    float soc_percent;
} OCV_SOC_TABLE[] = {
    {3.27, 0.0},
    {3.61, 10.0},
    {3.69, 20.0},
    {3.71, 30.0},
    {3.73, 40.0},
    {3.77, 50.0},
    {3.83, 60.0},
    {3.92, 70.0},
    {4.01, 80.0},
    {4.08, 90.0},
    {4.20, 100.0}
};

void BMS_SOC_Init(void) {
    /* Load last known SOC from EEPROM */
    NvM_ReadBlock(NVM_BLOCK_SOC_STATE, &g_soc_state);

    /* Initialize Kalman filter for SOC estimation */
    BMS_KalmanFilter_Init();
}

void BMS_SOC_Update(float current_a, uint32_t delta_time_ms) {
    /* Coulomb counting: integrate current over time */
    float delta_time_h = delta_time_ms / 3600000.0;
    float delta_ah = current_a * delta_time_h;

    /* Positive current = discharge, negative = charge */
    if (current_a > 0) {
        g_soc_state.coulomb_count_ah -= delta_ah;
    } else {
        g_soc_state.coulomb_count_ah -= delta_ah * COULOMB_EFFICIENCY;
    }

    /* Clamp to capacity limits */
    if (g_soc_state.coulomb_count_ah < 0) {
        g_soc_state.coulomb_count_ah = 0;
    }
    if (g_soc_state.coulomb_count_ah > g_soc_state.remaining_capacity_ah) {
        g_soc_state.coulomb_count_ah = g_soc_state.remaining_capacity_ah;
    }

    /* Calculate SOC from coulomb count */
    g_soc_state.soc_percent = (g_soc_state.coulomb_count_ah /
                                g_soc_state.remaining_capacity_ah) * 100.0;

    /* Kalman filter fusion with OCV-based SOC (when current near zero) */
    if (fabs(current_a) < 1.0) {  /* Low current: use OCV */
        float pack_voltage_v = BMS_GetPackVoltage() / 1000.0;
        float avg_cell_voltage_v = pack_voltage_v / TOTAL_CELLS;

        float ocv_soc = BMS_SOC_LookupOCV(avg_cell_voltage_v);

        /* Kalman filter update */
        g_soc_state.soc_percent = BMS_KalmanFilter_Update(
            g_soc_state.soc_percent,
            ocv_soc);
    }

    /* Persist SOC every 1% change */
    static float last_saved_soc = 0;
    if (fabs(g_soc_state.soc_percent - last_saved_soc) > 1.0) {
        NvM_WriteBlock(NVM_BLOCK_SOC_STATE, &g_soc_state);
        last_saved_soc = g_soc_state.soc_percent;
    }
}

float BMS_SOC_LookupOCV(float voltage_v) {
    /* Linear interpolation in OCV-SOC table */
    for (int i = 0; i < (sizeof(OCV_SOC_TABLE) / sizeof(OCV_SOC_TABLE[0])) - 1; i++) {
        if (voltage_v >= OCV_SOC_TABLE[i].voltage_v &&
            voltage_v <= OCV_SOC_TABLE[i+1].voltage_v) {

            float v_range = OCV_SOC_TABLE[i+1].voltage_v - OCV_SOC_TABLE[i].voltage_v;
            float soc_range = OCV_SOC_TABLE[i+1].soc_percent - OCV_SOC_TABLE[i].soc_percent;
            float v_delta = voltage_v - OCV_SOC_TABLE[i].voltage_v;

            return OCV_SOC_TABLE[i].soc_percent + (v_delta / v_range) * soc_range;
        }
    }

    return 50.0;  /* Default fallback */
}

/* SOH estimation based on capacity fade */
void BMS_SOH_Update(void) {
    /* Detect full charge cycle: SOC goes 100% -> 0% -> 100% */
    static bool charging = false;
    static bool discharged = false;

    if (g_soc_state.soc_percent > 99.0 && !charging) {
        charging = true;

        if (discharged) {
            /* Full cycle completed */
            g_soc_state.cycle_count++;

            /* Estimate capacity fade: 80% at 1000 cycles (linear model) */
            g_soc_state.remaining_capacity_ah =
                BATTERY_CAPACITY_AH * (1.0 - (g_soc_state.cycle_count / 5000.0));

            g_soc_state.soh_percent = (g_soc_state.remaining_capacity_ah /
                                       BATTERY_CAPACITY_AH) * 100.0;

            discharged = false;
        }
    }

    if (g_soc_state.soc_percent < 5.0) {
        discharged = true;
        charging = false;
    }
}
```

### 3. Cell Balancing (Active/Passive)
```c
/* bms_cell_balancing.c - Cell voltage equalization */
#include "bms_cell_balancing.h"

#define BALANCE_THRESHOLD_MV 10  /* Start balancing if cell delta > 10mV */
#define BALANCE_TARGET_MV 5      /* Stop when delta < 5mV */
#define MAX_BALANCE_CURRENT_MA 200

void BMS_CellBalancing_Update(void) {
    uint16_t min_voltage = BMS_GetMinCellVoltage_mV();
    uint16_t max_voltage = BMS_GetMaxCellVoltage_mV();

    if ((max_voltage - min_voltage) < BALANCE_THRESHOLD_MV) {
        /* Cells well balanced: disable all balancing */
        BMS_CellBalancing_DisableAll();
        return;
    }

    /* Passive balancing: discharge high cells through resistors */
    for (uint8_t mod = 0; mod < MAX_MODULES; mod++) {
        uint16_t balance_mask = 0;

        for (uint8_t cell = 0; cell < MAX_CELLS_PER_MODULE; cell++) {
            uint16_t cell_voltage = g_modules[mod].cells[cell].voltage_mv;

            /* Balance if above minimum + threshold */
            if (cell_voltage > (min_voltage + BALANCE_TARGET_MV)) {
                balance_mask |= (1 << cell);
                g_modules[mod].cells[cell].balancing_active = true;
            } else {
                g_modules[mod].cells[cell].balancing_active = false;
            }
        }

        /* Write balance control register to LTC6811 */
        BMS_LTC6811_SetBalancing(mod, balance_mask);
    }
}
```

### 4. Contactor Control (Safety-Critical)
```c
/* bms_contactor_control.c - High-voltage contactor sequencing */
#include "bms_contactor_control.h"

#define PRECHARGE_TIMEOUT_MS 5000
#define PRECHARGE_THRESHOLD_PERCENT 95

typedef enum {
    CONTACTOR_STATE_OPEN = 0,
    CONTACTOR_STATE_PRECHARGING,
    CONTACTOR_STATE_CLOSED,
    CONTACTOR_STATE_FAULT
} ContactorState_t;

static ContactorState_t g_contactor_state = CONTACTOR_STATE_OPEN;

void BMS_Contactor_Close(void) {
    /* Safety checks before closing */
    if (!BMS_Safety_PreCloseCheck()) {
        g_contactor_state = CONTACTOR_STATE_FAULT;
        return;
    }

    /* Step 1: Close negative contactor */
    GPIO_Set(GPIO_CONTACTOR_NEGATIVE, true);
    OsTask_Sleep(50);

    /* Step 2: Precharge positive side through resistor */
    g_contactor_state = CONTACTOR_STATE_PRECHARGING;
    GPIO_Set(GPIO_PRECHARGE_RELAY, true);

    uint32_t start_time = GetSystemTime_ms();
    uint16_t pack_voltage_v = BMS_GetPackVoltage();
    uint16_t link_voltage_v = ADC_ReadHVLinkVoltage();

    /* Wait for DC link to charge to 95% of pack voltage */
    while ((GetSystemTime_ms() - start_time) < PRECHARGE_TIMEOUT_MS) {
        link_voltage_v = ADC_ReadHVLinkVoltage();

        if (link_voltage_v > (pack_voltage_v * PRECHARGE_THRESHOLD_PERCENT / 100)) {
            break;  /* Precharge complete */
        }

        OsTask_Sleep(10);
    }

    if (link_voltage_v < (pack_voltage_v * PRECHARGE_THRESHOLD_PERCENT / 100)) {
        /* Precharge timeout: fault */
        GPIO_Set(GPIO_PRECHARGE_RELAY, false);
        GPIO_Set(GPIO_CONTACTOR_NEGATIVE, false);
        g_contactor_state = CONTACTOR_STATE_FAULT;
        DTC_SetFault(DTC_PRECHARGE_TIMEOUT);
        return;
    }

    /* Step 3: Close positive contactor */
    GPIO_Set(GPIO_CONTACTOR_POSITIVE, true);
    OsTask_Sleep(50);

    /* Step 4: Open precharge relay */
    GPIO_Set(GPIO_PRECHARGE_RELAY, false);

    g_contactor_state = CONTACTOR_STATE_CLOSED;
}

void BMS_Contactor_Open(void) {
    /* Open positive first, then negative */
    GPIO_Set(GPIO_CONTACTOR_POSITIVE, false);
    OsTask_Sleep(50);
    GPIO_Set(GPIO_CONTACTOR_NEGATIVE, false);

    g_contactor_state = CONTACTOR_STATE_OPEN;
}
```

## BMS CAN Database (DBC)
```
VERSION ""

NS_ :

BS_:

BU_: BMS VCU MCU

/* BMS Battery Status */
BO_ 768 BMS_BatteryStatus: 8 BMS
 SG_ BMS_PackVoltage_V : 0|16@1+ (0.1,0) [0|600] "V"  VCU,MCU
 SG_ BMS_PackCurrent_A : 16|16@1- (0.1,-320) [-320|320] "A"  VCU,MCU
 SG_ BMS_SOC_percent : 32|8@1+ (0.5,0) [0|100] "%"  VCU,MCU
 SG_ BMS_SOH_percent : 40|8@1+ (0.5,0) [0|100] "%"  VCU
 SG_ BMS_MaxCellTemp_C : 48|8@1+ (1,-40) [-40|100] "C"  VCU,MCU
 SG_ BMS_ContactorState : 56|8@1+ (0,0) [0|3] ""  VCU,MCU

VAL_ 768 BMS_ContactorState 0 "Open" 1 "Precharging" 2 "Closed" 3 "Fault";
```

## ISO 26262 ASIL-D Safety Mechanisms
- Dual voltage measurement paths with cross-checking
- Watchdog timer for contactor control
- Cell voltage plausibility checks
- Safe state transition on fault detection

## References
- ISO 26262: Functional Safety for Road Vehicles
- UL 2580: Batteries for Use in Electric Vehicles
- IEC 62133: Safety Requirements for Portable Sealed Secondary Cells
- SAE J2464: EV Battery Systems Crashworthiness

## Common Issues
- SOC drift from coulomb counting errors
- Cell balancing inefficiency at low SOC
- Precharge relay welding from inrush current
- Temperature sensor failures affecting thermal management
