"""
Tag-Based Attack Physics Engine for Quilltale TRPG.
Calculates kinetic energy, charge momentum, bow tension draw mechanics,
armor penetration, poise stagger, and action interrupts without hardcoding individual skills.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import math

from src.world.stat_engine import StatEngine


@dataclass
class AttackPhysicsResult:
    base_damage: int
    physics_damage_bonus: float
    total_damage: int
    armor_penetration_pct: float
    stagger_inflicted: float
    knockback_m: float
    tags_applied: List[str]
    interrupted_action: bool
    interrupt_reason: str
    bleed_inflicted: bool
    bone_fracture_risk: bool
    flight_time_seconds: float
    summary_ko: str
    traits: List[str] = field(default_factory=lambda: ["물리 타격 결과", "피격 저지력", "피해 산출"])


@dataclass
class AttackPhysicsEngine:
    TRAITS: List[str] = field(default_factory=lambda: [
        "태그 기반 물리 공격",
        "가속도 운동에너지",
        "활 장력 역학",
        "강인도 붕괴 저지력",
        "초고속 잽 캔슬"
    ])
    traits: List[str] = field(default_factory=lambda: [
        "태그 기반 물리 공격",
        "가속도 운동에너지",
        "활 장력 역학",
        "강인도 붕괴 저지력",
        "초고속 잽 캔슬"
    ])

    @classmethod
    def can_draw_bow(cls, strength: int, draw_weight_lbs: float) -> Tuple[bool, float, str]:
        """
        근력에 따른 활 당김 가능 여부 및 인장율(0.0 ~ 1.0) 계산.
        반환: (완발 가능 여부, 실제 인장 배율, 한글 설명)
        """
        max_draw = StatEngine.calculate_max_draw_weight(strength)
        if draw_weight_lbs <= 0.0:
            return (True, 1.0, "일반 투사체 (장력 제한 없음)")

        if max_draw >= draw_weight_lbs:
            ratio = min(1.2, max_draw / draw_weight_lbs)
            return (True, 1.0, f"완전 만작 (장력 {draw_weight_lbs:.0f} lbs / 근력 한계 {max_draw:.0f} lbs)")
        else:
            draw_ratio = max(0.1, max_draw / draw_weight_lbs)
            return (False, round(draw_ratio, 2), f"불완전 인장 (장력 부족: {draw_ratio * 100:.0f}%만 당겨짐, 탄속 및 사거리 급감)")

    @classmethod
    def calculate_flight_time(cls, distance_m: float, projectile_speed_mps: float = 60.0) -> float:
        """투사체 비행 시간(초) 계산: t = d / v."""
        if distance_m <= 0.0:
            return 0.0
        speed = max(5.0, projectile_speed_mps)
        return round(distance_m / speed, 3)

    @classmethod
    def evaluate_attack_physics(
        cls,
        attacker: Any,
        defender: Any,
        weapon: Optional[Any] = None,
        attack_tags: Optional[List[str]] = None,
        distance_charge_m: float = 0.0,
        target_current_action: str = ""
    ) -> AttackPhysicsResult:
        """
        태그 기반 물리 공격 연산.
        - thrust: 관통력 + 돌진 가속도 운동에너지 (E = 0.5 * m * v^2)
        - slash: 가속도 비례 절단 및 출혈
        - blunt / strike: 충격량(p = mv), 뼈 골절 위험, 높은 피격 저지력(stagger)
        - jab: 0.15초 초고속 타격, 피해는 낮으나 상대 영창/활 시위 즉각 캔슬
        - straight: 전신 체중 이동 강타, 넉백 및 뇌진탕
        - projectile: 탄속 및 장력 비례 피해
        """
        tags = list(attack_tags or [])
        if weapon and hasattr(weapon, "physics_tags") and weapon.physics_tags:
            for t in weapon.physics_tags:
                if t not in tags:
                    tags.append(t)

        # 기본 공격력 산출
        base_dmg = getattr(weapon, "damage", 5) if weapon else 4
        attacker_str = getattr(attacker, "effective_strength", getattr(attacker, "strength", 10))
        attacker_agi = getattr(attacker, "effective_agility", getattr(attacker, "agility", 10))
        defender_con = getattr(defender, "effective_constitution", getattr(defender, "constitution", 10))
        defender_poise = getattr(defender, "effective_poise", getattr(defender, "poise", 0.0))

        speed_mps = StatEngine.calculate_movement_speed(attacker_agi)
        physics_bonus = 0.0
        armor_pen_pct = 0.0
        stagger = getattr(weapon, "stagger_power", 5.0) if weapon else 3.0
        knockback_m = 0.0
        interrupted = False
        interrupt_reason = ""
        bleed = False
        bone_fracture = False
        flight_time = 0.0
        summary_parts = []

        # 1. Projectile (원거리/투사체)
        if "projectile" in tags:
            draw_lbs = getattr(weapon, "draw_weight_lbs", 50.0) if weapon else 50.0
            can_full, draw_ratio, draw_msg = cls.can_draw_bow(attacker_str, draw_lbs)
            effective_lbs = draw_lbs * draw_ratio
            physics_bonus += (effective_lbs - 40.0) * 0.12
            armor_pen_pct += min(0.5, effective_lbs * 0.003)
            summary_parts.append(f"투사체 발사 ({draw_msg})")

        # 2. Thrust (찌르기) & Charge Momentum
        if "thrust" in tags:
            armor_pen_pct += 0.35  # 좁은 면적 집중 압력: 35% 방어력 관통
            if distance_charge_m >= 3.0:
                # 운동에너지 E_k = 1/2 * m * v^2 비례 관통
                charge_momentum_bonus = 0.5 * (speed_mps ** 2) * 0.08
                physics_bonus += charge_momentum_bonus
                armor_pen_pct += min(0.35, distance_charge_m * 0.05)
                stagger += 8.0
                summary_parts.append(f"{distance_charge_m:.1f}m 돌진 가속 찌르기 (+{charge_momentum_bonus:.1f} 운동에너지 피해)")
            else:
                summary_parts.append("정밀 관통 찌르기 (방어구 35% 관통)")

        # 3. Slash (참격/베기)
        if "slash" in tags:
            agi_bonus = max(0, attacker_agi - 10) * 0.8
            physics_bonus += agi_bonus
            # 민첩 기반 절단 및 출혈
            if attacker_agi >= 12:
                bleed = True
                summary_parts.append("예리한 궤적의 참격 (출혈 유발)")
            else:
                summary_parts.append("수평 참격")

        # 4. Blunt / Strike (타격/둔기)
        if "blunt" in tags or "strike" in tags:
            str_bonus = max(0, attacker_str - 10) * 1.2
            physics_bonus += str_bonus
            stagger += 15.0 + (attacker_str - 10) * 1.5
            if attacker_str >= 14:
                bone_fracture = True
                summary_parts.append(f"육중한 둔기 충격량 (뼈 골절 위험, 피격 저지력 {stagger:.1f})")
            else:
                summary_parts.append(f"묵직한 타격 (피격 저지력 {stagger:.1f})")

        # 5. Jab (초고속 잽 견제)
        if "jab" in tags:
            # 피해는 40%로 축소되나, 0.15초 찰나에 적의 행동 즉시 캔슬
            base_dmg = max(1, int(base_dmg * 0.4))
            physics_bonus *= 0.3
            stagger += 4.0
            interrupted = True
            interrupt_reason = "초고속 잽이 안면에 꽂혀 영창/시위 당기기가 즉각 불발 캔슬됨!"
            summary_parts.append("0.15초 초고속 견제 잽 (적 행동 즉각 캔슬)")

        # 6. Straight (스트레이트/정권 강타)
        if "straight" in tags:
            weight_transfer = max(1.0, (attacker_str - 10) * 0.6)
            physics_bonus += weight_transfer
            stagger += 10.0
            knockback_m = max(0.5, round((attacker_str - defender_con) * 0.3 + 1.0, 1))
            summary_parts.append(f"체중 이동 스트레이트 ({knockback_m}m 넉백)")

        # 피격 저지력 vs 방어자 강인도 판정
        if stagger > defender_poise:
            if not interrupted and ("영창" in target_current_action or "조준" in target_current_action or "시위" in target_current_action):
                interrupted = True
                interrupt_reason = f"피격 저지력({stagger:.1f})이 상대 강인도({defender_poise:.1f})를 초과하여 경직 캔슬 발생!"

        total_dmg = max(1, int(round(base_dmg + physics_bonus)))
        summary_ko = " | ".join(summary_parts) if summary_parts else "기본 물리 공격"

        return AttackPhysicsResult(
            base_damage=base_dmg,
            physics_damage_bonus=round(physics_bonus, 2),
            total_damage=total_dmg,
            armor_penetration_pct=round(min(0.9, armor_pen_pct), 2),
            stagger_inflicted=round(stagger, 1),
            knockback_m=knockback_m,
            tags_applied=tags,
            interrupted_action=interrupted,
            interrupt_reason=interrupt_reason,
            bleed_inflicted=bleed,
            bone_fracture_risk=bone_fracture,
            flight_time_seconds=flight_time,
            summary_ko=summary_ko,
        )
