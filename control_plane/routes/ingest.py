from __future__ import annotations

from fastapi import APIRouter

from ingest.logs import normalize_log_file, parser_statuses
from shared.models import IngestNormalizeRequest, IngestNormalizeResponse, IngestSourceStatus

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.get("/sources", response_model=list[IngestSourceStatus])
def list_ingest_sources():
    """List available ingest parsers and their readiness state."""
    return [IngestSourceStatus(**item) for item in parser_statuses()]


@router.post("/normalize", response_model=IngestNormalizeResponse)
def normalize_native_log(request: IngestNormalizeRequest):
    """Normalize a native telemetry file into canonical ingest artifacts."""
    artifacts = normalize_log_file(
        input_path=request.input_path,
        output_dir=request.output_dir,
        vendor_hint=request.vendor_hint,
        session_id=request.session_id,
    )
    return IngestNormalizeResponse(
        status="complete",
        vendor=artifacts.vendor,
        input_path=str(artifacts.input_path),
        output_dir=str(artifacts.output_dir),
        normalized_csv=str(artifacts.normalized_csv),
        channel_manifest_csv=str(artifacts.channel_manifest_csv),
        session_manifest_json=str(artifacts.session_manifest_json),
        row_count=artifacts.row_count,
        column_count=artifacts.column_count,
        canonical_columns=artifacts.canonical_columns,
        notes=artifacts.notes,
    )
