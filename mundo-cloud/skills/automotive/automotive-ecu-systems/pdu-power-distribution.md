# PDU (Power Distribution Unit) - High/Low Voltage Power Management

## Overview
The Power Distribution Unit (PDU) manages high-voltage DC/DC converters, low-voltage power distribution, fuse/relay control, load shedding, power budgeting, battery voltage monitoring, and wake-up source management.

## Core Responsibilities

### 1. High-Voltage DC/DC Converter
```c
/* pdu_hv_dcdc.c - High-voltage to 12V DC/DC conversion */
#include "pdu_hv_dcdc.h"

#define HV_INPUT_MIN_V 200
#define HV_INPUT_MAX_V 450
#define LV_OUTPUT_TARGET_V 14.0
#define MAX_OUTPUT_CURRENT_A 150

typedef struct {
    uint16_t hv_input_voltage_v;
    float lv_output_voltage_v;
    float output_current_a;
    float efficiency_percent;
    bool enabled;
    bool fault_active;
} DCDC_State_t;

static DCDC_State_t g_dcdc = {0};

void PDU_DCDC_Init(void) {
    /* Configure PWM for DC/DC converter control */
    PWM_Init(PWM_CHANNEL_DCDC, 100000);  /* 100 kHz switching */

    /* Set initial duty cycle to 0 */
    PWM_SetDutyCycle(PWM_CHANNEL_DCDC, 0);

    g_dcdc.enabled = false;
}

void PDU_DCDC_Enable(void) {
    /* Safety checks */
    g_dcdc.hv_input_voltage_v = ADC_ReadHVInput();

    if (g_dcdc.hv_input_voltage_v < HV_INPUT_MIN_V ||
        g_dcdc.hv_input_voltage_v > HV_INPUT_MAX_V) {
        g_dcdc.fault_active = true;
        return;
    }

    /* Enable DC/DC converter */
    GPIO_Set(GPIO_DCDC_ENABLE, true);
    g_dcdc.enabled = true;

    /* Start voltage regulation loop */
    PDU_DCDC_RegulationLoop();
}

void PDU_DCDC_RegulationLoop(void) {
    /* PI controller for output voltage regulation */
    static float integral = 0;
    const float Kp = 0.5;
    const float Ki = 0.1;

    while (g_dcdc.enabled) {
        /* Read output voltage and current */
        g_dcdc.lv_output_voltage_v = ADC_ReadLVOutput();
        g_dcdc.output_current_a = ADC_ReadOutputCurrent();

        /* Calculate error */
        float error = LV_OUTPUT_TARGET_V - g_dcdc.lv_output_voltage_v;

        /* PI control */
        integral += error * 0.01;  /* 10ms loop time */
        float duty_cycle = (Kp * error) + (Ki * integral);

        /* Clamp duty cycle */
        if (duty_cycle > 95) duty_cycle = 95;
        if (duty_cycle < 5) duty_cycle = 5;

        PWM_SetDutyCycle(PWM_CHANNEL_DCDC, duty_cycle);

        /* Overcurrent protection */
        if (g_dcdc.output_current_a > MAX_OUTPUT_CURRENT_A) {
            PDU_DCDC_Disable();
            g_dcdc.fault_active = true;
            DTC_SetFault(DTC_DCDC_OVERCURRENT);
            break;
        }

        OsTask_Sleep(10);
    }
}

void PDU_DCDC_Disable(void) {
    PWM_SetDutyCycle(PWM_CHANNEL_DCDC, 0);
    GPIO_Set(GPIO_DCDC_ENABLE, false);
    g_dcdc.enabled = false;
}
```

### 2. Low-Voltage Power Distribution (Fuse/Relay Control)
```c
/* pdu_lv_distribution.c - 12V power distribution and load management */
#include "pdu_lv_distribution.h"

#define MAX_POWER_CHANNELS 16

typedef enum {
    LOAD_PRIORITY_CRITICAL = 0,    /* Safety: always on */
    LOAD_PRIORITY_HIGH,             /* Powertrain */
    LOAD_PRIORITY_MEDIUM,           /* Comfort */
    LOAD_PRIORITY_LOW               /* Infotainment */
} LoadPriority_t;

typedef struct {
    const char* name;
    uint8_t relay_pin;
    uint8_t current_sense_adc;
    float max_current_a;
    LoadPriority_t priority;
    bool enabled;
    float measured_current_a;
} PowerChannel_t;

static PowerChannel_t g_power_channels[MAX_POWER_CHANNELS] = {
    {"BCM", GPIO_RELAY_BCM, ADC_CH_BCM_CURRENT, 15.0, LOAD_PRIORITY_CRITICAL, true, 0},
    {"VCU", GPIO_RELAY_VCU, ADC_CH_VCU_CURRENT, 10.0, LOAD_PRIORITY_CRITICAL, true, 0},
    {"BMS", GPIO_RELAY_BMS, ADC_CH_BMS_CURRENT, 8.0, LOAD_PRIORITY_CRITICAL, true, 0},
    {"MCU", GPIO_RELAY_MCU, ADC_CH_MCU_CURRENT, 12.0, LOAD_PRIORITY_HIGH, true, 0},
    {"IVI", GPIO_RELAY_IVI, ADC_CH_IVI_CURRENT, 20.0, LOAD_PRIORITY_LOW, true, 0},
    {"HVAC", GPIO_RELAY_HVAC, ADC_CH_HVAC_CURRENT, 25.0, LOAD_PRIORITY_MEDIUM, true, 0},
    {"Headlights", GPIO_RELAY_LIGHTS, ADC_CH_LIGHTS_CURRENT, 10.0, LOAD_PRIORITY_HIGH, false, 0},
    {"USB_Ports", GPIO_RELAY_USB, ADC_CH_USB_CURRENT, 5.0, LOAD_PRIORITY_LOW, false, 0}
};

void PDU_LV_Init(void) {
    /* Initialize all relay control pins */
    for (int i = 0; i < MAX_POWER_CHANNELS; i++) {
        GPIO_ConfigOutput(g_power_channels[i].relay_pin);

        /* Enable critical and high priority loads by default */
        if (g_power_channels[i].priority <= LOAD_PRIORITY_HIGH) {
            PDU_LV_EnableChannel(i);
        }
    }
}

void PDU_LV_EnableChannel(uint8_t channel_id) {
    if (channel_id >= MAX_POWER_CHANNELS) return;

    GPIO_Set(g_power_channels[channel_id].relay_pin, true);
    g_power_channels[channel_id].enabled = true;
}

void PDU_LV_DisableChannel(uint8_t channel_id) {
    if (channel_id >= MAX_POWER_CHANNELS) return;

    GPIO_Set(g_power_channels[channel_id].relay_pin, false);
    g_power_channels[channel_id].enabled = false;
}

/* Monitor current and detect overcurrent faults */
void PDU_LV_MonitorCurrents(void) {
    for (int i = 0; i < MAX_POWER_CHANNELS; i++) {
        if (!g_power_channels[i].enabled) continue;

        /* Read current sensor (Hall effect sensor, 185mV/A) */
        uint16_t adc_value = ADC_Read(g_power_channels[i].current_sense_adc);
        float voltage_mv = (adc_value * 5000.0) / 4096.0;

        g_power_channels[i].measured_current_a = (voltage_mv - 2500.0) / 185.0;

        /* Check for overcurrent */
        if (g_power_channels[i].measured_current_a > g_power_channels[i].max_current_a) {
            /* Overcurrent detected: disable channel */
            PDU_LV_DisableChannel(i);
            DTC_SetFault(DTC_OVERCURRENT_BASE + i);

            /* Log event */
            Log("Overcurrent on %s: %.2f A (max %.2f A)",
                g_power_channels[i].name,
                g_power_channels[i].measured_current_a,
                g_power_channels[i].max_current_a);
        }
    }
}
```

### 3. Load Shedding (Power Budget Management)
```c
/* pdu_load_shedding.c - Intelligent load management under power constraints */
#include "pdu_load_shedding.h"

#define BATTERY_CRITICAL_VOLTAGE_V 11.0
#define BATTERY_LOW_VOLTAGE_V 11.5

void PDU_LoadShedding_Update(void) {
    float battery_voltage = ADC_ReadBatteryVoltage();
    float total_current = 0;

    /* Calculate total current draw */
    for (int i = 0; i < MAX_POWER_CHANNELS; i++) {
        if (g_power_channels[i].enabled) {
            total_current += g_power_channels[i].measured_current_a;
        }
    }

    /* Check if battery voltage is low */
    if (battery_voltage < BATTERY_CRITICAL_VOLTAGE_V) {
        /* Critical: shed all non-critical loads */
        for (int i = 0; i < MAX_POWER_CHANNELS; i++) {
            if (g_power_channels[i].priority > LOAD_PRIORITY_CRITICAL) {
                PDU_LV_DisableChannel(i);
            }
        }

        Log("Critical battery voltage: %.2f V - load shedding active", battery_voltage);

    } else if (battery_voltage < BATTERY_LOW_VOLTAGE_V) {
        /* Low: shed low-priority loads */
        for (int i = 0; i < MAX_POWER_CHANNELS; i++) {
            if (g_power_channels[i].priority >= LOAD_PRIORITY_LOW) {
                PDU_LV_DisableChannel(i);
            }
        }

        Log("Low battery voltage: %.2f V - reducing load", battery_voltage);
    }

    /* Check DC/DC converter output current limit */
    if (total_current > (MAX_OUTPUT_CURRENT_A * 0.9)) {
        /* Approaching limit: shed lowest priority loads */
        for (int i = MAX_POWER_CHANNELS - 1; i >= 0; i--) {
            if (g_power_channels[i].priority == LOAD_PRIORITY_LOW &&
                g_power_channels[i].enabled) {
                PDU_LV_DisableChannel(i);

                /* Recalculate total current */
                total_current -= g_power_channels[i].measured_current_a;

                if (total_current < (MAX_OUTPUT_CURRENT_A * 0.85)) {
                    break;  /* Sufficient headroom */
                }
            }
        }
    }
}
```

### 4. Wake-Up Source Management
```c
/* pdu_wakeup_sources.c - Network wake-up coordination */
#include "pdu_wakeup_sources.h"

#define WAKEUP_CAN_TIMEOUT_MS 100
#define SLEEP_DELAY_MS 5000

typedef enum {
    WAKEUP_SOURCE_CAN = 0,
    WAKEUP_SOURCE_LIN,
    WAKEUP_SOURCE_IGNITION,
    WAKEUP_SOURCE_DOOR,
    WAKEUP_SOURCE_TIMER,
    WAKEUP_SOURCE_COUNT
} WakeupSource_t;

static bool g_wakeup_pending[WAKEUP_SOURCE_COUNT] = {false};

void PDU_Wakeup_OnCANActivity(void) {
    g_wakeup_pending[WAKEUP_SOURCE_CAN] = true;

    /* Power up CAN transceivers */
    GPIO_Set(GPIO_CAN_POWERTRAIN_ENABLE, true);
    GPIO_Set(GPIO_CAN_CHASSIS_ENABLE, true);

    /* Notify ECUs of wake-up */
    CAN_SendWakeupNotification();
}

void PDU_Sleep_Prepare(void) {
    /* Wait for all ECUs to enter sleep */
    uint32_t start_time = GetSystemTime_ms();

    while ((GetSystemTime_ms() - start_time) < SLEEP_DELAY_MS) {
        /* Check for wake-up requests */
        for (int i = 0; i < WAKEUP_SOURCE_COUNT; i++) {
            if (g_wakeup_pending[i]) {
                /* Wake-up requested: abort sleep */
                return;
            }
        }
        OsTask_Sleep(10);
    }

    /* Enter sleep mode */
    PDU_EnterSleep();
}

void PDU_EnterSleep(void) {
    /* Disable non-critical power channels */
    for (int i = 0; i < MAX_POWER_CHANNELS; i++) {
        if (g_power_channels[i].priority > LOAD_PRIORITY_CRITICAL) {
            PDU_LV_DisableChannel(i);
        }
    }

    /* Configure wake-up sources */
    CAN_ConfigureWakeup(CAN_WAKEUP_ENABLED);
    GPIO_ConfigureWakeup(GPIO_IGNITION, GPIO_WAKEUP_RISING_EDGE);

    /* Enter low-power mode */
    Mcu_SetMode(MCU_MODE_SLEEP);
}
```

## PDU CAN Database (DBC)
```
VERSION ""

NS_ :

BS_:

BU_: PDU VCU BMS BCM

/* PDU Power Status */
BO_ 896 PDU_PowerStatus: 8 PDU
 SG_ PDU_BatteryVoltage_V : 0|16@1+ (0.01,0) [0|16] "V"  VCU,BMS
 SG_ PDU_DCDCOutputCurrent_A : 16|16@1+ (0.1,0) [0|200] "A"  VCU
 SG_ PDU_LoadSheddingActive : 32|1@1+ (0,0) [0|1] ""  VCU,BCM
 SG_ PDU_PowerChannelStatus : 40|16@1+ (0,0) [0|65535] ""  VCU

/* Each bit in PowerChannelStatus represents one load (0=off, 1=on) */
```

## References
- LTC3780: High-Voltage Buck-Boost DC/DC Controller
- ISO 16750: Road vehicles - Environmental conditions and testing for electrical and electronic equipment
- SAE J1455: Recommended Environmental Practices for Electronic Equipment Design
- IEC 61000-4-2: EMC Immunity to Electrostatic Discharge

## Common Issues
- DC/DC converter instability at high loads
- Relay contact welding from inrush current
- False overcurrent detection from current sensor noise
- Wake-up failures due to CAN transceiver not powered
