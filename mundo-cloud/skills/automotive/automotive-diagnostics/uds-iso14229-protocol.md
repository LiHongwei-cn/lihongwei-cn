# UDS ISO 14229 Protocol - Unified Diagnostic Services

## Overview

UDS (Unified Diagnostic Services) ISO 14229 is the automotive industry standard for ECU diagnostics. This skill provides comprehensive implementation guidance for all UDS services with production-ready code examples.

## Core UDS Services

### Service 0x10: DiagnosticSessionControl

Controls diagnostic session state (default, programming, extended).

**Request Format:**
```
Byte 0: 0x10 (Service ID)
Byte 1: Session Type
  0x01 - Default Session
  0x02 - Programming Session
  0x03 - Extended Diagnostic Session
  0x04-0x7F - OEM/Supplier specific
```

**Response Format:**
```
Byte 0: 0x50 (Positive Response)
Byte 1: Session Type (echo)
Byte 2-3: P2Server timing (ms)
Byte 4-5: P2*Server extended timing (ms × 10)
```

**Production Code (Python):**
```python
#!/usr/bin/env python3
"""
UDS Service 0x10 - DiagnosticSessionControl Implementation
ISO 14229-1:2020 compliant
"""

import struct
import time
from enum import IntEnum
from typing import Tuple, Optional

class DiagnosticSession(IntEnum):
    DEFAULT = 0x01
    PROGRAMMING = 0x02
    EXTENDED = 0x03
    SAFETY_SYSTEM = 0x04

class UDSSessionController:
    def __init__(self, can_interface):
        self.can_interface = can_interface
        self.current_session = DiagnosticSession.DEFAULT
        self.p2_server = 50  # ms, default
        self.p2_star_server = 5000  # ms, default
        self.session_timeout = 5.0  # S3Server timer (seconds)
        self.last_activity = time.time()

    def change_session(self, session: DiagnosticSession) -> Tuple[bool, str]:
        """
        Change diagnostic session.

        Args:
            session: Target diagnostic session

        Returns:
            Tuple of (success, message)
        """
        # Build request
        request = bytearray([0x10, session])

        # Send request
        response = self.can_interface.send_diagnostic_request(
            request,
            timeout=self.p2_server / 1000.0
        )

        if response is None:
            return False, "No response from ECU"

        # Check for negative response
        if response[0] == 0x7F:
            nrc = response[2]
            return False, f"Negative response: {self._decode_nrc(nrc)}"

        # Check positive response
        if response[0] != 0x50 or response[1] != session:
            return False, "Invalid response format"

        # Parse timing parameters
        if len(response) >= 6:
            self.p2_server = struct.unpack('>H', response[2:4])[0]
            self.p2_star_server = struct.unpack('>H', response[4:6])[0] * 10

        self.current_session = session
        self.last_activity = time.time()

        return True, f"Session changed to {session.name}"

    def _decode_nrc(self, nrc: int) -> str:
        """Decode negative response code."""
        nrc_map = {
            0x11: "serviceNotSupported",
            0x12: "subFunctionNotSupported",
            0x13: "incorrectMessageLengthOrInvalidFormat",
            0x22: "conditionsNotCorrect",
            0x24: "requestSequenceError",
            0x33: "securityAccessDenied",
        }
        return nrc_map.get(nrc, f"Unknown NRC: 0x{nrc:02X}")

# Example usage
if __name__ == "__main__":
    from can_interface import SocketCANInterface

    # Initialize CAN interface
    can_if = SocketCANInterface("can0", txid=0x7E0, rxid=0x7E8)

    # Create session controller
    controller = UDSSessionController(can_if)

    # Change to extended diagnostic session
    success, msg = controller.change_session(DiagnosticSession.EXTENDED)
    print(f"Session change: {msg}")
    print(f"P2Server: {controller.p2_server}ms")
    print(f"P2*Server: {controller.p2_star_server}ms")
```

### Service 0x22: ReadDataByIdentifier

Reads ECU data by Data Identifier (DID).

**Request Format:**
```
Byte 0: 0x22 (Service ID)
Byte 1-2: DID (2 bytes, big-endian)
[Optional: Additional DIDs]
```

**Production Code (Python):**
```python
#!/usr/bin/env python3
"""
UDS Service 0x22 - ReadDataByIdentifier Implementation
Supports multiple DIDs, ODX scaling, and caching
"""

import struct
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class DIDMetadata:
    """Metadata for a Data Identifier."""
    did: int
    name: str
    length: int  # bytes
    data_type: str  # 'uint8', 'uint16', 'uint32', 'ascii', 'binary'
    scale: float = 1.0
    offset: float = 0.0
    unit: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None

class UDSDataReader:
    def __init__(self, can_interface, odx_file: Optional[str] = None):
        self.can_interface = can_interface
        self.did_cache: Dict[int, Any] = {}
        self.did_metadata: Dict[int, DIDMetadata] = {}

        if odx_file:
            self._load_odx_metadata(odx_file)
        else:
            self._load_default_metadata()

    def _load_default_metadata(self):
        """Load common DIDs metadata."""
        common_dids = [
            DIDMetadata(0xF186, "ActiveDiagnosticSession", 1, "uint8"),
            DIDMetadata(0xF187, "VehicleManufacturerSparePartNumber", 11, "ascii"),
            DIDMetadata(0xF188, "VehicleManufacturerECUSoftwareNumber", 11, "ascii"),
            DIDMetadata(0xF189, "VehicleManufacturerECUSoftwareVersionNumber", 4, "ascii"),
            DIDMetadata(0xF18A, "SystemSupplierIdentifier", 16, "ascii"),
            DIDMetadata(0xF18C, "ECUSerialNumber", 16, "ascii"),
            DIDMetadata(0xF190, "VIN", 17, "ascii"),
            DIDMetadata(0xF191, "VehicleManufacturerECUHardwareNumber", 11, "ascii"),
            DIDMetadata(0xF194, "SystemSupplierECUHardwareNumber", 11, "ascii"),
            DIDMetadata(0xF195, "SystemSupplierECUSoftwareNumber", 11, "ascii"),
        ]

        for did_meta in common_dids:
            self.did_metadata[did_meta.did] = did_meta

    def _load_odx_metadata(self, odx_file: str):
        """Load DID metadata from ODX file."""
        # In production, parse ODX XML using odxtools library
        # This is a simplified example
        try:
            with open(odx_file, 'r') as f:
                odx_data = json.load(f)  # Assuming preprocessed JSON

            for did_entry in odx_data.get('dids', []):
                did_meta = DIDMetadata(
                    did=int(did_entry['id'], 16),
                    name=did_entry['name'],
                    length=did_entry['length'],
                    data_type=did_entry['type'],
                    scale=did_entry.get('scale', 1.0),
                    offset=did_entry.get('offset', 0.0),
                    unit=did_entry.get('unit', ''),
                )
                self.did_metadata[did_meta.did] = did_meta
        except Exception as e:
            print(f"Warning: Could not load ODX file: {e}")
            self._load_default_metadata()

    def read_did(self, did: int, use_cache: bool = False) -> Optional[Dict[str, Any]]:
        """
        Read single DID from ECU.

        Args:
            did: Data Identifier (0x0000-0xFFFF)
            use_cache: Use cached value if available

        Returns:
            Dictionary with raw value, scaled value, and metadata
        """
        # Check cache
        if use_cache and did in self.did_cache:
            return self.did_cache[did]

        # Build request
        request = bytearray([0x22, (did >> 8) & 0xFF, did & 0xFF])

        # Send request
        response = self.can_interface.send_diagnostic_request(request, timeout=1.0)

        if response is None:
            return None

        # Check for negative response
        if response[0] == 0x7F:
            print(f"Negative response for DID 0x{did:04X}: NRC 0x{response[2]:02X}")
            return None

        # Check positive response
        if response[0] != 0x62:
            print(f"Invalid response service ID: 0x{response[0]:02X}")
            return None

        # Parse response
        response_did = struct.unpack('>H', response[1:3])[0]
        if response_did != did:
            print(f"DID mismatch: requested 0x{did:04X}, got 0x{response_did:04X}")
            return None

        # Extract data
        data = response[3:]

        # Parse based on metadata
        parsed_value = self._parse_did_data(did, data)

        result = {
            'did': did,
            'raw_data': data.hex(),
            'parsed_value': parsed_value,
            'metadata': self.did_metadata.get(did),
        }

        # Cache result
        self.did_cache[did] = result

        return result

    def read_multiple_dids(self, dids: List[int]) -> Dict[int, Optional[Dict[str, Any]]]:
        """
        Read multiple DIDs in separate requests.
        Note: Some ECUs support multiple DIDs in one request, but not standardized.

        Args:
            dids: List of DIDs to read

        Returns:
            Dictionary mapping DID to result
        """
        results = {}
        for did in dids:
            results[did] = self.read_did(did)
        return results

    def _parse_did_data(self, did: int, data: bytes) -> Any:
        """Parse DID data based on metadata."""
        metadata = self.did_metadata.get(did)

        if metadata is None:
            return data.hex()  # Return hex string if unknown

        try:
            if metadata.data_type == 'ascii':
                return data.decode('ascii').rstrip('\x00')
            elif metadata.data_type == 'uint8':
                value = data[0]
            elif metadata.data_type == 'uint16':
                value = struct.unpack('>H', data[:2])[0]
            elif metadata.data_type == 'uint32':
                value = struct.unpack('>I', data[:4])[0]
            elif metadata.data_type == 'int16':
                value = struct.unpack('>h', data[:2])[0]
            elif metadata.data_type == 'int32':
                value = struct.unpack('>i', data[:4])[0]
            else:
                return data.hex()

            # Apply scaling
            if metadata.data_type.startswith('uint') or metadata.data_type.startswith('int'):
                scaled_value = value * metadata.scale + metadata.offset
                return {
                    'raw': value,
                    'scaled': scaled_value,
                    'unit': metadata.unit,
                }

            return value

        except Exception as e:
            print(f"Error parsing DID 0x{did:04X}: {e}")
            return data.hex()

# Example usage
if __name__ == "__main__":
    from can_interface import SocketCANInterface

    # Initialize
    can_if = SocketCANInterface("can0", txid=0x7E0, rxid=0x7E8)
    reader = UDSDataReader(can_if)

    # Read VIN
    vin_result = reader.read_did(0xF190)
    if vin_result:
        print(f"VIN: {vin_result['parsed_value']}")

    # Read multiple DIDs
    dids_to_read = [0xF186, 0xF187, 0xF190]
    results = reader.read_multiple_dids(dids_to_read)

    for did, result in results.items():
        if result:
            print(f"DID 0x{did:04X}: {result['parsed_value']}")
```

### Service 0x27: SecurityAccess

Implements seed-key security access mechanism.

**Production Code (Python):**
```python
#!/usr/bin/env python3
"""
UDS Service 0x27 - SecurityAccess Implementation
Supports multiple security levels and configurable seed-key algorithms
"""

import struct
from typing import Callable, Optional, Tuple
import hashlib

class SecurityAccessLevel:
    """Security access level definitions."""
    LEVEL_1 = 0x01  # Request seed for level 1
    LEVEL_1_KEY = 0x02  # Send key for level 1
    LEVEL_2 = 0x03  # Request seed for level 2
    LEVEL_2_KEY = 0x04  # Send key for level 2

class UDSSecurityAccess:
    def __init__(self, can_interface):
        self.can_interface = can_interface
        self.security_level_unlocked = 0
        self.seed_key_algorithms = {}
        self._register_default_algorithms()

    def _register_default_algorithms(self):
        """Register default seed-key algorithms."""
        # Example: Simple XOR-based algorithm (NOT SECURE - for demo only)
        def level1_algorithm(seed: bytes) -> bytes:
            key = bytearray(len(seed))
            for i, b in enumerate(seed):
                key[i] = b ^ 0xA5  # XOR with constant
            return bytes(key)

        # Example: Hash-based algorithm
        def level2_algorithm(seed: bytes) -> bytes:
            # Use SHA256 and take first 4 bytes
            hash_obj = hashlib.sha256(seed + b'SECRET_CONSTANT')
            return hash_obj.digest()[:4]

        self.register_seed_key_algorithm(SecurityAccessLevel.LEVEL_1, level1_algorithm)
        self.register_seed_key_algorithm(SecurityAccessLevel.LEVEL_2, level2_algorithm)

    def register_seed_key_algorithm(
        self,
        level: int,
        algorithm: Callable[[bytes], bytes]
    ):
        """
        Register a seed-key algorithm for a security level.

        Args:
            level: Security access level (odd number for seed request)
            algorithm: Function that takes seed bytes and returns key bytes
        """
        self.seed_key_algorithms[level] = algorithm

    def request_seed(self, level: int) -> Optional[bytes]:
        """
        Request seed from ECU for given security level.

        Args:
            level: Security access level (must be odd: 0x01, 0x03, 0x05, etc.)

        Returns:
            Seed bytes from ECU, or None on error
        """
        if level % 2 == 0:
            raise ValueError("Level must be odd for seed request")

        # Build request
        request = bytearray([0x27, level])

        # Send request
        response = self.can_interface.send_diagnostic_request(request, timeout=1.0)

        if response is None:
            print("No response from ECU")
            return None

        # Check for negative response
        if response[0] == 0x7F:
            nrc = response[2]
            print(f"Negative response: NRC 0x{nrc:02X}")
            if nrc == 0x24:
                print("  requestSequenceError - already unlocked or invalid sequence")
            elif nrc == 0x37:
                print("  requiredTimeDelayNotExpired - wait before retry")
            elif nrc == 0x36:
                print("  exceededNumberOfAttempts - too many failed attempts")
            return None

        # Check positive response
        if response[0] != 0x67 or response[1] != level:
            print(f"Invalid response format")
            return None

        # Check if already unlocked (seed = 0x00...)
        seed = response[2:]
        if all(b == 0 for b in seed):
            print(f"Security level {level} already unlocked")
            self.security_level_unlocked = level
            return None

        return seed

    def send_key(self, level: int, key: bytes) -> bool:
        """
        Send key to ECU for given security level.

        Args:
            level: Security access level (must be even: 0x02, 0x04, 0x06, etc.)
            key: Key bytes calculated from seed

        Returns:
            True if access granted, False otherwise
        """
        if level % 2 != 0:
            raise ValueError("Level must be even for key sending")

        # Build request
        request = bytearray([0x27, level]) + key

        # Send request
        response = self.can_interface.send_diagnostic_request(request, timeout=1.0)

        if response is None:
            print("No response from ECU")
            return False

        # Check for negative response
        if response[0] == 0x7F:
            nrc = response[2]
            print(f"Negative response: NRC 0x{nrc:02X}")
            if nrc == 0x35:
                print("  invalidKey - key calculation incorrect")
            elif nrc == 0x36:
                print("  exceededNumberOfAttempts - ECU locked out")
            return False

        # Check positive response
        if response[0] != 0x67 or response[1] != level:
            print("Invalid response format")
            return False

        print(f"Security level {level - 1} unlocked successfully")
        self.security_level_unlocked = level - 1
        return True

    def unlock_security_level(self, level: int) -> bool:
        """
        Complete security access procedure (request seed + send key).

        Args:
            level: Security access level (odd number: 0x01, 0x03, etc.)

        Returns:
            True if access granted, False otherwise
        """
        # Get algorithm
        algorithm = self.seed_key_algorithms.get(level)
        if algorithm is None:
            print(f"No seed-key algorithm registered for level {level}")
            return False

        # Request seed
        seed = self.request_seed(level)
        if seed is None:
            # Already unlocked or error
            return self.security_level_unlocked == level

        # Calculate key
        try:
            key = algorithm(seed)
        except Exception as e:
            print(f"Error calculating key: {e}")
            return False

        # Send key
        return self.send_key(level + 1, key)

    def is_security_level_unlocked(self, level: int) -> bool:
        """Check if security level is currently unlocked."""
        return self.security_level_unlocked >= level

# Example usage
if __name__ == "__main__":
    from can_interface import SocketCANInterface

    # Initialize
    can_if = SocketCANInterface("can0", txid=0x7E0, rxid=0x7E8)
    security = UDSSecurityAccess(can_if)

    # Unlock security level 1
    if security.unlock_security_level(SecurityAccessLevel.LEVEL_1):
        print("Security access level 1 granted")

        # Now can perform protected operations
        # ...
    else:
        print("Security access denied")
```

## CAN Interface Implementation

**Production Code (Python):**
```python
#!/usr/bin/env python3
"""
SocketCAN interface for UDS communication
Supports ISO-TP (ISO 15765-2) transport protocol
"""

import can
import isotp
import time
from typing import Optional

class SocketCANInterface:
    """CAN interface using python-can and python-can-isotp."""

    def __init__(self, channel: str, txid: int, rxid: int, bitrate: int = 500000):
        """
        Initialize CAN interface.

        Args:
            channel: CAN interface name (e.g., 'can0')
            txid: CAN ID for sending (tester address)
            rxid: CAN ID for receiving (ECU response address)
            bitrate: CAN bus bitrate in bps
        """
        self.channel = channel
        self.txid = txid
        self.rxid = rxid

        # Initialize CAN bus
        self.bus = can.interface.Bus(
            channel=channel,
            bustype='socketcan',
            bitrate=bitrate
        )

        # Initialize ISO-TP stack
        self.isotp_params = isotp.params.LinkLayerProtocol.CAN()
        self.isotp_params.tx_data_length = 8
        self.isotp_params.tx_data_min_length = 8

        self.isotp_address = isotp.Address(
            isotp.AddressingMode.Normal_11bits,
            txid=txid,
            rxid=rxid
        )

        self.isotp_stack = isotp.CanStack(
            bus=self.bus,
            address=self.isotp_address,
            params=self.isotp_params
        )

    def send_diagnostic_request(
        self,
        request: bytes,
        timeout: float = 1.0
    ) -> Optional[bytes]:
        """
        Send diagnostic request and wait for response.

        Args:
            request: Request bytes to send
            timeout: Response timeout in seconds

        Returns:
            Response bytes or None on timeout/error
        """
        # Start ISO-TP stack
        self.isotp_stack.start()

        try:
            # Send request
            self.isotp_stack.send(request)

            # Wait for response
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.isotp_stack.available():
                    response = self.isotp_stack.recv()
                    return response
                time.sleep(0.001)

            print("Response timeout")
            return None

        except Exception as e:
            print(f"Error during communication: {e}")
            return None

        finally:
            # Stop ISO-TP stack
            self.isotp_stack.stop()

    def close(self):
        """Close CAN interface."""
        self.isotp_stack.stop()
        self.bus.shutdown()

# Example usage
if __name__ == "__main__":
    # Initialize interface
    can_if = SocketCANInterface("can0", txid=0x7E0, rxid=0x7E8)

    # Send TesterPresent
    request = bytes([0x3E, 0x00])
    response = can_if.send_diagnostic_request(request)

    if response:
        print(f"Response: {response.hex()}")

    # Clean up
    can_if.close()
```

## UDS Timing Parameters

### P2 and P2* Timing

- **P2Client**: Default timeout for ECU response (typically 50ms)
- **P2Server**: ECU-specific timeout from DiagnosticSessionControl response
- **P2*Server**: Extended timeout for long-running operations (e.g., flash erase)

### S3 Timing

- **S3Client**: Session timeout (typically 5 seconds)
- Tester must send TesterPresent (0x3E) within S3 period to maintain session

## Error Handling - Negative Response Codes (NRC)

Common NRCs:
```
0x11 - serviceNotSupported
0x12 - subFunctionNotSupported
0x13 - incorrectMessageLengthOrInvalidFormat
0x21 - busyRepeatRequest (retry after delay)
0x22 - conditionsNotCorrect
0x24 - requestSequenceError
0x31 - requestOutOfRange
0x33 - securityAccessDenied
0x35 - invalidKey
0x36 - exceededNumberOfAttempts
0x37 - requiredTimeDelayNotExpired
0x78 - requestCorrectlyReceived-ResponsePending (wait for final response)
```

## Best Practices

1. **Always check for negative responses** before parsing positive response
2. **Implement proper timeout handling** with P2/P2* awareness
3. **Maintain session** with periodic TesterPresent during long operations
4. **Handle security access carefully** - too many failures can lock ECU
5. **Validate response length and format** before parsing
6. **Log all diagnostic operations** for traceability
7. **Use ODX databases** for DID metadata and scaling

## Testing

```python
#!/usr/bin/env python3
"""Unit tests for UDS implementation."""

import unittest
from unittest.mock import Mock, MagicMock
from uds_session_controller import UDSSessionController, DiagnosticSession

class TestUDSSession(unittest.TestCase):
    def setUp(self):
        self.mock_can = Mock()
        self.controller = UDSSessionController(self.mock_can)

    def test_session_change_success(self):
        """Test successful session change."""
        # Mock positive response
        self.mock_can.send_diagnostic_request.return_value = bytes([
            0x50, 0x03,  # Positive response, extended session
            0x00, 0x32,  # P2Server = 50ms
            0x07, 0xD0,  # P2*Server = 2000ms (200 * 10)
        ])

        success, msg = self.controller.change_session(DiagnosticSession.EXTENDED)

        self.assertTrue(success)
        self.assertEqual(self.controller.current_session, DiagnosticSession.EXTENDED)
        self.assertEqual(self.controller.p2_server, 50)
        self.assertEqual(self.controller.p2_star_server, 20000)

    def test_session_change_negative_response(self):
        """Test negative response handling."""
        # Mock negative response
        self.mock_can.send_diagnostic_request.return_value = bytes([
            0x7F, 0x10, 0x22  # NRC: conditionsNotCorrect
        ])

        success, msg = self.controller.change_session(DiagnosticSession.PROGRAMMING)

        self.assertFalse(success)
        self.assertIn("conditionsNotCorrect", msg)

if __name__ == '__main__':
    unittest.main()
```

## References

- ISO 14229-1:2020 - Unified diagnostic services (UDS) - Part 1: Application layer
- ISO 14229-2:2013 - Session layer services
- ISO 15765-2:2016 - Diagnostic communication over Controller Area Network (DoCAN)
