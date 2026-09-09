from __future__ import annotations

from typing import Any, Dict

from app.graph.state import ScanState

def supervisor_node(state: ScanState) -> Dict[str, Any]:
    print("[supervisor_node] synthesizing final risk decision")

    mrz_checksum_valid = state.get("mrz_checksum_valid", False)
    field_cross_check_passed = state.get("field_cross_check_passed", False)
    tampering_score = state.get("tampering_score", 100.0) or 100.0
    face_match_score = state.get("face_match_score", 0.0) or 0.0

    risk_score = 0.0
    if not mrz_checksum_valid:
        risk_score += 30
    if not field_cross_check_passed:
        risk_score += 30
    risk_score += min(tampering_score, 100) * 0.25
    risk_score += max(0.0, 100 - face_match_score) * 0.15

    if risk_score < 20:
        risk_level, decision = "LOW", "APPROVE"
    elif risk_score < 50:
        risk_level, decision = "MEDIUM", "MANUAL_REVIEW"
    elif risk_score < 75:
        risk_level, decision = "HIGH", "MANUAL_REVIEW"
    else:
        risk_level, decision = "CRITICAL", "REJECT"

    brief = (
        f"MRZ checksum validity={mrz_checksum_valid}, VIZ/MRZ cross-check passed={field_cross_check_passed}, "
        f"tampering score={tampering_score:.1f}/100, face match={face_match_score:.1f}%. "
        f"Aggregate risk={risk_score:.1f}/100 -> {risk_level}."
    )

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "final_decision": decision,
        "risk_brief": brief,
        "node_trace": ["supervisor_node"],
    }