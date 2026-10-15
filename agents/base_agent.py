"""Base agent interface for reinforcement learning in cloud autoscaling.

This module provides the abstract base class `BaseAgent` that all RL agents
(e.g., DQN, PPO, rule-based baselines) must inherit from in this project.
It defines standard lifecycle methods (action selection, training, persistence)
and a unified evaluation routine tracking domain-specific autoscaling metrics.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all reinforcement learning agents in the autoscaling system.

    Subclasses must implement:
        - `select_action`: Mapping environment observations to discrete autoscaling actions.
        - `train`: Updating policy/value networks or parameters from experience.
        - `save`: Persisting agent checkpoints to disk.
        - `load`: Restoring agent state from disk checkpoints.

    The class provides a built-in `evaluate` routine that standardizes reporting
    across agents by evaluating policies deterministically over multiple episodes
    and computing critical autoscaling Key Performance Indicators (KPIs):
        - Average total reward
        - Average SLA violations
        - Average resource / VM infrastructure cost
        - Average scaling actions (scale-up / scale-down events)
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the base agent."""
        super().__init__()

    @abstractmethod
    def select_action(self, state: np.ndarray, training: bool = False) -> int:
        """Select an action given the current environment state.

        Args:
            state: Environment observation array representing system metrics
                (e.g., CPU, memory, request latency, request rate, replica count).
            training: Whether action selection is performed during training
                (e.g., enabling exploration like epsilon-greedy or stochastic sampling)
                or during inference/evaluation (greedy / deterministic).

        Returns:
            int: Discrete action index (e.g., 0: Scale Down, 1: No-op, 2: Scale Up).
        """
        pass

    @abstractmethod
    def train(self, experiences: Any = None) -> Any:
        """Train the agent using experience transitions or replay memory.

        Args:
            experiences: Experience transition tuple (s, a, r, s', done),
                a batch of transitions, or None if the agent pulls directly
                from an internal replay buffer.

        Returns:
            Any: Training loss or dictionary of training diagnostic metrics.
        """
        pass

    @abstractmethod
    def save(self, path: Union[str, Path]) -> None:
        """Save the agent's model weights, configuration, and optimizer state.

        Args:
            path: Destination file path for the checkpoint (e.g., '.pt' or '.zip').
        """
        pass

    @abstractmethod
    def load(self, path: Union[str, Path]) -> None:
        """Load the agent's model weights, configuration, and optimizer state.

        Args:
            path: Source file path of the checkpoint to restore.
        """
        pass

    def evaluate(
        self,
        env: Any,
        n_episodes: int = 10,
    ) -> Dict[str, float]:
        """Evaluate the agent's policy in the autoscaling environment.

        Executes `n_episodes` using greedy/deterministic action selection,
        tracking cumulative reward, SLA violations, infrastructure cost,
        and scaling events.

        Compatible with Gymnasium and standard Gym environments (supporting both
        5-tuple and 4-tuple `step` return signatures).

        Args:
            env: Autoscaling environment instance adhering to the Gym/Gymnasium API.
            n_episodes: Number of complete evaluation episodes to run. Defaults to 10.

        Returns:
            Dict[str, float]: Evaluation statistics containing:
                - `avg_reward`: Mean cumulative reward per episode.
                - `avg_sla_violations`: Mean SLA violation count per episode.
                - `avg_cost`: Mean infrastructure cost per episode.
                - `avg_scaling_events`: Mean scaling decisions per episode.
                - `std_reward`: Standard deviation of episode rewards.
                - `avg_episode_length`: Mean episode duration in steps.

        Raises:
            ValueError: If `n_episodes` is less than 1.
        """
        if n_episodes < 1:
            raise ValueError(f"n_episodes must be positive, got {n_episodes}")

        episode_rewards: List[float] = []
        episode_sla_violations: List[float] = []
        episode_costs: List[float] = []
        episode_scaling_events: List[float] = []
        episode_lengths: List[int] = []

        for episode_idx in range(n_episodes):
            # Reset environment (handle Gymnasium (obs, info) vs Gym obs)
            reset_result = env.reset()
            if isinstance(reset_result, tuple) and len(reset_result) == 2:
                state, _ = reset_result
            else:
                state = reset_result

            total_reward: float = 0.0
            total_sla_violations: float = 0.0
            total_cost: float = 0.0
            total_scaling_events: float = 0.0
            step_count: int = 0
            done: bool = False

            while not done:
                # Ensure state is a numpy array
                if not isinstance(state, np.ndarray):
                    state_arr = np.asarray(state, dtype=np.float32)
                else:
                    state_arr = state

                # Select action in evaluation mode (training=False)
                try:
                    action = self.select_action(state_arr, training=False)
                except TypeError:
                    # In case subclass only accepts select_action(state)
                    action = self.select_action(state_arr)

                # Step environment
                step_result = env.step(action)
                if len(step_result) == 5:
                    next_state, reward, terminated, truncated, info = step_result
                    done = bool(terminated or truncated)
                elif len(step_result) == 4:
                    next_state, reward, done_flag, info = step_result
                    done = bool(done_flag)
                else:
                    raise ValueError(
                        f"Unexpected step() return length {len(step_result)}. "
                        "Expected 4 (Gym) or 5 (Gymnasium)."
                    )

                step_info: Dict[str, Any] = info if isinstance(info, dict) else {}

                total_reward += float(reward)
                step_count += 1

                # Extract SLA violations
                # Look for common keys: 'sla_violations', 'sla_violation', 'violations'
                sla_val = step_info.get(
                    "sla_violations",
                    step_info.get("sla_violation", step_info.get("violations", 0.0)),
                )
                total_sla_violations += float(sla_val)

                # Extract infrastructure cost
                # Look for common keys: 'cost', 'server_cost', 'resource_cost', 'step_cost'
                cost_val = step_info.get(
                    "cost",
                    step_info.get(
                        "server_cost",
                        step_info.get("resource_cost", step_info.get("step_cost", 0.0)),
                    ),
                )
                total_cost += float(cost_val)

                # Extract scaling events
                # Look for explicit flags, or fallback to non-noop action (action != 1)
                if "scaling_event" in step_info:
                    total_scaling_events += float(step_info["scaling_event"])
                elif "scaling_events" in step_info:
                    total_scaling_events += float(step_info["scaling_events"])
                elif "is_scaling" in step_info:
                    total_scaling_events += float(step_info["is_scaling"])
                elif "replicas_changed" in step_info:
                    total_scaling_events += float(bool(step_info["replicas_changed"]))
                elif "action_name" in step_info:
                    is_scaling = str(step_info["action_name"]).lower() in (
                        "scale_up",
                        "scale_down",
                        "scale-up",
                        "scale-down",
                    )
                    total_scaling_events += float(is_scaling)
                else:
                    # Conventional 3-action space: 0: Scale Down, 1: No-op, 2: Scale Up
                    # Any action other than 1 represents a scaling action.
                    if action != 1:
                        total_scaling_events += 1.0

                state = next_state

            # Override step accumulators if episode-level summaries exist in info
            if "episode_sla_violations" in step_info:
                total_sla_violations = float(step_info["episode_sla_violations"])
            if "episode_cost" in step_info:
                total_cost = float(step_info["episode_cost"])
            if "episode_scaling_events" in step_info:
                total_scaling_events = float(step_info["episode_scaling_events"])

            episode_rewards.append(total_reward)
            episode_sla_violations.append(total_sla_violations)
            episode_costs.append(total_cost)
            episode_scaling_events.append(total_scaling_events)
            episode_lengths.append(step_count)

            logger.debug(
                "Episode %d/%d - Reward: %.2f, SLA Violations: %.1f, Cost: %.2f, Scaling Events: %.1f",
                episode_idx + 1,
                n_episodes,
                total_reward,
                total_sla_violations,
                total_cost,
                total_scaling_events,
            )

        metrics: Dict[str, float] = {
            "avg_reward": float(np.mean(episode_rewards)),
            "avg_sla_violations": float(np.mean(episode_sla_violations)),
            "avg_cost": float(np.mean(episode_costs)),
            "avg_scaling_events": float(np.mean(episode_scaling_events)),
            "std_reward": float(np.std(episode_rewards)),
            "avg_episode_length": float(np.mean(episode_lengths)),
        }

        return metrics
