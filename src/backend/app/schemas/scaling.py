from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ScalingDecisionRequest(BaseModel):
    cpu_percent: float = Field(..., ge=0, le=100)
    memory_percent: float = Field(..., ge=0, le=100)
    request_rate: float = Field(..., ge=0)
    response_time_ms: float = Field(..., ge=0)
    instance_count: int = Field(1, ge=1)
    error_rate: float = Field(0.0, ge=0, le=100)


class ScalingDecisionResponse(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    action: str = Field(..., description="'scale_up', 'scale_down', or 'maintain'")
    current_instances: int
    desired_instances: int
    reason: str
    confidence: float
    triggered_by: str = "rl_agent"

    model_config = {"from_attributes": True}


class EvaluateAndActRequest(BaseModel):
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    request_rate: Optional[float] = None
    response_time_ms: Optional[float] = None
    current_instances: Optional[int] = None
    apply_to_aws: bool = Field(True, description="Whether to invoke AWS ASG client")


class EvaluateAndActResponse(BaseModel):
    decision: ScalingDecisionResponse
    aws_applied: bool
    aws_message: str
    db_logged: bool


class FeedbackRequest(BaseModel):
    decision_id: int
    observed_response_time_ms: float = Field(..., ge=0)
    observed_cpu_percent: float = Field(..., ge=0, le=100)
    reward: Optional[float] = None
