from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.telemetry import WorkloadMetricCreate, WorkloadMetricResponse, WorkloadBatchIngest
from ..services.workload_service import (
    record_metric,
    batch_record_metrics,
    get_latest_metric,
    get_recent_metrics,
    compute_workload_state,
)

router = APIRouter(prefix="/workload", tags=["Workload & Telemetry"])


@router.post("/metrics", response_model=WorkloadMetricResponse, status_code=status.HTTP_201_CREATED)
def ingest_workload_metric(metric_in: WorkloadMetricCreate, db: Session = Depends(get_db)):
    """
    Ingests real-time CloudWatch & ELB performance metrics:
    CPU utilization, memory usage, request count/rate, latency, error rate.
    """
    return record_metric(db, metric_in)


@router.post("/batch", status_code=status.HTTP_201_CREATED)
def batch_ingest_metrics(batch_in: WorkloadBatchIngest, db: Session = Depends(get_db)):
    """Bulk ingests historical or high-frequency telemetry samples."""
    count = batch_record_metrics(db, batch_in.metrics)
    return {"status": "success", "ingested_count": count}


@router.get("/latest", response_model=WorkloadMetricResponse)
def get_current_metric(db: Session = Depends(get_db)):
    """Retrieves the most recent telemetry metric."""
    metric = get_latest_metric(db)
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No telemetry metrics found")
    return metric


@router.get("/history", response_model=List[WorkloadMetricResponse])
def get_workload_history(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    """Returns historical workload metrics for time-series visualization."""
    return get_recent_metrics(db, limit=limit)


@router.get("/state")
def get_rl_state(db: Session = Depends(get_db)):
    """Returns the computed smoothed system state vector for the RL agent."""
    return compute_workload_state(db)
