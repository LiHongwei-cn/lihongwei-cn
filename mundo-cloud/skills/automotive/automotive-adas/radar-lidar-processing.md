# Radar & Lidar Processing for ADAS

## Overview

Radar signal processing (FMCW, chirp, range-Doppler), lidar point cloud processing, SLAM, occupancy grids, and clustering algorithms for ADAS perception.

## Radar Processing

### FMCW Radar Signal Processing

```matlab
% FMCW Radar Parameter Setup
c = 3e8;                    % Speed of light (m/s)
fc = 77e9;                  % Carrier frequency (77 GHz)
B = 150e6;                  % Bandwidth (150 MHz)
T_chirp = 40e-6;            % Chirp duration (40 μs)
slope = B / T_chirp;        % Chirp slope (Hz/s)

% Range resolution
range_res = c / (2 * B);    % ~1 meter

% Maximum range
max_range = c * T_chirp / (4 * B);  % ~40 meters (unambiguous)

% Doppler resolution
num_chirps = 256;
doppler_res = c / (2 * fc * T_chirp * num_chirps);

fprintf('Range Resolution: %.2f m\n', range_res);
fprintf('Velocity Resolution: %.2f m/s\n', doppler_res);
```

```cpp
#include <vector>
#include <complex>
#include <Eigen/Dense>
#include <fftw3.h>

class FMCWRadarProcessor {
public:
    struct RadarConfig {
        double carrier_freq = 77e9;     // 77 GHz
        double bandwidth = 150e6;       // 150 MHz
        double chirp_duration = 40e-6;  // 40 μs
        int num_samples = 256;
        int num_chirps = 256;
        int num_rx_antennas = 4;
        double sample_rate = 10e6;      // 10 MHz ADC
    };

    struct Detection {
        double range;           // meters
        double velocity;        // m/s
        double angle;           // radians
        double rcs;             // radar cross section (dBsm)
        double snr;             // signal-to-noise ratio (dB)
    };

    FMCWRadarProcessor(const RadarConfig& config) : config_(config) {
        range_res_ = SPEED_OF_LIGHT / (2 * config_.bandwidth);
        max_range_ = SPEED_OF_LIGHT * config_.chirp_duration / (4 * config_.bandwidth);
        vel_res_ = SPEED_OF_LIGHT / (2 * config_.carrier_freq *
                                     config_.chirp_duration * config_.num_chirps);

        // Allocate FFTW plans
        setup_fft_plans();
    }

    std::vector<Detection> process_frame(const std::vector<std::vector<std::complex<double>>>& raw_data) {
        // raw_data: [num_chirps][num_samples] complex samples from ADC

        // Step 1: Range FFT (per chirp)
        auto range_fft = compute_range_fft(raw_data);

        // Step 2: Doppler FFT (across chirps)
        auto range_doppler = compute_doppler_fft(range_fft);

        // Step 3: CFAR detection (Constant False Alarm Rate)
        auto detections_2d = cfar_detection(range_doppler);

        // Step 4: Angle estimation (using multiple RX antennas)
        auto detections_3d = estimate_angles(detections_2d, raw_data);

        return detections_3d;
    }

private:
    RadarConfig config_;
    double range_res_;
    double max_range_;
    double vel_res_;
    static constexpr double SPEED_OF_LIGHT = 3e8;

    fftw_plan fft_plan_range_;
    fftw_plan fft_plan_doppler_;

    void setup_fft_plans() {
        // Allocate and plan FFTs for efficiency
        fftw_complex *in = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * config_.num_samples);
        fftw_complex *out = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * config_.num_samples);

        fft_plan_range_ = fftw_plan_dft_1d(config_.num_samples, in, out,
                                          FFTW_FORWARD, FFTW_ESTIMATE);

        fftw_complex *in_doppler = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * config_.num_chirps);
        fftw_complex *out_doppler = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * config_.num_chirps);

        fft_plan_doppler_ = fftw_plan_dft_1d(config_.num_chirps, in_doppler, out_doppler,
                                            FFTW_FORWARD, FFTW_ESTIMATE);
    }

    Eigen::MatrixXcd compute_range_fft(const std::vector<std::vector<std::complex<double>>>& data) {
        int num_chirps = data.size();
        int num_samples = data[0].size();

        Eigen::MatrixXcd range_fft(num_chirps, num_samples);

        for (int chirp = 0; chirp < num_chirps; ++chirp) {
            // Apply window (Hanning)
            std::vector<std::complex<double>> windowed(num_samples);
            for (int i = 0; i < num_samples; ++i) {
                double window = 0.5 * (1 - std::cos(2 * M_PI * i / num_samples));
                windowed[i] = data[chirp][i] * window;
            }

            // Compute FFT
            fftw_complex *in = reinterpret_cast<fftw_complex*>(windowed.data());
            fftw_complex *out = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * num_samples);

            fftw_execute_dft(fft_plan_range_, in, out);

            for (int i = 0; i < num_samples; ++i) {
                range_fft(chirp, i) = std::complex<double>(out[i][0], out[i][1]);
            }

            fftw_free(out);
        }

        return range_fft;
    }

    Eigen::MatrixXcd compute_doppler_fft(const Eigen::MatrixXcd& range_fft) {
        int num_chirps = range_fft.rows();
        int num_range_bins = range_fft.cols();

        Eigen::MatrixXcd range_doppler(num_chirps, num_range_bins);

        for (int range_bin = 0; range_bin < num_range_bins; ++range_bin) {
            // Extract column (doppler dimension)
            std::vector<std::complex<double>> doppler_data(num_chirps);
            for (int chirp = 0; chirp < num_chirps; ++chirp) {
                doppler_data[chirp] = range_fft(chirp, range_bin);
            }

            // Apply window
            for (int i = 0; i < num_chirps; ++i) {
                double window = 0.5 * (1 - std::cos(2 * M_PI * i / num_chirps));
                doppler_data[i] *= window;
            }

            // Compute FFT
            fftw_complex *in = reinterpret_cast<fftw_complex*>(doppler_data.data());
            fftw_complex *out = (fftw_complex*)fftw_malloc(sizeof(fftw_complex) * num_chirps);

            fftw_execute_dft(fft_plan_doppler_, in, out);

            for (int i = 0; i < num_chirps; ++i) {
                range_doppler(i, range_bin) = std::complex<double>(out[i][0], out[i][1]);
            }

            fftw_free(out);
        }

        return range_doppler;
    }

    std::vector<Detection> cfar_detection(const Eigen::MatrixXcd& range_doppler) {
        // CA-CFAR (Cell Averaging - Constant False Alarm Rate)
        const int guard_cells = 4;
        const int training_cells = 12;
        const double pfa = 1e-6;  // Probability of false alarm

        // CFAR threshold factor
        double alpha = training_cells * (std::pow(pfa, -1.0 / training_cells) - 1);

        std::vector<Detection> detections;

        int num_doppler = range_doppler.rows();
        int num_range = range_doppler.cols();

        // Compute magnitude squared (power)
        Eigen::MatrixXd power(num_doppler, num_range);
        for (int i = 0; i < num_doppler; ++i) {
            for (int j = 0; j < num_range; ++j) {
                power(i, j) = std::norm(range_doppler(i, j));
            }
        }

        // 2D CFAR detection
        for (int d = guard_cells + training_cells; d < num_doppler - guard_cells - training_cells; ++d) {
            for (int r = guard_cells + training_cells; r < num_range - guard_cells - training_cells; ++r) {
                // Compute noise estimate (average of training cells)
                double noise_sum = 0.0;
                int count = 0;

                for (int dd = -training_cells - guard_cells; dd <= training_cells + guard_cells; ++dd) {
                    for (int rr = -training_cells - guard_cells; rr <= training_cells + guard_cells; ++rr) {
                        if (std::abs(dd) > guard_cells || std::abs(rr) > guard_cells) {
                            noise_sum += power(d + dd, r + rr);
                            count++;
                        }
                    }
                }

                double noise_level = noise_sum / count;
                double threshold = alpha * noise_level;

                // Detection
                if (power(d, r) > threshold) {
                    Detection det;
                    det.range = r * range_res_;
                    det.velocity = (d - num_doppler / 2) * vel_res_;
                    det.snr = 10 * std::log10(power(d, r) / noise_level);

                    // Estimate RCS
                    det.rcs = compute_rcs(power(d, r), det.range);

                    detections.push_back(det);
                }
            }
        }

        return detections;
    }

    std::vector<Detection> estimate_angles(const std::vector<Detection>& detections_2d,
                                          const std::vector<std::vector<std::complex<double>>>& raw_data) {
        // Use MUSIC or beamforming for angle estimation with multiple RX antennas
        std::vector<Detection> detections_3d = detections_2d;

        // For each detection, estimate angle of arrival
        for (auto& det : detections_3d) {
            det.angle = estimate_aoa_music(det, raw_data);
        }

        return detections_3d;
    }

    double estimate_aoa_music(const Detection& det,
                             const std::vector<std::vector<std::complex<double>>>& raw_data) {
        // MUSIC algorithm for angle estimation
        // Simplified: assume uniform linear array

        // Extract signals from all RX antennas for this detection
        // [Implementation of MUSIC algorithm]

        // Placeholder: return 0 angle
        return 0.0;
    }

    double compute_rcs(double power, double range) {
        // Radar equation: RCS estimation
        // RCS = (Power_rx * (4π)^3 * R^4) / (Power_tx * G_tx * G_rx * λ^2)

        // Simplified model
        double lambda = SPEED_OF_LIGHT / config_.carrier_freq;
        double rcs_linear = power * std::pow(range, 4) / std::pow(lambda, 2);
        double rcs_dbsm = 10 * std::log10(rcs_linear);

        return rcs_dbsm;
    }
};
```

## Lidar Point Cloud Processing

### Point Cloud Preprocessing

```cpp
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/filters/passthrough.h>
#include <pcl/segmentation/extract_clusters.h>
#include <pcl/segmentation/sac_segmentation.h>
#include <pcl/filters/extract_indices.h>

class LidarProcessor {
public:
    using PointT = pcl::PointXYZI;
    using PointCloudT = pcl::PointCloud<PointT>;

    LidarProcessor() {
        // Voxel grid filter for downsampling
        voxel_filter_.setLeafSize(0.1f, 0.1f, 0.1f);  // 10cm voxels

        // PassThrough filter for ROI
        pass_filter_x_.setFilterFieldName("x");
        pass_filter_x_.setFilterLimits(0.0, 100.0);  // 0-100m forward

        pass_filter_y_.setFilterFieldName("y");
        pass_filter_y_.setFilterLimits(-25.0, 25.0);  // ±25m lateral

        pass_filter_z_.setFilterFieldName("z");
        pass_filter_z_.setFilterLimits(-2.0, 5.0);    // -2m to 5m height

        // Ground plane segmentation
        ground_segmenter_.setOptimizeCoefficients(true);
        ground_segmenter_.setModelType(pcl::SACMODEL_PLANE);
        ground_segmenter_.setMethodType(pcl::SAC_RANSAC);
        ground_segmenter_.setMaxIterations(100);
        ground_segmenter_.setDistanceThreshold(0.1);  // 10cm

        // Euclidean clustering
        cluster_extractor_.setClusterTolerance(0.5);  // 50cm
        cluster_extractor_.setMinClusterSize(10);
        cluster_extractor_.setMaxClusterSize(10000);
    }

    struct ProcessedCloud {
        PointCloudT::Ptr ground;
        PointCloudT::Ptr obstacles;
        std::vector<PointCloudT::Ptr> clusters;
    };

    ProcessedCloud process(const PointCloudT::Ptr& input_cloud) {
        ProcessedCloud result;

        // Step 1: Downsample
        PointCloudT::Ptr cloud_filtered(new PointCloudT);
        voxel_filter_.setInputCloud(input_cloud);
        voxel_filter_.filter(*cloud_filtered);

        // Step 2: ROI filtering
        pass_filter_x_.setInputCloud(cloud_filtered);
        pass_filter_x_.filter(*cloud_filtered);

        pass_filter_y_.setInputCloud(cloud_filtered);
        pass_filter_y_.filter(*cloud_filtered);

        pass_filter_z_.setInputCloud(cloud_filtered);
        pass_filter_z_.filter(*cloud_filtered);

        // Step 3: Ground plane removal
        auto [ground, obstacles] = remove_ground_plane(cloud_filtered);
        result.ground = ground;
        result.obstacles = obstacles;

        // Step 4: Clustering
        result.clusters = cluster_obstacles(obstacles);

        return result;
    }

private:
    pcl::VoxelGrid<PointT> voxel_filter_;
    pcl::PassThrough<PointT> pass_filter_x_, pass_filter_y_, pass_filter_z_;
    pcl::SACSegmentation<PointT> ground_segmenter_;
    pcl::EuclideanClusterExtraction<PointT> cluster_extractor_;

    std::pair<PointCloudT::Ptr, PointCloudT::Ptr> remove_ground_plane(
        const PointCloudT::Ptr& cloud)
    {
        pcl::ModelCoefficients::Ptr coefficients(new pcl::ModelCoefficients);
        pcl::PointIndices::Ptr inliers(new pcl::PointIndices);

        ground_segmenter_.setInputCloud(cloud);
        ground_segmenter_.segment(*inliers, *coefficients);

        // Extract ground points
        PointCloudT::Ptr ground(new PointCloudT);
        pcl::ExtractIndices<PointT> extract;
        extract.setInputCloud(cloud);
        extract.setIndices(inliers);
        extract.setNegative(false);
        extract.filter(*ground);

        // Extract obstacle points (non-ground)
        PointCloudT::Ptr obstacles(new PointCloudT);
        extract.setNegative(true);
        extract.filter(*obstacles);

        return {ground, obstacles};
    }

    std::vector<PointCloudT::Ptr> cluster_obstacles(const PointCloudT::Ptr& obstacles) {
        // Create KD-tree for efficient nearest neighbor search
        pcl::search::KdTree<PointT>::Ptr tree(new pcl::search::KdTree<PointT>);
        tree->setInputCloud(obstacles);

        std::vector<pcl::PointIndices> cluster_indices;
        cluster_extractor_.setSearchMethod(tree);
        cluster_extractor_.setInputCloud(obstacles);
        cluster_extractor_.extract(cluster_indices);

        // Extract individual clusters
        std::vector<PointCloudT::Ptr> clusters;
        for (const auto& indices : cluster_indices) {
            PointCloudT::Ptr cluster(new PointCloudT);
            for (int idx : indices.indices) {
                cluster->points.push_back(obstacles->points[idx]);
            }
            cluster->width = cluster->points.size();
            cluster->height = 1;
            cluster->is_dense = true;

            clusters.push_back(cluster);
        }

        return clusters;
    }
};
```

### Object Detection from Point Clouds

```python
import numpy as np
import open3d as o3d

class PointCloudObjectDetector:
    """
    Detect and classify objects from lidar point clouds
    """

    def __init__(self):
        self.min_points = 10
        self.max_points = 10000

    def detect_objects(self, point_cloud):
        """
        Detect bounding boxes for objects

        Args:
            point_cloud: open3d.geometry.PointCloud

        Returns:
            List of detected objects with bounding boxes
        """
        # Ground removal
        ground_plane, obstacles = self.remove_ground(point_cloud)

        # Clustering
        clusters = self.cluster_dbscan(obstacles)

        # Bounding box extraction
        objects = []
        for cluster in clusters:
            if len(cluster.points) < self.min_points:
                continue

            # Compute oriented bounding box
            obb = cluster.get_oriented_bounding_box()
            obb.color = (1, 0, 0)  # Red

            # Compute axis-aligned bounding box
            aabb = cluster.get_axis_aligned_bounding_box()

            # Extract features
            centroid = np.mean(np.asarray(cluster.points), axis=0)
            dimensions = obb.extent  # [length, width, height]

            # Classify based on dimensions
            obj_class = self.classify_object(dimensions)

            obj = {
                'point_cloud': cluster,
                'obb': obb,
                'aabb': aabb,
                'centroid': centroid,
                'dimensions': dimensions,
                'class': obj_class,
                'num_points': len(cluster.points)
            }

            objects.append(obj)

        return objects

    def remove_ground(self, pcd, distance_threshold=0.1):
        """Remove ground plane using RANSAC"""
        plane_model, inliers = pcd.segment_plane(
            distance_threshold=distance_threshold,
            ransac_n=3,
            num_iterations=1000
        )

        ground = pcd.select_by_index(inliers)
        obstacles = pcd.select_by_index(inliers, invert=True)

        return ground, obstacles

    def cluster_dbscan(self, pcd, eps=0.5, min_points=10):
        """Cluster points using DBSCAN"""
        labels = np.array(pcd.cluster_dbscan(eps=eps, min_points=min_points))

        max_label = labels.max()
        clusters = []

        for label in range(max_label + 1):
            cluster_indices = np.where(labels == label)[0]
            cluster = pcd.select_by_index(cluster_indices)

            if len(cluster.points) >= self.min_points and \
               len(cluster.points) <= self.max_points:
                clusters.append(cluster)

        return clusters

    def classify_object(self, dimensions):
        """
        Classify object based on bounding box dimensions

        Args:
            dimensions: [length, width, height] in meters

        Returns:
            Object class string
        """
        length, width, height = dimensions

        # Heuristic classification
        if height < 0.5:
            return "ground_object"
        elif height < 1.0 and length < 1.5:
            return "small_obstacle"
        elif height > 1.2 and length > 3.0 and width > 1.5:
            return "vehicle"
        elif height > 1.5 and length < 1.0:
            return "pedestrian"
        elif height > 1.0 and length < 2.0:
            return "bicycle"
        else:
            return "unknown"
```

### Lidar SLAM

```cpp
#include <pcl/registration/icp.h>
#include <pcl/registration/ndt.h>
#include <Eigen/Dense>

class LidarSLAM {
public:
    LidarSLAM() {
        // Initialize NDT (Normal Distributions Transform)
        ndt_.setTransformationEpsilon(0.01);
        ndt_.setStepSize(0.1);
        ndt_.setResolution(1.0);
        ndt_.setMaximumIterations(35);

        current_pose_ = Eigen::Matrix4f::Identity();
    }

    using PointT = pcl::PointXYZI;
    using PointCloudT = pcl::PointCloud<PointT>;

    struct SLAMResult {
        Eigen::Matrix4f pose;
        double fitness_score;
        bool converged;
    };

    SLAMResult process_scan(const PointCloudT::Ptr& scan) {
        SLAMResult result;

        if (!previous_scan_) {
            // First scan - initialize
            previous_scan_ = scan;
            result.pose = current_pose_;
            result.converged = true;
            result.fitness_score = 0.0;
            return result;
        }

        // Scan matching using NDT
        ndt_.setInputSource(scan);
        ndt_.setInputTarget(previous_scan_);

        PointCloudT::Ptr aligned(new PointCloudT);
        ndt_.align(*aligned, current_pose_);

        result.converged = ndt_.hasConverged();
        result.fitness_score = ndt_.getFitnessScore();

        if (result.converged) {
            // Update pose
            Eigen::Matrix4f transformation = ndt_.getFinalTransformation();
            current_pose_ = transformation * current_pose_;

            result.pose = current_pose_;

            // Update previous scan
            previous_scan_ = scan;
        } else {
            result.pose = current_pose_;
        }

        return result;
    }

    Eigen::Matrix4f get_current_pose() const {
        return current_pose_;
    }

private:
    pcl::NormalDistributionsTransform<PointT, PointT> ndt_;
    PointCloudT::Ptr previous_scan_;
    Eigen::Matrix4f current_pose_;
};
```

## Occupancy Grid Mapping

```cpp
#include <vector>
#include <cmath>

class OccupancyGrid {
public:
    OccupancyGrid(double resolution, double width, double height)
        : resolution_(resolution),
          width_(static_cast<int>(width / resolution)),
          height_(static_cast<int>(height / resolution))
    {
        grid_.resize(width_ * height_, 0.5);  // Initialize to unknown (0.5)
    }

    void update_with_pointcloud(const std::vector<Eigen::Vector2d>& points,
                               const Eigen::Vector2d& sensor_origin) {
        for (const auto& point : points) {
            // Ray trace from sensor to point
            auto cells = bresenham(sensor_origin, point);

            // Mark cells along ray as free
            for (size_t i = 0; i < cells.size() - 1; ++i) {
                update_cell(cells[i], -0.1);  // Free space
            }

            // Mark endpoint as occupied
            if (!cells.empty()) {
                update_cell(cells.back(), 0.3);  // Occupied
            }
        }
    }

    double get_occupancy(int x, int y) const {
        if (x < 0 || x >= width_ || y < 0 || y >= height_) {
            return 0.5;  // Unknown
        }
        return grid_[y * width_ + x];
    }

    std::vector<uint8_t> to_image() const {
        // Convert to grayscale image (0-255)
        std::vector<uint8_t> image(grid_.size());
        for (size_t i = 0; i < grid_.size(); ++i) {
            image[i] = static_cast<uint8_t>((1.0 - grid_[i]) * 255);
        }
        return image;
    }

private:
    double resolution_;  // meters per cell
    int width_, height_;  // cells
    std::vector<double> grid_;  // Occupancy probabilities [0, 1]

    void update_cell(const Eigen::Vector2i& cell, double log_odds) {
        int idx = cell.y() * width_ + cell.x();
        if (idx >= 0 && idx < static_cast<int>(grid_.size())) {
            // Log-odds update
            double current = grid_[idx];
            double current_log_odds = std::log(current / (1.0 - current));
            double new_log_odds = current_log_odds + log_odds;

            // Convert back to probability
            grid_[idx] = 1.0 / (1.0 + std::exp(-new_log_odds));

            // Clamp
            grid_[idx] = std::max(0.01, std::min(0.99, grid_[idx]));
        }
    }

    std::vector<Eigen::Vector2i> bresenham(const Eigen::Vector2d& start,
                                          const Eigen::Vector2d& end) {
        // Bresenham's line algorithm
        Eigen::Vector2i start_cell = world_to_grid(start);
        Eigen::Vector2i end_cell = world_to_grid(end);

        std::vector<Eigen::Vector2i> cells;

        int x0 = start_cell.x(), y0 = start_cell.y();
        int x1 = end_cell.x(), y1 = end_cell.y();

        int dx = std::abs(x1 - x0);
        int dy = std::abs(y1 - y0);
        int sx = (x0 < x1) ? 1 : -1;
        int sy = (y0 < y1) ? 1 : -1;
        int err = dx - dy;

        while (true) {
            cells.push_back(Eigen::Vector2i(x0, y0));

            if (x0 == x1 && y0 == y1) break;

            int e2 = 2 * err;
            if (e2 > -dy) {
                err -= dy;
                x0 += sx;
            }
            if (e2 < dx) {
                err += dx;
                y0 += sy;
            }
        }

        return cells;
    }

    Eigen::Vector2i world_to_grid(const Eigen::Vector2d& world_pos) const {
        int x = static_cast<int>(world_pos.x() / resolution_ + width_ / 2);
        int y = static_cast<int>(world_pos.y() / resolution_ + height_ / 2);
        return Eigen::Vector2i(x, y);
    }
};
```

## ROS2 Integration

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from geometry_msgs.msg import PoseStamped
import numpy as np

class RadarLidarFusionNode(Node):
    def __init__(self):
        super().__init__('radar_lidar_fusion')

        # Subscribers
        self.radar_sub = self.create_subscription(
            PointCloud2,
            '/radar/points',
            self.radar_callback,
            10
        )

        self.lidar_sub = self.create_subscription(
            PointCloud2,
            '/lidar/points',
            self.lidar_callback,
            10
        )

        # Publishers
        self.fused_pub = self.create_publisher(
            PointCloud2,
            '/fused/points',
            10
        )

        self.pose_pub = self.create_publisher(
            PoseStamped,
            '/slam/pose',
            10
        )

        self.get_logger().info('Radar-Lidar Fusion Node started')

    def radar_callback(self, msg):
        # Process radar data
        radar_points = self.pointcloud2_to_array(msg)
        # ... processing logic
        pass

    def lidar_callback(self, msg):
        # Process lidar data
        lidar_points = self.pointcloud2_to_array(msg)
        # ... processing logic
        pass

    def pointcloud2_to_array(self, cloud_msg):
        # Convert ROS PointCloud2 to numpy array
        # Implementation details...
        pass

def main(args=None):
    rclpy.init(args=args)
    node = RadarLidarFusionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Performance Targets

- **Radar Processing**: 50ms per frame (77 GHz FMCW)
- **Lidar Processing**: 100ms per scan (128-channel, 10Hz)
- **SLAM Update**: < 200ms per scan
- **Occupancy Grid**: 10Hz update rate

## Standards

- **ISO 26262**: ASIL B-D for sensor processing
- **ISO 11898**: CAN communication for sensor data
- **AUTOSAR**: Radar/Lidar driver integration

## Related Skills

- sensor-fusion-perception.md
- camera-processing-vision.md
- hd-maps-localization.md
