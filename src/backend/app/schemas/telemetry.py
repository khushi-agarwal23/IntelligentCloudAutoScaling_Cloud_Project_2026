from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class WorkloadMetricCreate(BaseModel):
    cpu_percent: float = Field(..., ge=0, le=100)
    memory_percent: float = Field(..., ge=0, le=100)
    request_rate: float = Field(..., ge=0)
    response_time_ms: float = Field(..., ge=0)
    instance_count: int = Field(1, ge=1)
    error_rate: float = Field(0.0, ge=0, le=100)
    # Dataset-relative time is provenance only; persisted timestamp remains
    # the server's ingestion time and must not be replaced by trace time.
    source_timestamp_seconds: Optional[int] = Field(None, ge=0)


class WorkloadMetricResponse(BaseModel):
    id: int
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    request_rate: float
    response_time_ms: float
    instance_count: int
    error_rate: float
    telemetry_source: str = "manual_simulated"
    source_event_id: Optional[str] = None
    data_provenance: Optional[str] = None

    model_config = {"from_attributes": True}


class WorkloadBatchIngest(BaseModel):
    metrics: List[WorkloadMetricCreate]


class ReplayEventRequest(BaseModel):
    event_type: str = Field(..., pattern="^(metric|completed)$")
    event_id: str = Field(..., min_length=1, max_length=128)
    replay_id: str = Field(..., min_length=1, max_length=128)
    sequence: Optional[int] = Field(None, ge=0)
    metric: Optional[WorkloadMetricCreate] = None
    apply_to_aws: bool = False
    data_provenance: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_event_shape(self):
        if self.event_type == "metric" and self.metric is None:
            raise ValueError("metric event requires metric payload")
        if self.event_type == "completed" and self.metric is not None:
            raise ValueError("completion event must not include metric payload")
        if self.event_type == "metric" and self.sequence is None:
            raise ValueError("metric event requires sequence number")
        return self
