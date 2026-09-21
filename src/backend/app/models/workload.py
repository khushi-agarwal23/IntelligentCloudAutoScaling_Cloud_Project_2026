from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


def now_utc():
    return datetime.now(timezone.utc)


class WorkloadMetric(Base):
    __tablename__ = "workload_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True, nullable=False)
    cpu_percent: Mapped[float] = mapped_column(Float, nullable=False)
    memory_percent: Mapped[float] = mapped_column(Float, nullable=False)
    request_rate: Mapped[float] = mapped_column(Float, nullable=False)  # requests per second
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)  # average latency in ms
    instance_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    error_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # percentage 0-100
