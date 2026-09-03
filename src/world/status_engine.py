"""
Deterministic Status Effect Engine for Quilltale TRPG Engine.
Manages turn-based tick damage, healing, stat modifications, action blocks (stun/freeze),
duration decay, stacking, and deterministic cure conditions for Player and NPCs.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import copy


@dataclass
class StatusEffect:
    id: str
    name: str                               # Korean display name
    effect_type: str = "damage_tick"        # "damage_tick" | "heal_tick" | "stat_mod" | "action_block"
    damage_per_turn: int = 0
    heal_per_turn: int = 0
    mana_drain_per_turn: int = 0
    durability_damage_per_turn: int = 0
    stat_modifiers: Dict[str, int] = field(default_factory=dict)
    duration_turns: int = 3                 # Remaining turns (0 or negative = expired, -1 = infinite until cured)
    stacks: int = 1
    max_stacks: int = 5
    is_action_block: bool = False           # True for stun, freeze, paralysis (prevents physical actions)
    cure_conditions: List[str] = field(default_factory=list) # e.g. ["antidote", "heal", "bandage"]
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "effect_type": self.effect_type,
            "damage_per_turn": self.damage_per_turn,
            "heal_per_turn": self.heal_per_turn,
            "mana_drain_per_turn": self.mana_drain_per_turn,
            "durability_damage_per_turn": self.durability_damage_per_turn,
            "stat_modifiers": self.stat_modifiers,
            "duration_turns": self.duration_turns,
            "stacks": self.stacks,
            "max_stacks": self.max_stacks,
            "is_action_block": self.is_action_block,
            "cure_conditions": self.cure_conditions,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StatusEffect":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            effect_type=data.get("effect_type", "damage_tick"),
            damage_per_turn=int(data.get("damage_per_turn", 0)),
            heal_per_turn=int(data.get("heal_per_turn", 0)),
            mana_drain_per_turn=int(data.get("mana_drain_per_turn", 0)),
            durability_damage_per_turn=int(data.get("durability_damage_per_turn", 0)),
            stat_modifiers=dict(data.get("stat_modifiers", {})),
            duration_turns=int(data.get("duration_turns", 3)),
            stacks=int(data.get("stacks", 1)),
            max_stacks=int(data.get("max_stacks", 5)),
            is_action_block=bool(data.get("is_action_block", False)),
            cure_conditions=list(data.get("cure_conditions", [])),
            description=data.get("description", ""),
        )


# Standard Built-in Status Presets
STATUS_PRESETS: Dict[str, Dict[str, Any]] = {
    "poison": {
        "name": "맹독",
        "effect_type": "damage_tick",
        "damage_per_turn": 5,
        "duration_turns": 3,
        "max_stacks": 5,
        "cure_conditions": ["antidote", "cure_poison", "rest_long", "해독제", "해독"],
        "description": "체내에 퍼진 독소로 인해 매 턴 피해를 입습니다.",
    },
    "bleed": {
        "name": "과다출혈",
        "effect_type": "damage_tick",
        "damage_per_turn": 4,
        "duration_turns": 3,
        "max_stacks": 5,
        "cure_conditions": ["bandage", "heal_spell", "붕대", "지혈", "치료"],
        "description": "상처가 벌어져 매 턴 피를 흘리며 체력이 감소합니다.",
    },
    "burn": {
        "name": "작열 화상",
        "effect_type": "damage_tick",
        "damage_per_turn": 6,
        "durability_damage_per_turn": 1,
        "duration_turns": 2,
        "max_stacks": 3,
        "cure_conditions": ["water", "ice_spell", "물", "소화", "냉기"],
        "description": "신체가 불타며 매 턴 화염 지속 피해를 입고 방어구 내구도가 손상됩니다.",
    },
    "freeze": {
        "name": "동결",
        "effect_type": "action_block",
        "is_action_block": True,
        "duration_turns": 1,
        "stat_modifiers": {"agility": -6},
        "cure_conditions": ["fire_spell", "warmth", "화염", "온기"],
        "description": "극심한 한기로 전신이 얼어붙어 행동할 수 없습니다.",
    },
    "stun": {
        "name": "기절",
        "effect_type": "action_block",
        "is_action_block": True,
        "duration_turns": 1,
        "cure_conditions": [],
        "description": "강한 충격으로 정신을 잃어 이번 턴 행동이 불가합니다.",
    },
    "unconscious": {
        "name": "의식불명(혼수)",
        "effect_type": "action_block",
        "is_action_block": True,
        "duration_turns": 30,
        "cure_conditions": ["wake_up", "water", "heal", "찬물", "치료", "소생", "뺨때리기"],
        "description": "비살상 타격이나 치명타로 정신을 잃고 쓰러졌습니다. 깨어나기 전까지 모든 행동과 이동이 불가능합니다.",
    },
    "bound": {
        "name": "포박(결박)",
        "effect_type": "action_block",
        "is_action_block": True,
        "duration_turns": -1,  # Infinite until untied or cut
        "stat_modifiers": {"agility": -10},
        "cure_conditions": ["cut_rope", "untie", "break_chains", "밧줄자르기", "풀기", "해제", "열쇠"],
        "description": "밧줄, 쇠사슬, 마나 수갑으로 사지가 결박되었습니다. 이동 및 무기/마법 사용이 불가능합니다.",
    },
    "paralysis": {
        "name": "감전 마비",
        "effect_type": "action_block",
        "is_action_block": True,
        "duration_turns": 1,
        "stat_modifiers": {"agility": -4},
        "cure_conditions": ["grounding", "접지"],
        "description": "전류가 신경계를 마비시켜 몸을 통제할 수 없습니다.",
    },
    "fracture": {
        "name": "골절",
        "effect_type": "stat_mod",
        "duration_turns": 5,
        "stat_modifiers": {"strength": -3, "agility": -3},
        "cure_conditions": ["splint", "heal_spell", "rest_long", "부목", "정골", "고위치유"],
        "description": "뼈가 부러져 완력과 기동력이 크게 감소합니다.",
    },
    "exhaustion": {
        "name": "탈진",
        "effect_type": "stat_mod",
        "duration_turns": 3,
        "stat_modifiers": {"strength": -2, "agility": -2, "intelligence": -2},
        "cure_conditions": ["food", "rest", "potion", "음식", "휴식", "활력포션"],
        "description": "체력이 고갈되어 모든 신체 및 마법 능력이 둔화됩니다.",
    },
    "empower": {
        "name": "전투 고양",
        "effect_type": "stat_mod",
        "duration_turns": 3,
        "stat_modifiers": {"strength": 4, "crit_rate_bonus": 2},
        "cure_conditions": [],
        "description": "투지가 솟구쳐 공격력과 치명타 확률이 상승합니다.",
    },
    "shield": {
        "name": "마력 방호막",
        "effect_type": "stat_mod",
        "duration_turns": 3,
        "stat_modifiers": {"constitution": 4},
        "cure_conditions": [],
        "description": "압축된 마력 장벽이 가해지는 충격을 흡수합니다.",
    },
    "regen": {
        "name": "생명 재생",
        "effect_type": "heal_tick",
        "heal_per_turn": 6,
        "duration_turns": 3,
        "cure_conditions": [],
        "description": "생명력이 고속 순환하며 매 턴 체력이 회복됩니다.",
    },
    "blind": {
        "name": "실명",
        "effect_type": "stat_mod",
        "duration_turns": 2,
        "stat_modifiers": {"agility": -5},
        "cure_conditions": ["eye_wash", "세안", "치료"],
        "description": "시야가 완전히 차단되어 명중과 회피가 극단적으로 저하됩니다.",
    },
    "corrosion": {
        "name": "방어구 부식",
        "effect_type": "stat_mod",
        "damage_per_turn": 2,
        "durability_damage_per_turn": 2,
        "duration_turns": 3,
        "stat_modifiers": {"constitution": -3},
        "cure_conditions": ["repair", "수리", "중화"],
        "description": "강산에 의해 방어구와 피부가 녹아내려 내구도와 방어력이 약화됩니다.",
    },
    "curse": {
        "name": "사악한 저주",
        "effect_type": "damage_tick",
        "damage_per_turn": 5,
        "mana_drain_per_turn": 5,
        "durability_damage_per_turn": 0,
        "duration_turns": 4,
        "max_stacks": 3,
        "stat_modifiers": {"strength": -2, "agility": -2, "intelligence": -2},
        "cure_conditions": ["holy_water", "dispel", "purify", "성수", "정화", "디스펠", "축복"],
        "description": "부정한 저주가 육체와 영혼을 좀먹어 매 턴 체력과 마나를 흡수하고 전신 능력을 저하시킵니다.",
    },
}


class StatusEffectEngine:
    """
    Pure Python Status Effect Manager.
    Resolves tick damage, stat penalties, action blocking, and duration decay deterministically.
    """

    @classmethod
    def create_status(
        cls,
        status_id: str,
        duration: Optional[int] = None,
        potency: Optional[int] = None,
        stacks: int = 1,
    ) -> StatusEffect:
        """Instantiate a StatusEffect from builtin preset or custom config."""
        preset = STATUS_PRESETS.get(status_id, {})
        name = preset.get("name", status_id)
        effect_type = preset.get("effect_type", "damage_tick")
        damage_per_turn = potency if (potency is not None and effect_type == "damage_tick") else preset.get("damage_per_turn", 0)
        heal_per_turn = potency if (potency is not None and effect_type == "heal_tick") else preset.get("heal_per_turn", 0)
        mana_drain = preset.get("mana_drain_per_turn", 0)
        durability_damage = preset.get("durability_damage_per_turn", 0)
        stat_modifiers = copy.deepcopy(preset.get("stat_modifiers", {}))
        dur = duration if duration is not None else preset.get("duration_turns", 3)
        max_s = preset.get("max_stacks", 5)
        is_block = preset.get("is_action_block", False)
        cure_cond = list(preset.get("cure_conditions", []))
        desc = preset.get("description", "")

        return StatusEffect(
            id=status_id,
            name=name,
            effect_type=effect_type,
            damage_per_turn=damage_per_turn,
            heal_per_turn=heal_per_turn,
            mana_drain_per_turn=mana_drain,
            durability_damage_per_turn=durability_damage,
            stat_modifiers=stat_modifiers,
            duration_turns=dur,
            stacks=min(stacks, max_s),
            max_stacks=max_s,
            is_action_block=is_block,
            cure_conditions=cure_cond,
            description=desc,
        )

    @classmethod
    def apply_status(
        cls,
        target: Any,
        status_id_or_obj: Any,
        duration: Optional[int] = None,
        potency: Optional[int] = None,
        stacks: int = 1,
    ) -> str:
        """
        Applies or stacks a status effect onto a Player or NPC.
        Returns a human-readable confirmation message in Korean.
        """
        if not hasattr(target, "status_effects"):
            target.status_effects = {}

        if isinstance(status_id_or_obj, StatusEffect):
            status = copy.deepcopy(status_id_or_obj)
        else:
            status = cls.create_status(str(status_id_or_obj), duration, potency, stacks)

        target_name = getattr(target, "name", "대상")

        if status.id in target.status_effects:
            existing = target.status_effects[status.id]
            # Stack up
            existing.stacks = min(existing.max_stacks, existing.stacks + status.stacks)
            # Refresh duration if new is longer
            if status.duration_turns > existing.duration_turns:
                existing.duration_turns = status.duration_turns
            return f"[{target_name}] '{existing.name}' 상태가 중첩되었습니다. (현재 {existing.stacks}중첩 / 지속 {existing.duration_turns}턴)"
        else:
            target.status_effects[status.id] = status
            return f"[{target_name}] '{status.name}' 상태이상이 부여되었습니다. (지속 {status.duration_turns}턴)"

    @classmethod
    def has_status(cls, target: Any, status_id: str) -> bool:
        """Returns True if target currently has the active status effect."""
        if hasattr(target, "status_effects") and target.status_effects:
            return any(s_id == status_id or getattr(s, "id", "") == status_id for s_id, s in target.status_effects.items() if getattr(s, "duration_turns", 0) > 0)
        return False

    @classmethod
    def remove_status(cls, target: Any, status_id: str) -> bool:
        """Removes a status effect completely from target."""
        if hasattr(target, "status_effects") and status_id in target.status_effects:
            del target.status_effects[status_id]
            return True
        return False

    @classmethod
    def cure_by_condition(cls, target: Any, cure_tag: str) -> List[str]:
        """
        Cures all status effects matching the cure condition tag.
        Returns list of cured status names.
        """
        if not hasattr(target, "status_effects") or not target.status_effects:
            return []

        cured = []
        to_delete = []
        cure_lower = cure_tag.lower()

        for s_id, status in target.status_effects.items():
            if any(c.lower() in cure_lower or cure_lower in c.lower() for c in status.cure_conditions):
                cured.append(status.name)
                to_delete.append(s_id)

        for s_id in to_delete:
            del target.status_effects[s_id]

        return cured

    @classmethod
    def can_act(cls, target: Any) -> Tuple[bool, str]:
        """
        Checks if target is blocked from performing actions due to stun/freeze/paralysis.
        Returns (can_act: bool, reason_ko: str).
        """
        if not hasattr(target, "status_effects") or not target.status_effects:
            return True, ""

        for status in target.status_effects.values():
            if status.is_action_block and status.duration_turns > 0:
                return False, f"[{status.name}] 상태로 인해 몸을 움직일 수 없습니다! (남은 지속: {status.duration_turns}턴)"

        return True, ""

    @classmethod
    def get_effective_stat_modifiers(cls, target: Any) -> Dict[str, int]:
        """Calculates total net stat modifiers from all active status effects."""
        total_mods: Dict[str, int] = {}
        if not hasattr(target, "status_effects") or not target.status_effects:
            return total_mods

        for status in target.status_effects.values():
            if status.duration_turns <= 0:
                continue
            multiplier = status.stacks if status.effect_type == "damage_tick" else 1
            for stat, val in status.stat_modifiers.items():
                total_mods[stat] = total_mods.get(stat, 0) + (val * multiplier)

        return total_mods

    @classmethod
    def process_turn_ticks(cls, state: Any) -> Dict[str, Any]:
        """
        Executes Step 1 of the deterministic turn pipeline:
        Applies tick damage, tick healing, duration decrement, and cleanup for Player and NPCs.
        Returns detailed logs and summary dict.
        """
        logs: List[str] = []
        player_dmg_total = 0
        player_heal_total = 0

        # 1. Process Player
        player = state.player
        if not hasattr(player, "status_effects"):
            player.status_effects = {}

        player_expired: List[str] = []
        for s_id, status in list(player.status_effects.items()):
            # Apply tick damage
            if status.effect_type == "damage_tick" and status.damage_per_turn > 0:
                tick_dmg = status.damage_per_turn * status.stacks
                player.health = max(0, player.health - tick_dmg)
                player_dmg_total += tick_dmg
                logs.append(f"🩸 [{status.name}] 지속 피해로 체력 {tick_dmg} 소모 (남은 체력: {player.health}/{player.max_health})")

            # Apply tick healing
            elif status.effect_type == "heal_tick" and status.heal_per_turn > 0:
                tick_heal = status.heal_per_turn * status.stacks
                player.health = min(player.max_health, player.health + tick_heal)
                player_heal_total += tick_heal
                logs.append(f"✨ [{status.name}] 지속 회복으로 체력 +{tick_heal} 회복 (현재 체력: {player.health}/{player.max_health})")

            # Apply mana drain (e.g. curse)
            if getattr(status, "mana_drain_per_turn", 0) > 0:
                drain = status.mana_drain_per_turn * status.stacks
                player.mana = max(0, player.mana - drain)
                logs.append(f"🔮 [{status.name}] 영혼 잠식으로 마나 {drain} 소모 (남은 마나: {player.mana}/{player.max_mana})")

            # Apply durability loss to armor (e.g. burn, corrosion)
            if getattr(status, "durability_damage_per_turn", 0) > 0 and hasattr(state, "items"):
                dur_loss = status.durability_damage_per_turn * status.stacks
                chest_id = getattr(player.equipment, "chest", None) if hasattr(player, "equipment") else None
                if chest_id and chest_id in state.items:
                    armor_item = state.items[chest_id]
                    from src.world.enchant_engine import EnchantEngine
                    warn = EnchantEngine.consume_durability(armor_item, loss=dur_loss)
                    logs.append(f"🔥 [{status.name}] 지속 침식으로 [{armor_item.name}] 내구도 -{dur_loss} 손상")
                    if warn:
                        logs.append(warn)

            # Decrement duration (if not infinite -1)
            if status.duration_turns > 0:
                status.duration_turns -= 1
                if status.duration_turns == 0:
                    player_expired.append(s_id)

        for s_id in player_expired:
            exp_name = player.status_effects[s_id].name
            del player.status_effects[s_id]
            logs.append(f"🕊️ [{exp_name}] 지속시간이 만료되어 해제되었습니다.")

        # 2. Process Present NPCs
        curr_loc = state.current_location() if hasattr(state, "current_location") else None
        present_npc_ids = curr_loc.npcs if curr_loc else []

        for npc_id in present_npc_ids:
            if npc_id not in state.npcs:
                continue
            npc = state.npcs[npc_id]
            if not npc.alive:
                continue
            if not hasattr(npc, "status_effects"):
                npc.status_effects = {}

            npc_expired: List[str] = []
            for s_id, status in list(npc.status_effects.items()):
                if status.effect_type == "damage_tick" and status.damage_per_turn > 0:
                    tick_dmg = status.damage_per_turn * status.stacks
                    npc.health = max(0, npc.health - tick_dmg)
                    logs.append(f"⚔️ [{npc.name}] '{status.name}' 피해로 HP -{tick_dmg} (남은 HP: {npc.health}/{npc.max_health})")
                    if npc.health <= 0:
                        npc.alive = False
                        logs.append(f"💀 [{npc.name}] 상태이상 지속 피해로 사망하였습니다.")

                elif status.effect_type == "heal_tick" and status.heal_per_turn > 0:
                    tick_heal = status.heal_per_turn * status.stacks
                    npc.health = min(npc.max_health, npc.health + tick_heal)
                    logs.append(f"💚 [{npc.name}] '{status.name}' 효과로 HP +{tick_heal}")

                # Apply mana drain (e.g. curse)
                if getattr(status, "mana_drain_per_turn", 0) > 0:
                    drain = status.mana_drain_per_turn * status.stacks
                    npc.mana = max(0, npc.mana - drain)
                    logs.append(f"🔮 [{npc.name}] '{status.name}' 잠식으로 마나 -{drain}")

                if status.duration_turns > 0:
                    status.duration_turns -= 1
                    if status.duration_turns == 0:
                        npc_expired.append(s_id)

            for s_id in npc_expired:
                exp_name = npc.status_effects[s_id].name
                del npc.status_effects[s_id]
                logs.append(f"[{npc.name}] '{exp_name}' 효과가 종료되었습니다.")

        can_player_act, block_reason = cls.can_act(player)

        return {
            "logs": logs,
            "player_damage": player_dmg_total,
            "player_healed": player_heal_total,
            "can_act": can_player_act,
            "block_reason": block_reason,
        }

    @classmethod
    def format_status_for_html(cls, target: Any) -> str:
        """Generates crisp high-contrast HTML badges for UI display."""
        if not hasattr(target, "status_effects") or not target.status_effects:
            return "<span style='color:#718096; font-size:12px;'>정상 (상태이상 없음)</span>"

        badges = []
        for status in target.status_effects.values():
            if status.duration_turns <= 0:
                continue
            color = "#e53e3e" if status.effect_type in ["damage_tick", "action_block"] else "#38a169"
            if status.id in ["stun", "freeze", "paralysis"]:
                color = "#dd6b20"
            elif status.id in ["empower", "shield"]:
                color = "#3182ce"

            stack_str = f" x{status.stacks}" if status.stacks > 1 else ""
            dur_str = f"{status.duration_turns}턴" if status.duration_turns > 0 else "영구"
            badge = (
                f"<span style='display:inline-block; background:{color}22; border:1px solid {color}; "
                f"color:{color}; padding:2px 8px; border-radius:4px; font-size:11px; margin:2px 4px 2px 0; font-weight:600;'>"
                f"{status.name}{stack_str} ({dur_str})"
                f"</span>"
            )
            badges.append(badge)

        return "".join(badges) if badges else "<span style='color:#718096; font-size:12px;'>정상 (상태이상 없음)</span>"
