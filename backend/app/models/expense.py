"""Trip Expense model for AI Budget Guardian."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TripExpense(Base):
    __tablename__ = "trip_expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    original_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    exchange_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    category: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    trip: Mapped["Trip"] = relationship(back_populates="expenses")  # noqa: F821
