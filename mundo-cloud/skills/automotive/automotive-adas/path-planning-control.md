# Path Planning & Control for ADAS

## Overview

Path planning algorithms (A*, RRT, Hybrid A*), trajectory optimization, Model Predictive Control (MPC), Pure Pursuit, Stanley controller, and behavior planning for L2-L5 autonomy.

## Path Planning Algorithms

### A* for Grid-Based Planning

```python
import numpy as np
import heapq
from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass(order=True)
class Node:
    f_score: float
    position: Tuple[int, int] = field(compare=False)
    g_score: float = field(compare=False)
    parent: 'Node' = field(default=None, compare=False)

class AStarPlanner:
    """
    A* path planning on occupancy grid
    """

    def __init__(self, occupancy_grid, resolution=0.5):
        """
        Args:
            occupancy_grid: 2D numpy array (0=free, 1=occupied)
            resolution: meters per grid cell
        """
        self.grid = occupancy_grid
        self.resolution = resolution
        self.height, self.width = occupancy_grid.shape

    def plan(self, start, goal):
        """
        Find path from start to goal

        Args:
            start: (x, y) in meters
            goal: (x, y) in meters

        Returns:
            path: List of (x, y) waypoints in meters
        """
        start_cell = self.world_to_grid(start)
        goal_cell = self.world_to_grid(goal)

        if not self.is_valid(start_cell) or not self.is_valid(goal_cell):
            return []

        # Initialize
        open_set = []
        closed_set = set()

        start_node = Node(
            f_score=self.heuristic(start_cell, goal_cell),
            position=start_cell,
            g_score=0.0
        )

        heapq.heappush(open_set, start_node)

        while open_set:
            current = heapq.heappop(open_set)

            if current.position == goal_cell:
                return self.reconstruct_path(current)

            closed_set.add(current.position)

            # Explore neighbors (8-connected)
            for neighbor_pos in self.get_neighbors(current.position):
                if neighbor_pos in closed_set:
                    continue

                if not self.is_free(neighbor_pos):
                    continue

                # Calculate g_score
                move_cost = self.distance(current.position, neighbor_pos)
                tentative_g = current.g_score + move_cost

                # Check if better path
                neighbor_node = Node(
                    f_score=tentative_g + self.heuristic(neighbor_pos, goal_cell),
                    position=neighbor_pos,
                    g_score=tentative_g,
                    parent=current
                )

                heapq.heappush(open_set, neighbor_node)

        return []  # No path found

    def reconstruct_path(self, node):
        """Reconstruct path from goal to start"""
        path = []
        current = node

        while current:
            path.append(self.grid_to_world(current.position))
            current = current.parent

        return list(reversed(path))

    def get_neighbors(self, pos):
        """Get 8-connected neighbors"""
        x, y = pos
        neighbors = []

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                nx, ny = x + dx, y + dy
                if self.is_valid((nx, ny)):
                    neighbors.append((nx, ny))

        return neighbors

    def is_valid(self, pos):
        """Check if position is within grid bounds"""
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, pos):
        """Check if cell is free"""
        x, y = pos
        return self.grid[y, x] < 0.5  # Occupancy threshold

    def heuristic(self, pos1, pos2):
        """Euclidean distance heuristic"""
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def distance(self, pos1, pos2):
        """Actual distance between adjacent cells"""
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])

        if dx + dy == 2:  # Diagonal
            return np.sqrt(2)
        else:  # Straight
            return 1.0

    def world_to_grid(self, pos):
        """Convert world coordinates to grid indices"""
        x = int(pos[0] / self.resolution)
        y = int(pos[1] / self.resolution)
        return (x, y)

    def grid_to_world(self, pos):
        """Convert grid indices to world coordinates"""
        x = (pos[0] + 0.5) * self.resolution
        y = (pos[1] + 0.5) * self.resolution
        return (x, y)
```

### RRT (Rapidly-Exploring Random Trees)

```python
import numpy as np
import matplotlib.pyplot as plt

class RRTPlanner:
    """
    RRT path planning for continuous space
    """

    def __init__(self, start, goal, obstacle_list, rand_area,
                 max_iter=500, expand_dis=0.5, goal_sample_rate=5):
        """
        Args:
            start: (x, y) start position
            goal: (x, y) goal position
            obstacle_list: List of (x, y, radius) obstacles
            rand_area: [x_min, x_max, y_min, y_max] sampling area
            max_iter: Maximum iterations
            expand_dis: Step size for tree expansion
            goal_sample_rate: Percentage to sample goal directly
        """
        self.start = Node(start[0], start[1])
        self.goal = Node(goal[0], goal[1])
        self.obstacle_list = obstacle_list
        self.rand_area = rand_area
        self.max_iter = max_iter
        self.expand_dis = expand_dis
        self.goal_sample_rate = goal_sample_rate

        self.node_list = [self.start]

    class Node:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.path_x = []
            self.path_y = []
            self.parent = None

    def plan(self):
        """Execute RRT planning"""
        for i in range(self.max_iter):
            # Sample random point (or goal with probability)
            if np.random.rand() < self.goal_sample_rate / 100:
                rnd_node = self.Node(self.goal.x, self.goal.y)
            else:
                rnd_node = self.sample_random_node()

            # Find nearest node in tree
            nearest_node = self.get_nearest_node(rnd_node)

            # Extend tree towards random node
            new_node = self.steer(nearest_node, rnd_node)

            # Check for collisions
            if not self.check_collision(new_node):
                self.node_list.append(new_node)

                # Check if goal reached
                if self.distance_to_goal(new_node) <= self.expand_dis:
                    final_node = self.steer(new_node, self.goal)
                    if not self.check_collision(final_node):
                        return self.generate_final_path(len(self.node_list) - 1)

        return None  # No path found

    def sample_random_node(self):
        """Sample random point in free space"""
        x = np.random.uniform(self.rand_area[0], self.rand_area[1])
        y = np.random.uniform(self.rand_area[2], self.rand_area[3])
        return self.Node(x, y)

    def get_nearest_node(self, rnd_node):
        """Find nearest node in tree to random node"""
        distances = [(node.x - rnd_node.x)**2 + (node.y - rnd_node.y)**2
                    for node in self.node_list]
        nearest_idx = np.argmin(distances)
        return self.node_list[nearest_idx]

    def steer(self, from_node, to_node):
        """Steer from from_node towards to_node by expand_dis"""
        new_node = self.Node(from_node.x, from_node.y)
        new_node.parent = from_node

        # Calculate direction
        dx = to_node.x - from_node.x
        dy = to_node.y - from_node.y
        dist = np.hypot(dx, dy)

        # Extend by expand_dis or reach to_node
        if dist <= self.expand_dis:
            new_node.x = to_node.x
            new_node.y = to_node.y
        else:
            new_node.x = from_node.x + self.expand_dis * dx / dist
            new_node.y = from_node.y + self.expand_dis * dy / dist

        new_node.path_x = [from_node.x, new_node.x]
        new_node.path_y = [from_node.y, new_node.y]

        return new_node

    def check_collision(self, node):
        """Check if node collides with obstacles"""
        for (ox, oy, radius) in self.obstacle_list:
            dx = node.x - ox
            dy = node.y - oy
            dist = np.hypot(dx, dy)

            if dist <= radius:
                return True  # Collision

        return False

    def distance_to_goal(self, node):
        """Distance from node to goal"""
        return np.hypot(node.x - self.goal.x, node.y - self.goal.y)

    def generate_final_path(self, goal_idx):
        """Generate final path from start to goal"""
        path = [[self.goal.x, self.goal.y]]
        node = self.node_list[goal_idx]

        while node.parent:
            path.append([node.x, node.y])
            node = node.parent

        path.append([node.x, node.y])

        return list(reversed(path))
```

### Hybrid A* for Car-Like Vehicles

```cpp
#include <vector>
#include <queue>
#include <cmath>
#include <Eigen/Dense>

class HybridAStarPlanner {
public:
    struct VehicleParams {
        double wheelbase = 2.7;       // meters
        double max_steering_angle = 0.6;  // radians (~35 degrees)
        double min_turning_radius = wheelbase / std::tan(max_steering_angle);
    };

    struct State {
        double x, y, theta;  // Position and heading
        double g_cost, h_cost;
        std::vector<State> path;

        double f_cost() const { return g_cost + h_cost; }

        bool operator>(const State& other) const {
            return f_cost() > other.f_cost();
        }
    };

    HybridAStarPlanner(const VehicleParams& params) : params_(params) {}

    std::vector<State> plan(const State& start, const State& goal,
                           const std::vector<std::vector<double>>& obstacle_map) {
        std::priority_queue<State, std::vector<State>, std::greater<State>> open_set;

        State start_state = start;
        start_state.g_cost = 0.0;
        start_state.h_cost = heuristic(start, goal);

        open_set.push(start_state);

        while (!open_set.empty()) {
            State current = open_set.top();
            open_set.pop();

            // Check if goal reached
            if (distance(current, goal) < 0.5 &&
                std::abs(current.theta - goal.theta) < 0.1) {
                return current.path;
            }

            // Expand with motion primitives
            for (const auto& next_state : generate_successors(current)) {
                if (!is_collision_free(next_state, obstacle_map)) {
                    continue;
                }

                // Calculate costs
                double tentative_g = current.g_cost + distance(current, next_state);

                State new_state = next_state;
                new_state.g_cost = tentative_g;
                new_state.h_cost = heuristic(next_state, goal);
                new_state.path = current.path;
                new_state.path.push_back(current);

                open_set.push(new_state);
            }
        }

        return {};  // No path found
    }

private:
    VehicleParams params_;

    std::vector<State> generate_successors(const State& current) {
        std::vector<State> successors;

        // Motion primitives: different steering angles
        std::vector<double> steering_angles = {
            -params_.max_steering_angle,
            -params_.max_steering_angle / 2,
            0.0,
            params_.max_steering_angle / 2,
            params_.max_steering_angle
        };

        double dt = 0.5;  // Time step
        double v = 5.0;   // Velocity (m/s)

        for (double delta : steering_angles) {
            State next;

            // Bicycle model kinematics
            next.x = current.x + v * std::cos(current.theta) * dt;
            next.y = current.y + v * std::sin(current.theta) * dt;
            next.theta = current.theta + (v / params_.wheelbase) * std::tan(delta) * dt;

            // Normalize angle
            next.theta = std::atan2(std::sin(next.theta), std::cos(next.theta));

            successors.push_back(next);
        }

        return successors;
    }

    double heuristic(const State& state, const State& goal) {
        // Non-holonomic heuristic (Reeds-Shepp distance approximation)
        double dx = goal.x - state.x;
        double dy = goal.y - state.y;
        return std::sqrt(dx*dx + dy*dy);
    }

    double distance(const State& s1, const State& s2) {
        double dx = s2.x - s1.x;
        double dy = s2.y - s1.y;
        return std::sqrt(dx*dx + dy*dy);
    }

    bool is_collision_free(const State& state,
                          const std::vector<std::vector<double>>& obstacle_map) {
        // Check collision with obstacle map
        // Simplified: check if state position is in free space
        int x_idx = static_cast<int>(state.x);
        int y_idx = static_cast<int>(state.y);

        if (x_idx < 0 || x_idx >= obstacle_map.size() ||
            y_idx < 0 || y_idx >= obstacle_map[0].size()) {
            return false;
        }

        return obstacle_map[x_idx][y_idx] < 0.5;
    }
};
```

## Model Predictive Control (MPC)

```cpp
#include <Eigen/Dense>
#include <vector>
#include <qpOASES.hpp>

class MPCController {
public:
    struct MPCParams {
        int horizon = 20;           // Prediction horizon
        double dt = 0.1;            // Time step (100ms)
        double wheelbase = 2.7;     // meters

        // Cost weights
        double q_cte = 100.0;       // Cross-track error
        double q_epsi = 100.0;      // Heading error
        double q_v = 1.0;           // Velocity error
        double r_delta = 100.0;     // Steering input
        double r_a = 10.0;          // Acceleration input
        double r_delta_d = 1000.0;  // Steering rate
        double r_a_d = 10.0;        // Acceleration rate
    };

    MPCController(const MPCParams& params) : params_(params) {}

    struct ControlOutput {
        double steering_angle;
        double acceleration;
        std::vector<double> predicted_x;
        std::vector<double> predicted_y;
    };

    ControlOutput solve(const Eigen::VectorXd& state,
                       const std::vector<double>& ref_x,
                       const std::vector<double>& ref_y,
                       const std::vector<double>& ref_psi,
                       const std::vector<double>& ref_v) {
        // State: [x, y, psi, v, cte, epsi]
        // Inputs: [delta, a]

        int n_states = 6;
        int n_inputs = 2;
        int N = params_.horizon;

        int n_vars = n_states * N + n_inputs * (N - 1);
        int n_constraints = n_states * N;

        // Setup QP problem: min 0.5 * x^T * H * x + g^T * x
        //                   s.t. lbA <= A * x <= ubA
        //                        lb <= x <= ub

        Eigen::MatrixXd H = Eigen::MatrixXd::Zero(n_vars, n_vars);
        Eigen::VectorXd g = Eigen::VectorXd::Zero(n_vars);

        // Build cost function
        for (int t = 0; t < N; ++t) {
            // State costs
            H(t * n_states + 4, t * n_states + 4) = params_.q_cte;  // cte
            H(t * n_states + 5, t * n_states + 5) = params_.q_epsi; // epsi
            H(t * n_states + 3, t * n_states + 3) = params_.q_v;    // v

            if (t < N - 1) {
                // Input costs
                int delta_idx = N * n_states + t * n_inputs;
                int a_idx = delta_idx + 1;

                H(delta_idx, delta_idx) = params_.r_delta;
                H(a_idx, a_idx) = params_.r_a;

                // Input rate costs
                if (t < N - 2) {
                    int next_delta_idx = N * n_states + (t + 1) * n_inputs;
                    int next_a_idx = next_delta_idx + 1;

                    H(delta_idx, delta_idx) += params_.r_delta_d;
                    H(delta_idx, next_delta_idx) = -params_.r_delta_d;
                    H(next_delta_idx, delta_idx) = -params_.r_delta_d;
                    H(next_delta_idx, next_delta_idx) += params_.r_delta_d;

                    H(a_idx, a_idx) += params_.r_a_d;
                    H(a_idx, next_a_idx) = -params_.r_a_d;
                    H(next_a_idx, a_idx) = -params_.r_a_d;
                    H(next_a_idx, next_a_idx) += params_.r_a_d;
                }
            }
        }

        // Setup constraints (vehicle dynamics)
        Eigen::MatrixXd A = Eigen::MatrixXd::Zero(n_constraints, n_vars);
        Eigen::VectorXd lbA = Eigen::VectorXd::Zero(n_constraints);
        Eigen::VectorXd ubA = Eigen::VectorXd::Zero(n_constraints);

        // Initial state constraint
        for (int i = 0; i < n_states; ++i) {
            A(i, i) = 1.0;
            lbA(i) = state(i);
            ubA(i) = state(i);
        }

        // Dynamics constraints
        for (int t = 1; t < N; ++t) {
            // x_{t+1} = x_t + v_t * cos(psi_t) * dt
            A(t * n_states + 0, (t-1) * n_states + 0) = 1.0;  // x_t
            A(t * n_states + 0, t * n_states + 0) = -1.0;      // x_{t+1}
            // ... (complete dynamics implementation)
        }

        // Variable bounds
        Eigen::VectorXd lb = Eigen::VectorXd::Constant(n_vars, -1e9);
        Eigen::VectorXd ub = Eigen::VectorXd::Constant(n_vars, 1e9);

        // Steering angle limits
        for (int t = 0; t < N - 1; ++t) {
            int delta_idx = N * n_states + t * n_inputs;
            lb(delta_idx) = -0.6;  // -35 degrees
            ub(delta_idx) = 0.6;   // +35 degrees
        }

        // Acceleration limits
        for (int t = 0; t < N - 1; ++t) {
            int a_idx = N * n_states + t * n_inputs + 1;
            lb(a_idx) = -3.0;  // -3 m/s²
            ub(a_idx) = 2.0;   // +2 m/s²
        }

        // Solve QP using qpOASES
        qpOASES::QProblem qp(n_vars, n_constraints);
        qpOASES::Options options;
        options.printLevel = qpOASES::PL_NONE;
        qp.setOptions(options);

        int nWSR = 100;  // Max working set recalculations
        qp.init(H.data(), g.data(), A.data(), lb.data(), ub.data(),
               lbA.data(), ubA.data(), nWSR);

        Eigen::VectorXd solution(n_vars);
        qp.getPrimalSolution(solution.data());

        // Extract control inputs
        ControlOutput output;
        output.steering_angle = solution(N * n_states);
        output.acceleration = solution(N * n_states + 1);

        // Extract predicted trajectory
        for (int t = 0; t < N; ++t) {
            output.predicted_x.push_back(solution(t * n_states + 0));
            output.predicted_y.push_back(solution(t * n_states + 1));
        }

        return output;
    }

private:
    MPCParams params_;
};
```

## Pure Pursuit Controller

```cpp
#include <Eigen/Dense>
#include <vector>
#include <cmath>

class PurePursuitController {
public:
    PurePursuitController(double wheelbase, double lookahead_distance)
        : wheelbase_(wheelbase), lookahead_distance_(lookahead_distance) {}

    double compute_steering_angle(const Eigen::Vector3d& vehicle_state,
                                  const std::vector<Eigen::Vector2d>& path) {
        // vehicle_state: [x, y, heading]

        // Find lookahead point on path
        Eigen::Vector2d lookahead_point = find_lookahead_point(vehicle_state, path);

        // Transform lookahead point to vehicle frame
        double dx = lookahead_point.x() - vehicle_state.x();
        double dy = lookahead_point.y() - vehicle_state.y();

        double alpha = std::atan2(dy, dx) - vehicle_state.z();

        // Pure pursuit formula
        double steering_angle = std::atan2(2.0 * wheelbase_ * std::sin(alpha),
                                          lookahead_distance_);

        return steering_angle;
    }

private:
    double wheelbase_;
    double lookahead_distance_;

    Eigen::Vector2d find_lookahead_point(const Eigen::Vector3d& vehicle_state,
                                        const std::vector<Eigen::Vector2d>& path) {
        Eigen::Vector2d vehicle_pos(vehicle_state.x(), vehicle_state.y());

        // Find closest point on path
        double min_dist = std::numeric_limits<double>::max();
        size_t closest_idx = 0;

        for (size_t i = 0; i < path.size(); ++i) {
            double dist = (path[i] - vehicle_pos).norm();
            if (dist < min_dist) {
                min_dist = dist;
                closest_idx = i;
            }
        }

        // Search ahead for lookahead point
        for (size_t i = closest_idx; i < path.size(); ++i) {
            double dist = (path[i] - vehicle_pos).norm();
            if (dist >= lookahead_distance_) {
                return path[i];
            }
        }

        // Return last point if lookahead not found
        return path.back();
    }
};
```

## Stanley Controller

```cpp
class StanleyController {
public:
    StanleyController(double wheelbase, double k_e = 0.5, double k_v = 1.0)
        : wheelbase_(wheelbase), k_e_(k_e), k_v_(k_v) {}

    double compute_steering_angle(const Eigen::Vector3d& vehicle_state,
                                  double velocity,
                                  const std::vector<Eigen::Vector2d>& path) {
        // Find closest point on path
        auto [cte, heading_error] = compute_errors(vehicle_state, path);

        // Stanley law
        double steering_angle = heading_error +
                              std::atan2(k_e_ * cte, k_v_ + velocity);

        return steering_angle;
    }

private:
    double wheelbase_;
    double k_e_;  // Cross-track error gain
    double k_v_;  // Velocity gain

    std::pair<double, double> compute_errors(const Eigen::Vector3d& vehicle_state,
                                            const std::vector<Eigen::Vector2d>& path) {
        // Find closest point and compute cross-track error
        Eigen::Vector2d vehicle_pos(vehicle_state.x(), vehicle_state.y());

        double min_dist = std::numeric_limits<double>::max();
        size_t closest_idx = 0;

        for (size_t i = 0; i < path.size() - 1; ++i) {
            Eigen::Vector2d segment = path[i+1] - path[i];
            Eigen::Vector2d to_vehicle = vehicle_pos - path[i];

            double t = std::clamp(to_vehicle.dot(segment) / segment.squaredNorm(), 0.0, 1.0);
            Eigen::Vector2d closest_pt = path[i] + t * segment;

            double dist = (vehicle_pos - closest_pt).norm();
            if (dist < min_dist) {
                min_dist = dist;
                closest_idx = i;
            }
        }

        // Cross-track error (signed)
        Eigen::Vector2d segment = path[closest_idx + 1] - path[closest_idx];
        Eigen::Vector2d to_vehicle = vehicle_pos - path[closest_idx];

        double cross = segment.x() * to_vehicle.y() - segment.y() * to_vehicle.x();
        double cte = (cross > 0) ? min_dist : -min_dist;

        // Heading error
        double path_heading = std::atan2(segment.y(), segment.x());
        double heading_error = path_heading - vehicle_state.z();

        // Normalize to [-π, π]
        while (heading_error > M_PI) heading_error -= 2 * M_PI;
        while (heading_error < -M_PI) heading_error += 2 * M_PI;

        return {cte, heading_error};
    }
};
```

## Behavior Planning (Finite State Machine)

```cpp
#include <string>
#include <map>
#include <functional>

class BehaviorPlanner {
public:
    enum class State {
        LANE_KEEPING,
        LANE_CHANGE_LEFT,
        LANE_CHANGE_RIGHT,
        ADAPTIVE_CRUISE,
        EMERGENCY_BRAKE
    };

    BehaviorPlanner() : current_state_(State::LANE_KEEPING) {}

    State update(const SceneContext& context) {
        // State transition logic
        switch (current_state_) {
            case State::LANE_KEEPING:
                if (context.left_lane_clear && context.should_overtake) {
                    current_state_ = State::LANE_CHANGE_LEFT;
                } else if (context.leading_vehicle_distance < 50.0) {
                    current_state_ = State::ADAPTIVE_CRUISE;
                }
                break;

            case State::ADAPTIVE_CRUISE:
                if (context.leading_vehicle_distance < 10.0 &&
                    context.leading_vehicle_velocity < context.ego_velocity * 0.5) {
                    current_state_ = State::EMERGENCY_BRAKE;
                } else if (context.leading_vehicle_distance > 70.0) {
                    current_state_ = State::LANE_KEEPING;
                }
                break;

            case State::LANE_CHANGE_LEFT:
                if (context.lane_change_complete) {
                    current_state_ = State::LANE_KEEPING;
                }
                break;

            // ... other transitions
        }

        return current_state_;
    }

    struct SceneContext {
        double ego_velocity;
        double leading_vehicle_distance;
        double leading_vehicle_velocity;
        bool left_lane_clear;
        bool right_lane_clear;
        bool should_overtake;
        bool lane_change_complete;
        bool emergency_detected;
    };

private:
    State current_state_;
};
```

## Performance Targets

- **Path Planning**: < 100ms for 100m horizon
- **MPC**: < 50ms solve time (20-step horizon)
- **Control Loop**: 10-50 Hz (AUTOSAR compliant)
- **Trajectory Smoothness**: Jerk < 2 m/s³

## Standards

- **ISO 26262**: ASIL D for planning/control
- **ISO 22179**: Full-speed ACC requirements
- **SAE J3016**: L2-L5 automation levels

## Related Skills

- sensor-fusion-perception.md
- adas-features-implementation.md
- hd-maps-localization.md
