"""POST /trips/optimize — generate a day-by-day itinerary via the agent workflow."""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.itinerary import OptimizeRequest, OptimizeResponse
from app.services.itinerary_service import generate_itinerary

router = APIRouter(prefix="/trips", tags=["itinerary"])


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(
    body: OptimizeRequest,
    user: User = Depends(get_current_user),
):
    user_prefs = user.preferences or {}
    req_prefs = dict(body.preferences or {})

    # Priority: explicit top-level body field > body.preferences > user.preferences
    style = body.style or req_prefs.get("style") or user_prefs.get("style")
    pace = body.pace or req_prefs.get("pace") or user_prefs.get("pace")
    accommodation = (
        body.accommodation
        or req_prefs.get("accommodation")
        or user_prefs.get("accommodation")
    )
    food = body.food or req_prefs.get("food") or user_prefs.get("food")
    currency = (
        body.currency
        or req_prefs.get("currency")
        or user_prefs.get("currency")
        or "USD"
    )
    origin = body.origin or req_prefs.get("origin") or user_prefs.get("origin")
    special_requests = (
        body.special_requests
        or req_prefs.get("special_requests")
        or user_prefs.get("special_requests")
    )
    accessibility = (
        body.accessibility
        or req_prefs.get("accessibility")
        or user_prefs.get("accessibility")
    )
    interests = (
        body.interests
        or req_prefs.get("interests")
        or user_prefs.get("interests")
        or []
    )

    body.style = style
    body.pace = pace
    body.accommodation = accommodation
    body.food = food
    body.currency = currency
    body.origin = origin
    body.special_requests = special_requests
    body.accessibility = accessibility
    body.interests = interests
    body.preferences = {
        "style": style,
        "pace": pace,
        "accommodation": accommodation,
        "food": food,
        "currency": currency,
        "origin": origin,
        "special_requests": special_requests,
        "accessibility": accessibility,
        "interests": interests,
    }

    return {"itinerary": generate_itinerary(body)}
