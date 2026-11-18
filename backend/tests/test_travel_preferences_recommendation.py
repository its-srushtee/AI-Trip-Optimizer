"""Verification tests for Travel Preferences and Recommendations."""
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.api.auth import router as auth_router
from app.api.destinations import router as destinations_router
from app.core.deps import get_db
from app.services.destination_service import seed_destinations, recommend_destinations


class TestTravelPreferencesAndRecommendations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        cls.app = FastAPI()
        cls.app.include_router(auth_router)
        cls.app.include_router(destinations_router)
        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(cls.app)

        with cls.TestingSessionLocal() as db:
            seed_destinations(db)

    def test_signup_with_preferences(self):
        signup_data = {
            "name": "Jane Explorer",
            "email": "jane.explorer@example.com",
            "password": "securepassword123",
            "preferences": {
                "style": "Backpacker",
                "pace": "Fast-paced",
                "interests": ["nature", "adventure"],
                "food": "Vegetarian",
                "accommodation": "Hostel",
            },
        }
        res = self.client.post("/auth/signup", json=signup_data)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["name"], "Jane Explorer")
        self.assertEqual(data["user"]["preferences"]["style"], "Backpacker")
        self.assertIn("adventure", data["user"]["preferences"]["interests"])

    def test_beach_preferences_rank_beach_destinations_first(self):
        with self.TestingSessionLocal() as db:
            recs = recommend_destinations(
                db,
                interests=["beaches", "relaxation"],
                style="Comfort",
                pace="Relaxed",
            )
            self.assertTrue(len(recs) > 0)
            top_names = [r["name"] for r in recs[:3]]
            beach_destinations = {"Goa", "Bali", "Maldives", "Kerala"}
            self.assertTrue(any(name in beach_destinations for name in top_names))
            top_rec = recs[0]
            self.assertTrue(top_rec["match_score"] >= 90)
            self.assertTrue(len(top_rec["match_reasons"]) > 0)

    def test_adventure_preferences_rank_mountain_adventure_first(self):
        with self.TestingSessionLocal() as db:
            recs = recommend_destinations(
                db,
                interests=["nature", "adventure"],
                style="Backpacker",
                pace="Fast-paced",
            )
            self.assertTrue(len(recs) > 0)
            top_names = [r["name"] for r in recs[:3]]
            mountain_destinations = {"Manali", "Swiss Alps", "Banff", "Queenstown"}
            self.assertTrue(any(name in mountain_destinations for name in top_names))


if __name__ == "__main__":
    unittest.main()
