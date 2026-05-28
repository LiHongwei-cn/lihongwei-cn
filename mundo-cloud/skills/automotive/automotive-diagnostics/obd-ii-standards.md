# OBD-II Standards - On-Board Diagnostics

## Overview

OBD-II (On-Board Diagnostics, Second Generation) is mandated for all vehicles sold in the US since 1996. This skill covers SAE J1979 protocols, PIDs, emission DTCs, and readiness monitors.

## OBD-II Protocols

### Protocol Types

1. **SAE J1850 PWM** (41.6 kbaud) - Ford
2. **SAE J1850 VPW** (10.4 kbaud) - GM
3. **ISO 9141-2** - Asian/European vehicles
4. **ISO 14230 (KWP2000)** - Keyword Protocol 2000
5. **ISO 15765 (CAN)** - Modern vehicles (2008+)

### Physical Layer

**DLC Pinout (16-pin connector):**
```
Pin 4:  Chassis Ground
Pin 5:  Signal Ground
Pin 6:  CAN High (J1850 Bus+)
Pin 7:  ISO 9141-2 K-Line
Pin 14: CAN Low (J1850 Bus-)
Pin 16: Battery Power (12V)
```

## OBD-II Modes (Services)

### Mode 01: Show Current Data

Request real-time sensor data using PIDs.

**Request Format:**
```
Byte 0: 0x01 (Mode)
Byte 1: PID (0x00-0xFF)
```

**Response Format:**
```
Byte 0: 0x41 (Mode + 0x40)
Byte 1: PID (echo)
Byte 2-N: Data bytes (PID-specific)
```

### Mode 02: Show Freeze Frame Data

Snapshot of data when DTC was set.

### Mode 03: Show Stored DTCs

Returns emission-related DTCs.

**Response Format:**
```
Byte 0: 0x43
Byte 1: Number of DTCs
Byte 2-3: DTC #1
Byte 4-5: DTC #2
...
```

### Mode 04: Clear DTCs and Freeze Frame

Clears all emission-related diagnostic information.

### Mode 05: Test Results for O2 Sensors

Non-CAN monitoring test results.

### Mode 06: Test Results for Other Systems

On-board monitoring test results.

### Mode 07: Show Pending DTCs

DTCs detected in current or last driving cycle.

### Mode 08: Control Operations

Request control of on-board systems.

### Mode 09: Request Vehicle Information

VIN, calibration IDs, ECU name, etc.

**Key PIDs:**
- 0x02: VIN (17 characters)
- 0x04: Calibration ID
- 0x0A: ECU Name

### Mode 0A: Show Permanent DTCs

Permanent DTCs that cannot be cleared with Mode 04.

## Common PIDs (Mode 01)

### PID 0x00: Supported PIDs [01-20]

**Response:** 4 bytes bitmap showing supported PIDs

### PID 0x01: Monitor Status Since DTCs Cleared

```
Byte A:
  Bit 7: MIL status (0=off, 1=on)
  Bit 6-0: Number of DTCs
Byte B: Test availability
Byte C-D: Test completion status
```

### PID 0x04: Calculated Engine Load

**Formula:** `A * 100 / 255` (percentage)

### PID 0x05: Engine Coolant Temperature

**Formula:** `A - 40` (degrees Celsius)

### PID 0x0C: Engine RPM

**Formula:** `(A*256 + B) / 4` (RPM)

### PID 0x0D: Vehicle Speed

**Formula:** `A` (km/h)

### PID 0x0F: Intake Air Temperature

**Formula:** `A - 40` (degrees Celsius)

### PID 0x10: MAF Air Flow Rate

**Formula:** `(A*256 + B) / 100` (grams/sec)

### PID 0x11: Throttle Position

**Formula:** `A * 100 / 255` (percentage)

## Production Code - OBD-II Library

**Python Implementation:**
```python
#!/usr/bin/env python3
"""
OBD-II Protocol Implementation
Supports Mode 01-0A services with comprehensive PID decoding
"""

import struct
import time
from enum import IntEnum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

class OBDMode(IntEnum):
    """OBD-II service modes."""
    CURRENT_DATA = 0x01
    FREEZE_FRAME = 0x02
    STORED_DTCS = 0x03
    CLEAR_DTCS = 0x04
    TEST_RESULTS_O2 = 0x05
    TEST_RESULTS_OTHER = 0x06
    PENDING_DTCS = 0x07
    CONTROL_OPERATION = 0x08
    VEHICLE_INFO = 0x09
    PERMANENT_DTCS = 0x0A

@dataclass
class PIDDefinition:
    """PID metadata and decoding formula."""
    pid: int
    name: str
    description: str
    bytes_count: int
    formula: callable
    unit: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None

class OBDII:
    """OBD-II diagnostic interface."""

    def __init__(self, interface):
        """
        Initialize OBD-II interface.

        Args:
            interface: Communication interface (ELM327, SocketCAN, etc.)
        """
        self.interface = interface
        self.supported_pids = set()
        self.pid_definitions = {}
        self._init_standard_pids()

    def _init_standard_pids(self):
        """Initialize standard PID definitions."""
        pids = [
            PIDDefinition(
                0x00, "PIDs_supported_01_20", "Supported PIDs [01-20]",
                4, lambda data: self._decode_supported_pids(data, 0x00), "bitmap"
            ),
            PIDDefinition(
                0x01, "monitor_status", "Monitor status since DTCs cleared",
                4, lambda data: self._decode_monitor_status(data), "status"
            ),
            PIDDefinition(
                0x04, "engine_load", "Calculated engine load",
                1, lambda data: data[0] * 100 / 255, "%", 0, 100
            ),
            PIDDefinition(
                0x05, "coolant_temp", "Engine coolant temperature",
                1, lambda data: data[0] - 40, "°C", -40, 215
            ),
            PIDDefinition(
                0x06, "short_fuel_trim_bank1", "Short term fuel trim - Bank 1",
                1, lambda data: (data[0] - 128) * 100 / 128, "%", -100, 99.2
            ),
            PIDDefinition(
                0x07, "long_fuel_trim_bank1", "Long term fuel trim - Bank 1",
                1, lambda data: (data[0] - 128) * 100 / 128, "%", -100, 99.2
            ),
            PIDDefinition(
                0x0C, "engine_rpm", "Engine RPM",
                2, lambda data: (data[0] * 256 + data[1]) / 4, "RPM", 0, 16383.75
            ),
            PIDDefinition(
                0x0D, "vehicle_speed", "Vehicle speed",
                1, lambda data: data[0], "km/h", 0, 255
            ),
            PIDDefinition(
                0x0F, "intake_air_temp", "Intake air temperature",
                1, lambda data: data[0] - 40, "°C", -40, 215
            ),
            PIDDefinition(
                0x10, "maf_flow_rate", "MAF air flow rate",
                2, lambda data: (data[0] * 256 + data[1]) / 100, "g/s", 0, 655.35
            ),
            PIDDefinition(
                0x11, "throttle_position", "Throttle position",
                1, lambda data: data[0] * 100 / 255, "%", 0, 100
            ),
            PIDDefinition(
                0x1F, "runtime_since_start", "Run time since engine start",
                2, lambda data: data[0] * 256 + data[1], "seconds", 0, 65535
            ),
            PIDDefinition(
                0x20, "pids_supported_21_40", "Supported PIDs [21-40]",
                4, lambda data: self._decode_supported_pids(data, 0x20), "bitmap"
            ),
            PIDDefinition(
                0x21, "distance_with_mil", "Distance traveled with MIL on",
                2, lambda data: data[0] * 256 + data[1], "km", 0, 65535
            ),
            PIDDefinition(
                0x2F, "fuel_tank_level", "Fuel tank level input",
                1, lambda data: data[0] * 100 / 255, "%", 0, 100
            ),
            PIDDefinition(
                0x33, "barometric_pressure", "Absolute barometric pressure",
                1, lambda data: data[0], "kPa", 0, 255
            ),
            PIDDefinition(
                0x40, "pids_supported_41_60", "Supported PIDs [41-60]",
                4, lambda data: self._decode_supported_pids(data, 0x40), "bitmap"
            ),
            PIDDefinition(
                0x42, "control_module_voltage", "Control module voltage",
                2, lambda data: (data[0] * 256 + data[1]) / 1000, "V", 0, 65.535
            ),
            PIDDefinition(
                0x46, "ambient_air_temp", "Ambient air temperature",
                1, lambda data: data[0] - 40, "°C", -40, 215
            ),
            PIDDefinition(
                0x51, "fuel_type", "Fuel type",
                1, lambda data: self._decode_fuel_type(data[0]), "type"
            ),
            PIDDefinition(
                0x5C, "engine_oil_temp", "Engine oil temperature",
                1, lambda data: data[0] - 40, "°C", -40, 215
            ),
        ]

        for pid_def in pids:
            self.pid_definitions[pid_def.pid] = pid_def

    def query_supported_pids(self) -> set:
        """
        Query all supported PIDs from vehicle.

        Returns:
            Set of supported PID numbers
        """
        supported = set()

        # Query PID support ranges
        for base_pid in [0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0, 0xE0]:
            result = self.read_pid(base_pid)
            if result and 'value' in result:
                bitmap = result['value']
                if isinstance(bitmap, set):
                    supported.update(bitmap)

        self.supported_pids = supported
        return supported

    def read_pid(self, pid: int, mode: OBDMode = OBDMode.CURRENT_DATA) -> Optional[Dict[str, Any]]:
        """
        Read PID value from vehicle.

        Args:
            pid: PID number (0x00-0xFF)
            mode: OBD mode (default: Mode 01)

        Returns:
            Dictionary with parsed value and metadata
        """
        # Build request
        request = bytes([mode, pid])

        # Send request
        response = self.interface.send_request(request, timeout=1.0)

        if response is None:
            return None

        # Validate response
        if len(response) < 2:
            return None

        if response[0] != mode + 0x40:
            print(f"Invalid response mode: 0x{response[0]:02X}")
            return None

        if response[1] != pid:
            print(f"PID mismatch: requested 0x{pid:02X}, got 0x{response[1]:02X}")
            return None

        # Extract data
        data = response[2:]

        # Parse using definition
        pid_def = self.pid_definitions.get(pid)
        if pid_def:
            try:
                value = pid_def.formula(data)
                return {
                    'pid': pid,
                    'name': pid_def.name,
                    'value': value,
                    'unit': pid_def.unit,
                    'raw_data': data.hex(),
                }
            except Exception as e:
                print(f"Error parsing PID 0x{pid:02X}: {e}")
                return None
        else:
            # Unknown PID
            return {
                'pid': pid,
                'name': f'Unknown_PID_0x{pid:02X}',
                'value': data.hex(),
                'unit': 'raw',
                'raw_data': data.hex(),
            }

    def read_multiple_pids(self, pids: List[int]) -> Dict[int, Optional[Dict[str, Any]]]:
        """Read multiple PIDs sequentially."""
        results = {}
        for pid in pids:
            results[pid] = self.read_pid(pid)
        return results

    def read_dtcs(self, mode: OBDMode = OBDMode.STORED_DTCS) -> List[str]:
        """
        Read DTCs from vehicle.

        Args:
            mode: DTC mode (STORED_DTCS, PENDING_DTCS, or PERMANENT_DTCS)

        Returns:
            List of DTC strings (e.g., ['P0171', 'P0420'])
        """
        if mode not in [OBDMode.STORED_DTCS, OBDMode.PENDING_DTCS, OBDMode.PERMANENT_DTCS]:
            raise ValueError("Invalid mode for reading DTCs")

        # Build request
        request = bytes([mode])

        # Send request
        response = self.interface.send_request(request, timeout=1.0)

        if response is None:
            return []

        # Validate response
        if response[0] != mode + 0x40:
            return []

        # Parse DTCs
        dtc_count = response[1]
        dtcs = []

        for i in range(dtc_count):
            offset = 2 + i * 2
            if offset + 1 >= len(response):
                break

            dtc_bytes = response[offset:offset+2]
            dtc_string = self._decode_dtc(dtc_bytes)
            if dtc_string:
                dtcs.append(dtc_string)

        return dtcs

    def clear_dtcs(self) -> bool:
        """
        Clear all DTCs and freeze frame data.

        Returns:
            True if successful
        """
        request = bytes([OBDMode.CLEAR_DTCS])
        response = self.interface.send_request(request, timeout=2.0)

        if response is None:
            return False

        # Check for positive response
        return response[0] == OBDMode.CLEAR_DTCS + 0x40

    def read_vin(self) -> Optional[str]:
        """
        Read Vehicle Identification Number.

        Returns:
            17-character VIN string
        """
        # Mode 09, PID 02
        request = bytes([OBDMode.VEHICLE_INFO, 0x02])
        response = self.interface.send_request(request, timeout=1.0)

        if response is None or len(response) < 5:
            return None

        # VIN is in bytes 3+, 17 characters
        vin_bytes = response[3:3+17]
        try:
            return vin_bytes.decode('ascii')
        except:
            return None

    def _decode_dtc(self, dtc_bytes: bytes) -> Optional[str]:
        """
        Decode 2-byte DTC to string format.

        DTC Format:
          First 2 bits: System (P=00, C=01, B=10, U=11)
          Next 2 bits: First digit
          Remaining 12 bits: Last 3 digits (hex)

        Example: 0x0171 -> P0171
        """
        if len(dtc_bytes) != 2:
            return None

        dtc_value = struct.unpack('>H', dtc_bytes)[0]

        # Extract system code
        system_bits = (dtc_value >> 14) & 0x03
        system_map = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
        system = system_map[system_bits]

        # Extract digits
        digit1 = (dtc_value >> 12) & 0x03
        digit2 = (dtc_value >> 8) & 0x0F
        digit3 = (dtc_value >> 4) & 0x0F
        digit4 = dtc_value & 0x0F

        return f"{system}{digit1}{digit2:X}{digit3:X}{digit4:X}"

    def _decode_supported_pids(self, data: bytes, base: int) -> set:
        """Decode supported PIDs bitmap."""
        if len(data) != 4:
            return set()

        bitmap = struct.unpack('>I', data)[0]
        supported = set()

        for i in range(32):
            if bitmap & (1 << (31 - i)):
                supported.add(base + i + 1)

        return supported

    def _decode_monitor_status(self, data: bytes) -> Dict[str, Any]:
        """Decode monitor status (PID 01)."""
        if len(data) != 4:
            return {}

        byte_a = data[0]
        byte_b = data[1]
        byte_c = data[2]
        byte_d = data[3]

        return {
            'mil_on': bool(byte_a & 0x80),
            'dtc_count': byte_a & 0x7F,
            'tests_available': {
                'misfire': bool(byte_b & 0x01),
                'fuel_system': bool(byte_b & 0x02),
                'components': bool(byte_b & 0x04),
            },
            'tests_complete': {
                'misfire': bool(byte_c & 0x01),
                'fuel_system': bool(byte_c & 0x02),
                'components': bool(byte_c & 0x04),
                'catalyst': bool(byte_c & 0x08),
                'heated_catalyst': bool(byte_c & 0x10),
                'evap': bool(byte_c & 0x20),
                'secondary_air': bool(byte_c & 0x40),
                'ac_refrigerant': bool(byte_c & 0x80),
            }
        }

    def _decode_fuel_type(self, value: int) -> str:
        """Decode fuel type code."""
        fuel_types = {
            0x01: "Gasoline",
            0x02: "Methanol",
            0x03: "Ethanol",
            0x04: "Diesel",
            0x05: "LPG",
            0x06: "CNG",
            0x07: "Propane",
            0x08: "Electric",
            0x09: "Bifuel (Gasoline/Electric)",
            0x0A: "Bifuel (Gasoline/CNG)",
            0x0B: "Bifuel (Gasoline/LPG)",
            0x0C: "Bifuel (Gasoline/Propane)",
            0x0D: "Bifuel (Diesel/Electric)",
            0x0E: "Bifuel (Electric/ICE)",
            0x0F: "Hybrid (Gasoline/Electric)",
            0x10: "Hybrid (Ethanol/Electric)",
            0x11: "Hybrid (Diesel/Electric)",
            0x12: "Hybrid (Electric/ICE)",
        }
        return fuel_types.get(value, f"Unknown (0x{value:02X})")

# ELM327 Interface Implementation
class ELM327Interface:
    """ELM327 adapter interface for OBD-II communication."""

    def __init__(self, serial_port: str, baudrate: int = 38400):
        """
        Initialize ELM327 interface.

        Args:
            serial_port: Serial port device (e.g., '/dev/ttyUSB0')
            baudrate: Baud rate (default: 38400)
        """
        import serial
        self.serial = serial.Serial(serial_port, baudrate, timeout=1)
        self._initialize_elm327()

    def _initialize_elm327(self):
        """Initialize ELM327 adapter."""
        commands = [
            b'ATZ\r',      # Reset
            b'ATE0\r',     # Echo off
            b'ATL0\r',     # Linefeeds off
            b'ATS0\r',     # Spaces off
            b'ATH1\r',     # Headers on
            b'ATSP0\r',    # Auto protocol
        ]

        for cmd in commands:
            self.serial.write(cmd)
            time.sleep(0.1)
            response = self.serial.read_all()

    def send_request(self, request: bytes, timeout: float = 1.0) -> Optional[bytes]:
        """Send OBD-II request and receive response."""
        # Convert request to ASCII hex
        hex_string = request.hex().upper()
        command = hex_string.encode('ascii') + b'\r'

        # Send command
        self.serial.write(command)

        # Read response
        start_time = time.time()
        response_lines = []

        while time.time() - start_time < timeout:
            line = self.serial.readline()
            if not line:
                continue

            line = line.strip()
            if b'>' in line:
                break  # Prompt received
            if line and line != b'SEARCHING...':
                response_lines.append(line)

        if not response_lines:
            return None

        # Parse response
        try:
            # Remove spaces and decode hex
            hex_response = b''.join(response_lines).replace(b' ', b'')
            return bytes.fromhex(hex_response.decode('ascii'))
        except:
            return None

    def close(self):
        """Close serial connection."""
        self.serial.close()

# Example Usage
if __name__ == "__main__":
    # Initialize ELM327 interface
    elm_interface = ELM327Interface('/dev/ttyUSB0')

    # Create OBD-II instance
    obd = OBDII(elm_interface)

    # Query supported PIDs
    print("Querying supported PIDs...")
    supported = obd.query_supported_pids()
    print(f"Supported PIDs: {sorted(supported)}")

    # Read real-time data
    print("\nReading real-time data:")
    pids_to_read = [0x0C, 0x0D, 0x05, 0x11]  # RPM, Speed, Coolant, Throttle

    for pid in pids_to_read:
        result = obd.read_pid(pid)
        if result:
            print(f"{result['name']}: {result['value']} {result['unit']}")

    # Read DTCs
    print("\nReading stored DTCs:")
    dtcs = obd.read_dtcs()
    if dtcs:
        for dtc in dtcs:
            print(f"  {dtc}")
    else:
        print("  No DTCs found")

    # Read VIN
    print("\nReading VIN:")
    vin = obd.read_vin()
    if vin:
        print(f"  VIN: {vin}")

    # Clean up
    elm_interface.close()
```

## Readiness Monitors

OBD-II systems include continuous and non-continuous monitors:

**Continuous Monitors:**
- Misfire detection
- Fuel system monitoring
- Comprehensive component monitoring

**Non-Continuous Monitors:**
- Catalyst efficiency
- Heated catalyst
- Evaporative system
- Secondary air system
- A/C system refrigerant
- Oxygen sensor
- Oxygen sensor heater
- EGR system

## Freeze Frame Data

Captured when DTC is set, includes:
- Engine RPM
- Vehicle speed
- Coolant temperature
- Engine load
- Fuel trim
- Intake manifold pressure
- Throttle position

## Best Practices

1. **Always check for protocol support** before sending commands
2. **Query supported PIDs** to avoid unnecessary requests
3. **Handle slow responses** - some vehicles take 100ms+
4. **Clear DTCs only when appropriate** - may reset readiness monitors
5. **Monitor MIL status** - indicates emission-related faults
6. **Use freeze frame data** for diagnostics - provides fault context

## References

- SAE J1979 - E/E Diagnostic Test Modes
- SAE J2012 - Diagnostic Trouble Code Definitions
- ISO 15765-4 - Diagnostic communication over CAN (DoCAN)
