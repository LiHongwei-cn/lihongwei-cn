# HD Maps & Localization for ADAS

## Overview

High-definition map formats (Lanelet2, OpenDRIVE, NDS), map-based localization, GNSS/IMU fusion, visual odometry, SLAM (ORB-SLAM, Cartographer), and achieving <10cm localization accuracy for L3+ autonomy.

## HD Map Formats

### Lanelet2 Format

```xml
<!-- Example Lanelet2 map -->
<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <!-- Points (nodes) -->
  <node id="1" lat="48.778000" lon="9.180000"/>
  <node id="2" lat="48.778100" lon="9.180100"/>
  <node id="3" lat="48.778200" lon="9.180200"/>

  <!-- Left lane boundary -->
  <way id="100">
    <nd ref="1"/>
    <nd ref="2"/>
    <nd ref="3"/>
    <tag k="type" v="line_thin"/>
    <tag k="subtype" v="dashed"/>
  </way>

  <!-- Right lane boundary -->
  <way id="101">
    <nd ref="4"/>
    <nd ref="5"/>
    <nd ref="6"/>
    <tag k="type" v="line_thin"/>
    <tag k="subtype" v="solid"/>
  </way>

  <!-- Lanelet (lane) -->
  <relation id="1000">
    <member type="way" ref="100" role="left"/>
    <member type="way" ref="101" role="right"/>
    <tag k="type" v="lanelet"/>
    <tag k="subtype" v="road"/>
    <tag k="location" v="urban"/>
    <tag k="speed_limit" v="50"/>
    <tag k="participant:vehicle" v="yes"/>
  </relation>
</osm>
```

### Lanelet2 C++ API

```cpp
#include <lanelet2_core/LaneletMap.h>
#include <lanelet2_io/Io.h>
#include <lanelet2_projection/UTM.h>
#include <lanelet2_routing/RoutingGraph.h>
#include <lanelet2_traffic_rules/TrafficRulesFactory.h>

class HDMapManager {
public:
    HDMapManager(const std::string& map_file) {
        // Load map with UTM projection
        std::string projector_type = "utm";
        lanelet::projection::UtmProjector projector(
            lanelet::Origin({48.778, 9.180})  // Origin lat/lon
        );

        map_ = lanelet::load(map_file, projector);

        // Create traffic rules
        traffic_rules_ = lanelet::traffic_rules::TrafficRulesFactory::create(
            lanelet::Locations::Germany,
            lanelet::Participants::Vehicle
        );

        // Build routing graph
        routing_graph_ = lanelet::routing::RoutingGraph::build(*map_, *traffic_rules_);
    }

    struct LocalizationResult {
        lanelet::ConstLanelet current_lanelet;
        double lateral_offset;        // meters (negative = left of centerline)
        double longitudinal_position;  // meters along lanelet
        double heading_error;         // radians
        bool valid;
    };

    LocalizationResult localize(const Eigen::Vector2d& position, double heading) {
        LocalizationResult result;
        result.valid = false;

        // Find nearest lanelet
        lanelet::Point3d query_point(lanelet::utils::getId(), position.x(), position.y(), 0.0);

        auto nearest_lanelets = lanelet::geometry::findNearest(
            map_->laneletLayer, query_point, 1
        );

        if (nearest_lanelets.empty()) {
            return result;
        }

        result.current_lanelet = nearest_lanelets.front();

        // Calculate lateral offset
        result.lateral_offset = calculate_lateral_offset(position, result.current_lanelet);

        // Calculate longitudinal position
        result.longitudinal_position = calculate_arc_length(position, result.current_lanelet);

        // Calculate heading error
        double lanelet_heading = calculate_lanelet_heading(position, result.current_lanelet);
        result.heading_error = normalize_angle(heading - lanelet_heading);

        result.valid = true;
        return result;
    }

    lanelet::routing::Route plan_route(const lanelet::ConstLanelet& start,
                                      const lanelet::ConstLanelet& goal) {
        auto optional_route = routing_graph_->getRoute(start, goal, 0);

        if (optional_route) {
            return optional_route.get();
        }

        return lanelet::routing::Route();
    }

    double get_speed_limit(const lanelet::ConstLanelet& lanelet) {
        lanelet::SpeedLimitInformation speed_limit = traffic_rules_->speedLimit(lanelet);
        return speed_limit.speedLimit.value();  // m/s
    }

private:
    lanelet::LaneletMapPtr map_;
    lanelet::traffic_rules::TrafficRulesPtr traffic_rules_;
    lanelet::routing::RoutingGraphUPtr routing_graph_;

    double calculate_lateral_offset(const Eigen::Vector2d& position,
                                    const lanelet::ConstLanelet& lanelet) {
        // Project position onto lanelet centerline
        auto centerline = lanelet.centerline();

        double min_dist = std::numeric_limits<double>::max();
        Eigen::Vector2d closest_point;

        for (size_t i = 0; i < centerline.size() - 1; ++i) {
            Eigen::Vector2d p1(centerline[i].x(), centerline[i].y());
            Eigen::Vector2d p2(centerline[i+1].x(), centerline[i+1].y());

            Eigen::Vector2d segment = p2 - p1;
            Eigen::Vector2d to_pos = position - p1;

            double t = std::clamp(to_pos.dot(segment) / segment.squaredNorm(), 0.0, 1.0);
            Eigen::Vector2d projection = p1 + t * segment;

            double dist = (position - projection).norm();
            if (dist < min_dist) {
                min_dist = dist;
                closest_point = projection;
            }
        }

        // Determine sign (left/right of centerline)
        // Use cross product
        Eigen::Vector2d p1(centerline[0].x(), centerline[0].y());
        Eigen::Vector2d p2(centerline[1].x(), centerline[1].y());
        Eigen::Vector2d segment = p2 - p1;
        Eigen::Vector2d to_pos = position - p1;

        double cross = segment.x() * to_pos.y() - segment.y() * to_pos.x();
        double sign = (cross > 0) ? -1.0 : 1.0;

        return sign * min_dist;
    }

    double calculate_arc_length(const Eigen::Vector2d& position,
                                const lanelet::ConstLanelet& lanelet) {
        auto centerline = lanelet.centerline();
        double arc_length = 0.0;

        // Find closest segment and accumulate distance
        for (size_t i = 0; i < centerline.size() - 1; ++i) {
            Eigen::Vector2d p1(centerline[i].x(), centerline[i].y());
            Eigen::Vector2d p2(centerline[i+1].x(), centerline[i+1].y());

            // Check if position projects onto this segment
            Eigen::Vector2d segment = p2 - p1;
            Eigen::Vector2d to_pos = position - p1;

            double t = std::clamp(to_pos.dot(segment) / segment.squaredNorm(), 0.0, 1.0);

            if (t < 1.0) {
                // Position projects onto this segment
                arc_length += t * segment.norm();
                break;
            } else {
                arc_length += segment.norm();
            }
        }

        return arc_length;
    }

    double calculate_lanelet_heading(const Eigen::Vector2d& position,
                                     const lanelet::ConstLanelet& lanelet) {
        auto centerline = lanelet.centerline();

        // Find closest segment
        size_t closest_segment = 0;
        double min_dist = std::numeric_limits<double>::max();

        for (size_t i = 0; i < centerline.size() - 1; ++i) {
            Eigen::Vector2d p1(centerline[i].x(), centerline[i].y());
            Eigen::Vector2d p2(centerline[i+1].x(), centerline[i+1].y());

            Eigen::Vector2d segment = p2 - p1;
            Eigen::Vector2d to_pos = position - p1;

            double t = std::clamp(to_pos.dot(segment) / segment.squaredNorm(), 0.0, 1.0);
            Eigen::Vector2d projection = p1 + t * segment;

            double dist = (position - projection).norm();
            if (dist < min_dist) {
                min_dist = dist;
                closest_segment = i;
            }
        }

        // Calculate heading of closest segment
        Eigen::Vector2d p1(centerline[closest_segment].x(), centerline[closest_segment].y());
        Eigen::Vector2d p2(centerline[closest_segment+1].x(), centerline[closest_segment+1].y());

        return std::atan2(p2.y() - p1.y(), p2.x() - p1.x());
    }

    double normalize_angle(double angle) {
        while (angle > M_PI) angle -= 2 * M_PI;
        while (angle < -M_PI) angle += 2 * M_PI;
        return angle;
    }
};
```

### OpenDRIVE Format

```xml
<!-- OpenDRIVE HD map example -->
<?xml version="1.0" encoding="UTF-8"?>
<OpenDRIVE>
  <header revMajor="1" revMinor="4" name="HighwayMap" version="1.0"/>

  <road name="Highway_A9" length="1000.0" id="1" junction="-1">
    <link>
      <predecessor elementType="road" elementId="0"/>
      <successor elementType="road" elementId="2"/>
    </link>

    <!-- Road geometry -->
    <planView>
      <geometry s="0.0" x="0.0" y="0.0" hdg="0.0" length="500.0">
        <line/>
      </geometry>
      <geometry s="500.0" x="500.0" y="0.0" hdg="0.0" length="500.0">
        <arc curvature="0.002"/>  <!-- R = 500m curve -->
      </geometry>
    </planView>

    <!-- Lane sections -->
    <lanes>
      <laneSection s="0.0">
        <center>
          <lane id="0" type="driving" level="0"/>
        </center>
        <right>
          <lane id="-1" type="driving" level="0">
            <width sOffset="0.0" a="3.75" b="0.0" c="0.0" d="0.0"/>
            <roadMark sOffset="0.0" type="solid" weight="standard" color="white"/>
            <speed sOffset="0.0" max="33.33"/>  <!-- 120 km/h -->
          </lane>
          <lane id="-2" type="driving" level="0">
            <width sOffset="0.0" a="3.75" b="0.0" c="0.0" d="0.0"/>
            <roadMark sOffset="0.0" type="broken" weight="standard" color="white"/>
          </lane>
        </right>
      </laneSection>
    </lanes>
  </road>
</OpenDRIVE>
```

## GNSS/IMU Sensor Fusion

### Extended Kalman Filter for GNSS/IMU

```cpp
#include <Eigen/Dense>

class GNSSIMUFusion {
public:
    GNSSIMUFusion() {
        // State: [x, y, z, vx, vy, vz, roll, pitch, yaw]
        state_ = Eigen::VectorXd::Zero(9);
        covariance_ = Eigen::MatrixXd::Identity(9, 9) * 100.0;

        // Process noise
        Q_ = Eigen::MatrixXd::Identity(9, 9);
        Q_.block<3,3>(0,0) *= 0.1;   // Position
        Q_.block<3,3>(3,3) *= 1.0;   // Velocity
        Q_.block<3,3>(6,6) *= 0.01;  // Orientation

        // GNSS measurement noise
        R_gnss_ = Eigen::Matrix3d::Identity() * 1.0;  // 1m std dev

        // IMU measurement noise
        R_imu_ = Eigen::MatrixXd::Identity(6, 6);
        R_imu_.block<3,3>(0,0) *= 0.1;   // Acceleration (m/s²)
        R_imu_.block<3,3>(3,3) *= 0.01;  // Gyroscope (rad/s)
    }

    struct IMUMeasurement {
        Eigen::Vector3d acceleration;
        Eigen::Vector3d angular_velocity;
        double timestamp;
    };

    struct GNSSMeasurement {
        double latitude;
        double longitude;
        double altitude;
        Eigen::Vector3d position_enu;  // East-North-Up frame
        double timestamp;
        double horizontal_accuracy;
        double vertical_accuracy;
    };

    void predict_imu(const IMUMeasurement& imu, double dt) {
        // IMU-based prediction (high-rate, ~100Hz)

        // Gravity compensation
        Eigen::Vector3d gravity(0, 0, -9.81);

        // Rotate acceleration to world frame
        Eigen::Matrix3d R = rotation_matrix(state_(6), state_(7), state_(8));
        Eigen::Vector3d accel_world = R * imu.acceleration + gravity;

        // Update velocity
        state_.segment<3>(3) += accel_world * dt;

        // Update position
        state_.segment<3>(0) += state_.segment<3>(3) * dt + 0.5 * accel_world * dt * dt;

        // Update orientation (integrate gyroscope)
        state_.segment<3>(6) += imu.angular_velocity * dt;

        // Normalize angles
        state_(6) = normalize_angle(state_(6));
        state_(7) = normalize_angle(state_(7));
        state_(8) = normalize_angle(state_(8));

        // Predict covariance
        Eigen::MatrixXd F = compute_state_jacobian(imu, dt);
        covariance_ = F * covariance_ * F.transpose() + Q_;
    }

    void update_gnss(const GNSSMeasurement& gnss) {
        // GNSS measurement update (low-rate, ~10Hz)

        // Measurement matrix (GNSS observes position only)
        Eigen::MatrixXd H = Eigen::MatrixXd::Zero(3, 9);
        H.block<3,3>(0,0) = Eigen::Matrix3d::Identity();

        // Innovation
        Eigen::Vector3d z = gnss.position_enu;
        Eigen::Vector3d z_pred = state_.segment<3>(0);
        Eigen::Vector3d y = z - z_pred;

        // Measurement noise (from GNSS accuracy)
        Eigen::Matrix3d R = Eigen::Matrix3d::Identity();
        R(0,0) = gnss.horizontal_accuracy * gnss.horizontal_accuracy;
        R(1,1) = gnss.horizontal_accuracy * gnss.horizontal_accuracy;
        R(2,2) = gnss.vertical_accuracy * gnss.vertical_accuracy;

        // Innovation covariance
        Eigen::Matrix3d S = H * covariance_ * H.transpose() + R;

        // Kalman gain
        Eigen::MatrixXd K = covariance_ * H.transpose() * S.inverse();

        // Update state
        state_ = state_ + K * y;

        // Update covariance
        Eigen::MatrixXd I = Eigen::MatrixXd::Identity(9, 9);
        covariance_ = (I - K * H) * covariance_;
    }

    Eigen::VectorXd get_state() const { return state_; }
    Eigen::MatrixXd get_covariance() const { return covariance_; }

    struct LocalizationOutput {
        Eigen::Vector3d position;
        Eigen::Vector3d velocity;
        Eigen::Vector3d orientation;  // roll, pitch, yaw
        Eigen::Matrix3d position_covariance;
        double horizontal_accuracy() const {
            return std::sqrt(position_covariance(0,0) + position_covariance(1,1));
        }
    };

    LocalizationOutput get_localization() const {
        LocalizationOutput output;
        output.position = state_.segment<3>(0);
        output.velocity = state_.segment<3>(3);
        output.orientation = state_.segment<3>(6);
        output.position_covariance = covariance_.block<3,3>(0,0);
        return output;
    }

private:
    Eigen::VectorXd state_;       // [x, y, z, vx, vy, vz, roll, pitch, yaw]
    Eigen::MatrixXd covariance_;
    Eigen::MatrixXd Q_;           // Process noise
    Eigen::Matrix3d R_gnss_;      // GNSS measurement noise
    Eigen::MatrixXd R_imu_;       // IMU measurement noise

    Eigen::Matrix3d rotation_matrix(double roll, double pitch, double yaw) {
        Eigen::Matrix3d R;

        double cr = std::cos(roll);
        double sr = std::sin(roll);
        double cp = std::cos(pitch);
        double sp = std::sin(pitch);
        double cy = std::cos(yaw);
        double sy = std::sin(yaw);

        R << cy*cp, cy*sp*sr - sy*cr, cy*sp*cr + sy*sr,
             sy*cp, sy*sp*sr + cy*cr, sy*sp*cr - cy*sr,
             -sp,   cp*sr,            cp*cr;

        return R;
    }

    Eigen::MatrixXd compute_state_jacobian(const IMUMeasurement& imu, double dt) {
        // Simplified: assume linear dynamics
        Eigen::MatrixXd F = Eigen::MatrixXd::Identity(9, 9);

        // Position depends on velocity
        F.block<3,3>(0,3) = Eigen::Matrix3d::Identity() * dt;

        return F;
    }

    double normalize_angle(double angle) {
        while (angle > M_PI) angle -= 2 * M_PI;
        while (angle < -M_PI) angle += 2 * M_PI;
        return angle;
    }
};
```

## Visual Odometry

### ORB-SLAM3 Integration

```cpp
#include <System.h>
#include <opencv2/core.hpp>

class VisualOdometry {
public:
    VisualOdometry(const std::string& vocab_file, const std::string& settings_file) {
        // Initialize ORB-SLAM3
        slam_system_ = new ORB_SLAM3::System(
            vocab_file,
            settings_file,
            ORB_SLAM3::System::MONOCULAR,
            true  // Use viewer
        );
    }

    ~VisualOdometry() {
        slam_system_->Shutdown();
        delete slam_system_;
    }

    struct VOOutput {
        Eigen::Matrix4f pose;      // 4x4 transformation matrix
        bool tracking_good;
        int num_features;
        double scale_drift;
    };

    VOOutput process_frame(const cv::Mat& image, double timestamp) {
        VOOutput output;

        // Track frame
        cv::Mat Tcw = slam_system_->TrackMonocular(image, timestamp);

        if (Tcw.empty()) {
            output.tracking_good = false;
            return output;
        }

        // Convert to Eigen
        output.pose = Eigen::Matrix4f::Identity();
        for (int i = 0; i < 4; ++i) {
            for (int j = 0; j < 4; ++j) {
                output.pose(i, j) = Tcw.at<float>(i, j);
            }
        }

        output.tracking_good = true;
        output.num_features = slam_system_->GetTrackedMapPoints().size();

        return output;
    }

private:
    ORB_SLAM3::System* slam_system_;
};
```

## Map Matching for Lane-Level Localization

```python
import numpy as np
from scipy.spatial import KDTree

class MapMatcher:
    """
    Match GNSS/IMU pose to HD map for lane-level localization
    """

    def __init__(self, hd_map):
        """
        Args:
            hd_map: Dictionary with 'lanelets', 'centerlines', etc.
        """
        self.hd_map = hd_map

        # Build spatial index for efficient matching
        self.build_spatial_index()

    def build_spatial_index(self):
        """Build KD-tree for fast nearest neighbor search"""
        all_points = []

        for lanelet_id, centerline in self.hd_map['centerlines'].items():
            for point in centerline:
                all_points.append(point[:2])  # x, y only

        self.kdtree = KDTree(np.array(all_points))

    def match_to_map(self, pose, heading, search_radius=10.0):
        """
        Match vehicle pose to HD map

        Args:
            pose: (x, y) vehicle position
            heading: vehicle heading (radians)
            search_radius: search radius in meters

        Returns:
            matched_lanelet: Lanelet ID
            lateral_offset: Offset from centerline (meters)
            heading_error: Heading error (radians)
        """
        # Find candidate lanelets within search radius
        candidates = self.find_candidate_lanelets(pose, search_radius)

        if not candidates:
            return None, None, None

        # Score candidates based on position and heading
        best_match = None
        best_score = float('inf')

        for lanelet_id in candidates:
            score, lateral_offset, heading_error = self.score_lanelet_match(
                lanelet_id, pose, heading
            )

            if score < best_score:
                best_score = score
                best_match = lanelet_id
                best_lateral_offset = lateral_offset
                best_heading_error = heading_error

        return best_match, best_lateral_offset, best_heading_error

    def find_candidate_lanelets(self, pose, search_radius):
        """Find lanelets within search radius"""
        # Query KD-tree
        indices = self.kdtree.query_ball_point(pose, search_radius)

        # Map indices back to lanelet IDs
        candidate_lanelets = set()
        # ... (implementation to map point indices to lanelet IDs)

        return list(candidate_lanelets)

    def score_lanelet_match(self, lanelet_id, pose, heading):
        """
        Score how well pose matches lanelet

        Returns:
            score: Lower is better
            lateral_offset: Distance from centerline
            heading_error: Heading difference
        """
        centerline = self.hd_map['centerlines'][lanelet_id]

        # Find closest point on centerline
        min_dist = float('inf')
        closest_segment_idx = 0

        for i in range(len(centerline) - 1):
            p1 = np.array(centerline[i][:2])
            p2 = np.array(centerline[i+1][:2])

            # Project pose onto segment
            segment = p2 - p1
            to_pose = pose - p1

            t = np.clip(np.dot(to_pose, segment) / np.dot(segment, segment), 0, 1)
            projection = p1 + t * segment

            dist = np.linalg.norm(pose - projection)

            if dist < min_dist:
                min_dist = dist
                closest_segment_idx = i

        lateral_offset = min_dist

        # Calculate heading error
        p1 = np.array(centerline[closest_segment_idx][:2])
        p2 = np.array(centerline[closest_segment_idx + 1][:2])
        segment_heading = np.arctan2(p2[1] - p1[1], p2[0] - p1[0])

        heading_error = self.normalize_angle(heading - segment_heading)

        # Combined score
        score = lateral_offset + abs(heading_error) * 2.0

        return score, lateral_offset, heading_error

    def normalize_angle(self, angle):
        """Normalize angle to [-pi, pi]"""
        while angle > np.pi:
            angle -= 2 * np.pi
        while angle < -np.pi:
            angle += 2 * np.pi
        return angle
```

## Localization Accuracy Requirements

| Autonomy Level | Lateral Accuracy | Longitudinal Accuracy | Update Rate |
|----------------|------------------|------------------------|-------------|
| **L2 (ADAS)** | < 0.5m | < 2m | 10 Hz |
| **L3** | < 0.3m | < 1m | 20 Hz |
| **L4** | < 0.1m | < 0.5m | 50 Hz |
| **L5** | < 0.05m | < 0.2m | 50-100 Hz |

## Related Skills

- sensor-fusion-perception.md
- path-planning-control.md
- adas-features-implementation.md
