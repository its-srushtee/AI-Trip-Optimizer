"""Comprehensive Test Suite for Currency Conversion and Handling across the AI Trip Optimizer."""
import unittest

from app.agents.cost_agent import CostAgent
from app.agents.hotel_agent import HotelAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.transport_agent import TransportAgent
from app.api_clients.currency import (
    CURRENCY_SYMBOLS,
    FALLBACK_RATES_FROM_USD,
    FrankfurterClient,
    currency_client,
)
from app.schemas.trip import TripCreate, TripOut, TripUpdate


class TestFrankfurterClient(unittest.TestCase):
    def setUp(self):
        self.client = FrankfurterClient()

    def test_same_currency_conversion_is_one_to_one(self):
        res = self.client.convert(50000, "INR", "INR")
        self.assertEqual(res["converted_amount"], 50000)
        self.assertEqual(res["rate"], 1.0)
        self.assertEqual(res["from_currency"], "INR")
        self.assertEqual(res["to_currency"], "INR")

    def test_usd_to_inr_conversion_math(self):
        # 100 USD converts using live or fallback rate (~83.5-95 INR/USD)
        res = self.client.convert(100, "USD", "INR")
        self.assertGreaterEqual(res["converted_amount"], 8000)
        self.assertLessEqual(res["converted_amount"], 10500)
        self.assertEqual(res["to_currency"], "INR")

    def test_inr_to_usd_conversion_math(self):
        # 83500 INR converts to approx 800-1100 USD depending on live rate
        res = self.client.convert(83500, "INR", "USD")
        self.assertGreaterEqual(res["converted_amount"], 800)
        self.assertLessEqual(res["converted_amount"], 1100)

    def test_usd_to_eur_and_gbp_conversion(self):
        eur_res = self.client.convert(100, "USD", "EUR")
        gbp_res = self.client.convert(100, "USD", "GBP")
        self.assertGreaterEqual(eur_res["converted_amount"], 80)
        self.assertLessEqual(eur_res["converted_amount"], 105)
        self.assertGreaterEqual(gbp_res["converted_amount"], 65)
        self.assertLessEqual(gbp_res["converted_amount"], 95)

    def test_cross_currency_eur_to_inr(self):
        # 100 EUR converts to approx 8500-11500 INR
        res = self.client.convert(100, "EUR", "INR")
        self.assertGreaterEqual(res["converted_amount"], 8500)
        self.assertLessEqual(res["converted_amount"], 11500)

    def test_caching_mechanism(self):
        rates1, _ = self.client.get_rates("USD")
        rates2, is_cached = self.client.get_rates("USD")
        self.assertEqual(rates1, rates2)

    def test_parse_and_convert_various_price_formats(self):
        # Dollar string
        d_res = self.client.parse_and_convert("$500", "INR")
        self.assertEqual(d_res["original_currency"], "USD")
        self.assertEqual(d_res["original_amount"], 500)
        self.assertIn("₹", d_res["formatted"])
        self.assertGreater(d_res["converted_amount"], 35000)

        # Euro string
        e_res = self.client.parse_and_convert("€450", "USD")
        self.assertEqual(e_res["original_currency"], "EUR")
        self.assertIn("$", e_res["formatted"])

        # Rupee string
        inr_res = self.client.parse_and_convert("₹50,000", "USD")
        self.assertEqual(inr_res["original_currency"], "INR")
        self.assertIn("$", inr_res["formatted"])
        self.assertGreater(inr_res["converted_amount"], 500)


class TestTransportAndHotelCurrencyConversion(unittest.TestCase):
    def test_transport_agent_converts_usd_flights_to_inr(self):
        agent = TransportAgent()
        state = {
            "request": {
                "destination": "Tokyo",
                "origin": "Mumbai",
                "start_date": "2026-11-20",
                "end_date": "2026-11-27",
                "travelers": 1,
                "currency": "INR",
            }
        }
        res = agent.run(state)
        trans = res["transport"]
        self.assertEqual(trans["currency"], "INR")
        self.assertEqual(trans["currency_symbol"], "₹")
        flights = trans["flights"]
        self.assertGreater(len(flights), 0)
        for f in flights:
            self.assertEqual(f["currency"], "INR")
            # Should be in thousands of INR, NOT the USD price!
            self.assertGreater(f["price_amount"], 20000)
            self.assertIn("₹", f["price"])

    def test_hotel_agent_converts_usd_hotels_to_inr(self):
        agent = HotelAgent()
        state = {
            "request": {
                "destination": "Paris",
                "start_date": "2026-11-20",
                "end_date": "2026-11-27",
                "travelers": 2,
                "currency": "INR",
                "style": "Comfort",
                "accommodation": "Hotel",
            }
        }
        res = agent.run(state)
        hotels_data = res["hotels"]
        self.assertEqual(hotels_data["currency"], "INR")
        self.assertEqual(hotels_data["currency_symbol"], "₹")
        options = hotels_data["options"]
        self.assertGreater(len(options), 0)
        for h in options:
            self.assertEqual(h["currency"], "INR")
            # Nightly rate in INR should be thousands, not ~$75
            self.assertGreater(h["price_amount"], 4000)
            self.assertIn("₹", h["price_per_night"])


class TestCostAgentCurrencyConsistency(unittest.TestCase):
    def test_inr_budget_and_cost_consistency(self):
        agent = CostAgent()
        # User entered 50,000 INR budget for 5 days in Manali
        state = {
            "request": {
                "destination": "Manali",
                "start_date": "2026-11-20",
                "end_date": "2026-11-25",
                "budget": 50000,
                "currency": "INR",
                "travelers": 2,
                "style": "Budget",
                "interests": ["nature", "adventure"],
            },
            "hotels": {
                "options": [
                    {"name": "Mountain Lodge", "price_per_night": "₹2,500", "price_amount": 2500, "currency": "INR"}
                ]
            },
            "transport": {
                "flights": [
                    {"airline": "IndiGo", "price": "₹6,500", "price_amount": 6500, "currency": "INR"}
                ]
            },
        }

        res = agent.run(state)
        breakdown = res["costs"]["breakdown"]

        # Check currency fields
        self.assertEqual(breakdown["currency"], "INR")
        self.assertEqual(breakdown["currency_symbol"], "₹")
        self.assertEqual(breakdown["target_budget"], 50000)

        # Mathematical category sum
        total = (
            breakdown["flights"]
            + breakdown["stay"]
            + breakdown["food"]
            + breakdown["activities"]
            + breakdown["local_transit"]
            + breakdown["miscellaneous"]
        )
        self.assertEqual(breakdown["total"], total)

        # Accommodation: 5 nights * 2500 = 12500 INR
        self.assertEqual(breakdown["stay"], 12500)
        # Flights: 2 travelers * 6500 = 13000 INR
        self.assertEqual(breakdown["flights"], 13000)

        # Variance and status are computed in INR
        self.assertEqual(breakdown["budget_variance"], 50000 - total)
        self.assertIn("₹", breakdown["budget_status"])

    def test_eur_budget_consistency(self):
        agent = CostAgent()
        state = {
            "request": {
                "destination": "Rome",
                "start_date": "2026-11-20",
                "end_date": "2026-11-24",
                "budget": 1200,
                "currency": "EUR",
                "travelers": 1,
                "style": "Comfort",
            }
        }
        res = agent.run(state)
        breakdown = res["costs"]["breakdown"]
        self.assertEqual(breakdown["currency"], "EUR")
        self.assertEqual(breakdown["currency_symbol"], "€")
        self.assertEqual(breakdown["target_budget"], 1200)
        # Stay, food, and flights must be in EUR scale
        self.assertLess(breakdown["total"], 2500)
        self.assertGreater(breakdown["total"], 500)


class TestItineraryAgentCurrencyFormatting(unittest.TestCase):
    def test_itinerary_agent_formats_inr_activities_and_days(self):
        agent = ItineraryAgent()
        state = {
            "request": {
                "destination": "Goa",
                "start_date": "2026-11-20",
                "end_date": "2026-11-23",
                "budget": 35000,
                "currency": "INR",
                "travelers": 2,
                "interests": ["beaches", "food"],
                "style": "Comfort",
                "pace": "Moderate",
            },
            "destination": {
                "places_to_visit": [
                    {"name": "Calangute Beach", "category": "Beaches", "location": "North Goa"},
                    {"name": "Fort Aguada", "category": "Heritage & Fort", "location": "Candolim"},
                    {"name": "Anjuna Flea Market", "category": "Shopping", "location": "Anjuna"},
                ]
            },
            "costs": {
                "breakdown": {
                    "flights": 10000,
                    "stay": 12000,
                    "food": 6000,
                    "activities": 3000,
                    "local_transit": 2000,
                    "miscellaneous": 1500,
                    "total": 34500,
                    "currency": "INR",
                    "currency_symbol": "₹",
                    "target_budget": 35000,
                }
            },
        }

        res = agent.run(state)
        itin = res["itinerary"]
        self.assertEqual(itin["currency"], "INR")
        self.assertEqual(itin["currency_symbol"], "₹")
        self.assertIn("INR 35,000", itin["summary"])

        # Verify daily estimates and activities
        for day in itin["days"]:
            self.assertEqual(day["currency"], "INR")
            self.assertEqual(day["currency_symbol"], "₹")
            self.assertEqual(day["estimate_cost"], round(35000 / 4))
            for act in day["activities"]:
                cost = act.get("estimated_cost", "")
                # Should not have stray bare $ sign if formatted
                if "Free" not in cost and "Included" not in cost:
                    self.assertIn("₹", cost)


class TestTripModelAndSchemasCurrencyPreservation(unittest.TestCase):
    def test_trip_create_and_out_preserves_currency(self):
        # 1. Create with top-level currency
        create_payload = {
            "destination": "Jaipur",
            "start_date": "2026-11-20",
            "end_date": "2026-11-25",
            "budget": 40000,
            "travelers": 2,
            "interests": ["culture", "history"],
            "currency": "INR",
            "preferences": {"style": "Comfort"},
        }
        tc = TripCreate(**create_payload)
        self.assertEqual(tc.currency, "INR")

        # 2. TripOut correctly reads currency from dict or preferences
        out_dict = {
            "id": 1,
            "destination": "Jaipur",
            "start_date": "2026-11-20",
            "end_date": "2026-11-25",
            "budget": 40000,
            "travelers": 2,
            "interests": ["culture"],
            "status": "Planning",
            "currency": "INR",
            "preferences": {"currency": "INR"},
            "created_at": "2026-11-13T09:00:00Z",
        }
        tout = TripOut(**out_dict)
        self.assertEqual(tout.currency, "INR")

    def test_trip_update_allows_currency_change(self):
        tu = TripUpdate(currency="EUR", budget=1500)
        self.assertEqual(tu.currency, "EUR")
        self.assertEqual(tu.budget, 1500)


if __name__ == "__main__":
    unittest.main()

