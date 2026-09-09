from __future__ import annotations

from typing import Any, Dict

from app.graph.state import ScanState
from app.services.ocr_service import OCRExtractionError, extract_document_data


async def extraction_node(state: ScanState) -> Dict[str, Any]:
    file_name = state.get("file_name")
    image_bytes = state.get("image_bytes", b"")
    print(f"[extraction_node] processing '{file_name}' ({len(image_bytes)} bytes)")

    try:
        raw = await extract_document_data(image_bytes)
    except OCRExtractionError as exc:
        print(f"[extraction_node] extraction FAILED: {exc}")
        return {
            "viz_data": None,
            "mrz_data": None,
            "errors": [f"OCR extraction failed: {exc}"],
            "flags": ["EXTRACTION_FAILED"],
            "node_trace": ["extraction_node"],
        }

    viz_data = {
        "first_name": raw["viz_first_name"],
        "last_name": raw["viz_last_name"],
        "document_number": raw["viz_document_number"],
        "dob": raw["viz_dob"],
        "expiry": raw["viz_expiry"],
        "sex": raw["viz_sex"],
    }
    mrz_data = {
        "mrz_line1": raw["mrz_line1"],
        "mrz_line2": raw["mrz_line2"],
    }

    return {
        "viz_data": viz_data,
        "mrz_data": mrz_data,
        "node_trace": ["extraction_node"],
    }