"""
Stamina & Physical Combat Resource Engine for Quilltale TRPG.
Manages stamina consumption for martial/physical skills, exhaustion triggering,
action gating (blocking heavy actions when exhausted), turn-based regeneration,
and symmetric Player/NPC stamina mechanics.
"""
from typing import Tuple, Dict, Any, Optional
from src.world.status_engine import StatusEffectEngine


class StaminaEngine:
    """
    Deterministic stamina calculation and management engine.
    Calculates dynamic capacity and natural recovery, validates costs,
    and enforces exhaustion penalties.
    """
    # TODO: Final values will be determined in subsequent balancing sessions.
    # Currently using placeholder coefficients for prototype verification.
    BASE_MAX_STAMINA: int = 100
    CON_STAMINA_WEIGHT: int = 5     # TODO: Placeholder CON scaling coefficient
    AGI_STAMINA_WEIGHT: int = 2     # TODO: Placeholder AGI scaling coefficient

    BASE_REGEN_PER_TURN: int = 15   # TODO: Placeholder base recovery amount
    CON_REGEN_WEIGHT: float = 0.5   # TODO: Placeholder CON recovery weight
    AGI_REGEN_WEIGHT: float = 0.25  # TODO: Placeholder AGI recovery weight

    EXHAUSTION_REGEN_PENALTY: float = 0.5  # 50% recovery penalty during exhaustion
    EXHAUSTION_DURATION_TURNS: int = 2     # Exhaustion status effect duration

    @classmethod
    def calculate_max_stamina(cls, entity: Any) -> int:
        """
        Calculates maximum stamina based on Constitution (endurance) and Agility (efficiency).
        """
        con = getattr(entity, "constitution", 10)
        agi = getattr(entity, "agility", 10)
        bonus_con = max(0, con - 10) * cls.CON_STAMINA_WEIGHT
        bonus_agi = max(0, agi - 10) * cls.AGI_STAMINA_WEIGHT
        return cls.BASE_MAX_STAMINA + bonus_con + bonus_agi

    @classmethod
    def calculate_regen_rate(cls, entity: Any) -> int:
        """
        Calculates natural stamina recovery per turn with exhaustion penalty applied.
        """
        con = getattr(entity, "constitution", 10)
        agi = getattr(entity, "agility", 10)
        # TODO: Placeholder formula for turn recovery calculation
        regen = (
            cls.BASE_REGEN_PER_TURN
            + int(max(0, con - 10) * cls.CON_REGEN_WEIGHT)
            + int(max(0, agi - 10) * cls.AGI_REGEN_WEIGHT)
        )

        # 50% penalty if suffering from exhaustion status effect
        if StatusEffectEngine.has_status(entity, "exhaustion"):
            regen = int(regen * cls.EXHAUSTION_REGEN_PENALTY)

        return max(1, regen)

    @classmethod
    def can_afford(cls, entity: Any, cost: int) -> Tuple[bool, str]:
        """
        Pre-checks if entity has enough stamina to cast skill or perform action.
        Returns (can_afford, rejection_reason_ko).
        """
        current_stamina = getattr(entity, "stamina", 100)
        if current_stamina < cost:
            return False, f"기력이 부족합니다. (필요: {cost}, 현재: {current_stamina})"

        # Gated action: if already exhausted, high-cost stamina skills or sprints are forbidden
        # TODO: Placeholder threshold for high-cost skills while exhausted
        if StatusEffectEngine.has_status(entity, "exhaustion") and cost > 20:
            return False, "탈진 상태로 인해 무리한 신체 행동 및 고위 무술을 펼칠 수 없습니다."

        return True, ""

    @classmethod
    def consume(cls, entity: Any, cost: int) -> Dict[str, Any]:
        """
        Consumes stamina and checks for zero-stamina exhaustion trigger.
        Returns dictionary with consumption details.
        """
        old_stamina = getattr(entity, "stamina", 100)
        new_stamina = max(0, old_stamina - cost)
        entity.stamina = new_stamina

        triggered_exhaustion = False
        if new_stamina == 0:
            StatusEffectEngine.apply_status(
                entity,
                "exhaustion",
                duration=cls.EXHAUSTION_DURATION_TURNS,
                potency=1
            )
            triggered_exhaustion = True

        return {
            "consumed": old_stamina - new_stamina,
            "current_stamina": new_stamina,
            "triggered_exhaustion": triggered_exhaustion
        }

    @classmethod
    def recover_turn(cls, entity: Any) -> int:
        """
        Naturally restores stamina on turn end up to maximum effective stamina.
        Returns amount of stamina restored.
        """
        if not getattr(entity, "alive", True):
            return 0

        max_stam = getattr(entity, "max_stamina_effective", cls.calculate_max_stamina(entity))
        curr = getattr(entity, "stamina", 100)
        if curr >= max_stam:
            return 0

        regen = cls.calculate_regen_rate(entity)
        restored = min(max_stam - curr, regen)
        entity.stamina = curr + restored
        return restored
