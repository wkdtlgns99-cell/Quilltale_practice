"""
Thermal Survival, Hypothermia, Heatstroke & Environmental Weather Physics Engine for Quilltale TRPG.
Deterministic calculation of physiological body temperature, clothing insulation,
drenching wetness dynamics, wind chill, flood, mold, and lightning conductivity.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging

from src.world.state import WorldState, Player, Item, EnvironmentalMetrics

logger = logging.getLogger(__name__)

# ============================================================
# Master Raw System Data (External AI Extraction Specifications)
# ============================================================
THERMAL_SURVIVAL_SYSTEM = {
    "thermal_equilibrium": {
        "name_ko": "인체 열평형",
        "description": "인체의 심부 체온은 외부 기온, 젖음, 바람, 의복, 열원, 활동량에 따라 지속적으로 변화한다.",
        "traits": ["thermal_equilibrium", "body_temperature", "physiology", "environmental_heat", "hardcore_survival"],
        "normal_core_temperature": 36.5,
        "wetness": {
            "name_ko": "젖음 수치",
            "description": "비, 폭우, 물에 빠짐, 도하 등으로 의복과 신체가 젖은 정도 (0~100).",
            "traits": ["wetness", "rain", "water", "heat_loss"],
            "increase_sources": {
                "light_rain": 5,
                "heavy_rain": 15,
                "storm": 25,
                "river_crossing": 40,
                "fall_into_water": 80,
                "full_submersion": 100
            },
            "drying": {
                "natural_drying_per_turn": 2,
                "campfire_drying_per_turn": 10,
                "stove_drying_per_turn": 10
            },
            "heat_loss_multiplier": {
                "below_50_percent": 1.0,
                "50_to_74_percent": 3.0,
                "75_to_100_percent": 5.0
            }
        },
        "heat_sources": {
            "campfire": {
                "name_ko": "모닥불",
                "description": "주변의 젖은 장비를 말리고 체온을 회복시키는 대표적인 야외 열원.",
                "traits": ["heat_source", "fire", "drying", "warmth"],
                "wetness_change_per_turn": -10,
                "body_temperature_normalization_per_turn": 0.5
            },
            "stove": {
                "name_ko": "난로",
                "description": "밀폐된 공간에서 지속적으로 열을 공급하여 체온을 안정시키고 건조를 돕는다.",
                "traits": ["heat_source", "stove", "drying", "warmth"],
                "wetness_change_per_turn": -10,
                "body_temperature_normalization_per_turn": 0.5
            }
        }
    },

    "clothing_insulation": {
        "fur_coat": {
            "name_ko": "방한 모피",
            "description": "두꺼운 모피로 체온을 효과적으로 보존하지만 완전한 방수 장비는 아니다.",
            "traits": ["fur", "cold_resistant", "insulation", "moderate_waterproof"],
            "insulation": 8,
            "waterproofing": "moderate",
            "heat_resistance": -2,
            "wetness_protection": 30
        },
        "oilskin_cloak": {
            "name_ko": "유포 망토",
            "description": "기름을 먹인 천으로 제작되어 빗물과 외부 수분을 거의 완전히 차단한다.",
            "traits": ["oilskin", "fully_waterproof", "rain_protection", "moderate_insulation"],
            "insulation": 3,
            "waterproofing": "full",
            "heat_resistance": 0,
            "wetness_protection": 100
        },
        "heavy_plate": {
            "name_ko": "강철 판금",
            "description": "두꺼운 강철 갑옷은 냉기를 강하게 전달하고 폭염 시 극단적 체온 상승을 유발한다.",
            "traits": ["steel", "heavy_armor", "cold_conduction", "heat_accumulation"],
            "insulation": -3,
            "waterproofing": "low",
            "cold_conduction": "extreme",
            "heat_accumulation": "extreme",
            "heat_resistance": -5,
            "heat_rise_multiplier": 1.5,
            "wetness_protection": 10
        },
        "linen_tunic": {
            "name_ko": "마포 옷",
            "description": "얇고 통기성이 뛰어난 천으로 제작되어 열과 습기를 쉽게 배출한다.",
            "traits": ["linen", "breathable", "heat_resistant", "light_clothing"],
            "insulation": 0,
            "waterproofing": "none",
            "breathability": 10,
            "heat_resistance": 8,
            "heat_dissipation": 10,
            "wetness_protection": 0
        }
    },

    "hypothermia_stages": {
        "mild": {
            "name_ko": "경도 저체온증",
            "description": "심부 체온이 35.0~35.9℃로 떨어져 사지 떨림과 손 떨림이 발생하는 단계.",
            "traits": ["hypothermia", "mild", "shivering", "dexterity_penalty"],
            "temperature_range": (35.0, 35.9),
            "dexterity_penalty": -2,
            "ranged_aim_dice": -3
        },
        "moderate": {
            "name_ko": "중등도 저체온증",
            "description": "심부 체온 33.0~34.9℃. 발음이 부정확해지고 주문 영창 실패율이 증가하며 지속 피해 발생.",
            "traits": ["hypothermia", "moderate", "stamina_reduction", "spell_failure"],
            "temperature_range": (33.0, 34.9),
            "stamina_cap_multiplier": 0.6,
            "spell_failure_rate": 0.25,
            "damage_per_turn": 4
        },
        "severe": {
            "name_ko": "중증 저체온증",
            "description": "심부 체온 30.0~32.9℃. 섬망, 환각, 반혼수 상태 및 이동속도 반감.",
            "traits": ["hypothermia", "severe", "delirium", "hallucination", "semi_coma"],
            "temperature_range": (30.0, 32.9),
            "movement_speed_multiplier": 0.5,
            "damage_per_turn": 8
        },
        "fatal": {
            "name_ko": "치명적 저체온증",
            "description": "심부 체온 30.0℃ 미만. 심정지 및 생체 기능 정지 위기.",
            "traits": ["hypothermia", "fatal", "cardiac_arrest", "incapacitated"],
            "temperature_below": 30.0,
            "damage_per_turn": 20,
            "action_impossible": True
        }
    },

    "hyperthermia_stages": {
        "heat_exhaustion": {
            "name_ko": "열탈진",
            "description": "체온 37.5~38.4℃. 갈증 폭증 및 기력 소모량 1.5배 증가.",
            "traits": ["hyperthermia", "heat_exhaustion", "thirst", "dehydration"],
            "temperature_range": (37.5, 38.4),
            "stamina_cost_multiplier": 1.5
        },
        "heat_cramps": {
            "name_ko": "열경련",
            "description": "체온 38.5~39.4℃. 근육 경련으로 근력/민첩 -3 및 구토.",
            "traits": ["hyperthermia", "heat_cramps", "muscle_spasm", "dehydration"],
            "temperature_range": (38.5, 39.4),
            "strength_penalty": -3,
            "dexterity_penalty": -3
        },
        "heat_stroke": {
            "name_ko": "열사병",
            "description": "체온 39.5~40.4℃. 체온 조절 붕괴로 땀이 멈추고 턴당 피해 6.",
            "traits": ["hyperthermia", "heat_stroke", "delirium", "anhidrosis"],
            "temperature_range": (39.5, 40.4),
            "hp_loss_per_turn": 6
        },
        "multi_organ_failure": {
            "name_ko": "다발성 장기부전",
            "description": "체온 40.5℃ 이상. 뇌 손상 및 턴당 체력 손실 15.",
            "traits": ["hyperthermia", "critical", "brain_damage", "organ_failure"],
            "temperature_minimum": 40.5,
            "hp_loss_per_turn": 15
        }
    }
}

ADDITIONAL_SURVIVAL_ENVIRONMENT_SYSTEMS = {
    "WIND_CHILL_SYSTEM": {
        "calm": {"name_ko": "무풍", "heat_loss_multiplier": 1.0, "traits": ["calm"]},
        "breeze": {"name_ko": "산들바람", "heat_loss_multiplier": 1.2, "traits": ["breeze"]},
        "strong_wind": {"name_ko": "강풍", "heat_loss_multiplier": 1.8, "movement_penalty": -2, "traits": ["strong_wind"]},
        "storm": {"name_ko": "폭풍", "heat_loss_multiplier": 3.0, "movement_penalty": -4, "traits": ["storm"]}
    },
    "RAIN_AND_FLOOD_SYSTEM": {
        "drizzle": {"name_ko": "이슬비", "wetness_per_turn": 2, "visibility_penalty": -1, "traits": ["light_rain"]},
        "heavy_rain": {"name_ko": "폭우", "wetness_per_turn": 8, "visibility_penalty": -3, "traits": ["heavy_rain"]},
        "downpour": {"name_ko": "집중호우", "wetness_per_turn": 15, "visibility_penalty": -5, "traits": ["downpour"]}
    }
}


# ============================================================
# Dataclass Specifications (Mandatory traits tag list: Rule 6)
# ============================================================
@dataclass
class ThermalClothingSpec:
    clothing_id: str
    name_ko: str
    description: str
    insulation: float                  # Positive: warm, Negative: cold conduction
    waterproofing: str = "none"        # "none", "moderate", "full"
    heat_resistance: float = 0.0       # Resistance against heatwaves
    wetness_protection: float = 0.0    # 0~100% percentage of rain blocked
    heat_rise_multiplier: float = 1.0  # Heat multiplier (e.g. 1.5 for plate in sun)
    traits: List[str] = field(default_factory=list)


@dataclass
class HypothermiaStageSpec:
    stage_id: str
    name_ko: str
    description: str
    min_temp: float
    max_temp: float
    dexterity_penalty: int = 0
    ranged_aim_dice: int = 0
    stamina_cap_multiplier: float = 1.0
    spell_failure_rate: float = 0.0
    damage_per_turn: int = 0
    movement_speed_multiplier: float = 1.0
    action_impossible: bool = False
    traits: List[str] = field(default_factory=list)


@dataclass
class HyperthermiaStageSpec:
    stage_id: str
    name_ko: str
    description: str
    min_temp: float
    max_temp: float
    stamina_cost_multiplier: float = 1.0
    strength_penalty: int = 0
    dexterity_penalty: int = 0
    hp_loss_per_turn: int = 0
    traits: List[str] = field(default_factory=list)


# ============================================================
# Registries Initialized from Master Data
# ============================================================
CLOTHING_INSULATION_REGISTRY: Dict[str, ThermalClothingSpec] = {}
for _k, _v in THERMAL_SURVIVAL_SYSTEM["clothing_insulation"].items():
    CLOTHING_INSULATION_REGISTRY[_k] = ThermalClothingSpec(
        clothing_id=_k,
        name_ko=_v["name_ko"],
        description=_v["description"],
        insulation=float(_v["insulation"]),
        waterproofing=_v.get("waterproofing", "none"),
        heat_resistance=float(_v.get("heat_resistance", 0.0)),
        wetness_protection=float(_v.get("wetness_protection", 0.0)),
        heat_rise_multiplier=float(_v.get("heat_rise_multiplier", 1.0)),
        traits=list(_v.get("traits", []))
    )

HYPOTHERMIA_STAGES_REGISTRY: Dict[str, HypothermiaStageSpec] = {
    "mild": HypothermiaStageSpec(
        stage_id="mild",
        name_ko="경도 저체온증",
        description="사지 떨림과 손 떨림으로 민첩 저하.",
        min_temp=35.0,
        max_temp=35.9,
        dexterity_penalty=-2,
        ranged_aim_dice=-3,
        traits=["hypothermia", "mild", "shivering"]
    ),
    "moderate": HypothermiaStageSpec(
        stage_id="moderate",
        name_ko="중등도 저체온증",
        description="혀가 굳어 주문 영창 불안정 및 지속 피해 4.",
        min_temp=33.0,
        max_temp=34.9,
        stamina_cap_multiplier=0.6,
        spell_failure_rate=0.25,
        damage_per_turn=4,
        traits=["hypothermia", "moderate", "spell_failure"]
    ),
    "severe": HypothermiaStageSpec(
        stage_id="severe",
        name_ko="중증 저체온증",
        description="섬망, 환각, 반혼수 상태 및 지속 피해 8.",
        min_temp=30.0,
        max_temp=32.9,
        movement_speed_multiplier=0.5,
        damage_per_turn=8,
        traits=["hypothermia", "severe", "delirium"]
    ),
    "fatal": HypothermiaStageSpec(
        stage_id="fatal",
        name_ko="치명적 저체온증",
        description="심정지 위기 및 행동 불가, 지속 피해 20.",
        min_temp=0.0,
        max_temp=29.9,
        damage_per_turn=20,
        action_impossible=True,
        traits=["hypothermia", "fatal", "cardiac_arrest"]
    )
}

HYPERTHERMIA_STAGES_REGISTRY: Dict[str, HyperthermiaStageSpec] = {
    "heat_exhaustion": HyperthermiaStageSpec(
        stage_id="heat_exhaustion",
        name_ko="열탈진",
        description="갈증 폭증 및 기력 소모량 1.5배.",
        min_temp=37.5,
        max_temp=38.4,
        stamina_cost_multiplier=1.5,
        traits=["hyperthermia", "heat_exhaustion"]
    ),
    "heat_cramps": HyperthermiaStageSpec(
        stage_id="heat_cramps",
        name_ko="열경련",
        description="근육 경련으로 근력/민첩 -3.",
        min_temp=38.5,
        max_temp=39.4,
        strength_penalty=-3,
        dexterity_penalty=-3,
        traits=["hyperthermia", "heat_cramps"]
    ),
    "heat_stroke": HyperthermiaStageSpec(
        stage_id="heat_stroke",
        name_ko="열사병",
        description="체온 조절 중추 붕괴로 땀이 멈추고 턴당 피해 6.",
        min_temp=39.5,
        max_temp=40.4,
        hp_loss_per_turn=6,
        traits=["hyperthermia", "heat_stroke"]
    ),
    "multi_organ_failure": HyperthermiaStageSpec(
        stage_id="multi_organ_failure",
        name_ko="다발성 장기부전",
        description="뇌 손상 및 턴당 체력 손실 15.",
        min_temp=40.5,
        max_temp=50.0,
        hp_loss_per_turn=15,
        traits=["hyperthermia", "multi_organ_failure"]
    )
}


# ============================================================
# Deterministic Thermal Survival Engine
# ============================================================
class ThermalSurvivalEngine:
    """
    Evaluates body temperature, wetness dynamics, wind chill,
    insulation gear, hypothermia, and heatstroke with 100% deterministic logic.
    """

    @classmethod
    def get_clothing_spec(cls, item_name: str, item_type: str = "") -> ThermalClothingSpec:
        """
        Maps item names and types to ThermalClothingSpec.
        """
        name_l = item_name.lower()
        if "모피" in name_l or "fur" in name_l:
            return CLOTHING_INSULATION_REGISTRY["fur_coat"]
        elif "유포" in name_l or "oilskin" in name_l or "우비" in name_l:
            return CLOTHING_INSULATION_REGISTRY["oilskin_cloak"]
        elif "판금" in name_l or "플레이트" in name_l or "plate" in name_l or "강철" in name_l:
            return CLOTHING_INSULATION_REGISTRY["heavy_plate"]
        elif "마포" in name_l or "린넨" in name_l or "튜닉" in name_l or "linen" in name_l:
            return CLOTHING_INSULATION_REGISTRY["linen_tunic"]
        elif "가죽" in name_l or "leather" in name_l:
            return ThermalClothingSpec("leather_gear", "가죽 방어구", "방풍성 우수", insulation=4.0, wetness_protection=40.0, traits=["leather"])
        elif "로브" in name_l or "robe" in name_l:
            return ThermalClothingSpec("fabric_robe", "천 로브", "기본 보온성", insulation=2.0, wetness_protection=10.0, traits=["fabric"])
        
        # Default traveler clothes
        return ThermalClothingSpec("traveler_garb", "여행자 평복", "표준 의복", insulation=1.0, wetness_protection=10.0, traits=["standard"])

    @classmethod
    def calculate_net_insulation(cls, player: Player, state: Optional[WorldState] = None) -> Tuple[float, float, float]:
        """
        Calculates total insulation, wetness protection, and heat resistance.
        Returns: (net_insulation, net_wetness_protection, net_heat_resistance)
        """
        eq = player.equipment
        slots = [eq.chest, eq.cape, eq.legs, eq.head, eq.innerwear, eq.shoulders]
        total_insulation = 1.0  # Base body retention
        total_wetness_prot = 0.0
        total_heat_res = 0.0

        for item_id in slots:
            if not item_id:
                continue
            item_name = item_id
            if state and item_id in state.items:
                item_name = state.items[item_id].name
            spec = cls.get_clothing_spec(item_name)
            total_insulation += spec.insulation
            total_wetness_prot = max(total_wetness_prot, spec.wetness_protection)
            total_heat_res += spec.heat_resistance

        return total_insulation, min(100.0, total_wetness_prot), total_heat_res

    @classmethod
    def determine_thermal_stage(cls, core_temp: float) -> str:
        """
        Determines the hypothermia / hyperthermia stage ID based on body temperature.
        """
        if core_temp < 30.0:
            return "fatal"
        elif core_temp < 33.0:
            return "severe"
        elif core_temp < 35.0:
            return "moderate"
        elif core_temp < 36.0:
            return "mild"
        elif core_temp <= 37.4:
            return "normal"
        elif core_temp <= 38.4:
            return "heat_exhaustion"
        elif core_temp <= 39.4:
            return "heat_cramps"
        elif core_temp <= 40.4:
            return "heat_stroke"
        else:
            return "multi_organ_failure"

    @classmethod
    def process_turn_thermal_survival(cls, state: WorldState, delta_minutes: int = 30) -> List[str]:
        """
        Processes turn-based physiological body temperature, wetness, wind chill,
        and climate hazard ticks with 100% deterministic logic. Scales with delta_minutes.
        """
        logs: List[str] = []
        player = state.player
        env = state.environment
        weather = env.weather
        temp = env.temperature_celsius

        ticks = max(1, round(delta_minutes / 30.0))
        for _ in range(ticks):
            # 1. Calculate clothing metrics
            net_insulation, wet_prot, heat_res = cls.calculate_net_insulation(player, state)

            # 2. Wetness Dynamics
            is_raining = any(r in weather for r in ["비", "폭우", "소나기", "downpour", "rain"])
            is_storm = "폭풍" in weather or "태풍" in weather
            has_campfire = getattr(env, "has_heat_source", False)

            # Rain wetness intake
            rain_intake = 0.0
            if is_storm:
                rain_intake = 25.0 * (1.0 - (wet_prot / 100.0))
            elif "폭우" in weather:
                rain_intake = 15.0 * (1.0 - (wet_prot / 100.0))
            elif is_raining:
                rain_intake = 5.0 * (1.0 - (wet_prot / 100.0))

            # Drying dynamics
            drying = 0.0
            if has_campfire:
                drying = 10.0
            elif not is_raining:
                drying = 2.0

            wet_delta = rain_intake - drying

            current_wet = getattr(player, "wetness", 0.0)
            new_wet = max(0.0, min(100.0, round(current_wet + wet_delta, 1)))
            player.wetness = new_wet

            # Wetness heat loss multiplier
            if new_wet >= 75.0:
                wet_mult = 5.0
            elif new_wet >= 50.0:
                wet_mult = 3.0
            else:
                wet_mult = 1.0

            # Wind chill heat loss multiplier
            wind_mult = 1.0
            wind_level = getattr(env, "wind_level", "calm")
            if wind_level == "storm" or "폭풍" in weather:
                wind_mult = 3.0
            elif wind_level == "strong_wind" or "강풍" in weather:
                wind_mult = 1.8
            elif wind_level == "breeze":
                wind_mult = 1.2

            # 3. Physiological Temperature Evolution
            curr_temp = getattr(player, "body_temperature", 36.5)

            # Cold Environment (Snow / Blizzard / Sub-zero / Freezing)
            if "폭설" in weather or "한파" in weather or temp <= 0:
                if has_campfire:
                    new_temp = min(36.5, curr_temp + 0.5)
                else:
                    cold_severity = max(1.0, (10.0 - temp) / 10.0)
                    insulation_mitigation = max(0.0, net_insulation * 0.05)
                    heat_loss = max(0.1, (0.3 * cold_severity * wet_mult * wind_mult) - insulation_mitigation)
                    new_temp = max(28.0, curr_temp - heat_loss)

            # Hot Environment (Heatwave / Desert / Over 38C)
            elif "폭염" in weather or "열풍" in weather or temp >= 38:
                heat_severity = max(1.0, (temp - 30.0) / 10.0)
                heat_gain = 0.3 * heat_severity
                if net_insulation < 0:
                    heat_gain *= 1.5
                new_temp = min(42.0, curr_temp + heat_gain)

            else:
                # Mild Environment: Normalizes towards 36.5
                if has_campfire:
                    new_temp = min(36.5, curr_temp + 0.5)
                elif curr_temp < 36.5:
                    new_temp = min(36.5, curr_temp + 0.2)
                elif curr_temp > 36.5:
                    new_temp = max(36.5, curr_temp - 0.2)
                else:
                    new_temp = 36.5

            new_temp = round(new_temp, 1)
            player.body_temperature = new_temp
            stage_id = cls.determine_thermal_stage(new_temp)
            player.thermal_status = stage_id

            # Apply tick damage per tick if applicable
            if stage_id in ["moderate", "severe", "fatal"]:
                spec = HYPOTHERMIA_STAGES_REGISTRY[stage_id]
                player.health = max(1, player.health - spec.damage_per_turn)
            elif stage_id in ["heat_stroke", "multi_organ_failure"]:
                spec = HYPERTHERMIA_STAGES_REGISTRY[stage_id]
                player.health = max(1, player.health - spec.hp_loss_per_turn)
                fatigue_add = 10 if stage_id == "heat_stroke" else 15
                player.fatigue = min(100, player.fatigue + fatigue_add)

        # 4. Status Effects and Narration Logs
        duration_note = f" ({ticks * 30}분 경과)" if ticks > 1 else ""
        if stage_id == "mild":
            logs.append(
                f"🥶 [경도 저체온증]{duration_note} 체온이 {new_temp:.1f}℃로 떨어졌습니다! (젖음: {new_wet:.0f}%) 사지 떨림으로 민첩 -2 및 원거리 조준에 불이익을 받습니다."
            )
        elif stage_id == "moderate":
            spec = HYPOTHERMIA_STAGES_REGISTRY["moderate"]
            logs.append(
                f"🥶 [중등도 저체온증]{duration_note} 체온 {new_temp:.1f}℃! 혀가 굳어 주문 실패율이 25% 증가하고 지속 동상 피해 {spec.damage_per_turn}를 입었습니다."
            )
        elif stage_id == "severe":
            spec = HYPOTHERMIA_STAGES_REGISTRY["severe"]
            logs.append(
                f"🥶 [중증 저체온증]{duration_note} 체온 {new_temp:.1f}℃! 극심한 오한과 섬망으로 지속 피해 {spec.damage_per_turn}를 입었습니다! (이동속도 50% 반감)"
            )
        elif stage_id == "fatal":
            spec = HYPOTHERMIA_STAGES_REGISTRY["fatal"]
            logs.append(
                f"🚨 [치명적 저체온증]{duration_note} 체온이 {new_temp:.1f}℃로 급락하여 심정지 위기! 즉각적인 열원 확보가 없으면 사망합니다! (피해 {spec.damage_per_turn})"
            )
        elif stage_id == "heat_exhaustion":
            logs.append(
                f"☀️ [열탈진]{duration_note} 체온 {new_temp:.1f}℃! 살인적인 더위로 갈증이 폭증하고 기력 소모량이 1.5배로 증가합니다."
            )
        elif stage_id == "heat_cramps":
            logs.append(
                f"☀️ [열경련]{duration_note} 체온 {new_temp:.1f}℃! 전해질 고갈로 인한 근육 경련으로 근력과 민첩이 -3 저하됩니다."
            )
        elif stage_id == "heat_stroke":
            spec = HYPERTHERMIA_STAGES_REGISTRY["heat_stroke"]
            logs.append(
                f"☀️ [폭염 열사병]{duration_note} 체온이 {new_temp:.1f}℃로 치솟아 땀이 멈추고 열사 피해 {spec.hp_loss_per_turn}를 입었습니다!"
            )
        elif stage_id == "multi_organ_failure":
            spec = HYPERTHERMIA_STAGES_REGISTRY["multi_organ_failure"]
            logs.append(
                f"🚨 [다발성 장기부전]{duration_note} 체온 {new_temp:.1f}℃ 초고열로 뇌 손상 발생 및 치명적 피해 {spec.hp_loss_per_turn}를 입었습니다!"
            )

        return logs

    @classmethod
    def light_campfire(cls, state: WorldState) -> Tuple[bool, str]:
        """
        Lights a survival campfire at the current location to warm up and dry gear.
        """
        state.environment.has_heat_source = True
        state.player.wetness = max(0.0, state.player.wetness - 15.0)
        state.player.body_temperature = min(36.5, state.player.body_temperature + 0.5)
        return True, "🔥 [모닥불 점화] 주변에 따뜻한 모닥불을 피웠습니다. 젖은 옷이 빠르게 마르고 얼어붙은 체온이 회복됩니다. (턴당 건조 +10%, 체온 회복)"
