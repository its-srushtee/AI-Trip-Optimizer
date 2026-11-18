"""Dynamic Destination-Based Travel Preferences Service.

Analyzes destination attractions, activities, and geographical profile
to determine available and supported travel preference categories.
Caches results to optimize performance and prevent repeated lookups.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.destination_agent import (
    _normalize_key,
    retrieve_dynamic_attractions,
)

logger = logging.getLogger(__name__)

# In-memory preference cache: key -> analyzed preferences dict
_PREFERENCE_CACHE: dict[str, dict[str, Any]] = {}

# Standardized preference categories with semantic keywords, categories, and icons
PREFERENCE_CATEGORIES: list[dict[str, Any]] = [
    {
        "id": "adventure",
        "label": "Adventure",
        "emoji": "⛰️",
        "keywords": [
            "adventure", "hiking", "trekking", "trek", "paragliding", "rafting",
            "skiing", "snow", "climbing", "quad biking", "safari", "scuba",
            "snorkeling", "water sports", "zipline", "outdoor", "expedition",
            "trails", "canyoning", "camping", "atv", "zorbing", "bungee",
        ],
        "category_matches": ["adventure", "outdoors", "sports", "hiking", "trekking", "extreme sports", "water sports"],
        "description": "Thrilling outdoor sports, hiking trails, high-adrenaline excursions, and expeditions.",
    },
    {
        "id": "nature",
        "label": "Nature",
        "emoji": "🌲",
        "keywords": [
            "nature", "mountain", "mountains", "forest", "forests", "waterfall",
            "waterfalls", "valley", "valleys", "lake", "lakes", "river", "glacier",
            "pass", "scenic", "wildlife", "flora", "fauna", "national park",
            "sanctuary", "backwaters", "greenery", "plantation", "pine", "hill",
            "meadow", "alpine", "reserve", "gardens",
        ],
        "category_matches": ["nature", "outdoors", "park", "wildlife", "natural", "landscape", "hiking"],
        "description": "Scenic landscapes, lush forests, waterfalls, wildlife sanctuaries, and alpine valleys.",
    },
    {
        "id": "culture",
        "label": "Culture & History",
        "emoji": "🏛️",
        "keywords": [
            "culture", "history", "heritage", "temple", "temples", "fort", "forts",
            "palace", "palaces", "museum", "museums", "monument", "monuments",
            "ruins", "ancient", "historic", "architecture", "unesco", "church",
            "churches", "cathedral", "art", "castle", "dynasty", "tradition",
            "pagoda", "stupa", "corridor", "gothic", "archaeological", "memorial",
        ],
        "category_matches": ["culture", "history", "heritage", "museum", "art", "monument", "historic", "architecture"],
        "description": "Centuries-old monuments, majestic forts, palaces, museums, and rich cultural heritage.",
    },
    {
        "id": "food",
        "label": "Food & Culinary",
        "emoji": "🍜",
        "keywords": [
            "food", "culinary", "cuisine", "dining", "restaurant", "restaurants",
            "street food", "cafe", "cafes", "tasting", "seafood", "bazaar",
            "gastronomy", "market", "dishes", "flavors", "bakery", "thali",
            "dhabas", "tea", "sushi", "ramen", "coffee", "pastry", "sweets",
            "chaat", "lassi", "kachori", "sadya", "bhel", "pav bhaji",
        ],
        "category_matches": ["food", "culinary", "gastronomy", "dining", "restaurant", "cafe", "market"],
        "description": "Celebrated regional cuisines, artisan street food walks, local markets, and culinary tastings.",
    },
    {
        "id": "relaxation",
        "label": "Relaxation & Wellness",
        "emoji": "🏖️",
        "keywords": [
            "relaxation", "relax", "wellness", "spa", "ayurveda", "retreat",
            "hot spring", "thermal springs", "peaceful", "calm", "serene",
            "tranquil", "unhurried", "sunset", "sunsets", "resort", "leisure",
            "massage", "rejuvenation", "sanctuary", "gardens", "botanical",
            "houseboat", "breeze", "cliffside",
        ],
        "category_matches": ["relaxation", "wellness", "spa", "leisure", "health", "park"],
        "description": "Rejuvenating wellness therapies, serene retreats, tranquil sunsets, and unhurried leisure.",
    },
    {
        "id": "beaches",
        "label": "Beaches & Coastal",
        "emoji": "🌊",
        "keywords": [
            "beach", "beaches", "coastal", "coast", "cove", "sea", "ocean",
            "shore", "lagoons", "surf", "surfing", "scuba", "snorkeling",
            "water sports", "island", "bay", "promenade", "marine",
            "shacks", "coastal bay", "seafront", "necklace",
        ],
        "category_matches": ["beach", "beaches", "coastal", "sea", "ocean", "water sports"],
        "description": "Sun-kissed coastal shores, golden sand beaches, marine lagoons, and seafront walks.",
    },
    {
        "id": "shopping",
        "label": "Shopping",
        "emoji": "🛍️",
        "keywords": [
            "shopping", "bazaar", "bazaars", "market", "markets", "souvenir",
            "souvenirs", "handicrafts", "boutique", "boutiques", "textiles",
            "jewelry", "mall", "malls", "artisan", "flea market", "curios",
            "silk", "sarees", "handloom", "zari", "bargain",
        ],
        "category_matches": ["shopping", "bazaar", "market", "mall", "commercial"],
        "description": "Artisan craft bazaars, traditional silk markets, designer boutiques, and souvenir alleys.",
    },
    {
        "id": "nightlife",
        "label": "Nightlife",
        "emoji": "🌃",
        "keywords": [
            "nightlife", "clubs", "clubbing", "bars", "pubs", "cocktails",
            "party", "parties", "dj", "live music", "evening entertainment",
            "casinos", "shacks", "lounges", "neon", "late night", "titos",
            "rooftop", "indie music",
        ],
        "category_matches": ["nightlife", "bar", "pub", "club", "entertainment"],
        "description": "Vibrant beach clubs, rooftop cocktail lounges, craft cocktail bars, and energetic nightlife.",
    },
    {
        "id": "photography",
        "label": "Photography",
        "emoji": "📸",
        "keywords": [
            "photography", "photogenic", "scenic", "viewpoint", "viewpoints",
            "panoramic", "landscape", "sunsets", "sunrise", "skyline",
            "monuments", "vistas", "picturesque", "outlook", "glacier panorama",
            "views", "golden hour", "photographers", "iconic",
        ],
        "category_matches": ["photography", "viewpoint", "scenic", "view", "monument"],
        "description": "Panoramic viewpoints, photogenic monuments, golden-hour light, and striking landscapes.",
    },
    {
        "id": "spirituality",
        "label": "Spirituality",
        "emoji": "🧘",
        "keywords": [
            "spirituality", "spiritual", "temple", "temples", "ghat", "ghats",
            "aarti", "meditation", "sacred", "holy", "pilgrimage", "ashram",
            "prayer", "ritual", "rituals", "monastery", "monasteries",
            "shrine", "shrines", "divine", "blessing", "jyotirlinga",
            "stupa", "buddha", "yoga", "chants", "diyas", "subah",
        ],
        "category_matches": ["spirituality", "religion", "temple", "shrine", "sacred", "worship"],
        "description": "Sacred temples, river ghat rituals, meditative retreats, and timeless spiritual pilgrimages.",
    },
    {
        "id": "family",
        "label": "Family-friendly",
        "emoji": "👨‍👩‍👧‍👦",
        "keywords": [
            "family", "family-friendly", "kids", "children", "parks",
            "theme park", "gardens", "zoo", "aquarium", "all-ages", "safe",
            "picnic", "boating", "sightseeing tour", "museum", "sanctuary",
        ],
        "category_matches": ["family", "entertainment", "park", "garden", "zoo", "aquarium"],
        "description": "Safe, versatile attractions, scenic parks, boat cruises, and fun activities for all ages.",
    },
]

# Quick lookup by ID and Label
PREF_BY_ID = {p["id"]: p for p in PREFERENCE_CATEGORIES}
PREF_BY_LABEL = {p["label"]: p for p in PREFERENCE_CATEGORIES}


def _matches_category(text: str, tags: list[str], pref_def: dict[str, Any]) -> int:
    """Computes a match score for an attraction against a preference category."""
    score = 0
    t_lower = text.lower()
    tags_lower = [t.lower() for t in tags]

    # Tag matches (highest weight)
    for tag in tags_lower:
        if tag in pref_def["keywords"] or tag == pref_def["id"]:
            score += 3

    # Category matches
    for cm in pref_def["category_matches"]:
        if cm in t_lower:
            score += 2

    # Keyword matches
    for kw in pref_def["keywords"]:
        if re.search(r"\b" + re.escape(kw) + r"\b", t_lower):
            score += 1

    return score


def get_destination_preferences(destination: str) -> dict[str, Any]:
    """Dynamically analyzes ANY destination worldwide using live geocoding & verified places.

    Determines supported travel preference categories strictly based on:
    - Real attractions and places retrieved from APIs (Geoapify & SerpApi)
    - Place categories, tags, and spatial characteristics
    - Does NOT use static city lists or hardcoded catalogues.
    """
    clean_dest = (destination or "").strip()
    if not clean_dest or len(clean_dest) < 2:
        return {
            "destination": clean_dest,
            "available_preferences": [],
            "preferences": [],
            "total_attractions": 0,
            "supported": False,
            "message": "Please enter a destination to discover available experiences.",
        }

    cache_key = _normalize_key(clean_dest)

    # 1. Fast Cache Lookup
    if cache_key in _PREFERENCE_CACHE:
        logger.debug("Serving preferences from cache for '%s'", clean_dest)
        return _PREFERENCE_CACHE[cache_key]

    # 2. Retrieve Destination Intelligence dynamically
    try:
        geo_info, places = retrieve_dynamic_attractions(clean_dest)
    except Exception as e:
        logger.warning("Error fetching destination intelligence for '%s': %s", clean_dest, e)
        geo_info, places = {}, []

    has_coords = geo_info.get("lat") is not None and geo_info.get("lon") is not None

    # Destination could not be geocoded and has no places
    if not has_coords and not places:
        result = {
            "destination": clean_dest,
            "available_preferences": [],
            "preferences": [],
            "total_attractions": 0,
            "supported": False,
            "message": f"Destination '{clean_dest}' was not found. Please verify the spelling or select from suggestions.",
        }
        _PREFERENCE_CACHE[cache_key] = result
        return result

    combined_places = list(places)

    # 3. Score Each Category Against Real Retrieved Places
    category_scores: dict[str, dict[str, Any]] = {}

    for pref in PREFERENCE_CATEGORIES:
        pid = pref["id"]
        count = 0
        total_score = 0
        matching_attractions: list[str] = []

        # Check each attraction discovered at the destination
        for p in combined_places:
            text_corpus = f"{p.get('name', '')} {p.get('category', '')} {p.get('description', '')} {p.get('visit_info', '')}"
            tags = p.get("tags") or []
            match_score = _matches_category(text_corpus, tags, pref)

            if match_score > 0:
                count += 1
                total_score += match_score
                if len(matching_attractions) < 3:
                    matching_attractions.append(p.get("name", ""))

        category_scores[pid] = {
            "id": pid,
            "label": pref["label"],
            "emoji": pref["emoji"],
            "description": pref["description"],
            "count": count,
            "score": total_score,
            "sample_attractions": matching_attractions,
        }

    # 4. Filter Supported Preferences purely by actual discovered places
    supported_prefs: list[dict[str, Any]] = []

    for pref in PREFERENCE_CATEGORIES:
        pid = pref["id"]
        stats = category_scores[pid]
        cnt = stats["count"]
        sc = stats["score"]

        # Category-specific strict presence verification based on discovered places
        if pid == "beaches":
            has_actual_beach = any(
                any(re.search(r"\b" + re.escape(w) + r"\b", f"{p.get('name', '')} {p.get('category', '')}".lower()) for w in ["beach", "beaches", "coast", "coastal", "seashore", "oceanfront"])
                or "beaches" in [t.lower() for t in p.get("tags", [])]
                for p in combined_places
            )
            if not has_actual_beach or cnt < 1 or sc < 2:
                continue

        if pid == "nightlife":
            has_actual_nightlife = any(
                any(w in f"{p.get('name', '')} {p.get('category', '')}".lower() for w in ["nightclub", "club", "bar", "pub", "lounge", "cocktail", "nightlife"])
                or "nightlife" in [t.lower() for t in p.get("tags", [])]
                for p in combined_places
            )
            if not has_actual_nightlife or cnt < 1 or sc < 2:
                continue

        if pid == "spirituality":
            has_actual_spiritual = any(
                any(w in f"{p.get('name', '')} {p.get('category', '')}".lower() for w in ["temple", "church", "cathedral", "monastery", "basilica", "mosque", "ghat", "sacred", "shrine", "spirituality"])
                or "spirituality" in [t.lower() for t in p.get("tags", [])]
                for p in combined_places
            )
            if not has_actual_spiritual or cnt < 1 or sc < 2:
                continue

        # Only include if actual places exist for this category
        if cnt >= 1 and sc >= 2:
            supported_prefs.append({
                "id": stats["id"],
                "label": stats["label"],
                "emoji": stats["emoji"],
                "description": stats["description"],
                "count": stats["count"],
                "score": stats["score"],
                "sample_attractions": stats["sample_attractions"],
            })

    # Sort supported preferences by relevance (score descending, then count descending)
    supported_prefs.sort(key=lambda x: (x["score"], x["count"]), reverse=True)

    # If places exist but none reached strict threshold, provide baseline categories
    if not supported_prefs and combined_places:
        for pref in PREFERENCE_CATEGORIES:
            if pref["id"] in ["culture", "food", "nature", "photography", "relaxation"]:
                supported_prefs.append({
                    "id": pref["id"],
                    "label": pref["label"],
                    "emoji": pref["emoji"],
                    "description": pref["description"],
                    "count": 1,
                    "score": 1,
                    "sample_attractions": [p.get("name") for p in combined_places[:2]],
                })

    available_preference_labels = [p["label"] for p in supported_prefs]

    result = {
        "destination": clean_dest,
        "available_preferences": available_preference_labels,
        "preferences": supported_prefs,
        "total_attractions": len(combined_places),
        "country": geo_info.get("country", ""),
        "coordinates": {"lat": geo_info.get("lat"), "lon": geo_info.get("lon")} if has_coords else None,
        "supported": len(supported_prefs) > 0,
        "all_categories": [
            {"id": p["id"], "label": p["label"], "emoji": p["emoji"]}
            for p in PREFERENCE_CATEGORIES
        ],
    }

    if not supported_prefs and not combined_places:
        result["message"] = f"No verified tourist activities currently indexed for '{clean_dest}'. You can still create a trip and add custom preferences."

    # Cache result
    _PREFERENCE_CACHE[cache_key] = result
    return result


def clear_preferences_cache() -> None:
    """Clears the in-memory preference cache."""
    _PREFERENCE_CACHE.clear()
