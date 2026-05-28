# ISO/SAE 21434 Compliance Skill

## Overview

Expert skill for implementing ISO/SAE 21434 cybersecurity engineering standard for road vehicles. Covers CSMS (Cybersecurity Management System), TARA (Threat Analysis and Risk Assessment), cybersecurity concept phase, product development, and operations/maintenance.

## Core Competencies

### ISO/SAE 21434 Framework
- **Cybersecurity Management System (CSMS)**: Organizational processes, roles, responsibilities
- **Concept Phase**: Item definition, cybersecurity goals, threat scenarios
- **Product Development**: Security requirements, architecture design, verification
- **Operations & Maintenance**: Incident response, vulnerability management, EOL handling
- **Supporting Processes**: Risk assessment, security testing, change management

### TARA Methodology
- **Asset Identification**: Identify critical assets (ECUs, data, communication channels)
- **Threat Scenario Definition**: STRIDE/DREAD modeling, attack trees
- **Impact Rating**: ASIL-D alignment, damage scenarios (safety, financial, operational, privacy)
- **Attack Feasibility**: Elapsed time, specialist expertise, knowledge of item, window of opportunity, equipment
- **Risk Determination**: Risk = Impact × Attack Feasibility
- **Risk Treatment**: Avoid, reduce, share, retain

### UN R155 & R156 Alignment
- **R155**: Cybersecurity management system requirements
- **R156**: Software update management system requirements
- **Type Approval**: Demonstration of compliance for vehicle homologation

## ISO 21434 Workflow

### Phase 1: Concept Phase

```yaml
# Item Definition Template
item_definition:
  item_name: "Telematics Control Unit (TCU)"
  item_id: "TCU-2024-001"
  description: "4G/5G connected telematics unit with V2X capability"
  boundaries:
    physical: "TCU ECU, antenna, power supply"
    logical: "CAN, Ethernet, cellular modem interfaces"
    temporal: "Ignition-on to ignition-off, OTA updates"

  assets:
    - name: "Vehicle Location Data"
      type: "Data"
      confidentiality: HIGH
      integrity: MEDIUM
      availability: MEDIUM

    - name: "Firmware Image"
      type: "Software"
      confidentiality: LOW
      integrity: HIGH
      availability: HIGH

    - name: "Private Key for V2X"
      type: "Cryptographic Material"
      confidentiality: CRITICAL
      integrity: CRITICAL
      availability: HIGH

  interfaces:
    - name: "CAN Bus Interface"
      protocol: "CAN 2.0B"
      threat_exposure: MEDIUM
      security_properties: ["message authentication"]

    - name: "Cellular Interface"
      protocol: "LTE/5G"
      threat_exposure: HIGH
      security_properties: ["TLS 1.3", "certificate pinning"]
```

### Phase 2: TARA Execution

```python
#!/usr/bin/env python3
"""
ISO 21434 TARA (Threat Analysis and Risk Assessment) Tool
Performs automated threat modeling and risk calculation
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict
import json

class ImpactLevel(Enum):
    NEGLIGIBLE = 1
    MODERATE = 2
    MAJOR = 3
    SEVERE = 4

class AttackFeasibility(Enum):
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5

class RiskLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    VERY_HIGH = 4

@dataclass
class Threat:
    threat_id: str
    name: str
    description: str
    threat_type: str  # Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation
    asset: str
    impact_safety: ImpactLevel
    impact_financial: ImpactLevel
    impact_operational: ImpactLevel
    impact_privacy: ImpactLevel

    # Attack Feasibility Parameters (ISO 21434 Table A.1)
    elapsed_time: int  # 0-19 points
    specialist_expertise: int  # 0-11 points
    knowledge_of_item: int  # 0-11 points
    window_of_opportunity: int  # 0-10 points
    equipment: int  # 0-9 points

@dataclass
class RiskAssessment:
    threat: Threat
    overall_impact: ImpactLevel
    attack_feasibility: AttackFeasibility
    risk_level: RiskLevel
    risk_value: int
    treatment: str
    justification: str

class TARAEngine:
    def __init__(self):
        self.threats = []
        self.assessments = []

    def calculate_attack_feasibility(self, threat: Threat) -> AttackFeasibility:
        """Calculate attack feasibility per ISO 21434 Annex G"""
        total_score = (
            threat.elapsed_time +
            threat.specialist_expertise +
            threat.knowledge_of_item +
            threat.window_of_opportunity +
            threat.equipment
        )

        # ISO 21434 Table G.1 mapping
        if total_score >= 37:
            return AttackFeasibility.VERY_LOW
        elif total_score >= 25:
            return AttackFeasibility.LOW
        elif total_score >= 13:
            return AttackFeasibility.MEDIUM
        elif total_score >= 10:
            return AttackFeasibility.HIGH
        else:
            return AttackFeasibility.VERY_HIGH

    def calculate_overall_impact(self, threat: Threat) -> ImpactLevel:
        """Determine worst-case impact across all categories"""
        impacts = [
            threat.impact_safety,
            threat.impact_financial,
            threat.impact_operational,
            threat.impact_privacy
        ]
        return max(impacts, key=lambda x: x.value)

    def determine_risk_level(self, impact: ImpactLevel, feasibility: AttackFeasibility) -> tuple:
        """Map impact and feasibility to risk level (ISO 21434 Table 9)"""
        risk_matrix = {
            (ImpactLevel.SEVERE, AttackFeasibility.VERY_HIGH): (RiskLevel.VERY_HIGH, 5),
            (ImpactLevel.SEVERE, AttackFeasibility.HIGH): (RiskLevel.VERY_HIGH, 5),
            (ImpactLevel.SEVERE, AttackFeasibility.MEDIUM): (RiskLevel.HIGH, 4),
            (ImpactLevel.SEVERE, AttackFeasibility.LOW): (RiskLevel.MEDIUM, 3),
            (ImpactLevel.SEVERE, AttackFeasibility.VERY_LOW): (RiskLevel.LOW, 2),

            (ImpactLevel.MAJOR, AttackFeasibility.VERY_HIGH): (RiskLevel.VERY_HIGH, 5),
            (ImpactLevel.MAJOR, AttackFeasibility.HIGH): (RiskLevel.HIGH, 4),
            (ImpactLevel.MAJOR, AttackFeasibility.MEDIUM): (RiskLevel.MEDIUM, 3),
            (ImpactLevel.MAJOR, AttackFeasibility.LOW): (RiskLevel.LOW, 2),
            (ImpactLevel.MAJOR, AttackFeasibility.VERY_LOW): (RiskLevel.LOW, 1),

            (ImpactLevel.MODERATE, AttackFeasibility.VERY_HIGH): (RiskLevel.HIGH, 4),
            (ImpactLevel.MODERATE, AttackFeasibility.HIGH): (RiskLevel.MEDIUM, 3),
            (ImpactLevel.MODERATE, AttackFeasibility.MEDIUM): (RiskLevel.MEDIUM, 2),
            (ImpactLevel.MODERATE, AttackFeasibility.LOW): (RiskLevel.LOW, 1),
            (ImpactLevel.MODERATE, AttackFeasibility.VERY_LOW): (RiskLevel.LOW, 1),
        }

        key = (impact, feasibility)
        return risk_matrix.get(key, (RiskLevel.LOW, 1))

    def assess_threat(self, threat: Threat) -> RiskAssessment:
        """Perform complete risk assessment for a threat"""
        overall_impact = self.calculate_overall_impact(threat)
        attack_feasibility = self.calculate_attack_feasibility(threat)
        risk_level, risk_value = self.determine_risk_level(overall_impact, attack_feasibility)

        # Determine treatment strategy
        if risk_value >= 4:
            treatment = "REDUCE"
            justification = "High/Very High risk requires mitigation controls"
        elif risk_value >= 3:
            treatment = "REDUCE or SHARE"
            justification = "Medium risk may require mitigation or transfer"
        else:
            treatment = "ACCEPT"
            justification = "Low risk acceptable with documentation"

        assessment = RiskAssessment(
            threat=threat,
            overall_impact=overall_impact,
            attack_feasibility=attack_feasibility,
            risk_level=risk_level,
            risk_value=risk_value,
            treatment=treatment,
            justification=justification
        )

        self.assessments.append(assessment)
        return assessment

    def generate_report(self, output_file: str):
        """Generate TARA report in JSON format"""
        report = {
            "tara_metadata": {
                "standard": "ISO/SAE 21434:2021",
                "version": "1.0",
                "date": "2026-03-19",
                "total_threats": len(self.assessments)
            },
            "risk_summary": {
                "very_high": sum(1 for a in self.assessments if a.risk_level == RiskLevel.VERY_HIGH),
                "high": sum(1 for a in self.assessments if a.risk_level == RiskLevel.HIGH),
                "medium": sum(1 for a in self.assessments if a.risk_level == RiskLevel.MEDIUM),
                "low": sum(1 for a in self.assessments if a.risk_level == RiskLevel.LOW)
            },
            "assessments": []
        }

        for assessment in self.assessments:
            report["assessments"].append({
                "threat_id": assessment.threat.threat_id,
                "threat_name": assessment.threat.name,
                "threat_type": assessment.threat.threat_type,
                "asset": assessment.threat.asset,
                "impact": assessment.overall_impact.name,
                "attack_feasibility": assessment.attack_feasibility.name,
                "feasibility_score": {
                    "elapsed_time": assessment.threat.elapsed_time,
                    "specialist_expertise": assessment.threat.specialist_expertise,
                    "knowledge_of_item": assessment.threat.knowledge_of_item,
                    "window_of_opportunity": assessment.threat.window_of_opportunity,
                    "equipment": assessment.threat.equipment,
                    "total": sum([
                        assessment.threat.elapsed_time,
                        assessment.threat.specialist_expertise,
                        assessment.threat.knowledge_of_item,
                        assessment.threat.window_of_opportunity,
                        assessment.threat.equipment
                    ])
                },
                "risk_level": assessment.risk_level.name,
                "risk_value": assessment.risk_value,
                "treatment": assessment.treatment,
                "justification": assessment.justification
            })

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"TARA report generated: {output_file}")


# Example: TCU TARA
def run_tcu_tara():
    tara = TARAEngine()

    # Threat T-001: Remote Code Execution via OTA
    threat_rce = Threat(
        threat_id="T-001",
        name="Remote Code Execution via Malicious OTA Update",
        description="Attacker injects malicious firmware via compromised OTA server",
        threat_type="Tampering",
        asset="Firmware Image",
        impact_safety=ImpactLevel.SEVERE,  # Can control vehicle functions
        impact_financial=ImpactLevel.MAJOR,  # Massive recall
        impact_operational=ImpactLevel.SEVERE,  # Complete TCU compromise
        impact_privacy=ImpactLevel.MAJOR,  # Access to all telemetry data
        elapsed_time=13,  # Days to weeks (13-16 points per ISO 21434)
        specialist_expertise=6,  # Proficient (6 points)
        knowledge_of_item=3,  # Public information (0-3 points)
        window_of_opportunity=4,  # Easy (0-4 points)
        equipment=4  # Standard equipment (4 points)
    )

    # Threat T-002: CAN Bus Message Injection
    threat_can_injection = Threat(
        threat_id="T-002",
        name="CAN Bus Message Injection",
        description="Attacker with physical access injects spoofed CAN messages",
        threat_type="Spoofing",
        asset="CAN Bus Interface",
        impact_safety=ImpactLevel.MAJOR,  # Can send false sensor data
        impact_financial=ImpactLevel.MODERATE,
        impact_operational=ImpactLevel.MAJOR,
        impact_privacy=ImpactLevel.NEGLIGIBLE,
        elapsed_time=16,  # < 1 day (16-19 points)
        specialist_expertise=6,  # Proficient
        knowledge_of_item=7,  # Restricted information (4-7 points)
        window_of_opportunity=7,  # Moderate (5-7 points)
        equipment=6  # Specialized equipment (5-7 points)
    )

    # Threat T-003: V2X Certificate Theft
    threat_cert_theft = Threat(
        threat_id="T-003",
        name="V2X Certificate Private Key Extraction",
        description="Physical attack to extract private key from HSM",
        threat_type="Information Disclosure",
        asset="Private Key for V2X",
        impact_safety=ImpactLevel.MAJOR,  # Spoofed V2X messages
        impact_financial=ImpactLevel.SEVERE,  # PKI infrastructure compromise
        impact_operational=ImpactLevel.MAJOR,
        impact_privacy=ImpactLevel.SEVERE,  # Impersonation attacks
        elapsed_time=7,  # More than 1 month (7-12 points)
        specialist_expertise=0,  # Expert (0 points)
        knowledge_of_item=0,  # Sensitive information (0 points)
        window_of_opportunity=7,  # Moderate
        equipment=0  # Bespoke equipment (0 points)
    )

    # Assess all threats
    tara.assess_threat(threat_rce)
    tara.assess_threat(threat_can_injection)
    tara.assess_threat(threat_cert_theft)

    # Generate report
    tara.generate_report("/tmp/tcu_tara_report.json")

    # Print summary
    print("\n=== TARA Summary ===")
    for assessment in tara.assessments:
        print(f"\n{assessment.threat.threat_id}: {assessment.threat.name}")
        print(f"  Impact: {assessment.overall_impact.name}")
        print(f"  Attack Feasibility: {assessment.attack_feasibility.name}")
        print(f"  Risk Level: {assessment.risk_level.name} (Value: {assessment.risk_value})")
        print(f"  Treatment: {assessment.treatment}")

if __name__ == "__main__":
    run_tcu_tara()
```

### Phase 3: Cybersecurity Concept

```yaml
# Cybersecurity Concept Template
cybersecurity_concept:
  item: "Telematics Control Unit (TCU)"
  version: "1.0"
  date: "2026-03-19"

  cybersecurity_goals:
    - id: "CG-001"
      description: "Prevent unauthorized firmware modification"
      rationale: "Addresses T-001 (Remote Code Execution)"
      security_property: "Integrity"

    - id: "CG-002"
      description: "Prevent CAN message spoofing"
      rationale: "Addresses T-002 (CAN Bus Message Injection)"
      security_property: "Authenticity"

    - id: "CG-003"
      description: "Protect V2X private key from extraction"
      rationale: "Addresses T-003 (Certificate Theft)"
      security_property: "Confidentiality"

  cybersecurity_requirements:
    - id: "CSR-001"
      goal: "CG-001"
      description: "Firmware shall be signed with RSA-4096 signature"
      verification: "Cryptographic signature verification test"

    - id: "CSR-002"
      goal: "CG-001"
      description: "Secure boot shall verify firmware signature before execution"
      verification: "Tampered firmware rejection test"

    - id: "CSR-003"
      goal: "CG-002"
      description: "CAN messages shall include HMAC-SHA256 authentication tag"
      verification: "Message authentication test with spoofed frames"

    - id: "CSR-004"
      goal: "CG-003"
      description: "Private keys shall be stored in HSM with no export capability"
      verification: "Physical penetration test, key extraction attempt"

    - id: "CSR-005"
      goal: "CG-003"
      description: "Implement side-channel attack countermeasures (timing, power analysis)"
      verification: "Differential power analysis (DPA) test"
```

### Phase 4: Cybersecurity Verification

```python
#!/usr/bin/env python3
"""
ISO 21434 Cybersecurity Verification Test Suite
Automated validation of cybersecurity requirements
"""

import subprocess
import hashlib
import hmac
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import struct

class CybersecurityVerifier:
    def __init__(self):
        self.test_results = []

    def verify_csr_001_firmware_signature(self, firmware_path: str, signature_path: str, pubkey_path: str) -> bool:
        """
        CSR-001: Verify firmware is signed with RSA-4096
        Returns True if signature valid, False otherwise
        """
        print("\n[TEST] CSR-001: Firmware Signature Verification")

        try:
            # Load public key
            with open(pubkey_path, 'rb') as f:
                public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())

            # Load firmware and signature
            with open(firmware_path, 'rb') as f:
                firmware_data = f.read()

            with open(signature_path, 'rb') as f:
                signature = f.read()

            # Verify signature
            public_key.verify(
                signature,
                firmware_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            print("  [PASS] Firmware signature valid")
            self.test_results.append(("CSR-001", "PASS"))
            return True

        except Exception as e:
            print(f"  [FAIL] Signature verification failed: {e}")
            self.test_results.append(("CSR-001", "FAIL"))
            return False

    def verify_csr_002_secure_boot_rejection(self, tampered_firmware_path: str) -> bool:
        """
        CSR-002: Verify secure boot rejects tampered firmware
        Simulates flashing tampered firmware and checking boot status
        """
        print("\n[TEST] CSR-002: Secure Boot Tamper Detection")

        # This would interface with actual ECU via diagnostic protocol
        # Simulated example:
        try:
            # Attempt to flash tampered firmware
            result = subprocess.run(
                ['flash_tool', '--ecu', 'TCU', '--firmware', tampered_firmware_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Check if ECU rejected the firmware
            if "SIGNATURE_INVALID" in result.stderr or result.returncode != 0:
                print("  [PASS] Secure boot rejected tampered firmware")
                self.test_results.append(("CSR-002", "PASS"))
                return True
            else:
                print("  [FAIL] Secure boot accepted tampered firmware")
                self.test_results.append(("CSR-002", "FAIL"))
                return False

        except Exception as e:
            print(f"  [ERROR] Test execution failed: {e}")
            self.test_results.append(("CSR-002", "ERROR"))
            return False

    def verify_csr_003_can_message_authentication(self, can_interface: str) -> bool:
        """
        CSR-003: Verify CAN messages include HMAC authentication
        Captures CAN traffic and validates HMAC tags
        """
        print("\n[TEST] CSR-003: CAN Message Authentication")

        try:
            # Capture CAN frame (example using SocketCAN)
            import can

            bus = can.interface.Bus(channel=can_interface, bustype='socketcan')
            message = bus.recv(timeout=5.0)

            if message is None:
                print("  [FAIL] No CAN message received")
                self.test_results.append(("CSR-003", "FAIL"))
                return False

            # Extract payload and HMAC (last 32 bytes)
            if len(message.data) < 32:
                print("  [FAIL] CAN message too short for HMAC")
                self.test_results.append(("CSR-003", "FAIL"))
                return False

            payload = message.data[:-32]
            received_hmac = message.data[-32:]

            # Verify HMAC (key would be provisioned via secure channel)
            shared_key = b'REPLACE_WITH_PROVISIONED_KEY'
            expected_hmac = hmac.new(shared_key, payload, hashlib.sha256).digest()

            if hmac.compare_digest(received_hmac, expected_hmac):
                print("  [PASS] CAN message HMAC valid")
                self.test_results.append(("CSR-003", "PASS"))
                return True
            else:
                print("  [FAIL] CAN message HMAC invalid")
                self.test_results.append(("CSR-003", "FAIL"))
                return False

        except Exception as e:
            print(f"  [ERROR] Test failed: {e}")
            self.test_results.append(("CSR-003", "ERROR"))
            return False

    def generate_verification_report(self, output_file: str):
        """Generate ISO 21434 verification report"""
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result == "PASS")
        failed = sum(1 for _, result in self.test_results if result == "FAIL")
        errors = sum(1 for _, result in self.test_results if result == "ERROR")

        with open(output_file, 'w') as f:
            f.write("ISO/SAE 21434 Cybersecurity Verification Report\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Date: 2026-03-19\n")
            f.write(f"Item: Telematics Control Unit (TCU)\n")
            f.write(f"Standard: ISO/SAE 21434:2021\n\n")
            f.write(f"Summary:\n")
            f.write(f"  Total Tests: {total}\n")
            f.write(f"  Passed: {passed}\n")
            f.write(f"  Failed: {failed}\n")
            f.write(f"  Errors: {errors}\n\n")
            f.write(f"Test Results:\n")

            for req_id, result in self.test_results:
                f.write(f"  {req_id}: {result}\n")

            if failed == 0 and errors == 0:
                f.write("\nVerdict: COMPLIANT\n")
            else:
                f.write("\nVerdict: NON-COMPLIANT\n")

        print(f"\nVerification report saved: {output_file}")

# Example usage
if __name__ == "__main__":
    verifier = CybersecurityVerifier()

    # Run verification tests
    verifier.verify_csr_001_firmware_signature(
        "/tmp/tcu_firmware.bin",
        "/tmp/tcu_firmware.sig",
        "/tmp/tcu_pubkey.pem"
    )

    verifier.verify_csr_002_secure_boot_rejection("/tmp/tampered_firmware.bin")
    verifier.verify_csr_003_can_message_authentication("can0")

    # Generate report
    verifier.generate_verification_report("/tmp/iso21434_verification_report.txt")
```

## UN R155 Compliance

```yaml
# UN R155 Type Approval Documentation Template
un_r155_compliance:
  vehicle_manufacturer: "OEM Example Inc."
  vehicle_type: "Electric SUV Model X"
  approval_date: "2026-03-19"

  csms_description:
    scope: "Development, production, post-production phases"
    organizational_structure:
      cybersecurity_officer: "John Doe"
      security_team: ["Security Architect", "Pentest Lead", "Incident Response"]

    processes:
      - risk_management: "ISO 21434 TARA process implemented"
      - secure_development: "Secure SDLC with threat modeling"
      - testing: "Penetration testing, fuzzing, static analysis"
      - vulnerability_management: "CVE monitoring, patch management"
      - incident_response: "24/7 SOC, incident playbooks"

  cybersecurity_threats_addressed:
    - threat: "Backend Server Compromise"
      mitigation: "TLS 1.3, certificate pinning, rate limiting"

    - threat: "Vehicle Data Extraction"
      mitigation: "Data encryption at rest (AES-256)"

    - threat: "Unauthorized Vehicle Access"
      mitigation: "BLE pairing with PIN, rolling codes"

  cybersecurity_testing_performed:
    - type: "Penetration Testing"
      scope: "TCU, Gateway, Infotainment"
      result: "No critical vulnerabilities found"

    - type: "Fuzzing"
      scope: "CAN protocol stack, Ethernet stack"
      result: "2 medium severity bugs fixed"

  post_production_monitoring:
    - "SIEM integration for fleet-wide anomaly detection"
    - "OTA security patch deployment within 72 hours"
    - "Vulnerability disclosure program (VDP)"
```

## ISO 21434 Tool: Attack Tree Generator

```python
#!/usr/bin/env python3
"""
Attack Tree Generator for ISO 21434 TARA
Generates visual attack trees for threat scenarios
"""

class AttackTreeNode:
    def __init__(self, name: str, node_type: str, operator: str = None):
        self.name = name
        self.node_type = node_type  # "goal", "attack_step"
        self.operator = operator  # "AND", "OR", None
        self.children = []
        self.feasibility_score = None

    def add_child(self, child):
        self.children.append(child)
        return child

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.node_type,
            "operator": self.operator,
            "feasibility": self.feasibility_score,
            "children": [child.to_dict() for child in self.children]
        }

def generate_rce_attack_tree():
    """Generate attack tree for Remote Code Execution threat"""

    # Root goal
    root = AttackTreeNode("Achieve Remote Code Execution on TCU", "goal", "AND")

    # Top-level steps (AND)
    step1 = root.add_child(AttackTreeNode("Gain Network Access to OTA Server", "attack_step", "OR"))
    step2 = root.add_child(AttackTreeNode("Inject Malicious Firmware", "attack_step", "AND"))
    step3 = root.add_child(AttackTreeNode("Bypass Signature Verification", "attack_step", "OR"))

    # Step 1 branches (OR)
    step1.add_child(AttackTreeNode("Compromise OTA Server Credentials", "attack_step"))
    step1.add_child(AttackTreeNode("Man-in-the-Middle Attack on TLS Connection", "attack_step"))
    step1.add_child(AttackTreeNode("Exploit OTA Server Vulnerability (CVE)", "attack_step"))

    # Step 2 branches (AND)
    step2.add_child(AttackTreeNode("Craft Malicious Firmware Payload", "attack_step"))
    step2.add_child(AttackTreeNode("Upload Firmware to OTA Server", "attack_step"))

    # Step 3 branches (OR)
    step3.add_child(AttackTreeNode("Extract Private Key from HSM", "attack_step"))
    step3.add_child(AttackTreeNode("Exploit Signature Verification Bug", "attack_step"))
    step3.add_child(AttackTreeNode("Downgrade to Unsigned Firmware", "attack_step"))

    return root

def export_attack_tree_graphviz(tree: AttackTreeNode, output_file: str):
    """Export attack tree to Graphviz DOT format"""

    dot_lines = ["digraph AttackTree {"]
    dot_lines.append('  node [shape=box];')

    node_counter = [0]

    def traverse(node, parent_id=None):
        current_id = node_counter[0]
        node_counter[0] += 1

        # Node label
        label = node.name
        if node.operator:
            label += f"\\n[{node.operator}]"

        # Node style
        if node.node_type == "goal":
            style = 'style=filled, fillcolor=lightblue'
        else:
            style = 'style=filled, fillcolor=lightyellow'

        dot_lines.append(f'  node{current_id} [label="{label}", {style}];')

        if parent_id is not None:
            dot_lines.append(f'  node{parent_id} -> node{current_id};')

        for child in node.children:
            traverse(child, current_id)

    traverse(tree)
    dot_lines.append("}")

    with open(output_file, 'w') as f:
        f.write('\n'.join(dot_lines))

    print(f"Attack tree exported: {output_file}")
    print("Generate PNG: dot -Tpng attack_tree.dot -o attack_tree.png")

if __name__ == "__main__":
    tree = generate_rce_attack_tree()
    export_attack_tree_graphviz(tree, "/tmp/rce_attack_tree.dot")
```

## Best Practices

1. **TARA Execution**: Perform TARA at item definition phase and update after significant changes
2. **Risk Treatment Traceability**: Maintain traceability matrix from threats → cybersecurity goals → requirements → tests
3. **Tool Support**: Use dedicated ISO 21434 tools (Medini Analyze, PREEvision, ITEM ToolKit)
4. **Cross-Functional Collaboration**: Involve safety engineers, architects, developers, pentesters
5. **Continuous Monitoring**: ISO 21434 is not one-time; requires ongoing vulnerability management

## References

- ISO/SAE 21434:2021 - Road vehicles - Cybersecurity engineering
- UN R155 - Uniform provisions concerning cybersecurity and CSMS
- UN R156 - Uniform provisions concerning software update and SUMS
- UNECE WP.29 - Cybersecurity type approval guidance
