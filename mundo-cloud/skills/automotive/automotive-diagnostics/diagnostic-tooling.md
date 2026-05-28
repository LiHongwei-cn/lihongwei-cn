# Diagnostic Tooling - CANoe, CAPL, ODXStudio

## Overview

Professional automotive diagnostic tools include CANoe/CANalyzer for testing, CAPL for scripting, ODXStudio for database creation, and open-source alternatives. This skill covers tooling ecosystems and DIY diagnostic development.

## Vector CANoe/CANalyzer

### CANoe Features
- Network simulation and testing
- ECU testing and validation
- Diagnostic protocol support (UDS, OBD-II, DoIP)
- CAPL scripting for automation
- Test automation frameworks

### CAPL (Communication Access Programming Language)

**CAPL Script Example - Automated Diagnostic Test:**

```c
/*
 * CAPL Script: Automated UDS Diagnostic Test
 * Tests: Session control, DTC reading, parameter reading
 */

includes
{
  #include "DiagnosticLibrary.cin"
}

variables
{
  int gTestsPassed = 0;
  int gTestsFailed = 0;
  int gTestTimeout = 2000;  // ms

  // Diagnostic addresses
  const dword kTesterAddress = 0x7E0;
  const dword kECUAddress = 0x7E8;

  // Test results
  char gTestReport[1000];
}

/* Initialize test environment */
on start
{
  write("========================================");
  write("UDS Diagnostic Test Suite");
  write("========================================");

  // Initialize diagnostic session
  DiagInit(kTesterAddress, kECUAddress);

  // Start test sequence
  setTimer(tmrStartTests, 100);
}

/* Test 1: Extended Diagnostic Session */
on timer tmrStartTests
{
  write("\n[Test 1] Extended Diagnostic Session");

  // Build UDS request: 0x10 0x03
  byte request[2];
  request[0] = 0x10;  // DiagnosticSessionControl
  request[1] = 0x03;  // Extended session

  // Send diagnostic request
  DiagSendRequest(request, 2);

  // Wait for response
  setTimer(tmrTest1Response, gTestTimeout);
}

/* Handle Test 1 Response */
on timer tmrTest1Response
{
  byte response[100];
  int length;

  if (DiagReceiveResponse(response, length))
  {
    if (response[0] == 0x50 && response[1] == 0x03)
    {
      write("  [PASS] Extended session activated");
      gTestsPassed++;

      // Start next test
      setTimer(tmrTest2, 100);
    }
    else if (response[0] == 0x7F)
    {
      write("  [FAIL] Negative response: 0x%02X", response[2]);
      gTestsFailed++;
      TestFailed();
    }
    else
    {
      write("  [FAIL] Invalid response format");
      gTestsFailed++;
      TestFailed();
    }
  }
  else
  {
    write("  [FAIL] Timeout waiting for response");
    gTestsFailed++;
    TestFailed();
  }
}

/* Test 2: Read DTCs */
on timer tmrTest2
{
  write("\n[Test 2] Read Diagnostic Trouble Codes");

  // Build UDS request: 0x19 0x02 0xFF
  byte request[3];
  request[0] = 0x19;  // ReadDTCInformation
  request[1] = 0x02;  // reportDTCByStatusMask
  request[2] = 0xFF;  // All status masks

  DiagSendRequest(request, 3);
  setTimer(tmrTest2Response, gTestTimeout);
}

/* Handle Test 2 Response */
on timer tmrTest2Response
{
  byte response[100];
  int length;
  int i, dtcCount;

  if (DiagReceiveResponse(response, length))
  {
    if (response[0] == 0x59 && response[1] == 0x02)
    {
      // Parse DTC count (after status availability mask)
      dtcCount = (length - 4) / 4;

      write("  [PASS] Read %d DTCs", dtcCount);

      // Parse and display DTCs
      for (i = 0; i < dtcCount; i++)
      {
        int offset = 4 + i * 4;
        char dtc[10];
        ParseDTC(response[offset], response[offset+1], response[offset+2], dtc);
        byte status = response[offset+3];

        write("    DTC: %s, Status: 0x%02X", dtc, status);
      }

      gTestsPassed++;
      setTimer(tmrTest3, 100);
    }
    else if (response[0] == 0x7F)
    {
      write("  [FAIL] Negative response: 0x%02X", response[2]);
      gTestsFailed++;
      TestFailed();
    }
  }
  else
  {
    write("  [FAIL] Timeout");
    gTestsFailed++;
    TestFailed();
  }
}

/* Test 3: Read Data by Identifier (VIN) */
on timer tmrTest3
{
  write("\n[Test 3] Read VIN (DID 0xF190)");

  byte request[3];
  request[0] = 0x22;  // ReadDataByIdentifier
  request[1] = 0xF1;  // DID high byte
  request[2] = 0x90;  // DID low byte

  DiagSendRequest(request, 3);
  setTimer(tmrTest3Response, gTestTimeout);
}

/* Handle Test 3 Response */
on timer tmrTest3Response
{
  byte response[100];
  int length;
  char vin[18];

  if (DiagReceiveResponse(response, length))
  {
    if (response[0] == 0x62 && response[1] == 0xF1 && response[2] == 0x90)
    {
      // Extract VIN (17 characters)
      int i;
      for (i = 0; i < 17; i++)
      {
        vin[i] = response[3 + i];
      }
      vin[17] = 0;  // Null terminate

      write("  [PASS] VIN: %s", vin);
      gTestsPassed++;

      // Complete test suite
      setTimer(tmrTestComplete, 100);
    }
    else if (response[0] == 0x7F)
    {
      write("  [FAIL] Negative response: 0x%02X", response[2]);
      gTestsFailed++;
      TestFailed();
    }
  }
  else
  {
    write("  [FAIL] Timeout");
    gTestsFailed++;
    TestFailed();
  }
}

/* Test Suite Complete */
on timer tmrTestComplete
{
  write("\n========================================");
  write("Test Suite Complete");
  write("  Tests Passed: %d", gTestsPassed);
  write("  Tests Failed: %d", gTestsFailed);
  write("========================================");

  if (gTestsFailed == 0)
  {
    write("RESULT: ALL TESTS PASSED");
  }
  else
  {
    write("RESULT: SOME TESTS FAILED");
  }
}

/* Handle test failure */
void TestFailed()
{
  setTimer(tmrTestComplete, 100);
}

/* Parse DTC bytes to string format */
void ParseDTC(byte high, byte mid, byte low, char dtc[10])
{
  byte system = (high >> 6) & 0x03;
  byte digit1 = (high >> 4) & 0x03;
  byte digit2 = high & 0x0F;
  byte digit3 = (mid >> 4) & 0x0F;
  byte digit4 = mid & 0x0F;

  char systemChar;
  switch (system)
  {
    case 0: systemChar = 'P'; break;
    case 1: systemChar = 'C'; break;
    case 2: systemChar = 'B'; break;
    case 3: systemChar = 'U'; break;
  }

  snprintf(dtc, 10, "%c%d%X%X%X", systemChar, digit1, digit2, digit3, digit4);
}

/* Diagnostic helper functions */
void DiagInit(dword tester, dword ecu)
{
  // Initialize diagnostic addressing
  write("Initializing diagnostic session");
  write("  Tester: 0x%03X", tester);
  write("  ECU:    0x%03X", ecu);
}

void DiagSendRequest(byte request[], int length)
{
  // Send diagnostic request via CAN
  message * msg;
  int i;

  msg = {CAN, kTesterAddress, 0, 8};

  // Build ISO-TP single frame or multi-frame message
  if (length <= 7)
  {
    // Single frame
    msg.byte(0) = 0x00 | length;
    for (i = 0; i < length; i++)
    {
      msg.byte(i + 1) = request[i];
    }
    output(msg);
  }
  else
  {
    // Multi-frame (simplified - full implementation needed)
    write("  Sending multi-frame request");
  }
}

int DiagReceiveResponse(byte response[], int &length)
{
  // Simplified - actual implementation needs ISO-TP handling
  // This would be called from on message handler
  return 0;
}
```

## Open Source Diagnostic Tools

### python-uds

```python
#!/usr/bin/env python3
"""
python-uds library usage example
Install: pip install python-uds
"""

from uds import Uds
from uds.uds_communications import IsoTpProtocol

# Create UDS client
tp = IsoTpProtocol(bustype='socketcan', channel='can0', rxid=0x7E8, txid=0x7E0)
client = Uds(tp)

# Extended diagnostic session
response = client.diagnostic_session_control(0x03)
print(f"Session response: {response.hex()}")

# Read VIN
response = client.read_data_by_identifier(0xF190)
if response:
    vin = response[3:].decode('ascii')
    print(f"VIN: {vin}")

# Read DTCs
dtcs = client.read_dtc_information_report_dtc_by_status_mask(0xFF)
print(f"DTCs: {dtcs}")

# Close connection
tp.close()
```

### python-can with isotp

```python
#!/usr/bin/env python3
"""
DIY diagnostic tool using python-can
"""

import can
import isotp
import time

# Initialize CAN bus
bus = can.interface.Bus(channel='can0', bustype='socketcan')

# Initialize ISO-TP stack
isotp_params = isotp.params.LinkLayerProtocol.CAN()
address = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7E0, rxid=0x7E8)
stack = isotp.CanStack(bus, address, params=isotp_params)

# Start stack
stack.start()

# Send UDS request - Read VIN
request = bytes([0x22, 0xF1, 0x90])
stack.send(request)

# Wait for response
time.sleep(0.5)
if stack.available():
    response = stack.recv()
    print(f"Response: {response.hex()}")

    if response[0] == 0x62:
        vin = response[3:20].decode('ascii')
        print(f"VIN: {vin}")

# Clean up
stack.stop()
bus.shutdown()
```

### OpenDiag - Open Source Diagnostic Suite

```bash
# Install OpenDiag
git clone https://github.com/opendiag/opendiag.git
cd opendiag
make
sudo make install

# Run diagnostic session
opendiag -i can0 -t 0x7E0 -r 0x7E8

# Commands:
> session 03        # Extended session
> read 0xF190      # Read VIN
> dtc              # Read DTCs
> clear            # Clear DTCs
```

## DIY OBD-II Scanner

### ELM327-Based Scanner

```python
#!/usr/bin/env python3
"""
DIY OBD-II Scanner using ELM327
Hardware: ELM327 USB adapter
"""

import serial
import time

class OBD2Scanner:
    """Simple OBD-II scanner."""

    def __init__(self, port='/dev/ttyUSB0', baudrate=38400):
        self.serial = serial.Serial(port, baudrate, timeout=1)
        self.initialize()

    def initialize(self):
        """Initialize ELM327."""
        commands = ['ATZ', 'ATE0', 'ATL0', 'ATSP0']
        for cmd in commands:
            self.send_command(cmd)
            time.sleep(0.1)

    def send_command(self, cmd):
        """Send command to ELM327."""
        self.serial.write((cmd + '\r').encode())
        return self.serial.read_until(b'>').decode().strip()

    def read_rpm(self):
        """Read engine RPM."""
        response = self.send_command('010C')
        # Parse response: 41 0C AA BB
        if '410C' in response:
            hex_data = response.replace('410C', '').replace(' ', '')
            rpm = int(hex_data, 16) / 4
            return rpm
        return None

    def read_speed(self):
        """Read vehicle speed."""
        response = self.send_command('010D')
        if '410D' in response:
            hex_data = response.replace('410D', '').replace(' ', '')
            speed = int(hex_data, 16)
            return speed
        return None

    def read_dtcs(self):
        """Read stored DTCs."""
        response = self.send_command('03')
        # Parse DTCs from response
        dtcs = []
        # Implementation: Parse DTC bytes
        return dtcs

# Usage
scanner = OBD2Scanner()
rpm = scanner.read_rpm()
speed = scanner.read_speed()
print(f"RPM: {rpm}, Speed: {speed} km/h")
```

## CANalyzer Test Configuration

### Test Node Configuration (XML)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CANalyzerTestConfiguration>
  <TestModules>
    <TestModule name="UDS_DiagnosticTests">
      <TestCases>
        <TestCase name="ReadVIN">
          <Steps>
            <Step action="SendDiagnostic">
              <Request>22 F1 90</Request>
              <ExpectedResponse>62 F1 90 [17 bytes]</ExpectedResponse>
              <Timeout>1000</Timeout>
            </Step>
          </Steps>
        </TestCase>

        <TestCase name="ReadDTCs">
          <Steps>
            <Step action="SendDiagnostic">
              <Request>19 02 FF</Request>
              <ExpectedResponse>59 02 *</ExpectedResponse>
              <Timeout>2000</Timeout>
            </Step>
          </Steps>
        </TestCase>
      </TestCases>
    </TestModule>
  </TestModules>
</CANalyzerTestConfiguration>
```

## Vector ODXStudio

### Creating ODX Database

1. **Create New Project**: File → New → ODX Project
2. **Define ECU Variant**: Add base variant for ECU
3. **Add Diagnostic Services**: Import UDS services or create custom
4. **Define Data Identifiers**: Add DIDs with encoding/scaling
5. **Define DTCs**: Add trouble codes with descriptions
6. **Add Communication Parameters**: CAN IDs, timing, etc.
7. **Validate**: Tools → Validate ODX
8. **Export**: File → Export → ODX 2.2.0

## Best Practices

1. **Use version control** for CAPL scripts and test configurations
2. **Modularize test scripts** - separate test cases for reusability
3. **Log all test results** with timestamps and conditions
4. **Implement error handling** in CAPL scripts
5. **Use ODX databases** to avoid hardcoded values
6. **Automate regression testing** with CANoe test automation
7. **Validate diagnostic databases** before deployment

## Tool Comparison

| Tool | Purpose | Cost | Protocols | Scripting |
|------|---------|------|-----------|-----------|
| CANoe | Testing/Simulation | $$$ | CAN, LIN, FlexRay, Ethernet | CAPL, .NET |
| CANalyzer | Analysis | $$$ | CAN, LIN, FlexRay | CAPL |
| ODXStudio | ODX Creation | $$$ | N/A | N/A |
| python-uds | Diagnostics | Free | UDS | Python |
| python-can | CAN Communication | Free | CAN | Python |
| OpenDiag | Diagnostics | Free | OBD-II, UDS | CLI |

## References

- Vector CANoe User Manual
- CAPL Programming Guide
- ODXStudio Documentation
- python-uds documentation: https://github.com/pylessard/python-udsoncan
