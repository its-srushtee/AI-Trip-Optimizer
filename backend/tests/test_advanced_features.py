"""Automated tests for:
1. Smart Alternative Recommendation Engine
2. Explainable AI Itinerary
3. What-If Trip Simulation & Authorization
"""
import copy
from datetime import date
import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.models.trip import Trip
from app.services.alternative_recommendation_service import (
    find_alternative_attractions,
    replace_attraction_in_itinerary,
)
from app.services.explainability_service import (
    build_attraction_explanation,
    enrich_itinerary_with_explanations,
    extract_itinerary_explanations,
)
from app.services.trip_simulation_service import (
    apply_trip_simulation,
    simulate_trip_changes,
)


def _sample_trip() -> Trip:
    itinerary = {
        "destination": "Jaipur",
        "dates": {"start": "2026-12-10", "end": "2026-12-12", "nights": 2},
        "travelers": 2,
        "interests": ["history", "culture"],
        "budget": 30000,
        "currency": "INR",
        "currency_symbol": "₹",
        "coordinates": {"lat": 26.9124, "lon": 75.7873},
        "weather": {
            "condition": "Clear and sunny",
            "temp_range": "18°C – 26°C",
            "is_live": True,
        },
        "budget_breakdown": {
            "target_budget": 30000,
            "flights": 8000,
            "transport_mode": "Flight",
            "stay": 10000,
            "food": 5000,
            "activities": 4000,
            "local_transit": 1500,
            "miscellaneous": 1500,
            "total": 30000,
            "exceeds_budget": False,
            "remaining_budget": 0,
        },
        "transport": {
            "recommended_mode": "Flight",
            "flights": [{"airline": "IndiGo", "duration": "1h 15m", "price_amount": 8000}],
            "trains": [{"train_name": "Ajmer Shatabdi", "duration": "4h 30m", "lowest_fare_amount": 950}],
        },
        "places_to_visit": [
            {
                "name": "Amber Fort",
                "category": "History & Heritage",
                "coordinates": {"lat": 26.9855, "lon": 75.8513},
                "transit_distance_km": 4.2,
                "tags": ["history", "heritage"],
            },
            {
                "name": "City Palace Museum",
                "category": "Museum & Culture",
                "coordinates": {"lat": 26.9258, "lon": 75.8237},
                "tags": ["culture", "museum"],
            },
        ],
        "days": [
            {
                "day": 1,
                "date": "2026-12-10",
                "theme": "Arrival",
                "morning": "Arrival",
                "afternoon": "Neighborhood walk",
                "evening": "Welcome Dinner",
                "stay": "Heritage Haveli",
                "activities": [
                    {
                        "attraction_id": "day-1-morning",
                        "name": "Arrival & Check-In",
                        "time_slot": "Morning",
                        "time_window": "10:00 AM - 01:00 PM",
                        "location": "Jaipur",
                        "category": "Arrival",
                        "estimated_duration": "2 hours",
                        "estimated_cost": "Included in Stay & Flight",
                    },
                ],
            },
            {
                "day": 2,
                "date": "2026-12-11",
                "theme": "Heritage",
                "morning": "Visit Amber Fort",
                "afternoon": "Visit Nahargarh Park",
                "evening": "Dinner",
                "stay": "Heritage Haveli",
                "suggested_places": ["Amber Fort", "Nahargarh Park"],
                "activities": [
                    {
                        "attraction_id": "day-2-morning",
                        "name": "Amber Fort",
                        "time_slot": "Morning",
                        "time_window": "08:45 AM - 12:00 PM",
                        "location": "Amer, Jaipur",
                        "category": "History & Heritage",
                        "estimated_duration": "2.5 hours",
                        "estimated_cost": "₹500 - ₹800",
                    },
                    {
                        "attraction_id": "day-2-afternoon",
                        "name": "Nahargarh Park",
                        "time_slot": "Afternoon",
                        "time_window": "01:30 PM - 04:45 PM",
                        "location": "Nahargarh Hills",
                        "category": "Nature & Park",
                        "estimated_duration": "2.5 hours",
                        "estimated_cost": "₹300 - ₹500",
                    },
                ],
            },
            {
                "day": 3,
                "date": "2026-12-12",
                "theme": "Departure",
                "morning": "Bazaar",
                "afternoon": "Checkout",
                "evening": "Departure",
                "stay": "Heritage Haveli",
                "activities": [
                    {
                        "attraction_id": "day-3-morning",
                        "name": "Johari Bazaar",
                        "time_slot": "Morning",
                        "time_window": "09:00 AM - 11:30 AM",
                        "location": "Old City",
                        "category": "Shopping",
                        "estimated_duration": "2 hours",
                        "estimated_cost": "Free to browse",
                    },
                ],
            },
        ],
        "preferences_applied": {"style": "Comfort", "pace": "Balanced", "interests": ["history", "culture"]},
    }
    return Trip(
        id=999,
        user_id=1,
        destination="Jaipur",
        start_date=date(2026, 12, 10),
        end_date=date(2026, 12, 12),
        budget=30000,
        travelers=2,
        interests=["history", "culture"],
        preferences={"currency": "INR", "style": "Comfort", "pace": "Balanced", "itinerary": itinerary},
    )


class TestSmartAlternatives(unittest.TestCase):
    def test_preference_and_distance_and_weather_ranking_and_duplicates(self):
        trip = _sample_trip()
        candidates = [
            # Already scheduled -> MUST be excluded as duplicate
            {"name": "Amber Fort", "category": "History & Heritage", "coordinates": {"lat": 26.9855, "lon": 75.8513}},
            # Indoor + culture + nearby -> should rank #1 under bad_weather & preference
            {
                "name": "Albert Hall Museum",
                "category": "Museum & Culture",
                "coordinates": {"lat": 26.9116, "lon": 75.8194},
                "estimated_cost": "₹300",
                "estimated_duration": "2 hours",
                "tags": ["culture", "history", "museum"],
            },
            # Outdoor + far + unrelated -> should rank lower
            {
                "name": "Distant Desert Park",
                "category": "Outdoor Park",
                "coordinates": {"lat": 27.1500, "lon": 75.9900},
                "estimated_cost": "₹2,500",
                "estimated_duration": "3 hours",
                "tags": ["outdoor"],
            },
        ]
        res = find_alternative_attractions(
            trip,
            attraction_id="day-2-afternoon",
            reason="bad_weather",
            candidates_override=candidates,
        )
        alts = res["alternatives"]
        names = [a["name"] for a in alts]
        self.assertNotIn("Amber Fort", names)
        self.assertEqual(alts[0]["name"], "Albert Hall Museum")
        self.assertGreater(alts[0]["suitability_score"], alts[1]["suitability_score"])

    def test_budget_filtering_and_no_alternatives(self):
        trip = _sample_trip()
        candidates = [
            {"name": "Expensive Polo Club", "category": "Sports", "estimated_cost": "₹5,000"},
        ]
        res = find_alternative_attractions(
            trip,
            attraction_id="day-2-afternoon",
            max_budget=400,
            candidates_override=candidates,
        )
        self.assertEqual(res["alternatives"], [])
        self.assertIn("No suitable", res["message"])

    def test_invalid_attraction_id_raises_404(self):
        trip = _sample_trip()
        with self.assertRaises(HTTPException) as ctx:
            find_alternative_attractions(trip, attraction_id="non-existent-id", candidates_override=[])
        self.assertEqual(ctx.exception.status_code, 404)


class TestExplainableItinerary(unittest.TestCase):
    def test_schema_preference_and_budget_explanations(self):
        trip = _sample_trip()
        enriched = enrich_itinerary_with_explanations(copy.deepcopy(trip.itinerary))
        explanations = extract_itinerary_explanations(enriched)
        self.assertGreaterEqual(len(explanations), 4)

        amber = next(e for e in explanations if e["attraction_name"] == "Amber Fort")
        exp = amber["recommendation_explanation"]
        for key in ("preference_match", "location_reason", "budget_reason", "weather_reason", "time_reason", "summary"):
            self.assertIn(key, exp)
            self.assertTrue(len(exp[key]) > 0)
        self.assertIn("History", exp["preference_match"])
        self.assertIn("₹500 - ₹800", exp["budget_reason"])

    def test_missing_weather_and_cost_reported_honestly(self):
        exp = build_attraction_explanation(
            {"name": "Local Walk", "category": "Sightseeing", "time_slot": "Morning"},
            interests=["culture"],
            weather_info={},
            budget_breakdown={},
        )
        self.assertIn("unavailable", exp["weather_reason"].lower())
        self.assertIn("unavailable", exp["budget_reason"].lower())


class TestWhatIfSimulation(unittest.TestCase):
    def test_simulations_are_non_destructive(self):
        trip = _sample_trip()
        orig_budget = trip.budget
        orig_end = trip.end_date
        orig_days = len(trip.itinerary["days"])

        # Budget increase
        inc = simulate_trip_changes(trip, scenario="increase_budget", params={"budget_delta": 10000})
        self.assertEqual(inc["target_budget"], 40000)
        self.assertEqual(inc["feasibility_status"], "Feasible")

        # Budget decrease -> Over Budget
        dec = simulate_trip_changes(trip, scenario="decrease_budget", params={"budget_delta": 15000})
        self.assertEqual(dec["target_budget"], 15000)
        self.assertEqual(dec["feasibility_status"], "Over Budget")

        # Add a day
        add = simulate_trip_changes(trip, scenario="add_day", params={"days_delta": 1})
        self.assertEqual(add["original_duration_days"], 3)
        self.assertEqual(add["simulated_duration_days"], 4)

        # Remove attraction
        rem = simulate_trip_changes(trip, scenario="remove_attraction", params={"attraction_id": "day-2-afternoon"})
        self.assertEqual(rem["simulated_attraction_count"], rem["original_attraction_count"] - 1)

        # Change transport Flight -> Train
        trn = simulate_trip_changes(trip, scenario="change_transport", params={"transport_mode": "Train"})
        self.assertLess(trn["simulated_total_cost"], trn["original_total_cost"])
        self.assertIn("Train", trn["transportation_changes"])

        # Verify original trip was NEVER modified
        self.assertEqual(trip.budget, orig_budget)
        self.assertEqual(trip.end_date, orig_end)
        self.assertEqual(len(trip.itinerary["days"]), orig_days)

    def test_apply_simulation_updates_trip_and_unauthorized_blocked(self):
        trip = _sample_trip()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = trip
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        applied = apply_trip_simulation(
            mock_db,
            trip_id=999,
            user_id=1,
            scenario="add_day",
            params={"days_delta": 1},
        )
        self.assertEqual(applied["status"], "applied")
        self.assertEqual(trip.end_date, date(2026, 12, 13))
        self.assertEqual(len(trip.itinerary["days"]), 4)
        mock_db.commit.assert_called_once()

        # Unauthorized user (no matching trip for user_id=2)
        mock_db_unauth = MagicMock()
        mock_db_unauth.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(HTTPException) as ctx:
            apply_trip_simulation(mock_db_unauth, trip_id=999, user_id=2, scenario="add_day", params={"days_delta": 1})
        self.assertEqual(ctx.exception.status_code, 404)

    def test_unauthenticated_http_requests_rejected(self):
        client = TestClient(app)
        for method, path, body in [
            ("POST", "/trips/1/alternatives", {"attraction_id": "day-2-afternoon"}),
            ("POST", "/trips/1/replace-attraction", {"attraction_id": "day-2-afternoon", "replacement": {"name": "X"}}),
            ("GET", "/trips/1/itinerary-explanations", None),
            ("POST", "/trips/1/simulate", {"scenario": "add_day"}),
            ("POST", "/trips/1/apply-simulation", {"scenario": "add_day"}),
        ]:
            resp = client.request(method, path, json=body)
            self.assertIn(resp.status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
