from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.graph.state import ScanState
from app.services.ela_services import ELAAnalysisError, analyze_tampering
from app.services.face_service import (
    FaceServiceError,
    compare_faces,
    detect_primary_face_bbox,
)


async def forensics_node(state: ScanState) -> Dict[str, Any]:
    """
    AGENT: Forensics
    Runs in PARALLEL with validation_node - do not assume validation has run yet.

    Two real (non-mock) checks, chained so the second can use output from the
    first without depending on it succeeding:
      1. face_service.compare_faces()   - document photo vs. live selfie (ArcFace)
      2. ela_service.analyze_tampering() - ELA + photo-splice + noise-residual,
         targeted at the document's own face region when we have its bbox

    Uses the existing `image_bytes` / `selfie_image_bytes` state keys (not
    `document_image_bytes` / `live_webcam_bytes`) to stay consistent with
    scan_router.py and state.py, which already use those names end-to-end.
    """
    print("[forensics_node] running face match + ELA tampering analysis")

    flags: List[str] = []
    errors: List[str] = []

    document_bytes = state.get("image_bytes", b"")
    selfie_bytes = state.get("selfie_image_bytes", b"")

    face_match_score: Optional[float] = None
    face_match_similarity: Optional[float] = None
    face_match_verified = False
    document_face_bbox: Optional[List[int]] = None

    if not selfie_bytes:
        flags.append("SELFIE_UNAVAILABLE")
        errors.append("Face match skipped: no live/selfie image was provided.")
        # Still worth getting the document's own face bbox if we can - it lets
        # the ELA photo-splice check run even though full face-match can't.
        try:
            document_face_bbox = await detect_primary_face_bbox(document_bytes)
        except FaceServiceError as exc:
            print(f"[forensics_node] fallback face-location detection also failed: {exc}")
    else:
        try:
            face_result = await compare_faces(document_bytes, selfie_bytes)
            face_match_score = face_result.score
            face_match_similarity = face_result.cosine_similarity
            face_match_verified = face_result.verified
            document_face_bbox = face_result.document_face_bbox
            if not face_result.verified:
                flags.append("FACE_MATCH_FAILED")
        except FaceServiceError as exc:
            print(f"[forensics_node] face match FAILED: {exc}")
            flags.append("FACE_MATCH_ERROR")
            errors.append(f"Face match failed: {exc}")
            # compare_faces failed (e.g. no face in the selfie) - the document
            # image alone might still yield a bbox for the ELA check below.
            try:
                document_face_bbox = await detect_primary_face_bbox(document_bytes)
            except FaceServiceError as bbox_exc:
                print(f"[forensics_node] fallback face-location detection also failed: {bbox_exc}")

    tampering_score = 100.0  # conservative default if ELA itself can't run at all
    heatmap_base64: Optional[str] = None

    try:
        ela_result = await analyze_tampering(document_bytes, face_bbox=document_face_bbox)
        tampering_score = ela_result["tampering_score"]
        heatmap_base64 = ela_result["heatmap_base64"]
        flags.extend(ela_result["tampering_flags"])
    except ELAAnalysisError as exc:
        print(f"[forensics_node] ELA analysis FAILED: {exc}")
        flags.append("ELA_ANALYSIS_ERROR")
        errors.append(f"Tampering analysis failed: {exc}")

    return {
        "tampering_score": tampering_score,
        "ela_heatmap_base64": heatmap_base64,
        "face_match_score": face_match_score,
        "face_match_similarity": face_match_similarity,
        "face_match_verified": face_match_verified,
        "face_match_bbox": document_face_bbox,
        "flags": flags,
        "errors": errors,
        "node_trace": ["forensics_node"],
    }