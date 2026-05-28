# Intrusion Detection & Prevention Skill

## Overview

Expert skill for implementing IDS/IPS (Intrusion Detection/Prevention Systems) in automotive networks. Covers CAN bus anomaly detection, network traffic analysis, SIEM integration, honeypot deployment, and incident response playbooks.

## Core Competencies

### IDS/IPS Architecture
- **Network-based IDS (NIDS)**: Monitor CAN, FlexRay, Ethernet traffic
- **Host-based IDS (HIDS)**: Monitor ECU system calls, file integrity
- **Anomaly Detection**: Machine learning for baseline behavior
- **Signature-based Detection**: Known attack patterns
- **Prevention Mechanisms**: Frame filtering, rate limiting, isolation

### Detection Techniques
- **Statistical Analysis**: Abnormal message rates, timing violations
- **Protocol Validation**: Malformed frames, invalid DLC
- **Behavioral Analysis**: Unexpected ECU communication patterns
- **Entropy Analysis**: Randomness in payload data

## CAN Bus Intrusion Detection System

### CAN IDS Implementation

```python
#!/usr/bin/env python3
"""
CAN Bus Intrusion Detection System
Real-time anomaly detection for automotive CAN networks
"""

import can
import time
import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json

class CANIDSEngine:
    """Core CAN IDS detection engine"""

    def __init__(self, can_interface: str = 'can0', window_size: int = 100):
        self.interface = can_interface
        self.bus = can.interface.Bus(channel=can_interface, bustype='socketcan')

        # Message statistics per CAN ID
        self.msg_stats = defaultdict(lambda: {
            'count': 0,
            'last_timestamp': None,
            'intervals': deque(maxlen=window_size),
            'dlc_values': deque(maxlen=window_size),
            'payloads': deque(maxlen=window_size)
        })

        # Learned baseline (normal behavior)
        self.baseline = {}
        self.alerts = []

        print(f"=== CAN IDS Engine Initialized ===")
        print(f"[INFO] Interface: {can_interface}")
        print(f"[INFO] Window size: {window_size}")

    def learn_baseline(self, duration_seconds: int = 300):
        """Learn normal CAN traffic baseline (5 minutes)"""
        print(f"\n=== Learning Baseline (mode) ===")
        print(f"[INFO] Duration: {duration_seconds} seconds")
        print(f"[INFO] Capturing normal traffic...")

        start_time = time.time()
        message_count = 0

        while (time.time() - start_time) < duration_seconds:
            msg = self.bus.recv(timeout=1.0)
            if msg is None:
                continue

            self._update_statistics(msg)
            message_count += 1

            if message_count % 1000 == 0:
                elapsed = int(time.time() - start_time)
                print(f"[INFO] {message_count} messages captured ({elapsed}s)")

        # Compute baseline statistics
        self._compute_baseline()

        print(f"\n[PASS] Baseline learning complete")
        print(f"[INFO] Total messages: {message_count}")
        print(f"[INFO] Unique CAN IDs: {len(self.baseline)}")

    def _update_statistics(self, msg: can.Message):
        """Update statistics for received message"""
        stats = self.msg_stats[msg.arbitration_id]
        stats['count'] += 1

        # Calculate inter-arrival time
        if stats['last_timestamp'] is not None:
            interval = msg.timestamp - stats['last_timestamp']
            stats['intervals'].append(interval)

        stats['last_timestamp'] = msg.timestamp
        stats['dlc_values'].append(msg.dlc)
        stats['payloads'].append(bytes(msg.data))

    def _compute_baseline(self):
        """Compute baseline statistics from learned data"""
        print(f"\n[INFO] Computing baseline statistics...")

        for can_id, stats in self.msg_stats.items():
            if stats['count'] < 10:
                continue  # Insufficient data

            # Interval statistics
            intervals = list(stats['intervals'])
            interval_mean = statistics.mean(intervals) if intervals else 0
            interval_std = statistics.stdev(intervals) if len(intervals) > 1 else 0

            # Expected DLC
            dlc_mode = max(set(stats['dlc_values']), key=list(stats['dlc_values']).count)

            # Payload entropy (randomness)
            payloads = list(stats['payloads'])
            entropy_mean = statistics.mean([self._calculate_entropy(p) for p in payloads])

            self.baseline[can_id] = {
                'message_count': stats['count'],
                'interval_mean': interval_mean,
                'interval_std': interval_std,
                'interval_min': interval_mean - (3 * interval_std),  # 3-sigma
                'interval_max': interval_mean + (3 * interval_std),
                'expected_dlc': dlc_mode,
                'entropy_mean': entropy_mean,
                'payloads_sample': payloads[:10]  # Store samples for comparison
            }

            print(f"  CAN ID 0x{can_id:03X}: "
                  f"interval={interval_mean*1000:.2f}ms±{interval_std*1000:.2f}ms, "
                  f"DLC={dlc_mode}, "
                  f"entropy={entropy_mean:.2f}")

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of payload"""
        if len(data) == 0:
            return 0.0

        from collections import Counter
        import math

        counter = Counter(data)
        length = len(data)

        entropy = 0.0
        for count in counter.values():
            p = count / length
            entropy -= p * math.log2(p)

        return entropy

    def detect_anomalies(self, msg: can.Message) -> list:
        """Detect anomalies in received message"""
        anomalies = []
        can_id = msg.arbitration_id

        if can_id not in self.baseline:
            anomalies.append({
                'type': 'UNKNOWN_CAN_ID',
                'severity': 'HIGH',
                'description': f'New CAN ID 0x{can_id:03X} not seen during baseline',
                'timestamp': msg.timestamp
            })
            return anomalies

        baseline = self.baseline[can_id]
        stats = self.msg_stats[can_id]

        # Check 1: Inter-arrival time anomaly
        if stats['last_timestamp'] is not None:
            interval = msg.timestamp - stats['last_timestamp']

            if interval < baseline['interval_min']:
                anomalies.append({
                    'type': 'MESSAGE_FLOODING',
                    'severity': 'HIGH',
                    'description': f'CAN ID 0x{can_id:03X} flooding: '
                                 f'interval {interval*1000:.2f}ms < expected {baseline["interval_min"]*1000:.2f}ms',
                    'timestamp': msg.timestamp,
                    'can_id': can_id
                })

            elif interval > baseline['interval_max']:
                anomalies.append({
                    'type': 'MESSAGE_SUPPRESSION',
                    'severity': 'MEDIUM',
                    'description': f'CAN ID 0x{can_id:03X} delayed: '
                                 f'interval {interval*1000:.2f}ms > expected {baseline["interval_max"]*1000:.2f}ms',
                    'timestamp': msg.timestamp,
                    'can_id': can_id
                })

        # Check 2: DLC anomaly
        if msg.dlc != baseline['expected_dlc']:
            anomalies.append({
                'type': 'DLC_ANOMALY',
                'severity': 'MEDIUM',
                'description': f'CAN ID 0x{can_id:03X} unexpected DLC: '
                             f'{msg.dlc} != expected {baseline["expected_dlc"]}',
                'timestamp': msg.timestamp,
                'can_id': can_id
            })

        # Check 3: Payload entropy anomaly (possible injection/fuzzing)
        payload_entropy = self._calculate_entropy(bytes(msg.data))
        entropy_diff = abs(payload_entropy - baseline['entropy_mean'])

        if entropy_diff > 2.0:  # Significant entropy change
            anomalies.append({
                'type': 'PAYLOAD_ANOMALY',
                'severity': 'HIGH',
                'description': f'CAN ID 0x{can_id:03X} unusual payload entropy: '
                             f'{payload_entropy:.2f} (expected {baseline["entropy_mean"]:.2f})',
                'timestamp': msg.timestamp,
                'can_id': can_id,
                'payload': msg.data.hex()
            })

        # Update statistics
        self._update_statistics(msg)

        return anomalies

    def monitor(self, duration_seconds: int = None, prevention_mode: bool = False):
        """Monitor CAN bus for intrusions"""
        print(f"\n=== CAN IDS Monitoring ===")
        print(f"[INFO] Prevention mode: {prevention_mode}")

        start_time = time.time()
        message_count = 0
        anomaly_count = 0

        try:
            while True:
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    break

                msg = self.bus.recv(timeout=1.0)
                if msg is None:
                    continue

                message_count += 1

                # Detect anomalies
                anomalies = self.detect_anomalies(msg)

                if anomalies:
                    anomaly_count += len(anomalies)

                    for anomaly in anomalies:
                        self._handle_alert(anomaly, msg, prevention_mode)

                # Status update every 5000 messages
                if message_count % 5000 == 0:
                    elapsed = int(time.time() - start_time)
                    print(f"[INFO] {message_count} messages, {anomaly_count} anomalies ({elapsed}s)")

        except KeyboardInterrupt:
            print(f"\n[INFO] Monitoring stopped by user")

        print(f"\n=== Monitoring Summary ===")
        print(f"[INFO] Total messages: {message_count}")
        print(f"[INFO] Anomalies detected: {anomaly_count}")
        print(f"[INFO] Detection rate: {anomaly_count/message_count*100:.2f}%")

    def _handle_alert(self, anomaly: dict, msg: can.Message, prevention_mode: bool):
        """Handle detected anomaly"""
        timestamp = datetime.fromtimestamp(anomaly['timestamp']).strftime('%H:%M:%S.%f')[:-3]

        print(f"\n[ALERT] {anomaly['severity']} - {anomaly['type']} @ {timestamp}")
        print(f"  Description: {anomaly['description']}")
        print(f"  CAN ID: 0x{msg.arbitration_id:03X}, DLC: {msg.dlc}, Data: {msg.data.hex()}")

        # Log alert
        self.alerts.append(anomaly)

        # Prevention actions
        if prevention_mode:
            if anomaly['type'] == 'MESSAGE_FLOODING':
                print(f"  [BLOCK] Rate limiting CAN ID 0x{msg.arbitration_id:03X}")
                # In real system: configure CAN controller filters

            elif anomaly['type'] == 'UNKNOWN_CAN_ID':
                print(f"  [BLOCK] Dropping frames from unknown CAN ID 0x{msg.arbitration_id:03X}")

            elif anomaly['type'] == 'PAYLOAD_ANOMALY':
                print(f"  [ISOLATE] Potential fuzzing/injection detected - isolating ECU")

    def export_alerts(self, output_file: str):
        """Export alerts to JSON"""
        with open(output_file, 'w') as f:
            json.dump(self.alerts, f, indent=2)

        print(f"[INFO] Alerts exported: {output_file}")


# Example: Simulate CAN attacks and detect them
def demo_can_ids():
    import os

    # Setup virtual CAN interface
    os.system('sudo modprobe vcan')
    os.system('sudo ip link add dev vcan0 type vcan')
    os.system('sudo ip link set up vcan0')

    print("=== CAN IDS Demo ===")
    print("[INFO] Using virtual CAN interface vcan0")

    # Create IDS
    ids = CANIDSEngine(can_interface='vcan0', window_size=50)

    # Simulate normal traffic generator (in separate process)
    print("\n[INFO] Start normal CAN traffic generator in another terminal:")
    print("  python3 can_traffic_generator.py --interface vcan0 --scenario normal")

    input("\nPress Enter when normal traffic is running...")

    # Learn baseline
    ids.learn_baseline(duration_seconds=60)

    # Monitor for attacks
    print("\n[INFO] Now inject attacks using:")
    print("  python3 can_attack_simulator.py --interface vcan0 --attack flooding")

    input("\nPress Enter to start monitoring...")

    ids.monitor(duration_seconds=120, prevention_mode=True)

    # Export results
    ids.export_alerts('/tmp/can_ids_alerts.json')

if __name__ == "__main__":
    demo_can_ids()
```

### CAN Attack Simulator (for testing)

```python
#!/usr/bin/env python3
"""
CAN Attack Simulator for IDS Testing
Generates various attack scenarios
"""

import can
import time
import random

class CANAttackSimulator:
    def __init__(self, interface: str = 'vcan0'):
        self.bus = can.interface.Bus(channel=interface, bustype='socketcan')
        print(f"=== CAN Attack Simulator ===")
        print(f"[INFO] Interface: {interface}")

    def attack_flooding(self, target_can_id: int = 0x123, duration: int = 10):
        """Message flooding attack"""
        print(f"\n[ATTACK] Flooding CAN ID 0x{target_can_id:03X}")

        start_time = time.time()
        count = 0

        while (time.time() - start_time) < duration:
            msg = can.Message(
                arbitration_id=target_can_id,
                data=[0x00] * 8,
                is_extended_id=False
            )
            self.bus.send(msg)
            count += 1
            # No delay - flood as fast as possible

        print(f"[INFO] Sent {count} messages in {duration}s")

    def attack_fuzzing(self, target_can_id: int = 0x456, duration: int = 10):
        """Payload fuzzing attack"""
        print(f"\n[ATTACK] Fuzzing CAN ID 0x{target_can_id:03X}")

        start_time = time.time()
        count = 0

        while (time.time() - start_time) < duration:
            # Random payload
            payload = [random.randint(0, 255) for _ in range(8)]

            msg = can.Message(
                arbitration_id=target_can_id,
                data=payload,
                is_extended_id=False
            )
            self.bus.send(msg)
            count += 1
            time.sleep(0.01)  # 10ms interval

        print(f"[INFO] Sent {count} fuzzed messages")

    def attack_spoofing(self, spoof_can_id: int = 0x789, duration: int = 10):
        """ECU spoofing attack (new CAN ID)"""
        print(f"\n[ATTACK] Spoofing new CAN ID 0x{spoof_can_id:03X}")

        start_time = time.time()
        count = 0

        while (time.time() - start_time) < duration:
            msg = can.Message(
                arbitration_id=spoof_can_id,
                data=[0xDE, 0xAD, 0xBE, 0xEF, 0x00, 0x00, 0x00, 0x00],
                is_extended_id=False
            )
            self.bus.send(msg)
            count += 1
            time.sleep(0.02)

        print(f"[INFO] Sent {count} spoofed messages")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python3 can_attack_simulator.py --interface vcan0 --attack [flooding|fuzzing|spoofing]")
        sys.exit(1)

    interface = sys.argv[2]
    attack_type = sys.argv[4]

    attacker = CANAttackSimulator(interface=interface)

    if attack_type == "flooding":
        attacker.attack_flooding(target_can_id=0x123, duration=30)
    elif attack_type == "fuzzing":
        attacker.attack_fuzzing(target_can_id=0x456, duration=30)
    elif attack_type == "spoofing":
        attacker.attack_spoofing(spoof_can_id=0x999, duration=30)
    else:
        print(f"Unknown attack type: {attack_type}")
```

## Ethernet IDS (Gateway/TCU)

```python
#!/usr/bin/env python3
"""
Ethernet-based IDS for Automotive Gateway/TCU
Deep packet inspection for HTTP, MQTT, SOME/IP
"""

from scapy.all import sniff, IP, TCP, UDP
from collections import defaultdict
import time

class EthernetIDS:
    """Ethernet network IDS"""

    def __init__(self, interface: str = 'eth0'):
        self.interface = interface
        self.connection_tracker = defaultdict(lambda: {
            'count': 0,
            'first_seen': None,
            'last_seen': None
        })
        self.alerts = []

        print(f"=== Ethernet IDS Initialized ===")
        print(f"[INFO] Interface: {interface}")

    def packet_callback(self, packet):
        """Process captured packet"""
        if IP not in packet:
            return

        src_ip = packet[IP].src
        dst_ip = packet[IP].dst

        # Track connection
        conn_key = f"{src_ip}:{dst_ip}"
        tracker = self.connection_tracker[conn_key]
        tracker['count'] += 1
        tracker['last_seen'] = time.time()

        if tracker['first_seen'] is None:
            tracker['first_seen'] = time.time()

        # Detection rules
        if TCP in packet:
            self._check_tcp_anomalies(packet)
        elif UDP in packet:
            self._check_udp_anomalies(packet)

    def _check_tcp_anomalies(self, packet):
        """Check for TCP-based attacks"""
        tcp = packet[TCP]

        # SYN flood detection
        if tcp.flags == 'S':
            src_ip = packet[IP].src
            syn_count = sum(1 for key in self.connection_tracker
                          if key.startswith(src_ip) and
                          time.time() - self.connection_tracker[key]['first_seen'] < 10)

            if syn_count > 100:
                alert = {
                    'type': 'SYN_FLOOD',
                    'severity': 'HIGH',
                    'source': src_ip,
                    'description': f'Possible SYN flood from {src_ip} ({syn_count} connections in 10s)'
                }
                self._raise_alert(alert)

        # Port scanning detection
        dst_port = tcp.dport
        if dst_port > 1024:  # Non-standard ports
            src_ip = packet[IP].src
            unique_ports = len(set(
                key.split(':')[1] for key in self.connection_tracker
                if key.startswith(src_ip)
            ))

            if unique_ports > 50:
                alert = {
                    'type': 'PORT_SCAN',
                    'severity': 'MEDIUM',
                    'source': src_ip,
                    'description': f'Port scanning detected from {src_ip} ({unique_ports} unique ports)'
                }
                self._raise_alert(alert)

    def _check_udp_anomalies(self, packet):
        """Check for UDP-based attacks"""
        udp = packet[UDP]

        # SOME/IP message validation (automotive middleware)
        if udp.dport in [30490, 30491, 30492]:  # SOME/IP ports
            payload = bytes(packet[UDP].payload)

            if len(payload) < 16:
                alert = {
                    'type': 'MALFORMED_SOMEIP',
                    'severity': 'MEDIUM',
                    'source': packet[IP].src,
                    'description': 'Malformed SOME/IP message (too short)'
                }
                self._raise_alert(alert)

    def _raise_alert(self, alert: dict):
        """Raise security alert"""
        print(f"\n[ALERT] {alert['severity']} - {alert['type']}")
        print(f"  {alert['description']}")
        self.alerts.append(alert)

    def start_monitoring(self, count: int = 1000):
        """Start packet capture"""
        print(f"\n[INFO] Starting Ethernet monitoring ({count} packets)...")
        sniff(iface=self.interface, prn=self.packet_callback, count=count)

        print(f"\n=== Monitoring Complete ===")
        print(f"[INFO] Alerts raised: {len(self.alerts)}")

if __name__ == "__main__":
    ids = EthernetIDS(interface='eth0')
    ids.start_monitoring(count=5000)
```

## SIEM Integration (ELK Stack)

```yaml
# Logstash configuration for CAN IDS alerts
input {
  file {
    path => "/var/log/can_ids/alerts.json"
    start_position => "beginning"
    codec => "json"
  }
}

filter {
  # Parse CAN IDS alerts
  if [type] == "MESSAGE_FLOODING" {
    mutate {
      add_field => { "severity_score" => 9 }
      add_tag => ["dos_attack"]
    }
  }

  if [type] == "PAYLOAD_ANOMALY" {
    mutate {
      add_field => { "severity_score" => 8 }
      add_tag => ["potential_injection"]
    }
  }

  # Convert CAN ID to hex
  ruby {
    code => "event.set('can_id_hex', '0x%03X' % event.get('can_id'))"
  }

  # GeoIP lookup for external attacks
  if [source_ip] {
    geoip {
      source => "source_ip"
      target => "geoip"
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "automotive-ids-%{+YYYY.MM.dd}"
  }

  # High severity alerts to Slack
  if [severity] == "HIGH" {
    http {
      url => "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
      http_method => "post"
      format => "json"
      content_type => "application/json"
      message => '{
        "text": "🚨 CAN IDS Alert: %{type}",
        "attachments": [{
          "color": "danger",
          "fields": [
            {"title": "Description", "value": "%{description}"},
            {"title": "CAN ID", "value": "%{can_id_hex}"},
            {"title": "Timestamp", "value": "%{@timestamp}"}
          ]
        }]
      }'
    }
  }
}
```

## Incident Response Playbook

```yaml
# Automotive Cybersecurity Incident Response Playbook
incident_response:
  phase_1_identification:
    - alert: "IDS detects anomaly"
    - verify: "Confirm alert is not false positive"
    - classify: "Determine attack type and severity"
    - escalate: "Notify security team and OEM SOC"

  phase_2_containment:
    short_term:
      - action: "Isolate affected ECU/network segment"
      - method: "Gateway firewall rules, CAN filters"
      - verify: "Confirm attack traffic blocked"

    long_term:
      - action: "Patch vulnerable software"
      - method: "OTA security update"
      - timeline: "< 72 hours per UN R155"

  phase_3_eradication:
    - identify_root_cause: "Vulnerability analysis, forensics"
    - remove_threat: "Firmware update, key revocation"
    - verify_clean: "Scan for persistence mechanisms"

  phase_4_recovery:
    - restore_service: "Reboot ECU, restore network"
    - validate: "Functional testing, regression testing"
    - monitor: "Enhanced monitoring for 7 days"

  phase_5_lessons_learned:
    - document: "Incident timeline, root cause, actions taken"
    - improve: "Update IDS signatures, patch other vehicles"
    - report: "Notify regulatory authorities (UN R155 requirement)"
```

## Best Practices

1. **Layered Defense**: Deploy IDS at multiple layers (CAN, Ethernet, application)
2. **Baseline Learning**: Capture 24-hour baseline before production deployment
3. **False Positive Tuning**: Iterate on detection rules to reduce false positives < 1%
4. **SIEM Integration**: Centralize logs for fleet-wide threat intelligence
5. **Incident Playbooks**: Pre-define response procedures for < 15 minute MTTR

## References

- NIST SP 800-94: Guide to Intrusion Detection and Prevention Systems
- ISO 21434: Cybersecurity Engineering (Clause 11: Incident Response)
- AUTOSAR SecOC: Secure Onboard Communication specification
- J3061: Cybersecurity Guidebook for Cyber-Physical Vehicle Systems
