from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class ScanState(TypedDict, total=False):
    file_name: str
    image_bytes: bytes
    selfie_image_bytes: bytes
    document_type: Optional[str]     # request hint, e.g. "passport" - accepted but not yet used to branch logic (TD3-only for now)
    station_id: Optional[str]     # request-supplied audit/traceability tag, echoed back unmodified in the response

    viz_data: Optional[Dict[str, Any]]
    mrz_data: Optional[Dict[str, Any]]

    mrz_decoded: Optional[Dict[str, Any]]
    mrz_checksum_valid: Optional[bool]
    mrz_checksum_results: Optional[Dict[str, bool]]
    cross_check_mismatches: Optional[List[str]]
    field_cross_check_passed: Optional[bool]

    tampering_score: Optional[float]
    ela_heatmap_base64: Optional[str]
    face_match_score: Optional[float]           # 0-100, UI-friendly
    face_match_similarity: Optional[float]       # raw ArcFace cosine similarity, e.g. 0.0852 - kept for audit/threshold-recalibration
    face_match_verified: Optional[bool]
    face_match_bbox: Optional[List[int]]         # [x1,y1,x2,y2] document photo face location, pixel coords in the uploaded image

    risk_level: Optional[str]
    risk_score: Optional[float]
    risk_brief: Optional[str]
    final_decision: Optional[str]

    flags: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    node_trace: Annotated[List[str], operator.add]