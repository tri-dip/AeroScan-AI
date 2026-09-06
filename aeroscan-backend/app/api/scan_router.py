from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.graph.state import ScanState
from app.graph.workflow import scan_graph
from app.schemas.api_models import ScanResponse

router = APIRouter(prefix="/api/scan", tags=["scan"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}
MAX_FILE_SIZE_MB = 10


@router.post("/", response_model=ScanResponse)
async def scan_document(file: UploadFile = File(...)) -> ScanResponse:
    """
    Accepts a multipart/form-data image upload, runs it through the LangGraph
    multi-agent pipeline, and returns a JSON risk assessment. Raw image bytes
    are read in-memory only and are never persisted or echoed back.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Use JPEG or PNG.",
        )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(image_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit."
        )

    initial_state: ScanState = {
        "file_name": file.filename or "unknown",
        "image_bytes": image_bytes,
        "document_type": None,
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

    # CRITICAL: strip raw bytes before returning - never send document bytes back to the client
    result_state.pop("image_bytes", None)

    return ScanResponse(**result_state)