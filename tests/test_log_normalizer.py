"""tests/test_log_normalizer module."""

from pathlib import Path

from ingest.logs.registry import normalize_log_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalize_csv_export(tmp_path: Path):
    artifacts = normalize_log_file(FIXTURES / "sample_export.csv", tmp_path, vendor_hint="csv_export", session_id="csv-test")
    data = artifacts.normalized_csv.read_text(encoding="utf-8")
    assert "timestamp_ms" in data
    assert "speed_mps" in data
    assert "throttle_pct" in data
    assert "csv_export" in data


def test_normalize_vbox(tmp_path: Path):
    artifacts = normalize_log_file(FIXTURES / "sample.vbo", tmp_path)
    data = artifacts.normalized_csv.read_text(encoding="utf-8")
    assert "gps_lat_deg" in data
    assert "gps_lon_deg" in data
    assert "speed_mps" in data
