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

        # Resolve starting city if not specified so flight search and display never fail
        origin_inferred = False
        if not origin or not str(origin).strip():
            user_orig = req.get("preferences", {}).get("origin")
            if user_orig:
                origin = user_orig
            elif currency == "INR":
                origin = "Bengaluru"
                origin_inferred = True
            else:
                origin = "New York"
                origin_inferred = True

        # Read budget allocation targets
        alloc = state.get("budget_allocation") or {}
        transport_target = alloc.get("transport_target")
        per_person_target = alloc.get("per_person_transport_target")
        is_domestic = alloc.get("is_domestic", False)

        from app.services.transit_service import get_nearby_transit
        nearby_transit = get_nearby_transit(city)

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
            default_dep_code = "BLR" if currency == "INR" else "JFK"
            dep_code = resolve_airport_code(origin) or default_dep_code
            dep_name = origin or ("Bengaluru (BLR)" if currency == "INR" else "New York (JFK)")
            if nearby_transit and not nearby_transit.get("has_direct_airport"):
                arr_code = nearby_transit["nearby_airport"]["code"]
                arr_name = nearby_transit["nearby_airport"]["name"]
            else:
                arr_code = resolve_airport_code(city) or "ARR"
                arr_name = f"{city} Airport"

            if is_domestic:
                airline_1, usd_1 = f"Major Domestic Carrier to {city}", 65
                airline_2, usd_2 = f"Budget Express to {city}", 52
            else:
                airline_1, usd_1 = f"Major Carrier to {city}", 520
                airline_2, usd_2 = f"Regional Carrier to {city}", 440

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

        total_flight_cost = (lowest_flight_per_person or 0) * travelers
        flight_is_infeasible = False
        target_cap = transport_target or 999999

        if lowest_flight_per_person and total_flight_cost > target_cap:
            flight_is_infeasible = True

        if is_domestic:
            if flight_is_infeasible:
                if lowest_train_per_person:
                    recommended_mode = "Train"
                    recommendation_reason = (
                        f"Airfare ({curr_sym}{total_flight_cost:,}) exceeds transport budget target ({curr_sym}{target_cap:,}). "
                        f"Recommended economical train travel (~{curr_sym}{lowest_train_per_person * travelers:,} total) to maintain budget feasibility."
                    )
                else:
                    recommended_mode = "Train / Regional Transit"
                    recommendation_reason = (
                        f"Direct flight costs ({curr_sym}{total_flight_cost:,}) exceed allocated transport budget ({curr_sym}{target_cap:,}). "
                        f"Recommended economical rail/overland transit to preserve your vacation budget."
                    )
            elif lowest_train_per_person and (lowest_train_per_person < (lowest_flight_per_person or 999999) * 0.6):
                recommended_mode = "Train"
                recommendation_reason = (
                    f"Recommended for budget efficiency: train travel costs ~{curr_sym}{lowest_train_per_person:,} "
                    f"per traveler compared to ~{curr_sym}{lowest_flight_per_person:,} by air."
                )

        if origin_inferred:
            origin_note = f"Departure city estimated from {origin}. You can specify your starting city anytime in trip preferences."
        elif origin:
            origin_note = f"Origin: {origin}."
        else:
            origin_note = "Origin: Flexible departures."
        guidelines = [
            f"{origin_note} Travel Window: {start} to {end} for {travelers} traveler(s).",
            f"Recommended mode: {recommended_mode}. {recommendation_reason}",
        ]
        if nearby_transit and not nearby_transit.get("has_direct_airport"):
            ap = nearby_transit.get("nearby_airport", {})
            rw = nearby_transit.get("nearby_railway", {})
            guidelines.append(
                f"Transit Gateway: {city} has no direct commercial airport. Flights land at nearest airport {ap.get('name', 'Nearby Hub')} ({ap.get('code', '')}, {ap.get('distance', '')}). Nearest railway station: {rw.get('name', 'Nearby Station')} ({rw.get('distance', '')})."
            )
        guidelines.extend([
            "Advance booking recommended for peak season travel.",
            "Local taxis, app cabs, and station kiosks available at the arrival terminal.",
        ])

        state["transport"] = {
            "flights": flights,
            "trains": trains,
            "recommended_mode": recommended_mode,
            "recommendation_reason": recommendation_reason,
            "nearby_transit": nearby_transit,
            "currency": currency,
            "currency_symbol": curr_sym,
            "guidelines": guidelines,
            "configured": serpapi_client.is_configured(),
            "source": "serpapi_and_railcore" if serpapi_client.is_configured() or trains else "estimated_route",
        }
        return state
