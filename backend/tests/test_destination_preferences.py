"""Comprehensive verification tests for Dynamic Destination-Based Travel Preferences."""
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.destinations import router as destinations_router
from app.services.destination_preferences import (
    clear_preferences_cache,
    get_destination_preferences,
)
from app.agents.destination_agent import DestinationAgent


class TestDestinationPreferences(unittest.TestCase):
    def setUp(self):
        clear_preferences_cache()

    def test_goa_beach_preferences(self):
        """Goa should prominently offer Beaches & Coastal and Nightlife."""
        res = get_destination_preferences("Goa")
        self.assertTrue(res["supported"])
        prefs = res["available_preferences"]
        self.assertIn("Beaches & Coastal", prefs)
        self.assertIn("Nightlife", prefs)
        self.assertIn("Food & Culinary", prefs)
        self.assertIn("Relaxation & Wellness", prefs)
        self.assertGreaterEqual(res["total_attractions"], 5)

    def test_manali_mountain_preferences(self):
        """Manali (mountain destination) must NOT offer Beaches & Coastal or Nightlife."""
        res = get_destination_preferences("Manali")
        self.assertTrue(res["supported"])
        prefs = res["available_preferences"]
        self.assertIn("Nature", prefs)
        self.assertIn("Adventure", prefs)
        self.assertIn("Photography", prefs)
        # CRITICAL: Mountains must never offer beaches
        self.assertNotIn("Beaches & Coastal", prefs)
        self.assertNotIn("Nightlife", prefs)

    def test_jaipur_heritage_preferences(self):
        """Jaipur (royal historic city) must prioritize Culture & History and Shopping, not Beaches."""
        res = get_destination_preferences("Jaipur")
        self.assertTrue(res["supported"])
        prefs = res["available_preferences"]
        self.assertIn("Culture & History", prefs)
        self.assertIn("Shopping", prefs)
        self.assertIn("Photography", prefs)
        # Landlocked desert city must never offer beaches
        self.assertNotIn("Beaches & Coastal", prefs)

    def test_mumbai_metropolis_preferences(self):
        """Mumbai (coastal hub) should offer Culture, Food, Nightlife, and Coastal experiences."""
        res = get_destination_preferences("Mumbai")
        self.assertTrue(res["supported"])
        prefs = res["available_preferences"]
        self.assertIn("Culture & History", prefs)
        self.assertIn("Food & Culinary", prefs)
        self.assertIn("Nightlife", prefs)
        self.assertIn("Shopping", prefs)
        self.assertIn("Beaches & Coastal", prefs)

    def test_kerala_nature_wellness_preferences(self):
        """Kerala must feature Nature, Relaxation & Wellness, and Beaches."""
        res = get_destination_preferences("Kerala")
        self.assertTrue(res["supported"])
        prefs = res["available_preferences"]
        self.assertIn("Nature", prefs)
        self.assertIn("Relaxation & Wellness", prefs)
        self.assertIn("Beaches & Coastal", prefs)
        self.assertIn("Culture & History", prefs)

    def test_varanasi_spiritual_preferences(self):
        """Varanasi must feature Spirituality and Culture, and exclude Beaches & Nightlife."""
        res = get_destination_preferences("Varanasi")
        self.assertTrue(res["supported"])
        prefs = res["available_preferences"]
        self.assertIn("Spirituality", prefs)
        self.assertIn("Culture & History", prefs)
        self.assertIn("Photography", prefs)
        # Sacred ghats city has no beaches or nightlife
        self.assertNotIn("Beaches & Coastal", prefs)
        self.assertNotIn("Nightlife", prefs)

    def test_invalid_and_not_found_destinations(self):
        """Edge cases: empty destination, whitespace, or invalid destination."""
        empty_res = get_destination_preferences("")
        self.assertFalse(empty_res["supported"])
        self.assertEqual(len(empty_res["available_preferences"]), 0)

        whitespace_res = get_destination_preferences("   ")
        self.assertFalse(whitespace_res["supported"])
        self.assertEqual(len(whitespace_res["available_preferences"]), 0)

        unknown_res = get_destination_preferences("UnknownPlanetX999")
        self.assertFalse(unknown_res["supported"])
        self.assertEqual(len(unknown_res["available_preferences"]), 0)
        self.assertIn("not found", unknown_res["message"].lower())

    def test_caching_performance(self):
        """Subsequent queries for the same destination must be served from cache."""
        res1 = get_destination_preferences("Goa")
        res2 = get_destination_preferences("Goa")
        self.assertIs(res1, res2)

    def test_api_endpoints(self):
        """Tests GET and POST /destinations/preferences FastAPI routes."""
        test_app = FastAPI()
        test_app.include_router(destinations_router)
        client = TestClient(test_app)

        # GET request
        resp_get = client.get("/destinations/preferences?destination=Goa")
        self.assertEqual(resp_get.status_code, 200)
        data_get = resp_get.json()
        self.assertIn("Beaches & Coastal", data_get["available_preferences"])

        # POST request
        resp_post = client.post("/destinations/preferences", json={"destination": "Manali"})
        self.assertEqual(resp_post.status_code, 200)
        data_post = resp_post.json()
        self.assertIn("Nature", data_post["available_preferences"])
        self.assertNotIn("Beaches & Coastal", data_post["available_preferences"])

    def test_destination_agent_filters_unsupported_interests(self):
        """DestinationAgent must filter out unsupported preferences (e.g. beaches in Manali)."""
        agent = DestinationAgent()
        state = {
            "request": {
                "destination": "Manali",
                "interests": ["beaches"],  # Invalid for Manali
            }
        }
        out = agent.run(state)
        dest_data = out.get("destination", {})
        highlights = dest_data.get("highlights", [])
        # Highlights should not mention beaches or coastal sands in Manali
        for h in highlights:
            self.assertNotIn("coastal", h.lower())
            self.assertNotIn("beach", h.lower())


if __name__ == "__main__":
    unittest.main()
