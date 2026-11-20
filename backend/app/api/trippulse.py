"""TripPulse AI API Endpoints — Monitoring, Disruption Simulation, and Re-Optimization."""
from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.trippulse_service import (
    apply_reoptimization,
    dismiss_alert,
    get_trip_pulse,
    rollback_reoptimization,
    simulate_disruption,
    trigger_reoptimization,
)

router = APIRouter(prefix="/trips", tags=["trippulse"])


class SimulatePayload(BaseModel):
    simulation_type: str = "heavy_rain"
    affected_day: int = 2
    severity: str = "red"
    custom_title: str | None = None


class ApplyPayload(BaseModel):
    accepted_modification_ids: list[str] | None = None


@router.get("/{trip_id}/pulse")
def get_pulse_endpoint(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves real-time TripPulse health score (0-100), active alerts, weather, and budget health."""
    return get_trip_pulse(db, trip_id, user.id)


@router.post("/{trip_id}/pulse/simulate")
def post_simulate_disruption_endpoint(
    trip_id: int,
    payload: SimulatePayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Simulates a travel disruption (heavy rainfall, activity cancellation, transport delay, budget overrun).

    Generates AI re-optimization proposals with verified alternatives without modifying the active plan.
    """
    return simulate_disruption(
        db,
        trip_id=trip_id,
        user_id=user.id,
        simulation_type=payload.simulation_type,
        affected_day=payload.affected_day,
        severity=payload.severity,
        custom_title=payload.custom_title,
    )


@router.post("/{trip_id}/pulse/reoptimize")
def post_trigger_reoptimization_endpoint(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generates an adaptive AI itinerary re-optimization based on active real disruptions."""
    return trigger_reoptimization(db, trip_id, user.id)


@router.post("/{trip_id}/pulse/reoptimize/{reopt_id}/apply")
def post_apply_reoptimization_endpoint(
    trip_id: int,
    reopt_id: int,
    payload: ApplyPayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Applies a re-optimization proposal (either all modifications or user-selected subset).

    Requires explicit user approval. Preserves previous itinerary version for rollback.
    """
    return apply_reoptimization(
        db,
        trip_id=trip_id,
        reopt_id=reopt_id,
        user_id=user.id,
        accepted_mod_ids=payload.accepted_modification_ids,
    )


@router.post("/{trip_id}/pulse/reoptimize/{reopt_id}/rollback")
def post_rollback_reoptimization_endpoint(
    trip_id: int,
    reopt_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rolls back an applied re-optimization, restoring the previous original itinerary."""
    return rollback_reoptimization(db, trip_id, reopt_id, user.id)


@router.post("/{trip_id}/pulse/alerts/{alert_id}/dismiss")
def post_dismiss_alert_endpoint(
    trip_id: int,
    alert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dismisses an alert for a trip owned by the user."""
    return dismiss_alert(db, trip_id, alert_id, user.id)
