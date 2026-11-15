"""Multi-agent workflow: budget_planner -> destination -> hotels -> weather -> transport -> cost_validator -> itinerary.

Enforces budget as the primary constraint across the entire pipeline.
Uses LangGraph when installed, otherwise falls back to sequential execution.
"""
from typing import Any

from app.agents import (
    CostAgent,
    DestinationAgent,
    HotelAgent,
    ItineraryAgent,
    TransportAgent,
    WeatherAgent,
)

cost_agent = CostAgent()
destination_agent = DestinationAgent()
hotel_agent = HotelAgent()
weather_agent = WeatherAgent()
transport_agent = TransportAgent()
itinerary_agent = ItineraryAgent()

# Node functions
def budget_planner_node(state: dict[str, Any]) -> dict[str, Any]:
    return cost_agent.pre_allocate(state)

def destination_node(state: dict[str, Any]) -> dict[str, Any]:
    return destination_agent.run(state)

def hotel_node(state: dict[str, Any]) -> dict[str, Any]:
    return hotel_agent.run(state)

def weather_node(state: dict[str, Any]) -> dict[str, Any]:
    return weather_agent.run(state)

def transport_node(state: dict[str, Any]) -> dict[str, Any]:
    return transport_agent.run(state)

def cost_validator_node(state: dict[str, Any]) -> dict[str, Any]:
    return cost_agent.run(state)

def itinerary_node(state: dict[str, Any]) -> dict[str, Any]:
    return itinerary_agent.run(state)

NODE_SEQUENCE = [
    ("budget_planner", budget_planner_node),
    ("destination", destination_node),
    ("hotels", hotel_node),
    ("weather", weather_node),
    ("transport", transport_node),
    ("cost_validator", cost_validator_node),
    ("itinerary", itinerary_node),
]

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover
    LANGGRAPH_AVAILABLE = False


def _build_graph():
    graph = StateGraph(dict)
    for name, fn in NODE_SEQUENCE:
        graph.add_node(name, fn)
    names = [name for name, _ in NODE_SEQUENCE]
    for i in range(len(names) - 1):
        graph.add_edge(names[i], names[i + 1])
    graph.set_entry_point(names[0])
    graph.add_edge(names[-1], END)
    return graph.compile()


def _run_sequential(state: dict[str, Any]) -> dict[str, Any]:
    for _, fn in NODE_SEQUENCE:
        state = fn(state)
    return state


def run_workflow(state: dict[str, Any]) -> dict:
    if LANGGRAPH_AVAILABLE:
        result = _build_graph().invoke(state)
    else:
        result = _run_sequential(state)
    return result.get("itinerary", {})
