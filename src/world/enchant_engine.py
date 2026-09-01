"""
Durability & Rune Enchantment Engine for Quilltale TRPG.
Handles equipment wear & tear, blacksmith repair services,
rune socketing, and elemental on-hit/on-defend combat triggers.
"""
import os
import json
import random
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from src.world.state import WorldState, Item, Player, NPC

logger = logging.getLogger(__name__)

RUNE_TEMPLATES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "templates" / "rune_templates.json"


class EnchantEngine:
    _templates_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def load_templates(cls, path: Optional[Path] = None) -> Dict[str, Any]:
        target = path or RUNE_TEMPLATES_PATH
        if cls._templates_cache is not None and path is None:
            return cls._templates_cache

        if not os.path.exists(target):
            logger.warning(f"Rune templates not found at {target}.")
            return {"runes": []}

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._templates_cache = data
                return data
        except Exception as e:
            logger.error(f"Failed to load rune templates: {e}")
            return {"runes": []}

    @classmethod
    def socket_rune(cls, state: WorldState, item_id: str, rune_id: str) -> Tuple[bool, str]:
        """Sockets a rune into the target weapon or armor."""
        item = state.items.get(item_id)
        if not item:
            return False, "아이템을 찾을 수 없습니다."

        templates = cls.load_templates()
        rune_data = next((r for r in templates.get("runes", []) if r["id"] == rune_id), None)
        if not rune_data:
            return False, "유효하지 않은 룬 보석입니다."

        if item.item_type not in rune_data.get("applicable_types", []):
            return False, f"이 룬은 {item.item_type} 부위에 각인할 수 없습니다."

        # Ensure max 3 rune slots
        max_slots = max(1, item.rune_slots)
        if len(item.socketed_runes) >= max_slots:
            return False, f"더 이상 룬을 박을 소켓 구멍이 없습니다. (최대 {max_slots}개)"

        item.socketed_runes.append(rune_id)
        # Consume rune item if present in player inventory
        if rune_id in state.player.inventory:
            state.player.inventory.remove(rune_id)

        return True, f"✨ [룬 각인 완료] [{item.name}]에 [{rune_data['name_ko']}]을 성공적으로 결속했습니다!"

    @classmethod
    def consume_durability(cls, item: Item, loss: int = 1) -> Optional[str]:
        """Degrades durability by loss amount. Emits warning if broken."""
        item.durability = max(0, item.durability - loss)
        if item.durability == 0:
            return f"⚠️ [장비 파손 경고] [{item.name}]의 내구도가 0이 되어 성능이 50%로 격감했습니다! 대장간에서 수리가 필요합니다."
        return None

    @classmethod
    def repair_item(cls, state: WorldState, item_id: str) -> Tuple[bool, str, int]:
        """Repairs an item to full durability at the cost of gold."""
        item = state.items.get(item_id)
        if not item:
            return False, "수리할 아이템을 찾을 수 없습니다.", 0

        lost = item.max_durability - item.durability
        if lost <= 0:
            return False, "이미 완벽한 상태입니다.", 0

        cost = max(5, int(lost * 0.5))
        if state.player.gold < cost:
            return False, f"수리비가 부족합니다. (필요: {cost}G, 보유: {state.player.gold}G)", 0

        state.player.gold -= cost
        item.durability = item.max_durability
        return True, f"🔨 [수리 완료] {cost}G를 지불하고 [{item.name}]을(를) 완벽하게 수리했습니다! (내구도 100/100)", cost

    @classmethod
    def evaluate_rune_combat_effects(
        cls,
        state: WorldState,
        equipped_item: Optional[Item],
        damage_dealt: int,
        target_npc: Optional[NPC] = None
    ) -> List[str]:
        """Evaluates on-hit elemental rune effects during combat."""
        if not equipped_item or not equipped_item.socketed_runes:
            return []

        templates = cls.load_templates()
        rune_db = {r["id"]: r for r in templates.get("runes", [])}
        logs = []

        for r_id in equipped_item.socketed_runes:
            r_data = rune_db.get(r_id)
            if not r_data:
                continue

            effects = r_data.get("effects", {})
            r_name = r_data.get("name_ko", "룬")

            # Lifesteal
            if "lifesteal_ratio" in effects and damage_dealt > 0:
                heal_amt = max(1, int(damage_dealt * effects["lifesteal_ratio"]))
                state.player.health = min(state.player.max_health, state.player.health + heal_amt)
                logs.append(f"🩸 [{r_name}] 흡혈 효과로 가한 피해의 일부({heal_amt} HP)를 즉시 흡수 회복했습니다!")

            # Status effect trigger
            if "on_hit_status" in effects and target_npc and target_npc.alive:
                chance = effects.get("status_chance", 0.3)
                if random.random() < chance:
                    from src.world.status_engine import StatusEffectEngine
                    status_id = effects["on_hit_status"]
                    dur = effects.get("status_duration", 2)
                    pot = effects.get("status_potency", 2)
                    StatusEffectEngine.apply_status(target_npc, status_id, duration=dur, potency=pot)
                    logs.append(f"⚡ [{r_name}] 적에게 '{status_id}' 상태이상을 성공적으로 각인시켰습니다!")

        return logs
