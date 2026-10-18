"""Destination catalogue: seed + list."""
from sqlalchemy.orm import Session

from app.models.destination import Destination

DESTINATIONS = [
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
    "adventure": ["adventure", "hiking", "trekking", "outdoors", "sports", "trails", "active", "wildlife", "rafting", "climbing", "excursions"],
    "culture": ["culture", "history", "temples", "museums", "heritage", "landmarks", "ancient", "art", "architecture", "historic", "monuments"],
    "food": ["food", "culinary", "dining", "restaurants", "street food", "cafes", "gastronomy", "tasting", "local flavors", "sushi", "tapas"],
    "relaxation": ["relaxation", "beaches", "peaceful", "spa", "resort", "retreats", "lagoons", "wellness", "laid-back", "sunsets", "calm", "serene"],
    "beaches": ["beaches", "coastal", "islands", "lagoons", "ocean", "sea", "sand", "water sports"],
    "shopping": ["shopping", "markets", "fashion", "boutiques", "bazaars", "souvenirs"],
    "nightlife": ["nightlife", "bars", "clubs", "evening", "party", "cocktails"],
    "photography": ["photography", "scenic", "viewpoints", "sunsets", "panoramic", "landscape", "iconic", "photogenic"],
    "spirituality": ["spirituality", "temples", "meditation", "peaceful", "sacred", "shrines", "monasteries"],
    "family": ["family", "family-friendly", "kids", "parks", "safe", "all-ages"],
}

# Expanded world destinations for varied preference profiles
ADDITIONAL_DESTINATIONS = [
    {
        "id": "banff", "name": "Banff", "country": "Canada",
        "image_url": "/images/alps.jpg",
        "tags": ["nature", "adventure", "photography"],
        "styles": ["Comfort", "Luxury"],
        "paces": ["Balanced", "Packed"],
        "price": "$1,700",
        "base_usd": 1700,
        "rating": 4.9,
        "blurb": "Soaring Rocky Mountain peaks, turquoise glacial lakes, and world-class alpine trekking.",
    },
    {
        "id": "kyoto", "name": "Kyoto", "country": "Japan",
        "image_url": "/images/tokyo.jpg",
        "tags": ["culture", "spirituality", "food", "photography"],
        "styles": ["Comfort", "Luxury"],
        "paces": ["Relaxed", "Balanced"],
        "price": "$1,600",
        "base_usd": 1600,
        "rating": 4.9,
        "blurb": "Historic Shinto shrines, serene bamboo groves, traditional tea ceremonies, and culinary artistry.",
    },
    {
        "id": "rome", "name": "Rome", "country": "Italy",
        "image_url": "/images/paris.jpg",
        "tags": ["culture", "food", "photography"],
        "styles": ["Budget", "Comfort"],
        "paces": ["Balanced", "Packed"],
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
        "paces": ["Packed", "Balanced"],
        "price": "$2,100",
        "base_usd": 2100,
        "rating": 4.9,
        "blurb": "Alpine fjord exploration, exhilarating outdoor sports, mountain hikes, and tranquil lake vistas.",
    },
    {
        "id": "costa-rica", "name": "Costa Rica", "country": "Central America",
        "image_url": "/images/bali.jpg",
        "tags": ["nature", "adventure", "family", "relaxation"],
        "styles": ["Budget", "Comfort"],
        "paces": ["Relaxed", "Balanced"],
        "price": "$1,300",
        "base_usd": 1300,
        "rating": 4.8,
        "blurb": "Pristine rainforest biodiversity, volcanic hot springs, canopy ziplines, and eco-retreats.",
    },
]


def recommend_destinations(
    db: Session,
    interests: list[str] = None,
    destination_query: str = None,
    budget: int = None,
    travelers: int = 1,
    start_date: str = None,
    end_date: str = None,
    special_requests: str = None,
    style: str = None,
    pace: str = None,
) -> list[dict]:
    """Generates personalized destination recommendations reflecting user preferences,
    budget, duration, travelers, and free-text destination search."""
    from app.services.image_service import resolve as resolve_image

    interests = [i.lower().strip() for i in (interests or []) if i]
    dest_query = (destination_query or "").strip().lower()

    # Collect all base destinations
    candidates = []
    db_destinations = db.query(Destination).all()
    for d in db_destinations:
        try:
            raw_usd = int("".join(c for c in (d.price_label or "") if c.isdigit())) or 1200
        except ValueError:
            raw_usd = 1200
        candidates.append({
            "id": d.slug,
            "name": d.name,
            "country": d.country,
            "image_url": d.image_url,
            "tags": d.tags or [],
            "styles": d.styles or [],
            "paces": d.paces or [],
            "price": d.price_label,
            "base_usd": raw_usd,
            "rating": 4.7,
            "blurb": d.blurb,
        })

    # Include additional world destinations
    existing_ids = {c["id"] for c in candidates}
    for extra in ADDITIONAL_DESTINATIONS:
        if extra["id"] not in existing_ids:
            candidates.append(dict(extra))

    # Dynamic Destination: If user searched a destination not yet in candidates
    exact_match = None
    if dest_query:
        exact_match = next((c for c in candidates if dest_query in c["name"].lower() or c["name"].lower() in dest_query or dest_query in c["country"].lower()), None)
        if not exact_match and len(dest_query) >= 2:
            resolved_img = resolve_image(db, destination_query, allow_remote=True)
            img_url = resolved_img.get("url") or "/images/hero.jpg"
            title_name = destination_query.title()
            
            # Infer matching tags from user interests
            derived_tags = list(interests) if interests else ["culture", "sightseeing"]
            custom_blurb = f"Discover the iconic sights, local culture, and memorable experiences of {title_name}."
            if "adventure" in interests or "nature" in interests:
                custom_blurb = f"Explore scenic landscapes, outdoor trails, and natural wonders across {title_name}."
            elif "food" in interests:
                custom_blurb = f"Immerse yourself in authentic culinary traditions and vibrant local markets in {title_name}."
            elif "relaxation" in interests:
                custom_blurb = f"Unwind with scenic retreats, peaceful stays, and serene environments in {title_name}."

            custom_candidate = {
                "id": destination_query.lower().replace(" ", "-"),
                "name": title_name,
                "country": "International",
                "image_url": img_url,
                "tags": derived_tags,
                "styles": ["Comfort", "Luxury"],
                "paces": ["Balanced"],
                "price": f"${budget or 1500:,}",
                "base_usd": budget or 1500,
                "rating": 4.8,
                "blurb": custom_blurb,
                "is_custom": True,
            }
            candidates.insert(0, custom_candidate)

    # Multi-factor scoring for each candidate
    scored = []
    for c in candidates:
        score = 50
        reasons = []

        c_tags = [t.lower() for t in c.get("tags", [])]
        blurb_lower = (c.get("blurb") or "").lower()

        # 1. User Selected Interests & Semantic Matching
        matched_interests = []
        for interest in interests:
            keywords = INTEREST_KEYWORDS.get(interest, [interest])
            tag_hit = any(k in c_tags for k in keywords)
            text_hit = any(k in blurb_lower for k in keywords)

            if tag_hit or text_hit:
                score += 20
                matched_interests.append(interest.title())

        if matched_interests:
            reasons.append(f"Matches your {', '.join(matched_interests[:3])} travel preference{'s' if len(matched_interests) > 1 else ''}.")

        # 2. Specific prompt examples prioritization
        # Nature + Adventure -> prioritize mountains, trekking, forests, outdoors
        if "nature" in interests and "adventure" in interests:
            if any(k in blurb_lower or k in c_tags for k in ["mountain", "alps", "trekking", "forest", "hiking", "rocky", "outdoor"]):
                score += 25
                reasons.append("Prioritized for alpine mountains, trekking trails, and outdoor adventures.")

        # Culture + History -> prioritize heritage, temples, historic cities
        if "culture" in interests or "history" in interests:
            if any(k in blurb_lower or k in c_tags for k in ["temple", "museum", "historic", "heritage", "colosseum", "shrine", "ancient"]):
                score += 20
                reasons.append("Features historic heritage sites, museums, and architecture.")

        # Food -> prioritize culinary experiences
        if "food" in interests:
            if any(k in blurb_lower or k in c_tags for k in ["food", "culinary", "sushi", "street food", "trattoria", "tapas", "shacks"]):
                score += 20
                reasons.append("Celebrated for its distinct culinary culture and food scenes.")

        # Relaxation -> prioritize beaches, retreats, spas, scenic stays
        if "relaxation" in interests or "beaches" in interests:
            if any(k in blurb_lower or k in c_tags for k in ["beach", "villa", "lagoon", "hot spring", "spa", "laid-back", "sunset"]):
                score += 20
                reasons.append("Ideal for peaceful retreats, beaches, and scenic stays.")

        # 3. Budget Fit
        if budget:
            diff = abs(c.get("base_usd", 1200) - budget)
            if c.get("base_usd", 1200) <= budget:
                score += 15
                reasons.append(f"Fits within your ${budget:,} budget.")
            elif diff < 400:
                score += 8

        # 4. Destination Query Boost
        if dest_query:
            if dest_query in c["name"].lower() or dest_query in c["country"].lower():
                score += 50
                reasons.insert(0, f"Direct match for your search '{destination_query}'.")
            elif c.get("is_custom"):
                score += 60
                reasons.insert(0, f"Custom curated plan for '{c['name']}'.")

        # 5. Travel Style and Pace
        if style and style in c.get("styles", []):
            score += 10
        if pace and pace in c.get("paces", []):
            score += 10

        # Bound score between 55 and 99
        match_score = min(99, max(55, score))
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
            "match_score": match_score,
            "match_reasons": reasons[:2],
        })

    # Sort descending by match score
    scored.sort(key=lambda x: -x["match_score"])
    return scored
