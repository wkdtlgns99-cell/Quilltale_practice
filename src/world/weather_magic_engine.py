"""
Weather Magic & Spatiotemporal Environmental Hazard Simulation Engine for Quilltale TRPG.
Deterministic calculation of high-tier elemental weather control (Circle 4+ requirement),
circle-scaled duration (30 min base + 15 min per circle above minimum),
combat turn-based damage/saves vs exploration minute-aggregated cumulative hazard physics.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging
import random

logger = logging.getLogger(__name__)


@dataclass
class WeatherMagicSpec:
    magic_id: str
    name_ko: str
    element: str                          # "얼음", "번개", "화염", "독", "물/어둠"
    min_circle_required: int = 4          # 고위 마법: 최소 4서클 이상 요구
    mana_cost: int = 40
    base_duration_minutes: int = 30       # 기본 30분 지속 (+ 서클당 15분 추가)
    combat_damage_dice: str = "1d6"       # 전투 라운드당 피격 주사위
    combat_save_dc: int = 13              # 민첩/체질 회피 세이브 DC
    travel_damage_per_10min: int = 3      # 탐험 10분당 누적 관통/냉기 피해
    travel_wetness_per_10min: float = 15.0# 탐험 10분당 젖음 증가율
    travel_temp_drop_per_10min: float = 0.5# 탐험 10분당 체온 강하량
    description: str = ""
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "magic_id": self.magic_id,
            "name_ko": self.name_ko,
            "element": self.element,
            "min_circle_required": self.min_circle_required,
            "mana_cost": self.mana_cost,
            "base_duration_minutes": self.base_duration_minutes,
            "combat_damage_dice": self.combat_damage_dice,
            "combat_save_dc": self.combat_save_dc,
            "travel_damage_per_10min": self.travel_damage_per_10min,
            "travel_wetness_per_10min": self.travel_wetness_per_10min,
            "travel_temp_drop_per_10min": self.travel_temp_drop_per_10min,
            "description": self.description,
            "traits": self.traits,
        }


@dataclass
class ActiveWeatherAnomaly:
    anomaly_id: str
    magic_id: str
    name_ko: str
    location_id: str
    remaining_minutes: int
    caster_id: str
    caster_circle: int
    traits: List[str] = field(default_factory=lambda: ["weather_magic", "climate_hazard"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "magic_id": self.magic_id,
            "name_ko": self.name_ko,
            "location_id": self.location_id,
            "remaining_minutes": self.remaining_minutes,
            "caster_id": self.caster_id,
            "caster_circle": self.caster_circle,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActiveWeatherAnomaly":
        return cls(
            anomaly_id=data.get("anomaly_id", ""),
            magic_id=data.get("magic_id", ""),
            name_ko=data.get("name_ko", ""),
            location_id=data.get("location_id", ""),
            remaining_minutes=int(data.get("remaining_minutes", 30)),
            caster_id=data.get("caster_id", ""),
            caster_circle=int(data.get("caster_circle", 4)),
            traits=data.get("traits", ["weather_magic", "climate_hazard"]),
        )


WEATHER_MAGIC_REGISTRY: Dict[str, WeatherMagicSpec] = {
    "icicle_rain": WeatherMagicSpec(
        magic_id="icicle_rain",
        name_ko="창천의 고드름 비",
        element="얼음",
        min_circle_required=4,
        mana_cost=45,
        base_duration_minutes=30,
        combat_damage_dice="1d6",
        combat_save_dc=13,
        travel_damage_per_10min=4,
        travel_wetness_per_10min=20.0,
        travel_temp_drop_per_10min=0.8,
        description="먹구름에서 날카로운 얼음 송곳들이 빗발쳐 내리꽂히는 고위 빙결 기상 마법.",
        traits=["weather_magic", "ice", "piercing", "cold", "high_tier"]
    ),
    "blizzard_veil": WeatherMagicSpec(
        magic_id="blizzard_veil",
        name_ko="극광의 눈보라 장막",
        element="얼음",
        min_circle_required=5,
        mana_cost=55,
        base_duration_minutes=30,
        combat_damage_dice="1d8",
        combat_save_dc=14,
        travel_damage_per_10min=3,
        travel_wetness_per_10min=15.0,
        travel_temp_drop_per_10min=1.2,
        description="영하 수십 도의 눈보라를 전장에 소환하여 시야를 차단하고 동상을 유발하는 한대 마법.",
        traits=["weather_magic", "blizzard", "freezing", "hypothermia", "high_tier"]
    ),
    "thunderstorm_wrath": WeatherMagicSpec(
        magic_id="thunderstorm_wrath",
        name_ko="뇌제 강림의 폭풍우",
        element="번개",
        min_circle_required=6,
        mana_cost=70,
        base_duration_minutes=30,
        combat_damage_dice="1d10",
        combat_save_dc=15,
        travel_damage_per_10min=6,
        travel_wetness_per_10min=25.0,
        travel_temp_drop_per_10min=0.4,
        description="하늘을 찢는 낙뢰와 폭우를 쏟아붓는 파괴적인 대자연의 뇌격 마법.",
        traits=["weather_magic", "lightning", "storm", "shock", "legendary"]
    ),
    "acid_downpour": WeatherMagicSpec(
        magic_id="acid_downpour",
        name_ko="부식성 산성 폭우",
        element="독",
        min_circle_required=5,
        mana_cost=50,
        base_duration_minutes=30,
        combat_damage_dice="1d6",
        combat_save_dc=14,
        travel_damage_per_10min=5,
        travel_wetness_per_10min=10.0,
        travel_temp_drop_per_10min=0.2,
        description="장비와 살점을 녹여내리는 녹색 산성비를 내리게 하는 잔혹한 역병 독술.",
        traits=["weather_magic", "poison", "acid", "corrosion", "high_tier"]
    ),
    "scorching_drought": WeatherMagicSpec(
        magic_id="scorching_drought",
        name_ko="작열하는 태양의 가뭄",
        element="화염",
        min_circle_required=5,
        mana_cost=55,
        base_duration_minutes=30,
        combat_damage_dice="1d6",
        combat_save_dc=13,
        travel_damage_per_10min=2,
        travel_wetness_per_10min=-20.0,
        travel_temp_drop_per_10min=-1.5, # 체온 급상승
        description="대기를 끓어오르게 만들어 습기를 모두 증발시키고 열사병을 강요하는 초열 지옥.",
        traits=["weather_magic", "fire", "drought", "heat_stroke", "high_tier"]
    ),
    "dense_fog_mirage": WeatherMagicSpec(
        magic_id="dense_fog_mirage",
        name_ko="환각의 칠흑 농무",
        element="물/어둠",
        min_circle_required=4,
        mana_cost=40,
        base_duration_minutes=30,
        combat_damage_dice="0d0",
        combat_save_dc=12,
        travel_damage_per_10min=0,
        travel_wetness_per_10min=10.0,
        travel_temp_drop_per_10min=0.3,
        description="방향 감각을 마비시키고 환영을 보게 만드는 짙은 마력 안개.",
        traits=["weather_magic", "fog", "illusion", "stealth", "high_tier"]
    )
}


class WeatherMagicSimulationEngine:
    """
    Deterministic Weather Magic, High-Tier Circle Requirements,
    and Dual-Mode Combat Round / Travel Minute Exposure Resolution Engine.
    """

    @classmethod
    def get_anomalies(cls, state: Any) -> Dict[str, ActiveWeatherAnomaly]:
        """Retrieves or initializes active weather anomalies dictionary on state."""
        if not hasattr(state, "active_weather_anomalies") or state.active_weather_anomalies is None:
            state.active_weather_anomalies = {}
        return state.active_weather_anomalies

    @classmethod
    def cast_weather_magic(
        cls,
        state: Any,
        caster: Any,
        magic_id: str
    ) -> Tuple[bool, str]:
        """
        User Rule Q2: Weather magic is high-tier elemental magic (Circle 4+ required).
        Default 30 min duration + 15 min per circle above minimum.
        """
        spec = WEATHER_MAGIC_REGISTRY.get(magic_id)
        if not spec:
            return False, "존재하지 않는 기상 제어 마법입니다."

        caster_circle = getattr(caster, "mage_circle", 1)
        for t in getattr(caster, "traits", []):
            if "서클" in t:
                digits = "".join(filter(str.isdigit, t))
                if digits:
                    caster_circle = max(caster_circle, int(digits))

        # 1. Circle Requirement Check
        if caster_circle < spec.min_circle_required:
            return False, (
                f"❌ [서클 한계 도달] [{spec.name_ko}]은(는) 대자연의 기압을 뒤트는 고위 원소마법입니다. "
                f"최소 {spec.min_circle_required}서클 이상의 마법사만이 시전할 수 있습니다. (현재 시전자: {caster_circle}서클)"
            )

        # 2. Mana Cost Check
        current_mp = getattr(caster, "mana", 0)
        if current_mp < spec.mana_cost:
            return False, f"❌ [마나 부족] 기상 마법 영창을 위해 {spec.mana_cost} MP가 필요하지만, 현재 {current_mp} MP뿐입니다."

        # 3. Deduct Mana
        caster.mana = max(0, current_mp - spec.mana_cost)

        # 4. Calculate Duration: 30 mins base + 15 mins per circle above 4th circle
        extra_circle = max(0, caster_circle - 4)
        total_duration_minutes = spec.base_duration_minutes + (extra_circle * 15)

        # 5. Register Active Weather Anomaly
        current_loc_id = getattr(caster, "location", "start")
        anomaly_id = f"anomaly_{magic_id}_{current_loc_id}"
        anomaly = ActiveWeatherAnomaly(
            anomaly_id=anomaly_id,
            magic_id=magic_id,
            name_ko=spec.name_ko,
            location_id=current_loc_id,
            remaining_minutes=total_duration_minutes,
            caster_id=getattr(caster, "id", getattr(caster, "name", "caster")),
            caster_circle=caster_circle
        )

        anomalies = cls.get_anomalies(state)
        anomalies[anomaly_id] = anomaly

        # Override location environment weather name if possible
        loc = state.locations.get(current_loc_id) if hasattr(state, "locations") else None
        if loc:
            loc.environment_notes = f"[기상 이변]: {spec.name_ko} 발동 중 ({total_duration_minutes}분 잔여)"

        return True, (
            f"🌩️ [고위 기상 마법 영창 성공] {caster.name}이(가) 대기의 흐름을 강제로 개변하여 "
            f"현재 구역에 [{spec.name_ko}]을(를) 전개했습니다! "
            f"(지속시간: {total_duration_minutes}분 [{spec.base_duration_minutes}분 + {caster_circle}서클 보너스 {extra_circle * 15}분])"
        )

    @classmethod
    def resolve_combat_weather_tick(
        cls,
        state: Any,
        target: Any,
        has_cover_or_shield: bool = False,
        fixed_roll: Optional[int] = None
    ) -> List[str]:
        """
        Dual-mode Combat Resolution: Resolved at Round End for exposed actors.
        Rolls combat damage dice against reflex save DC.
        """
        logs = []
        loc_id = getattr(target, "location", "")
        anomalies = cls.get_anomalies(state)

        # Find active weather anomaly in this location
        active_anom = next((a for a in anomalies.values() if a.location_id == loc_id), None)
        if not active_anom:
            return logs

        spec = WEATHER_MAGIC_REGISTRY.get(active_anom.magic_id)
        if not spec or spec.combat_damage_dice == "0d0":
            return logs

        # Combat round strike
        base_dmg = random.randint(1, 6) if fixed_roll is None else fixed_roll
        # Saving throw (Agility check vs combat_save_dc)
        agi_mod = (getattr(target, "agility", 10) - 10) // 2
        save_roll = random.randint(1, 20)
        total_save = save_roll + agi_mod

        if total_save >= spec.combat_save_dc or has_cover_or_shield:
            final_dmg = max(1, base_dmg // 2)
            logs.append(
                f"🛡️ [기상 피격 완화] 쏟아지는 [{spec.name_ko}]의 파편을 방패와 엄폐물로 막아내어 "
                f"피해를 반감했습니다! ({final_dmg} 피해, 회피 판정: {total_save} vs DC {spec.combat_save_dc})"
            )
        else:
            final_dmg = base_dmg
            logs.append(
                f"💥 [기상 직격 피격] 피할 곳 없는 개활지에서 [{spec.name_ko}]의 직격을 맞았습니다! "
                f"({final_dmg} 관통/원소 피해, 판정: {total_save} vs DC {spec.combat_save_dc})"
            )

        target.health = max(1, target.health - final_dmg)
        return logs

    @classmethod
    def resolve_travel_weather_exposure(
        cls,
        state: Any,
        travel_minutes: int,
        has_shelter: bool = False,
        has_shield_or_coat: bool = False
    ) -> List[str]:
        """
        Dual-mode Travel Resolution:
        Converts total travel minutes into 10-minute environment ticks.
        Calculates cumulative damage, wetness, and body temperature drops.
        """
        logs = []
        if has_shelter or travel_minutes <= 0:
            return logs

        player = getattr(state, "player", None)
        if not player:
            return logs

        anomalies = cls.get_anomalies(state)
        active_anom = next((a for a in anomalies.values() if a.location_id == player.location), None)
        if not active_anom:
            return logs

        spec = WEATHER_MAGIC_REGISTRY.get(active_anom.magic_id)
        if not spec:
            return logs

        # Calculate ticks (1 environmental tick = 10 minutes)
        ticks = max(1, travel_minutes // 10)
        mitigation = 0.5 if has_shield_or_coat else 1.0

        total_damage = int(spec.travel_damage_per_10min * ticks * mitigation)
        total_wetness = round(spec.travel_wetness_per_10min * ticks * mitigation, 1)
        total_temp_drop = round(spec.travel_temp_drop_per_10min * ticks * mitigation, 1)

        # Apply state changes
        if total_damage > 0:
            player.health = max(1, player.health - total_damage)
        if hasattr(player, "wetness"):
            player.wetness = max(0.0, min(100.0, player.wetness + total_wetness))
        if hasattr(player, "body_temperature"):
            player.body_temperature = round(max(30.0, min(42.0, player.body_temperature - total_temp_drop)), 2)

        gear_str = " (방패 및 방한 코트로 50% 감쇄됨)" if has_shield_or_coat else ""
        logs.append(
            f"🌧️ [기상 이변 장기 노출 결산] [{spec.name_ko}]의 영향권에서 {travel_minutes}분간 이동했습니다{gear_str}:\n"
            f"  * 누적 타격 피해: -{total_damage} HP (현재 HP: {player.health})\n"
            f"  * 의복 젖음 수치: +{total_wetness}% (현재 젖음: {player.wetness:.1f}%)\n"
            f"  * 심부 체온 변동: -{total_temp_drop}℃ (현재 체온: {player.body_temperature:.1f}℃)"
        )

        return logs

    @classmethod
    def tick_anomalies(cls, state: Any, delta_minutes: int = 10) -> List[str]:
        """Decrements remaining anomaly duration and removes expired ones."""
        logs = []
        anomalies = cls.get_anomalies(state)
        expired = []

        for a_id, a_obj in list(anomalies.items()):
            a_obj.remaining_minutes -= delta_minutes
            if a_obj.remaining_minutes <= 0:
                expired.append(a_id)
                logs.append(f"🌤️ [기상 마법 소멸] 대기를 뒤흔들던 [{a_obj.name_ko}]의 마력이 소진되어 기상이 정상으로 돌아왔습니다.")

        for e_id in expired:
            anomalies.pop(e_id, None)

        return logs
