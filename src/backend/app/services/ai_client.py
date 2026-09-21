import json
import logging
from typing import Dict, Any, Optional
import httpx
from ..config import settings

logger = logging.getLogger("backend.services.ai_client")


def fallback_scaling_decision(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Intelligent heuristic fallback when the RL agent endpoint is offline
    or during local standalone development.
    """
    cpu = float(state.get("cpu_percent", 0.0))
    memory = float(state.get("memory_percent", 0.0))
    request_rate = float(state.get("request_rate", 0.0))
    response_time = float(state.get("response_time_ms", 0.0))
    instances = max(1, int(state.get("instance_count", 1)))
    error_rate = float(state.get("error_rate", 0.0))

    # Scale Up Trigger: High pressure or flash-sale surge
    if cpu >= 75.0 or memory >= 80.0 or response_time >= 800.0 or request_rate >= (instances * 80.0) or error_rate >= 5.0:
        step = 2 if (cpu >= 85.0 or response_time >= 1200.0) else 1
        return {
            "action": "scale_up",
            "current_instances": instances,
            "desired_instances": min(instances + step, 50),
            "confidence": 0.92,
            "reason": f"High festival traffic: CPU={cpu}%, Mem={memory}%, Latency={response_time}ms, ReqRate={request_rate}/s.",
            "triggered_by": "heuristic_fallback"
        }

    # Scale Down Trigger: Cluster significantly underutilized
    if cpu <= 30.0 and memory <= 40.0 and response_time <= 350.0 and request_rate <= (instances * 25.0) and instances > 1:
        return {
            "action": "scale_down",
            "current_instances": instances,
            "desired_instances": max(instances - 1, 1),
            "confidence": 0.85,
            "reason": f"Low workload pressure: CPU={cpu}%, Mem={memory}%, Latency={response_time}ms. Conserving resources.",
            "triggered_by": "heuristic_fallback"
        }

    # Maintain Equilibrium
    return {
        "action": "maintain",
        "current_instances": instances,
        "desired_instances": instances,
        "confidence": 0.88,
        "reason": f"Cluster operating within normal SLA thresholds (CPU={cpu}%, Latency={response_time}ms).",
        "triggered_by": "heuristic_fallback"
    }


def query_rl_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Communicates with Arpita's RL model inference endpoint.
    Seamlessly falls back to heuristic policy if endpoint is not configured or unavailable.
    """
    if not settings.AI_SERVICE_URL:
        logger.debug("AI_SERVICE_URL not configured. Using fallback policy.")
        return fallback_scaling_decision(state)

    try:
        with httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{settings.AI_SERVICE_URL.rstrip('/')}/predict",
                json=state
            )
            if response.status_code == 200:
                data = response.json()
                data["triggered_by"] = "rl_agent"
                return data
            logger.warning("RL service returned status %d. Falling back to heuristic.", response.status_code)
            return fallback_scaling_decision(state)
    except Exception as exc:
        logger.warning("Failed to connect to RL service at %s: %s. Using heuristic fallback.", settings.AI_SERVICE_URL, exc)
        return fallback_scaling_decision(state)


def send_rl_feedback(decision_id: int, observed_response_time_ms: float, observed_cpu_percent: float, reward: Optional[float] = None) -> Dict[str, Any]:
    """
    Sends reward/feedback metric back to RL model for experience replay.
    """
    # Calculate synthetic reward if none provided: reward = -latency_penalty - cost_penalty
    if reward is None:
        latency_penalty = (observed_response_time_ms / 500.0)
        cpu_optimal_dist = abs(observed_cpu_percent - 65.0) / 100.0
        reward = round(1.0 - latency_penalty - cpu_optimal_dist, 4)

    feedback_payload = {
        "decision_id": decision_id,
        "observed_response_time_ms": observed_response_time_ms,
        "observed_cpu_percent": observed_cpu_percent,
        "reward": reward
    }

    if settings.AI_SERVICE_URL:
        try:
            with httpx.Client(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                client.post(f"{settings.AI_SERVICE_URL.rstrip('/')}/feedback", json=feedback_payload)
        except Exception as exc:
            logger.warning("Failed to dispatch feedback to RL agent: %s", exc)

    return feedback_payload
