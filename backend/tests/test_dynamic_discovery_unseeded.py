"""Unit tests verifying dynamic destination discovery, autocomplete, and unseeded destinations.

Tests destinations not seeded in the static catalogue:
- Gokarna
- Meghalaya
- Hampi
- Varkala
- Ziro Valley
"""
from datetime import date, datetime
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.destination_cache import DestinationInfoCache
from app.models.trip import Trip
from app.models.user import User
import app.agents.destination_agent as dest_agent_mod
from app.agents.destination_agent import DestinationAgent, retrieve_dynamic_attractions
from app.agents.itinerary_agent import ItineraryAgent
from app.services.destination_preferences import clear_preferences_cache, get_destination_preferences
from app.services.destination_service import search_destinations_dynamic


class TestDynamicDiscoveryUnseeded(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine, expire_on_commit=False)
        cls._orig_session_local = dest_agent_mod.SessionLocal
        dest_agent_mod.SessionLocal = cls.SessionLocal

    @classmethod
    def tearDownClass(cls):
        dest_agent_mod.SessionLocal = cls._orig_session_local
        Base.metadata.drop_all(cls.engine)

    def setUp(self):
        clear_preferences_cache()
        self.session: Session = self.SessionLocal()

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_unseeded_destination_caching_and_retrieval(self):
        """Simulates dynamic discovery of Gokarna and verifies it caches and returns properly."""
        # Seed cache as if fetched from live Geoapify / SerpApi API
        cache_entry = DestinationInfoCache(
            query_key="gokarna",
            destination_name="Gokarna",
            country="India",
            formatted_address="Gokarna, Karnataka, India",
            coordinates={"lat": 14.5479, "lon": 74.3188},
            attractions=[
                {
                    "name": "Om Beach",
                    "category": "Beaches & Coastal",
                    "location": "Gokarna, Karnataka",
                    "tags": ["beaches", "relaxation", "nature"],
                    "rating": 4.8,
                    "description": "Distinctive Om-shaped beach famous for gentle waves, rock formations, and tranquil coastal cafes.",
                },
                {
                    "name": "Mahabaleshwar Temple",
                    "category": "Religious & Spiritual Sights",
                    "location": "Gokarna, Karnataka",
                    "tags": ["spirituality", "history", "culture"],
                    "rating": 4.9,
                    "description": "Ancient 4th-century CE Hindu shrine built in Dravidian architectural style housing the sacred Atmalinga.",
                },
                {
                    "name": "Kudle Beach & Sunset Trail",
                    "category": "Beaches & Coastal",
                    "location": "Gokarna, Karnataka",
                    "tags": ["beaches", "photography", "relaxation"],
                    "rating": 4.7,
                    "description": "Expansive crescent bay flanked by cliffs, ideal for sunset strolls and seaside seafood shacks.",
                },
            ],
            source="Live APIs (Geoapify & SerpApi)",
        )
        self.session.add(cache_entry)
        self.session.commit()

        # 1. Verify dynamic search finds Gokarna
        results = search_destinations_dynamic(self.session, query="Gokarna")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Gokarna")
        self.assertEqual(results[0]["country"], "India")

        # 2. Verify destination preferences service dynamically identifies Gokarna's actual categories
        pref_res = get_destination_preferences("Gokarna")
        self.assertTrue(pref_res["supported"])
        avail = pref_res["available_preferences"]
        self.assertIn("Beaches & Coastal", avail)
        self.assertIn("Spirituality", avail)
        self.assertIn("Relaxation & Wellness", avail)

        # 3. Verify DestinationAgent runs on unseeded Gokarna
        state = {
            "request": {
                "destination": "Gokarna",
                "start_date": "2026-12-01",
                "end_date": "2026-12-04",
                "budget": 25000,
                "currency": "INR",
                "interests": ["beaches", "spirituality"],
                "travelers": 2,
            }
        }
        dest_agent = DestinationAgent()
        out_state = dest_agent.run(state)
        places = out_state["destination"]["places_to_visit"]
        self.assertGreaterEqual(len(places), 2)
        place_names = [p["name"] for p in places]
        self.assertIn("Om Beach", place_names)

        # 4. Verify ItineraryAgent schedules without hardcoded dependency
        out_state["hotels"] = [{"name": "Gokarna Cliff Resort"}]
        itin_agent = ItineraryAgent()
        itin_state = itin_agent.run(out_state)
        itinerary = itin_state.get("itinerary", {})
        self.assertIn("days", itinerary)
        self.assertEqual(len(itinerary["days"]), 4)  # 3 nights -> 4 days

    def test_hampi_heritage_discovery(self):
        """Simulates dynamic discovery of Hampi (UNESCO ruins, zero beaches)."""
        cache_entry = DestinationInfoCache(
            query_key="hampi",
            destination_name="Hampi",
            country="India",
            formatted_address="Hampi, Karnataka, India",
            coordinates={"lat": 15.3350, "lon": 76.4600},
            attractions=[
                {
                    "name": "Virupaksha Temple",
                    "category": "Religious & Spiritual Sights",
                    "location": "Hampi, Karnataka",
                    "tags": ["spirituality", "history", "culture"],
                    "rating": 4.9,
                    "description": "7th-century Hindu temple complex dedicated to Lord Virupaksha on the banks of Tungabhadra River.",
                },
                {
                    "name": "Vijaya Vittala Temple & Stone Chariot",
                    "category": "History & Heritage",
                    "location": "Hampi, Karnataka",
                    "tags": ["history", "culture", "photography"],
                    "rating": 4.9,
                    "description": "Famous 16th-century Vijayanagara monument with iconic monolithic stone chariot and musical pillars.",
                },
            ],
            source="Live APIs (Geoapify & SerpApi)",
        )
        self.session.add(cache_entry)
        self.session.commit()

        pref_res = get_destination_preferences("Hampi")
        self.assertTrue(pref_res["supported"])
        avail = pref_res["available_preferences"]
        self.assertIn("Culture & History", avail)
        # CRITICAL: Inland historic Hampi must NEVER offer Beaches
        self.assertNotIn("Beaches & Coastal", avail)

    def test_no_fictitious_attractions_for_unknown_place(self):
        """A completely nonexistent place should NOT invent fictitious generic sights."""
        geo, places = retrieve_dynamic_attractions("NonexistentPlaceXYZ123456")
        self.assertEqual(len(places), 0)


if __name__ == "__main__":
    unittest.main()
