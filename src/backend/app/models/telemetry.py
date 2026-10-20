from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


def now_utc():
    return datetime.now(timezone.utc)


class TelemetrySnapshot(Base):
    """Immutable point-in-time source snapshot with explicit provenance."""
    __tablename__ = "telemetry_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True, nullable=False)
    telemetry_source: Mapped[str] = mapped_column(String(32), nullable=False)
    event_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    provenance_json: Mapped[str] = mapped_column(Text, nullable=False)


class ReplayReceipt(Base):
    """Durable idempotency record for at-least-once EventBridge deliveries."""
    __tablename__ = "workload_replay_receipts"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    replay_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="processing")
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)
