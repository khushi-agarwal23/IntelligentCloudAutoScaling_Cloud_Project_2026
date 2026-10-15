"""E-Commerce Autoscaling RL Environment.

This module provides the ECommerceScalingEnv class, a Gymnasium-compatible reinforcement
learning environment for dynamic resource autoscaling of e-commerce web applications.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

# Gymnasium import with lightweight fallback shim if gymnasium is not yet installed
try:
    import gymnasium as gym
    from gymnasium import spaces

    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False

    class _BaseSpaces:
        class Box:
            def __init__(
                self,
                low: Union[float, np.ndarray],
                high: Union[float, np.ndarray],
                shape: Optional[Tuple[int, ...]] = None,
                dtype: Any = np.float32,
            ) -> None:
                self.dtype = np.dtype(dtype)
                if shape is not None and np.isscalar(low) and np.isscalar(high):
                    self.low = np.full(shape, low, dtype=self.dtype)
                    self.high = np.full(shape, high, dtype=self.dtype)
                    self.shape = shape
                else:
                    self.low = np.array(low, dtype=self.dtype)
                    self.high = np.array(high, dtype=self.dtype)
                    self.shape = self.low.shape

            def sample(self) -> np.ndarray:
                return np.random.uniform(self.low, self.high).astype(self.dtype)

            def contains(self, x: Any) -> bool:
                arr = np.asarray(x, dtype=self.dtype)
                return bool(arr.shape == self.shape and np.all(arr >= self.low) and np.all(arr <= self.high))

        class Discrete:
            def __init__(self, n: int, start: int = 0) -> None:
                self.n = int(n)
                self.start = int(start)

            def sample(self) -> int:
                return int(np.random.randint(self.start, self.start + self.n))

            def contains(self, x: Any) -> bool:
                try:
                    val = int(x)
                    return self.start <= val < self.start + self.n
                except (ValueError, TypeError):
                    return False

    class _BaseEnv:
        metadata: Dict[str, Any] = {"render_modes": ["human"], "render_fps": 4}
        action_space: Any = None
        observation_space: Any = None
        np_random: np.random.Generator = np.random.default_rng()

        def reset(
            self,
            *,
            seed: Optional[int] = None,
            options: Optional[Dict[str, Any]] = None,
        ) -> Tuple[np.ndarray, Dict[str, Any]]:
            if seed is not None:
                self.np_random = np.random.default_rng(seed)
            return np.zeros(1, dtype=np.float32), {}

        def step(self, action: Any) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
            raise NotImplementedError

        def render(self) -> None:
            pass

        def close(self) -> None:
            pass

    gym = type("gym", (), {"Env": _BaseEnv})()  # type: ignore
    spaces = _BaseSpaces()  # type: ignore

from environment.workload_simulator import WorkloadSimulator

logger = logging.getLogger(__name__)


class ECommerceScalingEnv(gym.Env):
    """Gymnasium environment for autonomous e-commerce horizontal autoscaling.

    The agent observes workload demand, container resource utilization, queuing metrics,
    and SLA compliance, and takes discrete scaling actions: Hold, Scale Out, or Scale In.

    Observation Space (Box, float32, 10 dimensions):
        0. cpu_util (0 - 100): Cluster CPU utilization percentage.
        1. memory_util (0 - 100): Cluster Memory utilization percentage.
        2. request_rate (0 - 10000): Incoming request rate in requests/sec.
        3. response_time (0 - 5000): End-to-end response latency in milliseconds.
        4. active_instances (1 - 50): Number of active application instances.
        5. queue_length (0 - 10000): Number of queued/unserved requests.
        6. time_of_day (0 - 1): Normalized progress through 24-hour cycle.
        7. sla_violation_flag (0 or 1): Binary indicator of SLA threshold violation.
        8. cost_per_step (0 - 100): Monetary infrastructure cost incurred in current step.
        9. utilization_ratio (0 - 100): Ratio of request rate to aggregate cluster capacity.

    Action Space (Discrete(3)):
        - 0: Hold (keep current instance count)
        - 1: Scale Out (+1 active instance, bounded by max_instances)
        - 2: Scale In (-1 active instance, bounded by min_instances)

    Reward Function:
        R = alpha * throughput_norm - beta * sla_penalty - gamma * cost_norm - delta * thrashing_penalty
        where:
        - throughput_norm = min(request_rate, active_instances * capacity) / request_rate
        - sla_penalty = max(0, response_time - sla_threshold) / sla_threshold
        - cost_norm = active_instances / max_instances
        - thrashing_penalty = 1.0 if action != 0 and last_action != 0 and action != last_action else 0.0
        - alpha = 1.0, beta = 2.0, gamma = 0.5, delta = 0.3
    """

    metadata = {"render_modes": ["human"], "render_fps": 4}

    # Action mappings
    ACTION_HOLD: int = 0
    ACTION_SCALE_OUT: int = 1
    ACTION_SCALE_IN: int = 2

    def __init__(
        self,
        data_path: Optional[Union[str, Path]] = None,
        episode_length: int = 288,
        seed: int = 42,
        per_instance_capacity: float = 200.0,
        sla_threshold: float = 500.0,
        min_instances: int = 1,
        max_instances: int = 50,
        initial_instances: int = 2,
        cost_per_instance: float = 2.0,
        alpha: float = 1.0,
        beta: float = 2.0,
        gamma: float = 0.5,
        delta: float = 0.3,
        workload_simulator: Optional[WorkloadSimulator] = None,
    ) -> None:
        """Initialize the ECommerceScalingEnv.

        Args:
            data_path: Optional file path to Alibaba 2018 cluster trace data CSV.
            episode_length: Number of time steps per episode (default 288: 24h at 5-min intervals).
            seed: Random seed for workload simulator and environment.
            per_instance_capacity: Processing capacity per container (default 200 req/sec).
            sla_threshold: Maximum allowed response time before SLA penalty (default 500 ms).
            min_instances: Minimum allowable instance count (default 1).
            max_instances: Maximum allowable instance count (default 50).
            initial_instances: Starting instance count upon reset (default 2).
            cost_per_instance: Infrastructure cost per instance per step (default 2.0).
            alpha: Weight for throughput reward component (default 1.0).
            beta: Weight for SLA violation penalty component (default 2.0).
            gamma: Weight for monetary cost penalty component (default 0.5).
            delta: Weight for thrashing penalty component (default 0.3).
            workload_simulator: Optional custom WorkloadSimulator instance.
        """
        super().__init__()

        self.episode_length = int(episode_length)
        self.per_instance_capacity = float(per_instance_capacity)
        self.sla_threshold = float(sla_threshold)
        self.min_instances = int(min_instances)
        self.max_instances = int(max_instances)
        self.initial_instances = int(initial_instances)
        self.cost_per_instance = float(cost_per_instance)
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.gamma = float(gamma)
        self.delta = float(delta)

        # Internal workload simulator
        if workload_simulator is not None:
            self.simulator = workload_simulator
        else:
            self.simulator = WorkloadSimulator(
                data_path=data_path,
                episode_length=self.episode_length,
                seed=seed,
                capacity=self.per_instance_capacity,
            )

        # Action space: 0=Hold, 1=Scale Out, 2=Scale In
        self.action_space = spaces.Discrete(3)

        # Observation space bounds (10 dimensions):
        # 0: cpu_util (0-100)
        # 1: memory_util (0-100)
        # 2: request_rate (0-10000)
        # 3: response_time (0-5000 ms)
        # 4: active_instances (1-50)
        # 5: queue_length (0-10000)
        # 6: time_of_day (0-1)
        # 7: sla_violation_flag (0-1)
        # 8: cost_per_step (0-100)
        # 9: utilization_ratio (0-100)
        obs_low = np.array(
            [0.0, 0.0, 0.0, 0.0, float(self.min_instances), 0.0, 0.0, 0.0, 0.0, 0.0],
            dtype=np.float32,
        )
        obs_high = np.array(
            [100.0, 100.0, 10000.0, 5000.0, float(self.max_instances), 10000.0, 1.0, 1.0, 100.0, 100.0],
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(low=obs_low, high=obs_high, dtype=np.float32)

        # Episode runtime state variables
        self.active_instances: int = self.initial_instances
        self.current_step: int = 0
        self.last_action: int = self.ACTION_HOLD

        # Episode cumulative metrics
        self.total_reward: float = 0.0
        self.sla_violations: int = 0
        self.total_cost: float = 0.0
        self.scaling_events: int = 0

        # Latest state snapshot
        self._current_obs: Optional[np.ndarray] = None
        self._current_info: Dict[str, Any] = {}

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment to initial conditions.

        Args:
            seed: Optional random seed for reproducible episodes.
            options: Optional configuration dictionary.

        Returns:
            Tuple of (initial_observation, info_dictionary).
        """
        super().reset(seed=seed)

        if seed is not None:
            self.simulator.reset(seed=seed)

        # Reset episode state variables
        self.active_instances = int(self.initial_instances)
        self.current_step = 0
        self.last_action = self.ACTION_HOLD

        # Reset cumulative tracking metrics
        self.total_reward = 0.0
        self.sla_violations = 0
        self.total_cost = 0.0
        self.scaling_events = 0

        # Query simulator at step 0 with initial instances
        workload = self.simulator.get_workload(step=0, active_instances=self.active_instances)
        request_rate = float(workload["request_rate"])
        cpu_util = float(workload["cpu_util"])
        memory_util = float(workload["memory_util"])
        response_time = float(workload["response_time"])

        total_capacity = float(self.active_instances * self.per_instance_capacity)
        queue_length = float(np.clip(max(0.0, request_rate - total_capacity), 0.0, 10000.0))
        time_of_day = 0.0
        sla_violation_flag = 1.0 if response_time > self.sla_threshold else 0.0
        cost_per_step = float(np.clip(self.active_instances * self.cost_per_instance, 0.0, 100.0))
        utilization_ratio = float(request_rate / max(1e-6, total_capacity))

        obs = np.array(
            [
                cpu_util,
                memory_util,
                request_rate,
                response_time,
                float(self.active_instances),
                queue_length,
                time_of_day,
                sla_violation_flag,
                cost_per_step,
                utilization_ratio,
            ],
            dtype=np.float32,
        )

        self._current_obs = obs
        self._current_info = {
            "step": self.current_step,
            "active_instances": self.active_instances,
            "request_rate": request_rate,
            "cpu_util": cpu_util,
            "memory_util": memory_util,
            "response_time": response_time,
            "queue_length": queue_length,
            "time_of_day": time_of_day,
            "sla_violation": bool(sla_violation_flag > 0.5),
            "cost_per_step": cost_per_step,
            "utilization_ratio": utilization_ratio,
            "throughput_norm": 1.0,
            "sla_penalty": 0.0,
            "cost_norm": float(self.active_instances / self.max_instances),
            "thrashing_penalty": 0.0,
            "total_reward": self.total_reward,
            "sla_violations": self.sla_violations,
            "total_cost": self.total_cost,
            "scaling_events": self.scaling_events,
        }

        return obs, self._current_info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Execute one autoscaling time step.

        Args:
            action: Discrete scaling action (0=Hold, 1=Scale Out, 2=Scale In).

        Returns:
            Tuple of (observation, reward, terminated, truncated, info).
        """
        action = int(action)
        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action {action}. Must be one of {list(range(self.action_space.n))}.")

        # 1. Update instance count based on action
        if action == self.ACTION_SCALE_OUT:
            self.active_instances = min(self.max_instances, self.active_instances + 1)
            self.scaling_events += 1
        elif action == self.ACTION_SCALE_IN:
            self.active_instances = max(self.min_instances, self.active_instances - 1)
            self.scaling_events += 1

        # 2. Query workload simulator for current step with updated instance count
        workload = self.simulator.get_workload(self.current_step, self.active_instances)
        request_rate = float(workload["request_rate"])
        cpu_util = float(workload["cpu_util"])
        memory_util = float(workload["memory_util"])
        response_time = float(workload["response_time"])

        total_capacity = float(self.active_instances * self.per_instance_capacity)

        # 3. Compute derived state features
        queue_length = float(np.clip(max(0.0, request_rate - total_capacity), 0.0, 10000.0))
        time_of_day = float((self.current_step % self.episode_length) / self.episode_length)
        sla_violation_flag = 1.0 if response_time > self.sla_threshold else 0.0
        cost_per_step = float(np.clip(self.active_instances * self.cost_per_instance, 0.0, 100.0))
        utilization_ratio = float(request_rate / max(1e-6, total_capacity))

        # 4. Compute reward components:
        # Throughput normalized: min(request_rate, active_instances * capacity) / request_rate
        if request_rate > 0.0:
            throughput_norm = float(min(request_rate, total_capacity) / request_rate)
        else:
            throughput_norm = 1.0
        throughput_norm = float(np.clip(throughput_norm, 0.0, 1.0))

        # SLA penalty: max(0, response_time - sla_threshold) / sla_threshold
        sla_penalty = float(max(0.0, response_time - self.sla_threshold) / self.sla_threshold)

        # Cost normalized: active_instances / max_instances
        cost_norm = float(self.active_instances / self.max_instances)

        # Thrashing penalty: 1.0 if rapid alternating scale out/in without holding
        if action != self.ACTION_HOLD and self.last_action != self.ACTION_HOLD and action != self.last_action:
            thrashing_penalty = 1.0
        else:
            thrashing_penalty = 0.0

        # Composite reward formula
        reward = float(
            self.alpha * throughput_norm
            - self.beta * sla_penalty
            - self.gamma * cost_norm
            - self.delta * thrashing_penalty
        )

        # 5. Update cumulative episode metrics
        self.total_reward += reward
        if sla_violation_flag > 0.5:
            self.sla_violations += 1
        self.total_cost += cost_per_step

        # 6. Advance step and update last action
        self.last_action = action
        self.current_step += 1

        # 7. Check termination and truncation
        terminated = False
        truncated = bool(self.current_step >= self.episode_length)

        # 8. Assemble observation vector
        obs = np.array(
            [
                cpu_util,
                memory_util,
                request_rate,
                response_time,
                float(self.active_instances),
                queue_length,
                time_of_day,
                sla_violation_flag,
                cost_per_step,
                utilization_ratio,
            ],
            dtype=np.float32,
        )

        # 9. Detailed diagnostic info
        info: Dict[str, Any] = {
            "step": self.current_step,
            "action": action,
            "active_instances": self.active_instances,
            "request_rate": request_rate,
            "cpu_util": cpu_util,
            "memory_util": memory_util,
            "response_time": response_time,
            "queue_length": queue_length,
            "time_of_day": time_of_day,
            "sla_violation": bool(sla_violation_flag > 0.5),
            "cost_per_step": cost_per_step,
            "utilization_ratio": utilization_ratio,
            "throughput_norm": throughput_norm,
            "sla_penalty": sla_penalty,
            "cost_norm": cost_norm,
            "thrashing_penalty": thrashing_penalty,
            "step_reward": reward,
            "total_reward": self.total_reward,
            "sla_violations": self.sla_violations,
            "total_cost": self.total_cost,
            "scaling_events": self.scaling_events,
        }

        self._current_obs = obs
        self._current_info = info

        return obs, reward, terminated, truncated, info

    def render(self) -> None:
        """Render a readable status summary to stdout."""
        if self._current_info:
            info = self._current_info
            print(
                f"[Step {info['step']:03d}/{self.episode_length}] "
                f"Instances: {info['active_instances']:02d} | "
                f"Req/s: {info['request_rate']:6.1f} | "
                f"RT: {info['response_time']:6.1f}ms | "
                f"SLA Violations: {info['sla_violations']:02d} | "
                f"Step Reward: {info.get('step_reward', 0.0):+.3f} | "
                f"Total Reward: {info['total_reward']:+.2f}"
            )

    def close(self) -> None:
        """Clean up environment resources."""
        pass
