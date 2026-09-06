"""
Campsite Rest & Night Perimeter Defense Engine for Quilltale TRPG.
Deterministic calculation of campsite setup, campfire warmth vs predator/bandit aggro,
perimeter trap detection via intruder perception vs trap DC, sentry shift guard duty,
and sleep recovery integration.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging
import random

logger = logging.getLogger(__name__)


@dataclass
class SentryShift:
    shift_number: int = 1                 # 1교대, 2교대, 3교대
    companion_id: str = ""                # 담당 캐릭터 ID ("player" 또는 npc_id)
    companion_name: str = ""
    perception_bonus: int = 0
    fatigue_cost: int = 15                # 불침번으로 인한 수면 방해 피로도
    traits: List[str] = field(default_factory=lambda: ["sentry_duty", "guard_shift"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shift_number": self.shift_number,
            "companion_id": self.companion_id,
            "companion_name": self.companion_name,
            "perception_bonus": self.perception_bonus,
            "fatigue_cost": self.fatigue_cost,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SentryShift":
        return cls(
            shift_number=int(data.get("shift_number", 1)),
            companion_id=data.get("companion_id", ""),
            companion_name=data.get("companion_name", ""),
            perception_bonus=int(data.get("perception_bonus", 0)),
            fatigue_cost=int(data.get("fatigue_cost", 15)),
            traits=data.get("traits", ["sentry_duty", "guard_shift"]),
        )


@dataclass
class CampsiteState:
    location_id: str = ""
    has_tent: bool = False
    has_perimeter_traps: bool = False     # 경보 방울/나뭇가지 방어 덫
    perimeter_trap_detect_dc: int = 14    # 침입자가 덫을 간파/무력화하기 위한 지각 DC
    campfire_active: bool = False
    campfire_minutes_remaining: int = 0
    aggro_risk: int = 20                  # 야간 기습 위험도 (0~100)
    sentry_shifts: List[SentryShift] = field(default_factory=list)
    traits: List[str] = field(default_factory=lambda: ["campsite", "wilderness_shelter"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "location_id": self.location_id,
            "has_tent": self.has_tent,
            "has_perimeter_traps": self.has_perimeter_traps,
            "perimeter_trap_detect_dc": self.perimeter_trap_detect_dc,
            "campfire_active": self.campfire_active,
            "campfire_minutes_remaining": self.campfire_minutes_remaining,
            "aggro_risk": self.aggro_risk,
            "sentry_shifts": [s.to_dict() for s in self.sentry_shifts],
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CampsiteState":
        raw_shifts = data.get("sentry_shifts", [])
        shifts = [SentryShift.from_dict(s) if isinstance(s, dict) else s for s in raw_shifts]
        return cls(
            location_id=data.get("location_id", ""),
            has_tent=bool(data.get("has_tent", False)),
            has_perimeter_traps=bool(data.get("has_perimeter_traps", False)),
            perimeter_trap_detect_dc=int(data.get("perimeter_trap_detect_dc", 14)),
            campfire_active=bool(data.get("campfire_active", False)),
            campfire_minutes_remaining=int(data.get("campfire_minutes_remaining", 0)),
            aggro_risk=int(data.get("aggro_risk", 20)),
            sentry_shifts=shifts,
            traits=data.get("traits", ["campsite", "wilderness_shelter"]),
        )


@dataclass
class NightAmbushSpec:
    ambush_id: str
    name_ko: str
    attacker_perception: int              # 침입자 감각 스탯 (덫 간파 판정)
    attacker_stealth_dc: int              # 침입자 은신 DC (불침번 지각 대항)
    attacker_count: int
    danger_level: str = "medium"
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ambush_id": self.ambush_id,
            "name_ko": self.name_ko,
            "attacker_perception": self.attacker_perception,
            "attacker_stealth_dc": self.attacker_stealth_dc,
            "attacker_count": self.attacker_count,
            "danger_level": self.danger_level,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NightAmbushSpec":
        return cls(
            ambush_id=data.get("ambush_id", ""),
            name_ko=data.get("name_ko", ""),
            attacker_perception=int(data.get("attacker_perception", 10)),
            attacker_stealth_dc=int(data.get("attacker_stealth_dc", 12)),
            attacker_count=int(data.get("attacker_count", 1)),
            danger_level=data.get("danger_level", "medium"),
            traits=data.get("traits", ["ambush"]),
        )


NIGHT_AMBUSH_REGISTRY: Dict[str, NightAmbushSpec] = {
    "hungry_wolf_pack": NightAmbushSpec(
        ambush_id="hungry_wolf_pack",
        name_ko="굶주린 야생 늑대 무리",
        attacker_perception=13,
        attacker_stealth_dc=12,
        attacker_count=3,
        danger_level="medium",
        traits=["ambush", "beast", "predator", "night"]
    ),
    "bandit_raiders": NightAmbushSpec(
        ambush_id="bandit_raiders",
        name_ko="가도 야습 도적 척후조",
        attacker_perception=15,
        attacker_stealth_dc=15,
        attacker_count=2,
        danger_level="high",
        traits=["ambush", "humanoid", "bandit", "cunning"]
    ),
    "wandering_undead": NightAmbushSpec(
        ambush_id="wandering_undead",
        name_ko="헤매는 밤의 구울",
        attacker_perception=8,
        attacker_stealth_dc=10,
        attacker_count=2,
        danger_level="low",
        traits=["ambush", "undead", "ghoul", "blunt_senses"]
    ),
    "goblin_scavengers": NightAmbushSpec(
        ambush_id="goblin_scavengers",
        name_ko="고블린 야간 도둑 떼",
        attacker_perception=12,
        attacker_stealth_dc=16,
        attacker_count=4,
        danger_level="medium",
        traits=["ambush", "goblin", "thief", "stealthy"]
    )
}


class CampsiteRestEngine:
    """
    Deterministic Campsite, Sentry Guard Duty, and Night Ambush Physics Engine.
    """

    @classmethod
    def get_campsite(cls, state: Any) -> CampsiteState:
        """Retrieves or creates active CampsiteState on WorldState."""
        if not hasattr(state, "active_campsite") or state.active_campsite is None:
            state.active_campsite = CampsiteState(location_id=getattr(state.player, "location", "start"))
        elif isinstance(state.active_campsite, dict):
            state.active_campsite = CampsiteState.from_dict(state.active_campsite)
        return state.active_campsite

    @classmethod
    def setup_campsite(
        cls,
        state: Any,
        has_tent: bool = False,
        has_perimeter_traps: bool = False
    ) -> Tuple[bool, str]:
        """
        Sets up a campsite with optional tent and defensive tripwire traps.
        """
        camp = cls.get_campsite(state)
        camp.location_id = getattr(state.player, "location", "start")
        camp.has_tent = has_tent
        camp.has_perimeter_traps = has_perimeter_traps

        features = []
        if has_tent:
            features.append("방풍/방수 야영 텐트")
        if has_perimeter_traps:
            features.append("외곽 방어 덫 및 경보 방울선 (간파 DC 14)")

        feature_str = f" ({', '.join(features)})" if features else ""
        return True, f"⛺ [야영지 구축 완료] 현재 위치에 안전 숙영지를 마련했습니다.{feature_str}"

    @classmethod
    def light_campfire(cls, state: Any, duration_minutes: int = 240) -> Tuple[bool, str]:
        """
        Lights a campfire. Grants warmth and cooking station, but raises aggro risk.
        """
        camp = cls.get_campsite(state)
        camp.campfire_active = True
        camp.campfire_minutes_remaining = duration_minutes
        camp.aggro_risk = min(100, camp.aggro_risk + 30)

        # ThermalEngine environment heat source link
        if hasattr(state, "environment") and state.environment:
            state.environment.has_heat_source = True

        return True, (
            f"🔥 [모닥불 점화] 장작불을 피워 주변을 밝히고 온기를 확보했습니다. "
            f"({duration_minutes}분 지속 / 열원 및 조리 가능, 야생 맹수 유인 위험도 {camp.aggro_risk}%로 상승)"
        )

    @classmethod
    def assign_sentry_shifts(cls, state: Any, shifts: List[Dict[str, Any]]) -> List[str]:
        """
        Assigns up to 3 sentry shifts.
        """
        camp = cls.get_campsite(state)
        camp.sentry_shifts.clear()
        logs = []

        for s_data in shifts:
            shift_num = s_data.get("shift_number", len(camp.sentry_shifts) + 1)
            char_id = s_data.get("companion_id", "player")
            char_name = s_data.get("companion_name", "플레이어")

            # Determine perception bonus
            per_stat = 10
            if char_id == "player" and hasattr(state, "player"):
                per_stat = getattr(state.player, "perception", 10)
            elif hasattr(state, "party") and char_id in state.party:
                comp = state.party[char_id]
                per_stat = getattr(comp, "perception", 10)

            per_bonus = (per_stat - 10) // 2
            s_obj = SentryShift(
                shift_number=shift_num,
                companion_id=char_id,
                companion_name=char_name,
                perception_bonus=per_bonus,
                fatigue_cost=12
            )
            camp.sentry_shifts.append(s_obj)
            logs.append(f"🛡️ [불침번 배정] {shift_num}교대: [{char_name}] (감각 보정: +{per_bonus})")

        return logs

    @classmethod
    def resolve_campsite_night(
        cls,
        state: Any,
        hours: int = 8,
        bedding_id: str = "leather_bedroll",
        fixed_ambush: Optional[bool] = None,
        fixed_trap_roll: Optional[int] = None,
        fixed_sentry_roll: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Simulates an entire night of rest at the campsite.
        Handles intruder ambush check, perimeter trap detection, sentry alert, and sleep recovery.
        """
        camp = cls.get_campsite(state)
        logs = []
        is_ambushed = False
        ambush_spec: Optional[NightAmbushSpec] = None

        # 1. Determine Ambush Occurrence
        # Aggro risk check
        roll_ambush = random.random() * 100.0 if fixed_ambush is None else (0.0 if fixed_ambush else 100.0)
        if roll_ambush < camp.aggro_risk:
            # Ambush occurs!
            ambush_id = random.choice(list(NIGHT_AMBUSH_REGISTRY.keys()))
            ambush_spec = NIGHT_AMBUSH_REGISTRY[ambush_id]

            logs.append(f"🚨 [야간 기습 발생] 어둠 속에서 [{ambush_spec.name_ko}] {ambush_spec.attacker_count}마리가 야영지를 향해 은밀히 접근합니다!")

            # 2. Perimeter Trap Detection Check (User Rule Q1: Not 100%, Attacker Perception vs Trap DC)
            trap_triggered = False
            trap_bypassed = False
            if camp.has_perimeter_traps:
                trap_roll = random.randint(1, 20) if fixed_trap_roll is None else fixed_trap_roll
                trap_total = trap_roll + (ambush_spec.attacker_perception - 10) // 2

                if trap_total >= camp.perimeter_trap_detect_dc:
                    # Intruder spots and bypasses the trap silently!
                    trap_bypassed = True
                    logs.append(f"🐾 [함정 간파] 침입자가 뛰어난 감각({trap_total} vs DC {camp.perimeter_trap_detect_dc})으로 외곽 방어 덫을 피해 우회했습니다!")
                else:
                    # Trap triggered! Bells ring and alert camp!
                    trap_triggered = True
                    logs.append(f"🔔 [방어 덫 작동!] 침입자가 나뭇가지 덫을 건드려 방어 방울선이 요란하게 울렸습니다! (판정: {trap_total} vs DC {camp.perimeter_trap_detect_dc})")

            # 3. Sentry Alert vs Surprise Attack
            sentry_spotted = False
            if trap_triggered:
                sentry_spotted = True
                logs.append("⚔️ [기습 무력화] 요란한 방울 소리에 불침번과 전원이 즉시 깨어나 무기를 집어 들고 요격 태세를 갖췄습니다!")
            else:
                # Sentry makes Perception check vs attacker stealth DC
                active_sentry = camp.sentry_shifts[0] if camp.sentry_shifts else None
                sentry_bonus = active_sentry.perception_bonus if active_sentry else 0
                s_roll = random.randint(1, 20) if fixed_sentry_roll is None else fixed_sentry_roll
                s_total = s_roll + sentry_bonus

                if active_sentry and s_total >= ambush_spec.attacker_stealth_dc:
                    sentry_spotted = True
                    logs.append(f"👁️ [불침번 조기 포착] 불침번 [{active_sentry.companion_name}]이(가) 어둠 속의 기척을 감지하고 경보를 외쳤습니다! ({s_total} vs 은신 DC {ambush_spec.attacker_stealth_dc})")
                else:
                    sentry_spotted = False
                    is_ambushed = True
                    sentry_name = active_sentry.companion_name if active_sentry else "경계병 없음"
                    logs.append(f"💥 [불시 기습 피격!] {sentry_name}이(가) 침입자를 눈치채지 못해, 잠들어 있던 아군이 무방비 상태(방어구 미착용/다운)로 기습당했습니다!")

            return {
                "rest_completed": False,
                "ambush_triggered": True,
                "is_surprise_attack": is_ambushed,
                "ambush_spec": ambush_spec.to_dict() if ambush_spec else {},
                "logs": logs
            }

        # No ambush -> Peaceful Rest
        logs.append("🌙 [평화로운 밤] 야영지에 아무런 습격 없이 고요한 밤이 지나갔습니다.")

        # Apply sleep recovery via SleepDeprivationEngine
        from src.world.sleep_engine import SleepDeprivationEngine
        sleep_logs = SleepDeprivationEngine.resolve_sleep(state.player, bedding_id=bedding_id, hours=hours, state=state)
        logs.extend(sleep_logs)

        # Deduct campfire duration
        if camp.campfire_active:
            camp.campfire_minutes_remaining = max(0, camp.campfire_minutes_remaining - hours * 60)
            if camp.campfire_minutes_remaining == 0:
                camp.campfire_active = False
                if hasattr(state, "environment") and state.environment:
                    state.environment.has_heat_source = False
                logs.append("💨 밤새 타오르던 모닥불이 잿더미만 남기고 꺼졌습니다.")

        return {
            "rest_completed": True,
            "ambush_triggered": False,
            "is_surprise_attack": False,
            "ambush_spec": {},
            "logs": logs
        }
