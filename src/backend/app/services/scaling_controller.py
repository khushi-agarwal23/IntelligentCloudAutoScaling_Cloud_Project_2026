"""Safe controller shared by manual, CloudWatch, and replay evaluation paths."""
import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models.scaling import ScalingDecision
from .ai_client import local_rl_decision, query_rl_agent
from .aws_asg_client import aws_client

logger = logging.getLogger("backend.services.scaling_controller")
_VALID_ACTIONS = {"scale_up", "scale_down", "maintain", "scale_out", "scale_in"}


def _serialize_provenance(value: Optional[Dict[str, Any]]) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, separators=(",", ":"), sort_keys=True, default=str)


def _check_live_gates():
    if aws_client.mock_mode:
        return
    if not settings.AWS_LIVE_SCALING_ENABLED:
        raise HTTPException(status_code=403, detail="Live AWS scaling is disabled.")
    if not settings.AWS_LIVE_SCALING_PERMISSION_CONFIRMED:
        raise HTTPException(status_code=403, detail="Live scaling permission has not been confirmed by an AWS administrator.")


def _state_is_valid(state: Dict[str, Any]):
    for key in ("cpu_percent", "request_rate", "response_time_ms", "instance_count"):
        value = state.get(key)
        try:
            valid_number = value is not None and math.isfinite(float(value))
        except (TypeError, ValueError, OverflowError):
            valid_number = False
        if not valid_number:
            raise HTTPException(status_code=422, detail=f"Telemetry field {key} is missing or invalid.")
    memory = state.get("memory_percent")
    error_rate = state.get("error_rate", 0.0)
    try:
        memory_valid = memory is None or (math.isfinite(float(memory)) and 0 <= float(memory) <= 100)
        error_valid = math.isfinite(float(error_rate)) and 0 <= float(error_rate) <= 100
    except (TypeError, ValueError, OverflowError):
        memory_valid = error_valid = False
    if (not 0 <= float(state["cpu_percent"]) <= 100 or float(state["request_rate"]) < 0
            or float(state["response_time_ms"]) < 0 or not memory_valid or not error_valid):
        raise HTTPException(status_code=422, detail="Telemetry values are outside supported ranges.")
    try:
        integral_count = int(state["instance_count"]) == float(state["instance_count"])
    except (TypeError, ValueError, OverflowError):
        integral_count = False
    if not integral_count:
        raise HTTPException(status_code=422, detail="Instance count must be an integer.")


def _recent_applied_decision(db: Session):
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=max(0, settings.AWS_SCALING_COOLDOWN_SECONDS))
    return db.scalar(
        select(ScalingDecision)
        .where(ScalingDecision.aws_applied.is_(True), ScalingDecision.timestamp >= cutoff)
        .order_by(ScalingDecision.timestamp.desc())
        .limit(1)
    )


def evaluate_and_apply(
    db: Session,
    state: Dict[str, Any],
    *,
    telemetry_source: str,
    provenance: Optional[Dict[str, Any]] = None,
    apply_to_aws: bool = False,
    event_id: Optional[str] = None,
):
    """Evaluate with the current Q policy and optionally request one bounded ASG update."""
    _state_is_valid(state)
    if apply_to_aws and not aws_client.mock_mode:
        _check_live_gates()
        source_allows_live_action = (
            telemetry_source == "aws_cloudwatch"
            or (telemetry_source == "workload_replay" and settings.WORKLOAD_REPLAY_ALLOW_LIVE_SCALING)
        )
        if not source_allows_live_action:
            raise HTTPException(status_code=403, detail="Live AWS scaling requires fresh CloudWatch telemetry or separately enabled signed replay telemetry.")
    if apply_to_aws and not aws_client.mock_mode and settings.SCALING_POLICY.strip().lower() != "q_learning":
        raise HTTPException(status_code=403, detail="The configured policy is not approved for live AWS scaling.")
    live_preflight = None
    if apply_to_aws and not aws_client.mock_mode:
        live_preflight = aws_client.preflight()
        if not live_preflight.get("ready"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"message": "Read-only AWS preflight failed; no scaling change was attempted.", "preflight": live_preflight},
            )
        # Ignore client-supplied capacity when connected to AWS.
        state = dict(state)
        state["instance_count"] = int(live_preflight["capacity"]["current"])

    current = int(state["instance_count"])
    if live_preflight:
        minimum = int(live_preflight["capacity"]["minimum"])
        maximum = int(live_preflight["capacity"]["maximum"])
    else:
        minimum = int(settings.AWS_EXPECTED_MIN_SIZE)
        maximum = int(settings.AWS_EXPECTED_MAX_SIZE)
    if not minimum <= current <= maximum:
        raise HTTPException(status_code=422, detail="Current capacity is outside configured Auto Scaling Group bounds.")

    # When a live write is requested, never silently fall back to heuristics or a
    # remote service: require an explicitly validated production policy. The
    # teammate PPO checkpoint remains simulation-only pending validation of its
    # training/deployment feature mismatch and action quality.
    if apply_to_aws and not aws_client.mock_mode:
        if settings.SCALING_POLICY.strip().lower() != "q_learning":
            raise HTTPException(status_code=403, detail="The configured policy is not approved for live AWS scaling.")
        raw = local_rl_decision(state)
        if raw is None:
            raise HTTPException(status_code=503, detail="The local Q-learning policy has no decision for this live state; no AWS change was attempted.")
    else:
        raw = query_rl_agent(state)

    raw_action = str(raw.get("action", "maintain"))
    if raw_action not in _VALID_ACTIONS:
        raise HTTPException(status_code=503, detail="Policy returned an unsupported action; no AWS change was attempted.")
    action = {"scale_out": "scale_up", "scale_in": "scale_down"}.get(raw_action, raw_action)
    desired = int(raw.get("desired_instances", current))
    reason = str(raw.get("reason", "Q-learning policy decision"))

    if action == "scale_up" and (current >= maximum or not current < desired <= maximum):
        reason += f" Requested scale-up was held at the configured maximum/bounds {minimum}-{maximum}."
        action, desired = "maintain", current
    elif action == "scale_down" and (current <= minimum or not minimum <= desired < current):
        reason += f" Requested scale-down was held at the configured minimum/bounds {minimum}-{maximum}."
        action, desired = "maintain", current
    elif action == "maintain":
        desired = current

    aws_applied = False
    aws_result = "AWS ASG execution bypassed (apply_to_aws=False)." if not apply_to_aws else "No capacity change requested by policy."

    if apply_to_aws and action in {"scale_up", "scale_down"}:
        if live_preflight:
            action_preflight = aws_client.preflight(requested_action=action)
            if not action_preflight.get("ready"):
                action = "maintain"
                desired = current
                aws_result = "Action preflight failed; no AWS mutation attempted."
            elif _recent_applied_decision(db) is not None:
                action = "maintain"
                desired = current
                aws_result = f"Scaling cooldown active ({settings.AWS_SCALING_COOLDOWN_SECONDS}s); no AWS mutation attempted."
            else:
                aws_result = "Mutation pending; if request outcome is uncertain, inspect AWS before retrying."
        if action in {"scale_up", "scale_down"}:
            # Commit the decision intent before the external side effect. An
            # ambiguous timeout must never be silently retried by the replay path.
            decision = ScalingDecision(
                action=action,
                current_instances=current,
                desired_instances=desired,
                reason=reason,
                confidence=float(raw.get("confidence", 0.0)),
                triggered_by=raw.get("triggered_by", "q_learning_local"),
                telemetry_source=telemetry_source,
                event_id=event_id,
                aws_applied=False,
                aws_result=aws_result,
                data_provenance=_serialize_provenance(provenance),
            )
            db.add(decision)
            db.commit()
            db.refresh(decision)
            result = aws_client.set_desired_capacity(desired, expected_action=action)
            aws_applied = bool(result.get("success"))
            aws_result = str(result.get("message", "AWS mutation returned no message."))
            decision.aws_applied = aws_applied
            decision.aws_result = aws_result
            db.commit()
            db.refresh(decision)
            logger.info("scaling mutation action=%s source=%s event_id=%s current=%s desired=%s accepted=%s result=%s", action, telemetry_source, event_id, current, desired, aws_applied, result.get("error_code", "completed"))
            return {"decision": decision, "aws_applied": aws_applied, "aws_message": aws_result, "db_logged": True}

    decision = ScalingDecision(
        action=action,
        current_instances=current,
        desired_instances=desired,
        reason=reason,
        confidence=float(raw.get("confidence", 0.0)),
        triggered_by=raw.get("triggered_by", "q_learning_local"),
        telemetry_source=telemetry_source,
        event_id=event_id,
        aws_applied=False,
        aws_result=aws_result,
        data_provenance=_serialize_provenance(provenance),
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    logger.info("scaling decision action=%s source=%s event_id=%s current=%s desired=%s apply_requested=%s aws_applied=false", action, telemetry_source, event_id, current, desired, apply_to_aws)
    return {"decision": decision, "aws_applied": False, "aws_message": aws_result, "db_logged": True}
