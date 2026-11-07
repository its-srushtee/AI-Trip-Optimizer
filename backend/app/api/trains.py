"""Train API router — station autocomplete and trains search via RailCore."""
from fastapi import APIRouter, Query

from app.api_clients.railcore import railcore_client

router = APIRouter(prefix="/trains", tags=["trains"])


@router.get("/stations")
def search_stations(query: str = Query(default="", description="Station code or city name")):
    """Searches Indian Railways stations by code or city."""
    stations = railcore_client.search_stations(query)
    return {"stations": stations}


@router.get("/search")
def search_trains(
    from_station: str = Query(..., description="Origin station code or city"),
    to_station: str = Query(..., description="Destination station code or city"),
    date: str = Query(..., description="Journey date YYYY-MM-DD"),
    currency: str = Query(default="INR", description="Preferred fare currency"),
):
    """Searches trains between two stations on a journey date with fare conversion."""
    trains = railcore_client.search_trains(
        from_station=from_station,
        to_station=to_station,
        date_str=date,
        currency=currency,
    )
    message = None
    if not trains:
        message = f"No direct train route found between {from_station} and {to_station}. RailCore covers domestic Indian Railway (IRCTC) stations."

    return {
        "from_station": from_station,
        "to_station": to_station,
        "date": date,
        "currency": currency,
        "trains": trains,
        "message": message,
    }

