"""Cost agent — enforces strict budget awareness, dynamic multi-factor budget allocation,
multi-pass reconciliation, and transparent budget feasibility analysis.

Treats user's entered budget as the primary constraint during trip generation.
Aims to keep estimated total within 90-100% of budget with contingency buffer.
"""
import logging
import math
from datetime import date
from typing import Any

from app.agents.base import BaseAgent
from app.api_clients.currency import CURRENCY_SYMBOLS, currency_client

logger = logging.getLogger(__name__)

# Typical Indian domestic destinations & regions
DOMESTIC_INDIA_KEYWORDS = [
    "india", "indian", "goa", "manali", "jaipur", "agra", "delhi", "new delhi",
    "mumbai", "bombay", "kerala", "udaipur", "shimla", "kalka", "chandigarh",
    "bengaluru", "bangalore", "banglore", "chennai", "madras", "kolkata",
    "calcutta", "hyderabad", "pune", "ahmedabad", "varanasi", "kashi", "banaras",
    "amritsar", "haridwar", "rishikesh", "dehradun", "ooty", "munnar",
    "alleppey", "alappuzha", "hampi", "mysore", "mysuru", "pondicherry", "puducherry",
    "ladakh", "leh", "kashmir", "srinagar", "darjeeling", "gangtok", "andaman",
    "nicobar", "coorg", "kodagu", "lonavala", "khandala", "mathura", "vrindavan",
    "ayodhya", "surat", "vadodara", "baroda", "nagpur", "indore", "bhopal",
    "patna", "lucknow", "kanpur", "guwahati", "shillong", "kochi", "cochin",
    "trivandrum", "thiruvananthapuram", "madurai", "coimbatore", "tirupati",
    "vijayawada", "visakhapatnam", "vizag", "bhubaneswar", "puri", "ranchi",
    "jodhpur", "jaisalmer", "bikaner", "pushkar", "mount abu", "gwalior",
    "jabalpur", "nashik", "aurangabad", "chhatrapati sambhajinagar", "mahabaleshwar",
]


def is_domestic_trip(origin: str | None, destination: str | None, currency: str = "USD") -> bool:
    """Determines if a journey is domestic overland/railway connected within India."""
    dest_l = (destination or "").lower()
    orig_l = (origin or "").lower()

    # Immediate rejection for any recognized international destinations
    foreign_keys = [
        "berlin", "germany", "paris", "france", "tokyo", "japan", "kyoto",
        "london", "uk", "united kingdom", "bali", "indonesia", "alps", "swiss",
        "switzerland", "interlaken", "usa", "york", "singapore", "dubai", "uae",
        "maldives", "male", "thailand", "bangkok", "rome", "italy", "spain",
        "madrid", "barcelona", "toronto", "canada", "sydney", "australia",
        "europe", "america", "africa", "new zealand", "vietnam", "greece",
    ]
    if any(fk in dest_l for fk in foreign_keys):
        return False
    if orig_l and any(fk in orig_l for fk in foreign_keys):
        return False

    # Check if destination is positively identified as an Indian location
    is_dest_india = any(k in dest_l for k in DOMESTIC_INDIA_KEYWORDS)
    if is_dest_india:
        # If origin is provided, origin must also be an Indian location
        if not orig_l or any(k in orig_l for k in DOMESTIC_INDIA_KEYWORDS):
            return True
        return False

    # Same city / localized intra-region
    if orig_l and dest_l and orig_l == dest_l:
        return True

    # If currency is INR and neither destination nor origin matches foreign keywords
    if str(currency).upper() == "INR" and not any(fk in dest_l for fk in foreign_keys):
        return True

    return False


class CostAgent(BaseAgent):
    name = "cost"

    def pre_allocate(self, state: dict[str, Any]) -> dict[str, Any]:
        """Pre-allocates dynamic budget share targets across categories before other agents run.
        Enforces budget as the primary constraint from the start.
        """
        req = state["request"]
        target_budget = max(100, int(req.get("budget", 1000)))
        currency = (req.get("currency") or req.get("preferences", {}).get("currency") or "USD").upper()
        travelers = max(1, int(req.get("travelers", 1)))
        style = (req.get("style") or req.get("preferences", {}).get("style") or "Comfort").title()
        accommodation_pref = (req.get("accommodation") or req.get("preferences", {}).get("accommodation") or "Hotel").title()
        interests = [i.lower() for i in req.get("interests", [])]
        destination = req.get("destination", "")
        origin = req.get("origin") or req.get("preferences", {}).get("origin")

        try:
            nights = (date.fromisoformat(req["end_date"]) - date.fromisoformat(req["start_date"])).days
        except (KeyError, TypeError, ValueError):
            nights = 1
        nights = max(nights, 1)
        total_days = nights + 1

        # Rooms needed: 1 room per 2 travelers (1 room if Backpacker / Hostel)
        if "Hostel" in accommodation_pref or "Backpacker" in style:
            rooms_needed = 1
        else:
            rooms_needed = max(1, math.ceil(travelers / 2))

        domestic = is_domestic_trip(origin, destination, currency)

        # -------------------------------------------------------------
        # DYNAMIC BUDGET WEIGHT CALCULATION
        # -------------------------------------------------------------
        # Base weight shares that adapt to duration, style, travelers, and destination type
        if domestic:
            # Domestic trips: Transport is a smaller share; lodging and food take more
            if "Luxury" in style:
                w_trans = 0.20
                w_stay = 0.40
                w_food = 0.20
                w_act = 0.12
                w_local = 0.04
                w_buf = 0.04
            elif "Backpacker" in style:
                w_trans = 0.18
                w_stay = 0.22
                w_food = 0.28
                w_act = 0.20
                w_local = 0.06
                w_buf = 0.06
            elif "Budget" in style:
                w_trans = 0.20
                w_stay = 0.30
                w_food = 0.25
                w_act = 0.15
                w_local = 0.05
                w_buf = 0.05
            else:  # Comfort
                w_trans = 0.22
                w_stay = 0.35
                w_food = 0.22
                w_act = 0.12
                w_local = 0.05
                w_buf = 0.04
        else:
            # International trips: Intercity airfare requires a larger initial share
            if "Luxury" in style:
                w_trans = 0.30
                w_stay = 0.35
                w_food = 0.18
                w_act = 0.10
                w_local = 0.04
                w_buf = 0.03
            elif "Backpacker" in style:
                w_trans = 0.32
                w_stay = 0.20
                w_food = 0.22
                w_act = 0.16
                w_local = 0.05
                w_buf = 0.05
            elif "Budget" in style:
                w_trans = 0.32
                w_stay = 0.26
                w_food = 0.20
                w_act = 0.12
                w_local = 0.05
                w_buf = 0.05
            else:  # Comfort
                w_trans = 0.32
                w_stay = 0.30
                w_food = 0.19
                w_act = 0.11
                w_local = 0.04
                w_buf = 0.04

        # Adjust for traveler group size: 4 travelers increases lodging & food demand
        if travelers >= 3:
            w_stay = min(0.42, w_stay + 0.04)
            w_food = min(0.30, w_food + 0.03)
            w_act = max(0.08, w_act - 0.04)
            w_trans = max(0.18, w_trans - 0.03)

        # Adjust for specific user interests
        if "food" in interests:
            w_food = min(0.30, w_food + 0.04)
            w_act = max(0.08, w_act - 0.02)
            w_buf = max(0.03, w_buf - 0.02)

        if any(k in interests for k in ["adventure", "history", "culture"]):
            w_act = min(0.22, w_act + 0.04)
            w_stay = max(0.24, w_stay - 0.02)
            w_food = max(0.16, w_food - 0.02)

        # Normalize weights to sum exactly to 1.0
        w_sum = w_trans + w_stay + w_food + w_act + w_local + w_buf
        w_trans /= w_sum
        w_stay /= w_sum
        w_food /= w_sum
        w_act /= w_sum
        w_local /= w_sum
        w_buf /= w_sum

        transport_target = round(target_budget * w_trans)
        stay_target = round(target_budget * w_stay)
        food_target = round(target_budget * w_food)
        act_target = round(target_budget * w_act)
        local_target = round(target_budget * w_local)
        buf_target = max(1, target_budget - (transport_target + stay_target + food_target + act_target + local_target))

        nightly_room_target = max(1, round(stay_target / (nights * rooms_needed)))
        daily_food_per_person = max(1, round(food_target / (total_days * travelers)))
        daily_act_per_person = max(1, round(act_target / (total_days * travelers)))
        per_person_transport = max(1, round(transport_target / travelers))

        allocation = {
            "target_budget": target_budget,
            "currency": currency,
            "travelers": travelers,
            "nights": nights,
            "total_days": total_days,
            "rooms_needed": rooms_needed,
            "is_domestic": domestic,
            "transport_target": transport_target,
            "per_person_transport_target": per_person_transport,
            "stay_target": stay_target,
            "nightly_room_target": nightly_room_target,
            "food_target": food_target,
            "daily_food_per_person": daily_food_per_person,
            "act_target": act_target,
            "daily_act_per_person": daily_act_per_person,
            "local_target": local_target,
            "buf_target": buf_target,
            "weights": {
                "flights": round(w_trans * 100),
                "stay": round(w_stay * 100),
                "food": round(w_food * 100),
                "activities": round(w_act * 100),
                "local_transit": round(w_local * 100),
                "miscellaneous": round(w_buf * 100),
            },
        }

        state["budget_allocation"] = allocation
        return state

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Validates all agent cost outputs against the budget constraint.
        Performs multi-pass optimization and transparent feasibility analysis.
        """
        # Ensure budget pre-allocation exists
        if "budget_allocation" not in state:
            state = self.pre_allocate(state)

        alloc = state["budget_allocation"]
        req = state["request"]
        target_budget = alloc["target_budget"]
        currency = alloc["currency"]
        travelers = alloc["travelers"]
        nights = alloc["nights"]
        total_days = alloc["total_days"]
        rooms_needed = alloc["rooms_needed"]
        domestic = alloc["is_domestic"]
        style = (req.get("style") or req.get("preferences", {}).get("style") or "Comfort").title()

        # -------------------------------------------------------------
        # STEP 1: RESOLVE TRANSPORTATION COSTS
        # -------------------------------------------------------------
        raw_trans = state.get("transport") or {}
        flights = raw_trans.get("flights") if isinstance(raw_trans, dict) else (raw_trans if isinstance(raw_trans, list) else [])
        trains = raw_trans.get("trains", []) if isinstance(raw_trans, dict) else []

        selected_transport_per_person = None
        selected_transport_mode = "Flight"

        # Check train options if available and economical
        train_fare_found = None
        if trains and isinstance(trains, list) and len(trains) > 0:
            for t in trains:
                amt = t.get("lowest_fare_amount")
                if amt:
                    train_fare_found = int(amt)
                    break

        flight_fare_found = None
        if flights and isinstance(flights, list) and len(flights) > 0:
            for f in flights:
                amt = f.get("price_amount")
                if amt:
                    flight_fare_found = int(amt)
                    break

        # Preference & Feasibility selection:
        # If domestic and budget is constrained, prefer train or economical transport
        if domestic and train_fare_found and (flight_fare_found is None or (flight_fare_found * travelers > alloc["transport_target"])):
            selected_transport_per_person = train_fare_found
            selected_transport_mode = "Train"
        elif flight_fare_found:
            selected_transport_per_person = flight_fare_found
            selected_transport_mode = "Flight"
        elif train_fare_found:
            selected_transport_per_person = train_fare_found
            selected_transport_mode = "Train"
        else:
            # Baseline estimation tailored to budget and domestic status
            if domestic:
                # Domestic roundtrip in user currency
                # Budget trips: ~₹1,200 - ₹2,500 train/bus; Comfort: ~₹3,500 - ₹5,500 flight/train
                if target_budget < 30000:
                    base_inr = 1250
                    selected_transport_mode = "Train / Regional Transit"
                elif target_budget < 60000:
                    base_inr = 2800
                    selected_transport_mode = "Train (AC) / Economy Flight"
                elif "Luxury" in style:
                    base_inr = 9500
                    selected_transport_mode = "Prime Flight"
                else:
                    base_inr = 4500
                    selected_transport_mode = "Flight / Superfast Express"
                selected_transport_per_person = currency_client.convert(base_inr, "INR", currency)["converted_amount"]
            else:
                # International roundtrip baseline
                if "Backpacker" in style or target_budget < 60000:
                    usd_val = 240
                elif "Luxury" in style:
                    usd_val = 850
                else:
                    usd_val = 450
                selected_transport_per_person = currency_client.convert(usd_val, "USD", currency)["converted_amount"]

        flights_cost = round(selected_transport_per_person * travelers)

        # -------------------------------------------------------------
        # STEP 2: RESOLVE ACCOMMODATION COSTS
        # -------------------------------------------------------------
        raw_hotels = state.get("hotels")
        hotel_list = raw_hotels.get("options", []) if isinstance(raw_hotels, dict) else (raw_hotels if isinstance(raw_hotels, list) else [])

        # Find best hotel matching nightly target
        chosen_hotel_nightly = None
        if hotel_list:
            # Sort hotels by how close their price is to our nightly target
            valid_hotels = [h for h in hotel_list if h.get("price_amount")]
            if valid_hotels:
                # Filter hotels that are <= nightly target if possible
                within_budget = [h for h in valid_hotels if h["price_amount"] <= alloc["nightly_room_target"] * 1.15]
                if within_budget:
                    # Pick highest-rated among within-budget hotels
                    within_budget.sort(key=lambda x: (x.get("rating") or 4.0), reverse=True)
                    chosen_hotel_nightly = int(within_budget[0]["price_amount"])
                else:
                    # Pick the most economical available hotel
                    valid_hotels.sort(key=lambda x: x["price_amount"])
                    chosen_hotel_nightly = int(valid_hotels[0]["price_amount"])

        if not chosen_hotel_nightly:
            # Baseline room nightly rate bounded by allocated nightly room target
            if domestic:
                if target_budget < 30000:
                    base_nightly_inr = min(1500, max(800, alloc["nightly_room_target"]))
                elif target_budget < 60000:
                    base_nightly_inr = min(3800, max(1800, alloc["nightly_room_target"]))
                elif "Luxury" in style:
                    base_nightly_inr = max(6000, alloc["nightly_room_target"])
                else:
                    base_nightly_inr = min(5000, max(2200, alloc["nightly_room_target"]))
                chosen_hotel_nightly = currency_client.convert(base_nightly_inr, "INR", currency)["converted_amount"]
            else:
                chosen_hotel_nightly = max(25, alloc["nightly_room_target"])

        stay_cost = round(chosen_hotel_nightly * nights * rooms_needed)

        # -------------------------------------------------------------
        # STEP 3: FOOD & DINING
        # -------------------------------------------------------------
        daily_food_pp = alloc["daily_food_per_person"]
        food_cost = round(daily_food_pp * total_days * travelers)

        # -------------------------------------------------------------
        # STEP 4: ACTIVITIES & SIGHTSEEING
        # -------------------------------------------------------------
        daily_act_pp = alloc["daily_act_per_person"]
        act_cost = round(daily_act_pp * total_days * travelers)

        # -------------------------------------------------------------
        # STEP 5: LOCAL TRANSIT & CONTINGENCY
        # -------------------------------------------------------------
        transit_cost = alloc["local_target"]
        misc_cost = alloc["buf_target"]

        total_cost = flights_cost + stay_cost + food_cost + act_cost + transit_cost + misc_cost

        # -------------------------------------------------------------
        # STEP 6: MULTI-PASS RECONCILIATION & VALIDATION LOOP
        # -------------------------------------------------------------
        # If total exceeds target budget, optimize flexible categories
        if total_cost > target_budget and target_budget > 0:
            excess = total_cost - target_budget

            # Pass 1: If transport was flights, check if trains/bus can fit
            if domestic and selected_transport_mode != "Train" and train_fare_found:
                train_total = train_fare_found * travelers
                if train_total < flights_cost:
                    flights_cost = train_total
                    selected_transport_mode = "Train"
                    selected_transport_per_person = train_fare_found
                    total_cost = flights_cost + stay_cost + food_cost + act_cost + transit_cost + misc_cost

            # Pass 2: Re-balance stay, food, activities to fit within remaining budget
            if total_cost > target_budget:
                # If flights + stay already fit, only adjust food, activities, transit, misc
                if flights_cost + stay_cost < target_budget:
                    remaining_flexible = target_budget - (flights_cost + stay_cost)
                    food_cost = round(remaining_flexible * 0.50)
                    act_cost = round(remaining_flexible * 0.28)
                    transit_cost = round(remaining_flexible * 0.14)
                    misc_cost = max(0, remaining_flexible - (food_cost + act_cost + transit_cost))
                    total_cost = flights_cost + stay_cost + food_cost + act_cost + transit_cost + misc_cost
                else:
                    remaining_for_daily = target_budget - flights_cost
                    if remaining_for_daily > 0:
                        # Allocate remaining to stay, food, act, transit, misc
                        new_stay = round(remaining_for_daily * 0.42)
                        new_food = round(remaining_for_daily * 0.28)
                        new_act = round(remaining_for_daily * 0.16)
                        new_transit = round(remaining_for_daily * 0.08)
                        new_misc = max(0, remaining_for_daily - (new_stay + new_food + new_act + new_transit))

                        min_stay_floor = currency_client.convert(700 * nights * rooms_needed, "INR", currency)["converted_amount"] if domestic else round(20 * nights * rooms_needed)
                        min_food_floor = currency_client.convert(250 * total_days * travelers, "INR", currency)["converted_amount"] if domestic else round(12 * total_days * travelers)

                        if new_stay >= min_stay_floor and new_food >= min_food_floor:
                            stay_cost = new_stay
                            food_cost = new_food
                            act_cost = new_act
                            transit_cost = new_transit
                            misc_cost = new_misc
                            total_cost = flights_cost + stay_cost + food_cost + act_cost + transit_cost + misc_cost

        # -------------------------------------------------------------
        # STEP 7: BUDGET FEASIBILITY & HEALTH EVALUATION
        # -------------------------------------------------------------
        exceeds = total_cost > target_budget
        variance = max(0, total_cost - target_budget)
        remaining = max(0, target_budget - total_cost)

        # Check if budget is genuinely unrealistic for this destination & duration
        # (e.g. Paris from India with ₹20,000 for 2 travelers)
        is_unrealistic = False
        unrealistic_reason = ""
        cost_contributors = []
        suggested_alternatives = []
        suggested_revised_budget = None

        if exceeds:
            pct_over = round((total_cost / max(1, target_budget)) * 100)
            if pct_over >= 150:
                is_unrealistic = True
                dest_name = req.get("destination", "this destination")
                origin_name = req.get("origin") or "your location"

                if not domestic:
                    unrealistic_reason = (
                        f"Round-trip international flights between {origin_name} and {dest_name} "
                        f"alone cost approximately {currency} {flights_cost:,} for {travelers} traveler(s), "
                        f"which substantially exceeds your entire {currency} {target_budget:,} budget."
                    )
                    cost_contributors = [
                        f"International Flights: ~{currency} {flights_cost:,} ({round(flights_cost/total_cost*100)}% of total)",
                        f"Lodging & Accommodations: ~{currency} {stay_cost:,} for {nights} nights",
                    ]
                    suggested_revised_budget = round(total_cost * 1.05)
                    suggested_alternatives = [
                        f"Choose a scenic domestic alternative such as Goa, Manali, Jaipur, or Pondicherry which fits comfortably within {currency} {target_budget:,}.",
                        f"Reduce duration from {nights} nights to {max(2, nights - 2)} nights.",
                        f"Adjust your target budget to approximately {currency} {suggested_revised_budget:,} to support realistic international travel costs.",
                    ]
                else:
                    unrealistic_reason = (
                        f"Providing realistic lodging, dining, and transit in {dest_name} for {travelers} traveler(s) "
                        f"across {nights} nights requires a minimum estimated total of {currency} {total_cost:,}."
                    )
                    cost_contributors = [
                        f"Accommodation: ~{currency} {stay_cost:,} ({rooms_needed} room{'s' if rooms_needed > 1 else ''} for {nights} nights)",
                        f"Intercity Travel: ~{currency} {flights_cost:,} for {travelers} traveler(s)",
                    ]
                    suggested_revised_budget = round(total_cost * 1.05)
                    suggested_alternatives = [
                        f"Opt for budget homestays or boutique backpacker hostels instead of standard hotel rooms.",
                        f"Travel via economical superfast trains rather than flights.",
                        f"Increase target budget to ~{currency} {suggested_revised_budget:,}.",
                    ]

        # Calculate finalized category percentage distribution
        calc_total = max(1, total_cost)
        pct_flights = round((flights_cost / calc_total) * 100)
        pct_stay = round((stay_cost / calc_total) * 100)
        pct_food = round((food_cost / calc_total) * 100)
        pct_act = round((act_cost / calc_total) * 100)
        pct_transit = round((transit_cost / calc_total) * 100)
        pct_misc = max(1, 100 - (pct_flights + pct_stay + pct_food + pct_act + pct_transit))

        curr_sym = CURRENCY_SYMBOLS.get(currency, "$")
        breakdown = {
            "target_budget": target_budget,
            "total": total_cost,
            "currency": currency,
            "currency_symbol": curr_sym,
            "flights": flights_cost,
            "transport_mode": selected_transport_mode,
            "stay": stay_cost,
            "food": food_cost,
            "activities": act_cost,
            "local_transit": transit_cost,
            "miscellaneous": misc_cost,
            "exceeds_budget": exceeds,
            "budget_variance": target_budget - total_cost,
            "remaining_budget": remaining,
            "utilization_percent": min(100, round((total_cost / max(1, target_budget)) * 100)),
            "per_traveler": round(total_cost / travelers),
            "per_day": round(total_cost / total_days),
            "budget_status": (
                f"Within Target Budget ({curr_sym}{target_budget - total_cost:,} remaining)"
                if not exceeds
                else f"Exceeds Target Budget by {curr_sym}{total_cost - target_budget:,}"
            ),
            "percentages": {
                "flights": pct_flights,
                "stay": pct_stay,
                "food": pct_food,
                "activities": pct_act,
                "local_transit": pct_transit,
                "miscellaneous": pct_misc,
            },
            "feasibility": {
                "is_realistic": not is_unrealistic,
                "is_balanced": not exceeds,
                "unrealistic_reason": unrealistic_reason,
                "cost_contributors": cost_contributors,
                "suggested_alternatives": suggested_alternatives,
                "suggested_revised_budget": suggested_revised_budget,
            },
        }

        state["costs"] = {"breakdown": breakdown}
        return state
