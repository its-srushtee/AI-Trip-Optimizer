"""Itinerary agent — assembles a dynamic, non-repeating, preference-tailored,
and location-optimized day-by-day plan.

Strictly respects:
- Travel pace (Relaxed vs Moderate vs Fast-paced)
- Travel style (Backpacker, Budget, Comfort, Luxury)
- Selected interests (Nature, Adventure, History, Culture, Food, Photography, Beaches, Relaxation, etc.)
- Destination, dates, budget, and dining preferences
- Geographic proximity (clustering nearby attractions to eliminate backtracking)
- Non-repetition of attractions, activities, and meals across the entire itinerary
"""
import math
import re
from datetime import date, timedelta
from typing import Any

from app.agents.base import BaseAgent
from app.api_clients.currency import CURRENCY_SYMBOLS, currency_client


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes the great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def estimate_transit_info(dist_km: float | None) -> str:
    """Provides a realistic, sensible transit estimate without inventing exact GPS routes."""
    if dist_km is None:
        return "Local transit / 10-15 min stroll"
    if dist_km <= 1.2:
        return "Short 5-10 min walk through scenic pedestrian paths"
    elif dist_km <= 4.5:
        return f"Quick 10-15 min local transit / cab ride ({dist_km:.1f} km)"
    elif dist_km <= 12.0:
        return f"Approx. 20-25 min connection ({dist_km:.1f} km)"
    elif dist_km <= 25.0:
        return f"Scenic 35-45 min transfer ({dist_km:.1f} km)"
    else:
        return f"Approx. {round(dist_km * 1.4 + 15)} min regional transfer ({dist_km:.1f} km)"


def format_cost_range(usd_low: int, usd_high: int, currency: str = "USD", suffix: str = "") -> str:
    """Formats a cost range converted accurately to the target currency."""
    currency = (currency or "USD").upper()
    sym = CURRENCY_SYMBOLS.get(currency, "$")
    low = currency_client.convert(usd_low, "USD", currency)["converted_amount"]
    high = currency_client.convert(usd_high, "USD", currency)["converted_amount"]
    tail = f" {suffix}" if suffix else ""
    if low == 0:
        return f"{sym}0 - {sym}{high:,}{tail}"
    return f"{sym}{low:,} - {sym}{high:,}{tail}"


def estimate_activity_cost(category: str, style: str, currency: str = "USD") -> str:
    """Estimates realistic per-activity cost tailored to traveler style and currency."""
    cat = (category or "").lower()
    style_l = (style or "Comfort").lower()

    if any(k in cat for k in ["nature", "park", "beach", "trail", "viewpoint", "waterfall"]):
        if "luxury" in style_l:
            return f"{format_cost_range(25, 40, currency)} (Private eco-reserve pass & naturalist guide)"
        return f"Free / Nominal park pass ({format_cost_range(0, 5, currency)})"

    if any(k in cat for k in ["museum", "fort", "palace", "heritage", "monument", "temple", "shrine"]):
        if "luxury" in style_l:
            return f"{format_cost_range(45, 80, currency)} (VIP skip-the-line pass & historian guide)"
        elif "budget" in style_l or "backpacker" in style_l:
            return f"{format_cost_range(5, 12, currency)} (Standard entry ticket)"
        return f"{format_cost_range(15, 25, currency)} (Audio guide & admission)"

    if any(k in cat for k in ["adventure", "sport", "boat", "trek", "cruise", "snorkel", "diving"]):
        if "luxury" in style_l:
            return f"{format_cost_range(120, 220, currency)} (Private chartered excursion & premium gear)"
        elif "budget" in style_l or "backpacker" in style_l:
            return f"{format_cost_range(25, 45, currency)} (Group tour & equipment rental)"
        return f"{format_cost_range(55, 90, currency)} (Certified guided excursion)"

    if any(k in cat for k in ["food", "culinary", "market", "tasting", "cafe"]):
        if "luxury" in style_l:
            return f"{format_cost_range(65, 120, currency)} (Chef-led gastronomic tasting & wine pairing)"
        elif "budget" in style_l or "backpacker" in style_l:
            return f"{format_cost_range(8, 15, currency)} (Signature street market bites & drink)"
        return f"{format_cost_range(25, 40, currency)} (Artisan food hall selection & refreshments)"

    if "luxury" in style_l:
        return f"{format_cost_range(50, 90, currency)} (Curated experience)"
    elif "budget" in style_l or "backpacker" in style_l:
        return f"{format_cost_range(0, 10, currency)} (Budget-friendly self-guided)"
    return f"{format_cost_range(15, 30, currency)} (Standard visit)"


def _resolve_stay(city: str, style: str | None, accommodation: str | None, hotels: list[dict]) -> str:
    """Selects an authentic stay title reflecting user accommodation and style preferences."""
    if hotels and isinstance(hotels, list) and len(hotels) > 0:
        top_hotel = hotels[0].get("name")
        if top_hotel:
            return f"{top_hotel} ({city})"

    style_s = (style or "Comfort").title()
    acc_s = (accommodation or "Hotel").title()

    if "Luxury" in style_s or "Resort" in acc_s:
        return f"Luxury 5-Star Resort & Spa Sanctuary ({city})"
    if "Backpacker" in style_s or "Hostel" in acc_s:
        return f"Social Backpacker Boutique Hostel & Pods ({city})"
    if "Homestay" in acc_s:
        return f"Traditional Heritage Riverside Homestay ({city})"
    if "Budget" in style_s:
        return f"Charming Central Budget Boutique Inn ({city})"
    return f"Curated Comfort Boutique Hotel ({city})"


class MealEngine:
    """Generates varied, authentic, non-repeating meals for every day of the trip."""

    def __init__(self, city: str, food_pref: str | None, interests: list[str]):
        self.city = city
        self.city_lower = city.lower()
        self.food_pref = (food_pref or "").lower()
        self.is_veg = "veg" in self.food_pref and "non" not in self.food_pref
        self.interests = [i.lower() for i in interests]
        self.used_breakfasts = set()
        self.used_lunches = set()
        self.used_dinners = set()
        self._pool = self._build_pool()

    def _build_pool(self) -> dict[str, list[str]]:
        c = self.city_lower
        is_veg = self.is_veg

        # Regional meal repositories
        if "manali" in c:
            b = [
                "Artisan cafe porridge with wild honey, walnuts, and Himalayan herbal tea",
                "Warm bakery sourdough, masala cheese omelette, and freshly roasted espresso" if not is_veg else "Fresh apple crumble, toasted multigrain bread, and Himalayan butter tea",
                "Poha and stuffed aloo parathas with fresh mountain curd and spicy mint pickle",
                "Banana walnut buckwheat pancakes with local apricot jam and ginger lemon tea",
                "Tibetan Tingmo steamed buns with spiced chickpea curry and honey lemon water",
                "Crispy methi paratha with fresh churned white butter and spiced masala chai",
                "Old Manali organic granola bowl with mountain berries, chia seeds, and yak milk curd",
            ]
            l = [
                "Authentic Himachali Siddu stuffed with spiced poppy seeds and desi ghee at a heritage village dhaba",
                "Steamed vegetable momos and piping hot Thukpa noodle soup with chili chutney",
                "Pahadi Dal and slow-cooked Madra lentils served with fragrant steamed basmati rice",
                "Fresh pan-fried Beas river trout with garlic herb butter and mountain greens" if not is_veg else "Paneer Tikka skewers with roasted mountain bell peppers and mint chutney",
                "Himachali Dham feast featuring lentils, spiced kidney beans, and saffron sweet rice",
                "Rustic wood-fired thin crust pizza and local spiced apple cider at a riverside cafe",
                "Spiced Pahadi rajma bowl with red rice, radish salad, and bhangjeera chutney",
            ]
            d = [
                "Traditional Himachali Dham (Madra, sweet rice, and lentils) at an authentic local rasoi",
                "Fireside lodge dinner featuring slow-cooked saffron rice, paneer rogan josh, and hot naan",
                "Wood-fired artisanal sourdough flatbreads and craft mountain cider by the river",
                "Sizzling Tibetan momos, chili garlic noodles, and steaming sweet corn soup",
                "Candlelit riverside dinner with slow-braised mountain stew and warm herb bread",
                "Pahadi Kadi with steamed red rice, roasted papad, and walnut chutney",
                "Starlit terrace dinner enjoying fresh grilled skewers and warm spiced almond milk",
            ]
        elif "kyoto" in c:
            b = [
                "Traditional Kyoto Obanzai breakfast with simmered seasonal vegetables and dashi",
                "Fluffy Japanese souffle pancakes with matcha honey and pour-over drip coffee",
                "Warm tamagoyaki rolled omelet, miso soup with wakame, and onigiri rice ball",
                "Freshly baked matcha melon pan and cold-brew green tea in historic Gion",
                "Japanese rice porridge (Okayu) topped with pickled plum (umeboshi) and roasted nori",
                "Artisanal sourdough toast with yuzu marmalade and specialty Kyoto single-origin coffee",
                "Silken tofu hot pot breakfast with grated ginger and green scallions at a temple cafe",
            ]
            l = [
                "Shojin Ryori Buddhist vegetarian temple cuisine with delicate yuba (tofu skin)",
                "Chirashizushi bowl with fresh Kansai sashimi and pickled ginger" if not is_veg else "Crisp seasonal vegetable tempura over hand-cut soba noodles in chilled tsuyu broth",
                "Udon noodle clay pot in rich dashi broth with maitake mushrooms and soft poached egg",
                "Kyoto-style savory okonomiyaki pancake grilled with scallions and artisan brown sauce",
                "Matcha soba noodles served over ice with seasonal mountain vegetable tempura",
                "Tender chicken or mushroom katsu donburi simmered in sweet soy broth over rice",
                "Steamed bamboo leaf rice balls paired with slow-simmered lotus root and miso soup",
            ]
            d = [
                "Seasonal multi-course Kaiseki tasting dinner overlooking the serene Kamogawa River",
                "Charcoal-grilled yakitori and seasonal vegetable skewers in lantern-lit Pontocho Alley",
                "Simmered Kyoto duck hot pot" if not is_veg else "Yudofu boiling tofu hot pot with sesame ponzu and mountain herbs in Nanzenji",
                "Interactive Teppanyaki dinner featuring premium Wagyu beef or grilled king oyster mushrooms",
                "Atmospheric ramen tasting sampling 16-hour simmered broth with spring onions and bamboo shoots",
                "Traditional Izakaya feast with grilled eggplant in sweet red miso and crisp draft beer",
                "Zen garden restaurant dinner featuring seasonal Kansai root vegetable delicacies and plum wine",
            ]
        elif "interlaken" in c or "swiss" in c or "alps" in c:
            b = [
                "Bircher muesli with fresh alpine raspberries, local mountain cheeses, and crusty artisan bread",
                "Warm butter croissants, alpine wildflower honey, and freshly brewed Swiss roast coffee",
                "Hearty alpine breakfast platter with Emmental cheese, soft boiled farm egg, and dark rye",
                "Warm Swiss apple strudel slice with cinnamon cream and hot mountain herbal tea",
                "Swiss hazelnut pastry with fresh berry compote and hot dark chocolate in Unterseen",
                "Toasted brioche with Gruyère cheese spread and fresh pressed Valais orchard apple juice",
                "Rustic farmer's breakfast with scrambled farm eggs, fried alpine potatoes, and fresh milk",
            ]
            l = [
                "Traditional Swiss Rösti topped with melted Gruyère cheese and sunny-side farm egg",
                "Hearty Grisons barley soup with crusty mountain bread and local Alpine butter",
                "Thin crust Swiss Tarte Flambée topped with sweet onions and crème fraîche",
                "Fresh Lake Brienz whitefish fillet with herb butter and parsley potatoes" if not is_veg else "Creamy wild chanterelle mushroom ragout in puff pastry shell",
                "Alpine macaroni (Älplermagronen) with caramelized onions, melted cheese, and apple sauce",
                "Rustic fondue baguette sandwich enjoyed on a panoramic mountain overlook terrace",
                "Swiss cheese and dried fruit picnic basket sampled along the scenic Lake Thun shoreline",
            ]
            d = [
                "Authentic bubbling Swiss cheese fondue with crusty bread cubes, baby potatoes, and Fendant wine",
                "Raclette dinner with melted cheese scraped over roasted new potatoes and pickled gherkins",
                "Zürcher Geschnetzeltes slow-cooked in white wine mushroom sauce with crispy golden Rösti",
                "Lakeside terrace dinner sampling grilled trout and seasonal Swiss garden vegetables",
                "Cozy mountain chalet dinner featuring braised alpine beef" if not is_veg else "Braised alpine red cabbage, chestnut dumplings, and roasted root vegetables",
                "Fireside lodge dinner with cheese spaetzle, caramelized onions, and crisp Swiss cider",
                "Panoramic revolving mountain restaurant feast overlooking the Eiger, Mönch, and Jungfrau peaks",
            ]
        elif "bali" in c:
            b = [
                "Tropical dragonfruit smoothie bowl topped with toasted coconut, chia seeds, and Balinese coffee",
                "Warm black rice pudding (Bubur Ketan Hitam) with rich coconut cream and sliced ripe mango",
                "Fluffy banana banana pancakes drizzled with organic palm nectar and fresh papaya juice",
                "Balinese scrambled eggs with turmeric and kaffir lime served over sourdough toast",
                "Avocado toast topped with local goat feta, poached eggs, and fresh cold brew in Canggu",
                "Sweet coconut crepes (Dadar Gulung) stuffed with grated palm sugar and fresh young coconut",
                "Healthy organic acai bowl with passionfruit, granola, and chilled coconut water",
            ]
            l = [
                "Authentic Nasi Campur featuring spiced tempeh, sambal matah, and fragrant jasmine rice",
                "Traditional Gado-Gado vegetable salad with warm savory peanut dressing and krupuk crackers",
                "Balinese Mie Goreng wok-tossed noodles with fresh Asian greens and fried shallots",
                "Spiced grilled fish wrapped in banana leaf (Pepes Ikan)" if not is_veg else "Crispy spiced tofu and tempeh skewers with chili tamarind sauce",
                "Organic farm-to-table quinoa and roasted pumpkin salad at an Ubud jungle eco-cafe",
                "Aromatic Soto Ayam chicken turmeric broth with glass noodles" if not is_veg else "Sayur Lodeh fragrant coconut vegetable stew with steamed rice cakes",
                "Beach club wood-fired pizza and crisp seasonal green salad overlooking the surf breaks",
            ]
            d = [
                "Jimbaran Bay beachfront sunset grill with coconut-husk grilled seafood and sambal matah",
                "Balinese Sate Lilit minced skewers grilled over lemongrass stalks with lawar green bean salad",
                "Crispy Balinese Duck (Bebek Betutu) slow-roasted in banana leaves with rich yellow spice paste",
                "Candlelit riverside dinner in Ubud featuring multi-course royal Balinese tasting dishes",
                "Clifftop Uluwatu sunset dinner enjoying fresh tropical curries and ginger lemongrass coolers",
                "Contemporary Indonesian fusion dining with braised jackfruit rendang and turmeric rice",
                "Open-air pavilion feast accompanied by traditional Balinese gamelan music and coconut ice cream",
            ]
        elif "chefchaouen" in c or "morocco" in c:
            b = [
                "Warm Moroccan khobz bread with fresh goat cheese, black olives, fig jam, and mint tea",
                "Flaky layered Msemmen pancakes drizzled with wildflower honey and sweet spiced coffee",
                "Shakshuka poached eggs simmered in rich cumin tomato sauce with warm flatbread",
                "Harcha semolina flatbread with fresh local butter, dates, and fragrant orange blossom tea",
                "Creamy bissara fava bean soup with extra virgin olive oil, cumin, and crusty bread",
                "Moroccan Baghrir thousand-hole honeycomb pancakes soaked in melted honey butter",
                "Artisan fruit platter with sweet pomegranate seeds, dates, walnuts, and Moroccan mint infusion",
            ]
            l = [
                "Fragrant vegetable or lamb tagine slow-cooked in earthenware with preserved lemons and olives",
                "Steamed Moroccan couscous with seven garden vegetables, chickpeas, and caramelized onions",
                "Crispy chicken pastilla pastry dusted with cinnamon sugar and ground toasted almonds" if not is_veg else "Sweet caramelized onion and almond pastilla with seasonal greens",
                "Traditional Zaalouk roasted eggplant dip and spiced tomato chermoula served with warm khobz",
                "Grilled spiced kefta skewers with harissa sauce" if not is_veg else "Spiced chickpea and lentil tagine with apricots and roasted sesame",
                "Fresh Mediterranean salad with crisp cucumbers, tomatoes, goat cheese, and mountain oregano",
                "Rooftop medina lunch sampling savory lamb skewers, roasted peppers, and chilled citrus juice",
            ]
            d = [
                "Candlelit riad courtyard dinner featuring slow-braised tagine and saffron-infused rice",
                "Royal couscous feast crowned with roasted vegetables, raisins, and sweet cinnamon broth",
                "Harira traditional aromatic soup paired with sweet dates, chebakia sesame pastry, and warm bread",
                "Plaza Uta el-Hammam terrace dinner overlooking the illuminated Kasbah with spiced tagine",
                "Tender oven-roasted mountain goat with cumin salt and roasted baby potatoes in the Medina",
                "Seafood tagine with Atlantic catch, sweet bell peppers, and preserved lemon chermoula",
                "Starlit rooftop feast with Moroccan mint tea ceremony and sweet almond gazelle horns pastry",
            ]
        else:
            # Universal Dynamic Culinary Generator
            city_t = self.city.title()
            b = [
                f"Freshly baked artisan pastries, seasonal local fruit, and specialty espresso in {city_t}",
                f"Hearty farm-to-table breakfast with country sourdough, local cheese, and orchard preserves",
                f"Warm bakery croissants with fruit compote and barista-crafted pour-over coffee",
                f"Avocado toast on whole-grain sourdough with soft farm eggs and fresh pressed juice",
                f"Artisan bakery breakfast sampling regional morning specialties and specialty tea",
                f"Organic granola bowl with Greek yogurt, wild honey, and toasted orchard nuts",
                f"Classic local cafe breakfast with toasted brioche, farm butter, and hot chocolate",
            ]
            l = [
                f"Celebrated neighborhood bistro lunch sampling signature regional specialties of {city_t}",
                f"Atmospheric local food hall tasting featuring artisan cheeses, charcuterie, and fresh salads",
                f"Scenic terrace lunch overlooking historic {city_t} streetscapes with seasonal garden fare",
                f"Authentic local market tasting sampling regional street delicacies and fresh baked flatbreads",
                f"Waterfront / garden bistro lunch with freshly caught catch or seasonal risotto",
                f"Charming courtyard cafe lunch with artisanal quiche, crisp salad, and house-made lemonade",
                f"Historic tavern lunch sampling slow-simmered regional stews and rustic hearth bread",
            ]
            d = [
                f"Dinner reservation at a top-rated restaurant highlighting authentic regional cuisine of {city_t}",
                f"Candlelit courtyard dinner enjoying multi-course gastronomic tasting menu with local wine",
                f"Scenic panoramic restaurant with evening skyline views of {city_t} and seasonal dessert",
                f"Historic district tavern dinner sampling slow-braised local specialties and craft beverages",
                f"Vibrant central square dining with open-air terrace seating, fresh pasta / roasted delicacies",
                f"Atmospheric wine bar & bistro dinner featuring artisanal small plates and decadent dessert",
                f"Sunset view dining room experiencing modern gastronomic interpretations of local classics",
            ]

        return {"breakfast": b, "lunch": l, "dinner": d}

    def get_meals_for_day(self, day_idx: int) -> dict[str, str]:
        pool_b = self._pool["breakfast"]
        pool_l = self._pool["lunch"]
        pool_d = self._pool["dinner"]

        b = pool_b[day_idx % len(pool_b)]
        l = pool_l[day_idx % len(pool_l)]
        d = pool_d[day_idx % len(pool_d)]

        # If already used in an earlier day, look for the next unused candidate
        for candidate in pool_b:
            if candidate not in self.used_breakfasts:
                b = candidate
                break
        self.used_breakfasts.add(b)

        for candidate in pool_l:
            if candidate not in self.used_lunches:
                l = candidate
                break
        self.used_lunches.add(l)

        for candidate in pool_d:
            if candidate not in self.used_dinners:
                d = candidate
                break
        self.used_dinners.add(d)

        return {"breakfast": b, "lunch": l, "dinner": d}


class ItineraryAgent(BaseAgent):
    name = "itinerary"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        req = state["request"]
        start = date.fromisoformat(req["start_date"])
        end = date.fromisoformat(req["end_date"])
        nights = max(0, (end - start).days)
        total_days = nights + 1
        budget = int(req.get("budget", 1000))
        currency = (req.get("currency") or req.get("preferences", {}).get("currency") or "USD").upper()
        curr_sym = CURRENCY_SYMBOLS.get(currency, "$")

        interests = [i.lower().strip() for i in req.get("interests", [])]
        city = req.get("destination", "").strip()
        pace = (req.get("pace") or req.get("preferences", {}).get("pace") or "Moderate").title()
        style = (req.get("style") or req.get("preferences", {}).get("style") or "Comfort").title()
        food_pref = req.get("food") or req.get("preferences", {}).get("food") or "No preference"
        accommodation = req.get("accommodation") or req.get("preferences", {}).get("accommodation")

        pace_display = pace.lower().replace("-paced", "") + "-paced"

        # Destination curated places
        raw_places = state.get("destination", {}).get("places_to_visit", [])
        dest_coords = state.get("destination", {}).get("coordinates") or {}
        center_lat = dest_coords.get("lat")
        center_lon = dest_coords.get("lon") or dest_coords.get("lng")

        raw_hotels = state.get("hotels")
        if isinstance(raw_hotels, dict):
            hotels = raw_hotels.get("options", [])
        elif isinstance(raw_hotels, list):
            hotels = raw_hotels
        else:
            hotels = []
        stay_title = _resolve_stay(city, style, accommodation, hotels)

        # Pace configuration
        pace_is_relaxed = "Relax" in pace
        pace_is_fast = "Fast" in pace or "Packed" in pace

        if pace_is_relaxed:
            pace_note = "Relaxed unhurried pace: generous morning windows, dedicated afternoon rest, and zero rushed transits."
        elif pace_is_fast:
            pace_note = "Fast-paced energetic pace: early starts, geographically clustered sights, and vibrant evening exploration."
        else:
            pace_note = "Balanced moderate pace: structured morning sightseeing, leisurely meals, nearby afternoon discovery, and evening relaxation."

        # Initialize Meal Engine
        meal_engine = MealEngine(city, food_pref, interests)

        # -------------------------------------------------------------
        # LOCATION-BASED SCHEDULING & SPATIAL CLUSTERING
        # -------------------------------------------------------------
        # Clean place names and eliminate duplicates
        valid_places: list[dict] = []
        seen_place_names = set()

        for p in raw_places:
            clean_name = re.sub(r"\s+", " ", p.get("name", "")).strip()
            norm = re.sub(r"[^a-z0-9]+", "", clean_name.lower())
            if not norm or len(norm) < 3 or norm in seen_place_names:
                continue
            seen_place_names.add(norm)
            valid_places.append(dict(p))

        # Separate into available pool for assignment
        available_pool = list(valid_places)
        used_places_registry = set()

        # Helper to extract coordinates from place
        def get_coords(p: dict) -> tuple[float | None, float | None]:
            c = p.get("coordinates")
            if isinstance(c, dict) and c.get("lat") is not None and (c.get("lon") is not None or c.get("lng") is not None):
                return float(c["lat"]), float(c.get("lon") or c.get("lng"))
            return center_lat, center_lon

        # Pre-assign places per day using geographic clustering
        daily_assigned_places: list[list[dict]] = []

        for day_idx in range(total_days):
            day_places: list[dict] = []

            # Determine target number of places for this day based on pace & arrival/departure
            if day_idx == 0:
                # Arrival Day: 1 light place in afternoon near stay
                target_count = 1 if available_pool else 0
            elif day_idx == total_days - 1:
                # Departure Day: 1 morning place near stay / transit hub
                target_count = 1 if available_pool else 0
            elif pace_is_relaxed:
                # Relaxed: 1 primary sight per day to allow deep leisure
                target_count = 1 if available_pool else 0
            elif pace_is_fast:
                # Fast-paced: 2 to 3 sights per day
                target_count = min(3, len(available_pool)) if available_pool else 0
            else:
                # Moderate: 2 balanced sights per day
                target_count = min(2, len(available_pool)) if available_pool else 0

            # Step A: Pick Anchor Sight for the day (highest preference score remaining)
            if target_count > 0 and available_pool:
                anchor = available_pool.pop(0)
                day_places.append(anchor)
                used_places_registry.add(anchor["name"])
                anchor_lat, anchor_lon = get_coords(anchor)

                # Step B: Pick geographically nearest companions to eliminate backtracking
                for _ in range(target_count - 1):
                    if not available_pool:
                        break

                    best_idx = 0
                    best_dist = float("inf")

                    if anchor_lat is not None and anchor_lon is not None:
                        for idx, cand in enumerate(available_pool):
                            clat, clon = get_coords(cand)
                            if clat is not None and clon is not None:
                                d = haversine_distance_km(anchor_lat, anchor_lon, clat, clon)
                                if d < best_dist:
                                    best_dist = d
                                    best_idx = idx
                            else:
                                # Fallback: prioritize same category or name similarity
                                if cand.get("category") == anchor.get("category"):
                                    best_idx = idx
                                    break

                    companion = available_pool.pop(best_idx)
                    companion["transit_distance_km"] = best_dist if best_dist < 1000 else None
                    day_places.append(companion)
                    used_places_registry.add(companion["name"])

            daily_assigned_places.append(day_places)

        # -------------------------------------------------------------
        # SYNTHESIS OF PREFERENCE ACTIVITIES IF PLACES RUN OUT
        # -------------------------------------------------------------
        # If an extended trip (e.g. 7 days) exceeds available places, craft unique
        # preference-matched activities tailored to the destination so no places repeat.
        def craft_thematic_activity(slot: str, day_num: int, cluster_name: str) -> dict:
            int_str = " & ".join([i.title() for i in interests[:2]]) if interests else "Sightseeing"
            if "nature" in interests and "adventure" in interests:
                titles = [
                    f"Scenic Alpine Ridge Trail & Viewpoint Hike",
                    f"Hidden Forest Waterfalls & Pine Canopy Trail",
                    f"Valley River Kayaking & Mountain Panorama Walk",
                    f"High-Altitude Meadow Trek & Wilderness Photography",
                ]
                desc = (
                    f"Embark on an invigorating outdoor excursion along {city}'s natural trails. "
                    f"Enjoy pristine mountain air, panoramic ridgeline viewpoints, and active wilderness paths."
                )
                category = "Nature & Adventure"
            elif "history" in interests or "culture" in interests:
                titles = [
                    f"Historic Old Quarter & Artisan Guild Workshop Walk",
                    f"Royal Citadel Ramparts & Ancient Heritage Walk",
                    f"Sacred Shrines & Traditional Architectural Sanctuary",
                    f"City Cultural Museum & Rare Archival Gallery",
                ]
                desc = (
                    f"Immerse yourself in the storied history and architectural wonders of {city}. "
                    f"Discover centuries of heritage, traditional artisan ateliers, and preserved historic relics."
                )
                category = "History & Culture"
            elif "beaches" in interests or "relaxation" in interests:
                titles = [
                    f"Secluded Coastal Cove Swim & Seaside Hammock Pavilion",
                    f"Natural Mineral Spa Therapy & Restorative Wellness",
                    f"Sunset Lagoon Catamaran Sail & Gentle Ocean Breeze",
                    f"Quiet Coastal Promenade Stroll & Reading Sanctuary",
                ]
                desc = (
                    f"Unwind with dedicated rejuvenation along {city}'s tranquil shores. "
                    f"Experience serene coastal waters, gentle sea breezes, and unhurried wellness rest."
                )
                category = "Beaches & Relaxation"
            elif "food" in interests and "photography" in interests:
                titles = [
                    f"Artisan Culinary Market Walk & Street Photography Crawl",
                    f"Golden Hour Skyline Panorama & Rooftop Tasting",
                    f"Traditional Regional Cooking Masterclass & Chef's Table",
                    f"Atmospheric Lantern Alley Stroll & Night Photography",
                ]
                desc = (
                    f"Capture the vibrant flavors and photogenic vistas of {city}. "
                    f"Sample local specialties, explore bustling market lanes, and frame memorable travel compositions."
                )
                category = "Food & Photography"
            else:
                titles = [
                    f"Curated {city} Cultural Walk & Artisan Craft Discovery",
                    f"Panoramic City Viewpoint & Historic Boulevard Walk",
                    f"Botanical Garden Serenity & Local Heritage Discovery",
                    f"Riverside Promenade & Architectural Highlights Walk",
                ]
                desc = (
                    f"Explore curated neighborhood landmarks and vibrant streets of {city}. "
                    f"Featuring photogenic highlights, authentic regional character, and welcoming local ambiance."
                )
                category = "Sightseeing & Culture"

            title = titles[(day_num - 1) % len(titles)]
            return {
                "name": title,
                "category": category,
                "location": f"Central District, {city}",
                "description": desc,
                "estimated_duration": "2 - 2.5 hours",
                "estimated_cost": estimate_activity_cost(category, style, currency),
                "why_it_matches": f"Crafted specifically for your {int_str} focus with authentic local character.",
            }

        # -------------------------------------------------------------
        # GENERATE STRUCTURED DAY-BY-DAY ITINERARY
        # -------------------------------------------------------------
        days = []
        bb = state.get("costs", {}).get("breakdown", {})
        daily_stay_cost = round(bb.get("stay", round(budget * 0.35)) / max(1, nights))
        daily_food_cost = round(bb.get("food", round(budget * 0.22)) / max(1, total_days))
        daily_act_cost = round(bb.get("activities", round(budget * 0.12)) / max(1, total_days))
        daily_transit_cost = round(bb.get("local_transit", round(budget * 0.05)) / max(1, total_days))
        daily_total_estimate = daily_stay_cost + daily_food_cost + daily_act_cost + daily_transit_cost

        for i in range(total_days):
            current_date = start + timedelta(days=i)
            day_num = i + 1
            meals = meal_engine.get_meals_for_day(i)
            assigned = daily_assigned_places[i]
            day_activities: list[dict] = []
            day_place_names = [p["name"] for p in assigned]

            # ---------------------------------------------------------
            # DAY 1: ARRIVAL & ACCLIMATIZATION
            # ---------------------------------------------------------
            if i == 0:
                theme = "Arrival & Settle In"
                time_m = "10:00 AM - 01:00 PM"
                time_a = "02:30 PM - 05:00 PM"
                time_e = "06:30 PM - 09:30 PM"

                morning_text = (
                    f"[{time_m}] Arrival & Check-In: Arrive in {city}, meet your transfer to {stay_title}, "
                    f"complete check-in, and unpack comfortably. Rest after your journey and enjoy fresh welcome refreshments."
                )
                act_m = {
                    "name": f"Arrival & Check-In at {stay_title}",
                    "time_slot": "Morning",
                    "time_window": time_m,
                    "location": f"{stay_title}, {city}",
                    "category": "Arrival & Transfer",
                    "estimated_duration": "2 - 3 hours",
                    "estimated_cost": "Included in Stay & Flight",
                    "why_it_matches": f"Smooth arrival and settling into your preferred {style} accommodation.",
                    "transit_info": "Airport / Station transfer to hotel: ~25-35 mins",
                }
                day_activities.append(act_m)

                if assigned:
                    p1 = assigned[0]
                    p1_cost = estimate_activity_cost(p1.get("category", ""), style, currency)
                    p1_dur = p1.get("estimated_duration") or "2 hours"
                    afternoon_text = (
                        f"[{time_a}] Introductory Visit to {p1['name']}: {(p1.get('description') or p1.get('name') or 'Scenic sight')[:140]}... "
                        f"Category: {p1.get('category', 'Sightseeing')}. (Est. duration: {p1_dur}, Cost: {p1_cost}). "
                        f"Why: {p1.get('why_it_matches', 'Gentle scenic introduction to the destination')}."
                    )
                    act_a = {
                        "name": p1["name"],
                        "time_slot": "Afternoon",
                        "time_window": time_a,
                        "location": p1.get("address") or p1.get("location") or f"{city} Center",
                        "category": p1.get("category", "Sightseeing"),
                        "estimated_duration": p1_dur,
                        "estimated_cost": p1_cost,
                        "why_it_matches": p1.get("why_it_matches") or f"Matches your interest in {', '.join(interests[:2])}.",
                        "transit_info": "Convenient short transfer from accommodation (~10 mins)",
                    }
                else:
                    afternoon_text = (
                        f"[{time_a}] Neighborhood Orientation Walk: Take a gentle, unhurried stroll around {city}'s "
                        f"historic streets, discover charming local storefronts, and relax at a welcoming outdoor cafe."
                    )
                    act_a = {
                        "name": f"Historic {city} Neighborhood Orientation",
                        "time_slot": "Afternoon",
                        "time_window": time_a,
                        "location": f"Neighborhood surrounding {stay_title}",
                        "category": "Orientation & Leisure",
                        "estimated_duration": "2 hours",
                        "estimated_cost": format_cost_range(0, 5, currency, "(Free stroll & cafe coffee)"),
                        "why_it_matches": "Gentle acclimatization matching your travel pace.",
                        "transit_info": "Immediate walking distance from accommodation",
                    }
                day_activities.append(act_a)

                evening_text = (
                    f"[{time_e}] Welcome Dinner & Evening Rest: Savor an authentic dinner featuring {meals['dinner']}. "
                    f"Followed by an unhurried twilight stroll and early rest to recharge for tomorrow's exploration."
                )
                act_e = {
                    "name": f"Welcome Dinner & Evening Stroll in {city}",
                    "time_slot": "Evening",
                    "time_window": time_e,
                    "location": f"Local Restaurant District, {city}",
                    "category": "Dining & Leisure",
                    "estimated_duration": "2.5 hours",
                    "estimated_cost": format_cost_range(25, 45, currency, "per person"),
                    "why_it_matches": "Authentic regional culinary introduction.",
                    "transit_info": "Short 5-10 min walk from hotel",
                }
                day_activities.append(act_e)

                desc = f"Arrival in {city}. Settle into {stay_title}, ease into the regional tempo, and enjoy your first authentic evening meal."
                day_img = assigned[0].get("image_url") if assigned else "/images/hero.jpg"

            # ---------------------------------------------------------
            # FINAL DAY: FAREWELL & DEPARTURE
            # ---------------------------------------------------------
            elif i == total_days - 1:
                theme = "Farewell & Departure"
                time_m = "09:00 AM - 11:30 AM"
                time_a = "12:00 PM - 03:00 PM"
                time_e = "04:30 PM - 08:00 PM"

                if assigned:
                    p1 = assigned[0]
                    p1_cost = estimate_activity_cost(p1.get("category", ""), style, currency)
                    p1_dur = p1.get("estimated_duration") or "2 hours"
                    morning_text = (
                        f"[{time_m}] Farewell Visit to {p1['name']}: {(p1.get('description') or p1.get('name') or 'Scenic sight')[:130]}... "
                        f"(Est. duration: {p1_dur}, Cost: {p1_cost}). "
                        f"Pick up authentic local artisan keepsakes and capture final memorable photos."
                    )
                    act_m = {
                        "name": f"Final Visit: {p1['name']}",
                        "time_slot": "Morning",
                        "time_window": time_m,
                        "location": p1.get("address") or p1.get("location") or f"{city} Center",
                        "category": p1.get("category", "Sightseeing"),
                        "estimated_duration": p1_dur,
                        "estimated_cost": p1_cost,
                        "why_it_matches": p1.get("why_it_matches") or "Memorable final highlight of your trip.",
                        "transit_info": "Close proximity to hotel / city center (~10 mins)",
                    }
                else:
                    morning_text = (
                        f"[{time_m}] Artisan Bazaars & Souvenir Promenade: Enjoy breakfast featuring {meals['breakfast']}, "
                        f"followed by an unhurried visit to {city}'s central artisan craft markets for authentic souvenirs."
                    )
                    act_m = {
                        "name": f"Artisan Keepsakes & Morning Promenade in {city}",
                        "time_slot": "Morning",
                        "time_window": time_m,
                        "location": f"Artisan Market District, {city}",
                        "category": "Shopping & Culture",
                        "estimated_duration": "2 hours",
                        "estimated_cost": f"Free to browse ({format_cost_range(10, 25, currency, 'souvenirs optional')})",
                        "why_it_matches": "Relaxed cultural shopping before departure.",
                        "transit_info": "Walking distance from accommodation",
                    }
                day_activities.append(act_m)

                afternoon_text = (
                    f"[{time_a}] Farewell Lunch & Check-Out: Savor a celebrated farewell lunch featuring {meals['lunch']}. "
                    f"Return to {stay_title}, complete packing, check out, and meet your transfer to the departure terminal."
                )
                act_a = {
                    "name": f"Farewell Lunch & Check-Out at {stay_title}",
                    "time_slot": "Afternoon",
                    "time_window": time_a,
                    "location": f"{stay_title}, {city}",
                    "category": "Departure & Transit",
                    "estimated_duration": "2.5 hours",
                    "estimated_cost": format_cost_range(20, 35, currency, "per person"),
                    "why_it_matches": "Smooth, stress-free checkout and transfer.",
                    "transit_info": "Transfer to Airport / Departure Station: ~30-40 mins",
                }
                day_activities.append(act_a)

                evening_text = (
                    f"[{time_e}] Departure Journey: Scheduled onward flight / transit journey home carrying "
                    f"cherished memories of your personalized {style.lower()} trip to {city}."
                )
                act_e = {
                    "name": f"Onward Departure from {city}",
                    "time_slot": "Evening",
                    "time_window": time_e,
                    "location": f"{city} International Terminal / Station",
                    "category": "Departure & Transit",
                    "estimated_duration": "Onward Transit",
                    "estimated_cost": "Included in Transit",
                    "why_it_matches": "Concluding your tailored itinerary on schedule.",
                    "transit_info": "Terminal check-in & departure boarding",
                }
                day_activities.append(act_e)

                desc = f"Final day in {city}. Unhurried souvenir shopping, celebrated farewell lunch, smooth check-out, and onward departure."
                day_img = assigned[0].get("image_url") if assigned else "/images/hero.jpg"

            # ---------------------------------------------------------
            # INTERMEDIATE FULL DAYS: LOCATION-OPTIMIZED
            # ---------------------------------------------------------
            else:
                p1 = assigned[0] if len(assigned) > 0 else craft_thematic_activity("morning", day_num, "Sector A")
                p2 = assigned[1] if len(assigned) > 1 else (craft_thematic_activity("afternoon", day_num, "Sector A") if not pace_is_relaxed else None)
                p3 = assigned[2] if len(assigned) > 2 else (craft_thematic_activity("evening", day_num, "Sector A") if pace_is_fast else None)

                # Dynamic, varied theme matching scheduled places and interests
                if assigned and assigned[0].get("category"):
                    cat_clean = assigned[0]["category"].split("&")[0].strip()
                    theme = f"Day {day_num}: {cat_clean} & {city} Discovery"
                elif "nature" in interests and "adventure" in interests:
                    nature_themes = [
                        "Alpine Ridge Trails & High Meadow Vistas",
                        "Cascading Waterfalls & Forest Sanctuary Walk",
                        "Glacial River Valleys & Outdoor Excursion",
                        "Scenic Mountain Pass & Panoramic Trek",
                        "Wilderness Canopy & Nature Reserve Expedition",
                    ]
                    theme = nature_themes[(i - 1) % len(nature_themes)]
                elif "history" in interests or "culture" in interests:
                    culture_themes = [
                        "Ancient Citadels & Royal Fortress Ramparts",
                        "Architectural Masterpieces & Historic Palaces",
                        "Artisan Ateliers & Sacred Heritage Shrines",
                        "Cultural Museums & Walled Quarter Legends",
                        "UNESCO Landmarks & Historic Traditions Walk",
                    ]
                    theme = culture_themes[(i - 1) % len(culture_themes)]
                elif "beaches" in interests or "relaxation" in interests:
                    beach_themes = [
                        "Crescent Sands & Turquoise Coastal Breezes",
                        "Tranquil Lagoon Waters & Seaside Wellness",
                        "Oceanfront Relaxation & Palm Grove Stroll",
                        "Hidden Coastal Coves & Sunset Horizons",
                        "Secluded Bay Swimming & Restorative Rejuvenation",
                    ]
                    theme = beach_themes[(i - 1) % len(beach_themes)]
                elif "food" in interests and "photography" in interests:
                    food_themes = [
                        "Morning Golden Hour & Historic Market Tastings",
                        "Panoramic Skylines & Artisan Culinary Crawl",
                        "Heritage Street Photography & Traditional Masterclass",
                        "Atmospheric Alleys & Sunset Gastronomy",
                        "Scenic Viewpoints & Celebrated Tasting Menu",
                    ]
                    theme = food_themes[(i - 1) % len(food_themes)]
                else:
                    theme = f"Day {day_num}: Curated Highlights of {city}"

                # --- Slot 1: Morning Activity ---
                if pace_is_fast:
                    time_m = "08:00 AM - 11:30 AM"
                elif pace_is_relaxed:
                    time_m = "09:30 AM - 12:30 PM"
                else:
                    time_m = "08:45 AM - 12:00 PM"

                p1_dur = p1.get("estimated_duration") or "2.5 - 3 hours"
                p1_cost = estimate_activity_cost(p1.get("category", ""), style, currency)
                p1_transit = "Transit from accommodation: ~15 mins"

                morning_text = (
                    f"[{time_m}] Comprehensive Exploration of {p1['name']}: {(p1.get('description') or p1.get('name') or 'Scenic sight')[:140]}... "
                    f"Category: {p1.get('category', 'Attraction')}. (Duration: {p1_dur}, Cost: {p1_cost}). "
                    f"Why: {p1.get('why_it_matches', 'Aligns with your selected travel preferences')}."
                )
                act_m = {
                    "name": p1["name"],
                    "time_slot": "Morning",
                    "time_window": time_m,
                    "location": p1.get("address") or p1.get("location") or f"{city} Sector",
                    "category": p1.get("category", "Attraction"),
                    "estimated_duration": p1_dur,
                    "estimated_cost": p1_cost,
                    "why_it_matches": p1.get("why_it_matches") or f"Directly reflects your {', '.join(interests[:2])} preferences.",
                    "transit_info": p1_transit,
                }
                day_activities.append(act_m)

                # --- Slot 2: Afternoon Activity ---
                if pace_is_relaxed:
                    time_a = "02:30 PM - 05:30 PM"
                    afternoon_text = (
                        f"[{time_a}] Leisure Lunch & Dedicated Afternoon Rest: Enjoy an unhurried lunch featuring "
                        f"{meals['lunch']}. Spend a dedicated 2.5-hour afternoon relaxation window at {stay_title} "
                        f"(poolside, garden patio, reading, or quiet coffee), strictly honoring your relaxed tempo."
                    )
                    act_a = {
                        "name": f"Leisure Lunch & Afternoon Relaxation at {stay_title}",
                        "time_slot": "Afternoon",
                        "time_window": time_a,
                        "location": f"{stay_title}, {city}",
                        "category": "Rest & Wellness",
                        "estimated_duration": "2.5 - 3 hours",
                        "estimated_cost": format_cost_range(15, 30, currency, "(Lunch & refreshments)"),
                        "why_it_matches": "Dedicated downtime directly reflecting your Relaxed travel pace.",
                        "transit_info": "Zero transit stress; unhurried stroll back to hotel",
                    }
                elif p2:
                    time_a = "01:30 PM - 04:45 PM"
                    p2_dur = p2.get("estimated_duration") or "2 - 2.5 hours"
                    p2_cost = estimate_activity_cost(p2.get("category", ""), style, currency)
                    transit_km = p2.get("transit_distance_km")
                    transit_desc = estimate_transit_info(transit_km)

                    afternoon_text = (
                        f"[{time_a}] Midday Lunch & Nearby Visit to {p2['name']}: Savor lunch featuring {meals['lunch']}, "
                        f"then proceed via {transit_desc} to {p2['name']}. {(p2.get('description') or p2.get('name') or 'Scenic sight')[:130]}... "
                        f"(Duration: {p2_dur}, Cost: {p2_cost}). Geographically clustered with morning sight to eliminate backtracking."
                    )
                    act_a = {
                        "name": p2["name"],
                        "time_slot": "Afternoon",
                        "time_window": time_a,
                        "location": p2.get("address") or p2.get("location") or f"{city} Sector",
                        "category": p2.get("category", "Attraction"),
                        "estimated_duration": p2_dur,
                        "estimated_cost": p2_cost,
                        "why_it_matches": p2.get("why_it_matches") or f"Geographically optimized continuation of {interests[0] if interests else 'sightseeing'}.",
                        "transit_info": transit_desc,
                    }
                else:
                    time_a = "02:00 PM - 04:30 PM"
                    afternoon_text = (
                        f"[{time_a}] Authentic Lunch & Artisan Quarter Stroll: Savor {meals['lunch']}, followed by "
                        f"a curated exploration of {city}'s vibrant local artisan district and boutique workshops."
                    )
                    act_a = {
                        "name": f"{city} Artisan District & Cultural Walk",
                        "time_slot": "Afternoon",
                        "time_window": time_a,
                        "location": f"Artisan Quarter, {city}",
                        "category": "Culture & Shopping",
                        "estimated_duration": "2 hours",
                        "estimated_cost": format_cost_range(15, 25, currency),
                        "why_it_matches": "Authentic local craft and market experience.",
                        "transit_info": "Short 10-15 min stroll from lunch venue",
                    }
                day_activities.append(act_a)

                # --- Slot 3: Evening Activity ---
                time_e = "06:30 PM - 09:30 PM" if not pace_is_fast else "06:00 PM - 10:00 PM"

                if pace_is_fast and p3:
                    p3_dur = p3.get("estimated_duration") or "1.5 - 2 hours"
                    p3_cost = estimate_activity_cost(p3.get("category", ""), style, currency)
                    transit_km = p3.get("transit_distance_km")
                    transit_desc = estimate_transit_info(transit_km)

                    evening_text = (
                        f"[{time_e}] Golden Hour at {p3['name']} & Night Market Dining: Proceed via {transit_desc} to {p3['name']} "
                        f"for golden-hour views ({(p3.get('description') or p3.get('name') or 'Scenic sight')[:100]}...). Conclude with dinner enjoying {meals['dinner']} "
                        f"and an energetic evening night market stroll."
                    )
                    act_e = {
                        "name": f"Golden Hour at {p3['name']} & Evening Dinner",
                        "time_slot": "Evening",
                        "time_window": time_e,
                        "location": p3.get("address") or p3.get("location") or f"{city} Sector",
                        "category": p3.get("category", "Nightlife & Dining"),
                        "estimated_duration": "3 hours",
                        "estimated_cost": f"{p3_cost} + Dinner ({format_cost_range(25, 45, currency)})",
                        "why_it_matches": "High-energy evening exploration matching your Fast-paced preference.",
                        "transit_info": transit_desc,
                    }
                elif pace_is_relaxed:
                    evening_text = (
                        f"[{time_e}] Peaceful Sunset & Regional Dinner: Scenic sunset viewing by the water / panoramic overlook. "
                        f"Followed by an unhurried candlelit dinner savoring {meals['dinner']}. Zero rushed transit."
                    )
                    act_e = {
                        "name": f"Tranquil Sunset & Fine Regional Dinner in {city}",
                        "time_slot": "Evening",
                        "time_window": time_e,
                        "location": f"Scenic Dining Quarter, {city}",
                        "category": "Dining & Relaxation",
                        "estimated_duration": "2.5 hours",
                        "estimated_cost": format_cost_range(30, 55, currency, "per person"),
                        "why_it_matches": "Peaceful, restorative evening perfectly matched to your Relaxed pace.",
                        "transit_info": "Convenient stroll or short 5 min cab ride",
                    }
                else:
                    evening_text = (
                        f"[{time_e}] Twilight Promenade & Celebrated Dinner: Enjoy golden-hour stroll through {city}'s "
                        f"illuminated historic square, followed by dinner at a top-rated local restaurant savoring {meals['dinner']}."
                    )
                    act_e = {
                        "name": f"Twilight Plaza Promenade & Celebrated Dinner in {city}",
                        "time_slot": "Evening",
                        "time_window": time_e,
                        "location": f"Central Square / Riverfront, {city}",
                        "category": "Dining & Culture",
                        "estimated_duration": "2.5 hours",
                        "estimated_cost": format_cost_range(25, 45, currency, "per person"),
                        "why_it_matches": "Balanced evening dining and cultural ambiance.",
                        "transit_info": "Approx. 10 min transit from hotel",
                    }
                day_activities.append(act_e)

                focus_str = f"focusing on {', '.join(interests)}" if interests else "balanced sightseeing"
                desc = (
                    f"Day {day_num} in {city} ({pace} tempo) {focus_str}. "
                    f"Featuring {', '.join(day_place_names) if day_place_names else 'curated landmarks'}."
                )
                day_img = assigned[0].get("image_url") if assigned else "/images/hero.jpg"

            days.append({
                "day": day_num,
                "date": current_date.isoformat(),
                "theme": theme,
                "morning": morning_text,
                "afternoon": afternoon_text,
                "evening": evening_text,
                "stay": stay_title,
                "estimate_usd": round(budget / total_days),
                "estimate_cost": round(budget / total_days),
                "currency": currency,
                "currency_symbol": curr_sym,
                "suggested_places": day_place_names,
                "image_url": day_img,
                "description": desc,
                "pace_notes": pace_note,
                "meal_suggestions": meals,
                "activities": day_activities,
            })

        breakdown = state.get("costs", {}).get("breakdown", {})
        focus = f", tailored to {', '.join(interests)}" if interests else ""
        req_note = f" (Special request noted: {req.get('special_requests')})" if req.get("special_requests") else ""

        dest_info = state.get("destination", {})
        coords = dest_info.get("coordinates")
        formatted_address = dest_info.get("formatted_address")
        country = dest_info.get("country")

        state["itinerary"] = {
            "destination": city,
            "dates": {"start": req["start_date"], "end": req["end_date"], "nights": nights},
            "travelers": req.get("travelers", 1),
            "interests": req.get("interests", []),
            "budget": budget,
            "currency": currency,
            "currency_symbol": curr_sym,
            "budget_breakdown": breakdown,
            "coordinates": coords,
            "formatted_address": formatted_address,
            "country": country,
            "weather": state.get("weather", {}),
            "summary": (
                f"A {nights}-night personalized {pace_display} {style.lower()} journey to {city} for "
                f"{req.get('travelers', 1)} traveler(s) on a {currency} {budget:,} budget{focus}. "
                f"Featuring non-repeating activities, authentic dining, and curated attractions{req_note}."
            ),
            "days": days,
            "places_to_visit": raw_places,
            "hotels": hotels,
            "transport": state.get("transport", {}),
            "preferences_applied": {
                "style": style,
                "pace": pace,
                "accommodation": accommodation,
                "food": food_pref,
                "currency": currency,
                "interests": interests,
            },
        }
        return state
