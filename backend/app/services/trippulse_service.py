"""TripPulse AI Service — Intelligent travel monitoring, disruption simulation,
adaptive re-optimization, approval gating, and version rollback.
"""
from __future__ import annotations

import copy
import logging
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.alert import TripAlert, TripMonitoringLog
from app.models.expense import TripExpense
from app.models.reoptimization import TripReoptimization
from app.models.trip import Trip
from app.workflows.trippulse_graph import run_trippulse_workflow

logger = logging.getLogger(__name__)


def _verify_trip_ownership(db: Session, trip_id: int, user_id: int) -> Trip:
    """Verifies that the requested trip exists and belongs to the authenticated user."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or access denied.")
    return trip


def get_trip_pulse(db: Session, trip_id: int, user_id: int) -> dict[str, Any]:
    """Retrieves full TripPulse status: health score, weather, budget health, alerts, proposals."""
    trip = _verify_trip_ownership(db, trip_id, user_id)

    # 1. Fetch active alerts
    alerts = (
        db.query(TripAlert)
        .filter(TripAlert.trip_id == trip_id, TripAlert.is_dismissed == False)  # noqa: E712
        .order_by(TripAlert.created_at.desc())
        .all()
    )
    alerts_data = [
        {
            "id": a.id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "explanation": a.explanation,
            "recommended_action": a.recommended_action,
            "relevant_date": str(a.relevant_date) if a.relevant_date else None,
            "is_simulated": a.is_simulated,
            "simulation_type": a.simulation_type,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]

    # 2. Fetch expenses
    expenses = (
        db.query(TripExpense)
        .filter(TripExpense.trip_id == trip_id)
        .order_by(TripExpense.date.desc())
        .all()
    )
    expenses_data = [
        {"id": e.id, "amount": float(e.amount), "category": e.category, "currency": e.currency}
        for e in expenses
    ]

    # 3. Fetch proposals / re-optimization history
    proposals = (
        db.query(TripReoptimization)
        .filter(TripReoptimization.trip_id == trip_id)
        .order_by(TripReoptimization.created_at.desc())
        .all()
    )
    proposals_data = [
        {
            "id": p.id,
            "version": p.version,
            "trigger_reason": p.trigger_reason,
            "diff_summary": p.diff_summary,
            "explanation": p.explanation,
            "is_simulated": p.is_simulated,
            "status": p.status,
            "applied_changes": p.applied_changes,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in proposals
    ]

    # 4. Run TripPulse LangGraph workflow for health evaluation
    workflow_state = {
        "trip": {"id": trip.id, "destination": trip.destination},
        "itinerary": trip.itinerary or {},
        "expenses": expenses_data,
        "active_alerts": alerts_data,
    }
    evaluated = run_trippulse_workflow(workflow_state)

    # 5. Log monitoring check
    try:
        log = TripMonitoringLog(
            trip_id=trip.id,
            overall_health=evaluated.get("health_score", 100),
            health_status=evaluated.get("health_status", "green"),
            weather_status=evaluated.get("weather_summary", {}),
            budget_status=evaluated.get("budget_summary", {}),
            disruptions_detected=evaluated.get("disruptions", []),
            recommendations_summary=evaluated.get("explanation"),
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.debug("Failed to record TripMonitoringLog: %s", e)
        db.rollback()

    pending_proposal = next((p for p in proposals_data if p["status"] == "pending"), None)

    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "health_score": evaluated.get("health_score", 100),
        "health_status": evaluated.get("health_status", "green"),
        "weather": evaluated.get("weather_summary", {}),
        "budget": evaluated.get("budget_summary", {}),
        "alerts": alerts_data,
        "disruptions": evaluated.get("disruptions", []),
        "pending_proposal": pending_proposal,
        "history": proposals_data,
        "last_checked_at": evaluated.get("weather_summary", {}).get("checked_at"),
    }


def simulate_disruption(
    db: Session,
    trip_id: int,
    user_id: int,
    simulation_type: str,
    affected_day: int = 2,
    severity: str = "red",
    custom_title: str | None = None,
) -> dict[str, Any]:
    """Simulates a travel disruption (heavy rain, activity cancellation, transport disruption)

    Generates AI re-optimization proposal without modifying the user's active itinerary.
    """
    trip = _verify_trip_ownership(db, trip_id, user_id)

    # Human-friendly descriptions
    sim_configs = {
        "heavy_rain": {
            "title": f"Severe Heavy Rainfall on Day {affected_day}",
            "explanation": f"Monsoon/torrential rain alert issued for Day {affected_day}. Outdoor hiking and valley activities are disrupted.",
            "rec": "Reschedule outdoor activities to sheltered cultural or museum venues.",
        },
        "activity_cancelled": {
            "title": f"Activity Venue Closure on Day {affected_day}",
            "explanation": f"Scheduled venue or excursion on Day {affected_day} is temporarily closed for maintenance.",
            "rec": "Substitute with recommended nearby landmark.",
        },
        "transport_delay": {
            "title": f"Transport Disruption on Day {affected_day}",
            "explanation": f"Scheduled transit connection on Day {affected_day} faces significant delay.",
            "rec": "Reorder afternoon activities to allow extra transit buffer.",
        },
        "budget_overrun": {
            "title": f"Budget Alert on Day {affected_day}",
            "explanation": f"Actual expenses on Day {affected_day} deviate significantly from target allocation.",
            "rec": "Swap premium dining or paid activities for free scenic viewpoints.",
        },
    }

    config = sim_configs.get(simulation_type, {
        "title": custom_title or f"Simulated Disruption on Day {affected_day}",
        "explanation": f"Simulated {simulation_type} disruption on Day {affected_day}.",
        "rec": "Review AI re-optimization recommendations.",
    })

    # 1. Create simulated alert in database
    alert = TripAlert(
        trip_id=trip.id,
        alert_type=simulation_type,
        severity=severity,
        title=config["title"],
        explanation=config["explanation"],
        recommended_action=config["rec"],
        is_simulated=True,
        simulation_type=simulation_type,
        is_dismissed=False,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # 2. Run TripPulse LangGraph workflow to discover alternatives and create proposal
    workflow_state = {
        "trip": {"id": trip.id, "destination": trip.destination},
        "itinerary": trip.itinerary or {},
        "active_alerts": [
            {
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "relevant_day": affected_day,
                "is_simulated": True,
            }
        ],
        "simulation": {
            "type": simulation_type,
            "day": affected_day,
            "severity": severity,
            "title": config["title"],
            "explanation": config["explanation"],
        },
        "force_reoptimize": True,
    }

    evaluated = run_trippulse_workflow(workflow_state)
    proposed_itin = evaluated.get("proposed_itinerary")
    diff_sum = evaluated.get("diff_summary")

    if proposed_itin and diff_sum and diff_sum.get("modifications"):
        # Determine next re-optimization version
        last_version = (
            db.query(TripReoptimization.version)
            .filter(TripReoptimization.trip_id == trip.id)
            .order_by(TripReoptimization.version.desc())
            .first()
        )
        next_ver = (last_version[0] + 1) if last_version else 1

        reopt = TripReoptimization(
            trip_id=trip.id,
            version=next_ver,
            trigger_reason=alert.title,
            original_itinerary=copy.deepcopy(trip.itinerary or {}),
            proposed_itinerary=proposed_itin,
            diff_summary=diff_sum,
            explanation=evaluated.get("explanation", "AI adaptive re-optimization generated."),
            is_simulated=True,
            status="pending",
            applied_changes=[],
        )
        db.add(reopt)
        db.commit()
        db.refresh(reopt)

    return get_trip_pulse(db, trip_id, user_id)


def trigger_reoptimization(db: Session, trip_id: int, user_id: int) -> dict[str, Any]:
    """Generates an adaptive itinerary re-optimization based on real active alerts and conditions."""
    trip = _verify_trip_ownership(db, trip_id, user_id)

    alerts = (
        db.query(TripAlert)
        .filter(TripAlert.trip_id == trip_id, TripAlert.is_dismissed == False)  # noqa: E712
        .all()
    )
    alerts_data = [
        {
            "id": a.id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "is_simulated": a.is_simulated,
            "simulation_type": a.simulation_type,
            "relevant_day": 2 if "rain" in (a.alert_type or "").lower() else 1,
        }
        for a in alerts
    ]

    workflow_state = {
        "trip": {"id": trip.id, "destination": trip.destination},
        "itinerary": trip.itinerary or {},
        "active_alerts": alerts_data,
        "force_reoptimize": True,
    }
    evaluated = run_trippulse_workflow(workflow_state)

    proposed_itin = evaluated.get("proposed_itinerary")
    diff_sum = evaluated.get("diff_summary")

    if proposed_itin and diff_sum and diff_sum.get("modifications"):
        last_ver = (
            db.query(TripReoptimization.version)
            .filter(TripReoptimization.trip_id == trip.id)
            .order_by(TripReoptimization.version.desc())
            .first()
        )
        next_ver = (last_ver[0] + 1) if last_ver else 1

        reopt = TripReoptimization(
            trip_id=trip.id,
            version=next_ver,
            trigger_reason="Real-Time Disruption Re-Optimization",
            original_itinerary=copy.deepcopy(trip.itinerary or {}),
            proposed_itinerary=proposed_itin,
            diff_summary=diff_sum,
            explanation=evaluated.get("explanation", "Itinerary adapted to avoid travel disruptions."),
            is_simulated=any(a.get("is_simulated") for a in alerts_data),
            status="pending",
            applied_changes=[],
        )
        db.add(reopt)
        db.commit()

    return get_trip_pulse(db, trip_id, user_id)


def apply_reoptimization(
    db: Session,
    trip_id: int,
    reopt_id: int,
    user_id: int,
    accepted_mod_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Applies a re-optimization proposal (either all modifications or a user-selected subset).

    Never modifies trip itinerary without explicit user approval.
    Preserves original version in TripReoptimization for rollback.
    """
    trip = _verify_trip_ownership(db, trip_id, user_id)

    reopt = (
        db.query(TripReoptimization)
        .filter(TripReoptimization.id == reopt_id, TripReoptimization.trip_id == trip_id)
        .first()
    )
    if not reopt:
        raise HTTPException(status_code=404, detail="Re-optimization proposal not found.")

    if reopt.status == "applied":
        raise HTTPException(status_code=400, detail="This re-optimization has already been applied.")

    all_mods = (reopt.diff_summary or {}).get("modifications", [])
    accepted_set = set(accepted_mod_ids) if accepted_mod_ids else {m["id"] for m in all_mods}

    # Clone current itinerary to apply accepted modifications
    updated_itinerary = copy.deepcopy(trip.itinerary or {})
    applied_count = 0

    for mod in all_mods:
        mod_id = mod["id"]
        if mod_id in accepted_set:
            target_day = mod["day"]
            repl = mod["replacement_activity"]
            orig = mod["original_activity"]

            for d in updated_itinerary.get("days", []):
                if d.get("day") == target_day:
                    for act in d.get("activities", []):
                        if act.get("name") == orig.get("name") or act.get("reoptimization_id") == mod_id:
                            act["name"] = repl.get("name")
                            act["category"] = repl.get("category")
                            act["description"] = repl.get("description")
                            act["is_reoptimized"] = True
                            act["applied_mod_id"] = mod_id
                            applied_count += 1
                            break

    # Persist updated itinerary to Trip
    trip.itinerary = updated_itinerary
    reopt.status = "applied"
    reopt.applied_changes = list(accepted_set)

    # Dismiss related simulated or severe alert once resolved
    related_alerts = (
        db.query(TripAlert)
        .filter(TripAlert.trip_id == trip_id, TripAlert.is_dismissed == False)  # noqa: E712
        .all()
    )
    for a in related_alerts:
        if a.is_simulated or "Rain" in a.title or "Closure" in a.title:
            a.is_dismissed = True

    db.commit()
    db.refresh(trip)

    return {
        "status": "success",
        "message": f"Successfully applied {applied_count} itinerary update(s).",
        "trip_id": trip.id,
        "reopt_id": reopt.id,
        "applied_changes": list(accepted_set),
        "pulse": get_trip_pulse(db, trip_id, user_id),
    }


def rollback_reoptimization(
    db: Session,
    trip_id: int,
    reopt_id: int,
    user_id: int,
) -> dict[str, Any]:
    """Rolls back an applied re-optimization, restoring the previous original itinerary."""
    trip = _verify_trip_ownership(db, trip_id, user_id)

    reopt = (
        db.query(TripReoptimization)
        .filter(TripReoptimization.id == reopt_id, TripReoptimization.trip_id == trip_id)
        .first()
    )
    if not reopt:
        raise HTTPException(status_code=404, detail="Re-optimization record not found.")

    if reopt.status != "applied":
        raise HTTPException(status_code=400, detail="Only applied re-optimizations can be rolled back.")

    # Revert trip itinerary to the original snapshot
    trip.itinerary = copy.deepcopy(reopt.original_itinerary)
    reopt.status = "rolled_back"

    db.commit()
    db.refresh(trip)

    return {
        "status": "success",
        "message": f"Successfully rolled back itinerary to Version {reopt.version} baseline.",
        "trip_id": trip.id,
        "reopt_id": reopt.id,
        "pulse": get_trip_pulse(db, trip_id, user_id),
    }


def dismiss_alert(
    db: Session,
    trip_id: int,
    alert_id: int,
    user_id: int,
) -> dict[str, Any]:
    """Dismisses an alert for a trip owned by the user."""
    _verify_trip_ownership(db, trip_id, user_id)

    alert = (
        db.query(TripAlert)
        .filter(TripAlert.id == alert_id, TripAlert.trip_id == trip_id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    alert.is_dismissed = True
    db.commit()

    return {"status": "success", "message": "Alert dismissed."}
