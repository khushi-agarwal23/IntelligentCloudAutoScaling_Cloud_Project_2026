import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from ..models.workload import WorkloadMetric
from ..schemas.telemetry import WorkloadMetricCreate

logger = logging.getLogger("backend.services.workload")


def record_metric(db: Session, metric_in: WorkloadMetricCreate) -> WorkloadMetric:
    """Stores a single telemetry metric reading into Amazon RDS."""
    metric = WorkloadMetric(
        cpu_percent=metric_in.cpu_percent,
        memory_percent=metric_in.memory_percent,
        request_rate=metric_in.request_rate,
        response_time_ms=metric_in.response_time_ms,
        instance_count=metric_in.instance_count,
        error_rate=metric_in.error_rate
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def batch_record_metrics(db: Session, metrics_in: List[WorkloadMetricCreate]) -> int:
    """Bulk records multiple telemetry metrics into the database."""
    models = [
        WorkloadMetric(
            cpu_percent=m.cpu_percent,
            memory_percent=m.memory_percent,
            request_rate=m.request_rate,
            response_time_ms=m.response_time_ms,
            instance_count=m.instance_count,
            error_rate=m.error_rate
        )
        for m in metrics_in
    ]
    db.add_all(models)
    db.commit()
    return len(models)


def get_latest_metric(db: Session) -> Optional[WorkloadMetric]:
    """Retrieves the most recently recorded telemetry metric."""
    stmt = select(WorkloadMetric).order_by(desc(WorkloadMetric.timestamp)).limit(1)
    return db.scalar(stmt)


def get_recent_metrics(db: Session, limit: int = 50) -> List[WorkloadMetric]:
    """Retrieves the recent telemetry metrics history."""
    stmt = select(WorkloadMetric).order_by(desc(WorkloadMetric.timestamp)).limit(limit)
    return list(db.scalars(stmt).all())


def compute_workload_state(db: Session, window: int = 5) -> Dict[str, Any]:
    """
    Computes a smoothed moving-window state vector over recent telemetry readings
    to feed into the RL policy, preventing sudden oscillating scaling decisions.
    """
    metrics = get_recent_metrics(db, limit=window)
    if not metrics:
        return {
            "cpu_percent": 15.0,
            "memory_percent": 25.0,
            "request_rate": 10.0,
            "response_time_ms": 120.0,
            "instance_count": 1,
            "error_rate": 0.0
        }

    n = len(metrics)
    avg_cpu = sum(m.cpu_percent for m in metrics) / n
    avg_mem = sum(m.memory_percent for m in metrics) / n
    avg_req = sum(m.request_rate for m in metrics) / n
    avg_resp = sum(m.response_time_ms for m in metrics) / n
    avg_err = sum(m.error_rate for m in metrics) / n
    current_inst = metrics[0].instance_count

    return {
        "cpu_percent": round(avg_cpu, 2),
        "memory_percent": round(avg_mem, 2),
        "request_rate": round(avg_req, 2),
        "response_time_ms": round(avg_resp, 2),
        "instance_count": current_inst,
        "error_rate": round(avg_err, 2)
    }
