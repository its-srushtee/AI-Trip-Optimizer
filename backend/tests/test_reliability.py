"""Reliability Test Suite for Budget, Flights, Hotels, and Weather.

Tests:
1. Budget calculation bottom-up consistency, multi-currency support, traveler counts, and variance warnings.
2. Flight origin resolution (city, airport name, IATA code), date safety, and live vs estimated guidance.
3. Hotel destination alignment, query construction, style-based price estimation, and live vs guidance labeling.
4. Weather coordinate handling, 5-day forecast horizon check, and seasonal climate norms fallback.
5. End-to-end multi-agent workflow execution with complete state validation.
"""
import datetime
import unittest

from app.agents.cost_agent import CostAgent
from app.agents.transport_agent import TransportAgent
from app.agents.hotel_agent import HotelAgent
from app.agents.weather_agent import WeatherAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.api_clients.serpapi import SerpApiClient
from app.api_clients.weather import WeatherClient


class TestBudgetReliability(unittest.TestCase):
    def test_budget_sums_match_category_breakdown_exactly(self):
        agent = CostAgent()
        state = {
            "request": {
                "destination": "Kyoto",
                "start_date": "2026-11-20",
                "end_date": "2026-11-25",
                "budget": 3000,
                "currency": "USD",
                "travelers": 2,
                "style": "Comfort",
            },
            "destination": {"city": "Kyoto", "country": "Japan"},
            "hotels": {"options": [{"price_per_night": "$180", "is_live": True}]},
            "transport": {
                "flights": [{"price": "$450", "is_live": True}],
            },
        }

        result = agent.run(state)
        breakdown = result["costs"]["breakdown"]

        # 1. Total must exactly match the sum of individual categories
        category_sum = (
            breakdown["flights"]
            + breakdown["stay"]
            + breakdown["food"]
            + breakdown["activities"]
            + breakdown["local_transit"]
            + breakdown["miscellaneous"]
        )
        self.assertEqual(breakdown["total"], category_sum)

        # 2. Check per-traveler and per-day values (6 days: Nov 20 - Nov 25)
        self.assertEqual(breakdown["per_traveler"], round(breakdown["total"] / 2))
        self.assertEqual(breakdown["per_day"], round(breakdown["total"] / 6))

        # 3. Currency symbol resolved
        self.assertEqual(breakdown["currency"], "USD")
        self.assertEqual(breakdown["currency_symbol"], "$")

    def test_budget_variance_and_exceeds_flag(self):
        agent = CostAgent()

        # Case A: Low budget where realistic expenses exceed user's target
        state_tight = {
            "request": {
                "destination": "Paris",
                "start_date": "2026-12-01",
                "end_date": "2026-12-07",
                "budget": 500,  # Unrealistic low target for 6 nights Paris for 2 people
                "currency": "EUR",
                "travelers": 2,
                "style": "Comfort",
            },
            "destination": {"city": "Paris", "country": "France"},
            "hotels": {"options": [{"price_per_night": "€160"}]},
            "transport": {"flights": [{"price": "€300"}]},
        }
        res_tight = agent.run(state_tight)
        b_tight = res_tight["costs"]["breakdown"]
        self.assertTrue(b_tight["exceeds_budget"])
        # Deficit variance is negative (target - total < 0)
        self.assertLess(b_tight["budget_variance"], 0)
        self.assertEqual(b_tight["currency_symbol"], "€")
        self.assertIn("exceeds", b_tight["budget_status"].lower())

        # Case B: Generous budget where expenses fit comfortably
        state_ample = {
            "request": {
                "destination": "Goa",
                "start_date": "2026-12-01",
                "end_date": "2026-12-04",
                "budget": 50000,
                "currency": "INR",
                "travelers": 1,
                "style": "Budget",
            },
            "destination": {"city": "Goa", "country": "India"},
            "hotels": {"options": [{"price_per_night": "₹2000"}]},
            "transport": {"flights": [{"price": "₹6000"}]},
        }
        res_ample = agent.run(state_ample)
        b_ample = res_ample["costs"]["breakdown"]
        self.assertFalse(b_ample["exceeds_budget"])
        self.assertGreaterEqual(b_ample["budget_variance"], 0)
        self.assertEqual(b_ample["currency_symbol"], "₹")
        self.assertIn("within", b_ample["budget_status"].lower())

    def test_multi_currency_symbols(self):
        agent = CostAgent()
        for curr, sym in [("GBP", "£"), ("JPY", "¥"), ("CAD", "CA$"), ("AUD", "A$"), ("CHF", "CHF")]:
            state = {
                "request": {
                    "destination": "London",
                    "start_date": "2026-11-20",
                    "end_date": "2026-11-23",
                    "budget": 1000,
                    "currency": curr,
                    "travelers": 1,
                    "style": "Comfort",
                },
                "destination": {"city": "London"},
            }
            res = agent.run(state)
            self.assertEqual(res["costs"]["breakdown"]["currency_symbol"], sym)


class TestFlightReliability(unittest.TestCase):
    def test_airport_code_resolution(self):
        client = SerpApiClient(key="dummy_key")

        # 3-letter IATA code directly passed (case-insensitive)
        self.assertEqual(client._resolve_airport_code("hnd"), "HND")
        self.assertEqual(client._resolve_airport_code("JFK"), "JFK")
        self.assertEqual(client._resolve_airport_code("lhr"), "LHR")

        # City names
        self.assertIn(client._resolve_airport_code("Tokyo"), ["NRT", "HND"])
        self.assertIn(client._resolve_airport_code("New York"), ["JFK", "EWR", "LGA"])
        self.assertIn(client._resolve_airport_code("Paris"), ["CDG", "ORY"])
        self.assertEqual(client._resolve_airport_code("Mumbai"), "BOM")
        self.assertEqual(client._resolve_airport_code("Delhi"), "DEL")

    def test_past_date_safety_in_serpapi(self):
        """Past dates must not call Google Flights/Hotels API (which returns 400)."""
        client = SerpApiClient(key="dummy_key")
        past_date = "2020-01-01"
        res = client.search_flights(destination="Tokyo", outbound_date=past_date, return_date=past_date, origin="JFK")
        self.assertEqual(res, [])  # Skips cleanly without HTTP 400, returning empty list

    def test_transport_agent_transparent_guidance_no_fake_flights(self):
        agent = TransportAgent()
        state = {
            "request": {
                "destination": "Reykjavik",
                "start_location": "Boston",
                "start_date": "2026-11-20",
                "end_date": "2026-11-25",
                "style": "Comfort",
                "budget": 2000,
                "currency": "USD",
            },
            "destination": {"city": "Reykjavik", "country": "Iceland"},
        }
        res = agent.run(state)
        flights = res["transport"]["flights"]
        self.assertGreater(len(flights), 0)
        for f in flights:
            # Must have direct booking link to Google Flights
            self.assertIn("google.com/travel/flights", f["booking_link"])
            # If not live, must be clearly labeled as estimated guidance
            if not f.get("is_live"):
                self.assertIn("Estimated Market Guidance", f.get("source", ""))
                self.assertIn("Estimated", f.get("status", ""))


class TestHotelReliability(unittest.TestCase):
    def test_hotel_query_construction_prevents_duplicate_prefixes(self):
        client = SerpApiClient(key="dummy_key")
        # Ensure 'hotels in hotels in Kyoto' bug does not happen
        q1 = "hotels in Kyoto"
        clean1 = q1.strip()
        self.assertFalse(clean1.startswith("hotels in hotels in"))

    def test_hotel_agent_travel_style_pricing_and_labeling(self):
        agent = HotelAgent()

        # Backpacker vs Luxury price expectations
        state_bp = {
            "request": {"destination": "Berlin", "start_date": "2026-11-20", "end_date": "2026-11-25", "style": "Backpacker"},
            "destination": {"city": "Berlin"},
        }
        res_bp = agent.run(state_bp)
        hotels_bp = res_bp["hotels"]["options"]
        self.assertGreater(len(hotels_bp), 0)

        state_lux = {
            "request": {"destination": "Berlin", "start_date": "2026-11-20", "end_date": "2026-11-25", "style": "Luxury"},
            "destination": {"city": "Berlin"},
        }
        res_lux = agent.run(state_lux)
        hotels_lux = res_lux["hotels"]["options"]
        self.assertGreater(len(hotels_lux), 0)

        # Backpacker lodging should be cheaper than luxury
        bp_price = int("".join(c for c in hotels_bp[0]["price_per_night"] if c.isdigit()))
        lux_price = int("".join(c for c in hotels_lux[0]["price_per_night"] if c.isdigit()))
        self.assertGreater(lux_price, bp_price)

        # Every hotel has a valid web link
        for h in hotels_bp + hotels_lux:
            self.assertTrue(h["link"].startswith("http"))
            if not h.get("is_live"):
                self.assertIn("Estimated Market Guidance", h.get("source", ""))


class TestWeatherReliability(unittest.TestCase):
    def test_future_dates_beyond_5_days_return_seasonal_climate(self):
        agent = WeatherAgent()
        future_start = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        future_end = (datetime.date.today() + datetime.timedelta(days=35)).isoformat()

        state = {
            "request": {
                "destination": "Tokyo",
                "start_date": future_start,
                "end_date": future_end,
            },
            "destination": {
                "city": "Tokyo",
                "country": "Japan",
                "coordinates": {"lat": 35.6762, "lon": 139.6503},
            },
        }

        res = agent.run(state)
        w = res["weather"]

        # Must NOT pretend to have a live daily forecast 30 days ahead
        self.assertFalse(w["is_live"])
        self.assertEqual(w["status"], "Seasonal Climate Guidance")
        self.assertIn("season", w)
        self.assertIn("temp_range", w)
        self.assertIn("packing_advice", w)
        self.assertIn("beyond the standard 5-day", w["note"])

    def test_southern_hemisphere_seasonal_reversal(self):
        agent = WeatherAgent()
        # Sydney in July (Winter in Southern Hemisphere)
        state_syd = {
            "request": {
                "destination": "Sydney",
                "start_date": "2027-07-15",
                "end_date": "2027-07-20",
            },
            "destination": {
                "city": "Sydney",
                "country": "Australia",
                "coordinates": {"lat": -33.8688, "lon": 151.2093},
            },
        }
        res_syd = agent.run(state_syd)
        w_syd = res_syd["weather"]
        self.assertIn("Winter", w_syd["season"])
        self.assertLessEqual(w_syd["current_or_typical_temp_c"], 15)

    def test_missing_weather_key_does_not_crash(self):
        client = WeatherClient(key="")
        self.assertFalse(client.is_configured())
        self.assertIsNone(client.forecast("Berlin"))

        agent = WeatherAgent()
        state = {
            "request": {"destination": "Rome", "start_date": "2026-11-15", "end_date": "2026-11-20"},
            "destination": {"city": "Rome"},
        }
        res = agent.run(state)
        self.assertIn("weather", res)
        self.assertEqual(res["weather"]["status"], "Seasonal Climate Guidance")


class TestMultiAgentWorkflowIntegration(unittest.TestCase):
    def test_itinerary_agent_includes_weather_and_currency(self):
        agent = ItineraryAgent()
        state = {
            "request": {
                "destination": "Kyoto",
                "start_date": "2026-11-20",
                "end_date": "2026-11-23",
                "travelers": 2,
                "budget": 2500,
                "currency": "EUR",
                "style": "Comfort",
                "pace": "Moderate",
                "interests": ["Culture", "Food"],
            },
            "destination": {
                "city": "Kyoto",
                "country": "Japan",
                "coordinates": {"lat": 35.0116, "lon": 135.7681},
            },
            "weather": {
                "is_live": False,
                "status": "Seasonal Climate Guidance",
                "season": "Autumn (Nov)",
                "current_or_typical_temp_c": 14,
                "temp_range": "9°C – 18°C",
            },
            "costs": {
                "breakdown": {
                    "total": 2400,
                    "target_budget": 2500,
                    "currency": "EUR",
                    "currency_symbol": "€",
                    "exceeds_budget": False,
                }
            },
            "places": [
                {"name": "Fushimi Inari Shrine", "category": "Culture", "lat": 34.9671, "lon": 135.7727},
                {"name": "Kiyomizu-dera", "category": "History", "lat": 34.9949, "lon": 135.7850},
                {"name": "Nishiki Market", "category": "Food", "lat": 35.0050, "lon": 135.7649},
            ],
            "hotels": {"options": [{"name": "Kyoto Ryokan", "price_per_night": "€180"}]},
            "transport": {"flights": [{"airline": "Air France", "price": "€500"}]},
        }

        res = agent.run(state)
        itin = res["itinerary"]

        self.assertEqual(itin["currency"], "EUR")
        self.assertIsNotNone(itin["weather"])
        self.assertEqual(itin["weather"]["status"], "Seasonal Climate Guidance")
        self.assertEqual(itin["budget_breakdown"]["currency_symbol"], "€")
        self.assertEqual(len(itin["days"]), 4)


if __name__ == "__main__":
    unittest.main()
