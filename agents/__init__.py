"""Reinforcement Learning agents package for autonomous cloud resource scaling.

This package provides base abstractions and concrete agent implementations:
    - `BaseAgent`: Abstract base class defining the agent interface and evaluation logic.
    - `DQNAgent`: Deep Q-Network agent implementation using PyTorch.
    - `QNetwork`: 3-layer MLP value network architecture.
    - `ReplayBuffer`: Fixed-size experience replay buffer for transition storage.
"""

from agents.base_agent import BaseAgent
from agents.dqn_agent import DQNAgent, QNetwork, ReplayBuffer
from agents.hierarchical_agent import HierarchicalAgent

try:
    from agents.ppo_agent import PPOAgent
except ImportError:
    PPOAgent = None  # type: ignore[assignment, misc]

__all__ = [
    "BaseAgent",
    "DQNAgent",
    "QNetwork",
    "ReplayBuffer",
    "PPOAgent",
    "HierarchicalAgent",
]
