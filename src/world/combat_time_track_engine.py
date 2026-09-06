"""
Meter-Based Combat Distance & Action Time-Track Engine for Quilltale TRPG.
Replaces fixed 6-second rounds with dynamic second-based action ticks,
meter-based distance matrices (up to 150m+ extreme-range), and Perception-gated
Option A reaction interrupt triggers.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import math

from src.world.state import WorldState
from src.world.dice import DiceEngine
from src.world.stat_engine import StatEngine


# 5 Distance Zones
DISTANCE_ZONES: Dict[str, Dict[str, Any]] = {
    "melee": {
        "name_ko": "초근접 (0~2m)",
        "min_m": 0.0,
        "max_m": 2.0,
        "description": "즉각 칼질 및 육탄전 거리. 원거리 사격 시 대폭 명중 페널티(-5).",
    },
    "close": {
        "name_ko": "근거리 (3~8m)",
        "min_m": 2.0,
        "max_m": 8.0,
        "description": "1초 내 도약/돌진 참격 거리. 투척 무기 유효 사거리.",
    },
    "mid_range": {
        "name_ko": "중거리 (9~20m)",
        "min_m": 8.0,
        "max_m": 20.0,
        "description": "일반 마법 탄환 및 단궁 교전 사거리.",
    },
    "long_range": {
        "name_ko": "원거리 (21~50m)",
        "min_m": 20.0,
        "max_m": 50.0,
        "description": "장궁 및 장거리 저격 마법 유효 사거리.",
    },
    "extreme_range": {
        "name_ko": "초장거리 (51~150m+)",
        "min_m": 50.0,
        "max_m": 999.0,
        "description": "성벽 공성궁, 초원 저격, 보이지 않는 지평선 너머의 척후 화살비.",
    },
}


@dataclass
class CombatDistanceManager:
    TRAITS: List[str] = field(default_factory=lambda: [
        "미터 거리 매트릭스",
        "5대 사거리 구간",
        "초장거리 지원",
        "동적 상대 좌표"
    ])
    traits: List[str] = field(default_factory=lambda: [
        "미터 거리 매트릭스",
        "5대 사거리 구간",
        "초장거리 지원",
        "동적 상대 좌표"
    ])

    @classmethod
    def get_distance(cls, state: WorldState, id_a: str, id_b: str, default: float = 5.0) -> float:
        """두 엔티티 간 거리(m) 반환."""
        return state.get_distance(id_a, id_b, default=default)

    @classmethod
    def set_distance(cls, state: WorldState, id_a: str, id_b: str, distance_m: float) -> None:
        """두 엔티티 간 거리(m) 설정."""
        state.set_distance(id_a, id_b, distance_m)

    @classmethod
    def get_distance_zone(cls, distance_m: float) -> str:
        """거리(m)에 해당하는 영문 존 키 반환."""
        if distance_m <= 2.0:
            return "melee"
        elif distance_m <= 8.0:
            return "close"
        elif distance_m <= 20.0:
            return "mid_range"
        elif distance_m <= 50.0:
            return "long_range"
        else:
            return "extreme_range"

    @classmethod
    def get_distance_zone_ko(cls, distance_m: float) -> str:
        """거리(m)에 해당하는 한글 사거리 구간명 반환."""
        z_key = cls.get_distance_zone(distance_m)
        return DISTANCE_ZONES[z_key]["name_ko"]

    @classmethod
    def move_towards(
        cls,
        state: WorldState,
        mover_id: str,
        target_id: str,
        speed_mps: float,
        seconds: float
    ) -> float:
        """상대를 향해 접근 이동 (거리 감소). 최소 거리 0.0m."""
        cur_dist = cls.get_distance(state, mover_id, target_id)
        travelled = speed_mps * seconds
        new_dist = max(0.0, cur_dist - travelled)
        cls.set_distance(state, mover_id, target_id, new_dist)
        return new_dist

    @classmethod
    def move_away(
        cls,
        state: WorldState,
        mover_id: str,
        target_id: str,
        speed_mps: float,
        seconds: float
    ) -> float:
        """상대로부터 후퇴/거리 벌리기 (거리 증가)."""
        cur_dist = cls.get_distance(state, mover_id, target_id)
        travelled = speed_mps * seconds
        new_dist = cur_dist + travelled
        cls.set_distance(state, mover_id, target_id, new_dist)
        return new_dist


@dataclass
class CombatAction:
    entity_id: str
    action_name: str
    start_second: float
    duration_seconds: float
    target_id: Optional[str] = None
    is_interruptible: bool = True
    payload: Dict[str, Any] = field(default_factory=dict)
    traits: List[str] = field(default_factory=lambda: ["전투 액션 타임트랙"])

    @property
    def end_second(self) -> float:
        return self.start_second + self.duration_seconds


@dataclass
class InterruptEvent:
    perceived_at_second: float
    victim_id: str
    threat_source_id: str
    threat_action_name: str
    time_remaining_seconds: float
    distance_at_perception_m: float
    perception_margin: int
    narrative_ko: str
    options_ko: List[str]
    traits: List[str] = field(default_factory=lambda: ["A안 인지 인터럽트 사건"])


@dataclass
class ActionTimeTrackEngine:
    TRAITS: List[str] = field(default_factory=lambda: [
        "액션 타임트랙",
        "A안 인지 인터럽트",
        "초 단위 시뮬레이션",
        "위기 지각 판정"
    ])
    traits: List[str] = field(default_factory=lambda: [
        "액션 타임트랙",
        "A안 인지 인터럽트",
        "초 단위 시뮬레이션",
        "위기 지각 판정"
    ])

    @classmethod
    def check_perception_interrupt(
        cls,
        state: WorldState,
        victim: Any,
        threat_source: Any,
        action: CombatAction,
        distance_m: float,
        is_surprise: bool = False
    ) -> Optional[InterruptEvent]:
        """
        [A안 원칙]: 피해자가 위협을 '인지(Perceive)'했을 때만 턴 정지 및 인터럽트 발생!
        - 감각(Perception) 주사위 판정: d20 + PER modifier vs DC
        - 거리, 은폐, 기습 여부에 따라 DC 결정
        - 감각이 매우 높으면(PER 15+) 초기 0.1~0.2초 시점에 즉각 인지 -> 여유로운 회피/반격
        - 감각이 보통이면 중간 지점에서 인지 -> 긴급 방어만 가능
        - 판정 대실패/완전 기습: 인지하지 못하므로 턴 정지 없음! 그대로 피격.
        """
        victim_id = getattr(victim, "id", getattr(victim, "name", "player"))
        source_id = getattr(threat_source, "id", getattr(threat_source, "name", "enemy"))

        victim_per = getattr(victim, "effective_perception", getattr(victim, "perception", 10))
        per_mod = (victim_per - 10) // 2

        # DC 결정: 기본 DC 12 (거리 및 기습에 따른 가감)
        base_dc = 12
        if distance_m >= 50.0:
            base_dc += 4  # 초장거리: 화살 식별 어려움
        elif distance_m >= 20.0:
            base_dc += 2  # 원거리
        elif distance_m <= 3.0:
            base_dc -= 2  # 코앞

        if is_surprise:
            base_dc += 6  # 기습 암살

        roll = DiceEngine.roll_d20()
        total = roll + per_mod
        margin = total - base_dc

        if margin < 0:
            # 인지 실패! 턴 정지 없음 (뒤통수 직격 또는 불의의 기습)
            return None

        # 인지 성공 시점 산출: margin과 PER이 높을수록 극초반에 인지
        total_duration = max(0.1, action.duration_seconds)
        if victim_per >= 15:
            # 인간 정점의 감각: 발사/출발 직후 15~20% 시점에 즉시 포착
            ratio = 0.15
        elif margin >= 5:
            # 뛰어난 포착: 30% 시점에 포착
            ratio = 0.30
        else:
            # 턱걸이 인지: 70% 시점에 포착 (코앞에 닥쳐서야 알아챔)
            ratio = 0.70

        perceived_second = round(action.start_second + total_duration * ratio, 2)
        remaining_time = round(total_duration * (1.0 - ratio), 2)
        distance_at_perception = max(0.5, round(distance_m * (1.0 - ratio), 1))

        if ratio <= 0.2:
            desc = (
                f"예리한 감각({victim_per})으로 {distance_m:.1f}m 밖에서 날아드는 "
                f"[{action.action_name}]의 궤적을 출발 찰나에 즉각 포착했습니다! (남은 여유: {remaining_time:.2f}초)"
            )
            options = [
                f"화살/칼날 쳐내기 (반격 패링)",
                f"몸을 굴려 측면 도약 회피 ({distance_at_perception:.1f}m)",
                f"방패 전면 전개 방어",
                f"반대편 엄폐물 뒤로 질주"
            ]
        elif ratio <= 0.4:
            desc = (
                f"공기를 가르는 날카로운 파열음에 {distance_at_perception:.1f}m 전방에서 "
                f"급습해오는 [{action.action_name}]을 인지했습니다! (남은 대응 시간: {remaining_time:.2f}초)"
            )
            options = [
                f"긴급 방패/무기 가드 올리기",
                f"바닥으로 급격히 엎드리기",
                f"시전 중인 행동 즉각 캔슬하고 회피"
            ]
        else:
            desc = (
                f"코앞 {distance_at_perception:.1f}m까지 육박한 찰나, 서늘한 살기에 간신히 반응했습니다! "
                f"(극도로 촉박: {remaining_time:.2f}초)"
            )
            options = [
                f"치명타를 피하기 위해 몸을 비틀어 어깨로 받아내기",
                f"본능적인 긴급 쳐내기"
            ]

        return InterruptEvent(
            perceived_at_second=perceived_second,
            victim_id=victim_id,
            threat_source_id=source_id,
            threat_action_name=action.action_name,
            time_remaining_seconds=remaining_time,
            distance_at_perception_m=distance_at_perception,
            perception_margin=margin,
            narrative_ko=desc,
            options_ko=options,
        )
