# VGU (Vehicle Gateway Unit) - Network Routing and Security

## Overview
The Vehicle Gateway Unit (VGU) acts as the central network hub, routing messages between different vehicle networks (CAN-to-Ethernet, CAN-to-CAN), implementing security firewalls, handling diagnostic access (DoIP), and managing network wake-up. This skill covers production-ready gateway development with AUTOSAR COM stack.

## Core Responsibilities

### 1. Network Routing (CAN-to-Ethernet, CAN-to-CAN)
```c
/* vgu_routing_engine.c - Multi-network message routing */
#include "vgu_routing_engine.h"
#include "Com.h"
#include "PduR.h"
#include <stdint.h>
#include <stdbool.h>

#define MAX_ROUTING_ENTRIES 256
#define MAX_NETWORKS 8

typedef enum {
    NETWORK_CAN_POWERTRAIN = 0,
    NETWORK_CAN_CHASSIS,
    NETWORK_CAN_BODY,
    NETWORK_CAN_INFOTAINMENT,
    NETWORK_ETH_BACKBONE,
    NETWORK_LIN_DOOR,
    NETWORK_FLEXRAY_ADAS,
    NETWORK_INVALID
} NetworkID_t;

typedef enum {
    ROUTING_MODE_UNCONDITIONAL,  /* Always route */
    ROUTING_MODE_CONDITIONAL,    /* Route based on vehicle mode */
    ROUTING_MODE_FILTERED,       /* Apply gateway filter */
    ROUTING_MODE_BLOCKED         /* Never route (security) */
} RoutingMode_t;

typedef struct {
    uint32_t source_pdu_id;
    NetworkID_t source_network;
    uint32_t dest_pdu_id;
    NetworkID_t dest_network;
    RoutingMode_t routing_mode;
    uint16_t cycle_time_ms;       /* For cyclic routing */
    bool transform_required;      /* Endianness/scaling conversion */
    uint32_t route_count;         /* Statistics */
} RoutingEntry_t;

static RoutingEntry_t g_routing_table[MAX_ROUTING_ENTRIES];
static uint16_t g_routing_table_size = 0;

/* Example routing table configuration */
static const RoutingEntry_t DEFAULT_ROUTING_TABLE[] = {
    /* VCU Motor Command: CAN Powertrain -> Ethernet Backbone */
    {
        .source_pdu_id = 0x100,
        .source_network = NETWORK_CAN_POWERTRAIN,
        .dest_pdu_id = 0x100,
        .dest_network = NETWORK_ETH_BACKBONE,
        .routing_mode = ROUTING_MODE_UNCONDITIONAL,
        .cycle_time_ms = 10,
        .transform_required = false
    },
    /* BMS Battery Status: CAN Powertrain -> CAN Infotainment (for display) */
    {
        .source_pdu_id = 0x300,
        .source_network = NETWORK_CAN_POWERTRAIN,
        .dest_pdu_id = 0x300,
        .dest_network = NETWORK_CAN_INFOTAINMENT,
        .routing_mode = ROUTING_MODE_FILTERED,
        .cycle_time_ms = 100,
        .transform_required = false
    },
    /* IVI User Input: CAN Infotainment -> Ethernet Backbone (blocked in drive) */
    {
        .source_pdu_id = 0x400,
        .source_network = NETWORK_CAN_INFOTAINMENT,
        .dest_pdu_id = 0x400,
        .dest_network = NETWORK_ETH_BACKBONE,
        .routing_mode = ROUTING_MODE_CONDITIONAL,
        .cycle_time_ms = 50,
        .transform_required = false
    },
    /* ADAS Camera: Ethernet -> CAN Chassis (lane keeping) */
    {
        .source_pdu_id = 0x500,
        .source_network = NETWORK_ETH_BACKBONE,
        .dest_pdu_id = 0x500,
        .dest_network = NETWORK_CAN_CHASSIS,
        .routing_mode = ROUTING_MODE_UNCONDITIONAL,
        .cycle_time_ms = 20,
        .transform_required = true  /* SOME/IP to CAN conversion */
    }
};

void VGU_RoutingEngine_Init(void) {
    /* Load default routing table */
    g_routing_table_size = sizeof(DEFAULT_ROUTING_TABLE) / sizeof(RoutingEntry_t);
    memcpy(g_routing_table, DEFAULT_ROUTING_TABLE, sizeof(DEFAULT_ROUTING_TABLE));

    /* Initialize network interfaces */
    for (int i = 0; i < MAX_NETWORKS; i++) {
        VGU_Network_Init((NetworkID_t)i);
    }

    /* Load routing table from NVM if available */
    NvM_ReadBlock(NVM_BLOCK_ROUTING_TABLE, g_routing_table);
}

Std_ReturnType VGU_RouteMessage(uint32_t source_pdu_id,
                                 NetworkID_t source_network,
                                 const uint8_t* data,
                                 uint8_t length) {
    /* Find routing entry */
    for (uint16_t i = 0; i < g_routing_table_size; i++) {
        RoutingEntry_t* entry = &g_routing_table[i];

        if (entry->source_pdu_id == source_pdu_id &&
            entry->source_network == source_network) {

            /* Check routing mode */
            if (!VGU_RoutingAllowed(entry)) {
                return E_NOT_OK;
            }

            /* Apply security filter */
            if (!VGU_SecurityFilter_Check(entry, data, length)) {
                VGU_SecurityEvent_Log(SECURITY_EVENT_FILTER_REJECT, source_pdu_id);
                return E_NOT_OK;
            }

            /* Transform if required */
            uint8_t transformed_data[64];
            uint8_t transformed_length = length;

            if (entry->transform_required) {
                VGU_DataTransform(data, length, transformed_data,
                                   &transformed_length, entry);
            } else {
                memcpy(transformed_data, data, length);
            }

            /* Route to destination network */
            Std_ReturnType result = VGU_Network_Transmit(
                entry->dest_network,
                entry->dest_pdu_id,
                transformed_data,
                transformed_length);

            if (result == E_OK) {
                entry->route_count++;
            }

            return result;
        }
    }

    /* No routing entry found */
    return E_NOT_OK;
}

bool VGU_RoutingAllowed(const RoutingEntry_t* entry) {
    switch (entry->routing_mode) {
        case ROUTING_MODE_UNCONDITIONAL:
            return true;

        case ROUTING_MODE_CONDITIONAL:
            /* Example: block IVI messages when vehicle is driving */
            if (entry->source_network == NETWORK_CAN_INFOTAINMENT) {
                uint16_t vehicle_speed = VCU_GetVehicleSpeed_kph();
                return (vehicle_speed < 5);  /* Only allow when stopped */
            }
            return true;

        case ROUTING_MODE_FILTERED:
            /* Additional filtering logic */
            return true;

        case ROUTING_MODE_BLOCKED:
            return false;

        default:
            return false;
    }
}

/* CAN-to-Ethernet transformation (CAN frame -> SOME/IP) */
void VGU_DataTransform_CANtoETH(const uint8_t* can_data, uint8_t can_length,
                                 uint8_t* eth_data, uint8_t* eth_length) {
    /* SOME/IP header: Service ID, Method ID, Length, Client ID, Session ID, ... */
    uint16_t service_id = 0x1234;
    uint16_t method_id = 0x0001;

    /* Build SOME/IP message */
    eth_data[0] = (service_id >> 8) & 0xFF;
    eth_data[1] = service_id & 0xFF;
    eth_data[2] = (method_id >> 8) & 0xFF;
    eth_data[3] = method_id & 0xFF;

    /* Length field */
    uint32_t payload_length = can_length + 8;  /* Payload + SOME/IP overhead */
    eth_data[4] = (payload_length >> 24) & 0xFF;
    eth_data[5] = (payload_length >> 16) & 0xFF;
    eth_data[6] = (payload_length >> 8) & 0xFF;
    eth_data[7] = payload_length & 0xFF;

    /* Copy CAN payload */
    memcpy(&eth_data[16], can_data, can_length);

    *eth_length = 16 + can_length;
}
```

### 2. Security Firewall
```c
/* vgu_security_firewall.c - Message filtering and intrusion detection */
#include "vgu_security_firewall.h"

#define MAX_FIREWALL_RULES 128
#define MAX_ALLOWED_CAN_IDS 512
#define ANOMALY_THRESHOLD 10

typedef enum {
    FIREWALL_ACTION_ALLOW = 0,
    FIREWALL_ACTION_BLOCK,
    FIREWALL_ACTION_LOG,
    FIREWALL_ACTION_ALERT
} FirewallAction_t;

typedef struct {
    uint32_t can_id;
    NetworkID_t network;
    FirewallAction_t action;
    uint32_t min_cycle_time_ms;  /* Minimum expected cycle time */
    uint32_t max_cycle_time_ms;  /* Maximum expected cycle time */
    uint8_t expected_dlc;
    bool require_authentication;
} FirewallRule_t;

typedef struct {
    uint32_t can_id;
    uint32_t last_rx_timestamp_ms;
    uint32_t rx_count;
    uint32_t anomaly_count;
} MessageMonitor_t;

static FirewallRule_t g_firewall_rules[MAX_FIREWALL_RULES];
static MessageMonitor_t g_message_monitors[MAX_ALLOWED_CAN_IDS];

/* Example firewall rules */
static const FirewallRule_t DEFAULT_FIREWALL_RULES[] = {
    /* VCU Motor Command: strict timing, authenticated */
    {
        .can_id = 0x100,
        .network = NETWORK_CAN_POWERTRAIN,
        .action = FIREWALL_ACTION_ALLOW,
        .min_cycle_time_ms = 8,
        .max_cycle_time_ms = 12,
        .expected_dlc = 8,
        .require_authentication = true
    },
    /* BMS Battery Status: allow with timing check */
    {
        .can_id = 0x300,
        .network = NETWORK_CAN_POWERTRAIN,
        .action = FIREWALL_ACTION_ALLOW,
        .min_cycle_time_ms = 90,
        .max_cycle_time_ms = 110,
        .expected_dlc = 8,
        .require_authentication = false
    },
    /* Diagnostic request: block unless diagnostic session active */
    {
        .can_id = 0x7DF,  /* OBD-II diagnostic request */
        .network = NETWORK_CAN_POWERTRAIN,
        .action = FIREWALL_ACTION_LOG,
        .min_cycle_time_ms = 0,
        .max_cycle_time_ms = 0xFFFFFFFF,
        .expected_dlc = 8,
        .require_authentication = true
    },
    /* Unknown high-priority CAN ID: block and alert */
    {
        .can_id = 0x000,  /* High priority range 0x000-0x0FF */
        .network = NETWORK_CAN_POWERTRAIN,
        .action = FIREWALL_ACTION_BLOCK,
        .min_cycle_time_ms = 0,
        .max_cycle_time_ms = 0xFFFFFFFF,
        .expected_dlc = 0,
        .require_authentication = false
    }
};

void VGU_SecurityFirewall_Init(void) {
    memcpy(g_firewall_rules, DEFAULT_FIREWALL_RULES, sizeof(DEFAULT_FIREWALL_RULES));
    memset(g_message_monitors, 0, sizeof(g_message_monitors));
}

bool VGU_SecurityFilter_Check(const RoutingEntry_t* route,
                               const uint8_t* data,
                               uint8_t length) {
    uint32_t can_id = route->source_pdu_id;
    uint32_t current_time_ms = GetSystemTime_ms();

    /* Find firewall rule */
    FirewallRule_t* rule = NULL;
    for (int i = 0; i < MAX_FIREWALL_RULES; i++) {
        if (g_firewall_rules[i].can_id == can_id &&
            g_firewall_rules[i].network == route->source_network) {
            rule = &g_firewall_rules[i];
            break;
        }
    }

    if (rule == NULL) {
        /* No rule defined: default deny */
        return false;
    }

    /* Check DLC */
    if (rule->expected_dlc > 0 && length != rule->expected_dlc) {
        VGU_SecurityEvent_Log(SECURITY_EVENT_DLC_MISMATCH, can_id);
        return false;
    }

    /* Find message monitor entry */
    MessageMonitor_t* monitor = NULL;
    for (int i = 0; i < MAX_ALLOWED_CAN_IDS; i++) {
        if (g_message_monitors[i].can_id == can_id) {
            monitor = &g_message_monitors[i];
            break;
        } else if (g_message_monitors[i].can_id == 0) {
            /* Create new monitor entry */
            monitor = &g_message_monitors[i];
            monitor->can_id = can_id;
            break;
        }
    }

    if (monitor != NULL) {
        /* Check cycle time */
        if (monitor->last_rx_timestamp_ms > 0) {
            uint32_t delta_ms = current_time_ms - monitor->last_rx_timestamp_ms;

            if (delta_ms < rule->min_cycle_time_ms ||
                delta_ms > rule->max_cycle_time_ms) {
                monitor->anomaly_count++;

                if (monitor->anomaly_count > ANOMALY_THRESHOLD) {
                    VGU_SecurityEvent_Log(SECURITY_EVENT_TIMING_VIOLATION, can_id);
                    /* Don't block, but alert */
                }
            } else {
                /* Reset anomaly counter on valid timing */
                if (monitor->anomaly_count > 0) {
                    monitor->anomaly_count--;
                }
            }
        }

        monitor->last_rx_timestamp_ms = current_time_ms;
        monitor->rx_count++;
    }

    /* Check authentication if required */
    if (rule->require_authentication) {
        if (!VGU_Security_VerifyMAC(data, length)) {
            VGU_SecurityEvent_Log(SECURITY_EVENT_AUTH_FAIL, can_id);
            return false;
        }
    }

    /* Apply firewall action */
    switch (rule->action) {
        case FIREWALL_ACTION_ALLOW:
            return true;

        case FIREWALL_ACTION_BLOCK:
            VGU_SecurityEvent_Log(SECURITY_EVENT_BLOCKED, can_id);
            return false;

        case FIREWALL_ACTION_LOG:
            VGU_SecurityEvent_Log(SECURITY_EVENT_LOGGED, can_id);
            return true;

        case FIREWALL_ACTION_ALERT:
            VGU_SecurityEvent_Log(SECURITY_EVENT_ALERT, can_id);
            return true;

        default:
            return false;
    }
}

/* SecOC (Secure Onboard Communication) - MAC verification */
bool VGU_Security_VerifyMAC(const uint8_t* data, uint8_t length) {
    /* Extract MAC from last 8 bytes */
    uint64_t received_mac = 0;
    for (int i = 0; i < 8; i++) {
        received_mac = (received_mac << 8) | data[length - 8 + i];
    }

    /* Calculate expected MAC using CMAC-AES */
    uint64_t calculated_mac = VGU_Crypto_CalculateMAC(data, length - 8);

    return (received_mac == calculated_mac);
}
```

### 3. Diagnostic Gateway (DoIP - Diagnostics over IP)
```c
/* vgu_doip_gateway.c - ISO 13400 Diagnostic over IP */
#include "vgu_doip_gateway.h"

#define DOIP_UDP_PORT 13400
#define DOIP_TCP_PORT 13400
#define MAX_DOIP_CONNECTIONS 4

typedef enum {
    DOIP_VEHICLE_ANNOUNCEMENT = 0x0004,
    DOIP_ROUTING_ACTIVATION_REQUEST = 0x0005,
    DOIP_ROUTING_ACTIVATION_RESPONSE = 0x0006,
    DOIP_DIAGNOSTIC_MESSAGE = 0x8001,
    DOIP_DIAGNOSTIC_MESSAGE_ACK = 0x8002,
    DOIP_DIAGNOSTIC_MESSAGE_NACK = 0x8003
} DoIPMessageType_t;

typedef struct {
    uint8_t protocol_version;
    uint8_t inverse_protocol_version;
    uint16_t payload_type;
    uint32_t payload_length;
} DoIPHeader_t;

typedef struct {
    int socket_fd;
    bool active;
    uint16_t source_address;
    uint16_t target_address;
    uint8_t activation_type;
    uint32_t last_activity_ms;
} DoIPConnection_t;

static DoIPConnection_t g_doip_connections[MAX_DOIP_CONNECTIONS];

void VGU_DoIP_Init(void) {
    /* Create UDP socket for vehicle announcement */
    int udp_socket = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(DOIP_UDP_PORT),
        .sin_addr.s_addr = INADDR_ANY
    };
    bind(udp_socket, (struct sockaddr*)&addr, sizeof(addr));

    /* Create TCP socket for diagnostic communication */
    int tcp_socket = socket(AF_INET, SOCK_STREAM, 0);
    bind(tcp_socket, (struct sockaddr*)&addr, sizeof(addr));
    listen(tcp_socket, MAX_DOIP_CONNECTIONS);

    /* Send periodic vehicle announcement */
    VGU_DoIP_SendVehicleAnnouncement(udp_socket);
}

void VGU_DoIP_SendVehicleAnnouncement(int udp_socket) {
    uint8_t announcement[32];
    DoIPHeader_t* header = (DoIPHeader_t*)announcement;

    header->protocol_version = 0x02;  /* ISO 13400-2:2012 */
    header->inverse_protocol_version = 0xFD;
    header->payload_type = htons(DOIP_VEHICLE_ANNOUNCEMENT);
    header->payload_length = htonl(14);

    /* Payload: VIN (17 bytes) + Logical Address (2 bytes) + EID (6 bytes) + GID (6 bytes) */
    const char* vin = "1HGBH41JXMN109186";
    memcpy(&announcement[8], vin, 17);

    uint16_t logical_address = 0x0001;  /* Gateway address */
    memcpy(&announcement[25], &logical_address, 2);

    /* Broadcast announcement */
    struct sockaddr_in broadcast_addr = {
        .sin_family = AF_INET,
        .sin_port = htons(DOIP_UDP_PORT),
        .sin_addr.s_addr = htonl(INADDR_BROADCAST)
    };
    sendto(udp_socket, announcement, 32, 0,
           (struct sockaddr*)&broadcast_addr, sizeof(broadcast_addr));
}

void VGU_DoIP_HandleRoutingActivation(int tcp_socket,
                                       const uint8_t* request,
                                       uint16_t length) {
    /* Parse routing activation request */
    uint16_t source_address = (request[8] << 8) | request[9];
    uint8_t activation_type = request[10];

    /* Find available connection slot */
    DoIPConnection_t* conn = NULL;
    for (int i = 0; i < MAX_DOIP_CONNECTIONS; i++) {
        if (!g_doip_connections[i].active) {
            conn = &g_doip_connections[i];
            break;
        }
    }

    uint8_t response_code;
    if (conn != NULL) {
        conn->socket_fd = tcp_socket;
        conn->active = true;
        conn->source_address = source_address;
        conn->activation_type = activation_type;
        conn->last_activity_ms = GetSystemTime_ms();

        response_code = 0x10;  /* Routing successfully activated */
    } else {
        response_code = 0x02;  /* All sockets in use */
    }

    /* Send routing activation response */
    uint8_t response[13];
    DoIPHeader_t* header = (DoIPHeader_t*)response;
    header->protocol_version = 0x02;
    header->inverse_protocol_version = 0xFD;
    header->payload_type = htons(DOIP_ROUTING_ACTIVATION_RESPONSE);
    header->payload_length = htonl(5);

    response[8] = (source_address >> 8) & 0xFF;
    response[9] = source_address & 0xFF;
    response[10] = 0x00;  /* Logical address of gateway */
    response[11] = 0x01;
    response[12] = response_code;

    send(tcp_socket, response, 13, 0);
}

void VGU_DoIP_RouteDiagnosticMessage(const uint8_t* doip_message, uint16_t length) {
    /* Extract source and target addresses */
    uint16_t source_addr = (doip_message[8] << 8) | doip_message[9];
    uint16_t target_addr = (doip_message[10] << 8) | doip_message[11];

    /* Extract UDS payload */
    const uint8_t* uds_payload = &doip_message[12];
    uint16_t uds_length = length - 12;

    /* Route to target ECU based on logical address */
    NetworkID_t target_network;
    uint32_t target_can_id;

    switch (target_addr) {
        case 0x0010:  /* VCU */
            target_network = NETWORK_CAN_POWERTRAIN;
            target_can_id = 0x7E0;  /* VCU diagnostic address */
            break;
        case 0x0020:  /* BMS */
            target_network = NETWORK_CAN_POWERTRAIN;
            target_can_id = 0x7E1;
            break;
        case 0x0030:  /* MCU */
            target_network = NETWORK_CAN_POWERTRAIN;
            target_can_id = 0x7E2;
            break;
        default:
            /* Unknown target */
            return;
    }

    /* Send diagnostic request over CAN */
    VGU_Network_Transmit(target_network, target_can_id, uds_payload, uds_length);
}
```

### 4. Gateway Wake-Up Management
```c
/* vgu_wakeup_management.c - Network wake-up and power management */
#include "vgu_wakeup_management.h"

typedef enum {
    WAKEUP_SOURCE_CAN_POWERTRAIN = 0,
    WAKEUP_SOURCE_CAN_CHASSIS,
    WAKEUP_SOURCE_LIN_DOOR,
    WAKEUP_SOURCE_ETHERNET,
    WAKEUP_SOURCE_TIMER,
    WAKEUP_SOURCE_IGNITION,
    WAKEUP_SOURCE_COUNT
} WakeupSource_t;

typedef struct {
    bool wakeup_enabled[WAKEUP_SOURCE_COUNT];
    WakeupSource_t last_wakeup_source;
    uint32_t wakeup_timestamp_ms;
} WakeupState_t;

static WakeupState_t g_wakeup_state = {0};

void VGU_WakeupManagement_Init(void) {
    /* Enable relevant wakeup sources */
    g_wakeup_state.wakeup_enabled[WAKEUP_SOURCE_CAN_POWERTRAIN] = true;
    g_wakeup_state.wakeup_enabled[WAKEUP_SOURCE_LIN_DOOR] = true;
    g_wakeup_state.wakeup_enabled[WAKEUP_SOURCE_IGNITION] = true;

    /* Configure CAN transceivers for selective wake-up */
    CanTrcv_SetOpMode(CAN_POWERTRAIN, CANTRCV_WUMODE_ENABLE);
    CanTrcv_SetOpMode(CAN_CHASSIS, CANTRCV_WUMODE_ENABLE);
}

void VGU_WakeupManagement_OnWakeup(WakeupSource_t source) {
    g_wakeup_state.last_wakeup_source = source;
    g_wakeup_state.wakeup_timestamp_ms = GetSystemTime_ms();

    /* Notify EcuM of wakeup event */
    EcuM_SetWakeupEvent((EcuM_WakeupSourceType)(1 << source));

    /* Start network initialization sequence based on wakeup source */
    switch (source) {
        case WAKEUP_SOURCE_CAN_POWERTRAIN:
            /* High-priority startup: VCU, BMS, MCU needed */
            VGU_Network_Start(NETWORK_CAN_POWERTRAIN);
            VGU_Network_Start(NETWORK_CAN_CHASSIS);
            break;

        case WAKEUP_SOURCE_LIN_DOOR:
            /* Body network startup: BCM, door modules */
            VGU_Network_Start(NETWORK_CAN_BODY);
            VGU_Network_Start(NETWORK_LIN_DOOR);
            break;

        case WAKEUP_SOURCE_IGNITION:
            /* Full network startup */
            for (NetworkID_t net = 0; net < NETWORK_INVALID; net++) {
                VGU_Network_Start(net);
            }
            break;

        default:
            break;
    }
}

void VGU_WakeupManagement_EnterSleep(void) {
    /* Shutdown sequence: least critical networks first */
    VGU_Network_Stop(NETWORK_CAN_INFOTAINMENT);
    VGU_Network_Stop(NETWORK_CAN_BODY);

    /* Wait for pending transmissions */
    while (VGU_Network_HasPendingTx(NETWORK_CAN_CHASSIS)) {
        OsTask_Sleep(10);
    }

    VGU_Network_Stop(NETWORK_CAN_CHASSIS);

    /* Powertrain network last (safety-critical) */
    VGU_Network_Stop(NETWORK_CAN_POWERTRAIN);

    /* Configure transceivers for wake-up */
    CanTrcv_SetOpMode(CAN_POWERTRAIN, CANTRCV_WUMODE_ENABLE);

    /* Enter low-power mode */
    Mcu_SetMode(MCU_MODE_SLEEP);
}
```

## AUTOSAR COM Stack Configuration

### Gateway PDU Router (ARXML)
```xml
<!-- vgu_pdur_configuration.arxml -->
<AUTOSAR xmlns="http://autosar.org/schema/r4.0">
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>PduR_RoutingTables</SHORT-NAME>
      <ELEMENTS>
        <PDU-R-ROUTING-TABLE>
          <SHORT-NAME>VGU_RoutingTable</SHORT-NAME>
          <ROUTING-PATHS>
            <!-- CAN Powertrain -> Ethernet Backbone -->
            <PDU-R-ROUTING-PATH>
              <SHORT-NAME>VCU_MotorCmd_CANtoETH</SHORT-NAME>
              <PDU-R-SOURCE-PDU-REF DEST="I-PDU">
                /CAN_Powertrain/VCU_MotorCmd
              </PDU-R-SOURCE-PDU-REF>
              <PDU-R-DESTINATION-PDU-REF DEST="I-PDU">
                /ETH_Backbone/VCU_MotorCmd_ETH
              </PDU-R-DESTINATION-PDU-REF>
              <PDU-R-DEFAULT-VALUE>0</PDU-R-DEFAULT-VALUE>
            </PDU-R-ROUTING-PATH>

            <!-- Ethernet -> CAN Chassis (ADAS commands) -->
            <PDU-R-ROUTING-PATH>
              <SHORT-NAME>ADAS_SteeringCmd_ETHtoGAN</SHORT-NAME>
              <PDU-R-SOURCE-PDU-REF DEST="I-PDU">
                /ETH_Backbone/ADAS_SteeringCmd
              </PDU-R-SOURCE-PDU-REF>
              <PDU-R-DESTINATION-PDU-REF DEST="I-PDU">
                /CAN_Chassis/ADAS_SteeringCmd_CAN
              </PDU-R-DESTINATION-PDU-REF>
              <PDU-R-DEFAULT-VALUE>0</PDU-R-DEFAULT-VALUE>
            </PDU-R-ROUTING-PATH>
          </ROUTING-PATHS>
        </PDU-R-ROUTING-TABLE>
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>
```

## VGU Network Configuration (DBC)
```
VERSION ""

NS_ :

BS_:

BU_: VGU VCU BMS MCU BCM IVI

/* Gateway Status Message */
BO_ 1024 VGU_Status: 8 VGU
 SG_ VGU_NetworkStatus_Powertrain : 0|2@1+ (0,0) [0|3] ""  VCU,BMS,MCU
 SG_ VGU_NetworkStatus_Chassis : 2|2@1+ (0,0) [0|3] ""  BCM
 SG_ VGU_NetworkStatus_Body : 4|2@1+ (0,0) [0|3] ""  BCM
 SG_ VGU_NetworkStatus_Infotainment : 6|2@1+ (0,0) [0|3] ""  IVI
 SG_ VGU_NetworkStatus_Ethernet : 8|2@1+ (0,0) [0|3] ""  VCU,IVI
 SG_ VGU_RoutingActive : 10|1@1+ (0,0) [0|1] ""  ALL
 SG_ VGU_FirewallActive : 11|1@1+ (0,0) [0|1] ""  ALL
 SG_ VGU_DiagnosticSessionActive : 12|1@1+ (0,0) [0|1] ""  ALL
 SG_ VGU_SecurityAnomalyCount : 16|16@1+ (0,0) [0|65535] ""  ALL
 SG_ VGU_RoutedMessageCount : 32|32@1+ (0,0) [0|4294967295] ""  ALL

VAL_ 1024 VGU_NetworkStatus_Powertrain 0 "Offline" 1 "Initializing" 2 "Active" 3 "Error";
VAL_ 1024 VGU_NetworkStatus_Chassis 0 "Offline" 1 "Initializing" 2 "Active" 3 "Error";
VAL_ 1024 VGU_NetworkStatus_Body 0 "Offline" 1 "Initializing" 2 "Active" 3 "Error";
VAL_ 1024 VGU_NetworkStatus_Infotainment 0 "Offline" 1 "Initializing" 2 "Active" 3 "Error";
VAL_ 1024 VGU_NetworkStatus_Ethernet 0 "Offline" 1 "Initializing" 2 "Active" 3 "Error";
```

## Testing Requirements

### Gateway HIL Test
```python
# vgu_hil_test.py - Hardware-in-the-Loop testing for VGU
import can
import socket
import pytest

class TestVGURouting:
    def test_can_to_ethernet_routing(self, vgu_hil):
        """Verify CAN message is routed to Ethernet"""
        # Send VCU_MotorCmd on CAN Powertrain
        can_msg = can.Message(arbitration_id=0x100,
                               data=[0x64, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0xAB],
                               is_extended_id=False)
        vgu_hil.can_powertrain.send(can_msg)

        # Verify message appears on Ethernet backbone (SOME/IP)
        eth_packet = vgu_hil.eth_backbone.recv(timeout=0.1)
        assert eth_packet is not None
        assert eth_packet[0:2] == b'\x12\x34'  # Service ID

    def test_security_firewall_blocks_invalid_dlc(self, vgu_hil):
        """Verify firewall blocks message with wrong DLC"""
        # Send message with incorrect DLC
        invalid_msg = can.Message(arbitration_id=0x100,
                                   data=[0x64, 0x00],  # DLC=2, expected=8
                                   is_extended_id=False)
        vgu_hil.can_powertrain.send(invalid_msg)

        # Verify VGU logs security event
        security_log = vgu_hil.read_can_message(0x400, timeout=0.1)
        assert security_log.data[0] == 0x01  # DLC_MISMATCH event

        # Verify message NOT routed to Ethernet
        eth_packet = vgu_hil.eth_backbone.recv(timeout=0.1)
        assert eth_packet is None

    def test_doip_routing_activation(self, vgu_hil):
        """Verify DoIP routing activation over TCP"""
        # Connect to DoIP port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("192.168.1.100", 13400))

        # Send routing activation request
        activation_request = bytes([
            0x02, 0xFD,  # Protocol version
            0x00, 0x05,  # Payload type: Routing Activation Request
            0x00, 0x00, 0x00, 0x07,  # Payload length
            0x0E, 0x80,  # Source address (tester)
            0x00,        # Activation type
            0x00, 0x00, 0x00, 0x00  # Reserved
        ])
        sock.send(activation_request)

        # Receive routing activation response
        response = sock.recv(13)
        assert len(response) == 13
        assert response[2:4] == b'\x00\x06'  # Routing Activation Response
        assert response[12] == 0x10  # Response code: Successfully activated

        sock.close()
```

## References
- ISO 13400: Diagnostic communication over Internet Protocol (DoIP)
- AUTOSAR Classic Platform R20-11: PDU Router Specification
- SAE J1939: Serial Control and Communications Heavy Duty Vehicle Network
- IEEE 802.1Q: Virtual LANs and Network Segmentation
- ISO 14229-1: Unified Diagnostic Services (UDS)

## Common Issues
- Message routing latency causing control delays
- Firewall false positives blocking legitimate messages
- DoIP connection timeout during long diagnostic sessions
- Wake-up signal not propagating across networks
- Ethernet packet loss during high CAN traffic bursts
