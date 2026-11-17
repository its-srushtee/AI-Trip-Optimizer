"""Tests for strict budget-aware trip generation and dynamic budget allocation."""
import unittest
from datetime import date
from unittest.mock import patch

from app.agents.cost_agent import CostAgent, is_domestic_trip
from app.agents.hotel_agent import HotelAgent
from app.agents.transport_agent import TransportAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.workflows.trip_graph import run_workflow


class TestBudgetAwareness(unittest.TestCase):
    def test_domestic_trip_detection(self):
        self.assertTrue(is_domestic_trip("Mumbai", "Goa", "INR"))
        self.assertTrue(is_domestic_trip("Delhi", "Manali", "INR"))
        self.assertTrue(is_domestic_trip("Bangalore", "Jaipur", "INR"))
        self.assertFalse(is_domestic_trip("Mumbai", "Paris", "INR"))
        self.assertFalse(is_domestic_trip("Delhi", "Tokyo", "INR"))

    def test_pre_allocation_shares_50k_2_travelers(self):
        agent = CostAgent()
        state = {
            "request": {
                "destination": "Goa",
                "origin": "Mumbai",
                "start_date": "2026-11-20",
                "end_date": "2026-11-24",  # 4 nights, 5 days
                "budget": 50000,
                "currency": "INR",
                "travelers": 2,
                "style": "Comfort",
                "interests": ["nature", "food"],
            }
        }
        res = agent.pre_allocate(state)
        alloc = res["budget_allocation"]

        self.assertEqual(alloc["target_budget"], 50000)
        self.assertEqual(alloc["currency"], "INR")
        self.assertEqual(alloc["travelers"], 2)
        self.assertEqual(alloc["nights"], 4)
        self.assertEqual(alloc["rooms_needed"], 1)

        # Budget should sum to ~50,000
        sum_targets = (
            alloc["transport_target"]
            + alloc["stay_target"]
            + alloc["food_target"]
            + alloc["act_target"]
            + alloc["local_target"]
            + alloc["buf_target"]
        )
        self.assertEqual(sum_targets, 50000)

        # Nightly room target should be realistic
        self.assertTrue(2000 <= alloc["nightly_room_target"] <= 5500)
        # Daily food per person should be realistic
        self.assertTrue(500 <= alloc["daily_food_per_person"] <= 1800)

    def test_pre_allocation_4_travelers_needs_2_rooms(self):
        agent = CostAgent()
        state = {
            "request": {
                "destination": "Goa",
                "origin": "Mumbai",
                "start_date": "2026-11-20",
                "end_date": "2026-11-24",
                "budget": 50000,
                "currency": "INR",
                "travelers": 4,
                "style": "Budget",
                "interests": ["beaches"],
            }
        }
        res = agent.pre_allocate(state)
        alloc = res["budget_allocation"]
        self.assertEqual(alloc["rooms_needed"], 2)

    def test_budget_50k_2_travelers_fits_within_budget(self):
        """A ₹50,000 domestic trip for 2 travelers must fit within budget (NOT ₹2,02,276!)."""
        req_state = {
            "request": {
                "destination": "Goa",
                "origin": "Mumbai",
                "start_date": "2026-11-20",
                "end_date": "2026-11-24",  # 4 nights
                "budget": 50000,
                "currency": "INR",
                "travelers": 2,
                "style": "Comfort",
                "interests": ["beaches", "food"],
            },
            "destination": None,
            "hotels": None,
            "weather": None,
            "transport": None,
            "costs": None,
            "itinerary": None,
        }

        itinerary = run_workflow(req_state)
        self.assertIsNotNone(itinerary)
        bb = itinerary["budget_breakdown"]

        # Crucial assertion: Total must be strictly within or very close to ₹50,000 budget
        self.assertLessEqual(bb["total"], 50000)
        self.assertGreaterEqual(bb["total"], 25000)
        self.assertFalse(bb["exceeds_budget"])
        self.assertTrue(bb["feasibility"]["is_balanced"])

    def test_international_destination_does_not_generate_trains(self):
        """Bangalore to Berlin is international: no trains must be returned, mode must be Flight."""
        from app.api_clients.railcore import railcore_client
        trains = railcore_client.search_trains("Banglore", "Berlin", "2026-11-21", "INR")
        self.assertEqual(len(trains), 0, "No Indian Railway trains should be returned for Berlin")

        from app.agents.cost_agent import is_domestic_trip
        self.assertFalse(is_domestic_trip("Banglore", "Berlin", "INR"))

        from app.agents.transport_agent import TransportAgent
        agent = TransportAgent()
        res = agent.run({
            "request": {
                "destination": "Berlin",
                "origin": "Banglore",
                "start_date": "2026-11-21",
                "end_date": "2026-11-25",
                "currency": "INR",
                "travelers": 2,
            },
            "budget_allocation": {"is_domestic": False},
        })
        t = res.get("transport", {})
        self.assertEqual(t.get("recommended_mode"), "Flight")
        self.assertEqual(len(t.get("trains", [])), 0)

    def test_budget_20k_2_travelers(self):
        """A ₹20,000 budget for 2 travelers must prioritize economical choices and fit."""
        req_state = {
            "request": {
                "destination": "Goa",
                "origin": "Mumbai",
                "start_date": "2026-11-20",
                "end_date": "2026-11-23",  # 3 nights
                "budget": 20000,
                "currency": "INR",
                "travelers": 2,
                "style": "Backpacker",
                "interests": ["nature"],
            },
            "destination": None,
            "hotels": None,
            "weather": None,
            "transport": None,
            "costs": None,
            "itinerary": None,
        }
        itinerary = run_workflow(req_state)
        bb = itinerary["budget_breakdown"]
        self.assertLessEqual(bb["total"], 20000)
        self.assertFalse(bb["exceeds_budget"])

    def test_budget_100k_luxury_scales_up(self):
        """A ₹1,00,000 budget allows upscale hotels, flights, and activities."""
        req_state = {
            "request": {
                "destination": "Goa",
                "origin": "Mumbai",
                "start_date": "2026-11-20",
                "end_date": "2026-11-24",
                "budget": 100000,
                "currency": "INR",
                "travelers": 2,
                "style": "Luxury",
                "interests": ["food", "culture"],
            },
            "destination": None,
            "hotels": None,
            "weather": None,
            "transport": None,
            "costs": None,
            "itinerary": None,
        }
        itinerary = run_workflow(req_state)
        bb = itinerary["budget_breakdown"]
        self.assertLessEqual(bb["total"], 100000)
        self.assertGreater(bb["total"], 70000)

    def test_unrealistic_budget_explains_and_suggests_alternatives(self):
        """Paris for 2 travelers with ₹20,000 is genuinely unrealistic and must be flagged transparently."""
        req_state = {
            "request": {
                "destination": "Paris",
                "origin": "Mumbai",
                "start_date": "2026-11-20",
                "end_date": "2026-11-24",
                "budget": 20000,
                "currency": "INR",
                "travelers": 2,
                "style": "Comfort",
                "interests": ["culture", "food"],
            },
            "destination": None,
            "hotels": None,
            "weather": None,
            "transport": None,
            "costs": None,
            "itinerary": None,
        }
        itinerary = run_workflow(req_state)
        bb = itinerary["budget_breakdown"]
        self.assertTrue(bb["exceeds_budget"])
        feas = bb["feasibility"]
        self.assertFalse(feas["is_realistic"])
        self.assertTrue(len(feas["unrealistic_reason"]) > 10)
        self.assertTrue(len(feas["suggested_alternatives"]) >= 2)
        self.assertIsNotNone(feas["suggested_revised_budget"])


if __name__ == "__main__":
    unittest.main()

