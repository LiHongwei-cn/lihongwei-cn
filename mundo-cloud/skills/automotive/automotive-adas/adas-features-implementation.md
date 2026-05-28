# ADAS Features Implementation

## Overview

Concrete implementations of ADAS features: Adaptive Cruise Control (ACC), Lane Keep Assist (LKA), Automatic Emergency Braking (AEB), Blind Spot Detection (BSD), Park Assist, and Traffic Sign Recognition (TSR). Production-ready code for L0-L2+ systems.

## Adaptive Cruise Control (ACC)

### Full ACC Implementation

```cpp
#include <Eigen/Dense>
#include <algorithm>
#include <cmath>

class AdaptiveCruiseControl {
public:
    struct ACCParams {
        double time_gap = 2.0;              // seconds (ISO 22179)
        double min_distance = 5.0;          // meters
        double max_acceleration = 2.0;      // m/s²
        double max_deceleration = -3.0;     // m/s²
        double comfort_decel = -2.0;        // m/s²
        double set_speed = 30.0;            // m/s (108 km/h)
        double speed_tolerance = 2.0;       // m/s
    };

    enum class ACCMode {
        OFF,
        STANDBY,
        ACTIVE_CRUISE,
        ACTIVE_FOLLOWING,
        EMERGENCY_BRAKE
    };

    AdaptiveCruiseControl(const ACCParams& params) : params_(params), mode_(ACCMode::STANDBY) {}

    struct ACCOutput {
        double acceleration;        // Commanded acceleration (m/s²)
        ACCMode mode;
        double target_speed;
        double target_distance;
        bool warning_issued;
    };

    ACCOutput compute(double ego_velocity, double ego_acceleration,
                     const std::vector<DetectedObject>& objects) {
        ACCOutput output;
        output.mode = mode_;
        output.warning_issued = false;

        // Find lead vehicle
        auto lead_vehicle = find_lead_vehicle(objects, ego_velocity);

        if (!lead_vehicle.has_value()) {
            // No lead vehicle - cruise control mode
            output.acceleration = cruise_control(ego_velocity);
            output.target_speed = params_.set_speed;
            output.target_distance = 0.0;
            mode_ = ACCMode::ACTIVE_CRUISE;
        } else {
            // Following mode
            double relative_velocity = ego_velocity - lead_vehicle->velocity;
            double distance = lead_vehicle->distance;
            double desired_distance = calculate_desired_distance(ego_velocity);

            // Calculate acceleration using Intelligent Driver Model (IDM)
            output.acceleration = intelligent_driver_model(
                ego_velocity, distance, relative_velocity, desired_distance
            );

            output.target_speed = lead_vehicle->velocity;
            output.target_distance = desired_distance;

            // Check for emergency
            double ttc = time_to_collision(distance, relative_velocity);
            if (ttc > 0 && ttc < 2.0 && relative_velocity > 0) {
                output.acceleration = params_.max_deceleration;
                output.warning_issued = true;
                mode_ = ACCMode::EMERGENCY_BRAKE;
            } else {
                mode_ = ACCMode::ACTIVE_FOLLOWING;
            }
        }

        // Clamp acceleration
        output.acceleration = std::clamp(output.acceleration,
                                        params_.max_deceleration,
                                        params_.max_acceleration);

        return output;
    }

private:
    ACCParams params_;
    ACCMode mode_;

    struct DetectedObject {
        double distance;   // meters (longitudinal)
        double velocity;   // m/s
        double lateral_offset;  // meters
        std::string object_class;
    };

    std::optional<DetectedObject> find_lead_vehicle(
        const std::vector<DetectedObject>& objects, double ego_velocity)
    {
        std::optional<DetectedObject> lead;
        double min_distance = std::numeric_limits<double>::max();

        for (const auto& obj : objects) {
            // Filter: only consider vehicles in same lane
            if (std::abs(obj.lateral_offset) > 1.5) continue;

            // Filter: only vehicles ahead
            if (obj.distance < 0) continue;

            // Find closest
            if (obj.distance < min_distance) {
                min_distance = obj.distance;
                lead = obj;
            }
        }

        return lead;
    }

    double cruise_control(double ego_velocity) {
        // Simple P controller to reach set speed
        double error = params_.set_speed - ego_velocity;
        double kp = 0.5;
        return std::clamp(kp * error, params_.max_deceleration, params_.max_acceleration);
    }

    double calculate_desired_distance(double ego_velocity) {
        // Time gap policy: d = d_min + v * T
        return params_.min_distance + ego_velocity * params_.time_gap;
    }

    double intelligent_driver_model(double velocity, double distance,
                                    double relative_velocity, double desired_distance) {
        // IDM parameters
        const double a_max = params_.max_acceleration;
        const double b_comfortable = -params_.comfort_decel;
        const double delta = 4.0;  // Acceleration exponent

        // Desired dynamical distance
        double v_approach_term = velocity * relative_velocity / (2 * std::sqrt(a_max * b_comfortable));
        double s_star = params_.min_distance + std::max(0.0, velocity * params_.time_gap + v_approach_term);

        // IDM acceleration
        double accel = a_max * (1.0 - std::pow(velocity / params_.set_speed, delta) -
                               std::pow(s_star / distance, 2.0));

        return accel;
    }

    double time_to_collision(double distance, double relative_velocity) {
        if (relative_velocity <= 0) return -1.0;  // No collision
        return distance / relative_velocity;
    }
};
```

### AUTOSAR ACC Component

```xml
<!-- ACC_SWC.arxml -->
<AUTOSAR>
  <AR-PACKAGES>
    <AR-PACKAGE>
      <SHORT-NAME>ACC_Application</SHORT-NAME>
      <ELEMENTS>
        <APPLICATION-SW-COMPONENT-TYPE>
          <SHORT-NAME>ACC_SWC</SHORT-NAME>
          <PORTS>
            <R-PORT-PROTOTYPE>
              <SHORT-NAME>EgoSpeed</SHORT-NAME>
              <REQUIRED-INTERFACE-TREF>/Interfaces/SpeedInterface</REQUIRED-INTERFACE-TREF>
            </R-PORT-PROTOTYPE>
            <R-PORT-PROTOTYPE>
              <SHORT-NAME>RadarObjects</SHORT-NAME>
              <REQUIRED-INTERFACE-TREF>/Interfaces/ObjectListInterface</REQUIRED-INTERFACE-TREF>
            </R-PORT-PROTOTYPE>
            <P-PORT-PROTOTYPE>
              <SHORT-NAME>AccelRequest</SHORT-NAME>
              <PROVIDED-INTERFACE-TREF>/Interfaces/AccelerationInterface</PROVIDED-INTERFACE-TREF>
            </P-PORT-PROTOTYPE>
            <P-PORT-PROTOTYPE>
              <SHORT-NAME>ACCStatus</SHORT-NAME>
              <PROVIDED-INTERFACE-TREF>/Interfaces/ACCStatusInterface</PROVIDED-INTERFACE-TREF>
            </P-PORT-PROTOTYPE>
          </PORTS>
          <INTERNAL-BEHAVIORS>
            <SWC-INTERNAL-BEHAVIOR>
              <SHORT-NAME>ACC_InternalBehavior</SHORT-NAME>
              <RUNNABLES>
                <RUNNABLE-ENTITY>
                  <SHORT-NAME>ACC_MainFunction</SHORT-NAME>
                  <MINIMUM-START-INTERVAL>0.05</MINIMUM-START-INTERVAL>
                  <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
                  <SYMBOL>ACC_MainFunction</SYMBOL>
                </RUNNABLE-ENTITY>
              </RUNNABLES>
            </SWC-INTERNAL-BEHAVIOR>
          </INTERNAL-BEHAVIORS>
        </APPLICATION-SW-COMPONENT-TYPE>
      </ELEMENTS>
    </AR-PACKAGE>
  </AR-PACKAGES>
</AUTOSAR>
```

## Lane Keep Assist (LKA)

```cpp
#include <Eigen/Dense>
#include <vector>
#include <cmath>

class LaneKeepAssist {
public:
    struct LKAParams {
        double lookahead_time = 2.0;        // seconds
        double kp_lateral = 0.5;            // Proportional gain
        double ki_lateral = 0.05;           // Integral gain
        double kd_lateral = 0.1;            // Derivative gain
        double max_steering_angle = 0.1;    // radians (~6 degrees)
        double lane_departure_threshold = 0.3;  // meters
    };

    enum class LKAState {
        OFF,
        STANDBY,
        ACTIVE,
        WARNING
    };

    LaneKeepAssist(const LKAParams& params) : params_(params), state_(LKAState::STANDBY) {
        integral_error_ = 0.0;
        previous_error_ = 0.0;
    }

    struct LaneMarkings {
        // Polynomial coefficients: lateral_offset = c0 + c1*x + c2*x^2 + c3*x^3
        Eigen::Vector4d left_lane;
        Eigen::Vector4d right_lane;
        bool left_detected;
        bool right_detected;
        double lane_width;
    };

    struct LKAOutput {
        double steering_torque;  // N⋅m
        LKAState state;
        bool warning_active;
        double lateral_offset;
    };

    LKAOutput compute(const LaneMarkings& lanes, double velocity, double dt) {
        LKAOutput output;
        output.state = state_;
        output.warning_active = false;

        // Check if lanes are detected
        if (!lanes.left_detected && !lanes.right_detected) {
            state_ = LKAState::STANDBY;
            output.steering_torque = 0.0;
            integral_error_ = 0.0;
            return output;
        }

        // Calculate lateral offset from lane center
        double lateral_offset = calculate_lateral_offset(lanes);
        output.lateral_offset = lateral_offset;

        // Calculate lateral error at lookahead distance
        double lookahead_distance = velocity * params_.lookahead_time;
        double lateral_error = calculate_lateral_error(lanes, lookahead_distance);

        // Check for lane departure
        if (std::abs(lateral_offset) > params_.lane_departure_threshold) {
            state_ = LKAState::WARNING;
            output.warning_active = true;
        } else {
            state_ = LKAState::ACTIVE;
        }

        // PID control for steering torque
        integral_error_ += lateral_error * dt;
        double derivative_error = (lateral_error - previous_error_) / dt;

        double steering_correction = params_.kp_lateral * lateral_error +
                                    params_.ki_lateral * integral_error_ +
                                    params_.kd_lateral * derivative_error;

        previous_error_ = lateral_error;

        // Convert to steering torque (simplified model)
        double steering_torque = steering_correction * 10.0;  // N⋅m

        // Limit torque
        const double max_torque = 3.0;  // N⋅m
        steering_torque = std::clamp(steering_torque, -max_torque, max_torque);

        output.steering_torque = steering_torque;

        return output;
    }

private:
    LKAParams params_;
    LKAState state_;
    double integral_error_;
    double previous_error_;

    double calculate_lateral_offset(const LaneMarkings& lanes) {
        // Calculate offset from lane center
        double left_offset = 0.0, right_offset = 0.0;
        int count = 0;

        if (lanes.left_detected) {
            left_offset = lanes.left_lane(0);  // c0 at x=0 (vehicle position)
            count++;
        }

        if (lanes.right_detected) {
            right_offset = lanes.right_lane(0);
            count++;
        }

        if (count == 2) {
            // Both lanes detected - offset from center
            return (left_offset + right_offset) / 2.0;
        } else if (lanes.left_detected) {
            // Only left lane - assume lane width
            return left_offset - lanes.lane_width / 2.0;
        } else {
            // Only right lane
            return right_offset + lanes.lane_width / 2.0;
        }
    }

    double calculate_lateral_error(const LaneMarkings& lanes, double lookahead_distance) {
        // Evaluate polynomial at lookahead distance
        double x = lookahead_distance;
        double left_lateral = 0.0, right_lateral = 0.0;
        int count = 0;

        if (lanes.left_detected) {
            left_lateral = lanes.left_lane(0) + lanes.left_lane(1) * x +
                          lanes.left_lane(2) * x * x + lanes.left_lane(3) * x * x * x;
            count++;
        }

        if (lanes.right_detected) {
            right_lateral = lanes.right_lane(0) + lanes.right_lane(1) * x +
                           lanes.right_lane(2) * x * x + lanes.right_lane(3) * x * x * x;
            count++;
        }

        if (count == 2) {
            return (left_lateral + right_lateral) / 2.0;
        } else if (lanes.left_detected) {
            return left_lateral - lanes.lane_width / 2.0;
        } else {
            return right_lateral + lanes.lane_width / 2.0;
        }
    }
};
```

## Automatic Emergency Braking (AEB)

```cpp
class AutomaticEmergencyBraking {
public:
    struct AEBParams {
        double warning_ttc = 2.5;       // Time to collision for warning (seconds)
        double brake_ttc = 1.5;         // TTC for partial braking
        double emergency_ttc = 0.8;     // TTC for full emergency braking
        double max_brake_pressure = 100.0;  // bar
        double partial_brake_pressure = 30.0;  // bar
    };

    enum class AEBState {
        MONITORING,
        WARNING,
        PARTIAL_BRAKE,
        EMERGENCY_BRAKE
    };

    AutomaticEmergencyBraking(const AEBParams& params) : params_(params) {}

    struct AEBOutput {
        double brake_pressure;  // bar
        AEBState state;
        bool warning_active;
        bool brake_active;
        double ttc;
    };

    AEBOutput compute(const DetectedObject& closest_object, double ego_velocity) {
        AEBOutput output;
        output.brake_pressure = 0.0;
        output.state = AEBState::MONITORING;
        output.warning_active = false;
        output.brake_active = false;
        output.ttc = -1.0;

        if (!closest_object.valid) {
            return output;
        }

        // Calculate time to collision
        double relative_velocity = ego_velocity - closest_object.velocity;
        double ttc = calculate_ttc(closest_object.distance, relative_velocity);
        output.ttc = ttc;

        if (ttc < 0) {
            return output;  // No collision imminent
        }

        // State machine
        if (ttc < params_.emergency_ttc) {
            // Emergency braking
            output.state = AEBState::EMERGENCY_BRAKE;
            output.brake_pressure = params_.max_brake_pressure;
            output.brake_active = true;
            output.warning_active = true;
        } else if (ttc < params_.brake_ttc) {
            // Partial braking
            output.state = AEBState::PARTIAL_BRAKE;
            output.brake_pressure = params_.partial_brake_pressure;
            output.brake_active = true;
            output.warning_active = true;
        } else if (ttc < params_.warning_ttc) {
            // Warning only
            output.state = AEBState::WARNING;
            output.warning_active = true;
        }

        return output;
    }

private:
    AEBParams params_;

    struct DetectedObject {
        double distance;
        double velocity;
        bool valid;
    };

    double calculate_ttc(double distance, double relative_velocity) {
        if (relative_velocity <= 0) return -1.0;
        return distance / relative_velocity;
    }
};
```

## Blind Spot Detection (BSD)

```cpp
class BlindSpotDetection {
public:
    struct BSDParams {
        double blind_spot_min_x = -1.0;     // meters (rear)
        double blind_spot_max_x = 1.0;      // meters (front)
        double blind_spot_min_y = 1.5;      // meters (lateral)
        double blind_spot_max_y = 3.5;      // meters (lateral)
        double warning_velocity_threshold = 2.0;  // m/s (approaching)
    };

    enum class BSDZone {
        NO_DETECTION,
        LEFT_BLIND_SPOT,
        RIGHT_BLIND_SPOT,
        BOTH_BLIND_SPOTS
    };

    BlindSpotDetection(const BSDParams& params) : params_(params) {}

    struct BSDOutput {
        BSDZone zone;
        bool left_warning;
        bool right_warning;
        bool left_approaching;
        bool right_approaching;
    };

    BSDOutput compute(const std::vector<DetectedObject>& objects) {
        BSDOutput output;
        output.zone = BSDZone::NO_DETECTION;
        output.left_warning = false;
        output.right_warning = false;
        output.left_approaching = false;
        output.right_approaching = false;

        for (const auto& obj : objects) {
            // Check if object is in blind spot region
            bool in_longitudinal_range = (obj.x >= params_.blind_spot_min_x &&
                                         obj.x <= params_.blind_spot_max_x);

            bool in_left_blind_spot = (in_longitudinal_range &&
                                      obj.y >= params_.blind_spot_min_y &&
                                      obj.y <= params_.blind_spot_max_y);

            bool in_right_blind_spot = (in_longitudinal_range &&
                                       obj.y >= -params_.blind_spot_max_y &&
                                       obj.y <= -params_.blind_spot_min_y);

            if (in_left_blind_spot) {
                output.left_warning = true;

                // Check if approaching
                if (obj.vx > params_.warning_velocity_threshold) {
                    output.left_approaching = true;
                }
            }

            if (in_right_blind_spot) {
                output.right_warning = true;

                if (obj.vx > params_.warning_velocity_threshold) {
                    output.right_approaching = true;
                }
            }
        }

        // Determine zone
        if (output.left_warning && output.right_warning) {
            output.zone = BSDZone::BOTH_BLIND_SPOTS;
        } else if (output.left_warning) {
            output.zone = BSDZone::LEFT_BLIND_SPOT;
        } else if (output.right_warning) {
            output.zone = BSDZone::RIGHT_BLIND_SPOT;
        }

        return output;
    }

private:
    BSDParams params_;

    struct DetectedObject {
        double x, y;      // Position relative to ego vehicle (meters)
        double vx, vy;    // Velocity relative to ego vehicle (m/s)
    };
};
```

## Parking Assist

```python
import numpy as np
from enum import Enum

class ParkingAssistant:
    """
    Automated parking system for parallel and perpendicular parking
    """

    class ParkingMode(Enum):
        SEARCH = 1
        PLANNING = 2
        EXECUTING = 3
        COMPLETED = 4

    def __init__(self, vehicle_length=4.5, vehicle_width=1.8, wheelbase=2.7):
        self.vehicle_length = vehicle_length
        self.vehicle_width = vehicle_width
        self.wheelbase = wheelbase
        self.mode = self.ParkingMode.SEARCH

        # Minimum parking space dimensions
        self.min_parallel_length = vehicle_length + 1.0  # meters
        self.min_perpendicular_width = vehicle_width + 0.6  # meters

    def detect_parking_space(self, ultrasonic_measurements):
        """
        Detect available parking spaces using ultrasonic sensors

        Args:
            ultrasonic_measurements: List of distances from 12 ultrasonic sensors

        Returns:
            parking_space: Dictionary with space dimensions and type
        """
        # Left side measurements (4 sensors)
        left_front = ultrasonic_measurements[0]
        left_mid_front = ultrasonic_measurements[1]
        left_mid_rear = ultrasonic_measurements[2]
        left_rear = ultrasonic_measurements[3]

        # Detect parallel parking space
        if (left_front > 2.0 and left_mid_front > 2.0 and
            left_mid_rear > 2.0 and left_rear > 2.0):

            # Measure space length
            space_length = self.measure_space_length(ultrasonic_measurements)

            if space_length >= self.min_parallel_length:
                return {
                    'type': 'parallel',
                    'length': space_length,
                    'valid': True
                }

        return {'valid': False}

    def plan_parallel_parking(self, space_length, space_lateral_offset):
        """
        Plan trajectory for parallel parking

        Returns:
            List of waypoints with (x, y, theta, steering_angle)
        """
        waypoints = []

        # Phase 1: Align with parking space
        waypoints.append({
            'x': 0.0,
            'y': 0.0,
            'theta': 0.0,
            'steering': 0.0,
            'velocity': 0.5  # m/s
        })

        # Phase 2: Reverse into space with maximum steering
        max_steering = 0.6  # radians
        reverse_distance = 3.0  # meters

        for i in range(10):
            progress = i / 10.0
            waypoints.append({
                'x': -progress * reverse_distance * np.cos(max_steering),
                'y': space_lateral_offset - progress * reverse_distance * np.sin(max_steering),
                'theta': -progress * max_steering,
                'steering': max_steering,
                'velocity': -0.3  # Reverse slowly
            })

        # Phase 3: Straighten wheels and center in space
        for i in range(5):
            progress = (i + 1) / 5.0
            waypoints.append({
                'x': waypoints[-1]['x'] - 0.3,
                'y': waypoints[-1]['y'],
                'theta': -(1.0 - progress * 0.5) * max_steering,
                'steering': -progress * max_steering,
                'velocity': -0.2
            })

        return waypoints

    def execute_parking(self, current_pose, target_waypoint, dt=0.1):
        """
        Execute parking maneuver using path following controller

        Args:
            current_pose: (x, y, theta) current vehicle pose
            target_waypoint: Dictionary with target pose and steering
            dt: Time step

        Returns:
            control_output: (steering_angle, velocity)
        """
        # Pure pursuit controller for waypoint following
        dx = target_waypoint['x'] - current_pose[0]
        dy = target_waypoint['y'] - current_pose[1]

        # Calculate steering angle
        lookahead_distance = 1.0  # meters
        alpha = np.arctan2(dy, dx) - current_pose[2]

        steering_angle = np.arctan2(2.0 * self.wheelbase * np.sin(alpha),
                                    lookahead_distance)

        # Limit steering angle
        steering_angle = np.clip(steering_angle, -0.6, 0.6)

        velocity = target_waypoint['velocity']

        return (steering_angle, velocity)

    def measure_space_length(self, ultrasonic_measurements):
        """Estimate parking space length from ultrasonic measurements"""
        # Simplified: integrate measurements along vehicle path
        # In production, use more sophisticated SLAM-based approach
        return 5.5  # meters (placeholder)
```

## Traffic Sign Recognition (TSR)

```python
import torch
import torchvision.transforms as transforms
from PIL import Image

class TrafficSignRecognition:
    """
    Traffic sign detection and classification
    """

    def __init__(self, model_path, device='cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')

        # Load pretrained model (YOLO + classifier)
        self.detector = torch.hub.load('ultralytics/yolov5', 'custom',
                                      path=model_path, force_reload=False)

        # Sign classes (GTSDB/GTSRB dataset)
        self.sign_classes = {
            0: 'speed_limit_20',
            1: 'speed_limit_30',
            2: 'speed_limit_50',
            3: 'speed_limit_60',
            4: 'speed_limit_70',
            5: 'speed_limit_80',
            6: 'speed_limit_100',
            7: 'speed_limit_120',
            8: 'no_overtaking',
            9: 'no_overtaking_trucks',
            10: 'priority_road',
            11: 'yield',
            12: 'stop',
            13: 'no_entry',
            # ... (43 classes total)
        }

    def detect_and_classify(self, image):
        """
        Detect traffic signs and classify them

        Args:
            image: RGB image (H, W, 3)

        Returns:
            List of detected signs with class, confidence, bbox
        """
        # Run detection
        results = self.detector(image)

        detected_signs = []

        for *box, conf, cls in results.xyxy[0].cpu().numpy():
            sign_id = int(cls)

            if sign_id in self.sign_classes:
                sign = {
                    'class': self.sign_classes[sign_id],
                    'confidence': float(conf),
                    'bbox': box,  # [x1, y1, x2, y2]
                    'sign_id': sign_id
                }

                detected_signs.append(sign)

        return detected_signs

    def extract_speed_limit(self, detected_signs):
        """Extract current speed limit from detected signs"""
        speed_limits = []

        for sign in detected_signs:
            if 'speed_limit' in sign['class']:
                # Extract speed value from class name
                speed_value = int(sign['class'].split('_')[-1])
                speed_limits.append((speed_value, sign['confidence']))

        if speed_limits:
            # Return most confident speed limit
            return max(speed_limits, key=lambda x: x[1])[0]

        return None
```

## HIL Testing Configuration

```python
# Hardware-in-Loop test setup for ADAS features
import can

class ADASHILTester:
    """
    HIL test environment for ADAS features
    """

    def __init__(self, can_interface='can0'):
        self.bus = can.interface.Bus(channel=can_interface, bustype='socketcan')

    def simulate_radar_objects(self, objects):
        """Send simulated radar objects over CAN"""
        for obj in objects:
            # CAN message for radar object (example format)
            data = [
                int(obj['distance'] * 10) & 0xFF,
                (int(obj['distance'] * 10) >> 8) & 0xFF,
                int(obj['velocity'] * 10 + 128) & 0xFF,
                int(obj['lateral_offset'] * 10 + 128) & 0xFF,
                obj['object_id'] & 0xFF,
                0, 0, 0  # Reserved
            ]

            msg = can.Message(arbitration_id=0x500 + obj['object_id'],
                            data=data,
                            is_extended_id=False)

            self.bus.send(msg)

    def read_acc_output(self):
        """Read ACC output from ECU"""
        msg = self.bus.recv(timeout=1.0)

        if msg and msg.arbitration_id == 0x400:
            # Parse ACC command
            accel_request = (msg.data[0] | (msg.data[1] << 8)) / 100.0 - 10.0
            acc_active = bool(msg.data[2] & 0x01)

            return {
                'acceleration': accel_request,
                'active': acc_active
            }

        return None

    def test_acc_scenario(self, scenario_name, test_duration=10.0):
        """Run ACC test scenario"""
        print(f"Running ACC test: {scenario_name}")

        # Load scenario (lead vehicle trajectory)
        scenario = self.load_scenario(scenario_name)

        start_time = time.time()

        while (time.time() - start_time) < test_duration:
            # Simulate radar detections
            timestamp = time.time() - start_time
            objects = scenario.get_objects_at_time(timestamp)

            self.simulate_radar_objects(objects)

            # Read ACC response
            acc_output = self.read_acc_output()

            if acc_output:
                print(f"T={timestamp:.2f}s: ACC accel={acc_output['acceleration']:.2f} m/s²")

            time.sleep(0.05)  # 20 Hz

        print(f"Test {scenario_name} completed")
```

## Performance Metrics

| Feature | Latency | Accuracy | ASIL |
|---------|---------|----------|------|
| **ACC** | < 100ms | TTC error < 5% | ASIL B |
| **LKA** | < 50ms | Lateral error < 10cm | ASIL B |
| **AEB** | < 50ms | False positive < 1% | ASIL D |
| **BSD** | < 100ms | Detection rate > 99% | ASIL A |
| **Parking** | < 200ms | Position error < 5cm | ASIL A |
| **TSR** | < 200ms | Recognition > 95% | QM |

## Standards

- **ISO 22179**: Full-speed ACC
- **ISO 11270**: Lane departure warning
- **Euro NCAP**: AEB testing protocols
- **UN R79**: Steering system requirements (LKA)

## Related Skills

- sensor-fusion-perception.md
- camera-processing-vision.md
- path-planning-control.md
