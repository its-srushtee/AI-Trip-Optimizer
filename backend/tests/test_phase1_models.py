"""Unit tests for Phase 1 Database extensions and models."""
from datetime import date, datetime
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.user import User
from app.models.trip import Trip
from app.models.expense import TripExpense
from app.models.alert import TripAlert, TripMonitoringLog
from app.models.reoptimization import TripReoptimization
from app.models.chat import TripChatMessage


class TestPhase1Models(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # In-memory SQLite with StaticPool for fast, isolated sandbox testing
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine, expire_on_commit=False)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)

    def setUp(self):
        self.session: Session = self.SessionLocal()

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def _create_sample_user_and_trip(self, currency="INR") -> tuple[User, Trip]:
        user = User(
            name="Traveler Alpha",
            email=f"traveler_{datetime.now().timestamp()}@example.com",
            hashed_password="hashed_pw_secret",
            preferences={"currency": currency, "style": "Luxury", "interests": ["food", "nature"]},
        )
        self.session.add(user)
        self.session.flush()

        trip = Trip(
            user_id=user.id,
            destination="Manali",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 5),
            budget=50000,
            travelers=2,
            interests=["nature", "adventure"],
            preferences={"currency": currency},
        )
        self.session.add(trip)
        self.session.flush()
        return user, trip

    def test_trip_expense_creation_and_currency(self):
        user, trip = self._create_sample_user_and_trip("INR")
        self.assertEqual(trip.currency, "INR")

        expense = TripExpense(
            trip_id=trip.id,
            user_id=user.id,
            amount=3500.0,
            currency="INR",
            original_amount=3500.0,
            original_currency="INR",
            exchange_rate=1.0,
            category="Transportation",
            date=date(2026, 12, 1),
            description="Private cab from Chandigarh to Manali",
            payment_method="UPI",
            idempotency_key="tx_cab_001",
        )
        self.session.add(expense)
        self.session.commit()

        # Query back
        saved = self.session.scalar(select(TripExpense).where(TripExpense.id == expense.id))
        self.assertIsNotNone(saved)
        self.assertEqual(saved.amount, 3500.0)
        self.assertEqual(saved.currency, "INR")
        self.assertEqual(saved.category, "Transportation")
        self.assertEqual(saved.idempotency_key, "tx_cab_001")
        self.assertEqual(len(trip.expenses), 1)
        self.assertEqual(trip.expenses[0].id, saved.id)

    def test_trip_alert_and_simulation_fields(self):
        user, trip = self._create_sample_user_and_trip()

        alert = TripAlert(
            trip_id=trip.id,
            alert_type="weather",
            severity="red",
            title="Heavy Rainfall Warning",
            explanation="Solang Valley road blocked due to landslide warning.",
            recommended_action="Reschedule paragliding to Day 4 and visit Museum of Himachal Culture.",
            relevant_date=date(2026, 12, 2),
            is_simulated=True,
            simulation_type="heavy_rainfall",
            is_dismissed=False,
        )
        self.session.add(alert)
        self.session.commit()

        saved = self.session.scalar(select(TripAlert).where(TripAlert.id == alert.id))
        self.assertIsNotNone(saved)
        self.assertTrue(saved.is_simulated)
        self.assertEqual(saved.simulation_type, "heavy_rainfall")
        self.assertEqual(saved.severity, "red")
        self.assertEqual(len(trip.alerts), 1)

    def test_trip_monitoring_log(self):
        user, trip = self._create_sample_user_and_trip()

        log = TripMonitoringLog(
            trip_id=trip.id,
            overall_health=85,
            health_status="yellow",
            weather_status={"temperature": 12, "condition": "rain_showers", "forecast_days": 5},
            budget_status={"allocated": 50000, "spent": 12000, "remaining": 38000, "burn_rate": "normal"},
            disruptions_detected=[{"type": "weather", "level": "moderate", "date": "2026-12-02"}],
            recommendations_summary="Indoor backup activities advised for Day 2 afternoon.",
        )
        self.session.add(log)
        self.session.commit()

        saved = self.session.scalar(select(TripMonitoringLog).where(TripMonitoringLog.id == log.id))
        self.assertIsNotNone(saved)
        self.assertEqual(saved.overall_health, 85)
        self.assertEqual(saved.health_status, "yellow")
        self.assertEqual(len(trip.monitoring_logs), 1)

    def test_trip_reoptimization_versioning_and_diff(self):
        user, trip = self._create_sample_user_and_trip()

        orig_itinerary = {
            "days": [
                {"day": 1, "activities": [{"name": "Solang Valley Trek", "cost": 2000}]}
            ]
        }
        prop_itinerary = {
            "days": [
                {"day": 1, "activities": [{"name": "Museum of Himachal Culture & Art", "cost": 500}]}
            ]
        }
        diff = {
            "replaced": [{"old": "Solang Valley Trek", "new": "Museum of Himachal Culture & Art", "reason": "Heavy rainfall"}]
        }

        reopt = TripReoptimization(
            trip_id=trip.id,
            version=1,
            trigger_reason="heavy_rainfall_simulation",
            original_itinerary=orig_itinerary,
            proposed_itinerary=prop_itinerary,
            diff_summary=diff,
            explanation="Replaced outdoor Solang trek with indoor cultural museum due to heavy rain alert.",
            is_simulated=True,
            status="pending",
        )
        self.session.add(reopt)
        self.session.commit()

        saved = self.session.scalar(select(TripReoptimization).where(TripReoptimization.id == reopt.id))
        self.assertIsNotNone(saved)
        self.assertEqual(saved.version, 1)
        self.assertEqual(saved.status, "pending")
        self.assertEqual(saved.diff_summary["replaced"][0]["new"], "Museum of Himachal Culture & Art")
        self.assertEqual(len(trip.reoptimizations), 1)

    def test_trip_chat_message(self):
        user, trip = self._create_sample_user_and_trip()

        msg = TripChatMessage(
            trip_id=trip.id,
            user_id=user.id,
            role="assistant",
            content="Heavy rain is predicted for Day 2. Would you like me to switch to indoor cafes and museums?",
            action_proposal={"action": "reoptimize_day", "day": 2, "focus": "indoor"},
        )
        self.session.add(msg)
        self.session.commit()

        saved = self.session.scalar(select(TripChatMessage).where(TripChatMessage.id == msg.id))
        self.assertIsNotNone(saved)
        self.assertEqual(saved.role, "assistant")
        self.assertEqual(saved.action_proposal["action"], "reoptimize_day")
        self.assertEqual(len(trip.chat_messages), 1)

    def test_cascade_delete_on_trip(self):
        user, trip = self._create_sample_user_and_trip()
        trip_id = trip.id

        # Add expense, alert, reoptimization, log, chat
        self.session.add(TripExpense(
            trip_id=trip_id, user_id=user.id, amount=100.0, category="Food",
            date=date(2026, 12, 1), description="Lunch",
        ))
        self.session.add(TripAlert(
            trip_id=trip_id, alert_type="budget", title="Budget check", explanation="On track"
        ))
        self.session.commit()

        self.assertEqual(len(trip.expenses), 1)
        self.assertEqual(len(trip.alerts), 1)

        # Delete trip -> cascade delete children
        self.session.delete(trip)
        self.session.commit()

        expenses = self.session.scalars(select(TripExpense).where(TripExpense.trip_id == trip_id)).all()
        alerts = self.session.scalars(select(TripAlert).where(TripAlert.trip_id == trip_id)).all()
        self.assertEqual(len(expenses), 0)
        self.assertEqual(len(alerts), 0)


if __name__ == "__main__":
    unittest.main()
