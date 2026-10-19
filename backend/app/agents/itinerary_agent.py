"""Itinerary agent — assembles the final day-by-day plan."""
from datetime import date, timedelta
from typing import Any

from app.agents.base import BaseAgent

THEMES = ["Arrival", "Explore", "Discover", "Day trip", "Relax", "Highlights", "Farewell"]


class ItineraryAgent(BaseAgent):
    name = "itinerary"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        req = state["request"]
        start = date.fromisoformat(req["start_date"])
        end = date.fromisoformat(req["end_date"])
        nights = (end - start).days
        total_days = nights + 1
        budget = int(req.get("budget", 1000))

        interests = [i.lower() for i in req.get("interests", [])]
        city = req.get("destination", "")

        # Dynamic themed activities based on interests
        morning_options = []
        afternoon_options = []
        evening_options = []

        if "adventure" in interests or "nature" in interests:
            morning_options.extend([
                f"Scenic hiking excursion along the panoramic trails of {city}",
                f"Alpine viewpoint trek and nature reserve walk in {city}",
            ])
            afternoon_options.extend([
                f"Outdoor adventure activities and scenic lake / mountain discovery",
                f"Guided eco-tour exploring local flora and canyon trails",
            ])
            evening_options.extend([
                f"Sunset mountain overlook followed by hearty campfire / lodge dinner",
            ])

        if "culture" in interests or "history" in interests:
            morning_options.extend([
                f"Guided walking tour of {city}'s iconic historic quarter and ancient landmarks",
                f"Visit world-renowned architectural monuments and historic temples in {city}",
            ])
            afternoon_options.extend([
                f"Explore premier art & history museums and traditional artisan ateliers",
                f"Heritage district exploration discovering hidden shrines and historic courtyards",
            ])
            evening_options.extend([
                f"Cultural evening performance and candlelit dinner in the historic old town",
            ])

        if "food" in interests:
            morning_options.extend([
                f"Morning artisan bakery and signature breakfast coffee crawl in {city}",
                f"Explore vibrant local morning produce and spice markets",
            ])
            afternoon_options.extend([
                f"Hands-on culinary cooking masterclass tasting signature regional dishes",
                f"Street food tour discovering hidden culinary gems and local specialties",
            ])
            evening_options.extend([
                f"Fine dining reservation celebrating authentic regional gastronomy",
                f"Bustling night market tasting crawl and scenic evening dessert lounge",
            ])

        if "relaxation" in interests or "beaches" in interests:
            morning_options.extend([
                f"Tranquil morning seaside stroll and relaxed beachside breakfast in {city}",
                f"Peaceful sunrise meditation and calm scenic water views",
            ])
            afternoon_options.extend([
                f"Rejuvenating thermal spa / wellness massage and coastal lounge afternoon",
                f"Scenic boat cruise gliding past turquoise lagoons and peaceful coves",
            ])
            evening_options.extend([
                f"Seafood dinner by the water watching the golden coastal sunset",
            ])

        if not morning_options:
            morning_options = [
                f"Morning sightseeing at top-rated landmarks in {city}",
                f"Explore scenic viewpoints and central historic avenues",
            ]
        if not afternoon_options:
            afternoon_options = [
                f"Lunch at a celebrated local eatery followed by cultural exploration",
                f"Discover vibrant boutique shopping streets and artisan markets",
            ]
        if not evening_options:
            evening_options = [
                f"Dinner at a well-reviewed restaurant and relaxed evening stroll",
                f"Scenic evening vistas and dining under the lights of {city}",
            ]

        places = state.get("destination", {}).get("places_to_visit", [])
        place_names = [p["name"] for p in places]

        days = []
        for i in range(total_days):
            d = start + timedelta(days=i)
            # Pick 1-2 suggested places for this day if available
            day_places = []
            if place_names:
                p1 = place_names[(i * 2) % len(place_names)]
                day_places.append(p1)
                if len(place_names) > 1:
                    p2 = place_names[(i * 2 + 1) % len(place_names)]
                    if p2 != p1:
                        day_places.append(p2)

            day_img = None
            if places:
                day_img = places[i % len(places)].get("image_url")

            if i == 0:
                morning = f"Arrive in {city}, check into accommodation and settle in comfortably"
                afternoon = f"Gentle afternoon walk getting acquainted with the neighborhood of {city}"
                evening = "Welcome dinner at a cozy local restaurant and evening rest"
                desc = f"Arrival day in {city}. Ease in, unpack, and enjoy your first authentic evening meal."
            elif i == total_days - 1:
                morning = f"Final morning souvenir shopping and scenic cafe breakfast in {city}"
                afternoon = "Pack up, check out of accommodation, and transfer to departure terminal"
                evening = "Departure flight / transit home with unforgettable memories"
                desc = f"Final day in {city}. Relaxed packing, last-minute artisan finds, and smooth journey home."
            else:
                morning = morning_options[(i - 1) % len(morning_options)]
                afternoon = afternoon_options[(i - 1) % len(afternoon_options)]
                evening = evening_options[(i - 1) % len(evening_options)]
                desc = f"Full day exploring {city} focusing on {', '.join(interests) if interests else 'local culture and sights'}."

            days.append(
                {
                    "day": i + 1,
                    "date": d.isoformat(),
                    "theme": THEMES[min(i, len(THEMES) - 1)],
                    "morning": morning,
                    "afternoon": afternoon,
                    "evening": evening,
                    "stay": f"Comfort stay in {city}",
                    "estimate_usd": round(budget / total_days),
                    "suggested_places": day_places,
                    "image_url": day_img,
                    "description": desc,
                }
            )

        breakdown = state.get("costs", {}).get("breakdown", {})
        focus = f", tailored to {', '.join(req.get('interests', []))}" if req.get("interests") else ""
        req_note = f" (Special request noted: {req.get('special_requests')})" if req.get("special_requests") else ""
        state["itinerary"] = {
            "destination": req["destination"],
            "dates": {"start": req["start_date"], "end": req["end_date"], "nights": nights},
            "travelers": req.get("travelers", 1),
            "interests": req.get("interests", []),
            "budget": budget,
            "budget_breakdown": breakdown,
            "summary": (
                f"A {nights}-night personalized journey to {req['destination']} for "
                f"{req.get('travelers', 1)} traveler(s) on a ${budget:,} budget{focus}. "
                f"Balanced across accommodation, dining, and curated experiences{req_note}."
            ),
            "days": days,
            "places_to_visit": places,
            "hotels": state.get("hotels", {}).get("options", []),
            "transport": state.get("transport", {}),
        }
        return state

