"""
Deterministic Posture, Poise, and Guard Break Impact Engine for Quilltale TRPG.
Models Sekiro-style posture mechanics:
1. Multi-source Posture Damage:
   - Physical attack impact (heavy bonus when blocked, blunt/strike high poise dmg).
   - Magic elemental impact (explosive blasts destabilize center of mass).
   - Mental/fear shock (destabilizes psychological balance and stance).
2. Sekiro-style Posture Recovery:
   - Natural recovery scaled by current stamina ratio.
   - Guard stance accelerates recovery 2.0x.
   - Stamina 0 (exhaustion) completely halts posture recovery.
3. Time-based Guard Break Stun (User Decision Q3):
   - Base 1.0s vulnerability stun.
   - Scales up with longer combat duration (+0.5s per min) and lower current stamina (+1.5s max).
   - Guaranteed critical hit on next attack during guard break.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class PosturePoiseState:
    max_posture: float = 100.0                  # 최대 체간 수치 (유효 강인도 기반 스케일)
    current_posture_damage: float = 0.0         # 누적된 체간 피해량 (0.0 ~ max_posture)
    is_guard_broken: bool = False               # 가드 브레이크 (자세 붕괴) 상태 여부
    guard_break_seconds_remaining: float = 0.0  # 가드 브레이크 무방비 기절 잔여 시간 (초)
    is_blocking_stance: bool = False            # 가드/방어 태세 유지 여부 (회복 속도 2배)
    combat_duration_seconds: float = 0.0        # 전투 누적 지속 시간 (초)
    traits: List[str] = field(default_factory=lambda: ["posture_poise", "guard_break", "sekiro_mechanics"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_posture": round(self.max_posture, 1),
            "current_posture_damage": round(self.current_posture_damage, 1),
            "is_guard_broken": self.is_guard_broken,
            "guard_break_seconds_remaining": round(self.guard_break_seconds_remaining, 2),
            "is_blocking_stance": self.is_blocking_stance,
            "combat_duration_seconds": round(self.combat_duration_seconds, 1),
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "PosturePoiseState":
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            data = {}
        return cls(
            max_posture=float(data.get("max_posture", 100.0)),
            current_posture_damage=float(data.get("current_posture_damage", 0.0)),
            is_guard_broken=bool(data.get("is_guard_broken", False)),
            guard_break_seconds_remaining=float(data.get("guard_break_seconds_remaining", 0.0)),
            is_blocking_stance=bool(data.get("is_blocking_stance", False)),
            combat_duration_seconds=float(data.get("combat_duration_seconds", 0.0)),
            traits=list(data.get("traits", ["posture_poise", "guard_break", "sekiro_mechanics"])),
        )


class PosturePoiseEngine:
    """
    Deterministic Posture & Poise Engine.
    Calculates impact buildup from physical, magical, and psychological sources,
    manages Sekiro-style stamina-linked recovery, and handles scaling time-based guard breaks.
    """

    @classmethod
    def get_state(cls, character: Any) -> PosturePoiseState:
        raw = getattr(character, "posture_state", None)
        eff_poise = getattr(character, "effective_poise", getattr(character, "poise", 0.0))
        calculated_max = max(50.0, 100.0 + eff_poise * 2.0)

        if raw is None or not isinstance(raw, (dict, PosturePoiseState)):
            state_obj = PosturePoiseState(max_posture=calculated_max)
            character.posture_state = state_obj.to_dict()
            return state_obj
        if isinstance(raw, dict):
            state_obj = PosturePoiseState.from_dict(raw)
            state_obj.max_posture = calculated_max
            return state_obj
        raw.max_posture = calculated_max
        return raw

    @classmethod
    def sync_state(cls, character: Any, state_obj: PosturePoiseState):
        character.posture_state = state_obj.to_dict()

    @classmethod
    def set_blocking_stance(cls, character: Any, is_blocking: bool) -> str:
        state = cls.get_state(character)
        state.is_blocking_stance = is_blocking
        cls.sync_state(character, state)
        if is_blocking:
            return "🛡️ [가드 자세] 방어 태세를 취했습니다. 체간 회복 속도가 2배로 증가하지만 막을 때 체간 충격이 집중됩니다."
        else:
            return "방어 자세를 풀고 기본 전투 태세로 전환했습니다."

    @classmethod
    def tick_combat_duration(cls, character: Any, delta_seconds: float):
        state = cls.get_state(character)
        state.combat_duration_seconds += delta_seconds
        cls.sync_state(character, state)

    @classmethod
    def _calculate_guard_break_stun(cls, character: Any, state: PosturePoiseState) -> float:
        """
        User Decision Q3:
        Base 1.0 second stun.
        Scales longer as combat duration increases and as stamina depletes.
        """
        stamina = float(getattr(character, "stamina", 100))
        max_stamina = max(1.0, float(getattr(character, "max_stamina", 100)))
        stamina_ratio = max(0.0, min(1.0, stamina / max_stamina))

        # Combat duration factor: +0.5s per 60 seconds of combat (capped at +2.0s)
        duration_factor = min(2.0, (state.combat_duration_seconds / 60.0) * 0.5)

        # Stamina depletion factor: up to +1.5s when completely exhausted
        stamina_depletion_factor = (1.0 - stamina_ratio) * 1.5

        total_stun = 1.0 + duration_factor + stamina_depletion_factor
        return round(total_stun, 2)

    @classmethod
    def _trigger_guard_break(cls, defender: Any, state: PosturePoiseState) -> List[str]:
        """Triggers guard break and applies scaled stun duration."""
        stun_duration = cls._calculate_guard_break_stun(defender, state)
        state.is_guard_broken = True
        state.guard_break_seconds_remaining = stun_duration
        state.is_blocking_stance = False
        state.current_posture_damage = state.max_posture

        def_name = getattr(defender, "name", "대상")
        logs = [
            f"💥 [가드 브레이크 (Guard Break)] {def_name}의 자세와 체간이 완전히 붕괴되었습니다!",
            f"⚠️ [자세 붕괴 무방비] 방어가 튕겨 나가며 {stun_duration:.2f}초간 완전 무방비 경직에 빠집니다! (다음 피격 시 확정 치명타 +50% 피해)",
        ]
        return logs

    @classmethod
    def apply_physical_impact(
        cls,
        defender: Any,
        attacker: Any = None,
        weapon_type: str = "blunt",
        is_blocked: bool = False,
        impact_override: Optional[float] = None
    ) -> Tuple[bool, List[str]]:
        """
        Applies physical impact to defender's posture meter.
        Blocked hit: absorptive defense transfers heavy posture damage (impact * 1.6).
        Unblocked hit: blunt/straight/heavy strikes deal high posture damage.
        """
        state = cls.get_state(defender)
        logs: List[str] = []

        if impact_override is not None:
            base_impact = impact_override
        else:
            atk_str = getattr(attacker, "effective_strength", getattr(attacker, "strength", 10)) if attacker else 10
            weapon_multipliers = {
                "blunt": 22.0,
                "strike": 20.0,
                "straight": 18.0,
                "slash": 12.0,
                "thrust": 10.0,
                "projectile": 8.0,
            }
            mult = weapon_multipliers.get(weapon_type.lower(), 12.0)
            base_impact = mult + max(0, atk_str - 10) * 1.5

        if is_blocked or state.is_blocking_stance:
            # Blocked attack: Absorbs HP but heaps heavy posture strain
            posture_gain = base_impact * 1.6
            logs.append(f"🛡️ [방어 충격 흡수] 공격을 받아냈으나 방패/무기를 타고 {posture_gain:.1f}의 체간 충격량이 누적되었습니다.")
        else:
            posture_gain = base_impact
            logs.append(f"⚔️ [물리 충격량] 직격으로 인해 중심이 흔들리며 {posture_gain:.1f}의 체간 충격량이 누적되었습니다.")

        state.current_posture_damage += posture_gain

        is_broken = False
        if state.current_posture_damage >= state.max_posture:
            break_logs = cls._trigger_guard_break(defender, state)
            logs.extend(break_logs)
            is_broken = True

        cls.sync_state(defender, state)
        return is_broken, logs

    @classmethod
    def apply_magic_impact(
        cls,
        defender: Any,
        spell_element: str,
        spell_power: float,
        spell_circle: int = 1
    ) -> Tuple[bool, List[str]]:
        """
        Applies magical blast/shockwave impact to posture.
        Heavy kinetic elements (earth, wind, gravity, explosion) cause intense posture destabilization.
        """
        state = cls.get_state(defender)
        logs: List[str] = []

        element_posture_mult = {
            "earth": 1.5, "땅": 1.5,
            "wind": 1.3, "바람": 1.3,
            "gravity": 1.8, "중력": 1.8,
            "fire": 1.2, "불": 1.2,
            "lightning": 1.1, "번개": 1.1,
            "water": 1.0, "물": 1.0,
            "ice": 1.2, "얼음": 1.2,
            "void": 1.4, "공허": 1.4,
        }
        mult = element_posture_mult.get(spell_element.lower(), 1.0)
        posture_gain = (spell_power * 0.5 + spell_circle * 3.0) * mult

        state.current_posture_damage += posture_gain
        logs.append(f"🔮 [원소 마법 충격] {spell_element} 속성 마력 폭압으로 인해 {posture_gain:.1f}의 체간 균형이 무너졌습니다.")

        is_broken = False
        if state.current_posture_damage >= state.max_posture:
            break_logs = cls._trigger_guard_break(defender, state)
            logs.extend(break_logs)
            is_broken = True

        cls.sync_state(defender, state)
        return is_broken, logs

    @classmethod
    def apply_mental_impact(
        cls,
        defender: Any,
        mental_stress: float,
        fear_source: str = "공포/정신적 충격"
    ) -> Tuple[bool, List[str]]:
        """
        Applies psychological/fear destabilization to posture.
        Mental panic weakens muscular balance and defensive stance.
        """
        state = cls.get_state(defender)
        logs: List[str] = []

        # Psychological destabilization ratio (approx 60% of physical force)
        posture_gain = mental_stress * 0.6
        state.current_posture_damage += posture_gain

        def_name = getattr(defender, "name", "대상")
        logs.append(f"🧠 [정신적 동요와 자세 흔들림] {fear_source}으로 인해 {def_name}의 중심 자세가 흔들립니다 (+{posture_gain:.1f} 체간 누적).")

        is_broken = False
        if state.current_posture_damage >= state.max_posture:
            break_logs = cls._trigger_guard_break(defender, state)
            logs.extend(break_logs)
            is_broken = True

        cls.sync_state(defender, state)
        return is_broken, logs

    @classmethod
    def recover_posture_time(cls, character: Any, delta_seconds: float = 1.0) -> List[str]:
        """
        Sekiro-style time-based posture recovery:
        - Recovers at base rate * stamina ratio.
        - Blocking stance accelerates recovery 2.0x.
        - Stamina 0 halts recovery completely.
        - Also decrements guard break stun seconds if broken.
        """
        state = cls.get_state(character)
        logs: List[str] = []

        # If guard broken, tick down stun duration
        if state.is_guard_broken:
            state.guard_break_seconds_remaining = max(0.0, state.guard_break_seconds_remaining - delta_seconds)
            if state.guard_break_seconds_remaining <= 0.0:
                state.is_guard_broken = False
                state.current_posture_damage = state.max_posture * 0.4  # Restores with 40% initial damage
                logs.append("🛡️ [자세 회복] 휘청거리던 몸의 균형을 되찾고 방어 태세로 복귀했습니다.")
            cls.sync_state(character, state)
            return logs

        # Natural Sekiro Recovery
        stamina = float(getattr(character, "stamina", 100))
        max_stamina = max(1.0, float(getattr(character, "max_stamina", 100)))
        stamina_ratio = max(0.0, min(1.0, stamina / max_stamina))

        if stamina <= 0.0:
            # Exhaustion halts recovery
            cls.sync_state(character, state)
            return []

        base_regen_per_sec = 8.0 * stamina_ratio
        if state.is_blocking_stance:
            base_regen_per_sec *= 2.0  # Guard stance acceleration

        recovered = base_regen_per_sec * delta_seconds
        state.current_posture_damage = max(0.0, state.current_posture_damage - recovered)
        cls.sync_state(character, state)
        return logs

    @classmethod
    def recover_posture_turn(cls, character: Any, state: Any = None) -> List[str]:
        """Standard turn tick recovery (simulates 3.0 seconds per turn round)."""
        return cls.recover_posture_time(character, delta_seconds=3.0)

    @classmethod
    def consume_guard_break_crit(cls, defender: Any) -> Tuple[bool, float, str]:
        """
        Checks if defender is in guard break stun:
        If yes, grants guaranteed critical hit and +50% bonus critical damage,
        then terminates the guard break stun early due to the devastating blow impact.
        """
        state = cls.get_state(defender)
        if not state.is_guard_broken:
            return False, 0.0, ""

        # Hit consumed
        state.is_guard_broken = False
        state.guard_break_seconds_remaining = 0.0
        state.current_posture_damage = state.max_posture * 0.5
        cls.sync_state(defender, state)

        return True, 0.50, "💥 [가드 브레이크 치명타 (Posture Critical)] 붕괴된 무방비 틈새로 확정 치명타가 적중했습니다! (+50% 추가 피해)"
