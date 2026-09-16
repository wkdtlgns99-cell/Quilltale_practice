"""
Save Schema Migration & Auto-Healer for Quilltale TRPG.
Ensures legacy world state saves are gracefully upgraded to the latest format
without throwing missing key errors or breaking gameplay.
"""
from typing import Dict, Any


class SaveMigrationEngine:
    CURRENT_SAVE_VERSION = 3

    @classmethod
    def migrate(cls, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrades legacy raw dictionary to the latest schema version and sanitizes oversized lists."""
        save_ver = raw_data.get("save_version", 1)

        # v1 -> v2: Party and Bounties
        if save_ver < 2:
            if "party" not in raw_data:
                raw_data["party"] = {}
            if "player" in raw_data and "bounties" not in raw_data["player"]:
                raw_data["player"]["bounties"] = {}
            save_ver = 2

        # v2 -> v3: Visual profiles, puzzles, durability, runes
        if save_ver < 3:
            for npc_id, npc_data in raw_data.get("npcs", {}).items():
                if isinstance(npc_data, dict) and "visual" not in npc_data:
                    npc_data["visual"] = {
                        "species": "인간",
                        "life_stage": "성인",
                        "build_archetype": "보통 체형",
                        "height_cm": 175
                    }
            for item_id, item_data in raw_data.get("items", {}).items():
                if isinstance(item_data, dict):
                    if "durability" not in item_data:
                        item_data["durability"] = 100
                        item_data["max_durability"] = 100
                    if "socketed_runes" not in item_data:
                        item_data["socketed_runes"] = []
            if "puzzles" not in raw_data:
                raw_data["puzzles"] = {}
            if "celestial_phase" not in raw_data:
                raw_data["celestial_phase"] = "normal"
            save_ver = 3

        # List sanitization & archive excess history to SQLite (applied to all saves during migration/load)
        # 1. world_facts: cap at 30
        if "world_facts" in raw_data and isinstance(raw_data["world_facts"], list):
            if len(raw_data["world_facts"]) > 30:
                raw_data["world_facts"] = raw_data["world_facts"][-30:]

        # 2. off_screen_logs per NPC: cap at 10
        for npc_id, npc_data in raw_data.get("npcs", {}).items():
            if isinstance(npc_data, dict) and "off_screen_logs" in npc_data:
                if isinstance(npc_data["off_screen_logs"], list) and len(npc_data["off_screen_logs"]) > 10:
                    npc_data["off_screen_logs"] = npc_data["off_screen_logs"][-10:]

        # 3. physical_traces per location: cap at 10
        for loc_id, loc_data in raw_data.get("locations", {}).items():
            if isinstance(loc_data, dict) and "physical_traces" in loc_data:
                if isinstance(loc_data["physical_traces"], list) and len(loc_data["physical_traces"]) > 10:
                    loc_data["physical_traces"] = loc_data["physical_traces"][-10:]

        # 4. history: archive excess (> 50) turns to SQLite and retain last 50
        history = raw_data.get("history", [])
        if isinstance(history, list) and len(history) > 50:
            excess = history[:-50]
            world_id = raw_data.get("world_id") or raw_data.get("session_id", "default_world")
            try:
                from src.world.persistence import PersistenceManager
                PersistenceManager.archive_turns(world_id, excess)
            except Exception:
                pass
            raw_data["history"] = history[-50:]

        raw_data["save_version"] = cls.CURRENT_SAVE_VERSION
        return raw_data
