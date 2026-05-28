# DTC Management - Diagnostic Trouble Codes

## Overview

Diagnostic Trouble Codes (DTCs) are standardized codes that identify vehicle faults. This skill covers DTC structure, fault memory management, status bytes, snapshot data, and aging counters according to SAE J2012 and ISO 14229.

## DTC Structure

### Format: XNNNN

**First Character (System):**
- **P** - Powertrain (Engine, Transmission)
- **C** - Chassis (ABS, Steering, Suspension)
- **B** - Body (Airbags, HVAC, Seats)
- **U** - Network Communication (CAN, LIN, FlexRay)

**Second Character (Type):**
- **0** - Generic (SAE J2012 standardized)
- **1** - Manufacturer-specific
- **2** - Generic (SAE reserved)
- **3** - Manufacturer-specific

**Last Three Characters:**
- Specific fault code (000-999 hex)

### Examples

```
P0171 - System Too Lean (Bank 1) - Generic powertrain
P1234 - Fuel Pump Control Circuit - Manufacturer-specific
C0035 - Left Front Wheel Speed Sensor Circuit - Generic chassis
B1234 - Driver Airbag Circuit Shorted to Ground - Manufacturer-specific
U0100 - Lost Communication with ECM/PCM - Generic network
```

## DTC Status Byte (ISO 14229)

Each DTC has an 8-bit status byte:

```
Bit 0: testFailed                    - 0x01
Bit 1: testFailedThisOperationCycle  - 0x02
Bit 2: pendingDTC                    - 0x04
Bit 3: confirmedDTC                  - 0x08
Bit 4: testNotCompletedSinceLastClear - 0x10
Bit 5: testFailedSinceLastClear      - 0x20
Bit 6: testNotCompletedThisOperationCycle - 0x40
Bit 7: warningIndicatorRequested     - 0x80
```

**Status Examples:**
- `0x08` - Confirmed DTC (stored in memory)
- `0x04` - Pending DTC (occurred once, not confirmed)
- `0x88` - Confirmed DTC with MIL on
- `0x00` - DTC tested and passed

## Production Code - DTC Manager

```python
#!/usr/bin/env python3
"""
DTC Management System
Handles DTC reading, parsing, aging, and fault memory management
"""

from enum import IntEnum, Flag
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime
import json

class DTCSystem(IntEnum):
    """DTC system identifier."""
    POWERTRAIN = 0  # P
    CHASSIS = 1     # C
    BODY = 2        # B
    NETWORK = 3     # U

class DTCType(IntEnum):
    """DTC type identifier."""
    GENERIC_SAE = 0
    MANUFACTURER = 1
    GENERIC_RESERVED = 2
    MANUFACTURER_2 = 3

class DTCStatus(Flag):
    """DTC status byte flags (ISO 14229)."""
    TEST_FAILED = 0x01
    TEST_FAILED_THIS_CYCLE = 0x02
    PENDING_DTC = 0x04
    CONFIRMED_DTC = 0x08
    TEST_NOT_COMPLETED_SINCE_CLEAR = 0x10
    TEST_FAILED_SINCE_CLEAR = 0x20
    TEST_NOT_COMPLETED_THIS_CYCLE = 0x40
    WARNING_INDICATOR_REQUESTED = 0x80  # MIL

@dataclass
class SnapshotData:
    """Snapshot data captured when DTC was set."""
    timestamp: datetime
    engine_rpm: Optional[int] = None
    vehicle_speed: Optional[int] = None
    coolant_temp: Optional[int] = None
    engine_load: Optional[float] = None
    fuel_trim_bank1: Optional[float] = None
    intake_pressure: Optional[int] = None
    throttle_position: Optional[float] = None
    ambient_temp: Optional[int] = None
    odometer: Optional[int] = None
    custom_data: Dict = field(default_factory=dict)

@dataclass
class ExtendedData:
    """Extended data for DTC."""
    occurrence_counter: int = 0
    aging_counter: int = 0
    aged_counter: int = 0
    fault_detection_counter: int = 0
    max_fdc_since_clear: int = 0
    max_fdc_this_cycle: int = 0
    cycles_since_first_failed: int = 0
    cycles_since_last_failed: int = 0
    failed_cycles_counter: int = 0
    custom_data: Dict = field(default_factory=dict)

@dataclass
class DTC:
    """Diagnostic Trouble Code with full metadata."""
    code: str  # Format: PNNNN, CNNNN, BNNNN, UNNNN
    status: int  # Status byte
    description: str = ""
    system: Optional[DTCSystem] = None
    severity: str = "medium"  # low, medium, high, critical
    snapshot: Optional[SnapshotData] = None
    extended_data: Optional[ExtendedData] = None
    first_occurred: Optional[datetime] = None
    last_occurred: Optional[datetime] = None

    def __post_init__(self):
        """Parse DTC code to extract system."""
        if not self.system and len(self.code) >= 5:
            system_char = self.code[0].upper()
            system_map = {'P': DTCSystem.POWERTRAIN, 'C': DTCSystem.CHASSIS,
                         'B': DTCSystem.BODY, 'U': DTCSystem.NETWORK}
            self.system = system_map.get(system_char)

    @property
    def is_pending(self) -> bool:
        """Check if DTC is pending."""
        return bool(self.status & DTCStatus.PENDING_DTC)

    @property
    def is_confirmed(self) -> bool:
        """Check if DTC is confirmed."""
        return bool(self.status & DTCStatus.CONFIRMED_DTC)

    @property
    def is_mil_on(self) -> bool:
        """Check if MIL (Malfunction Indicator Lamp) is on."""
        return bool(self.status & DTCStatus.WARNING_INDICATOR_REQUESTED)

    @property
    def test_failed_this_cycle(self) -> bool:
        """Check if test failed in current operation cycle."""
        return bool(self.status & DTCStatus.TEST_FAILED_THIS_CYCLE)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'code': self.code,
            'status': f"0x{self.status:02X}",
            'description': self.description,
            'system': self.system.name if self.system else None,
            'severity': self.severity,
            'is_pending': self.is_pending,
            'is_confirmed': self.is_confirmed,
            'is_mil_on': self.is_mil_on,
            'snapshot': self.snapshot.__dict__ if self.snapshot else None,
            'extended_data': self.extended_data.__dict__ if self.extended_data else None,
        }

class DTCManager:
    """DTC fault memory manager."""

    def __init__(self, can_interface, dtc_database_file: Optional[str] = None):
        """
        Initialize DTC manager.

        Args:
            can_interface: CAN communication interface
            dtc_database_file: JSON file with DTC descriptions
        """
        self.can_interface = can_interface
        self.dtc_database: Dict[str, Dict] = {}
        self.active_dtcs: Dict[str, DTC] = {}

        if dtc_database_file:
            self._load_dtc_database(dtc_database_file)
        else:
            self._load_standard_dtcs()

    def _load_dtc_database(self, filename: str):
        """Load DTC descriptions from JSON file."""
        try:
            with open(filename, 'r') as f:
                self.dtc_database = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load DTC database: {e}")
            self._load_standard_dtcs()

    def _load_standard_dtcs(self):
        """Load common standardized DTCs (SAE J2012)."""
        standard_dtcs = {
            # Powertrain - Fuel/Air Metering
            "P0171": {"desc": "System Too Lean (Bank 1)", "severity": "medium"},
            "P0172": {"desc": "System Too Rich (Bank 1)", "severity": "medium"},
            "P0174": {"desc": "System Too Lean (Bank 2)", "severity": "medium"},
            "P0175": {"desc": "System Too Rich (Bank 2)", "severity": "medium"},

            # Powertrain - Ignition System
            "P0300": {"desc": "Random/Multiple Cylinder Misfire Detected", "severity": "high"},
            "P0301": {"desc": "Cylinder 1 Misfire Detected", "severity": "high"},
            "P0302": {"desc": "Cylinder 2 Misfire Detected", "severity": "high"},
            "P0303": {"desc": "Cylinder 3 Misfire Detected", "severity": "high"},
            "P0304": {"desc": "Cylinder 4 Misfire Detected", "severity": "high"},

            # Powertrain - Emission Control
            "P0420": {"desc": "Catalyst System Efficiency Below Threshold (Bank 1)", "severity": "medium"},
            "P0430": {"desc": "Catalyst System Efficiency Below Threshold (Bank 2)", "severity": "medium"},
            "P0440": {"desc": "Evaporative Emission System Malfunction", "severity": "low"},
            "P0442": {"desc": "Evaporative Emission System Leak Detected (Small Leak)", "severity": "low"},

            # Powertrain - Sensors
            "P0100": {"desc": "Mass or Volume Air Flow Circuit Malfunction", "severity": "medium"},
            "P0105": {"desc": "Manifold Absolute Pressure/Barometric Pressure Circuit Malfunction", "severity": "medium"},
            "P0110": {"desc": "Intake Air Temperature Circuit Malfunction", "severity": "low"},
            "P0115": {"desc": "Engine Coolant Temperature Circuit Malfunction", "severity": "medium"},
            "P0120": {"desc": "Throttle Position Sensor/Switch A Circuit Malfunction", "severity": "high"},
            "P0335": {"desc": "Crankshaft Position Sensor A Circuit Malfunction", "severity": "critical"},
            "P0340": {"desc": "Camshaft Position Sensor Circuit Malfunction", "severity": "critical"},

            # Chassis - ABS
            "C0035": {"desc": "Left Front Wheel Speed Sensor Circuit", "severity": "high"},
            "C0040": {"desc": "Right Front Wheel Speed Sensor Circuit", "severity": "high"},
            "C0045": {"desc": "Left Rear Wheel Speed Sensor Circuit", "severity": "high"},
            "C0050": {"desc": "Right Rear Wheel Speed Sensor Circuit", "severity": "high"},

            # Body - Airbag
            "B0001": {"desc": "Driver Airbag Circuit Shorted to Ground", "severity": "critical"},
            "B0002": {"desc": "Passenger Airbag Circuit Shorted to Ground", "severity": "critical"},

            # Network - Communication
            "U0100": {"desc": "Lost Communication With ECM/PCM A", "severity": "critical"},
            "U0101": {"desc": "Lost Communication With TCM", "severity": "high"},
            "U0121": {"desc": "Lost Communication With ABS Control Module", "severity": "high"},
            "U0140": {"desc": "Lost Communication With Body Control Module", "severity": "medium"},
        }

        self.dtc_database = standard_dtcs

    def read_dtcs(self, status_mask: int = 0xFF) -> List[DTC]:
        """
        Read DTCs from ECU.

        Args:
            status_mask: Status mask to filter DTCs (default: all DTCs)

        Returns:
            List of DTC objects
        """
        # UDS Service 0x19, Sub-function 0x02: reportDTCByStatusMask
        request = bytes([0x19, 0x02, status_mask])

        response = self.can_interface.send_diagnostic_request(request, timeout=2.0)

        if response is None or response[0] == 0x7F:
            return []

        # Parse response
        dtcs = []
        i = 4  # Skip header bytes

        while i + 3 < len(response):
            # Parse DTC (3 bytes + 1 status byte)
            dtc_bytes = response[i:i+3]
            status_byte = response[i+3]

            # Convert to DTC string
            dtc_code = self._parse_dtc_bytes(dtc_bytes)

            # Get description from database
            dtc_info = self.dtc_database.get(dtc_code, {})
            description = dtc_info.get("desc", "Unknown DTC")
            severity = dtc_info.get("severity", "medium")

            # Create DTC object
            dtc = DTC(
                code=dtc_code,
                status=status_byte,
                description=description,
                severity=severity,
                last_occurred=datetime.now()
            )

            dtcs.append(dtc)
            self.active_dtcs[dtc_code] = dtc

            i += 4

        return dtcs

    def read_dtc_snapshot(self, dtc_code: str, record_number: int = 0xFF) -> Optional[SnapshotData]:
        """
        Read snapshot data for a DTC.

        Args:
            dtc_code: DTC code (e.g., "P0171")
            record_number: Snapshot record number (0xFF = most recent)

        Returns:
            SnapshotData object or None
        """
        # Convert DTC code to bytes
        dtc_bytes = self._dtc_code_to_bytes(dtc_code)

        # UDS Service 0x19, Sub-function 0x04: reportDTCSnapshotRecordByDTCNumber
        request = bytes([0x19, 0x04]) + dtc_bytes + bytes([record_number])

        response = self.can_interface.send_diagnostic_request(request, timeout=2.0)

        if response is None or response[0] == 0x7F:
            return None

        # Parse snapshot data (simplified - actual format is ODX-defined)
        snapshot = SnapshotData(timestamp=datetime.now())

        # Example parsing (actual format depends on ECU)
        if len(response) >= 10:
            snapshot.engine_rpm = (response[6] << 8 | response[7]) // 4
            snapshot.vehicle_speed = response[8]
            snapshot.coolant_temp = response[9] - 40

        return snapshot

    def read_dtc_extended_data(self, dtc_code: str, record_number: int = 0xFF) -> Optional[ExtendedData]:
        """
        Read extended data for a DTC.

        Args:
            dtc_code: DTC code
            record_number: Extended data record number

        Returns:
            ExtendedData object or None
        """
        dtc_bytes = self._dtc_code_to_bytes(dtc_code)

        # UDS Service 0x19, Sub-function 0x06: reportDTCExtDataRecordByDTCNumber
        request = bytes([0x19, 0x06]) + dtc_bytes + bytes([record_number])

        response = self.can_interface.send_diagnostic_request(request, timeout=2.0)

        if response is None or response[0] == 0x7F:
            return None

        # Parse extended data (format is ODX-defined)
        extended = ExtendedData()

        if len(response) >= 10:
            extended.occurrence_counter = response[6]
            extended.aging_counter = response[7]
            extended.fault_detection_counter = response[8]

        return extended

    def clear_dtcs(self, group: int = 0xFFFFFF) -> bool:
        """
        Clear DTCs from fault memory.

        Args:
            group: DTC group to clear (0xFFFFFF = all DTCs)

        Returns:
            True if successful
        """
        # UDS Service 0x14: ClearDiagnosticInformation
        request = bytes([0x14, (group >> 16) & 0xFF, (group >> 8) & 0xFF, group & 0xFF])

        response = self.can_interface.send_diagnostic_request(request, timeout=2.0)

        if response is None:
            return False

        if response[0] == 0x7F:
            print(f"Clear DTCs failed: NRC 0x{response[2]:02X}")
            return False

        if response[0] == 0x54:
            print("DTCs cleared successfully")
            self.active_dtcs.clear()
            return True

        return False

    def get_dtc_count(self) -> int:
        """Get total number of confirmed DTCs."""
        # UDS Service 0x19, Sub-function 0x01: reportNumberOfDTCByStatusMask
        request = bytes([0x19, 0x01, 0x08])  # Confirmed DTCs

        response = self.can_interface.send_diagnostic_request(request, timeout=1.0)

        if response and len(response) >= 6:
            # Byte 3 contains availability mask
            # Bytes 4-5 contain count
            count = (response[4] << 8) | response[5]
            return count

        return 0

    def _parse_dtc_bytes(self, dtc_bytes: bytes) -> str:
        """
        Parse 3-byte DTC to string format.

        Format: [High byte][Mid byte][Low byte]
        High byte bits 7-6: System (00=P, 01=C, 10=B, 11=U)
        High byte bits 5-4: Type (0=Generic, 1=Manufacturer)
        Remaining 12 bits: Code digits
        """
        if len(dtc_bytes) != 3:
            return "UNKNOWN"

        high = dtc_bytes[0]
        mid = dtc_bytes[1]
        low = dtc_bytes[2]

        # Extract system
        system_bits = (high >> 6) & 0x03
        system_chars = ['P', 'C', 'B', 'U']
        system = system_chars[system_bits]

        # Extract type and first digit
        type_bit = (high >> 4) & 0x03
        digit1 = type_bit

        # Extract remaining digits
        digit2 = high & 0x0F
        digit3 = (mid >> 4) & 0x0F
        digit4 = mid & 0x0F

        return f"{system}{digit1}{digit2:X}{digit3:X}{digit4:X}"

    def _dtc_code_to_bytes(self, dtc_code: str) -> bytes:
        """Convert DTC string to 3-byte format."""
        if len(dtc_code) != 5:
            raise ValueError("Invalid DTC code format")

        # Parse system
        system = dtc_code[0].upper()
        system_map = {'P': 0, 'C': 1, 'B': 2, 'U': 3}
        system_bits = system_map.get(system, 0)

        # Parse digits
        digit1 = int(dtc_code[1])
        digit2 = int(dtc_code[2], 16)
        digit3 = int(dtc_code[3], 16)
        digit4 = int(dtc_code[4], 16)

        # Build bytes
        high = (system_bits << 6) | (digit1 << 4) | digit2
        mid = (digit3 << 4) | digit4
        low = 0x00  # Typically unused or manufacturer-specific

        return bytes([high, mid, low])

    def generate_report(self, dtcs: List[DTC]) -> str:
        """Generate human-readable DTC report."""
        if not dtcs:
            return "No DTCs found."

        report = []
        report.append(f"DTC Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)

        # Group by severity
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for dtc in dtcs:
            by_severity[dtc.severity].append(dtc)

        for severity in ['critical', 'high', 'medium', 'low']:
            severity_dtcs = by_severity[severity]
            if not severity_dtcs:
                continue

            report.append(f"\n{severity.upper()} Severity ({len(severity_dtcs)} DTCs):")
            report.append("-" * 80)

            for dtc in severity_dtcs:
                report.append(f"  {dtc.code}: {dtc.description}")
                report.append(f"    Status: 0x{dtc.status:02X} "
                            f"{'[MIL ON]' if dtc.is_mil_on else ''} "
                            f"{'[Confirmed]' if dtc.is_confirmed else '[Pending]'}")

                if dtc.snapshot:
                    report.append(f"    Snapshot: RPM={dtc.snapshot.engine_rpm}, "
                                f"Speed={dtc.snapshot.vehicle_speed} km/h")

        report.append("\n" + "=" * 80)
        return "\n".join(report)

# Example Usage
if __name__ == "__main__":
    from can_interface import SocketCANInterface

    # Initialize
    can_if = SocketCANInterface("can0", txid=0x7E0, rxid=0x7E8)
    dtc_mgr = DTCManager(can_if, "dtc_database.json")

    # Read all DTCs
    print("Reading DTCs...")
    dtcs = dtc_mgr.read_dtcs()

    print(f"Found {len(dtcs)} DTCs")

    # Generate report
    print(dtc_mgr.generate_report(dtcs))

    # Read snapshot for specific DTC
    if dtcs:
        first_dtc = dtcs[0]
        snapshot = dtc_mgr.read_dtc_snapshot(first_dtc.code)
        if snapshot:
            print(f"\nSnapshot for {first_dtc.code}:")
            print(f"  RPM: {snapshot.engine_rpm}")
            print(f"  Speed: {snapshot.vehicle_speed} km/h")
            print(f"  Coolant: {snapshot.coolant_temp}°C")
```

## DTC Aging and Healing

### Aging Counters

**Purpose:** Prevent fault memory from filling with intermittent faults

**Mechanism:**
1. DTC is stored when fault confirmed (typically 2-3 consecutive failures)
2. Aging counter increments each driving cycle without fault
3. DTC deleted when aging counter reaches threshold (typically 40-100 cycles)

### Healing Counters

**Purpose:** Track recovery from faults

**Mechanism:**
1. Fault Detection Counter (FDC) increments on fault conditions
2. FDC decrements (heals) when conditions normal
3. DTC confirmed when FDC reaches threshold

## WWH-OBD (Worldwide Harmonized OBD)

**Permanent DTCs:**
- Cannot be cleared with Mode 04 or UDS 0x14
- Only cleared when ECU determines fault is repaired
- Used for emission-critical faults
- Requires multiple driving cycles with passing monitors

## Best Practices

1. **Always read snapshot data** with DTCs for diagnosis context
2. **Check extended data** for occurrence and aging counters
3. **Clear DTCs only after repair** - premature clearing hides patterns
4. **Monitor status changes** - pending → confirmed indicates recurring fault
5. **Log all DTC events** for trend analysis and predictive maintenance
6. **Use severity levels** to prioritize repairs
7. **Correlate DTCs across ECUs** - root cause may be in different module

## References

- SAE J2012 - Diagnostic Trouble Code Definitions
- ISO 14229-1 - UDS Specification
- ISO 15031 - Road vehicles communication between vehicle and external equipment for emissions-related diagnostics
