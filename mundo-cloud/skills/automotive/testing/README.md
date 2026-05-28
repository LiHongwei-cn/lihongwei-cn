# Physical Testing & Metrology Skills

Comprehensive testing equipment integration for automotive battery validation and quality assurance.

## Overview

This testing suite provides integration with industry-standard physical testing equipment used in automotive battery development and validation. All implementations follow ISO 17025 calibration practices and industry test standards (ISO 16750, IEC 62133, SAE J2380, UN ECE R100).

## Skills Catalog

### 1. Power Analysis (`power-analysis.yaml`)
**Equipment:** Yokogawa WT series, Hioki PW series, Keysight PA series

**Capabilities:**
- High-precision voltage/current/power measurement (0.02% accuracy)
- Energy efficiency calculation (charge/discharge Wh, Ah)
- Harmonic analysis up to 50th order for AC systems
- Waveform capture up to 5MHz bandwidth
- Multi-channel synchronized measurements

**Standards:** IEC 61850, IEEE 1459, ISO 17025

**Skills (15):**
- Configure voltage/current ranges
- Measure instantaneous power (W, VAR, VA, PF)
- Start/stop energy integration
- Read integrated Wh and Ah
- Calculate round-trip efficiency
- Perform harmonic analysis (THD)
- Export waveform data
- Synchronize with external triggers
- Monitor power quality
- Generate calibration reports

### 2. Battery Cycling (`battery-cycling.yaml`)
**Equipment:** Chroma 17000 series, Arbin BT/MSTAT, Bitrode FTV/MCV, Maccor 4000

**Capabilities:**
- Automated charge/discharge cycling (up to 256 channels)
- CC-CV, CP, pulse, HPPC, GITT profiles
- Energy regeneration (up to 95% efficiency)
- Real-time safety monitoring
- Multi-year cycle life testing

**Standards:** IEC 62133, ISO 12405, UN 38.3, SAE J2464

**Skills (20):**
- Configure channel ranges
- Execute CC-CV charge
- Execute CC discharge
- Pulse power testing (HPPC)
- GITT analysis
- Formation cycling
- Cycle life testing (1000+ cycles)
- Calendar aging
- Load test schedules
- Monitor safety limits
- Emergency stop
- Export cycling data
- Calculate capacity fade
- Measure resistance growth
- Generate test reports

### 3. Oscilloscope (`oscilloscope.yaml`)
**Equipment:** Keysight MSOX/DSOX, Tektronix MSO/DPO, Rohde & Schwarz RTO, Lecroy

**Capabilities:**
- Waveform capture (16-bit, up to 2 GHz bandwidth)
- Ripple voltage/current measurement (mV resolution on DC)
- Transient analysis (rise time, overshoot, ringing)
- FFT spectrum analysis
- Protocol decoding (CAN, LIN, I2C, SPI)

**Standards:** IEC 61000-4-x (EMC), CISPR 25 (automotive EMI)

**Skills (15):**
- Configure channels and probes
- Set timebase and triggers
- Single/continuous acquisition
- Measure DC ripple
- Measure switching transients
- Perform FFT analysis
- Decode serial protocols
- Statistical analysis
- Export waveforms (CSV, binary)
- Segmented memory capture

### 4. Data Acquisition (`data-acquisition.yaml`)
**Equipment:** NI CompactDAQ/PXI, Dewetron DEWE2, HBM QuantumX, Yokogawa MX/MW

**Capabilities:**
- Multi-channel synchronized acquisition (up to 1000 channels)
- Diverse sensor types (voltage, current, TC, RTD, strain, IEPE)
- High-speed sampling (up to 1 MHz)
- GPS time synchronization
- Real-time calculation and alarming

**Standards:** ISO 16750 (automotive), ASAM MDF4 (data format)

**Skills (20):**
- Configure analog input channels
- Configure temperature sensors (TC, RTD)
- Configure strain gauges (bridge circuits)
- Set sampling rates per channel
- Implement triggered acquisition
- Continuous buffered acquisition
- Calculate derived channels (power, energy)
- Implement threshold alarms
- Export to TDMS, MDF4, HDF5, CSV
- Synchronize with CAN bus data

### 5. 3D Scanning (`3d-scanning.yaml`)
**Equipment:** Faro Focus/Freestyle, Hexagon Absolute Arm, GOM ATOS, Artec Eva

**Capabilities:**
- Point cloud acquisition (±0.05mm accuracy)
- CAD comparison and deviation analysis
- GD&T inspection (flatness, parallelism, position)
- Volume measurement
- Reverse engineering

**Standards:** ISO 10360 (CMM), ISO 1101 (GD&T), ASME Y14.5

**Skills (15):**
- Configure scanner parameters
- Acquire point clouds
- Register and align scans
- Compare to CAD model
- Measure flatness and parallelism
- Calculate form deviations
- Generate deviation color maps
- Export STL, STEP, IGES
- Perform statistical analysis
- Generate inspection reports

### 6. Thermal Chamber (`thermal-chamber.yaml`)
**Equipment:** Espec ESU/SU, Weiss Technik LabEvent, Cincinnati Sub-Zero, Thermotron

**Capabilities:**
- Temperature range: -40°C to +180°C (±0.5°C accuracy)
- Humidity control: 10-95% RH
- Programmable profiles (ramp, soak, cycle)
- Altitude simulation
- Combined environmental stress

**Standards:** ISO 16750-4, IEC 60068-2-1/2, MIL-STD-810

**Skills (15):**
- Set temperature setpoint
- Set humidity setpoint
- Program temperature profiles
- Execute thermal cycling
- Monitor chamber uniformity
- Implement safety interlocks
- Thermal shock testing
- Altitude simulation
- Export temperature logs
- Generate compliance reports

### 7. Vibration Test (`vibration-test.yaml`)
**Equipment:** IMV i-Series, Bruel & Kjaer LDS, Thermotron S-Series, MTS 850

**Capabilities:**
- Frequency range: 5-2000 Hz
- Acceleration: 0.1-100g RMS
- Test types: sine sweep, random, shock, road load
- Multi-axis (6-DOF) capability
- Closed-loop control

**Standards:** ISO 16750-3, SAE J2380, IEC 60068-2-64, MIL-STD-810

**Skills (10):**
- Configure sine sweep
- Configure random vibration (PSD)
- Execute shock profiles
- Replicate road load data
- Resonance search
- Set abort limits
- Multi-axis control
- Monitor transmissibility
- Export vibration data
- Generate test reports

## Tool Adapters

### Yokogawa Adapter (`yokogawa_adapter.py`)
**Lines:** 270+

**Features:**
- PyVISA interface for GPIB/Ethernet
- Support for WT1800E, WT5000, WT3000E models
- Integration mode control
- Harmonic analysis
- Efficiency calculation
- Waveform export

**Commands:**
- `measure_power`: Instantaneous V, I, P, S, Q, PF
- `configure_channels`: Set ranges and modes
- `start_integration`: Begin Wh/Ah accumulation
- `read_integration`: Get energy and charge
- `calculate_efficiency`: Compute round-trip efficiency
- `harmonic_analysis`: THD and individual harmonics
- `export_waveform`: Save raw waveform data

### Chroma Adapter (`chroma_adapter.py`)
**Lines:** 320+

**Features:**
- Modbus TCP communication
- Support for 17010H, 17020H, 17208M models
- CC-CV charge profiles
- CC discharge profiles
- Safety limit validation
- Test schedule loading

**Commands:**
- `configure_channel`: Set voltage/current ranges
- `charge_cc_cv`: Execute CC-CV charge
- `discharge_cc`: Execute CC discharge
- `rest`: Open circuit rest period
- `read_measurement`: Get V, I, Ah, Wh, T
- `run_cycle_test`: Automated cycling
- `stop_output`: Emergency stop
- `load_schedule`: Load test sequence file
- `export_data`: Save to CSV/JSON/TDMS

### INA226 Adapter (`ina226_adapter.py`)
**Lines:** 180+

**Features:**
- I2C interface for embedded systems
- High-precision current/voltage monitoring (16-bit)
- Programmable averaging (1-1024 samples)
- Alert threshold configuration
- Suitable for Raspberry Pi, BeagleBone

**Commands:**
- `configure`: Set averaging and conversion times
- `read_voltage`: Bus voltage (0-36V)
- `read_current`: Shunt current
- `read_power`: Calculated power
- `read_all`: V, I, P simultaneously
- `set_alert`: Configure threshold alarms
- `continuous_read`: Data logging
- `calibrate`: Update calibration for shunt

## Command Scripts

### power-analyze.sh
**Usage:**
```bash
./power-analyze.sh --model WT1800E \
                   --address "TCPIP0::192.168.1.10::INSTR" \
                   --channel 1 \
                   --voltage-range 300 \
                   --current-range 50 \
                   --integration \
                   --duration 3600 \
                   --output power_test.csv
```

**Output:** CSV with timestamp, V, I, P, S, Q, PF, Wh, Ah

### battery-cycle.sh
**Usage:**
```bash
./battery-cycle.sh --model 17010H \
                   --ip 192.168.1.100 \
                   --channel 1 \
                   --charge-current 1.0 \
                   --charge-voltage 4.2 \
                   --discharge-current 2.0 \
                   --discharge-voltage 2.5 \
                   --cycles 100 \
                   --rest-time 300 \
                   --output cycle_test.csv
```

**Output:** CSV with cycle number, phase, V, I, Ah, Wh, T

### thermal-test.sh
**Usage:**
```bash
./thermal-test.sh --ip 192.168.1.50 \
                  --hot-temp 60 \
                  --cold-temp -20 \
                  --soak-time 1800 \
                  --cycles 10 \
                  --ramp-rate 5.0 \
                  --humidity 50 \
                  --output thermal_log.csv
```

**Output:** CSV with cycle, phase, setpoint, actual temp, humidity

## Agents

### Test Engineer Agent (`test-engineer.yaml`)
**Role:** Physical testing equipment integration and test execution

**Expertise:**
- Power analyzers, battery cyclers, DAQ systems
- Environmental chambers, vibration systems
- Test automation and data analysis
- ISO/IEC/SAE standards compliance

**Use Cases:**
- Battery efficiency testing
- Cycle life validation
- Environmental stress testing
- Vibration qualification
- Power quality measurement

### Metrology Specialist Agent (`metrology-specialist.yaml`)
**Role:** Dimensional inspection and quality assurance

**Expertise:**
- 3D laser scanning and CMM programming
- GD&T per ASME Y14.5
- Point cloud processing
- Statistical process control
- Reverse engineering

**Use Cases:**
- Battery module dimensional inspection
- Busbar flatness measurement
- Assembly gap analysis
- CAD vs. as-built comparison
- Manufacturing process capability studies

## Dependencies

```bash
# Python packages
pip install pyvisa pyvisa-py  # VISA instrument control
pip install pymodbus          # Modbus TCP/RTU
pip install python-can        # CAN bus integration
pip install smbus2            # I2C for INA226
pip install numpy pandas      # Data processing
pip install scipy             # Signal analysis
pip install matplotlib        # Visualization
pip install open3d            # Point cloud processing
pip install h5py              # HDF5 file format
pip install cantools          # CAN database parsing

# System packages (Ubuntu/Debian)
sudo apt-get install libusb-1.0-0-dev  # USB-TMC
sudo apt-get install libnidaqmx        # NI-DAQmx (if using NI hardware)
```

## Quick Start

### 1. Battery Efficiency Test
```bash
# Terminal 1: Power analyzer
cd commands/testing
./power-analyze.sh --model WT1800E --integration --duration 7200 --output power.csv

# Terminal 2: Battery cycler
./battery-cycle.sh --model 17010H --cycles 1 --output cycling.csv

# Analyze results
python3 << EOF
import pandas as pd
power = pd.read_csv('power.csv')
cycling = pd.read_csv('cycling.csv')

# Calculate efficiency
charge_wh = power[power['current_a'] > 0]['power_w'].sum() / 3600
discharge_wh = power[power['current_a'] < 0]['power_w'].sum() / 3600
efficiency = (discharge_wh / charge_wh) * 100

print(f"Charge Energy: {charge_wh:.2f} Wh")
print(f"Discharge Energy: {discharge_wh:.2f} Wh")
print(f"Efficiency: {efficiency:.2f}%")
EOF
```

### 2. Thermal Cycling Test
```bash
# Execute 100 cycles (-20°C to +60°C)
./thermal-test.sh --hot-temp 60 --cold-temp -20 \
                  --soak-time 1800 --cycles 100 \
                  --output thermal_cycling_100cycles.csv

# Plot temperature profile
python3 << EOF
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('thermal_cycling_100cycles.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['actual_c'], label='Actual')
plt.plot(df['timestamp'], df['setpoint_c'], label='Setpoint', linestyle='--')
plt.xlabel('Time')
plt.ylabel('Temperature (°C)')
plt.title('Thermal Cycling Profile')
plt.legend()
plt.grid(True)
plt.savefig('thermal_profile.png', dpi=300)
EOF
```

## Test Standards Compliance

| Standard | Description | Applicable Skills |
|----------|-------------|-------------------|
| ISO 16750-3 | Mechanical loads | vibration-test |
| ISO 16750-4 | Climate loads | thermal-chamber |
| IEC 62133 | Safety of batteries | battery-cycling, power-analysis |
| ISO 12405 | HEV battery testing | battery-cycling |
| SAE J2380 | EV battery vibration | vibration-test |
| UN ECE R100 | Electric powertrains | All |
| ISO 17025 | Testing/calibration labs | All |
| IEC 61850 | Substation automation | power-analysis |
| ISO 1101 | Geometrical tolerancing | 3d-scanning |
| ASME Y14.5 | Dimensioning and tolerancing | 3d-scanning |

## Safety Considerations

### Electrical Safety
- High voltage battery packs (up to 800V)
- Isolation barriers and safety interlocks
- Emergency stop procedures
- Arc flash protection
- Regular calibration verification

### Environmental Safety
- Thermal runaway detection
- Smoke and gas sensors
- Fire suppression systems
- Ventilation requirements
- Personal protective equipment

### Mechanical Safety
- Vibration fixture validation
- Abort limits for specimen protection
- Proper mounting and grounding
- Resonance avoidance
- Safety barriers during operation

## Data Management

### File Formats
- **CSV**: Universal, human-readable, but large file size
- **TDMS**: NI format, efficient binary, includes metadata
- **MDF4**: ASAM standard, automotive industry standard
- **HDF5**: Hierarchical, efficient for large datasets
- **Parquet**: Columnar storage, excellent compression

### Traceability Requirements
- Equipment serial numbers and calibration dates
- Test procedure version and revision
- DUT identification (serial number, batch)
- Environmental conditions during test
- Operator identification
- Timestamp with time zone
- Git commit hash of test code (if automated)

## Contribution

When adding new testing equipment:
1. Create skill YAML with 10-20 specific capabilities
2. Implement tool adapter inheriting from `OpensourceToolAdapter`
3. Add command script with comprehensive error handling
4. Update this README with equipment specifications
5. Include example usage and output format
6. Document applicable standards

## License

All testing skills and adapters are provided under the project's main license.
Equipment-specific communication protocols remain property of manufacturers.

---

**Total Skills:** 110 (across 7 categories)
**Total Adapters:** 3 (270+ lines each)
**Total Agents:** 2 (specialized expertise)
**Total Commands:** 3 (comprehensive automation)
**Supported Equipment Vendors:** 20+ (Yokogawa, Chroma, Keysight, NI, Faro, etc.)
