"""Smart Alternative Recommendation Engine — discovers, scores, ranks, and applies
context-aware replacement attractions for itinerary activities.

Reuses:
- DestinationAgent (`retrieve_dynamic_attractions`) & Geoapify/SerpApi
- WeatherAgent / itinerary weather metadata
- CostAgent / itinerary budget breakdown
- ExplainabilityService for grounded recommendation explanations
"""
from __future__ import annotations

import copy
import logging
import math
import re
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.destination_agent import retrieve_dynamic_attractions
from app.agents.itinerary_agent import estimate_activity_cost
from app.agents.weather_agent import WeatherAgent
from app.api_clients.currency import CURRENCY_SYMBOLS
from app.models.reoptimization import TripReoptimization
from app.models.trip import Trip
from app.services.explainability_service import (
    _parse_cost_midpoint,
    build_attraction_explanation,
    enrich_itinerary_with_explanations,
)

logger = logging.getLogger(__name__)
weather_agent = WeatherAgent()

DEFAULT_SCORING_WEIGHTS: dict[str, float] = {
    "preference": 0.30,
    "distance": 0.20,
    "budget": 0.20,
    "weather": 0.20,
    "time": 0.10,
}

INDOOR_KEYWORDS = (
    "museum", "gallery", "art", "mall", "shopping", "temple", "palace",
    "church", "cathedral", "mosque", "spa", "wellness", "cinema", "theatre",
    "theater", "aquarium", "planetarium", "cafe", "restaurant", "indoor",
    "cultural center", "exhibition", "library", "monastery", "fortress",
)

OUTDOOR_KEYWORDS = (
    "park", "beach", "mountain", "trek", "hike", "waterfall", "lake", "river",
    "garden", "botanical", "zoo", "safari", "viewpoint", "valley", "trail",
    "island", "outdoor", "camp", "peak", "cliff",
)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance in kilometers between two coordinates."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def _parse_duration_hours(dur_str: str | None) -> float | None:
    """Extracts approximate hours from strings like '2 - 3 hours' or '90 mins'."""
    if not dur_str or not isinstance(dur_str, str):
        return None
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", dur_str)]
    if not nums:
        return None
    val = sum(nums[:2]) / min(2, len(nums))
    if "min" in dur_str.lower() and "hour" not in dur_str.lower():
        return round(val / 60.0, 2)
    return round(val, 2)


def _is_indoor(place: dict[str, Any]) -> bool:
    text = f"{place.get('name', '')} {place.get('category', '')} {' '.join(place.get('tags') or [])}".lower()
    return any(k in text for k in INDOOR_KEYWORDS)


def _is_outdoor(place: dict[str, Any]) -> bool:
    text = f"{place.get('name', '')} {place.get('category', '')} {' '.join(place.get('tags') or [])}".lower()
    return any(k in text for k in OUTDOOR_KEYWORDS)


def _locate_activity(
    itinerary: dict[str, Any],
    attraction_id: str | None = None,
    day_number: int | None = None,
    time_slot: str | None = None,
    attraction_name: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """Finds the target day dict, activity dict, and activity index inside `itinerary`."""
    enrich_itinerary_with_explanations(itinerary)
    days = itinerary.get("days") or []

    for day in days:
        if day_number is not None and day.get("day") != day_number:
            continue
        for idx, act in enumerate(day.get("activities") or []):
            if attraction_id and act.get("attraction_id") == attraction_id:
                return day, act, idx
            if time_slot and (act.get("time_slot") or "").lower() == time_slot.lower():
                if day_number is not None or not attraction_name:
                    return day, act, idx
            if attraction_name and (act.get("name") or "").strip().lower() == attraction_name.strip().lower():
                return day, act, idx

    raise HTTPException(status_code=404, detail="Target itinerary attraction not found.")


def _collect_scheduled_names(itinerary: dict[str, Any]) -> set[str]:
    """Collects lowercase names of all activities and suggested places already in the itinerary."""
    names: set[str] = set()
    for day in itinerary.get("days") or []:
        for p in day.get("suggested_places") or []:
            if isinstance(p, str) and p.strip():
                names.add(p.strip().lower())
        for act in day.get("activities") or []:
            if isinstance(act, dict) and act.get("name"):
                names.add(act["name"].strip().lower())
    return names


def _resolve_reference_coords(
    day: dict[str, Any],
    target_act: dict[str, Any],
    itinerary: dict[str, Any],
) -> tuple[float | None, float | None]:
    """Finds reference coordinates from the target/previous attraction or destination center."""
    places_by_name = {
        (p.get("name") or "").strip().lower(): p
        for p in (itinerary.get("places_to_visit") or [])
        if isinstance(p, dict)
    }

    for candidate_name in [target_act.get("name"), *(day.get("suggested_places") or [])]:
        if not candidate_name:
            continue
        meta = places_by_name.get(candidate_name.strip().lower(), {})
        coords = meta.get("coordinates") or {}
        lat = coords.get("lat")
        lon = coords.get("lon") if coords.get("lon") is not None else coords.get("lng")
        if lat is not None and lon is not None:
            return float(lat), float(lon)

    dest_coords = itinerary.get("coordinates") or {}
    lat = dest_coords.get("lat")
    lon = dest_coords.get("lon") if dest_coords.get("lon") is not None else dest_coords.get("lng")
    if lat is not None and lon is not None:
        return float(lat), float(lon)
    return None, None


def find_alternative_attractions(
    trip: Trip,
    *,
    attraction_id: str | None = None,
    day_number: int | None = None,
    time_slot: str | None = None,
    attraction_name: str | None = None,
    reason: str = "user_preference",
    max_budget: float | None = None,
    weights: dict[str, float] | None = None,
    limit: int = 5,
    candidates_override: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Discovers and ranks suitable replacement attractions for a specific itinerary activity."""
    itinerary = copy.deepcopy(trip.itinerary or {})
    if not itinerary or not itinerary.get("days"):
        raise HTTPException(status_code=400, detail="Trip does not have a generated itinerary yet.")

    day, target_act, _ = _locate_activity(
        itinerary,
        attraction_id=attraction_id,
        day_number=day_number,
        time_slot=time_slot,
        attraction_name=attraction_name,
    )

    destination = trip.destination
    prefs = trip.preferences or {}
    currency = (itinerary.get("currency") or trip.currency or "USD").upper()
    curr_sym = CURRENCY_SYMBOLS.get(currency, "$")
    style = prefs.get("style") or (itinerary.get("preferences_applied") or {}).get("style") or "Comfort"
    pace = prefs.get("pace") or (itinerary.get("preferences_applied") or {}).get("pace") or "Balanced"
    interests = [str(i).lower() for i in (trip.interests or itinerary.get("interests") or []) if i]

    # Normalize weights
    w = dict(DEFAULT_SCORING_WEIGHTS)
    if weights:
        for k, v in weights.items():
            if k in w and isinstance(v, (int, float)) and v >= 0:
                w[k] = float(v)
    w_sum = sum(w.values()) or 1.0
    w = {k: v / w_sum for k, v in w.items()}

    # Weather context (reuse itinerary weather or WeatherAgent)
    weather_info = itinerary.get("weather") or {}
    if not weather_info:
        try:
            w_state = weather_agent.run({
                "request": {
                    "destination": destination,
                    "start_date": str(trip.start_date),
                    "end_date": str(trip.end_date),
                },
                "destination": {"country": itinerary.get("country")},
            })
            weather_info = w_state.get("weather") or {}
        except Exception:
            weather_info = {}

    cond_lower = str(weather_info.get("condition") or "").lower()
    bad_weather = reason in ("bad_weather", "weather") or any(
        k in cond_lower for k in ("rain", "storm", "snow", "thunder", "cyclone", "heavy")
    )

    # Budget context
    breakdown = itinerary.get("budget_breakdown") or {}
    total_days = max(1, len(itinerary.get("days") or []))
    daily_act_cap = (
        float(max_budget)
        if max_budget is not None
        else float(breakdown.get("activities") or max(1, trip.budget * 0.15)) / total_days
    )
    if daily_act_cap <= 0:
        daily_act_cap = 50.0

    ref_lat, ref_lon = _resolve_reference_coords(day, target_act, itinerary)
    scheduled_names = _collect_scheduled_names(itinerary)
    target_name_lower = (target_act.get("name") or "").strip().lower()
    target_cat_lower = (target_act.get("category") or "").lower()
    target_hours = _parse_duration_hours(target_act.get("estimated_duration")) or 2.5

    # Gather candidate pool dynamically (avoid duplicates)
    pool: list[dict[str, Any]] = []
    if candidates_override is not None:
        pool.extend(candidates_override)
    else:
        for p in itinerary.get("places_to_visit") or []:
            if isinstance(p, dict):
                pool.append(p)
        try:
            dynamic_places = retrieve_dynamic_attractions(destination, interests=interests, limit=25)
            pool.extend(dynamic_places)
        except Exception as e:
            logger.warning("Dynamic attraction retrieval failed during alternative lookup: %s", e)

    seen_candidates: set[str] = set()
    scored_alternatives: list[dict[str, Any]] = []

    for cand in pool:
        cname = (cand.get("name") or "").strip()
        if not cname:
            continue
        ckey = cname.lower()
        if ckey in seen_candidates or ckey == target_name_lower or ckey in scheduled_names:
            continue
        seen_candidates.add(ckey)

        cand_cat = cand.get("category") or "Attraction"
        cand_cat_l = cand_cat.lower()
        cand_tags = [str(t).lower() for t in (cand.get("tags") or [])]

        # Cost estimation & optional budget cap filter
        est_cost_str = cand.get("estimated_cost") or estimate_activity_cost(cand_cat, style, currency)
        cost_mid = _parse_cost_midpoint(est_cost_str)
        if max_budget is not None and cost_mid is not None and cost_mid > max_budget:
            continue

        # 1. Preference score (0..1)
        matched_prefs = [
            intr for intr in interests
            if intr in cand_cat_l or intr in ckey or any(intr in t for t in cand_tags)
        ]
        cat_overlap = 0.25 if target_cat_lower and any(
            tok in cand_cat_l for tok in target_cat_lower.split() if len(tok) > 3
        ) else 0.0
        if interests:
            pref_score = min(1.0, (len(matched_prefs) / max(1, min(2, len(interests)))) * 0.8 + cat_overlap)
        else:
            pref_score = 0.6 + cat_overlap

        # 2. Distance score (0..1)
        coords = cand.get("coordinates") or {}
        clat = coords.get("lat")
        clon = coords.get("lon") if coords.get("lon") is not None else coords.get("lng")
        distance_km: float | None = None
        travel_time_mins: int | None = None
        if ref_lat is not None and ref_lon is not None and clat is not None and clon is not None:
            distance_km = _haversine_km(ref_lat, ref_lon, float(clat), float(clon))
            travel_time_mins = max(5, int(round((distance_km / 28.0) * 60)))
            distance_score = max(0.0, min(1.0, 1.0 - (distance_km / 30.0)))
        else:
            distance_score = 0.5  # Unknown coordinates: neutral without fabricating distance

        # If reason is excessive travel time, boost nearby candidates or filter very distant ones
        if reason == "excessive_travel_time" and distance_km is not None and distance_km > 25.0:
            continue

        # 3. Budget score (0..1)
        if cost_mid is not None:
            if cost_mid <= daily_act_cap:
                budget_score = 1.0 - (cost_mid / max(1.0, daily_act_cap)) * 0.25
            else:
                over_ratio = (cost_mid - daily_act_cap) / max(1.0, daily_act_cap)
                budget_score = max(0.0, 0.7 - over_ratio * 0.5)
        else:
            budget_score = 0.5

        # 4. Weather score (0..1)
        cand_indoor = _is_indoor(cand)
        cand_outdoor = _is_outdoor(cand)
        if bad_weather:
            if cand_indoor:
                weather_score = 1.0
            elif cand_outdoor:
                weather_score = 0.15
            else:
                weather_score = 0.55
        else:
            weather_score = 0.85

        # 5. Time score (0..1)
        cand_dur_str = cand.get("estimated_duration") or "2 hours"
        cand_hours = _parse_duration_hours(cand_dur_str) or 2.0
        hour_diff = abs(cand_hours - target_hours)
        time_score = max(0.2, min(1.0, 1.0 - (hour_diff / 4.0)))

        weighted = (
            pref_score * w["preference"]
            + distance_score * w["distance"]
            + budget_score * w["budget"]
            + weather_score * w["weather"]
            + time_score * w["time"]
        )
        suitability_score = int(round(weighted * 100))

        # Build concise grounded selection explanation
        reasons_list = []
        if matched_prefs:
            reasons_list.append(f"matches {', '.join(matched_prefs)} interest(s)")
        if bad_weather and cand_indoor:
            reasons_list.append("indoor/sheltered option suited for inclement weather")
        if distance_km is not None:
            reasons_list.append(f"only {distance_km} km away (~{travel_time_mins} mins)")
        if cost_mid is not None and cost_mid <= daily_act_cap:
            reasons_list.append(f"fits daily activity budget ({est_cost_str})")
        if not reasons_list:
            reasons_list.append(f"relevant {cand_cat} option in {destination}")

        selection_explanation = f"Selected because it {', '.join(reasons_list)}."

        # Full explainable breakdown for the candidate
        cand_activity_preview = {
            "name": cname,
            "category": cand_cat,
            "time_slot": target_act.get("time_slot"),
            "time_window": target_act.get("time_window"),
            "location": cand.get("address") or cand.get("location") or destination,
            "estimated_duration": cand_dur_str,
            "estimated_cost": est_cost_str,
            "why_it_matches": cand.get("why_it_matches") or selection_explanation,
            "transit_info": (
                f"~{travel_time_mins} mins ({distance_km} km)" if distance_km is not None else "Local transfer"
            ),
        }
        cand_meta_for_exp = {**cand, "transit_distance_km": distance_km}
        explanation_obj = build_attraction_explanation(
            cand_activity_preview,
            interests=interests,
            style=style,
            pace=pace,
            place_meta=cand_meta_for_exp,
            weather_info=weather_info,
            budget_breakdown=breakdown,
            currency_symbol=curr_sym,
            total_days=total_days,
        )

        scored_alternatives.append({
            "name": cname,
            "category": cand_cat,
            "description": cand.get("description") or f"Curated {cand_cat} experience in {destination}.",
            "location": cand_activity_preview["location"],
            "estimated_cost": est_cost_str,
            "estimated_cost_amount": cost_mid,
            "estimated_duration": cand_dur_str,
            "distance_km": distance_km,
            "estimated_travel_time": f"~{travel_time_mins} mins" if travel_time_mins is not None else "Unavailable",
            "suitability_score": suitability_score,
            "score_breakdown": {
                "preference": round(pref_score * 100),
                "distance": round(distance_score * 100),
                "budget": round(budget_score * 100),
                "weather": round(weather_score * 100),
                "time": round(time_score * 100),
            },
            "is_indoor": cand_indoor,
            "image_url": cand.get("image_url"),
            "coordinates": cand.get("coordinates"),
            "tags": cand.get("tags") or [],
            "selection_explanation": selection_explanation,
            "recommendation_explanation": explanation_obj,
        })

    scored_alternatives.sort(key=lambda x: x["suitability_score"], reverse=True)
    top_alternatives = scored_alternatives[:max(1, limit)]

    return {
        "trip_id": trip.id,
        "destination": destination,
        "day": day.get("day"),
        "time_slot": target_act.get("time_slot"),
        "reason": reason,
        "original_attraction": target_act,
        "weather_context": {
            "condition": weather_info.get("condition"),
            "bad_weather_detected": bad_weather,
            "is_live": weather_info.get("is_live", False),
        },
        "weights_used": w,
        "alternatives": top_alternatives,
        "message": (
            f"Found {len(top_alternatives)} ranked alternative(s) for '{target_act.get('name')}'."
            if top_alternatives
            else f"No suitable non-duplicate alternatives found for '{target_act.get('name')}' under the current constraints."
        ),
    }


def replace_attraction_in_itinerary(
    db: Session,
    trip_id: int,
    user_id: int,
    *,
    attraction_id: str | None = None,
    day_number: int | None = None,
    time_slot: str | None = None,
    replacement: dict[str, Any],
    reason: str = "user_selection",
) -> dict[str, Any]:
    """Replaces an attraction in the user's itinerary while preserving dates,
    chronological order, preferences, and recording a rollback version.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or access denied.")

    original_itinerary = copy.deepcopy(trip.itinerary or {})
    if not original_itinerary or not original_itinerary.get("days"):
        raise HTTPException(status_code=400, detail="Trip does not have a generated itinerary.")

    new_name = (replacement.get("name") or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Replacement attraction name is required.")

    proposed_itinerary = copy.deepcopy(original_itinerary)
    day, old_act, act_idx = _locate_activity(
        proposed_itinerary,
        attraction_id=attraction_id,
        day_number=day_number,
        time_slot=time_slot,
    )

    old_name = old_act.get("name", "")
    # Duplicate prevention (allow replacing with itself only if renaming doesn't collide elsewhere)
    scheduled = _collect_scheduled_names(proposed_itinerary)
    scheduled.discard(old_name.strip().lower())
    if new_name.lower() in scheduled:
        raise HTTPException(
            status_code=400,
            detail=f"'{new_name}' is already scheduled elsewhere in this itinerary.",
        )

    old_cost = _parse_cost_midpoint(old_act.get("estimated_cost")) or 0.0
    new_cost_str = replacement.get("estimated_cost") or old_act.get("estimated_cost")
    new_cost = _parse_cost_midpoint(new_cost_str)
    if new_cost is None:
        new_cost = old_cost
    cost_delta = int(round(new_cost - old_cost))

    slot_name = old_act.get("time_slot") or "Afternoon"
    time_window = old_act.get("time_window") or ""
    transit_str = replacement.get("estimated_travel_time")
    if transit_str and transit_str != "Unavailable":
        transit_info = f"Local transfer ({transit_str})"
    else:
        transit_info = old_act.get("transit_info") or "Convenient local transfer"

    updated_act = {
        "attraction_id": old_act.get("attraction_id"),
        "name": new_name,
        "time_slot": slot_name,
        "time_window": time_window,
        "location": replacement.get("location") or f"{trip.destination} Center",
        "category": replacement.get("category") or old_act.get("category") or "Attraction",
        "estimated_duration": replacement.get("estimated_duration") or old_act.get("estimated_duration") or "2 hours",
        "estimated_cost": new_cost_str,
        "why_it_matches": replacement.get("selection_explanation") or f"User-selected replacement for {old_name}.",
        "transit_info": transit_info,
    }

    day["activities"][act_idx] = updated_act

    # Update narrative slot text (morning / afternoon / evening) while preserving chronology
    slot_key = slot_name.lower()
    if slot_key in ("morning", "afternoon", "evening"):
        prefix = f"[{time_window}] " if time_window else ""
        desc_snippet = (replacement.get("description") or updated_act["why_it_matches"])[:140]
        day[slot_key] = (
            f"{prefix}{new_name}: {desc_snippet} "
            f"(Category: {updated_act['category']}, Duration: {updated_act['estimated_duration']}, "
            f"Cost: {updated_act['estimated_cost'] or 'Included'})."
        )

    # Update suggested_places list on that day
    sug_places = list(day.get("suggested_places") or [])
    if old_name in sug_places:
        sug_places = [new_name if p == old_name else p for p in sug_places]
    elif new_name not in sug_places:
        sug_places.append(new_name)
    day["suggested_places"] = sug_places

    # Ensure replacement place metadata is in places_to_visit for future distance/explanation lookups
    places_list = list(proposed_itinerary.get("places_to_visit") or [])
    if not any((p.get("name") or "").strip().lower() == new_name.lower() for p in places_list if isinstance(p, dict)):
        places_list.append({
            "name": new_name,
            "description": replacement.get("description") or updated_act["why_it_matches"],
            "category": updated_act["category"],
            "location": updated_act["location"],
            "coordinates": replacement.get("coordinates"),
            "estimated_duration": updated_act["estimated_duration"],
            "tags": replacement.get("tags") or [],
            "image_url": replacement.get("image_url") or "/images/hero.jpg",
        })
        proposed_itinerary["places_to_visit"] = places_list

    # Recalculate budget breakdown if cost changed
    bb = dict(proposed_itinerary.get("budget_breakdown") or {})
    if cost_delta != 0 and "activities" in bb:
        bb["activities"] = max(0, int(bb["activities"]) + cost_delta)
        bb["total"] = max(0, int(bb.get("total", 0)) + cost_delta)
        target_b = int(bb.get("target_budget") or trip.budget or 0)
        if target_b > 0:
            bb["remaining_budget"] = max(0, target_b - bb["total"])
            bb["budget_variance"] = target_b - bb["total"]
            bb["exceeds_budget"] = bb["total"] > target_b
            bb["utilization_percent"] = min(100, round((bb["total"] / target_b) * 100))
        proposed_itinerary["budget_breakdown"] = bb

    # Re-generate grounded explanations
    enrich_itinerary_with_explanations(proposed_itinerary)

    # Version history for rollback
    existing_count = db.query(TripReoptimization).filter(TripReoptimization.trip_id == trip_id).count()
    reopt = TripReoptimization(
        trip_id=trip_id,
        version=existing_count + 1,
        trigger_reason=f"Attraction Replacement ({reason}): {old_name} -> {new_name}",
        original_itinerary=original_itinerary,
        proposed_itinerary=proposed_itinerary,
        diff_summary={
            "day": day.get("day"),
            "time_slot": slot_name,
            "old_attraction": old_name,
            "new_attraction": new_name,
            "cost_delta": cost_delta,
        },
        explanation=updated_act["why_it_matches"],
        is_simulated=False,
        status="applied",
        applied_changes=[old_act.get("attraction_id") or f"day-{day.get('day')}-{slot_key}"],
    )
    db.add(reopt)

    trip.itinerary = proposed_itinerary
    db.commit()
    db.refresh(trip)

    return {
        "trip_id": trip.id,
        "reoptimization_id": reopt.id,
        "version": reopt.version,
        "replaced": {"old": old_name, "new": new_name, "day": day.get("day"), "time_slot": slot_name},
        "cost_delta": cost_delta,
        "itinerary": proposed_itinerary,
    }
