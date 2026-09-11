"""
Sleep Deprivation & Circadian Clock Engine for Quilltale TRPG.
Deterministic calculation of continuous wakefulness, sleep deprivation stages (24h/48h/72h),
microsleep sudden collapses, stimulant tolerance & withdrawal crash,
and realistic bedding quality recovery physics.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging
import random

logger = logging.getLogger(__name__)


@dataclass
class CircadianClock:
    awake_turns: int = 0                  # 연속 각성 턴수 (1시간 = 약 3턴 또는 1턴=20분)
    awake_hours: float = 0.0              # 연속 각성 시간 (hours)
    deprivation_tier: int = 0             # 0: 정상, 1: 경도(24h+), 2: 중등도(48h+), 3: 급성 착란/실신(72h+)
    active_stimulant_turns: int = 0       # 각성제 약효 잔여 턴수
    stimulant_id: Optional[str] = None    # 복용한 각성제 종류
    crash_pending: bool = False           # 약효 종료 시 피로 폭풍(Crash) 대기 플래그
    tolerance: float = 0.0                # 각성제 내성치 (0~100)
    microsleep_occurred_this_turn: bool = False # 이번 턴 미세수면 발생 여부
    traits: List[str] = field(default_factory=lambda: ["circadian_clock", "sleep_physiology"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "awake_turns": self.awake_turns,
            "awake_hours": self.awake_hours,
            "deprivation_tier": self.deprivation_tier,
            "active_stimulant_turns": self.active_stimulant_turns,
            "stimulant_id": self.stimulant_id,
            "crash_pending": self.crash_pending,
            "tolerance": self.tolerance,
            "microsleep_occurred_this_turn": self.microsleep_occurred_this_turn,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CircadianClock":
        return cls(
            awake_turns=int(data.get("awake_turns", 0)),
            awake_hours=float(data.get("awake_hours", 0.0)),
            deprivation_tier=int(data.get("deprivation_tier", 0)),
            active_stimulant_turns=int(data.get("active_stimulant_turns", 0)),
            stimulant_id=data.get("stimulant_id"),
            crash_pending=bool(data.get("crash_pending", False)),
            tolerance=float(data.get("tolerance", 0.0)),
            microsleep_occurred_this_turn=bool(data.get("microsleep_occurred_this_turn", False)),
            traits=data.get("traits", ["circadian_clock", "sleep_physiology"]),
        )


@dataclass
class StimulantSpec:
    stimulant_id: str
    name_ko: str
    duration_turns: int                   # 각성 지속 턴수
    fatigue_suppression: int              # 일시 피로도 억제 수치
    crash_fatigue_penalty: int            # 약효 소진 시 반동 피로도
    tolerance_gain: float                 # 복용 시 내성 축적치
    traits: List[str] = field(default_factory=list)


STIMULANTS_REGISTRY: Dict[str, StimulantSpec] = {
    "black_coffee": StimulantSpec(
        stimulant_id="black_coffee",
        name_ko="진한 쓴물 커피",
        duration_turns=15,
        fatigue_suppression=20,
        crash_fatigue_penalty=25,
        tolerance_gain=5.0,
        traits=["stimulant", "beverage", "caffeine"]
    ),
    "stimulant_herb": StimulantSpec(
        stimulant_id="stimulant_herb",
        name_ko="야생 각성초",
        duration_turns=25,
        fatigue_suppression=35,
        crash_fatigue_penalty=40,
        tolerance_gain=12.0,
        traits=["stimulant", "herb", "heart_palpitation"]
    ),
    "arcane_elixir": StimulantSpec(
        stimulant_id="arcane_elixir",
        name_ko="마나 비전 각성제",
        duration_turns=40,
        fatigue_suppression=60,
        crash_fatigue_penalty=70,
        tolerance_gain=25.0,
        traits=["stimulant", "alchemy", "severe_crash"]
    )
}


@dataclass
class BeddingQualitySpec:
    bedding_id: str
    name_ko: str
    recovery_efficiency: float            # 회로/피로 회복 효율 (0.35 ~ 1.35)
    stress_relief: int                    # 스트레스 완화치
    hypothermia_risk: bool                # 맨땅 저체온증 노출 위험
    traits: List[str] = field(default_factory=list)


BEDDING_REGISTRY: Dict[str, BeddingQualitySpec] = {
    "bare_ground": BeddingQualitySpec(
        bedding_id="bare_ground",
        name_ko="맨땅/진흙 노숙",
        recovery_efficiency=0.35,
        stress_relief=-5,                 # 맨땅 노숙은 오히려 스트레스 유발
        hypothermia_risk=True,
        traits=["bedding", "hardcore", "ground", "cold_exposure"]
    ),
    "leather_bedroll": BeddingQualitySpec(
        bedding_id="leather_bedroll",
        name_ko="가죽 모포 침낭",
        recovery_efficiency=0.70,
        stress_relief=5,
        hypothermia_risk=False,
        traits=["bedding", "portable", "bedroll"]
    ),
    "inn_bed": BeddingQualitySpec(
        bedding_id="inn_bed",
        name_ko="여관 보통 침대",
        recovery_efficiency=1.00,
        stress_relief=15,
        hypothermia_risk=False,
        traits=["bedding", "shelter", "inn"]
    ),
    "luxury_feather_bed": BeddingQualitySpec(
        bedding_id="luxury_feather_bed",
        name_ko="귀족 깃털 침대",
        recovery_efficiency=1.35,
        stress_relief=30,
        hypothermia_risk=False,
        traits=["bedding", "luxury", "feather", "super_rest"]
    )
}


class SleepDeprivationEngine:
    """
    Deterministic Sleep Deprivation, Microsleep, Stimulant, and Circadian Engine.
    """

    @classmethod
    def get_clock(cls, target: Any) -> CircadianClock:
        """Retrieves or initializes CircadianClock for target."""
        if not hasattr(target, "circadian") or target.circadian is None:
            target.circadian = CircadianClock()
        elif isinstance(target.circadian, dict):
            target.circadian = CircadianClock.from_dict(target.circadian)
        return target.circadian

    @classmethod
    def process_turn_circadian(cls, state: Any, delta_minutes: int = 20) -> List[str]:
        """
        Advances wakefulness by delta_minutes (~20 minutes = 1 turn, 3 turns = 1 hour).
        """
        logs = []
        player = getattr(state, "player", None)
        if not player:
            return logs

        clock = cls.get_clock(player)
        clock.microsleep_occurred_this_turn = False
        added_turns = max(1, round(delta_minutes / 20.0))
        prev_awake = clock.awake_turns
        clock.awake_turns += added_turns
        clock.awake_hours = round(clock.awake_turns / 3.0, 1)

        # 1. Stimulant Timer Countdown & Crash Trigger
        if clock.active_stimulant_turns > 0:
            clock.active_stimulant_turns = max(0, clock.active_stimulant_turns - added_turns)
            if clock.active_stimulant_turns == 0 and clock.crash_pending:
                clock.crash_pending = False
                stim_spec = STIMULANTS_REGISTRY.get(clock.stimulant_id or "")
                crash_penalty = stim_spec.crash_fatigue_penalty if stim_spec else 30
                player.fatigue = min(100, player.fatigue + crash_penalty)
                logs.append(
                    f"💀 [각성제 약효 소진 - 피로 폭풍(Crash)] 각성제의 흥분 효과가 완전히 끝나며 "
                    f"억눌려 있던 극심한 피로가 한꺼번에 몰려옵니다! (피로도 +{crash_penalty} ➔ 현재 {player.fatigue}/100)"
                )
                clock.stimulant_id = None

        # 2. Update Deprivation Tier
        prev_tier = clock.deprivation_tier
        if clock.awake_hours >= 72.0:
            clock.deprivation_tier = 3  # 급성 착란 및 환각
        elif clock.awake_hours >= 48.0:
            clock.deprivation_tier = 2  # 미세수면 및 반사 저하
        elif clock.awake_hours >= 24.0:
            clock.deprivation_tier = 1  # 경미한 주의 산만
        else:
            clock.deprivation_tier = 0

        # Tier Escalation Notice
        if clock.deprivation_tier > prev_tier:
            if clock.deprivation_tier == 1:
                logs.append(f"🥱 [수면 결핍 1단계: 24시간 무수면] 눈꺼풀이 무거워지고 초점이 흐려집니다. (명중/지각 -2)")
            elif clock.deprivation_tier == 2:
                logs.append(f"😵‍💫 [수면 결핍 2단계: 48시간 무수면] 뇌의 신호 전달이 지연되며 순간적으로 졸도하는 '미세수면' 위험이 발생합니다! (회피 DC +4, 미세수면 15%)")
            elif clock.deprivation_tier == 3:
                logs.append(f"👁️‍🗨️ [수면 결핍 3단계: 72시간 무수면 - 급성 착란] 헛것이 보이고 속삭임이 들립니다. 뇌 기능이 붕괴 직전이며 언제 쓰러져도 이상하지 않습니다! (미세수면 35%, 심장마비 위험)")

        # In-Turn Passive Fatigue Gain
        if clock.active_stimulant_turns == 0:
            boundaries = (clock.awake_turns // 6) - (prev_awake // 6)
            if boundaries > 0:
                fatigue_inc = (1 + clock.deprivation_tier) * boundaries
                player.fatigue = min(100, player.fatigue + fatigue_inc)

        return logs

    @classmethod
    def check_microsleep(cls, player: Any, state: Optional[Any] = None) -> Tuple[bool, str]:
        """
        Rolls for sudden microsleep in Tier 2 or 3.
        If triggered, player loses their action and drops defense.
        """
        clock = cls.get_clock(player)

        # Stimulant temporarily prevents microsleep
        if clock.active_stimulant_turns > 0:
            return False, ""

        chance = 0.0
        if clock.deprivation_tier == 2:
            chance = 0.15
        elif clock.deprivation_tier == 3:
            chance = 0.35

        if chance > 0.0 and random.random() < chance:
            clock.microsleep_occurred_this_turn = True
            msg = (
                "💤 [미세수면(Microsleep) 격발!] 극심한 수면 결핍으로 인해 순간적으로 뇌의 전원이 꺼지며 "
                "고개가 푹 꺾였습니다! 이번 턴의 행동이 강제로 취소되며 무방비 상태에 빠집니다!"
            )
            return True, msg

        return False, ""

    @classmethod
    def apply_stimulant(
        cls,
        target: Any,
        stimulant_id: str
    ) -> Tuple[bool, str]:
        """
        Consumes stimulant to temporarily relieve fatigue.
        """
        stim_spec = STIMULANTS_REGISTRY.get(stimulant_id)
        if not stim_spec:
            return False, "유효하지 않은 각성제입니다."

        clock = cls.get_clock(target)
        target.fatigue = max(0, target.fatigue - stim_spec.fatigue_suppression)
        clock.active_stimulant_turns = stim_spec.duration_turns
        clock.stimulant_id = stimulant_id
        clock.crash_pending = True
        clock.tolerance = min(100.0, clock.tolerance + stim_spec.tolerance_gain)

        return True, (
            f"☕ [{stim_spec.name_ko} 복용] 신경계가 강제로 흥분되며 피로가 {stim_spec.fatigue_suppression} 억제되었습니다. "
            f"({stim_spec.duration_turns}턴 동안 졸음 및 미세수면 면역. 약효 종료 시 피로 반동 발생 예정)"
        )

    @classmethod
    def resolve_sleep(
        cls,
        target: Any,
        bedding_id: str = "leather_bedroll",
        hours: int = 8,
        state: Optional[Any] = None
    ) -> List[str]:
        """
        Resolves sleeping and resting for a given number of hours.
        """
        logs = []
        clock = cls.get_clock(target)
        bedding = BEDDING_REGISTRY.get(bedding_id, BEDDING_REGISTRY["leather_bedroll"])

        # Check ambient cold during bare ground sleep
        if bedding.hypothermia_risk and state:
            temp = getattr(target, "body_temperature", 36.5)
            if temp <= 35.0:
                logs.append("❄️ 차가운 맨땅의 한기가 뼛속까지 스며들어 수면 중 극심한 오한과 저체온증에 시달렸습니다!")
                target.health = max(1, target.health - 5)

        # Calculate Fatigue Recovery
        base_recovery = hours * 12.0
        effective_recovery = int(base_recovery * bedding.recovery_efficiency)
        prev_fatigue = target.fatigue
        target.fatigue = max(0, target.fatigue - effective_recovery)

        # Reset Continuous Wakefulness
        if hours >= 7:
            clock.awake_turns = 0
            clock.awake_hours = 0.0
        else:
            hours_slept_turns = hours * 6
            clock.awake_turns = max(0, clock.awake_turns - hours_slept_turns)
            clock.awake_hours = round(clock.awake_turns / 3.0, 1)
        clock.deprivation_tier = 0 if clock.awake_hours < 24.0 else (1 if clock.awake_hours < 48.0 else 2)
        clock.active_stimulant_turns = 0
        clock.crash_pending = False

        logs.append(
            f"🛌 [{bedding.name_ko}에서 {hours}시간 수면 완료] "
            f"피로도가 {prev_fatigue - target.fatigue} 회복되어 {target.fatigue}/100이 되었습니다. "
            f"(누적 무수면 시간 초기화 ➔ 현재 {clock.awake_hours:.1f}h)"
        )

        return logs
