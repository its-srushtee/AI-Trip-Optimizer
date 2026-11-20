"""Unit and integration tests for TripPulse AI LangGraph workflow and service."""
import unittest
import uuid
from datetime import date
from unittest.mock import patch

from app.database.base import Base, SessionLocal, engine
from app.models.alert import TripAlert
from app.models.reoptimization import TripReoptimization
from app.models.trip import Trip
from app.models.user import User
from app.services.trippulse_service import (
    apply_reoptimization,
    dismiss_alert,
    get_trip_pulse,
    rollback_reoptimization,
    simulate_disruption,
)
from app.workflows.trippulse_graph import (
    alternative_discovery_node,
    disruption_detector_node,
    health_analyzer_node,
    reoptimization_node,
    run_trippulse_workflow,
)


class TestTripPulseWorkflow(unittest.TestCase):
    def setUp(self):
        self.sample_manali_itinerary = {
            "destination": "Manali",
            "budget": 35000,
            "currency": "INR",
            "days": [
                {
                    "day": 1,
                    "date": "2026-12-01",
                    "activities": [
                        {"name": "Arrival & Mall Road Walk", "category": "Walking & Leisure", "time": "Evening"}
                    ],
                },
                {
                    "day": 2,
                    "date": "2026-12-02",
                    "activities": [
                        {"name": "Solang Valley Outdoor Adventure & Paragliding", "category": "Adventure & Outdoors", "time": "Morning"},
                        {"name": "Jogini Waterfall Hike", "category": "Nature & Hiking", "time": "Afternoon"},
                    ],
                },
                {
                    "day": 3,
                    "date": "2026-12-03",
                    "activities": [
                        {"name": "Hadimba Temple Visit", "category": "Culture & Heritage", "time": "Morning"}
                    ],
                },
            ],
            "weather": {"condition": "Sunny", "temp_range": "8°C – 18°C"},
        }

    def test_health_analyzer_healthy_trip(self):
        state = {
            "itinerary": self.sample_manali_itinerary,
            "expenses": [],
            "active_alerts": [],
        }
        res = health_analyzer_node(state)
        self.assertEqual(res["health_score"], 100)
        self.assertEqual(res["health_status"], "green")
        self.assertEqual(len(res["disruptions"]), 0)

    def test_health_analyzer_severe_alert(self):
        state = {
            "itinerary": self.sample_manali_itinerary,
            "expenses": [],
            "active_alerts": [
                {"alert_type": "heavy_rain", "severity": "red", "title": "Severe Rain Alert", "relevant_day": 2}
            ],
        }
        res = health_analyzer_node(state)
        self.assertLessEqual(res["health_score"], 75)
        self.assertEqual(res["health_status"], "yellow")
        self.assertEqual(len(res["disruptions"]), 1)

    def test_disruption_detector_identifies_affected_day(self):
        state = {
            "itinerary": self.sample_manali_itinerary,
            "active_alerts": [
                {"alert_type": "heavy_rain", "severity": "red", "title": "Torrential Downpour", "relevant_day": 2}
            ],
        }
        res = disruption_detector_node(state)
        self.assertIn(2, res["affected_days"])
        self.assertIn("Torrential Downpour", res["trigger_reason"])

    def test_reoptimization_node_swaps_outdoor_for_indoor(self):
        state = {
            "itinerary": self.sample_manali_itinerary,
            "affected_days": [2],
            "trigger_reason": "Heavy Rainfall on Day 2",
            "is_simulated": True,
            "discovered_alternatives": [
                {
                    "name": "Museum of Himachal Culture & Folk Art",
                    "category": "Culture & Heritage",
                    "description": "Sheltered indoor museum with traditional heritage.",
                    "rating": 4.8,
                },
                {
                    "name": "Naggar Castle Art Gallery",
                    "category": "Art & History",
                    "description": "Historic wooden castle gallery.",
                    "rating": 4.7,
                },
            ],
        }
        res = reoptimization_node(state)
        proposed = res["proposed_itinerary"]
        diff = res["diff_summary"]

        self.assertIsNotNone(proposed)
        self.assertIsNotNone(diff)
        self.assertGreater(diff["changes_count"], 0)

        # Day 2 activities should have been replaced with indoor alternatives
        day_2_acts = proposed["days"][1]["activities"]
        act_names = [a["name"] for a in day_2_acts]
        self.assertIn("Museum of Himachal Culture & Folk Art", act_names)

        # Original itinerary in state should remain intact
        orig_day_2 = self.sample_manali_itinerary["days"][1]["activities"]
        self.assertEqual(orig_day_2[0]["name"], "Solang Valley Outdoor Adventure & Paragliding")


class TestTripPulseService(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()

        unique_id = uuid.uuid4().hex[:8]
        self.user_email = f"pulse_{unique_id}@example.com"
        self.user = User(email=self.user_email, hashed_password="pw", name="Pulse Tester")
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

        # Create test trip
        sample_plan = {
            "destination": "Manali",
            "budget": 35000,
            "currency": "INR",
            "days": [
                {
                    "day": 1,
                    "activities": [{"name": "Mall Road", "category": "Leisure"}],
                },
                {
                    "day": 2,
                    "activities": [
                        {"name": "Solang Valley Trek", "category": "Adventure & Outdoors"}
                    ],
                },
            ],
        }
        self.trip = Trip(
            user_id=self.user.id,
            destination="Manali",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 4),
            budget=35000,
            travelers=2,
            preferences={"itinerary": sample_plan, "currency": "INR"},
        )
        self.db.add(self.trip)
        self.db.commit()
        self.db.refresh(self.trip)

    def tearDown(self):
        self.db.query(TripReoptimization).filter(TripReoptimization.trip_id == self.trip.id).delete()
        self.db.query(TripAlert).filter(TripAlert.trip_id == self.trip.id).delete()
        self.db.query(Trip).filter(Trip.id == self.trip.id).delete()
        self.db.query(User).filter(User.id == self.user.id).delete()
        self.db.commit()
        self.db.close()

    def test_simulate_disruption_and_rollback_flow(self):
        # 1. Simulate heavy rainfall on Day 2
        pulse = simulate_disruption(
            self.db,
            trip_id=self.trip.id,
            user_id=self.user.id,
            simulation_type="heavy_rain",
            affected_day=2,
            severity="red",
        )
        self.assertLess(pulse["health_score"], 100)
        self.assertTrue(any(a["is_simulated"] for a in pulse["alerts"]))
        self.assertIsNotNone(pulse["pending_proposal"])

        proposal_id = pulse["pending_proposal"]["id"]

        # 2. Verify original itinerary is NOT modified yet (requires explicit approval)
        trip_db = self.db.get(Trip, self.trip.id)
        day_2_acts = trip_db.itinerary["days"][1]["activities"]
        self.assertEqual(day_2_acts[0]["name"], "Solang Valley Trek")

        # 3. Approve changes
        apply_res = apply_reoptimization(
            self.db,
            trip_id=self.trip.id,
            reopt_id=proposal_id,
            user_id=self.user.id,
        )
        self.assertEqual(apply_res["status"], "success")

        # 4. Verify itinerary updated in database
        self.db.refresh(trip_db)
        updated_acts = trip_db.itinerary["days"][1]["activities"]
        self.assertNotEqual(updated_acts[0]["name"], "Solang Valley Trek")
        self.assertTrue(updated_acts[0].get("is_reoptimized"))

        # 5. Rollback to original itinerary
        rollback_res = rollback_reoptimization(
            self.db,
            trip_id=self.trip.id,
            reopt_id=proposal_id,
            user_id=self.user.id,
        )
        self.assertEqual(rollback_res["status"], "success")

        # 6. Verify itinerary restored back to baseline
        self.db.refresh(trip_db)
        restored_acts = trip_db.itinerary["days"][1]["activities"]
        self.assertEqual(restored_acts[0]["name"], "Solang Valley Trek")


if __name__ == "__main__":
    unittest.main()
