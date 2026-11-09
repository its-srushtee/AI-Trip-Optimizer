"""Weather client — OpenWeatherMap current weather + 5-day forecast.

Set OPENWEATHERMAP_API_KEY to enable. Returns None when not configured.
"""
from functools import lru_cache

from app.api_clients.base import BaseApiClient
from app.core.config import settings


class WeatherClient(BaseApiClient):
    base_url = "https://api.openweathermap.org/data/2.5/forecast"

    def forecast(
        self,
        city: str,
        lat: float | None = None,
        lon: float | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> dict | None:
        if not self.is_configured():
            return None
        params: dict = {"units": "metric", "appid": self._key}
        if lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        elif city:
            params["q"] = city
        else:
            return None

        data = self._get("", params=params)
        if not data or "list" not in data:
            return None
        items = [
            {
                "dt": it.get("dt_txt"),
                "temp_c": round(it.get("main", {}).get("temp", 0)),
                "feels_like_c": round(it.get("main", {}).get("feels_like", 0)),
                "humidity": it.get("main", {}).get("humidity"),
                "description": (it.get("weather", [{}])[0].get("description") or "").capitalize(),
                "icon": it.get("weather", [{}])[0].get("icon"),
            }
            for it in data.get("list", [])[:10]
        ]
        return {
            "city": data.get("city", {}).get("name") or city,
            "country": data.get("city", {}).get("country"),
            "forecast": items,
        }


@lru_cache(maxsize=1)
def get_weather_client() -> WeatherClient:
    return WeatherClient(key=settings.OPENWEATHERMAP_API_KEY)

