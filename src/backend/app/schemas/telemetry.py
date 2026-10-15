from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WorkloadMetricCreate(BaseModel):
    cpu_percent: float = Field(..., ge=0, le=100, description="Average CPU utilization percentage")
    memory_percent: float = Field(..., ge=0, le=100, description="Memory utilization percentage")
    request_rate: float = Field(..., ge=0, description="Incoming requests per second")
    response_time_ms: float = Field(..., ge=0, description="Average response latency in milliseconds")
    instance_count: int = Field(1, ge=1, description="Current number of active server instances")
    error_rate: float = Field(0.0, ge=0, le=100, description="Error rate percentage")


class WorkloadMetricResponse(BaseModel):
    id: int
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    request_rate: float
    response_time_ms: float
    instance_count: int
    error_rate: float

    model_config = {"from_attributes": True}


class WorkloadBatchIngest(BaseModel):
    metrics: List[WorkloadMetricCreate]
