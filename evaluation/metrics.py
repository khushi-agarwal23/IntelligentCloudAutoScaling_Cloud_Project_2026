#!/usr/bin/env python3
"""
Evaluation Metrics for RL-Based Autoscaling
=============================================

Computes performance metrics for RL agents and baseline policies,
and generates comparison tables for Student 2 vs Student 3 analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

# Add project root to path
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def compute_metrics(env, agent, n_episodes: int = 10) -> Dict[str, float]:
    """
    Evaluate an RL agent over multiple episodes and compute aggregate metrics.

    Args:
        env: Gymnasium environment (ECommerceScalingEnv).
        agent: Trained agent with select_action(state, training=False) method.
        n_episodes: Number of evaluation episodes.

    Returns:
        Dictionary containing:
            - avg_reward, std_reward
            - avg_sla_violation_rate (fraction of steps violating SLA)
            - avg_cost (average infrastructure cost per episode)
            - avg_scaling_events (average number of scale in/out per episode)
            - avg_throughput (average requests served per episode)
            - avg_response_time (average response time in ms)
    """
    all_rewards = []
    all_sla_rates = []
    all_costs = []
    all_scaling_events = []
    all_throughputs = []
    all_response_times = []

    for _ in range(n_episodes):
        state, _ = env.reset()
        done = False
        episode_reward = 0.0
        episode_steps = 0
        sla_violations = 0
        total_cost = 0.0
        scaling_events = 0
        total_throughput = 0.0
        total_response_time = 0.0

        while not done:
            action = agent.select_action(state, training=False)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            episode_reward += reward
            episode_steps += 1

            # Extract metrics from state
            response_time = next_state[3]  # response_time index
            cost_per_step = next_state[8]  # cost_per_step index
            request_rate = next_state[2]   # request_rate index
            active_instances = next_state[4]  # active_instances index

            # SLA violation check (500ms threshold)
            if response_time > 500.0:
                sla_violations += 1

            total_cost += cost_per_step
            total_response_time += response_time

            # Throughput: min(request_rate, capacity * instances)
            throughput = min(request_rate, 200.0 * active_instances)
            total_throughput += throughput

            # Count scaling actions (not Hold=0)
            if action != 0:
                scaling_events += 1

            state = next_state

        all_rewards.append(episode_reward)
        all_sla_rates.append(sla_violations / max(episode_steps, 1))
        all_costs.append(total_cost)
        all_scaling_events.append(scaling_events)
        all_throughputs.append(total_throughput / max(episode_steps, 1))
        all_response_times.append(total_response_time / max(episode_steps, 1))

    return {
        "avg_reward": float(np.mean(all_rewards)),
        "std_reward": float(np.std(all_rewards)),
        "avg_sla_violation_rate": float(np.mean(all_sla_rates)),
        "avg_cost": float(np.mean(all_costs)),
        "avg_scaling_events": float(np.mean(all_scaling_events)),
        "avg_throughput": float(np.mean(all_throughputs)),
        "avg_response_time": float(np.mean(all_response_times)),
    }


class BaselinePolicy:
    """
    Rule-based threshold auto-scaling baseline representing Student 2's approach.

    Supports:
        - 'threshold' / 'student2_threshold': Scale out when CPU utilization exceeds
          upper threshold (default: 70%), and scale in when it drops below lower threshold (default: 30%).
        - 'random': Random scaling decisions
        - 'always_scale_out': Always adds instances
    """

    def __init__(
        self,
        policy: str = "threshold",
        cpu_scale_out_threshold: float = 70.0,
        cpu_scale_in_threshold: float = 30.0,
        seed: int = 42,
    ):
        self.policy = policy.lower()
        self.cpu_scale_out_threshold = float(cpu_scale_out_threshold)
        self.cpu_scale_in_threshold = float(cpu_scale_in_threshold)
        self.rng = np.random.RandomState(seed)

    def select_action(self, state: np.ndarray, training: bool = False, **kwargs) -> int:
        """Select action based on the baseline policy."""
        if self.policy == "random":
            return self.rng.randint(0, 3)

        elif self.policy == "always_scale_out":
            return 1  # Always scale out

        elif self.policy in ["threshold", "student2_threshold", "rule_based"]:
            cpu_util = state[0]
            active_instances = state[4]
            if cpu_util > self.cpu_scale_out_threshold and active_instances < 50:
                return 1  # Scale out
            elif cpu_util < self.cpu_scale_in_threshold and active_instances > 1:
                return 2  # Scale in
            else:
                return 0  # Hold

        else:
            raise ValueError(f"Unknown policy: {self.policy}")


def compute_baseline_metrics(
    env, policy: str = "threshold", n_episodes: int = 10, seed: int = 42
) -> Dict[str, float]:
    """
    Compute metrics for a baseline policy.

    This represents Student 2's rule-based or threshold-based approach
    for comparison purposes.

    Args:
        env: Gymnasium environment.
        policy: One of 'random', 'always_scale_out', 'threshold'.
        n_episodes: Number of evaluation episodes.
        seed: Random seed for reproducible baselines.

    Returns:
        Same metric dictionary as compute_metrics().
    """
    baseline = BaselinePolicy(policy=policy, seed=seed)
    return compute_metrics(env, baseline, n_episodes=n_episodes)


def create_comparison_table(results_dict: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Create a formatted comparison DataFrame from multiple methods' results.

    Args:
        results_dict: Dictionary mapping method names to their metrics.
            e.g. {'DQN': {...}, 'PPO': {...}, 'Threshold Baseline': {...}}

    Returns:
        pd.DataFrame with methods as rows and metrics as columns.
    """
    rows = []
    for method_name, metrics in results_dict.items():
        row = {"Method": method_name}
        row["Avg Reward"] = f"{metrics.get('avg_reward', 0):.2f}"
        row["SLA Violation %"] = f"{metrics.get('avg_sla_violation_rate', 0) * 100:.1f}%"
        row["Avg Cost"] = f"{metrics.get('avg_cost', 0):.2f}"
        row["Scaling Events"] = f"{metrics.get('avg_scaling_events', 0):.1f}"
        row["Avg Throughput"] = f"{metrics.get('avg_throughput', 0):.1f}"
        row["Avg Response Time (ms)"] = f"{metrics.get('avg_response_time', 0):.1f}"
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.set_index("Method")
    return df


if __name__ == "__main__":
    # Quick test with synthetic data
    from environment.ecommerce_env import ECommerceScalingEnv

    env = ECommerceScalingEnv()
    print("Testing baseline policies...\n")

    for policy_name in ["random", "always_scale_out", "threshold"]:
        metrics = compute_baseline_metrics(env, policy=policy_name, n_episodes=3)
        print(f"{policy_name}: reward={metrics['avg_reward']:.2f}, "
              f"SLA={metrics['avg_sla_violation_rate']*100:.1f}%, "
              f"cost={metrics['avg_cost']:.2f}")

    print("\nDone!")
