from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ScanResponse(BaseModel):
    """
    Public API contract returned to the Next.js frontend.

    Deliberately does NOT include `image_bytes` - the router strips that key
    out of the graph's final state before this model is constructed, so raw
    document bytes never leave the server in the JSON response.
    """

    model_config = {"extra": "ignore"}  # tolerate extra internal state keys defensively

    file_name: str
    document_type: Optional[str] = None

    ocr_confidence: Optional[float] = None
    extracted_fields: Optional[Dict[str, Any]] = None

    mrz_valid: Optional[bool] = None
    mrz_checksum_results: Optional[Dict[str, bool]] = None
    field_cross_check_passed: Optional[bool] = None

    tampering_score: Optional[float] = None
    ela_heatmap_base64: Optional[str] = None
    face_match_score: Optional[float] = None
    face_match_verified: Optional[bool] = None

    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    risk_brief: Optional[str] = None
    final_decision: Optional[str] = None

    flags: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    node_trace: List[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    detail: str