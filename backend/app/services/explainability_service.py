"""Explainable AI Itinerary Service — generates grounded, transparent explanations
for why each attraction/activity in an itinerary was recommended.

All explanations are derived strictly from actual trip preferences, attraction
metadata, route distances, estimated costs, weather data, and schedule slots.
Missing data is reported honestly as unavailable rather than fabricated.
"""
from __future__ import annotations

import re
from typing import Any


def _parse_cost_midpoint(cost_str: str | None) -> float | None:
    """Extracts a numeric midpoint from formatted cost strings like '₹500 - ₹1,200'."""
    if not cost_str or not isinstance(cost_str, str):
        return None
    low = cost_str.lower()
    if "free" in low or "included" in low:
        return 0.0
    nums = [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", cost_str)]
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0]
    return sum(nums[:2]) / 2.0


def build_attraction_explanation(
    activity: dict[str, Any],
    *,
    interests: list[str] | None = None,
    style: str | None = None,
    pace: str | None = None,
    food_pref: str | None = None,
    place_meta: dict[str, Any] | None = None,
    weather_info: dict[str, Any] | None = None,
    budget_breakdown: dict[str, Any] | None = None,
    currency_symbol: str = "$",
    total_days: int = 1,
) -> dict[str, str]:
    """Builds a structured, data-grounded explanation for a single itinerary activity."""
    interests = [str(i).lower() for i in (interests or []) if i]
    place_meta = place_meta or {}
    weather_info = weather_info or {}
    budget_breakdown = budget_breakdown or {}

    name = activity.get("name", "Attraction")
    category = activity.get("category") or place_meta.get("category") or ""
    cat_lower = category.lower()
    tags = [str(t).lower() for t in (place_meta.get("tags") or [])]
    why_meta = activity.get("why_it_matches") or place_meta.get("why_it_matches") or ""

    # 1. Preference Match
    matched_interests = [
        intr for intr in interests
        if intr in cat_lower or intr in name.lower() or any(intr in t for t in tags)
    ]
    if matched_interests:
        pref_text = (
            f"Matches your selected interest(s): {', '.join(m.title() for m in matched_interests)}"
            + (f" and fits your {style} style" if style else "")
            + "."
        )
    elif why_meta:
        pref_text = why_meta if why_meta.endswith(".") else f"{why_meta}."
    elif style or pace:
        pref_text = (
            f"Selected to align with your {style or 'balanced'} travel style"
            + (f" and {pace} pace" if pace else "")
            + "."
        )
    else:
        pref_text = "User preference match data unavailable; included as a general highlight."

    if food_pref and food_pref.lower() not in ("no preference", "none") and any(
        k in cat_lower or k in name.lower() for k in ["dining", "food", "lunch", "dinner", "culinary"]
    ):
        pref_text += f" Accommodates your {food_pref} dining preference."

    # 2. Location Suitability
    transit_info = activity.get("transit_info") or ""
    transit_km = place_meta.get("transit_distance_km")
    location_str = activity.get("location") or place_meta.get("address") or place_meta.get("location")
    if transit_km is not None:
        location_reason = (
            f"Located ~{round(float(transit_km), 1)} km from the previous stop"
            + (f" ({location_str})" if location_str else "")
            + ", minimizing transit backtracking."
        )
    elif transit_info:
        location_reason = f"Route logistics: {transit_info}."
    elif location_str:
        location_reason = f"Situated at {location_str}; exact inter-stop distance unavailable."
    else:
        location_reason = "Location distance data unavailable for this activity."

    # 3. Budget Suitability
    est_cost_str = activity.get("estimated_cost")
    parsed_cost = _parse_cost_midpoint(est_cost_str)
    act_budget_total = budget_breakdown.get("activities")
    daily_act_budget = (
        round(float(act_budget_total) / max(1, total_days), 2)
        if act_budget_total is not None
        else None
    )

    if est_cost_str and parsed_cost is not None:
        if parsed_cost == 0:
            budget_reason = f"Free or included ({est_cost_str}), preserving your remaining budget."
        elif daily_act_budget is not None:
            if parsed_cost <= daily_act_budget:
                budget_reason = (
                    f"Estimated at {est_cost_str}, fitting comfortably within your "
                    f"~{currency_symbol}{int(round(daily_act_budget)):,}/day activity allocation."
                )
            else:
                budget_reason = (
                    f"Estimated at {est_cost_str}, which is higher than the average "
                    f"~{currency_symbol}{int(round(daily_act_budget)):,}/day activity target."
                )
        else:
            budget_reason = f"Estimated cost is {est_cost_str}; daily activity allocation unavailable."
    else:
        budget_reason = "Estimated activity cost data unavailable."

    # 4. Weather Suitability
    condition = weather_info.get("condition")
    temp_range = weather_info.get("temp_range")
    is_live_weather = weather_info.get("is_live")
    is_outdoor = any(
        k in f"{cat_lower} {name.lower()} {' '.join(tags)}"
        for k in ["park", "beach", "mountain", "outdoor", "nature", "garden", "trek", "fort", "lake", "waterfall", "walk"]
    )
    is_indoor = any(
        k in f"{cat_lower} {name.lower()} {' '.join(tags)}"
        for k in ["museum", "gallery", "mall", "indoor", "spa", "temple", "palace", "restaurant", "dining", "cafe", "check-in", "departure"]
    )

    if condition:
        cond_lower = str(condition).lower()
        inclement = any(w in cond_lower for w in ["rain", "storm", "snow", "thunder", "cyclone", "heavy"])
        src_label = "live forecast" if is_live_weather else "seasonal climate guidance"
        if inclement and is_outdoor and not is_indoor:
            weather_reason = (
                f"Caution: {src_label} indicates '{condition}'"
                + (f" ({temp_range})" if temp_range else "")
                + "; this outdoor activity may be weather-sensitive."
            )
        elif inclement and is_indoor:
            weather_reason = (
                f"Well-suited indoor/sheltered option for '{condition}' ({src_label})."
            )
        else:
            weather_reason = (
                f"Suitable for expected conditions: {condition}"
                + (f" ({temp_range})" if temp_range else "")
                + f" per {src_label}."
            )
    else:
        weather_reason = "Weather condition data unavailable for this date."

    # 5. Time Suitability
    time_slot = activity.get("time_slot")
    time_window = activity.get("time_window")
    est_dur = activity.get("estimated_duration")
    if time_slot or time_window:
        slot_label = f"{time_slot} ({time_window})" if time_slot and time_window else (time_slot or time_window)
        time_reason = (
            f"Scheduled in the {slot_label} slot"
            + (f" with an estimated duration of {est_dur}" if est_dur else "")
            + (f" aligned to your {pace} pace." if pace else ".")
        )
    else:
        time_reason = "Schedule timing details unavailable."

    # 6. Summary
    summary_parts = []
    if matched_interests:
        summary_parts.append(f"matches your {', '.join(matched_interests)} interest(s)")
    elif why_meta:
        summary_parts.append("fits your trip theme")
    if transit_km is not None:
        summary_parts.append(f"keeps travel short (~{round(float(transit_km), 1)} km)")
    if parsed_cost is not None and (daily_act_budget is None or parsed_cost <= daily_act_budget):
        summary_parts.append("stays within budget")
    if condition and not (any(w in str(condition).lower() for w in ["rain", "storm"]) and is_outdoor):
        summary_parts.append("suits expected weather")

    if summary_parts:
        summary = f"Recommended because it {', '.join(summary_parts)}."
    else:
        summary = f"Included in your {time_slot or 'daily'} schedule based on available destination data."

    return {
        "preference_match": pref_text,
        "location_reason": location_reason,
        "budget_reason": budget_reason,
        "weather_reason": weather_reason,
        "time_reason": time_reason,
        "summary": summary,
    }


def enrich_itinerary_with_explanations(itinerary: dict[str, Any]) -> dict[str, Any]:
    """Adds deterministic, grounded `attraction_id` and `recommendation_explanation`
    fields to every activity in `itinerary["days"]` without overwriting existing valid data.
    """
    if not itinerary or not isinstance(itinerary, dict):
        return itinerary

    days = itinerary.get("days") or []
    total_days = max(1, len(days))
    prefs = itinerary.get("preferences_applied") or {}
    interests = itinerary.get("interests") or prefs.get("interests") or []
    style = prefs.get("style")
    pace = prefs.get("pace")
    food_pref = prefs.get("food")
    weather_info = itinerary.get("weather") or {}
    budget_breakdown = itinerary.get("budget_breakdown") or {}
    currency_symbol = itinerary.get("currency_symbol") or "$"

    # Index places_to_visit by lowercase name for quick metadata lookup
    places_index: dict[str, dict[str, Any]] = {}
    for p in itinerary.get("places_to_visit") or []:
        if isinstance(p, dict) and p.get("name"):
            places_index[p["name"].strip().lower()] = p

    for day in days:
        day_num = day.get("day", 1)
        activities = day.get("activities") or []
        for idx, act in enumerate(activities):
            if not isinstance(act, dict):
                continue
            slot = (act.get("time_slot") or f"slot{idx + 1}").lower().replace(" ", "_")
            if not act.get("attraction_id"):
                act["attraction_id"] = f"day-{day_num}-{slot}"

            act_name_key = (act.get("name") or "").strip().lower()
            place_meta = places_index.get(act_name_key, {})

            act["recommendation_explanation"] = build_attraction_explanation(
                act,
                interests=interests,
                style=style,
                pace=pace,
                food_pref=food_pref,
                place_meta=place_meta,
                weather_info=weather_info,
                budget_breakdown=budget_breakdown,
                currency_symbol=currency_symbol,
                total_days=total_days,
            )

    return itinerary


def extract_itinerary_explanations(itinerary: dict[str, Any]) -> list[dict[str, Any]]:
    """Extracts structured explanations for all scheduled attractions across days."""
    enriched = enrich_itinerary_with_explanations(itinerary)
    results: list[dict[str, Any]] = []
    for day in enriched.get("days") or []:
        day_num = day.get("day")
        day_date = str(day.get("date") or "")
        for act in day.get("activities") or []:
            results.append({
                "attraction_id": act.get("attraction_id"),
                "day": day_num,
                "date": day_date,
                "time_slot": act.get("time_slot"),
                "attraction_name": act.get("name"),
                "category": act.get("category"),
                "recommendation_explanation": act.get("recommendation_explanation", {}),
            })
    return results
