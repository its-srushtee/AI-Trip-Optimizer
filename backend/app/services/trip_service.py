"""Trip CRUD business logic."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.schemas.trip import TripCreate, TripUpdate


def list_trips(db: Session, user_id: int) -> list[Trip]:
    return (
        db.query(Trip)
        .filter(Trip.user_id == user_id)
        .order_by(Trip.created_at.desc())
        .all()
    )


def get_trip(db: Session, user_id: int, trip_id: int) -> Trip:
    trip = db.get(Trip, trip_id)
    if not trip or trip.user_id != user_id:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


def create_trip(db: Session, user_id: int, body: TripCreate) -> Trip:
    if body.end_date <= body.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    data = body.model_dump()
    currency = data.pop("currency", None)
    prefs = dict(data.get("preferences") or {})
    if currency:
        prefs["currency"] = str(currency).upper()
    data["preferences"] = prefs

    trip = Trip(user_id=user_id, **data)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def update_trip(db: Session, user_id: int, trip_id: int, body: TripUpdate) -> Trip:
    trip = get_trip(db, user_id, trip_id)
    data = body.model_dump(exclude_unset=True)

    new_start = data.get("start_date", trip.start_date)
    new_end = data.get("end_date", trip.end_date)
    if new_end <= new_start:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    currency = data.pop("currency", None)
    if currency:
        curr_prefs = dict(trip.preferences or {})
        curr_prefs["currency"] = str(currency).upper()
        trip.preferences = curr_prefs

    for field, val in data.items():
        setattr(trip, field, val)

    db.commit()
    db.refresh(trip)
    return trip


def delete_trip(db: Session, user_id: int, trip_id: int) -> None:
    trip = db.get(Trip, trip_id)
    if not trip or trip.user_id != user_id:
        raise HTTPException(status_code=404, detail="Trip not found")
    db.delete(trip)
    db.commit()

