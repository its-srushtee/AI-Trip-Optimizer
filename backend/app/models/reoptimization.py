"""Trip Reoptimization model for TripPulse AI Itinerary Re-Optimization."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TripReoptimization(Base):
    __tablename__ = "trip_reoptimizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    trigger_reason: Mapped[str] = mapped_column(String(100), nullable=False)
    original_itinerary: Mapped[dict] = mapped_column(JSON, nullable=False)
    proposed_itinerary: Mapped[dict] = mapped_column(JSON, nullable=False)
    diff_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    applied_changes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    trip: Mapped["Trip"] = relationship(back_populates="reoptimizations")  # noqa: F821
