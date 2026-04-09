"""control_plane/services/session_receipts module."""

from __future__ import annotations

from typing import Iterable

from shared.models import EvidencePacket, Recommendation


def build_state_surface(packet: EvidencePacket, recommendations: Iterable[Recommendation]) -> dict:
    return {
        "evidence": packet.model_dump(mode="json"),
        "recommendations": [rec.model_dump(mode="json") for rec in recommendations],
    }
