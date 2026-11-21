"""GET /destinations — catalogue used to power recommendations.

Also exposes the photo resolver, which turns a free-text destination name
("Kyoto", "North Goa") into a usable image URL. See image_service for the
lookup order.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db
from app.models.image_cache import ImageCache
from app.services.destination_preferences import get_destination_preferences
from app.services.destination_service import (
    list_destinations,
    recommend_destinations,
    search_destinations_dynamic,
)
from app.services.image_service import (
    invalidate_cached_image,
    resolve as resolve_image,
)
from pydantic import BaseModel

router = APIRouter(prefix="/destinations", tags=["destinations"])


class RecommendPayload(BaseModel):
    destination: str | None = None
    interests: list[str] = []
    budget: int | None = None
    travelers: int = 1
    start_date: str | None = None
    end_date: str | None = None
    special_requests: str | None = None
    style: str | None = None
    pace: str | None = None
    currency: str | None = None


@router.get("")
def get_destinations(db: Session = Depends(get_db)):
    return list_destinations(db)


@router.get("/autocomplete")
def get_destination_autocomplete(
    q: str = Query(..., min_length=1, max_length=120, description="Destination search query"),
    limit: int = Query(6, ge=1, le=20, description="Max results"),
    db: Session = Depends(get_db),
):
    """Dynamically autocompletes any global destination (city, town, region, island, country)."""
    return search_destinations_dynamic(db, query=q, limit=limit)


@router.get("/search")
def get_destination_search(
    q: str = Query(..., min_length=1, max_length=120, description="Destination search query"),
    limit: int = Query(10, ge=1, le=30, description="Max results"),
    db: Session = Depends(get_db),
):
    """Dynamic destination search with live geocoding, coordinates, and photo preview."""
    return search_destinations_dynamic(db, query=q, limit=limit)


@router.post("/recommend")
def post_recommendations(payload: RecommendPayload, db: Session = Depends(get_db)):
    """Personalized destination recommendations tailored to preferences, budget, duration, and search."""
    return recommend_destinations(
        db,
        interests=payload.interests,
        destination_query=payload.destination,
        budget=payload.budget,
        travelers=payload.travelers,
        start_date=payload.start_date,
        end_date=payload.end_date,
        special_requests=payload.special_requests,
        style=payload.style,
        pace=payload.pace,
        currency=payload.currency,
    )


class DestinationPreferencesPayload(BaseModel):
    destination: str


@router.get("/preferences")
def get_destination_preferences_endpoint(
    destination: str = Query(..., min_length=1, max_length=120, description="Destination name to analyze"),
):
    """Dynamically analyzes destination and returns supported travel preference categories."""
    return get_destination_preferences(destination)


@router.post("/preferences")
def post_destination_preferences_endpoint(payload: DestinationPreferencesPayload):
    """Dynamically analyzes destination and returns supported travel preference categories."""
    return get_destination_preferences(payload.destination)


class InvalidateImagePayload(BaseModel):
    query: str


@router.get("/image")
def get_destination_image(
    q: str = Query(..., min_length=1, max_length=120, description="Destination name"),
    remote: bool = Query(True, description="Allow an outbound provider lookup"),
    refresh: bool = Query(False, description="Force refresh from provider"),
    db: Session = Depends(get_db),
):
    """Resolve a destination name to a photo URL + its required credit."""
    return resolve_image(db, q, allow_remote=remote, force_refresh=refresh)


@router.post("/image/invalidate")
def invalidate_image(
    payload: InvalidateImagePayload,
    db: Session = Depends(get_db),
):
    """Invalidates or refreshes a specific destination image cache record without affecting other valid records."""
    return invalidate_cached_image(db, payload.query)


_PROVIDER_META = {
    "unsplash": {"name": "Unsplash",
                 "url": "https://unsplash.com?utm_source=trip_optimizer&utm_medium=referral"},
    "pexels": {"name": "Pexels", "url": "https://www.pexels.com"},
    "openverse": {"name": "Openverse", "url": "https://openverse.org"},
}


@router.get("/image-providers")
def get_image_providers(db: Session = Depends(get_db)):
    """Providers that have actually supplied at least one cached photo."""
    used = {p for (p,) in db.query(ImageCache.provider).distinct() if p}
    return [_PROVIDER_META[p] for p in ("unsplash", "pexels", "openverse") if p in used]


@router.get("/image-config")
def get_image_config():
    """Which photo providers are usable. Never returns the keys themselves."""
    pexels = bool(settings.PEXELS_API_KEY)
    unsplash = bool(settings.UNSPLASH_ACCESS_KEY)
    return {
        "order": ["pexels", "unsplash", "openverse"],
        "pexels": {"configured": pexels, "key_len": len(settings.PEXELS_API_KEY)},
        "unsplash": {"configured": unsplash, "key_len": len(settings.UNSPLASH_ACCESS_KEY)},
        "openverse": {"configured": True, "note": "no key required"},
        "active": "pexels" if pexels else ("unsplash" if unsplash else "openverse"),
    }
