from __future__ import annotations

from typing import Any, Dict, List

from app.graph.state import ScanState
from app.services.mrz_service import (
    cross_verify_viz_and_mrz,
    decode_mrz,
    validate_mrz_checksums,
)

_CHECKSUM_FLAG_BY_FIELD = {
    "document_number": "MRZ_DOCUMENT_NUMBER_CHECKSUM_INVALID",
    "date_of_birth": "MRZ_DATE_OF_BIRTH_CHECKSUM_INVALID",
    "expiry_date": "MRZ_EXPIRY_DATE_CHECKSUM_INVALID",
    "composite": "MRZ_COMPOSITE_CHECKSUM_INVALID",
}


def validation_node(state: ScanState) -> Dict[str, Any]:
    viz_data = state.get("viz_data")
    mrz_data = state.get("mrz_data")

    if not mrz_data or not mrz_data.get("mrz_line1") or not mrz_data.get("mrz_line2"):
        print("[validation_node] no MRZ data available - extraction must have failed upstream")
        return {
            "mrz_decoded": None,
            "mrz_checksum_valid": False,
            "mrz_checksum_results": None,
            "cross_check_mismatches": None,
            "field_cross_check_passed": False,
            "flags": ["MRZ_UNAVAILABLE"],
            "errors": ["Validation skipped: no MRZ data was extracted from the document."],
            "node_trace": ["validation_node"],
        }

    decoded = decode_mrz(mrz_data["mrz_line1"], mrz_data["mrz_line2"])

    if decoded["error"] is not None:
        print(f"[validation_node] MRZ decode failed: {decoded['error']}")
        return {
            "mrz_decoded": decoded,
            "mrz_checksum_valid": False,
            "mrz_checksum_results": None,
            "cross_check_mismatches": None,
            "field_cross_check_passed": False,
            "flags": ["MRZ_MALFORMED"],
            "errors": [f"MRZ decode error: {decoded['error']}"],
            "node_trace": ["validation_node"],
        }

    print("[validation_node] validating MRZ checksums")
    checksum_result = validate_mrz_checksums(mrz_data["mrz_line2"])

    flags: List[str] = []
    if checksum_result["error"] is not None:
        flags.append("MRZ_CHECKSUM_ERROR")
    else:
        flags.extend(
            _CHECKSUM_FLAG_BY_FIELD[name]
            for name, passed in checksum_result["checks"].items()
            if not passed
        )

    mismatches: List[str] = []
    field_cross_check_passed = False

    if viz_data:
        print("[validation_node] cross-verifying VIZ against decoded MRZ")
        mismatches = cross_verify_viz_and_mrz(viz_data, decoded)
        field_cross_check_passed = len(mismatches) == 0
        flags.extend(mismatches)
    else:
        flags.append("VIZ_UNAVAILABLE")

    return {
        "mrz_decoded": decoded,
        "mrz_checksum_valid": checksum_result["mrz_valid"],
        "mrz_checksum_results": checksum_result["checks"],
        "cross_check_mismatches": mismatches,
        "field_cross_check_passed": field_cross_check_passed,
        "flags": flags,
        "node_trace": ["validation_node"],
    }