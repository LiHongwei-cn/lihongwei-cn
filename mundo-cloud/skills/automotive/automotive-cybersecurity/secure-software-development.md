# Secure Software Development Skill

## Overview

Expert skill for implementing secure coding practices in automotive software development. Covers MISRA C/C++, static analysis, fuzzing, threat modeling (STRIDE/DREAD), and secure CI/CD pipelines.

## Core Competencies

### Secure SDLC
- **Requirements Phase**: Security requirements definition, abuse cases
- **Design Phase**: Threat modeling, security architecture review
- **Implementation Phase**: Secure coding standards, peer review
- **Testing Phase**: SAST, DAST, fuzzing, penetration testing
- **Deployment Phase**: Secure OTA updates, code signing
- **Maintenance Phase**: Vulnerability management, patch deployment

### Coding Standards
- **MISRA C:2012**: Mandatory rules for automotive C code
- **MISRA C++:2008**: C++ guidelines for safety-critical systems
- **CERT C**: SEI CERT C Coding Standard
- **AUTOSAR C++14**: Guidelines for modern C++ in automotive

## MISRA C Compliance

### MISRA C:2012 Critical Rules

```c
/*
 * MISRA C:2012 Compliant Code Example
 * Demonstrates mandatory rules for automotive software
 */

#include <stdint.h>
#include <stdbool.h>
#include <string.h>

/* Rule 8.4: Compatible declarations for functions */
extern uint16_t calculate_checksum(const uint8_t *data, size_t length);

/* Rule 8.2: Function types shall be in prototype form with named parameters */
static bool validate_can_message(const uint8_t *payload, uint8_t dlc);

/* Rule 21.3: malloc/free shall not be used in automotive */
#define MAX_CAN_BUFFER 100
static uint8_t can_buffer[MAX_CAN_BUFFER];

/*
 * Rule 17.7: Return value of functions shall not be discarded
 * Rule 10.1: Operands shall not be implicitly converted
 */
static int16_t process_sensor_data(uint16_t raw_value) {
    int16_t processed_value;

    /* Rule 10.4: Both operands of operators shall have compatible types */
    if (raw_value > (uint16_t)1000) {
        /* Rule 15.5: Avoid multiple exit points (single return preferred) */
        processed_value = -1;  /* Error code */
    } else {
        /* Rule 10.3: Explicit cast for type conversion */
        processed_value = (int16_t)raw_value;
    }

    return processed_value;
}

/*
 * Rule 17.3: Implicitly declared functions shall not be called
 * Rule 17.4: All exit paths shall return a value
 */
static bool validate_can_message(const uint8_t *payload, uint8_t dlc) {
    bool is_valid = false;

    /* Rule 14.4: Controlling expression shall be bool */
    if (dlc <= (uint8_t)8) {
        /* Rule 12.1: Precedence of operators shall be explicit */
        if ((payload != NULL) && (dlc > (uint8_t)0)) {
            /* Rule 21.6: Use of stdio shall be avoided in embedded */
            /* No printf() - use logging framework instead */
            is_valid = true;
        }
    }

    /* Rule 15.5: Single exit point */
    return is_valid;
}

/*
 * Rule 18.1: Pointer arithmetic shall not be used with arrays of unknown size
 * Rule 18.4: Pointer arithmetic shall not result in invalid pointers
 */
uint16_t calculate_checksum(const uint8_t *data, size_t length) {
    uint16_t checksum = 0U;
    size_t i;

    /* Rule 14.3: Controlling expressions shall not be invariant */
    if ((data != NULL) && (length > (size_t)0)) {
        /* Rule 14.2: for loop shall have single counter */
        for (i = 0U; i < length; i++) {
            /* Rule 10.1: No implicit conversion */
            checksum = (uint16_t)(checksum + (uint16_t)data[i]);
        }
    }

    return checksum;
}

/*
 * Rule 9.1: All automatic variables shall be initialized
 * Rule 9.2: Braces shall initialize all elements
 */
void secure_buffer_copy(void) {
    uint8_t source[8] = {0U, 1U, 2U, 3U, 4U, 5U, 6U, 7U};
    uint8_t destination[8] = {0U};  /* Initialize all elements */
    size_t copy_size = sizeof(source);

    /* Rule 21.14: memcpy shall not be used with overlapping regions */
    /* Use safe copy function */
    (void)memcpy(destination, source, copy_size);

    /* Rule 2.2: No dead code */
    /* All code paths reachable and executed */
}

/*
 * Rule 13.5: Right-hand operand of && or || shall not have side effects
 * Rule 13.6: sizeof operator shall not have side effects
 */
static bool safe_condition_check(uint8_t *counter) {
    bool condition_met = false;

    /* WRONG: if ((counter != NULL) && ((*counter)++ < 10)) */
    /* RIGHT: Separate side effect from condition */
    if (counter != NULL) {
        uint8_t current_value = *counter;
        (*counter)++;

        if (current_value < (uint8_t)10) {
            condition_met = true;
        }
    }

    return condition_met;
}

/*
 * Rule 11.8: Cast shall not remove const or volatile qualification
 * Rule 11.5: Cast from pointer to void to pointer to object allowed
 */
static void process_const_data(const uint8_t *const_data, size_t length) {
    uint8_t mutable_copy[8];

    if ((const_data != NULL) && (length <= sizeof(mutable_copy))) {
        /* Rule 21.14: Safe copy, not modifying const source */
        (void)memcpy(mutable_copy, const_data, length);

        /* Process mutable copy, not const original */
        mutable_copy[0] = 0xFF;
    }
}
```

### MISRA C Checker Integration

```bash
#!/bin/bash
# MISRA C Compliance Checker Script
# Uses PC-lint Plus or similar static analyzer

PROJECT_DIR="."
OUTPUT_DIR="misra_reports"
LINT_CONFIG="misra_c_2012.lnt"

mkdir -p $OUTPUT_DIR

echo "=== MISRA C:2012 Compliance Check ==="

# Run PC-lint Plus
pclp64_linux \
    -passes=2 \
    -width=0 \
    -hF1 \
    +v \
    -i/opt/pclp/config/au-misra3.lnt \
    -i/opt/pclp/config/co-gcc.lnt \
    $LINT_CONFIG \
    *.c *.h \
    > $OUTPUT_DIR/misra_violations.txt 2>&1

# Parse results
MANDATORY_VIOLATIONS=$(grep -c "MISRA C:2012 Rule.*\[Mandatory\]" $OUTPUT_DIR/misra_violations.txt || true)
REQUIRED_VIOLATIONS=$(grep -c "MISRA C:2012 Rule.*\[Required\]" $OUTPUT_DIR/misra_violations.txt || true)
ADVISORY_VIOLATIONS=$(grep -c "MISRA C:2012 Rule.*\[Advisory\]" $OUTPUT_DIR/misra_violations.txt || true)

echo ""
echo "=== MISRA C:2012 Compliance Summary ==="
echo "Mandatory violations: $MANDATORY_VIOLATIONS"
echo "Required violations: $REQUIRED_VIOLATIONS"
echo "Advisory violations: $ADVISORY_VIOLATIONS"

# Fail if mandatory violations found
if [ $MANDATORY_VIOLATIONS -gt 0 ]; then
    echo ""
    echo "[FAIL] Mandatory MISRA violations detected - code is non-compliant"
    echo "Review: $OUTPUT_DIR/misra_violations.txt"
    exit 1
else
    echo ""
    echo "[PASS] No mandatory MISRA violations"
fi
```

## Static Analysis (Coverity, Klocwork)

### Coverity Integration

```yaml
# Coverity Scan Configuration for Automotive Project
coverity_scan:
  project: "automotive-ecu-firmware"
  language: "c, c++"
  build_command: "make clean && make all"

  checkers:
    security:
      - BUFFER_OVERFLOW
      - BUFFER_UNDERRUN
      - DIVIDE_BY_ZERO
      - INTEGER_OVERFLOW
      - NULL_DEREFERENCE
      - USE_AFTER_FREE
      - RESOURCE_LEAK
      - TAINTED_SCALAR
      - WEAK_RANDOM

    concurrency:
      - DEADLOCK
      - RACE_CONDITION
      - ATOMICITY
      - LOCK_ORDER

    automotive_specific:
      - MISRA_C_2012_ALL
      - CERT_C_ALL
      - AUTOSAR_CPP14_ALL

  severity_thresholds:
    high: 0       # Zero high-severity defects allowed
    medium: 5     # Max 5 medium-severity defects
    low: 20       # Max 20 low-severity defects

  defect_filters:
    # Exclude test code from security checks
    - path: "tests/"
      checker: "*"

    # Exclude third-party libraries (already vetted)
    - path: "third_party/"
      checker: "*"
```

### Coverity Scan Script

```python
#!/usr/bin/env python3
"""
Automated Coverity Scan for Automotive CI/CD
Integrates static analysis into build pipeline
"""

import subprocess
import json
import sys

class CoverityScanRunner:
    def __init__(self, project_dir: str, output_dir: str):
        self.project_dir = project_dir
        self.output_dir = output_dir
        self.cov_dir = f"{output_dir}/cov-int"

    def run_build_with_coverity(self):
        """Capture build with Coverity"""
        print("=== Running Coverity Build Capture ===")

        cmd = [
            'cov-build',
            '--dir', self.cov_dir,
            'make', '-C', self.project_dir, 'clean', 'all'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[FAIL] Build capture failed: {result.stderr}")
            return False

        print(f"[PASS] Build captured to {self.cov_dir}")
        return True

    def run_analysis(self):
        """Run Coverity static analysis"""
        print("\n=== Running Coverity Analysis ===")

        cmd = [
            'cov-analyze',
            '--dir', self.cov_dir,
            '--all',
            '--security',
            '--concurrency',
            '--enable-constraint-fpp',
            '--enable-fnptr',
            '--enable-virtual',
            '--ticker-mode', 'none'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[FAIL] Analysis failed: {result.stderr}")
            return False

        print(f"[PASS] Analysis complete")
        return True

    def generate_report(self):
        """Generate defect report"""
        print("\n=== Generating Coverity Report ===")

        # Export defects to JSON
        cmd = [
            'cov-format-errors',
            '--dir', self.cov_dir,
            '--json-output-v7', f'{self.output_dir}/defects.json'
        ]

        subprocess.run(cmd, capture_output=True)

        # Parse results
        with open(f'{self.output_dir}/defects.json', 'r') as f:
            defects = json.load(f)

        total_defects = len(defects.get('issues', []))
        high_severity = sum(1 for d in defects.get('issues', [])
                          if d.get('impact') == 'High')
        medium_severity = sum(1 for d in defects.get('issues', [])
                            if d.get('impact') == 'Medium')

        print(f"\n=== Defect Summary ===")
        print(f"Total defects: {total_defects}")
        print(f"High severity: {high_severity}")
        print(f"Medium severity: {medium_severity}")

        # Fail build if thresholds exceeded
        if high_severity > 0:
            print(f"\n[FAIL] {high_severity} high-severity defects found")
            return False

        if medium_severity > 5:
            print(f"\n[FAIL] {medium_severity} medium-severity defects (max 5 allowed)")
            return False

        print(f"\n[PASS] Code meets quality thresholds")
        return True

# Example usage
if __name__ == "__main__":
    scanner = CoverityScanRunner(
        project_dir="/home/user/ecu-firmware",
        output_dir="/tmp/coverity-scan"
    )

    if not scanner.run_build_with_coverity():
        sys.exit(1)

    if not scanner.run_analysis():
        sys.exit(1)

    if not scanner.generate_report():
        sys.exit(1)

    sys.exit(0)
```

## Fuzzing for Vulnerability Discovery

```python
#!/usr/bin/env python3
"""
LibFuzzer Integration for Automotive Software
Continuous fuzzing in CI/CD pipeline
"""

import subprocess
import os
import time

class LibFuzzer:
    """LibFuzzer harness for automotive protocols"""

    def __init__(self, target_binary: str, corpus_dir: str):
        self.target_binary = target_binary
        self.corpus_dir = corpus_dir
        self.crashes_dir = f"{corpus_dir}/crashes"

        os.makedirs(self.crashes_dir, exist_ok=True)

    def fuzz(self, max_total_time: int = 3600, max_len: int = 1024):
        """Run fuzzing campaign"""
        print(f"=== Starting Fuzzing Campaign ===")
        print(f"[INFO] Target: {self.target_binary}")
        print(f"[INFO] Max time: {max_total_time}s")
        print(f"[INFO] Max input length: {max_len} bytes")

        cmd = [
            self.target_binary,
            self.corpus_dir,
            f'-max_total_time={max_total_time}',
            f'-max_len={max_len}',
            f'-artifact_prefix={self.crashes_dir}/',
            '-print_final_stats=1',
            '-close_fd_mask=3'  # Close stdout/stderr of target
        ]

        start_time = time.time()

        result = subprocess.run(cmd, capture_output=True, text=True)

        elapsed_time = time.time() - start_time

        # Parse fuzzing statistics
        stats = self._parse_stats(result.stderr)

        print(f"\n=== Fuzzing Results ===")
        print(f"Elapsed time: {elapsed_time:.2f}s")
        print(f"Total executions: {stats.get('total_execs', 0)}")
        print(f"Executions per second: {stats.get('execs_per_sec', 0)}")
        print(f"Coverage: {stats.get('coverage', 'N/A')}")

        # Check for crashes
        crash_files = [f for f in os.listdir(self.crashes_dir) if f.startswith('crash-')]

        if crash_files:
            print(f"\n[CRITICAL] {len(crash_files)} crashes discovered!")
            for crash_file in crash_files[:5]:  # Show first 5
                print(f"  - {crash_file}")

            return False
        else:
            print(f"\n[PASS] No crashes found during fuzzing")
            return True

    def _parse_stats(self, stderr_output: str) -> dict:
        """Parse libFuzzer statistics from stderr"""
        stats = {}

        # Example: "#12345: cov: 678 ft: 901 corp: 12/345b exec/s: 123 rss: 45Mb"
        import re

        match = re.search(r'#(\d+):', stderr_output)
        if match:
            stats['total_execs'] = int(match.group(1))

        match = re.search(r'exec/s:\s*(\d+)', stderr_output)
        if match:
            stats['execs_per_sec'] = int(match.group(1))

        match = re.search(r'cov:\s*(\d+)', stderr_output)
        if match:
            stats['coverage'] = match.group(1)

        return stats

# Example: CAN message parser fuzzing target
"""
// fuzz_can_parser.c
#include <stdint.h>
#include <stddef.h>
#include <string.h>

// Target function to fuzz
extern int parse_can_message(const uint8_t *data, size_t size);

// LibFuzzer entry point
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 8 || size > 16) {
        return 0;  // Invalid CAN message size
    }

    // Fuzz the CAN parser
    parse_can_message(data, size);

    return 0;
}

// Compile with:
// clang -fsanitize=fuzzer,address -g -O2 fuzz_can_parser.c can_parser.c -o fuzz_can_parser
"""

if __name__ == "__main__":
    fuzzer = LibFuzzer(
        target_binary="./fuzz_can_parser",
        corpus_dir="./corpus/can_messages"
    )

    # Seed corpus with valid CAN messages
    if not os.listdir(fuzzer.corpus_dir):
        print("[INFO] Creating seed corpus...")
        os.makedirs(fuzzer.corpus_dir, exist_ok=True)

        # Example: valid CAN message
        with open(f"{fuzzer.corpus_dir}/seed1", 'wb') as f:
            f.write(b'\x12\x34\x56\x78\x9A\xBC\xDE\xF0')

    # Run 1-hour fuzzing campaign
    if not fuzzer.fuzz(max_total_time=3600):
        print("[FAIL] Crashes found - investigate before release")
        exit(1)
```

## Secure CI/CD Pipeline

```yaml
# GitLab CI/CD Pipeline for Secure Automotive Software
stages:
  - build
  - security
  - test
  - deploy

variables:
  MISRA_COMPLIANCE_REQUIRED: "true"
  COVERITY_THRESHOLD_HIGH: "0"
  FUZZING_DURATION: "3600"

# Stage 1: Build with security flags
build_secure:
  stage: build
  script:
    - echo "Building with security hardening flags..."
    - make clean
    - make CFLAGS="-Wall -Wextra -Werror -fstack-protector-strong -D_FORTIFY_SOURCE=2 -fPIE -pie -Wformat -Wformat-security"
  artifacts:
    paths:
      - bin/
    expire_in: 1 hour

# Stage 2: MISRA C compliance check
misra_check:
  stage: security
  script:
    - echo "Running MISRA C:2012 compliance check..."
    - ./scripts/misra_check.sh
    - if [ $(grep -c "Mandatory.*violation" misra_reports/violations.txt) -gt 0 ]; then exit 1; fi
  dependencies:
    - build_secure
  artifacts:
    paths:
      - misra_reports/
    when: always

# Stage 3: Static analysis (Coverity)
static_analysis:
  stage: security
  script:
    - echo "Running Coverity static analysis..."
    - cov-build --dir cov-int make clean all
    - cov-analyze --dir cov-int --all --security
    - cov-format-errors --dir cov-int --json-output-v7 defects.json
    - python3 scripts/check_coverity_thresholds.py defects.json
  dependencies:
    - build_secure
  artifacts:
    paths:
      - defects.json
    when: always

# Stage 4: Fuzzing
fuzz_testing:
  stage: security
  script:
    - echo "Running LibFuzzer for $FUZZING_DURATION seconds..."
    - ./scripts/run_fuzzing.sh $FUZZING_DURATION
    - if [ -f crashes/*.crash ]; then echo "Crashes found!"; exit 1; fi
  dependencies:
    - build_secure
  allow_failure: false

# Stage 5: Dynamic analysis (AddressSanitizer)
dynamic_analysis:
  stage: test
  script:
    - echo "Running tests with AddressSanitizer..."
    - make clean
    - make CFLAGS="-fsanitize=address -fno-omit-frame-pointer -g"
    - ./run_tests.sh
  dependencies:
    - build_secure

# Stage 6: Code signing
sign_firmware:
  stage: deploy
  script:
    - echo "Signing firmware with HSM key..."
    - openssl dgst -sha256 -sign /secure/private_key.pem -out bin/firmware.sig bin/firmware.bin
    - echo "Firmware signed successfully"
  dependencies:
    - build_secure
    - static_analysis
    - fuzz_testing
  artifacts:
    paths:
      - bin/firmware.bin
      - bin/firmware.sig
  only:
    - main
    - release/*
```

## Threat Modeling (STRIDE)

```python
#!/usr/bin/env python3
"""
STRIDE Threat Modeling for Automotive Systems
Systematic identification of security threats
"""

from enum import Enum
from dataclasses import dataclass
from typing import List

class ThreatCategory(Enum):
    SPOOFING = "Spoofing"
    TAMPERING = "Tampering"
    REPUDIATION = "Repudiation"
    INFORMATION_DISCLOSURE = "Information Disclosure"
    DENIAL_OF_SERVICE = "Denial of Service"
    ELEVATION_OF_PRIVILEGE = "Elevation of Privilege"

@dataclass
class Threat:
    category: ThreatCategory
    description: str
    asset: str
    mitigation: str
    severity: str  # "Critical", "High", "Medium", "Low"

class STRIDEThreatModeler:
    """STRIDE threat modeling tool"""

    def __init__(self, system_name: str):
        self.system_name = system_name
        self.threats = []

    def model_data_flow(self, source: str, destination: str, protocol: str):
        """Model threats in data flow"""
        print(f"\n=== Threat Modeling: {source} -> {destination} ({protocol}) ===")

        # Spoofing
        self.threats.append(Threat(
            category=ThreatCategory.SPOOFING,
            description=f"Attacker impersonates {source} to send malicious data to {destination}",
            asset=f"Data flow: {source} -> {destination}",
            mitigation="Implement message authentication (MAC/digital signature)",
            severity="High"
        ))

        # Tampering
        self.threats.append(Threat(
            category=ThreatCategory.TAMPERING,
            description=f"Attacker modifies data in transit from {source} to {destination}",
            asset=f"Data flow: {source} -> {destination}",
            mitigation="Implement data integrity checks (HMAC, CRC with authentication)",
            severity="High"
        ))

        # Information Disclosure
        self.threats.append(Threat(
            category=ThreatCategory.INFORMATION_DISCLOSURE,
            description=f"Attacker eavesdrops on {protocol} communication",
            asset=f"Data flow: {source} -> {destination}",
            mitigation="Implement encryption (TLS 1.3, AES-256-GCM)",
            severity="Medium" if "telemetry" in source.lower() else "High"
        ))

        # Denial of Service
        self.threats.append(Threat(
            category=ThreatCategory.DENIAL_OF_SERVICE,
            description=f"Attacker floods {protocol} channel to prevent legitimate communication",
            asset=f"Data flow: {source} -> {destination}",
            mitigation="Implement rate limiting and traffic shaping",
            severity="Medium"
        ))

    def generate_threat_report(self, output_file: str):
        """Generate threat model report"""
        with open(output_file, 'w') as f:
            f.write(f"STRIDE Threat Model Report: {self.system_name}\n")
            f.write("=" * 60 + "\n\n")

            # Group by severity
            critical = [t for t in self.threats if t.severity == "Critical"]
            high = [t for t in self.threats if t.severity == "High"]
            medium = [t for t in self.threats if t.severity == "Medium"]
            low = [t for t in self.threats if t.severity == "Low"]

            f.write(f"Total threats identified: {len(self.threats)}\n")
            f.write(f"  Critical: {len(critical)}\n")
            f.write(f"  High: {len(high)}\n")
            f.write(f"  Medium: {len(medium)}\n")
            f.write(f"  Low: {len(low)}\n\n")

            # Detail threats
            for threat in self.threats:
                f.write(f"\n[{threat.severity}] {threat.category.value}\n")
                f.write(f"  Description: {threat.description}\n")
                f.write(f"  Asset: {threat.asset}\n")
                f.write(f"  Mitigation: {threat.mitigation}\n")

        print(f"[INFO] Threat model report: {output_file}")

# Example usage
if __name__ == "__main__":
    modeler = STRIDEThreatModeler("Telematics Control Unit (TCU)")

    # Model data flows
    modeler.model_data_flow("TCU", "Cloud Backend", "HTTPS/TLS")
    modeler.model_data_flow("TCU", "Gateway ECU", "CAN")
    modeler.model_data_flow("Mobile App", "TCU", "Bluetooth LE")

    # Generate report
    modeler.generate_threat_report("/tmp/stride_threat_model.txt")
```

## Best Practices

1. **Defense in Depth**: Multiple security layers (code quality + runtime protection + monitoring)
2. **Shift Left**: Integrate security early in SDLC (design phase threat modeling)
3. **Automated Enforcement**: CI/CD gates for MISRA compliance, static analysis, fuzzing
4. **Continuous Monitoring**: Track new CVEs, update dependencies, patch promptly
5. **Security Training**: Mandatory secure coding training for all developers

## References

- MISRA C:2012 Guidelines for C
- CERT C Secure Coding Standard
- AUTOSAR C++14 Coding Guidelines
- OWASP Secure Coding Practices
- ISO/SAE 21434: Cybersecurity Engineering
