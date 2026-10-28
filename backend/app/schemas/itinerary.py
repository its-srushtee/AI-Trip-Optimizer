"""Itinerary schemas (POST /trips/optimize)."""
from datetime import date

from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    destination: str = Field(min_length=1, max_length=120)
    start_date: date
    end_date: date
    budget: int = Field(default=1000, ge=0)
    travelers: int = Field(default=1, ge=1, le=20)
    interests: list[str] = Field(default_factory=list)
    style: str | None = None
    pace: str | None = None
    accommodation: str | None = None
    food: str | None = None
    currency: str | None = None
    origin: str | None = None
    special_requests: str | None = None
    accessibility: str | None = None
    preferences: dict = Field(default_factory=dict)


class ActivityItem(BaseModel):
    name: str
    time_slot: str  # "Morning", "Afternoon", "Evening"
    time_window: str | None = None  # e.g., "08:30 AM - 11:30 AM"
    location: str
    category: str
    estimated_duration: str | None = None
    estimated_cost: str | None = None
    why_it_matches: str | None = None
    transit_info: str | None = None


class DayOut(BaseModel):
    day: int
    date: date
    theme: str
    morning: str
    afternoon: str
    evening: str
    stay: str
    estimate_usd: int
    estimate_cost: int | None = None
    currency: str | None = "USD"
    currency_symbol: str | None = "$"
    suggested_places: list[str] = Field(default_factory=list)
    image_url: str | None = None
    description: str | None = None
    pace_notes: str | None = None
    meal_suggestions: dict | None = None
    activities: list[ActivityItem] = Field(default_factory=list)


class PlaceOut(BaseModel):
    name: str
    description: str
    category: str
    image_url: str | None = "/images/hero.jpg"
    location: str
    why_it_matches: str | None = None
    match_reasons: list[str] = Field(default_factory=list)
    visit_info: str | None = None
    estimated_duration: str | None = None
    rating: float | None = 4.8
    tags: list[str] = Field(default_factory=list)
    coordinates: dict | None = None
    source: str | None = None
    address: str | None = None


class BudgetBreakdown(BaseModel):
    flights: int
    transport_mode: str | None = "Flight"
    stay: int
    food: int
    activities: int
    local_transit: int = 0
    miscellaneous: int = 0
    total: int
    target_budget: int | None = None
    currency: str | None = "USD"
    currency_symbol: str | None = "$"
    is_estimated: bool = True
    exceeds_budget: bool = False
    budget_variance: int | None = 0
    remaining_budget: int | None = 0
    utilization_percent: int | None = 100
    percentages: dict | None = None
    feasibility: dict | None = None
    budget_status: str | None = "Within Target Budget"
    per_traveler: int | None = None
    per_day: int | None = None


class ItineraryDates(BaseModel):
    start: date
    end: date
    nights: int


class ItineraryOut(BaseModel):
    destination: str
    dates: ItineraryDates
    travelers: int
    interests: list[str]
    budget: int
    budget_breakdown: BudgetBreakdown
    coordinates: dict | None = None
    formatted_address: str | None = None
    country: str | None = None
    summary: str
    days: list[DayOut]
    places_to_visit: list[PlaceOut] = Field(default_factory=list)
    hotels: list[dict] = Field(default_factory=list)
    transport: dict | None = Field(default_factory=dict)
    weather: dict | None = None
    currency: str | None = "USD"
    currency_symbol: str | None = "$"
    preferences_applied: dict | None = Field(default_factory=dict)
    coordinates: dict | None = None
    formatted_address: str | None = None
    country: str | None = None


class OptimizeResponse(BaseModel):
    itinerary: ItineraryOut

