"""Destination catalogue: seed + list."""
from typing import Any
from sqlalchemy.orm import Session

from app.api_clients.currency import CURRENCY_SYMBOLS, currency_client
from app.models.destination import Destination

DESTINATIONS: list[dict[str, Any]] = [
    {
        "slug": "bali", "name": "Bali", "country": "Indonesia",
        "image_url": "/images/bali.jpg",
        "tags": ["beaches", "nature", "culture", "food"],
        "styles": ["Budget", "Comfort", "Luxury"],
        "paces": ["Relaxed", "Balanced"],
        "price_label": "$1,100",
        "blurb": "Island temples, rice terraces and golden beaches.",
    },
    {
        "slug": "maldives", "name": "Maldives", "country": "Indian Ocean",
        "image_url": "/images/maldives.jpg",
        "tags": ["beaches"],
        "styles": ["Comfort", "Luxury"],
        "paces": ["Relaxed"],
        "price_label": "$2,400",
        "blurb": "Overwater villas and endless turquoise lagoons.",
    },
    {
        "slug": "thailand", "name": "Thailand", "country": "Southeast Asia",
        "image_url": "/images/thailand.jpg",
        "tags": ["food", "adventure", "beaches", "nightlife", "culture"],
        "styles": ["Budget", "Comfort"],
        "paces": ["Balanced", "Packed"],
        "price_label": "$900",
        "blurb": "Street food, temples and island hopping.",
    },
    {
        "slug": "paris", "name": "Paris", "country": "France",
        "image_url": "/images/paris.jpg",
        "tags": ["culture", "food", "shopping"],
        "styles": ["Comfort", "Luxury"],
        "paces": ["Balanced", "Packed"],
        "price_label": "$1,600",
        "blurb": "Museums, cafés and iconic landmarks.",
    },
    {
        "slug": "tokyo", "name": "Tokyo", "country": "Japan",
        "image_url": "/images/tokyo.jpg",
        "tags": ["food", "shopping", "nightlife", "culture"],
        "styles": ["Budget", "Comfort", "Luxury"],
        "paces": ["Balanced", "Packed"],
        "price_label": "$1,800",
        "blurb": "Neon nights, sushi and endless discovery.",
    },
    {
        "slug": "alps", "name": "Swiss Alps", "country": "Switzerland",
        "image_url": "/images/alps.jpg",
        "tags": ["adventure", "nature"],
        "styles": ["Comfort", "Luxury"],
        "paces": ["Relaxed", "Balanced"],
        "price_label": "$2,000",
        "blurb": "Alpine peaks, trails and cozy villages.",
    },
    {
        "slug": "goa", "name": "Goa", "country": "India",
        "image_url": "/images/goa.jpg",
        "tags": ["beaches", "nightlife", "food"],
        "styles": ["Budget", "Comfort"],
        "paces": ["Relaxed", "Balanced"],
        "price_label": "$500",
        "blurb": "Beach shacks, sunsets and laid-back vibes.",
    },
    {
        "slug": "london", "name": "London", "country": "United Kingdom",
        "image_url": "/images/london.jpg",
        "tags": ["culture", "history", "food", "shopping", "nightlife"],
        "styles": ["Comfort", "Luxury", "Budget"],
        "paces": ["Balanced", "Packed"],
        "price_label": "$1,700",
        "blurb": "Historic palaces, West End theaters, world-class museums, and royal parks.",
    },
]


def seed_destinations(db: Session) -> int:
    """Insert the catalogue if the table is empty. Returns rows created."""
    if db.query(Destination).count() > 0:
        return 0
    created = 0
    for d in DESTINATIONS:
        db.add(Destination(**d))
        created += 1
    db.commit()
    return created


def list_destinations(db: Session) -> list[dict]:
    rows = db.query(Destination).order_by(Destination.name).all()
    return [
        {
            "id": d.slug,
            "name": d.name,
            "country": d.country,
            "image_url": d.image_url,
            "tags": d.tags,
            "styles": d.styles,
            "paces": d.paces,
            "price": d.price_label,
            "blurb": d.blurb,
        }
        for d in rows
    ]


# Semantic keyword expansion mapping for user preferences
INTEREST_KEYWORDS = {
    "nature": ["nature", "mountains", "forests", "wildlife", "outdoors", "scenic", "trekking", "alpine", "valleys", "lakes", "park", "flora"],
    "adventure": ["adventure", "hiking", "trekking", "outdoors", "sports", "trails", "active", "wildlife", "rafting", "climbing", "excursions", "paragliding"],
    "culture": ["culture", "history", "temples", "museums", "heritage", "landmarks", "ancient", "art", "architecture", "historic", "monuments"],
    "history": ["history", "historic", "heritage", "ancient", "forts", "palaces", "monuments", "museums", "archaeological", "antiquities", "ruins"],
    "food": ["food", "culinary", "dining", "restaurants", "street food", "cafes", "gastronomy", "tasting", "local flavors", "sushi", "tapas", "ramen"],
    "relaxation": ["relaxation", "beaches", "peaceful", "spa", "resort", "retreats", "lagoons", "wellness", "laid-back", "sunsets", "calm", "serene"],
    "beaches": ["beaches", "coastal", "islands", "lagoons", "ocean", "sea", "sand", "water sports"],
    "shopping": ["shopping", "markets", "fashion", "boutiques", "bazaars", "souvenirs"],
    "nightlife": ["nightlife", "bars", "clubs", "evening", "party", "cocktails"],
    "photography": ["photography", "scenic", "viewpoints", "sunsets", "panoramic", "landscape", "iconic", "photogenic", "skyline", "neon", "nightscape", "crossing"],
    "spirituality": ["spirituality", "temples", "meditation", "peaceful", "sacred", "shrines", "monasteries"],
    "family": ["family", "family-friendly", "kids", "parks", "safe", "all-ages"],
}

# Expanded world destinations for varied preference profiles
ADDITIONAL_DESTINATIONS: list[dict[str, Any]] = [
    {
        "id": "manali", "name": "Manali", "country": "India",
        "image_url": "/images/alps.jpg",
        "tags": ["nature", "adventure", "photography", "relaxation"],
        "styles": ["Backpacker", "Budget", "Comfort"],
        "paces": ["Fast-paced", "Packed", "Balanced", "Moderate"],
        "price": "$450",
        "base_usd": 450,
        "rating": 4.9,
        "blurb": "Towering Himalayan peaks, Solang Valley adventure sports, Rohtang Pass, and scenic pine-forested trails.",
    },
    {
        "id": "jaipur", "name": "Jaipur", "country": "India",
        "image_url": "/images/hero.jpg",
        "tags": ["history", "culture", "photography", "food", "shopping"],
        "styles": ["Budget", "Comfort", "Luxury"],
        "paces": ["Moderate", "Balanced", "Relaxed"],
        "price": "$550",
        "base_usd": 550,
        "rating": 4.9,
        "blurb": "The historic Pink City, famed for majestic hill forts (Amber, Nahargarh), City Palace, royal Rajasthani culinary feasts, and vibrant artisan bazaars.",
    },
    {
        "id": "banff", "name": "Banff", "country": "Canada",
        "image_url": "/images/alps.jpg",
        "tags": ["nature", "adventure", "photography"],
        "styles": ["Comfort", "Luxury"],
        "paces": ["Fast-paced", "Balanced", "Packed", "Moderate"],
        "price": "$1,700",
        "base_usd": 1700,
        "rating": 4.9,
        "blurb": "Soaring Rocky Mountain peaks, turquoise glacial lakes, and world-class alpine wilderness trekking.",
    },
    {
        "id": "kyoto", "name": "Kyoto", "country": "Japan",
        "image_url": "/images/tokyo.jpg",
        "tags": ["culture", "history", "spirituality", "food", "photography"],
        "styles": ["Comfort", "Luxury"],
        "paces": ["Relaxed", "Balanced", "Moderate"],
        "price": "$1,600",
        "base_usd": 1600,
        "rating": 4.9,
        "blurb": "Historic Shinto shrines, serene bamboo groves, traditional tea ceremonies, and culinary artistry.",
    },
    {
        "id": "rome", "name": "Rome", "country": "Italy",
        "image_url": "/images/paris.jpg",
        "tags": ["history", "culture", "food", "photography"],
        "styles": ["Budget", "Comfort", "Luxury"],
        "paces": ["Balanced", "Packed", "Moderate"],
        "price": "$1,500",
        "base_usd": 1500,
        "rating": 4.8,
        "blurb": "The Colosseum, Vatican museums, historic cobblestone piazzas, and authentic trattoria dining.",
    },
    {
        "id": "queenstown", "name": "Queenstown", "country": "New Zealand",
        "image_url": "/images/alps.jpg",
        "tags": ["adventure", "nature", "photography"],
        "styles": ["Comfort", "Luxury"],
        "paces": ["Fast-paced", "Packed", "Balanced", "Moderate"],
        "price": "$2,100",
        "base_usd": 2100,
        "rating": 4.9,
        "blurb": "Alpine fjord exploration, exhilarating outdoor sports, mountain hikes, and tranquil lake vistas.",
    },
    {
        "id": "costa-rica", "name": "Costa Rica", "country": "Central America",
        "image_url": "/images/bali.jpg",
        "tags": ["nature", "adventure", "family", "relaxation"],
        "styles": ["Backpacker", "Budget", "Comfort"],
        "paces": ["Relaxed", "Balanced", "Moderate"],
        "price": "$1,300",
        "base_usd": 1300,
        "rating": 4.8,
        "blurb": "Pristine rainforest biodiversity, volcanic hot springs, canopy ziplines, and eco-retreats.",
    },
]


def recommend_destinations(
    db: Session,
    interests: list[str] | None = None,
    destination_query: str | None = None,
    budget: int | None = None,
    travelers: int = 1,
    start_date: str | None = None,
    end_date: str | None = None,
    special_requests: str | None = None,
    style: str | None = None,
    pace: str | None = None,
    currency: str | None = None,
) -> list[dict]:
    """Generates personalized destination recommendations reflecting user preferences,
    budget, duration, travelers, and free-text destination search."""
    from app.services.image_service import resolve as resolve_image

    interests = [i.lower().strip() for i in (interests or []) if i]
    dest_query = (destination_query or "").strip().lower()
    target_currency = (currency or "USD").upper()
    curr_sym = CURRENCY_SYMBOLS.get(target_currency, "$")

    # Collect all base destinations
    candidates = []
    db_destinations = db.query(Destination).all()
    for d in db_destinations:
        try:
            raw_usd = int("".join(c for c in (d.price_label or "") if c.isdigit())) or 1200
        except ValueError:
            raw_usd = 1200
        conv = currency_client.convert(raw_usd, "USD", target_currency)
        candidates.append({
            "id": d.slug,
            "name": d.name,
            "country": d.country,
            "image_url": d.image_url,
            "tags": d.tags or [],
            "styles": d.styles or [],
            "paces": d.paces or [],
            "price": f"{curr_sym}{conv['converted_amount']:,}",
            "base_usd": raw_usd,
            "converted_cost": conv["converted_amount"],
            "currency": target_currency,
            "rating": 4.7,
            "blurb": d.blurb,
        })

    # Include additional world destinations
    existing_ids = {c["id"] for c in candidates}
    for extra in ADDITIONAL_DESTINATIONS:
        if extra["id"] not in existing_ids:
            c_copy = dict(extra)
            val = c_copy.get("base_usd")
            raw_usd = int(val) if isinstance(val, (int, float, str)) else 1200
            conv = currency_client.convert(raw_usd, "USD", target_currency)
            c_copy["price"] = f"{curr_sym}{conv['converted_amount']:,}"
            c_copy["converted_cost"] = conv["converted_amount"]
            c_copy["currency"] = target_currency
            candidates.append(c_copy)

    # Dynamic Destination: If user searched a destination not yet in candidates
    exact_match = None
    clean_dest = (destination_query or "").strip()
    if clean_dest:
        dest_query = clean_dest.lower()
        exact_match = next((c for c in candidates if dest_query in c["name"].lower() or c["name"].lower() in dest_query or dest_query in c["country"].lower()), None)
        if not exact_match and len(dest_query) >= 2:
            resolved_img = resolve_image(db, clean_dest, allow_remote=True)
            img_url = resolved_img.get("url") or "/images/hero.jpg"
            title_name = clean_dest.title()
            
            # Geocode to retrieve real country and location
            from app.api_clients.geoapify import geoapify_client
            geo_info = geoapify_client.geocode(clean_dest)
            dest_country = (geo_info.get("country") if geo_info else None) or "Global Destination"

            # Infer matching tags from user interests
            derived_tags = list(interests) if interests else ["culture", "sightseeing"]
            custom_blurb = f"Discover the iconic sights, local culture, and memorable experiences of {title_name}."
            if "adventure" in interests or "nature" in interests:
                custom_blurb = f"Explore scenic landscapes, outdoor trails, and natural wonders across {title_name}."
            elif "food" in interests:
                custom_blurb = f"Immerse yourself in authentic culinary traditions and vibrant local markets in {title_name}."
            elif "relaxation" in interests:
                custom_blurb = f"Unwind with scenic retreats, peaceful stays, and serene environments in {title_name}."

            conv_b = currency_client.convert(budget or 1500, target_currency, "USD")["converted_amount"] if budget else 1500
            custom_candidate = {
                "id": clean_dest.lower().replace(" ", "-"),
                "name": title_name,
                "country": dest_country,
                "image_url": img_url,
                "tags": derived_tags,
                "styles": ["Comfort", "Luxury"],
                "paces": ["Balanced"],
                "price": f"{curr_sym}{budget:,}" if budget else f"{curr_sym}{currency_client.convert(1500, 'USD', target_currency)['converted_amount']:,}",
                "base_usd": conv_b,
                "converted_cost": budget or currency_client.convert(1500, "USD", target_currency)["converted_amount"],
                "currency": target_currency,
                "rating": 4.8,
                "blurb": custom_blurb,
                "is_custom": True,
            }
            candidates.insert(0, custom_candidate)

    # Multi-factor scoring for each candidate
    scored = []
    pace_lower = (pace or "").lower().strip()
    style_lower = (style or "").lower().strip()

    for c in candidates:
        raw_score = 40
        reasons = []

        c_tags = [t.lower() for t in c.get("tags", [])]
        blurb_lower = (c.get("blurb") or "").lower()
        c_name_lower = (c.get("name") or "").lower()
        combined_text = f"{c_name_lower} {blurb_lower} {' '.join(c_tags)}"

        # 1. Exact Tag Matches & Semantic Matching
        matched_interests = []
        for interest in interests:
            keywords = INTEREST_KEYWORDS.get(interest, [interest])
            if interest in c_tags:
                raw_score += 28
                matched_interests.append(interest.title())
            elif any(k in c_tags for k in keywords):
                raw_score += 20
                matched_interests.append(interest.title())
            elif any(k in blurb_lower for k in keywords):
                raw_score += 12
                matched_interests.append(interest.title())

        # 2. Synergy Combinations from Requirements
        # Nature + Adventure -> mountains, trekking destinations, outdoor activities
        if "nature" in interests and "adventure" in interests:
            if "nature" in c_tags and "adventure" in c_tags:
                raw_score += 45
            if any(k in combined_text for k in ["mountain", "himalayan", "alps", "trekking", "forest", "hiking", "rocky", "outdoor", "pass", "peak", "valley"]):
                raw_score += 35
                reasons.append("Top recommendation for Nature & Adventure with mountain trekking trails, alpine peaks, and outdoor experiences.")

        # History + Culture -> heritage cities, historical monuments, museums, royal palaces
        if "history" in interests or "culture" in interests:
            if "history" in c_tags and "culture" in c_tags:
                raw_score += 45
                reasons.append("Top recommendation for History & Culture featuring royal palaces, UNESCO heritage forts, and historic monuments.")
            elif "history" in c_tags:
                raw_score += 35
                reasons.append("Rich in storied historical landmarks, ancient forts, and heritage sites.")
            elif "culture" in c_tags and any(k in combined_text for k in ["fort", "palace", "museum", "historic", "heritage", "ancient", "shrine"]):
                raw_score += 25
                reasons.append("Renowned for cultural heritage, museums, and historic architecture.")

        # Beaches + Relaxation -> coastal destinations, islands, peaceful beach locations
        if "beaches" in interests or "relaxation" in interests:
            is_beach_relax = ("beaches" in c_tags or "beach" in combined_text) and (
                "relaxation" in c_tags or any(k in combined_text for k in ["laid-back", "sunset", "spa", "retreat", "cove", "peaceful", "calm", "lagoons", "villas", "shacks"])
            )
            if is_beach_relax:
                raw_score += 48
                reasons.append("Top recommendation for Beaches & Relaxation featuring peaceful coastal coves, soft sands, and serene ocean views.")
            elif "beaches" in c_tags:
                raw_score += 28
                reasons.append("Famous coastal destination with golden beaches and seaside atmosphere.")
            elif "relaxation" in c_tags:
                raw_score += 28
                reasons.append("Ideal for peaceful wellness retreats and restorative stays.")

        # Food + Photography or Food + Culture -> culinary markets, signature cuisine, photogenic streets
        if "food" in interests and "photography" in interests:
            has_food = "food" in c_tags or any(k in combined_text for k in ["sushi", "ramen", "street food", "market", "culinary"])
            has_photo = "photography" in c_tags or any(k in combined_text for k in ["neon", "viewpoint", "panoramic", "photogenic", "skyline", "scenic", "crossing", "nightscape"])
            if has_food and has_photo:
                raw_score += 55
                reasons.append("Top recommendation for Food & Photography with world-class culinary markets and photogenic streetscapes.")
            if any(k in combined_text for k in ["sushi", "ramen", "street food", "market", "culinary", "gastronomy", "feasts"]):
                raw_score += 25
            if any(k in combined_text for k in ["neon", "viewpoint", "panoramic", "photogenic", "skyline", "scenic", "shinjuku", "shibuya"]):
                raw_score += 25
        elif "food" in interests:
            if "food" in c_tags:
                raw_score += 28
                reasons.append("Celebrated for its distinct culinary culture, street markets, and authentic gastronomy.")
        elif "photography" in interests:
            if "photography" in c_tags:
                raw_score += 28
                reasons.append("Features iconic compositions, panoramic viewpoints, and golden-hour vistas.")

        if matched_interests and not reasons:
            reasons.append(f"Matches your {', '.join(matched_interests[:3])} travel preference{'s' if len(matched_interests) > 1 else ''}.")

        # 3. Travel Pace Matching
        c_paces = [p.lower() for p in c.get("paces", [])]
        if pace_lower:
            if pace_lower in ["fast-paced", "fast", "packed"]:
                if any(p in c_paces for p in ["fast-paced", "packed"]):
                    raw_score += 20
                    reasons.append("Matches your fast-paced tempo with active exploration schedules.")
                elif any(p in c_paces for p in ["balanced", "moderate"]):
                    raw_score += 8
            elif pace_lower in ["moderate", "balanced"]:
                if any(p in c_paces for p in ["moderate", "balanced"]):
                    raw_score += 20
                    reasons.append("Matches your moderate, balanced sightseeing pace.")
            elif pace_lower in ["relaxed", "slow"]:
                if any(p in c_paces for p in ["relaxed"]):
                    raw_score += 22
                    reasons.append("Matches your relaxed pace with plenty of downtime and unhurried leisure.")

        # 4. Travel Style Matching
        c_styles = [s.lower() for s in c.get("styles", [])]
        if style_lower:
            if style_lower in ["backpacker", "backpacking"]:
                if any(s in c_styles for s in ["backpacker", "budget"]):
                    raw_score += 18
                    reasons.append("Great for backpackers with affordable local transit, social stays, and self-guided trails.")
            elif style_lower in ["budget"]:
                if "budget" in c_styles:
                    raw_score += 18
                    reasons.append("Excellent value destination matching your budget preference.")
            elif style_lower in ["comfort"]:
                if "comfort" in c_styles:
                    raw_score += 15
                    reasons.append("Offers boutique accommodation and comfortable transport.")
            elif style_lower in ["luxury"]:
                if "luxury" in c_styles:
                    raw_score += 18
                    reasons.append("Features premium luxury resorts, fine dining, and bespoke private experiences.")

        # 5. Budget Fit
        if budget:
            raw_base = c.get("base_usd")
            base_usd = int(raw_base) if isinstance(raw_base, (int, float, str)) else 1200
            c_cost = c.get("converted_cost") or currency_client.convert(base_usd, "USD", target_currency)["converted_amount"]
            diff = abs(c_cost - budget)
            if c_cost <= budget:
                raw_score += 12
                reasons.append("Fits within your budget estimate.")
            elif diff < (budget * 0.3):
                raw_score += 6

        # 6. Destination Query Boost (if explicitly searched)
        if dest_query:
            if dest_query in c_name_lower or dest_query in c.get("country", "").lower():
                raw_score += 100
                reasons.insert(0, f"Direct match for your requested destination '{c['name']}'.")
            elif c.get("is_custom"):
                raw_score += 100
                reasons.insert(0, f"Custom curated plan for '{c['name']}'.")

        if not reasons:
            reasons.append("Top-rated destination with high traveler satisfaction.")

        scored.append({
            "id": c["id"],
            "name": c["name"],
            "country": c["country"],
            "image_url": c["image_url"],
            "tags": c.get("tags", []),
            "styles": c.get("styles", []),
            "paces": c.get("paces", []),
            "price": c.get("price", "$1,200"),
            "rating": c.get("rating", 4.7),
            "blurb": c.get("blurb", ""),
            "raw_score": raw_score,
            "match_reasons": reasons[:2],
        })

    # Sort descending by raw_score, then rating
    scored.sort(key=lambda x: (-x["raw_score"], -x.get("rating", 4.5)))

    # Compute scaled match_score based on relative rank
    highest_score = scored[0]["raw_score"] if scored else 100
    for i, item in enumerate(scored):
        if highest_score > 60:
            ratio = item["raw_score"] / highest_score
            scaled = int(58 + ratio * 41)
            # Ensure top item is 98-99 and monotonic descent
            item["match_score"] = min(99, max(55, scaled))
        else:
            item["match_score"] = max(55, 90 - (i * 4))

    return scored
