"""Destination photo providers.

Three providers are tried in order of quality:

  1. Unsplash  - needs a free key. Best quality, and supports width params so
                 we can request a card-sized image instead of a 3MB original.
  2. Pexels    - needs a free key. Same idea, different catalogue.
  3. Openverse - NO KEY. Public-domain / Creative-Commons search. Always
                 available, so it guarantees the chain resolves something.

Each returns a normalised dict or None:

    {"url", "thumb_url", "credit", "credit_url", "license", "provider"}

Notes learned from probing the live APIs:
  * source.unsplash.com (the old keyless endpoint) is dead - returns 503.
  * Openverse's own /thumb/ proxy is unreliable (observed HTTP 424), and its
    `url` is the full original, often 2-3 MB. We therefore prefer providers
    that expose resized URLs, and treat Openverse as the safety net.
  * Openverse results are frequently CC-BY / CC-BY-SA, which *legally require
    attribution*. We always carry the credit string through to the UI.
"""
from __future__ import annotations

import httpx

_TIMEOUT = 8.0
_UA = {"User-Agent": "TripOptimizer/1.0 (student project)"}


def _get(url: str, params: dict, headers: dict | None = None):
    try:
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as c:
            r = c.get(url, params=params, headers={**_UA, **(headers or {})})
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


APP_NAME = "trip_optimizer"
_UTM = f"?utm_source={APP_NAME}&utm_medium=referral"


def from_unsplash(query: str, key: str):
    """Unsplash search.

    The Unsplash *License* says attribution is optional. The Unsplash *API
    Guidelines* say it is mandatory - and using the API binds you to the
    guidelines. So we always return a credit, link to the photographer's
    profile AND to Unsplash, both carrying the required utm parameters.

    We also carry `download_location`; the guidelines require pinging it when
    a photo is actually adopted for use (see trigger_download).
    """
    if not key:
        return None
    data = _get(
        "https://api.unsplash.com/search/photos",
        {"query": query, "per_page": 1, "orientation": "landscape",
         "content_filter": "high"},
        {"Authorization": f"Client-ID {key}"},
    )
    results = (data or {}).get("results") or []
    if not results:
        return None
    p = results[0]
    raw = p["urls"]["raw"]
    return {
        # Guideline 1: must use the hotlinked URLs from photo.urls.
        "url": f"{raw}&w=1200&q=80&fm=jpg&fit=crop",
        "thumb_url": f"{raw}&w=600&q=70&fm=jpg&fit=crop",
        "title": p.get("description") or p.get("alt_description") or "",
        "credit": p["user"]["name"],
        "credit_url": p["user"]["links"]["html"] + _UTM,
        "source_name": "Unsplash",
        "source_url": "https://unsplash.com" + _UTM,
        "license": "Unsplash License",
        "license_url": "https://unsplash.com/license",
        "download_location": (p.get("links") or {}).get("download_location", ""),
        "provider": "unsplash",
    }


def trigger_download(download_location: str, key: str) -> bool:
    """Guideline 2: ping the download endpoint when a photo is adopted.

    Unsplash uses this to credit the photographer with a "download". It is a
    hard requirement for API approval, not an optional analytics ping.
    """
    if not (download_location and key):
        return False
    try:
        with httpx.Client(timeout=_TIMEOUT) as c:
            r = c.get(download_location, headers={**_UA, "Authorization": f"Client-ID {key}"})
            return r.status_code == 200
    except Exception:
        return False


def from_pexels(query: str, key: str):
    """Pexels search.

    Pexels' API guidelines differ from Unsplash's in two ways that matter:

      * There is no download endpoint to ping.
      * As well as crediting the photographer, the integration must show a
        "prominent link to Pexels" somewhere in the UI - not only a per-image
        credit. That site-level link is rendered by ProviderCredit.jsx.

    Their documented credit format links BOTH the photographer's profile and
    the photo's page on Pexels, so we return both rather than linking the
    Pexels homepage.
    """
    if not key:
        return None
    data = _get(
        "https://api.pexels.com/v1/search",
        {"query": query, "per_page": 1, "orientation": "landscape"},
        {"Authorization": key},
    )
    photos = (data or {}).get("photos") or []
    if not photos:
        return None
    p = photos[0]
    return {
        "url": p["src"]["large"],
        "thumb_url": p["src"]["medium"],
        "credit": p["photographer"],
        "credit_url": p["photographer_url"],
        "license": "Pexels License",
        "license_url": "https://www.pexels.com/license/",
        "title": p.get("alt") or "",
        "source_name": "Pexels",
        # the photo's own page, per their documented example
        "source_url": p.get("url") or "https://www.pexels.com",
        "provider": "pexels",
    }


# Openverse returns a lot of diagrams, maps and book scans. Filtering these
# out matters: an unfiltered "Kyoto" search returns a vintage *map* first.
_JUNK = (
    "map", "locator", "flag", "coat of arms", "diagram", "chart", "logo",
    "seal", "emblem", "plan of", "sketch", "engraving", "postage", "stamp",
)


def _looks_like_a_photo(result: dict) -> bool:
    title = (result.get("title") or "").lower()
    if any(word in title for word in _JUNK):
        return False
    # SVGs are never photographs.
    url = (result.get("url") or "").lower()
    return not url.endswith(".svg")


def from_openverse(query: str, _key: str = ""):
    data = _get(
        "https://api.openverse.org/v1/images/",
        {
            "q": f"{query} landscape",
            "page_size": 8,
            "license_type": "commercial",
            "aspect_ratio": "wide",
            "size": "large",
            "mature": "false",
        },
    )
    for r in (data or {}).get("results") or []:
        if not _looks_like_a_photo(r):
            continue
        code = (r.get("license") or "").lower()
        ver = r.get("license_version") or ""
        # CC0 is branded "CC0", the rest are "CC BY", "CC BY-SA", ...
        label = ("CC0" if code == "cc0" else f"CC {code.upper()}")
        if ver:
            label = f"{label} {ver}"
        deed = (
            f"https://creativecommons.org/publicdomain/zero/{ver or '1.0'}/"
            if code == "cc0"
            else f"https://creativecommons.org/licenses/{code}/{ver or '4.0'}/"
        )
        return {
            "url": r["url"],
            "thumb_url": r["url"],
            "title": r.get("title") or "",
            "credit": r.get("creator") or "Unknown",
            "credit_url": r.get("foreign_landing_url") or "",
            "license": label,
            "license_url": deed,
            "source_name": "Openverse",
            "source_url": r.get("foreign_landing_url") or "https://openverse.org",
            "provider": "openverse",
        }
    return None
