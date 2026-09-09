from __future__ import annotations

from typing import Any, Dict, List

from app.graph.state import ScanState
from app.services.face_service import FaceServiceError, compare_faces

# Phase 2 remaining target: services/ela_service.py (OpenCV ELA) for the tampering score.


async def forensics_node(state: ScanState) -> Dict[str, Any]:
    """
    AGENT: Forensics
    Runs in PARALLEL with validation_node - do not assume validation has run yet.
    Produces a tampering score + heatmap (ELA, still mocked) and a real face
    similarity score between the document photo and the live/selfie capture.
    """
    print("[forensics_node] running ELA (mock) + face match")

    # 1x1 transparent PNG placeholder - Phase 2 generates a real heatmap overlay
    mock_heatmap_b64 = (
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
        "AAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )

    flags: List[str] = []
    document_bytes = state.get("image_bytes", b"")
    selfie_bytes = state.get("selfie_image_bytes", b"")

    if not selfie_bytes:
        face_match_score = None
        face_match_verified = False
        flags.append("SELFIE_UNAVAILABLE")
        errors = ["Face match skipped: no live/selfie image was provided."]
    else:
        try:
            result = await compare_faces(document_bytes, selfie_bytes)
            face_match_score = result.score
            face_match_verified = result.verified
            errors = []
            if not result.verified:
                flags.append("FACE_MATCH_FAILED")
        except FaceServiceError as exc:
            print(f"[forensics_node] face match FAILED: {exc}")
            face_match_score = None
            face_match_verified = False
            flags.append("FACE_MATCH_ERROR")
            errors = [f"Face match failed: {exc}"]

    return {
        "tampering_score": 12.5,
        "ela_heatmap_base64": mock_heatmap_b64,
        "face_match_score": face_match_score,
        "face_match_verified": face_match_verified,
        "flags": flags,
        "errors": errors,
        "node_trace": ["forensics_node"],
    }
