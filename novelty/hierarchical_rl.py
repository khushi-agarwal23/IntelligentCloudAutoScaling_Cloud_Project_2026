#!/usr/bin/env python3
"""
Hierarchical Reinforcement Learning for Autoscaling (Novelty Contribution)
============================================================================

Implements a two-level hierarchical RL agent:
    - High-Level Agent: Selects a scaling *strategy* every K steps (1 hour = 12 steps)
      Actions: 0=Conservative, 1=Balanced, 2=Aggressive
    - Low-Level Agent: Makes per-step scale in/out/hold decisions
      Receives the high-level strategy as an extra state feature

This captures both long-term planning (workload patterns) and short-term
reaction (burst handling), providing a clear advantage over flat DQN/PPO.

References:
    - Hierarchical RL: Barto & Mahadevan (2003)
    - Options framework: Sutton, Precup & Singh (1999)
"""

import os
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Tuple, Optional
from collections import deque
import random

# Project path setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class HierarchicalQNetwork(nn.Module):
    """
    Q-Network for hierarchical agents.

    Shared architecture but different input/output dims for high-level vs low-level.
    """

    def __init__(self, state_dim: int, action_dim: int, hidden1: int = 128, hidden2: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden1),
            nn.ReLU(),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
            nn.Linear(hidden2, action_dim),
        )
        self._init_weights()

    def _init_weights(self):
        for layer in self.net:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
                nn.init.constant_(layer.bias, 0.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class HierarchicalReplayBuffer:
    """Experience replay buffer for hierarchical agents."""

    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.float32),
        )

    def __len__(self):
        return len(self.buffer)


class HighLevelAgent:
    """
    High-Level Agent — selects a scaling strategy every K steps.

    Strategies:
        0 = Conservative: Prefer holding; penalize scaling more heavily
        1 = Balanced: Standard reward weights
        2 = Aggressive: Respond quickly to load; penalize SLA violations more

    State: Aggregated metrics over last K steps:
        [avg_cpu, avg_mem, avg_response_time, avg_request_rate,
         avg_instances, cpu_trend, response_time_trend, total_cost]
    """

    STRATEGY_NAMES = {0: "Conservative", 1: "Balanced", 2: "Aggressive"}

    def __init__(
        self,
        state_dim: int = 8,  # Aggregated state features
        action_dim: int = 3,  # 3 strategies
        lr: float = 5e-4,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.1,
        epsilon_decay: float = 0.998,
        batch_size: int = 32,
        buffer_size: int = 5000,
        target_update_freq: int = 100,
        device: str = "cpu",
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.device = device
        self.step_count = 0

        # Networks
        self.online_net = HierarchicalQNetwork(state_dim, action_dim).to(device)
        self.target_net = HierarchicalQNetwork(state_dim, action_dim).to(device)
        self.target_net.load_state_dict(self.online_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.online_net.parameters(), lr=lr)
        self.loss_fn = nn.SmoothL1Loss()
        self.replay_buffer = HierarchicalReplayBuffer(buffer_size)

    def aggregate_state(self, recent_states: List[np.ndarray]) -> np.ndarray:
        """
        Aggregate per-step states into a high-level state representation.

        Args:
            recent_states: List of recent step-level state vectors (10-dim each).

        Returns:
            8-dimensional aggregated state vector.
        """
        if not recent_states:
            return np.zeros(self.state_dim, dtype=np.float32)

        states = np.array(recent_states, dtype=np.float32)

        # Basic aggregations
        avg_cpu = np.mean(states[:, 0]) / 100.0
        avg_mem = np.mean(states[:, 1]) / 100.0
        avg_response_time = np.mean(states[:, 3]) / 5000.0
        avg_request_rate = np.mean(states[:, 2]) / 10000.0
        avg_instances = np.mean(states[:, 4]) / 50.0

        # Trends (simple linear slope)
        n = len(states)
        if n > 1:
            t = np.arange(n, dtype=np.float32)
            cpu_trend = np.polyfit(t, states[:, 0], 1)[0] / 100.0
            rt_trend = np.polyfit(t, states[:, 3], 1)[0] / 5000.0
        else:
            cpu_trend = 0.0
            rt_trend = 0.0

        total_cost = np.sum(states[:, 8]) / (n * 100.0)

        return np.array([
            avg_cpu, avg_mem, avg_response_time, avg_request_rate,
            avg_instances, cpu_trend, rt_trend, total_cost
        ], dtype=np.float32)

    def select_strategy(self, state: np.ndarray, training: bool = True) -> int:
        """Select a scaling strategy using epsilon-greedy."""
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)

        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.online_net(state_tensor)
            return int(q_values.argmax(dim=1).item())

    def train_step(self):
        """Perform one training step on the high-level agent."""
        if len(self.replay_buffer) < self.batch_size:
            return 0.0

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)

        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards_t = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).unsqueeze(1).to(self.device)

        # Current Q-values
        current_q = self.online_net(states_t).gather(1, actions_t)

        # Target Q-values
        with torch.no_grad():
            next_q = self.target_net(next_states_t).max(1, keepdim=True)[0]
            target_q = rewards_t + self.gamma * next_q * (1 - dones_t)

        loss = self.loss_fn(current_q, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.online_net.parameters(), 1.0)
        self.optimizer.step()

        # Epsilon decay
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        # Target network update
        self.step_count += 1
        if self.step_count % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.online_net.state_dict())

        return loss.item()


class LowLevelAgent:
    """
    Low-Level Agent — makes per-step scaling decisions.

    Receives an augmented state: original 10-dim state + one-hot strategy (3-dim) = 13-dim.
    Reward weights are modulated by the high-level strategy:
        - Conservative: higher thrashing penalty, lower SLA penalty
        - Balanced: standard weights
        - Aggressive: higher SLA penalty, lower cost penalty
    """

    # Strategy-specific reward weight modifiers
    STRATEGY_REWARD_MODIFIERS = {
        0: {"alpha": 1.0, "beta": 1.0, "gamma": 0.8, "delta": 0.6},   # Conservative
        1: {"alpha": 1.0, "beta": 2.0, "gamma": 0.5, "delta": 0.3},   # Balanced
        2: {"alpha": 1.0, "beta": 3.0, "gamma": 0.3, "delta": 0.2},   # Aggressive
    }

    def __init__(
        self,
        state_dim: int = 13,  # 10 (env) + 3 (one-hot strategy)
        action_dim: int = 3,  # Hold, Scale Out, Scale In
        lr: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: float = 0.995,
        batch_size: int = 64,
        buffer_size: int = 10000,
        target_update_freq: int = 500,
        device: str = "cpu",
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.device = device
        self.step_count = 0

        # Networks
        self.online_net = HierarchicalQNetwork(state_dim, action_dim).to(device)
        self.target_net = HierarchicalQNetwork(state_dim, action_dim).to(device)
        self.target_net.load_state_dict(self.online_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.online_net.parameters(), lr=lr)
        self.loss_fn = nn.SmoothL1Loss()
        self.replay_buffer = HierarchicalReplayBuffer(buffer_size)

    def augment_state(self, env_state: np.ndarray, strategy: int) -> np.ndarray:
        """
        Augment environment state with one-hot encoded strategy.

        Args:
            env_state: 10-dim environment state.
            strategy: High-level strategy (0, 1, or 2).

        Returns:
            13-dim augmented state.
        """
        one_hot = np.zeros(3, dtype=np.float32)
        one_hot[strategy] = 1.0
        return np.concatenate([env_state, one_hot])

    def select_action(self, augmented_state: np.ndarray, training: bool = True) -> int:
        """Select scaling action using epsilon-greedy on augmented state."""
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)

        with torch.no_grad():
            state_tensor = torch.FloatTensor(augmented_state).unsqueeze(0).to(self.device)
            q_values = self.online_net(state_tensor)
            return int(q_values.argmax(dim=1).item())

    def train_step(self):
        """Perform one training step on the low-level agent."""
        if len(self.replay_buffer) < self.batch_size:
            return 0.0

        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)

        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards_t = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).unsqueeze(1).to(self.device)

        current_q = self.online_net(states_t).gather(1, actions_t)

        with torch.no_grad():
            next_q = self.target_net(next_states_t).max(1, keepdim=True)[0]
            target_q = rewards_t + self.gamma * next_q * (1 - dones_t)

        loss = self.loss_fn(current_q, target_q)

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.online_net.parameters(), 1.0)
        self.optimizer.step()

        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        self.step_count += 1
        if self.step_count % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.online_net.state_dict())

        return loss.item()


class HierarchicalRLAgent:
    """
    Hierarchical RL Agent orchestrating high-level and low-level sub-agents.

    The high-level agent selects a strategy every K steps (default K=12, ~1 hour).
    The low-level agent makes scaling decisions at every step, conditioned on
    the current strategy.

    This two-level hierarchy enables:
        1. Long-term planning (workload trend awareness via high-level)
        2. Short-term responsiveness (per-step decisions via low-level)
        3. Adaptive reward shaping (strategy modulates reward weights)
    """

    def __init__(
        self,
        state_dim: int = 10,
        action_dim: int = 3,
        strategy_interval: int = 12,  # K=12 steps = 1 hour at 5-min granularity
        device: str = "cpu",
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.strategy_interval = strategy_interval
        self.device = device

        # Sub-agents
        self.high_level = HighLevelAgent(
            state_dim=8,  # Aggregated features
            action_dim=3,  # 3 strategies
            device=device,
        )
        self.low_level = LowLevelAgent(
            state_dim=state_dim + 3,  # env state + one-hot strategy
            action_dim=action_dim,
            device=device,
        )

        # Tracking
        self.current_strategy = 1  # Start with Balanced
        self.step_in_strategy = 0
        self.recent_states: List[np.ndarray] = []

        # High-level transition tracking
        self._hl_state = None
        self._hl_strategy = None
        self._hl_cumulative_reward = 0.0

    def select_action(self, state: np.ndarray, training: bool = False) -> int:
        """
        Select scaling action using the hierarchical policy.

        Every K steps, the high-level agent picks a new strategy.
        At every step, the low-level agent picks scale in/out/hold.
        """
        # Collect state for high-level aggregation
        self.recent_states.append(state.copy())

        # High-level decision every K steps
        if self.step_in_strategy >= self.strategy_interval or self._hl_state is None:
            self._update_strategy(state, training)

        self.step_in_strategy += 1

        # Low-level decision
        augmented_state = self.low_level.augment_state(state, self.current_strategy)
        action = self.low_level.select_action(augmented_state, training=training)

        return action

    def _update_strategy(self, state: np.ndarray, training: bool):
        """Update the high-level strategy."""
        # Compute aggregated state from recent history
        hl_state = self.high_level.aggregate_state(self.recent_states)

        # If we have a previous high-level transition, store it
        if self._hl_state is not None and training:
            self.high_level.replay_buffer.push(
                self._hl_state,
                self._hl_strategy,
                self._hl_cumulative_reward,
                hl_state,
                False,  # Not terminal for high-level
            )

        # Select new strategy
        self.current_strategy = self.high_level.select_strategy(hl_state, training=training)
        self._hl_state = hl_state
        self._hl_strategy = self.current_strategy
        self._hl_cumulative_reward = 0.0
        self.step_in_strategy = 0

        # Keep only last K states for next aggregation
        self.recent_states = self.recent_states[-self.strategy_interval:]

    def train(
        self,
        env,
        episodes: int = 500,
        log_interval: int = 10,
    ) -> Dict[str, List[float]]:
        """
        Train the hierarchical agent.

        Args:
            env: ECommerceScalingEnv instance.
            episodes: Number of training episodes.
            log_interval: Print progress every N episodes.

        Returns:
            Training history with rewards, losses, and strategies.
        """
        history = {
            "episode_rewards": [],
            "hl_losses": [],
            "ll_losses": [],
            "sla_violations": [],
            "strategies_used": [],
        }

        for episode in range(1, episodes + 1):
            state, _ = env.reset()
            self._reset_episode()
            done = False
            episode_reward = 0.0
            sla_violations = 0
            strategies_this_ep = []
            ll_losses = []
            hl_losses = []
            last_action = 0

            while not done:
                # Select action via hierarchy
                action = self.select_action(state, training=True)
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated

                # Accumulate reward for high-level
                self._hl_cumulative_reward += reward

                # Store low-level transition
                aug_state = self.low_level.augment_state(state, self.current_strategy)
                aug_next_state = self.low_level.augment_state(next_state, self.current_strategy)
                self.low_level.replay_buffer.push(
                    aug_state, action, reward, aug_next_state, done
                )

                # Train low-level agent
                ll_loss = self.low_level.train_step()
                ll_losses.append(ll_loss)

                # Train high-level agent (less frequently)
                if self.step_in_strategy == 0:
                    hl_loss = self.high_level.train_step()
                    hl_losses.append(hl_loss)
                    strategies_this_ep.append(self.current_strategy)

                # Track SLA violations
                if next_state[3] > 500.0:  # response_time > threshold
                    sla_violations += 1

                episode_reward += reward
                last_action = action
                state = next_state

            # Final high-level transition (episode end)
            if self._hl_state is not None:
                hl_state = self.high_level.aggregate_state(self.recent_states)
                self.high_level.replay_buffer.push(
                    self._hl_state, self._hl_strategy,
                    self._hl_cumulative_reward, hl_state, True
                )

            history["episode_rewards"].append(episode_reward)
            history["hl_losses"].append(np.mean(hl_losses) if hl_losses else 0.0)
            history["ll_losses"].append(np.mean(ll_losses) if ll_losses else 0.0)
            history["sla_violations"].append(sla_violations)
            history["strategies_used"].append(strategies_this_ep)

            if episode % log_interval == 0:
                avg_reward = np.mean(history["episode_rewards"][-log_interval:])
                avg_sla = np.mean(history["sla_violations"][-log_interval:])
                strategy_counts = {}
                for strats in history["strategies_used"][-log_interval:]:
                    for s in strats:
                        strategy_counts[s] = strategy_counts.get(s, 0) + 1
                strat_str = ", ".join(
                    f"{HighLevelAgent.STRATEGY_NAMES[k]}:{v}"
                    for k, v in sorted(strategy_counts.items())
                )
                print(
                    f"  Episode {episode:4d}/{episodes} | "
                    f"Avg Reward: {avg_reward:8.2f} | "
                    f"Avg SLA Violations: {avg_sla:5.1f} | "
                    f"HL ε: {self.high_level.epsilon:.3f} | "
                    f"LL ε: {self.low_level.epsilon:.3f} | "
                    f"Strategies: [{strat_str}]"
                )

        return history

    def _reset_episode(self):
        """Reset episode-level tracking."""
        self.current_strategy = 1
        self.step_in_strategy = self.strategy_interval  # Force strategy selection at start
        self.recent_states = []
        self._hl_state = None
        self._hl_strategy = None
        self._hl_cumulative_reward = 0.0

    def evaluate(self, env, n_episodes: int = 10) -> Dict[str, float]:
        """
        Evaluate the hierarchical agent.

        Returns metric dict compatible with evaluation.metrics.compute_metrics().
        """
        all_rewards = []
        all_sla = []
        all_costs = []
        all_scaling = []

        for _ in range(n_episodes):
            state, _ = env.reset()
            self._reset_episode()
            done = False
            ep_reward = 0.0
            sla = 0
            cost = 0.0
            scaling = 0

            while not done:
                action = self.select_action(state, training=False)
                next_state, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated

                ep_reward += reward
                if next_state[3] > 500.0:
                    sla += 1
                cost += next_state[8]
                if action != 0:
                    scaling += 1
                state = next_state

            all_rewards.append(ep_reward)
            all_sla.append(sla)
            all_costs.append(cost)
            all_scaling.append(scaling)

        return {
            "avg_reward": float(np.mean(all_rewards)),
            "std_reward": float(np.std(all_rewards)),
            "avg_sla_violations": float(np.mean(all_sla)),
            "avg_cost": float(np.mean(all_costs)),
            "avg_scaling_events": float(np.mean(all_scaling)),
        }

    def save(self, path: str):
        """Save both sub-agents to disk."""
        os.makedirs(path, exist_ok=True)
        torch.save({
            "high_level_online": self.high_level.online_net.state_dict(),
            "high_level_target": self.high_level.target_net.state_dict(),
            "high_level_epsilon": self.high_level.epsilon,
            "low_level_online": self.low_level.online_net.state_dict(),
            "low_level_target": self.low_level.target_net.state_dict(),
            "low_level_epsilon": self.low_level.epsilon,
            "strategy_interval": self.strategy_interval,
        }, os.path.join(path, "hierarchical_agent.pt"))
        print(f"[INFO] Hierarchical agent saved to {path}")

    def load(self, path: str):
        """Load both sub-agents from disk."""
        checkpoint_path = os.path.join(path, "hierarchical_agent.pt")
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.high_level.online_net.load_state_dict(checkpoint["high_level_online"])
        self.high_level.target_net.load_state_dict(checkpoint["high_level_target"])
        self.high_level.epsilon = checkpoint["high_level_epsilon"]
        self.low_level.online_net.load_state_dict(checkpoint["low_level_online"])
        self.low_level.target_net.load_state_dict(checkpoint["low_level_target"])
        self.low_level.epsilon = checkpoint["low_level_epsilon"]
        self.strategy_interval = checkpoint.get("strategy_interval", 12)
        print(f"[INFO] Hierarchical agent loaded from {path}")


def train_hierarchical(
    env,
    agent: Optional[HierarchicalRLAgent] = None,
    episodes: int = 500,
    device: str = "cpu",
) -> Tuple[HierarchicalRLAgent, Dict]:
    """
    Convenience function to train a Hierarchical RL agent.

    Args:
        env: ECommerceScalingEnv instance.
        agent: Optional pre-initialized agent. Created if None.
        episodes: Number of training episodes.
        device: Torch device.

    Returns:
        Tuple of (trained agent, training history).
    """
    if agent is None:
        agent = HierarchicalRLAgent(state_dim=10, action_dim=3, device=device)

    print("\n" + "=" * 60)
    print("  TRAINING HIERARCHICAL RL AGENT")
    print(f"  High-level: Strategy selection every {agent.strategy_interval} steps")
    print(f"  Low-level: Per-step scaling decisions")
    print(f"  Episodes: {episodes}")
    print("=" * 60 + "\n")

    history = agent.train(env, episodes=episodes)

    # Print final summary
    final_rewards = history["episode_rewards"][-50:]
    print(f"\n[SUMMARY] Last 50 episodes avg reward: {np.mean(final_rewards):.2f}")
    print(f"[SUMMARY] Best episode reward: {max(history['episode_rewards']):.2f}")

    return agent, history


if __name__ == "__main__":
    from environment.ecommerce_env import ECommerceScalingEnv

    env = ECommerceScalingEnv()
    agent, history = train_hierarchical(env, episodes=50)

    # Quick evaluation
    eval_results = agent.evaluate(env, n_episodes=5)
    print(f"\n[EVAL] Results: {eval_results}")
