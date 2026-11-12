"""Transport agent — travel guidelines, live flights via SerpApi, live & scheduled trains via RailCore,
and strict budget-aware transport comparison.
"""
from typing import Any

from app.agents.base import BaseAgent
from app.api_clients.currency import CURRENCY_SYMBOLS, currency_client
from app.api_clients.railcore import railcore_client
from app.api_clients.serpapi import resolve_airport_code, serpapi_client


class TransportAgent(BaseAgent):
    name = "transport"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        req = state["request"]
        city = req.get("destination", "")
        origin = req.get("origin") or req.get("preferences", {}).get("origin")
        start = str(req.get("start_date", ""))
        end = str(req.get("end_date", ""))
        travelers = max(1, int(req.get("travelers", 1)))
        currency = (req.get("currency") or req.get("preferences", {}).get("currency") or "USD").upper()
        curr_sym = CURRENCY_SYMBOLS.get(currency, "$")

        # Read budget allocation targets
        alloc = state.get("budget_allocation") or {}
        transport_target = alloc.get("transport_target")
        per_person_target = alloc.get("per_person_transport_target")
        is_domestic = alloc.get("is_domestic", False)

        # -------------------------------------------------------------
        # 1. LIVE / SCHEDULED TRAINS VIA RAILCORE (DOMESTIC INDIA ONLY)
        # -------------------------------------------------------------
        trains = []
        if is_domestic and origin and city:
            try:
                trains = railcore_client.search_trains(
                    from_station=origin,
                    to_station=city,
                    date_str=start,
                    currency=currency,
                )
            except Exception:
                trains = []

        # -------------------------------------------------------------
        # 2. FLIGHTS VIA SERPAPI
        # -------------------------------------------------------------
        flights = []
        if serpapi_client.is_configured() and city:
            raw_flights = serpapi_client.search_flights(
                destination=city,
                outbound_date=start,
                return_date=end,
                origin=origin,
                travelers=travelers,
                currency=currency,
            )
            for f in raw_flights:
                price_val = f.get("price")
                conv = currency_client.parse_and_convert(price_val, target_currency=currency, default_source_currency=currency)
                f["price"] = conv["formatted"]
                f["price_amount"] = conv.get("converted_amount")
                f["currency"] = currency
                flights.append(f)

        # Fallback flight guidance if SerpApi returned no live results
        if not flights:
            c_lower = city.lower()
            dep_code = resolve_airport_code(origin) if origin else "DEP"
            dep_name = origin or "Nearest Major Hub"

            if "tokyo" in c_lower or "japan" in c_lower:
                arr_code, arr_name = "HND", "Tokyo Haneda Airport"
                airline_1, usd_1, airline_2, usd_2 = "All Nippon Airways (ANA)", 680, "Japan Airlines (JAL)", 720
            elif "paris" in c_lower or "france" in c_lower:
                arr_code, arr_name = "CDG", "Paris Charles de Gaulle"
                airline_1, usd_1, airline_2, usd_2 = "Air France", 590, "Lufthansa", 540
            elif "alps" in c_lower or "swiss" in c_lower or "interlaken" in c_lower:
                arr_code, arr_name = "ZRH", "Zurich International Airport"
                airline_1, usd_1, airline_2, usd_2 = "Swiss International Air Lines", 620, "Emirates", 660
            elif "maldives" in c_lower:
                arr_code, arr_name = "MLE", "Velana International Airport (Malé)"
                airline_1, usd_1, airline_2, usd_2 = "Qatar Airways", 480, "Emirates", 510
            elif "manali" in c_lower:
                arr_code, arr_name = "KUU", "Kullu-Manali Bhuntar Airport"
                airline_1, usd_1, airline_2, usd_2 = "Alliance Air", 75, "IndiGo", 68
            elif "jaipur" in c_lower:
                arr_code, arr_name = "JAI", "Jaipur International Airport"
                airline_1, usd_1, airline_2, usd_2 = "IndiGo", 55, "Air India", 62
            elif "goa" in c_lower:
                arr_code, arr_name = "GOI", "Goa Dabolim / Mopa International Airport"
                airline_1, usd_1, airline_2, usd_2 = "IndiGo", 65, "Air India Express", 58
            elif "bali" in c_lower or "indonesia" in c_lower:
                arr_code, arr_name = "DPS", "Ngurah Rai International Airport (Denpasar)"
                airline_1, usd_1, airline_2, usd_2 = "Singapore Airlines", 580, "Garuda Indonesia", 520
            else:
                arr_code = resolve_airport_code(city) or "ARR"
                arr_name = f"{city} Airport"
                if is_domestic:
                    airline_1, usd_1 = f"Major Domestic Carrier to {city}", 50
                    airline_2, usd_2 = f"Budget Express to {city}", 42
                else:
                    airline_1, usd_1 = f"Major Carrier to {city}", 450
                    airline_2, usd_2 = f"Regional Carrier to {city}", 380

            p_1 = currency_client.convert(usd_1, "USD", currency)["converted_amount"]
            p_2 = currency_client.convert(usd_2, "USD", currency)["converted_amount"]

            flights = [
                {
                    "airline": airline_1,
                    "flight_number": "",
                    "departure_time": f"{start} Morning (Est.)",
                    "departure_airport": dep_name,
                    "departure_code": dep_code,
                    "arrival_time": f"{start} Afternoon (Est.)",
                    "arrival_airport": arr_name,
                    "arrival_code": arr_code,
                    "duration": "Direct / 1-stop",
                    "stops": "Check carrier",
                    "price": f"~{curr_sym}{p_1:,}",
                    "price_amount": p_1,
                    "currency": currency,
                    "booking_link": f"https://www.google.com/travel/flights?q=flights+from+{dep_code}+to+{arr_code}",
                    "source": "Estimated Market Guidance",
                    "is_live": False,
                    "status": "Estimated Market Guidance (Budget-Optimized)",
                },
                {
                    "airline": airline_2,
                    "flight_number": "",
                    "departure_time": f"{start} Afternoon (Est.)",
                    "departure_airport": dep_name,
                    "departure_code": dep_code,
                    "arrival_time": f"{start} Evening (Est.)",
                    "arrival_airport": arr_name,
                    "arrival_code": arr_code,
                    "duration": "Connecting / Direct",
                    "stops": "Check carrier",
                    "price": f"~{curr_sym}{p_2:,}",
                    "price_amount": p_2,
                    "currency": currency,
                    "booking_link": f"https://www.google.com/travel/flights?q=flights+from+{dep_code}+to+{arr_code}",
                    "source": "Estimated Market Guidance",
                    "is_live": False,
                    "status": "Estimated Market Guidance (Budget-Optimized)",
                },
            ]

        # -------------------------------------------------------------
        # 3. COMPARE & RECOMMEND OPTIMAL MODE (TRAIN VS FLIGHT)
        # -------------------------------------------------------------
        lowest_flight_per_person = flights[0]["price_amount"] if flights and flights[0].get("price_amount") else None
        lowest_train_per_person = trains[0]["lowest_fare_amount"] if trains and trains[0].get("lowest_fare_amount") else None

        recommended_mode = "Flight"
        recommendation_reason = (
            f"International flight route to {city}."
            if not is_domestic
            else "Fastest air connection for your itinerary."
        )

        if is_domestic and lowest_train_per_person:
            # If domestic train is significantly cheaper and trip budget is constrained, recommend train
            if (
                lowest_flight_per_person is None
                or (lowest_flight_per_person * travelers > (transport_target or 999999))
                or (lowest_train_per_person < (lowest_flight_per_person or 999999) * 0.6)
            ):
                recommended_mode = "Train"
                recommendation_reason = (
                    f"Recommended for budget efficiency: train travel costs ~{curr_sym}{lowest_train_per_person:,} "
                    f"per traveler compared to ~{curr_sym}{lowest_flight_per_person:,} by air."
                    if lowest_flight_per_person else "Economical and scenic rail link for your destination."
                )

        origin_note = f"Origin: {origin}." if origin else "Origin: Flexible departures."
        state["transport"] = {
            "flights": flights,
            "trains": trains,
            "recommended_mode": recommended_mode,
            "recommendation_reason": recommendation_reason,
            "currency": currency,
            "currency_symbol": curr_sym,
            "guidelines": [
                f"{origin_note} Travel Window: {start} to {end} for {travelers} traveler(s).",
                f"Recommended mode: {recommended_mode}. {recommendation_reason}",
                "Advance booking recommended for peak season travel.",
                "Local taxis, app cabs, and station kiosks available at the arrival terminal.",
            ],
            "configured": serpapi_client.is_configured(),
            "source": "serpapi_and_railcore" if serpapi_client.is_configured() or trains else "estimated_route",
        }
        return state
