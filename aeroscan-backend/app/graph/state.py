from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

class ScanState(TypedDict, total=False):
    file_name: str
    image_bytes: bytes
    document_type: Optional[str] 

    ocr_raw_text: Optional[str]
    ocr_confidence: Optional[float]  
    mrz_raw_lines: Optional[List[str]]            
    extracted_fields: Optional[Dict[str, Any]]    

    mrz_valid: Optional[bool]
    mrz_checksum_results: Optional[Dict[str, bool]]   
    field_cross_check_passed: Optional[bool]          

    tampering_score: Optional[float]      
    ela_heatmap_base64: Optional[str]     
    face_match_score: Optional[float]     
    face_match_verified: Optional[bool]

    risk_level: Optional[str]      
    risk_score: Optional[float]    
    risk_brief: Optional[str]      
    final_decision: Optional[str]  

    flags: Annotated[List[str], operator.add]       
    errors: Annotated[List[str], operator.add]      
    node_trace: Annotated[List[str], operator.add]