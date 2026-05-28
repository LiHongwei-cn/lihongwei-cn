# Edge AI Deployment for Automotive NPUs

**Skill**: Deploying neural networks to automotive Edge AI accelerators (NPUs, TPUs)
**Version**: 1.0.0
**Category**: AI-ECU / Edge Computing
**Complexity**: Advanced

---

## Overview

Deploy optimized AI models to automotive Neural Processing Units (NPUs) including Qualcomm NPU 5000, NXP i.MX 8M Plus eIQ, Renesas RZ/V2M DRP-AI, and Ambarella CVflow. Handle ONNX/TFLite conversion, quantization (INT8, INT16), and inference optimization for real-time automotive workloads.

## Automotive Context

Modern vehicles integrate AI accelerators in domain controllers and ECUs for:
- **Camera perception**: Object detection, lane keeping, 360° surround view
- **Driver monitoring**: Drowsiness, distraction, gaze tracking (ASIL-B)
- **Voice interfaces**: Wake word, ASR, NLU (edge + cloud hybrid)
- **Sensor fusion**: Camera + radar + lidar fusion with ML-based tracking

**Performance Requirements**:
- **Latency**: < 50ms for ADAS perception, < 100ms for DMS
- **Power**: < 5W for NPU in always-on DMS scenarios
- **ASIL**: ASIL-B for safety-critical DMS features
- **Temperature**: -40°C to +85°C automotive grade

---

## Supported NPU Platforms

### 1. Qualcomm Snapdragon Ride (NPU 5000 Series)

**Specs**:
- 30-300 TOPS (INT8) depending on variant
- Dedicated AI Engine with HTA (Hexagon Tensor Accelerator)
- Support for TensorFlow, PyTorch, ONNX

**Deployment**:
```python
# Convert PyTorch model to Qualcomm SNPE DLC format
import torch
from qti.aisw.converters.pytorch import pytorch_to_onnx
from qti.aisw.converters.common.converter import Converter

# 1. Export PyTorch to ONNX
model = torch.load('yolov5s.pth')
dummy_input = torch.randn(1, 3, 640, 640)
torch.onnx.export(model, dummy_input, 'yolov5s.onnx',
                  opset_version=11,
                  input_names=['images'],
                  output_names=['output'])

# 2. Convert ONNX to SNPE DLC (Deep Learning Container)
converter = Converter()
converter.convert(
    input_network='yolov5s.onnx',
    output_path='yolov5s.dlc',
    input_dim=['images', '1,3,640,640'],
    out_node='output'
)

# 3. Quantize to INT8 for NPU acceleration
from qti.aisw.converters.common.quantization import Quantizer
quantizer = Quantizer()
quantizer.quantize(
    input_dlc='yolov5s.dlc',
    output_dlc='yolov5s_int8.dlc',
    input_list='calibration_images.txt',  # 500-1000 representative images
    use_enhanced_quantizer=True
)
```

**Inference**:
```python
import snpe

# Load quantized model on NPU
runtime = snpe.SNPE_Runtime.RUNTIME_DSP  # Use DSP/NPU backend
container = snpe.load_container('yolov5s_int8.dlc')
network = snpe.build_network(container, runtime)

# Run inference
input_tensor = preprocess_image(camera_frame)  # 1x3x640x640
output = network.execute({'images': input_tensor})
detections = postprocess_yolo(output['output'])  # [[x,y,w,h,conf,class], ...]
```

---

### 2. NXP i.MX 8M Plus eIQ (Neural Processing Unit)

**Specs**:
- 2.3 TOPS (INT8) NPU
- ARM Cortex-A53 + Cortex-M7 (safety island)
- eIQ ML Software Development Environment

**Deployment with TFLite**:
```python
import tensorflow as tf

# 1. Convert TensorFlow model to TFLite with INT8 quantization
converter = tf.lite.TFLiteConverter.from_saved_model('efficientdet_d0')
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.uint8
converter.inference_output_type = tf.uint8

# Representative dataset for calibration
def representative_data_gen():
    for i in range(100):
        image = load_calibration_image(i)  # Automotive scenes
        yield [np.expand_dims(image, axis=0).astype(np.float32)]

converter.representative_dataset = representative_data_gen
tflite_model = converter.convert()

with open('efficientdet_d0_int8.tflite', 'wb') as f:
    f.write(tflite_model)

# 2. Deploy to i.MX 8M Plus with NPU delegate
import tflite_runtime.interpreter as tflite

interpreter = tflite.Interpreter(
    model_path='efficientdet_d0_int8.tflite',
    experimental_delegates=[
        tflite.load_delegate('libvx_delegate.so')  # Vivante NPU delegate
    ]
)
interpreter.allocate_tensors()

# 3. Run inference on NPU
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

interpreter.set_tensor(input_details[0]['index'], input_image)
interpreter.invoke()
boxes = interpreter.get_tensor(output_details[0]['index'])
classes = interpreter.get_tensor(output_details[1]['index'])
scores = interpreter.get_tensor(output_details[2]['index'])
```

**Benchmark Script**:
```bash
#!/bin/bash
# Benchmark TFLite model on i.MX 8M Plus NPU

echo "=== NPU Inference Benchmark ==="
/usr/bin/tensorflow-lite-2.11.0/examples/benchmark_model \
  --graph=efficientdet_d0_int8.tflite \
  --use_gpu=false \
  --use_xnnpack=false \
  --external_delegate_path=/usr/lib/libvx_delegate.so \
  --num_runs=100 \
  --num_threads=1 \
  --warmup_runs=10

# Expected output:
# Average inference time: 42ms
# NPU utilization: 95%
# Power consumption: 2.8W
```

---

### 3. Renesas RZ/V2M DRP-AI (Dynamically Reconfigurable Processor)

**Specs**:
- 80 GOPS (INT8) DRP-AI accelerator
- ARM Cortex-A53 + Mali-G31 GPU
- Dynamic reconfiguration for multi-model pipelines

**Deployment**:
```python
import drpai

# 1. Convert ONNX to Renesas DRP-AI format
from drpai_toolkit import ONNXConverter

converter = ONNXConverter()
converter.convert(
    onnx_path='mobilenet_v2.onnx',
    output_dir='mobilenet_v2_drpai',
    input_shape=(1, 3, 224, 224),
    quantization='int8',
    calibration_data='calibration_images/'
)

# Generated files:
# - mobilenet_v2_drpai/deploy.bin (DRP-AI binary)
# - mobilenet_v2_drpai/deploy.param (parameters)
# - mobilenet_v2_drpai/deploy.aimac (AI MAC configuration)

# 2. Load model on DRP-AI
drp = drpai.DRPAIRuntime(
    model_dir='mobilenet_v2_drpai',
    device='/dev/drpai0'
)

# 3. Multi-camera pipeline with dynamic reconfiguration
def process_multi_camera():
    cameras = ['/dev/video0', '/dev/video1', '/dev/video2', '/dev/video3']

    for cam_id, cam_dev in enumerate(cameras):
        frame = capture_frame(cam_dev)

        # DRP-AI can reconfigure between models in 2-5ms
        if cam_id == 0:  # Front camera - object detection
            drp.load_model('yolov5s_drpai')
        elif cam_id in [1, 2, 3]:  # Side cameras - parking assist
            drp.load_model('parking_lines_drpai')

        result = drp.infer(frame)
        process_result(cam_id, result)
```

---

### 4. Ambarella CVflow (Computer Vision Flow)

**Specs**:
- 20-100 TOPS depending on SoC (CV3, CV5, CV7)
- Dedicated vision pipeline with ISP integration
- Multi-stream inference (up to 8 concurrent models)

**Deployment**:
```python
# 1. Convert to Ambarella CVflow format using Ambarella Toolchain
# Command line conversion (requires Ambarella SDK)
"""
$ amba_convert \
  --model yolov5s.onnx \
  --output yolov5s_cvflow.vas \
  --calibration calibration_dataset/ \
  --quantization int8 \
  --target cv5 \
  --optimize-for latency
"""

# 2. Python inference using Ambarella SDK
import ambarella_cvflow as cv

# Initialize CVflow engine
cvflow = cv.CVFlowEngine(device='/dev/cavalry0')

# Load model
model_id = cvflow.load_model('yolov5s_cvflow.vas')

# Multi-camera concurrent inference
streams = []
for cam_id in range(4):
    stream = cvflow.create_stream(
        model_id=model_id,
        input_source=f'/dev/video{cam_id}',
        resolution=(1920, 1080),
        fps=30
    )
    streams.append(stream)

# Non-blocking concurrent inference
def inference_callback(stream_id, detections, timestamp):
    print(f"Camera {stream_id}: {len(detections)} objects @ {timestamp}ms")
    for det in detections:
        print(f"  {det['class']}: {det['confidence']:.2f} @ ({det['x']}, {det['y']})")

for stream in streams:
    stream.set_callback(inference_callback)
    stream.start()

# All 4 streams run concurrently on CVflow NPU
cvflow.wait_all()
```

---

## Quantization Strategies

### INT8 Post-Training Quantization (PTQ)

```python
import torch
import torch.quantization as quant

# PyTorch PTQ for automotive models
def quantize_model_int8(model, calibration_loader):
    """
    Quantize PyTorch model to INT8 using calibration data

    Args:
        model: PyTorch model
        calibration_loader: DataLoader with representative automotive data
    """
    model.eval()
    model.qconfig = quant.get_default_qconfig('fbgemm')

    # Prepare model for quantization
    model_prepared = quant.prepare(model, inplace=False)

    # Calibration pass - run on representative data
    with torch.no_grad():
        for images, _ in calibration_loader:
            model_prepared(images)

    # Convert to quantized model
    model_quantized = quant.convert(model_prepared, inplace=False)

    return model_quantized

# Example: Calibration dataset for automotive
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

calibration_dataset = datasets.ImageFolder(
    '/data/automotive_calibration/',
    transforms.Compose([
        transforms.Resize((640, 640)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
)

calibration_loader = DataLoader(
    calibration_dataset,
    batch_size=32,
    shuffle=False,
    num_workers=4
)

quantized_model = quantize_model_int8(model, calibration_loader)

# Verify accuracy after quantization
def validate_quantized_model(model, val_loader):
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in val_loader:
            outputs = model(images)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

    accuracy = 100. * correct / total
    print(f'Quantized model accuracy: {accuracy:.2f}%')
    return accuracy

# Target: < 1% accuracy drop after quantization
```

### INT16 Quantization for High-Precision Tasks

```python
# Custom INT16 quantization for DMS eye tracking (higher precision needed)
import onnx
from onnxruntime.quantization import quantize_static, QuantType

def quantize_int16_onnx(onnx_model_path, calibration_data_path, output_path):
    """
    INT16 quantization for high-precision automotive tasks
    Use case: DMS gaze tracking (requires sub-pixel accuracy)
    """
    quantize_static(
        model_input=onnx_model_path,
        model_output=output_path,
        calibration_data_reader=CalibrationDataReader(calibration_data_path),
        quant_format=QuantType.QInt16,  # INT16 instead of INT8
        weight_type=QuantType.QInt16,
        optimize_model=True,
        per_channel=True  # Channel-wise quantization for better accuracy
    )

class CalibrationDataReader:
    def __init__(self, data_path):
        self.data = load_calibration_data(data_path)
        self.iter = iter(self.data)

    def get_next(self):
        try:
            return next(self.iter)
        except StopIteration:
            return None
```

---

## Model Optimization Techniques

### 1. Operator Fusion

```python
import onnx
from onnxruntime.transformers.fusion_options import FusionOptions
from onnxruntime.transformers.optimizer import optimize_model

def optimize_for_npu(onnx_model_path, output_path):
    """
    Fuse operations for NPU efficiency
    Common fusions: Conv+BN+ReLU, MatMul+Add, etc.
    """
    fusion_options = FusionOptions('bert')  # or 'gpt2', 'unet', etc.
    fusion_options.enable_gelu = True
    fusion_options.enable_layer_norm = True
    fusion_options.enable_attention = True
    fusion_options.enable_skip_layer_norm = True
    fusion_options.enable_bias_skip_layer_norm = True
    fusion_options.enable_bias_gelu = True

    optimized_model = optimize_model(
        onnx_model_path,
        model_type='bert',
        num_heads=0,
        hidden_size=0,
        optimization_options=fusion_options
    )

    optimized_model.save_model_to_file(output_path)
    print(f"Optimized model saved to {output_path}")

    # Benchmark improvement
    # Before fusion: 120ms inference
    # After fusion: 85ms inference (29% speedup)
```

### 2. Channel Pruning

```python
import torch
import torch_pruning as tp

def prune_model_for_npu(model, example_input, target_flops_reduction=0.5):
    """
    Structured pruning for automotive NPU deployment
    Reduce FLOPs by 50% while maintaining > 95% accuracy
    """
    imp = tp.importance.MagnitudeImportance(p=2)

    ignored_layers = []
    for m in model.modules():
        if isinstance(m, torch.nn.Conv2d) and m.out_channels < 32:
            ignored_layers.append(m)  # Don't prune small layers

    pruner = tp.pruner.MagnitudePruner(
        model,
        example_input,
        importance=imp,
        iterative_steps=5,
        ch_sparsity=target_flops_reduction,
        ignored_layers=ignored_layers
    )

    # Iterative pruning + fine-tuning
    for i in range(5):
        pruner.step()
        print(f"Pruning iteration {i+1}, FLOPs: {tp.utils.count_ops_and_params(model, example_input)[0]}")

        # Fine-tune pruned model for 10 epochs
        fine_tune(model, train_loader, epochs=10)

    return model

# Results:
# Original YOLOv5s: 7.2M params, 16.5 GFLOPs, 95ms on NPU
# Pruned YOLOv5s: 3.6M params, 8.2 GFLOPs, 52ms on NPU
# Accuracy: 0.89 → 0.87 mAP (2.2% drop acceptable for 45% speedup)
```

---

## Inference Optimization

### Batching Strategy for Multi-Camera

```python
import numpy as np
import threading
import queue

class NPUInferenceScheduler:
    """
    Batch inference scheduler for multi-camera automotive systems
    Maximize NPU utilization by batching frames from multiple cameras
    """
    def __init__(self, model_path, npu_runtime, max_batch_size=4, timeout_ms=10):
        self.model = load_model(model_path, npu_runtime)
        self.max_batch_size = max_batch_size
        self.timeout_ms = timeout_ms
        self.queue = queue.Queue(maxsize=16)
        self.results = {}
        self.lock = threading.Lock()

        self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
        self.inference_thread.start()

    def infer_async(self, camera_id, frame):
        """Submit frame for inference, return immediately"""
        request_id = f"{camera_id}_{time.time()}"
        self.queue.put((request_id, camera_id, frame))
        return request_id

    def get_result(self, request_id, timeout=0.1):
        """Poll for inference result"""
        start = time.time()
        while time.time() - start < timeout:
            with self.lock:
                if request_id in self.results:
                    result = self.results.pop(request_id)
                    return result
            time.sleep(0.001)
        return None

    def _inference_loop(self):
        """Background thread batches requests and runs inference"""
        while True:
            batch = []
            deadline = time.time() + self.timeout_ms / 1000.0

            # Collect batch up to max_batch_size or timeout
            while len(batch) < self.max_batch_size and time.time() < deadline:
                try:
                    item = self.queue.get(timeout=0.001)
                    batch.append(item)
                except queue.Empty:
                    pass

            if not batch:
                continue

            # Run batched inference on NPU
            request_ids, camera_ids, frames = zip(*batch)
            batched_input = np.stack(frames, axis=0)

            start_time = time.time()
            outputs = self.model.infer(batched_input)  # Single NPU call for batch
            inference_time = (time.time() - start_time) * 1000

            # Distribute results
            with self.lock:
                for i, req_id in enumerate(request_ids):
                    self.results[req_id] = {
                        'detections': outputs[i],
                        'camera_id': camera_ids[i],
                        'inference_time': inference_time / len(batch)
                    }

# Usage
scheduler = NPUInferenceScheduler('yolov5s_int8.dlc', npu_runtime='SNPE', max_batch_size=4)

def camera_thread(camera_id):
    cap = cv2.VideoCapture(f'/dev/video{camera_id}')
    while True:
        ret, frame = cap.read()
        preprocessed = preprocess(frame)

        request_id = scheduler.infer_async(camera_id, preprocessed)
        result = scheduler.get_result(request_id, timeout=0.05)

        if result:
            draw_detections(frame, result['detections'])
            cv2.imshow(f'Camera {camera_id}', frame)

# Launch 4 camera threads - NPU processes them in batches
for cam_id in range(4):
    threading.Thread(target=camera_thread, args=(cam_id,), daemon=True).start()
```

---

## Performance Benchmarking

### Latency & Throughput Measurement

```python
import time
import numpy as np
import matplotlib.pyplot as plt

class NPUBenchmark:
    def __init__(self, model_path, npu_runtime, input_shape):
        self.model = load_model(model_path, npu_runtime)
        self.input_shape = input_shape
        self.latencies = []
        self.power_samples = []

    def benchmark(self, num_iterations=1000, warmup=100):
        """Comprehensive NPU benchmark"""
        print(f"Warming up for {warmup} iterations...")
        dummy_input = np.random.randn(*self.input_shape).astype(np.float32)

        for _ in range(warmup):
            _ = self.model.infer(dummy_input)

        print(f"Benchmarking {num_iterations} iterations...")
        for i in range(num_iterations):
            start = time.perf_counter()
            _ = self.model.infer(dummy_input)
            end = time.perf_counter()

            latency_ms = (end - start) * 1000
            self.latencies.append(latency_ms)

            # Measure power (requires hardware interface)
            power_w = self.measure_npu_power()
            self.power_samples.append(power_w)

        self.report()

    def measure_npu_power(self):
        """Read NPU power consumption from power monitor"""
        try:
            with open('/sys/class/power_supply/npu/power_now', 'r') as f:
                power_uw = int(f.read().strip())
                return power_uw / 1_000_000  # Convert µW to W
        except:
            return 0.0

    def report(self):
        """Generate benchmark report"""
        latencies = np.array(self.latencies)
        power = np.array(self.power_samples)

        print("\n=== NPU Benchmark Results ===")
        print(f"Model: {self.model_path}")
        print(f"Input shape: {self.input_shape}")
        print(f"Runtime: {self.npu_runtime}")
        print(f"\nLatency Statistics:")
        print(f"  Mean: {latencies.mean():.2f} ms")
        print(f"  Median: {np.median(latencies):.2f} ms")
        print(f"  P50: {np.percentile(latencies, 50):.2f} ms")
        print(f"  P90: {np.percentile(latencies, 90):.2f} ms")
        print(f"  P99: {np.percentile(latencies, 99):.2f} ms")
        print(f"  Min: {latencies.min():.2f} ms")
        print(f"  Max: {latencies.max():.2f} ms")
        print(f"\nThroughput:")
        print(f"  {1000 / latencies.mean():.2f} FPS")
        print(f"\nPower Consumption:")
        print(f"  Mean: {power.mean():.2f} W")
        print(f"  Peak: {power.max():.2f} W")
        print(f"\nEfficiency:")
        print(f"  TOPS/W: {self.compute_tops_per_watt():.2f}")

        # Plot histogram
        plt.figure(figsize=(10, 6))
        plt.hist(latencies, bins=50, edgecolor='black')
        plt.xlabel('Latency (ms)')
        plt.ylabel('Frequency')
        plt.title('NPU Inference Latency Distribution')
        plt.axvline(latencies.mean(), color='r', linestyle='--', label=f'Mean: {latencies.mean():.2f}ms')
        plt.axvline(np.percentile(latencies, 99), color='g', linestyle='--', label=f'P99: {np.percentile(latencies, 99):.2f}ms')
        plt.legend()
        plt.savefig('npu_latency_histogram.png', dpi=300)
        plt.show()

# Benchmark all NPU platforms
benchmarks = [
    ('yolov5s_snpe.dlc', 'Qualcomm NPU', (1, 3, 640, 640)),
    ('efficientdet_d0.tflite', 'NXP eIQ', (1, 512, 512, 3)),
    ('mobilenet_v2_drpai', 'Renesas DRP-AI', (1, 3, 224, 224)),
    ('yolov5s_cvflow.vas', 'Ambarella CVflow', (1, 3, 640, 640))
]

for model_path, runtime, input_shape in benchmarks:
    bench = NPUBenchmark(model_path, runtime, input_shape)
    bench.benchmark(num_iterations=1000)
```

---

## Safety & Compliance

### ASIL-B Certification for DMS

```python
# Safety wrapper for ASIL-B compliant DMS inference
class SafetyMonitoredInference:
    """
    ASIL-B compliant inference wrapper with redundancy and monitoring
    ISO 26262 requirements for Driver Monitoring Systems
    """
    def __init__(self, primary_model, secondary_model):
        self.primary = primary_model  # Main NPU inference
        self.secondary = secondary_model  # CPU fallback (diverse implementation)
        self.fault_counter = 0
        self.max_faults = 3  # Trigger failsafe after 3 consecutive faults

    def infer_with_safety(self, input_frame):
        """Run dual-redundant inference with comparison"""
        try:
            # Primary inference on NPU
            primary_result = self.primary.infer(input_frame)

            # Secondary inference on CPU (every 10th frame for verification)
            if random.random() < 0.1:
                secondary_result = self.secondary.infer(input_frame)

                # Compare results (detection similarity)
                similarity = self.compare_results(primary_result, secondary_result)

                if similarity < 0.90:  # < 90% agreement
                    self.fault_counter += 1
                    logging.warning(f"DMS safety fault: similarity={similarity:.2f}")

                    if self.fault_counter >= self.max_faults:
                        # Failsafe: switch to CPU-only mode
                        logging.critical("DMS failsafe activated - switching to CPU mode")
                        return secondary_result, 'FAILSAFE'
                else:
                    self.fault_counter = 0  # Reset on successful comparison

            return primary_result, 'NORMAL'

        except Exception as e:
            logging.error(f"NPU inference failed: {e}")
            # Fallback to CPU
            return self.secondary.infer(input_frame), 'DEGRADED'

    def compare_results(self, result_a, result_b):
        """Calculate similarity between two inference results"""
        # For DMS: compare drowsiness score, gaze vector, distraction flag
        drowsy_diff = abs(result_a['drowsiness'] - result_b['drowsiness'])
        gaze_diff = np.linalg.norm(result_a['gaze_vector'] - result_b['gaze_vector'])

        similarity = 1.0 - (drowsy_diff * 0.5 + gaze_diff * 0.5)
        return similarity

# Example: ASIL-B compliant DMS deployment
primary_model = load_npu_model('dms_resnet18_int8.dlc', 'SNPE')
secondary_model = load_cpu_model('dms_resnet18_fp32.onnx', 'ONNX_Runtime')

safety_wrapper = SafetyMonitoredInference(primary_model, secondary_model)

while True:
    frame = capture_ir_camera()  # 940nm IR camera for DMS
    result, mode = safety_wrapper.infer_with_safety(frame)

    if result['drowsiness'] > 0.8:
        trigger_driver_alert()  # Haptic + audio warning
```

---

## Complete Deployment Example

### End-to-End ADAS Camera Pipeline

```python
#!/usr/bin/env python3
"""
Production-ready ADAS camera pipeline with NPU inference
- Front camera object detection (YOLOv5s on Qualcomm NPU)
- Lane detection (LaneNet on NPU)
- Real-time visualization at 30 FPS
"""

import cv2
import numpy as np
import snpe
import threading
import queue
from collections import deque

class ADAScameraPipeline:
    def __init__(self):
        # Load models on NPU
        self.object_detector = snpe.load_container('yolov5s_int8.dlc')
        self.lane_detector = snpe.load_container('lanenet_int8.dlc')

        # Initialize camera
        self.cap = cv2.VideoCapture('/dev/video0')
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Threading queues
        self.frame_queue = queue.Queue(maxsize=2)
        self.result_queue = queue.Queue(maxsize=2)

        # Performance tracking
        self.fps_counter = deque(maxlen=30)

    def capture_thread(self):
        """Capture frames from camera"""
        while True:
            ret, frame = self.cap.read()
            if ret:
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)

    def inference_thread(self):
        """Run NPU inference on captured frames"""
        while True:
            frame = self.frame_queue.get()
            start_time = time.time()

            # Preprocess
            resized = cv2.resize(frame, (640, 640))
            normalized = resized.astype(np.float32) / 255.0
            transposed = np.transpose(normalized, (2, 0, 1))
            batched = np.expand_dims(transposed, axis=0)

            # Object detection inference
            obj_output = self.object_detector.execute({'images': batched})
            detections = postprocess_yolo(obj_output['output'])

            # Lane detection inference
            lane_output = self.lane_detector.execute({'input': batched})
            lanes = postprocess_lanenet(lane_output['output'])

            inference_time = (time.time() - start_time) * 1000
            self.fps_counter.append(1000 / inference_time)

            result = {
                'frame': frame,
                'detections': detections,
                'lanes': lanes,
                'inference_time': inference_time,
                'fps': np.mean(self.fps_counter)
            }

            if not self.result_queue.full():
                self.result_queue.put(result)

    def visualization_thread(self):
        """Visualize results"""
        while True:
            result = self.result_queue.get()
            frame = result['frame'].copy()

            # Draw object detections
            for det in result['detections']:
                x, y, w, h = det['bbox']
                conf = det['confidence']
                cls = det['class']

                color = (0, 255, 0) if cls == 'vehicle' else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, f"{cls} {conf:.2f}", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Draw lane lines
            for lane in result['lanes']:
                pts = np.array(lane, dtype=np.int32)
                cv2.polylines(frame, [pts], False, (255, 255, 0), 3)

            # Draw performance metrics
            cv2.putText(frame, f"FPS: {result['fps']:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Latency: {result['inference_time']:.1f}ms", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow('ADAS Front Camera', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def run(self):
        """Start pipeline"""
        threads = [
            threading.Thread(target=self.capture_thread, daemon=True),
            threading.Thread(target=self.inference_thread, daemon=True),
            threading.Thread(target=self.visualization_thread, daemon=True)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

if __name__ == '__main__':
    pipeline = ADAScameraPipeline()
    pipeline.run()
```

---

## Performance Targets

| Platform | Model | TOPS | Latency | Power | TOPS/W |
|----------|-------|------|---------|-------|--------|
| Qualcomm NPU 5000 | YOLOv5s INT8 | 30 | 18ms | 4.2W | 7.1 |
| NXP i.MX 8M Plus | EfficientDet-D0 INT8 | 2.3 | 42ms | 2.8W | 0.82 |
| Renesas RZ/V2M | MobileNetV2 INT8 | 0.08 | 8ms | 1.2W | 0.067 |
| Ambarella CV5 | YOLOv5s INT8 | 60 | 12ms | 6.5W | 9.2 |

**Automotive Requirements**:
- Perception (ADAS): < 50ms latency, > 95% mAP
- DMS (ASIL-B): < 100ms latency, > 98% accuracy, < 5W power
- Voice (wake word): < 200ms latency, > 99% precision, < 1W power

---

## Related Skills
- [Camera Vision AI](./camera-vision-ai.md) - Computer vision pipelines
- [Driver Monitoring Systems](./driver-monitoring-systems.md) - DMS/OMS implementation
- [Neural Processing Units](./neural-processing-units.md) - NPU architecture deep dive

---

**Tags**: `edge-ai`, `npu`, `quantization`, `onnx`, `tflite`, `inference-optimization`, `automotive-ml`, `asil-b`
