import logging
import json
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from ..database import get_db
from ..models.scaling import ScalingDecision
from ..models.telemetry import TelemetrySnapshot
from ..schemas.scaling import (
    ScalingDecisionRequest,
    ScalingDecisionResponse,
    EvaluateAndActRequest,
    EvaluateAndActResponse,
    FeedbackRequest,
)
from ..services.ai_client import send_rl_feedback
from ..services.aws_asg_client import aws_client
from ..services.workload_service import compute_workload_state
from ..services.scaling_controller import evaluate_and_apply
from ..services.cloudwatch_telemetry import cloudwatch_telemetry, TelemetryUnavailable
from ..config import settings

router = APIRouter(prefix="/scaling", tags=["AI/RL Auto-Scaling"])
logger = logging.getLogger("backend.routers.scaling")


@router.get("/aws/preflight")
def aws_read_only_preflight(
    requested_action: str = Query("maintain", pattern="^(maintain|scale_up|scale_down)$"),
):
    """Read-only AWS identity, ASG configuration, capacity and health check."""
    runtime = {
        "process_id": os.getpid(),
        "configured_mock_mode": settings.AWS_MOCK_MODE,
        "client_mock_mode": aws_client.mock_mode,
    }
    if bool(settings.AWS_MOCK_MODE) != bool(aws_client.mock_mode):
        logger.error("AWS mode mismatch between settings and initialized client: %s", runtime)
        return {
            "mode": "configuration_error",
            "ready": False,
            "identity": {"verified": False},
            "target": {"region": settings.AWS_REGION, "auto_scaling_group": settings.AWS_ASG_NAME},
            "capacity": {"requested_action": requested_action, "action_allowed": False},
            "health": {"all_healthy": False, "simulated": False},
            "in_progress_activities": [],
            "permissions": {"read_only_preflight": "not attempted due to configuration mismatch"},
            "errors": ["AWSModeConfigurationMismatch"],
            "runtime": runtime,
        }
    result = aws_client.preflight(requested_action=requested_action)
    result["runtime"] = runtime
    return result


@router.post("/decision", response_model=ScalingDecisionResponse)
def evaluate_scaling_decision(req: ScalingDecisionRequest, db: Session = Depends(get_db)):
    """
    Simulates or validates an RL agent policy decision given workload metrics,
    logging the decision in Amazon RDS without directly altering cloud infrastructure.
    """
    state = req.model_dump()
    return evaluate_and_apply(
        db, state, telemetry_source="manual_simulated",
        provenance={"source": "api_request", "simulated": True},
        apply_to_aws=False,
    )["decision"]


@router.post("/evaluate-and-act", response_model=EvaluateAndActResponse)
def evaluate_and_act(req: EvaluateAndActRequest, db: Session = Depends(get_db)):
    """
    Evaluate provided simulated metrics or recorded workload data. AWS-backed
    decisions must use the dedicated CloudWatch endpoint.
    """
    if req.cpu_percent is not None:
        state = {
            "cpu_percent": req.cpu_percent,
            "memory_percent": req.memory_percent,
            "request_rate": req.request_rate,
            "response_time_ms": req.response_time_ms,
            "instance_count": req.current_instances or settings.AWS_EXPECTED_MIN_SIZE,
            "error_rate": 0.0,
        }
        source, provenance = "manual_simulated", {"source": "api_request", "simulated": True}
    else:
        state = compute_workload_state(db)
        source, provenance = state.pop("telemetry_source", "manual_simulated"), state.pop("data_provenance", {"simulated": True})
        state["instance_count"] = req.current_instances or state["instance_count"]
    return evaluate_and_apply(db, state, telemetry_source=source, provenance=provenance, apply_to_aws=req.apply_to_aws)


@router.post("/evaluate-cloudwatch", response_model=EvaluateAndActResponse)
def evaluate_cloudwatch(req: EvaluateAndActRequest, db: Session = Depends(get_db)):
    """Collect fresh AWS telemetry, persist its provenance, then evaluate the existing Q policy."""
    try:
        collected = cloudwatch_telemetry.collect()
    except TelemetryUnavailable as exc:
        detail = {"code": exc.code, "message": str(exc), "aws_mutation_attempted": False}
        if exc.diagnostics:
            detail["diagnostics"] = exc.diagnostics
        raise HTTPException(status_code=503, detail=detail) from exc
    metrics, provenance = collected["metrics"], collected["provenance"]
    snapshot = TelemetrySnapshot(
        telemetry_source="aws_cloudwatch",
        metrics_json=json.dumps(metrics, separators=(",", ":"), sort_keys=True),
        provenance_json=json.dumps(provenance, separators=(",", ":"), sort_keys=True),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    result = evaluate_and_apply(
        db,
        {"cpu_percent": metrics["cpu_percent"], "memory_percent": metrics["memory_percent"],
         "request_rate": metrics["request_rate"], "response_time_ms": metrics["response_time_ms"],
         "instance_count": metrics["current_instances"], "error_rate": metrics["error_rate"]},
        telemetry_source="aws_cloudwatch", provenance=provenance,
        apply_to_aws=req.apply_to_aws,
    )
    result["telemetry_snapshot_id"] = snapshot.id
    return result


@router.post("/feedback")
def log_scaling_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Ingests post-scaling observed latency and CPU utilization to calculate
    and update RL reward functions for experience replay.
    """
    decision = db.get(ScalingDecision, req.decision_id)
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found")

    feedback_res = send_rl_feedback(
        decision_id=req.decision_id,
        observed_response_time_ms=req.observed_response_time_ms,
        observed_cpu_percent=req.observed_cpu_percent,
        reward=req.reward
    )

    decision.feedback_reward = feedback_res["reward"]
    db.commit()

    return {
        "status": "success",
        "decision_id": req.decision_id,
        "calculated_reward": feedback_res["reward"],
        "message": "Feedback successfully logged and reward assigned."
    }


@router.get("/history", response_model=List[ScalingDecisionResponse])
def get_scaling_history(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    """Retrieves past scaling decisions audit log."""
    stmt = select(ScalingDecision).order_by(desc(ScalingDecision.timestamp)).limit(limit)
    return list(db.scalars(stmt).all())
