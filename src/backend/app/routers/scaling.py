from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from ..database import get_db
from ..models.scaling import ScalingDecision
from ..schemas.scaling import (
    ScalingDecisionRequest,
    ScalingDecisionResponse,
    EvaluateAndActRequest,
    EvaluateAndActResponse,
    FeedbackRequest,
)
from ..services.ai_client import query_rl_agent, send_rl_feedback
from ..services.aws_asg_client import aws_client
from ..services.workload_service import compute_workload_state

router = APIRouter(prefix="/scaling", tags=["AI/RL Auto-Scaling"])


@router.post("/decision", response_model=ScalingDecisionResponse)
def evaluate_scaling_decision(req: ScalingDecisionRequest, db: Session = Depends(get_db)):
    """
    Simulates or validates an RL agent policy decision given workload metrics,
    logging the decision in Amazon RDS without directly altering cloud infrastructure.
    """
    state = req.model_dump()
    raw_decision = query_rl_agent(state)

    decision = ScalingDecision(
        action=raw_decision.get("action", "maintain"),
        current_instances=raw_decision.get("current_instances", req.instance_count),
        desired_instances=raw_decision.get("desired_instances", req.instance_count),
        reason=raw_decision.get("reason", "RL policy evaluation"),
        confidence=raw_decision.get("confidence", 0.0),
        triggered_by=raw_decision.get("triggered_by", "rl_agent")
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@router.post("/evaluate-and-act", response_model=EvaluateAndActResponse)
def evaluate_and_act(req: EvaluateAndActRequest, db: Session = Depends(get_db)):
    """
    Core orchestrator:
    1. Collects live workload metrics (from request or smoothed DB telemetry).
    2. Sends state to the AI/RL model.
    3. Triggers AWS Auto Scaling Group capacity adjustments.
    4. Persists the scaling decision audit trail in Amazon RDS.
    """
    # 1. State compilation
    if req.cpu_percent is not None and req.memory_percent is not None:
        state = {
            "cpu_percent": req.cpu_percent,
            "memory_percent": req.memory_percent,
            "request_rate": req.request_rate or 0.0,
            "response_time_ms": req.response_time_ms or 0.0,
            "instance_count": req.current_instances or aws_client.get_current_capacity(),
            "error_rate": 0.0
        }
    else:
        state = compute_workload_state(db)
        if req.current_instances:
            state["instance_count"] = req.current_instances
        else:
            state["instance_count"] = aws_client.get_current_capacity()

    # 2. RL Model Decision
    raw_decision = query_rl_agent(state)
    action = raw_decision.get("action", "maintain")
    desired = int(raw_decision.get("desired_instances", state["instance_count"]))

    # 3. Apply to AWS ASG if action requires scaling and enabled
    aws_applied = False
    aws_msg = "No scaling required (maintain state)."

    if req.apply_to_aws and action in ["scale_up", "scale_down", "scale_out", "scale_in"]:
        aws_res = aws_client.set_desired_capacity(desired)
        aws_applied = aws_res.get("success", False)
        aws_msg = aws_res.get("message", "")
    elif not req.apply_to_aws:
        aws_msg = "AWS ASG execution bypassed (apply_to_aws=False)."

    # 4. Log in Amazon RDS
    decision = ScalingDecision(
        action=action,
        current_instances=state["instance_count"],
        desired_instances=desired,
        reason=raw_decision.get("reason", "RL orchestrator decision"),
        confidence=raw_decision.get("confidence", 0.0),
        triggered_by=raw_decision.get("triggered_by", "rl_agent")
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    return {
        "decision": decision,
        "aws_applied": aws_applied,
        "aws_message": aws_msg,
        "db_logged": True
    }


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
