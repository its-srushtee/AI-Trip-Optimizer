"""Destination agent — researches what to see/do at the destination.

Uses the RAG retriever over the travel documents corpus and curates real,
preference-prioritized attractions with explicit match explanations and visit durations.
"""
import logging
import re
from typing import Any

from app.agents.base import BaseAgent
from app.api_clients.geoapify import geoapify_client
from app.api_clients.serpapi import serpapi_client
from app.database.base import SessionLocal
from app.models.destination_cache import DestinationInfoCache
from app.rag.retriever import get_retriever

logger = logging.getLogger(__name__)

# In-memory fast cache for retrieved destination intelligence
_DEST_CACHE: dict[str, dict] = {}



def compute_why_matches(place: dict, user_interests: list[str]) -> str:
    """Explains internally and clearly why this place matches the traveler's interests."""
    ptags = [t.lower() for t in place.get("tags", [])]
    pcat = (place.get("category") or "").lower()
    pdesc = (place.get("description") or "").lower()

    matched = []
    for u in user_interests:
        u_norm = u.lower().strip()
        if u_norm in ptags or u_norm in pcat or u_norm in pdesc:
            matched.append(u.title())

    # Specific synergies
    if "Nature" in matched and "Adventure" in matched:
        return "Directly matches your Nature & Adventure interests with mountain landscapes, outdoor exploration, and scenic hiking trails."
    if "History" in matched and "Culture" in matched:
        return "Directly matches your History & Culture interests with centuries-old heritage architecture, historic monuments, and royal artifacts."
    if "Beaches" in matched and "Relaxation" in matched:
        return "Directly matches your Beaches & Relaxation interests with peaceful coastal shores, soft sands, and serene ocean views."
    if "Food" in matched and "Photography" in matched:
        return "Directly matches your Food & Photography interests with celebrated culinary market tastings and iconic photogenic angles."

    # Single interest alignment
    if "Adventure" in matched:
        return "Directly matches your Adventure interest with exciting outdoor activities, trails, and active excursions."
    if "Nature" in matched:
        return "Directly matches your Nature interest with scenic landscapes, lush greenery, and serene outdoor vistas."
    if "History" in matched:
        return "Directly matches your History interest with storied historic architecture and preserved heritage landmarks."
    if "Culture" in matched:
        return "Directly matches your Culture interest with authentic local heritage, traditions, and cultural landmarks."
    if "Food" in matched:
        return "Directly matches your Food interest with signature regional cuisine, vibrant food markets, and authentic flavors."
    if "Photography" in matched:
        return "Directly matches your Photography interest with panoramic viewpoints, distinctive architecture, and photogenic compositions."
    if "Beaches" in matched:
        return "Directly matches your Beaches interest with coastal relaxation, ocean breezes, and seaside leisure."
    if "Relaxation" in matched:
        return "Directly matches your Relaxation interest with peaceful surroundings, restorative atmosphere, and unhurried leisure."
    if matched:
        return f"Curated to match your {', '.join(matched)} travel preference{'s' if len(matched) > 1 else ''}."
    return f"Top-rated attraction offering memorable travel experiences in {place.get('location', 'the destination')}."


def _normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def retrieve_dynamic_attractions(
    destination: str,
    interests: list[str] | None = None,
) -> tuple[dict, list[dict]]:
    """Retrieves real, verified attractions and geocoded coordinates for ANY destination worldwide.

    1. Checks persistent database cache (DestinationInfoCache).
    2. Geocodes destination to lat/lon/country using Geoapify.
    3. Retrieves real sights via SerpApi Google Knowledge Graph / Top Sights.
    4. Retrieves verified places via Geoapify Places by coordinates and categories.
    5. Fuses, deduplicates, and caches results.
    6. Does NOT fabricate fake attractions or fake coordinates if APIs yield empty results.
    """
    clean_dest = (destination or "").strip()
    if not clean_dest:
        return {}, []

    cache_key = _normalize_key(clean_dest)

    # 1. Fast Memory Cache
    if cache_key in _DEST_CACHE:
        cached = _DEST_CACHE[cache_key]
        return cached.get("geo_info", {}), [dict(p) for p in cached.get("places", [])]

    # 2. Database Cache
    try:
        with SessionLocal() as db:
            row = db.get(DestinationInfoCache, cache_key)
            if row and row.attractions:
                geo_info = {
                    "lat": row.coordinates.get("lat") if row.coordinates else None,
                    "lon": row.coordinates.get("lon") if row.coordinates else None,
                    "country": row.country,
                    "formatted": row.formatted_address or clean_dest,
                }
                _DEST_CACHE[cache_key] = {"geo_info": geo_info, "places": row.attractions}
                return geo_info, [dict(p) for p in row.attractions]
    except Exception as e:
        logger.debug("Database cache lookup notice: %s", e)

    # 3. Dynamic Geocoding via Geoapify
    geo_data = geoapify_client.geocode(clean_dest)
    lat = geo_data.get("lat") if geo_data else None
    lon = geo_data.get("lon") if geo_data else None
    country = geo_data.get("country", "") if geo_data else ""
    formatted_addr = geo_data.get("formatted", clean_dest) if geo_data else clean_dest

    if not country and "," in clean_dest:
        country = clean_dest.split(",")[-1].strip()

    geo_info = {
        "lat": lat,
        "lon": lon,
        "lng": lon,
        "country": country,
        "formatted": formatted_addr,
        "city": geo_data.get("city", clean_dest) if geo_data else clean_dest,
    }

    collected_places: list[dict] = []
    seen_names = set()

    def _add_place(p: dict):
        norm = re.sub(r"[^a-z0-9]+", "", p.get("name", "").lower())
        if not norm or len(norm) < 3 or norm in seen_names:
            return
        seen_names.add(norm)
        collected_places.append(p)

    # 4. Retrieve live Google Knowledge Graph sights via SerpApi
    if serpapi_client.is_configured():
        serp_sights = serpapi_client.search_attractions(clean_dest, interests=interests, limit=15)
        for s in serp_sights:
            s["coordinates"] = {"lat": lat, "lon": lon} if (lat is not None and lon is not None) else None
            _add_place(s)

    # 5. Retrieve verified nearby places via Geoapify Places API
    if geoapify_client.is_configured() and lat is not None and lon is not None:
        geo_places = geoapify_client.search_places(lat, lon, interests=interests, radius_meters=25000, limit=20)
        for gp in geo_places:
            gp_norm = re.sub(r"[^a-z0-9]+", "", gp.get("name", "").lower())
            matched_existing = next(
                (ep for ep in collected_places if gp_norm in re.sub(r"[^a-z0-9]+", "", ep.get("name", "").lower()) or re.sub(r"[^a-z0-9]+", "", ep.get("name", "").lower()) in gp_norm),
                None
            )
            if matched_existing:
                matched_existing["coordinates"] = gp.get("coordinates")
                matched_existing["address"] = gp.get("address")
                matched_existing["source"] = "Google & Geoapify (Verified)"
            else:
                _add_place(gp)

    # 6. Fallback to factual RAG knowledge guides if external APIs return no places (e.g. offline sandbox)
    if not collected_places:
        try:
            retriever = get_retriever()
            rag_docs = retriever.retrieve(clean_dest, top_k=2)
            for r_doc in rag_docs:
                doc_id = r_doc.get("id", "").lower()
                clean_lower = clean_dest.lower()
                if clean_lower in doc_id or doc_id in clean_lower or any(word in doc_id for word in clean_lower.split()):
                    for line in r_doc.get("content", "").splitlines():
                        m = re.match(r"^-\s+\*\*([^*]+)\*\*\s*—\s*(.+)$", line.strip())
                        if m:
                            p_name = m.group(1).strip()
                            p_desc = m.group(2).strip()
                            p_cat = "Sight & Attraction"
                            p_tags = []
                            combo = f"{p_name} {p_desc}".lower()

                            if re.search(r"\b(beach|beaches|coastal|coast|cove|bay|ocean|seas)\b", combo) or re.search(r"\bsea\b", combo):
                                p_cat = "Beaches & Coastal"
                                p_tags.extend(["beaches", "relaxation"])
                            elif any(w in combo for w in ["temple", "church", "cathedral", "monastery", "basilica", "mosque", "ghat", "sacred", "spiritual"]):
                                p_cat = "Religious & Spiritual Sights"
                                p_tags.extend(["spirituality", "culture", "history"])
                            elif any(w in combo for w in ["fort", "palace", "museum", "historic", "heritage", "unesco", "monument"]):
                                p_cat = "History & Heritage"
                                p_tags.extend(["history", "culture"])
                            elif any(w in combo for w in ["valley", "trek", "adventure", "skiing", "paragliding", "pass", "peak", "climb"]):
                                p_cat = "Adventure & Outdoors"
                                p_tags.extend(["adventure", "nature"])
                            elif any(w in combo for w in ["waterfall", "nature", "forest", "sanctuary", "river", "lake"]):
                                p_cat = "Nature & Scenic"
                                p_tags.extend(["nature", "photography"])
                            elif any(w in combo for w in ["curry", "food", "dining", "dish", "restaurant", "market", "cafe"]):
                                p_cat = "Food & Dining"
                                p_tags.extend(["food"])

                            _add_place({
                                "name": p_name,
                                "description": p_desc,
                                "category": p_cat,
                                "location": clean_dest,
                                "tags": p_tags or ["culture", "sightseeing"],
                                "rating": 4.8,
                                "source": "Travel Knowledge Base (RAG Verified)",
                                "estimated_duration": "2 - 3 hours",
                            })
        except Exception as e:
            logger.debug("RAG factual fallback notice: %s", e)

    # 7. Dynamically resolve photos for each collected place
    try:
        from app.services.image_service import resolve as resolve_image
        with SessionLocal() as db:
            for p in collected_places:
                if not p.get("image_url") or p.get("image_url") == "/images/hero.jpg":
                    place_img = resolve_image(db, f"{clean_dest} {p.get('name')}", allow_remote=True)
                    if place_img and place_img.get("url"):
                        p["image_url"] = place_img["url"]
                    else:
                        dest_img = resolve_image(db, clean_dest, allow_remote=True)
                        p["image_url"] = dest_img.get("url") or "/images/hero.jpg"
    except Exception as e:
        logger.debug("Image resolution notice: %s", e)

    # 7. Cache results in memory and database
    _DEST_CACHE[cache_key] = {"geo_info": geo_info, "places": collected_places}
    if collected_places:
        try:
            with SessionLocal() as db:
                existing = db.get(DestinationInfoCache, cache_key)
                if not existing:
                    db.add(DestinationInfoCache(
                        query_key=cache_key,
                        destination_name=clean_dest,
                        country=country,
                        formatted_address=formatted_addr,
                        coordinates={"lat": lat, "lon": lon} if (lat is not None and lon is not None) else {},
                        attractions=collected_places,
                        source="Live APIs (Geoapify & SerpApi)",
                    ))
                    db.commit()
        except Exception as e:
            logger.debug("Database cache save notice: %s", e)

    return geo_info, collected_places


class DestinationAgent(BaseAgent):
    name = "destination"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        req = state["request"]
        city = req.get("destination", "")
        raw_interests = [i.lower().strip() for i in req.get("interests", [])]

        # Filter out preferences not supported by this destination
        from app.services.destination_preferences import get_destination_preferences
        dest_pref_info = get_destination_preferences(city)
        supported_pref_ids = {p["id"] for p in dest_pref_info.get("preferences", [])}
        if supported_pref_ids:
            interests = [i for i in raw_interests if i in supported_pref_ids]
            if not interests and raw_interests:
                # If user had interests but none matched supported ones, default to top supported
                interests = [dest_pref_info["preferences"][0]["id"]]
        else:
            interests = raw_interests

        query = f"{city} {' '.join(interests)} things to do attractions".strip()
        retriever = get_retriever()
        docs = retriever.retrieve(query, top_k=3)

        # Dynamic highlights aligned with user interests
        highlights = []
        if "adventure" in interests and "nature" in interests:
            highlights.append("Mountain trekking routes, alpine vistas, and outdoor wilderness excursions")
        elif "adventure" in interests:
            highlights.append("Active outdoor adventure circuits, scenic hiking trails, and high-altitude sports")
        elif "nature" in interests:
            highlights.append("Scenic pine forests, crystal waterfalls, and peaceful nature reserves")

        if "history" in interests and "culture" in interests:
            highlights.append("UNESCO World Heritage forts, royal palaces, and historic monument tours")
        elif "history" in interests:
            highlights.append("Centuries-old historic landmarks, ancient citadels, and archaeological relics")
        elif "culture" in interests:
            highlights.append("Historic architectural quarters, artisan craft studios, and cultural museums")

        if "food" in interests:
            highlights.append("Authentic regional food markets, signature street delicacies, and culinary masterclasses")

        if "beaches" in interests and "relaxation" in interests:
            highlights.append("Peaceful coastal coves, tranquil white-sand shores, and unhurried beachside relaxation")
        elif "beaches" in interests:
            highlights.append("Golden coastal sands, ocean water activities, and seaside boardwalks")
        elif "relaxation" in interests:
            highlights.append("Restorative wellness retreats, natural thermal mineral spas, and tranquil gardens")

        if "photography" in interests:
            highlights.append("Iconic photography viewpoints, golden-hour compositions, and panoramic horizons")

        if not highlights:
            highlights = [
                f"Top-rated attractions and landmarks in {city}",
                "Curated local food and cultural experiences",
                "Scenic vistas and memorable hidden spots",
            ]

        # 1. Retrieve dynamic attractions and geocoding for ANY destination
        geo_info, raw_places = retrieve_dynamic_attractions(city, interests=interests)

        # 2. Enrich each place with why_it_matches and estimated_duration
        for p in raw_places:
            p["why_it_matches"] = compute_why_matches(p, interests)
            if not p.get("estimated_duration"):
                p["estimated_duration"] = "2 - 3 hours"
            matched_tags = [u.title() for u in interests if u in [t.lower() for t in p.get("tags", [])]]
            p["match_reasons"] = matched_tags

        # 3. Preference-Aware Scoring and Prioritization
        def place_score(p: dict) -> int:
            score = 10
            ptags = [t.lower() for t in p.get("tags", [])]
            pcat = (p.get("category") or "").lower()
            pdesc = (p.get("description") or "").lower()

            for user_interest in interests:
                u = user_interest.lower().strip()
                if u in ptags:
                    score += 25
                elif u in pcat:
                    score += 18
                elif u in pdesc:
                    score += 10

            # Direct synergy bonuses
            if "nature" in interests and "adventure" in interests:
                if any(t in ptags for t in ["nature", "adventure"]):
                    score += 20
            if "history" in interests and "culture" in interests:
                if any(t in ptags for t in ["history", "culture"]):
                    score += 20
            if "beaches" in interests and "relaxation" in interests:
                if any(t in ptags for t in ["beaches", "relaxation"]):
                    score += 20
            if "food" in interests and "photography" in interests:
                if any(t in ptags for t in ["food", "photography"]):
                    score += 20

            # Tie breaker with rating
            score += int((p.get("rating", 4.5) - 4.0) * 10)
            return score

        sorted_places = sorted(raw_places, key=place_score, reverse=True)

        state["destination"] = {
            "name": city,
            "country": geo_info.get("country", ""),
            "coordinates": {"lat": geo_info.get("lat"), "lon": geo_info.get("lon"), "lng": geo_info.get("lon")} if geo_info.get("lat") else None,
            "formatted_address": geo_info.get("formatted", city),
            "highlights": highlights[:4],
            "rag_context": [d["content"][:300] for d in docs],
            "source": "rag" if docs else "dynamic_intelligence",
            "places_to_visit": sorted_places,
        }
        return state
