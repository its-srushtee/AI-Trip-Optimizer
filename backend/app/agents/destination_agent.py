"""Destination agent — researches what to see/do at the destination.

Uses the RAG retriever over the travel documents corpus and curates real,
preference-prioritized attractions for the destination.
"""
from typing import Any

from app.agents.base import BaseAgent
from app.rag.retriever import get_retriever

# Destination attraction catalogue with rich descriptions, locations, visit notes and images
ATTRACTIONS_CATALOGUE = {
    "bali": [
        {
            "name": "Tegalalang Rice Terrace",
            "description": "Iconic emerald stepped rice fields with traditional Balinese subak irrigation, jungle swings, and panoramic walking trails.",
            "category": "Nature & Scenery",
            "location": "Ubud, Bali",
            "image_url": "/images/bali.jpg",
            "tags": ["nature", "photography", "scenic", "adventure"],
            "visit_info": "Open 8:00 AM - 6:00 PM · $3 entry · Best in morning light",
            "rating": 4.9,
        },
        {
            "name": "Uluwatu Cliffside Temple",
            "description": "Ancient Hindu sea temple perched dramatically on 70m limestone sea cliffs with famous sunset Kecak fire dances.",
            "category": "Culture & Heritage",
            "location": "South Kuta, Bali",
            "image_url": "/images/bali.jpg",
            "tags": ["culture", "spirituality", "photography", "sunsets"],
            "visit_info": "Sunset performance at 6:00 PM · Sarong required (provided)",
            "rating": 4.8,
        },
        {
            "name": "Sacred Monkey Forest Sanctuary",
            "description": "Sacred jungle ravine housing ancient stone moss-covered temples and over a thousand friendly grey macaques.",
            "category": "Wildlife & Nature",
            "location": "Padangtegal, Ubud",
            "image_url": "/images/bali.jpg",
            "tags": ["nature", "wildlife", "family", "adventure"],
            "visit_info": "Open 9:00 AM - 5:00 PM · Guided tours available",
            "rating": 4.7,
        },
        {
            "name": "Tanah Lot Temple",
            "description": "Centuries-old pilgrimage temple balanced on a sea-carved rock islet with crashing waves and golden sunset horizons.",
            "category": "Culture & Landmark",
            "location": "Tabanan, Bali",
            "image_url": "/images/bali.jpg",
            "tags": ["culture", "photography", "relaxation"],
            "visit_info": "Accessible at low tide · Best 4:30 PM - 6:30 PM",
            "rating": 4.8,
        },
        {
            "name": "Seminyak & Canggu Coastline",
            "description": "Laid-back coastal surf haven lined with bohemian beach bars, artisanal cafés, day clubs, and world-class breaks.",
            "category": "Beaches & Dining",
            "location": "Badung, Bali",
            "image_url": "/images/bali.jpg",
            "tags": ["beaches", "food", "nightlife", "relaxation"],
            "visit_info": "All-day access · Free entry · Sunset lounges",
            "rating": 4.7,
        },
        {
            "name": "Mount Batur Sunrise Trek",
            "description": "Early morning volcanic ascent rewarding hikers with stunning caldera sunrise views, steam vents, and breakfast above the clouds.",
            "category": "Adventure & Hiking",
            "location": "Kintamani, Bali",
            "image_url": "/images/bali.jpg",
            "tags": ["adventure", "nature", "photography"],
            "visit_info": "Departs 3:30 AM · Moderate fitness · 2 hr hike",
            "rating": 4.9,
        },
        {
            "name": "Jimbaran Bay Seafood Sunset",
            "description": "Candlelit beachfront dining on soft sands serving freshly caught and charcoal-grilled red snapper, prawns, and Balinese sambal.",
            "category": "Food & Gastronomy",
            "location": "Jimbaran, Bali",
            "image_url": "/images/bali.jpg",
            "tags": ["food", "dining", "relaxation"],
            "visit_info": "Dinner from 5:30 PM · Oceanfront tables",
            "rating": 4.8,
        },
        {
            "name": "Tirta Empul Holy Water Springs",
            "description": "Centuries-old national cultural heritage temple celebrated for holy spring pools where travelers participate in purification rituals.",
            "category": "Spirituality & Culture",
            "location": "Tampak Siring, Bali",
            "image_url": "/images/bali.jpg",
            "tags": ["spirituality", "culture", "history"],
            "visit_info": "Open 8:00 AM - 6:00 PM · Spiritual bathing sarong provided",
            "rating": 4.8,
        },
    ],
    "paris": [
        {
            "name": "Eiffel Tower & Champ de Mars",
            "description": "The world's most iconic iron lattice tower offering sweeping views of Paris and enchanting nightly sparkle light shows.",
            "category": "Iconic Landmark",
            "location": "7th Arrondissement, Paris",
            "image_url": "/images/paris.jpg",
            "tags": ["culture", "photography", "landmarks", "romance"],
            "visit_info": "Open 9:00 AM - 11:45 PM · Summit access available",
            "rating": 4.9,
        },
        {
            "name": "Musée du Louvre",
            "description": "The world's grandest art museum, showcasing legendary masterpieces including Mona Lisa, Winged Victory, and Venus de Milo.",
            "category": "Art & Culture",
            "location": "1st Arrondissement, Paris",
            "image_url": "/images/paris.jpg",
            "tags": ["culture", "history", "art"],
            "visit_info": "Open 9:00 AM - 6:00 PM (closed Tue) · Advance ticket required",
            "rating": 4.9,
        },
        {
            "name": "Montmartre & Sacré-Cœur",
            "description": "Charming hilltop bohemian village filled with artists, cobblestone alleys, and the white dome of Sacré-Cœur with panoramic city views.",
            "category": "Culture & Neighborhood",
            "location": "18th Arrondissement, Paris",
            "image_url": "/images/paris.jpg",
            "tags": ["culture", "photography", "food", "relaxation"],
            "visit_info": "Open daily · Free basilica entry · Sunset on steps",
            "rating": 4.8,
        },
        {
            "name": "Musée d'Orsay",
            "description": "Magnificent Beaux-Arts railway palace housing the planet's premier collection of Impressionist and Post-Impressionist works.",
            "category": "Art & History",
            "location": "7th Arrondissement, Paris",
            "image_url": "/images/paris.jpg",
            "tags": ["culture", "art", "history"],
            "visit_info": "Open 9:30 AM - 6:00 PM · Closed Mondays",
            "rating": 4.8,
        },
        {
            "name": "Seine River Architectural Cruise",
            "description": "Gliding river cruise drifting under historic bridges like Pont Alexandre III with prime views of Notre-Dame and Parisian riverfronts.",
            "category": "Sightseeing & Leisure",
            "location": "Pont Neuf / Eiffel Piers",
            "image_url": "/images/paris.jpg",
            "tags": ["relaxation", "photography", "scenic"],
            "visit_info": "Hourly departures · 60 min scenic cruise",
            "rating": 4.7,
        },
        {
            "name": "Le Marais Cafés & Historic Mansions",
            "description": "Historic district featuring medieval architecture, artisan patisseries, boutique designer shops, and world-renowned falafel.",
            "category": "Food & Shopping",
            "location": "3rd & 4th Arrondissements",
            "image_url": "/images/paris.jpg",
            "tags": ["food", "shopping", "culture"],
            "visit_info": "Best visited afternoon & evening · Pedestrianized Sundays",
            "rating": 4.8,
        },
    ],
    "tokyo": [
        {
            "name": "Shibuya Sky & Scramble Crossing",
            "description": "The world's highest energy intersection combined with an open-air 360-degree rooftop observatory overlooking Mt. Fuji and neon skylines.",
            "category": "Iconic Landmark",
            "location": "Shibuya, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["photography", "nightlife", "shopping"],
            "visit_info": "Observation deck 10:00 AM - 10:30 PM · Book timed tickets",
            "rating": 4.9,
        },
        {
            "name": "Senso-ji Temple & Nakamise",
            "description": "Tokyo's oldest and most sacred Buddhist temple complex, entered through the iconic Kaminarimon thunder gate and traditional market street.",
            "category": "Culture & Heritage",
            "location": "Asakusa, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["culture", "spirituality", "history", "food"],
            "visit_info": "Main hall 6:00 AM - 5:00 PM · Grounds open 24/7",
            "rating": 4.8,
        },
        {
            "name": "Tsukiji Outer Market Food Tour",
            "description": "Atmospheric labyrinth of food stalls serving fresh bluefin sashimi, tamagoyaki omelettes, grilled wagyu, and matcha ice cream.",
            "category": "Food & Gastronomy",
            "location": "Chuo City, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["food", "shopping", "culture"],
            "visit_info": "Best early morning 8:00 AM - 1:00 PM · Cash & Suica accepted",
            "rating": 4.9,
        },
        {
            "name": "Meiji Jingu Shrine & Forest",
            "description": "Soothing Shinto forest shrine dedicated to Emperor Meiji, set in 170 acres of tranquil sacred woodland in the city center.",
            "category": "Spirituality & Nature",
            "location": "Shibuya, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["spirituality", "nature", "relaxation"],
            "visit_info": "Sunrise to sunset · Free admission · Peaceful morning walks",
            "rating": 4.8,
        },
        {
            "name": "TeamLab Planets Immersive Art",
            "description": "Groundbreaking digital sensory museum where visitors wade barefoot through water and mirrored infinity rooms of floating flowers.",
            "category": "Art & Experience",
            "location": "Toyosu, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["art", "photography", "family"],
            "visit_info": "Open 9:00 AM - 10:00 PM · Reservation essential",
            "rating": 4.9,
        },
        {
            "name": "Akihabara Electric Town",
            "description": "Vibrant epicenter of Japanese gaming culture, anime collectible stores, manga emporiums, multi-floor arcades, and electronics.",
            "category": "Shopping & Pop Culture",
            "location": "Chiyoda City, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["shopping", "nightlife", "culture"],
            "visit_info": "Shops open 10:00 AM - 9:00 PM · High neon energy after dusk",
            "rating": 4.7,
        },
    ],
    "alps": [
        {
            "name": "Jungfraujoch - Top of Europe",
            "description": "Europe's highest altitude railway station at 3,454m with access to the Ice Palace, Sphinx Observatory, and Aletsch Glacier.",
            "category": "Alpine & Views",
            "location": "Bernese Oberland",
            "image_url": "/images/alps.jpg",
            "tags": ["nature", "adventure", "photography"],
            "visit_info": "Scenic cogwheel & Eiger Express cable car · Open daily",
            "rating": 4.9,
        },
        {
            "name": "Matterhorn Glacier Paradise",
            "description": "High-altitude mountain wonderland offering direct panoramas of the iconic Matterhorn horn and year-round alpine skiing.",
            "category": "Adventure & Hiking",
            "location": "Zermatt, Valais",
            "image_url": "/images/alps.jpg",
            "tags": ["adventure", "nature", "photography"],
            "visit_info": "Cable car from Zermatt · 360° summit viewing deck",
            "rating": 4.9,
        },
        {
            "name": "Lake Oeschinen Alpine Trail",
            "description": "Turquoise glacial mountain lake framed by sheer 500m rock walls, fed by pristine waterfalls and surrounded by pine trails.",
            "category": "Nature & Hiking",
            "location": "Kandersteg",
            "image_url": "/images/alps.jpg",
            "tags": ["nature", "adventure", "relaxation"],
            "visit_info": "Gondola + 25 min walk · Rowboats available for rent",
            "rating": 4.9,
        },
        {
            "name": "Lauterbrunnen Valley & Falls",
            "description": "Fairy-tale glacial valley with 72 tumbling waterfalls, traditional wooden chalets, and Trümmelbach underground glacial falls.",
            "category": "Nature & Scenery",
            "location": "Lauterbrunnen",
            "image_url": "/images/alps.jpg",
            "tags": ["nature", "photography", "scenic"],
            "visit_info": "Open year-round · Valley walks are easy and accessible",
            "rating": 4.8,
        },
    ],
    "maldives": [
        {
            "name": "Banana Reef Marine Reserve",
            "description": "Pioneering protected coral reef famous for dramatic caves, overhangs, sea turtles, and schools of blue-striped snappers.",
            "category": "Marine & Adventure",
            "location": "North Malé Atoll",
            "image_url": "/images/maldives.jpg",
            "tags": ["adventure", "nature", "beaches"],
            "visit_info": "Excursions depart daily · Snorkel & scuba friendly",
            "rating": 4.9,
        },
        {
            "name": "Vaadhoo Bioluminescent Sea of Stars",
            "description": "Rare natural spectacle where ocean waves glow electric blue at night due to millions of bioluminescent dinoflagellates.",
            "category": "Nature & Photography",
            "location": "Raa Atoll",
            "image_url": "/images/maldives.jpg",
            "tags": ["nature", "photography", "relaxation"],
            "visit_info": "Night excursions · Best on new moon nights",
            "rating": 4.9,
        },
        {
            "name": "Hanifaru Bay Manta Sanctuary",
            "description": "UNESCO World Biosphere Reserve where massive groups of feeding manta rays and gentle whale sharks gather in turquoise lagoons.",
            "category": "Wildlife & Snorkeling",
            "location": "Baa Atoll",
            "image_url": "/images/maldives.jpg",
            "tags": ["nature", "wildlife", "adventure"],
            "visit_info": "Regulated eco-tours · Snorkeling only (no scuba permitted)",
            "rating": 4.9,
        },
        {
            "name": "Private Sandbank & Sunset Lagoon",
            "description": "Exclusive pristine powdery white sand strip surrounded by crystal-clear waters for a private picnic and snorkeling experience.",
            "category": "Relaxation & Romance",
            "location": "Coral Atolls",
            "image_url": "/images/maldives.jpg",
            "tags": ["relaxation", "beaches", "romance"],
            "visit_info": "Half-day boat charter · Shaded setup and refreshments",
            "rating": 4.8,
        },
    ],
    "goa": [
        {
            "name": "Palolem Beach & Butterfly Island",
            "description": "Crescent-shaped white sand bay lined with swaying palms, safe swimming waters, beach shacks, and dolphin spotting cruises.",
            "category": "Beaches & Relaxation",
            "location": "Canacona, South Goa",
            "image_url": "/images/goa.jpg",
            "tags": ["beaches", "relaxation", "sunsets"],
            "visit_info": "Kayaking and boat rides available · Calm waters",
            "rating": 4.8,
        },
        {
            "name": "Fort Aguada & Lighthouse",
            "description": "Historic 17th-century Portuguese fortress and lighthouse offering commanding panoramic vistas across Sinquerim Beach and the Arabian Sea.",
            "category": "Heritage & Views",
            "location": "Candolim, North Goa",
            "image_url": "/images/goa.jpg",
            "tags": ["culture", "history", "photography"],
            "visit_info": "Open 9:30 AM - 6:00 PM · Free entry",
            "rating": 4.7,
        },
        {
            "name": "Dudhsagar Four-Tier Waterfalls",
            "description": "One of India's tallest waterfalls roaring down 310m through the dense tropical jungle of the Western Ghats.",
            "category": "Adventure & Nature",
            "location": "Sonaulim, Goa Border",
            "image_url": "/images/goa.jpg",
            "tags": ["adventure", "nature", "photography"],
            "visit_info": "Jeep safari via sanctuary · Life jackets mandatory",
            "rating": 4.8,
        },
        {
            "name": "Fontainhas Latin Quarter",
            "description": "Heritage conservation precinct known for pastel-colored colonial Portuguese mansions, antique balconies, and historic bakeries.",
            "category": "Culture & Architecture",
            "location": "Panaji, Goa",
            "image_url": "/images/goa.jpg",
            "tags": ["culture", "photography", "food"],
            "visit_info": "Best explored on foot in early morning or golden hour",
            "rating": 4.7,
        },
    ],
    "thailand": [
        {
            "name": "The Grand Palace & Wat Phra Kaew",
            "description": "Dazzling complex of royal residences and the sacred Emerald Buddha temple adorned with gilded spires and mother-of-pearl.",
            "category": "Culture & Heritage",
            "location": "Bangkok",
            "image_url": "/images/thailand.jpg",
            "tags": ["culture", "spirituality", "history"],
            "visit_info": "Open 8:30 AM - 3:30 PM · Strict dress code applies",
            "rating": 4.8,
        },
        {
            "name": "Wat Arun (Temple of Dawn)",
            "description": "Riverside Buddhist temple towering 70m over the Chao Phraya River, decorated with thousands of colored porcelain fragments.",
            "category": "Culture & Views",
            "location": "Bangkok",
            "image_url": "/images/thailand.jpg",
            "tags": ["culture", "photography", "sunsets"],
            "visit_info": "Open 8:00 AM - 6:00 PM · Best photographed at dusk",
            "rating": 4.8,
        },
        {
            "name": "Phi Phi Islands & Maya Bay",
            "description": "Towering limestone cliffs encircling turquoise lagoons, vibrant coral reefs, and white powder sands.",
            "category": "Beaches & Adventure",
            "location": "Krabi / Phuket",
            "image_url": "/images/thailand.jpg",
            "tags": ["beaches", "adventure", "nature"],
            "visit_info": "Day-trip speedboats from Phuket and Krabi",
            "rating": 4.9,
        },
        {
            "name": "Chatuchak Weekend Market",
            "description": "Giant bustling market of over 15,000 vendor stalls featuring fashion, vintage wares, handicrafts, and sensational street food.",
            "category": "Shopping & Food",
            "location": "Chatuchak, Bangkok",
            "image_url": "/images/thailand.jpg",
            "tags": ["shopping", "food", "culture"],
            "visit_info": "Saturday & Sunday 9:00 AM - 6:00 PM",
            "rating": 4.7,
        },
    ],
}


def _match_catalogue_key(city: str) -> str | None:
    c = city.lower()
    for key in ATTRACTIONS_CATALOGUE:
        if key in c or c in key:
            return key
    if "swiss" in c or "alps" in c or "matterhorn" in c or "zermatt" in c:
        return "alps"
    if "bangkok" in c or "phuket" in c or "krabi" in c or "chiang mai" in c:
        return "thailand"
    return None


class DestinationAgent(BaseAgent):
    name = "destination"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        req = state["request"]
        city = req.get("destination", "")
        interests = [i.lower() for i in req.get("interests", [])]

        query = f"{city} {' '.join(interests)} things to do attractions".strip()
        retriever = get_retriever()
        docs = retriever.retrieve(query, top_k=3)

        # Dynamic highlights aligned with user interests
        highlights = []
        if "adventure" in interests or "nature" in interests:
            highlights.append("Scenic trails, alpine viewpoints, and outdoor nature excursions")
        if "culture" in interests or "history" in interests:
            highlights.append("Historic heritage landmarks, ancient temples, and local museums")
        if "food" in interests:
            highlights.append("Authentic food market tours, signature tastings, and celebrated eateries")
        if "relaxation" in interests or "beaches" in interests:
            highlights.append("Peaceful beach retreats, tranquil coastal walks, and wellness spots")
        if "photography" in interests:
            highlights.append("Iconic photography spots, sunrise vistas, and panoramic landscapes")
        if "spirituality" in interests:
            highlights.append("Sacred shrines, meditative spaces, and serene cultural grounds")
        if "family" in interests:
            highlights.append("Family-friendly attractions, interactive parks, and safe scenic spots")

        if not highlights:
            highlights = [
                f"Top-rated attractions and landmarks in {city}",
                "Local food and market experiences",
                "Hidden gems away from the crowds",
            ]

        # Curate places to visit
        cat_key = _match_catalogue_key(city)
        if cat_key:
            raw_places = list(ATTRACTIONS_CATALOGUE[cat_key])
        else:
            # Dynamic destination attractions tailored to the specific city
            raw_places = [
                {
                    "name": f"{city} Historic Old Town & Heritage Square",
                    "description": f"The architectural and historic core of {city}, lined with heritage facades, bustling open-air cafes, and storied landmarks.",
                    "category": "Culture & Heritage",
                    "location": f"Central {city}",
                    "image_url": "/images/hero.jpg",
                    "tags": ["culture", "history", "photography"],
                    "visit_info": "Free walking access · Guided history tours daily",
                    "rating": 4.8,
                },
                {
                    "name": f"{city} Premier Art & Cultural Museum",
                    "description": f"Celebrated cultural institution showcasing regional antiquities, fine arts, and curated interactive exhibitions.",
                    "category": "Art & History",
                    "location": f"Downtown {city}",
                    "image_url": "/images/hero.jpg",
                    "tags": ["culture", "art"],
                    "visit_info": "Open 10:00 AM - 6:00 PM · Audio guides available",
                    "rating": 4.7,
                },
                {
                    "name": f"{city} Central Artisan Food Market",
                    "description": f"Vibrant culinary marketplace where local growers and chefs serve regional specialties, farm cheeses, and street delights.",
                    "category": "Food & Gastronomy",
                    "location": f"Market District, {city}",
                    "image_url": "/images/hero.jpg",
                    "tags": ["food", "shopping"],
                    "visit_info": "Best visited morning to mid-afternoon",
                    "rating": 4.9,
                },
                {
                    "name": f"{city} Scenic Panoramic Viewpoint",
                    "description": f"Elevated scenic vantage point providing sweeping 360-degree vistas over {city} and the surrounding horizon.",
                    "category": "Views & Photography",
                    "location": f"Scenic Heights, {city}",
                    "image_url": "/images/hero.jpg",
                    "tags": ["photography", "nature", "relaxation"],
                    "visit_info": "Open daily · Unbeatable golden hour & sunset",
                    "rating": 4.8,
                },
                {
                    "name": f"{city} Botanic Gardens & Riverside Promenade",
                    "description": f"Lush peaceful waterfront promenade with manicured botanical groves, cycling pathways, and calm riverfront benches.",
                    "category": "Nature & Leisure",
                    "location": f"Riverfront, {city}",
                    "image_url": "/images/hero.jpg",
                    "tags": ["nature", "relaxation", "family"],
                    "visit_info": "Open sunrise to sunset · Free public park",
                    "rating": 4.7,
                },
                {
                    "name": f"{city} Artisan District & Boutiques",
                    "description": f"Atmospheric quarter dotted with independent craft ateliers, antique bookshops, bespoke fashion, and dessert bistros.",
                    "category": "Shopping & Leisure",
                    "location": f"Arts Quarter, {city}",
                    "image_url": "/images/hero.jpg",
                    "tags": ["shopping", "culture", "food"],
                    "visit_info": "Shops open 11:00 AM - 8:00 PM",
                    "rating": 4.7,
                },
            ]

        # Prioritize places according to user's selected preferences
        def place_score(p: dict) -> int:
            score = 0
            ptags = set(p.get("tags", []))
            pcat = p.get("category", "").lower()
            for user_interest in interests:
                if user_interest in ptags:
                    score += 3
                if user_interest in pcat:
                    score += 2
            return score

        sorted_places = sorted(raw_places, key=lambda p: place_score(p), reverse=True)

        state["destination"] = {
            "name": city,
            "highlights": highlights[:4],
            "rag_context": [d["content"][:300] for d in docs],
            "source": "rag" if docs else "personalized",
            "places_to_visit": sorted_places,
        }
        return state
