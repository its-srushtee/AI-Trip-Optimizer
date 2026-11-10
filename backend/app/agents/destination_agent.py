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

# Destination attraction catalogue with rich descriptions, locations, visit notes, durations, and tags
ATTRACTIONS_CATALOGUE = {
    "manali": [
        {
            "name": "Solang Valley Alpine Adventure & High Meadow",
            "description": "Premier high-altitude adventure hub located 14 km from Manali; famous for paragliding, zorbing, quad biking, and winter skiing with panoramic snow-capped mountain views.",
            "category": "Adventure & Outdoors",
            "location": "Solang Valley, Manali",
            "image_url": "/images/alps.jpg",
            "tags": ["adventure", "nature", "photography"],
            "estimated_duration": "4 - 5 hours",
            "visit_info": "Open 9:00 AM - 6:00 PM · Tandem paragliding and ATV rides · Best morning start",
            "rating": 4.9,
        },
        {
            "name": "Rohtang Pass Glacial Panorama",
            "description": "Legendary mountain pass at 3,978m elevation offering dramatic Himalayan glacial landscapes, high-altitude snow treks, and gateway vistas to Lahaul and Spiti valleys.",
            "category": "Nature & Adventure",
            "location": "Rohtang Highway, Manali",
            "image_url": "/images/alps.jpg",
            "tags": ["nature", "adventure", "photography"],
            "estimated_duration": "Full day excursion (6-7 hrs)",
            "visit_info": "Permit required · Warm layers essential · Breathtaking 360 Himalayan peaks",
            "rating": 4.9,
        },
        {
            "name": "Jogini Waterfall & Pine Forest Trail",
            "description": "Scenic pine-forested nature trek starting from Vashisht village leading to a cascading multi-tiered waterfall with serene valley views.",
            "category": "Nature & Hiking",
            "location": "Vashisht, Manali",
            "image_url": "/images/alps.jpg",
            "tags": ["nature", "adventure", "relaxation", "photography"],
            "estimated_duration": "2.5 - 3 hours",
            "visit_info": "Easy-to-moderate walking trail · Free access · Best in morning light",
            "rating": 4.8,
        },
        {
            "name": "Hampta Pass Trek Base & Valley Trail",
            "description": "Breathtaking crossover trail from lush green Kullu Valley pine forests into rugged alpine mountain ridges and rushing glacier streams.",
            "category": "Adventure & Trekking",
            "location": "Prini / Hampta, Manali",
            "image_url": "/images/alps.jpg",
            "tags": ["adventure", "nature"],
            "estimated_duration": "4 - 6 hours",
            "visit_info": "Guided mountain trekking trail · High-altitude alpine scenery",
            "rating": 4.9,
        },
        {
            "name": "Hadimba Devi Pagoda Temple & Cedar Forest",
            "description": "16th-century four-tiered wooden pagoda temple set inside the tranquil Dhungri cedar (deodar) sanctuary with intricately carved timber facades.",
            "category": "History & Culture",
            "location": "Dhungri, Manali",
            "image_url": "/images/hero.jpg",
            "tags": ["history", "culture", "nature"],
            "estimated_duration": "1.5 hours",
            "visit_info": "Open 8:00 AM - 6:00 PM · Sacred wooden architecture built in 1553 AD",
            "rating": 4.8,
        },
        {
            "name": "Manu Temple & Old Manali Village",
            "description": "Historic stone-and-timber village overlooking the Manalsu river, featuring bohemian artisan bakeries, acoustic live music, and scenic cafes.",
            "category": "Culture & Heritage",
            "location": "Old Manali, Manali",
            "image_url": "/images/hero.jpg",
            "tags": ["culture", "history", "food", "relaxation"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Historic cobblestone village · Great local bakeries and live music in evenings",
            "rating": 4.7,
        },
        {
            "name": "Naggar Castle & Roerich Heritage Art Gallery",
            "description": "Ancient timber-and-stone fortress overlooking the Beas valley, celebrated for its Nicholas Roerich Himalayan art gallery and traditional Himachali architecture.",
            "category": "History & Art",
            "location": "Naggar, Kullu Valley",
            "image_url": "/images/hero.jpg",
            "tags": ["history", "culture", "photography"],
            "estimated_duration": "2.5 hours",
            "visit_info": "Open 9:00 AM - 5:30 PM · Medieval Himalayan royal seat with sweeping valley views",
            "rating": 4.8,
        },
        {
            "name": "Vashisht Thermal Springs & Sanctuary",
            "description": "Natural thermal sulfur springs renowned for therapeutic minerals, set beside an ancient stone temple overlooking snow-capped mountain ridges.",
            "category": "Relaxation & Nature",
            "location": "Vashisht Village, Manali",
            "image_url": "/images/hero.jpg",
            "tags": ["relaxation", "nature", "spirituality"],
            "estimated_duration": "1.5 - 2 hours",
            "visit_info": "Natural hot sulfur baths · Ideal post-trek muscle relaxation",
            "rating": 4.7,
        },
        {
            "name": "Old Manali Riverside Food Walk & Bakery Crawl",
            "description": "Riverside culinary trail sampling freshly baked Himachali Siddu with ghee, wood-fired thin crust pizzas, grilled river trout, and mountain herbal infusions.",
            "category": "Food & Gastronomy",
            "location": "Club House Road, Old Manali",
            "image_url": "/images/hero.jpg",
            "tags": ["food", "relaxation"],
            "estimated_duration": "2 hours",
            "visit_info": "Best mid-afternoon to evening · Riverside patio seating with mountain views",
            "rating": 4.8,
        },
    ],
    "jaipur": [
        {
            "name": "Amber Fort & Maota Lake Palace",
            "description": "UNESCO World Heritage hilltop fortress constructed in pink and yellow sandstone, featuring the mirror-studded Sheesh Mahal, Diwan-e-Aam, and panoramic reflections over Maota Lake.",
            "category": "History & Heritage",
            "location": "Amer, Jaipur",
            "image_url": "/images/hero.jpg",
            "tags": ["history", "culture", "photography"],
            "estimated_duration": "3 - 4 hours",
            "visit_info": "Open 8:00 AM - 5:30 PM · Sheesh Mahal mirror palace · Hilltop fort with elephant/jeep access",
            "rating": 4.9,
        },
        {
            "name": "Hawa Mahal (Palace of Winds)",
            "description": "Five-story pink honeycomb facade with 953 intricately carved jharokhas (casements) designed for royal women to observe street processions without being seen.",
            "category": "History & Architecture",
            "location": "Badi Choupad, Walled City, Jaipur",
            "image_url": "/images/hero.jpg",
            "tags": ["history", "culture", "photography"],
            "estimated_duration": "1.5 hours",
            "visit_info": "Open 9:00 AM - 5:00 PM · 953 honeycomb jharokhas · Best photographed in early morning light",
            "rating": 4.8,
        },
        {
            "name": "City Palace & Royal Maharaja Museum",
            "description": "The regal seat of the Maharaja of Jaipur, featuring Mubarak Mahal, Chandra Mahal, royal courtyards, and museum galleries of royal textiles, manuscripts, and weaponry.",
            "category": "Culture & Royal Heritage",
            "location": "Old City, Jaipur",
            "image_url": "/images/hero.jpg",
            "tags": ["culture", "history", "art"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Open 9:30 AM - 5:00 PM · Royal courtyards, textiles, and armory museum",
            "rating": 4.8,
        },
        {
            "name": "Nahargarh Fort Sunset Ramparts",
            "description": "Hilltop ramparts on the Aravalli range delivering breathtaking sunset vistas and night panoramas across the entire pink city grid.",
            "category": "History & Viewpoints",
            "location": "Aravalli Hills, Jaipur",
            "image_url": "/images/hero.jpg",
            "tags": ["history", "photography", "relaxation"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Open 10:00 AM - 5:30 PM · Panoramic 360 sunset vistas over Pink City ramparts",
            "rating": 4.9,
        },
        {
            "name": "Jantar Mantar UNESCO Astronomical Observatory",
            "description": "18th-century UNESCO World Heritage astronomical observatory housing the world's largest stone sundial (Vrihat Samrat Yantra) and precision architectural instruments.",
            "category": "History & Science",
            "location": "Gangori Bazaar, Jaipur",
            "image_url": "/images/hero.jpg",
            "tags": ["history", "culture"],
            "estimated_duration": "1.5 - 2 hours",
            "visit_info": "Open 9:00 AM - 5:00 PM · 19 architectural astronomical instruments built by Sawai Jai Singh II",
            "rating": 4.8,
        },
        {
            "name": "Jal Mahal Water Palace Promenade",
            "description": "Serene 18th-century water palace appearing to float in the center of Man Sagar Lake, beautifully framed by the surrounding Aravalli hills.",
            "category": "Photography & Scenic Views",
            "location": "Amer Road, Jaipur",
            "image_url": "/images/hero.jpg",
            "tags": ["photography", "nature", "relaxation"],
            "estimated_duration": "1 hour",
            "visit_info": "Viewing promenade open all day · Best photographed at dusk when palace lights illuminate",
            "rating": 4.7,
        },
        {
            "name": "Johari Bazaar & Heritage Street Food Trail",
            "description": "Bustling walled city market famous for authentic Pyaaz Kachori at Rawat, royal Ghevar at LMB, creamy kulhad lassi, and vibrant gem bazaars.",
            "category": "Food & Culinary",
            "location": "Johari Bazaar, Pink City",
            "image_url": "/images/hero.jpg",
            "tags": ["food", "culture", "shopping"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Open 10:30 AM - 8:30 PM · Historic food walk with celebrated local sweet shops",
            "rating": 4.8,
        },
        {
            "name": "Chokhi Dhani Ethnic Cultural Village & Royal Feast",
            "description": "Immersive ethnic Rajasthani cultural village with traditional folk dance (Ghoomar, Kalbelia), puppet shows, pottery, and an authentic royal Dal Baati Churma dining feast.",
            "category": "Food & Culture",
            "location": "Tonk Road, Jaipur",
            "image_url": "/images/hero.jpg",
            "tags": ["food", "culture", "family"],
            "estimated_duration": "Evening (3 - 4 hours)",
            "visit_info": "Open 5:00 PM - 11:00 PM · Traditional sit-down multi-course dining and live cultural arts",
            "rating": 4.9,
        },
        {
            "name": "Patrika Gate & Jawahar Circle Garden",
            "description": "Opulently painted circular monument displaying colorful hand-painted murals of Rajasthan's architectural history, temples, and royal lore.",
            "category": "Photography & Art",
            "location": "Malviya Nagar, Jaipur",
            "image_url": "/images/hero.jpg",
            "tags": ["photography", "culture", "relaxation"],
            "estimated_duration": "1.5 hours",
            "visit_info": "Open 24 hours · Extremely photogenic symmetrical pastel archways and landscaped gardens",
            "rating": 4.8,
        },
        {
            "name": "Albert Hall State Museum",
            "description": "The oldest museum in Rajasthan, showcasing Indo-Saracenic royal architecture, Persian carpets, royal antiquities, ivory sculptures, and Egyptian relics.",
            "category": "History & Antiquities",
            "location": "Ram Niwas Garden, Jaipur",
            "image_url": "/images/hero.jpg",
            "tags": ["history", "culture", "art"],
            "estimated_duration": "2 hours",
            "visit_info": "Open 9:00 AM - 5:00 PM (and night viewing 7-10 PM) · Stunning yellow floodlights at night",
            "rating": 4.7,
        },
    ],
    "goa": [
        {
            "name": "Palolem Beach & Butterfly Island Cove",
            "description": "Picturesque crescent-shaped bay in South Goa surrounded by coconut groves, safe swimming waters, dolphin-watching boat trips, and peaceful beach hut stays.",
            "category": "Beaches & Relaxation",
            "location": "Canacona, South Goa",
            "image_url": "/images/goa.jpg",
            "tags": ["beaches", "relaxation", "photography"],
            "estimated_duration": "Half day (3 - 4 hours)",
            "visit_info": "Calm sheltered bay · Kayaking and dolphin boat trips available · Shaded beachfront dining",
            "rating": 4.9,
        },
        {
            "name": "Morjim & Ashwem Quiet Turtle Beaches",
            "description": "Tranquil northern coastline known for Olive Ridley turtle nesting grounds, serene beach beds, shallow swimming waters, and uncrowded sunsets.",
            "category": "Beaches & Relaxation",
            "location": "Pernem, North Goa",
            "image_url": "/images/goa.jpg",
            "tags": ["beaches", "relaxation", "nature"],
            "estimated_duration": "3 - 4 hours",
            "visit_info": "Protected turtle conservation sanctuary · Unhurried peaceful beaches away from crowds",
            "rating": 4.8,
        },
        {
            "name": "Cabo de Rama Fort & Ocean Cliff",
            "description": "Ancient coastal clifftop fort in Canacona offering dramatic 360-degree Arabian Sea views and quiet panoramic walking trails along rugged headlands.",
            "category": "History & Views",
            "location": "Canacona, South Goa",
            "image_url": "/images/goa.jpg",
            "tags": ["history", "relaxation", "photography"],
            "estimated_duration": "2 hours",
            "visit_info": "Open 9:00 AM - 5:30 PM · Free entry · Spectacular clifftop ocean horizon vistas",
            "rating": 4.8,
        },
        {
            "name": "Dudhsagar Four-Tier Waterfalls Jungle Safari",
            "description": "One of India's tallest waterfalls roaring down 310m through the dense tropical jungle of the Western Ghats inside Bhagwan Mahaveer Sanctuary.",
            "category": "Adventure & Nature",
            "location": "Sonaulim, Goa Border",
            "image_url": "/images/goa.jpg",
            "tags": ["adventure", "nature", "photography"],
            "estimated_duration": "Full day excursion (6-7 hrs)",
            "visit_info": "Jeep safari via national sanctuary · Natural plunge pool swim · Life jackets mandatory",
            "rating": 4.9,
        },
        {
            "name": "Grand Island Scuba Diving & Snorkeling Excursion",
            "description": "Marine adventure excursion departing to Grand Island featuring coral reef scuba diving, guided snorkeling among exotic reef fish, and coastal dolphin spotting.",
            "category": "Adventure & Water Sports",
            "location": "Mormugao / Grand Island",
            "image_url": "/images/goa.jpg",
            "tags": ["adventure", "beaches", "nature"],
            "estimated_duration": "Full day (5 - 6 hours)",
            "visit_info": "Boat departures from Sinquerim/Baina · Certified PADI dive instructors · Equipment provided",
            "rating": 4.8,
        },
        {
            "name": "Basilica of Bom Jesus & Old Goa Churches",
            "description": "UNESCO World Heritage Portuguese baroque shrines in Old Goa housing the sacred relics of St. Francis Xavier, adorned with gilded woodwork and historic frescos.",
            "category": "History & Culture",
            "location": "Old Goa, Panaji",
            "image_url": "/images/goa.jpg",
            "tags": ["history", "culture"],
            "estimated_duration": "2 hours",
            "visit_info": "Open 9:00 AM - 6:30 PM · Free entry · Modest dress code requested",
            "rating": 4.8,
        },
        {
            "name": "Fontainhas Latin Quarter Heritage Walk",
            "description": "Historic conservation precinct in Panaji with cobblestone streets, Portuguese-style pastel yellow and blue villas, and artisanal bakeries.",
            "category": "Culture & Photography",
            "location": "Panaji, Goa",
            "image_url": "/images/goa.jpg",
            "tags": ["culture", "photography", "food"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Best explored on foot in early morning or golden hour · Traditional Portuguese cafes",
            "rating": 4.8,
        },
        {
            "name": "Fisherman's Wharf & Coastal Goan Seafood Feast",
            "description": "Celebrated riverside dining serving authentic Goan fish curry with kingfish, fiery prawn balchão, butter garlic crab, and traditional seven-layer bebinca.",
            "category": "Food & Dining",
            "location": "Cavelossim / Salcete, Goa",
            "image_url": "/images/goa.jpg",
            "tags": ["food", "relaxation"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Waterfront dining with live acoustic music · Fresh daily catch preparations",
            "rating": 4.9,
        },
        {
            "name": "South Goa Ayurvedic Spa & Oceanfront Yoga Sanctuary",
            "description": "Serene tropical wellness retreat offering authentic Ayurvedic Abhyanga herbal oil massages, cedar sauna therapies, and sunset beachside meditation.",
            "category": "Relaxation & Wellness",
            "location": "Agonda / Benaulim, South Goa",
            "image_url": "/images/goa.jpg",
            "tags": ["relaxation", "nature"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Certified Ayurvedic practitioners · Beachside open-air pavilions · Rejuvenating therapies",
            "rating": 4.9,
        },
    ],
    "tokyo": [
        {
            "name": "Tsukiji Outer Market Food Tour",
            "description": "Atmospheric labyrinth of food stalls serving fresh bluefin sashimi, tamagoyaki omelettes, grilled A5 wagyu skewers, and matcha sweets.",
            "category": "Food & Gastronomy",
            "location": "Chuo City, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["food", "culture", "shopping"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Best early morning 8:00 AM - 1:00 PM · Over 400 artisan vendors · Cash & Suica accepted",
            "rating": 4.9,
        },
        {
            "name": "Omoide Yokocho & Memory Lane Yakitori Stalls",
            "description": "Atmospheric lantern-lit Showa-era alleyway packed with intimate charcoal-grill yakitori stalls, craft beers, and nostalgic old-Tokyo ambiance.",
            "category": "Food & Photography",
            "location": "Shinjuku, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["food", "photography", "nightlife", "culture"],
            "estimated_duration": "Evening (2 hours)",
            "visit_info": "Open 5:00 PM - 11:30 PM · Lantern-lit alleyways · Charcoal-grilled skewers and craft beer",
            "rating": 4.8,
        },
        {
            "name": "Shinjuku Artisan Ramen Street & Tasting",
            "description": "Legendary ramen corridor showcasing rich 16-hour simmered tonkotsu broths, artisanal dipping tsukemen, and seasonal Tokyo soy-dashi noodle bowls.",
            "category": "Food & Dining",
            "location": "West Shinjuku, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["food", "culture"],
            "estimated_duration": "1.5 hours",
            "visit_info": "Ticket vending machine ordering · Quick seating · Iconic regional noodle varieties",
            "rating": 4.9,
        },
        {
            "name": "Shibuya Sky Observation Deck & Scramble Crossing",
            "description": "The world's most photogenic intersection combined with an open-air 360-degree rooftop observatory 229m above Shibuya overlooking Mt. Fuji and neon skylines.",
            "category": "Photography & Viewpoints",
            "location": "Shibuya, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["photography", "nightlife", "shopping"],
            "estimated_duration": "2 - 2.5 hours",
            "visit_info": "Open 10:00 AM - 10:30 PM · Timed entry ticket recommended · Best at golden hour & sunset",
            "rating": 4.9,
        },
        {
            "name": "Senso-ji Temple & Asakusa Historic Pagoda",
            "description": "Tokyo's oldest and most sacred Buddhist temple complex (founded in 645 AD), entered through the iconic Kaminarimon thunder gate and Nakamise market street.",
            "category": "History & Photography",
            "location": "Asakusa, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["history", "culture", "photography", "spirituality"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Main hall 6:00 AM - 5:00 PM · Temple grounds open 24/7 · Stunning red illumination at night",
            "rating": 4.8,
        },
        {
            "name": "TeamLab Planets Digital Art Immersion",
            "description": "Groundbreaking digital sensory museum where visitors wade barefoot through water and mirrored infinity rooms of floating seasonal flowers and crystals.",
            "category": "Photography & Art",
            "location": "Toyosu, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["photography", "art", "family"],
            "estimated_duration": "2 - 2.5 hours",
            "visit_info": "Open 9:00 AM - 10:00 PM · Advance reservation essential · Exceptional photography angles",
            "rating": 4.9,
        },
        {
            "name": "Shinjuku Gyoen National Garden",
            "description": "Expansive 144-acre botanical haven blending traditional Japanese landscape, English formal, and French formal garden aesthetics with tranquil koi ponds.",
            "category": "Nature & Photography",
            "location": "Shinjuku, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["nature", "photography", "relaxation"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Open 9:00 AM - 4:30 PM · ¥500 entry · Seasonal cherry blossoms and autumn maples",
            "rating": 4.8,
        },
        {
            "name": "Meiji Jingu Shrine & Harajuku Forest",
            "description": "Soothing imperial Shinto forest shrine dedicated to Emperor Meiji, set inside 170 acres of tranquil sacred woodland of 120,000 evergreen trees in the city center.",
            "category": "Culture & Nature",
            "location": "Shibuya, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["culture", "spirituality", "nature", "history"],
            "estimated_duration": "2 hours",
            "visit_info": "Open sunrise to sunset · Free admission · Giant cypress Torii gate and sake barrel wall",
            "rating": 4.8,
        },
        {
            "name": "Akihabara Electric Town & Neon Nightscape",
            "description": "Vibrant epicenter of Japanese gaming culture, anime collectible emporiums, multi-floor arcades, and photogenic neon-lit street facades.",
            "category": "Shopping & Photography",
            "location": "Chiyoda City, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["shopping", "photography", "nightlife", "culture"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Shops open 10:00 AM - 9:00 PM · Dazzling multi-story neon signs and photography viewpoints",
            "rating": 4.7,
        },
        {
            "name": "Traditional Onsen Bathhouse & Wellness Spa",
            "description": "Peaceful natural mineral hot spring bathhouse featuring cedar-lined saunas, outdoor rock pools, and rejuvenating Japanese wellness therapies.",
            "category": "Relaxation & Wellness",
            "location": "Bunkyo / Minato, Tokyo",
            "image_url": "/images/tokyo.jpg",
            "tags": ["relaxation", "wellness", "culture"],
            "estimated_duration": "2 hours",
            "visit_info": "Natural geothermal spring waters · Indoor and open-air hot baths",
            "rating": 4.8,
        },
    ],
    "bali": [
        {
            "name": "Tegalalang Rice Terrace",
            "description": "Iconic emerald stepped rice fields with traditional Balinese subak irrigation, jungle swings, and panoramic walking trails.",
            "category": "Nature & Scenery",
            "location": "Ubud, Bali",
            "image_url": "/images/bali.jpg",
            "tags": ["nature", "photography", "scenic", "adventure"],
            "estimated_duration": "2.5 - 3 hours",
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
            "estimated_duration": "2 - 3 hours",
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
            "estimated_duration": "2 hours",
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
            "estimated_duration": "2 hours",
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
            "estimated_duration": "Half day (3 - 4 hours)",
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
            "estimated_duration": "5 - 6 hours",
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
            "estimated_duration": "Evening (2 hours)",
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
            "estimated_duration": "2 hours",
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
            "tags": ["photography", "culture", "scenic"],
            "estimated_duration": "2.5 - 3 hours",
            "visit_info": "Open 9:30 AM - 11:45 PM · Summit access via elevator · Book ahead",
            "rating": 4.9,
        },
        {
            "name": "Musée du Louvre",
            "description": "The world's largest art museum, home to thousands of masterworks including the Mona Lisa, Venus de Milo, and Winged Victory.",
            "category": "Art & History",
            "location": "1st Arrondissement, Paris",
            "image_url": "/images/paris.jpg",
            "tags": ["culture", "history", "art"],
            "estimated_duration": "3 - 4 hours",
            "visit_info": "Open 9:00 AM - 6:00 PM (closed Tuesdays) · Timed tickets mandatory",
            "rating": 4.8,
        },
        {
            "name": "Montmartre & Sacré-Cœur Basilica",
            "description": "Bohemian hilltop quarter of winding cobblestone alleys, portrait painters in Place du Tertre, and sweeping panoramic views of Paris.",
            "category": "Culture & Views",
            "location": "18th Arrondissement, Paris",
            "image_url": "/images/paris.jpg",
            "tags": ["culture", "photography", "views"],
            "estimated_duration": "2.5 - 3 hours",
            "visit_info": "Basilica open 6:30 AM - 10:30 PM · Dome climb 300 steps",
            "rating": 4.7,
        },
        {
            "name": "Seine River Evening Cruise",
            "description": "Romantic gliding cruise under historic stone bridges past illuminated monuments including Notre-Dame, Musée d'Orsay, and the Eiffel Tower.",
            "category": "Scenic & Leisure",
            "location": "Port de la Bourdonnais, Paris",
            "image_url": "/images/paris.jpg",
            "tags": ["relaxation", "photography", "scenic"],
            "estimated_duration": "1.5 hours",
            "visit_info": "Cruises depart every 30 mins · Golden hour and illuminated departures",
            "rating": 4.8,
        },
        {
            "name": "Le Marais Gourmet Food & Boutiques",
            "description": "Historic aristocratic neighborhood featuring artisan boulangeries, falafel along Rue des Rosiers, high-end pastry salons, and designer boutiques.",
            "category": "Food & Shopping",
            "location": "3rd & 4th Arrondissements, Paris",
            "image_url": "/images/paris.jpg",
            "tags": ["food", "shopping", "culture"],
            "estimated_duration": "2.5 - 3 hours",
            "visit_info": "Best visited afternoon & evening · Pedestrianized Sundays",
            "rating": 4.8,
        },
    ],
    "alps": [
        {
            "name": "Matterhorn Glacier Paradise & Zermatt",
            "description": "Europe's highest mountain cable car station at 3,883m with 360-degree views of 38 alpine peaks and year-round glacier snow sports.",
            "category": "Nature & Adventure",
            "location": "Zermatt, Valais",
            "image_url": "/images/alps.jpg",
            "tags": ["adventure", "nature", "photography"],
            "estimated_duration": "Full day (5 - 6 hours)",
            "visit_info": "Open 8:30 AM - 4:30 PM · Year-round glacier access · Dress warmly",
            "rating": 4.9,
        },
        {
            "name": "Jungfraujoch - Top of Europe",
            "description": "Historic cogwheel railway ascending through the Eiger mountain to the Sphinx Observatory at 3,454m overlooking the Great Aletsch Glacier.",
            "category": "Alpine Landmark",
            "location": "Bernese Oberland",
            "image_url": "/images/alps.jpg",
            "tags": ["nature", "adventure", "photography"],
            "estimated_duration": "Full day (6 - 7 hours)",
            "visit_info": "Year-round rail departures · Ice Palace and Sphinx viewing deck",
            "rating": 4.9,
        },
        {
            "name": "Lauterbrunnen Valley of 72 Waterfalls",
            "description": "Deep glacial valley with sheer vertical rock faces, traditional Swiss chalets, and roaring subterranean cascades at Trümmelbach Falls.",
            "category": "Nature & Scenery",
            "location": "Lauterbrunnen, Bern",
            "image_url": "/images/alps.jpg",
            "tags": ["nature", "photography", "scenic"],
            "estimated_duration": "3 - 4 hours",
            "visit_info": "Trümmelbach open 9:00 AM - 5:00 PM · Iconic valley walking path",
            "rating": 4.8,
        },
        {
            "name": "Alpine Fondue Chalet & Cheese Tasting",
            "description": "Cozy wood-timbered mountain refuge serving traditional Gruyère and Emmental fondue, cured alpine meats, and crisp local wines.",
            "category": "Food & Gastronomy",
            "location": "Grindelwald / Zermatt",
            "image_url": "/images/alps.jpg",
            "tags": ["food", "relaxation"],
            "estimated_duration": "2 hours",
            "visit_info": "Dinner reservations recommended · Traditional fireside dining",
            "rating": 4.8,
        },
    ],
    "maldives": [
        {
            "name": "Overwater Coral Reef Snorkeling Safari",
            "description": "Guided marine safari exploring pristine coral gardens teeming with sea turtles, harmless reef sharks, and manta rays.",
            "category": "Beaches & Marine Life",
            "location": "Ari Atoll, Maldives",
            "image_url": "/images/maldives.jpg",
            "tags": ["beaches", "nature", "adventure"],
            "estimated_duration": "3 hours",
            "visit_info": "Morning trips have best visibility · Snorkel gear and guide provided",
            "rating": 4.9,
        },
        {
            "name": "Private Sandbank Picnic & Sunset Dolphin Cruise",
            "description": "Exclusive speedboat excursion to an isolated powdery white sandbar surrounded by turquoise lagoons, followed by sunset spinner dolphin watching.",
            "category": "Relaxation & Scenery",
            "location": "Baa Atoll, Maldives",
            "image_url": "/images/maldives.jpg",
            "tags": ["relaxation", "photography", "beaches"],
            "estimated_duration": "Half day (4 hours)",
            "visit_info": "Afternoon departure at 2:30 PM · Romantic setups available",
            "rating": 4.9,
        },
        {
            "name": "Overwater Spa & Ocean Wellness Pavilion",
            "description": "Holistic wellness therapies in glass-floored overwater pavilions where travelers watch marine life glide below during traditional restorative massages.",
            "category": "Relaxation & Wellness",
            "location": "North Malé Atoll, Maldives",
            "image_url": "/images/maldives.jpg",
            "tags": ["relaxation", "wellness"],
            "estimated_duration": "2 hours",
            "visit_info": "Open 9:00 AM - 8:00 PM · Ocean-sound meditation",
            "rating": 4.8,
        },
    ],
    "thailand": [
        {
            "name": "The Grand Palace & Wat Phra Kaew",
            "description": "Dazzling complex of royal residences and the sacred Emerald Buddha temple adorned with gilded spires and mother-of-pearl.",
            "category": "Culture & Heritage",
            "location": "Bangkok, Thailand",
            "image_url": "/images/thailand.jpg",
            "tags": ["culture", "spirituality", "history"],
            "estimated_duration": "2.5 - 3 hours",
            "visit_info": "Open 8:30 AM - 3:30 PM · Strict dress code applies",
            "rating": 4.8,
        },
        {
            "name": "Wat Arun (Temple of Dawn)",
            "description": "Riverside Buddhist temple towering 70m over the Chao Phraya River, decorated with thousands of colored porcelain fragments.",
            "category": "Culture & Views",
            "location": "Bangkok, Thailand",
            "image_url": "/images/thailand.jpg",
            "tags": ["culture", "photography", "sunsets"],
            "estimated_duration": "1.5 - 2 hours",
            "visit_info": "Open 8:00 AM - 6:00 PM · Best photographed at dusk",
            "rating": 4.8,
        },
        {
            "name": "Phi Phi Islands & Maya Bay Lagoon",
            "description": "Towering limestone cliffs encircling turquoise lagoons, vibrant coral reefs, and white powder sands.",
            "category": "Beaches & Adventure",
            "location": "Krabi / Phuket, Thailand",
            "image_url": "/images/thailand.jpg",
            "tags": ["beaches", "adventure", "nature"],
            "estimated_duration": "Full day (6 - 7 hours)",
            "visit_info": "Day-trip speedboats from Phuket and Krabi · Mask & snorkel provided",
            "rating": 4.9,
        },
        {
            "name": "Chatuchak Weekend Market Street Food Crawl",
            "description": "Giant bustling market of over 15,000 vendor stalls featuring handicrafts, vintage wares, and sensational Thai street food dishes.",
            "category": "Shopping & Food",
            "location": "Chatuchak, Bangkok",
            "image_url": "/images/thailand.jpg",
            "tags": ["shopping", "food", "culture"],
            "estimated_duration": "3 hours",
            "visit_info": "Saturday & Sunday 9:00 AM - 6:00 PM · Mango sticky rice, pad thai, coconut ice cream",
            "rating": 4.7,
        },
    ],
}


def _match_catalogue_key(city: str) -> str | None:
    c = city.lower().strip()
    for key in ATTRACTIONS_CATALOGUE:
        if key in c or c in key:
            return key
    if "manali" in c or "kullu" in c:
        return "manali"
    if "jaipur" in c or "pink city" in c:
        return "jaipur"
    if "goa" in c or "panaji" in c or "calangute" in c or "palolem" in c:
        return "goa"
    if "tokyo" in c or "shinjuku" in c or "shibuya" in c or "asakusa" in c:
        return "tokyo"
    if "swiss" in c or "alps" in c or "matterhorn" in c or "zermatt" in c:
        return "alps"
    if "bangkok" in c or "phuket" in c or "krabi" in c or "chiang mai" in c or "thailand" in c:
        return "thailand"
    if "paris" in c or "france" in c:
        return "paris"
    if "bali" in c or "ubud" in c or "seminyak" in c:
        return "bali"
    if "maldives" in c or "male" in c:
        return "maldives"
    return None


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


def _synthesize_offline_fallback_places(city: str, country: str, interests: list[str]) -> list[dict]:
    """Generates geographically and interest-aligned fallback suggestions when external APIs are unavailable.
    
    Clearly tagged with 'AI Estimated (Offline Fallback)'.
    Does NOT fabricate fake exact coordinates or fake street addresses.
    """
    clean_city = city.strip().title()
    clean_country = (country or "").strip().title()
    loc_label = f"{clean_city}, {clean_country}" if clean_country else clean_city
    pool = []

    c_comb = f"{clean_city} {clean_country}".lower()
    is_alpine = any(k in c_comb for k in ["switzerland", "austria", "alps", "himalaya", "manali", "interlaken", "zermatt", "banff", "aspen", "mountain", "tyrol"])
    is_island = any(k in c_comb for k in ["bali", "maldives", "santorini", "island", "hawaii", "phuket", "beach", "goa", "fiji", "mauritius", "caribbean"])
    is_historic = any(k in c_comb for k in ["japan", "kyoto", "italy", "rome", "morocco", "chefchaouen", "jaipur", "india", "france", "paris", "greece", "egypt", "spain", "mexico"])

    # 1. Nature / Outdoors
    if is_alpine:
        pool.append({
            "name": f"{clean_city} Alpine Panorama & High Mountain Trail",
            "description": f"Elevated alpine trail near {clean_city} delivering sweeping vistas of mountain peaks, glacial valleys, and pristine pine slopes.",
            "category": "Nature & Outdoors",
            "location": loc_label,
            "image_url": "/images/alps.jpg",
            "tags": ["nature", "adventure", "photography"],
            "estimated_duration": "3 - 5 hours",
            "visit_info": "Scenic walking trail · Mountain footwear advised",
            "source": "AI Estimated (Offline Fallback)",
            "coordinates": None,
            "address": None,
            "rating": 4.8,
        })
    elif is_island:
        pool.append({
            "name": f"{clean_city} Coastal Bay & Sunset Marine Beach",
            "description": f"Scenic coastal stretch along {clean_city} with soft sand, gentle sea breezes, and idyllic sunset viewing spots.",
            "category": "Beaches & Relaxation",
            "location": loc_label,
            "image_url": "/images/bali.jpg",
            "tags": ["beaches", "relaxation", "photography"],
            "estimated_duration": "3 - 4 hours",
            "visit_info": "Open all day · Waterfront relaxation and sunset views",
            "source": "AI Estimated (Offline Fallback)",
            "coordinates": None,
            "address": None,
            "rating": 4.8,
        })
    else:
        pool.append({
            "name": f"{clean_city} Nature Reserve & Panoramic River Park",
            "description": f"Tranquil natural park in {clean_city} featuring shaded walking paths, native flora, and open scenic viewpoints.",
            "category": "Nature & Outdoors",
            "location": loc_label,
            "image_url": "/images/hero.jpg",
            "tags": ["nature", "scenic"],
            "estimated_duration": "2 - 3 hours",
            "visit_info": "Open sunrise to sunset · Gentle footpaths",
            "source": "AI Estimated (Offline Fallback)",
            "coordinates": None,
            "address": None,
            "rating": 4.7,
        })

    # 2. History & Heritage
    if is_historic:
        pool.append({
            "name": f"{clean_city} Historic Old Town & Heritage Citadel",
            "description": f"Ancient architectural core of {clean_city} with preserved stone quarters, historic gateways, and storied cultural landmarks.",
            "category": "History & Heritage",
            "location": loc_label,
            "image_url": "/images/hero.jpg",
            "tags": ["history", "culture", "photography"],
            "estimated_duration": "2.5 - 3 hours",
            "visit_info": "Historic cobblestone district · Guided walking tours available",
            "source": "AI Estimated (Offline Fallback)",
            "coordinates": None,
            "address": None,
            "rating": 4.9,
        })
    else:
        pool.append({
            "name": f"{clean_city} Historic Quarter & Memorial Monument",
            "description": f"Centuries-old focal landmark commemorating the heritage, architectural origins, and founding history of {clean_city}.",
            "category": "History & Heritage",
            "location": loc_label,
            "image_url": "/images/hero.jpg",
            "tags": ["history", "culture"],
            "estimated_duration": "1.5 - 2 hours",
            "visit_info": "Open daily · Historical exhibits",
            "source": "AI Estimated (Offline Fallback)",
            "coordinates": None,
            "address": None,
            "rating": 4.7,
        })

    # 3. Culture & Arts
    pool.append({
        "name": f"{clean_city} Cultural Arts Museum & Regional Gallery",
        "description": f"Celebrated cultural institution showcasing regional fine arts, traditional handicrafts, folkloric antiquities, and seasonal exhibitions of {clean_city}.",
        "category": "Culture & Heritage",
        "location": loc_label,
        "image_url": "/images/hero.jpg",
        "tags": ["culture", "art", "history"],
        "estimated_duration": "2 hours",
        "visit_info": "Open 10:00 AM - 5:00 PM · Audio guides available",
        "source": "AI Estimated (Offline Fallback)",
        "coordinates": None,
        "address": None,
        "rating": 4.7,
    })

    # 4. Food & Dining
    pool.append({
        "name": f"{clean_city} Central Artisan Gastronomy Market",
        "description": f"Lively culinary gathering place where regional vendors, bakers, and chefs serve authentic signature dishes and fresh local specialties of {clean_city}.",
        "category": "Food & Gastronomy",
        "location": loc_label,
        "image_url": "/images/hero.jpg",
        "tags": ["food", "culture", "shopping"],
        "estimated_duration": "2 hours",
        "visit_info": "Best visited morning to lunch · Fresh artisan food stalls",
        "source": "AI Estimated (Offline Fallback)",
        "coordinates": None,
        "address": None,
        "rating": 4.8,
    })

    # 5. Photography & Viewpoints
    pool.append({
        "name": f"{clean_city} Panoramic Skyline & Sunset Viewpoint",
        "description": f"Prominent elevated outlook offering panoramic 360-degree compositions across {clean_city}, perfect for landscape and golden-hour photography.",
        "category": "Photography & Viewpoints",
        "location": loc_label,
        "image_url": "/images/hero.jpg",
        "tags": ["photography", "scenic"],
        "estimated_duration": "1.5 hours",
        "visit_info": "Open daily · Unbeatable golden-hour lighting",
        "source": "AI Estimated (Offline Fallback)",
        "coordinates": None,
        "address": None,
        "rating": 4.8,
    })

    # 6. Relaxation & Wellness
    pool.append({
        "name": f"{clean_city} Botanical Sanctuary & Wellness Gardens",
        "description": f"Peaceful landscape gardens featuring curated flora, calm reflective water pools, and unhurried rest pavilions in {clean_city}.",
        "category": "Relaxation & Wellness",
        "location": loc_label,
        "image_url": "/images/hero.jpg",
        "tags": ["relaxation", "nature"],
        "estimated_duration": "2 hours",
        "visit_info": "Open 8:00 AM - 6:00 PM · Peaceful relaxation grounds",
        "source": "AI Estimated (Offline Fallback)",
        "coordinates": None,
        "address": None,
        "rating": 4.7,
    })

    return pool


def retrieve_dynamic_attractions(
    destination: str,
    interests: list[str] | None = None,
) -> tuple[dict, list[dict]]:
    """Retrieves real, verified attractions and geocoded coordinates for ANY destination worldwide.
    
    1. Geocodes destination to lat/lon/country using Geoapify.
    2. Retrieves real sights via SerpApi Google Knowledge Graph / Top Sights.
    3. Retrieves verified places via Geoapify Places by coordinates and categories.
    4. Incorporates curated local catalogue if destination matches known hubs.
    5. Fuses, deduplicates, and caches results.
    6. Falls back gracefully without fabricating fake coordinates if APIs are unreachable.
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

    # Fallback coordinates for known seeded hubs if Geoapify was offline
    if lat is None or lon is None:
        c_low = clean_dest.lower()
        if "manali" in c_low:
            lat, lon, country = 32.2455, 77.1873, "India"
        elif "jaipur" in c_low:
            lat, lon, country = 26.9124, 75.7873, "India"
        elif "goa" in c_low:
            lat, lon, country = 15.2993, 74.1240, "India"
        elif "tokyo" in c_low:
            lat, lon, country = 35.6762, 139.6503, "Japan"
        elif "kyoto" in c_low:
            lat, lon, country = 35.0116, 135.7681, "Japan"
        elif "interlaken" in c_low:
            lat, lon, country = 46.6855, 7.8585, "Switzerland"
        elif "bali" in c_low:
            lat, lon, country = -8.8329, 115.1476, "Indonesia"
        elif "paris" in c_low:
            lat, lon, country = 48.8566, 2.3522, "France"
        elif "alps" in c_low or "swiss" in c_low:
            lat, lon, country = 46.5584, 7.9864, "Switzerland"
        elif "chefchaouen" in c_low:
            lat, lon, country = 35.1688, -5.2684, "Morocco"
        elif "rome" in c_low:
            lat, lon, country = 41.9028, 12.4964, "Italy"
        elif "london" in c_low:
            lat, lon, country = 51.5074, -0.1278, "United Kingdom"
        elif "new york" in c_low or "nyc" in c_low:
            lat, lon, country = 40.7128, -74.0060, "United States"
        elif "dubai" in c_low:
            lat, lon, country = 25.2048, 55.2708, "United Arab Emirates"
        elif "bangkok" in c_low:
            lat, lon, country = 13.7563, 100.5018, "Thailand"

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
        if not p.get("image_url"):
            p["image_url"] = "/images/hero.jpg"
        collected_places.append(p)

    # 4. Retrieve live Google Knowledge Graph sights via SerpApi
    if serpapi_client.is_configured():
        serp_sights = serpapi_client.search_attractions(clean_dest, interests=interests, limit=15)
        for s in serp_sights:
            # If coordinates are available for the city, associate city coordinates if sight doesn't have its own
            s["coordinates"] = {"lat": lat, "lon": lon} if (lat is not None and lon is not None) else None
            _add_place(s)

    # 5. Retrieve verified nearby places via Geoapify Places API
    if geoapify_client.is_configured() and lat is not None and lon is not None:
        geo_places = geoapify_client.search_places(lat, lon, interests=interests, radius_meters=25000, limit=15)
        for gp in geo_places:
            # Check if this place matches an existing SerpApi place to merge coordinates and street address
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

    # 6. Merge Curated Catalogue if destination is one of the rich catalogued hubs
    cat_key = _match_catalogue_key(clean_dest)
    if cat_key and cat_key in ATTRACTIONS_CATALOGUE:
        for cp in ATTRACTIONS_CATALOGUE[cat_key]:
            cp_copy = dict(cp)
            cp_copy["source"] = "Curated Travel Guide"
            if lat is not None and lon is not None and not cp_copy.get("coordinates"):
                cp_copy["coordinates"] = {"lat": lat, "lon": lon}
            _add_place(cp_copy)

    # 7. Fallback if no external or catalogue places could be gathered
    if not collected_places:
        fallback_places = _synthesize_offline_fallback_places(clean_dest, country, interests or [])
        for fp in fallback_places:
            _add_place(fp)

    # 8. Cache results
    _DEST_CACHE[cache_key] = {"geo_info": geo_info, "places": collected_places}
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
                    source="Geoapify + SerpApi",
                ))
                db.commit()
    except Exception as e:
        logger.debug("Failed saving to destination_info_cache: %s", e)

    return geo_info, collected_places


class DestinationAgent(BaseAgent):
    name = "destination"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        req = state["request"]
        city = req.get("destination", "")
        interests = [i.lower().strip() for i in req.get("interests", [])]

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
