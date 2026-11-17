"""Trip Alert and Monitoring Log models for TripPulse AI."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TripAlert(Base):
    __tablename__ = "trip_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)

    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="yellow", nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    relevant_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    simulation_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    trip: Mapped["Trip"] = relationship(back_populates="alerts")  # noqa: F821


class TripMonitoringLog(Base):
    __tablename__ = "trip_monitoring_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)

    overall_health: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    health_status: Mapped[str] = mapped_column(String(20), default="green", nullable=False)
    weather_status: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    budget_status: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    disruptions_detected: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    recommendations_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    trip: Mapped["Trip"] = relationship(back_populates="monitoring_logs")  # noqa: F821
