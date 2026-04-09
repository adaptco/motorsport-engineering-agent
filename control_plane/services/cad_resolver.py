"""control_plane/services/cad_resolver module."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from shared.forensic_ledger import sha256_prefixed
from shared.models import AeroSourceRef, AeroSimulationRunRequest


def _safe_name(value: str) -> str:
    normalized = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value.strip().lower())
    return normalized.strip("-") or "vehicle"


def _score_candidate(source: AeroSourceRef) -> int:
    score = 0
    if source.kind == "cad":
        score += 100
    elif source.kind == "public_reference":
        score += 80
    elif source.kind == "measurement":
        score += 60
    elif source.kind == "photo":
        score += 40
    elif source.kind == "solver_case":
        score += 20
    if source.label:
        score += 5
    if source.sha256:
        score += 5
    score += int(bool(source.metadata.get("licensed")))
    return score


@dataclass(frozen=True)
class CadResolution:
    requested_strategy: str
    resolved_strategy: str
    candidate_sources: list[AeroSourceRef]
    selected_source: AeroSourceRef | None
    confidence: float
    selection_reason: str
    geometry_manifest_uri: str
    geometry_manifest_sha256: str
    proxy_generated: bool
    proxy_geometry_uri: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_state_dict(self) -> dict[str, Any]:
        return {
            "requested_strategy": self.requested_strategy,
            "resolved_strategy": self.resolved_strategy,
            "candidate_sources": [source.model_dump(mode="json") for source in self.candidate_sources],
            "selected_source": self.selected_source.model_dump(mode="json") if self.selected_source else None,
            "confidence": self.confidence,
            "selection_reason": self.selection_reason,
            "geometry_manifest_uri": self.geometry_manifest_uri,
            "geometry_manifest_sha256": self.geometry_manifest_sha256,
            "proxy_generated": self.proxy_generated,
            "proxy_geometry_uri": self.proxy_geometry_uri,
            "notes": list(self.notes),
        }


def _candidate_sources(source_refs: Iterable[AeroSourceRef]) -> list[AeroSourceRef]:
    return [source for source in source_refs if source.kind != "telemetry"]


def _write_json_manifest(path: Path, payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text(serialized, encoding="utf-8")
    return sha256_prefixed(payload)


def resolve_cad_candidate(req: AeroSimulationRunRequest, *, run_id: str, case_dir: Path) -> CadResolution:
    geometry_dir = case_dir / "geometry"
    geometry_dir.mkdir(parents=True, exist_ok=True)

    candidate_sources = _candidate_sources(req.source_refs)
    cad_candidates = [source for source in candidate_sources if source.kind == "cad"]
    selected_source = max(cad_candidates, key=_score_candidate) if cad_candidates else None

    if selected_source is not None:
        resolved_strategy = "public_cad"
        confidence = 0.88
        proxy_generated = False
        proxy_geometry_uri = None
        selection_reason = (
            f"Selected {selected_source.label or selected_source.uri} from {len(cad_candidates)} CAD candidate(s) "
            f"for run {run_id}."
        )
        notes = [
            "CAD source resolved from supplied inputs.",
            "Adapter should prefer snappyHexMesh-style workflows for this branch.",
        ]
    else:
        resolved_strategy = "proxy_geometry"
        confidence = 0.52
        proxy_generated = True
        proxy_manifest_path = geometry_dir / "proxy_geometry.json"
        proxy_geometry_payload = {
            "run_id": run_id,
            "vehicle_identity": req.vehicle_identity.model_dump(mode="json"),
            "dimensions": req.metadata.get("dimensions", {}),
            "aero_targets": req.metadata.get("aero_targets", {}),
            "parametric_overrides": req.metadata.get("parametric_overrides", {}),
            "notes": req.metadata.get("proxy_geometry_notes", []),
        }
        proxy_geometry_uri = str(proxy_manifest_path)
        _write_json_manifest(proxy_manifest_path, proxy_geometry_payload)
        selection_reason = "No CAD source was supplied, so a proxy geometry scaffold was generated from vehicle metadata."
        notes = [
            "No CAD input found; falling back to a proxy geometry branch.",
            "Proxy branch remains linked to the same durable aero run.",
        ]

    manifest_path = geometry_dir / "cad_resolution.json"
    manifest_payload = {
        "run_id": run_id,
        "requested_strategy": req.baseline_geometry_strategy,
        "resolved_strategy": resolved_strategy,
        "candidate_sources": [source.model_dump(mode="json") for source in candidate_sources],
        "selected_source": selected_source.model_dump(mode="json") if selected_source else None,
        "confidence": confidence,
        "selection_reason": selection_reason,
        "proxy_generated": proxy_generated,
        "proxy_geometry_uri": proxy_geometry_uri,
        "notes": notes,
    }
    manifest_sha = _write_json_manifest(manifest_path, manifest_payload)

    return CadResolution(
        requested_strategy=req.baseline_geometry_strategy,
        resolved_strategy=resolved_strategy,
        candidate_sources=candidate_sources,
        selected_source=selected_source,
        confidence=confidence,
        selection_reason=selection_reason,
        geometry_manifest_uri=str(manifest_path),
        geometry_manifest_sha256=manifest_sha,
        proxy_generated=proxy_generated,
        proxy_geometry_uri=proxy_geometry_uri,
        notes=notes,
    )
