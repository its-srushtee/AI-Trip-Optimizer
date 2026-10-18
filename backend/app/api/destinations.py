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
from app.services.destination_service import list_destinations, recommend_destinations
from app.services.image_service import resolve as resolve_image
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


@router.get("")
def get_destinations(db: Session = Depends(get_db)):
    return list_destinations(db)


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
    )


@router.get("/image")
def get_destination_image(
    q: str = Query(..., min_length=1, max_length=120, description="Destination name"),
    remote: bool = Query(True, description="Allow an outbound provider lookup"),
    db: Session = Depends(get_db),
):
    """Resolve a destination name to a photo URL + its required credit."""
    return resolve_image(db, q, allow_remote=remote)


# Pexels requires a "prominent link to Pexels" wherever their API is used, and
# Unsplash requires the app to attribute Unsplash itself. This tells the UI
# which providers have actually supplied an image, so the site-level credit
# only names the ones in use.
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
