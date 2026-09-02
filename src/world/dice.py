"""
Deterministic D&D-style Dice & Skill Check Engine for Quilltale.
Resolves combat and skill challenges deterministically before generating narrative text.
Enforces skill scaling limits and stat calculation thresholds.
"""
import random
from dataclasses import dataclass
from typing import Optional
from src.core.config import MIN_SKILL_SCALING, MAX_SKILL_SCALING


@dataclass
class DiceCheckResult:
    action_type: str
    d20_roll: int
    modifier: int
    total: int
    dc: int
    is_success: bool
    is_critical_success: bool
    is_critical_failure: bool
    damage_dealt: int = 0
    target_npc_id: Optional[str] = None
    summary_ko: str = ""
    target_part: str = ""
    weak_point_penalty: int = 0
    interrupt_counter: bool = False
    is_no_incantation: bool = False



def roll_crit(player) -> tuple[bool, float]:
    """Returns (is_crit, damage_multiplier)"""
    crit_roll = random.random() * 100
    if crit_roll < player.effective_crit_rate:
        return True, player.effective_crit_damage / 100.0
    return False, 1.0


class DiceEngine:
    """
    Handles d20 rolls, stat modifiers, damage calculations, and DC checks.
    """

    WEAK_POINT_DC_PENALTIES = {
        '머리': 4,
        '목': 6,
        '눈': 8,
        '급소': 8,
        '관절': 5,
        '팔': 2,
        '다리': 2,
        '등': 4,
        '심장': 10,
    }

    @staticmethod
    def stat_modifier(stat_value: int) -> int:
        """Standard D&D modifier: (stat - 10) // 2"""
        return (stat_value - 10) // 2

    @staticmethod
    def roll_d20() -> int:
        return random.randint(1, 20)

    @classmethod
    def calculate_skill_damage(
        cls,
        base_damage: int,
        stat_value: int,
        scaling: float = 1.5,
        target_defense: int = 0,
    ) -> int:
        """
        Damage formula: max(1, int(base_damage + (stat_modifier * clamped_scaling) - target_defense))
        Scaling is clamped between MIN_SKILL_SCALING (0.5) and MAX_SKILL_SCALING (3.0).
        """
        clamped_scaling = max(MIN_SKILL_SCALING, min(MAX_SKILL_SCALING, scaling))
        mod = max(0, cls.stat_modifier(stat_value))
        calculated = base_damage + int(mod * clamped_scaling) - target_defense
        return max(1, calculated)

    @classmethod
    def calculate_skill_damage_with_crit(
        cls, base_damage, stat_value, scaling=1.5, target_defense=0, player=None, is_no_incantation: bool = False
    ) -> tuple[int, bool]:
        """Returns (final_damage, is_crit)"""
        base = cls.calculate_skill_damage(base_damage, stat_value, scaling, target_defense)
        if is_no_incantation:
            from src.core.config import NO_INCANTATION_DAMAGE_MULT
            base = max(1, int(base * NO_INCANTATION_DAMAGE_MULT))
        if player:
            is_crit, crit_mult = roll_crit(player)
            if is_crit:
                return int(base * crit_mult), True
        return base, False


    @staticmethod
    def incantation_interrupted_check(npc_agility: int) -> bool:
        """NPC attempts to interrupt player's incantation. Returns True if interrupted."""
        roll = DiceEngine.roll_d20()
        return roll + DiceEngine.stat_modifier(npc_agility) >= 12

    @classmethod
    def perform_check(
        cls,
        action_type: str,
        stat_value: int,
        dc: int = 12,
        base_damage: int = 0,
        scaling: float = 1.5,
        target_defense: int = 0,
        target_npc_id: Optional[str] = None,
        target_part: str = '',
        is_no_incantation: bool = False,
        fatigue: int = -1,
    ) -> DiceCheckResult:
        """
        Executes a deterministic d20 check against DC with fatigue modifier.
        """
        penalty = 0
        if target_part in cls.WEAK_POINT_DC_PENALTIES:
            penalty = cls.WEAK_POINT_DC_PENALTIES[target_part]
        
        final_dc = dc + penalty
        
        roll = cls.roll_d20()
        base_mod = cls.stat_modifier(stat_value)
        
        fatigue_mod = 0
        if fatigue == 0:
            fatigue_mod = 1
        elif fatigue >= 80:
            fatigue_mod = -3
        elif fatigue >= 50:
            fatigue_mod = -1

        modifier = base_mod + fatigue_mod
        total = roll + modifier

        is_crit_succ = roll == 20
        is_crit_fail = roll == 1

        if is_crit_succ:
            is_success = True
        elif is_crit_fail:
            is_success = False
        else:
            is_success = total >= final_dc

        interrupt_counter = False
        if not is_success and penalty >= 5:
            interrupt_counter = True

        damage = 0
        if is_success and base_damage > 0:
            raw_dmg = cls.calculate_skill_damage(
                base_damage, stat_value, scaling, target_defense
            )
            if is_no_incantation:
                from src.core.config import NO_INCANTATION_DAMAGE_MULT
                raw_dmg = max(1, int(raw_dmg * NO_INCANTATION_DAMAGE_MULT))
            damage = raw_dmg * 2 if is_crit_succ else raw_dmg

        # Format Korean summary
        if is_crit_succ:
            status_ko = f"🌟 대성공! (주사위: 20 + 보정치 {modifier} = {total} vs 난이도 {final_dc})"
        elif is_crit_fail:
            status_ko = f"💀 대실패! (주사위: 1 + 보정치 {modifier} = {total} vs 난이도 {final_dc})"
        elif is_success:
            status_ko = f"✅ 성공 (주사위: {roll} + 보정치 {modifier} = {total} vs 난이도 {final_dc})"
        else:
            status_ko = f"❌ 실패 (주사위: {roll} + 보정치 {modifier} = {total} vs 난이도 {final_dc})"

        if fatigue == 0:
            status_ko += " [✨ 완벽한 휴식: 판정 +1 메리트]"
        elif fatigue >= 80:
            status_ko += " [🩸 극심한 탈진: 판정 -3 디메리트]"
        elif fatigue >= 50:
            status_ko += " [💦 심한 피로: 판정 -1 디메리트]"

        if is_no_incantation and is_success:
            status_ko += " [⚡ 무영창 시전: 본래 위력의 1/10]"

        if penalty > 0:
            status_ko += f" [{target_part} 노리기 패널티 +{penalty}]"

        if interrupt_counter:
            status_ko += " ⚠️ 적의 반격 기회!"

        if damage > 0:
            status_ko += f" | 가한 피해: {damage}"

        return DiceCheckResult(
            action_type=action_type,
            d20_roll=roll,
            modifier=modifier,
            total=total,
            dc=final_dc,
            is_success=is_success,
            is_critical_success=is_crit_succ,
            is_critical_failure=is_crit_fail,
            damage_dealt=damage,
            target_npc_id=target_npc_id,
            summary_ko=status_ko,
            target_part=target_part,
            weak_point_penalty=penalty,
            interrupt_counter=interrupt_counter,
            is_no_incantation=is_no_incantation,
        )


