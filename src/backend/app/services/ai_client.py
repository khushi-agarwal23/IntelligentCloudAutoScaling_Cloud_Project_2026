
import logging
import pickle
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

from ..config import settings

logger = logging.getLogger("backend.services.ai_client")

# Project root:
# IntelligentCloudAutoScaling_Cloud_Project_2026/
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
MODEL_PATH = PROJECT_ROOT / "models" / "q_table.pkl"

# Lazy loading avoids making backend startup depend on the model file.
_rl_agent = None
_rl_load_attempted = False


def get_local_rl_agent():
    """Load the existing Q-learning model once, when first needed."""
    global _rl_agent, _rl_load_attempted

    if _rl_load_attempted:
        return _rl_agent

    _rl_load_attempted = True

    try:
        if not MODEL_PATH.is_file():
            logger.warning("Local RL model not found: %s", MODEL_PATH)
            return None

        with MODEL_PATH.open("rb") as model_file:
            agent = pickle.load(model_file)

        if not hasattr(agent, "q_table") or not hasattr(agent, "choose_action"):
            logger.warning("Local RL model has an unexpected format.")
            return None

        _rl_agent = agent
        logger.info(
            "Loaded local Q-learning model with %d states.",
            len(agent.q_table),
        )
        return _rl_agent

    except Exception:
        logger.exception("Could not load the local Q-learning model.")
        return None


def fallback_scaling_decision(state: Dict[str, Any]) -> Dict[str, Any]:
    """Existing heuristic policy used if no RL model is available."""
    cpu = float(state.get("cpu_percent", 0.0))
    memory_value = state.get("memory_percent")
    memory = float(memory_value) if memory_value is not None else None
    request_rate = float(state.get("request_rate", 0.0))
    response_time = float(state.get("response_time_ms", 0.0))
    instances = max(1, int(state.get("instance_count", 1)))
    error_rate = float(state.get("error_rate", 0.0))

    if (
        cpu >= 75.0
        or (memory is not None and memory >= 80.0)
        or response_time >= 800.0
        or request_rate >= instances * 80.0
        or error_rate >= 5.0
    ):
        step = 2 if cpu >= 85.0 or response_time >= 1200.0 else 1
        desired = min(instances + step, 3)
        return {
            "action": "scale_up",
            "current_instances": instances,
            "desired_instances": desired,
            "confidence": 0.92,
            "reason": (
                f"High workload: CPU={cpu}%, memory={memory}%, "
                f"latency={response_time}ms, request rate={request_rate}/s."
            ),
            "triggered_by": "heuristic_fallback",
        }

    if (
        cpu <= 30.0
        and memory is not None and memory <= 40.0
        and response_time <= 350.0
        and request_rate <= instances * 25.0
        and instances > 1
    ):
        return {
            "action": "scale_down",
            "current_instances": instances,
            "desired_instances": max(instances - 1, 1),
            "confidence": 0.85,
            "reason": "Low workload pressure; heuristic recommends scaling in.",
            "triggered_by": "heuristic_fallback",
        }

    return {
        "action": "maintain",
        "current_instances": instances,
        "desired_instances": instances,
        "confidence": 0.88,
        "reason": "Workload remains within the heuristic policy's thresholds.",
        "triggered_by": "heuristic_fallback",
    }


def local_rl_decision(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Use the existing Q-table.

    Note: request_rate is mapped using the original model's count thresholds.
    This is a prototype assumption because requests/second may not match the
    units used when the Q-table was trained.
    """
    agent = get_local_rl_agent()
    if agent is None:
        return None

    cpu = float(state.get("cpu_percent", 0.0))
    request_rate = float(state.get("request_rate", 0.0))
    instances = max(1, min(3, int(state.get("instance_count", 1))))

    cpu_level = 0 if cpu < 30 else 1 if cpu <= 60 else 2
    request_level = (
        0 if request_rate < 40
        else 1 if request_rate <= 70
        else 2
    )

    rl_state = (cpu_level, request_level, instances)

    # Avoid modifying the Q-table when an unseen state is encountered.
    q_values = agent.q_table.get(rl_state)
    if not q_values:
        logger.warning("Q-table has no entry for state %s.", rl_state)
        return None

    action_id = max(
        range(len(q_values)),
        key=lambda index: q_values[index],
    )

    action_names = {
        0: "scale_down",
        1: "maintain",
        2: "scale_up",
    }
    action = action_names.get(action_id)

    if action is None:
        return None

    desired = instances
    if action == "scale_up":
        desired = min(instances + 1, 3)
    elif action == "scale_down":
        desired = max(instances - 1, 1)

    return {
        "action": action,
        "current_instances": instances,
        "desired_instances": desired,
        "confidence": 0.0,
        "reason": (
            f"Local Q-learning policy selected action {action_id} "
            f"for state {rl_state}; Q-values={q_values}."
        ),
        "triggered_by": "q_learning_local",
    }


def query_rl_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Prefer a configured RL service, then the local Q-table, then heuristic."""
    if settings.SCALING_POLICY.strip().lower() == "ppo_candidate":
        from fastapi import HTTPException
        from .ppo_policy import PPOPolicyError, ppo_decision
        try:
            return ppo_decision(state)
        except PPOPolicyError as exc:
            logger.error("PPO candidate inference failed closed: %s", exc)
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    if settings.SCALING_POLICY.strip().lower() != "q_learning":
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="SCALING_POLICY must be q_learning or ppo_candidate.")
    if settings.AI_SERVICE_URL:
        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                response = client.post(
                    f"{settings.AI_SERVICE_URL.rstrip('/')}/predict",
                    json=state,
                )
                response.raise_for_status()
                data = response.json()
                data["triggered_by"] = "rl_agent"
                return data
        except Exception as exc:
            logger.warning(
                "Remote RL service unavailable (%s); trying local Q-table.",
                exc,
            )

    local_decision = local_rl_decision(state)
    if local_decision is not None:
        return local_decision

    decision = fallback_scaling_decision(state)
    decision["triggered_by"] = "heuristic_fallback"
    return decision


def send_rl_feedback(
    decision_id: int,
    observed_response_time_ms: float,
    observed_cpu_percent: float,
    reward: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate and record feedback; forward it if a remote service exists."""
    if reward is None:
        latency_penalty = observed_response_time_ms / 500.0
        cpu_optimal_dist = abs(observed_cpu_percent - 65.0) / 100.0
        reward = round(1.0 - latency_penalty - cpu_optimal_dist, 4)

    feedback_payload = {
        "decision_id": decision_id,
        "observed_response_time_ms": observed_response_time_ms,
        "observed_cpu_percent": observed_cpu_percent,
        "reward": reward,
    }

    if settings.AI_SERVICE_URL:
        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                client.post(
                    f"{settings.AI_SERVICE_URL.rstrip('/')}/feedback",
                    json=feedback_payload,
                )
        except Exception as exc:
            logger.warning("Could not send RL feedback: %s", exc)

    return feedback_payload
