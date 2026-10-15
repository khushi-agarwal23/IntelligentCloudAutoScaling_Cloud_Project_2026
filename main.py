#!/usr/bin/env python3
"""
RL-Based Autoscaling for E-Commerce Cloud Infrastructure
=========================================================

Main entrypoint for training, evaluating, and comparing RL agents
(DQN, PPO, Hierarchical RL) for autoscaling decisions using
Alibaba Cloud 2018 cluster trace data.

Usage:
    python main.py train --agent dqn --episodes 500
    python main.py train --agent ppo --timesteps 100000
    python main.py train --agent hierarchical --episodes 500
    python main.py evaluate --models-dir models/ --episodes 20
    python main.py compare --models-dir models/ --episodes 20
    python main.py demo --agent dqn --model-path models/best_dqn_model.pt
"""

import argparse
import os
import sys
import random
import yaml
import numpy as np
import torch

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from environment.ecommerce_env import ECommerceScalingEnv
from agents.dqn_agent import DQNAgent
from agents.ppo_agent import PPOAgent


def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility across all libraries."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device() -> str:
    """Auto-detect best available device (CUDA > MPS > CPU)."""
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"[INFO] Using device: {device}")
    return device


def load_config(config_path: str) -> dict:
    """Load hyperparameters from YAML config file."""
    default_path = os.path.join(PROJECT_ROOT, "training", "hyperparams.yaml")
    path = config_path if config_path else default_path
    if os.path.exists(path):
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        print(f"[INFO] Loaded config from {path}")
        return config
    else:
        print(f"[WARN] Config not found at {path}, using defaults.")
        return {}


# ─────────────────────────────────────────────────────────
# TRAIN
# ─────────────────────────────────────────────────────────

def cmd_train(args: argparse.Namespace) -> None:
    """Train an RL agent for autoscaling."""
    set_seed(args.seed)
    device = get_device()
    config = load_config(args.config)

    env = ECommerceScalingEnv(data_path=args.data_path)

    if args.agent == "dqn":
        _train_dqn(env, config, device, args)
    elif args.agent == "ppo":
        _train_ppo(env, config, args)
    elif args.agent == "hierarchical":
        _train_hierarchical(env, config, device, args)
    else:
        print(f"[ERROR] Unknown agent: {args.agent}")
        sys.exit(1)


def _train_dqn(env, config: dict, device: str, args) -> None:
    """Train DQN agent inline with proper data_path support."""
    print("\n" + "=" * 60)
    print("  TRAINING DQN AGENT (Alibaba Trace Data)")
    print("=" * 60)

    dqn_cfg = config.get("dqn", {})
    episodes = args.episodes or dqn_cfg.get("episodes", 500)
    target_update_freq = dqn_cfg.get("target_update_freq", 10)

    agent = DQNAgent(state_dim=10, action_dim=3, device=device,
                     lr=dqn_cfg.get("lr", 1e-3),
                     gamma=dqn_cfg.get("gamma", 0.99),
                     epsilon_start=dqn_cfg.get("epsilon_start", 1.0),
                     epsilon_end=dqn_cfg.get("epsilon_end", 0.01),
                     epsilon_decay=dqn_cfg.get("epsilon_decay", 0.995),
                     batch_size=dqn_cfg.get("batch_size", 64),
                     buffer_size=dqn_cfg.get("buffer_size", 50000))

    print(f"Episodes: {episodes} | Device: {device} | Data: {env.simulator.data_source}")

    os.makedirs(args.models_dir, exist_ok=True)
    best_reward = -float("inf")
    recent_rewards = []

    for episode in range(1, episodes + 1):
        reset_res = env.reset(seed=args.seed + episode)
        state = reset_res[0] if isinstance(reset_res, tuple) else reset_res
        episode_reward = 0.0
        sla_violations = 0
        ep_cost = 0.0
        done = False

        while not done:
            action = agent.select_action(state)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated)

            if hasattr(agent, "replay_buffer") and hasattr(agent.replay_buffer, "push"):
                agent.replay_buffer.push(state, action, reward, next_state, done)

            loss = agent.train_step() if hasattr(agent, "train_step") else None
            episode_reward += float(reward)
            if info.get("sla_violation", False):
                sla_violations += 1
            ep_cost += info.get("cost", 0.0)
            state = next_state

        if hasattr(agent, "decay_epsilon"):
            agent.decay_epsilon()
        if hasattr(agent, "update_target_network") and episode % target_update_freq == 0:
            agent.update_target_network()

        recent_rewards.append(episode_reward)
        if len(recent_rewards) > 10:
            recent_rewards.pop(0)

        if episode_reward > best_reward:
            best_reward = episode_reward
            agent.save(os.path.join(args.models_dir, "best_dqn_model.pt"))

        if episode % 10 == 0 or episode == 1:
            avg10 = float(np.mean(recent_rewards))
            eps_val = getattr(agent, "epsilon", 0.0)
            print(f"  Ep {episode:4d}/{episodes} | Reward: {episode_reward:8.2f} "
                  f"(avg10: {avg10:8.2f}) | SLA: {sla_violations} | "
                  f"Cost: {ep_cost:.0f} | ε: {eps_val:.4f}")

    agent.save(os.path.join(args.models_dir, "final_dqn_model.pt"))
    print(f"\n✅ DQN Training Complete! Best reward: {best_reward:.2f}")


def _train_ppo(env, config: dict, args) -> None:
    """Train PPO agent inline with proper data_path support."""
    print("\n" + "=" * 60)
    print("  TRAINING PPO AGENT (Alibaba Trace Data)")
    print("=" * 60)

    ppo_cfg = config.get("ppo", {})
    timesteps = args.timesteps or ppo_cfg.get("total_timesteps", 100000)

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
        verbose=1,
        seed=args.seed,
    )

    print(f"Timesteps: {timesteps} | Data: {env.simulator.data_source}")

    os.makedirs(args.models_dir, exist_ok=True)
    agent.train(total_timesteps=timesteps)

    agent.save(os.path.join(args.models_dir, "best_ppo_model.zip"))
    agent.save(os.path.join(args.models_dir, "final_ppo_model.zip"))
    print(f"\n✅ PPO Training Complete!")


def _train_hierarchical(env, config: dict, device: str, args) -> None:
    """Train Hierarchical RL agent."""
    try:
        from novelty.hierarchical_rl import HierarchicalRLAgent, train_hierarchical
    except ImportError:
        print("[ERROR] Hierarchical RL module not found. Check novelty/hierarchical_rl.py")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  TRAINING HIERARCHICAL RL AGENT")
    print("=" * 60)

    episodes = args.episodes or config.get("dqn", {}).get("episodes", 500)
    agent = HierarchicalRLAgent(state_dim=10, action_dim=3, device=device)
    train_hierarchical(env, agent, episodes=episodes)

    os.makedirs(args.models_dir, exist_ok=True)
    save_path = os.path.join(args.models_dir, "hierarchical_agent")
    agent.save(save_path)
    print(f"[INFO] Hierarchical agent saved to {save_path}")


# ─────────────────────────────────────────────────────────
# EVALUATE
# ─────────────────────────────────────────────────────────

def cmd_evaluate(args: argparse.Namespace) -> None:
    """Evaluate trained agents."""
    set_seed(args.seed)
    device = get_device()

    env = ECommerceScalingEnv(data_path=args.data_path)

    results = {}

    # Try loading DQN
    dqn_path = os.path.join(args.models_dir, "best_dqn_model.pt")
    if os.path.exists(dqn_path):
        print(f"\n[INFO] Loading DQN from {dqn_path}")
        dqn_agent = DQNAgent(state_dim=10, action_dim=3, device=device)
        dqn_agent.load(dqn_path)
        results["DQN"] = dqn_agent.evaluate(env, n_episodes=args.episodes)
        print(f"  DQN Results: {results['DQN']}")

    # Try loading PPO
    ppo_path = os.path.join(args.models_dir, "best_ppo_model.zip")
    if os.path.exists(ppo_path):
        print(f"\n[INFO] Loading PPO from {ppo_path}")
        ppo_agent = PPOAgent(env=env)
        ppo_agent.load(ppo_path)
        results["PPO"] = ppo_agent.evaluate(env, n_episodes=args.episodes)
        print(f"  PPO Results: {results['PPO']}")

    # Try loading Hierarchical
    hrl_path = os.path.join(args.models_dir, "hierarchical_agent")
    if os.path.exists(hrl_path):
        try:
            from novelty.hierarchical_rl import HierarchicalRLAgent
            print(f"\n[INFO] Loading Hierarchical RL from {hrl_path}")
            hrl_agent = HierarchicalRLAgent(state_dim=10, action_dim=3, device=device)
            hrl_agent.load(hrl_path)
            results["Hierarchical RL"] = hrl_agent.evaluate(env, n_episodes=args.episodes)
            print(f"  HRL Results: {results['Hierarchical RL']}")
        except ImportError:
            print("[WARN] Hierarchical RL module not available")

    if not results:
        print("[WARN] No trained models found. Train agents first.")
        return

    # Print summary
    print("\n" + "=" * 60)
    print("  EVALUATION SUMMARY")
    print("=" * 60)
    for name, metrics in results.items():
        print(f"\n  {name}:")
        for k, v in metrics.items():
            print(f"    {k}: {v:.4f}" if isinstance(v, float) else f"    {k}: {v}")


# ─────────────────────────────────────────────────────────
# COMPARE
# ─────────────────────────────────────────────────────────

def cmd_compare(args: argparse.Namespace) -> None:
    """Run full comparison of all methods including baselines."""
    set_seed(args.seed)

    try:
        from evaluation.evaluate import main as evaluate_main
        evaluate_main(
            models_dir=args.models_dir,
            n_episodes=args.episodes,
            data_path=args.data_path,
        )
    except ImportError:
        print("[ERROR] Evaluation module not found. Check evaluation/evaluate.py")
        # Fallback: run evaluate command
        cmd_evaluate(args)


# ─────────────────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────────────────

def cmd_demo(args: argparse.Namespace) -> None:
    """Run a single demo episode with live visualization."""
    import matplotlib.pyplot as plt

    set_seed(args.seed)
    device = get_device()

    env = ECommerceScalingEnv(data_path=args.data_path)

    # Default model path if not specified
    model_path = args.model_path
    if not model_path:
        if args.agent == "dqn":
            model_path = "models/best_dqn_model.pt"
        elif args.agent == "ppo":
            model_path = "models/best_ppo_model.zip"

    # Load agent
    if args.agent == "dqn":
        agent = DQNAgent(state_dim=10, action_dim=3, device=device)
        agent.load(model_path)
    elif args.agent == "ppo":
        agent = PPOAgent(env=env)
        agent.load(model_path)
    else:
        print(f"[ERROR] Demo not supported for agent: {args.agent}")
        return

    # Run one episode and collect data
    state, _ = env.reset()
    done = False
    step_data = {
        "cpu": [], "request_rate": [], "response_time": [],
        "instances": [], "actions": [], "rewards": [], "cost": []
    }
    action_icons = {0: "HOLD ⏸️", 1: "SCALE OUT ➕", 2: "SCALE IN ➖"}

    total_reward = 0.0
    step_count = 0

    print("\n" + "=" * 90)
    print(f"  LIVE SCALING DEMO — {args.agent.upper()} AGENT")
    print("=" * 90)
    print(f"{'Step':>4} | {'Time':>5} | {'Reqs/sec':>8} | {'CPU%':>6} | {'Instances':>9} | {'Action':>13} | {'Latency':>10} | {'SLA Status'}")
    print("-" * 90)

    while not done:
        action = agent.select_action(state, training=False)
        next_state, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated

        step_data["cpu"].append(state[0])
        step_data["request_rate"].append(state[2])
        step_data["response_time"].append(next_state[3])
        step_data["instances"].append(next_state[4])
        step_data["actions"].append(action)
        step_data["rewards"].append(reward)
        step_data["cost"].append(next_state[8])

        total_reward += reward
        step_count += 1

        # Print live steps (every 5 steps or whenever a scale in/out occurs)
        if step_count <= 25 or action != 0 or step_count % 20 == 0:
            hour = int((step_count * 5) / 60)
            minute = (step_count * 5) % 60
            sla_text = "⚠️ VIOLATION" if next_state[3] > 500.0 else "✅ OK"
            print(f"{step_count:4d} | {hour:02d}:{minute:02d} | {state[2]:8.0f} | {state[0]:5.1f}% | {int(next_state[4]):9d} | {action_icons.get(action, 'HOLD'):>13} | {next_state[3]:8.1f}ms | {sla_text}")

        state = next_state

    print(f"\n[DEMO] Episode completed: {step_count} steps, Total Reward: {total_reward:.2f}")

    # Plot results
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)

    axes[0].plot(step_data["request_rate"], color="blue", label="Request Rate")
    axes[0].set_ylabel("Requests/sec")
    axes[0].legend()
    axes[0].set_title("Demo Episode — Scaling Decisions Over Time")

    axes[1].plot(step_data["response_time"], color="orange", label="Response Time")
    axes[1].axhline(y=500, color="red", linestyle="--", alpha=0.7, label="SLA Threshold (500ms)")
    axes[1].set_ylabel("Response Time (ms)")
    axes[1].legend()

    axes[2].plot(step_data["instances"], color="green", label="Active Instances")
    # Mark scaling actions
    for i, a in enumerate(step_data["actions"]):
        if a == 1:
            axes[2].axvline(x=i, color="blue", alpha=0.15, linewidth=0.8)
        elif a == 2:
            axes[2].axvline(x=i, color="red", alpha=0.15, linewidth=0.8)
    axes[2].set_ylabel("Instances")
    axes[2].legend()

    axes[3].plot(step_data["rewards"], color="purple", label="Reward")
    axes[3].set_ylabel("Reward")
    axes[3].set_xlabel("Time Step (5-min intervals)")
    axes[3].legend()

    plt.tight_layout()
    os.makedirs("evaluation/plots", exist_ok=True)
    plt.savefig("evaluation/plots/demo_episode.png", dpi=150)
    print("[INFO] Demo plot saved to evaluation/plots/demo_episode.png")
    plt.show()


# ─────────────────────────────────────────────────────────
# CLI PARSER
# ─────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="RL-Based Autoscaling for E-Commerce Cloud Infrastructure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py train --agent dqn --episodes 500
  python main.py train --agent ppo --timesteps 100000
  python main.py train --agent hierarchical --episodes 500
  python main.py evaluate --models-dir models/ --episodes 20
  python main.py compare --models-dir models/
  python main.py demo --agent dqn --model-path models/best_dqn_model.pt
        """
    )

    # Common arguments
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--data-path", type=str, default=None,
                        help="Path to Alibaba trace CSV (default: synthetic)")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # TRAIN
    train_parser = subparsers.add_parser("train", help="Train an RL agent")
    train_parser.add_argument("--agent", type=str, required=True,
                              choices=["dqn", "ppo", "hierarchical"],
                              help="Agent type to train")
    train_parser.add_argument("--episodes", type=int, default=None,
                              help="Number of training episodes (DQN/HRL)")
    train_parser.add_argument("--timesteps", type=int, default=None,
                              help="Total timesteps (PPO)")
    train_parser.add_argument("--config", type=str, default=None,
                              help="Path to hyperparams YAML")
    train_parser.add_argument("--models-dir", type=str, default="models",
                              help="Directory to save models")
    train_parser.set_defaults(func=cmd_train)

    # EVALUATE
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate trained agents")
    eval_parser.add_argument("--models-dir", type=str, default="models",
                             help="Directory containing trained models")
    eval_parser.add_argument("--episodes", type=int, default=10,
                             help="Number of evaluation episodes")
    eval_parser.set_defaults(func=cmd_evaluate)

    # COMPARE
    compare_parser = subparsers.add_parser("compare", help="Compare all methods")
    compare_parser.add_argument("--models-dir", type=str, default="models",
                                help="Directory containing trained models")
    compare_parser.add_argument("--episodes", type=int, default=10,
                                help="Number of evaluation episodes")
    compare_parser.set_defaults(func=cmd_compare)

    # DEMO
    demo_parser = subparsers.add_parser("demo", help="Run a demo episode with visualization")
    demo_parser.add_argument("--agent", type=str, required=True,
                             choices=["dqn", "ppo"],
                             help="Agent type to demo")
    demo_parser.add_argument("--model-path", type=str, default=None,
                             help="Path to trained model (defaults to models/best_*.pt/zip)")
    demo_parser.set_defaults(func=cmd_demo)

    return parser


def main():
    """Main entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    print("=" * 60)
    print("  RL-Based Autoscaling for E-Commerce")
    print("  Alibaba Cloud 2018 Cluster Trace Data")
    print("=" * 60)

    args.func(args)


if __name__ == "__main__":
    main()
