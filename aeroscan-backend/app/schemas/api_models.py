from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ScanResponse(BaseModel):
    model_config = {"extra": "ignore"} 

    file_name: str
    document_type: Optional[str] = None

    viz_data: Optional[Dict[str, Any]] = None       
    mrz_data: Optional[Dict[str, Any]] = None       
    mrz_decoded: Optional[Dict[str, Any]] = None    

    mrz_checksum_valid: Optional[bool] = None
    mrz_checksum_results: Optional[Dict[str, bool]] = None
    cross_check_mismatches: Optional[List[str]] = None
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