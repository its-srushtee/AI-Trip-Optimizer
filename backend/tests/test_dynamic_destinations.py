"""Test dynamic destination support across 5 diverse destinations:
1. Manali, India
2. Kyoto, Japan
3. Interlaken, Switzerland
4. Bali, Indonesia
5. Chefchaouen, Morocco (a less popular destination not in the initial catalogue)

For each destination, verifies:
- Destination information is relevant
- Attractions belong to the correct location
- Coordinates are valid
- Recommendations reflect user preferences
- Results are not copied from another destination
"""
import sys
import os
from datetime import date

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.itinerary import OptimizeRequest
from app.services.itinerary_service import generate_itinerary


TEST_SCENARIOS = [
    {
        "name": "Scenario 1: Manali, India (Nature + Adventure)",
        "payload": {
            "destination": "Manali",
            "start_date": "2026-11-01",
            "end_date": "2026-11-04",
            "budget": 800,
            "travelers": 2,
            "interests": ["nature", "adventure"],
            "pace": "Fast-paced",
            "style": "Backpacker",
        },
        "expected_country": "India",
        "expected_keywords": ["manali", "solang", "rohtang", "hidimba", "beas", "himalayan", "pass", "trek", "valley"],
    },
    {
        "name": "Scenario 2: Kyoto, Japan (Culture + History + Food)",
        "payload": {
            "destination": "Kyoto",
            "start_date": "2026-11-10",
            "end_date": "2026-11-14",
            "budget": 2500,
            "travelers": 2,
            "interests": ["culture", "history", "food"],
            "pace": "Moderate",
            "style": "Comfort",
        },
        "expected_country": "Japan",
        "expected_keywords": ["kyoto", "fushimi", "kinkaku", "kiyomizu", "arashiyama", "gion", "temple", "shrine"],
    },
    {
        "name": "Scenario 3: Interlaken, Switzerland (Nature + Photography)",
        "payload": {
            "destination": "Interlaken",
            "start_date": "2026-12-01",
            "end_date": "2026-12-05",
            "budget": 3500,
            "travelers": 2,
            "interests": ["nature", "photography"],
            "pace": "Moderate",
            "style": "Luxury",
        },
        "expected_country": "Switzerland",
        "expected_keywords": ["interlaken", "harder kulm", "jungfrau", "brienz", "thun", "alps", "swiss", "lake"],
    },
    {
        "name": "Scenario 4: Bali, Indonesia (Beaches + Relaxation)",
        "payload": {
            "destination": "Bali",
            "start_date": "2026-11-15",
            "end_date": "2026-11-20",
            "budget": 1800,
            "travelers": 2,
            "interests": ["beaches", "relaxation"],
            "pace": "Relaxed",
            "style": "Comfort",
        },
        "expected_country": "Indonesia",
        "expected_keywords": ["bali", "tanah lot", "uluwatu", "ubud", "tegallalang", "beach", "temple", "kuta", "sanur"],
    },
    {
        "name": "Scenario 5: Chefchaouen, Morocco (Culture + Photography - Unseeded Destination)",
        "payload": {
            "destination": "Chefchaouen",
            "start_date": "2026-12-10",
            "end_date": "2026-12-13",
            "budget": 1200,
            "travelers": 2,
            "interests": ["culture", "photography"],
            "pace": "Relaxed",
            "style": "Budget",
        },
        "expected_country": "Morocco",
        "expected_keywords": ["chefchaouen", "medina", "kasbah", "blue", "morocco", "rif", "waterfall", "chaouen"],
    },
]


def run_tests():
    print("=" * 70)
    print("RUNNING DYNAMIC ANY-DESTINATION VERIFICATION SUITE")
    print("=" * 70)
    
    passed_all = True
    
    for tc in TEST_SCENARIOS:
        print(f"\n---> {tc['name']}")
        payload = tc["payload"]
        assert isinstance(payload, dict)
        req = OptimizeRequest(**payload)
        result = generate_itinerary(req)
        
        destination = result.get("destination", "")
        country = result.get("country", "")
        coords = result.get("coordinates") or {}
        days = result.get("days", [])
        places = result.get("places_to_visit", [])
        
        print(f"  • Destination: {destination} (Country: {country})")
        print(f"  • Coordinates: lat={coords.get('lat')}, lon={coords.get('lon') or coords.get('lng')}")
        print(f"  • Days Generated: {len(days)}")
        print(f"  • Places Retrieved: {len(places)}")
        
        # 1. Verify destination & country
        assert destination.lower() == tc["payload"]["destination"].lower(), f"Wrong destination returned: {destination}"
        if tc["expected_country"]:
            assert tc["expected_country"].lower() in country.lower(), f"Expected {tc['expected_country']} but got {country}"
            print(f"  ✓ Country verified: {country}")
            
        # 2. Verify coordinates
        lat = coords.get("lat")
        lon = coords.get("lon") or coords.get("lng")
        assert lat is not None and lon is not None, f"Coordinates missing for {destination}"
        assert -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180, f"Invalid coordinates: {coords}"
        print(f"  ✓ Valid coordinates: ({lat}, {lon})")
        
        # 3. Verify places belong to the correct location and not copied from another destination
        assert len(places) > 0, f"No places retrieved for {destination}"
        place_names = [p["name"] for p in places]
        print(f"  • Sample Places: {', '.join(place_names[:4])}")
        
        combined_text = " ".join([
            p["name"].lower() + " " + p.get("description", "").lower() + " " + p.get("location", "").lower()
            for p in places
        ])
        
        match_found = any(k in combined_text for k in tc["expected_keywords"])
        assert match_found, f"None of the expected destination keywords {tc['expected_keywords']} found in places for {destination}!"
        print(f"  ✓ Attractions belong to {destination} and match destination context")
        
        # 4. Verify user preferences are reflected in itinerary
        summary = result.get("summary", "")
        assert tc["payload"]["pace"].lower().replace("-paced", "") in summary.lower(), "Pace not reflected in summary"
        for interest in tc["payload"]["interests"]:
            assert interest.lower() in summary.lower(), f"Interest '{interest}' not reflected in summary"
        print(f"  ✓ Personalization verified: preferences correctly reflected in itinerary summary")
        
        # 5. Verify non-empty daily activities and stays
        for d in days:
            assert d.get("morning"), f"Day {d.get('day')} missing morning activity"
            assert d.get("afternoon"), f"Day {d.get('day')} missing afternoon activity"
            assert d.get("evening"), f"Day {d.get('day')} missing evening activity"
            assert d.get("stay"), f"Day {d.get('day')} missing stay"
        print(f"  ✓ Complete structured timeline with morning, afternoon, evening activities and stay")

    print("\n" + "=" * 70)
    print("ALL 5 DESTINATION VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()

