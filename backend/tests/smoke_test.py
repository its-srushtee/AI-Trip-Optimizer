"""End-to-end smoke test. Run against a live server:

    python tests/smoke_test.py
"""
import json
import urllib.error
import urllib.request
import uuid

BASE = "http://127.0.0.1:8000"
PASS = "\u2713"
FAIL = "\u2717"


def call(method, path, body=None, token=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as r:
            raw = r.read().decode() or "null"
            return r.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode() or "null"
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def check(label, ok, detail=""):
    print(f"  {PASS if ok else FAIL} {label}" + (f"  -> {detail}" if detail else ""))
    return ok


def main():
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    password = "secret123"
    results = []

    print("\n== health ==")
    s, r = call("GET", "/health")
    results.append(check("GET /health -> 200", s == 200 and r.get("status") == "ok", r))

    print("\n== auth ==")
    # Signup collects basic details only — no travel preferences.
    s, r = call("POST", "/auth/signup", {"name": "Test User", "email": email, "password": password})
    results.append(check("signup -> 201 + token", s == 201 and "access_token" in r, f"status={s}"))
    results.append(check("signup -> empty preferences", r.get("user", {}).get("preferences") == {},
                         r.get("user", {}).get("preferences")))
    results.append(check("signup -> profile_complete false",
                         r.get("user", {}).get("profile_complete") is False,
                         r.get("user", {}).get("profile_complete")))
    token = r.get("access_token", "")

    s, r = call("POST", "/auth/login", {"email": email, "password": password})
    results.append(check("login -> 200 + token", s == 200 and "access_token" in r, f"status={s}"))

    s, r = call("POST", "/auth/signup", {"name": "X", "email": email, "password": password})
    results.append(check("duplicate signup -> 409", s == 409, r.get("detail")))

    s, r = call("POST", "/auth/login", {"email": email, "password": "wrongpass"})
    results.append(check("bad password -> 401", s == 401, r.get("detail")))

    s, r = call("POST", "/auth/signup", {"name": "X", "email": email, "password": "123"})
    results.append(check("short password -> 422", s == 422, ""))

    print("\n== users ==")
    s, r = call("GET", "/users/me", token=token)
    results.append(check("GET /users/me -> 200", s == 200 and r.get("email") == email, r))
    results.append(check("new account starts incomplete", r.get("profile_complete") is False,
                         r.get("preferences")))

    # Profile completion happens after sign-in, via PATCH /users/me.
    s, r = call("PATCH", "/users/me", {"name": "Updated Name", "preferences": {"style": "Luxury", "interests": ["food"], "pace": "Relaxed", "accommodation": "Hotel", "food": "No preference"}}, token=token)
    results.append(check("PATCH /users/me -> 200", s == 200 and r.get("name") == "Updated Name"
                         and r.get("preferences", {}).get("style") == "Luxury", r))
    results.append(check("profile_complete true after completion",
                         r.get("profile_complete") is True, r.get("profile_complete")))

    # Partial preferences must NOT count as complete.
    s, r = call("PATCH", "/users/me", {"preferences": {"style": "Luxury", "interests": []}}, token=token)
    results.append(check("partial preferences -> incomplete", r.get("profile_complete") is False,
                         r.get("profile_complete")))
    # restore a complete profile for the remaining checks
    call("PATCH", "/users/me", {"preferences": {"style": "Luxury", "interests": ["food"], "pace": "Relaxed", "accommodation": "Hotel", "food": "No preference"}}, token=token)

    s, r = call("GET", "/users/me")
    results.append(check("no token -> 401", s == 401, r.get("detail")))

    print("\n== trips ==")
    trip = {"destination": "Bali", "start_date": "2026-10-12", "end_date": "2026-10-19",
            "budget": 2000, "travelers": 2, "interests": ["beaches", "food"]}
    s, r = call("POST", "/trips", trip, token=token)
    results.append(check("POST /trips -> 201", s == 201 and r.get("destination") == "Bali", f"status={s}"))

    s, r = call("GET", "/trips", token=token)
    results.append(check("GET /trips -> 1 trip", s == 200 and isinstance(r, list) and len(r) == 1, f"count={len(r) if isinstance(r, list) else r}"))

    s, r = call("POST", "/trips", {**trip, "start_date": "2026-10-19", "end_date": "2026-10-12"}, token=token)
    results.append(check("end < start -> 400", s == 400, r.get("detail")))

    s, r = call("GET", "/trips")
    results.append(check("no token -> 401", s == 401, r.get("detail")))

    print("\n== optimize ==")
    s, r = call("POST", "/trips/optimize", trip, token=token)
    itin = r.get("itinerary", {}) if isinstance(r, dict) else {}
    results.append(check("POST /trips/optimize -> 8 days", s == 200 and len(itin.get("days", [])) == 8,
                         f"days={len(itin.get('days', []))}"))

    print("\n== destinations ==")
    s, r = call("GET", "/destinations")
    results.append(check("GET /destinations -> 7", s == 200 and isinstance(r, list) and len(r) == 7,
                         f"count={len(r) if isinstance(r, list) else r}"))

    print("\n== destination images ==")
    # Local catalogue hit: must not touch the network (remote=false).
    s, r = call("GET", "/destinations/image?q=Bali&remote=false")
    results.append(check("image: Bali -> local catalogue",
                         s == 200 and r.get("url") == "/images/bali.jpg",
                         f"{r.get('source')} {r.get('url')}"))

    # Word-boundary matching: the old substring helper mapped this to goa.jpg.
    s, r = call("GET", "/destinations/image?q=Goat%20Island&remote=false")
    results.append(check("image: 'Goat Island' does NOT match Goa",
                         s == 200 and r.get("url") != "/images/goa.jpg",
                         f"{r.get('url')}"))

    # "Alps" should still resolve to the "Swiss Alps" catalogue entry.
    s, r = call("GET", "/destinations/image?q=Alps&remote=false")
    results.append(check("image: 'Alps' -> alps.jpg",
                         s == 200 and r.get("url") == "/images/alps.jpg",
                         f"{r.get('url')}"))

    # Unknown destination with remote disabled must still return a usable URL.
    s, r = call("GET", "/destinations/image?q=Zzyzx&remote=false")
    results.append(check("image: unknown + offline -> hero fallback",
                         s == 200 and r.get("url") == "/images/hero.jpg",
                         f"{r.get('source')} {r.get('url')}"))

    print()
    ok = sum(results)
    print(f"{ok}/{len(results)} checks passed")
    raise SystemExit(0 if ok == len(results) else 1)


if __name__ == "__main__":
    main()
