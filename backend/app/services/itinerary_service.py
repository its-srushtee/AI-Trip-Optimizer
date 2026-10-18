"""Itinerary service — orchestrates the multi-agent workflow.

Replace the workflow runner in app/workflows/trip_graph.py with the real
LangGraph pipeline (researcher -> feasibility -> writer + RAG). The response
contract (ItineraryOut) stays stable so the frontend never changes.
"""
from app.schemas.itinerary import OptimizeRequest
from app.workflows.trip_graph import run_workflow


def generate_itinerary(request: OptimizeRequest) -> dict:
    state = {
        "request": request.model_dump(mode="json"),
        "destination": None,
        "hotels": None,
        "weather": None,
        "transport": None,
        "costs": None,
        "itinerary": None,
    }
    return run_workflow(state)
