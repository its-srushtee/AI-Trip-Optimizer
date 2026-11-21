"""Resolve a destination name to a photo URL.

Lookup order:

    1. image_cache table          - no network call
    2. catalogue local file       - /images/<slug>.jpg shipped with the app
    3. provider chain             - Unsplash -> Pexels -> Openverse
    4. /images/hero.jpg           - final fallback, never fails

Steps 1 and 2 mean the seeded destinations never touch the network at
all; the providers only get hit for destinations a user types that we have no
local photo for (Kyoto, Barcelona, ...), which is exactly the gap the old
string-matching helper fell into.
"""
from __future__ import annotations

import logging
import os
import re

from sqlalchemy.orm import Session

from app.api_clients.images import (
    from_openverse, from_pexels, from_unsplash, trigger_download,
)
from app.core.config import settings
from app.models.destination import Destination
from app.models.image_cache import ImageCache

logger = logging.getLogger(__name__)

FALLBACK = "/images/hero.jpg"

_IMAGES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "public", "images")
)


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", (name or "").lower()).strip()


def is_valid_image_url(url: str | None) -> bool:
    """Validates that a URL is non-empty and points to an existing local file or valid http(s) URL."""
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    if not u:
        return False
    if u.startswith("/images/"):
        fname = os.path.basename(u)
        return os.path.exists(os.path.join(_IMAGES_DIR, fname))
    if u.startswith("http://") or u.startswith("https://"):
        return len(u) > 10 and "." in u
    return False


def get_fallback_image() -> str:
    """Return the verified local hero fallback, with a filesystem safety check."""
    if os.path.exists(os.path.join(_IMAGES_DIR, "hero.jpg")):
        return "/images/hero.jpg"
    try:
        for f in os.listdir(_IMAGES_DIR):
            if f.endswith(".jpg") or f.endswith(".png"):
                return f"/images/{f}"
    except Exception:
        pass
    return FALLBACK


def _local_file_for(db: Session, name: str) -> str | None:
    """Exact/word-boundary match against the local images directory or verified catalogue entries.

    Deliberately NOT a substring test - compare whole words instead.
    Only returns URLs that point to verified existing files on disk.
    """
    n = _norm(name)
    if not n:
        return None

    # Check if a matching image file exists directly on disk (e.g. london.jpg, tokyo.jpg, goa.jpg)
    direct_file = f"{n.replace(' ', '_')}.jpg"
    if os.path.exists(os.path.join(_IMAGES_DIR, direct_file)):
        return f"/images/{direct_file}"
    if os.path.exists(os.path.join(_IMAGES_DIR, f"{n}.jpg")):
        return f"/images/{n}.jpg"

    all_dests = db.query(Destination).all()
    words = set(n.split())
    for d in all_dests:
        dn = _norm(d.name)
        if not dn:
            continue
        # match when the full catalogue name appears as a word sequence
        if dn == n or re.search(rf"(^| ){re.escape(dn)}( |$)", n):
            if is_valid_image_url(d.image_url) and d.image_url.startswith("/images/"):
                return d.image_url
        # single-word catalogue names may also match a lone word ("Alps")
        if " " not in dn and dn in words:
            if is_valid_image_url(d.image_url) and d.image_url.startswith("/images/"):
                return d.image_url
    for d in all_dests:
        dn = _norm(d.name)
        if " " in dn and any(w in words for w in dn.split() if len(w) > 3):
            if is_valid_image_url(d.image_url) and d.image_url.startswith("/images/"):
                return d.image_url
    return None


def _from_providers(query: str) -> dict | None:
    # Try providers in order: Unsplash -> Pexels -> Openverse
    # If Unsplash is configured, use it first; otherwise Pexels; Openverse is keyless fallback.
    providers = []
    if settings.UNSPLASH_ACCESS_KEY:
        providers.append((from_unsplash, settings.UNSPLASH_ACCESS_KEY))
    if settings.PEXELS_API_KEY:
        providers.append((from_pexels, settings.PEXELS_API_KEY))
    providers.append((from_openverse, ""))

    for fn, key in providers:
        try:
            hit = fn(query, key)
        except Exception as e:
            logger.debug("Provider lookup exception for %s: %s", query, e)
            hit = None
        if hit and is_valid_image_url(hit.get("url")):
            return hit
    return None


def resolve(db: Session, name: str, allow_remote: bool = True, force_refresh: bool = False) -> dict:
    """Return {url, thumb_url, credit, credit_url, license, license_url, title, source_name, source_url, provider, source}."""
    fallback_url = get_fallback_image()
    key = _norm(name)
    if not key:
        return {"url": fallback_url, "thumb_url": fallback_url, "provider": "local", "source": "fallback"}

    # 1. Check verified local catalogue / bundled image files first (highest quality, zero network)
    if not force_refresh:
        local = _local_file_for(db, name)
        if local and is_valid_image_url(local):
            return {
                "url": local, "thumb_url": local, "credit": "", "credit_url": "",
                "license": "", "license_url": "", "title": "",
                "source_name": "", "source_url": "",
                "provider": "local", "source": "catalogue",
            }

    # 2. Check cached third-party photo
    cached = db.get(ImageCache, key)
    if cached and not force_refresh:
        if is_valid_image_url(cached.url):
            # Cached URL is valid and confirmed reusable
            return {
                "url": cached.url,
                "thumb_url": cached.thumb_url or cached.url,
                "credit": cached.credit or "",
                "credit_url": cached.credit_url or "",
                "license": cached.license or "",
                "license_url": cached.license_url or "",
                "source_name": cached.source_name or "",
                "source_url": cached.source_url or "",
                "title": cached.title or "",
                "provider": cached.provider or "cache",
                "source": "cache",
            }
        else:
            # Cached URL is broken/invalid (e.g. non-existent local file or empty) - do not repeatedly serve
            logger.warning("Cached image for '%s' has invalid URL (%s); refreshing.", key, cached.url)
            if allow_remote:
                hit = _from_providers(name)
                if hit and is_valid_image_url(hit.get("url")):
                    cached.url = hit["url"]
                    cached.thumb_url = hit.get("thumb_url") or hit["url"]
                    cached.credit = hit.get("credit", "")
                    cached.credit_url = hit.get("credit_url", "")
                    cached.license = hit.get("license", "")
                    cached.license_url = hit.get("license_url", "")
                    cached.source_name = hit.get("source_name", "")
                    cached.source_url = hit.get("source_url", "")
                    cached.title = hit.get("title", "")
                    cached.provider = hit["provider"]
                    db.commit()
                    return {**hit, "source": "refreshed"}
            # Provider unavailable or remote disabled: fall back gracefully
            return {"url": fallback_url, "thumb_url": fallback_url, "provider": "local", "source": "fallback"}

    if not allow_remote:
        return {"url": fallback_url, "thumb_url": fallback_url, "provider": "local", "source": "fallback"}

    # 3. Dynamic lookup from providers
    hit = _from_providers(name)
    if not hit or not is_valid_image_url(hit.get("url")):
        return {"url": fallback_url, "thumb_url": fallback_url, "provider": "local", "source": "fallback"}

    if cached:
        cached.url = hit["url"]
        cached.thumb_url = hit.get("thumb_url") or hit["url"]
        cached.credit = hit.get("credit", "")
        cached.credit_url = hit.get("credit_url", "")
        cached.license = hit.get("license", "")
        cached.license_url = hit.get("license_url", "")
        cached.source_name = hit.get("source_name", "")
        cached.source_url = hit.get("source_url", "")
        cached.title = hit.get("title", "")
        cached.provider = hit["provider"]
    else:
        db.add(ImageCache(
            query=key, url=hit["url"], thumb_url=hit.get("thumb_url", ""),
            credit=hit.get("credit", ""), credit_url=hit.get("credit_url", ""),
            license=hit.get("license", ""), license_url=hit.get("license_url", ""),
            source_name=hit.get("source_name", ""), source_url=hit.get("source_url", ""),
            title=hit.get("title", ""), provider=hit["provider"],
        ))
    db.commit()

    if hit["provider"] == "unsplash":
        trigger_download(hit.get("download_location", ""), settings.UNSPLASH_ACCESS_KEY)

    return {**hit, "source": "provider"}


def invalidate_cached_image(db: Session, name_or_query: str) -> dict:
    """Invalidates or refreshes a specific cached image record without affecting other valid records.

    If providers return a new photo, updates the row.
    If providers cannot find one, updates to fallback so broken URLs are not repeatedly served.
    """
    key = _norm(name_or_query)
    if not key:
        return {"query": name_or_query, "status": "invalid_query"}

    fallback_url = get_fallback_image()
    cached = db.get(ImageCache, key)

    hit = _from_providers(name_or_query)
    if hit and is_valid_image_url(hit.get("url")):
        if cached:
            cached.url = hit["url"]
            cached.thumb_url = hit.get("thumb_url") or hit["url"]
            cached.credit = hit.get("credit", "")
            cached.credit_url = hit.get("credit_url", "")
            cached.license = hit.get("license", "")
            cached.license_url = hit.get("license_url", "")
            cached.source_name = hit.get("source_name", "")
            cached.source_url = hit.get("source_url", "")
            cached.title = hit.get("title", "")
            cached.provider = hit["provider"]
        else:
            cached = ImageCache(
                query=key, url=hit["url"], thumb_url=hit.get("thumb_url") or hit["url"],
                credit=hit.get("credit", ""), credit_url=hit.get("credit_url", ""),
                license=hit.get("license", ""), license_url=hit.get("license_url", ""),
                source_name=hit.get("source_name", ""), source_url=hit.get("source_url", ""),
                title=hit.get("title", ""), provider=hit["provider"],
            )
            db.add(cached)
        db.commit()
        return {"query": key, "status": "refreshed", "url": hit["url"], "provider": hit["provider"]}
    else:
        # Provider unavailable: set fallback on this record so broken URL is not repeated
        if cached:
            cached.url = fallback_url
            cached.provider = "fallback"
            db.commit()
        return {"query": key, "status": "fallback_applied", "url": fallback_url, "provider": "fallback"}
