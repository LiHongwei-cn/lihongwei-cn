# Domain Controller Architecture - Next-Gen Vehicle E/E Architecture

## Overview
Domain Controller architecture centralizes ECU functions into fewer, more powerful computing platforms: Chassis Domain, Powertrain Domain, Body/Comfort Domain, ADAS Domain, with cross-domain communication via service-oriented architecture (SOA) and resource sharing.

## Domain Controller Concepts

### 1. Chassis Domain Controller
```c
/* chassis_domain_controller.c - Integrated chassis functions */
#include "chassis_domain.h"

/* Consolidated functions: ESC, ABS, TCS, EPS, ADAS braking */
typedef struct {
    /* Electronic Stability Control */
    bool esc_active;
    float yaw_rate_deg_s;
    float lateral_acceleration_g;

    /* Anti-lock Braking System */
    uint8_t wheel_speeds_kph[4];
    bool abs_active[4];

    /* Traction Control System */
    bool tcs_active;
    uint16_t tcs_torque_reduction_nm;

    /* Electric Power Steering */
    float steering_angle_deg;
    float steering_torque_nm;

    /* ADAS Braking Interface */
    bool adas_brake_request;
    float adas_decel_mps2;
} ChassisDomain_t;

static ChassisDomain_t g_chassis = {0};

void ChassisDomain_Main_10ms(void) {
    /* Read sensors from CAN/FlexRay */
    ChassisDomain_ReadSensors();

    /* ESC control loop */
    ChassisDomain_ESC_Update();

    /* ABS control per wheel */
    for (int i = 0; i < 4; i++) {
        ChassisDomain_ABS_UpdateWheel(i);
    }

    /* TCS integration with powertrain domain */
    if (g_chassis.tcs_active) {
        /* Send torque reduction request to powertrain domain */
        SOMEIP_SendRequest(POWERTRAIN_DOMAIN_SERVICE_ID,
                           METHOD_REDUCE_TORQUE,
                           &g_chassis.tcs_torque_reduction_nm,
                           sizeof(uint16_t));
    }

    /* ADAS brake arbitration */
    if (g_chassis.adas_brake_request) {
        ChassisDomain_ADAS_BrakeControl();
    }

    /* Publish chassis status to Ethernet backbone */
    ChassisDomain_PublishStatus();
}

void ChassisDomain_ESC_Update(void) {
    /* Read IMU (gyroscope + accelerometer) */
    float yaw_rate = IMU_GetYawRate();
    float lat_accel = IMU_GetLateralAcceleration();

    /* Calculate desired yaw rate from steering angle */
    float desired_yaw = (g_chassis.steering_angle_deg * VCU_GetVehicleSpeed_kph()) / 15.0;

    /* ESC intervention if yaw error exceeds threshold */
    float yaw_error = desired_yaw - yaw_rate;

    if (fabs(yaw_error) > 5.0) {
        g_chassis.esc_active = true;

        /* Apply differential braking to correct yaw */
        if (yaw_error > 0) {
            /* Understeer: brake inside rear wheel */
            ChassisDomain_ApplyBrake(WHEEL_RL, 30);
        } else {
            /* Oversteer: brake outside front wheel */
            ChassisDomain_ApplyBrake(WHEEL_FL, 30);
        }

        /* Reduce engine torque */
        SOMEIP_SendRequest(POWERTRAIN_DOMAIN_SERVICE_ID,
                           METHOD_REDUCE_TORQUE,
                           &(uint16_t){100}, 2);
    } else {
        g_chassis.esc_active = false;
    }
}
```

### 2. Powertrain Domain Controller
```c
/* powertrain_domain_controller.c - EV powertrain integration */
#include "powertrain_domain.h"

/* Consolidated: VCU, BMS, MCU functions */
typedef struct {
    /* Motor control */
    int16_t motor_torque_cmd_nm;
    uint16_t motor_speed_rpm;
    float motor_temperature_c;

    /* Battery management */
    float battery_soc_percent;
    uint16_t battery_voltage_v;
    float battery_current_a;

    /* Thermal management */
    bool cooling_pump_active;
    uint8_t radiator_fan_speed_percent;
} PowertrainDomain_t;

static PowertrainDomain_t g_powertrain = {0};

void PowertrainDomain_Main_10ms(void) {
    /* Motor control */
    PowertrainDomain_MotorControl();

    /* Battery management */
    PowertrainDomain_BMS_Update();

    /* Thermal management */
    PowertrainDomain_ThermalControl();

    /* Service-oriented communication */
    PowertrainDomain_HandleSOARequests();
}

void PowertrainDomain_HandleSOARequests(void) {
    /* Handle SOME/IP service requests from other domains */
    SOMEIP_Request_t req;

    if (SOMEIP_ReceiveRequest(&req)) {
        switch (req.method_id) {
            case METHOD_REDUCE_TORQUE: {
                uint16_t reduction_nm = *(uint16_t*)req.payload;
                g_powertrain.motor_torque_cmd_nm -= reduction_nm;

                /* Send response */
                SOMEIP_SendResponse(&req, RESPONSE_OK, NULL, 0);
                break;
            }

            case METHOD_GET_SOC: {
                uint8_t soc = (uint8_t)g_powertrain.battery_soc_percent;
                SOMEIP_SendResponse(&req, RESPONSE_OK, &soc, 1);
                break;
            }

            case METHOD_SET_CHARGING_LIMIT: {
                uint8_t limit_percent = *(uint8_t*)req.payload;
                PowertrainDomain_SetChargingLimit(limit_percent);
                SOMEIP_SendResponse(&req, RESPONSE_OK, NULL, 0);
                break;
            }
        }
    }
}
```

### 3. Body/Comfort Domain Controller
```c
/* body_domain_controller.c - Comfort and convenience functions */
#include "body_domain.h"

/* Consolidated: BCM, HVAC, seats, ambient lighting */
typedef struct {
    /* Climate control */
    float cabin_temperature_c;
    uint8_t hvac_fan_speed;
    bool ac_compressor_active;

    /* Lighting */
    HeadlightMode_t headlight_mode;
    uint8_t ambient_light_brightness;

    /* Seats */
    uint8_t driver_seat_heating_level;
    uint8_t passenger_seat_heating_level;
} BodyDomain_t;

static BodyDomain_t g_body = {0};

void BodyDomain_Main_50ms(void) {
    /* Climate control */
    BodyDomain_HVAC_Update();

    /* Lighting control */
    BodyDomain_Lighting_Update();

    /* Seat control */
    BodyDomain_Seats_Update();

    /* User preference synchronization (cloud) */
    BodyDomain_SyncUserPreferences();
}

void BodyDomain_SyncUserPreferences(void) {
    /* Load user profile from cloud (via TCU) */
    UserProfile_t profile;

    if (Cloud_GetUserProfile(g_authenticated_user_id, &profile)) {
        /* Apply preferences */
        g_body.driver_seat_heating_level = profile.seat_heat_pref;
        g_body.ambient_light_brightness = profile.ambient_light_pref;
        g_body.headlight_mode = profile.headlight_mode_pref;

        /* Adjust seat position (via LIN to seat ECU) */
        LIN_SendSeatPosition(profile.seat_position);
    }
}
```

### 4. ADAS Domain Controller
```c
/* adas_domain_controller.c - Perception, planning, control */
#include "adas_domain.h"

/* Consolidated: camera, radar, lidar fusion, path planning */
typedef struct {
    /* Perception */
    Object_t detected_objects[32];
    uint8_t object_count;

    /* Localization */
    float ego_position_x;
    float ego_position_y;
    float ego_heading_deg;

    /* Path planning */
    Trajectory_t planned_path;

    /* Control */
    float target_acceleration_mps2;
    float target_steering_angle_deg;
} ADASDomain_t;

static ADASDomain_t g_adas = {0};

void ADASDomain_Main_20ms(void) {
    /* Sensor fusion */
    ADASDomain_SensorFusion();

    /* Object detection and tracking */
    ADASDomain_ObjectTracking();

    /* Path planning */
    ADASDomain_PathPlanning();

    /* Send control commands to chassis/powertrain domains */
    ADASDomain_SendControlCommands();
}

void ADASDomain_SendControlCommands(void) {
    /* Request steering via chassis domain */
    SOMEIP_SendRequest(CHASSIS_DOMAIN_SERVICE_ID,
                       METHOD_SET_STEERING_ANGLE,
                       &g_adas.target_steering_angle_deg,
                       sizeof(float));

    /* Request acceleration via powertrain domain */
    if (g_adas.target_acceleration_mps2 > 0) {
        /* Acceleration */
        int16_t torque_nm = (int16_t)(g_adas.target_acceleration_mps2 * 50);
        SOMEIP_SendRequest(POWERTRAIN_DOMAIN_SERVICE_ID,
                           METHOD_SET_TORQUE,
                           &torque_nm,
                           sizeof(int16_t));
    } else {
        /* Braking */
        float decel_mps2 = -g_adas.target_acceleration_mps2;
        SOMEIP_SendRequest(CHASSIS_DOMAIN_SERVICE_ID,
                           METHOD_APPLY_BRAKE,
                           &decel_mps2,
                           sizeof(float));
    }
}
```

## Service-Oriented Architecture (SOME/IP)

### SOME/IP Service Definition (ARXML)
```xml
<!-- adas_services.arxml -->
<AUTOSAR>
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>ADAS_Services</SHORT-NAME>
      <ELEMENTS>
        <SOMEIP-SERVICE-INTERFACE>
          <SHORT-NAME>ADAS_Control_Service</SHORT-NAME>
          <SERVICE-INTERFACE-ID>0x1234</SERVICE-INTERFACE-ID>
          <MAJOR-VERSION>1</MAJOR-VERSION>
          <MINOR-VERSION>0</MINOR-VERSION>

          <METHODS>
            <SOMEIP-METHOD>
              <SHORT-NAME>SetSteeringAngle</SHORT-NAME>
              <METHOD-ID>0x0001</METHOD-ID>
              <CALL-SEMANTIC>REQUEST-RESPONSE</CALL-SEMANTIC>
            </SOMEIP-METHOD>
            <SOMEIP-METHOD>
              <SHORT-NAME>ApplyBrake</SHORT-NAME>
              <METHOD-ID>0x0002</METHOD-ID>
              <CALL-SEMANTIC>REQUEST-RESPONSE</CALL-SEMANTIC>
            </SOMEIP-METHOD>
          </METHODS>

          <EVENTS>
            <SOMEIP-EVENT>
              <SHORT-NAME>ObjectDetected</SHORT-NAME>
              <EVENT-ID>0x8001</EVENT-ID>
            </SOMEIP-EVENT>
          </EVENTS>
        </SOMEIP-SERVICE-INTERFACE>
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>
```

### Cross-Domain Communication Example
```c
/* domain_communication.c - SOME/IP client/server example */
#include "someip.h"

/* Client: ADAS domain requests torque from powertrain domain */
void ADAS_RequestTorque(int16_t torque_nm) {
    SOMEIP_Message_t msg;
    msg.service_id = POWERTRAIN_SERVICE_ID;
    msg.method_id = METHOD_SET_TORQUE;
    msg.client_id = ADAS_DOMAIN_CLIENT_ID;
    msg.session_id = GetNextSessionID();
    msg.payload_length = sizeof(int16_t);
    memcpy(msg.payload, &torque_nm, sizeof(int16_t));

    SOMEIP_Send(&msg);

    /* Wait for response */
    SOMEIP_Message_t response;
    if (SOMEIP_WaitForResponse(&response, 100)) {
        if (response.return_code == SOMEIP_RETURN_OK) {
            /* Request acknowledged */
        }
    }
}

/* Server: Powertrain domain handles torque request */
void Powertrain_SOMEIP_Handler(const SOMEIP_Message_t* request) {
    if (request->method_id == METHOD_SET_TORQUE) {
        int16_t requested_torque = *(int16_t*)request->payload;

        /* Apply safety limits */
        if (requested_torque > MAX_TORQUE_NM) {
            requested_torque = MAX_TORQUE_NM;
        }

        /* Set motor torque */
        VCU_SetMotorTorque(requested_torque);

        /* Send response */
        SOMEIP_Message_t response;
        response.service_id = request->service_id;
        response.method_id = request->method_id;
        response.client_id = request->client_id;
        response.session_id = request->session_id;
        response.return_code = SOMEIP_RETURN_OK;
        response.payload_length = 0;

        SOMEIP_Send(&response);
    }
}
```

## Resource Sharing and Timing

### Hypervisor-Based Domain Isolation
```c
/* hypervisor_config.h - QNX Hypervisor partition configuration */

/* Chassis Domain - Guest VM #1 */
#define CHASSIS_DOMAIN_RAM_BASE 0x80000000
#define CHASSIS_DOMAIN_RAM_SIZE 512MB
#define CHASSIS_DOMAIN_CPU_MASK 0x03  /* CPU 0-1 */
#define CHASSIS_DOMAIN_PRIORITY CRITICAL

/* Powertrain Domain - Guest VM #2 */
#define POWERTRAIN_DOMAIN_RAM_BASE 0xA0000000
#define POWERTRAIN_DOMAIN_RAM_SIZE 512MB
#define POWERTRAIN_DOMAIN_CPU_MASK 0x0C  /* CPU 2-3 */
#define POWERTRAIN_DOMAIN_PRIORITY CRITICAL

/* Body Domain - Guest VM #3 */
#define BODY_DOMAIN_RAM_BASE 0xC0000000
#define BODY_DOMAIN_RAM_SIZE 256MB
#define BODY_DOMAIN_CPU_MASK 0x10  /* CPU 4 */
#define BODY_DOMAIN_PRIORITY NORMAL

/* ADAS Domain - Guest VM #4 (highest compute) */
#define ADAS_DOMAIN_RAM_BASE 0xD0000000
#define ADAS_DOMAIN_RAM_SIZE 2GB
#define ADAS_DOMAIN_CPU_MASK 0xE0  /* CPU 5-7 */
#define ADAS_DOMAIN_PRIORITY HIGH
```

## Benefits of Domain Controller Architecture
- **Reduced wiring harness complexity**: Fewer ECUs = less copper
- **Centralized computing**: More powerful processors, better performance
- **OTA update efficiency**: Update entire domain instead of individual ECUs
- **Cost reduction**: Consolidation reduces hardware costs
- **Scalability**: Easier to add features without new ECUs

## References
- AUTOSAR Adaptive Platform R22-11
- SOME/IP Protocol Specification v1.3
- QNX Hypervisor for Automotive
- ISO 21434: Road Vehicles - Cybersecurity Engineering
- ASAM OpenX: Service-Oriented Communication

## Common Issues
- Inter-domain latency exceeding real-time requirements
- Resource contention between domains on shared CPU cores
- SOME/IP service discovery failures
- Hypervisor overhead impacting deterministic timing
- Cross-domain debugging complexity
