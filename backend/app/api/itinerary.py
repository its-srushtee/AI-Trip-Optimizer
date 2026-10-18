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
    return {"itinerary": generate_itinerary(body)}
