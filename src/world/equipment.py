"""
Deterministic Equipment Engine for Quilltale TRPG.
Calculates:
1. Aggregated equipment stats and total defense (AC bonus) across all 10 slots.
2. Dynamic stat bonuses (STR, AGI, INT, CON, WIS, LUK, Crit) from weapons, armors, and accessories.
3. Body part hit mapping to equipment slots and armor durability consumption.
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
from src.world.state import WorldState, Item, Player, NPC
from src.world.enchant_engine import EnchantEngine

logger = logging.getLogger(__name__)


class EquipmentEngine:
    BODY_PART_SLOT_MAP: Dict[str, str] = {
        "머리": "head",
        "목": "head",
        "눈": "face",
        "얼굴": "face",
        "가슴": "chest",
        "몸통": "chest",
        "심장": "chest",
        "배": "chest",
        "등": "cape",
        "어깨": "cape",
        "팔": "gloves",
        "손": "gloves",
        "손목": "gloves",
        "다리": "legs",
        "무릎": "legs",
        "관절": "legs",
        "허벅지": "legs",
        "발": "boots",
        "발목": "boots"
    }

    @classmethod
    def get_equipped_items(cls, state: WorldState, entity: Any = None) -> List[Item]:
        """Returns all equipped Item objects for the entity (defaults to Player)."""
        target = entity if entity is not None else state.player
        if not hasattr(target, "equipment") or not target.equipment:
            return []

        eq = target.equipment
        single_slots = ["weapon", "head", "face", "chest", "legs", "boots", "gloves", "cape"]
        equipped_item_ids: List[str] = []

        for s in single_slots:
            item_id = getattr(eq, s, None)
            if item_id:
                equipped_item_ids.append(item_id)

        # Multi-slots (rings, earrings)
        for r_id in getattr(eq, "rings", []):
            if r_id:
                equipped_item_ids.append(r_id)
        for e_id in getattr(eq, "earrings", []):
            if e_id:
                equipped_item_ids.append(e_id)

        return [state.items[i_id] for i_id in equipped_item_ids if i_id in state.items]

    @classmethod
    def calculate_equipment_bonuses(cls, state: WorldState, entity: Any = None) -> Dict[str, Any]:
        """
        Calculates total defense, damage bonuses, and stat modifiers from all equipped items.
        """
        items = cls.get_equipped_items(state, entity)
        total_defense = 0
        total_damage = 0
        stat_bonuses: Dict[str, int] = {
            "strength": 0,
            "agility": 0,
            "intelligence": 0,
            "constitution": 0,
            "wisdom": 0,
            "luck": 0,
            "crit_rate": 0,
            "crit_damage": 0,
            "max_health": 0,
            "max_mana": 0
        }

        for item in items:
            total_defense += getattr(item, "defense", 0)
            total_damage += getattr(item, "damage", 0)

            # Check properties for stat bonuses
            props = getattr(item, "properties", {}) or {}
            item_stat_mods = props.get("stat_bonuses", {})
            if isinstance(item_stat_mods, dict):
                for stat_k, stat_v in item_stat_mods.items():
                    # Normalize key
                    norm_k = stat_k.lower()
                    if norm_k in ["str", "strength", "근력"]:
                        stat_bonuses["strength"] += int(stat_v)
                    elif norm_k in ["agi", "dex", "agility", "민첩"]:
                        stat_bonuses["agility"] += int(stat_v)
                    elif norm_k in ["int", "intelligence", "지능"]:
                        stat_bonuses["intelligence"] += int(stat_v)
                    elif norm_k in ["con", "constitution", "체력", "건강"]:
                        stat_bonuses["constitution"] += int(stat_v)
                    elif norm_k in ["wis", "wisdom", "지혜"]:
                        stat_bonuses["wisdom"] += int(stat_v)
                    elif norm_k in ["luk", "luck", "cha", "행운", "매력"]:
                        stat_bonuses["luck"] += int(stat_v)
                    elif norm_k in ["crit", "crit_rate", "치명타"]:
                        stat_bonuses["crit_rate"] += int(stat_v)
                    elif norm_k in ["crit_dmg", "crit_damage"]:
                        stat_bonuses["crit_damage"] += int(stat_v)
                    elif norm_k in ["hp", "max_hp", "max_health", "체력최대치"]:
                        stat_bonuses["max_health"] += int(stat_v)
                    elif norm_k in ["mp", "mana", "max_mana", "마나최대치"]:
                        stat_bonuses["max_mana"] += int(stat_v)

        return {
            "total_defense": total_defense,
            "total_damage": total_damage,
            "stat_bonuses": stat_bonuses,
            "equipped_count": len(items)
        }

    @classmethod
    def get_slot_for_body_part(cls, target_part: str) -> str:
        """Maps specific targeted anatomy to equipment slot."""
        clean_part = target_part.strip().lower()
        return cls.BODY_PART_SLOT_MAP.get(clean_part, "chest")

    @classmethod
    def apply_armor_durability_and_mitigation(
        cls,
        state: WorldState,
        entity: Any,
        incoming_damage: int,
        target_part: str = ""
    ) -> Tuple[int, List[str]]:
        """
        Consumes durability of the targeted armor piece and slightly mitigates damage.
        Returns (mitigated_damage: int, logs: List[str]).
        """
        logs: List[str] = []
        if not hasattr(entity, "equipment") or not entity.equipment:
            return incoming_damage, logs

        slot = cls.get_slot_for_body_part(target_part) if target_part else "chest"
        item_id = getattr(entity.equipment, slot, None)
        # Fallback to chest if specific slot is empty
        if not item_id and slot != "chest":
            item_id = getattr(entity.equipment, "chest", None)

        if not item_id or item_id not in state.items:
            return incoming_damage, logs

        armor_item = state.items[item_id]
        # Durability loss
        dur_warn = EnchantEngine.consume_durability(armor_item, loss=1)
        if dur_warn:
            logs.append(dur_warn)

        # Damage reduction based on armor defense
        armor_def = getattr(armor_item, "defense", 0)
        mitigated = max(1, incoming_damage - (armor_def // 2))
        if armor_def > 0 and incoming_damage > mitigated:
            logs.append(f"[{armor_item.name}]이(가) 충격을 흡수하여 피해 {incoming_damage - mitigated} 경감 (내구도 -1)")

        return mitigated, logs
