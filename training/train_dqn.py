"""
DQN Training Script for Cloud Autoscaling Environments.

This script trains a Deep Q-Network (DQN) agent on the ECommerceScalingEnv.
Hyperparameters are loaded from hyperparams.yaml and can be overridden via
command-line arguments. Metrics (episode reward, SLA violations, cost, epsilon,
and loss) are logged to TensorBoard, and the best-performing model checkpoint is saved.
"""

from __future__ import annotations

import argparse
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
import yaml

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional TensorBoard SummaryWriter with fallback warning
try:
    from torch.utils.tensorboard import SummaryWriter
except ImportError:
    try:
        from tensorboardX import SummaryWriter  # type: ignore[no-redef]
    except ImportError:
        SummaryWriter = None  # type: ignore[assignment, misc]

# Import environment and DQN agent with robust fallbacks
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
    from agents.dqn_agent import DQNAgent
except ImportError:
    try:
        from agents import DQNAgent  # type: ignore[no-redef]
    except ImportError:
        DQNAgent = None  # type: ignore[assignment, misc]


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to the hyperparams.yaml file.

    Returns:
        Dictionary with parsed configuration data.
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
    Instantiate ECommerceScalingEnv dynamically matching available constructor arguments.

    Args:
        env_cfg: Environment configuration parameters.
        reward_cfg: Reward weights and penalty parameters.
        seed: Random seed for initialization.

    Returns:
        Instantiated gymnasium environment.
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
    return env


def create_dqn_agent(
    env: gym.Env,
    dqn_cfg: Dict[str, Any],
    device: str = "auto",
) -> Any:
    """
    Instantiate DQNAgent dynamically matching available constructor parameters.

    Args:
        env: The gymnasium environment.
        dqn_cfg: DQN hyperparameters dictionary.
        device: Device to run PyTorch computations ('cpu', 'cuda', etc.).

    Returns:
        Instantiated DQNAgent.
    """
    if DQNAgent is None:
        raise ImportError(
            "DQNAgent could not be found. Please ensure agents/dqn_agent.py "
            "is created and defines DQNAgent."
        )

    # Infer state and action dimensions
    obs_space = env.observation_space
    act_space = env.action_space

    state_dim = obs_space.shape[0] if obs_space.shape is not None and len(obs_space.shape) > 0 else 10
    action_dim = act_space.n if hasattr(act_space, "n") else 3

    possible_args: Dict[str, Any] = {
        "env": env,
        "state_dim": state_dim,
        "obs_dim": state_dim,
        "observation_dim": state_dim,
        "action_dim": action_dim,
        "action_size": action_dim,
        "num_actions": action_dim,
        "lr": dqn_cfg.get("lr", 0.0005),
        "learning_rate": dqn_cfg.get("lr", 0.0005),
        "gamma": dqn_cfg.get("gamma", 0.99),
        "epsilon_start": dqn_cfg.get("epsilon_start", 1.0),
        "epsilon_end": dqn_cfg.get("epsilon_end", 0.05),
        "epsilon_decay": dqn_cfg.get("epsilon_decay", 0.995),
        "batch_size": dqn_cfg.get("batch_size", 64),
        "buffer_size": dqn_cfg.get("buffer_size", 50000),
        "target_update_freq": dqn_cfg.get("target_update_freq", 10),
        "device": device,
    }

    sig = inspect.signature(DQNAgent.__init__)
    agent_kwargs = {k: v for k, v in possible_args.items() if k in sig.parameters}

    return DQNAgent(**agent_kwargs)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for DQN training."""
    parser = argparse.ArgumentParser(
        description="Train DQN agent on ECommerceScalingEnv with TensorBoard logging."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="hyperparams.yaml",
        help="Path to YAML hyperparameter config file (default: hyperparams.yaml).",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=None,
        help="Total number of training episodes (default: 500 or from config).",
    )
    parser.add_argument("--lr", type=float, default=None, help="Learning rate for DQN optimizer.")
    parser.add_argument("--gamma", type=float, default=None, help="Discount factor gamma.")
    parser.add_argument("--epsilon-start", type=float, default=None, help="Initial exploration rate.")
    parser.add_argument("--epsilon-end", type=float, default=None, help="Minimum exploration rate.")
    parser.add_argument("--epsilon-decay", type=float, default=None, help="Exploration decay factor.")
    parser.add_argument("--batch-size", type=int, default=None, help="Replay buffer batch size.")
    parser.add_argument("--buffer-size", type=int, default=None, help="Replay buffer capacity.")
    parser.add_argument(
        "--target-update-freq",
        type=int,
        default=None,
        help="Target network update frequency.",
    )
    parser.add_argument(
        "--save-dir",
        type=str,
        default="./checkpoints/dqn",
        help="Directory to save model checkpoints (default: ./checkpoints/dqn).",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="./logs/dqn",
        help="TensorBoard log directory (default: ./logs/dqn).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Device to use ('auto', 'cpu', 'cuda', 'mps').",
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


def train_dqn() -> None:
    """Execute the DQN training pipeline."""
    args = parse_args()

    # Load configuration from YAML
    yaml_config = load_config(args.config)
    dqn_cfg: Dict[str, Any] = yaml_config.get("dqn", {})
    env_cfg: Dict[str, Any] = yaml_config.get("environment", {})
    reward_cfg: Dict[str, Any] = yaml_config.get("reward", {})

    # Apply command-line overrides
    num_episodes = args.episodes if args.episodes is not None else dqn_cfg.get("episodes", 500)
    if args.lr is not None:
        dqn_cfg["lr"] = args.lr
    if args.gamma is not None:
        dqn_cfg["gamma"] = args.gamma
    if args.epsilon_start is not None:
        dqn_cfg["epsilon_start"] = args.epsilon_start
    if args.epsilon_end is not None:
        dqn_cfg["epsilon_end"] = args.epsilon_end
    if args.epsilon_decay is not None:
        dqn_cfg["epsilon_decay"] = args.epsilon_decay
    if args.batch_size is not None:
        dqn_cfg["batch_size"] = args.batch_size
    if args.buffer_size is not None:
        dqn_cfg["buffer_size"] = args.buffer_size
    if args.target_update_freq is not None:
        dqn_cfg["target_update_freq"] = args.target_update_freq

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

    target_update_freq = dqn_cfg.get("target_update_freq", 10)

    # Prepare directories
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Initialize TensorBoard writer
    writer: Optional[SummaryWriter] = None
    if SummaryWriter is not None:
        writer = SummaryWriter(log_dir=str(log_dir))
        print(f"[TensorBoard] Logging to: {log_dir}")
    else:
        print("[Warning] TensorBoard / tensorboardX is not installed. Skipping TensorBoard logging.")

    # Create Environment and DQN Agent
    env = create_environment(env_cfg, reward_cfg, seed=args.seed)
    agent = create_dqn_agent(env, dqn_cfg, device=args.device)

    print("=================================================================")
    print("                DQN Autoscaling Agent Training                   ")
    print("=================================================================")
    print(f"Total Episodes        : {num_episodes}")
    print(f"Target Update Freq    : {target_update_freq}")
    print(f"Replay Buffer Size    : {dqn_cfg.get('buffer_size', 50000)}")
    print(f"Batch Size            : {dqn_cfg.get('batch_size', 64)}")
    print(f"Initial Epsilon       : {dqn_cfg.get('epsilon_start', 1.0)}")
    print(f"Checkpoints Directory : {save_dir}")
    print("=================================================================\n")

    best_reward = -float("inf")
    recent_rewards: list[float] = []

    for episode in range(1, num_episodes + 1):
        # Reset environment
        reset_res = env.reset(seed=args.seed + episode if args.seed is not None else None)
        state = reset_res[0] if isinstance(reset_res, tuple) else reset_res

        episode_reward = 0.0
        ep_sla_violations = 0.0
        ep_cost = 0.0
        step_losses: list[float] = []
        step_count = 0
        done = False

        while not done:
            # Select action
            action = agent.select_action(state)

            # Step environment
            next_state, reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated)

            # Store transition in replay buffer
            if hasattr(agent, "store_transition"):
                agent.store_transition(state, action, reward, next_state, done)
            elif hasattr(agent, "remember"):
                agent.remember(state, action, reward, next_state, done)
            elif hasattr(agent, "replay_buffer"):
                if hasattr(agent.replay_buffer, "push"):
                    agent.replay_buffer.push(state, action, reward, next_state, done)
                elif hasattr(agent.replay_buffer, "add"):
                    agent.replay_buffer.add(state, action, reward, next_state, done)

            # Train agent step
            loss = None
            if hasattr(agent, "train_step"):
                loss = agent.train_step()
            elif hasattr(agent, "update"):
                loss = agent.update()
            elif hasattr(agent, "train"):
                loss = agent.train()
            elif hasattr(agent, "learn"):
                loss = agent.learn()

            if loss is not None:
                if hasattr(loss, "item"):
                    step_losses.append(float(loss.item()))
                elif isinstance(loss, (int, float)):
                    step_losses.append(float(loss))

            episode_reward += float(reward)
            step_count += 1

            # Track SLA violations from info dict
            if "sla_violation" in info:
                ep_sla_violations += float(info["sla_violation"])
            elif "sla_violations" in info:
                ep_sla_violations = float(info["sla_violations"])

            # Track cost from info dict
            if "cost" in info:
                ep_cost += float(info["cost"])
            elif "total_cost" in info:
                ep_cost = float(info["total_cost"])

            state = next_state

        # Post-episode hook: epsilon decay
        if hasattr(agent, "decay_epsilon"):
            agent.decay_epsilon()

        # Post-episode hook: periodic target network update
        if hasattr(agent, "update_target_network") and episode % target_update_freq == 0:
            agent.update_target_network()

        # Compute episode summary statistics
        avg_loss = float(np.mean(step_losses)) if step_losses else 0.0
        epsilon_val = float(getattr(agent, "epsilon", getattr(agent, "eps", 0.0)))
        recent_rewards.append(episode_reward)
        if len(recent_rewards) > 10:
            recent_rewards.pop(0)

        # TensorBoard Logging
        if writer is not None:
            writer.add_scalar("Train/Episode_Reward", episode_reward, episode)
            writer.add_scalar("Train/SLA_Violations", ep_sla_violations, episode)
            writer.add_scalar("Train/Cost", ep_cost, episode)
            writer.add_scalar("Train/Epsilon", epsilon_val, episode)
            writer.add_scalar("Train/Loss", avg_loss, episode)
            writer.add_scalar("Train/Episode_Length", step_count, episode)

        # Save best model checkpoint based on reward
        if episode_reward > best_reward:
            best_reward = episode_reward
            best_checkpoint_path = save_dir / "best_dqn_model.pt"
            if hasattr(agent, "save"):
                agent.save(str(best_checkpoint_path))
                print(
                    f"[*] Checkpoint saved: New best reward {best_reward:.2f} at episode {episode} "
                    f"-> {best_checkpoint_path}"
                )

        # Print progress every 10 episodes
        if episode % 10 == 0 or episode == 1:
            mean_10 = float(np.mean(recent_rewards))
            print(
                f"Episode {episode:4d}/{num_episodes:4d} | "
                f"Reward: {episode_reward:8.2f} (10-ep avg: {mean_10:8.2f}) | "
                f"SLA Violations: {ep_sla_violations:4.0f} | "
                f"Cost: {ep_cost:7.2f} | "
                f"Epsilon: {epsilon_val:.4f} | "
                f"Loss: {avg_loss:8.4f}"
            )

    # Save final model
    final_checkpoint_path = save_dir / "final_dqn_model.pt"
    if hasattr(agent, "save"):
        agent.save(str(final_checkpoint_path))
        print(f"\nFinal model saved to: {final_checkpoint_path}")

    if writer is not None:
        writer.close()

    print("\nDQN Training Complete.")


if __name__ == "__main__":
    train_dqn()
