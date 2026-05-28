# Automotive ECU Systems Skills

## Overview
Comprehensive collection of production-ready skills for modern vehicle Electronic Control Units (ECUs), covering all major domain controllers and systems.

## Skills Included

### 1. [VCU - Vehicle Control Unit](./vcu-vehicle-control.md)
**Electric Vehicle Brain**
- Torque arbitration (driver, cruise, traction control, stability)
- Drive modes (Eco/Sport/Custom) with throttle response curves
- Regenerative braking control and friction brake blending
- Traction control integration with wheel slip detection
- AUTOSAR RTE configuration for VCU software components

**Code**: Torque arbiter, drive mode manager, regen braking, traction control
**Standards**: ISO 26262 ASIL-C
**File Size**: 24 KB | 580 lines

---

### 2. [VGU - Vehicle Gateway Unit](./vgu-gateway-architecture.md)
**Network Routing Hub**
- Multi-network routing (CAN-to-Ethernet, CAN-to-CAN, LIN-to-CAN)
- Security firewall with message filtering and intrusion detection
- DoIP (Diagnostics over IP) gateway for remote diagnostics
- Network wake-up management and power-down sequencing
- AUTOSAR PDU Router configuration

**Code**: Routing engine, security firewall, DoIP handler, wake-up manager
**Standards**: ISO 13400 (DoIP), SecOC
**File Size**: 27 KB | 640 lines

---

### 3. [TCU - Telematics Control Unit](./tcu-telematics-connectivity.md)
**Connected Car Services**
- 4G/5G modem integration (Quectel, Sierra Wireless)
- GNSS/GPS positioning with geofencing
- Remote diagnostics via UDS over HTTP
- OTA update management (download, verify, flash)
- eCall/bCall emergency services (EU regulations)

**Code**: Modem AT commands, GNSS positioning, OTA manager, eCall MSD
**Standards**: 3GPP LTE/NR, ETSI EN 16072 (eCall)
**File Size**: 23 KB | 550 lines

---

### 4. [BCM - Body Control Module](./bcm-body-control.md)
**Comfort and Convenience**
- Exterior/interior lighting control with PWM dimming
- Keyless entry and passive entry systems (BLE/RF)
- Door lock/unlock with central locking
- Window control with anti-pinch detection
- LIN bus mastering for door/seat modules

**Code**: PWM lighting, keyless entry (BLE), window anti-pinch, LIN master
**Standards**: ISO 17987 (LIN), IEC 60529 (IP Rating)
**File Size**: 18 KB | 430 lines

---

### 5. [IVI - In-Vehicle Infotainment](./ivi-infotainment-systems.md)
**User Interface and Entertainment**
- Android Automotive OS / QNX CAR Platform integration
- Navigation (HERE SDK, TomTom SDK)
- CarPlay / Android Auto projection
- Voice assistant (Alexa, Google Assistant)
- HMI frameworks (Qt QML, Flutter)

**Code**: Vehicle HAL (Java), QNX integration (C), navigation (Kotlin), voice (Python)
**Platforms**: AAOS, QNX, Linux (Yocto)
**File Size**: 8 KB | 190 lines

---

### 6. [BMS - Battery Management System](./bms-battery-management.md)
**Energy Guardian for EVs**
- Cell voltage monitoring (LTC6811, TI BQ76xx)
- SOC estimation (Coulomb counting, Kalman filter, OCV-based)
- SOH estimation (capacity fade, internal resistance)
- Cell balancing (passive resistor, active capacitive)
- Contactor control and precharge sequencing
- Thermal management (liquid/air cooling)

**Code**: LTC6811 interface, Kalman filter SOC, cell balancing, precharge
**Standards**: ISO 26262 ASIL-D, UL 2580
**File Size**: 13 KB | 310 lines

---

### 7. [PDU - Power Distribution Unit](./pdu-power-distribution.md)
**High/Low Voltage Power Management**
- HV DC/DC converter (400V to 12V/48V)
- Low-voltage power distribution (16 channels)
- Load shedding under power constraints
- Fuse/relay control and overcurrent protection
- Wake-up source management

**Code**: DC/DC PI controller, power channel monitoring, load shedding
**Standards**: ISO 16750, IEC 61000-4-2 (EMC)
**File Size**: 11 KB | 260 lines

---

### 8. [Domain Controller Architecture](./domain-controller-integration.md)
**Next-Gen E/E Architecture**
- Chassis domain (ESC, ABS, TCS, EPS)
- Powertrain domain (VCU, BMS, MCU consolidation)
- Body/comfort domain (BCM, HVAC, seats, lighting)
- ADAS domain (perception, planning, control)
- Service-oriented architecture (SOME/IP)
- Hypervisor-based domain isolation (QNX, Linux)

**Code**: Domain controller main loops, SOME/IP client/server
**Standards**: AUTOSAR Adaptive Platform, SOME/IP
**File Size**: 13 KB | 310 lines

---

## Quick Start

### For Vehicle Systems Engineers
```bash
# Start with VCU to understand torque arbitration
cat vcu-vehicle-control.md

# Then move to gateway for network integration
cat vgu-gateway-architecture.md

# Add connectivity via TCU
cat tcu-telematics-connectivity.md
```

### For EV Specialists
```bash
# Start with BMS for battery management
cat bms-battery-management.md

# Understand power distribution
cat pdu-power-distribution.md

# Integrate with VCU for power control
cat vcu-vehicle-control.md
```

### For Domain Architects
```bash
# Understand domain consolidation
cat domain-controller-integration.md

# Study individual domain controllers
cat vcu-vehicle-control.md  # Powertrain domain
cat bcm-body-control.md     # Body domain
```

## Total Package Statistics
- **8 Skills**: 137 KB total, 3,270 lines of documentation + code
- **Production Code**: C, Java, Kotlin, Python, ARXML, DBC
- **Standards Covered**: ISO 26262, ISO 13400, ISO 17987, 3GPP, AUTOSAR
- **Platforms**: AUTOSAR Classic/Adaptive, QNX, Android Automotive, Linux

## Related Resources
- **Agents**: See `../../agents/vehicle-systems/` for specialized agents
- **Summary**: See `../../VEHICLE_SYSTEMS_DELIVERABLES.md` for full reference
- **Examples**: All skills include production-ready code examples

## Authentication Status
All skills are authentication-free and ready for immediate use.

## License
See repository LICENSE file for terms of use.
