from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


def now_utc():
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    product: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="credit_card", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="completed", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, index=True, nullable=False)

    user = relationship("User", back_populates="transactions")
