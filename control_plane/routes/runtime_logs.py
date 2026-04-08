from __future__ import annotations

from pathlib import Path
from typing import Any
import csv
import io
import json

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

router = APIRouter(prefix="/runtime", tags=["runtime"])

LOG_DIR = Path("runtime_logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

class RuntimeLogSummary(BaseModel):
    session_id: str
    filename: str
    rows: int
    columns: list[str]
    preview: list[dict[str, Any]] = Field(default_factory=list)

class ParseResponse(BaseModel):
    source_type: str
    summary: RuntimeLogSummary

class SessionIndexItem(BaseModel):
    session_id: str
    filename: str
    rows: int
    columns: list[str]

def _safe_session_id(name: str) -> str:
    stem = Path(name).stem
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in stem)

def _csv_summary(raw: bytes, filename: str) -> RuntimeLogSummary:
    text = raw.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    cols = reader.fieldnames or []
    session_id = _safe_session_id(filename)
    payload = {
        "session_id": session_id,
        "filename": filename,
        "rows": len(rows),
        "columns": cols,
        "preview": rows[:20],
    }
    (LOG_DIR / f"{session_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return RuntimeLogSummary(**payload)

@router.post("/logs/parse", response_model=ParseResponse)
async def parse_runtime_log(file: UploadFile = File(...)) -> ParseResponse:
    """Parse uploaded CSV/TXT runtime logs into indexed session artifacts."""
    raw = await file.read()
    if not file.filename:
        raise HTTPException(status_code=400, detail="filename required")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".csv", ".txt"}:
        raise HTTPException(status_code=415, detail="Only CSV/TXT runtime logs supported by this route")
    summary = _csv_summary(raw, file.filename)
    return ParseResponse(source_type="csv", summary=summary)

@router.get("/sessions", response_model=list[SessionIndexItem])
def list_sessions() -> list[SessionIndexItem]:
    """List parsed runtime sessions available for review."""
    items: list[SessionIndexItem] = []
    for p in sorted(LOG_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        items.append(SessionIndexItem(
            session_id=data["session_id"],
            filename=data["filename"],
            rows=data["rows"],
            columns=data["columns"],
        ))
    return items

@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    """Load full parsed runtime session payload by session identifier."""
    p = LOG_DIR / f"{session_id}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="session not found")
    return json.loads(p.read_text(encoding="utf-8"))

@router.get("/sessions/{session_id}/debrief")
def get_session_debrief(session_id: str) -> dict[str, Any]:
    """Generate a lightweight operator-facing debrief for a runtime session."""
    p = LOG_DIR / f"{session_id}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="session not found")
    data = json.loads(p.read_text(encoding="utf-8"))
    return {
        "session_id": session_id,
        "headline": "Runtime log parsed and ready for HITL review",
        "row_count": data["rows"],
        "column_count": len(data["columns"]),
        "observations": [
            "Parser currently supports CSV/TXT runtime exports through this endpoint.",
            "Native vendor normalization remains owned by /ingest/normalize.",
            "This endpoint is intended for quick GUI review of simulator output logs."
        ],
        "top_columns": data["columns"][:12],
    }
