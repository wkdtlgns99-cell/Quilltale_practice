"""
Cave Collapse, Structural Mechanics & Subterranean Environment Physics Engine for Quilltale TRPG.
Deterministic calculation of subterranean rock stability, vibration-induced collapses,
oxygen dynamics, toxic gas contamination, and floor hazards.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging

from src.world.state import WorldState, Location

logger = logging.getLogger(__name__)

# ============================================================
# Master Raw System Data (External AI Extraction Specifications)
# ============================================================
CAVE_COLLAPSE_SYSTEM = {
    "rock_strata": {
        "limestone": {
            "name_ko": "석회암",
            "description": "수분을 흡수하면 암반 강도가 저하되며 장기간의 침식과 진동에 취약하다.",
            "traits": ["rock", "limestone", "fragile", "water_sensitive"],
            "base_durability": 70,
            "vibration_resistance": 55,
            "fragment_sharpness": "d8",
            "water_damage_multiplier": 1.5,
            "collapse_risk": "high"
        },
        "granite": {
            "name_ko": "화강암",
            "description": "매우 단단하고 충격에 강해 구조적 안정성이 높은 암반이다.",
            "traits": ["rock", "granite", "hard", "impact_resistant"],
            "base_durability": 120,
            "vibration_resistance": 90,
            "fragment_sharpness": "d6",
            "water_damage_multiplier": 0.5,
            "collapse_risk": "low"
        },
        "sandstone": {
            "name_ko": "사암",
            "description": "입자 결합력이 약해 지속적인 진동과 침식에 쉽게 무너지며 붕괴 위험이 매우 높다.",
            "traits": ["rock", "sandstone", "fragile", "high_collapse_risk"],
            "base_durability": 55,
            "vibration_resistance": 40,
            "fragment_sharpness": "d10",
            "water_damage_multiplier": 1.8,
            "collapse_risk": "very_high"
        },
        "basalt": {
            "name_ko": "현무암",
            "description": "단단하고 충격에 강하지만 균열이 연결될 경우 연쇄적인 붕괴가 발생할 수 있다.",
            "traits": ["rock", "basalt", "hard", "fracture_chain"],
            "base_durability": 110,
            "vibration_resistance": 75,
            "fragment_sharpness": "d8",
            "water_damage_multiplier": 0.8,
            "collapse_risk": "medium",
            "chain_collapse_chance": 25
        },
        "obsidian": {
            "name_ko": "흑요석",
            "description": "단단하지만 마력성 충격에 취약하며 파괴될 경우 극도로 날카로운 파편을 발생시킨다.",
            "traits": ["rock", "obsidian", "magically_fragile", "razor_sharp"],
            "base_durability": 85,
            "vibration_resistance": 60,
            "fragment_sharpness": "d12",
            "magic_damage_multiplier": 2.0,
            "collapse_risk": "medium"
        }
    },

    "vibration_sources": {
        "fireball_explosion": {
            "name_ko": "화염구/폭발 마법",
            "description": "폭발적인 마력과 열압력으로 주변 암반에 강한 충격 진동을 발생시킨다.",
            "traits": ["magic", "explosion", "vibration", "fire"],
            "circle_1": 10,
            "circle_2": 20,
            "circle_3": 30,
            "circle_4": 40,
            "circle_5": 50
        },
        "heavy_blunt_strike": {
            "name_ko": "대형 둔기 강타",
            "description": "거대한 둔기나 공성급 무기가 암반을 강타하여 구조물에 충격을 전달한다.",
            "traits": ["impact", "blunt", "vibration"],
            "impact_range": (5, 15)
        },
        "mining": {
            "name_ko": "굴착/곡괭이질",
            "description": "반복적인 굴착 작업이 암반에 지속적인 미세 진동을 축적시킨다.",
            "traits": ["mining", "repeated_vibration"],
            "impact_per_action": 3
        },
        "trap_activation": {
            "name_ko": "함정 격발",
            "description": "대형 기계식 함정이나 폭발성 함정이 작동하며 주변 구조물에 강한 충격을 전달한다.",
            "traits": ["trap", "impact", "sudden_vibration"],
            "impact": 20
        }
    },

    "collapse_stages": {
        "stable": {
            "name_ko": "안정",
            "description": "암반과 천장 구조가 안정적으로 유지되고 있으며 즉각적인 붕괴 위험이 없다.",
            "traits": ["stable", "safe"],
            "durability_threshold": 70,
            "movement_penalty": 0
        },
        "cracking": {
            "name_ko": "천장 균열",
            "description": "암반에 균열이 발생하기 시작하며 흙먼지와 작은 돌조각이 지속적으로 떨어진다.",
            "traits": ["cracking", "unstable", "dust", "falling_debris"],
            "durability_threshold": 40,
            "dust_fall": True,
            "visibility_penalty": -10,
            "light_penalty": -10,
            "minor_debris_damage": "1d4"
        },
        "partial_collapse": {
            "name_ko": "부분 낙반",
            "description": "천장이나 벽면 일부가 무너져 거대한 암석이 떨어지고 일부 통로가 폐쇄된다.",
            "traits": ["partial_collapse", "falling_rocks", "blocked_path", "unstable"],
            "durability_threshold": 15,
            "falling_rock_damage": "1d8~1d12",
            "dex_save_dc": 15,
            "passage_blocked": True,
            "escape_route_reduction": 1
        },
        "full_collapse": {
            "name_ko": "전면 붕괴",
            "description": "주요 지지 구조가 완전히 파괴되어 천장과 벽면 전체가 무너지고 생존자를 암석 아래 매몰시킨다.",
            "traits": ["full_collapse", "burial", "lethal", "escape_blocked"],
            "durability_threshold": 0,
            "burial_damage": "10d12",
            "instant_death_risk": True,
            "escape_possible": False,
            "rescue_required": True
        }
    },

    "oxygen_dynamics": {
        "name_ko": "밀폐 공간 산소 농도 역학",
        "description": "밀폐된 지하 공간에서 생명체의 호흡과 연소에 의해 산소가 감소하며 환기구를 개방하면 산소가 회복된다.",
        "traits": ["oxygen", "sealed_room", "suffocation", "survival"],
        "base_oxygen_percent": 100.0,
        "minimum_oxygen_percent": 0.0,

        "consumption_per_turn": {
            "adult_breathing": {
                "name_ko": "성인 1인 호흡",
                "description": "성인 한 명이 한 턴 동안 소비하는 산소량.",
                "traits": ["breathing", "oxygen_consumption"],
                "oxygen_change": -0.2
            },
            "burning_torch": {
                "name_ko": "불타는 횃불 1개",
                "description": "연소 중인 횃불이 한 턴 동안 소비하는 산소량.",
                "traits": ["fire", "torch", "oxygen_consumption"],
                "oxygen_change": -1.0
            },
            "fire_magic": {
                "name_ko": "화염 마법 1회",
                "description": "화염 마법이 순간적으로 대량의 산소를 소모한다.",
                "traits": ["magic", "fire", "instant_consumption"],
                "oxygen_change": -5.0,
                "instant": True
            }
        },

        "ventilation": {
            "name_ko": "환기구 개방",
            "description": "외부와 연결된 환기구가 개방되면 신선한 공기가 유입되어 산소 농도가 회복된다.",
            "traits": ["ventilation", "fresh_air", "oxygen_recovery"],
            "oxygen_recovery_per_turn": 2.0,
            "maximum_oxygen_percent": 100.0
        },

        "hypoxia_stages": {
            "mild": {
                "name_ko": "경도 저산소증",
                "description": "산소 농도가 낮아지기 시작하여 두통과 피로가 발생한다.",
                "traits": ["hypoxia", "mild", "headache"],
                "oxygen_range": (70, 80),
                "effects": {
                    "headache": True,
                    "stamina_regeneration_multiplier": 0.7
                }
            },
            "moderate": {
                "name_ko": "중등도 저산소증",
                "description": "판단력이 눈에 띄게 저하되며 지적 능력과 화염의 연소 상태에도 이상이 나타난다.",
                "traits": ["hypoxia", "moderate", "impaired_judgment"],
                "oxygen_range": (50, 69),
                "effects": {
                    "judgment_penalty": -3,
                    "intelligence_penalty": -3,
                    "wisdom_penalty": -3,
                    "torch_flame": "blue_weak"
                }
            },
            "severe": {
                "name_ko": "중증 저산소증",
                "description": "심각한 산소 부족으로 호흡 곤란과 의식 장애가 발생하며 횃불이 완전히 꺼진다.",
                "traits": ["hypoxia", "severe", "respiratory_distress", "unconsciousness"],
                "oxygen_range": (30, 49),
                "effects": {
                    "breathing_difficulty": True,
                    "torch_extinguished": True,
                    "hp_loss_per_turn": 5,
                    "con_save_required": True
                }
            },
            "suffocation": {
                "name_ko": "질식",
                "description": "산소 농도가 생존 한계 아래로 떨어져 의식을 잃으며 빠르게 치명적인 뇌 손상이 진행된다.",
                "traits": ["suffocation", "critical", "unconscious", "brain_damage"],
                "oxygen_range": (0, 29),
                "effects": {
                    "consciousness": False,
                    "hp_loss_per_turn": 15,
                    "rescue_deadline_turns": 3,
                    "brain_death_if_unrescued": True
                }
            }
        }
    }
}

DUNGEON_ENVIRONMENT_SYSTEMS = {
    "TOXIC_GAS_SYSTEM": {
        "name_ko": "독성 가스 & 대기 오염 시스템",
        "description": "던전 내부에 축적된 독성 가스, 화산성 가스, 부패 가스 등이 산소와 별개로 생존자에게 지속적인 영향을 준다.",
        "traits": ["hardcore", "realistic", "gas", "poison", "air_quality"],
        "gas_types": {
            "carbon_dioxide": {
                "name_ko": "이산화탄소",
                "description": "밀폐된 공간이나 생물의 부패로 축적되며 낮은 곳에 고인다.",
                "traits": ["suffocation", "heavy_gas", "low_area"],
                "symptoms": ["두통", "호흡곤란", "졸음", "판단력저하"],
                "dangerous_concentration": 5.0,
                "con_save_dc": 12
            },
            "sulfur_gas": {
                "name_ko": "황화 가스",
                "description": "화산 지대나 유황 광맥에서 발생하며 고농도에서는 후각이 마비되어 위험을 감지하기 어렵다.",
                "traits": ["toxic", "volcanic", "odorless_at_high_concentration"],
                "symptoms": ["눈 따가움", "기침", "구토", "의식저하"],
                "dangerous_concentration": 3.0,
                "con_save_dc": 15
            },
            "corpse_gas": {
                "name_ko": "시체 부패 가스",
                "description": "수많은 시체가 밀폐된 공간에서 부패하면서 발생하는 유독성 가스.",
                "traits": ["decay", "toxic", "corpse"],
                "symptoms": ["메스꺼움", "현기증", "구토"],
                "dangerous_concentration": 4.0,
                "con_save_dc": 13
            },
            "spore_cloud": {
                "name_ko": "포자 구름",
                "description": "거대한 균류가 방출한 포자가 공기 중에 떠다닌다.",
                "traits": ["fungus", "spore", "infection"],
                "symptoms": ["기침", "호흡곤란", "환각"],
                "dangerous_concentration": 2.5,
                "con_save_dc": 14
            }
        }
    },
    "UNDERGROUND_WATER_SYSTEM": {
        "name_ko": "지하수 & 오염된 물 시스템",
        "description": "던전 내부의 물은 광물, 시체, 균류, 하수 등에 의해 오염될 수 있다.",
        "traits": ["hardcore", "water", "contamination", "survival"],
        "water_quality": {
            "clean": {
                "name_ko": "청정수",
                "description": "안전하게 음용할 수 있는 자연 지하수.",
                "traits": ["safe", "drinkable"],
                "disease_risk": 0,
                "poison_risk": 0
            },
            "stagnant": {
                "name_ko": "고인 물",
                "description": "오랫동안 흐르지 않아 세균과 기생충이 번식하기 쉽다.",
                "traits": ["stagnant", "bacteria", "parasite"],
                "disease_risk": 20,
                "poison_risk": 0
            },
            "sewage": {
                "name_ko": "하수 오염수",
                "description": "배설물과 부패물이 섞여 있어 심각한 감염을 일으킬 수 있다.",
                "traits": ["sewage", "fecal_contamination", "high_risk"],
                "disease_risk": 60,
                "poison_risk": 10
            },
            "corpse_contaminated": {
                "name_ko": "시체 오염수",
                "description": "부패한 시체가 장기간 잠겨 있던 물. 치명적인 병원체가 존재할 수 있다.",
                "traits": ["corpse", "pathogen", "extreme_risk"],
                "disease_risk": 80,
                "poison_risk": 25
            },
            "mineral_toxic": {
                "name_ko": "중금속 광천",
                "description": "광맥을 통과하며 독성 광물이 녹아든 물.",
                "traits": ["mineral", "heavy_metal", "toxic"],
                "disease_risk": 10,
                "poison_risk": 40
            }
        }
    },
    "FLOOR_HAZARD_SYSTEM": {
        "name_ko": "지면 붕괴 & 지형 위험 시스템",
        "description": "던전의 바닥은 침식, 수분, 지하 공동, 오래된 구조물 등에 의해 무너질 수 있다.",
        "traits": ["hardcore", "floor", "terrain", "collapse", "fall"],
        "floor_types": {
            "solid_rock": {
                "name_ko": "견고한 암반",
                "description": "자연적으로 형성된 단단한 암반층.",
                "traits": ["stable", "rock"],
                "durability": 120,
                "collapse_risk": 0,
                "slip_risk": 0,
                "break_risk": 0
            },
            "weathered_rock": {
                "name_ko": "풍화 암반",
                "description": "수분과 침식으로 내부 균열이 발생한 암반.",
                "traits": ["unstable", "weathered"],
                "durability": 60,
                "collapse_risk": 20,
                "slip_risk": 5,
                "break_risk": 15
            },
            "rotten_wood": {
                "name_ko": "부식 목재 바닥",
                "description": "오래된 지하 구조물의 목재가 부패하여 체중을 버티지 못할 수 있다.",
                "traits": ["wood", "rotting", "fragile"],
                "durability": 30,
                "collapse_risk": 50,
                "slip_risk": 10,
                "break_risk": 40
            },
            "thin_crust": {
                "name_ko": "지하 공동 위 얇은 지각",
                "description": "아래에 거대한 빈 공간이 존재하여 작은 충격에도 무너질 수 있다.",
                "traits": ["hidden_void", "extreme_risk"],
                "durability": 20,
                "collapse_risk": 80,
                "slip_risk": 10,
                "break_risk": 70
            },
            "ice_floor": {
                "name_ko": "빙결 지면",
                "description": "얼어붙은 물로 만들어진 바닥. 온도와 하중에 따라 미끄러지거나 깨질 수 있다.",
                "traits": ["ice", "slippery", "temperature_sensitive"],
                "durability": 50,
                "collapse_risk": 25,
                "slip_risk": 30,
                "break_risk": 25
            }
        }
    }
}


# ============================================================
# Dataclass Specifications (Mandatory traits tag list: Rule 6)
# ============================================================
@dataclass
class RockStrataSpec:
    strata_id: str
    name_ko: str
    description: str
    base_durability: float
    vibration_resistance: float
    fragment_sharpness: str
    water_damage_multiplier: float
    collapse_risk: str
    chain_collapse_chance: float = 0.0
    magic_damage_multiplier: float = 1.0
    traits: List[str] = field(default_factory=list)


@dataclass
class VibrationSourceSpec:
    source_id: str
    name_ko: str
    description: str
    base_impact: float
    is_magic: bool = False
    magic_circle_impacts: Dict[int, float] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)


@dataclass
class CollapseStageSpec:
    stage_id: str
    name_ko: str
    description: str
    durability_threshold: float
    dust_fall: bool = False
    visibility_penalty: int = 0
    light_penalty: int = 0
    minor_debris_damage: str = ""
    falling_rock_damage: str = ""
    dex_save_dc: int = 0
    passage_blocked: bool = False
    escape_route_reduction: int = 0
    burial_damage: str = ""
    instant_death_risk: bool = False
    escape_possible: bool = True
    rescue_required: bool = False
    movement_penalty: int = 0
    traits: List[str] = field(default_factory=list)


@dataclass
class ToxicGasSpec:
    gas_id: str
    name_ko: str
    description: str
    symptoms: List[str]
    dangerous_concentration: float = 5.0
    con_save_dc: int = 12
    traits: List[str] = field(default_factory=list)


@dataclass
class WaterQualitySpec:
    quality_id: str
    name_ko: str
    description: str
    disease_risk: int = 0
    poison_risk: int = 0
    traits: List[str] = field(default_factory=list)


@dataclass
class FloorHazardSpec:
    floor_type_id: str
    name_ko: str
    description: str
    durability: float = 100.0
    collapse_risk: int = 0
    slip_risk: int = 0
    break_risk: int = 0
    traits: List[str] = field(default_factory=list)


# ============================================================
# Registries Initialized from Master Data
# ============================================================
ROCK_STRATA_REGISTRY: Dict[str, RockStrataSpec] = {}
for _k, _v in CAVE_COLLAPSE_SYSTEM["rock_strata"].items():
    ROCK_STRATA_REGISTRY[_k] = RockStrataSpec(
        strata_id=_k,
        name_ko=_v["name_ko"],
        description=_v["description"],
        base_durability=float(_v["base_durability"]),
        vibration_resistance=float(_v["vibration_resistance"]),
        fragment_sharpness=_v.get("fragment_sharpness", "d8"),
        water_damage_multiplier=float(_v.get("water_damage_multiplier", 1.0)),
        collapse_risk=_v.get("collapse_risk", "medium"),
        chain_collapse_chance=float(_v.get("chain_collapse_chance", 0.0)),
        magic_damage_multiplier=float(_v.get("magic_damage_multiplier", 1.0)),
        traits=list(_v.get("traits", []))
    )

VIBRATION_SOURCES_REGISTRY: Dict[str, VibrationSourceSpec] = {
    "fireball_explosion": VibrationSourceSpec(
        source_id="fireball_explosion",
        name_ko="화염구/폭발 마법",
        description="폭발적인 마력과 열압력으로 주변 암반에 강한 충격 진동을 발생시킨다.",
        base_impact=20.0,
        is_magic=True,
        magic_circle_impacts={1: 10.0, 2: 20.0, 3: 30.0, 4: 40.0, 5: 50.0},
        traits=["magic", "explosion", "vibration", "fire"]
    ),
    "heavy_blunt_strike": VibrationSourceSpec(
        source_id="heavy_blunt_strike",
        name_ko="대형 둔기 강타",
        description="거대한 둔기나 공성급 무기가 암반을 강타하여 충격을 전달한다.",
        base_impact=10.0,
        traits=["impact", "blunt", "vibration"]
    ),
    "mining": VibrationSourceSpec(
        source_id="mining",
        name_ko="굴착/곡괭이질",
        description="반복적인 굴착 작업이 암반에 지속적인 미세 진동을 축적시킨다.",
        base_impact=3.0,
        traits=["mining", "repeated_vibration"]
    ),
    "trap_activation": VibrationSourceSpec(
        source_id="trap_activation",
        name_ko="함정 격발",
        description="대형 기계식 함정이나 폭발성 함정이 작동하여 강한 충격을 전달한다.",
        base_impact=20.0,
        traits=["trap", "impact", "sudden_vibration"]
    )
}

COLLAPSE_STAGES_REGISTRY: Dict[str, CollapseStageSpec] = {}
for _k, _v in CAVE_COLLAPSE_SYSTEM["collapse_stages"].items():
    COLLAPSE_STAGES_REGISTRY[_k] = CollapseStageSpec(
        stage_id=_k,
        name_ko=_v["name_ko"],
        description=_v["description"],
        durability_threshold=float(_v["durability_threshold"]),
        dust_fall=_v.get("dust_fall", False),
        visibility_penalty=_v.get("visibility_penalty", 0),
        light_penalty=_v.get("light_penalty", 0),
        minor_debris_damage=_v.get("minor_debris_damage", ""),
        falling_rock_damage=_v.get("falling_rock_damage", ""),
        dex_save_dc=_v.get("dex_save_dc", 0),
        passage_blocked=_v.get("passage_blocked", False),
        escape_route_reduction=_v.get("escape_route_reduction", 0),
        burial_damage=_v.get("burial_damage", ""),
        instant_death_risk=_v.get("instant_death_risk", False),
        escape_possible=_v.get("escape_possible", True),
        rescue_required=_v.get("rescue_required", False),
        movement_penalty=_v.get("movement_penalty", 0),
        traits=list(_v.get("traits", []))
    )

TOXIC_GAS_REGISTRY: Dict[str, ToxicGasSpec] = {}
for _k, _v in DUNGEON_ENVIRONMENT_SYSTEMS["TOXIC_GAS_SYSTEM"]["gas_types"].items():
    TOXIC_GAS_REGISTRY[_k] = ToxicGasSpec(
        gas_id=_k,
        name_ko=_v["name_ko"],
        description=_v["description"],
        symptoms=list(_v.get("symptoms", [])),
        dangerous_concentration=float(_v.get("dangerous_concentration", 5.0)),
        con_save_dc=int(_v.get("con_save_dc", 12)),
        traits=list(_v.get("traits", []))
    )

WATER_QUALITY_REGISTRY: Dict[str, WaterQualitySpec] = {}
for _k, _v in DUNGEON_ENVIRONMENT_SYSTEMS["UNDERGROUND_WATER_SYSTEM"]["water_quality"].items():
    WATER_QUALITY_REGISTRY[_k] = WaterQualitySpec(
        quality_id=_k,
        name_ko=_v["name_ko"],
        description=_v["description"],
        disease_risk=int(_v.get("disease_risk", 0)),
        poison_risk=int(_v.get("poison_risk", 0)),
        traits=list(_v.get("traits", []))
    )

FLOOR_HAZARD_REGISTRY: Dict[str, FloorHazardSpec] = {}
for _k, _v in DUNGEON_ENVIRONMENT_SYSTEMS["FLOOR_HAZARD_SYSTEM"]["floor_types"].items():
    FLOOR_HAZARD_REGISTRY[_k] = FloorHazardSpec(
        floor_type_id=_k,
        name_ko=_v["name_ko"],
        description=_v["description"],
        durability=float(_v.get("durability", 100.0)),
        collapse_risk=int(_v.get("collapse_risk", 0)),
        slip_risk=int(_v.get("slip_risk", 0)),
        break_risk=int(_v.get("break_risk", 0)),
        traits=list(_v.get("traits", []))
    )


# ============================================================
# Deterministic Cave Collapse & Dungeon Environment Physics Engine
# ============================================================
class CaveCollapseEngine:
    """
    Evaluates cave-in structural integrity, falling rocks, oxygen depletion,
    and environmental subterranean hazards with 100% deterministic logic.
    """

    @classmethod
    def get_rock_strata(cls, strata_id: str) -> RockStrataSpec:
        """Returns RockStrataSpec by ID, defaulting to granite."""
        return ROCK_STRATA_REGISTRY.get(strata_id, ROCK_STRATA_REGISTRY["granite"])

    @classmethod
    def get_collapse_stage_for_durability(cls, durability: float) -> str:
        """Determines the collapse stage string based on remaining durability."""
        if durability >= 70.0:
            return "stable"
        elif durability >= 40.0:
            return "cracking"
        elif durability >= 15.0:
            return "partial_collapse"
        else:
            return "full_collapse"

    @classmethod
    def apply_vibration(
        cls,
        location: Location,
        source_id: str,
        magnitude_override: Optional[float] = None,
        magic_circle: int = 1,
        state: Optional[WorldState] = None
    ) -> Tuple[float, str, List[str]]:
        """
        Applies impact vibration to a location's subterranean rock structure.
        Calculates durability loss, stage transitions, and generates event logs.
        Returns: (remaining_integrity, new_stage, event_logs)
        """
        logs: List[str] = []
        strata_id = getattr(location, "rock_strata", "granite")
        strata = cls.get_rock_strata(strata_id)

        # 1. Determine raw impact
        source_spec = VIBRATION_SOURCES_REGISTRY.get(source_id)
        if magnitude_override is not None:
            raw_impact = float(magnitude_override)
        elif source_spec:
            if source_spec.is_magic:
                circle = min(5, max(1, magic_circle))
                raw_impact = source_spec.magic_circle_impacts.get(circle, source_spec.base_impact)
            else:
                raw_impact = source_spec.base_impact
        else:
            raw_impact = 10.0

        # 2. Rock resistance & environmental multipliers
        effective_resistance = max(1.0, strata.vibration_resistance)
        damage = raw_impact * (100.0 / effective_resistance)

        if source_spec and source_spec.is_magic:
            damage *= strata.magic_damage_multiplier

        # Water dampening / erosion penalty if location is moist
        if getattr(location, "water_quality", "clean") != "clean" or "습기" in getattr(location, "traits", []):
            damage *= strata.water_damage_multiplier

        damage = round(max(1.0, damage), 1)

        # 3. Apply damage to structural integrity
        current_dur = getattr(location, "structural_integrity", strata.base_durability)
        new_dur = max(0.0, current_dur - damage)
        location.structural_integrity = new_dur

        old_stage = getattr(location, "collapse_stage", "stable")
        new_stage = cls.get_collapse_stage_for_durability(new_dur)
        location.collapse_stage = new_stage

        source_name = source_spec.name_ko if source_spec else source_id
        logs.append(
            f"⛏️ [암반 충격 진동] [{source_name}] 충격으로 [{strata.name_ko}] 천장 내구도 {damage} 손상! (잔여 내구도: {new_dur:.1f})"
        )

        # 4. Stage Transition Handling
        if new_stage != old_stage:
            stage_spec = COLLAPSE_STAGES_REGISTRY[new_stage]
            logs.append(f"⚠️ [낙반 위험 단계 격상] 천장 구조가 [{stage_spec.name_ko}] 단계로 악화되었습니다! ({stage_spec.description})")

            if new_stage == "cracking":
                if state and state.player:
                    dmg = 2
                    state.player.health = max(1, state.player.health - dmg)
                    logs.append(f"   * 천장에서 낙하한 흙먼지와 자갈 파편(1d4)으로 {dmg} 타박상을 입었습니다.")

            elif new_stage == "partial_collapse":
                if state and state.player:
                    # Agility Saving Throw (DC 15)
                    agi_mod = (state.player.agility - 10) // 2
                    save_roll = 10 + agi_mod  # Deterministic base average
                    if save_roll >= stage_spec.dex_save_dc:
                        logs.append("   * [민첩 판정 성공] 머리 위로 떨어지는 거대한 암석 덩어리를 몸을 날려 아슬아슬하게 피했습니다!")
                    else:
                        rock_dmg = 12
                        state.player.health = max(1, state.player.health - rock_dmg)
                        logs.append(f"   * [민첩 판정 실패!] 무너진 암석(1d12)에 직격당해 {rock_dmg} 심각한 압쇄 피해를 입었습니다!")

            elif new_stage == "full_collapse":
                if state and state.player:
                    burial_dmg = 40
                    state.player.health = max(1, state.player.health - burial_dmg)
                    logs.append(f"🚨 [전면 대붕괴!] 천장 전체가 굉음과 함께 붕괴하여 매몰 압쇄 피해 {burial_dmg}를 입었습니다! 탈출 통로가 차단되었습니다!")

        return new_dur, new_stage, logs

    @classmethod
    def consume_oxygen(cls, state: WorldState, amount: float, reason: str = "") -> List[str]:
        """
        Consumes subterranean oxygen and adjusts environmental metrics.
        """
        logs = []
        old_oxy = state.environment.oxygen_level
        new_oxy = max(0, min(100, int(old_oxy - amount)))
        state.environment.oxygen_level = new_oxy

        if reason:
            logs.append(f"🔥 [산소 급감] {reason}으로 인해 석실 산소가 {amount:.1f}% 소모되었습니다. (현재 산소: {new_oxy}%)")

        if old_oxy >= 50 and new_oxy < 50:
            logs.append("⚠️ [산소 위험] 석실 산소 농도가 50% 아래로 떨어져 불꽃이 푸른색으로 약화되고 호흡이 가빠집니다!")
        elif old_oxy >= 30 and new_oxy < 30:
            logs.append("🚨 [질식 경보] 산소 농도가 30% 미만으로 급락했습니다! 모든 횃불이 꺼지고 질식사가 임박했습니다!")

        return logs

    @classmethod
    def open_ventilation(cls, location: Location) -> Tuple[bool, str]:
        """
        Opens ventilation shafts in the location to allow fresh airflow.
        """
        location.ventilation_open = True
        return True, "🌬️ [환기구 개방] 외부와 연결된 석조 환기구를 개방하여 신선한 외기가 유입되기 시작합니다! (턴당 산소 +2.0% 회복)"

    @classmethod
    def purify_water(cls, source_water_type: str, method: str) -> Tuple[str, str, bool]:
        """
        Purifies contaminated water using boiling, filtering, or holy purification.
        Returns: (result_water_type, message_ko, is_safe)
        """
        if method == "holy_purification":
            return "clean", "✨ [성역 정화] 신성한 마력으로 물속의 모든 병원체와 중금속을 완전 정화했습니다! (청정수 전환)", True
        elif method == "boiling":
            if source_water_type == "mineral_toxic":
                return "mineral_toxic", "⚠️ [끓이기 실패] 끓여도 녹아든 중금속 독극물은 제거되지 않습니다.", False
            else:
                return "clean", "♨️ [물 끓이기 완료] 고온으로 가열하여 세균과 미생물 오염을 제거했습니다. (안전 음용 가능)", True
        elif method == "filtering":
            if source_water_type in ["sewage", "corpse_contaminated"]:
                return "stagnant", "💧 [물 여과] 큰 불순물과 유충은 걸러냈으나 미세 병원체가 잔류합니다. (고인 물 수준)", False
            elif source_water_type == "mineral_toxic":
                return "clean", "💧 [광물 여과] 숯과 모래 필터로 유독 침전물을 성공적으로 흡착했습니다.", True
            else:
                return "clean", "💧 [물 여과 완료] 안전한 식수로 정제되었습니다.", True
        return source_water_type, "정화 방법이 올바르지 않습니다.", False

    @classmethod
    def process_turn_environment(cls, state: WorldState) -> List[str]:
        """
        Processes subterranean environmental dynamics (Oxygen, Toxic Gas, Floor stability)
        per turn with 100% deterministic logic.
        """
        logs: List[str] = []
        loc = state.locations.get(state.player.location)
        if not loc:
            return logs

        # Check subterranean context
        is_underground = (
            getattr(loc, "location_category", "") == "dungeon"
            or getattr(loc, "floor_depth", 0) > 0
            or "지하" in getattr(loc, "name", "")
            or "지하" in getattr(state.environment, "weather", "")
            or "밀실" in getattr(loc, "traits", [])
        )

        if not is_underground:
            # Surface area naturally restores full oxygen
            if state.environment.oxygen_level < 100:
                state.environment.oxygen_level = min(100, state.environment.oxygen_level + 10)
            return logs

        # --------------------------------------------------------
        # 1. Oxygen Dynamics
        # --------------------------------------------------------
        party_count = 1 + len(state.party)
        oxy_delta = -0.2 * party_count  # Breathing

        # Check torch consumption
        has_torch = (
            getattr(state.player.equipment, "main_hand", "") == "torch"
            or getattr(state.player.equipment, "off_hand", "") == "torch"
            or "torch" in state.player.inventory
        )
        if has_torch and state.environment.lighting != "완전한 암흑":
            oxy_delta -= 1.0

        # Ventilation recovery
        if getattr(loc, "ventilation_open", False):
            oxy_delta += 2.0

        current_oxy = state.environment.oxygen_level
        new_oxy = max(0, min(100, int(round(current_oxy + oxy_delta))))
        state.environment.oxygen_level = new_oxy

        # Hypoxia Effects
        if new_oxy <= 29:
            suffocate_dmg = 15
            state.player.health = max(1, state.player.health - suffocate_dmg)
            logs.append(
                f"🚨 [치명적 질식!] 산소 농도가 {new_oxy}%로 떨어져 호흡 정지! 턴당 질식 피해 {suffocate_dmg}를 입었습니다! (3턴 내 환기 미개방 시 뇌사 위험)"
            )
        elif new_oxy <= 49:
            severe_dmg = 5
            state.player.health = max(1, state.player.health - severe_dmg)
            logs.append(
                f"⚠️ [중증 저산소증] 산소 농도 {new_oxy}%! 극심한 호흡 곤란으로 지속 피해 {severe_dmg}를 입었습니다. (횃불 불꽃 소화됨)"
            )
        elif new_oxy <= 69:
            logs.append(
                f"🌀 [중등도 저산소증] 산소 농도 {new_oxy}%. 뇌에 산소가 부족하여 판단력이 흐려지고 지능/지혜 -3 페널티를 받습니다."
            )
        elif new_oxy <= 80:
            logs.append(
                f"💧 [경도 저산소증] 산소 농도 {new_oxy}%. 두통과 피로감으로 인해 기력 자연 회복량이 30% 감소합니다."
            )

        # --------------------------------------------------------
        # 2. Toxic Gas Contamination
        # --------------------------------------------------------
        active_gas = getattr(loc, "active_toxic_gas", None)
        if active_gas and active_gas in TOXIC_GAS_REGISTRY:
            gas_spec = TOXIC_GAS_REGISTRY[active_gas]
            con_save = 10 + (state.player.constitution - 10) // 2
            if con_save < gas_spec.con_save_dc:
                if active_gas == "carbon_dioxide":
                    logs.append(f"🤢 [독성 가스: {gas_spec.name_ko}] 바닥에 고인 이산화탄소로 인해 심한 졸음과 두통이 밀려옵니다.")
                elif active_gas == "sulfur_gas":
                    gas_dmg = 6
                    state.player.health = max(1, state.player.health - gas_dmg)
                    logs.append(f"☣️ [독성 가스: {gas_spec.name_ko}] 매캐한 황화 가스를 흡입하여 눈이 따갑고 지속 피해 {gas_dmg}를 입었습니다!")
                elif active_gas == "corpse_gas":
                    logs.append(f"☠️ [독성 가스: {gas_spec.name_ko}] 부패한 시체 가스 흡입으로 심한 구토와 메스꺼움을 겪습니다.")
                elif active_gas == "spore_cloud":
                    logs.append(f"🍄 [독성 가스: {gas_spec.name_ko}] 공기 중 포자 구름을 들이마셔 기침 발작과 환각에 빠져듭니다.")

        # --------------------------------------------------------
        # 3. Floor Hazard Stability
        # --------------------------------------------------------
        floor_type = getattr(loc, "floor_type", "solid_rock")
        if floor_type != "solid_rock":
            floor_dur = getattr(loc, "floor_durability", 100.0)
            if floor_dur <= 30.0 and getattr(loc, "floor_collapse_stage", "stable") != "crack":
                loc.floor_collapse_stage = "crack"
                logs.append(f"⚠️ [발판 지면 균열] 딛고 있는 [{floor_type}] 바닥에서 쩌적 소리와 함께 균열이 번집니다! (붕괴 주의)")

        return logs

    @classmethod
    def assess_stability(cls, location: Location) -> Dict[str, Any]:
        """
        Returns a diagnostic summary of the location's structural & environmental state.
        """
        strata_id = getattr(location, "rock_strata", "granite")
        strata = cls.get_rock_strata(strata_id)
        stage_id = getattr(location, "collapse_stage", "stable")
        stage = COLLAPSE_STAGES_REGISTRY.get(stage_id, COLLAPSE_STAGES_REGISTRY["stable"])
        durability = getattr(location, "structural_integrity", strata.base_durability)

        return {
            "rock_strata": strata.name_ko,
            "structural_integrity": durability,
            "collapse_stage": stage.name_ko,
            "collapse_risk": strata.collapse_risk,
            "vibration_resistance": strata.vibration_resistance,
            "floor_type": getattr(location, "floor_type", "solid_rock"),
            "ventilation_open": getattr(location, "ventilation_open", False),
            "active_toxic_gas": getattr(location, "active_toxic_gas", None),
            "water_quality": getattr(location, "water_quality", "clean"),
            "traits": list(getattr(location, "traits", []))
        }
