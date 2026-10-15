"""Deep Q-Network (DQN) implementation for reinforcement learning autoscaling.

This module provides a production-grade DQN agent tailored for discrete autoscaling
decision-making (e.g., Scale-Down, Maintain/No-op, Scale-Up). It includes:
    - `QNetwork`: 3-layer MLP with ReLU activations and Xavier initialization.
    - `ReplayBuffer`: Experience replay memory for off-policy transition storage.
    - `DQNAgent`: Deep Q-learning agent implementing epsilon-greedy exploration with
      decay, target network synchronization, Huber loss minimization, and checkpointing.
"""

from __future__ import annotations

import logging
import random
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, NamedTuple, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Transition(NamedTuple):
    """Named tuple representing a single Markov Decision Process (MDP) transition."""

    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class QNetwork(nn.Module):
    """3-layer Multi-Layer Perceptron (MLP) for Q-value estimation.

    Architecture:
        - Input layer: state_dim -> 128 (Linear + ReLU)
        - Hidden layer: 128 -> 64 (Linear + ReLU)
        - Output layer: 64 -> action_dim (Linear)

    All linear layer weights are initialized using Xavier uniform initialization,
    and biases are initialized to zero.
    """

    def __init__(self, state_dim: int = 10, action_dim: int = 3) -> None:
        """Initialize the Q-network architecture.

        Args:
            state_dim: Dimensionality of the observation space. Defaults to 10.
            action_dim: Number of discrete autoscaling actions. Defaults to 3.
        """
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim

        self.fc1 = nn.Linear(state_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, action_dim)

        self._init_weights()

    def _init_weights(self) -> None:
        """Apply Xavier uniform initialization to weights and zero initialization to biases."""
        for layer in (self.fc1, self.fc2, self.fc3):
            nn.init.xavier_uniform_(layer.weight)
            if layer.bias is not None:
                nn.init.zeros_(layer.bias)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass estimating action-values Q(s, a).

        Args:
            state: State tensor of shape (batch_size, state_dim) or (state_dim,).

        Returns:
            torch.Tensor: Estimated Q-values for each discrete action,
                shape (batch_size, action_dim).
        """
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


class ReplayBuffer:
    """Fixed-capacity experience replay buffer for off-policy reinforcement learning.

    Stores environment transitions (state, action, reward, next_state, done) and
    provides random uniform batch sampling to break correlation between consecutive
    experience steps.
    """

    def __init__(self, capacity: int = 10000) -> None:
        """Initialize the replay buffer.

        Args:
            capacity: Maximum number of transitions to store. Defaults to 10000.
        """
        if capacity <= 0:
            raise ValueError(f"ReplayBuffer capacity must be positive, got {capacity}")
        self.capacity: int = capacity
        self.buffer: Deque[Transition] = deque(maxlen=capacity)

    def push(
        self,
        state: Union[np.ndarray, List[float]],
        action: int,
        reward: float,
        next_state: Union[np.ndarray, List[float]],
        done: bool,
    ) -> None:
        """Add a transition to the replay buffer.

        Args:
            state: Current state observation.
            action: Discrete action executed.
            reward: Scalar reward received.
            next_state: Next state observation.
            done: Flag indicating whether the episode terminated/truncated.
        """
        s_arr = np.asarray(state, dtype=np.float32)
        ns_arr = np.asarray(next_state, dtype=np.float32)
        transition = Transition(
            state=s_arr,
            action=int(action),
            reward=float(reward),
            next_state=ns_arr,
            done=bool(done),
        )
        self.buffer.append(transition)

    def add(
        self,
        state: Union[np.ndarray, List[float]],
        action: int,
        reward: float,
        next_state: Union[np.ndarray, List[float]],
        done: bool,
    ) -> None:
        """Alias for `push`."""
        self.push(state, action, reward, next_state, done)

    def sample(
        self, batch_size: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Sample a random batch of transitions as numpy arrays.

        Args:
            batch_size: Number of transitions to sample.

        Returns:
            Tuple of numpy arrays:
                - states: shape (batch_size, state_dim)
                - actions: shape (batch_size, 1)
                - rewards: shape (batch_size, 1)
                - next_states: shape (batch_size, state_dim)
                - dones: shape (batch_size, 1)

        Raises:
            ValueError: If `batch_size` exceeds the current buffer size.
        """
        if len(self.buffer) < batch_size:
            raise ValueError(
                f"Cannot sample {batch_size} items from buffer of size {len(self.buffer)}"
            )

        batch = random.sample(self.buffer, batch_size)

        states = np.array([t.state for t in batch], dtype=np.float32)
        actions = np.array([[t.action] for t in batch], dtype=np.int64)
        rewards = np.array([[t.reward] for t in batch], dtype=np.float32)
        next_states = np.array([t.next_state for t in batch], dtype=np.float32)
        dones = np.array([[float(t.done)] for t in batch], dtype=np.float32)

        return states, actions, rewards, next_states, dones

    def sample_tensors(
        self, batch_size: int, device: torch.device
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Sample a random batch of transitions converted directly to PyTorch tensors.

        Args:
            batch_size: Number of transitions to sample.
            device: PyTorch device on which to allocate tensors.

        Returns:
            Tuple of torch.Tensor on `device`:
                - states: (batch_size, state_dim) torch.float32
                - actions: (batch_size, 1) torch.int64
                - rewards: (batch_size, 1) torch.float32
                - next_states: (batch_size, state_dim) torch.float32
                - dones: (batch_size, 1) torch.float32
        """
        states_np, actions_np, rewards_np, next_states_np, dones_np = self.sample(batch_size)

        states = torch.from_numpy(states_np).to(device)
        actions = torch.from_numpy(actions_np).to(device)
        rewards = torch.from_numpy(rewards_np).to(device)
        next_states = torch.from_numpy(next_states_np).to(device)
        dones = torch.from_numpy(dones_np).to(device)

        return states, actions, rewards, next_states, dones

    def __len__(self) -> int:
        """Return the current number of transitions in the buffer."""
        return len(self.buffer)

    def clear(self) -> None:
        """Clear all transitions from the buffer."""
        self.buffer.clear()


class DQNAgent(BaseAgent):
    """Deep Q-Network (DQN) Agent for autonomous cloud scaling.

    Features:
        - Online Network & Target Network (Double network architecture)
        - Epsilon-greedy exploration with configurable decay schedule
        - Smooth L1 (Huber) loss minimization for robust gradient updates
        - Periodic hard target network updates
        - Experience Replay Buffer integration
        - Checkpoint saving and loading
        - Comprehensive training statistics logging (losses, rewards, epsilons)
    """

    def __init__(
        self,
        state_dim: int = 10,
        action_dim: int = 3,
        lr: float = 1e-3,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.05,
        epsilon_decay: float = 0.995,
        batch_size: int = 64,
        target_update_freq: int = 500,
        buffer_size: int = 10000,
        device: str = "auto",
    ) -> None:
        """Initialize the DQN Agent.

        Args:
            state_dim: Dimension of environment state vector. Defaults to 10.
            action_dim: Number of discrete actions. Defaults to 3 (Down, No-op, Up).
            lr: Learning rate for Adam optimizer. Defaults to 1e-3.
            gamma: Discount factor for future rewards. Defaults to 0.99.
            epsilon_start: Initial exploration rate. Defaults to 1.0.
            epsilon_end: Minimum exploration rate. Defaults to 0.05.
            epsilon_decay: Multiplicative decay factor per training step. Defaults to 0.995.
            batch_size: Minibatch size sampled for training. Defaults to 64.
            target_update_freq: Frequency (in train steps) to sync target network. Defaults to 500.
            buffer_size: Maximum capacity of the replay buffer. Defaults to 10000.
            device: Computing device ('auto', 'cpu', 'cuda', 'mps'). Defaults to 'auto'.
        """
        super().__init__()

        self.state_dim: int = state_dim
        self.action_dim: int = action_dim
        self.lr: float = lr
        self.gamma: float = gamma
        self.epsilon: float = float(epsilon_start)
        self.epsilon_start: float = float(epsilon_start)
        self.epsilon_end: float = float(epsilon_end)
        self.epsilon_decay: float = float(epsilon_decay)
        self.batch_size: int = batch_size
        self.target_update_freq: int = target_update_freq
        self.buffer_size: int = buffer_size

        # Device configuration
        self.device: torch.device = self._resolve_device(device)

        # Networks
        self.online_net: QNetwork = QNetwork(self.state_dim, self.action_dim).to(self.device)
        self.target_net: QNetwork = QNetwork(self.state_dim, self.action_dim).to(self.device)
        self.update_target_network()
        self.target_net.eval()  # Target network is purely for inference

        # Optimizer and Huber Loss (Smooth L1)
        self.optimizer: torch.optim.Optimizer = torch.optim.Adam(
            self.online_net.parameters(), lr=self.lr
        )
        self.criterion: nn.SmoothL1Loss = nn.SmoothL1Loss()

        # Experience Replay
        self.replay_buffer: ReplayBuffer = ReplayBuffer(capacity=self.buffer_size)

        # Training Diagnostics
        self.step_count: int = 0
        self.losses: List[float] = []
        self.rewards: List[float] = []
        self.epsilons: List[float] = []

        logger.info(
            "DQNAgent initialized on %s (state_dim=%d, action_dim=%d, lr=%.4f, gamma=%.2f)",
            self.device,
            self.state_dim,
            self.action_dim,
            self.lr,
            self.gamma,
        )

    @staticmethod
    def _resolve_device(device_arg: str) -> torch.device:
        """Resolve PyTorch device from 'auto' or specified identifier."""
        if device_arg.lower() == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return torch.device("mps")
            return torch.device("cpu")
        return torch.device(device_arg)

    def select_action(
        self,
        state: Union[np.ndarray, List[float], torch.Tensor],
        training: bool = True,
    ) -> int:
        """Select an action using epsilon-greedy exploration if training, or greedy otherwise.

        Args:
            state: Current state observation vector.
            training: If True, uses epsilon-greedy exploration.
                If False, strictly chooses the argmax greedy action.

        Returns:
            int: Discrete action index in [0, action_dim - 1].
        """
        # Epsilon-greedy exploration check
        if training and random.random() < self.epsilon:
            return random.randrange(self.action_dim)

        # Greedy action selection from online network
        self.online_net.eval()
        with torch.no_grad():
            if isinstance(state, torch.Tensor):
                state_tensor = state.to(self.device, dtype=torch.float32)
            else:
                state_tensor = torch.as_tensor(state, dtype=torch.float32, device=self.device)

            if state_tensor.ndim == 1:
                state_tensor = state_tensor.unsqueeze(0)

            q_values = self.online_net(state_tensor)
            action = int(torch.argmax(q_values, dim=-1).item())

        return action

    def train_step(self) -> Optional[float]:
        """Perform one step of gradient descent using a batch from the replay buffer.

        Computes Huber (Smooth L1) loss between online Q-values and Bellman target
        Q-values, updates online network parameters, periodically synchronizes the
        target network, decays epsilon, and tracks statistics.

        Returns:
            Optional[float]: Scalar loss value, or None if buffer size < batch_size.
        """
        if len(self.replay_buffer) < self.batch_size:
            return None

        self.online_net.train()

        states, actions, rewards, next_states, dones = self.replay_buffer.sample_tensors(
            self.batch_size, self.device
        )

        # Current Q-values: Q_online(s, a)
        q_values = self.online_net(states)
        state_action_values = q_values.gather(1, actions)

        # Target Q-values: r + gamma * max_a' Q_target(s', a') * (1 - done)
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(dim=1, keepdim=True)[0]
            target_action_values = rewards + (1.0 - dones) * self.gamma * next_q_values

        # Huber loss
        loss = self.criterion(state_action_values, target_action_values)

        # Backpropagation and gradient clipping
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.online_net.parameters(), max_norm=10.0)
        self.optimizer.step()

        # Update counters and diagnostic metrics
        loss_val = float(loss.item())
        self.losses.append(loss_val)
        self.epsilons.append(self.epsilon)
        self.step_count += 1

        # Periodic hard target network update
        if self.step_count % self.target_update_freq == 0:
            self.update_target_network()
            logger.debug(
                "Target network synchronized with online network at step %d",
                self.step_count,
            )

        # Epsilon decay
        self.decay_epsilon()

        return loss_val

    def train(self, experiences: Any = None) -> Optional[float]:
        """Train agent using experiences or replay buffer.

        Fulfills BaseAgent abstract interface. Experiences can be:
            - A single transition tuple: (state, action, reward, next_state, done)
            - An iterable of transition tuples
            - None (samples directly from internal replay buffer)

        Args:
            experiences: Single transition, list of transitions, or None.

        Returns:
            Optional[float]: Loss from the optimization step, or None if buffer not ready.
        """
        if experiences is not None:
            if isinstance(experiences, tuple) and len(experiences) == 5:
                self.store_transition(*experiences)
            elif isinstance(experiences, (list, tuple)):
                for exp in experiences:
                    if isinstance(exp, tuple) and len(exp) == 5:
                        self.store_transition(*exp)

        return self.train_step()

    def store_transition(
        self,
        state: Union[np.ndarray, List[float]],
        action: int,
        reward: float,
        next_state: Union[np.ndarray, List[float]],
        done: bool,
    ) -> None:
        """Store an environment transition into the replay buffer.

        Args:
            state: Current state observation.
            action: Selected action.
            reward: Scalar reward received.
            next_state: Next state observation.
            done: Episode termination flag.
        """
        self.replay_buffer.push(state, action, reward, next_state, done)

    def update_target_network(self) -> None:
        """Copy weights from online network to target network."""
        self.target_net.load_state_dict(self.online_net.state_dict())

    def decay_epsilon(self) -> float:
        """Decay exploration rate epsilon by `epsilon_decay` down to `epsilon_end`.

        Returns:
            float: Updated epsilon value.
        """
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        return self.epsilon

    def record_reward(self, reward: float) -> None:
        """Track an episode or step reward.

        Args:
            reward: Scalar reward to append to tracking history.
        """
        self.rewards.append(float(reward))

    def save(self, path: Union[str, Path]) -> None:
        """Save complete agent checkpoint to disk.

        Saves online and target network parameters, optimizer state, current epsilon,
        step count, and training metric trajectories.

        Args:
            path: Destination file path for checkpoint (e.g., 'dqn_checkpoint.pt').
        """
        dest_path = Path(path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint: Dict[str, Any] = {
            "online_net_state_dict": self.online_net.state_dict(),
            "target_net_state_dict": self.target_net.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "step_count": self.step_count,
            "losses": self.losses,
            "rewards": self.rewards,
            "epsilons": self.epsilons,
            "hyperparameters": {
                "state_dim": self.state_dim,
                "action_dim": self.action_dim,
                "lr": self.lr,
                "gamma": self.gamma,
                "epsilon_start": self.epsilon_start,
                "epsilon_end": self.epsilon_end,
                "epsilon_decay": self.epsilon_decay,
                "batch_size": self.batch_size,
                "target_update_freq": self.target_update_freq,
                "buffer_size": self.buffer_size,
            },
        }

        torch.save(checkpoint, dest_path)
        logger.info("Successfully saved DQN checkpoint to %s", dest_path)

    def load(self, path: Union[str, Path]) -> None:
        """Load agent checkpoint from disk.

        Restores online and target network weights, optimizer state, epsilon,
        step count, and historical metrics.

        Args:
            path: Source checkpoint file path to restore.

        Raises:
            FileNotFoundError: If path does not exist.
        """
        source_path = Path(path)
        if not source_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {source_path}")

        checkpoint = torch.load(source_path, map_location=self.device)

        self.online_net.load_state_dict(checkpoint["online_net_state_dict"])
        self.target_net.load_state_dict(checkpoint["target_net_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epsilon = float(checkpoint.get("epsilon", self.epsilon_end))
        self.step_count = int(checkpoint.get("step_count", 0))
        self.losses = list(checkpoint.get("losses", []))
        self.rewards = list(checkpoint.get("rewards", []))
        self.epsilons = list(checkpoint.get("epsilons", []))

        self.target_net.eval()
        logger.info(
            "Successfully loaded DQN checkpoint from %s (step_count=%d, epsilon=%.4f)",
            source_path,
            self.step_count,
            self.epsilon,
        )

    def get_training_stats(self) -> Dict[str, Any]:
        """Retrieve a summary of training statistics.

        Returns:
            Dict[str, Any]: Aggregated stats including recent loss, rewards, epsilon,
                and buffer utilization.
        """
        recent_loss = float(np.mean(self.losses[-100:])) if self.losses else 0.0
        recent_reward = float(np.mean(self.rewards[-100:])) if self.rewards else 0.0

        return {
            "step_count": self.step_count,
            "current_epsilon": self.epsilon,
            "buffer_length": len(self.replay_buffer),
            "total_updates": len(self.losses),
            "recent_avg_loss": recent_loss,
            "recent_avg_reward": recent_reward,
            "total_recorded_rewards": len(self.rewards),
        }
