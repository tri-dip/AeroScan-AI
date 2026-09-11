from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.graph.state import ScanState
from app.graph.workflow import scan_graph
from app.schemas.api_models import ScanResponse

router = APIRouter(prefix="/api/scan", tags=["scan"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}
MAX_FILE_SIZE_MB = 10


async def _read_validated_upload(file: UploadFile, *, label: str) -> bytes:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported {label} file type: {file.content_type}. Use JPEG or PNG.",
        )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail=f"Uploaded {label} file is empty.")

    if len(image_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail=f"{label.capitalize()} file exceeds {MAX_FILE_SIZE_MB}MB limit."
        )

    return image_bytes


@router.post("/", response_model=ScanResponse)
async def scan_document(
    file: UploadFile = File(..., description="The passport/ID document image."),
    selfie: UploadFile = File(
        ..., description="A live/real-time capture of the user's face, taken on the platform."
    ),
    document_type: str | None = Form(
        None, description="Optional hint, e.g. 'passport'. Accepted and echoed back; not yet used to branch extraction logic (TD3/passport MRZ only for now)."
    ),
    station_id: str | None = Form(
        None, description="Optional caller-supplied audit/traceability tag (e.g. kiosk or checkpoint ID). Echoed back unmodified; not validated or interpreted by the backend."
    ),
) -> ScanResponse:
    """
    Accepts a multipart/form-data document image plus a live selfie capture,
    runs both through the LangGraph multi-agent pipeline (which includes a
    document-photo-vs-selfie face match), and returns a JSON risk assessment.
    Raw image bytes are read in-memory only and are never persisted or echoed back.
    """
    image_bytes = await _read_validated_upload(file, label="document")
    selfie_bytes = await _read_validated_upload(selfie, label="selfie")

    initial_state: ScanState = {
        "file_name": file.filename or "unknown",
        "image_bytes": image_bytes,
        "selfie_image_bytes": selfie_bytes,
        "document_type": document_type,
        "station_id": station_id,
        "flags": [],
        "errors": [],
        "node_trace": [],
    }

    try:
        result_state: ScanState = await scan_graph.ainvoke(initial_state)
    except Exception as exc:  # noqa: BLE001 - surface graph failures as 500s for now
        raise HTTPException(
            status_code=500, detail=f"Graph execution failed: {exc}"
        ) from exc

    # CRITICAL: strip raw bytes before returning - never send document/selfie bytes back to the client
    result_state.pop("image_bytes", None)
    result_state.pop("selfie_image_bytes", None)

    return ScanResponse(**result_state)