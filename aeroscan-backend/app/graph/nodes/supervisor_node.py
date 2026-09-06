from __future__ import annotations

from typing import Any, Dict

from app.graph.state import ScanState

# Phase 3+ candidate: swap the deterministic scoring below for an LLM call that
# reads the aggregated signals and writes `risk_brief` in natural language.


def supervisor_node(state: ScanState) -> Dict[str, Any]:
    """
    AGENT: Supervisor
    Runs AFTER both validation_node and forensics_node complete (fan-in join).
    Synthesizes all upstream signals into a final risk score and decision.
    """
    print("[supervisor_node] synthesizing final risk decision")

    mrz_valid = state.get("mrz_valid", False)
    tampering_score = state.get("tampering_score", 100.0) or 100.0
    face_match_score = state.get("face_match_score", 0.0) or 0.0

    risk_score = 0.0
    if not mrz_valid:
        risk_score += 40
    risk_score += min(tampering_score, 100) * 0.4
    risk_score += max(0.0, 100 - face_match_score) * 0.3

    if risk_score < 20:
        risk_level, decision = "LOW", "APPROVE"
    elif risk_score < 50:
        risk_level, decision = "MEDIUM", "MANUAL_REVIEW"
    elif risk_score < 75:
        risk_level, decision = "HIGH", "MANUAL_REVIEW"
    else:
        risk_level, decision = "CRITICAL", "REJECT"

    brief = (
        f"MRZ validity={mrz_valid}, tampering score={tampering_score:.1f}/100, "
        f"face match={face_match_score:.1f}%. Aggregate risk={risk_score:.1f}/100 -> {risk_level}."
    )

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "final_decision": decision,
        "risk_brief": brief,
        "node_trace": ["supervisor_node"],
    }