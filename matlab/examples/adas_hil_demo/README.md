# ADAS HIL Test Demo

Hardware-in-the-loop test demo for Advanced Driver Assistance Systems (ADAS), compatible with MATLAB R2016b.

## Features

- **Vehicle Model** — Single-track longitudinal dynamics with aerodynamic drag and rolling resistance
- **Sensor Model** — Radar (range/rate/azimuth), camera (detection probability + lane offset), ultrasonic (short range)
- **ADAS Controller** — FCW (TTC < 2.5s), AEB (TTC < 1.0s), LDW (lateral offset > 0.3m)
- **HIL Test Runner** — 5 automated test cases with PASS/FAIL reporting
- **Visualization** — Trajectory, speed, sensor data, controller outputs

## How to Run

```matlab
cd matlab/examples/adas_hil_demo
main_adas_hil_demo
```

## Scenario

| Parameter | Value |
|-----------|-------|
| Initial speed | 80 km/h |
| Obstacle distance | 60 m (stationary) |
| Simulation time | 5 s |
| Time step | 0.01 s |

## Test Cases

| TC | Description | Expected |
|----|-------------|----------|
| 1 | Normal driving (first 0.5s) | No warning |
| 2 | Closing obstacle | FCW triggers |
| 3 | Very close (< 1s TTC) | AEB triggers |
| 4 | Lane drift | LDW triggers |
| 5 | Sensor failure | Graceful degradation (no crash) |

## R2016b Compatibility

- No `rms()` function
- No `arguments` block
- No string types (uses `char` arrays)
- No `tiledlayout` (uses `subplot`)
- Forward Euler integration

## File Structure

```
adas_hil_demo/
├── main_adas_hil_demo.m      Main script
├── vehicle_model.m           Longitudinal vehicle dynamics
├── sensor_model.m            Radar + camera + ultrasonic
├── adas_controller.m         FCW / AEB / LDW logic
├── hil_test_runner.m         Test case validation
├── visualize_results.m       Plotting
└── README.md                 This file
```
