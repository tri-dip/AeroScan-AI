from __future__ import annotations

from typing import Any, Dict

from app.graph.state import ScanState

# Phase 2 target: services/mrz_service.py (ICAO 9303 checksum math)


def validation_node(state: ScanState) -> Dict[str, Any]:
    """
    AGENT: Validation
    Runs in PARALLEL with forensics_node - do not assume forensics has run yet.
    Verifies MRZ checksums and cross-checks OCR visual fields against MRZ fields.
    """
    print("[validation_node] validating MRZ checksums (mock)")

    return {
        "mrz_valid": True,
        "mrz_checksum_results": {
            "document_number": True,
            "date_of_birth": True,
            "expiry_date": True,
            "composite": True,
        },
        "field_cross_check_passed": True,
        "flags": [],  # real logic will append e.g. "MRZ_CHECKSUM_FAILED"
        "node_trace": ["validation_node"],
    }