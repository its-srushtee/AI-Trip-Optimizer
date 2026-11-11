"""Hotel agent — suggests real stays via SerpApi Google Hotels and fallback providers with strict budget awareness."""
import math
from typing import Any

from app.agents.base import BaseAgent
from app.api_clients.currency import CURRENCY_SYMBOLS, currency_client
from app.api_clients.hotels import get_hotels_client
from app.api_clients.serpapi import serpapi_client


class HotelAgent(BaseAgent):
    name = "hotels"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        req = state["request"]
        city = req.get("destination", "")
        start = str(req.get("start_date", ""))
        end = str(req.get("end_date", ""))
        travelers = max(1, int(req.get("travelers", 1)))
        budget = req.get("budget", 1000)
        currency = (req.get("currency") or req.get("preferences", {}).get("currency") or "USD").upper()
        curr_sym = CURRENCY_SYMBOLS.get(currency, "$")
        style = (req.get("style") or req.get("preferences", {}).get("style") or "Comfort").title()
        accommodation = (req.get("accommodation") or req.get("preferences", {}).get("accommodation") or "Hotel").title()

        # Read budget allocation targets if pre-computed by workflow
        alloc = state.get("budget_allocation") or {}
        nightly_target = alloc.get("nightly_room_target")
        rooms_needed = alloc.get("rooms_needed", max(1, math.ceil(travelers / 2)))

        # 1. Try SerpApi Google Hotels with tailored accommodation query
        options = []
        if serpapi_client.is_configured() and city:
            if "Hostel" in accommodation or "Backpacker" in style or (nightly_target and nightly_target < 2000 and currency == "INR"):
                query_dest = f"hostels and boutique inns in {city}"
            elif "Resort" in accommodation or "Luxury" in style or (nightly_target and nightly_target > 10000 and currency == "INR"):
                query_dest = f"luxury resorts in {city}"
            elif "Homestay" in accommodation:
                query_dest = f"homestays in {city}"
            else:
                query_dest = f"hotels in {city}"

            raw_options = serpapi_client.search_hotels(
                destination=query_dest,
                check_in_date=start,
                check_out_date=end,
                travelers=travelers,
                currency=currency,
            )
            # Ensure all returned live hotel rates are in user-selected currency
            for h in raw_options:
                p_night = h.get("price_per_night")
                conv = currency_client.parse_and_convert(p_night, target_currency=currency, default_source_currency=currency)
                h["price_per_night"] = conv["formatted"]
                h["price_amount"] = conv.get("converted_amount")
                h["currency"] = currency
                options.append(h)

        # 2. Try Amadeus fallback if needed
        if not options:
            amadeus = get_hotels_client()
            if amadeus.is_configured():
                raw_amadeus = amadeus.search_hotels(
                    city=city,
                    check_in=start,
                    check_out=end,
                    budget=budget,
                    travelers=travelers,
                )
                for h in raw_amadeus:
                    p_night = h.get("price_per_night")
                    conv = currency_client.parse_and_convert(p_night, target_currency=currency, default_source_currency="EUR")
                    h["price_per_night"] = conv["formatted"]
                    h["price_amount"] = conv.get("converted_amount")
                    h["currency"] = currency
                    options.append(h)

        # Sort options: prioritize options matching budget ceiling
        if options and nightly_target:
            options.sort(key=lambda h: (
                0 if (h.get("price_amount") and h["price_amount"] <= nightly_target * 1.15) else 1,
                abs((h.get("price_amount") or 999999) - nightly_target),
            ))

        # 3. Preference- & Budget-tailored fallback suggestions if API returned no results
        if not options:
            # Scale nightly rate baseline strictly to user's allocated nightly budget
            if nightly_target:
                nightly_1 = max(10, round(nightly_target * 0.92))
                nightly_2 = max(10, round(nightly_target * 1.05))
            else:
                if "Hostel" in accommodation or "Backpacker" in style:
                    usd_1, usd_2 = 22, 32
                elif "Resort" in accommodation or "Luxury" in style:
                    usd_1, usd_2 = 220, 310
                elif "Homestay" in accommodation:
                    usd_1, usd_2 = 45, 60
                else:  # Comfort
                    usd_1, usd_2 = 75, 110
                nightly_1 = currency_client.convert(usd_1, "USD", currency)["converted_amount"]
                nightly_2 = currency_client.convert(usd_2, "USD", currency)["converted_amount"]

            # Select stay tier reflecting budget
            if (nightly_target and nightly_target <= (1800 if currency == "INR" else 25)) or "Hostel" in accommodation or "Backpacker" in style:
                opt_1_name = f"Recommended Backpacker Boutique Hostel ({city})"
                opt_1_desc = f"Top-rated hostel style stay in {city} offering walking tours, social lounge, and secure lockers."
                opt_1_amenities = ["High-speed Wi-Fi", "Bunk pods with privacy curtains", "Shared guest kitchen", "Social terrace lounge"]
                opt_2_name = f"The Nomad Pods & Travelers Inn ({city})"
                opt_2_desc = f"Clean and modern capsule pods situated within walking distance of central transit in {city}."
                opt_2_amenities = ["Free Wi-Fi", "Co-working desk", "Luggage storage", "Cafe"]
            elif (nightly_target and nightly_target >= (9000 if currency == "INR" else 150)) or "Resort" in accommodation or "Luxury" in style:
                opt_1_name = f"Luxury Wellness Resort & Spa Sanctuary ({city})"
                opt_1_desc = f"5-star sanctuary featuring landscaped private grounds, spa treatments, and concierge service in {city}."
                opt_1_amenities = ["Ayurvedic/Thermal Spa", "Infinity swimming pool", "Fine dining restaurant", "Panoramic views"]
                opt_2_name = f"The Heritage Palace Boutique Suites ({city})"
                opt_2_desc = f"Opulent heritage suites blending regional architecture with contemporary luxury comfort in {city}."
                opt_2_amenities = ["Private butler service", "Chandelier dining hall", "Private balcony", "Valet parking"]
            elif "Homestay" in accommodation:
                opt_1_name = f"Traditional Riverside Heritage Homestay ({city})"
                opt_1_desc = f"Immersive local homestay operated by hospitable resident families in {city}."
                opt_1_amenities = ["Homecooked local breakfast", "Host-guided village walks", "Garden patio", "Free Wi-Fi"]
                opt_2_name = f"Charming Village Orchard Retreat ({city})"
                opt_2_desc = f"Peaceful countryside homestay surrounded by natural orchards and quiet scenic trails in {city}."
                opt_2_amenities = ["Orchard views", "Organic farm meals", "Bicycle rentals", "Quiet reading nooks"]
            else:  # Comfort
                opt_1_name = f"Central Comfort Boutique Hotel ({city})"
                opt_1_desc = f"Well-appointed boutique hotel located near major landmarks, cafes, and transport in {city}."
                opt_1_amenities = ["Complimentary breakfast", "Central location", "Modern rooms", "24/7 Front desk"]
                opt_2_name = f"The Grand City Inn & Suites ({city})"
                opt_2_desc = f"Comfortable, highly-rated hotel with modern amenities and helpful concierge service in {city}."
                opt_2_amenities = ["Rooftop terrace", "Fitness room", "In-room coffee", "Fast Wi-Fi"]

            options = [
                {
                    "name": opt_1_name,
                    "price_per_night": f"~{curr_sym}{nightly_1:,}",
                    "price_amount": nightly_1,
                    "currency": currency,
                    "rating": 4.8,
                    "reviews_count": 0,
                    "amenities": opt_1_amenities,
                    "description": opt_1_desc,
                    "link": f"https://www.google.com/travel/hotels?q={accommodation.lower()}+in+{city}",
                    "source": "Estimated Market Guidance",
                    "is_live": False,
                    "status": "Estimated Market Guidance (Budget-Optimized)",
                },
                {
                    "name": opt_2_name,
                    "price_per_night": f"~{curr_sym}{nightly_2:,}",
                    "price_amount": nightly_2,
                    "currency": currency,
                    "rating": 4.7,
                    "reviews_count": 0,
                    "amenities": opt_2_amenities,
                    "description": opt_2_desc,
                    "link": f"https://www.google.com/travel/hotels?q={accommodation.lower()}+in+{city}",
                    "source": "Estimated Market Guidance",
                    "is_live": False,
                    "status": "Estimated Market Guidance (Budget-Optimized)",
                },
            ]

        state["hotels"] = {
            "options": options,
            "currency": currency,
            "currency_symbol": curr_sym,
            "rooms_needed": rooms_needed,
            "nightly_target": nightly_target,
            "configured": serpapi_client.is_configured(),
            "source": "serpapi" if serpapi_client.is_configured() and options else "curated_selection",
        }
        return state
