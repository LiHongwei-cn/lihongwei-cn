# Camera Processing & Computer Vision for ADAS

## Overview

Camera-based perception for ADAS including lane detection, object detection, semantic segmentation, depth estimation, and ISP tuning. Covers classical computer vision (Hough transform, edge detection) and deep learning approaches (YOLO, SSD, Faster R-CNN, semantic segmentation networks).

## Camera Hardware Architecture

### Typical ADAS Camera Setup

```
Multi-Camera System (ADAS L2-L5)
────────────────────────────────────────

Front View:
  - Wide FOV (120°): Pedestrian detection, lane keeping
  - Tele FOV (30°): Long-range object detection (up to 200m)
  - Fisheye (180°+): Parking assistance

Surround View (360°):
  - Front fisheye: 190° FOV
  - Rear fisheye: 190° FOV
  - Left/Right fisheye: 190° FOV each

Specifications:
  - Resolution: 1280x960 to 3840x2160 (1-8MP)
  - Frame Rate: 30-60 FPS
  - Dynamic Range: 100-120 dB HDR
  - Interface: MIPI CSI-2, GMSL2, FPD-Link III
  - ISP: Hardware accelerated (denoise, HDR, lens correction)
```

## Lane Detection

### Classical Approach: Hough Transform

```python
import cv2
import numpy as np

class LaneDetector:
    """
    Classical lane detection using edge detection and Hough transform
    """

    def __init__(self):
        # Canny edge detection parameters
        self.canny_low = 50
        self.canny_high = 150

        # Hough transform parameters
        self.rho = 1              # Distance resolution (pixels)
        self.theta = np.pi/180    # Angular resolution (radians)
        self.threshold = 50       # Min intersections to detect line
        self.min_line_length = 100
        self.max_line_gap = 50

        # ROI vertices (trapezoid)
        self.roi_vertices = None

    def detect_lanes(self, image):
        """
        Detect lane lines in image

        Args:
            image: RGB image (H, W, 3)

        Returns:
            lane_image: Image with detected lanes drawn
            lane_lines: List of detected lane line parameters
        """
        # 1. Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # 2. Apply Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # 3. Edge detection
        edges = cv2.Canny(blur, self.canny_low, self.canny_high)

        # 4. Apply ROI mask
        masked_edges = self.apply_roi(edges, image.shape)

        # 5. Hough line detection
        lines = cv2.HoughLinesP(
            masked_edges,
            self.rho,
            self.theta,
            self.threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap
        )

        # 6. Filter and cluster lines into left/right lanes
        left_lane, right_lane = self.separate_lanes(lines, image.shape)

        # 7. Fit polynomial to lane points
        lane_lines = self.fit_lane_polynomials(left_lane, right_lane)

        # 8. Draw lanes on image
        lane_image = self.draw_lanes(image, lane_lines)

        return lane_image, lane_lines

    def apply_roi(self, edges, image_shape):
        """Apply region of interest mask"""
        height, width = image_shape[:2]

        # Define trapezoid ROI
        vertices = np.array([[
            (width * 0.1, height),
            (width * 0.4, height * 0.6),
            (width * 0.6, height * 0.6),
            (width * 0.9, height)
        ]], dtype=np.int32)

        mask = np.zeros_like(edges)
        cv2.fillPoly(mask, vertices, 255)

        masked = cv2.bitwise_and(edges, mask)
        return masked

    def separate_lanes(self, lines, image_shape):
        """Separate left and right lane lines based on slope"""
        if lines is None:
            return [], []

        height, width = image_shape[:2]
        left_lines = []
        right_lines = []

        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Calculate slope
            if x2 - x1 == 0:
                continue
            slope = (y2 - y1) / (x2 - x1)

            # Filter by slope
            if slope < -0.5:  # Left lane (negative slope)
                left_lines.append(line[0])
            elif slope > 0.5:  # Right lane (positive slope)
                right_lines.append(line[0])

        return left_lines, right_lines

    def fit_lane_polynomials(self, left_lines, right_lines):
        """Fit polynomial curves to lane line points"""
        def fit_poly(lines):
            if not lines:
                return None

            # Extract all points
            points = []
            for x1, y1, x2, y2 in lines:
                points.extend([(x1, y1), (x2, y2)])

            if len(points) < 2:
                return None

            # Convert to numpy arrays
            points = np.array(points)
            x = points[:, 0]
            y = points[:, 1]

            # Fit 2nd order polynomial
            poly_coeffs = np.polyfit(y, x, 2)
            return poly_coeffs

        left_poly = fit_poly(left_lines)
        right_poly = fit_poly(right_lines)

        return {"left": left_poly, "right": right_poly}

    def draw_lanes(self, image, lane_lines):
        """Draw detected lanes on image"""
        lane_image = np.copy(image)
        height = image.shape[0]

        # Y coordinates for drawing
        y_vals = np.linspace(height * 0.6, height, 100)

        # Draw left lane
        if lane_lines["left"] is not None:
            left_poly = lane_lines["left"]
            left_x = np.polyval(left_poly, y_vals).astype(int)
            left_points = np.array([np.column_stack((left_x, y_vals.astype(int)))])
            cv2.polylines(lane_image, left_points, False, (255, 0, 0), 5)

        # Draw right lane
        if lane_lines["right"] is not None:
            right_poly = lane_lines["right"]
            right_x = np.polyval(right_poly, y_vals).astype(int)
            right_points = np.array([np.column_stack((right_x, y_vals.astype(int)))])
            cv2.polylines(lane_image, right_points, False, (0, 0, 255), 5)

        return lane_image
```

### Deep Learning Approach: Lane Segmentation

```python
import torch
import torch.nn as nn
import torchvision.transforms as transforms

class LaneSegmentationNet(nn.Module):
    """
    U-Net style architecture for lane segmentation
    """

    def __init__(self, in_channels=3, num_classes=2):
        super(LaneSegmentationNet, self).__init__()

        # Encoder (downsampling)
        self.enc1 = self.conv_block(in_channels, 64)
        self.enc2 = self.conv_block(64, 128)
        self.enc3 = self.conv_block(128, 256)
        self.enc4 = self.conv_block(256, 512)

        # Bottleneck
        self.bottleneck = self.conv_block(512, 1024)

        # Decoder (upsampling)
        self.upconv4 = nn.ConvTranspose2d(1024, 512, 2, stride=2)
        self.dec4 = self.conv_block(1024, 512)

        self.upconv3 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.dec3 = self.conv_block(512, 256)

        self.upconv2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.dec2 = self.conv_block(256, 128)

        self.upconv1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec1 = self.conv_block(128, 64)

        # Output
        self.out = nn.Conv2d(64, num_classes, 1)

        self.pool = nn.MaxPool2d(2, 2)

    def conv_block(self, in_ch, out_ch):
        return nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        # Encoder
        enc1 = self.enc1(x)
        enc2 = self.enc2(self.pool(enc1))
        enc3 = self.enc3(self.pool(enc2))
        enc4 = self.enc4(self.pool(enc3))

        # Bottleneck
        bottleneck = self.bottleneck(self.pool(enc4))

        # Decoder with skip connections
        dec4 = self.upconv4(bottleneck)
        dec4 = torch.cat([dec4, enc4], dim=1)
        dec4 = self.dec4(dec4)

        dec3 = self.upconv3(dec4)
        dec3 = torch.cat([dec3, enc3], dim=1)
        dec3 = self.dec3(dec3)

        dec2 = self.upconv2(dec3)
        dec2 = torch.cat([dec2, enc2], dim=1)
        dec2 = self.dec2(dec2)

        dec1 = self.upconv1(dec2)
        dec1 = torch.cat([dec1, enc1], dim=1)
        dec1 = self.dec1(dec1)

        return self.out(dec1)


class DeepLaneDetector:
    """
    Deep learning-based lane detection
    """

    def __init__(self, model_path, device='cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.model = LaneSegmentationNet().to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225])
        ])

    def detect(self, image):
        """
        Detect lanes using deep learning

        Args:
            image: RGB image (H, W, 3) numpy array

        Returns:
            lane_mask: Binary mask (H, W) with lane pixels
            lane_lines: Fitted polynomial lane lines
        """
        # Preprocess
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)

        # Inference
        with torch.no_grad():
            output = self.model(input_tensor)
            pred = torch.argmax(output, dim=1).squeeze().cpu().numpy()

        # Post-process: fit polynomials to predicted lane pixels
        lane_lines = self.fit_lanes_from_mask(pred)

        return pred, lane_lines

    def fit_lanes_from_mask(self, lane_mask):
        """Fit polynomial curves to segmented lane mask"""
        height, width = lane_mask.shape

        # Find lane pixels
        lane_pixels = np.where(lane_mask > 0)
        y_coords = lane_pixels[0]
        x_coords = lane_pixels[1]

        if len(y_coords) < 10:
            return {"left": None, "right": None}

        # Separate left and right lanes based on x position
        midpoint = width // 2
        left_mask = x_coords < midpoint
        right_mask = x_coords >= midpoint

        left_x = x_coords[left_mask]
        left_y = y_coords[left_mask]
        right_x = x_coords[right_mask]
        right_y = y_coords[right_mask]

        # Fit polynomials
        left_poly = np.polyfit(left_y, left_x, 2) if len(left_y) > 10 else None
        right_poly = np.polyfit(right_y, right_x, 2) if len(right_y) > 10 else None

        return {"left": left_poly, "right": right_poly}
```

## Object Detection

### YOLO v5 for Real-Time Object Detection

```python
import torch
import cv2
import numpy as np

class YOLOv5Detector:
    """
    YOLO v5 object detector optimized for automotive applications
    """

    def __init__(self, model_path='yolov5s.pt', conf_thresh=0.5, iou_thresh=0.45):
        self.model = torch.hub.load('ultralytics/yolov5', 'custom',
                                    path=model_path, force_reload=False)
        self.model.conf = conf_thresh
        self.model.iou = iou_thresh

        # COCO class names relevant for ADAS
        self.classes_of_interest = [
            'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck',
            'traffic light', 'stop sign'
        ]

    def detect(self, image):
        """
        Detect objects in image

        Args:
            image: RGB image (H, W, 3)

        Returns:
            detections: List of Detection objects
        """
        # Run inference
        results = self.model(image)

        # Parse results
        detections = []
        for *box, conf, cls in results.xyxy[0].cpu().numpy():
            class_name = self.model.names[int(cls)]

            # Filter for ADAS-relevant objects
            if class_name in self.classes_of_interest:
                detection = {
                    'bbox': box,  # [x1, y1, x2, y2]
                    'confidence': conf,
                    'class': class_name,
                    'class_id': int(cls)
                }
                detections.append(detection)

        return detections

    def detect_with_tracking(self, image, prev_detections=None):
        """
        Detect and track objects using simple IOU matching
        """
        current_detections = self.detect(image)

        if prev_detections is None:
            # Initialize track IDs
            for i, det in enumerate(current_detections):
                det['track_id'] = i
            return current_detections

        # Match current detections with previous using IOU
        matched, unmatched_current, unmatched_prev = self.match_detections(
            current_detections, prev_detections
        )

        # Update track IDs
        next_track_id = max([d['track_id'] for d in prev_detections]) + 1

        for curr_idx, prev_idx in matched:
            current_detections[curr_idx]['track_id'] = \
                prev_detections[prev_idx]['track_id']

        for curr_idx in unmatched_current:
            current_detections[curr_idx]['track_id'] = next_track_id
            next_track_id += 1

        return current_detections

    def match_detections(self, current, previous, iou_thresh=0.3):
        """Match detections using IOU"""
        if not current or not previous:
            return [], list(range(len(current))), list(range(len(previous)))

        # Compute IOU matrix
        iou_matrix = np.zeros((len(current), len(previous)))
        for i, curr_det in enumerate(current):
            for j, prev_det in enumerate(previous):
                if curr_det['class'] == prev_det['class']:
                    iou_matrix[i, j] = self.compute_iou(
                        curr_det['bbox'], prev_det['bbox']
                    )

        # Hungarian algorithm for matching (greedy approximation)
        matched = []
        unmatched_current = list(range(len(current)))
        unmatched_prev = list(range(len(previous)))

        while iou_matrix.size > 0:
            max_iou = iou_matrix.max()
            if max_iou < iou_thresh:
                break

            curr_idx, prev_idx = np.unravel_index(iou_matrix.argmax(),
                                                  iou_matrix.shape)
            matched.append((curr_idx, prev_idx))

            unmatched_current.remove(curr_idx)
            unmatched_prev.remove(prev_idx)

            # Remove matched from matrix
            iou_matrix[curr_idx, :] = 0
            iou_matrix[:, prev_idx] = 0

        return matched, unmatched_current, unmatched_prev

    def compute_iou(self, box1, box2):
        """Compute IOU between two bounding boxes"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2

        # Intersection area
        inter_xmin = max(x1_min, x2_min)
        inter_ymin = max(y1_min, y2_min)
        inter_xmax = min(x1_max, x2_max)
        inter_ymax = min(y1_max, y2_max)

        inter_area = max(0, inter_xmax - inter_xmin) * \
                    max(0, inter_ymax - inter_ymin)

        # Union area
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0
```

## Semantic Segmentation

```python
import torch
import torch.nn as nn
from torchvision.models.segmentation import deeplabv3_resnet50

class SemanticSegmentor:
    """
    Semantic segmentation for ADAS scene understanding
    """

    def __init__(self, model_path=None, num_classes=19, device='cuda'):
        """
        Args:
            num_classes: Number of classes (Cityscapes: 19 classes)
                0: road, 1: sidewalk, 2: building, 3: wall, 4: fence,
                5: pole, 6: traffic light, 7: traffic sign, 8: vegetation,
                9: terrain, 10: sky, 11: person, 12: rider, 13: car,
                14: truck, 15: bus, 16: train, 17: motorcycle, 18: bicycle
        """
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.num_classes = num_classes

        # Load pretrained DeepLabV3
        self.model = deeplabv3_resnet50(pretrained=True)
        self.model.classifier[4] = nn.Conv2d(256, num_classes, kernel_size=1)

        if model_path:
            self.model.load_state_dict(torch.load(model_path,
                                                  map_location=self.device))

        self.model.to(self.device)
        self.model.eval()

        # Class color map (Cityscapes colors)
        self.color_map = self.create_cityscapes_colormap()

    def create_cityscapes_colormap(self):
        """Create color map for visualization"""
        colors = [
            [128, 64, 128],   # road
            [244, 35, 232],   # sidewalk
            [70, 70, 70],     # building
            [102, 102, 156],  # wall
            [190, 153, 153],  # fence
            [153, 153, 153],  # pole
            [250, 170, 30],   # traffic light
            [220, 220, 0],    # traffic sign
            [107, 142, 35],   # vegetation
            [152, 251, 152],  # terrain
            [70, 130, 180],   # sky
            [220, 20, 60],    # person
            [255, 0, 0],      # rider
            [0, 0, 142],      # car
            [0, 0, 70],       # truck
            [0, 60, 100],     # bus
            [0, 80, 100],     # train
            [0, 0, 230],      # motorcycle
            [119, 11, 32],    # bicycle
        ]
        return np.array(colors, dtype=np.uint8)

    def segment(self, image):
        """
        Perform semantic segmentation

        Args:
            image: RGB image (H, W, 3)

        Returns:
            segmentation_mask: (H, W) class labels
            colored_mask: (H, W, 3) RGB colored segmentation
        """
        # Preprocess
        input_tensor = self.preprocess(image)

        # Inference
        with torch.no_grad():
            output = self.model(input_tensor)['out']
            pred = torch.argmax(output, dim=1).squeeze().cpu().numpy()

        # Colorize for visualization
        colored_mask = self.color_map[pred]

        return pred, colored_mask

    def preprocess(self, image):
        """Preprocess image for model input"""
        # Normalize using ImageNet statistics
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])

        # Convert to tensor and normalize
        img = image.astype(np.float32) / 255.0
        img = (img - mean) / std
        img = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)

        return img.to(self.device)

    def get_drivable_area(self, segmentation_mask):
        """Extract drivable area from segmentation"""
        # Drivable classes: road (0), sidewalk (1)
        drivable_mask = np.isin(segmentation_mask, [0, 1])
        return drivable_mask.astype(np.uint8)
```

## Depth Estimation

### Stereo Depth Estimation

```cpp
#include <opencv2/opencv.hpp>
#include <opencv2/calib3d.hpp>

class StereoDepthEstimator {
public:
    StereoDepthEstimator(const cv::Mat& K_left, const cv::Mat& K_right,
                        const cv::Mat& R, const cv::Mat& T, float baseline)
        : K_left_(K_left), K_right_(K_right), R_(R), T_(T), baseline_(baseline)
    {
        // Create stereo matcher
        stereo_ = cv::StereoSGBM::create(
            0,                      // minDisparity
            16 * 10,                // numDisparities (must be divisible by 16)
            5,                      // blockSize
            8 * 5 * 5,              // P1
            32 * 5 * 5,             // P2
            1,                      // disp12MaxDiff
            0,                      // preFilterCap
            10,                     // uniquenessRatio
            100,                    // speckleWindowSize
            32,                     // speckleRange
            cv::StereoSGBM::MODE_SGBM_3WAY
        );

        // Compute rectification maps
        cv::Size img_size(1280, 720);  // Adjust to your camera
        cv::stereoRectify(K_left_, cv::Mat(), K_right_, cv::Mat(),
                         img_size, R_, T_, R1_, R2_, P1_, P2_, Q_);

        cv::initUndistortRectifyMap(K_left_, cv::Mat(), R1_, P1_,
                                   img_size, CV_32FC1, map_left_x_, map_left_y_);
        cv::initUndistortRectifyMap(K_right_, cv::Mat(), R2_, P2_,
                                   img_size, CV_32FC1, map_right_x_, map_right_y_);
    }

    cv::Mat compute_disparity(const cv::Mat& left_img, const cv::Mat& right_img) {
        // Rectify images
        cv::Mat left_rect, right_rect;
        cv::remap(left_img, left_rect, map_left_x_, map_left_y_, cv::INTER_LINEAR);
        cv::remap(right_img, right_rect, map_right_x_, map_right_y_, cv::INTER_LINEAR);

        // Convert to grayscale
        cv::Mat left_gray, right_gray;
        cv::cvtColor(left_rect, left_gray, cv::COLOR_BGR2GRAY);
        cv::cvtColor(right_rect, right_gray, cv::COLOR_BGR2GRAY);

        // Compute disparity
        cv::Mat disparity;
        stereo_->compute(left_gray, right_gray, disparity);

        // Convert to float and normalize
        disparity.convertTo(disparity, CV_32F, 1.0 / 16.0);

        return disparity;
    }

    cv::Mat disparity_to_depth(const cv::Mat& disparity) {
        // depth = (focal_length * baseline) / disparity
        cv::Mat depth;
        float focal_length = K_left_.at<double>(0, 0);

        depth = (focal_length * baseline_) / disparity;

        // Clip unrealistic depths
        cv::threshold(depth, depth, 0.1, 100.0, cv::THRESH_TOZERO);
        cv::threshold(depth, depth, 100.0, 100.0, cv::THRESH_TRUNC);

        return depth;
    }

    cv::Mat compute_point_cloud(const cv::Mat& disparity) {
        // Reproject to 3D using Q matrix
        cv::Mat points_3d;
        cv::reprojectImageTo3D(disparity, points_3d, Q_, true);

        return points_3d;
    }

private:
    cv::Mat K_left_, K_right_;  // Intrinsic matrices
    cv::Mat R_, T_;              // Extrinsic: rotation and translation
    cv::Mat R1_, R2_, P1_, P2_, Q_;  // Rectification matrices
    cv::Mat map_left_x_, map_left_y_, map_right_x_, map_right_y_;
    float baseline_;
    cv::Ptr<cv::StereoSGBM> stereo_;
};
```

### Monocular Depth Estimation (Deep Learning)

```python
import torch
import torch.nn as nn

class MonoDepthNet(nn.Module):
    """
    Monocular depth estimation network based on encoder-decoder architecture
    """

    def __init__(self, encoder='resnet50'):
        super(MonoDepthNet, self).__init__()

        # Encoder (pretrained ResNet)
        if encoder == 'resnet50':
            resnet = torch.hub.load('pytorch/vision:v0.10.0', 'resnet50',
                                   pretrained=True)
            self.encoder = nn.ModuleList([
                nn.Sequential(resnet.conv1, resnet.bn1, resnet.relu, resnet.maxpool),
                resnet.layer1,
                resnet.layer2,
                resnet.layer3,
                resnet.layer4
            ])
            encoder_channels = [64, 256, 512, 1024, 2048]

        # Decoder
        self.decoder = nn.ModuleList([
            self.upconv_block(2048, 1024),
            self.upconv_block(1024 + 1024, 512),
            self.upconv_block(512 + 512, 256),
            self.upconv_block(256 + 256, 128),
            self.upconv_block(128 + 64, 64)
        ])

        # Output layer
        self.output_conv = nn.Sequential(
            nn.Conv2d(64, 32, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, 1),
            nn.Sigmoid()  # Output in range [0, 1]
        )

    def upconv_block(self, in_channels, out_channels):
        return nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, 3, stride=2, padding=1,
                             output_padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        # Encoder with skip connections
        skip_connections = []
        for layer in self.encoder:
            x = layer(x)
            skip_connections.append(x)

        # Decoder
        x = skip_connections[-1]
        for i, decoder_layer in enumerate(self.decoder):
            x = decoder_layer(x)
            if i < len(skip_connections) - 1:
                # Concatenate with skip connection
                x = torch.cat([x, skip_connections[-(i + 2)]], dim=1)

        # Output depth map
        depth = self.output_conv(x)

        return depth
```

## ISP Tuning

### HDR and Low-Light Enhancement

```cpp
#include <opencv2/opencv.hpp>

class ISPProcessor {
public:
    cv::Mat process_hdr(const std::vector<cv::Mat>& exposures) {
        // Multi-exposure HDR fusion
        cv::Ptr<cv::MergeDebevec> merge = cv::createMergeDebevec();

        std::vector<float> exposure_times;
        for (size_t i = 0; i < exposures.size(); ++i) {
            exposure_times.push_back(std::pow(2.0f, i - 1));  // -1, 0, +1 EV
        }

        cv::Mat hdr;
        merge->process(exposures, hdr, exposure_times, cv::Mat());

        // Tone mapping
        cv::Ptr<cv::TonemapDrago> tonemap = cv::createTonemapDrago(2.2f);
        cv::Mat ldr;
        tonemap->process(hdr, ldr);

        // Convert to 8-bit
        ldr = ldr * 255.0;
        ldr.convertTo(ldr, CV_8UC3);

        return ldr;
    }

    cv::Mat enhance_low_light(const cv::Mat& image) {
        // CLAHE (Contrast Limited Adaptive Histogram Equalization)
        cv::Mat lab;
        cv::cvtColor(image, lab, cv::COLOR_BGR2Lab);

        std::vector<cv::Mat> lab_planes;
        cv::split(lab, lab_planes);

        // Apply CLAHE to L channel
        cv::Ptr<cv::CLAHE> clahe = cv::createCLAHE(3.0, cv::Size(8, 8));
        clahe->apply(lab_planes[0], lab_planes[0]);

        cv::merge(lab_planes, lab);
        cv::Mat enhanced;
        cv::cvtColor(lab, enhanced, cv::COLOR_Lab2BGR);

        return enhanced;
    }

    cv::Mat denoise(const cv::Mat& image) {
        // Fast non-local means denoising
        cv::Mat denoised;
        cv::fastNlMeansDenoisingColored(image, denoised, 10, 10, 7, 21);
        return denoised;
    }
};
```

## Performance Optimization

### TensorRT Optimization for NVIDIA Platforms

```python
import tensorrt as trt
import pycuda.driver as cuda
import numpy as np

class TensorRTInference:
    """
    Optimize and run deep learning models with TensorRT
    """

    def __init__(self, onnx_path, fp16_mode=True):
        self.logger = trt.Logger(trt.Logger.WARNING)
        self.engine = self.build_engine(onnx_path, fp16_mode)
        self.context = self.engine.create_execution_context()

        # Allocate buffers
        self.inputs, self.outputs, self.bindings = self.allocate_buffers()

    def build_engine(self, onnx_path, fp16_mode):
        """Build TensorRT engine from ONNX model"""
        builder = trt.Builder(self.logger)
        network = builder.create_network(
            1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
        )
        parser = trt.OnnxParser(network, self.logger)

        # Parse ONNX
        with open(onnx_path, 'rb') as model:
            parser.parse(model.read())

        # Builder config
        config = builder.create_builder_config()
        config.max_workspace_size = 1 << 30  # 1GB

        if fp16_mode:
            config.set_flag(trt.BuilderFlag.FP16)

        # Build engine
        engine = builder.build_engine(network, config)
        return engine

    def allocate_buffers(self):
        inputs = []
        outputs = []
        bindings = []

        for binding in self.engine:
            size = trt.volume(self.engine.get_binding_shape(binding))
            dtype = trt.nptype(self.engine.get_binding_dtype(binding))

            # Allocate host and device buffers
            host_mem = cuda.pagelocked_empty(size, dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)

            bindings.append(int(device_mem))

            if self.engine.binding_is_input(binding):
                inputs.append({'host': host_mem, 'device': device_mem})
            else:
                outputs.append({'host': host_mem, 'device': device_mem})

        return inputs, outputs, bindings

    def infer(self, input_data):
        """Run inference"""
        # Copy input to device
        np.copyto(self.inputs[0]['host'], input_data.ravel())
        cuda.memcpy_htod(self.inputs[0]['device'], self.inputs[0]['host'])

        # Run inference
        self.context.execute_v2(bindings=self.bindings)

        # Copy output to host
        cuda.memcpy_dtoh(self.outputs[0]['host'], self.outputs[0]['device'])

        return self.outputs[0]['host']
```

## Standards & Safety

- **ISO 26262**: ASIL B-D depending on function (lane keeping: ASIL B, AEB: ASIL D)
- **ISO 21448 (SOTIF)**: Validation for lighting conditions, occlusions
- **MISRA C++**: Code quality for production deployment

## Performance Targets

- **Lane Detection**: 30 FPS @ 1280x720
- **Object Detection**: 30 FPS @ 1920x1080 (YOLOv5s on GPU)
- **Semantic Segmentation**: 20 FPS @ 1280x720 (DeepLabV3)
- **Latency**: < 50ms camera-to-decision

## Related Skills

- sensor-fusion-perception.md
- radar-lidar-processing.md
- adas-features-implementation.md
