"""
NPC Skill & Opportunistic Action Engine for Quilltale TRPG Engine.
Deterministic resolution of:
1. Combat skill execution & counter-attacks for hostile NPCs.
2. Opportunistic, desire/personality-driven non-combat actions (theft, pickpocketing, backstab, coercion).
3. Turn-based cooldown management for all active skills.
"""
import random
import logging
from typing import Optional, Dict, Any, List, Tuple
from src.world.state import WorldState, NPC, Player, Skill
from src.world.dice import DiceEngine
from src.world.status_engine import StatusEffectEngine

logger = logging.getLogger(__name__)


class NPCSkillEngine:
    @staticmethod
    def tick_all_skill_cooldowns(state: WorldState):
        """Ticks down skill cooldowns by 1 turn across all skills in the database and loaded entities."""
        for skill in state.skills_db.values():
            if getattr(skill, "current_cooldown", 0) > 0:
                skill.current_cooldown -= 1

    @staticmethod
    def get_available_npc_skills(npc: NPC, state: WorldState, offensive_only: bool = True) -> List[Skill]:
        """Finds all ready-to-cast skills for an NPC based on current mana and cooldown."""
        ready_skills = []
        for skill_id in npc.skills:
            skill = state.skills_db.get(skill_id)
            if not skill:
                continue
            if getattr(skill, "current_cooldown", 0) > 0:
                continue
            if skill.resource_type == "mana" and npc.mana < skill.resource_cost:
                continue
            if offensive_only and skill.role_type not in ["single_attack", "aoe_attack", "debuff_curse"]:
                continue
            ready_skills.append(skill)
        return ready_skills

    @classmethod
    def process_npc_combat_turn(
        cls,
        npc: NPC,
        state: WorldState,
        player_ac: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Executes an autonomous combat turn for an active hostile NPC.
        Returns a dictionary summarizing the deterministic action outcome or None.
        """
        if not npc.alive or npc.disposition != "hostile":
            return None

        # Check for CC status effects preventing action
        if StatusEffectEngine.has_status(npc, "stun") or StatusEffectEngine.has_status(npc, "paralysis"):
            return {
                "npc_id": npc.id,
                "npc_name": npc.name,
                "action_type": "cc_stunned",
                "summary_ko": f"[{npc.name}]은(는) 기절/마비 상태로 인해 이번 턴에 행동할 수 없습니다.",
                "damage": 0,
                "is_success": False
            }

        ready_skills = cls.get_available_npc_skills(npc, state, offensive_only=True)
        chosen_skill: Optional[Skill] = None

        target_hp = state.player.health
        is_target_weak = (target_hp <= 15)
        npc_int = npc.intelligence
        npc_wis = npc.wisdom
        npc_aggro = getattr(npc.personality, "aggression", 50)

        # Situational choice: on weak targets, smart NPCs conserve mana while sadistic/high-aggro NPCs overkill
        should_conserve_mana = False
        if is_target_weak and ready_skills:
            if npc_int >= 12 or npc_wis >= 12:
                if npc_aggro < 80:
                    should_conserve_mana = True  # Smartly conserve mana
            elif npc_aggro >= 80:
                should_conserve_mana = False  # Sadistic overkill
            else:
                should_conserve_mana = (random.random() < 0.5)

        if ready_skills and not should_conserve_mana:
            tier_weights = {"legendary": 5, "epic": 4, "rare": 3, "uncommon": 2, "common": 1}
            ready_skills.sort(key=lambda s: tier_weights.get(s.tier, 1), reverse=True)
            chosen_skill = ready_skills[0]

        # Determine stat for roll
        stat_key = chosen_skill.scaling_stat if chosen_skill else "str"
        stat_map = {
            "str": npc.strength,
            "dex": npc.agility,
            "int": npc.intelligence,
            "wis": npc.wisdom,
            "con": npc.constitution,
            "cha": getattr(npc.personality, "courage", 50) // 5
        }
        stat_val = stat_map.get(stat_key, npc.strength)

        # Roll d20 hit check vs player AC
        d20 = DiceEngine.roll_d20()
        modifier = DiceEngine.stat_modifier(stat_val)
        total_hit = d20 + modifier
        is_hit = (total_hit >= player_ac) or (d20 == 20)

        skill_name = chosen_skill.name if chosen_skill else "물리 공격"
        skill_cost = chosen_skill.resource_cost if chosen_skill else 0

        # Apply resource deduction and cooldown
        if chosen_skill:
            if chosen_skill.resource_type == "mana":
                npc.mana = max(0, npc.mana - skill_cost)
            chosen_skill.current_cooldown = chosen_skill.cooldown_turns

        if not is_hit and d20 != 1:
            return {
                "npc_id": npc.id,
                "npc_name": npc.name,
                "action_type": "skill_attack_miss",
                "skill_name": skill_name,
                "d20_roll": d20,
                "modifier": modifier,
                "total_hit": total_hit,
                "player_ac": player_ac,
                "is_success": False,
                "damage": 0,
                "summary_ko": f"[{npc.name}]의 [{skill_name}] 공격이 빗나갔습니다! (판정: {total_hit} vs 플레이어 AC {player_ac})"
            }

        # Calculate damage
        base_dmg = chosen_skill.base_value if chosen_skill else 5
        scaling = chosen_skill.scaling_factor if chosen_skill else 1.0
        calculated_dmg = DiceEngine.calculate_skill_damage(
            base_damage=base_dmg,
            stat_value=stat_val,
            scaling=scaling,
            target_defense=max(0, (player_ac - 10) // 2)
        )
        if d20 == 20:
            calculated_dmg = int(calculated_dmg * 1.5)

        # Apply armor durability and damage mitigation
        from src.world.equipment import EquipmentEngine
        mitigated_dmg, armor_logs = EquipmentEngine.apply_armor_durability_and_mitigation(
            state, state.player, calculated_dmg, target_part=""
        )

        # Apply damage directly to player health
        hp_before = state.player.health
        hp_after = max(0, hp_before - mitigated_dmg)
        state.player.health = hp_after

        # Inflict status effects if defined in skill
        applied_statuses = []
        if chosen_skill and chosen_skill.inflicted_status:
            for s_info in chosen_skill.inflicted_status:
                s_name = s_info.get("status")
                dur = s_info.get("duration_turns", s_info.get("duration", 2))
                pot = s_info.get("dot_damage_per_turn", s_info.get("potency", 5))
                if s_name:
                    StatusEffectEngine.apply_status(state.player, s_name, duration=dur, potency=pot)
                    applied_statuses.append(f"{s_name}({dur}턴)")

        status_text = f", 상태이상 [{', '.join(applied_statuses)}] 부여" if applied_statuses else ""
        return {
            "npc_id": npc.id,
            "npc_name": npc.name,
            "action_type": "skill_attack_hit",
            "skill_name": skill_name,
            "d20_roll": d20,
            "modifier": modifier,
            "total_hit": total_hit,
            "player_ac": player_ac,
            "is_success": True,
            "damage": calculated_dmg,
            "player_hp_before": hp_before,
            "player_hp_after": hp_after,
            "applied_statuses": applied_statuses,
            "summary_ko": f"[{npc.name}]이(가) [{skill_name}] 시전! 플레이어에게 {calculated_dmg} 피해 적중 (체력: {hp_before} → {hp_after}/{state.player.max_health}){status_text}"
        }

    @classmethod
    def process_npc_opportunistic_turn(
        cls,
        npc: NPC,
        state: WorldState,
        player_action: str
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates and executes opportunistic, desire/personality-driven non-combat actions:
        - Sleight of hand / Pickpocketing (Greed >= 60, Rogue/Thief job, or greed keywords)
        - Sudden backstab/ambush (Wary + Aggression >= 75)
        Returns outcome dict or None if no opportunistic action is triggered.
        """
        if not npc.alive or npc.disposition == "hostile":
            return None

        p_action_lower = player_action.lower()
        greed_score = getattr(npc.personality, "greed", 50)
        aggression_score = getattr(npc.personality, "aggression", 50)
        job_lower = npc.job.lower()
        desire_lower = getattr(npc, "desire", "").lower()

        # 1. Opportunistic Pickpocketing / Theft Check
        is_thief_profile = (
            greed_score >= 60 or
            any(k in job_lower for k in ["도적", "소매치기", "부랑", "밀수", "살수", "용병"]) or
            any(k in desire_lower for k in ["골드", "돈", "금화", "보물", "재물", "가보", "약탈"])
        )

        # Player must possess gold or stealable items
        stealable_items = [
            i_id for i_id in state.player.inventory
            if i_id in state.items and state.items[i_id].item_type in ["misc", "consumable", "accessory", "currency"]
        ]
        has_loot = (state.player.gold >= 10) or bool(stealable_items)

        # Trigger if player is distracted
        is_distracted = any(k in p_action_lower for k in [
            "살핀다", "바라본", "둘러", "조사", "읽", "대화", "말을 건", "인벤토리", "뒤적", "잠", "휴식", "눈을 감"
        ])

        if is_thief_profile and has_loot and is_distracted:
            from src.world.perception_engine import PerceptionEngine
            eval_res = PerceptionEngine.evaluate_theft_vs_perception(npc, state.player, is_distracted=True)

            if eval_res["success"]:
                stolen_desc = ""
                stolen_type = ""
                stolen_amount = 0
                stolen_item_id = ""

                if state.player.gold >= 20 and random.random() < 0.6:
                    stolen_amount = min(state.player.gold, random.randint(10, 25))
                    state.player.gold -= stolen_amount
                    npc.gold += stolen_amount
                    stolen_desc = f"금화 {stolen_amount}닢"
                    stolen_type = "gold"
                elif stealable_items:
                    target_item_id = random.choice(stealable_items)
                    target_item = state.items[target_item_id]
                    state.player.inventory.remove(target_item_id)
                    npc.inventory.append(target_item_id)
                    stolen_desc = f"[{target_item.name}]"
                    stolen_type = "item"
                    stolen_item_id = target_item_id
                else:
                    stolen_amount = min(state.player.gold, 5)
                    state.player.gold -= stolen_amount
                    npc.gold += stolen_amount
                    stolen_desc = f"금화 {stolen_amount}닢"
                    stolen_type = "gold"

                # Record into player's unnoticed_thefts
                PerceptionEngine.record_unnoticed_theft(
                    state, npc, stolen_desc, stolen_type, amount=stolen_amount, item_id=stolen_item_id
                )

                tier_desc = "완전 은밀 (복선 없음)" if eval_res["tier"] == "imperceptible" else "미묘한 기척 감지 (복선 노출)"
                return {
                    "npc_id": npc.id,
                    "npc_name": npc.name,
                    "action_type": "opportunistic_theft_success",
                    "total_stealth": eval_res["total_stealth"],
                    "player_dc": eval_res["victim_passive_per"],
                    "stolen_target": stolen_desc,
                    "stolen_type": stolen_type,
                    "player_noticed": False,
                    "tier": eval_res["tier"],
                    "hint_desc": eval_res["hint_desc"],
                    "summary_ko": f"[{npc.name}]이(가) 은밀히 {stolen_desc}을(를) 소매치기했습니다! ({tier_desc}: 판정 {eval_res['total_stealth']} vs 감각 DC {eval_res['victim_passive_per']})",
                    "gm_directive": eval_res["gm_directive"]
                }
            else:
                # Failure! Caught in the act
                npc.disposition = "wary"
                return {
                    "npc_id": npc.id,
                    "npc_name": npc.name,
                    "action_type": "opportunistic_theft_failed",
                    "total_stealth": eval_res["total_stealth"],
                    "player_dc": eval_res["victim_passive_per"],
                    "player_noticed": True,
                    "tier": "caught",
                    "summary_ko": f"[{npc.name}]이(가) 플레이어의 가방에 손을 뻗다 현장에서 발각되었습니다! (발각 판정: {eval_res['total_stealth']} vs 플레이어 감각 DC {eval_res['victim_passive_per']})",
                    "gm_directive": eval_res["gm_directive"]
                }

        # 2. Sudden Backstab / Ambush by Highly Aggressive Wary NPCs
        if npc.disposition == "wary" and aggression_score >= 75 and any(k in p_action_lower for k in ["등을 돌", "떠나", "무시", "잠"]):
            npc.disposition = "hostile"
            return {
                "npc_id": npc.id,
                "npc_name": npc.name,
                "action_type": "opportunistic_ambush",
                "summary_ko": f"[{npc.name}]이(가) 적개심을 억누르지 못하고 빈틈을 보인 플레이어의 등 뒤에서 기습을 개시했습니다! (태도: 적대적으로 전환)",
                "gm_directive": f"{npc.name}이(가) 경계 상태를 깨고 흉기를 뽑아 플레이어의 등 뒤를 기습하는 긴박한 돌발 상황을 서사에 반영하십시오."
            }

        return None
