"""
Party & Companion Sanity / Mental Breakdown Engine for Quilltale TRPG.
Manages deterministic stress accumulation, environmental triggers, 15-tier mental breakdown afflictions,
heroic awakenings, and personality-weighted breakdown resolution.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import random
import logging

from src.world.dice import DiceEngine
from src.world.status_engine import StatusEffectEngine

logger = logging.getLogger(__name__)


@dataclass
class MentalBreakdownSpec:
    id: str
    name_ko: str
    name_en: str
    description: str
    duration: int
    activation_weight: int
    is_positive: bool = False
    effects: Dict[str, Any] = field(default_factory=dict)
    combat_behavior: Dict[str, Any] = field(default_factory=dict)
    # Mandatory traits tag list (Rule 6)
    traits: List[str] = field(default_factory=list)


# 15-Tier Full Mental Breakdown Registry (Base 5 + Additional 10)
MENTAL_BREAKDOWN_REGISTRY: Dict[str, MentalBreakdownSpec] = {
    # ---------------------------------------------------------
    # 1. Base Core Afflictions
    # ---------------------------------------------------------
    "panic": MentalBreakdownSpec(
        id="panic",
        name_ko="공황 발작",
        name_en="Panic",
        description="공포가 이성을 압도한다. 주변 상황을 제대로 판단하지 못하고 본능적으로 도망치려 한다.",
        duration=1,
        activation_weight=25,
        effects={"action_disabled": True, "movement": "random_direction", "skill_usage": False, "item_usage": False},
        combat_behavior={"flee": True, "ignore_orders": True, "ignore_player_commands": True},
        traits=["공황", "통제 불능", "적전 도주", "행동 불가"]
    ),
    "paranoia": MentalBreakdownSpec(
        id="paranoia",
        name_ko="편집증",
        name_en="Paranoia",
        description="모든 것을 의심하기 시작한다. 동료의 선의조차 자신을 해치려는 음모로 받아들인다.",
        duration=3,
        activation_weight=25,
        effects={"refuse_healing": True, "refuse_buffs": True, "refuse_food_from_allies": True, "trust_reduction": -20},
        combat_behavior={"ignore_support_actions": True, "ally_interaction_penalty": True},
        traits=["의심", "치료 거부", "버프 거부", "불신"]
    ),
    "selfishness": MentalBreakdownSpec(
        id="selfishness",
        name_ko="이기주의",
        name_en="Selfishness",
        description="극도의 생존 본능이 발현되어 자신 이외의 존재를 고려하지 않는다.",
        duration=4,
        activation_weight=20,
        effects={"item_sharing": False, "loot_sharing": False, "consumable_sharing": False, "party_loyalty": -15},
        combat_behavior={"leave_frontline": True, "prioritize_self_survival": True, "avoid_high_risk_actions": True},
        traits=["이기주의", "전열 이탈", "아이템 독점", "생존 집착"]
    ),
    "hopelessness": MentalBreakdownSpec(
        id="hopelessness",
        name_ko="절망",
        name_en="Hopelessness",
        description="모든 노력이 무의미하다고 느끼며 싸울 의지와 생존 의지가 급격히 감소한다.",
        duration=5,
        activation_weight=25,
        effects={"dice_roll_modifier": -4, "stamina_regeneration": 0, "mana_regeneration": 0, "morale": -30, "initiative_modifier": -2},
        combat_behavior={"aggressive_actions_reduced": True, "retreat_preference": True},
        traits=["절망", "주사위 페널티", "회복 불가", "사기 저하"]
    ),
    "awakening": MentalBreakdownSpec(
        id="awakening",
        name_ko="각성 / 영웅적 기개",
        name_en="Awakening",
        description="극한의 스트레스 속에서 오히려 정신이 한계를 돌파한다. 공포는 사라지고 살아남겠다는 강렬한 의지가 솟구친다.",
        duration=5,
        activation_weight=5,
        is_positive=True,
        effects={"stress_reset": 0, "all_stats_bonus": 5, "all_stats_multiplier": 1.10, "morale": 100, "fear_immunity": True},
        combat_behavior={"heroic_resolve": True, "protect_allies": True},
        traits=["영웅적 각성", "전 스탯 +5", "공포 면역", "사기 충천"]
    ),

    # ---------------------------------------------------------
    # 2. Additional Specialized Afflictions (10종)
    # ---------------------------------------------------------
    "dissociation": MentalBreakdownSpec(
        id="dissociation",
        name_ko="해리",
        name_en="Dissociation",
        description="현실감이 희미해져 주변 상황과 자신의 행동을 제대로 인식하지 못한다.",
        duration=3,
        activation_weight=10,
        effects={"action_delay": 1, "dice_roll_modifier": -2, "perception": -30},
        combat_behavior={"occasionally_ignore_commands": True, "random_idle_action": True},
        traits=["현실 괴리", "반응 지연", "지각 저하", "멍때림"]
    ),
    "rage": MentalBreakdownSpec(
        id="rage",
        name_ko="광폭화",
        name_en="Rage",
        description="공포를 분노로 전환하여 이성을 잃고 눈앞의 적을 파괴하려 한다.",
        duration=3,
        activation_weight=10,
        effects={"strength_bonus": 8, "defense_penalty": -4, "critical_chance_bonus": 10},
        combat_behavior={"target_priority": "nearest_enemy", "retreat": False, "ignore_player_commands": True},
        traits=["이성 상실", "근력 폭증", "방어 급감", "맹목적 돌진"]
    ),
    "freeze": MentalBreakdownSpec(
        id="freeze",
        name_ko="얼어붙음",
        name_en="Freeze",
        description="공포에 압도되어 몸이 굳어버린다. 도망치지도 싸우지도 못한다.",
        duration=2,
        activation_weight=10,
        effects={"movement_disabled": True, "attack_disabled": True, "skill_usage": False, "defense_modifier": -5},
        combat_behavior={"remain_in_place": True, "ignore_movement_commands": True},
        traits=["공포 마비", "제자리 굳음", "무방비", "행동 정지"]
    ),
    "obsession": MentalBreakdownSpec(
        id="obsession",
        name_ko="강박",
        name_en="Obsession",
        description="특정 행동이나 목표에 집착하여 다른 상황을 무시한다.",
        duration=4,
        activation_weight=8,
        effects={"target_lock": True, "judgment_penalty": -3},
        combat_behavior={"repeat_same_action": True, "ignore_alternative_orders": True},
        traits=["행동 집착", "외골수", "명령 무시", "반복 행동"]
    ),
    "regression": MentalBreakdownSpec(
        id="regression",
        name_ko="퇴행",
        name_en="Regression",
        description="정신적 압박을 견디지 못하고 어린아이와 같은 행동 양상으로 퇴행한다.",
        duration=5,
        activation_weight=8,
        effects={"dice_roll_modifier": -2, "social_skill": -20, "combat_effectiveness": -15},
        combat_behavior={"seek_nearest_trusted_ally": True, "avoid_independent_actions": True},
        traits=["유아 퇴행", "의존 심리", "전투력 저하", "공포 호소"]
    ),
    "flight_instinct": MentalBreakdownSpec(
        id="flight_instinct",
        name_ko="도주 본능",
        name_en="Flight Instinct",
        description="생존 본능이 이성을 압도하여 전투를 포기하고 출구를 찾아 도망친다.",
        duration=3,
        activation_weight=10,
        effects={"movement_speed_bonus": 20, "defense_bonus": 3, "attack_power": -50},
        combat_behavior={"target_priority": "exit", "flee_from_combat": True, "ignore_orders": True},
        traits=["생존 질주", "전투 포기", "퇴각 본능", "명령 거부"]
    ),
    "survivor_guilt": MentalBreakdownSpec(
        id="survivor_guilt",
        name_ko="생존자 죄책감",
        name_en="Survivor's Guilt",
        description="자신만 살아남았다는 죄책감에 사로잡혀 동료를 구하지 못한 자신을 책망한다.",
        duration=6,
        activation_weight=7,
        effects={"dice_roll_modifier": -3, "morale": -40, "healing_received_modifier": -20},
        combat_behavior={"prioritize_ally_rescue": True, "risk_self_for_ally": True},
        traits=["자책", "자기 희생", "치료 기피", "사기 바닥"]
    ),
    "destructive_impulse": MentalBreakdownSpec(
        id="destructive_impulse",
        name_ko="파괴 충동",
        name_en="Destructive Impulse",
        description="쌓인 긴장을 억누르지 못하고 주변의 물건과 환경을 무차별적으로 파괴한다.",
        duration=3,
        activation_weight=6,
        effects={"strength_bonus": 5, "dexterity_penalty": -3, "interaction_accuracy": -30},
        combat_behavior={"attack_environment": True, "destroy_containers": True},
        traits=["기물 파괴", "난동", "통제 불능", "완력 폭주"]
    ),
    "emotional_shutdown": MentalBreakdownSpec(
        id="emotional_shutdown",
        name_ko="감정 폐쇄",
        name_en="Emotional Shutdown",
        description="더 이상의 감정을 느끼지 않기 위해 스스로 마음을 닫아버린다.",
        duration=5,
        activation_weight=7,
        effects={"fear_immunity": True, "morale": 0, "healing_received_modifier": -30, "buff_effectiveness": -30},
        combat_behavior={"minimal_dialogue": True, "refuse_emotional_interactions": True},
        traits=["감정 결여", "교감 거부", "냉담", "버프 반감"]
    ),
    "false_confidence": MentalBreakdownSpec(
        id="false_confidence",
        name_ko="허세",
        name_en="False Confidence",
        description="극심한 공포를 인정하지 않기 위해 자신이 모든 것을 통제하고 있다고 믿는다.",
        duration=4,
        activation_weight=6,
        effects={"attack_power": 10, "defense_penalty": -8, "dice_roll_modifier": -2},
        combat_behavior={"refuse_retreat": True, "take_unnecessary_risks": True, "challenge_strong_enemies": True},
        traits=["근자감", "무모한 돌격", "후퇴 거부", "방어 포기"]
    )
}


# Personality-Weighted Breakdown Resolution Tables
PERSONALITY_BREAKDOWN_TABLES: Dict[str, Dict[str, int]] = {
    "brave": {
        "awakening": 50, "hopelessness": 15, "paranoia": 15, "panic": 10, "selfishness": 10,
        "rage": 25, "false_confidence": 20, "survivor_guilt": 15
    },
    "cowardly": {
        "panic": 55, "paranoia": 20, "freeze": 25, "flight_instinct": 30, "regression": 20,
        "selfishness": 10, "hopelessness": 10, "awakening": 5
    },
    "loyal": {
        "hopelessness": 40, "awakening": 25, "panic": 20, "survivor_guilt": 35, "paranoia": 10,
        "selfishness": 5, "freeze": 10
    },
    "selfish": {
        "selfishness": 45, "paranoia": 25, "flight_instinct": 30, "panic": 15, "hopelessness": 10,
        "awakening": 5, "destructive_impulse": 15
    },
    "suspicious": {
        "paranoia": 55, "dissociation": 20, "panic": 15, "selfishness": 15, "hopelessness": 10,
        "awakening": 5, "emotional_shutdown": 20
    },
    "idealistic": {
        "hopelessness": 50, "awakening": 25, "regression": 20, "panic": 15, "paranoia": 5,
        "selfishness": 5, "survivor_guilt": 20
    },
    "survivalist": {
        "selfishness": 50, "flight_instinct": 35, "paranoia": 20, "hopelessness": 15, "panic": 10,
        "awakening": 5, "false_confidence": 10
    },
    "stoic": {
        "awakening": 50, "emotional_shutdown": 35, "hopelessness": 20, "paranoia": 15, "selfishness": 10,
        "dissociation": 15, "panic": 5
    }
}


class PartySanityEngine:
    """
    Deterministic Mental Health & Sanity Engine for Companions.
    """

    MAX_STRESS: int = 100
    SAFE_DECAY_PER_TURN: int = 2

    @classmethod
    def add_stress(cls, companion: Any, amount: int, reason_ko: str = "") -> Dict[str, Any]:
        """
        Adds stress points to a companion up to MAX_STRESS (100).
        If stress reaches 100, automatically triggers mental breakdown resolution.
        """
        old_stress = getattr(companion, "stress", 0)
        new_stress = min(cls.MAX_STRESS, max(0, old_stress + amount))
        companion.stress = new_stress

        breakdown_triggered = False
        breakdown_result = None

        if new_stress >= cls.MAX_STRESS:
            breakdown_result = cls.trigger_breakdown(companion)
            breakdown_triggered = True

        log_msg = f"🧠 [{companion.name_ko}] 스트레스 +{amount} ({old_stress} -> {new_stress}/{cls.MAX_STRESS}) [{reason_ko}]"
        return {
            "companion_id": companion.companion_id,
            "old_stress": old_stress,
            "new_stress": new_stress,
            "breakdown_triggered": breakdown_triggered,
            "breakdown_result": breakdown_result,
            "log": log_msg
        }

    @classmethod
    def trigger_breakdown(cls, companion: Any, forced_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolves mental breakdown when companion reaches 100 stress.
        Picks affliction based on personality weights or forced_id.
        Resets stress to 0.
        """
        p_type = getattr(companion, "personality_type", "stoic")
        weights = PERSONALITY_BREAKDOWN_TABLES.get(p_type, PERSONALITY_BREAKDOWN_TABLES["stoic"])

        chosen_id = forced_id
        if not chosen_id:
            afflictions = list(weights.keys())
            weight_values = list(weights.values())
            chosen_id = random.choices(afflictions, weights=weight_values, k=1)[0]

        spec = MENTAL_BREAKDOWN_REGISTRY.get(chosen_id, MENTAL_BREAKDOWN_REGISTRY["hopelessness"])

        companion.mental_status = spec.id
        companion.breakdown_turns_remaining = spec.duration
        companion.stress = 0  # Reset stress on breakdown

        if spec.is_positive:
            # Heroic Awakening clears negative mental states and buffs stats
            summary_msg = f"🌟 [영웅적 각성!] [{companion.name_ko}]이(가) 극한의 공포를 극복하고 각성했습니다! ({spec.name_ko}: {spec.duration}턴 지속, 전 스탯 보너스)"
        else:
            summary_msg = f"⚡ [멘탈 붕괴!] [{companion.name_ko}]의 이성이 한계에 도달하여 [{spec.name_ko}] 상태에 빠졌습니다! ({spec.description} - {spec.duration}턴 지속)"

        return {
            "companion_id": companion.companion_id,
            "affliction_id": spec.id,
            "name_ko": spec.name_ko,
            "duration": spec.duration,
            "is_positive": spec.is_positive,
            "summary_ko": summary_msg
        }

    @classmethod
    def process_turn_sanity(cls, state: Any, delta_minutes: int = 30) -> List[str]:
        """
        Executes environmental stress ticks for all active party companions scaled by delta_minutes:
        1. Underground darkness: +2 stress per 30m if pitch_black.
        2. Safe zones (towns/rest): -2 stress per 30m.
        3. Breakdown turn counters decrement and recover.
        """
        logs: List[str] = []
        if not hasattr(state, "party") or not state.party:
            return logs

        curr_loc = state.locations.get(state.player.location)
        is_underground = (getattr(curr_loc, "location_category", "surface") == "dungeon")
        is_safe = (getattr(curr_loc, "location_category", "surface") == "surface" and getattr(curr_loc, "danger_level", 20) <= 20)
        turn_ticks = max(1, round(delta_minutes / 30.0))

        for c_id, comp in state.party.items():
            if not getattr(comp, "is_active_party", True):
                continue

            # 1. Darkness stress
            if is_underground:
                res = cls.add_stress(comp, 2 * turn_ticks, f"지하 칠흑 어둠 체류 ({turn_ticks * 30}분)" if turn_ticks > 1 else "지하 칠흑 어둠 체류")
                if res["breakdown_triggered"]:
                    logs.append(res["breakdown_result"]["summary_ko"])

            # 2. Safe zone stress decay
            elif is_safe and comp.stress > 0:
                comp.stress = max(0, comp.stress - (cls.SAFE_DECAY_PER_TURN * turn_ticks))

            # 3. Decrement breakdown status
            if comp.breakdown_turns_remaining > 0:
                comp.breakdown_turns_remaining = max(0, comp.breakdown_turns_remaining - turn_ticks)
                if comp.breakdown_turns_remaining == 0:
                    old_status = comp.mental_status
                    comp.mental_status = "normal"
                    spec = MENTAL_BREAKDOWN_REGISTRY.get(old_status)
                    name_ko = spec.name_ko if spec else old_status
                    logs.append(f"🕊️ [{comp.name_ko}]의 [{name_ko}] 상태가 해제되어 평정심을 되찾았습니다.")

        return logs

    @classmethod
    def trigger_event_stress(cls, state: Any, event_type: str, details: Dict[str, Any] = None) -> List[str]:
        """
        Triggers situational stress for all party members based on high-impact events:
        - ally_near_death (+15)
        - horrific_encounter (+10)
        - trap_hit (+8)
        - critical_hit (+12)
        """
        logs: List[str] = []
        if not hasattr(state, "party") or not state.party:
            return logs

        amount_map = {
            "ally_near_death": (15, "동료의 치명적 빈사 목격"),
            "horrific_encounter": (10, "기괴한 혐오체 조우"),
            "trap_hit": (8, "기습 함정 피격"),
            "critical_hit": (12, "치명타 강타 피격")
        }

        if event_type not in amount_map:
            return logs

        amt, desc = amount_map[event_type]
        for comp in state.party.values():
            if getattr(comp, "is_active_party", True):
                res = cls.add_stress(comp, amt, desc)
                if res["breakdown_triggered"]:
                    logs.append(res["breakdown_result"]["summary_ko"])

        return logs

    @classmethod
    def filter_companion_combat_intent(cls, companion: Any, proposed_action: str) -> Tuple[bool, str]:
        """
        Filters companion's action based on active mental breakdown.
        Returns (allow_action, narrative_reason_ko).
        """
        status = getattr(companion, "mental_status", "normal")
        if status == "normal" or status == "awakening":
            return True, ""

        spec = MENTAL_BREAKDOWN_REGISTRY.get(status)
        if not spec:
            return True, ""

        behavior = spec.combat_behavior
        if behavior.get("flee"):
            return False, f"[{companion.name_ko}]은(는) 극심한 [{spec.name_ko}]으로 인해 무작위 방향으로 비명을 지르며 도주합니다!"
        if behavior.get("remain_in_place"):
            return False, f"[{companion.name_ko}]은(는) 공포에 사로잡혀 온몸이 [{spec.name_ko}] 상태로 굳어 아무런 행동도 하지 못합니다."
        if behavior.get("ignore_orders"):
            return False, f"[{companion.name_ko}]은(는) [{spec.name_ko}]에 휩쓸려 플레이어의 전술 명령을 완전히 거부합니다!"

        return True, ""
