"""
PPO Agent Wrapper using Stable-Baselines3 for RL Autoscaling.

This module provides a production-ready wrapper around Stable-Baselines3's
Proximal Policy Optimization (PPO) algorithm, tailored for dynamic resource
allocation and cloud autoscaling environments.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Union

import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import VecEnv

# Robust import for BaseAgent
try:
    from agents.base_agent import BaseAgent
except ImportError:
    try:
        from base_agent import BaseAgent
    except ImportError:
        from abc import ABC, abstractmethod

        class BaseAgent(ABC):  # type: ignore[no-redef]
            """Abstract fallback base class for reinforcement learning agents."""

            @abstractmethod
            def select_action(self, state: np.ndarray) -> Union[int, np.ndarray]:
                """Select an action given state observation."""
                pass

            @abstractmethod
            def train(self, *args: Any, **kwargs: Any) -> Any:
                """Train the agent."""
                pass

            @abstractmethod
            def save(self, path: Union[str, Path]) -> None:
                """Save model weights."""
                pass

            @abstractmethod
            def load(self, path: Union[str, Path]) -> "BaseAgent":
                """Load model weights."""
                pass


class PPOAgent(BaseAgent):
    """
    PPO Agent wrapper integrating Stable-Baselines3 PPO with the BaseAgent interface.

    Features:
    - Wraps SB3 PPO algorithm with standard RL interface methods.
    - Supports custom policies, entropy/value coefficients, and clipping ranges.
    - Integrates with TensorBoard for monitoring policy metrics.
    - Provides evaluation utilities tracking SLA violations and cost metrics.

    Attributes:
        env (Optional[Union[gym.Env, VecEnv]]): Training or evaluation environment.
        learning_rate (Union[float, Callable[[float], float]]): Learning rate schedule or float.
        n_steps (int): The number of steps to run for each environment per update.
        batch_size (int): Minibatch size for policy/value function optimization.
        n_epochs (int): Number of epochs when optimizing the surrogate loss.
        gamma (float): Discount factor.
        clip_range (Union[float, Callable[[float], float]]): Clipping range for PPO loss.
        ent_coef (float): Entropy coefficient for exploration.
        vf_coef (float): Value function loss coefficient.
        policy (str): Policy architecture class (default: 'MlpPolicy').
        tensorboard_log (Optional[str]): TensorBoard logging directory.
        verbose (int): Verbosity level (0: no output, 1: info, 2: debug).
        seed (Optional[int]): Random seed for reproducibility.
        device (str): Device to use for PyTorch operations ('auto', 'cpu', 'cuda').
        model (Optional[PPO]): Internal Stable-Baselines3 PPO model instance.
    """

    def __init__(
        self,
        env: Optional[Union[gym.Env, VecEnv]] = None,
        learning_rate: Union[float, Callable[[float], float]] = 3e-4,
        n_steps: int = 2048,
        batch_size: int = 64,
        n_epochs: int = 10,
        gamma: float = 0.99,
        clip_range: Union[float, Callable[[float], float]] = 0.2,
        ent_coef: float = 0.01,
        vf_coef: float = 0.5,
        policy: str = "MlpPolicy",
        tensorboard_log: Optional[str] = "./logs/ppo",
        verbose: int = 1,
        seed: Optional[int] = None,
        device: str = "auto",
        **kwargs: Any,
    ) -> None:
        """
        Initialize the PPOAgent wrapper.

        Args:
            env: Optional gymnasium environment or SB3 VecEnv.
            learning_rate: Learning rate for the optimizer.
            n_steps: Number of steps per environment rollout buffer.
            batch_size: Minibatch size for training updates.
            n_epochs: Number of optimization epochs per rollout buffer.
            gamma: Discount factor for rewards.
            clip_range: PPO clipping parameter epsilon.
            ent_coef: Entropy coefficient for exploration bonus.
            vf_coef: Value function loss coefficient.
            policy: Policy network architecture string (e.g., 'MlpPolicy').
            tensorboard_log: Path to the TensorBoard log directory.
            verbose: Verbosity level (0, 1, or 2).
            seed: Seed for random number generators.
            device: Computing device ('auto', 'cpu', 'cuda', 'mps').
            **kwargs: Additional parameters passed to stable_baselines3.PPO.
        """
        super().__init__()
        self.env = env
        self.learning_rate = learning_rate
        self.n_steps = n_steps
        self.batch_size = batch_size
        self.n_epochs = n_epochs
        self.gamma = gamma
        self.clip_range = clip_range
        self.ent_coef = ent_coef
        self.vf_coef = vf_coef
        self.policy = policy
        self.tensorboard_log = tensorboard_log
        self.verbose = verbose
        self.seed = seed
        self.device = device
        self.extra_kwargs = kwargs

        self.model: Optional[PPO] = None

        if self.env is not None:
            self._init_model()

    def _init_model(self) -> None:
        """Instantiate the internal SB3 PPO model."""
        if self.env is None:
            raise ValueError("Environment must be specified before initializing PPO model.")

        self.model = PPO(
            policy=self.policy,
            env=self.env,
            learning_rate=self.learning_rate,
            n_steps=self.n_steps,
            batch_size=self.batch_size,
            n_epochs=self.n_epochs,
            gamma=self.gamma,
            clip_range=self.clip_range,
            ent_coef=self.ent_coef,
            vf_coef=self.vf_coef,
            tensorboard_log=self.tensorboard_log,
            verbose=self.verbose,
            seed=self.seed,
            device=self.device,
            **self.extra_kwargs,
        )

    def select_action(
        self,
        state: Union[np.ndarray, list[float]],
        deterministic: bool = True,
        **kwargs,  # absorbs training=False passed by base evaluator
    ) -> Union[int, np.ndarray]:
        """
        Select an action for the given state using the trained policy network.

        Args:
            state: Current environment state observation.
            deterministic: Whether to select the deterministic mode action (greedy)
                or sample from the policy distribution.

        Returns:
            Selected action as an integer (for discrete spaces) or numpy array.
        """
        if self.model is None:
            raise RuntimeError(
                "PPO model is not initialized. Please train or load a model first."
            )

        if not isinstance(state, np.ndarray):
            state = np.array(state, dtype=np.float32)

        action, _states = self.model.predict(state, deterministic=deterministic)

        # For discrete action environments, extract scalar integer
        if isinstance(action, np.ndarray) and action.ndim == 0:
            return int(action.item())
        elif isinstance(action, np.ndarray) and action.size == 1:
            return int(action.item())

        return action

    def train(
        self,
        total_timesteps: int = 100000,
        callback: Optional[Union[BaseCallback, list[BaseCallback]]] = None,
        progress_bar: bool = False,
        **kwargs: Any,
    ) -> "PPOAgent":
        """
        Train the PPO agent on the specified environment.

        Args:
            total_timesteps: Total timesteps to train the policy on.
            callback: Stable-Baselines3 callback(s) for metric logging/checkpointing.
            progress_bar: Whether to display an interactive progress bar.
            **kwargs: Extra keyword arguments forwarded to model.learn().

        Returns:
            self: The trained PPOAgent instance.
        """
        if self.model is None:
            if self.env is not None:
                self._init_model()
            else:
                raise ValueError(
                    "PPO model is not initialized and no environment is provided. "
                    "Pass an environment upon initialization or set agent.env before calling train()."
                )

        assert self.model is not None
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            progress_bar=progress_bar,
            **kwargs,
        )
        return self

    def save(self, path: Union[str, Path]) -> None:
        """
        Save the underlying Stable-Baselines3 model to disk.

        Args:
            path: Destination file path (with or without .zip extension).
        """
        if self.model is None:
            raise RuntimeError("Cannot save an uninitialized PPO model.")

        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(str(path_obj))

    def load(
        self,
        path: Union[str, Path],
        env: Optional[Union[gym.Env, VecEnv]] = None,
        **kwargs: Any,
    ) -> "PPOAgent":
        """
        Load a saved Stable-Baselines3 model from disk.

        Args:
            path: Path to the saved model file.
            env: Optional environment to attach to the loaded model.
            **kwargs: Additional keyword arguments passed to PPO.load().

        Returns:
            self: The loaded PPOAgent instance.
        """
        target_env = env if env is not None else self.env
        self.model = PPO.load(str(path), env=target_env, **kwargs)
        if env is not None:
            self.env = env
        return self

    def evaluate(
        self,
        env: Optional[gym.Env] = None,
        n_episodes: int = 10,
        deterministic: bool = True,
    ) -> Dict[str, float]:
        """
        Run evaluation episodes and compute summary performance metrics.

        Args:
            env: Evaluation environment. Defaults to self.env if None.
            n_episodes: Number of evaluation episodes to run.
            deterministic: Whether to use deterministic action selection.

        Returns:
            Dictionary containing evaluation summary metrics:
                - mean_reward: Average cumulative reward per episode
                - std_reward: Standard deviation of cumulative episode rewards
                - min_reward: Minimum episode reward observed
                - max_reward: Maximum episode reward observed
                - mean_length: Average episode length in steps
                - mean_sla_violations: Average SLA violations per episode
                - mean_cost: Average infrastructure cost per episode
        """
        eval_env = env if env is not None else self.env
        if eval_env is None:
            raise ValueError("An evaluation environment must be provided.")

        episode_rewards: list[float] = []
        episode_lengths: list[int] = []
        sla_violations_list: list[float] = []
        costs_list: list[float] = []

        for _ in range(n_episodes):
            state, _ = eval_env.reset()
            ep_reward = 0.0
            ep_len = 0
            ep_sla = 0.0
            ep_cost = 0.0
            done = False

            while not done:
                action = self.select_action(state, deterministic=deterministic)
                next_state, reward, terminated, truncated, info = eval_env.step(action)
                done = terminated or truncated

                ep_reward += float(reward)
                ep_len += 1

                # Extract domain-specific metrics if present in info dict
                if "sla_violation" in info:
                    ep_sla += float(info["sla_violation"])
                elif "sla_violations" in info:
                    ep_sla = float(info["sla_violations"])

                if "cost" in info:
                    ep_cost += float(info["cost"])
                elif "total_cost" in info:
                    ep_cost = float(info["total_cost"])

                state = next_state

            episode_rewards.append(ep_reward)
            episode_lengths.append(ep_len)
            sla_violations_list.append(ep_sla)
            costs_list.append(ep_cost)

        metrics = {
            "mean_reward": float(np.mean(episode_rewards)),
            "std_reward": float(np.std(episode_rewards)),
            "min_reward": float(np.min(episode_rewards)),
            "max_reward": float(np.max(episode_rewards)),
            "mean_length": float(np.mean(episode_lengths)),
            "mean_sla_violations": float(np.mean(sla_violations_list)),
            "mean_cost": float(np.mean(costs_list)),
        }
        return metrics
