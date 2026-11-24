"""GET /trips, POST /trips, DELETE /trips/{id}, plus alternatives, explanations & simulation."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.trip import TripCreate, TripOut, TripUpdate
from app.services.alternative_recommendation_service import (
    find_alternative_attractions,
    replace_attraction_in_itinerary,
)
from app.services.explainability_service import extract_itinerary_explanations
from app.services.trip_service import (
    create_trip,
    delete_trip,
    get_trip,
    list_trips,
    update_trip,
)
from app.services.trip_simulation_service import (
    apply_trip_simulation,
    simulate_trip_changes,
)

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("", response_model=list[TripOut])
def get_trips(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_trips(db, user.id)


@router.get("/{trip_id}", response_model=TripOut)
def get_trip_detail(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_trip(db, user.id, trip_id)


@router.post("", response_model=TripOut, status_code=201)
def post_trip(
    body: TripCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_trip(db, user.id, body)


@router.patch("/{trip_id}", response_model=TripOut)
def patch_trip(
    trip_id: int,
    body: TripUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_trip(db, user.id, trip_id, body)


@router.put("/{trip_id}", response_model=TripOut)
def put_trip(
    trip_id: int,
    body: TripUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_trip(db, user.id, trip_id, body)


@router.delete("/{trip_id}", status_code=204)
def remove_trip(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_trip(db, user.id, trip_id)


class AlternativesRequest(BaseModel):
    attraction_id: str | None = None
    day_number: int | None = None
    time_slot: str | None = None
    attraction_name: str | None = None
    reason: str = "user_preference"
    max_budget: float | None = None
    weights: dict[str, float] | None = None
    limit: int = Field(default=5, ge=1, le=15)


class ReplaceAttractionRequest(BaseModel):
    attraction_id: str | None = None
    day_number: int | None = None
    time_slot: str | None = None
    replacement: dict[str, Any]
    reason: str = "user_selection"


class TripSimulationRequest(BaseModel):
    scenario: str
    params: dict[str, Any] = Field(default_factory=dict)


@router.post("/{trip_id}/alternatives")
def post_find_alternatives(
    trip_id: int,
    body: AlternativesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Discover and rank context-aware replacement attractions for a scheduled activity."""
    trip = get_trip(db, user.id, trip_id)
    return find_alternative_attractions(
        trip,
        attraction_id=body.attraction_id,
        day_number=body.day_number,
        time_slot=body.time_slot,
        attraction_name=body.attraction_name,
        reason=body.reason,
        max_budget=body.max_budget,
        weights=body.weights,
        limit=body.limit,
    )


@router.post("/{trip_id}/replace-attraction")
def post_replace_attraction(
    trip_id: int,
    body: ReplaceAttractionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Replace an itinerary attraction with a user-selected alternative."""
    return replace_attraction_in_itinerary(
        db,
        trip_id=trip_id,
        user_id=user.id,
        attraction_id=body.attraction_id,
        day_number=body.day_number,
        time_slot=body.time_slot,
        replacement=body.replacement,
        reason=body.reason,
    )


@router.get("/{trip_id}/itinerary-explanations")
def get_itinerary_explanations(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return structured, grounded recommendation explanations for every itinerary attraction."""
    trip = get_trip(db, user.id, trip_id)
    if not trip.itinerary or not trip.itinerary.get("days"):
        raise HTTPException(status_code=400, detail="Trip does not have a generated itinerary yet.")
    explanations = extract_itinerary_explanations(trip.itinerary)
    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "count": len(explanations),
        "explanations": explanations,
    }


@router.post("/{trip_id}/simulate")
def post_simulate_trip(
    trip_id: int,
    body: TripSimulationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run a non-destructive What-If simulation on the trip without mutating DB state."""
    trip = get_trip(db, user.id, trip_id)
    return simulate_trip_changes(trip, scenario=body.scenario, params=body.params)


@router.post("/{trip_id}/apply-simulation")
def post_apply_simulation(
    trip_id: int,
    body: TripSimulationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm and apply a What-If simulation to the trip in PostgreSQL."""
    return apply_trip_simulation(
        db,
        trip_id=trip_id,
        user_id=user.id,
        scenario=body.scenario,
        params=body.params,
    )


