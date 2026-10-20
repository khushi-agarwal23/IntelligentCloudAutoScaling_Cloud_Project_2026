from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, model_validator


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
    action: str = Field(..., description="scale_up, maintain, or scale_down")
    current_instances: int
    desired_instances: int
    reason: str
    confidence: float
    triggered_by: str = "rl_agent"
    telemetry_source: str = "manual_simulated"
    event_id: Optional[str] = None
    aws_applied: bool = False
    aws_result: Optional[str] = None
    data_provenance: Optional[str] = None

    model_config = {"from_attributes": True}


class EvaluateAndActRequest(BaseModel):
    cpu_percent: Optional[float] = Field(None, ge=0, le=100)
    memory_percent: Optional[float] = Field(None, ge=0, le=100)
    request_rate: Optional[float] = Field(None, ge=0)
    response_time_ms: Optional[float] = Field(None, ge=0)
    current_instances: Optional[int] = Field(None, ge=1)
    apply_to_aws: bool = Field(False, description="Explicit per-request AWS capacity opt-in; live mode also requires backend gates")

    @model_validator(mode="after")
    def require_complete_manual_metrics(self):
        metric_fields = (self.cpu_percent, self.memory_percent, self.request_rate, self.response_time_ms)
        if any(value is not None for value in metric_fields) and not all(value is not None for value in metric_fields):
            raise ValueError("Provide CPU, memory, request rate, and response time together, or omit all four to use recorded workload data.")
        return self


class EvaluateAndActResponse(BaseModel):
    decision: ScalingDecisionResponse
    aws_applied: bool
    aws_message: str
    db_logged: bool
    telemetry_snapshot_id: Optional[int] = None


class FeedbackRequest(BaseModel):
    decision_id: int
    observed_response_time_ms: float = Field(..., ge=0)
    observed_cpu_percent: float = Field(..., ge=0, le=100)
    reward: Optional[float] = None
