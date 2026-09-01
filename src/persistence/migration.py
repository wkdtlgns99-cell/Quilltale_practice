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
        """Upgrades legacy raw dictionary to the latest schema version."""
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

        raw_data["save_version"] = cls.CURRENT_SAVE_VERSION
        return raw_data
