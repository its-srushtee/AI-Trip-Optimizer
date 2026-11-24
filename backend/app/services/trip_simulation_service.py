"""What-If Trip Simulation Service — non-destructive hypothetical trip modeling
and transactional application upon explicit user confirmation.

Reuses CostAgent, WeatherAgent, ExplainabilityService, and
AlternativeRecommendationService without mutating database state during simulation.
"""
from __future__ import annotations

import copy
import logging
from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.cost_agent import CostAgent
from app.agents.itinerary_agent import estimate_activity_cost, format_cost_range
from app.api_clients.currency import CURRENCY_SYMBOLS
from app.models.reoptimization import TripReoptimization
from app.models.trip import Trip
from app.services.alternative_recommendation_service import (
    _locate_activity,
    find_alternative_attractions,
)
from app.services.explainability_service import (
    _parse_cost_midpoint,
    enrich_itinerary_with_explanations,
)

logger = logging.getLogger(__name__)
cost_agent = CostAgent()


def _count_attractions(itinerary: dict[str, Any]) -> int:
    count = 0
    for day in itinerary.get("days") or []:
        for act in day.get("activities") or []:
            cat = (act.get("category") or "").lower()
            if "departure" in cat or "arrival" in (act.get("name") or "").lower():
                continue
            count += 1
    return count


def _estimate_intercity_travel_duration(itinerary: dict[str, Any], mode: str) -> str:
    transport = itinerary.get("transport") or {}
    if mode.lower() == "train":
        trains = transport.get("trains") or []
        if trains and trains[0].get("duration"):
            return str(trains[0]["duration"])
        return "Overnight / Express Rail"
    flights = transport.get("flights") or []
    if flights and flights[0].get("duration"):
        return str(flights[0]["duration"])
    return "Standard Air Transit"


def _recalculate_budget_breakdown(
    sim_itin: dict[str, Any],
    *,
    target_budget: int,
    orig_days: int,
    new_days: int,
    travelers: int,
    currency: str,
    curr_sym: str,
    new_transport_mode: str | None = None,
    new_transport_cost: int | None = None,
    act_cost_delta: int = 0,
) -> dict[str, Any]:
    """Deterministically recalculates budget breakdown for the simulated trip."""
    bb = copy.deepcopy(sim_itin.get("budget_breakdown") or {})
    orig_nights = max(1, orig_days - 1)
    new_nights = max(1, new_days - 1)

    flights_cost = int(bb.get("flights", 0))
    stay_cost = int(bb.get("stay", 0))
    food_cost = int(bb.get("food", 0))
    act_cost = int(bb.get("activities", 0))
    transit_cost = int(bb.get("local_transit", 0))
    misc_cost = int(bb.get("miscellaneous", 0))

    if new_days != orig_days and orig_days > 0:
        stay_cost = max(0, round(stay_cost * (new_nights / orig_nights)))
        food_cost = max(0, round(food_cost * (new_days / orig_days)))
        act_cost = max(0, round(act_cost * (new_days / orig_days)))
        transit_cost = max(0, round(transit_cost * (new_days / orig_days)))
        misc_cost = max(0, round(misc_cost * (new_days / orig_days)))

    if new_transport_cost is not None:
        flights_cost = max(0, int(new_transport_cost))
    if new_transport_mode:
        bb["transport_mode"] = new_transport_mode

    act_cost = max(0, act_cost + act_cost_delta)
    total = flights_cost + stay_cost + food_cost + act_cost + transit_cost + misc_cost

    bb["target_budget"] = target_budget
    bb["flights"] = flights_cost
    bb["stay"] = stay_cost
    bb["food"] = food_cost
    bb["activities"] = act_cost
    bb["local_transit"] = transit_cost
    bb["miscellaneous"] = misc_cost
    bb["total"] = total
    bb["currency"] = currency
    bb["currency_symbol"] = curr_sym
    bb["exceeds_budget"] = total > target_budget if target_budget > 0 else False
    bb["budget_variance"] = target_budget - total
    bb["remaining_budget"] = max(0, target_budget - total)
    bb["utilization_percent"] = min(100, round((total / max(1, target_budget)) * 100)) if target_budget > 0 else 100
    bb["per_traveler"] = round(total / max(1, travelers))
    bb["per_day"] = round(total / max(1, new_days))
    bb["budget_status"] = (
        f"Within Target Budget ({curr_sym}{target_budget - total:,} remaining)"
        if not bb["exceeds_budget"]
        else f"Exceeds Target Budget by {curr_sym}{total - target_budget:,}"
    )

    calc_total = max(1, total)
    bb["percentages"] = {
        "flights": round((flights_cost / calc_total) * 100),
        "stay": round((stay_cost / calc_total) * 100),
        "food": round((food_cost / calc_total) * 100),
        "activities": round((act_cost / calc_total) * 100),
        "local_transit": round((transit_cost / calc_total) * 100),
        "miscellaneous": max(1, round((misc_cost / calc_total) * 100)),
    }
    return bb


def simulate_trip_changes(
    trip: Trip,
    *,
    scenario: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Runs a non-destructive What-If simulation on a deep copy of `trip` and its itinerary."""
    params = params or {}
    orig_itin = copy.deepcopy(trip.itinerary or {})
    if not orig_itin or not orig_itin.get("days"):
        raise HTTPException(status_code=400, detail="Trip does not have a generated itinerary to simulate.")

    sim_itin = copy.deepcopy(orig_itin)
    orig_days_list = orig_itin.get("days") or []
    orig_days_count = len(orig_days_list)
    orig_budget = int(trip.budget or orig_itin.get("budget") or 0)
    orig_bb = orig_itin.get("budget_breakdown") or {}
    orig_total_cost = int(orig_bb.get("total") or orig_budget)
    orig_mode = orig_bb.get("transport_mode") or (orig_itin.get("transport") or {}).get("recommended_mode") or "Flight"
    orig_travel_duration = _estimate_intercity_travel_duration(orig_itin, orig_mode)
    orig_attraction_count = _count_attractions(orig_itin)

    currency = (orig_itin.get("currency") or trip.currency or "USD").upper()
    curr_sym = CURRENCY_SYMBOLS.get(currency, "$")
    travelers = max(1, int(trip.travelers or orig_itin.get("travelers") or 1))
    prefs = copy.deepcopy(trip.preferences or {})
    style = prefs.get("style") or (orig_itin.get("preferences_applied") or {}).get("style") or "Comfort"

    sim_budget = orig_budget
    sim_end_date = trip.end_date
    sim_interests = list(trip.interests or orig_itin.get("interests") or [])
    sim_mode = orig_mode
    new_transport_cost: int | None = None
    act_cost_delta = 0
    transportation_changes = "No transportation changes."
    warnings: list[str] = []
    change_description = ""

    sc = scenario.strip().lower()

    # 1. Add Day(s)
    if sc == "add_day":
        delta = max(1, min(7, int(params.get("days_delta", 1))))
        sim_end_date = trip.end_date + timedelta(days=delta)
        days_list = sim_itin["days"]
        used_names = {
            (act.get("name") or "").strip().lower()
            for d in days_list
            for act in (d.get("activities") or [])
        }
        unused_places = [
            p for p in (sim_itin.get("places_to_visit") or [])
            if isinstance(p, dict) and (p.get("name") or "").strip().lower() not in used_names
        ]
        last_stay = days_list[-1].get("stay") or f"Stay in {trip.destination}"
        for k in range(delta):
            new_day_num = len(days_list) + 1
            new_date = (trip.start_date + timedelta(days=new_day_num - 1)).isoformat()
            p_m = unused_places.pop(0) if unused_places else None
            p_a = unused_places.pop(0) if unused_places else None
            m_name = p_m["name"] if p_m else f"Extended {trip.destination} Morning Discovery"
            a_name = p_a["name"] if p_a else f"Local Cultural Quarter in {trip.destination}"
            m_cost = estimate_activity_cost(p_m.get("category", "") if p_m else "Attraction", style, currency)
            a_cost = estimate_activity_cost(p_a.get("category", "") if p_a else "Culture", style, currency)

            new_day = {
                "day": new_day_num,
                "date": new_date,
                "theme": f"Day {new_day_num}: Extended {trip.destination} Exploration",
                "morning": f"[09:00 AM - 12:00 PM] {m_name} — Added via What-If trip extension.",
                "afternoon": f"[02:00 PM - 05:00 PM] {a_name} — Added via What-If trip extension.",
                "evening": f"[06:30 PM - 09:00 PM] Leisure evening & regional dinner in {trip.destination}.",
                "stay": last_stay,
                "estimate_cost": round(orig_total_cost / max(1, orig_days_count)),
                "estimate_usd": round(orig_total_cost / max(1, orig_days_count)),
                "currency": currency,
                "currency_symbol": curr_sym,
                "suggested_places": [m_name, a_name],
                "activities": [
                    {
                        "attraction_id": f"day-{new_day_num}-morning",
                        "name": m_name,
                        "time_slot": "Morning",
                        "time_window": "09:00 AM - 12:00 PM",
                        "location": (p_m or {}).get("location") or trip.destination,
                        "category": (p_m or {}).get("category") or "Sightseeing",
                        "estimated_duration": "2.5 hours",
                        "estimated_cost": m_cost,
                        "why_it_matches": "Added to fill extended trip duration.",
                        "transit_info": "Local transit (~15 mins)",
                    },
                    {
                        "attraction_id": f"day-{new_day_num}-afternoon",
                        "name": a_name,
                        "time_slot": "Afternoon",
                        "time_window": "02:00 PM - 05:00 PM",
                        "location": (p_a or {}).get("location") or trip.destination,
                        "category": (p_a or {}).get("category") or "Culture",
                        "estimated_duration": "2.5 hours",
                        "estimated_cost": a_cost,
                        "why_it_matches": "Added to fill extended trip duration.",
                        "transit_info": "Local transit (~15 mins)",
                    },
                ],
            }
            # Insert before final departure day if > 1 days
            if len(days_list) >= 2:
                days_list.insert(-1, new_day)
            else:
                days_list.append(new_day)

        # Renumber days and dates sequentially
        for idx, d in enumerate(days_list):
            d["day"] = idx + 1
            d["date"] = (trip.start_date + timedelta(days=idx)).isoformat()
        sim_itin["dates"]["end"] = sim_end_date.isoformat()
        sim_itin["dates"]["nights"] = max(1, len(days_list) - 1)
        change_description = f"Added {delta} extra day(s), extending trip to {len(days_list)} days."

    # 2. Remove Day / Destination
    elif sc in ("remove_day", "remove_destination"):
        if orig_days_count <= 2:
            warnings.append("Cannot shorten a trip below 2 days.")
            change_description = "Trip is already at minimum 2-day duration."
        else:
            target_day = int(params.get("day_number") or (orig_days_count - 1))
            idx_to_remove = next(
                (i for i, d in enumerate(sim_itin["days"]) if d.get("day") == target_day),
                orig_days_count - 2,
            )
            removed_day = sim_itin["days"].pop(idx_to_remove)
            for idx, d in enumerate(sim_itin["days"]):
                d["day"] = idx + 1
                d["date"] = (trip.start_date + timedelta(days=idx)).isoformat()
            sim_end_date = trip.start_date + timedelta(days=len(sim_itin["days"]) - 1)
            sim_itin["dates"]["end"] = sim_end_date.isoformat()
            sim_itin["dates"]["nights"] = max(1, len(sim_itin["days"]) - 1)
            change_description = f"Removed Day {removed_day.get('day')} ({removed_day.get('theme', 'stop')}), shortening trip to {len(sim_itin['days'])} days."

    # 3. Budget Increase / Decrease / Set
    elif sc in ("increase_budget", "decrease_budget", "set_budget"):
        if sc == "set_budget":
            sim_budget = max(100, int(params.get("new_budget", orig_budget)))
        elif sc == "increase_budget":
            delta = abs(int(params.get("budget_delta") or round(orig_budget * 0.2)))
            sim_budget = orig_budget + delta
        else:
            delta = abs(int(params.get("budget_delta") or round(orig_budget * 0.2)))
            sim_budget = max(100, orig_budget - delta)
        sim_itin["budget"] = sim_budget
        change_description = f"Adjusted target budget from {curr_sym}{orig_budget:,} to {curr_sym}{sim_budget:,}."

    # 4. Change Transportation (Flight <-> Train)
    elif sc == "change_transport":
        target_mode = str(params.get("transport_mode") or ("Train" if orig_mode.lower() == "flight" else "Flight")).title()
        transport = sim_itin.get("transport") or {}
        if target_mode == "Train":
            trains = transport.get("trains") or []
            if trains:
                fare = next((t.get("lowest_fare_amount") for t in trains if t.get("lowest_fare_amount")), None)
                new_transport_cost = int(fare) * travelers if fare else round(int(orig_bb.get("flights", 0)) * 0.35)
                sim_mode = "Train"
                transportation_changes = f"Switched from {orig_mode} to Train ({trains[0].get('train_name', 'Express Rail')})."
            elif transport.get("nearby_transit") or currency == "INR":
                new_transport_cost = round(int(orig_bb.get("flights", 0)) * 0.4)
                sim_mode = "Train"
                transportation_changes = f"Switched from {orig_mode} to estimated Train/Rail transit."
                warnings.append("Live rail inventory was unavailable; train fare is estimated.")
            else:
                warnings.append(f"Direct rail transit may not be feasible for {trip.destination}; keeping transport comparison advisory.")
                sim_mode = target_mode
                transportation_changes = f"Simulated switch from {orig_mode} to {target_mode} (limited rail link)."
        else:
            flights = transport.get("flights") or []
            if flights and flights[0].get("price_amount"):
                new_transport_cost = int(flights[0]["price_amount"])
            else:
                new_transport_cost = max(int(orig_bb.get("flights", 0)), round(orig_budget * 0.35))
            sim_mode = "Flight"
            transportation_changes = f"Switched from {orig_mode} to Flight."
        change_description = transportation_changes

    # 5. Remove Attraction
    elif sc == "remove_attraction":
        day_num = params.get("day_number")
        att_id = params.get("attraction_id")
        att_name = params.get("attraction_name")
        day, act, act_idx = _locate_activity(
            sim_itin,
            attraction_id=att_id,
            day_number=day_num,
            attraction_name=att_name,
        )
        removed_name = act.get("name", "Attraction")
        removed_cost = int(round(_parse_cost_midpoint(act.get("estimated_cost")) or 0))
        act_cost_delta = -removed_cost
        day["activities"].pop(act_idx)
        slot_key = (act.get("time_slot") or "").lower()
        if slot_key in ("morning", "afternoon", "evening"):
            day[slot_key] = f"[{act.get('time_window') or slot_key.title()}] Open leisure window (removed '{removed_name}')."
        day["suggested_places"] = [p for p in (day.get("suggested_places") or []) if p.lower() != removed_name.lower()]
        change_description = f"Removed '{removed_name}' from Day {day.get('day')}."

    # 6. Replace Attraction
    elif sc == "replace_attraction":
        day_num = params.get("day_number")
        att_id = params.get("attraction_id")
        att_name = params.get("attraction_name")
        replacement = params.get("replacement")
        if not replacement:
            alt_res = find_alternative_attractions(
                trip,
                attraction_id=att_id,
                day_number=day_num,
                attraction_name=att_name,
                reason=params.get("reason", "user_preference"),
                limit=1,
            )
            if not alt_res["alternatives"]:
                raise HTTPException(status_code=404, detail="No suitable replacement attraction found for simulation.")
            replacement = alt_res["alternatives"][0]

        day, old_act, act_idx = _locate_activity(
            sim_itin,
            attraction_id=att_id,
            day_number=day_num,
            attraction_name=att_name,
        )
        old_cost = _parse_cost_midpoint(old_act.get("estimated_cost")) or 0
        new_cost = _parse_cost_midpoint(replacement.get("estimated_cost")) or old_cost
        act_cost_delta = int(round(new_cost - old_cost))
        new_name = replacement["name"]
        slot_name = old_act.get("time_slot") or "Afternoon"
        day["activities"][act_idx] = {
            "attraction_id": old_act.get("attraction_id"),
            "name": new_name,
            "time_slot": slot_name,
            "time_window": old_act.get("time_window"),
            "location": replacement.get("location") or trip.destination,
            "category": replacement.get("category") or old_act.get("category"),
            "estimated_duration": replacement.get("estimated_duration") or old_act.get("estimated_duration"),
            "estimated_cost": replacement.get("estimated_cost") or old_act.get("estimated_cost"),
            "why_it_matches": replacement.get("selection_explanation") or "Simulated attraction swap.",
            "transit_info": replacement.get("estimated_travel_time") or old_act.get("transit_info"),
        }
        slot_key = slot_name.lower()
        if slot_key in ("morning", "afternoon", "evening"):
            day[slot_key] = f"[{old_act.get('time_window') or ''}] {new_name}: {replacement.get('description', '')[:120]}"
        change_description = f"Replaced '{old_act.get('name')}' with '{new_name}' on Day {day.get('day')}."

    # 7. Change Preferences
    elif sc == "change_preferences":
        if params.get("style"):
            prefs["style"] = params["style"]
            sim_itin.setdefault("preferences_applied", {})["style"] = params["style"]
        if params.get("pace"):
            prefs["pace"] = params["pace"]
            sim_itin.setdefault("preferences_applied", {})["pace"] = params["pace"]
        if isinstance(params.get("interests"), list):
            sim_interests = params["interests"]
            sim_itin["interests"] = sim_interests
            sim_itin.setdefault("preferences_applied", {})["interests"] = sim_interests
        change_description = (
            f"Updated preferences (Style: {prefs.get('style')}, Pace: {prefs.get('pace')}, "
            f"Interests: {', '.join(sim_interests) or 'Default'})."
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported simulation scenario: '{scenario}'.")

    sim_days_count = len(sim_itin.get("days") or [])
    new_bb = _recalculate_budget_breakdown(
        sim_itin,
        target_budget=sim_budget,
        orig_days=orig_days_count,
        new_days=sim_days_count,
        travelers=travelers,
        currency=currency,
        curr_sym=curr_sym,
        new_transport_mode=sim_mode,
        new_transport_cost=new_transport_cost,
        act_cost_delta=act_cost_delta,
    )
    sim_itin["budget_breakdown"] = new_bb
    enrich_itinerary_with_explanations(sim_itin)

    sim_total_cost = int(new_bb["total"])
    budget_difference = sim_total_cost - orig_total_cost
    sim_travel_duration = _estimate_intercity_travel_duration(sim_itin, sim_mode)
    sim_attraction_count = _count_attractions(sim_itin)

    if new_bb["exceeds_budget"]:
        over_amt = sim_total_cost - sim_budget
        feasibility_status = "Over Budget"
        warnings.append(
            f"Simulated cost ({curr_sym}{sim_total_cost:,}) exceeds target budget ({curr_sym}{sim_budget:,}) by {curr_sym}{over_amt:,}."
        )
    elif sim_budget > 0 and (sim_total_cost / sim_budget) > 0.92:
        feasibility_status = "Tight"
        warnings.append("Simulated plan uses over 92% of your budget, leaving a small contingency buffer.")
    else:
        feasibility_status = "Feasible"

    if feasibility_status == "Feasible":
        recommendation = f"This change is financially feasible ({curr_sym}{new_bb['remaining_budget']:,} buffer remaining) and ready to apply."
    elif feasibility_status == "Tight":
        recommendation = "Feasible, though buffer is tight. Consider keeping discretionary spending low."
    else:
        recommendation = (
            f"Over budget by {curr_sym}{sim_total_cost - sim_budget:,}. Consider switching to rail transit, "
            f"reducing trip duration, or increasing budget to {curr_sym}{sim_total_cost:,}."
        )

    return {
        "trip_id": trip.id,
        "scenario": sc,
        "change_description": change_description,
        "non_destructive": True,
        "currency": currency,
        "currency_symbol": curr_sym,
        "target_budget": sim_budget,
        "original_total_cost": orig_total_cost,
        "simulated_total_cost": sim_total_cost,
        "budget_difference": budget_difference,
        "original_duration_days": orig_days_count,
        "simulated_duration_days": sim_days_count,
        "original_travel_duration": orig_travel_duration,
        "simulated_travel_duration": sim_travel_duration,
        "original_attraction_count": orig_attraction_count,
        "simulated_attraction_count": sim_attraction_count,
        "transportation_changes": transportation_changes,
        "feasibility_status": feasibility_status,
        "warnings": warnings,
        "recommendation": recommendation,
        "simulated_trip_params": {
            "budget": sim_budget,
            "end_date": sim_end_date.isoformat(),
            "interests": sim_interests,
            "preferences": prefs,
        },
        "simulated_itinerary": sim_itin,
    }


def apply_trip_simulation(
    db: Session,
    trip_id: int,
    user_id: int,
    *,
    scenario: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-validates a What-If simulation and atomically persists it to the trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or access denied.")

    original_itinerary = copy.deepcopy(trip.itinerary or {})
    sim_result = simulate_trip_changes(trip, scenario=scenario, params=params)
    sim_params = sim_result["simulated_trip_params"]
    sim_itin = sim_result["simulated_itinerary"]

    # Record rollback version in TripReoptimization
    existing_count = db.query(TripReoptimization).filter(TripReoptimization.trip_id == trip_id).count()
    reopt = TripReoptimization(
        trip_id=trip_id,
        version=existing_count + 1,
        trigger_reason=f"What-If Simulation Applied ({scenario})",
        original_itinerary=original_itinerary,
        proposed_itinerary=sim_itin,
        diff_summary={
            "scenario": scenario,
            "change_description": sim_result["change_description"],
            "original_total_cost": sim_result["original_total_cost"],
            "simulated_total_cost": sim_result["simulated_total_cost"],
            "budget_difference": sim_result["budget_difference"],
        },
        explanation=sim_result["recommendation"],
        is_simulated=True,
        status="applied",
        applied_changes=[scenario],
    )
    db.add(reopt)

    trip.budget = int(sim_params["budget"])
    trip.end_date = date.fromisoformat(sim_params["end_date"])
    trip.interests = list(sim_params["interests"])
    new_prefs = dict(sim_params["preferences"])
    new_prefs["itinerary"] = sim_itin
    trip.preferences = new_prefs

    db.commit()
    db.refresh(trip)

    return {
        "trip_id": trip.id,
        "status": "applied",
        "reoptimization_id": reopt.id,
        "version": reopt.version,
        "trip": {
            "id": trip.id,
            "destination": trip.destination,
            "start_date": trip.start_date.isoformat(),
            "end_date": trip.end_date.isoformat(),
            "budget": trip.budget,
            "travelers": trip.travelers,
            "interests": trip.interests,
            "currency": trip.currency,
            "preferences": trip.preferences,
        },
        "simulation_summary": {
            "change_description": sim_result["change_description"],
            "original_total_cost": sim_result["original_total_cost"],
            "simulated_total_cost": sim_result["simulated_total_cost"],
            "feasibility_status": sim_result["feasibility_status"],
        },
        "itinerary": sim_itin,
    }
