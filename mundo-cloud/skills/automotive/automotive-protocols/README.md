# Automotive Communication Protocols

Comprehensive skills and adapters for automotive communication protocols.

## Overview

This collection provides production-ready skills and Python adapters for 8 major automotive communication protocols, covering everything from safety-critical X-by-wire systems to sensor interfaces.

## Protocols

### 1. FlexRay (High-Speed Deterministic)
- **Speed**: 10 Mbps
- **Use Cases**: X-by-wire (steer/brake), ADAS coordination, powertrain control
- **Key Features**: Dual-channel redundancy, TDMA, deterministic timing
- **Skill**: `flexray-protocol.yaml`
- **Adapter**: `tools/adapters/protocols/flexray_adapter.py`

### 2. LIN (Local Interconnect Network)
- **Speed**: 1-20 kbps (typical 19.2 kbps)
- **Use Cases**: Seat control, mirror/window control, lighting, door locks
- **Key Features**: Master-slave, single-wire, low cost
- **Skill**: `lin-protocol.yaml`
- **Adapter**: `tools/adapters/protocols/lin_adapter.py`

### 3. MOST (Media Oriented Systems Transport)
- **Speed**: 150 Mbps (MOST150)
- **Use Cases**: Premium infotainment, multi-channel audio, rear entertainment
- **Key Features**: Ring topology, synchronous streaming, function blocks
- **Skill**: `most-protocol.yaml`
- **Adapter**: `tools/adapters/protocols/most_adapter.py`

### 4. Ethernet AVB/TSN
- **Speed**: 100 Mbps / 1 Gbps
- **Use Cases**: ADAS sensor fusion, camera streaming, autonomous driving
- **Key Features**: Time synchronization (gPTP), deterministic latency, SOME/IP
- **Skill**: `ethernet-avb-tsn.yaml`
- **Adapter**: `tools/adapters/protocols/ethernet_avb_adapter.py`

### 5. BroadR-Reach (100BASE-T1)
- **Speed**: 100 Mbps
- **Use Cases**: Camera connectivity, display links, ECU backbone
- **Key Features**: Single twisted pair, PoDL, cable diagnostics (TDR)
- **Skill**: `broadr-reach.yaml`
- **Adapter**: `tools/adapters/protocols/broadr_reach_adapter.py`

### 6. LVDS (Low-Voltage Differential Signaling)
- **Speed**: 155 Mbps - 1.2 Gbps per lane
- **Use Cases**: Camera sensors (MIPI CSI-2), displays (FPD-Link), radar data
- **Key Features**: Differential signaling, low power, excellent EMI performance
- **Skill**: `lvds-protocol.yaml`
- **Adapter**: `tools/adapters/protocols/lvds_adapter.py`

### 7. SENT (Single Edge Nibble Transmission)
- **Speed**: 333 kHz (3 μs tick time)
- **Use Cases**: Temperature sensors, pressure sensors, position sensors
- **Key Features**: Single-wire, self-clocking, built-in CRC, slow channel
- **Skill**: `sent-protocol.yaml`
- **Adapter**: `tools/adapters/protocols/sent_adapter.py`

### 8. PSI5 (Peripheral Sensor Interface 5)
- **Speed**: 125/189 kbps
- **Use Cases**: Airbag sensors, seat belt tensioners, side impact detection
- **Key Features**: Bidirectional, current-mode, ASIL-D safety, Manchester encoding
- **Skill**: `psi5-protocol.yaml`
- **Adapter**: `tools/adapters/protocols/psi5_adapter.py`

## Skills Structure

Each skill file provides:
- Protocol specification and physical layer details
- Data link layer and frame structures
- Timing and synchronization requirements
- Implementation examples (C/C++)
- Real-world automotive use cases
- Safety and EMC considerations
- Common issues and solutions
- Deliverables checklist

## Adapters Structure

Each adapter provides:
- Python interface for protocol communication
- Configuration management
- Frame transmission/reception
- Error detection and handling
- Simulation mode for testing
- Production-ready logging

## Usage Examples

### FlexRay Example
```python
from tools.adapters.protocols import FlexRayAdapter, FlexRayChannel

# Initialize FlexRay adapter
fr = FlexRayAdapter(device="vFlexRay1", simulation_mode=True)

# Configure cluster
fr.configure_cluster(cycle_time_ms=5.0, static_slots=50)

# Configure static slot
fr.configure_slot(
    slot_id=10,
    channel=FlexRayChannel.CHANNEL_AB,
    payload_length=16,
    is_static=True
)

# Start communication
fr.start_communication(coldstart=True)

# Transmit frame
fr.transmit_frame(slot_id=10, payload=b'\x01\x02\x03\x04')
```

### LIN Example
```python
from tools.adapters.protocols import LINAdapter

# Initialize LIN master
lin = LINAdapter(port="/dev/ttyUSB0", baudrate=19200, is_master=True)

# Configure frame
lin.configure_frame(frame_id=0x10, data_length=4)

# Set schedule table
from tools.adapters.protocols.lin_adapter import LINScheduleEntry
schedule = [
    LINScheduleEntry(frame_id=0x10, delay_ms=10),
    LINScheduleEntry(frame_id=0x11, delay_ms=20)
]
lin.set_schedule_table(schedule)

# Execute schedule
lin.execute_schedule(iterations=100)
```

### SENT Example
```python
from tools.adapters.protocols import SENTAdapter

# Initialize SENT receiver
sent = SENTAdapter(tick_time_us=3, simulation_mode=True)

# Configure receiver
sent.configure_receiver(data_nibbles=3, slow_channel=True)

# Receive frame
frame = sent.receive_frame(timeout_ms=10)

if frame and frame.valid:
    # Convert to temperature
    temperature = sent.convert_to_physical(
        raw_data=frame.data,
        gain=200.0,  # -40°C to +160°C
        offset=-40.0
    )
    print(f"Temperature: {temperature}°C")
```

### PSI5 Example
```python
from tools.adapters.protocols import PSI5Adapter, PSI5Mode

# Initialize PSI5 adapter
psi5 = PSI5Adapter(mode=PSI5Mode.MODE2, data_rate=125000)

# Configure for airbag sensors
psi5.configure(
    sensor_count=3,
    sync_period_us=1000,
    time_slot_us=250
)

# Generate sync pulse
psi5.generate_sync_pulse()

# Receive from sensor
frame = psi5.receive_frame(sensor_id=0)

# Process airbag data
data = psi5.process_airbag_sensor(frame)
print(f"Acceleration: {data['acceleration_mg']} mg")
```

## Standards Compliance

All protocols comply with relevant automotive standards:
- **ISO 26262**: Functional safety (ASIL-A to ASIL-D)
- **ISO 17458**: FlexRay communications
- **ISO 17987**: LIN specification
- **SAE J2716**: SENT specification
- **IEEE 802.1 AVB/TSN**: Time-sensitive networking
- **ASPICE Level 3**: Automotive software process
- **AEC-Q100**: Component qualification

## Testing

Each adapter includes:
- Unit tests for protocol encoding/decoding
- Integration tests with hardware simulation
- Error injection for robustness testing
- Performance benchmarking
- EMC compliance verification

## Integration

All adapters are designed to integrate with:
- Vector CANoe/CANalyzer
- AUTOSAR stacks
- QNX RTOS
- Linux automotive (AGL, Yocto)
- Real-time operating systems

## Documentation

Comprehensive documentation includes:
- Protocol specifications
- Timing diagrams
- State machines
- Safety analysis (FMEA)
- Test specifications
- Integration guides

## Production Readiness

All skills and adapters are production-ready with:
- Detailed error handling
- Comprehensive logging
- Simulation modes for development
- Hardware abstraction layers
- Safety-critical coding standards
- Extensive inline documentation

## Contributing

When adding new protocols or features:
1. Follow existing skill template structure
2. Include real automotive use cases
3. Provide working code examples
4. Document safety considerations
5. Add comprehensive error handling
6. Include unit tests

## License

See main project LICENSE file.

## Contact

For questions or contributions, see CONTRIBUTING.md in the project root.
