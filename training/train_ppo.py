"""
PPO Training Script for Cloud Autoscaling Environments.

This script trains a Proximal Policy Optimization (PPO) agent on the
ECommerceScalingEnv using Stable-Baselines3 and the custom PPOAgent wrapper.
Episode metrics (reward, SLA violations, cost, length) are logged to TensorBoard
via a custom callback, and the best-performing model checkpoint is saved.
"""

from __future__ import annotations

import argparse
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import gymnasium as gym
import numpy as np
import yaml
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import environment and PPOAgent
try:
    from envs.ecommerce_env import ECommerceScalingEnv
except ImportError:
    try:
        from envs.ecommerce_scaling_env import ECommerceScalingEnv  # type: ignore[no-redef]
    except ImportError:
        try:
            from envs import ECommerceScalingEnv  # type: ignore[no-redef]
        except ImportError:
            ECommerceScalingEnv = None  # type: ignore[assignment, misc]

try:
    from agents.ppo_agent import PPOAgent
except ImportError:
    try:
        from ppo_agent import PPOAgent  # type: ignore[no-redef]
    except ImportError:
        PPOAgent = None  # type: ignore[assignment, misc]


class AutoscalingMetricsCallback(BaseCallback):
    """
    Custom Stable-Baselines3 Callback for Cloud Autoscaling Environments.

    Monitors environment interactions on each step to track:
    - Episode total reward
    - Cumulative SLA violations per episode
    - Total infrastructure cost per episode
    - Episode duration (steps)

    Logs metrics to TensorBoard via the SB3 logger and saves the best model checkpoint
    whenever an episode sets a new cumulative reward record.
    """

    def __init__(
        self,
        save_path: str = "./checkpoints/ppo",
        check_freq: int = 1,
        verbose: int = 1,
    ) -> None:
        """
        Initialize the callback.

        Args:
            save_path: Directory path where best model checkpoints will be stored.
            check_freq: Frequency (in steps) to check metrics.
            verbose: Verbosity level for console output.
        """
        super().__init__(verbose)
        self.save_path = Path(save_path)
        self.check_freq = check_freq
        self.best_reward = -float("inf")
        self.episode_count = 0
        self.episode_rewards: List[float] = []

        # Episode accumulators
        self.cur_reward = 0.0
        self.cur_length = 0
        self.cur_sla_violations = 0.0
        self.cur_cost = 0.0

        self.save_path.mkdir(parents=True, exist_ok=True)

    def _on_step(self) -> bool:
        """
        Callback step method invoked after every environment transition.

        Returns:
            bool: Always True to continue training.
        """
        # Read step outputs from local variables
        rewards = self.locals.get("rewards")
        dones = self.locals.get("dones")
        infos = self.locals.get("infos")

        if rewards is not None:
            self.cur_reward += float(rewards[0])
        self.cur_length += 1

        if infos and len(infos) > 0:
            first_info = infos[0]
            if "sla_violation" in first_info:
                self.cur_sla_violations += float(first_info["sla_violation"])
            elif "sla_violations" in first_info:
                self.cur_sla_violations = float(first_info["sla_violations"])

            if "cost" in first_info:
                self.cur_cost += float(first_info["cost"])
            elif "total_cost" in first_info:
                self.cur_cost = float(first_info["total_cost"])

        # Check if episode terminated or truncated
        if dones is not None and dones[0]:
            self.episode_count += 1
            ep_reward = self.cur_reward
            ep_length = self.cur_length
            ep_sla = self.cur_sla_violations
            ep_cost = self.cur_cost

            # Check if Monitor wrapper supplied canonical episode return
            if infos and len(infos) > 0 and "episode" in infos[0]:
                ep_reward = float(infos[0]["episode"]["r"])
                ep_length = int(infos[0]["episode"]["l"])

            self.episode_rewards.append(ep_reward)

            # Record domain metrics in TensorBoard
            self.logger.record("rollout/ep_reward", ep_reward)
            self.logger.record("rollout/ep_len", ep_length)
            self.logger.record("autoscaling/sla_violations", ep_sla)
            self.logger.record("autoscaling/cost", ep_cost)
            self.logger.record("autoscaling/episodes", self.episode_count)

            # Print progress every 10 episodes
            if self.episode_count % 10 == 0:
                recent_avg = float(np.mean(self.episode_rewards[-10:]))
                if self.verbose > 0:
                    print(
                        f"PPO Episode {self.episode_count:4d} | "
                        f"Step: {self.num_timesteps:7d} | "
                        f"Reward: {ep_reward:8.2f} (10-ep avg: {recent_avg:8.2f}) | "
                        f"SLA Violations: {ep_sla:4.0f} | "
                        f"Cost: {ep_cost:7.2f}"
                    )

            # Save best model checkpoint based on reward
            if ep_reward > self.best_reward:
                self.best_reward = ep_reward
                best_checkpoint = self.save_path / "best_ppo_model.zip"
                self.model.save(str(best_checkpoint))
                if self.verbose > 0:
                    print(
                        f"[*] Checkpoint saved: New best reward {self.best_reward:.2f} at step "
                        f"{self.num_timesteps} -> {best_checkpoint}"
                    )

            # Reset accumulators for next episode
            self.cur_reward = 0.0
            self.cur_length = 0
            self.cur_sla_violations = 0.0
            self.cur_cost = 0.0

        return True


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to hyperparams.yaml.

    Returns:
        Dictionary containing configuration sections.
    """
    config_file = Path(config_path)
    if not config_file.is_absolute():
        candidates = [
            config_file,
            PROJECT_ROOT / "training" / config_path,
            PROJECT_ROOT / config_path,
        ]
        for candidate in candidates:
            if candidate.exists():
                config_file = candidate
                break

    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    return {}


def create_environment(
    env_cfg: Dict[str, Any],
    reward_cfg: Dict[str, Any],
    seed: Optional[int] = None,
) -> gym.Env:
    """
    Instantiate ECommerceScalingEnv dynamically matching constructor parameters.

    Args:
        env_cfg: Environment settings.
        reward_cfg: Reward penalty and cost weights.
        seed: Random seed.

    Returns:
        Gymnasium environment wrapped with Monitor for episode metric tracking.
    """
    if ECommerceScalingEnv is None:
        raise ImportError(
            "ECommerceScalingEnv could not be found. Please ensure envs/ecommerce_env.py "
            "is created and defines ECommerceScalingEnv."
        )

    all_kwargs = {**env_cfg, **reward_cfg}
    sig = inspect.signature(ECommerceScalingEnv.__init__)
    valid_kwargs = {k: v for k, v in all_kwargs.items() if k in sig.parameters}

    if "seed" in sig.parameters and seed is not None:
        valid_kwargs["seed"] = seed

    env = ECommerceScalingEnv(**valid_kwargs)
    # Wrap with Monitor for standard episode return and length tracking
    return Monitor(env)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for PPO training."""
    parser = argparse.ArgumentParser(
        description="Train PPO agent on ECommerceScalingEnv with TensorBoard logging."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="hyperparams.yaml",
        help="Path to YAML hyperparameter config file (default: hyperparams.yaml).",
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=None,
        help="Total training timesteps (default: 100000 or from config).",
    )
    parser.add_argument("--lr", type=float, default=None, help="Learning rate for PPO optimizer.")
    parser.add_argument("--n-steps", type=int, default=None, help="Steps per rollout buffer.")
    parser.add_argument("--batch-size", type=int, default=None, help="PPO minibatch size.")
    parser.add_argument("--n-epochs", type=int, default=None, help="Number of surrogate epochs.")
    parser.add_argument("--gamma", type=float, default=None, help="Discount factor gamma.")
    parser.add_argument("--clip-range", type=float, default=None, help="PPO clipping range.")
    parser.add_argument("--ent-coef", type=float, default=None, help="Entropy bonus coefficient.")
    parser.add_argument("--vf-coef", type=float, default=None, help="Value function coefficient.")
    parser.add_argument(
        "--policy",
        type=str,
        default="MlpPolicy",
        help="Policy architecture ('MlpPolicy').",
    )
    parser.add_argument(
        "--save-dir",
        type=str,
        default="./checkpoints/ppo",
        help="Directory to save checkpoints (default: ./checkpoints/ppo).",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="./logs/ppo",
        help="TensorBoard log directory (default: ./logs/ppo).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Device to use ('auto', 'cpu', 'cuda', 'mps').",
    )
    parser.add_argument(
        "--verbose",
        type=int,
        default=1,
        help="Verbosity level (0: silent, 1: info, 2: debug).",
    )

    # Environment overrides
    parser.add_argument("--episode-length", type=int, default=None, help="Horizon steps per episode.")
    parser.add_argument("--sla-threshold", type=float, default=None, help="SLA response time threshold.")
    parser.add_argument("--max-instances", type=int, default=None, help="Maximum instances limit.")
    parser.add_argument("--min-instances", type=int, default=None, help="Minimum instances limit.")
    parser.add_argument(
        "--per-instance-capacity",
        type=float,
        default=None,
        help="Throughput capacity per instance.",
    )

    return parser.parse_args()


def train_ppo() -> None:
    """Execute the PPO training pipeline."""
    args = parse_args()

    # Load configuration from YAML
    yaml_config = load_config(args.config)
    ppo_cfg: Dict[str, Any] = yaml_config.get("ppo", {})
    env_cfg: Dict[str, Any] = yaml_config.get("environment", {})
    reward_cfg: Dict[str, Any] = yaml_config.get("reward", {})

    # Apply command-line overrides
    total_timesteps = (
        args.timesteps
        if args.timesteps is not None
        else ppo_cfg.get("total_timesteps", 100000)
    )

    if args.lr is not None:
        ppo_cfg["lr"] = args.lr
    if args.n_steps is not None:
        ppo_cfg["n_steps"] = args.n_steps
    if args.batch_size is not None:
        ppo_cfg["batch_size"] = args.batch_size
    if args.n_epochs is not None:
        ppo_cfg["n_epochs"] = args.n_epochs
    if args.gamma is not None:
        ppo_cfg["gamma"] = args.gamma
    if args.clip_range is not None:
        ppo_cfg["clip_range"] = args.clip_range
    if args.ent_coef is not None:
        ppo_cfg["ent_coef"] = args.ent_coef
    if args.vf_coef is not None:
        ppo_cfg["vf_coef"] = args.vf_coef

    if args.episode_length is not None:
        env_cfg["episode_length"] = args.episode_length
    if args.sla_threshold is not None:
        env_cfg["sla_threshold"] = args.sla_threshold
    if args.max_instances is not None:
        env_cfg["max_instances"] = args.max_instances
    if args.min_instances is not None:
        env_cfg["min_instances"] = args.min_instances
    if args.per_instance_capacity is not None:
        env_cfg["per_instance_capacity"] = args.per_instance_capacity

    # Prepare directories
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    if PPOAgent is None:
        raise ImportError(
            "PPOAgent could not be found. Please ensure agents/ppo_agent.py "
            "is created and defines PPOAgent."
        )

    # Initialize environment
    env = create_environment(env_cfg, reward_cfg, seed=args.seed)

    print("=================================================================")
    print("                PPO Autoscaling Agent Training                   ")
    print("=================================================================")
    print(f"Total Timesteps       : {total_timesteps}")
    print(f"Learning Rate         : {ppo_cfg.get('lr', 3e-4)}")
    print(f"Steps per Rollout     : {ppo_cfg.get('n_steps', 2048)}")
    print(f"Batch Size            : {ppo_cfg.get('batch_size', 64)}")
    print(f"Epochs per Update     : {ppo_cfg.get('n_epochs', 10)}")
    print(f"Clip Range            : {ppo_cfg.get('clip_range', 0.2)}")
    print(f"TensorBoard Log Dir   : {log_dir}")
    print(f"Checkpoints Directory : {save_dir}")
    print("=================================================================\n")

    # Instantiate PPO agent wrapper
    agent = PPOAgent(
        env=env,
        learning_rate=ppo_cfg.get("lr", 3e-4),
        n_steps=ppo_cfg.get("n_steps", 2048),
        batch_size=ppo_cfg.get("batch_size", 64),
        n_epochs=ppo_cfg.get("n_epochs", 10),
        gamma=ppo_cfg.get("gamma", 0.99),
        clip_range=ppo_cfg.get("clip_range", 0.2),
        ent_coef=ppo_cfg.get("ent_coef", 0.01),
        vf_coef=ppo_cfg.get("vf_coef", 0.5),
        policy=args.policy,
        tensorboard_log=str(log_dir),
        verbose=args.verbose,
        seed=args.seed,
        device=args.device,
    )

    # Instantiate custom callback
    callback = AutoscalingMetricsCallback(
        save_path=str(save_dir),
        verbose=args.verbose,
    )

    # Train PPO Agent
    print("[*] Starting PPO training loop...")
    agent.train(
        total_timesteps=total_timesteps,
        callback=callback,
    )

    # Save final model
    final_model_path = save_dir / "final_ppo_model.zip"
    agent.save(final_model_path)
    print(f"\nFinal PPO model saved to: {final_model_path}")

    # Run evaluation
    print("\n[*] Running final evaluation over 10 episodes...")
    try:
        eval_metrics = agent.evaluate(env, n_episodes=10)
        print("Evaluation Summary:")
        for metric, val in eval_metrics.items():
            print(f"  {metric:22s}: {val:10.4f}")
    except Exception as exc:
        print(f"[Warning] Post-training evaluation could not be completed: {exc}")

    print("\nPPO Training Complete.")


if __name__ == "__main__":
    train_ppo()
