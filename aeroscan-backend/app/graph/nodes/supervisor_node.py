from __future__ import annotations

from typing import Any, Dict

from app.graph.state import ScanState

def supervisor_node(state: ScanState) -> Dict[str, Any]:
    """
    AGENT: Supervisor
    Runs AFTER both validation_node and forensics_node complete (fan-in join).
    Synthesizes all upstream signals into a final risk score and decision.
    """
    print("[supervisor_node] synthesizing final risk decision")

    mrz_checksum_valid = state.get("mrz_checksum_valid", False)
    field_cross_check_passed = state.get("field_cross_check_passed", False)
    face_match_verified = state.get("face_match_verified", False)
    tampering_score = state.get("tampering_score")
    if tampering_score is None:
        tampering_score = 100.0
    face_match_score = state.get("face_match_score")
    if face_match_score is None:
        face_match_score = 0.0
    flags = state.get("flags", [])

    # Direct, specific evidence that the document's own photo was pasted/altered
    # (as opposed to generic compression noise, which is far more prone to false
    # positives on low-quality scans) - weighted comparably to a failed face
    # match, since a substituted portrait is itself a forged-document signal.
    photo_tamper_flags = {"SUSPICIOUS_PHOTO_SEAM", "PHOTO_ELA_MISMATCH"}
    photo_splice_detected = bool(photo_tamper_flags.intersection(flags))

    risk_score = 0.0
    if not mrz_checksum_valid:
        risk_score += 20
    if not field_cross_check_passed:
        risk_score += 20
    if not face_match_verified:
        risk_score += 50
    # Was 0.10 - a maxed-out tampering_score of 100 could only ever add 10
    # points, meaning a confirmed photo splice could never clear even the LOW
    # risk threshold on its own. 0.30 lets tampering evidence actually move
    # the needle in line with the other checks.
    risk_score += min(tampering_score, 100) * 0.30
    if photo_splice_detected:
        risk_score += 40
    risk_score = min(risk_score, 100.0)

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
        f"face match verified={face_match_verified} (score={face_match_score:.1f}%), "
        f"tampering score={tampering_score:.1f}/100"
        f"{', photo splice detected' if photo_splice_detected else ''}. "
        f"Aggregate risk={risk_score:.1f}/100 -> {risk_level}."
    )

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "final_decision": decision,
        "risk_brief": brief,
        "node_trace": ["supervisor_node"],
    }