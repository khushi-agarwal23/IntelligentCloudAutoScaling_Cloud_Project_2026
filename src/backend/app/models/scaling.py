from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


def now_utc():
    return datetime.now(timezone.utc)


class ScalingDecision(Base):
    __tablename__ = "scaling_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)  # "scale_up", "scale_down", "maintain"
    current_instances: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    desired_instances: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(50), default="rl_agent", nullable=False)
    feedback_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
