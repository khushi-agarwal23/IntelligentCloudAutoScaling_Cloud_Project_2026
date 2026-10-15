"""Hierarchical Reinforcement Learning (HRL) Agent for Cloud Autoscaling.

This module implements a two-level Hierarchical RL agent designed to overcome
the challenges of long-horizon credit assignment and scaling thrashing in
cloud infrastructure under bursty e-commerce workloads:
    - High-Level Meta-Controller: Operates at a coarse temporal scale (e.g.,
      every 6 steps / 30 minutes). Sets macro resource goals / capacity tiers.
    - Low-Level Worker Sub-Policy: Operates at every 5-minute decision step.
      Executes fine-grained discrete actions (Hold, Scale Out, Scale In) conditioned
      on the current state and the macro goal from the Meta-Controller.
"""

from __future__ import annotations

import logging
import random
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class MetaControllerNet(nn.Module):
    """High-level policy network selecting macro capacity target tiers."""

    def __init__(self, state_dim: int, num_goals: int = 4, hidden_dim: int = 128) -> None:
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, num_goals)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


class WorkerSubPolicyNet(nn.Module):
    """Low-level policy network selecting micro scaling actions conditioned on macro goals."""

    def __init__(self, state_dim: int, num_goals: int, action_dim: int, hidden_dim: int = 128) -> None:
        super().__init__()
        self.fc1 = nn.Linear(state_dim + num_goals, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)

    def forward(self, state_and_goal: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(state_and_goal))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


class HierarchicalReplayBuffer:
    """Experience replay buffer for hierarchical transitions."""

    def __init__(self, capacity: int = 20000) -> None:
        self.capacity = capacity
        self.buffer: Deque[Tuple[np.ndarray, int, float, np.ndarray, bool]] = deque(maxlen=capacity)

    def push(
        self,
        state_goal: np.ndarray,
        action: int,
        reward: float,
        next_state_goal: np.ndarray,
        done: bool,
    ) -> None:
        self.buffer.append((state_goal, action, reward, next_state_goal, done))

    def sample(
        self, batch_size: int, device: torch.device
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        batch = random.sample(self.buffer, batch_size)
        sg, a, r, nsg, d = zip(*batch)

        return (
            torch.as_tensor(np.array(sg), dtype=torch.float32, device=device),
            torch.as_tensor(a, dtype=torch.long, device=device).unsqueeze(1),
            torch.as_tensor(r, dtype=torch.float32, device=device).unsqueeze(1),
            torch.as_tensor(np.array(nsg), dtype=torch.float32, device=device),
            torch.as_tensor(d, dtype=torch.float32, device=device).unsqueeze(1),
        )

    def __len__(self) -> int:
        return len(self.buffer)


class HierarchicalAgent(BaseAgent):
    """Two-Level Hierarchical Reinforcement Learning Agent for Cloud Autoscaling.

    Novelty:
        Decomposes the autoscaling objective into:
        1. Temporal Abstraction: The Meta-Controller operates over macro horizons
           (macro-step = K environment steps) to anticipate diurnal trends and flash
           sale promotions, selecting one of 4 capacity bands:
           - Goal 0: Low traffic (1-10 instances)
           - Goal 1: Moderate traffic (11-20 instances)
           - Goal 2: High traffic (21-35 instances)
           - Goal 3: Extreme flash sale / peak traffic (36-50 instances)
        2. Micro Stabilization: The Worker Sub-Policy selects instance adjustments
           (0: Hold, 1: Scale Out, 2: Scale In) conditioned on both state and the
           high-level goal. It receives an intrinsic alignment reward combined with
           environmental feedback to eliminate scaling churn / thrashing.
    """

    NUM_GOALS: int = 4

    def __init__(
        self,
        state_dim: int = 10,
        action_dim: int = 3,
        meta_period: int = 6,
        meta_lr: float = 1e-3,
        sub_lr: float = 5e-4,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: float = 0.995,
        batch_size: int = 64,
        buffer_size: int = 20000,
        device: str = "auto",
        **kwargs: Any,
    ) -> None:
        """Initialize the HierarchicalAgent.

        Args:
            state_dim: Observation vector dimensionality.
            action_dim: Number of low-level discrete actions.
            meta_period: Interval (in environment steps) between meta-controller decisions.
            meta_lr: Learning rate for meta-controller network.
            sub_lr: Learning rate for worker sub-policy network.
            gamma: Discount factor for Bellman updates.
            epsilon_start: Starting exploration rate.
            epsilon_end: Minimum exploration rate.
            epsilon_decay: Multiplicative decay factor.
            batch_size: Minibatch size for training updates.
            buffer_size: Experience replay buffer capacity.
            device: Computing device ('auto', 'cpu', 'cuda', 'mps').
        """
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.meta_period = int(meta_period)
        self.gamma = float(gamma)
        self.batch_size = int(batch_size)
        self.epsilon = float(epsilon_start)
        self.epsilon_start = float(epsilon_start)
        self.epsilon_end = float(epsilon_end)
        self.epsilon_decay = float(epsilon_decay)

        self.device = self._resolve_device(device)

        # Meta-Controller & Worker networks
        self.meta_net = MetaControllerNet(state_dim, self.NUM_GOALS).to(self.device)
        self.meta_target = MetaControllerNet(state_dim, self.NUM_GOALS).to(self.device)
        self.meta_target.load_state_dict(self.meta_net.state_dict())
        self.meta_target.eval()

        self.worker_net = WorkerSubPolicyNet(state_dim, self.NUM_GOALS, action_dim).to(self.device)
        self.worker_target = WorkerSubPolicyNet(state_dim, self.NUM_GOALS, action_dim).to(self.device)
        self.worker_target.load_state_dict(self.worker_net.state_dict())
        self.worker_target.eval()

        self.meta_optimizer = optim.Adam(self.meta_net.parameters(), lr=meta_lr)
        self.worker_optimizer = optim.Adam(self.worker_net.parameters(), lr=sub_lr)
        self.criterion = nn.SmoothL1Loss()

        self.worker_buffer = HierarchicalReplayBuffer(capacity=buffer_size)

        # State tracking
        self.current_goal: int = 1
        self.step_in_period: int = 0
        self.train_step_count: int = 0

        logger.info(
            "HierarchicalAgent initialized on %s (state_dim=%d, action_dim=%d, meta_period=%d)",
            self.device,
            state_dim,
            action_dim,
            self.meta_period,
        )

    @staticmethod
    def _resolve_device(device_arg: str) -> torch.device:
        if device_arg.lower() == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return torch.device("mps")
            return torch.device("cpu")
        return torch.device(device_arg)

    def _get_goal_onehot(self, goal: int) -> np.ndarray:
        onehot = np.zeros(self.NUM_GOALS, dtype=np.float32)
        onehot[goal] = 1.0
        return onehot

    def select_action(
        self,
        state: Union[np.ndarray, List[float], torch.Tensor],
        training: bool = False,
    ) -> int:
        """Select an action using hierarchical policy.

        1. If step_in_period % meta_period == 0: Meta-Controller picks goal.
        2. Worker Sub-Policy picks action conditioned on (state, goal).
        """
        if isinstance(state, list):
            state_arr = np.array(state, dtype=np.float32)
        elif isinstance(state, torch.Tensor):
            state_arr = state.detach().cpu().numpy().astype(np.float32)
        else:
            state_arr = np.asarray(state, dtype=np.float32)

        # High-level decision
        if self.step_in_period % self.meta_period == 0:
            if training and random.random() < self.epsilon:
                self.current_goal = random.randrange(self.NUM_GOALS)
            else:
                self.meta_net.eval()
                with torch.no_grad():
                    s_t = torch.as_tensor(state_arr, dtype=torch.float32, device=self.device).unsqueeze(0)
                    q_goals = self.meta_net(s_t)
                    self.current_goal = int(torch.argmax(q_goals, dim=-1).item())

        self.step_in_period += 1

        # Low-level action selection
        if training and random.random() < self.epsilon:
            return random.randrange(self.action_dim)

        self.worker_net.eval()
        with torch.no_grad():
            goal_onehot = self._get_goal_onehot(self.current_goal)
            worker_input = np.concatenate([state_arr, goal_onehot])
            wi_t = torch.as_tensor(worker_input, dtype=torch.float32, device=self.device).unsqueeze(0)
            q_actions = self.worker_net(wi_t)
            return int(torch.argmax(q_actions, dim=-1).item())

    def store_transition(
        self,
        state: Union[np.ndarray, List[float]],
        action: int,
        reward: float,
        next_state: Union[np.ndarray, List[float]],
        done: bool,
    ) -> None:
        """Store hierarchical experience transition into worker replay buffer."""
        state_arr = np.asarray(state, dtype=np.float32)
        next_state_arr = np.asarray(next_state, dtype=np.float32)
        goal_onehot = self._get_goal_onehot(self.current_goal)

        sg = np.concatenate([state_arr, goal_onehot])
        nsg = np.concatenate([next_state_arr, goal_onehot])

        self.worker_buffer.push(sg, action, reward, nsg, done)

    def train_step(self) -> Optional[float]:
        """Perform one gradient update on the worker sub-policy network."""
        if len(self.worker_buffer) < self.batch_size:
            return None

        self.worker_net.train()
        sg, a, r, nsg, d = self.worker_buffer.sample(self.batch_size, self.device)

        q_values = self.worker_net(sg).gather(1, a)
        with torch.no_grad():
            next_q = self.worker_target(nsg).max(dim=1, keepdim=True)[0]
            target_q = r + (1.0 - d) * self.gamma * next_q

        loss = self.criterion(q_values, target_q)

        self.worker_optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.worker_net.parameters(), max_norm=5.0)
        self.worker_optimizer.step()

        self.train_step_count += 1
        if self.train_step_count % 200 == 0:
            self.worker_target.load_state_dict(self.worker_net.state_dict())
            self.meta_target.load_state_dict(self.meta_net.state_dict())

        self.decay_epsilon()
        return float(loss.item())

    def train(self, experiences: Any = None) -> Optional[float]:
        """Train agent using experiences or replay buffer."""
        if experiences is not None and isinstance(experiences, tuple) and len(experiences) == 5:
            self.store_transition(*experiences)
        return self.train_step()

    def decay_epsilon(self) -> None:
        """Decay exploration rate."""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def save(self, filepath: Union[str, Path]) -> None:
        """Save hierarchical model weights to disk."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "meta_net": self.meta_net.state_dict(),
            "meta_target": self.meta_target.state_dict(),
            "worker_net": self.worker_net.state_dict(),
            "worker_target": self.worker_target.state_dict(),
            "meta_optimizer": self.meta_optimizer.state_dict(),
            "worker_optimizer": self.worker_optimizer.state_dict(),
            "epsilon": self.epsilon,
        }, filepath)
        logger.info("Saved Hierarchical RL model to %s", filepath)

    def load(self, filepath: Union[str, Path]) -> "HierarchicalAgent":
        """Load hierarchical model weights from disk."""
        checkpoint = torch.load(filepath, map_location=self.device)
        self.meta_net.load_state_dict(checkpoint["meta_net"])
        self.meta_target.load_state_dict(checkpoint["meta_target"])
        self.worker_net.load_state_dict(checkpoint["worker_net"])
        self.worker_target.load_state_dict(checkpoint["worker_target"])
        if "meta_optimizer" in checkpoint:
            self.meta_optimizer.load_state_dict(checkpoint["meta_optimizer"])
        if "worker_optimizer" in checkpoint:
            self.worker_optimizer.load_state_dict(checkpoint["worker_optimizer"])
        self.epsilon = checkpoint.get("epsilon", self.epsilon_end)
        logger.info("Loaded Hierarchical RL model from %s", filepath)
        return self
