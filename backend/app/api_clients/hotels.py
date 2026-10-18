"""Hotels client — Amadeus Hotel Search (requires API key + secret).

Set AMADEUS_API_KEY and AMADEUS_API_SECRET to enable. Returns [] otherwise.
"""
from functools import lru_cache

import httpx

from app.api_clients.base import BaseApiClient
from app.core.config import settings

TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
HOTEL_URL = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"


class HotelsClient(BaseApiClient):
    def __init__(self, key: str, secret: str):
        super().__init__(key=key)
        self._secret = secret

    def is_configured(self) -> bool:
        return bool(self._key and self._secret)

    def _access_token(self) -> str | None:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                r = client.post(
                    TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self._key,
                        "client_secret": self._secret,
                    },
                )
                r.raise_for_status()
                return r.json().get("access_token")
        except httpx.HTTPError:
            return None

    def search_hotels(
        self, city: str, check_in: str, check_out: str, budget: int, travelers: int
    ) -> list[dict]:
        if not self.is_configured():
            return []
        token = self._access_token()
        if not token:
            return []
        try:
            with httpx.Client(timeout=self._timeout) as client:
                r = client.get(
                    HOTEL_URL,
                    params={"cityCode": city, "radius": 10, "radiusUnit": "KM"},
                    headers={"Authorization": f"Bearer {token}"},
                )
                r.raise_for_status()
                return [
                    {"name": h.get("name"), "geo_code": h.get("geoCode")}
                    for h in r.json().get("data", [])[:10]
                ]
        except httpx.HTTPError:
            return []


@lru_cache(maxsize=1)
def get_hotels_client() -> HotelsClient:
    return HotelsClient(key=settings.AMADEUS_API_KEY, secret=settings.AMADEUS_API_SECRET)
