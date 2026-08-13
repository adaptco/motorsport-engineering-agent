# API Guide

## Health

### `GET /healthz`
Returns service version heartbeat.

### `GET /healthz/dependencies`
Returns DB pool and ledger dependency status.

## Ingest

### `GET /ingest/sources`
Lists known ingest parsers and readiness.

### `POST /ingest/normalize`
Normalizes a native telemetry export.

Example:
```bash
curl -X POST http://localhost:8000/ingest/normalize \
  -H "Content-Type: application/json" \
  -d '{
    "input_path":"tests/fixtures/sample_export.csv",
    "output_dir":".mea_tmp/normalized",
    "vendor_hint":"csv_export"
  }'
```

## Runtime Logs

### `POST /runtime/logs/parse`
Parses runtime CSV/TXT logs for quick HITL review.

### `GET /runtime/sessions`
Lists parsed sessions.

### `GET /runtime/sessions/{session_id}/debrief`
Returns debrief summary for a parsed session.

## Jobs

### `POST /repos/fix-ci`
Queues CI-fix job.

### `GET /jobs/{job_id}`
Fetches current job status.
