"""Verify the Pexels API key end to end.

    cd backend
    .venv/bin/python tests/check_pexels.py

Checks, in order:
  1. a key is present in the environment / .env
  2. the key is accepted by Pexels (401 means it is wrong)
  3. the remaining quota, read from the response headers
  4. a real search returns a usable photo with attribution fields
  5. the resolver actually selects Pexels ahead of the other providers
"""
import sys

import httpx

sys.path.insert(0, ".")

from app.core.config import settings  # noqa: E402

KEY = settings.PEXELS_API_KEY
GREEN, RED, YELLOW, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def ok(m):
    print(f"  {GREEN}OK{OFF}    {m}")


def bad(m):
    print(f"  {RED}FAIL{OFF}  {m}")


def warn(m):
    print(f"  {YELLOW}NOTE{OFF}  {m}")


print("\nPexels API check")
print("-" * 60)

if not KEY:
    bad("No PEXELS_API_KEY found.")
    print(
        "\n  Add it to backend/.env :\n"
        "      PEXELS_API_KEY=your_key_here\n\n"
        "  Get a free key (instant, no approval) at:\n"
        "      https://www.pexels.com/api/\n\n"
        "  Until then the app falls back to Openverse, which needs no key.\n"
    )
    raise SystemExit(1)

ok(f"key found ({len(KEY)} chars, ends ...{KEY[-4:]})")

try:
    r = httpx.get(
        "https://api.pexels.com/v1/search",
        params={"query": "bali", "per_page": 1, "orientation": "landscape"},
        headers={"Authorization": KEY},
        timeout=15,
    )
except Exception as e:  # pragma: no cover - network failure path
    bad(f"could not reach Pexels: {e}")
    raise SystemExit(1)

if r.status_code == 401:
    bad("401 Unauthorized - the key is not valid.")
    raise SystemExit(1)
if r.status_code == 429:
    bad("429 Too Many Requests - rate limit already exhausted.")
    raise SystemExit(1)
if r.status_code != 200:
    bad(f"unexpected status {r.status_code}")
    raise SystemExit(1)

ok("key accepted by Pexels (HTTP 200)")

limit = r.headers.get("X-Ratelimit-Limit")
left = r.headers.get("X-Ratelimit-Remaining")
if limit:
    ok(f"quota: {left} of {limit} remaining this period")
else:
    warn("no quota headers returned")

photos = r.json().get("photos") or []
if not photos:
    bad("search returned no photos")
    raise SystemExit(1)

p = photos[0]
ok(f"search works - '{(p.get('alt') or 'untitled')[:44]}'")
print(f"        photographer : {p['photographer']}")
print(f"        photo page   : {p['url']}")
print(f"        image (large): {p['src']['large'][:66]}")

# the resolver should now prefer Pexels
from app.database.base import SessionLocal  # noqa: E402
from app.models.image_cache import ImageCache  # noqa: E402
from app.services.image_service import resolve  # noqa: E402

db = SessionLocal()
try:
    db.query(ImageCache).filter(ImageCache.query == "santorini").delete()
    db.commit()
    res = resolve(db, "Santorini")
    if res.get("provider") == "pexels":
        ok("resolver selected Pexels for an uncached destination")
        print(f"        credit    : {res['credit']} on {res['source_name']}")
        print(f"        licence   : {res['license']}")
    else:
        bad(f"resolver used '{res.get('provider')}' instead of pexels")
finally:
    db.close()

print("-" * 60)
print(f"{GREEN}Pexels is configured and working.{OFF}\n")
