from __future__ import annotations

from typing import Any, Dict

from app.graph.state import ScanState

# Phase 2 target: services/ela_service.py (OpenCV ELA) + services/face_service.py (DeepFace)


def forensics_node(state: ScanState) -> Dict[str, Any]:
    """
    AGENT: Forensics
    Runs in PARALLEL with validation_node - do not assume validation has run yet.
    Produces a tampering score + heatmap (ELA) and a face similarity score.
    """
    print("[forensics_node] running ELA + face match (mock)")

    # 1x1 transparent PNG placeholder - Phase 2 generates a real heatmap overlay
    mock_heatmap_b64 = (
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
        "AAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )

    return {
        "tampering_score": 12.5,
        "ela_heatmap_base64": mock_heatmap_b64,
        "face_match_score": 91.3,
        "face_match_verified": True,
        "flags": [],  # real logic will append e.g. "HIGH_ELA_VARIANCE"
        "node_trace": ["forensics_node"],
    }