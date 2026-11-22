"""SerpApi client for Google Flights and Google Hotels."""
import datetime
import difflib
import logging
import re
from typing import Any
import httpx

from app.api_clients.currency import currency_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Common airport code mappings (cities, common phonetic variations, and country gateways)
AIRPORT_CODES = {
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "goa": "GOI",
    "dabolim": "GOI",
    "mopa": "GOX",
    "bangalore": "BLR",
    "banglore": "BLR",
    "bengaluru": "BLR",
    "bengalore": "BLR",
    "hyderabad": "HYD",
    "chennai": "MAA",
    "madras": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "ahmedabad": "AMD",
    "jaipur": "JAI",
    "manali": "KUU",
    "kullu": "KUU",
    "chandigarh": "IXC",
    "shimla": "SLV",
    "dharamshala": "DHM",
    "amritsar": "ATQ",
    "varanasi": "VNS",
    "kochi": "COK",
    "cochin": "COK",
    "pune": "PNQ",
    "srinagar": "SXR",
    "leh": "IXL",
    "dubai": "DXB",
    "abu dhabi": "AUH",
    "doha": "DOH",
    "singapore": "SIN",
    "bangkok": "BKK",
    "chiang mai": "CNX",
    "phuket": "HKT",
    "bali": "DPS",
    "denpasar": "DPS",
    "kuala lumpur": "KUL",
    "london": "LHR",
    "paris": "CDG",
    "new york": "JFK",
    "san francisco": "SFO",
    "los angeles": "LAX",
    "chicago": "ORD",
    "tokyo": "HND",
    "kyoto": "KIX",
    "osaka": "KIX",
    "amsterdam": "AMS",
    "rome": "FCO",
    "milan": "MXP",
    "florence": "FLR",
    "venice": "VCE",
    "berlin": "BER",
    "frankfurt": "FRA",
    "munich": "MUC",
    "zurich": "ZRH",
    "geneva": "GVA",
    "basel": "BSL",
    "interlaken": "ZRH",
    "bern": "BRN",
    "vienna": "VIE",
    "prague": "PRG",
    "budapest": "BUD",
    "barcelona": "BCN",
    "madrid": "MAD",
    "lisbon": "LIS",
    "athens": "ATH",
    "santorini": "JTR",
    "sydney": "SYD",
    "melbourne": "MEL",
    "auckland": "AKL",
    "queenstown": "ZQN",
    "toronto": "YYZ",
    "vancouver": "YVR",
    "cairo": "CAI",
    "istanbul": "IST",
    "maldives": "MLE",
    "male": "MLE",
    "colombo": "CMB",
    "kathmandu": "KTM",
    "seoul": "ICN",
    "taipei": "TPE",
    # Vietnam and Southeast Asia Gateways
    "vietnam": "HAN",
    "vitnam": "HAN",
    "vietnem": "HAN",
    "viet nam": "HAN",
    "hanoi": "HAN",
    "ho chi minh": "SGN",
    "ho chi minh city": "SGN",
    "saigon": "SGN",
    "da nang": "DAD",
    "danang": "DAD",
    "thailand": "BKK",
    "indonesia": "DPS",
    "jakarta": "CGK",
    "malaysia": "KUL",
    "philippines": "MNL",
    "manila": "MNL",
    "japan": "HND",
    "south korea": "ICN",
    "korea": "ICN",
    "taiwan": "TPE",
    "united arab emirates": "DXB",
    "uae": "DXB",
    "united kingdom": "LHR",
    "uk": "LHR",
    "england": "LHR",
    "france": "CDG",
    "germany": "FRA",
    "italy": "FCO",
    "spain": "BCN",
    "switzerland": "ZRH",
    "netherlands": "AMS",
    "australia": "SYD",
    "new zealand": "AKL",
    "canada": "YYZ",
    "usa": "JFK",
    "united states": "JFK",
    "america": "JFK",
    "south africa": "CPT",
    "egypt": "CAI",
    "turkey": "IST",
    "turkiye": "IST",
    "greece": "ATH",
    "portugal": "LIS",
    "brazil": "GIG",
    "mexico": "MEX",
    "peru": "LIM",
    "argentina": "EZE",
    "india": "DEL",
    "marrakech": "RAK",
    "casablanca": "CMN",
    "cancun": "CUN",
    "mexico city": "MEX",
    "buenos aires": "EZE",
    "rio de janeiro": "GIG",
    "lima": "LIM",
    "cape town": "CPT",
    "palawan": "PPS",
    "puerto princesa": "PPS",
    "el nido": "ENI",
    "kerala": "COK",
    "hampi": "VDY",
    "vidyanagar": "VDY",
    "hubli": "HBX",
    "hubballi": "HBX",
    "udaipur": "UDR",
    "jodhpur": "JDH",
    "jaisalmer": "JSA",
    "agra": "AGR",
    "dehradun": "DED",
    "rishikesh": "DED",
    "haridwar": "DED",
    "mysore": "MYQ",
    "mysuru": "MYQ",
    "madurai": "IXM",
    "coimbatore": "CJB",
    "mangalore": "IXE",
    "mangaluru": "IXE",
    "bagdogra": "IXB",
    "darjeeling": "IXB",
    "gangtok": "IXB",
    "port blair": "IXZ",
    "andaman": "IXZ",
    "nha trang": "CXR",
    "cam ranh": "CXR",
    "phu quoc": "PQC",
    "krabi": "KBV",
    "koh samui": "USM",
    "siem reap": "SAI",
    "phnom penh": "PNH",
    "boracay": "MPH",
    "cebu": "CEB",
    "johannesburg": "JNB",
    "durban": "DUR",
    "nairobi": "NBO",
    "vancouver": "YVR",
    "montreal": "YUL",
    "calgary": "YYC",
}


def resolve_airport_code(text: str | None) -> str | None:
    """Accurately resolves an airport code using exact, substring, and fuzzy matching."""
    if not text:
        return None
    cleaned = text.strip()
    if len(cleaned) == 3 and cleaned.isalpha():
        return cleaned.upper()
    lower = re.sub(r"[^a-z0-9 ]+", " ", cleaned.lower()).strip()
    if not lower:
        return None

    # 1. Exact match
    if lower in AIRPORT_CODES:
        return AIRPORT_CODES[lower]

    # 2. Word-boundary or substring search
    padded = f" {lower} "
    for city, code in AIRPORT_CODES.items():
        if f" {city} " in padded:
            return code
    for city, code in AIRPORT_CODES.items():
        if city in lower or (len(city) > 4 and lower in city):
            return code

    # 3. Fuzzy matching for phonetic typos (e.g. "banglore", "vitnam", "vietnem")
    close = difflib.get_close_matches(lower, AIRPORT_CODES.keys(), n=1, cutoff=0.7)
    if close:
        return AIRPORT_CODES[close[0]]

    # 4. Word-by-word fuzzy matching
    for w in lower.split():
        if len(w) >= 4:
            close_w = difflib.get_close_matches(w, AIRPORT_CODES.keys(), n=1, cutoff=0.75)
            if close_w:
                return AIRPORT_CODES[close_w[0]]

    # 5. Check nearby transit registry for destinations without direct commercial airports
    try:
        from app.services.transit_service import get_nearby_transit
        nearby = get_nearby_transit(lower)
        if nearby and nearby.get("nearby_airport"):
            return nearby["nearby_airport"]["code"]
    except Exception:
        pass

    return None


class SerpApiClient:
    BASE_URL = "https://serpapi.com/search.json"

    def __init__(self, api_key: str | None = None, key: str | None = None):
        self.api_key = api_key or key or settings.SERPAPI_API_KEY

    _resolve_airport_code = staticmethod(resolve_airport_code)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search_hotels(
        self,
        destination: str,
        check_in_date: str,
        check_out_date: str,
        travelers: int = 2,
        currency: str = "USD",
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        """Search real hotels via SerpApi Google Hotels engine."""
        if not self.is_configured() or not destination:
            return []

        # Validate dates are not in the past
        today_str = datetime.date.today().isoformat()
        if check_in_date < today_str:
            logger.info("Check-in date %s is in the past; skipping live hotel search.", check_in_date)
            return []

        raw_dest = destination.strip()
        lower_raw = raw_dest.lower()
        for prefix in ["hotels and boutique inns in ", "luxury resorts in ", "homestays in ", "hostels in ", "resorts in ", "hotels in "]:
            if lower_raw.startswith(prefix):
                lower_raw = lower_raw[len(prefix):].strip()
                break

        if lower_raw in {"vietnem", "vitnam", "viet nam"}:
            city_target = "Vietnam"
        elif lower_raw in {"banglore", "bengaluru", "bengalore"}:
            city_target = "Bangalore"
        else:
            city_target = lower_raw.title()

        clean_q = f"hotels in {city_target}"

        params = {
            "engine": "google_hotels",
            "q": clean_q,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "adults": max(1, travelers),
            "currency": currency,
            "api_key": self.api_key,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(self.BASE_URL, params=params)
                if resp.status_code != 200:
                    logger.warning("SerpApi Hotels failed: HTTP %s", resp.status_code)
                    return []

                data = resp.json()
                properties = data.get("properties", [])
                hotels = []

                for prop in properties[:limit]:
                    rate = prop.get("rate_per_night", {})
                    lowest_price = rate.get("lowest") or rate.get("extracted_lowest") or rate.get("display_price")
                    converted_hotel = currency_client.parse_and_convert(lowest_price, target_currency=currency, default_source_currency=currency)
                    price_str = converted_hotel["formatted"] if converted_hotel.get("converted_amount") else "Check dates"

                    images = prop.get("images", [])
                    thumb = images[0].get("thumbnail") if images else None

                    hotels.append({
                        "name": prop.get("name"),
                        "price_per_night": price_str,
                        "price_amount": converted_hotel.get("converted_amount"),
                        "currency": currency.upper(),
                        "original_price": str(lowest_price) if lowest_price is not None else None,
                        "rating": prop.get("overall_rating", 4.5),
                        "reviews_count": prop.get("reviews", 0),
                        "amenities": prop.get("amenities", [])[:4],
                        "description": prop.get("description") or f"Top-rated stay in {destination}.",
                        "thumbnail": thumb,
                        "link": prop.get("link") or f"https://www.google.com/travel/hotels?q={clean_q.replace(' ', '+')}",
                        "source": "Google Hotels via SerpApi",
                        "is_live": True,
                        "status": "Confirmed Live Availability",
                    })

                return hotels
        except Exception as e:
            logger.error("SerpApi search_hotels error: %s", e)
            return []

    def search_flights(
        self,
        destination: str,
        outbound_date: str,
        return_date: str,
        origin: str | None = None,
        travelers: int = 1,
        currency: str = "USD",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search live flights via SerpApi Google Flights engine."""
        if not self.is_configured() or not destination:
            return []

        today_str = datetime.date.today().isoformat()
        actual_outbound = outbound_date
        actual_return = return_date
        if actual_outbound < today_str:
            try:
                d_out = datetime.date.fromisoformat(actual_outbound)
                d_ret = datetime.date.fromisoformat(actual_return) if actual_return else d_out + datetime.timedelta(days=7)
                diff = max(1, (d_ret - d_out).days)
                future_out = datetime.date.today() + datetime.timedelta(days=7)
                future_ret = future_out + datetime.timedelta(days=diff)
                actual_outbound = future_out.isoformat()
                actual_return = future_ret.isoformat()
                logger.info("Outbound flight date %s is in the past; searching upcoming live fares for %s -> %s", outbound_date, actual_outbound, actual_return)
            except Exception:
                actual_outbound = (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
                actual_return = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()

        arr_code = resolve_airport_code(destination)
        dep_code = resolve_airport_code(origin) if origin else None

        # Do NOT substitute unrelated random hubs (e.g. BOM/DEL) when user entered specific cities!
        if not arr_code or not dep_code:
            logger.info("Could not resolve specific airport codes for origin='%s' (%s) -> destination='%s' (%s)", origin, dep_code, destination, arr_code)
            return []

        # Prevent circular route
        if dep_code == arr_code:
            logger.warning("Circular route detected for %s to %s", dep_code, arr_code)
            return []

        params = {
            "engine": "google_flights",
            "departure_id": dep_code,
            "arrival_id": arr_code,
            "outbound_date": actual_outbound,
            "return_date": actual_return,
            "currency": currency,
            "adults": max(1, travelers),
            "api_key": self.api_key,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(self.BASE_URL, params=params)
                if resp.status_code != 200:
                    logger.warning("SerpApi Flights failed: HTTP %s", resp.status_code)
                    return []

                data = resp.json()
                flight_groups = data.get("best_flights", []) + data.get("other_flights", [])
                results = []

                from app.services.transit_service import get_nearby_transit
                nearby_transit = get_nearby_transit(destination)
                is_nearby_hub = bool(nearby_transit and not nearby_transit.get("has_direct_airport"))
                nearby_distance = nearby_transit.get("nearby_airport", {}).get("distance", "") if nearby_transit else ""

                for group in flight_groups[:limit]:
                    flights_list = group.get("flights", [])
                    if not flights_list:
                        continue
                    first_leg = flights_list[0]
                    final_leg = flights_list[-1]

                    dep_info = first_leg.get("departure_airport", {})
                    arr_info = final_leg.get("arrival_airport", {})

                    duration_mins = group.get("total_duration") or sum(l.get("duration", 0) for l in flights_list)
                    hrs = duration_mins // 60
                    mins = duration_mins % 60
                    duration_str = f"{hrs}h {mins}m" if hrs else f"{mins}m"

                    price_val = group.get("price")
                    converted_flight = currency_client.parse_and_convert(price_val, target_currency=currency, default_source_currency=currency)
                    price_str = converted_flight["formatted"] if converted_flight.get("converted_amount") else "Available"

                    results.append({
                        "airline": first_leg.get("airline", "Commercial Airline"),
                        "flight_number": first_leg.get("flight_number", ""),
                        "airline_logo": first_leg.get("airline_logo"),
                        "departure_time": dep_info.get("time", ""),
                        "departure_airport": dep_info.get("name", dep_code),
                        "departure_code": dep_info.get("id", dep_code),
                        "arrival_time": arr_info.get("time", ""),
                        "arrival_airport": arr_info.get("name", arr_code),
                        "arrival_code": arr_info.get("id", arr_code),
                        "duration": duration_str,
                        "stops": "Nonstop" if len(flights_list) == 1 else f"{len(flights_list) - 1} stop(s)",
                        "price": price_str,
                        "price_amount": converted_flight.get("converted_amount"),
                        "currency": currency.upper(),
                        "original_price": str(price_val) if price_val is not None else None,
                        "booking_link": (
                            f"https://www.google.com/travel/flights?q=flights+from+{dep_code}+to+{arr_code}"
                        ),
                        "source": "Google Flights via SerpApi",
                        "is_live": True,
                        "status": "Confirmed Live Airfare",
                        "is_nearby_hub": is_nearby_hub,
                        "nearby_destination": destination if is_nearby_hub else None,
                        "hub_distance": nearby_distance if is_nearby_hub else None,
                        "hub_note": f"Lands at {arr_code} ({nearby_distance} to {destination})" if is_nearby_hub else None,
                    })

                return results
        except Exception as e:
            logger.error("SerpApi search_flights error: %s", e)
            return []
        except Exception as e:
            logger.error("SerpApi search_flights error: %s", e)
            return []

    def search_attractions(
        self,
        destination: str,
        interests: list[str] | None = None,
        limit: int = 15,
    ) -> list[dict[str, Any]]:
        """Search real attractions, landmarks, and sights via SerpApi Google Search."""
        if not self.is_configured() or not destination or not destination.strip():
            return []

        clean_dest = destination.strip()
        query_str = f"top sights in {clean_dest}"

        params = {
            "engine": "google",
            "q": query_str,
            "hl": "en",
            "gl": "us",
            "api_key": self.api_key,
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(self.BASE_URL, params=params)
                if resp.status_code != 200:
                    logger.warning("SerpApi Google search failed: HTTP %s", resp.status_code)
                    return []

                data = resp.json()
                sights = data.get("top_sights", {}).get("sights", [])
                places = []

                for s in sights[:limit]:
                    title = s.get("title")
                    if not title or len(title.strip()) < 2:
                        continue

                    desc = s.get("description") or ""
                    snippet = s.get("snippet") or ""
                    full_desc = desc if len(desc) > 20 else (snippet or f"Premier landmark and tourist highlight in {clean_dest}.")

                    # Infer readable category based on keywords in title & description
                    comb = f"{title} {desc} {snippet}".lower()
                    if any(k in comb for k in ["park", "garden", "nature", "mountain", "valley", "lake", "forest", "falls", "river", "peak"]):
                        cat = "Nature & Outdoors"
                        duration = "3 - 4 hours"
                        tags = ["nature", "scenic"]
                    elif any(k in comb for k in ["museum", "gallery", "art", "center", "theatre", "opera"]):
                        cat = "Museum & Art"
                        duration = "2 - 3 hours"
                        tags = ["culture", "art"]
                    elif any(k in comb for k in ["temple", "shrine", "castle", "fort", "palace", "citadel", "ruin", "ancient", "church", "cathedral", "basilica", "monument"]):
                        cat = "History & Heritage"
                        duration = "2 hours"
                        tags = ["history", "culture"]
                    elif any(k in comb for k in ["beach", "cove", "coast", "bay", "island", "sea"]):
                        cat = "Beaches & Relaxation"
                        duration = "3 - 4 hours"
                        tags = ["beaches", "relaxation"]
                    elif any(k in comb for k in ["market", "street", "food", "culinary", "bazaar"]):
                        cat = "Food & Culture"
                        duration = "1.5 - 2 hours"
                        tags = ["food", "culture", "shopping"]
                    elif any(k in comb for k in ["view", "deck", "skyline", "tower", "panoramic"]):
                        cat = "Photography & Viewpoints"
                        duration = "1.5 hours"
                        tags = ["photography", "scenic"]
                    else:
                        cat = "Sight & Attraction"
                        duration = "2 hours"
                        tags = ["culture", "sightseeing"]

                    thumb = s.get("thumbnail") or "/images/hero.jpg"
                    rating_val = s.get("rating")
                    try:
                        rating = round(float(rating_val), 1) if rating_val else 4.7
                    except (ValueError, TypeError):
                        rating = 4.7

                    places.append({
                        "name": title.strip(),
                        "description": full_desc,
                        "category": cat,
                        "location": clean_dest,
                        "image_url": thumb,
                        "rating": rating,
                        "estimated_duration": duration,
                        "visit_info": desc or f"Must-see landmark in {clean_dest}",
                        "source": "Google via SerpApi (Verified)",
                        "tags": tags,
                    })

                # If no top_sights returned, extract organic results as fallback points of interest
                if not places:
                    for org in data.get("organic_results", [])[:5]:
                        title = org.get("title", "").split(" - ")[0].split(" | ")[0]
                        snippet = org.get("snippet", "")
                        if title and len(title) > 3 and "things to do" not in title.lower():
                            places.append({
                                "name": title.strip(),
                                "description": snippet or f"Celebrated travel highlight in {clean_dest}.",
                                "category": "Sight & Attraction",
                                "location": clean_dest,
                                "image_url": "/images/hero.jpg",
                                "rating": 4.6,
                                "estimated_duration": "2 - 3 hours",
                                "visit_info": f"Featured sight in {clean_dest}",
                                "source": "Google Search via SerpApi",
                                "tags": ["culture", "sightseeing"],
                            })

                return places
        except Exception as e:
            logger.error("SerpApi search_attractions error: %s", e)
            return []


serpapi_client = SerpApiClient()
