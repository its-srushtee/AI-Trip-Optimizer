"""Multi-agent workflow: destination -> hotels -> weather -> transport -> cost -> itinerary.

Uses LangGraph when installed (install `langgraph` to enable), otherwise falls
back to a simple sequential runner. Either way the output contract is the same.
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

AGENTS = [
    DestinationAgent(),
    HotelAgent(),
    WeatherAgent(),
    TransportAgent(),
    CostAgent(),
    ItineraryAgent(),
]

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover
    LANGGRAPH_AVAILABLE = False


def _build_graph():
    graph = StateGraph(dict)
    for agent in AGENTS:
        graph.add_node(agent.name, agent.run)
    names = [a.name for a in AGENTS]
    for i in range(len(names) - 1):
        graph.add_edge(names[i], names[i + 1])
    graph.set_entry_point(names[0])
    graph.add_edge(names[-1], END)
    return graph.compile()


def _run_sequential(state: dict[str, Any]) -> dict[str, Any]:
    for agent in AGENTS:
        state = agent.run(state)
    return state


def run_workflow(state: dict[str, Any]) -> dict:
    if LANGGRAPH_AVAILABLE:
        result = _build_graph().invoke(state)
    else:
        result = _run_sequential(state)
    return result.get("itinerary", {})
