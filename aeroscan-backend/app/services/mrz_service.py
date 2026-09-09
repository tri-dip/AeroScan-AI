from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, TypedDict

_WEIGHTS = (7, 3, 1)

_DOC_NUMBER_SLICE = slice(0, 9)
_DOC_NUMBER_CHECK_POS = 9
_DOB_SLICE = slice(13, 19)
_DOB_CHECK_POS = 19
_EXPIRY_SLICE = slice(21, 27)
_EXPIRY_CHECK_POS = 27
_COMPOSITE_CHECK_POS = 43
_TD3_LINE_LENGTH = 44


class MRZChecksumResults(TypedDict):
    document_number: bool
    date_of_birth: bool
    expiry_date: bool
    composite: bool


class MRZValidationResult(TypedDict):
    mrz_valid: bool
    checks: MRZChecksumResults
    error: Optional[str]


def _char_value(char: str) -> int:
    if char.isdigit():
        return int(char)
    if char == "<":
        return 0
    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 10
    raise ValueError(f"Character {char!r} is not valid in an MRZ checksum field")


def _compute_check_digit(data: str) -> int:
    total = 0
    for i, char in enumerate(data):
        total += _char_value(char) * _WEIGHTS[i % 3]
    return total % 10


def _digit_matches(data: str, check_char: str) -> bool:
    computed = _compute_check_digit(data)
    if check_char == "<":
        return computed == 0
    if not check_char.isdigit():
        return False
    return computed == int(check_char)


def validate_mrz_checksums(line2: str) -> MRZValidationResult:
    all_false: MRZChecksumResults = {
        "document_number": False,
        "date_of_birth": False,
        "expiry_date": False,
        "composite": False,
    }

    if not isinstance(line2, str):
        return {"mrz_valid": False, "checks": all_false, "error": "line2 must be a string."}

    line = line2.strip().upper()

    if len(line) != _TD3_LINE_LENGTH:
        return {
            "mrz_valid": False,
            "checks": all_false,
            "error": f"line2 must be exactly {_TD3_LINE_LENGTH} characters (TD3 format), got {len(line)}.",
        }

    try:
        doc_number_ok = _digit_matches(line[_DOC_NUMBER_SLICE], line[_DOC_NUMBER_CHECK_POS])
        dob_ok = _digit_matches(line[_DOB_SLICE], line[_DOB_CHECK_POS])
        expiry_ok = _digit_matches(line[_EXPIRY_SLICE], line[_EXPIRY_CHECK_POS])

        composite_input = line[0:10] + line[13:20] + line[21:43]
        composite_ok = _digit_matches(composite_input, line[_COMPOSITE_CHECK_POS])
    except ValueError as exc:
        return {"mrz_valid": False, "checks": all_false, "error": str(exc)}

    checks: MRZChecksumResults = {
        "document_number": doc_number_ok,
        "date_of_birth": dob_ok,
        "expiry_date": expiry_ok,
        "composite": composite_ok,
    }

    return {"mrz_valid": all(checks.values()), "checks": checks, "error": None}


class MRZDecodedFields(TypedDict):
    document_type: Optional[str]
    issuing_country: Optional[str]
    surname: Optional[str]
    given_names: Optional[str]
    document_number: Optional[str]
    nationality: Optional[str]
    date_of_birth: Optional[str]
    sex: Optional[str]
    date_of_expiry: Optional[str]
    personal_number: Optional[str]
    error: Optional[str]


def _strip_filler(value: str) -> str:
    return value.replace("<", "").strip()


def _normalize_sex(raw: str) -> str:
    raw = raw.strip().upper()
    return raw if raw in ("M", "F", "X") else "X"


def _empty_decoded(error: Optional[str] = None) -> MRZDecodedFields:
    return {
        "document_type": None,
        "issuing_country": None,
        "surname": None,
        "given_names": None,
        "document_number": None,
        "nationality": None,
        "date_of_birth": None,
        "sex": None,
        "date_of_expiry": None,
        "personal_number": None,
        "error": error,
    }


def decode_mrz(line1: str, line2: str) -> MRZDecodedFields:
    if not isinstance(line1, str) or not isinstance(line2, str):
        return _empty_decoded("Both mrz_line1 and mrz_line2 must be strings.")

    line1 = line1.strip().upper()
    line2 = line2.strip().upper()

    if len(line1) != _TD3_LINE_LENGTH or len(line2) != _TD3_LINE_LENGTH:
        return _empty_decoded(
            f"Both MRZ lines must be exactly {_TD3_LINE_LENGTH} characters (TD3 format); "
            f"got line1={len(line1)}, line2={len(line2)}."
        )

    document_type = _strip_filler(line1[0:2]) or None
    issuing_country = line1[2:5]
    name_field = line1[5:44]

    if "<<" in name_field:
        surname_raw, given_raw = name_field.split("<<", 1)
    else:
        surname_raw, given_raw = name_field, ""

    surname = surname_raw.replace("<", " ").strip()
    given_names = given_raw.rstrip("<").replace("<", " ").strip()

    document_number = _strip_filler(line2[_DOC_NUMBER_SLICE])
    nationality = line2[10:13]
    date_of_birth = line2[_DOB_SLICE]
    sex = _normalize_sex(line2[20])
    date_of_expiry = line2[_EXPIRY_SLICE]
    personal_number = _strip_filler(line2[28:42])

    return {
        "document_type": document_type,
        "issuing_country": issuing_country,
        "surname": surname,
        "given_names": given_names,
        "document_number": document_number,
        "nationality": nationality,
        "date_of_birth": date_of_birth,
        "sex": sex,
        "date_of_expiry": date_of_expiry,
        "personal_number": personal_number,
        "error": None,
    }


_CROSS_CHECK_FIELDS = (
    ("Document Number", "document_number", "document_number"),
    ("DOB", "dob", "date_of_birth"),
    ("Expiry", "expiry", "date_of_expiry"),
    ("Sex", "sex", "sex"),
)


def _normalize_for_compare(value: Any) -> str:
    return re.sub(r"[\s\-]", "", str(value or "")).strip().upper()


def cross_verify_viz_and_mrz(viz_data: Dict[str, Any], mrz_data: Dict[str, Any]) -> List[str]:
    mismatches: List[str] = []

    for label, viz_key, mrz_key in _CROSS_CHECK_FIELDS:
        viz_raw = viz_data.get(viz_key)
        mrz_raw = mrz_data.get(mrz_key)

        viz_value = _normalize_for_compare(viz_raw)
        mrz_value = _normalize_for_compare(mrz_raw)

        if not viz_value or not mrz_value:
            continue 

        if viz_value != mrz_value:
            mismatches.append(
                f"MISMATCH: VIZ {label} ({viz_raw}) does not match MRZ {label} ({mrz_raw})"
            )

    return mismatches