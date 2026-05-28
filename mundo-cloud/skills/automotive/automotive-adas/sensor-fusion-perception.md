# Sensor Fusion & Perception

## Overview

Multi-sensor fusion combining camera, radar, lidar, and ultrasonic sensors for robust environmental perception in ADAS and autonomous driving. Covers Kalman filters (EKF, UKF), particle filters, coordinate transformations, time synchronization, and early/late fusion strategies.

## Sensor Suite Architecture

### Typical L2-L5 Sensor Configuration

```
Vehicle Coordinate System (ISO 8855)
──────────────────────────────────────────
                  Front (X+)
                     ▲
        Camera ──────┼────── Camera
      (Wide FOV)     │     (Tele FOV)
                     │
    Radar ───────────┼─────────── Radar
   (77GHz)           │            (77GHz)
   Long Range        │         Long Range
                     │
        Lidar ───────┼─────── Lidar
       (128 Ch)      │        (128 Ch)
                     │
    Ultrasonic array (12-16 sensors)
   ──────────────────┼────────────────────
                     │
                Left (Y+)
```

### Sensor Characteristics Table

| Sensor | Range | FOV | Resolution | Weather | Velocity | Cost |
|--------|-------|-----|------------|---------|----------|------|
| **Camera** | 150m | 120° H | 0.1° | Poor | No | $ |
| **Radar** | 250m | 30° H | 1-2° | Excellent | Yes (Doppler) | $$ |
| **Lidar** | 200m | 360° | 0.1-0.2° | Poor-Medium | No | $$$$ |
| **Ultrasonic** | 5m | 120° | N/A | Excellent | No | $ |

## Fusion Architectures

### 1. Early Fusion (Raw Data Level)

```python
import numpy as np
from scipy.ndimage import convolve

class EarlyFusion:
    """
    Fuse raw sensor data before object detection
    Used for complementary sensors (camera + lidar for depth)
    """

    def fuse_camera_lidar(self, camera_image, lidar_pointcloud, calibration):
        """
        Project lidar points onto camera image to create RGB-D

        Args:
            camera_image: (H, W, 3) RGB image
            lidar_pointcloud: (N, 4) [x, y, z, intensity]
            calibration: Camera-Lidar extrinsic calibration

        Returns:
            rgbd_image: (H, W, 4) RGB + Depth
        """
        H, W = camera_image.shape[:2]
        depth_map = np.zeros((H, W), dtype=np.float32)

        # Project lidar points to camera coordinates
        points_cam = self.transform_to_camera(lidar_pointcloud[:, :3], calibration)

        # Filter points in front of camera
        mask = points_cam[:, 2] > 0
        points_cam = points_cam[mask]

        # Project to image plane
        pixels = self.project_to_image(points_cam, calibration.K)

        # Valid pixels
        valid = (pixels[:, 0] >= 0) & (pixels[:, 0] < W) & \
                (pixels[:, 1] >= 0) & (pixels[:, 1] < H)

        pixels = pixels[valid].astype(int)
        depths = points_cam[valid, 2]

        # Fill depth map (handle occlusions by keeping closest)
        for (u, v), d in zip(pixels, depths):
            if depth_map[v, u] == 0 or d < depth_map[v, u]:
                depth_map[v, u] = d

        # Inpaint missing depth values
        depth_map = self.inpaint_depth(depth_map)

        # Combine RGB + D
        rgbd = np.dstack([camera_image, depth_map])

        return rgbd

    def transform_to_camera(self, points, calibration):
        """Transform lidar points to camera coordinate system"""
        # Homogeneous coordinates
        ones = np.ones((points.shape[0], 1))
        points_h = np.hstack([points, ones])

        # Apply extrinsic transformation
        points_cam = (calibration.T_cam_lidar @ points_h.T).T

        return points_cam[:, :3]

    def project_to_image(self, points_cam, K):
        """Project 3D camera points to 2D image pixels"""
        # K is intrinsic matrix [3x3]
        pixels_h = (K @ points_cam.T).T
        pixels = pixels_h[:, :2] / pixels_h[:, 2:3]
        return pixels

    def inpaint_depth(self, depth_map, kernel_size=5):
        """Inpaint missing depth values using convolution"""
        mask = depth_map > 0
        kernel = np.ones((kernel_size, kernel_size)) / (kernel_size ** 2)

        # Iterative inpainting
        inpainted = depth_map.copy()
        for _ in range(3):
            inpainted = convolve(inpainted, kernel, mode='constant')
            inpainted[mask] = depth_map[mask]  # Keep original valid values

        return inpainted
```

### 2. Mid-Level Fusion (Feature Level)

```cpp
// Feature-level fusion: combine object detections from different sensors
#include <Eigen/Dense>
#include <vector>
#include <algorithm>

struct Detection {
    Eigen::Vector3d position;      // [x, y, z] in vehicle frame
    Eigen::Vector3d velocity;      // [vx, vy, vz]
    Eigen::Vector3d dimensions;    // [length, width, height]
    std::string object_class;      // "car", "pedestrian", etc.
    double confidence;             // 0-1
    std::string sensor_source;     // "camera", "radar", "lidar"
    Eigen::Matrix3d covariance;    // Position uncertainty
};

class MidLevelFusion {
public:
    std::vector<Detection> fuse_detections(
        const std::vector<Detection>& camera_detections,
        const std::vector<Detection>& radar_detections,
        const std::vector<Detection>& lidar_detections)
    {
        // Combine all detections
        std::vector<Detection> all_detections;
        all_detections.insert(all_detections.end(),
                            camera_detections.begin(), camera_detections.end());
        all_detections.insert(all_detections.end(),
                            radar_detections.begin(), radar_detections.end());
        all_detections.insert(all_detections.end(),
                            lidar_detections.begin(), lidar_detections.end());

        // Cluster detections that refer to same object
        std::vector<std::vector<Detection>> clusters = cluster_detections(all_detections);

        // Fuse each cluster into single detection
        std::vector<Detection> fused_detections;
        for (const auto& cluster : clusters) {
            if (!cluster.empty()) {
                fused_detections.push_back(fuse_cluster(cluster));
            }
        }

        return fused_detections;
    }

private:
    std::vector<std::vector<Detection>> cluster_detections(
        const std::vector<Detection>& detections)
    {
        const double DISTANCE_THRESHOLD = 2.0;  // 2 meters

        std::vector<std::vector<Detection>> clusters;
        std::vector<bool> assigned(detections.size(), false);

        for (size_t i = 0; i < detections.size(); ++i) {
            if (assigned[i]) continue;

            std::vector<Detection> cluster;
            cluster.push_back(detections[i]);
            assigned[i] = true;

            // Find nearby detections
            for (size_t j = i + 1; j < detections.size(); ++j) {
                if (assigned[j]) continue;

                double dist = (detections[i].position - detections[j].position).norm();

                if (dist < DISTANCE_THRESHOLD) {
                    // Check if same object type
                    if (is_compatible_class(detections[i].object_class,
                                          detections[j].object_class)) {
                        cluster.push_back(detections[j]);
                        assigned[j] = true;
                    }
                }
            }

            clusters.push_back(cluster);
        }

        return clusters;
    }

    Detection fuse_cluster(const std::vector<Detection>& cluster) {
        Detection fused;

        // Calculate weighted average based on confidence
        double total_weight = 0.0;
        Eigen::Vector3d weighted_position = Eigen::Vector3d::Zero();
        Eigen::Vector3d weighted_velocity = Eigen::Vector3d::Zero();

        for (const auto& det : cluster) {
            // Weight by confidence and sensor reliability
            double weight = det.confidence * get_sensor_weight(det.sensor_source);
            total_weight += weight;

            weighted_position += weight * det.position;
            weighted_velocity += weight * det.velocity;
        }

        fused.position = weighted_position / total_weight;
        fused.velocity = weighted_velocity / total_weight;

        // Take highest confidence classification
        double max_conf = 0.0;
        for (const auto& det : cluster) {
            if (det.confidence > max_conf) {
                max_conf = det.confidence;
                fused.object_class = det.object_class;
                fused.dimensions = det.dimensions;
            }
        }

        fused.confidence = std::min(1.0, max_conf * 1.2);  // Boost confidence for fused

        // Covariance intersection for combined uncertainty
        fused.covariance = covariance_intersection(cluster);

        return fused;
    }

    double get_sensor_weight(const std::string& sensor) {
        // Sensor reliability weights (can be adaptive based on conditions)
        if (sensor == "lidar") return 1.0;
        if (sensor == "radar") return 0.8;
        if (sensor == "camera") return 0.7;
        return 0.5;
    }

    bool is_compatible_class(const std::string& class1, const std::string& class2) {
        // Check if two classifications are compatible
        if (class1 == class2) return true;

        // Allow some flexibility (e.g., "car" and "vehicle")
        std::vector<std::string> vehicle_types = {"car", "truck", "van", "vehicle"};

        bool is_vehicle1 = std::find(vehicle_types.begin(), vehicle_types.end(), class1)
                          != vehicle_types.end();
        bool is_vehicle2 = std::find(vehicle_types.begin(), vehicle_types.end(), class2)
                          != vehicle_types.end();

        return is_vehicle1 && is_vehicle2;
    }

    Eigen::Matrix3d covariance_intersection(const std::vector<Detection>& cluster) {
        // Covariance intersection for combining uncertain estimates
        Eigen::Matrix3d P_inv = Eigen::Matrix3d::Zero();

        for (const auto& det : cluster) {
            P_inv += det.covariance.inverse();
        }

        return P_inv.inverse();
    }
};
```

### 3. Late Fusion (Track-to-Track)

```cpp
#include <Eigen/Dense>
#include <vector>

struct Track {
    int id;
    Eigen::Vector4d state;         // [x, y, vx, vy]
    Eigen::Matrix4d covariance;
    std::string object_class;
    double confidence;
    std::string source_sensor;
    uint64_t timestamp_us;
};

class LateFusion {
public:
    std::vector<Track> fuse_tracks(
        const std::vector<Track>& camera_tracks,
        const std::vector<Track>& radar_tracks,
        const std::vector<Track>& lidar_tracks)
    {
        std::vector<Track> all_tracks;
        all_tracks.insert(all_tracks.end(), camera_tracks.begin(), camera_tracks.end());
        all_tracks.insert(all_tracks.end(), radar_tracks.begin(), radar_tracks.end());
        all_tracks.insert(all_tracks.end(), lidar_tracks.begin(), lidar_tracks.end());

        // Track-to-track association
        auto associations = associate_tracks(all_tracks);

        // Fuse associated tracks
        std::vector<Track> fused_tracks;
        for (const auto& group : associations) {
            fused_tracks.push_back(fuse_track_group(group));
        }

        return fused_tracks;
    }

private:
    std::vector<std::vector<Track>> associate_tracks(const std::vector<Track>& tracks) {
        const double MAHALANOBIS_THRESHOLD = 9.21;  // Chi-square 99% @ 4D

        std::vector<std::vector<Track>> groups;
        std::vector<bool> assigned(tracks.size(), false);

        for (size_t i = 0; i < tracks.size(); ++i) {
            if (assigned[i]) continue;

            std::vector<Track> group;
            group.push_back(tracks[i]);
            assigned[i] = true;

            for (size_t j = i + 1; j < tracks.size(); ++j) {
                if (assigned[j]) continue;

                // Mahalanobis distance between tracks
                double dist = mahalanobis_distance(tracks[i], tracks[j]);

                if (dist < MAHALANOBIS_THRESHOLD) {
                    group.push_back(tracks[j]);
                    assigned[j] = true;
                }
            }

            groups.push_back(group);
        }

        return groups;
    }

    double mahalanobis_distance(const Track& t1, const Track& t2) {
        Eigen::Vector4d diff = t1.state - t2.state;
        Eigen::Matrix4d S = t1.covariance + t2.covariance;

        return std::sqrt(diff.transpose() * S.inverse() * diff);
    }

    Track fuse_track_group(const std::vector<Track>& group) {
        // Covariance intersection for track fusion
        Track fused;

        Eigen::Matrix4d P_inv = Eigen::Matrix4d::Zero();
        Eigen::Vector4d weighted_state = Eigen::Vector4d::Zero();

        for (const auto& track : group) {
            Eigen::Matrix4d P_inv_i = track.covariance.inverse();
            P_inv += P_inv_i;
            weighted_state += P_inv_i * track.state;
        }

        fused.covariance = P_inv.inverse();
        fused.state = fused.covariance * weighted_state;

        // Take highest confidence classification
        double max_conf = 0.0;
        for (const auto& track : group) {
            if (track.confidence > max_conf) {
                max_conf = track.confidence;
                fused.object_class = track.object_class;
                fused.source_sensor = track.source_sensor;
            }
        }

        fused.confidence = max_conf;
        fused.id = group[0].id;  // Use first track ID

        return fused;
    }
};
```

## Extended Kalman Filter (EKF)

### Complete EKF Implementation for Multi-Sensor Tracking

```cpp
#include <Eigen/Dense>
#include <cmath>

class ExtendedKalmanFilter {
public:
    ExtendedKalmanFilter() {
        // Initialize state: [x, y, vx, vy, ax, ay]
        state_ = Eigen::VectorXd::Zero(6);

        // Initialize covariance
        covariance_ = Eigen::MatrixXd::Identity(6, 6) * 1000.0;

        // Process noise
        Q_ = Eigen::MatrixXd::Identity(6, 6);
        Q_(0, 0) = 0.1;  // Position noise
        Q_(1, 1) = 0.1;
        Q_(2, 2) = 1.0;  // Velocity noise
        Q_(3, 3) = 1.0;
        Q_(4, 4) = 2.0;  // Acceleration noise
        Q_(5, 5) = 2.0;

        // Measurement noise covariances
        R_camera_ = Eigen::Matrix2d::Identity() * 0.5;      // 0.5m position uncertainty
        R_radar_ = Eigen::Matrix3d::Identity();
        R_radar_(0, 0) = 0.3;  // Range: 0.3m
        R_radar_(1, 1) = 0.5;  // Range rate: 0.5 m/s
        R_radar_(2, 2) = 0.02; // Azimuth: 0.02 rad

        R_lidar_ = Eigen::Matrix3d::Identity() * 0.2;       // 0.2m 3D position
    }

    void predict(double dt) {
        // State transition matrix F (constant acceleration model)
        Eigen::MatrixXd F = Eigen::MatrixXd::Identity(6, 6);
        F(0, 2) = dt;
        F(0, 4) = 0.5 * dt * dt;
        F(1, 3) = dt;
        F(1, 5) = 0.5 * dt * dt;
        F(2, 4) = dt;
        F(3, 5) = dt;

        // Predict state
        state_ = F * state_;

        // Predict covariance
        covariance_ = F * covariance_ * F.transpose() + Q_;
    }

    void update_camera(const Eigen::Vector2d& z_cam) {
        // Camera measurement model: H = [1 0 0 0 0 0]
        //                               [0 1 0 0 0 0]
        Eigen::MatrixXd H = Eigen::MatrixXd::Zero(2, 6);
        H(0, 0) = 1.0;
        H(1, 1) = 1.0;

        // Predicted measurement
        Eigen::Vector2d z_pred = H * state_;

        // Innovation
        Eigen::Vector2d y = z_cam - z_pred;

        // Innovation covariance
        Eigen::Matrix2d S = H * covariance_ * H.transpose() + R_camera_;

        // Kalman gain
        Eigen::MatrixXd K = covariance_ * H.transpose() * S.inverse();

        // Update state
        state_ = state_ + K * y;

        // Update covariance
        Eigen::MatrixXd I = Eigen::MatrixXd::Identity(6, 6);
        covariance_ = (I - K * H) * covariance_;
    }

    void update_radar(const Eigen::Vector3d& z_radar) {
        // Radar measurement: [range, range_rate, azimuth]
        // Non-linear measurement model - need Jacobian

        double px = state_(0);
        double py = state_(1);
        double vx = state_(2);
        double vy = state_(3);

        // Predicted measurement h(x)
        double rho = std::sqrt(px*px + py*py);
        double phi = std::atan2(py, px);
        double rho_dot = (px*vx + py*vy) / rho;

        Eigen::Vector3d z_pred;
        z_pred << rho, rho_dot, phi;

        // Measurement Jacobian H
        Eigen::MatrixXd H = Eigen::MatrixXd::Zero(3, 6);

        if (rho > 0.001) {  // Avoid division by zero
            H(0, 0) = px / rho;
            H(0, 1) = py / rho;

            H(1, 0) = vx / rho - (px * (px*vx + py*vy)) / (rho*rho*rho);
            H(1, 1) = vy / rho - (py * (px*vx + py*vy)) / (rho*rho*rho);
            H(1, 2) = px / rho;
            H(1, 3) = py / rho;

            H(2, 0) = -py / (rho*rho);
            H(2, 1) = px / (rho*rho);
        }

        // Innovation
        Eigen::Vector3d y = z_radar - z_pred;

        // Normalize angle to [-π, π]
        while (y(2) > M_PI) y(2) -= 2.0 * M_PI;
        while (y(2) < -M_PI) y(2) += 2.0 * M_PI;

        // Innovation covariance
        Eigen::Matrix3d S = H * covariance_ * H.transpose() + R_radar_;

        // Kalman gain
        Eigen::MatrixXd K = covariance_ * H.transpose() * S.inverse();

        // Update
        state_ = state_ + K * y;

        Eigen::MatrixXd I = Eigen::MatrixXd::Identity(6, 6);
        covariance_ = (I - K * H) * covariance_;
    }

    void update_lidar(const Eigen::Vector3d& z_lidar) {
        // Lidar measurement: [x, y, z] (3D position)
        Eigen::MatrixXd H = Eigen::MatrixXd::Zero(3, 6);
        H(0, 0) = 1.0;
        H(1, 1) = 1.0;
        // Assume z is observed but not in state (could extend state if needed)

        // For 2D tracking, only use x, y
        Eigen::Vector2d z_lidar_2d = z_lidar.head(2);
        Eigen::MatrixXd H_2d = H.topRows(2);

        Eigen::Vector2d z_pred = H_2d * state_;
        Eigen::Vector2d y = z_lidar_2d - z_pred;

        Eigen::Matrix2d S = H_2d * covariance_ * H_2d.transpose()
                          + R_lidar_.topLeftCorner(2, 2);

        Eigen::MatrixXd K = covariance_ * H_2d.transpose() * S.inverse();

        state_ = state_ + K * y;

        Eigen::MatrixXd I = Eigen::MatrixXd::Identity(6, 6);
        covariance_ = (I - K * H_2d) * covariance_;
    }

    Eigen::VectorXd get_state() const { return state_; }
    Eigen::MatrixXd get_covariance() const { return covariance_; }

private:
    Eigen::VectorXd state_;         // State vector [x, y, vx, vy, ax, ay]
    Eigen::MatrixXd covariance_;    // State covariance
    Eigen::MatrixXd Q_;             // Process noise covariance
    Eigen::Matrix2d R_camera_;      // Camera measurement noise
    Eigen::Matrix3d R_radar_;       // Radar measurement noise
    Eigen::Matrix3d R_lidar_;       // Lidar measurement noise
};
```

## Unscented Kalman Filter (UKF)

```cpp
#include <Eigen/Dense>
#include <vector>

class UnscentedKalmanFilter {
public:
    UnscentedKalmanFilter(int n_states, int n_aug)
        : n_x_(n_states), n_aug_(n_aug)
    {
        lambda_ = 3 - n_aug_;
        n_sigma_ = 2 * n_aug_ + 1;

        // Weights for sigma points
        weights_ = Eigen::VectorXd(n_sigma_);
        weights_(0) = lambda_ / (lambda_ + n_aug_);
        for (int i = 1; i < n_sigma_; ++i) {
            weights_(i) = 0.5 / (lambda_ + n_aug_);
        }

        // Initialize state and covariance
        x_ = Eigen::VectorXd::Zero(n_x_);
        P_ = Eigen::MatrixXd::Identity(n_x_, n_x_);
    }

    void predict(double dt) {
        // Create augmented sigma points
        Eigen::VectorXd x_aug = Eigen::VectorXd::Zero(n_aug_);
        x_aug.head(n_x_) = x_;

        Eigen::MatrixXd P_aug = Eigen::MatrixXd::Zero(n_aug_, n_aug_);
        P_aug.topLeftCorner(n_x_, n_x_) = P_;
        P_aug(n_x_, n_x_) = 1.0;  // Process noise variance
        P_aug(n_x_ + 1, n_x_ + 1) = 1.0;

        Eigen::MatrixXd Xsig_aug = generate_sigma_points(x_aug, P_aug);

        // Predict sigma points
        Eigen::MatrixXd Xsig_pred = Eigen::MatrixXd::Zero(n_x_, n_sigma_);
        for (int i = 0; i < n_sigma_; ++i) {
            Xsig_pred.col(i) = process_model(Xsig_aug.col(i), dt);
        }

        // Predict mean and covariance
        x_ = Xsig_pred * weights_;

        P_.setZero();
        for (int i = 0; i < n_sigma_; ++i) {
            Eigen::VectorXd x_diff = Xsig_pred.col(i) - x_;
            P_ += weights_(i) * x_diff * x_diff.transpose();
        }

        Xsig_pred_ = Xsig_pred;  // Store for update
    }

    void update_radar(const Eigen::Vector3d& z) {
        int n_z = 3;  // Radar measurement dimension

        // Transform sigma points to measurement space
        Eigen::MatrixXd Zsig = Eigen::MatrixXd::Zero(n_z, n_sigma_);
        for (int i = 0; i < n_sigma_; ++i) {
            Zsig.col(i) = measurement_model_radar(Xsig_pred_.col(i));
        }

        // Predicted measurement mean
        Eigen::Vector3d z_pred = Zsig * weights_;

        // Measurement covariance S
        Eigen::Matrix3d S = Eigen::Matrix3d::Zero();
        for (int i = 0; i < n_sigma_; ++i) {
            Eigen::Vector3d z_diff = Zsig.col(i) - z_pred;
            S += weights_(i) * z_diff * z_diff.transpose();
        }

        // Add measurement noise
        Eigen::Matrix3d R = Eigen::Matrix3d::Identity();
        R(0, 0) = 0.3;  // Range
        R(1, 1) = 0.5;  // Range rate
        R(2, 2) = 0.02; // Azimuth
        S += R;

        // Cross-correlation matrix
        Eigen::MatrixXd Tc = Eigen::MatrixXd::Zero(n_x_, n_z);
        for (int i = 0; i < n_sigma_; ++i) {
            Eigen::VectorXd x_diff = Xsig_pred_.col(i) - x_;
            Eigen::Vector3d z_diff = Zsig.col(i) - z_pred;
            Tc += weights_(i) * x_diff * z_diff.transpose();
        }

        // Kalman gain
        Eigen::MatrixXd K = Tc * S.inverse();

        // Update state
        Eigen::Vector3d z_diff = z - z_pred;
        x_ = x_ + K * z_diff;

        // Update covariance
        P_ = P_ - K * S * K.transpose();
    }

private:
    int n_x_;                       // State dimension
    int n_aug_;                     // Augmented dimension
    int n_sigma_;                   // Number of sigma points
    double lambda_;                 // Sigma point spreading parameter
    Eigen::VectorXd weights_;       // Weights for sigma points
    Eigen::VectorXd x_;             // State vector
    Eigen::MatrixXd P_;             // State covariance
    Eigen::MatrixXd Xsig_pred_;     // Predicted sigma points

    Eigen::MatrixXd generate_sigma_points(const Eigen::VectorXd& x,
                                         const Eigen::MatrixXd& P) {
        int n = x.size();
        Eigen::MatrixXd Xsig = Eigen::MatrixXd::Zero(n, 2 * n + 1);

        // Cholesky decomposition
        Eigen::MatrixXd L = P.llt().matrixL();

        // Central sigma point
        Xsig.col(0) = x;

        // Other sigma points
        double coef = std::sqrt(lambda_ + n);
        for (int i = 0; i < n; ++i) {
            Xsig.col(i + 1) = x + coef * L.col(i);
            Xsig.col(i + 1 + n) = x - coef * L.col(i);
        }

        return Xsig;
    }

    Eigen::VectorXd process_model(const Eigen::VectorXd& x_aug, double dt) {
        // Constant turn rate and velocity (CTRV) model
        double px = x_aug(0);
        double py = x_aug(1);
        double v = x_aug(2);
        double yaw = x_aug(3);
        double yawd = x_aug(4);
        double nu_a = x_aug(5);  // Process noise acceleration
        double nu_yawdd = x_aug(6);  // Process noise yaw acceleration

        Eigen::VectorXd x_pred = Eigen::VectorXd::Zero(n_x_);

        // Avoid division by zero
        if (std::abs(yawd) > 0.001) {
            x_pred(0) = px + v/yawd * (std::sin(yaw + yawd*dt) - std::sin(yaw));
            x_pred(1) = py + v/yawd * (-std::cos(yaw + yawd*dt) + std::cos(yaw));
        } else {
            x_pred(0) = px + v * std::cos(yaw) * dt;
            x_pred(1) = py + v * std::sin(yaw) * dt;
        }

        x_pred(2) = v;
        x_pred(3) = yaw + yawd * dt;
        x_pred(4) = yawd;

        // Add process noise
        x_pred(0) += 0.5 * dt * dt * std::cos(yaw) * nu_a;
        x_pred(1) += 0.5 * dt * dt * std::sin(yaw) * nu_a;
        x_pred(2) += dt * nu_a;
        x_pred(3) += 0.5 * dt * dt * nu_yawdd;
        x_pred(4) += dt * nu_yawdd;

        return x_pred;
    }

    Eigen::Vector3d measurement_model_radar(const Eigen::VectorXd& x) {
        double px = x(0);
        double py = x(1);
        double v = x(2);
        double yaw = x(3);

        double rho = std::sqrt(px*px + py*py);
        double phi = std::atan2(py, px);
        double rho_dot = (px * std::cos(yaw) * v + py * std::sin(yaw) * v) / rho;

        Eigen::Vector3d z;
        z << rho, rho_dot, phi;
        return z;
    }
};
```

## Time Synchronization

```cpp
#include <chrono>
#include <map>
#include <queue>

class SensorTimeSynchronizer {
public:
    struct SensorData {
        uint64_t timestamp_us;
        std::string sensor_id;
        // ... sensor-specific data
    };

    SensorTimeSynchronizer(uint64_t sync_window_us = 10000)  // 10ms window
        : sync_window_us_(sync_window_us) {}

    void add_measurement(const SensorData& data) {
        sensor_buffers_[data.sensor_id].push(data);
    }

    std::map<std::string, SensorData> get_synchronized_frame() {
        std::map<std::string, SensorData> synced_frame;

        if (sensor_buffers_.empty()) return synced_frame;

        // Find reference timestamp (usually camera frame time)
        uint64_t ref_time = get_reference_timestamp();

        // Extract measurements closest to reference time
        for (auto& [sensor_id, buffer] : sensor_buffers_) {
            while (!buffer.empty()) {
                auto& data = buffer.front();

                // Check if within sync window
                int64_t time_diff = std::abs(
                    static_cast<int64_t>(data.timestamp_us) -
                    static_cast<int64_t>(ref_time)
                );

                if (time_diff < sync_window_us_) {
                    synced_frame[sensor_id] = data;
                    buffer.pop();
                    break;
                }

                // Too old, discard
                if (data.timestamp_us < ref_time - sync_window_us_) {
                    buffer.pop();
                } else {
                    break;  // Future measurement, wait
                }
            }
        }

        return synced_frame;
    }

private:
    uint64_t sync_window_us_;
    std::map<std::string, std::queue<SensorData>> sensor_buffers_;

    uint64_t get_reference_timestamp() {
        // Use camera timestamp as reference (usually most accurate)
        if (sensor_buffers_.count("camera") &&
            !sensor_buffers_["camera"].empty()) {
            return sensor_buffers_["camera"].front().timestamp_us;
        }

        // Fallback to first available sensor
        for (const auto& [id, buffer] : sensor_buffers_) {
            if (!buffer.empty()) {
                return buffer.front().timestamp_us;
            }
        }

        return 0;
    }
};
```

## Performance Metrics

### Key Performance Indicators

- **Fusion Latency**: < 50ms end-to-end
- **Position Accuracy**: < 0.3m (95th percentile)
- **Velocity Accuracy**: < 0.5 m/s (95th percentile)
- **False Positive Rate**: < 0.01 per km
- **Miss Rate**: < 0.001 for safety-critical objects

## Standards Compliance

- **ISO 26262**: ASIL-D for safety-critical fusion
- **ISO 21448 (SOTIF)**: Scenario-based validation
- **ISO 23150**: Augmented reality coordination
- **SAE J3016**: Levels of automation (L0-L5)

## Related Skills

- camera-processing-vision.md
- radar-lidar-processing.md
- path-planning-control.md
- hd-maps-localization.md
