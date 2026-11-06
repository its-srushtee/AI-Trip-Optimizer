"""SerpApi client for Google Flights and Google Hotels."""
import datetime
import logging
from typing import Any
import httpx

from app.api_clients.currency import currency_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Common airport code mappings
AIRPORT_CODES = {
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "goa": "GOI",
    "dabolim": "GOI",
    "mopa": "GOX",
    "bangalore": "BLR",
    "bengaluru": "BLR",
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
    "hanoi": "HAN",
    "ho chi minh": "SGN",
    "da nang": "DAD",
    "marrakech": "RAK",
    "casablanca": "CMN",
    "cancun": "CUN",
    "mexico city": "MEX",
    "buenos aires": "EZE",
    "rio de janeiro": "GIG",
    "lima": "LIM",
    "cape town": "CPT",
}


def resolve_airport_code(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = text.strip()
    if len(cleaned) == 3 and cleaned.isalpha():
        return cleaned.upper()
    lower = cleaned.lower()
    for city, code in AIRPORT_CODES.items():
        if city in lower or lower in city:
            return code
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

        clean_q = destination.strip()
        if not any(clean_q.lower().startswith(prefix) for prefix in ["hotels in", "hostels in", "luxury resorts in", "homestays in", "resorts in"]):
            clean_q = f"hotels in {clean_q}"

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
        if outbound_date < today_str:
            logger.info("Outbound flight date %s is in the past; skipping live flight search.", outbound_date)
            return []

        arr_code = resolve_airport_code(destination)
        if not arr_code:
            arr_code = "GOI" if "goa" in destination.lower() else "DEL"

        dep_code = resolve_airport_code(origin) if origin else None
        if not dep_code:
            dep_code = "BOM" if arr_code == "GOI" else "DEL"

        # Prevent circular route
        if dep_code == arr_code:
            dep_code = "BOM" if arr_code != "BOM" else "DEL"

        params = {
            "engine": "google_flights",
            "departure_id": dep_code,
            "arrival_id": arr_code,
            "outbound_date": outbound_date,
            "return_date": return_date,
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

                for group in flight_groups[:limit]:
                    flights_list = group.get("flights", [])
                    if not flights_list:
                        continue
                    leg = flights_list[0]

                    dep_info = leg.get("departure_airport", {})
                    arr_info = leg.get("arrival_airport", {})

                    duration_mins = group.get("total_duration") or leg.get("duration", 0)
                    hrs = duration_mins // 60
                    mins = duration_mins % 60
                    duration_str = f"{hrs}h {mins}m" if hrs else f"{mins}m"

                    price_val = group.get("price")
                    converted_flight = currency_client.parse_and_convert(price_val, target_currency=currency, default_source_currency=currency)
                    price_str = converted_flight["formatted"] if converted_flight.get("converted_amount") else "Available"

                    results.append({
                        "airline": leg.get("airline", "Commercial Airline"),
                        "flight_number": leg.get("flight_number", ""),
                        "airline_logo": leg.get("airline_logo"),
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
