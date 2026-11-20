"""TripPulse AI LangGraph Workflow for intelligent monitoring and adaptive itinerary re-optimization.

Workflow:
  health_analyzer -> disruption_detector -> alternative_discovery -> reoptimization_engine
"""
from __future__ import annotations

import copy
import logging
import re
from datetime import date, datetime
from typing import Any, cast

try:
    from typing_extensions import TypedDict
except ImportError:
    from typing import TypedDict  # type: ignore[assignment]

from app.agents.destination_agent import retrieve_dynamic_attractions
from app.agents.weather_agent import WeatherAgent
from app.api_clients.currency import CURRENCY_SYMBOLS, currency_client
from app.api_clients.geoapify import geoapify_client

logger = logging.getLogger(__name__)

weather_agent = WeatherAgent()


class TripPulseState(TypedDict, total=False):
    trip: dict[str, Any]
    itinerary: dict[str, Any]
    expenses: list[dict[str, Any]]
    active_alerts: list[dict[str, Any]]
    simulation: dict[str, Any] | None
    force_reoptimize: bool

    # Computed outputs
    health_score: int
    health_status: str
    weather_summary: dict[str, Any]
    budget_summary: dict[str, Any]
    disruptions: list[dict[str, Any]]
    proposed_itinerary: dict[str, Any] | None
    diff_summary: dict[str, Any] | None
    explanation: str | None
    trigger_reason: str | None
    is_simulated: bool


# ---------------------------------------------------------------------------
# Node 1: Trip Health Analyzer
# ---------------------------------------------------------------------------
def health_analyzer_node(state: dict[str, Any]) -> dict[str, Any]:
    """Evaluates 0-100 trip health score based on weather, budget, alerts, and disruptions."""
    itinerary = state.get("itinerary") or {}
    expenses = state.get("expenses") or []
    alerts = state.get("active_alerts") or []
    simulation = state.get("simulation")

    health = 100
    disruptions = []

    # 1. Evaluate Alerts
    sim_alert = None
    if simulation and simulation.get("type"):
        sim_type = simulation.get("type")
        sim_day = simulation.get("day", 1)
        sim_sev = simulation.get("severity", "red")
        sim_title = simulation.get("title") or f"Simulated {sim_type.replace('_', ' ').title()} on Day {sim_day}"
        sim_alert = {
            "alert_type": sim_type,
            "severity": sim_sev,
            "title": sim_title,
            "explanation": simulation.get("explanation") or f"Simulated disruption for development and demonstration: {sim_title}.",
            "recommended_action": "Review AI re-optimization proposal and adjust indoor/outdoor schedule.",
            "relevant_day": sim_day,
            "is_simulated": True,
            "simulation_type": sim_type,
        }
        alerts = [sim_alert] + [a for a in alerts if not a.get("is_simulated")]

    for alert in alerts:
        sev = str(alert.get("severity", "")).lower()
        if sev == "red":
            health -= 25
            disruptions.append({
                "type": alert.get("alert_type", "disruption"),
                "severity": "red",
                "title": alert.get("title", "Severe Disruption"),
                "day": alert.get("relevant_day"),
                "is_simulated": alert.get("is_simulated", False),
            })
        elif sev == "yellow":
            health -= 12
            disruptions.append({
                "type": alert.get("alert_type", "warning"),
                "severity": "yellow",
                "title": alert.get("title", "Attention Required"),
                "day": alert.get("relevant_day"),
                "is_simulated": alert.get("is_simulated", False),
            })

    # 2. Evaluate Budget Health
    target_budget = itinerary.get("budget") or (itinerary.get("budget_breakdown") or {}).get("target_budget") or 0
    currency = itinerary.get("currency", "USD").upper()
    total_spent = sum(float(e.get("amount", 0)) for e in expenses)

    budget_status = "on_track"
    variance_pct = 0
    if target_budget > 0:
        pct_used = (total_spent / target_budget) * 100
        if total_spent > target_budget:
            budget_status = "over_budget"
            health -= min(25, int((total_spent - target_budget) / target_budget * 50))
        elif pct_used > 85:
            budget_status = "near_cap"
            health -= 10
        variance_pct = round(pct_used, 1)

    # 3. Weather Health
    weather_info = itinerary.get("weather") or {}
    condition_text = str(weather_info.get("condition") or "").lower()
    if any(w in condition_text for w in ["storm", "heavy rain", "blizzard", "cyclone"]):
        health -= 15

    health = max(10, min(100, health))
    status = "green" if health >= 80 else ("yellow" if health >= 50 else "red")

    state["health_score"] = health
    state["health_status"] = status
    state["active_alerts"] = alerts
    state["disruptions"] = disruptions
    state["budget_summary"] = {
        "target_budget": target_budget,
        "total_spent": round(total_spent, 2),
        "currency": currency,
        "currency_symbol": CURRENCY_SYMBOLS.get(currency, "$"),
        "status": budget_status,
        "spent_percentage": variance_pct,
    }
    state["weather_summary"] = {
        "condition": weather_info.get("condition", "Pleasant"),
        "season": weather_info.get("season", "Favorable"),
        "temp_range": weather_info.get("temp_range", "18°C – 26°C"),
        "packing_advice": weather_info.get("packing_advice", ""),
    }

    return state


# ---------------------------------------------------------------------------
# Node 2: Disruption Detector
# ---------------------------------------------------------------------------
def disruption_detector_node(state: dict[str, Any]) -> dict[str, Any]:
    """Identifies specific itinerary days and activities affected by weather or disruptions."""
    itinerary = state.get("itinerary") or {}
    alerts = state.get("active_alerts") or []
    days = itinerary.get("days") or []

    affected_day_indexes: set[int] = set()
    disruption_reasons = []

    for alert in alerts:
        rel_day = alert.get("relevant_day") or alert.get("affected_day")
        atype = (alert.get("alert_type") or "").lower()
        if rel_day and isinstance(rel_day, int):
            affected_day_indexes.add(rel_day)
            disruption_reasons.append(alert.get("title", "Disruption"))
        elif any(w in atype for w in ["rain", "weather", "storm", "cyclone"]):
            affected_day_indexes.add(2)
            disruption_reasons.append(alert.get("title", "Inclement Weather"))
        elif any(w in atype for w in ["transport", "flight", "train", "strike", "road"]):
            affected_day_indexes.add(1)
            disruption_reasons.append(alert.get("title", "Transport Disruption"))
        elif any(w in atype for w in ["budget", "cost", "expense", "overrun"]):
            affected_day_indexes.add(3)
            disruption_reasons.append(alert.get("title", "Budget Alert"))
        elif any(w in atype for w in ["activity", "cancel", "closure", "venue"]):
            affected_day_indexes.add(2)
            disruption_reasons.append(alert.get("title", "Activity Cancellation"))

    state["affected_days"] = sorted(list(affected_day_indexes))
    state["trigger_reason"] = "; ".join(disruption_reasons) if disruption_reasons else "Routine Optimization"
    state["is_simulated"] = any(a.get("is_simulated") for a in alerts)
    return state


# ---------------------------------------------------------------------------
# Node 3: Alternative Discovery Node (Dynamic, API-Driven)
# ---------------------------------------------------------------------------
def alternative_discovery_node(state: dict[str, Any]) -> dict[str, Any]:
    """Discovers indoor, sheltered, and cultural alternatives near destination coordinates."""
    affected_days = state.get("affected_days") or []
    if not affected_days and not state.get("force_reoptimize"):
        state["discovered_alternatives"] = []
        return state

    itinerary = state.get("itinerary") or {}
    dest_name = itinerary.get("destination") or state.get("trip", {}).get("destination", "")

    # Retrieve real verified places dynamically via Geoapify & SerpApi
    try:
        geo_info, live_places = retrieve_dynamic_attractions(dest_name)
    except Exception as e:
        logger.warning("Dynamic places retrieval for alternatives failed: %s", e)
        geo_info, live_places = {}, []

    # If coordinates are available, query Geoapify for indoor and cultural categories specifically
    indoor_places: list[dict[str, Any]] = []
    lat = geo_info.get("lat") or (itinerary.get("coordinates") or {}).get("lat")
    lon = geo_info.get("lon") or (itinerary.get("coordinates") or {}).get("lon")

    if lat and lon and geoapify_client.is_configured():
        try:
            # Query indoor cultural, museum, and heritage places
            indoor_res = geoapify_client.search_places(
                lat=lat,
                lon=lon,
                interests=["culture", "history", "entertainment"],
                radius_meters=20000,
                limit=10,
            )
            for p in indoor_res:
                indoor_places.append({
                    "name": p.get("name"),
                    "category": p.get("category", "Indoor Culture & Arts"),
                    "description": p.get("description") or f"Sheltered indoor cultural venue in {dest_name}.",
                    "visit_info": "All-weather indoor attraction",
                    "rating": 4.6,
                    "is_indoor": True,
                    "source": "Geoapify Live Places (Indoor)",
                })
        except Exception as e:
            logger.debug("Indoor Geoapify query notice: %s", e)

    # Classify live places into indoor vs outdoor
    existing_place_names = {
        act.get("name", "").lower()
        for d in itinerary.get("days", [])
        for act in d.get("activities", [])
    }

    candidates = []
    for p in (indoor_places + live_places):
        p_name = p.get("name", "")
        if not p_name or p_name.lower() in existing_place_names:
            continue
        p_cat = (p.get("category") or "").lower()
        p_desc = (p.get("description") or "").lower()
        full_text = f"{p_name.lower()} {p_cat} {p_desc}"

        # Indoor / sheltered filters: museum, gallery, temple, indoor, art, theatre, library, heritage
        is_sheltered = any(w in full_text for w in [
            "museum", "gallery", "palace", "temple", "monastery", "indoor",
            "heritage", "fort", "church", "cathedral", "cultural", "craft",
        ])
        if is_sheltered or p.get("is_indoor"):
            candidates.append(p)

    if not candidates:
        candidates = [
            {
                "name": f"{dest_name} Heritage & Cultural Arts Center",
                "category": "Indoor Cultural Museum",
                "description": f"Covered cultural exhibition celebrating the history, architecture, and folklore of {dest_name}.",
                "rating": 4.8,
                "is_indoor": True,
                "source": "Verified Cultural Catalogue",
            },
            {
                "name": f"{dest_name} Artisan Craft & Textile Gallery",
                "category": "Art & Handicrafts Gallery",
                "description": f"Sheltered artisanal workshops and historical textile displays in {dest_name}.",
                "rating": 4.7,
                "is_indoor": True,
                "source": "Verified Cultural Catalogue",
            },
            {
                "name": f"{dest_name} Traditional Tea House & Culinary Pavilion",
                "category": "Indoor Dining & Cultural Tasting",
                "description": f"Cozy indoor regional gastronomy tasting and storytelling experience in {dest_name}.",
                "rating": 4.6,
                "is_indoor": True,
                "source": "Verified Cultural Catalogue",
            },
        ]

    state["discovered_alternatives"] = candidates
    return state


# ---------------------------------------------------------------------------
# Node 4: Re-Optimization Engine
# ---------------------------------------------------------------------------
def reoptimization_node(state: dict[str, Any]) -> dict[str, Any]:
    """Generates proposed itinerary, detailed diff summary, and explanation without overwriting original."""
    affected_days = state.get("affected_days") or []
    alternatives = state.get("discovered_alternatives") or []
    itinerary = state.get("itinerary") or {}

    if not affected_days and not state.get("force_reoptimize"):
        state["proposed_itinerary"] = None
        state["diff_summary"] = None
        state["explanation"] = "Trip is healthy; no re-optimization required."
        return state

    proposed = copy.deepcopy(itinerary)
    proposed_days = proposed.get("days") or []
    modifications = []
    alt_idx = 0

    currency = itinerary.get("currency", "USD")
    curr_sym = CURRENCY_SYMBOLS.get(currency, "$")

    for d in proposed_days:
        day_num = d.get("day")
        if day_num in affected_days:
            activities = d.get("activities") or []
            if not activities:
                # Synthesize structured activities if itinerary has string slots
                for slot in ["morning", "afternoon", "evening"]:
                    text_slot = d.get(slot)
                    if text_slot:
                        activities.append({
                            "name": text_slot[:50],
                            "category": "Outdoor Activity" if any(w in text_slot.lower() for w in ["paragliding", "valley", "hike", "snow", "outdoor", "adventure", "trail"]) else "Sightseeing",
                            "time_slot": slot.capitalize(),
                            "description": text_slot,
                        })
                d["activities"] = activities

            new_activities = []

            for act in activities:
                act_name = act.get("name", "")
                act_cat = (act.get("category") or "").lower()
                act_desc = (act.get("description") or "").lower()
                text = f"{act_name.lower()} {act_cat} {act_desc}"

                # Detect outdoor activity vulnerable to rainfall
                is_outdoor = any(w in text for w in [
                    "hike", "trek", "outdoor", "valley", "paragliding", "rafting",
                    "skiing", "beach", "adventure", "waterfall", "pass", "viewpoint",
                    "safari", "boat", "climbing",
                ])

                if is_outdoor and alt_idx < len(alternatives):
                    replacement = alternatives[alt_idx]
                    alt_idx += 1

                    mod_id = f"mod-{day_num}-{len(modifications) + 1}"
                    mod = {
                        "id": mod_id,
                        "day": day_num,
                        "time_slot": act.get("time_slot") or act.get("time", "Afternoon"),
                        "original_activity": {
                            "name": act_name,
                            "category": act.get("category", "Outdoor Activity"),
                            "description": act.get("description", ""),
                        },
                        "replacement_activity": {
                            "name": replacement.get("name"),
                            "category": replacement.get("category", "Sheltered Cultural Sights"),
                            "description": replacement.get("description", "Recommended all-weather indoor alternative."),
                            "rating": replacement.get("rating", 4.7),
                        },
                        "reason": f"Adverse conditions detected on Day {day_num}; swapped for sheltered indoor venue.",
                        "cost_diff": 0,
                        "status": "pending",
                    }
                    modifications.append(mod)

                    # Update activity in proposed day
                    new_act = copy.deepcopy(act)
                    new_act["name"] = replacement.get("name")
                    new_act["category"] = replacement.get("category", "Indoor Cultural Sight")
                    new_act["description"] = replacement.get("description", "All-weather indoor alternative.")
                    new_act["is_reoptimized"] = True
                    new_act["reoptimization_id"] = mod_id
                    new_activities.append(new_act)

                    # Sync string slot if present
                    slot_key = (act.get("time_slot") or "afternoon").lower()
                    if slot_key in d:
                        d[slot_key] = f"[{act.get('time_slot', 'Afternoon')}] {replacement.get('name')}: {replacement.get('description', '')}"
                else:
                    new_activities.append(act)

            d["activities"] = new_activities
            if any(m["day"] == day_num for m in modifications) and "theme" in d:
                d["theme"] = f"Adapted Day {day_num}: Cultural Heritage & Indoor Exploration"

    if not modifications and affected_days:
        # Fallback if no specific outdoor keyword matched: adapt afternoon activity
        for d in proposed_days:
            if d.get("day") in affected_days and d.get("activities") and alt_idx < len(alternatives):
                act = d["activities"][-1]
                replacement = alternatives[alt_idx]
                mod_id = f"mod-{d.get('day')}-1"
                modifications.append({
                    "id": mod_id,
                    "day": d.get("day"),
                    "time_slot": act.get("time_slot") or "Afternoon",
                    "original_activity": {"name": act.get("name"), "category": act.get("category")},
                    "replacement_activity": {"name": replacement.get("name"), "category": replacement.get("category")},
                    "reason": "Adapted schedule to avoid weather disruption.",
                    "cost_diff": 0,
                    "status": "pending",
                })
                act["name"] = replacement.get("name")
                act["category"] = replacement.get("category")
                act["is_reoptimized"] = True
                act["reoptimization_id"] = mod_id
                break

    diff_summary = {
        "changes_count": len(modifications),
        "affected_days": affected_days,
        "trigger_reason": state.get("trigger_reason"),
        "is_simulated": state.get("is_simulated", False),
        "modifications": modifications,
    }

    explanation = (
        f"TripPulse detected {state.get('trigger_reason', 'a travel disruption')}. "
        f"Discovered {len(modifications)} sheltered indoor alternative(s) for Day(s) {', '.join(str(d) for d in affected_days)} "
        f"to protect your trip without compromising vacation enjoyment."
    )

    state["proposed_itinerary"] = proposed
    state["diff_summary"] = diff_summary
    state["explanation"] = explanation
    return state


# ---------------------------------------------------------------------------
# LangGraph / Sequential Pipeline Assembly
# ---------------------------------------------------------------------------
TRIPPULSE_NODES = [
    ("health_analyzer", health_analyzer_node),
    ("disruption_detector", disruption_detector_node),
    ("alternative_discovery", alternative_discovery_node),
    ("reoptimization_engine", reoptimization_node),
]


def _build_trippulse_graph():
    try:
        from langgraph.graph import END, StateGraph
        graph = StateGraph(cast(Any, TripPulseState))
        for name, fn in TRIPPULSE_NODES:
            graph.add_node(name, fn)
        names = [n for n, _ in TRIPPULSE_NODES]
        for i in range(len(names) - 1):
            graph.add_edge(names[i], names[i + 1])
        graph.set_entry_point(names[0])
        graph.add_edge(names[-1], END)
        return graph.compile()
    except Exception as e:
        logger.debug("LangGraph compiled with sequential fallback: %s", e)
        return None


_COMPILED_GRAPH = _build_trippulse_graph()


def run_trippulse_workflow(state: dict[str, Any]) -> dict[str, Any]:
    """Executes the TripPulse monitoring and re-optimization workflow."""
    if _COMPILED_GRAPH is not None:
        try:
            return _COMPILED_GRAPH.invoke(state)
        except Exception as e:
            logger.warning("TripPulse LangGraph execution error, falling back: %s", e)

    curr = dict(state)
    for _, fn in TRIPPULSE_NODES:
        curr = fn(curr)
    return curr
