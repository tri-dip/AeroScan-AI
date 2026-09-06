from __future__ import annotations

from typing import Any, Dict

from app.graph.state import ScanState



def extraction_node(state: ScanState) -> Dict[str, Any]:
    """
    AGENT: Extraction
    Turns raw image_bytes into raw OCR text, raw MRZ lines, and structured fields.
    First node in the graph - runs alone, before the parallel fan-out.
    """
    print(f"[extraction_node] processing '{state.get('file_name')}' "
          f"({len(state.get('image_bytes', b''))} bytes)")

    mock_ocr_text = (
        "REPUBLIC OF EXAMPLAND\nPASSPORT\nDOE, JOHN\n"
        "P<EXMDOE<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n"
        "L898902C36EXM7408122M1204159<<<<<<<<<<<<<06"
    )

    return {
        "ocr_raw_text": mock_ocr_text,
        "ocr_confidence": 0.94,
        "mrz_raw_lines": [
            "P<EXMDOE<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "L898902C36EXM7408122M1204159<<<<<<<<<<<<<06",
        ],
        "extracted_fields": {
            "surname": "DOE",
            "given_names": "JOHN",
            "document_number": "L898902C3",
            "nationality": "EXM",
            "date_of_birth": "1974-08-12",
            "sex": "M",
            "expiry_date": "2012-04-15",
        },
        "node_trace": ["extraction_node"],
    }