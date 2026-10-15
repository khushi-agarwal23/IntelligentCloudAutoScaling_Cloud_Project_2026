"""Environment package for e-commerce cloud autoscaling RL.

Exposes:
- WorkloadSimulator: Alibaba 2018 trace replay and synthetic traffic generator.
- ECommerceScalingEnv: Gymnasium environment for autoscaling policy optimization.
"""

from environment.ecommerce_env import ECommerceScalingEnv
from environment.workload_simulator import WorkloadSimulator

# Register environment with Gymnasium if gymnasium is installed
try:
    import gymnasium as gym

    if "ECommerceScaling-v0" not in gym.envs.registry:
        gym.register(
            id="ECommerceScaling-v0",
            entry_point="environment.ecommerce_env:ECommerceScalingEnv",
            max_episode_steps=288,
        )
except (ImportError, Exception):
    pass

__all__ = ["WorkloadSimulator", "ECommerceScalingEnv"]
