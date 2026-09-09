"""Compatibility helpers for wiring the psychology layer into existing WorldState.

The existing state.py intentionally remains the owner of the current WorldState/NPC
schema. These helpers attach the new psychological state to each NPC at runtime and
provide explicit persistence boundaries so callers can include the state in the
existing WorldState JSON rather than creating a second save system.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

from .npc_psychology_engine import (
    NPCPsychologicalState,
    PsychologyEngine,
    psychology_from_worldstate_dict,
    psychology_to_worldstate_dict,
)


def ensure_worldstate_psychology(world_state: Any, engine: PsychologyEngine | None = None) -> PsychologyEngine:
    """Attach one psychology state to every existing NPC without replacing legacy fields."""
    engine = engine or PsychologyEngine()
    for npc in getattr(world_state, "npcs", {}).values():
        if getattr(npc, "alive", True):
            engine.ensure_npc(npc)
    return engine


def export_npc_psychology(npc: Any) -> Dict[str, Any]:
    """Return the persistent psychology payload for an existing NPC."""
    return psychology_to_worldstate_dict(npc)


def import_npc_psychology(npc: Any, payload: Mapping[str, Any]) -> NPCPsychologicalState:
    """Restore psychology from an NPC's existing WorldState JSON payload."""
    return psychology_from_worldstate_dict(npc, payload)


def export_all_psychology(world_state: Any) -> Dict[str, Dict[str, Any]]:
    """Build an NPC-id keyed payload suitable for an existing WorldState serializer."""
    return {
        npc_id: export_npc_psychology(npc)
        for npc_id, npc in getattr(world_state, "npcs", {}).items()
        if isinstance(getattr(npc, "psychology", None), NPCPsychologicalState)
    }


def import_all_psychology(world_state: Any, payload: Mapping[str, Any]) -> None:
    """Restore only known NPC psychology payloads; unknown NPC IDs are ignored."""
    if not isinstance(payload, Mapping):
        return
    for npc_id, npc_payload in payload.items():
        npc = getattr(world_state, "npcs", {}).get(npc_id)
        if npc is not None and isinstance(npc_payload, Mapping):
            import_npc_psychology(npc, npc_payload)


__all__ = [
    "ensure_worldstate_psychology",
    "export_npc_psychology",
    "import_npc_psychology",
    "export_all_psychology",
    "import_all_psychology",
]
