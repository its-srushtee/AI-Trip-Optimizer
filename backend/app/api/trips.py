"""GET /trips, POST /trips, DELETE /trips/{id}"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.trip import TripCreate, TripOut, TripUpdate
from app.services.trip_service import (
    create_trip,
    delete_trip,
    get_trip,
    list_trips,
    update_trip,
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

