# DoIP - Diagnostics over IP (ISO 13400)

## Overview

DoIP enables automotive diagnostics over Ethernet/IP networks, replacing traditional CAN-based diagnostics for modern vehicles. Supports TCP/IP for diagnostic messages and UDP for vehicle discovery.

## Protocol Structure

### DoIP Header (8 bytes)

```
Byte 0:    Protocol Version (0x02 or 0x03)
Byte 1:    Inverse Protocol Version (0xFD or 0xFC)
Byte 2-3:  Payload Type (big-endian)
Byte 4-7:  Payload Length (big-endian)
```

### Common Payload Types

```
0x0001 - Vehicle identification request
0x0002 - Vehicle identification request with EID
0x0003 - Vehicle identification request with VIN
0x0004 - Vehicle announcement/identification response
0x0005 - Routing activation request
0x0006 - Routing activation response
0x0007 - Alive check request
0x0008 - Alive check response
0x8001 - Diagnostic message
0x8002 - Diagnostic message positive acknowledgement
0x8003 - Diagnostic message negative acknowledgement
```

## Production Code - DoIP Implementation

```python
#!/usr/bin/env python3
"""
DoIP (Diagnostics over IP) Implementation
ISO 13400-2:2019 compliant
"""

import socket
import struct
import threading
import time
from enum import IntEnum
from typing import Optional, Tuple, List
from dataclasses import dataclass

class DoIPPayloadType(IntEnum):
    """DoIP payload type identifiers."""
    VEHICLE_ID_REQUEST = 0x0001
    VEHICLE_ID_REQUEST_EID = 0x0002
    VEHICLE_ID_REQUEST_VIN = 0x0003
    VEHICLE_ANNOUNCEMENT = 0x0004
    ROUTING_ACTIVATION_REQUEST = 0x0005
    ROUTING_ACTIVATION_RESPONSE = 0x0006
    ALIVE_CHECK_REQUEST = 0x0007
    ALIVE_CHECK_RESPONSE = 0x0008
    ENTITY_STATUS_REQUEST = 0x4001
    ENTITY_STATUS_RESPONSE = 0x4002
    POWER_MODE_REQUEST = 0x4003
    POWER_MODE_RESPONSE = 0x4004
    DIAGNOSTIC_MESSAGE = 0x8001
    DIAGNOSTIC_MESSAGE_ACK = 0x8002
    DIAGNOSTIC_MESSAGE_NACK = 0x8003

class RoutingActivationType(IntEnum):
    """Routing activation types."""
    DEFAULT = 0x00
    WWH_OBD = 0x01
    CENTRAL_SECURITY = 0xE0

class DoIPNACK(IntEnum):
    """Diagnostic message negative acknowledgement codes."""
    INVALID_SOURCE_ADDRESS = 0x02
    UNKNOWN_TARGET_ADDRESS = 0x03
    MESSAGE_TOO_LARGE = 0x04
    OUT_OF_MEMORY = 0x05
    TARGET_UNREACHABLE = 0x06
    UNKNOWN_NETWORK = 0x07
    TRANSPORT_PROTOCOL_ERROR = 0x08

@dataclass
class DoIPVehicleInfo:
    """Vehicle information from DoIP announcement."""
    vin: str
    logical_address: int
    eid: bytes
    gid: bytes
    further_action: int
    vin_sync_status: Optional[int] = None

class DoIPHeader:
    """DoIP protocol header."""
    PROTOCOL_VERSION = 0x02
    INVERSE_VERSION = 0xFD

    @staticmethod
    def build(payload_type: int, payload_length: int) -> bytes:
        """Build DoIP header."""
        return struct.pack(
            '>BBHI',
            DoIPHeader.PROTOCOL_VERSION,
            DoIPHeader.INVERSE_VERSION,
            payload_type,
            payload_length
        )

    @staticmethod
    def parse(data: bytes) -> Tuple[int, int, int]:
        """
        Parse DoIP header.

        Returns:
            Tuple of (protocol_version, payload_type, payload_length)
        """
        if len(data) < 8:
            raise ValueError("Header too short")

        version, inv_version, payload_type, payload_length = struct.unpack('>BBHI', data[:8])

        if version != DoIPHeader.PROTOCOL_VERSION:
            raise ValueError(f"Invalid protocol version: {version}")

        if inv_version != DoIPHeader.INVERSE_VERSION:
            raise ValueError(f"Invalid inverse version: {inv_version}")

        return version, payload_type, payload_length

class DoIPClient:
    """DoIP client for diagnostic communication over Ethernet."""

    def __init__(self, gateway_ip: str, gateway_port: int = 13400):
        """
        Initialize DoIP client.

        Args:
            gateway_ip: DoIP gateway IP address
            gateway_port: DoIP TCP port (default: 13400)
        """
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.tcp_socket: Optional[socket.socket] = None
        self.udp_socket: Optional[socket.socket] = None
        self.source_address = 0x0E00  # Tester address
        self.target_address = 0x0000  # ECU address (set during routing activation)
        self.is_activated = False
        self.alive_check_thread: Optional[threading.Thread] = None
        self.alive_check_running = False

    def discover_vehicles(self, timeout: float = 2.0) -> List[DoIPVehicleInfo]:
        """
        Discover DoIP vehicles on network via UDP broadcast.

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            List of discovered vehicles
        """
        vehicles = []

        # Create UDP socket
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_sock.settimeout(timeout)

        try:
            # Build vehicle identification request
            header = DoIPHeader.build(DoIPPayloadType.VEHICLE_ID_REQUEST, 0)

            # Broadcast request
            udp_sock.sendto(header, ('<broadcast>', 13400))

            # Receive responses
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = udp_sock.recvfrom(4096)
                    vehicle = self._parse_vehicle_announcement(data)
                    if vehicle:
                        vehicles.append(vehicle)
                except socket.timeout:
                    break

        finally:
            udp_sock.close()

        return vehicles

    def connect(self, target_address: int = 0x0001,
                routing_type: RoutingActivationType = RoutingActivationType.DEFAULT) -> bool:
        """
        Connect to DoIP gateway and activate routing.

        Args:
            target_address: Target ECU logical address
            routing_type: Routing activation type

        Returns:
            True if connection and routing activation successful
        """
        self.target_address = target_address

        # Create TCP socket
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(5.0)

        try:
            # Connect to gateway
            self.tcp_socket.connect((self.gateway_ip, self.gateway_port))

            # Activate routing
            if not self._activate_routing(routing_type):
                self.disconnect()
                return False

            # Start alive check thread
            self._start_alive_check()

            self.is_activated = True
            return True

        except Exception as e:
            print(f"Connection failed: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """Disconnect from DoIP gateway."""
        self._stop_alive_check()

        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except:
                pass
            self.tcp_socket = None

        self.is_activated = False

    def send_diagnostic(self, request: bytes, timeout: float = 2.0) -> Optional[bytes]:
        """
        Send diagnostic request and receive response.

        Args:
            request: UDS request bytes
            timeout: Response timeout in seconds

        Returns:
            UDS response bytes or None
        """
        if not self.is_activated or not self.tcp_socket:
            print("Not connected or routing not activated")
            return None

        # Build diagnostic message
        payload = struct.pack('>HH', self.source_address, self.target_address) + request
        header = DoIPHeader.build(DoIPPayloadType.DIAGNOSTIC_MESSAGE, len(payload))
        message = header + payload

        # Send diagnostic message
        try:
            self.tcp_socket.sendall(message)
        except Exception as e:
            print(f"Send failed: {e}")
            return None

        # Wait for acknowledgement
        ack_data = self._receive_message(timeout=1.0)
        if not ack_data:
            return None

        _, ack_type, _ = DoIPHeader.parse(ack_data)

        if ack_type == DoIPPayloadType.DIAGNOSTIC_MESSAGE_NACK:
            nack_code = ack_data[8]
            print(f"Diagnostic NACK: {DoIPNACK(nack_code).name}")
            return None

        # Wait for diagnostic response
        response_data = self._receive_message(timeout=timeout)
        if not response_data:
            return None

        _, resp_type, resp_len = DoIPHeader.parse(response_data)

        if resp_type != DoIPPayloadType.DIAGNOSTIC_MESSAGE:
            print(f"Unexpected response type: 0x{resp_type:04X}")
            return None

        # Extract UDS response (skip source/target addresses)
        uds_response = response_data[12:]
        return uds_response

    def _activate_routing(self, routing_type: RoutingActivationType) -> bool:
        """Activate routing to target ECU."""
        # Build routing activation request
        payload = struct.pack('>HB', self.source_address, routing_type)
        payload += b'\x00\x00\x00\x00'  # Reserved (OEM specific)

        header = DoIPHeader.build(DoIPPayloadType.ROUTING_ACTIVATION_REQUEST, len(payload))
        message = header + payload

        # Send request
        self.tcp_socket.sendall(message)

        # Wait for response
        response = self._receive_message(timeout=2.0)
        if not response:
            return False

        _, resp_type, _ = DoIPHeader.parse(response)

        if resp_type != DoIPPayloadType.ROUTING_ACTIVATION_RESPONSE:
            print(f"Unexpected response type: 0x{resp_type:04X}")
            return False

        # Parse routing activation response
        tester_addr, entity_addr, response_code = struct.unpack('>HHB', response[8:13])

        if response_code == 0x10:
            print(f"Routing activated: Tester=0x{tester_addr:04X}, ECU=0x{entity_addr:04X}")
            return True
        else:
            print(f"Routing activation failed: code=0x{response_code:02X}")
            return False

    def _receive_message(self, timeout: float = 2.0) -> Optional[bytes]:
        """Receive complete DoIP message."""
        if not self.tcp_socket:
            return None

        original_timeout = self.tcp_socket.gettimeout()
        self.tcp_socket.settimeout(timeout)

        try:
            # Receive header
            header = b''
            while len(header) < 8:
                chunk = self.tcp_socket.recv(8 - len(header))
                if not chunk:
                    return None
                header += chunk

            # Parse header
            _, _, payload_length = DoIPHeader.parse(header)

            # Receive payload
            payload = b''
            while len(payload) < payload_length:
                chunk = self.tcp_socket.recv(payload_length - len(payload))
                if not chunk:
                    return None
                payload += chunk

            return header + payload

        except socket.timeout:
            return None
        except Exception as e:
            print(f"Receive error: {e}")
            return None
        finally:
            self.tcp_socket.settimeout(original_timeout)

    def _parse_vehicle_announcement(self, data: bytes) -> Optional[DoIPVehicleInfo]:
        """Parse vehicle announcement message."""
        try:
            _, payload_type, _ = DoIPHeader.parse(data)

            if payload_type != DoIPPayloadType.VEHICLE_ANNOUNCEMENT:
                return None

            # Parse payload
            vin = data[8:25].decode('ascii')
            logical_address = struct.unpack('>H', data[25:27])[0]
            eid = data[27:33]
            gid = data[33:39]
            further_action = data[39]

            return DoIPVehicleInfo(
                vin=vin,
                logical_address=logical_address,
                eid=eid,
                gid=gid,
                further_action=further_action
            )

        except Exception as e:
            print(f"Error parsing vehicle announcement: {e}")
            return None

    def _start_alive_check(self):
        """Start alive check thread."""
        self.alive_check_running = True
        self.alive_check_thread = threading.Thread(target=self._alive_check_worker)
        self.alive_check_thread.daemon = True
        self.alive_check_thread.start()

    def _stop_alive_check(self):
        """Stop alive check thread."""
        self.alive_check_running = False
        if self.alive_check_thread:
            self.alive_check_thread.join(timeout=1.0)

    def _alive_check_worker(self):
        """Alive check worker thread (sends alive check every 500ms if inactive)."""
        last_activity = time.time()

        while self.alive_check_running:
            time.sleep(0.5)

            # Check if activity within timeout
            if time.time() - last_activity > 5.0:
                # Send alive check request
                header = DoIPHeader.build(DoIPPayloadType.ALIVE_CHECK_REQUEST, 0)
                try:
                    if self.tcp_socket:
                        self.tcp_socket.sendall(header)
                        last_activity = time.time()
                except:
                    break

# Example Usage
if __name__ == "__main__":
    # Discover vehicles
    print("Discovering DoIP vehicles...")
    client = DoIPClient("192.168.1.100")  # Gateway IP
    vehicles = client.discover_vehicles()

    for vehicle in vehicles:
        print(f"Found vehicle: VIN={vehicle.vin}, Addr=0x{vehicle.logical_address:04X}")

    # Connect to gateway
    if client.connect(target_address=0x0001):
        print("Connected and routing activated")

        # Send diagnostic request (e.g., Read VIN)
        request = bytes([0x22, 0xF1, 0x90])
        response = client.send_diagnostic(request)

        if response:
            print(f"Response: {response.hex()}")
            if response[0] == 0x62:
                vin = response[3:20].decode('ascii')
                print(f"VIN: {vin}")

        # Disconnect
        client.disconnect()
```

## DoIP Security (TLS)

### TLS Configuration

For secure DoIP communication (ISO 13400-3):

```python
import ssl

def create_secure_connection(gateway_ip: str, gateway_port: int = 3496) -> socket.socket:
    """Create TLS-secured DoIP connection."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # In production, use proper certificate validation

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    secure_sock = context.wrap_socket(sock)
    secure_sock.connect((gateway_ip, gateway_port))

    return secure_sock
```

## Best Practices

1. **Always use vehicle discovery** before connecting
2. **Handle routing activation failures** - retry or use different activation type
3. **Implement alive check** to maintain connection
4. **Use TLS for production** - unsecured DoIP is vulnerable
5. **Monitor NACK codes** - indicates gateway or ECU issues
6. **Handle network transitions** - vehicle may switch between Ethernet interfaces
7. **Implement timeout handling** - ECU may be slow to respond

## References

- ISO 13400-2:2019 - DoIP transport protocol and network layer services
- ISO 13400-3:2016 - DoIP security support
