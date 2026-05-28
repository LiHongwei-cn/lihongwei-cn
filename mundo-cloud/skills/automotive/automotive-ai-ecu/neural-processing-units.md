# Neural Processing Units (NPUs) for Automotive

**Skill**: Deep understanding of automotive NPU architectures, performance characteristics, and optimization
**Version**: 1.0.0
**Category**: AI-ECU / Hardware Architecture
**Complexity**: Expert

---

## Overview

Comprehensive guide to Neural Processing Units (NPUs) in automotive systems. Covers architecture, performance benchmarking, memory optimization, power management, and thermal considerations for production vehicle deployments.

## NPU Architecture Fundamentals

### What is an NPU?

**Neural Processing Unit (NPU)** = Specialized accelerator for neural network inference
- **MAC Arrays**: Massive parallel multiply-accumulate units (thousands to millions)
- **Dataflow**: Optimized for tensor operations (convolution, matrix multiplication)
- **Memory Hierarchy**: On-chip SRAM, DDR interface, DMA engines
- **Quantization Support**: INT8, INT16, INT4, mixed-precision

**Why NPUs over GPUs/CPUs?**
- **10-100x** better TOPS/Watt efficiency
- **Lower latency** (no PCIe overhead, optimized dataflow)
- **Smaller footprint** (< 10mm² die area vs. 300mm² GPU)
- **Automotive-grade** (-40°C to +125°C junction temp)

---

## Automotive NPU Landscape

### 1. Qualcomm Snapdragon Ride Platform

**Architecture**: Hexagon Tensor Accelerator (HTA) + Scalar/Vector DSP

```
Snapdragon Ride Flex SoC (2023)
├── CPU: 8x Kryo Gold (ARM Cortex-A78) @ 2.8 GHz
├── NPU: HTA 7th Gen
│   ├── 300 TOPS (INT8)
│   ├── 32 MB on-chip SRAM
│   ├── 8x 512-bit vector units
│   └── Hardware FP16/INT8/INT4 support
├── GPU: Adreno 740 (3 TFLOPS FP32)
├── Memory: LPDDR5 @ 51.2 GB/s
└── ISP: Triple 14-bit Spectra ISP (3x 36 MP @ 30fps)

Power Budget:
- Peak: 35W (full SoC)
- NPU only: 8-12W @ 300 TOPS
- Efficiency: 25-37 TOPS/W
```

**Programming Model**:
```python
# Qualcomm SNPE (Snapdragon Neural Processing Engine)
import snpe

# Model compiled for HTA backend
container = snpe.load_container('model_hta.dlc')

# Execution options
runtime = snpe.SNPE_Runtime.RUNTIME_HTA  # Force HTA backend
buffer_type = snpe.BufferType.USERBUFFER_TF8  # Use INT8 tensors

network = snpe.build_network(
    container,
    runtime_list=[runtime],
    use_user_supplied_buffers=True,
    buffer_type=buffer_type
)

# Inference
input_tensor = np.random.randint(0, 255, (1, 3, 640, 640), dtype=np.uint8)
output = network.execute({'input': input_tensor})

# Performance profiling
perf_info = network.get_performance_metrics()
print(f"Total time: {perf_info['total_inference_time']}ms")
print(f"HTA time: {perf_info['hta_execution_time']}ms")
print(f"DMA time: {perf_info['dma_transfer_time']}ms")
```

**HTA Architecture Details**:
- **Tensor Cores**: 32x32 systolic array per core (8 cores)
- **Vector ALUs**: 512-bit SIMD units for element-wise ops
- **Activation Functions**: Hardware-accelerated ReLU, Sigmoid, Tanh
- **Bandwidth**: 512 GB/s internal, 51 GB/s external DDR

---

### 2. NXP i.MX 8M Plus eIQ

**Architecture**: Vivante VIPNano-QI NPU

```
i.MX 8M Plus SoC
├── CPU: 4x Cortex-A53 @ 1.8 GHz + 1x Cortex-M7 @ 800 MHz
├── NPU: Vivante VIPNano-QI
│   ├── 2.3 TOPS (INT8)
│   ├── 384 KB on-chip SRAM
│   ├── 64 MAC units (8x8 array)
│   └── INT8/INT16/FP16 support
├── GPU: GC7000UL (176 GFLOPS FP32)
├── Memory: LPDDR4 @ 4 GB/s
└── ISP: Dual-camera ISP (2x 12 MP)

Power Budget:
- Full SoC: 3-5W (typical automotive workload)
- NPU only: 0.8-1.5W @ 2.3 TOPS
- Efficiency: 1.5-2.8 TOPS/W
```

**NPU Register Programming** (low-level):
```c
/* Direct register access for NPU control (advanced) */
#include <vip_lite.h>

typedef struct {
    uint32_t base_addr;
    uint32_t axi_sram_base;
    uint32_t axi_sram_size;
} vip_npu_config_t;

int configure_npu_for_inference(vip_npu_config_t *config) {
    // 1. Enable NPU clock
    writel(NPU_CLK_ENABLE, config->base_addr + NPU_CLK_CTRL);

    // 2. Configure AXI SRAM (384 KB on-chip)
    writel(config->axi_sram_base, config->base_addr + NPU_AXI_SRAM_BASE);
    writel(config->axi_sram_size, config->base_addr + NPU_AXI_SRAM_SIZE);

    // 3. Set memory bandwidth priority (critical for automotive)
    writel(NPU_PRIORITY_HIGH, config->base_addr + NPU_AXI_QOS);

    // 4. Configure power management
    writel(NPU_POWER_MODE_PERFORMANCE, config->base_addr + NPU_PM_CTRL);

    // 5. Clear interrupt flags
    writel(0xFFFFFFFF, config->base_addr + NPU_INT_CLEAR);

    return 0;
}

/* Measure actual NPU utilization */
float measure_npu_utilization(uint32_t base_addr, uint32_t duration_ms) {
    uint64_t busy_cycles, total_cycles;

    // Start performance counters
    writel(PERF_COUNTER_ENABLE, base_addr + NPU_PERF_CTRL);

    usleep(duration_ms * 1000);

    // Read counters
    busy_cycles = readl(base_addr + NPU_BUSY_CYCLES_LOW) |
                  ((uint64_t)readl(base_addr + NPU_BUSY_CYCLES_HIGH) << 32);
    total_cycles = readl(base_addr + NPU_TOTAL_CYCLES_LOW) |
                   ((uint64_t)readl(base_addr + NPU_TOTAL_CYCLES_HIGH) << 32);

    float utilization = (float)busy_cycles / total_cycles * 100.0f;
    return utilization;
}
```

---

### 3. Renesas RZ/V2M DRP-AI

**Architecture**: Dynamically Reconfigurable Processor for AI

```
RZ/V2M SoC
├── CPU: 2x Cortex-A53 @ 1.0 GHz
├── DRP-AI: Reconfigurable AI Accelerator
│   ├── 80 GOPS (INT8) - dynamically configurable
│   ├── 8192 MAC units (reconfigurable topology)
│   ├── 1 MB on-chip memory
│   └── Reconfiguration time: 2-5ms
├── GPU: Mali-G31 (38 GFLOPS FP32)
├── Memory: DDR4 @ 8 GB/s
└── ISP: Dual MIPI CSI-2

Power Budget:
- Full SoC: 2-4W
- DRP-AI only: 0.5-1.2W @ 80 GOPS
- Efficiency: ~0.8 GOPS/mW
```

**Dynamic Reconfiguration** (unique feature):
```python
import drpai_reconfigure

# Scenario: Multi-model pipeline with model switching
class MultiModelPipeline:
    def __init__(self):
        self.drp = drpai_reconfigure.DRPAIDevice('/dev/drpai0')

        # Pre-load model configurations (compiled offline)
        self.models = {
            'detection': 'yolov5s_drpai_config.bin',
            'segmentation': 'unet_drpai_config.bin',
            'classification': 'resnet50_drpai_config.bin'
        }

        self.current_model = None

    def switch_model(self, model_name):
        """
        Dynamically reconfigure DRP-AI for different model
        Reconfiguration time: 2-5ms (acceptable for automotive)
        """
        if model_name == self.current_model:
            return  # Already loaded

        config_path = self.models[model_name]

        # Reconfigure DRP-AI fabric
        start = time.time()
        self.drp.reconfigure(config_path)
        reconfig_time = (time.time() - start) * 1000

        print(f"DRP-AI reconfigured to {model_name} in {reconfig_time:.2f}ms")
        self.current_model = model_name

    def process_automotive_frames(self):
        """
        Example: Adaptive processing based on driving scenario
        - Highway: Object detection (fast moving vehicles)
        - Urban: Semantic segmentation (pedestrians, cyclists)
        - Parking: Classification (parking space occupancy)
        """
        scenario = detect_driving_scenario()

        if scenario == 'highway':
            self.switch_model('detection')
            result = self.drp.infer(camera_frame)
            return process_detections(result)

        elif scenario == 'urban':
            self.switch_model('segmentation')
            result = self.drp.infer(camera_frame)
            return process_segmentation(result)

        elif scenario == 'parking':
            self.switch_model('classification')
            result = self.drp.infer(camera_frame)
            return process_classification(result)

# DRP-AI allows running different models without multiple NPU instances
# Saves cost and power compared to dedicated NPUs for each task
```

---

### 4. Ambarella CVflow Architecture

**Architecture**: Multi-core CNN accelerator with vision pipeline integration

```
Ambarella CV5 SoC (2023)
├── CPU: 6x Cortex-A76 @ 2.0 GHz
├── CVflow NPU: 5th Generation
│   ├── 60 TOPS (INT8) - 4x independent cores
│   ├── 16 MB on-chip SRAM
│   ├── Hardware-accelerated NMS, RoI Align
│   └── Direct ISP → NPU pipeline (zero-copy)
├── GPU: Mali-G78 (500 GFLOPS FP32)
├── ISP: Quad 4K60 HDR ISP
├── Memory: LPDDR5 @ 34 GB/s
└── Codec: 8K30 HEVC encoder

Power Budget:
- Full SoC: 15-20W (multi-camera ADAS)
- CVflow only: 5-8W @ 60 TOPS
- Efficiency: 7.5-12 TOPS/W
```

**Multi-Stream Concurrent Inference**:
```python
import ambarella_cvflow as cv

class MultiCameraCVflow:
    """
    Leverage CVflow's 4 independent cores for concurrent inference
    Use case: 4-camera ADAS (front, rear, left, right)
    """
    def __init__(self):
        self.cvflow = cv.CVFlowEngine('/dev/cavalry0')

        # Load model once, deploy to 4 cores
        self.model_id = self.cvflow.load_model('yolov5m_cvflow.vas')

        # Create 4 streams (one per camera/core)
        self.streams = []
        for cam_id in range(4):
            stream = self.cvflow.create_stream(
                model_id=self.model_id,
                core_id=cam_id % 4,  # Round-robin core assignment
                input_source=f'/dev/video{cam_id}',
                resolution=(1920, 1080),
                fps=30,
                zero_copy=True  # Direct ISP → CVflow (no memcpy)
            )
            self.streams.append(stream)

    def start_concurrent_inference(self):
        """All 4 streams run in parallel on separate CVflow cores"""
        for stream_id, stream in enumerate(self.streams):
            stream.set_callback(lambda result: self.handle_result(stream_id, result))
            stream.start()

    def handle_result(self, stream_id, result):
        """
        Handle inference result from specific camera
        Callback runs on NPU hardware interrupt (minimal latency)
        """
        detections = result['detections']
        timestamp = result['timestamp_us']
        latency = result['inference_time_us'] / 1000.0

        print(f"Camera {stream_id}: {len(detections)} objects, "
              f"latency={latency:.1f}ms, ts={timestamp}µs")

        # Send to sensor fusion module
        send_to_fusion(stream_id, detections, timestamp)

    def measure_aggregate_performance(self):
        """Measure total system throughput"""
        stats = self.cvflow.get_statistics()

        print(f"=== CVflow Performance ===")
        print(f"Total throughput: {stats['total_fps']:.1f} FPS")
        print(f"Core 0: {stats['core_0_utilization']:.1f}%")
        print(f"Core 1: {stats['core_1_utilization']:.1f}%")
        print(f"Core 2: {stats['core_2_utilization']:.1f}%")
        print(f"Core 3: {stats['core_3_utilization']:.1f}%")
        print(f"Memory bandwidth: {stats['ddr_bandwidth_gbps']:.2f} GB/s")
        print(f"Power consumption: {stats['cvflow_power_watts']:.2f} W")

# Expected performance:
# - 4 cameras × 30 FPS = 120 FPS aggregate
# - Per-stream latency: 15-20ms
# - Total power: 6-8W (CVflow only)
```

---

## Memory Optimization Strategies

### On-Chip SRAM Utilization

**Challenge**: Limited on-chip memory (384 KB - 32 MB depending on NPU)
**Goal**: Minimize DDR accesses (high latency, high power)

```python
def optimize_memory_layout(model, npu_config):
    """
    Optimize tensor layout to maximize on-chip SRAM usage
    Reduces DDR accesses by 60-80%
    """
    on_chip_sram_size = npu_config['sram_size_bytes']  # e.g., 16 MB for Ambarella

    # 1. Identify tensors that fit in SRAM
    layer_memory_map = {}
    for layer in model.layers:
        activation_size = layer.output_shape.total_size()
        weight_size = layer.weight.total_size()
        total_size = activation_size + weight_size

        layer_memory_map[layer.name] = {
            'activation_size': activation_size,
            'weight_size': weight_size,
            'total_size': total_size,
            'fits_in_sram': total_size <= on_chip_sram_size
        }

    # 2. Pin frequently accessed layers to SRAM
    pinned_layers = []
    remaining_sram = on_chip_sram_size

    for layer_name, mem_info in sorted(layer_memory_map.items(),
                                       key=lambda x: x[1]['total_size']):
        if mem_info['total_size'] <= remaining_sram:
            pinned_layers.append(layer_name)
            remaining_sram -= mem_info['total_size']

    print(f"Pinned {len(pinned_layers)} layers to on-chip SRAM")
    print(f"SRAM utilization: {(on_chip_sram_size - remaining_sram) / on_chip_sram_size * 100:.1f}%")

    # 3. Generate memory allocation hints for compiler
    memory_hints = {
        'pinned_to_sram': pinned_layers,
        'allow_ddr_spill': [l for l in model.layers if l.name not in pinned_layers]
    }

    return memory_hints

# Example: YOLOv5s on Qualcomm NPU (32 MB SRAM)
# - Conv layers 1-15: Pin to SRAM (12 MB)
# - Conv layers 16-25: Partial SRAM (8 MB)
# - Final layers: DDR (slower but acceptable)
# Result: 3x speedup, 40% power reduction
```

### Weight Compression

```python
def compress_weights_for_npu(model, compression_ratio=0.5):
    """
    Compress model weights using structured pruning + Huffman encoding
    Reduces memory footprint and DDR bandwidth
    """
    import torch_pruning as tp
    import huffman

    # 1. Structured pruning (remove entire channels)
    pruned_model = tp.prune_model(
        model,
        pruning_ratio=compression_ratio,
        method='magnitude',
        structured=True  # Channel-wise pruning (NPU-friendly)
    )

    # 2. Group weights by magnitude for better compression
    for name, param in pruned_model.named_parameters():
        if 'weight' in name:
            # Quantize to 4-bit (already INT8 from quantization)
            weights_int8 = param.data.cpu().numpy().astype(np.int8)

            # Huffman encoding (lossless compression)
            huffman_tree = huffman.build_tree(weights_int8.flatten())
            encoded_weights = huffman.encode(weights_int8.flatten(), huffman_tree)

            # Store compressed weights + Huffman table
            compressed_size = len(encoded_weights) / 8  # bits to bytes
            original_size = weights_int8.nbytes

            print(f"{name}: {original_size} → {compressed_size:.0f} bytes "
                  f"({compressed_size/original_size*100:.1f}% of original)")

    # 3. NPU runtime decompresses on-the-fly during inference
    # - Huffman decoder in hardware (some NPUs)
    # - Or software decompression to SRAM (adds ~2ms latency)

# Example: YOLOv5m (21 MB) → 8 MB compressed
# - 62% size reduction
# - Fits in 16 MB SRAM (Ambarella CVflow)
# - No DDR access for weights during inference
```

---

## Power Management

### Dynamic Voltage and Frequency Scaling (DVFS)

```python
class NPUPowerManager:
    """
    Automotive-grade power management for NPU
    Balances performance vs. power based on vehicle state
    """
    def __init__(self, npu_device):
        self.npu = npu_device
        self.power_modes = {
            'PARKING': {'freq_mhz': 400, 'voltage_mv': 750, 'max_power_w': 1.5},
            'DRIVING': {'freq_mhz': 800, 'voltage_mv': 900, 'max_power_w': 5.0},
            'ADAS_ACTIVE': {'freq_mhz': 1200, 'voltage_mv': 1050, 'max_power_w': 10.0}
        }
        self.current_mode = 'PARKING'

    def set_power_mode(self, mode):
        """
        Adjust NPU frequency and voltage based on driving mode
        PARKING: Low power DMS only (drowsiness detection)
        DRIVING: Medium power (lane keeping, basic ADAS)
        ADAS_ACTIVE: Full power (autonomous driving features)
        """
        if mode not in self.power_modes:
            raise ValueError(f"Invalid power mode: {mode}")

        config = self.power_modes[mode]

        # Write to NPU power management registers
        self.npu.set_frequency(config['freq_mhz'])
        self.npu.set_voltage(config['voltage_mv'])
        self.npu.set_power_limit(config['max_power_w'])

        print(f"NPU power mode: {mode}")
        print(f"  Frequency: {config['freq_mhz']} MHz")
        print(f"  Voltage: {config['voltage_mv']} mV")
        print(f"  Max power: {config['max_power_w']} W")

        self.current_mode = mode

    def auto_adjust_based_on_vehicle_state(self):
        """
        Automatically adjust NPU power based on CAN bus signals
        """
        vehicle_speed = read_can_signal('VehicleSpeed')  # km/h
        adas_engaged = read_can_signal('ADAS_Active')  # bool
        ignition_state = read_can_signal('IgnitionState')  # OFF/ACC/ON

        if ignition_state == 'OFF':
            self.set_power_mode('PARKING')

        elif vehicle_speed < 5 and not adas_engaged:
            self.set_power_mode('PARKING')

        elif vehicle_speed >= 5 and not adas_engaged:
            self.set_power_mode('DRIVING')

        elif adas_engaged:
            self.set_power_mode('ADAS_ACTIVE')

    def measure_power_consumption(self):
        """
        Read actual power consumption from NPU power monitor
        """
        voltage_v = self.npu.read_voltage() / 1000.0  # mV → V
        current_ma = self.npu.read_current()  # mA
        power_w = (voltage_v * current_ma) / 1000.0  # W

        return {
            'voltage_v': voltage_v,
            'current_ma': current_ma,
            'power_w': power_w,
            'mode': self.current_mode
        }

# Usage in vehicle
power_mgr = NPUPowerManager(npu_device)

while True:
    power_mgr.auto_adjust_based_on_vehicle_state()
    power_stats = power_mgr.measure_power_consumption()

    if power_stats['power_w'] > power_mgr.power_modes[power_mgr.current_mode]['max_power_w']:
        logging.warning(f"NPU power exceeded: {power_stats['power_w']:.2f}W")

    time.sleep(1.0)
```

---

## Thermal Management

### Temperature Monitoring and Throttling

```python
class NPUThermalManager:
    """
    Prevent NPU thermal shutdown in automotive environment
    Challenge: -40°C to +125°C ambient (inside cabin during summer)
    """
    def __init__(self, npu_device):
        self.npu = npu_device

        # Temperature thresholds (junction temperature)
        self.TEMP_NORMAL = 85  # °C
        self.TEMP_WARNING = 100  # °C - start throttling
        self.TEMP_CRITICAL = 115  # °C - emergency shutdown

        self.throttle_level = 0  # 0 = no throttling, 100 = full throttle

    def read_npu_temperature(self):
        """Read NPU die temperature from thermal sensor"""
        try:
            with open('/sys/class/thermal/thermal_zone3/temp', 'r') as f:
                temp_millidegree = int(f.read().strip())
                temp_celsius = temp_millidegree / 1000.0
                return temp_celsius
        except:
            return 0.0

    def thermal_throttling_policy(self, temperature):
        """
        Adaptive throttling to prevent thermal shutdown
        Reduces NPU frequency/voltage to lower power dissipation
        """
        if temperature < self.TEMP_NORMAL:
            # No throttling - full performance
            self.throttle_level = 0
            self.npu.set_frequency(1200)  # MHz
            self.npu.set_voltage(1050)  # mV

        elif self.TEMP_NORMAL <= temperature < self.TEMP_WARNING:
            # Mild throttling (10-30%)
            self.throttle_level = int((temperature - self.TEMP_NORMAL) / (self.TEMP_WARNING - self.TEMP_NORMAL) * 30)
            freq_mhz = 1200 - (self.throttle_level * 4)  # Reduce frequency
            voltage_mv = 1050 - (self.throttle_level * 2)  # Reduce voltage
            self.npu.set_frequency(freq_mhz)
            self.npu.set_voltage(voltage_mv)

        elif self.TEMP_WARNING <= temperature < self.TEMP_CRITICAL:
            # Aggressive throttling (30-70%)
            self.throttle_level = 30 + int((temperature - self.TEMP_WARNING) / (self.TEMP_CRITICAL - self.TEMP_WARNING) * 40)
            freq_mhz = 1200 - (self.throttle_level * 8)
            voltage_mv = 1050 - (self.throttle_level * 3)
            self.npu.set_frequency(max(freq_mhz, 400))  # Don't go below 400 MHz
            self.npu.set_voltage(max(voltage_mv, 750))
            logging.warning(f"NPU thermal warning: {temperature:.1f}°C, throttling {self.throttle_level}%")

        else:  # temperature >= TEMP_CRITICAL
            # Emergency: Pause inference, trigger cooling
            self.throttle_level = 100
            self.npu.set_frequency(400)
            self.npu.set_voltage(750)
            self.npu.pause_inference()
            logging.critical(f"NPU thermal critical: {temperature:.1f}°C, inference paused")

            # Trigger cabin cooling request via CAN
            send_can_message('HVACRequest', {'mode': 'MAX_COOL', 'fan_speed': 'HIGH'})

    def monitor_thermal(self):
        """Continuous thermal monitoring loop"""
        while True:
            temp = self.read_npu_temperature()
            self.thermal_throttling_policy(temp)

            # Log thermal metrics
            print(f"NPU temp: {temp:.1f}°C, throttle: {self.throttle_level}%")

            time.sleep(0.5)  # 2 Hz monitoring

# Real-world scenario:
# Summer day, cabin temperature 60°C
# NPU reaches 110°C under full load
# Thermal manager reduces frequency to 600 MHz
# Temperature stabilizes at 95°C
# Inference latency increases from 20ms → 40ms (acceptable for non-critical ADAS)
```

---

## Benchmarking NPU Performance

### Comprehensive NPU Benchmark Suite

```python
class NPUBenchmarkSuite:
    """
    Automotive NPU benchmark suite
    Tests: latency, throughput, power, thermal, accuracy
    """
    def __init__(self, npu_device, model_zoo_path):
        self.npu = npu_device
        self.model_zoo = self.load_model_zoo(model_zoo_path)

    def load_model_zoo(self, path):
        """Load standardized automotive model zoo"""
        return {
            'yolov5s': f'{path}/yolov5s_int8.dlc',
            'efficientdet_d0': f'{path}/efficientdet_d0_int8.tflite',
            'resnet50': f'{path}/resnet50_int8.onnx',
            'mobilenet_v2': f'{path}/mobilenet_v2_int8.onnx',
            'lanenet': f'{path}/lanenet_int8.dlc',
            'dms_drowsiness': f'{path}/dms_drowsiness_int8.tflite'
        }

    def benchmark_latency(self, model_name, num_iterations=1000):
        """Measure inference latency distribution"""
        model = self.npu.load_model(self.model_zoo[model_name])
        latencies = []

        # Warmup
        for _ in range(100):
            _ = model.infer(dummy_input)

        # Benchmark
        for _ in range(num_iterations):
            start = time.perf_counter()
            _ = model.infer(dummy_input)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # ms

        return {
            'model': model_name,
            'mean_ms': np.mean(latencies),
            'median_ms': np.median(latencies),
            'p50_ms': np.percentile(latencies, 50),
            'p90_ms': np.percentile(latencies, 90),
            'p99_ms': np.percentile(latencies, 99),
            'min_ms': np.min(latencies),
            'max_ms': np.max(latencies),
            'std_ms': np.std(latencies)
        }

    def benchmark_throughput(self, model_name, duration_sec=60):
        """Measure sustained throughput (FPS)"""
        model = self.npu.load_model(self.model_zoo[model_name])
        count = 0
        start_time = time.time()

        while time.time() - start_time < duration_sec:
            _ = model.infer(dummy_input)
            count += 1

        fps = count / duration_sec
        return {'model': model_name, 'fps': fps}

    def benchmark_power_efficiency(self, model_name, num_iterations=1000):
        """Measure TOPS/Watt efficiency"""
        model = self.npu.load_model(self.model_zoo[model_name])
        power_samples = []
        latencies = []

        for _ in range(num_iterations):
            power_start = self.npu.read_power()
            time_start = time.perf_counter()

            _ = model.infer(dummy_input)

            time_end = time.perf_counter()
            power_end = self.npu.read_power()

            latencies.append((time_end - time_start) * 1000)
            power_samples.append((power_start + power_end) / 2)  # Average

        # Calculate TOPS
        model_ops = model.get_total_ops()  # e.g., 16.5 GFLOPs for YOLOv5s
        avg_latency = np.mean(latencies) / 1000  # seconds
        tops = (model_ops / avg_latency) / 1e12  # TOPS

        avg_power = np.mean(power_samples)  # Watts
        tops_per_watt = tops / avg_power

        return {
            'model': model_name,
            'tops': tops,
            'power_w': avg_power,
            'tops_per_watt': tops_per_watt
        }

    def run_full_suite(self):
        """Run complete benchmark suite"""
        results = {}

        for model_name in self.model_zoo.keys():
            print(f"\n=== Benchmarking {model_name} ===")

            latency_result = self.benchmark_latency(model_name)
            throughput_result = self.benchmark_throughput(model_name)
            power_result = self.benchmark_power_efficiency(model_name)

            results[model_name] = {
                'latency': latency_result,
                'throughput': throughput_result,
                'power': power_result
            }

            print(f"Latency: {latency_result['mean_ms']:.2f}ms (P99: {latency_result['p99_ms']:.2f}ms)")
            print(f"Throughput: {throughput_result['fps']:.2f} FPS")
            print(f"Power: {power_result['power_w']:.2f}W, {power_result['tops_per_watt']:.2f} TOPS/W")

        # Generate report
        self.generate_report(results)
        return results

    def generate_report(self, results):
        """Generate markdown benchmark report"""
        with open('npu_benchmark_report.md', 'w') as f:
            f.write("# NPU Benchmark Report\n\n")
            f.write(f"**NPU**: {self.npu.get_device_name()}\n")
            f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Latency Results\n\n")
            f.write("| Model | Mean (ms) | P50 (ms) | P90 (ms) | P99 (ms) |\n")
            f.write("|-------|-----------|----------|----------|----------|\n")
            for model, data in results.items():
                lat = data['latency']
                f.write(f"| {model} | {lat['mean_ms']:.2f} | {lat['p50_ms']:.2f} | "
                       f"{lat['p90_ms']:.2f} | {lat['p99_ms']:.2f} |\n")

            f.write("\n## Throughput Results\n\n")
            f.write("| Model | FPS |\n")
            f.write("|-------|-----|\n")
            for model, data in results.items():
                f.write(f"| {model} | {data['throughput']['fps']:.2f} |\n")

            f.write("\n## Power Efficiency\n\n")
            f.write("| Model | TOPS | Power (W) | TOPS/W |\n")
            f.write("|-------|------|-----------|--------|\n")
            for model, data in results.items():
                pwr = data['power']
                f.write(f"| {model} | {pwr['tops']:.2f} | {pwr['power_w']:.2f} | "
                       f"{pwr['tops_per_watt']:.2f} |\n")

# Example usage
benchmark = NPUBenchmarkSuite(qualcomm_npu, '/models/automotive_zoo')
results = benchmark.run_full_suite()
```

---

## NPU Comparison Table

| Platform | TOPS (INT8) | On-Chip SRAM | Memory BW | Power | TOPS/W | Use Case |
|----------|-------------|--------------|-----------|-------|--------|----------|
| **Qualcomm Snapdragon Ride** | 300 | 32 MB | 51 GB/s | 8-12W | 25-37 | L3+ Autonomous |
| **NXP i.MX 8M Plus** | 2.3 | 384 KB | 4 GB/s | 0.8-1.5W | 1.5-2.8 | ADAS Entry |
| **Renesas RZ/V2M** | 0.08 | 1 MB | 8 GB/s | 0.5-1.2W | ~0.8 | DMS/Parking |
| **Ambarella CV5** | 60 | 16 MB | 34 GB/s | 5-8W | 7.5-12 | Multi-Camera ADAS |
| **NVIDIA Orin** | 275 | 8 MB | 204 GB/s | 15-45W | 6-18 | Autonomous Driving |
| **Tesla FSD (HW3)** | 144 | N/A | 68 GB/s | 72W | 2 | Full Self-Driving |

**Selection Guide**:
- **Entry ADAS** (Lane Keep, AEB): NXP i.MX 8M Plus
- **Advanced ADAS** (Multi-camera, parking): Ambarella CV5
- **L3 Autonomous**: Qualcomm Snapdragon Ride or NVIDIA Orin
- **DMS/OMS**: Renesas RZ/V2M or NXP i.MX 8M Plus

---

## Related Skills
- [Edge AI Deployment](./edge-ai-deployment.md) - Deploy models to NPUs
- [Camera Vision AI](./camera-vision-ai.md) - Vision pipelines
- [Driver Monitoring Systems](./driver-monitoring-systems.md) - DMS with NPU

---

**Tags**: `npu`, `ai-accelerator`, `tops`, `automotive-hardware`, `performance-optimization`, `thermal-management`, `power-management`
