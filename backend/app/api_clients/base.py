"""Minimal HTTP client shared by external API clients.

When no API key is configured the client is "disabled": calls return None
instead of raising, so agents degrade gracefully to placeholders.
"""
import httpx


class BaseApiClient:
    base_url: str = ""

    def __init__(self, key: str = "", timeout: float = 10.0):
        self._key = key
        self._timeout = timeout

    def is_configured(self) -> bool:
        return bool(self._key)

    def _get(self, path: str, params: dict | None = None, headers: dict | None = None):
        if not self.is_configured():
            return None
        try:
            with httpx.Client(timeout=self._timeout) as client:
                r = client.get(f"{self.base_url}{path}", params=params, headers=headers)
                r.raise_for_status()
                return r.json()
        except httpx.HTTPError:
            return None
