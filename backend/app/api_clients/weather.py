"""Weather client — OpenWeatherMap current weather + 5-day forecast.

Set OPENWEATHERMAP_API_KEY to enable. Returns None when not configured.
"""
from functools import lru_cache

from app.api_clients.base import BaseApiClient
from app.core.config import settings


class WeatherClient(BaseApiClient):
    base_url = "https://api.openweathermap.org/data/2.5/forecast"

    def forecast(self, city: str, start: str | None = None, end: str | None = None) -> dict | None:
        if not self.is_configured():
            return None
        data = self._get("", params={"q": city, "units": "metric", "appid": self._key})
        if not data or "list" not in data:
            return None
        items = [
            {
                "dt": it.get("dt_txt"),
                "temp_c": round(it.get("main", {}).get("temp", 0)),
                "description": it.get("weather", [{}])[0].get("description"),
            }
            for it in data["list"][:10]
        ]
        return {"city": data.get("city", {}).get("name"), "forecast": items}


@lru_cache(maxsize=1)
def get_weather_client() -> WeatherClient:
    return WeatherClient(key=settings.OPENWEATHERMAP_API_KEY)
