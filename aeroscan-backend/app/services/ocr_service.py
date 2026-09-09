from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

GEMINI_MODEL = "gemini-3.5-flash"
REQUEST_TIMEOUT_SECONDS = 30
_EXPECTED_MRZ_LINE_LENGTH = 44


class OCRExtractionError(Exception):
    pass


class DocumentExtraction(BaseModel):
    viz_first_name: str = Field(
        ...,
        description="Given name(s) exactly as printed on the visual data page (NOT read from the MRZ).",
    )
    viz_last_name: str = Field(
        ...,
        description="Surname exactly as printed on the visual data page (NOT read from the MRZ).",
    )
    viz_document_number: str = Field(
        ...,
        description="Document/passport number exactly as printed on the visual data page (NOT read from the MRZ).",
    )
    viz_dob: str = Field(
        ...,
        description="Date of birth as printed on the visual data page, converted to YYMMDD format. Read from the printed date, NOT from the MRZ.",
    )
    viz_expiry: str = Field(
        ...,
        description="Expiry date as printed on the visual data page, converted to YYMMDD format. Read from the printed date, NOT from the MRZ.",
    )
    viz_sex: str = Field(
        ...,
        description="Sex exactly as printed on the visual data page: 'M', 'F', or 'X'. NOT read from the MRZ.",
    )
    mrz_line1: str = Field(
        ...,
        description="Exact first line of the Machine Readable Zone (MRZ), transcribed character-for-character including every '<' filler character. 44 characters for a TD3 (passport) document.",
    )
    mrz_line2: str = Field(
        ...,
        description="Exact second line of the Machine Readable Zone (MRZ), transcribed character-for-character including every '<' filler character. 44 characters for a TD3 (passport) document.",
    )


_EXTRACTION_PROMPT = (
    "You are analyzing a scanned identity document (passport or national ID) for a "
    "border-security screening system. This system's core function is cross-checking "
    "the printed data page against the Machine Readable Zone (MRZ) to detect tampering "
    "- so you MUST read both zones INDEPENDENTLY AND FAITHFULLY, even if they appear to "
    "disagree with each other.\n\n"
    "1) VISUAL INSPECTION ZONE (VIZ): Read the printed, human-readable fields on the "
    "data page - given name(s), surname, document number, date of birth, expiry date, "
    "and sex. Convert both dates to YYMMDD format. Read these values from the printed "
    "text itself - do NOT copy or infer them from the MRZ.\n\n"
    "2) MACHINE READABLE ZONE (MRZ): Transcribe the 2-line MRZ printed at the bottom of "
    "the document EXACTLY as printed, character for character, including every '<' "
    "filler character. Do NOT correct, normalize, or reconcile it with the VIZ fields - "
    "transcribe exactly what is visually present, even if it looks like it contains an "
    "error.\n\n"
    "CRITICAL: If the VIZ and MRZ appear inconsistent with each other (different dates, "
    "different names, different numbers), transcribe BOTH exactly as printed anyway. Do "
    "NOT silently correct one zone to match the other. A disagreement between the two "
    "zones is exactly the kind of tampering this system exists to catch - 'fixing' it in "
    "your transcription would hide the fraud instead of surfacing it."
)


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise OCRExtractionError(
            "GEMINI_API_KEY is not set. Add it to your environment or .env file before calling extract_document_data()."
        )
    return genai.Client(api_key=api_key)


def _guess_mime_type(image_bytes: bytes) -> str:
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


async def extract_document_data(image_bytes: bytes) -> Dict[str, Any]:
    if not image_bytes:
        raise OCRExtractionError("Received empty image bytes - nothing to analyze.")

    client = _get_client()
    mime_type = _guess_mime_type(image_bytes)

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=[
                    _EXTRACTION_PROMPT,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=DocumentExtraction,
                    temperature=0.0,
                ),
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise OCRExtractionError(
            f"Gemini API call timed out after {REQUEST_TIMEOUT_SECONDS}s."
        ) from exc
    except Exception as exc:
        raise OCRExtractionError(f"Gemini API call failed: {exc}") from exc

    result = _parse_and_validate(response)
    return result.model_dump()


def _parse_and_validate(response: Any) -> DocumentExtraction:
    parsed: Optional[Any] = getattr(response, "parsed", None)

    if parsed is None:
        finish_reason = getattr(response, "finish_reason", "unknown")
        raise OCRExtractionError(
            f"Gemini did not return a parseable structured response (finish_reason={finish_reason}). "
            "The document may be unreadable, or the MRZ may be absent from the image."
        )

    try:
        result = (
            parsed
            if isinstance(parsed, DocumentExtraction)
            else DocumentExtraction.model_validate(parsed)
        )
    except ValidationError as exc:
        raise OCRExtractionError(f"Gemini response failed schema validation: {exc}") from exc

    if (
        len(result.mrz_line1) != _EXPECTED_MRZ_LINE_LENGTH
        or len(result.mrz_line2) != _EXPECTED_MRZ_LINE_LENGTH
    ):
        raise OCRExtractionError(
            "Extracted MRZ lines are not the expected 44 characters "
            f"(line1={len(result.mrz_line1)}, line2={len(result.mrz_line2)}). "
            "Document may be blurry, cropped, or not a TD3-format (2-line) passport."
        )

    return result