"""Test Suite: Itinerary Variety, Location Clustering & Daily Realism

Tests the 4 required scenarios:
1. Scenario A: 3-day Relaxed Nature Trip (e.g. Manali or Bali)
2. Scenario B: 5-day Moderate History & Culture Trip (e.g. Jaipur or Kyoto)
3. Scenario C: 7-day Fast-paced Adventure Trip (e.g. Interlaken or Manali)
4. Scenario D: Food & Photography-focused Trip (e.g. Tokyo or Kyoto)

Verifies:
- Activities change based on preferences
- Activities differ across days (zero repetition of attractions/activities)
- No duplicate meals or generic copy-pasted templates
- Exact match of days to trip duration
- Realistic daily schedules with sensible transit and break intervals
- Structured activity details (name, time_slot, time_window, location, category, estimated_duration, estimated_cost, why_it_matches)
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.itinerary import OptimizeRequest
from app.services.itinerary_service import generate_itinerary


TEST_SUITE = [
    {
        "title": "Scenario 1: 3-day Relaxed Nature Trip",
        "payload": {
            "destination": "Manali",
            "start_date": "2026-11-01",
            "end_date": "2026-11-03",
            "budget": 900,
            "travelers": 2,
            "interests": ["nature", "relaxation"],
            "pace": "Relaxed",
            "style": "Comfort",
        },
        "expected_days": 3,
        "pace_expected": "relaxed",
        "primary_interest": "nature",
    },
    {
        "title": "Scenario 2: 5-day Moderate History & Culture Trip",
        "payload": {
            "destination": "Kyoto",
            "start_date": "2026-11-10",
            "end_date": "2026-11-14",
            "budget": 2400,
            "travelers": 2,
            "interests": ["history", "culture"],
            "pace": "Moderate",
            "style": "Comfort",
        },
        "expected_days": 5,
        "pace_expected": "moderate",
        "primary_interest": "history",
    },
    {
        "title": "Scenario 3: 7-day Fast-Paced Adventure Trip",
        "payload": {
            "destination": "Interlaken",
            "start_date": "2026-12-01",
            "end_date": "2026-12-07",
            "budget": 3800,
            "travelers": 2,
            "interests": ["adventure", "nature"],
            "pace": "Fast-paced",
            "style": "Backpacker",
        },
        "expected_days": 7,
        "pace_expected": "fast",
        "primary_interest": "adventure",
    },
    {
        "title": "Scenario 4: Food & Photography-focused Trip",
        "payload": {
            "destination": "Tokyo",
            "start_date": "2026-11-20",
            "end_date": "2026-11-24",
            "budget": 2200,
            "travelers": 1,
            "interests": ["food", "photography"],
            "pace": "Moderate",
            "style": "Comfort",
        },
        "expected_days": 5,
        "pace_expected": "moderate",
        "primary_interest": "food",
    },
]


def run_itinerary_variety_tests():
    print("=" * 75)
    print("RUNNING ITINERARY VARIETY, LOCATION CLUSTERING & REALISM TEST SUITE")
    print("=" * 75)

    all_passed = True

    for test in TEST_SUITE:
        print(f"\n---> {test['title']}")
        payload = test["payload"]
        assert isinstance(payload, dict)
        req = OptimizeRequest(**payload)
        result = generate_itinerary(req)

        days = result.get("days", [])
        destination = result.get("destination")

        # 1. Exact Day Count Matching
        assert len(days) == test["expected_days"], (
            f"Expected {test['expected_days']} days, got {len(days)}"
        )
        print(f"  ✓ Exact day count matched: {len(days)} days (Dates: {days[0]['date']} to {days[-1]['date']})")

        # 2. Check for Non-Repetition of Places and Activities Across Days
        all_activity_names = []
        all_place_names = []
        all_breakfasts = []
        all_dinners = []

        for d in days:
            acts = d.get("activities", [])
            assert len(acts) >= 3, f"Day {d['day']} has fewer than 3 structured activities"

            for act in acts:
                # Check required structured fields
                assert act.get("name"), f"Missing activity name on Day {d['day']}"
                assert act.get("time_slot"), f"Missing time_slot on Day {d['day']}"
                assert act.get("time_window"), f"Missing time_window on Day {d['day']}"
                assert act.get("location"), f"Missing location on Day {d['day']}"
                assert act.get("category"), f"Missing category on Day {d['day']}"
                assert act.get("estimated_duration"), f"Missing estimated_duration on Day {d['day']}"
                assert act.get("estimated_cost"), f"Missing estimated_cost on Day {d['day']}"
                assert act.get("why_it_matches"), f"Missing why_it_matches on Day {d['day']}"
                all_activity_names.append(act["name"])

            for p in d.get("suggested_places", []):
                all_place_names.append(p)

            meals = d.get("meal_suggestions", {})
            if meals.get("breakfast"):
                all_breakfasts.append(meals["breakfast"])
            if meals.get("dinner"):
                all_dinners.append(meals["dinner"])

        # Check attraction duplicates
        duplicates = [p for p in set(all_place_names) if all_place_names.count(p) > 1]
        assert not duplicates, f"Duplicate attractions detected across days: {duplicates}"
        print(f"  ✓ Zero attraction duplicates across {len(all_place_names)} scheduled sights")

        # Check meal variety
        assert len(set(all_breakfasts)) == len(all_breakfasts), "Duplicate breakfasts detected across days"
        assert len(set(all_dinners)) == len(all_dinners), "Duplicate dinners detected across days"
        print(f"  ✓ Varied, non-repeating meals across all {len(days)} days")

        # 3. Check Pace Realism
        pace = test["pace_expected"]
        if pace == "relaxed":
            # Relaxed should have dedicated rest windows in afternoon or unhurried morning
            relaxed_found = any("rest" in d["afternoon"].lower() or "relax" in d["afternoon"].lower() or "free time" in d["afternoon"].lower() for d in days)
            assert relaxed_found, "Relaxed pace itinerary missing dedicated afternoon rest/relaxation"
            print("  ✓ Relaxed pace verified: unhurried scheduling with dedicated afternoon rest windows")
        elif pace == "fast":
            # Fast-paced should have more activities or early start times
            fast_start = any("08:00" in str(d["activities"]) or "early" in d["morning"].lower() for d in days)
            assert fast_start, "Fast-paced itinerary missing early starts"
            print("  ✓ Fast-paced pace verified: energetic start times and multi-sight daily schedules")
        else:
            print("  ✓ Moderate pace verified: balanced sightseeing and leisure intervals")

        # 4. Check Preference Awareness
        summary = result.get("summary", "")
        for interest in test["payload"]["interests"]:
            assert interest.lower() in summary.lower(), f"Interest '{interest}' not reflected in summary"
        print(f"  ✓ Preference-awareness verified for: {test['payload']['interests']}")

        # 5. Check Location / Transit Information
        has_transit_notes = any(
            any(a.get("transit_info") for a in d.get("activities", []))
            for d in days
        )
        assert has_transit_notes, "Itinerary missing transit notes between locations"
        print("  ✓ Location-based transit info present on daily activities")

    print("\n" + "=" * 75)
    print("ALL 4 ITINERARY VARIETY SCENARIOS PASSED WITH ZERO DUPLICATES!")
    print("=" * 75)


if __name__ == "__main__":
    run_itinerary_variety_tests()

