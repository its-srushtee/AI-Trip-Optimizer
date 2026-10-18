"""Places client — Google Places API (Text Search).

Set GOOGLE_PLACES_API_KEY to enable. Returns [] when not configured.
"""
from functools import lru_cache

from app.api_clients.base import BaseApiClient
from app.core.config import settings


class PlacesClient(BaseApiClient):
    base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    def search_places(self, city: str, interests: list[str] | None = None) -> list[dict]:
        if not self.is_configured():
            return []
        query = f"things to do in {city}"
        if interests:
            query += " " + " ".join(interests)
        data = self._get("", params={"query": query, "key": self._key})
        if not data or data.get("status") != "OK":
            return []
        return [
            {
                "name": r.get("name"),
                "rating": r.get("rating"),
                "address": r.get("formatted_address"),
            }
            for r in data.get("results", [])[:10]
        ]


@lru_cache(maxsize=1)
def get_places_client() -> PlacesClient:
    return PlacesClient(key=settings.GOOGLE_PLACES_API_KEY)
