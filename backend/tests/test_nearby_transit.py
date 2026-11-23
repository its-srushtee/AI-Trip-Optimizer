"""Unit tests for Nearby Transit Service and gateway resolution."""
import unittest

from app.services.transit_service import (
    NEARBY_TRANSIT_REGISTRY,
    get_nearby_transit,
    resolve_arrival_transit_hub,
)
from app.api_clients.serpapi import resolve_airport_code
from app.api_clients.railcore import resolve_station_code


class TestNearbyTransit(unittest.TestCase):
    def test_destinations_without_airport_have_gateways(self):
        destinations = [
            ("Hampi", "VDY", "HPT"),
            ("Manali", "KUU", "CDG"),
            ("Rishikesh", "DED", "YNRK"),
            ("Ooty", "CJB", "CBE"),
            ("Munnar", "COK", "ERS"),
            ("Coorg", "CNN", "MYS"),
            ("Gokarna", "GOI", "GOK"),
            ("Lonavala", "PNQ", "LNL"),
            ("Mount Abu", "UDR", "ABR"),
            ("Darjeeling", "IXB", "NJP"),
            ("Pondicherry", "MAA", "PDY"),
            ("Alleppey", "COK", "ALLP"),
        ]
        for dest, expected_airport, expected_station in destinations:
            transit = get_nearby_transit(dest)
            self.assertIsNotNone(transit, f"Expected nearby transit for {dest}")
            self.assertFalse(transit["has_direct_airport"])
            self.assertIn("nearby_airport", transit)
            self.assertIn("nearby_railway", transit)
            self.assertTrue(len(transit["nearby_airport"]["distance"]) > 0)
            self.assertTrue(len(transit["nearby_railway"]["distance"]) > 0)
            self.assertTrue(len(transit["nearby_airport"]["transfer_tip"]) > 0)
            self.assertTrue(len(transit["nearby_railway"]["transfer_tip"]) > 0)

            # Test airport code resolution falls back to nearby airport
            resolved_code = resolve_airport_code(dest)
            self.assertEqual(
                resolved_code,
                expected_airport,
                f"For {dest}, expected airport code {expected_airport}, got {resolved_code}"
            )

            # Test railway station code resolution falls back to nearby station
            station_code = resolve_station_code(dest)
            self.assertEqual(
                station_code,
                expected_station,
                f"For {dest}, expected station code {expected_station}, got {station_code}"
            )

    def test_direct_airport_destinations_return_none_from_registry(self):
        # Direct airport cities should not be in NEARBY_TRANSIT_REGISTRY
        direct_cities = ["Delhi", "Mumbai", "Bengaluru", "Goa", "Paris", "Tokyo"]
        for city in direct_cities:
            transit = get_nearby_transit(city)
            self.assertIsNone(transit, f"{city} is a direct airport city and should not be in non-airport registry")

    def test_resolve_arrival_transit_hub(self):
        code, meta = resolve_arrival_transit_hub("Hampi")
        self.assertEqual(code, "VDY")
        self.assertIsNotNone(meta)
        self.assertEqual(meta["destination_name"], "Hampi")

        code_direct, meta_direct = resolve_arrival_transit_hub("Mumbai")
        self.assertIsNone(code_direct)
        self.assertIsNone(meta_direct)


if __name__ == "__main__":
    unittest.main()
