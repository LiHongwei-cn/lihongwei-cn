# BCM (Body Control Module) - Comfort and Convenience Systems

## Overview
The Body Control Unit (BCM) manages exterior/interior lighting, HVAC integration, door locks, windows, wipers, keyless entry, anti-theft systems, and power distribution across body electronics. This skill covers production-ready BCM development with LIN bus mastering.

## Core Responsibilities

### 1. Exterior/Interior Lighting Control
```c
/* bcm_lighting_control.c - Comprehensive lighting management */
#include "bcm_lighting_control.h"
#include <stdint.h>
#include <stdbool.h>

#define PWM_FREQUENCY_HZ 1000
#define DIM_STEP_PERCENT 5
#define AUTO_HEADLIGHT_THRESHOLD_LUX 100

typedef enum {
    LIGHT_MODE_OFF = 0,
    LIGHT_MODE_PARKING,
    LIGHT_MODE_DAYTIME_RUNNING,
    LIGHT_MODE_LOW_BEAM,
    LIGHT_MODE_HIGH_BEAM,
    LIGHT_MODE_AUTO
} HeadlightMode_t;

typedef struct {
    bool left_turn_signal_active;
    bool right_turn_signal_active;
    bool hazard_active;
    uint8_t turn_signal_phase;  /* 0-100% for flashing */
    uint32_t last_toggle_ms;
} TurnSignalState_t;

typedef struct {
    HeadlightMode_t mode;
    uint8_t brightness_percent;
    bool high_beam_assist_active;
    bool adaptive_lighting_active;
} HeadlightState_t;

static TurnSignalState_t g_turn_signals = {0};
static HeadlightState_t g_headlights = {0};

void BCM_Lighting_Init(void) {
    /* Initialize PWM channels for LED control */
    PWM_Init(PWM_CHANNEL_LEFT_HEADLIGHT, PWM_FREQUENCY_HZ);
    PWM_Init(PWM_CHANNEL_RIGHT_HEADLIGHT, PWM_FREQUENCY_HZ);
    PWM_Init(PWM_CHANNEL_DOME_LIGHT, PWM_FREQUENCY_HZ);
    PWM_Init(PWM_CHANNEL_AMBIENT_LIGHT, PWM_FREQUENCY_HZ);

    /* Set initial state */
    g_headlights.mode = LIGHT_MODE_OFF;
    g_headlights.brightness_percent = 100;

    /* Load saved settings from EEPROM */
    NvM_ReadBlock(NVM_BLOCK_LIGHTING_SETTINGS, &g_headlights);
}

void BCM_TurnSignals_Update(void) {
    uint32_t current_time = GetSystemTime_ms();

    /* Flash at 1 Hz (500ms on, 500ms off) */
    if ((current_time - g_turn_signals.last_toggle_ms) > 500) {
        g_turn_signals.turn_signal_phase = (g_turn_signals.turn_signal_phase == 0) ? 100 : 0;
        g_turn_signals.last_toggle_ms = current_time;
    }

    /* Left turn signal */
    if (g_turn_signals.left_turn_signal_active || g_turn_signals.hazard_active) {
        PWM_SetDutyCycle(PWM_CHANNEL_LEFT_TURN_FRONT, g_turn_signals.turn_signal_phase);
        PWM_SetDutyCycle(PWM_CHANNEL_LEFT_TURN_REAR, g_turn_signals.turn_signal_phase);
    } else {
        PWM_SetDutyCycle(PWM_CHANNEL_LEFT_TURN_FRONT, 0);
        PWM_SetDutyCycle(PWM_CHANNEL_LEFT_TURN_REAR, 0);
    }

    /* Right turn signal */
    if (g_turn_signals.right_turn_signal_active || g_turn_signals.hazard_active) {
        PWM_SetDutyCycle(PWM_CHANNEL_RIGHT_TURN_FRONT, g_turn_signals.turn_signal_phase);
        PWM_SetDutyCycle(PWM_CHANNEL_RIGHT_TURN_REAR, g_turn_signals.turn_signal_phase);
    } else {
        PWM_SetDutyCycle(PWM_CHANNEL_RIGHT_TURN_FRONT, 0);
        PWM_SetDutyCycle(PWM_CHANNEL_RIGHT_TURN_REAR, 0);
    }
}

void BCM_Headlights_Update(void) {
    uint16_t ambient_light_lux = BCM_LightSensor_Read();

    switch (g_headlights.mode) {
        case LIGHT_MODE_OFF:
            PWM_SetDutyCycle(PWM_CHANNEL_LEFT_HEADLIGHT, 0);
            PWM_SetDutyCycle(PWM_CHANNEL_RIGHT_HEADLIGHT, 0);
            break;

        case LIGHT_MODE_PARKING:
            /* 20% brightness for parking lights */
            PWM_SetDutyCycle(PWM_CHANNEL_LEFT_HEADLIGHT, 20);
            PWM_SetDutyCycle(PWM_CHANNEL_RIGHT_HEADLIGHT, 20);
            break;

        case LIGHT_MODE_DAYTIME_RUNNING:
            /* 50% brightness for DRL */
            PWM_SetDutyCycle(PWM_CHANNEL_LEFT_HEADLIGHT, 50);
            PWM_SetDutyCycle(PWM_CHANNEL_RIGHT_HEADLIGHT, 50);
            break;

        case LIGHT_MODE_LOW_BEAM:
            PWM_SetDutyCycle(PWM_CHANNEL_LEFT_HEADLIGHT, g_headlights.brightness_percent);
            PWM_SetDutyCycle(PWM_CHANNEL_RIGHT_HEADLIGHT, g_headlights.brightness_percent);
            break;

        case LIGHT_MODE_HIGH_BEAM:
            /* Full brightness for high beam */
            PWM_SetDutyCycle(PWM_CHANNEL_LEFT_HEADLIGHT, 100);
            PWM_SetDutyCycle(PWM_CHANNEL_RIGHT_HEADLIGHT, 100);
            PWM_SetDutyCycle(PWM_CHANNEL_HIGH_BEAM, 100);
            break;

        case LIGHT_MODE_AUTO:
            /* Automatic headlight control based on ambient light */
            if (ambient_light_lux < AUTO_HEADLIGHT_THRESHOLD_LUX) {
                /* Dark: enable low beams */
                g_headlights.mode = LIGHT_MODE_LOW_BEAM;
            } else {
                /* Bright: enable DRL only */
                g_headlights.mode = LIGHT_MODE_DAYTIME_RUNNING;
            }
            break;
    }

    /* High beam assist: automatically switch to low beam when oncoming traffic detected */
    if (g_headlights.high_beam_assist_active && g_headlights.mode == LIGHT_MODE_HIGH_BEAM) {
        bool oncoming_detected = ADAS_Camera_DetectOncomingVehicle();
        if (oncoming_detected) {
            g_headlights.mode = LIGHT_MODE_LOW_BEAM;
        }
    }
}

/* Interior dome light with fade-in/fade-out */
void BCM_DomeLight_SetState(bool on, bool fade) {
    static uint8_t current_brightness = 0;
    uint8_t target_brightness = on ? 100 : 0;

    if (fade) {
        /* Fade gradually */
        while (current_brightness != target_brightness) {
            if (current_brightness < target_brightness) {
                current_brightness += DIM_STEP_PERCENT;
            } else {
                current_brightness -= DIM_STEP_PERCENT;
            }

            PWM_SetDutyCycle(PWM_CHANNEL_DOME_LIGHT, current_brightness);
            OsTask_Sleep(50);  /* 50ms steps for smooth fade */
        }
    } else {
        /* Immediate switch */
        current_brightness = target_brightness;
        PWM_SetDutyCycle(PWM_CHANNEL_DOME_LIGHT, current_brightness);
    }
}
```

### 2. Door Lock/Unlock and Keyless Entry
```c
/* bcm_door_control.c - Central locking and keyless entry */
#include "bcm_door_control.h"

#define KEYFOB_UNLOCK_TIMEOUT_MS 3000
#define AUTO_LOCK_SPEED_THRESHOLD_KPH 10
#define PASSIVE_ENTRY_RANGE_M 2.0

typedef enum {
    DOOR_FL = 0,
    DOOR_FR,
    DOOR_RL,
    DOOR_RR,
    DOOR_TRUNK,
    DOOR_COUNT
} DoorID_t;

typedef struct {
    bool locked;
    bool open;
    uint32_t last_lock_timestamp_ms;
} DoorState_t;

typedef struct {
    uint32_t keyfob_id;
    int8_t rssi_dbm;
    float distance_m;  /* Estimated from RSSI */
    bool authenticated;
} KeyFobState_t;

static DoorState_t g_doors[DOOR_COUNT] = {0};
static KeyFobState_t g_active_keyfob = {0};

void BCM_DoorControl_Init(void) {
    /* Initialize door lock actuators */
    for (int i = 0; i < DOOR_COUNT; i++) {
        GPIO_ConfigOutput(DOOR_LOCK_PINS[i]);
        g_doors[i].locked = true;
    }

    /* Initialize door open sensors (switches) */
    for (int i = 0; i < DOOR_COUNT; i++) {
        GPIO_ConfigInput(DOOR_SWITCH_PINS[i], GPIO_PULL_UP);
    }

    /* Initialize BLE for passive keyless entry */
    BLE_Init();
    BLE_StartAdvertising("VehicleKey");
}

void BCM_DoorControl_LockAll(void) {
    for (int i = 0; i < DOOR_COUNT; i++) {
        if (!g_doors[i].locked) {
            /* Activate lock actuator (pulse for 500ms) */
            GPIO_Set(DOOR_LOCK_PINS[i], true);
            OsTask_Sleep(500);
            GPIO_Set(DOOR_LOCK_PINS[i], false);

            g_doors[i].locked = true;
            g_doors[i].last_lock_timestamp_ms = GetSystemTime_ms();
        }
    }

    /* Chirp horn once to confirm lock */
    BCM_Horn_Chirp(1);

    /* Flash turn signals once */
    BCM_TurnSignals_Flash(1);
}

void BCM_DoorControl_UnlockAll(void) {
    /* Unlock driver door first (common in luxury vehicles) */
    BCM_DoorControl_UnlockSingle(DOOR_FL);

    /* Wait 2 seconds, then unlock all if button pressed again */
    uint32_t start_time = GetSystemTime_ms();
    while ((GetSystemTime_ms() - start_time) < 2000) {
        if (KeyFob_ButtonPressed(KEYFOB_BUTTON_UNLOCK)) {
            /* Second press: unlock all doors */
            for (int i = 0; i < DOOR_COUNT; i++) {
                BCM_DoorControl_UnlockSingle((DoorID_t)i);
            }
            break;
        }
        OsTask_Sleep(10);
    }

    /* Flash turn signals twice */
    BCM_TurnSignals_Flash(2);
}

void BCM_DoorControl_UnlockSingle(DoorID_t door) {
    if (g_doors[door].locked) {
        /* Activate unlock actuator */
        GPIO_Set(DOOR_UNLOCK_PINS[door], true);
        OsTask_Sleep(500);
        GPIO_Set(DOOR_UNLOCK_PINS[door], false);

        g_doors[door].locked = false;
    }
}

/* Passive keyless entry: unlock when approaching with authenticated key */
void BCM_PassiveEntry_Update(void) {
    /* Scan for BLE key fobs */
    if (BLE_ScanForDevice(g_active_keyfob.keyfob_id)) {
        g_active_keyfob.rssi_dbm = BLE_GetRSSI();

        /* Estimate distance from RSSI (simplified model) */
        g_active_keyfob.distance_m = pow(10, (-59 - g_active_keyfob.rssi_dbm) / (10 * 2.0));

        /* Authenticate key fob */
        if (!g_active_keyfob.authenticated) {
            uint8_t challenge[16];
            uint8_t response[16];

            BCM_Crypto_GenerateChallenge(challenge);
            BLE_SendChallenge(challenge);

            if (BLE_ReceiveResponse(response) &&
                BCM_Crypto_VerifyResponse(challenge, response)) {
                g_active_keyfob.authenticated = true;
            }
        }

        /* Unlock if authenticated and within range */
        if (g_active_keyfob.authenticated &&
            g_active_keyfob.distance_m < PASSIVE_ENTRY_RANGE_M) {
            /* Check if door handle touched (capacitive sensor) */
            if (GPIO_Read(DOOR_HANDLE_SENSOR_FL)) {
                BCM_DoorControl_UnlockSingle(DOOR_FL);
            }
        }
    }
}

/* Auto-lock when driving */
void BCM_AutoLock_Update(void) {
    uint16_t vehicle_speed = VCU_GetVehicleSpeed_kph();

    if (vehicle_speed > AUTO_LOCK_SPEED_THRESHOLD_KPH) {
        /* Vehicle is moving: auto-lock all doors */
        bool any_unlocked = false;
        for (int i = 0; i < DOOR_COUNT; i++) {
            if (!g_doors[i].locked) {
                any_unlocked = true;
                break;
            }
        }

        if (any_unlocked) {
            BCM_DoorControl_LockAll();
        }
    }
}
```

### 3. Window Control with Anti-Pinch
```c
/* bcm_window_control.c - Power window management with anti-pinch */
#include "bcm_window_control.h"

#define WINDOW_FL 0
#define WINDOW_FR 1
#define WINDOW_RL 2
#define WINDOW_RR 3
#define WINDOW_COUNT 4

#define ANTI_PINCH_FORCE_THRESHOLD_N 100
#define WINDOW_POSITION_SAMPLES 10

typedef enum {
    WINDOW_STATE_STOPPED = 0,
    WINDOW_STATE_MOVING_UP,
    WINDOW_STATE_MOVING_DOWN,
    WINDOW_STATE_PINCH_DETECTED
} WindowState_t;

typedef struct {
    WindowState_t state;
    uint8_t position_percent;  /* 0=closed, 100=fully open */
    uint16_t motor_current_ma;
    bool one_touch_up_active;
    bool one_touch_down_active;
} WindowControl_t;

static WindowControl_t g_windows[WINDOW_COUNT] = {0};

void BCM_WindowControl_Init(void) {
    /* Initialize window motor drivers (H-bridge) */
    for (int i = 0; i < WINDOW_COUNT; i++) {
        GPIO_ConfigOutput(WINDOW_MOTOR_UP_PINS[i]);
        GPIO_ConfigOutput(WINDOW_MOTOR_DOWN_PINS[i]);
    }

    /* Initialize window position sensors (Hall effect) */
    for (int i = 0; i < WINDOW_COUNT; i++) {
        ADC_ConfigChannel(WINDOW_POSITION_ADC_CHANNELS[i]);
    }

    /* Initialize current sensing for anti-pinch */
    for (int i = 0; i < WINDOW_COUNT; i++) {
        ADC_ConfigChannel(WINDOW_CURRENT_ADC_CHANNELS[i]);
    }
}

void BCM_Window_MoveUp(uint8_t window_id) {
    if (window_id >= WINDOW_COUNT) return;

    WindowControl_t* window = &g_windows[window_id];

    if (window->position_percent == 0) {
        return;  /* Already fully closed */
    }

    /* Activate motor upward */
    GPIO_Set(WINDOW_MOTOR_UP_PINS[window_id], true);
    GPIO_Set(WINDOW_MOTOR_DOWN_PINS[window_id], false);

    window->state = WINDOW_STATE_MOVING_UP;
}

void BCM_Window_MoveDown(uint8_t window_id) {
    if (window_id >= WINDOW_COUNT) return;

    WindowControl_t* window = &g_windows[window_id];

    if (window->position_percent == 100) {
        return;  /* Already fully open */
    }

    /* Activate motor downward */
    GPIO_Set(WINDOW_MOTOR_UP_PINS[window_id], false);
    GPIO_Set(WINDOW_MOTOR_DOWN_PINS[window_id], true);

    window->state = WINDOW_STATE_MOVING_DOWN;
}

void BCM_Window_Stop(uint8_t window_id) {
    if (window_id >= WINDOW_COUNT) return;

    /* Stop motor */
    GPIO_Set(WINDOW_MOTOR_UP_PINS[window_id], false);
    GPIO_Set(WINDOW_MOTOR_DOWN_PINS[window_id], false);

    g_windows[window_id].state = WINDOW_STATE_STOPPED;
}

/* Anti-pinch detection: monitor motor current during closing */
void BCM_Window_AntiPinchUpdate(uint8_t window_id) {
    WindowControl_t* window = &g_windows[window_id];

    if (window->state != WINDOW_STATE_MOVING_UP) {
        return;  /* Only check during closing */
    }

    /* Read motor current */
    uint16_t adc_value = ADC_Read(WINDOW_CURRENT_ADC_CHANNELS[window_id]);
    window->motor_current_ma = (adc_value * 5000) / 4096;  /* 12-bit ADC, 0-5A range */

    /* Detect excessive current (indicates obstruction) */
    if (window->motor_current_ma > ANTI_PINCH_FORCE_THRESHOLD_N) {
        /* Pinch detected: reverse window */
        window->state = WINDOW_STATE_PINCH_DETECTED;

        BCM_Window_Stop(window_id);
        OsTask_Sleep(100);

        /* Move down slightly to release obstruction */
        GPIO_Set(WINDOW_MOTOR_DOWN_PINS[window_id], true);
        OsTask_Sleep(500);
        GPIO_Set(WINDOW_MOTOR_DOWN_PINS[window_id], false);

        window->state = WINDOW_STATE_STOPPED;

        /* Log event */
        DTC_SetFault(DTC_WINDOW_ANTI_PINCH_TRIGGERED + window_id);
    }
}

/* One-touch up/down */
void BCM_Window_OneTouchUp(uint8_t window_id) {
    g_windows[window_id].one_touch_up_active = true;

    while (g_windows[window_id].position_percent > 0 &&
           g_windows[window_id].state != WINDOW_STATE_PINCH_DETECTED) {
        BCM_Window_MoveUp(window_id);
        BCM_Window_UpdatePosition(window_id);
        BCM_Window_AntiPinchUpdate(window_id);
        OsTask_Sleep(10);
    }

    BCM_Window_Stop(window_id);
    g_windows[window_id].one_touch_up_active = false;
}
```

### 4. LIN Bus Mastering (Door Modules)
```c
/* bcm_lin_master.c - LIN bus control for door modules */
#include "bcm_lin_master.h"

#define LIN_BAUDRATE 19200
#define LIN_BREAK_DURATION_US 750
#define LIN_FRAME_TIMEOUT_MS 50

typedef struct {
    uint8_t frame_id;
    uint8_t data[8];
    uint8_t length;
    uint8_t checksum;
} LINFrame_t;

/* Door module addresses */
#define LIN_DOOR_FL_ID 0x01
#define LIN_DOOR_FR_ID 0x02
#define LIN_DOOR_RL_ID 0x03
#define LIN_DOOR_RR_ID 0x04

void BCM_LIN_Init(void) {
    /* Configure UART for LIN */
    UART_Init(LIN_UART_PORT, LIN_BAUDRATE);
    UART_SetMode(LIN_UART_PORT, UART_MODE_LIN);
}

void BCM_LIN_SendBreak(void) {
    /* Generate LIN break field (dominant for 750µs) */
    GPIO_Set(LIN_TX_PIN, false);
    usleep(LIN_BREAK_DURATION_US);
    GPIO_Set(LIN_TX_PIN, true);
}

bool BCM_LIN_SendFrame(const LINFrame_t* frame) {
    /* Send break + sync byte + frame ID */
    BCM_LIN_SendBreak();
    UART_WriteByte(LIN_UART_PORT, 0x55);  /* Sync byte */
    UART_WriteByte(LIN_UART_PORT, frame->frame_id);

    /* Send data */
    for (int i = 0; i < frame->length; i++) {
        UART_WriteByte(LIN_UART_PORT, frame->data[i]);
    }

    /* Send checksum */
    UART_WriteByte(LIN_UART_PORT, frame->checksum);

    return true;
}

/* Command door module to lock/unlock */
void BCM_LIN_DoorLockCommand(uint8_t door_module_id, bool lock) {
    LINFrame_t frame;
    frame.frame_id = door_module_id;
    frame.length = 2;
    frame.data[0] = lock ? 0x01 : 0x02;  /* 0x01=lock, 0x02=unlock */
    frame.data[1] = 0x00;
    frame.checksum = BCM_LIN_CalculateChecksum(&frame);

    BCM_LIN_SendFrame(&frame);
}

/* Read door status from LIN module */
bool BCM_LIN_ReadDoorStatus(uint8_t door_module_id, bool* door_open, bool* window_position) {
    LINFrame_t request;
    request.frame_id = door_module_id | 0x40;  /* Read request */
    request.length = 0;
    request.checksum = BCM_LIN_CalculateChecksum(&request);

    BCM_LIN_SendFrame(&request);

    /* Wait for response */
    LINFrame_t response;
    if (BCM_LIN_ReceiveFrame(&response, LIN_FRAME_TIMEOUT_MS)) {
        *door_open = (response.data[0] & 0x01) != 0;
        *window_position = response.data[1];
        return true;
    }

    return false;
}
```

## BCM CAN Database (DBC)
```
VERSION ""

NS_ :

BS_:

BU_: BCM VCU IVI

/* BCM Lighting Status */
BO_ 512 BCM_LightingStatus: 8 BCM
 SG_ BCM_HeadlightMode : 0|8@1+ (0,0) [0|5] ""  IVI
 SG_ BCM_LeftTurnSignal : 8|1@1+ (0,0) [0|1] ""  VCU,IVI
 SG_ BCM_RightTurnSignal : 9|1@1+ (0,0) [0|1] ""  VCU,IVI
 SG_ BCM_HazardActive : 10|1@1+ (0,0) [0|1] ""  VCU,IVI
 SG_ BCM_HighBeamActive : 11|1@1+ (0,0) [0|1] ""  VCU,IVI
 SG_ BCM_BrakeLight : 12|1@1+ (0,0) [0|1] ""  VCU

/* BCM Door Status */
BO_ 513 BCM_DoorStatus: 8 BCM
 SG_ BCM_DoorLocked_FL : 0|1@1+ (0,0) [0|1] ""  IVI
 SG_ BCM_DoorLocked_FR : 1|1@1+ (0,0) [0|1] ""  IVI
 SG_ BCM_DoorLocked_RL : 2|1@1+ (0,0) [0|1] ""  IVI
 SG_ BCM_DoorLocked_RR : 3|1@1+ (0,0) [0|1] ""  IVI
 SG_ BCM_DoorOpen_FL : 8|1@1+ (0,0) [0|1] ""  VCU,IVI
 SG_ BCM_DoorOpen_FR : 9|1@1+ (0,0) [0|1] ""  VCU,IVI
 SG_ BCM_DoorOpen_RL : 10|1@1+ (0,0) [0|1] ""  VCU,IVI
 SG_ BCM_DoorOpen_RR : 11|1@1+ (0,0) [0|1] ""  VCU,IVI
 SG_ BCM_TrunkOpen : 12|1@1+ (0,0) [0|1] ""  VCU,IVI

VAL_ 512 BCM_HeadlightMode 0 "Off" 1 "Parking" 2 "DRL" 3 "LowBeam" 4 "HighBeam" 5 "Auto";
```

## References
- SAE J1850: Class B Data Communication Network Interface
- ISO 17987: Local Interconnect Network (LIN) Protocol
- IEC 60529: IP Rating (Ingress Protection)
- ECE R48: Installation of lighting devices

## Common Issues
- LIN bus communication errors due to incorrect timing
- Anti-pinch false triggers from motor current spikes
- Keyless entry authentication failures
- Door lock actuators jamming in cold weather
- PWM flicker at low brightness levels
