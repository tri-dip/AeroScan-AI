from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    extraction_node,
    forensics_node,
    supervisor_node,
    validation_node,
)
from app.graph.state import ScanState


def build_scan_graph():
    r"""
    Topology:

        START -> extraction -> validation  \
                             \-> forensics  --> supervisor -> END

    `validation` and `forensics` both fire in the same superstep once
    `extraction` completes (fan-out). `supervisor` only fires once BOTH
    have completed (fan-in) - LangGraph handles this join automatically
    because it has two incoming edges.
    """
    graph = StateGraph(ScanState)

    graph.add_node("extraction", extraction_node)
    graph.add_node("validation", validation_node)
    graph.add_node("forensics", forensics_node)
    graph.add_node("supervisor", supervisor_node)

    graph.add_edge(START, "extraction")

    # Fan-out: both branches scheduled off the single extraction result
    graph.add_edge("extraction", "validation")
    graph.add_edge("extraction", "forensics")

    # Fan-in: supervisor waits for both parallel branches
    graph.add_edge("validation", "supervisor")
    graph.add_edge("forensics", "supervisor")

    graph.add_edge("supervisor", END)

    return graph.compile()


# Compiled once at import time and reused across requests (cheap to hold in memory,
# avoids rebuilding the graph on every API call).
scan_graph = build_scan_graph()