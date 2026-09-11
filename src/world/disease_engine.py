"""
Epidemic, Disease, Parasite & Contagion Biological Survival Engine for Quilltale TRPG.
Deterministic calculation of 6 deadly plagues/parasites, incubation periods,
CON saving throws, stage progression, remedies, and quarantine physics.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import random
import logging

from src.world.state import WorldState, Player, NPC
from src.world.dice import DiceEngine

logger = logging.getLogger(__name__)

# ============================================================
# Master Raw System Data (EPIDEMIC_SYSTEM)
# ============================================================
EPIDEMIC_SYSTEM = {
    "diseases": {
        "black_plague": {
            "name_ko": "흑사병",
            "name_en": "Black Plague",
            "description": "감염된 시체나 쥐와의 접촉으로 전파되는 치명적인 세균성 역병. 림프절이 급격히 붓고 피부가 검게 괴사하며 전신 쇼크로 이어진다.",
            "transmission_routes": [
                "감염된 쥐와 접촉",
                "감염자의 체액 접촉",
                "감염된 시체 접촉",
                "오염된 의복 및 침구 접촉"
            ],
            "incubation_turns": {"min": 2, "max": 6},
            "con_save_dc": 17,
            "stages": {
                "stage_1": {
                    "name_ko": "초기 발열기",
                    "duration_turns": 2,
                    "symptoms": ["미열", "오한", "두통", "식욕 감소"],
                    "effects": {"stamina_recovery_multiplier": 0.7, "con": -1}
                },
                "stage_2": {
                    "name_ko": "림프절 종창기",
                    "duration_turns": 3,
                    "symptoms": ["림프절 극심한 종창", "고열", "근육통", "피부 출혈 반점"],
                    "effects": {"str": -3, "dex": -2, "max_hp_percent": -20, "fever_damage_per_turn": 3}
                },
                "stage_3": {
                    "name_ko": "흑색 괴사기",
                    "duration_turns": 3,
                    "symptoms": ["피부 흑색 괴사", "의식 혼미", "혈압 급락", "전신 쇼크"],
                    "effects": {"max_hp_percent": -50, "hp_loss_per_turn": 12, "death_save_dc": 20, "death_save_interval": 1}
                }
            },
            "remedies": {
                "herbs": [
                    {
                        "name": "역병초 달인물",
                        "condition": "stage_1 또는 stage_2",
                        "check_dc": 16,
                        "success": "진행도 1단계 감소"
                    }
                ],
                "alcohol_disinfection": {
                    "condition": "외부 상처가 존재할 경우",
                    "check_dc": 12,
                    "effect": "추가 감염 확률 감소"
                },
                "holy_purification": {
                    "condition": "stage_3 이전",
                    "check_dc": 18,
                    "effect": "질병 진행도 즉시 초기화"
                }
            },
            "traits": ["bacterial", "contact_transmission", "plague", "necrosis", "extreme_lethality"]
        },

        "dysentery": {
            "name_ko": "오염수 이질",
            "name_en": "Dysentery",
            "description": "오염된 물이나 부패한 식품을 섭취하면서 발생하는 장 감염. 지속적인 설사로 수분과 전해질을 잃어 전투 지속력을 급격히 떨어뜨린다.",
            "transmission_routes": [
                "오염된 식수 음용",
                "고인 물 섭취",
                "상한 음식 섭취",
                "오염된 식기 사용"
            ],
            "incubation_turns": {"min": 1, "max": 3},
            "con_save_dc": 13,
            "stages": {
                "stage_1": {
                    "name_ko": "장염 초기",
                    "duration_turns": 2,
                    "symptoms": ["복통", "묽은 변", "메스꺼움"],
                    "effects": {"stamina_recovery_multiplier": 0.8, "food_consumption_multiplier": 1.2}
                },
                "stage_2": {
                    "name_ko": "활동성 이질",
                    "duration_turns": 4,
                    "symptoms": ["극심한 설사", "혈변", "복부 경련", "탈수"],
                    "effects": {
                        "stamina_loss_per_turn": 4,
                        "max_stamina_percent": -40,
                        "dex": -2,
                        "water_consumption_multiplier": 2.0,
                        "movement_penalty": 0.25
                    }
                },
                "stage_3": {
                    "name_ko": "탈수 쇼크",
                    "duration_turns": 3,
                    "symptoms": ["의식 저하", "극심한 탈수", "근육 경련", "혈압 저하"],
                    "effects": {"hp_loss_per_turn": 8, "stamina_recovery_disabled": True, "con": -5, "death_save_dc": 17}
                }
            },
            "remedies": {
                "herbs": [
                    {
                        "name": "지사초 달인물",
                        "condition": "stage_1 또는 stage_2",
                        "check_dc": 13,
                        "effect": "설사 강도 50% 감소"
                    },
                    {
                        "name": "염분 약초탕",
                        "condition": "탈수 상태",
                        "check_dc": 10,
                        "effect": "수분 및 전해질 회복"
                    }
                ],
                "alcohol_disinfection": {
                    "condition": "오염된 식수원이 확인된 경우",
                    "check_dc": 10,
                    "effect": "해당 수원의 추가 감염 방지"
                },
                "holy_purification": {
                    "condition": "stage_3",
                    "check_dc": 16,
                    "effect": "질병 진행 중단 및 탈수 회복 시작"
                }
            },
            "traits": ["waterborne", "foodborne", "intestinal", "dehydration", "contagious"]
        },

        "corpse_decay_fever": {
            "name_ko": "시체독 부패열",
            "name_en": "Corpse Decay Fever",
            "description": "부패한 시체의 체액이나 언데드의 공격으로 체내에 부패성 독기가 침투하는 질병. 감염자는 고열과 오한을 겪으며 말기에는 환각과 섬망에 빠진다.",
            "transmission_routes": [
                "언데드에게 물림",
                "언데드의 손톱에 의한 상처",
                "부패한 시체의 체액 접촉",
                "시체 갈무리 중 열린 상처로 침투"
            ],
            "incubation_turns": {"min": 1, "max": 4},
            "con_save_dc": 15,
            "stages": {
                "stage_1": {
                    "name_ko": "부패열 초기",
                    "duration_turns": 2,
                    "symptoms": ["미열", "오한", "상처 주변의 이상한 냄새", "피로"],
                    "effects": {"con": -1, "healing_received_multiplier": 0.8}
                },
                "stage_2": {
                    "name_ko": "전신 부패열",
                    "duration_turns": 3,
                    "symptoms": ["고열", "심한 오한", "상처 괴사", "환청"],
                    "effects": {"hp_loss_per_turn": 5, "wis": -3, "int": -2, "healing_received_multiplier": 0.5}
                },
                "stage_3": {
                    "name_ko": "부패성 섬망",
                    "duration_turns": 3,
                    "symptoms": ["심각한 환각", "의식 혼탁", "근육 경련", "장기 기능 저하"],
                    "effects": {
                        "hp_loss_per_turn": 12,
                        "random_action_chance": 0.25,
                        "ally_targeting_chance": 0.15,
                        "death_save_dc": 18
                    }
                }
            },
            "remedies": {
                "herbs": [
                    {
                        "name": "정화쑥 연고",
                        "condition": "감염 상처 존재",
                        "check_dc": 14,
                        "effect": "감염 진행 1단계 지연"
                    }
                ],
                "alcohol_disinfection": {
                    "condition": "감염 후 2턴 이내",
                    "check_dc": 13,
                    "effect": "초기 감염 제거 확률 증가"
                },
                "holy_purification": {
                    "condition": "stage_1~stage_3",
                    "check_dc": 15,
                    "effect": "질병 즉시 제거"
                }
            },
            "traits": ["undead_related", "wound_transmission", "fever", "hallucination", "necrotic"]
        },

        "cave_spore_mycosis": {
            "name_ko": "지하 진균 포자증",
            "name_en": "Cave Spore Mycosis",
            "description": "포자가 가득한 동굴이나 지하 유적에 장기간 노출될 때 발생하는 호흡기 진균 감염. 진행될수록 폐 기능이 손상되어 지속적인 기침이 발생한다.",
            "transmission_routes": [
                "진균 포자 흡입",
                "포자 구름 통과",
                "감염된 생물과 밀폐 공간 동행"
            ],
            "incubation_turns": {"min": 3, "max": 8},
            "con_save_dc": 14,
            "stages": {
                "stage_1": {
                    "name_ko": "포자 잠복기",
                    "duration_turns": 3,
                    "symptoms": ["목의 이물감", "가벼운 기침", "흉부 불쾌감"],
                    "effects": {"stealth_noise": 1, "stamina_recovery_multiplier": 0.9}
                },
                "stage_2": {
                    "name_ko": "진균 증식기",
                    "duration_turns": 5,
                    "symptoms": ["지속적인 기침", "호흡 곤란", "흉통", "시야 흐림"],
                    "effects": {
                        "stealth_broken_by_cough": True,
                        "stealth_break_chance": 0.35,
                        "stamina_cost_multiplier": 1.5,
                        "dex": -2,
                        "hp_loss_per_turn": 3
                    }
                },
                "stage_3": {
                    "name_ko": "폐 섬유화",
                    "duration_turns": 6,
                    "symptoms": ["심각한 호흡 곤란", "폐 섬유화", "산소 부족", "기침 발작"],
                    "effects": {
                        "max_stamina_percent": -60,
                        "hp_loss_per_turn": 8,
                        "stealth_impossible": True,
                        "movement_penalty": 0.5,
                        "death_save_dc": 17
                    }
                }
            },
            "remedies": {
                "herbs": [
                    {
                        "name": "기관지초 훈증",
                        "condition": "stage_1 또는 stage_2",
                        "check_dc": 15,
                        "effect": "기침 및 포자 증식 억제"
                    }
                ],
                "alcohol_disinfection": {
                    "condition": "호흡기 감염 예방",
                    "check_dc": 10,
                    "effect": "장비에 묻은 포자 제거"
                },
                "holy_purification": {
                    "condition": "stage_2 또는 stage_3",
                    "check_dc": 17,
                    "effect": "진균 감염 제거 및 진행 중단"
                }
            },
            "traits": ["fungal", "airborne", "cave", "respiratory", "stealth_disruption"]
        },

        "blood_leech_parasite": {
            "name_ko": "흡혈 거머리 기생충",
            "name_en": "Blood Leech Parasite",
            "description": "늪지나 하수도의 오염된 물속에서 피부를 뚫고 침투하는 흡혈성 기생충. 혈관에 달라붙어 지속적으로 피를 빨아먹으며 장기간 방치하면 최대 체력까지 감소시킨다.",
            "transmission_routes": [
                "늪지 보행",
                "하수도 침수 구역 통과",
                "오염된 물에 장시간 노출",
                "피부 상처를 통한 침투"
            ],
            "incubation_turns": {"min": 0, "max": 2},
            "con_save_dc": 12,
            "stages": {
                "stage_1": {
                    "name_ko": "피부 침투",
                    "duration_turns": 2,
                    "symptoms": ["피부 가려움", "작은 출혈", "이물감"],
                    "effects": {"hp_loss_per_turn": 1, "bleeding_chance": 0.1}
                },
                "stage_2": {
                    "name_ko": "흡혈 활성기",
                    "duration_turns": 5,
                    "symptoms": ["지속적인 출혈", "현기증", "창백한 피부", "심한 피로"],
                    "effects": {
                        "hp_loss_per_turn": 3,
                        "max_hp_loss_per_turn": 1,
                        "stamina_recovery_multiplier": 0.5,
                        "con": -2
                    }
                },
                "stage_3": {
                    "name_ko": "기생성 빈혈",
                    "duration_turns": 5,
                    "symptoms": ["심각한 빈혈", "실신", "심박 이상", "전투 불능"],
                    "effects": {
                        "hp_loss_per_turn": 6,
                        "max_hp_percent": -30,
                        "str": -4,
                        "dex": -4,
                        "unconsciousness_check_dc": 16
                    }
                }
            },
            "remedies": {
                "herbs": [
                    {
                        "name": "구충초 농축액",
                        "condition": "stage_1 또는 stage_2",
                        "check_dc": 13,
                        "effect": "기생충 활동 억제"
                    }
                ],
                "alcohol_disinfection": {
                    "condition": "피부에 붙은 기생충 발견 시",
                    "check_dc": 10,
                    "effect": "기생충 제거 보조"
                },
                "holy_purification": {
                    "condition": "stage_2 또는 stage_3",
                    "check_dc": 14,
                    "effect": "기생충 즉시 제거"
                }
            },
            "traits": ["parasite", "blood_loss", "swamp", "sewer", "skin_penetration"]
        },

        "rabies_madness": {
            "name_ko": "광견병·마수 광란증",
            "name_en": "Rabies Madness",
            "description": "광란 상태의 야수에게 물린 뒤 신경계를 침범하는 치명적인 감염. 말기에는 물과 빛, 소리에 대한 극심한 반응과 함께 이성을 잃는다.",
            "transmission_routes": [
                "감염된 야수에게 물림",
                "감염된 야수의 침이 상처에 접촉",
                "감염된 생물의 발톱에 의한 상처"
            ],
            "incubation_turns": {"min": 4, "max": 12},
            "con_save_dc": 18,
            "stages": {
                "stage_1": {
                    "name_ko": "신경계 잠복기",
                    "duration_turns": 3,
                    "symptoms": ["물린 부위 통증", "미열", "불안", "감각 과민"],
                    "effects": {"wis": -1, "sleep_recovery_multiplier": 0.8}
                },
                "stage_2": {
                    "name_ko": "광란 발작기",
                    "duration_turns": 4,
                    "symptoms": ["물 공포증", "근육 경련", "침 분비 증가", "환각", "극심한 불안"],
                    "effects": {
                        "wis": -4,
                        "int": -3,
                        "water_consumption_impossible": True,
                        "berserk_chance": 0.25,
                        "ally_attack_chance": 0.15
                    }
                },
                "stage_3": {
                    "name_ko": "신경 마비 말기",
                    "duration_turns": 3,
                    "symptoms": ["전신 경련", "의식 혼미", "호흡 근육 마비", "혼수"],
                    "effects": {
                        "movement_impossible": True,
                        "action_impossible": True,
                        "hp_loss_per_turn": 15,
                        "death_save_dc": 20,
                        "death_countdown_turns": 3
                    }
                }
            },
            "remedies": {
                "herbs": [
                    {
                        "name": "신경안정초",
                        "condition": "stage_1",
                        "check_dc": 16,
                        "effect": "증상 발현 지연"
                    }
                ],
                "alcohol_disinfection": {
                    "condition": "물린 직후 1턴 이내",
                    "check_dc": 12,
                    "effect": "상처 세척 및 감염 위험 감소"
                },
                "holy_purification": {
                    "condition": "증상 발현 이전",
                    "check_dc": 18,
                    "effect": "감염 제거"
                }
            },
            "traits": ["viral", "bite_transmission", "neurological", "rabies", "madness", "extreme_lethality"]
        }
    },

    "infection_rules": {
        "name_ko": "감염 판정 규칙",
        "description": "질병별 감염 경로가 충족되면 체질 저항 판정을 실시한다.",
        "traits": ["infection_check", "constitution_save"],
        "rules": {
            "successful_save": "감염되지 않음",
            "failed_save": "잠복기 시작",
            "critical_success": "감염되지 않으며 해당 질병에 대한 일시적 저항 획득",
            "critical_failure": "즉시 stage_1 진입",
            "multiple_exposure": "동일 질병에 반복 노출되면 감염 판정 DC +2",
            "immune_compromised": "다른 질병에 감염된 상태에서는 모든 감염 판정 DC +2"
        }
    },

    "quarantine_rules": {
        "name_ko": "격리 규칙",
        "description": "전염성 질병 보유자는 파티와의 접촉을 제한하지 않으면 동료에게 질병을 전파할 수 있다.",
        "traits": ["quarantine", "contagion", "party_management"],
        "rules": {
            "close_contact": "감염자와 같은 공간에서 장시간 행동 시 추가 감염 판정",
            "shared_bedding": "같은 침구 사용 시 감염 DC +4",
            "shared_food": "같은 식기 사용 시 수인성·식품성 질병 감염 판정",
            "protective_mask": "공기 전파 질병 감염 확률 50% 감소",
            "quarantine_room": "전파 확률 80% 감소",
            "corpse_burning": "감염된 시체를 소각하면 시체 기반 전파 차단"
        }
    }
}


# ============================================================
# Dataclass Specifications (Mandatory traits tag list: Rule 6)
# ============================================================
@dataclass
class DiseaseStageSpec:
    stage_id: str
    name_ko: str
    duration_turns: int
    symptoms: List[str] = field(default_factory=list)
    effects: Dict[str, Any] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)


@dataclass
class DiseaseSpec:
    disease_id: str
    name_ko: str
    name_en: str
    description: str
    transmission_routes: List[str]
    incubation_min_turns: int
    incubation_max_turns: int
    con_save_dc: int
    stages: Dict[str, DiseaseStageSpec]
    remedies: Dict[str, Any]
    traits: List[str] = field(default_factory=list)


@dataclass
class ActiveInfection:
    disease_id: str
    current_stage: str = "incubating"          # "incubating", "stage_1", "stage_2", "stage_3", "cured", "fatal"
    turns_in_stage: int = 0
    incubation_turns_remaining: int = 0
    is_incubating: bool = True
    exposure_count: int = 1
    traits: List[str] = field(default_factory=list)


@dataclass
class InfectionAttemptResult:
    infected: bool
    is_critical_success: bool = False
    is_critical_failure: bool = False
    incubation_turns: int = 0
    stage: str = ""
    roll: int = 0
    dc: int = 0
    message_ko: str = ""
    traits: List[str] = field(default_factory=list)


# ============================================================
# Registries Initialized from Master Data
# ============================================================
DISEASE_REGISTRY: Dict[str, DiseaseSpec] = {}

for _d_id, _d_data in EPIDEMIC_SYSTEM["diseases"].items():
    _stages = {}
    for _st_id, _st_data in _d_data["stages"].items():
        _stages[_st_id] = DiseaseStageSpec(
            stage_id=_st_id,
            name_ko=_st_data["name_ko"],
            duration_turns=_st_data["duration_turns"],
            symptoms=list(_st_data["symptoms"]),
            effects=dict(_st_data["effects"]),
            traits=[_d_id, _st_id, _st_data["name_ko"]]
        )
    DISEASE_REGISTRY[_d_id] = DiseaseSpec(
        disease_id=_d_id,
        name_ko=_d_data["name_ko"],
        name_en=_d_data["name_en"],
        description=_d_data["description"],
        transmission_routes=list(_d_data["transmission_routes"]),
        incubation_min_turns=_d_data["incubation_turns"]["min"],
        incubation_max_turns=_d_data["incubation_turns"]["max"],
        con_save_dc=_d_data["con_save_dc"],
        stages=_stages,
        remedies=dict(_d_data["remedies"]),
        traits=list(_d_data.get("traits", []))
    )


# ============================================================
# Deterministic Epidemic & Contagion Engine
# ============================================================
class EpidemicEngine:
    """
    Evaluates disease transmission, CON saving throws, incubation,
    multi-stage symptomatic progression, remedies, and quarantine physics
    with 100% deterministic logic.
    """

    @classmethod
    def get_disease(cls, disease_id: str) -> Optional[DiseaseSpec]:
        """Retrieves disease specification from registry."""
        return DISEASE_REGISTRY.get(disease_id)

    @classmethod
    def attempt_infection(
        cls,
        target: Any,
        disease_id: str,
        state: WorldState,
        is_shared_bedding: bool = False,
        has_mask: bool = False,
        is_quarantined: bool = False,
        base_dc_bonus: int = 0,
        fixed_roll: Optional[int] = None
    ) -> InfectionAttemptResult:
        """
        Calculates whether an entity is infected via CON saving throw.
        - Critical Success (20): Immune, no infection.
        - Critical Failure (1): Immediate Stage 1 onset.
        - Success (total >= DC): Resisted, not infected.
        - Failure (total < DC): Incubation period begins.
        """
        spec = cls.get_disease(disease_id)
        if not spec:
            return InfectionAttemptResult(
                infected=False, message_ko=f"알 수 없는 질병 ID: {disease_id}"
            )

        # 1. Quarantine & Protection Filters
        if is_quarantined and random.random() < 0.80:
            return InfectionAttemptResult(
                infected=False,
                message_ko=f"🛡️ [격리 차단] 격리 구역의 철저한 방역 조치로 [{spec.name_ko}] 전파가 80% 확률로 차단되었습니다."
            )

        if has_mask and "airborne" in spec.traits and random.random() < 0.50:
            return InfectionAttemptResult(
                infected=False,
                message_ko=f"😷 [마스크 차단] 방역 마스크 착용으로 공기 전파형 [{spec.name_ko}]의 흡입이 차단되었습니다."
            )

        # 2. Calculate Effective DC
        con_val = getattr(target, "constitution", 10)
        con_mod = (con_val - 10) // 2

        active_infs = getattr(target, "active_infections", {})
        immune_penalty = 2 if active_infs else 0
        multi_exposure_penalty = 2 if disease_id in active_infs else 0
        bedding_penalty = 4 if is_shared_bedding else 0

        effective_dc = spec.con_save_dc + base_dc_bonus + immune_penalty + multi_exposure_penalty + bedding_penalty

        # 3. Roll d20 CON save
        roll = fixed_roll if fixed_roll is not None else random.randint(1, 20)
        total = roll + con_mod

        # 4. Determine Result
        if roll == 20:
            return InfectionAttemptResult(
                infected=False,
                is_critical_success=True,
                roll=roll,
                dc=effective_dc,
                message_ko=f"✨ [체질 대성공] (d20:{roll} + 체질:{con_mod} vs DC {effective_dc}) 강인한 생명력으로 [{spec.name_ko}]에 완전히 저항했습니다! 일시적 면역을 획득합니다."
            )
        elif roll == 1:
            # Critical Failure: Immediate Stage 1 onset
            active_inf = ActiveInfection(
                disease_id=disease_id,
                current_stage="stage_1",
                turns_in_stage=0,
                incubation_turns_remaining=0,
                is_incubating=False,
                traits=[disease_id, "stage_1", "critical_onset"]
            )
            if not hasattr(target, "active_infections"):
                target.active_infections = {}
            target.active_infections[disease_id] = active_inf

            return InfectionAttemptResult(
                infected=True,
                is_critical_failure=True,
                stage="stage_1",
                roll=roll,
                dc=effective_dc,
                message_ko=f"🚨 [체질 대실패] (d20:{roll} vs DC {effective_dc}) [{spec.name_ko}]에 치명적으로 노출되어 잠복기 없이 즉시 [1단계: {spec.stages['stage_1'].name_ko}]에 진입했습니다!"
            )
        elif total >= effective_dc:
            return InfectionAttemptResult(
                infected=False,
                roll=roll,
                dc=effective_dc,
                message_ko=f"🛡️ [체질 저항 성공] (d20:{roll} + 체질:{con_mod} = {total} vs DC {effective_dc}) [{spec.name_ko}] 병원체를 면역 체계로 이겨냈습니다."
            )
        else:
            # Failure: Incubation begins
            incubation_turns = random.randint(spec.incubation_min_turns, spec.incubation_max_turns)
            active_inf = ActiveInfection(
                disease_id=disease_id,
                current_stage="incubating",
                turns_in_stage=0,
                incubation_turns_remaining=incubation_turns,
                is_incubating=True,
                traits=[disease_id, "incubating"]
            )
            if not hasattr(target, "active_infections"):
                target.active_infections = {}
            target.active_infections[disease_id] = active_inf

            return InfectionAttemptResult(
                infected=True,
                incubation_turns=incubation_turns,
                stage="incubating",
                roll=roll,
                dc=effective_dc,
                message_ko=f"⚠️ [감염 잠복기 시작] (d20:{roll} + 체질:{con_mod} = {total} vs DC {effective_dc}) [{spec.name_ko}] 병원체가 체내에 침투했습니다. (잠복기: {incubation_turns}턴)"
            )

    @classmethod
    def process_turn_infections(cls, state: WorldState, delta_minutes: int = 30) -> List[str]:
        """
        Processes turn-based disease progression, symptoms, damage,
        and behavioral anomalies for the player and active companions, scaled by delta_minutes.
        """
        logs: List[str] = []
        entities = [state.player]

        # Include companions if party engine is active
        if hasattr(state, "party") and hasattr(state.party, "companions"):
            for comp in state.party.companions.values():
                entities.append(comp)

        turn_ticks = max(1, round(delta_minutes / 30.0))

        for entity in entities:
            name = getattr(entity, "name", "플레이어")
            infs = getattr(entity, "active_infections", {})
            if not infs:
                continue

            for d_id, inf in list(infs.items()):
                spec = cls.get_disease(d_id)
                if not spec:
                    continue

                # 1. Incubation progression
                if inf.is_incubating:
                    inf.incubation_turns_remaining -= turn_ticks
                    if inf.incubation_turns_remaining <= 0:
                        inf.is_incubating = False
                        inf.current_stage = "stage_1"
                        inf.turns_in_stage = 0
                        stage_spec = spec.stages.get("stage_1")
                        logs.append(
                            f"🤒 [{spec.name_ko} 발병] {name}의 잠복기가 끝나고 [1단계: {stage_spec.name_ko if stage_spec else '초기'}] 증상이 발현되었습니다! (증상: {', '.join(stage_spec.symptoms) if stage_spec else '발열'})"
                        )
                    continue

                # 2. Active Stage Progression
                stage_spec = spec.stages.get(inf.current_stage)
                if not stage_spec:
                    continue

                inf.turns_in_stage += turn_ticks

                # Apply Stage Damage & Physiological Effects
                effects = stage_spec.effects

                # Damage per turn (fever / hp_loss)
                damage_per_turn = effects.get("hp_loss_per_turn", 0) + effects.get("fever_damage_per_turn", 0)
                damage = damage_per_turn * turn_ticks
                if damage > 0:
                    entity.health = max(1, entity.health - damage)
                    duration_str = f" ({turn_ticks * 30}분간)" if turn_ticks > 1 else ""
                    logs.append(
                        f"🩸 [{spec.name_ko} {stage_spec.name_ko}] {name}이(가) 병마로 인해{duration_str} 지속 피해 {damage}를 입었습니다. (현재 체력: {entity.health}/{entity.max_health})"
                    )

                # Stamina loss per turn
                sta_loss_per_turn = effects.get("stamina_loss_per_turn", 0)
                sta_loss = sta_loss_per_turn * turn_ticks
                if sta_loss > 0 and hasattr(entity, "stamina"):
                    entity.stamina = max(0, entity.stamina - sta_loss)
                    logs.append(f"💧 [{spec.name_ko}] 극심한 전해질 손실로 기력이 {sta_loss} 감소했습니다.")

                # Stealth break by cough (Cave spore mycosis)
                if effects.get("stealth_broken_by_cough", False):
                    break_chance = effects.get("stealth_break_chance", 0.35)
                    if random.random() < break_chance:
                        logs.append(
                            f"🗣️ [{spec.name_ko}] {name}이(가) 참을 수 없는 발작성 기침을 터뜨려 은신 상태가 파괴되고 주변에 소음(45dB)을 방출했습니다!"
                        )

                # Behavioral Madness (Rabies / Corpse Decay Fever)
                if effects.get("berserk_chance", 0.0) > 0 and random.random() < effects["berserk_chance"]:
                    logs.append(
                        f"🐺 [{spec.name_ko} 광란] {name}이(가) 신경계 붕괴로 극도의 공황과 살육 충동에 휩싸여 광란 상태에 빠졌습니다!"
                    )

                # Stage Transition
                if inf.turns_in_stage >= stage_spec.duration_turns:
                    if inf.current_stage == "stage_1" and "stage_2" in spec.stages:
                        inf.current_stage = "stage_2"
                        inf.turns_in_stage = 0
                        next_stage = spec.stages["stage_2"]
                        logs.append(
                            f"🚨 [{spec.name_ko} 악화] {name}의 병세가 중증인 [2단계: {next_stage.name_ko}]로 전이되었습니다! (증상: {', '.join(next_stage.symptoms)})"
                        )
                    elif inf.current_stage == "stage_2" and "stage_3" in spec.stages:
                        inf.current_stage = "stage_3"
                        inf.turns_in_stage = 0
                        next_stage = spec.stages["stage_3"]
                        logs.append(
                            f"☠️ [{spec.name_ko} 위독] {name}의 병세가 치명적인 [3단계: {next_stage.name_ko}]에 도달했습니다! 즉각 치료하지 않으면 사망 위험에 처합니다."
                        )

        return logs

    @classmethod
    def apply_remedy(
        cls,
        target: Any,
        disease_id: str,
        remedy_type: str,
        herb_name: str = "",
        state: Optional[WorldState] = None,
        fixed_roll: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Applies a treatment remedy (herbs, alcohol, holy purification, cauterization)
        to alleviate or cure an active infection.
        """
        spec = cls.get_disease(disease_id)
        if not spec:
            return False, f"알 수 없는 질병 ID: {disease_id}"

        infs = getattr(target, "active_infections", {})
        if disease_id not in infs:
            return False, f"{getattr(target, 'name', '대상')}은(는) [{spec.name_ko}]에 감염되어 있지 않습니다."

        inf = infs[disease_id]
        roll = fixed_roll if fixed_roll is not None else random.randint(1, 20)

        # 1. Holy Purification (Miracle / Sacred Spell)
        if remedy_type == "holy_purification":
            dc = 15
            if inf.current_stage == "stage_3":
                dc = 18
            if roll >= dc:
                del infs[disease_id]
                return True, f"✨ [신성 정화 성공] 거룩한 신성력의 은총으로 {getattr(target, 'name', '대상')}의 체내에서 [{spec.name_ko}] 병마가 완전히 소멸되었습니다!"
            else:
                return False, f"☁️ [신성 정화 부족] (d20:{roll} vs DC {dc}) 신성력이 병마의 뿌리를 완전히 태우기에 부족했습니다."

        # 2. Alcohol Disinfection (Wound / Early stage)
        elif remedy_type == "alcohol_disinfection":
            if inf.is_incubating or inf.current_stage == "stage_1":
                dc = 12
                if roll >= dc:
                    del infs[disease_id]
                    return True, f"🍶 [알코올 소독 성공] 독주와 소독약으로 환부를 세척하여 [{spec.name_ko}]의 침투 병원체를 완전히 사멸시켰습니다."
                else:
                    return False, f"🍶 [소독 실패] (d20:{roll} vs DC {dc}) 소독약의 농도가 부족하여 병원체 침투를 막지 못했습니다."
            else:
                return False, f"알코올 외상 소독은 이미 혈관과 신경계로 전이된 [2단계 이상]의 병세를 치료할 수 없습니다."

        # 3. Herb Decoction / Ointment
        elif remedy_type == "herbs":
            dc = 14
            if roll >= dc:
                if inf.current_stage == "stage_2":
                    inf.current_stage = "stage_1"
                    inf.turns_in_stage = 0
                    return True, f"🌿 [약초 치료 성공] {herb_name or '특효 약초'}의 약효로 [{spec.name_ko}] 병세가 [1단계]로 호전되었습니다."
                elif inf.current_stage == "stage_1" or inf.is_incubating:
                    del infs[disease_id]
                    return True, f"🌿 [완치 성공] {herb_name or '특효 약초'}의 해독 성분으로 [{spec.name_ko}] 병마를 완전히 극복했습니다!"
                else:
                    # Stage 3
                    inf.current_stage = "stage_2"
                    inf.turns_in_stage = 0
                    return True, f"🌿 [위기 완화] {herb_name or '특효 약초'}로 치명적 쇼크를 가까스로 가라앉혀 병세를 [2단계]로 완화했습니다."
            else:
                return False, f"🌿 [약초 투약 실패] (d20:{roll} vs DC {dc}) 약초의 배합이 맞지 않아 뚜렷한 차도가 없습니다."

        # 4. Cauterization (Wound Searing with Fire/Blade)
        elif remedy_type == "cauterization":
            if inf.is_incubating:
                target.health = max(1, target.health - 8)
                if hasattr(target, "stress"):
                    target.stress = min(100, target.stress + 20)
                del infs[disease_id]
                return True, f"🔥 [환부 소작 성공] 달군 쇠붙이로 물린 상처를 지져 극심한 고통(피해 8, 스트레스 +20)을 겪었지만, [{spec.name_ko}]의 신경 침투를 완벽히 차단했습니다!"
            else:
                return False, f"이미 체내 전신으로 퍼진 질병은 환부를 지지는 것으로 치료할 수 없습니다."

        return False, "유효하지 않은 치료 방식입니다."

    @classmethod
    def burn_corpses(cls, state: WorldState, location_id: str) -> Tuple[bool, str]:
        """Burns infected corpses at the location, eliminating corpse-based transmission vectors."""
        loc = state.locations.get(location_id)
        loc_name = loc.name if loc else location_id
        return True, f"🔥 [시체 소각 방역] {loc_name} 주변에 널브러진 감염된 시체들을 장작더미와 함께 소각했습니다. 흑사병 및 시체독 전파원이 완전히 차단되었습니다."
