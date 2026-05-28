# TCU (Telematics Control Unit) - Connectivity and Remote Services

## Overview
The Telematics Control Unit (TCU) provides 4G/5G cellular connectivity, GNSS positioning, remote diagnostics, OTA updates, eCall/bCall emergency services, and fleet management integration. This skill covers production-ready TCU development with modem integration.

## Core Responsibilities

### 1. 4G/5G Modem Integration
```c
/* tcu_modem_manager.c - Cellular modem control (Quectel/Sierra Wireless) */
#include "tcu_modem_manager.h"
#include <string.h>
#include <stdio.h>

#define MODEM_UART_PORT "/dev/ttyUSB2"
#define MODEM_BAUD_RATE 115200
#define AT_COMMAND_TIMEOUT_MS 5000
#define MAX_AT_RESPONSE_LENGTH 512

typedef enum {
    MODEM_STATE_OFF = 0,
    MODEM_STATE_INITIALIZING,
    MODEM_STATE_REGISTERING,
    MODEM_STATE_CONNECTED,
    MODEM_STATE_ERROR
} ModemState_t;

typedef struct {
    int uart_fd;
    ModemState_t state;
    char imei[16];
    char iccid[21];
    int signal_strength_dbm;
    char network_operator[32];
    char ip_address[16];
    bool data_session_active;
} ModemContext_t;

static ModemContext_t g_modem = {0};

/* AT command send/receive */
bool TCU_Modem_SendATCommand(const char* cmd, char* response, uint16_t response_size) {
    /* Send AT command */
    char cmd_buffer[128];
    snprintf(cmd_buffer, sizeof(cmd_buffer), "%s\r\n", cmd);

    int bytes_written = write(g_modem.uart_fd, cmd_buffer, strlen(cmd_buffer));
    if (bytes_written < 0) {
        return false;
    }

    /* Wait for response */
    uint32_t start_time = GetSystemTime_ms();
    int total_bytes = 0;

    while ((GetSystemTime_ms() - start_time) < AT_COMMAND_TIMEOUT_MS) {
        int bytes_available = 0;
        ioctl(g_modem.uart_fd, FIONREAD, &bytes_available);

        if (bytes_available > 0) {
            int bytes_read = read(g_modem.uart_fd,
                                   &response[total_bytes],
                                   response_size - total_bytes - 1);
            if (bytes_read > 0) {
                total_bytes += bytes_read;
                response[total_bytes] = '\0';

                /* Check for "OK" or "ERROR" */
                if (strstr(response, "OK\r\n") != NULL) {
                    return true;
                }
                if (strstr(response, "ERROR\r\n") != NULL) {
                    return false;
                }
            }
        }

        usleep(10000);  /* 10ms polling interval */
    }

    return false;  /* Timeout */
}

void TCU_Modem_Init(void) {
    /* Open UART port */
    g_modem.uart_fd = open(MODEM_UART_PORT, O_RDWR | O_NOCTTY);
    if (g_modem.uart_fd < 0) {
        g_modem.state = MODEM_STATE_ERROR;
        return;
    }

    /* Configure UART: 115200 8N1 */
    struct termios tty;
    tcgetattr(g_modem.uart_fd, &tty);
    cfsetospeed(&tty, B115200);
    cfsetispeed(&tty, B115200);
    tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8;
    tty.c_cflag &= ~PARENB;
    tty.c_cflag &= ~CSTOPB;
    tcsetattr(g_modem.uart_fd, TCSANOW, &tty);

    g_modem.state = MODEM_STATE_INITIALIZING;

    char response[MAX_AT_RESPONSE_LENGTH];

    /* Basic AT command check */
    if (!TCU_Modem_SendATCommand("AT", response, sizeof(response))) {
        g_modem.state = MODEM_STATE_ERROR;
        return;
    }

    /* Disable echo */
    TCU_Modem_SendATCommand("ATE0", response, sizeof(response));

    /* Get IMEI */
    if (TCU_Modem_SendATCommand("AT+GSN", response, sizeof(response))) {
        sscanf(response, "%15s", g_modem.imei);
    }

    /* Get ICCID (SIM card ID) */
    if (TCU_Modem_SendATCommand("AT+CCID", response, sizeof(response))) {
        sscanf(response, "+CCID: %20s", g_modem.iccid);
    }

    /* Check SIM status */
    if (!TCU_Modem_SendATCommand("AT+CPIN?", response, sizeof(response))) {
        g_modem.state = MODEM_STATE_ERROR;
        return;
    }

    /* Start network registration */
    TCU_Modem_StartNetworkRegistration();
}

void TCU_Modem_StartNetworkRegistration(void) {
    char response[MAX_AT_RESPONSE_LENGTH];

    /* Set network mode: LTE only for 4G, NR+LTE for 5G */
    TCU_Modem_SendATCommand("AT+QCFG=\"nwscanmode\",3", response, sizeof(response));

    /* Enable network registration URC */
    TCU_Modem_SendATCommand("AT+CREG=2", response, sizeof(response));

    /* Check registration status */
    if (TCU_Modem_SendATCommand("AT+CREG?", response, sizeof(response))) {
        int n, stat;
        if (sscanf(response, "+CREG: %d,%d", &n, &stat) == 2) {
            if (stat == 1 || stat == 5) {  /* Registered (home or roaming) */
                g_modem.state = MODEM_STATE_REGISTERED;
                TCU_Modem_GetNetworkInfo();
            } else {
                g_modem.state = MODEM_STATE_REGISTERING;
            }
        }
    }
}

void TCU_Modem_GetNetworkInfo(void) {
    char response[MAX_AT_RESPONSE_LENGTH];

    /* Get signal strength */
    if (TCU_Modem_SendATCommand("AT+CSQ", response, sizeof(response))) {
        int rssi, ber;
        if (sscanf(response, "+CSQ: %d,%d", &rssi, &ber) == 2) {
            /* Convert RSSI to dBm: dBm = -113 + 2*rssi */
            g_modem.signal_strength_dbm = -113 + (2 * rssi);
        }
    }

    /* Get operator name */
    if (TCU_Modem_SendATCommand("AT+COPS?", response, sizeof(response))) {
        char operator_name[32];
        if (sscanf(response, "+COPS: 0,0,\"%31[^\"]\"", operator_name) == 1) {
            strncpy(g_modem.network_operator, operator_name, sizeof(g_modem.network_operator));
        }
    }
}

bool TCU_Modem_StartDataSession(const char* apn) {
    char response[MAX_AT_RESPONSE_LENGTH];
    char cmd[128];

    /* Configure PDP context */
    snprintf(cmd, sizeof(cmd), "AT+QICSGP=1,1,\"%s\",\"\",\"\",1", apn);
    if (!TCU_Modem_SendATCommand(cmd, response, sizeof(response))) {
        return false;
    }

    /* Activate PDP context */
    if (!TCU_Modem_SendATCommand("AT+QIACT=1", response, sizeof(response))) {
        return false;
    }

    /* Get IP address */
    if (TCU_Modem_SendATCommand("AT+QIACT?", response, sizeof(response))) {
        char ip_addr[16];
        if (sscanf(response, "+QIACT: 1,1,1,\"%15[^\"]\"", ip_addr) == 1) {
            strncpy(g_modem.ip_address, ip_addr, sizeof(g_modem.ip_address));
            g_modem.data_session_active = true;
            g_modem.state = MODEM_STATE_CONNECTED;
            return true;
        }
    }

    return false;
}

/* HTTP client for cloud connectivity */
bool TCU_Modem_HTTPPost(const char* url, const char* json_payload, char* response) {
    char cmd[256];
    char at_response[MAX_AT_RESPONSE_LENGTH];

    /* Configure HTTP context */
    snprintf(cmd, sizeof(cmd), "AT+QHTTPCFG=\"contextid\",1");
    TCU_Modem_SendATCommand(cmd, at_response, sizeof(at_response));

    /* Set URL */
    snprintf(cmd, sizeof(cmd), "AT+QHTTPURL=%zu,80", strlen(url));
    TCU_Modem_SendATCommand(cmd, at_response, sizeof(at_response));

    /* Send URL */
    write(g_modem.uart_fd, url, strlen(url));
    usleep(100000);

    /* POST data */
    snprintf(cmd, sizeof(cmd), "AT+QHTTPPOST=%zu,80,80", strlen(json_payload));
    TCU_Modem_SendATCommand(cmd, at_response, sizeof(at_response));

    /* Send payload */
    write(g_modem.uart_fd, json_payload, strlen(json_payload));

    /* Wait for response */
    sleep(2);

    /* Read response */
    TCU_Modem_SendATCommand("AT+QHTTPREAD=80", response, MAX_AT_RESPONSE_LENGTH);

    return true;
}
```

### 2. GNSS/GPS Position Tracking
```c
/* tcu_gnss_manager.c - GPS/GLONASS/BeiDou positioning */
#include "tcu_gnss_manager.h"
#include <math.h>

#define EARTH_RADIUS_KM 6371.0

typedef struct {
    double latitude;
    double longitude;
    float altitude_m;
    float speed_kph;
    float heading_deg;
    uint8_t satellites_used;
    float hdop;  /* Horizontal dilution of precision */
    bool fix_valid;
    uint32_t timestamp_ms;
} GNSSPosition_t;

static GNSSPosition_t g_gnss_position = {0};

void TCU_GNSS_Init(void) {
    char response[MAX_AT_RESPONSE_LENGTH];

    /* Enable GNSS */
    TCU_Modem_SendATCommand("AT+QGPS=1", response, sizeof(response));

    /* Configure GNSS to use GPS+GLONASS+BeiDou */
    TCU_Modem_SendATCommand("AT+QGPSCFG=\"gnssconfig\",7", response, sizeof(response));
}

bool TCU_GNSS_GetPosition(GNSSPosition_t* position) {
    char response[MAX_AT_RESPONSE_LENGTH];

    /* Query GNSS position */
    if (!TCU_Modem_SendATCommand("AT+QGPSLOC=2", response, sizeof(response))) {
        return false;
    }

    /* Parse NMEA-like response: +QGPSLOC: <time>,<lat>,<lon>,<hdop>,<alt>,<fix>,<cog>,<spkm>,<spkn>,<date>,<nsat> */
    char time_str[16], date_str[16];
    int fix_type, nsat;

    int parsed = sscanf(response,
                        "+QGPSLOC: %15[^,],%lf,%lf,%f,%f,%d,%f,%f,%*f,%15[^,],%d",
                        time_str,
                        &position->latitude,
                        &position->longitude,
                        &position->hdop,
                        &position->altitude_m,
                        &fix_type,
                        &position->heading_deg,
                        &position->speed_kph,
                        date_str,
                        &nsat);

    if (parsed >= 9) {
        position->satellites_used = nsat;
        position->fix_valid = (fix_type >= 2);  /* 2D or 3D fix */
        position->timestamp_ms = GetSystemTime_ms();

        /* Update global position */
        memcpy(&g_gnss_position, position, sizeof(GNSSPosition_t));

        return true;
    }

    return false;
}

/* Calculate distance between two GPS coordinates (Haversine formula) */
float TCU_GNSS_CalculateDistance_km(double lat1, double lon1, double lat2, double lon2) {
    double dLat = (lat2 - lat1) * M_PI / 180.0;
    double dLon = (lon2 - lon1) * M_PI / 180.0;

    lat1 = lat1 * M_PI / 180.0;
    lat2 = lat2 * M_PI / 180.0;

    double a = sin(dLat / 2) * sin(dLat / 2) +
               sin(dLon / 2) * sin(dLon / 2) * cos(lat1) * cos(lat2);

    double c = 2 * atan2(sqrt(a), sqrt(1 - a));

    return EARTH_RADIUS_KM * c;
}

/* Geofencing: check if vehicle is inside defined boundary */
bool TCU_GNSS_IsInsideGeofence(double center_lat, double center_lon, float radius_km) {
    if (!g_gnss_position.fix_valid) {
        return false;
    }

    float distance = TCU_GNSS_CalculateDistance_km(
        g_gnss_position.latitude,
        g_gnss_position.longitude,
        center_lat,
        center_lon);

    return (distance <= radius_km);
}
```

### 3. Remote Diagnostics (UDS over HTTP)
```c
/* tcu_remote_diagnostics.c - Cloud-based diagnostic services */
#include "tcu_remote_diagnostics.h"
#include "json.h"

#define CLOUD_DIAGNOSTICS_URL "https://telemetry.example.com/api/v1/diagnostics"

typedef struct {
    uint32_t dtc_code;
    uint8_t status;
    uint32_t occurrence_count;
    uint32_t first_occurrence_timestamp;
} DTC_Entry_t;

void TCU_RemoteDiagnostics_SendDTCs(void) {
    /* Read DTCs from all ECUs via CAN */
    DTC_Entry_t dtc_list[32];
    uint8_t dtc_count = 0;

    /* Query VCU for DTCs */
    uint8_t uds_request[] = {0x19, 0x02, 0xFF};  /* ReadDTCByStatusMask */
    uint8_t uds_response[256];
    uint16_t response_length;

    if (UDS_SendRequest(VCU_DIAGNOSTIC_ADDR, uds_request, 3,
                        uds_response, &response_length)) {
        /* Parse DTC response */
        for (int i = 3; i < response_length; i += 4) {
            dtc_list[dtc_count].dtc_code = (uds_response[i] << 16) |
                                            (uds_response[i+1] << 8) |
                                            uds_response[i+2];
            dtc_list[dtc_count].status = uds_response[i+3];
            dtc_count++;
        }
    }

    /* Build JSON payload */
    char json_payload[1024];
    snprintf(json_payload, sizeof(json_payload),
             "{"
             "\"vin\":\"%s\","
             "\"timestamp\":%u,"
             "\"dtcs\":[",
             g_vehicle_vin,
             GetSystemTime_ms());

    for (int i = 0; i < dtc_count; i++) {
        char dtc_entry[128];
        snprintf(dtc_entry, sizeof(dtc_entry),
                 "{\"code\":\"0x%06X\",\"status\":0x%02X}%s",
                 dtc_list[i].dtc_code,
                 dtc_list[i].status,
                 (i < dtc_count - 1) ? "," : "");
        strcat(json_payload, dtc_entry);
    }

    strcat(json_payload, "]}");

    /* Send to cloud via HTTPS */
    char response[512];
    TCU_Modem_HTTPPost(CLOUD_DIAGNOSTICS_URL, json_payload, response);
}

void TCU_RemoteDiagnostics_ExecuteCommand(const char* command_json) {
    /* Parse remote diagnostic command */
    json_object* root = json_tokener_parse(command_json);
    json_object* cmd_type_obj = json_object_object_get(root, "command");

    const char* cmd_type = json_object_get_string(cmd_type_obj);

    if (strcmp(cmd_type, "READ_DTC") == 0) {
        TCU_RemoteDiagnostics_SendDTCs();
    } else if (strcmp(cmd_type, "CLEAR_DTC") == 0) {
        /* Send UDS ClearDiagnosticInformation */
        uint8_t uds_clear_dtc[] = {0x14, 0xFF, 0xFF, 0xFF};
        uint8_t response[8];
        uint16_t response_length;
        UDS_SendRequest(VCU_DIAGNOSTIC_ADDR, uds_clear_dtc, 4, response, &response_length);
    } else if (strcmp(cmd_type, "READ_DATA") == 0) {
        /* Read live data via UDS ReadDataByIdentifier */
        json_object* did_obj = json_object_object_get(root, "did");
        uint16_t did = json_object_get_int(did_obj);

        uint8_t uds_read_data[] = {0x22, (did >> 8) & 0xFF, did & 0xFF};
        uint8_t response[256];
        uint16_t response_length;

        if (UDS_SendRequest(VCU_DIAGNOSTIC_ADDR, uds_read_data, 3,
                            response, &response_length)) {
            /* Send response back to cloud */
            char response_json[512];
            snprintf(response_json, sizeof(response_json),
                     "{\"vin\":\"%s\",\"did\":\"0x%04X\",\"data\":\"",
                     g_vehicle_vin, did);

            for (int i = 0; i < response_length; i++) {
                char hex[4];
                snprintf(hex, sizeof(hex), "%02X", response[i]);
                strcat(response_json, hex);
            }

            strcat(response_json, "\"}");
            TCU_Modem_HTTPPost(CLOUD_DIAGNOSTICS_URL, response_json, NULL);
        }
    }

    json_object_put(root);
}
```

### 4. eCall / bCall Emergency Services
```c
/* tcu_ecall.c - Automatic emergency call (eCall) - EU regulation */
#include "tcu_ecall.h"

#define ECALL_EMERGENCY_NUMBER "112"
#define BCALL_ROADSIDE_NUMBER "1234567890"

typedef struct {
    uint8_t msd_format_version;
    uint8_t message_identifier;
    uint32_t timestamp;
    double latitude;
    double longitude;
    uint8_t vehicle_class;
    char vin[18];
    uint8_t propulsion_storage_type;
    bool recent_engine_status;
} MSD_t;  /* Minimum Set of Data for eCall */

void TCU_eCall_Trigger(bool automatic) {
    /* Build MSD (Minimum Set of Data) */
    MSD_t msd = {0};
    msd.msd_format_version = 1;
    msd.message_identifier = automatic ? 1 : 2;  /* 1=automatic, 2=manual */
    msd.timestamp = GetSystemTime_ms() / 1000;

    /* Get current GPS position */
    GNSSPosition_t position;
    if (TCU_GNSS_GetPosition(&position)) {
        msd.latitude = position.latitude;
        msd.longitude = position.longitude;
    }

    msd.vehicle_class = 1;  /* M1 (passenger car) */
    strncpy(msd.vin, g_vehicle_vin, sizeof(msd.vin));
    msd.propulsion_storage_type = 0x05;  /* Electric */
    msd.recent_engine_status = VCU_IsVehicleOn();

    /* Encode MSD to ASN.1 format */
    uint8_t msd_encoded[140];  /* Max 140 bytes for MSD */
    uint16_t msd_length = TCU_eCall_EncodeMSD(&msd, msd_encoded);

    /* Initiate voice call to emergency services */
    char at_cmd[64];
    char response[MAX_AT_RESPONSE_LENGTH];

    snprintf(at_cmd, sizeof(at_cmd), "ATD%s;", ECALL_EMERGENCY_NUMBER);
    TCU_Modem_SendATCommand(at_cmd, response, sizeof(response));

    /* Wait for call connection */
    sleep(3);

    /* Send MSD over in-band modem (IVS - In-Vehicle System) */
    TCU_eCall_SendMSDInBand(msd_encoded, msd_length);

    /* Keep call active for voice communication */
    /* Operator will speak with occupants if possible */
}

void TCU_bCall_Trigger(void) {
    /* Breakdown call: non-emergency roadside assistance */
    char at_cmd[64];
    char response[MAX_AT_RESPONSE_LENGTH];

    snprintf(at_cmd, sizeof(at_cmd), "ATD%s;", BCALL_ROADSIDE_NUMBER);
    TCU_Modem_SendATCommand(at_cmd, response, sizeof(response));

    /* Send vehicle data to roadside assistance */
    char json_payload[512];
    GNSSPosition_t position;
    TCU_GNSS_GetPosition(&position);

    snprintf(json_payload, sizeof(json_payload),
             "{"
             "\"vin\":\"%s\","
             "\"latitude\":%.6f,"
             "\"longitude\":%.6f,"
             "\"issue\":\"Breakdown assistance requested\""
             "}",
             g_vehicle_vin,
             position.latitude,
             position.longitude);

    TCU_Modem_HTTPPost("https://roadside.example.com/api/assist", json_payload, NULL);
}
```

### 5. OTA Download Manager
```c
/* tcu_ota_manager.c - Over-the-Air software updates */
#include "tcu_ota_manager.h"

#define OTA_SERVER_URL "https://ota.example.com/api/v1/updates"
#define OTA_CHUNK_SIZE 4096

typedef struct {
    char version[16];
    char ecu_target[32];
    uint32_t file_size;
    char download_url[256];
    uint8_t sha256_hash[32];
} OTAPackage_t;

typedef struct {
    bool update_available;
    OTAPackage_t package;
    uint32_t bytes_downloaded;
    uint8_t download_progress_percent;
    bool download_complete;
} OTAState_t;

static OTAState_t g_ota_state = {0};

bool TCU_OTA_CheckForUpdates(void) {
    /* Query OTA server for available updates */
    char json_request[256];
    snprintf(json_request, sizeof(json_request),
             "{\"vin\":\"%s\",\"current_versions\":{"
             "\"vcu\":\"1.2.3\",\"bms\":\"2.0.1\",\"mcu\":\"3.1.0\""
             "}}",
             g_vehicle_vin);

    char response[1024];
    if (!TCU_Modem_HTTPPost(OTA_SERVER_URL, json_request, response)) {
        return false;
    }

    /* Parse JSON response */
    json_object* root = json_tokener_parse(response);
    json_object* update_available_obj = json_object_object_get(root, "update_available");

    if (json_object_get_boolean(update_available_obj)) {
        json_object* package_obj = json_object_object_get(root, "package");

        /* Extract package info */
        json_object* version_obj = json_object_object_get(package_obj, "version");
        json_object* ecu_obj = json_object_object_get(package_obj, "ecu");
        json_object* size_obj = json_object_object_get(package_obj, "size");
        json_object* url_obj = json_object_object_get(package_obj, "url");

        strncpy(g_ota_state.package.version,
                json_object_get_string(version_obj),
                sizeof(g_ota_state.package.version));

        strncpy(g_ota_state.package.ecu_target,
                json_object_get_string(ecu_obj),
                sizeof(g_ota_state.package.ecu_target));

        g_ota_state.package.file_size = json_object_get_int(size_obj);

        strncpy(g_ota_state.package.download_url,
                json_object_get_string(url_obj),
                sizeof(g_ota_state.package.download_url));

        g_ota_state.update_available = true;

        json_object_put(root);
        return true;
    }

    json_object_put(root);
    return false;
}

bool TCU_OTA_DownloadPackage(void) {
    if (!g_ota_state.update_available) {
        return false;
    }

    /* Open file for writing */
    int fd = open("/data/ota/update.bin", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) {
        return false;
    }

    /* Download in chunks */
    uint32_t offset = 0;
    uint8_t buffer[OTA_CHUNK_SIZE];

    while (offset < g_ota_state.package.file_size) {
        uint32_t chunk_size = (g_ota_state.package.file_size - offset) > OTA_CHUNK_SIZE ?
                               OTA_CHUNK_SIZE : (g_ota_state.package.file_size - offset);

        /* HTTP range request */
        char range_header[64];
        snprintf(range_header, sizeof(range_header),
                 "Range: bytes=%u-%u", offset, offset + chunk_size - 1);

        /* Download chunk (simplified - use libcurl in production) */
        if (!TCU_HTTP_DownloadChunk(g_ota_state.package.download_url,
                                      range_header, buffer, chunk_size)) {
            close(fd);
            return false;
        }

        /* Write to file */
        write(fd, buffer, chunk_size);

        offset += chunk_size;
        g_ota_state.bytes_downloaded = offset;
        g_ota_state.download_progress_percent =
            (offset * 100) / g_ota_state.package.file_size;

        /* Notify user via CAN */
        CAN_SendOTAProgress(g_ota_state.download_progress_percent);
    }

    close(fd);
    g_ota_state.download_complete = true;

    /* Verify SHA256 hash */
    uint8_t calculated_hash[32];
    TCU_OTA_CalculateSHA256("/data/ota/update.bin", calculated_hash);

    if (memcmp(calculated_hash, g_ota_state.package.sha256_hash, 32) != 0) {
        /* Hash mismatch: corrupted download */
        unlink("/data/ota/update.bin");
        return false;
    }

    return true;
}

void TCU_OTA_InstallPackage(void) {
    /* Flash update to target ECU */
    if (strcmp(g_ota_state.package.ecu_target, "VCU") == 0) {
        /* Flash VCU via UDS RequestDownload / TransferData / RequestTransferExit */
        TCU_OTA_FlashECU(VCU_DIAGNOSTIC_ADDR, "/data/ota/update.bin");
    } else if (strcmp(g_ota_state.package.ecu_target, "BMS") == 0) {
        TCU_OTA_FlashECU(BMS_DIAGNOSTIC_ADDR, "/data/ota/update.bin");
    }

    /* Cleanup */
    unlink("/data/ota/update.bin");
    memset(&g_ota_state, 0, sizeof(OTAState_t));
}
```

## TCU CAN Database (DBC)
```
VERSION ""

NS_ :

BS_:

BU_: TCU VCU BCM IVI

/* TCU Status */
BO_ 768 TCU_Status: 8 TCU
 SG_ TCU_ModemState : 0|8@1+ (0,0) [0|4] ""  VCU,IVI
 SG_ TCU_SignalStrength_dBm : 8|8@1- (-113,0) [-113|0] "dBm"  IVI
 SG_ TCU_DataSessionActive : 16|1@1+ (0,0) [0|1] ""  IVI
 SG_ TCU_GNSSFixValid : 17|1@1+ (0,0) [0|1] ""  VCU,IVI
 SG_ TCU_SatellitesUsed : 24|8@1+ (0,0) [0|32] ""  IVI
 SG_ TCU_OTAUpdateAvailable : 32|1@1+ (0,0) [0|1] ""  IVI
 SG_ TCU_OTADownloadProgress : 40|8@1+ (0,0) [0|100] "%"  IVI

/* TCU GPS Position */
BO_ 769 TCU_Position: 8 TCU
 SG_ TCU_Latitude : 0|32@1+ (0.0000001,-90) [-90|90] "deg"  VCU,IVI
 SG_ TCU_Longitude : 32|32@1+ (0.0000001,-180) [-180|180] "deg"  VCU,IVI

/* TCU Speed and Heading */
BO_ 770 TCU_Navigation: 8 TCU
 SG_ TCU_GPSSpeed_kph : 0|16@1+ (0.01,0) [0|300] "km/h"  VCU,IVI
 SG_ TCU_Heading_deg : 16|16@1+ (0.01,0) [0|360] "deg"  VCU,IVI
 SG_ TCU_Altitude_m : 32|16@1+ (0.1,-500) [-500|9000] "m"  IVI
 SG_ TCU_HDOP : 48|8@1+ (0.1,0) [0|25] ""  IVI

VAL_ 768 TCU_ModemState 0 "Off" 1 "Initializing" 2 "Registering" 3 "Connected" 4 "Error";
```

## References
- 3GPP TS 24.008: Mobile radio interface Layer 3 specification
- ETSI EN 16072: eCall Minimum Set of Data (MSD)
- ISO 17987: Local Interconnect Network (LIN)
- MQTT Protocol Specification v5.0
- AWS IoT Core: Fleet Provisioning

## Common Issues
- Modem not responding to AT commands (baud rate mismatch)
- GPS fix lost in urban canyons or underground parking
- OTA download interrupted due to poor signal strength
- eCall MSD encoding errors
- Data session dropped during handover between cell towers
