"""
Siege Warfare, Structural Durability & Large-Scale Formation Tactics Engine for Quilltale TRPG.
Deterministic simulation of fortress assaults, siege engine mechanics, multi-layer structural durability
(walls, gates, moats, battlements, watchtowers, magical barriers), 3-corps formation advantage matrix,
morale rout cascades, and external AI narrative generation.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import math
import random
import logging

from src.world.state import WorldState
from src.world.infrastructure import Settlement, Nation
from src.world.dice import DiceEngine

logger = logging.getLogger(__name__)

# ============================================================
# Master Raw System Data (External AI Extraction Specifications)
# ============================================================
SIEGE_WEAPON_CATALOG: Dict[str, Dict[str, Any]] = {
    "battering_ram": {
        "name_ko": "중장갑 충차 (공성추)",
        "category": "gate_breaker",
        "description": "두꺼운 참나무와 무쇠 머리로 제작된 대형 충차. 성문 파괴에 절대적인 위력을 발휘하나 해자가 메워지기 전에는 접근할 수 없다.",
        "traits": ["siege_weapon", "ram", "heavy_wood", "iron_head", "gate_breaker"],
        "base_durability": 450.0,
        "hardness": 12.0,
        "min_crew": 15,
        "optimal_crew": 30,
        "base_siege_damage": 180.0,
        "wall_damage_multiplier": 0.15,
        "gate_damage_multiplier": 1.5,
        "fire_vulnerability_multiplier": 1.6,
        "requires_moat_cleared": True,
    },
    "trebuchet": {
        "name_ko": "중형 평형추 트레뷰셋",
        "category": "wall_crusher",
        "description": "거대한 평형추의 낙하 에너지를 이용해 백 수십 킬로그램의 바위를 초장거리로 투척하는 성벽 파쇄 병기.",
        "traits": ["siege_weapon", "trebuchet", "artillery", "wall_crusher", "long_range"],
        "base_durability": 320.0,
        "hardness": 6.0,
        "min_crew": 20,
        "optimal_crew": 40,
        "base_siege_damage": 220.0,
        "wall_damage_multiplier": 1.2,
        "gate_damage_multiplier": 0.8,
        "splash_casualty_base": 25,
        "fire_vulnerability_multiplier": 1.8,
        "requires_moat_cleared": False,
    },
    "catapult": {
        "name_ko": "비틀림식 망고넬 투석기",
        "category": "field_artillery",
        "description": "동물 힘줄의 비틀림 탄성을 이용해 기름 항아리나 자갈탄을 투척하는 공성 병기. 인마 살상 및 화재 유발에 능하다.",
        "traits": ["siege_weapon", "catapult", "artillery", "anti_infantry", "fire_starter"],
        "base_durability": 260.0,
        "hardness": 5.0,
        "min_crew": 10,
        "optimal_crew": 20,
        "base_siege_damage": 140.0,
        "wall_damage_multiplier": 0.7,
        "gate_damage_multiplier": 0.7,
        "splash_casualty_base": 35,
        "fire_vulnerability_multiplier": 1.8,
        "requires_moat_cleared": False,
    },
    "siege_tower": {
        "name_ko": "철갑 공성탑 (벨프라이)",
        "category": "wall_scaler",
        "description": "생가죽과 철판으로 덮인 다층 이동식 탑. 보병을 성벽 상단으로 안전하게 직송 진입시키나 화공과 진흙탕에 매우 취약하다.",
        "traits": ["siege_weapon", "tower", "infantry_transport", "wall_scaler"],
        "base_durability": 550.0,
        "hardness": 10.0,
        "min_crew": 25,
        "optimal_crew": 50,
        "base_siege_damage": 0.0,
        "wall_damage_multiplier": 0.0,
        "gate_damage_multiplier": 0.0,
        "troop_capacity": 80,
        "fire_vulnerability_multiplier": 1.7,
        "requires_moat_cleared": True,
    },
    "heavy_ballista": {
        "name_ko": "거치식 대형 노포 (발리스타)",
        "category": "sniper_artillery",
        "description": "강철 화살촉이 달린 대형 볼트를 정밀 발사하는 중화기. 적의 공성 병기 파괴 및 성벽 흉벽 뒤의 지휘관을 저격한다.",
        "traits": ["siege_weapon", "ballista", "precision", "anti_engine", "anti_commander"],
        "base_durability": 200.0,
        "hardness": 5.0,
        "min_crew": 6,
        "optimal_crew": 12,
        "base_siege_damage": 90.0,
        "wall_damage_multiplier": 0.25,
        "gate_damage_multiplier": 0.4,
        "anti_engine_multiplier": 2.2,
        "fire_vulnerability_multiplier": 1.5,
        "requires_moat_cleared": False,
    },
    "sappers_tunnel": {
        "name_ko": "공병 지하 굴착 갱도",
        "category": "subterranean_undermine" ,
        "description": "성벽 하부의 지반을 파고들어가 지지 목책에 불을 질러 성벽 전체를 무너뜨리는 은밀한 지하 공성 공학 작전.",
        "traits": ["siege_weapon", "sappers", "mining", "foundation_collapse", "covert"],
        "base_durability": 300.0,
        "hardness": 20.0,
        "min_crew": 15,
        "optimal_crew": 30,
        "base_siege_damage": 350.0,
        "wall_damage_multiplier": 2.2,
        "gate_damage_multiplier": 0.0,
        "fire_vulnerability_multiplier": 1.0,
        "requires_moat_cleared": False,
    }
}

# 3군 진형 정의 및 상성 데이터
FORMATION_TACTICS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "shield_wall": {
        "name_ko": "방패벽 장창 방진 (테스투도)",
        "description": "대형 방패를 겹치고 장창을 앞으로 내세워 전면 방어선을 형성하는 밀집 보병 진형.",
        "traits": ["formation", "shield_wall", "defensive", "anti_cavalry"],
        "ranged_damage_reduction": 0.70,
        "cavalry_counter_multiplier": 2.0,
        "movement_penalty": 0.60,
        "artillery_vulnerability_multiplier": 1.4,
    },
    "wedge_charge": {
        "name_ko": "쐐기형 돌격진 (웨지 차지)",
        "description": "중장기병이나 충격 보병이 삼각형 대형으로 적의 전열 중앙부를 뚫고 들어가는 파괴적 돌격 진형.",
        "traits": ["formation", "wedge_charge", "shock", "armor_pierce"],
        "breakthrough_bonus": 1.8,
        "open_field_infantry_bonus": 1.8,
        "anti_ranged_bonus": 2.0,
        "recoil_penalty_vs_shield_wall": 2.0,
    },
    "volley_rain": {
        "name_ko": "일제 사격선 (볼리 파이어)",
        "description": "궁병과 석궁병이 2열 또는 3열로 교대하며 쉼 없이 화살비를 쏟아붓는 원거리 화망 진형.",
        "traits": ["formation", "volley_rain", "ranged_barrage", "suppression"],
        "ranged_lethality_multiplier": 1.6,
        "elevation_bonus_multiplier": 1.5,
        "melee_defense_penalty": 0.50,
        "cavalry_vulnerability_multiplier": 2.2,
    },
    "feigned_retreat": {
        "name_ko": "위장 후퇴 및 유인 진형",
        "description": "일부러 패배한 척 퇴각하여 적의 진형을 흩뜨리고 성벽 밖으로 유인하여 측면을 포위하는 기동 전술.",
        "traits": ["formation", "feigned_retreat", "cunning", "ambush"],
        "flanking_advantage_multiplier": 1.9,
        "morale_damage_to_enemy": 20,
        "intelligence_dc": 14,
    },
    "loose_skirmish": {
        "name_ko": "산개 교란 진형 (스커미시)",
        "description": "병사들이 넓게 흩어져 적의 투석 및 광역 마법 폭격 피해를 최소화하고 보급로를 교란하는 진형.",
        "traits": ["formation", "skirmish", "evasive", "anti_artillery"],
        "artillery_damage_reduction": 0.55,
        "melee_holding_penalty": 0.40,
        "harass_bonus": 1.3,
    }
}


# ============================================================
# Dataclasses with traits (Rule 6 Compliance)
# ============================================================
@dataclass
class SiegeEngineInstance:
    """개별 공성 병기 인스턴스 모델 (내구도 및 조작원 완비)"""
    engine_id: str
    engine_type: str
    name_ko: str
    durability: float
    max_durability: float
    hardness: float
    assigned_crew: int
    min_crew: int
    optimal_crew: int
    is_operational: bool = True
    is_destroyed: bool = False
    subterranean_progress_pct: float = 0.0
    traits: List[str] = field(default_factory=list)

    def take_damage(self, raw_damage: float, is_fire: bool = False) -> Tuple[float, bool]:
        """물리/화공 피해를 입고 내구도를 깎는다. 0 이하 시 파괴된다."""
        spec = SIEGE_WEAPON_CATALOG.get(self.engine_type, {})
        effective_damage = max(1.0, raw_damage - self.hardness)
        if is_fire:
            vuln = spec.get("fire_vulnerability_multiplier", 1.0)
            effective_damage *= vuln

        actual_lost = min(self.durability, effective_damage)
        self.durability = max(0.0, self.durability - actual_lost)

        if self.durability <= 0.0:
            self.is_destroyed = True
            self.is_operational = False
            return actual_lost, True

        # 크루 부족 또는 파손 심화 시 조작 불가
        if self.assigned_crew < self.min_crew or self.durability <= (self.max_durability * 0.15):
            self.is_operational = False

        return actual_lost, False

    def repair(self, amount: float) -> float:
        """내구도를 수리한다."""
        if self.is_destroyed:
            return 0.0
        old = self.durability
        self.durability = min(self.max_durability, self.durability + amount)
        if self.assigned_crew >= self.min_crew and self.durability > (self.max_durability * 0.15):
            self.is_operational = True
        return self.durability - old


@dataclass
class FortressDefenseState:
    """방어 요새/성채의 다층 구조물 물리 내구도 및 방호 스탯 모델"""
    settlement_id: str
    settlement_name: str
    wall_tier: int                                         # 0: 목책, 1: 석벽, 2: 겹성벽, 3: 마도 요새
    wall_durability: float
    max_wall_durability: float
    wall_hardness: float
    wall_breached: bool = False

    gate_type: str = "wooden_bar"                          # "none", "wooden_bar", "iron_reinforced", "portcullis", "drawbridge_chains"
    gate_durability: float = 350.0
    max_gate_durability: float = 350.0
    gate_hardness: float = 4.0
    gate_breached: bool = False

    moat_type: str = "none"                                # "none", "dry_ditch", "water_moat", "spiked_trench"
    moat_durability: float = 0.0                           # 100.0: 완전 방어, 0.0: 완전 매립/도하 가능
    max_moat_durability: float = 0.0
    moat_cleared: bool = True

    battlement_type: str = "none"                          # "none", "wooden_hurdles", "stone_crenels", "machicolations"
    battlement_durability: float = 0.0
    max_battlement_durability: float = 0.0
    battlement_cover_rating: float = 0.0

    tower_count: int = 2
    tower_durability: float = 600.0
    max_tower_durability: float = 600.0

    barrier_active: bool = False
    barrier_durability: float = 0.0
    max_barrier_durability: float = 0.0

    elevation_meters: int = 50
    supplies_remaining_days: int = 90
    traits: List[str] = field(default_factory=list)

    def damage_barrier(self, damage: float) -> Tuple[float, float]:
        """마도 결계에 피해를 준다. 남은 피해량(관통분)을 반환한다."""
        if not self.barrier_active or self.barrier_durability <= 0.0:
            return 0.0, damage
        
        absorbed = min(self.barrier_durability, damage)
        self.barrier_durability -= absorbed
        remaining = damage - absorbed
        if self.barrier_durability <= 0.0:
            self.barrier_active = False
        return absorbed, remaining

    def damage_wall(self, raw_damage: float) -> Tuple[float, bool]:
        """성벽에 물리 피해를 가한다. 0 도달 시 외벽 돌파구가 뚫린다."""
        if self.wall_breached:
            return 0.0, True

        eff_dmg = max(1.0, raw_damage - self.wall_hardness)
        actual_loss = min(self.wall_durability, eff_dmg)
        self.wall_durability = max(0.0, self.wall_durability - actual_loss)

        if self.wall_durability <= 0.0:
            self.wall_breached = True
            return actual_loss, True
        return actual_loss, False

    def damage_gate(self, raw_damage: float) -> Tuple[float, bool]:
        """성문에 물리 피해를 가한다. 0 도달 시 성문이 박살 난다."""
        if self.gate_breached or self.max_gate_durability <= 0.0:
            self.gate_breached = True
            return 0.0, True

        eff_dmg = max(1.0, raw_damage - self.gate_hardness)
        actual_loss = min(self.gate_durability, eff_dmg)
        self.gate_durability = max(0.0, self.gate_durability - actual_loss)

        if self.gate_durability <= 0.0:
            self.gate_breached = True
            return actual_loss, True
        return actual_loss, False

    def fill_moat(self, work_volume: float) -> Tuple[float, bool]:
        """공격군이 흙/자루를 넣어 해자를 메운다 (해자 내구도 삭감)."""
        if self.moat_cleared or self.moat_durability <= 0.0:
            self.moat_cleared = True
            return 0.0, True

        actual_reduction = min(self.moat_durability, work_volume)
        self.moat_durability = max(0.0, self.moat_durability - actual_reduction)
        if self.moat_durability <= 0.0:
            self.moat_cleared = True
            return actual_reduction, True
        return actual_reduction, False

    def damage_battlement(self, raw_damage: float) -> float:
        """흉벽을 포격하여 수비 궁병의 엄폐율을 깎는다."""
        if self.battlement_durability <= 0.0:
            return 0.0
        eff = max(1.0, raw_damage - 5.0)
        lost = min(self.battlement_durability, eff)
        self.battlement_durability = max(0.0, self.battlement_durability - lost)
        if self.battlement_durability <= 0.0:
            self.battlement_cover_rating = 0.0
        else:
            self.battlement_cover_rating = (self.battlement_durability / self.max_battlement_durability) * 0.5
        return lost


@dataclass
class TroopCorps:
    """군단 편성 단위 (보병/기병/궁병/특수부대)"""
    corps_id: str
    corps_name: str
    troop_type: str                                       # "infantry", "cavalry", "ranged", "elite_special"
    current_count: int
    initial_count: int
    current_formation: str = "shield_wall"
    veteran_tier: int = 1                                 # 1: 징집병, 2: 정규병, 3: 정예병, 4: 베테랑
    equipment_tier: int = 1                               # 1: 경무장, 2: 쇠사슬갑, 3: 판금 중장갑
    is_routed: bool = False
    traits: List[str] = field(default_factory=list)

    @property
    def casualty_count(self) -> int:
        return max(0, self.initial_count - self.current_count)

    @property
    def casualty_rate(self) -> float:
        if self.initial_count <= 0:
            return 0.0
        return float(self.casualty_count) / float(self.initial_count)

    def apply_casualties(self, amount: int) -> int:
        actual = min(self.current_count, amount)
        self.current_count = max(0, self.current_count - actual)
        if self.current_count <= 0:
            self.is_routed = True
        return actual


@dataclass
class ArmyMoraleState:
    """군대 사기 및 지휘 통제 모델"""
    side_name: str                                        # "attacker" | "defender"
    morale: int = 85                                      # 0 ~ 100
    commander_name: str = "총지휘관"
    commander_alive: bool = True
    commander_wounded: bool = False
    desertion_total: int = 0
    traits: List[str] = field(default_factory=list)

    @property
    def morale_tier(self) -> str:
        if self.morale >= 80:
            return "high_spirits"                         # 사기 충천
        elif self.morale >= 50:
            return "steady"                               # 전열 유지
        elif self.morale >= 25:
            return "wavering"                             # 동요 및 불안
        else:
            return "broken_rout"                          # 전면 붕괴 및 패주

    def adjust_morale(self, delta: int) -> int:
        old = self.morale
        self.morale = max(0, min(100, self.morale + delta))
        return self.morale - old


@dataclass
class SiegeBattleState:
    """공성전 마스터 인스턴스 상태"""
    siege_id: str
    settlement_id: str
    day_count: int = 1
    current_phase: int = 1                                # 1: 포격, 2: 해자/접근, 3: 전열격돌, 4: 결산
    fortress: FortressDefenseState = field(default_factory=lambda: FortressDefenseState(settlement_id="", settlement_name="", wall_tier=1, wall_durability=1000, max_wall_durability=1000, wall_hardness=10))
    attacker_engines: List[SiegeEngineInstance] = field(default_factory=list)
    defender_engines: List[SiegeEngineInstance] = field(default_factory=list)
    attacker_corps: List[TroopCorps] = field(default_factory=list)
    defender_corps: List[TroopCorps] = field(default_factory=list)
    attacker_morale: ArmyMoraleState = field(default_factory=lambda: ArmyMoraleState(side_name="attacker"))
    defender_morale: ArmyMoraleState = field(default_factory=lambda: ArmyMoraleState(side_name="defender"))
    battle_concluded: bool = False
    winner_side: Optional[str] = None                     # "attacker" | "defender" | "stalemate"
    logs: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)


# ============================================================
# Master Engine Implementation
# ============================================================
class SiegeWarfareEngine:
    """
    Quilltale 결정론적 공성전 & 전열 전술 시뮬레이터.
    Settlement 및 Nation 인프라 데이터와 100% 결합하여 물리적 내구도와 3군 상성을 계산한다.
    """

    @classmethod
    def initialize_fortress_defense(cls, settlement: Settlement) -> FortressDefenseState:
        """
        정주지(Settlement)의 인프라 스탯을 읽어 방어 구조물 내구도를 결정론적으로 초기화한다.
        """
        tier = settlement.wall_defense_tier
        # 성벽 등급별 기본 내구도
        wall_spec_map = {
            0: (400.0, 2.0, ["palisade", "wooden", "flammable"]),
            1: (1500.0, 15.0, ["stone_wall", "solid", "durable"]),
            2: (3500.0, 25.0, ["double_walls", "curtain_wall", "citadel"]),
            3: (7500.0, 40.0, ["magical_fortress", "runic_stone", "impregnable"])
        }
        max_w, hard_w, wall_traits = wall_spec_map.get(tier, wall_spec_map[1])

        # 성문 등급별 내구도
        gate_map = {
            "none": (0.0, 0.0),
            "wooden_bar": (350.0, 4.0),
            "iron_reinforced": (900.0, 12.0),
            "portcullis": (1800.0, 20.0),
            "drawbridge_chains": (2500.0, 22.0)
        }
        gate_type = getattr(settlement, "gate_type", "wooden_bar")
        max_g, hard_g = gate_map.get(gate_type, (350.0, 4.0))

        # 해자 등급별 내구도
        moat_map = {
            "none": 0.0,
            "dry_ditch": 100.0,
            "water_moat": 160.0,
            "spiked_trench": 120.0
        }
        moat_type = getattr(settlement, "moat_type", "none")
        max_m = moat_map.get(moat_type, 0.0)

        # 흉벽 등급별 내구도
        battlement_map = {
            "none": (0.0, 0.0),
            "wooden_hurdles": (200.0, 0.25),
            "stone_crenels": (500.0, 0.50),
            "machicolations": (800.0, 0.70)
        }
        battlement_type = getattr(settlement, "battlement_type", "none")
        max_b, cover_b = battlement_map.get(battlement_type, (0.0, 0.0))

        # 마도 결계
        barrier_active = getattr(settlement, "magical_barrier_active", False)
        barrier_dur = 2500.0 if barrier_active else 0.0

        # 고도
        elev = getattr(settlement, "elevation_meters", 100)
        supplies = getattr(settlement, "siege_supplies_days", 90)

        traits = [
            f"wall_tier_{tier}",
            f"gate_{gate_type}",
            f"moat_{moat_type}",
            f"battlement_{battlement_type}",
            "fortress_defense"
        ]
        traits.extend(wall_traits)

        return FortressDefenseState(
            settlement_id=settlement.id,
            settlement_name=settlement.name,
            wall_tier=tier,
            wall_durability=max_w,
            max_wall_durability=max_w,
            wall_hardness=hard_w,
            wall_breached=False,
            gate_type=gate_type,
            gate_durability=max_g,
            max_gate_durability=max_g,
            gate_hardness=hard_g,
            gate_breached=(max_g <= 0.0),
            moat_type=moat_type,
            moat_durability=max_m,
            max_moat_durability=max_m,
            moat_cleared=(max_m <= 0.0),
            battlement_type=battlement_type,
            battlement_durability=max_b,
            max_battlement_durability=max_b,
            battlement_cover_rating=cover_b,
            tower_count=2 + tier,
            tower_durability=400.0 + tier * 200.0,
            max_tower_durability=400.0 + tier * 200.0,
            barrier_active=barrier_active,
            barrier_durability=barrier_dur,
            max_barrier_durability=barrier_dur,
            elevation_meters=elev,
            supplies_remaining_days=supplies,
            traits=traits
        )

    @classmethod
    def create_siege_engine(cls, engine_type: str, engine_id: Optional[str] = None, assigned_crew: Optional[int] = None) -> SiegeEngineInstance:
        """지정된 타입의 공성 병기 인스턴스를 생성한다."""
        spec = SIEGE_WEAPON_CATALOG.get(engine_type)
        if not spec:
            spec = SIEGE_WEAPON_CATALOG["catapult"]
            engine_type = "catapult"

        eid = engine_id or f"{engine_type}_{random.randint(1000, 9999)}"
        crew = assigned_crew if assigned_crew is not None else spec["optimal_crew"]

        return SiegeEngineInstance(
            engine_id=eid,
            engine_type=engine_type,
            name_ko=spec["name_ko"],
            durability=spec["base_durability"],
            max_durability=spec["base_durability"],
            hardness=spec["hardness"],
            assigned_crew=crew,
            min_crew=spec["min_crew"],
            optimal_crew=spec["optimal_crew"],
            is_operational=(crew >= spec["min_crew"]),
            is_destroyed=False,
            subterranean_progress_pct=0.0,
            traits=list(spec["traits"])
        )

    @classmethod
    def initialize_siege(
        cls,
        siege_id: str,
        settlement: Settlement,
        attacker_nation: Optional[Nation] = None,
        attacker_corps: Optional[List[TroopCorps]] = None,
        attacker_engines: Optional[List[SiegeEngineInstance]] = None,
        defender_corps: Optional[List[TroopCorps]] = None,
        defender_engines: Optional[List[SiegeEngineInstance]] = None,
    ) -> SiegeBattleState:
        """
        공성전 전체 마스터 인스턴스를 조립하고 초기화한다.
        """
        fortress = cls.initialize_fortress_defense(settlement)

        # 기본 공격군 병력 생성 (지정되지 않은 경우)
        if not attacker_corps:
            attacker_corps = [
                TroopCorps(corps_id="atk_infantry", corps_name="공격군 정규 보병단", troop_type="infantry", current_count=1200, initial_count=1200, current_formation="shield_wall", traits=["regular", "infantry"]),
                TroopCorps(corps_id="atk_cavalry", corps_name="공격군 기병 기동대", troop_type="cavalry", current_count=400, initial_count=400, current_formation="wedge_charge", traits=["shock", "cavalry"]),
                TroopCorps(corps_id="atk_ranged", corps_name="공격군 노도 궁병대", troop_type="ranged", current_count=500, initial_count=500, current_formation="volley_rain", traits=["ranged", "archers"]),
            ]

        # 기본 공격군 공성 무기 생성
        if attacker_engines is None:
            attacker_engines = [
                cls.create_siege_engine("trebuchet", "atk_trebuchet_1"),
                cls.create_siege_engine("trebuchet", "atk_trebuchet_2"),
                cls.create_siege_engine("battering_ram", "atk_ram_1"),
                cls.create_siege_engine("siege_tower", "atk_tower_1"),
            ]

        # 기본 수비군 병력 생성
        if not defender_corps:
            patrol = getattr(settlement, "patrol_strength", 50)
            def_inf_count = 500 + patrol * 8
            def_ranged_count = 300 + patrol * 5
            defender_corps = [
                TroopCorps(corps_id="def_garrison", corps_name="성채 수비 보병대", troop_type="infantry", current_count=def_inf_count, initial_count=def_inf_count, current_formation="shield_wall", traits=["garrison", "infantry"]),
                TroopCorps(corps_id="def_archers", corps_name="성벽 총안 궁병대", troop_type="ranged", current_count=def_ranged_count, initial_count=def_ranged_count, current_formation="volley_rain", traits=["marksmen", "wall_guards"]),
            ]

        # 기본 수비군 노포 생성
        if defender_engines is None:
            defender_engines = [
                cls.create_siege_engine("heavy_ballista", "def_ballista_1"),
                cls.create_siege_engine("heavy_ballista", "def_ballista_2"),
            ]

        atk_morale = ArmyMoraleState(side_name="attacker", morale=90, commander_name="공격군 총사령관", traits=["attacker_hq"])
        def_morale = ArmyMoraleState(side_name="defender", morale=85, commander_name=getattr(settlement, "lord_npc_id", "성주 영주"), traits=["defender_hq"])

        return SiegeBattleState(
            siege_id=siege_id,
            settlement_id=settlement.id,
            day_count=1,
            current_phase=1,
            fortress=fortress,
            attacker_engines=attacker_engines,
            defender_engines=defender_engines,
            attacker_corps=attacker_corps,
            defender_corps=defender_corps,
            attacker_morale=atk_morale,
            defender_morale=def_morale,
            traits=["active_siege", f"settlement_{settlement.id}"]
        )

    # ------------------------------------------------------------
    # Phase 1: Artillery & Long-Range Bombardment
    # ------------------------------------------------------------
    @classmethod
    def execute_artillery_phase(cls, state: SiegeBattleState) -> List[str]:
        """
        1페이즈: 투석기, 발리스타, 대포병 사격 교환.
        성벽, 성문, 흉벽, 마도 결계 내구도 삭감 및 요격.
        """
        logs = []
        fort = state.fortress

        # A. 수비군 노포(Ballista)의 적 공성 병기 정밀 요격
        for d_eng in state.defender_engines:
            if not d_eng.is_operational or d_eng.is_destroyed:
                continue

            # 살아있는 적 공성 병기 중 무작위 타겟 선정
            valid_targets = [e for e in state.attacker_engines if e.is_operational and not e.is_destroyed]
            if valid_targets:
                target = random.choice(valid_targets)
                ballista_dmg = 85.0 * (d_eng.assigned_crew / d_eng.optimal_crew)
                spec = SIEGE_WEAPON_CATALOG.get(d_eng.engine_type, {})
                anti_mult = spec.get("anti_engine_multiplier", 1.8)
                total_dmg = ballista_dmg * anti_mult
                lost, destroyed = target.take_damage(total_dmg, is_fire=False)
                logs.append(f"🏹 [수비군 노포 요격] [{d_eng.name_ko}]이 적 [{target.name_ko}]에 직격! 내구도 {lost:.1f} 손상 (잔여: {target.durability:.1f}/{target.max_durability:.1f})")
                if destroyed:
                    logs.append(f"💥 [공성 병기 파괴] 적의 [{target.name_ko}]이 완파되어 잔해로 무너져 내렸습니다!")
                    state.attacker_morale.adjust_morale(-6)

        # B. 공격군 투석기 및 포병 사격
        for a_eng in state.attacker_engines:
            if not a_eng.is_operational or a_eng.is_destroyed:
                continue

            spec = SIEGE_WEAPON_CATALOG.get(a_eng.engine_type, {})
            crew_ratio = max(0.5, a_eng.assigned_crew / a_eng.optimal_crew)
            base_dmg = spec.get("base_siege_damage", 100.0) * crew_ratio

            # 충차나 공성탑은 초장거리 포격 페이즈에서는 사격 불가
            if a_eng.engine_type in ["battering_ram", "siege_tower"]:
                continue

            # 공병 갱도 진척도 진행
            if a_eng.engine_type == "sappers_tunnel":
                a_eng.subterranean_progress_pct = min(100.0, a_eng.subterranean_progress_pct + 25.0)
                logs.append(f"⛏️ [공병 갱도 굴착] 성벽 하부 굴착 진척도 {a_eng.subterranean_progress_pct:.0f}% 달성!")
                if a_eng.subterranean_progress_pct >= 100.0 and not fort.wall_breached:
                    w_loss, breached = fort.damage_wall(base_dmg * 2.5)
                    logs.append(f"💣 [성벽 기초 대붕괴] 지하 갱도 지지목 소각으로 성벽 기저가 붕괴되었습니다! (내구도 -{w_loss:.1f})")
                    if breached:
                        logs.append(f"🚨🚨 [성벽 외벽 전면 돌파!] 거대한 석벽이 굉음과 함께 무너지며 전열 진입로가 열렸습니다!")
                        state.defender_morale.adjust_morale(-25)
                continue

            # 마도 결계가 살아있으면 결계가 우선 흡수
            if fort.barrier_active and fort.barrier_durability > 0.0:
                abs_dmg, remain_dmg = fort.damage_barrier(base_dmg)
                logs.append(f"🔮 [마도 결계 흡수] 도시 방호 결계가 투석 피해 {abs_dmg:.1f}를 차단했습니다! (결계 잔여: {fort.barrier_durability:.1f}/{fort.max_barrier_durability:.1f})")
                if not fort.barrier_active:
                    logs.append("⚡ [마도 결계 파괴!] 도시 방호 룬 결계가 과부하로 깨져 산산조각 났습니다!")
                    state.defender_morale.adjust_morale(-10)
                base_dmg = remain_dmg
                if base_dmg <= 0.0:
                    continue

            # 성벽 파쇄 공격
            if not fort.wall_breached:
                w_mult = spec.get("wall_damage_multiplier", 1.0)
                w_loss, breached = fort.damage_wall(base_dmg * w_mult)
                logs.append(f"☄️ [투석 폭격] [{a_eng.name_ko}]의 암석탄이 성벽을 강타! 내구도 {w_loss:.1f} 삭감 (잔여: {fort.wall_durability:.1f}/{fort.max_wall_durability:.1f})")
                if breached:
                    logs.append("🚨🚨 [성벽 완파 돌파구 형성!] 성벽에 거대한 균열이 터지며 통로가 열렸습니다!")
                    state.defender_morale.adjust_morale(-25)

            # 흉벽 및 수비 궁병 파편 피해
            b_loss = fort.damage_battlement(base_dmg * 0.3)
            if b_loss > 0:
                logs.append(f"🧱 [흉벽 파괴] 총안 흉벽이 부서져 수비측 엄폐율이 저하되었습니다 (-{b_loss:.1f})")

            # 수비군 병력 파편 사상자 발생
            splash_base = spec.get("splash_casualty_base", 15)
            casualty = int(splash_base * crew_ratio * random.uniform(0.8, 1.3))
            def_inf = next((c for c in state.defender_corps if c.troop_type == "infantry"), None)
            if def_inf and def_inf.current_count > 0:
                lost_soldiers = def_inf.apply_casualties(casualty)
                logs.append(f"🩸 [성내 파편 사상] 성벽 투석 파편으로 수비 보병 {lost_soldiers}명이 사상했습니다.")

        return logs

    # ------------------------------------------------------------
    # Phase 2: Moat Filling & Siege Equipment Advance
    # ------------------------------------------------------------
    @classmethod
    def execute_advance_phase(cls, state: SiegeBattleState) -> List[str]:
        """
        2페이즈: 해자 메우기, 충차 접안, 공성탑 사다리 가설.
        해자 내구도가 0이 되어야 충차/공성탑이 성문과 성벽에 직접 타격을 가할 수 있다.
        """
        logs = []
        fort = state.fortress

        # A. 해자가 아직 메워지지 않은 경우 공격군 매립 작업 진행
        if not fort.moat_cleared and fort.moat_durability > 0.0:
            fill_volume = 35.0  # 기본 매립 공병 작업량
            atk_inf = next((c for c in state.attacker_corps if c.troop_type == "infantry"), None)
            if atk_inf:
                # 보병 인원수에 비례하여 매립 속도 증가
                work_scale = max(0.5, min(2.0, atk_inf.current_count / 1000.0))
                fill_volume *= work_scale

            # 수비 궁병의 방해 사격 (고도 및 흉벽 보너스 적용)
            def_arc = next((c for c in state.defender_corps if c.troop_type == "ranged"), None)
            if def_arc and def_arc.current_count > 0:
                elevation_bonus = 1.0 + (fort.elevation_meters / 100.0) * 0.4
                arrow_lethality = int(def_arc.current_count * 0.08 * elevation_bonus)
                if atk_inf:
                    # 방패벽이면 피해 70% 차단
                    if atk_inf.current_formation == "shield_wall":
                        arrow_lethality = int(arrow_lethality * 0.30)
                    lost = atk_inf.apply_casualties(arrow_lethality)
                    logs.append(f"🏹 [수비군 요격 화살비] 성벽 위에서 쏟아지는 화살로 해자 매립 인부/보병 {lost}명이 전사했습니다.")

            reduced, cleared = fort.fill_moat(fill_volume)
            logs.append(f"🚜 [해자 매립 작업] 흙포대와 통나무를 투입하여 해자 방호도를 {reduced:.1f} 삭감했습니다 (잔여: {fort.moat_durability:.1f}/{fort.max_moat_durability:.1f})")
            if cleared:
                logs.append("🚩 [해자 평토화 완료!] 해자가 완전히 메워져 공성추와 공성탑의 성벽/성문 직결 진입로가 확보되었습니다!")
        else:
            fort.moat_cleared = True

        # B. 해자가 메워진 후 충차(Battering Ram)의 성문 타격
        if fort.moat_cleared:
            for ram in [e for e in state.attacker_engines if e.engine_type == "battering_ram" and e.is_operational]:
                if fort.gate_breached:
                    continue

                crew_mult = ram.assigned_crew / ram.optimal_crew
                ram_dmg = 180.0 * crew_mult * 1.5
                g_lost, g_breached = fort.damage_gate(ram_dmg)
                logs.append(f"💥 [충차 성문 직격] [{ram.name_ko}]의 무쇠 머리가 성문을 강타! 내구도 {g_lost:.1f} 파손 (잔여: {fort.gate_durability:.1f}/{fort.max_gate_durability:.1f})")
                if g_breached:
                    logs.append("🚪🚨 [성문 대파 함락!] 빗장과 경첩이 박살 나며 거대한 성문이 안쪽으로 무너져 내렸습니다!")
                    state.defender_morale.adjust_morale(-25)

                # 수비군 끓는 기름 / 낙하 바위 반격
                oil_dmg = 40.0
                if fort.battlement_type == "machicolations":
                    oil_dmg = 80.0  # 살인창(머시콜리스) 보너스
                ram_lost, ram_broken = ram.take_damage(oil_dmg, is_fire=True)
                logs.append(f"🔥 [기름 투하 반격] 성벽 위에서 쏟아진 끓는 기름으로 [{ram.name_ko}]이 내구도 {ram_lost:.1f} 피해를 입었습니다.")

        return logs

    # ------------------------------------------------------------
    # Phase 3: Formation Clash & Breach Assault
    # ------------------------------------------------------------
    @classmethod
    def resolve_formation_clash(
        cls,
        atk_corps: TroopCorps,
        def_corps: TroopCorps,
        fort: FortressDefenseState,
        in_breach: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        3군 진형 상성 매트릭스에 따른 보병/기병/궁병 전열 백병전 사상자 산출.
        """
        logs = []
        atk_form = FORMATION_TACTICS_REGISTRY.get(atk_corps.current_formation, FORMATION_TACTICS_REGISTRY["shield_wall"])
        def_form = FORMATION_TACTICS_REGISTRY.get(def_corps.current_formation, FORMATION_TACTICS_REGISTRY["shield_wall"])

        # 기본 화력 계수 (병력 수 및 숙련도 반영)
        atk_power = atk_corps.current_count * (0.8 + atk_corps.veteran_tier * 0.2)
        def_power = def_corps.current_count * (0.8 + def_corps.veteran_tier * 0.2)

        # A. 상성 및 진형 효과: 기병 돌격 vs 방패벽 장창
        if atk_corps.troop_type == "cavalry" and atk_corps.current_formation == "wedge_charge":
            if def_corps.troop_type == "infantry" and def_corps.current_formation == "shield_wall":
                # 기병 자멸 및 튕겨나감
                counter = def_form.get("cavalry_counter_multiplier", 2.0)
                atk_losses = int(def_power * 0.12 * counter)
                def_losses = int(atk_power * 0.04)
                logs.append(f"🛡️ [장창 방패벽 저지] 적 기병의 쐐기 돌격이 장창벽에 들이받아 말들이 꿰뚫렸습니다! (공격 기병 사상: {atk_losses}, 수비 보병: {def_losses})")
            else:
                # 기병 돌격 성공 (보병/궁병 학살)
                breakthrough = atk_form.get("breakthrough_bonus", 1.8)
                def_losses = int(atk_power * 0.14 * breakthrough)
                atk_losses = int(def_power * 0.05)
                logs.append(f"⚔️ [기병 전열 돌파] 쐐기 돌격진이 적의 방어선을 찢어발겼습니다! (수비군 사상: {def_losses}, 공격 기병: {atk_losses})")

        elif atk_corps.troop_type == "ranged" and atk_corps.current_formation == "volley_rain":
            # 화살비 사격 vs 방패벽
            if def_corps.current_formation == "shield_wall":
                reduct = def_form.get("ranged_damage_reduction", 0.70)
                def_losses = int(atk_power * 0.10 * (1.0 - reduct))
                atk_losses = 0
                logs.append(f"🛡️ [방패벽 화살 차단] 수비군이 방패를 머리 위로 올려 화살비의 70%를 튕겨냈습니다. (수비 사상: {def_losses})")
            else:
                def_losses = int(atk_power * 0.12)
                atk_losses = 0
                logs.append(f"🏹 [일제 사격 타격] 노출된 적 전열에 화살비가 쏟아졌습니다. (수비 사상: {def_losses})")

        else:
            # 일반 보병 백병전 충돌
            def_advantage = 1.3 if not in_breach else 1.0  # 성벽 지형 이점
            def_losses = int(atk_power * 0.07 / def_advantage)
            atk_losses = int(def_power * 0.07 * def_advantage)
            logs.append(f"⚔️ [전열 백병전 격돌] 칼과 창이 부딪히며 치열한 난투가 벌어졌습니다. (공격군 사상: {atk_losses}, 수비군 사상: {def_losses})")

        actual_atk_loss = atk_corps.apply_casualties(atk_losses)
        actual_def_loss = def_corps.apply_casualties(def_losses)

        return actual_atk_loss, actual_def_loss, logs

    @classmethod
    def execute_breach_assault_phase(cls, state: SiegeBattleState) -> List[str]:
        """
        3페이즈: 성벽 돌파구 또는 성문 파괴 시 백병전 돌입.
        아직 뚫리지 않은 경우 사다리/공성탑에 의한 국소 성벽 쟁탈전 진행.
        """
        logs = []
        fort = state.fortress
        can_mass_assault = fort.wall_breached or fort.gate_breached

        atk_inf = next((c for c in state.attacker_corps if c.troop_type == "infantry" and c.current_count > 0), None)
        def_inf = next((c for c in state.defender_corps if c.troop_type == "infantry" and c.current_count > 0), None)

        if not atk_inf or not def_inf:
            return logs

        if can_mass_assault:
            logs.append("⚔️🚨 [돌파구 총돌격 개시] 무너진 성벽 틈과 박살 난 성문으로 공격군 주력이 물밀듯이 쏟아져 들어갑니다!")
            _, _, clash_logs = cls.resolve_formation_clash(atk_inf, def_inf, fort, in_breach=True)
            logs.extend(clash_logs)

            # 기병 돌입 지원
            atk_cav = next((c for c in state.attacker_corps if c.troop_type == "cavalry" and c.current_count > 0), None)
            if atk_cav:
                logs.append("🐎 [기병대 시가전 진입] 기병 기동대가 함락된 성문을 통과해 적의 배후를 급습합니다!")
                _, _, cav_logs = cls.resolve_formation_clash(atk_cav, def_inf, fort, in_breach=True)
                logs.extend(cav_logs)
                state.defender_morale.adjust_morale(-12)
        else:
            # 성벽 위 공성탑 진입
            operational_towers = [t for t in state.attacker_engines if t.engine_type == "siege_tower" and t.is_operational and fort.moat_cleared]
            if operational_towers:
                logs.append("🏰 [공성탑 성벽 접안!] 거대한 공성탑 다리가 성벽 상단에 내려앉으며 정예 충격 보병이 쏟아져 나옵니다!")
                _, _, tower_logs = cls.resolve_formation_clash(atk_inf, def_inf, fort, in_breach=False)
                logs.extend(tower_logs)
            else:
                logs.append("🧱 [성벽 방어선 건재] 성문과 외벽이 아직 뚫리지 않아 대규모 보병 돌입이 억제되고 있습니다.")

        return logs

    # ------------------------------------------------------------
    # Phase 4: Morale Check & Rout Resolution
    # ------------------------------------------------------------
    @classmethod
    def execute_morale_and_logistics_phase(cls, state: SiegeBattleState) -> List[str]:
        """
        4페이즈: 군량 보급 소모, 사상자 누적에 따른 사기 붕괴 및 패주(Rout) 판정.
        """
        logs = []
        fort = state.fortress

        # A. 군량 비축일 삭감 (1일 경과)
        fort.supplies_remaining_days = max(0, fort.supplies_remaining_days - 1)
        if fort.supplies_remaining_days == 0:
            logs.append("💀 [농성 식량 고갈!] 성내 식량과 식수가 바닥나 병사들이 쥐와 가죽을 씹으며 사기가 폭락합니다!")
            state.defender_morale.adjust_morale(-15)

        # B. 사상자 비율에 따른 사기 감소
        atk_total_init = sum(c.initial_count for c in state.attacker_corps)
        atk_total_curr = sum(c.current_count for c in state.attacker_corps)
        if atk_total_init > 0:
            atk_loss_ratio = (atk_total_init - atk_total_curr) / atk_total_init
            if atk_loss_ratio >= 0.50:
                state.attacker_morale.adjust_morale(-20)
                logs.append("⚠️ [공격군 심대한 피해] 공격군 누적 사상자가 50%를 초과하여 동요가 극심합니다!")
            elif atk_loss_ratio >= 0.30:
                state.attacker_morale.adjust_morale(-10)

        def_total_init = sum(c.initial_count for c in state.defender_corps)
        def_total_curr = sum(c.current_count for c in state.defender_corps)
        if def_total_init > 0:
            def_loss_ratio = (def_total_init - def_total_curr) / def_total_init
            if def_loss_ratio >= 0.50:
                state.defender_morale.adjust_morale(-20)
                logs.append("⚠️ [수비군 치명적 손실] 수비군 절반 이상이 전사하여 방어선 유지가 한계에 도달했습니다!")
            elif def_loss_ratio >= 0.30:
                state.defender_morale.adjust_morale(-10)

        # C. 사기 붕괴(Rout) 및 승패 판정
        if state.defender_morale.morale <= 20 or def_total_curr <= (def_total_init * 0.15):
            state.battle_concluded = True
            state.winner_side = "attacker"
            logs.append("🏳️💥 [수비군 전면 패주 및 성채 함락!] 수비 병력이 무기를 버리고 도주하며 성채가 완전히 함락되었습니다!")
            return logs

        if state.attacker_morale.morale <= 20 or atk_total_curr <= (atk_total_init * 0.20):
            state.battle_concluded = True
            state.winner_side = "defender"
            logs.append("🛡️🎉 [공격군 패퇴 및 수성 성공!] 공격군이 참혹한 피해를 감당하지 못하고 포위망을 풀고 패주했습니다!")
            return logs

        logs.append(f"📊 [전황 결산] 공격군 사기: {state.attacker_morale.morale}/100 ({state.attacker_morale.morale_tier}) | 수비군 사기: {state.defender_morale.morale}/100 ({state.defender_morale.morale_tier})")
        return logs

    # ------------------------------------------------------------
    # Master Turn Pipeline
    # ------------------------------------------------------------
    @classmethod
    def advance_siege_turn(cls, state: SiegeBattleState) -> List[str]:
        """
        공성전 1턴 (1작전 틱 / 하루 분량)을 순차적으로 진행한다.
        """
        if state.battle_concluded:
            return [f"이미 공성전이 종료되었습니다 (승자: {state.winner_side})."]

        turn_logs = [f"=== [공성전 {state.day_count}일차 작전 전개] ==="]

        # Phase 1: 포격
        p1_logs = cls.execute_artillery_phase(state)
        turn_logs.extend(p1_logs)

        # Phase 2: 해자 & 접근
        p2_logs = cls.execute_advance_phase(state)
        turn_logs.extend(p2_logs)

        # Phase 3: 전열 돌파 충돌
        p3_logs = cls.execute_breach_assault_phase(state)
        turn_logs.extend(p3_logs)

        # Phase 4: 보급 & 사기 결산
        p4_logs = cls.execute_morale_and_logistics_phase(state)
        turn_logs.extend(p4_logs)

        state.day_count += 1
        state.logs.extend(turn_logs)
        return turn_logs

    # ------------------------------------------------------------
    # Commando Special Infiltration Action
    # ------------------------------------------------------------
    @classmethod
    def execute_commando_action(
        cls,
        state: SiegeBattleState,
        action_type: str,
        infiltrator_stealth_mod: int = 0
    ) -> Dict[str, Any]:
        """
        플레이어 또는 특공대의 야간 침투 특수 공작.
        성문 빗장 개방, 투석기 방화, 군량고 파괴, 지휘관 저격 등.
        """
        dc_map = {
            "burn_catapult": 14,
            "open_gate": 18,
            "sabotage_supplies": 13,
            "snipe_commander": 19
        }
        dc = dc_map.get(action_type, 15)
        roll = DiceEngine.roll_d20()
        total_check = roll + infiltrator_stealth_mod
        success = total_check >= dc

        result = {
            "action_type": action_type,
            "roll": roll,
            "total_check": total_check,
            "dc": dc,
            "success": success,
            "log": ""
        }

        if action_type == "burn_catapult":
            if success:
                target = next((e for e in state.attacker_engines if not e.is_destroyed), None)
                if target:
                    target.is_destroyed = True
                    target.is_operational = False
                    target.durability = 0.0
                    state.attacker_morale.adjust_morale(-10)
                    result["log"] = f"🔥 [특공 성공] 적의 [{target.name_ko}]에 불을 질러 전소시켰습니다! (적 사기 -10)"
                else:
                    result["log"] = "파괴할 적 공성 병기가 없습니다."
            else:
                result["log"] = "🚨 [특공 실패] 투석기 경비병에게 발각되어 화살 세례를 받고 간신히 탈출했습니다!"

        elif action_type == "open_gate":
            if success:
                state.fortress.gate_breached = True
                state.fortress.gate_durability = 0.0
                state.defender_morale.adjust_morale(-20)
                result["log"] = "🚪🗝️ [특공 성공] 성문 빗장 쇠사슬을 절단하여 문을 활짝 열어젖혔습니다! (수비군 사기 -20)"
            else:
                result["log"] = "🚨 [특공 실패] 성문 안쪽 경비초소의 삼엄한 불침번을 뚫지 못하고 후퇴했습니다."

        elif action_type == "sabotage_supplies":
            if success:
                state.fortress.supplies_remaining_days = max(0, state.fortress.supplies_remaining_days - 30)
                state.defender_morale.adjust_morale(-15)
                result["log"] = "🌾🔥 [특공 성공] 성내 군량 창고에 불을 질러 비축 군량 30일분을 전소시켰습니다! (수비군 사기 -15)"
            else:
                result["log"] = "🚨 [특공 실패] 군량 창고 주변 순찰대에게 쫓겨 연기만 피우고 도주했습니다."

        elif action_type == "snipe_commander":
            if success:
                state.attacker_morale.commander_wounded = True
                state.attacker_morale.adjust_morale(-30)
                result["log"] = "🎯🩸 [특공 대성공] 야간 저격으로 적 총지휘관의 어깨를 관통 중상을 입혔습니다! (적 사기 -30)"
            else:
                result["log"] = "🚨 [특공 실패] 바람의 영향으로 화살이 빗나가 지휘관의 투구 깃털만 스쳤습니다."

        return result

    # ------------------------------------------------------------
    # External LLM Prompt Generation (Rule 8 Compliance)
    # ------------------------------------------------------------
    @classmethod
    def generate_external_llm_prompt(cls, state: SiegeBattleState, latest_logs: List[str]) -> str:
        """
        규칙 8 준수: 외부 대형 LLM(GPT/Claude) 연동을 위한 서사 묘사 프롬프트를 생성한다.
        결정론적 수치(내구도, 사상자, 사기, 진형)를 바탕으로 처절한 전장 문학 묘사를 요청한다.
        """
        fort = state.fortress
        prompt = f"""[시스템 컨텍스트: Quilltale TRPG 대규모 성벽 공성전 시뮬레이션 결과]
당신은 냉혹하고 사실적인 다크 판타지 전장 문학을 집필하는 마스터 스토리텔러(GM)입니다.
아래의 결정론적 파이썬 물리 연산 수치와 발생 사건 로그를 바탕으로, 플레이어의 오감(비명, 화약과 피비린내, 지면의 진동, 부서지는 석재 먼지)을 자극하는 생생한 2단계 서사를 작성하십시오.

### 1. 전장 물리 및 구조물 상태 현황
- 격전지 정주지: [{fort.settlement_name}] (성벽 등급: Tier {fort.wall_tier})
- 성벽 내구도: {fort.wall_durability:.1f} / {fort.max_wall_durability:.1f} (외벽 돌파 여부: {fort.wall_breached})
- 성문 상태: [{fort.gate_type}] (내구도: {fort.gate_durability:.1f} / {fort.max_gate_durability:.1f}, 돌파 여부: {fort.gate_breached})
- 해자 상태: [{fort.moat_type}] (방호도: {fort.moat_durability:.1f} / {fort.max_moat_durability:.1f}, 매립 도하 가능: {fort.moat_cleared})
- 성내 잔여 군량: {fort.supplies_remaining_days}일분
- 마도 결계 활성: {fort.barrier_active} (결계 내구도: {fort.barrier_durability:.1f})

### 2. 양군 전력 및 사기 현황
- 공격군:
  * 총 잔여 병력: {sum(c.current_count for c in state.attacker_corps)}명 (사상자: {sum(c.casualty_count for c in state.attacker_corps)}명)
  * 진형: {", ".join(f"{c.corps_name}({c.current_formation})" for c in state.attacker_corps)}
  * 사기: {state.attacker_morale.morale}/100 [{state.attacker_morale.morale_tier}]
- 수비군:
  * 총 잔여 병력: {sum(c.current_count for c in state.defender_corps)}명 (사상자: {sum(c.casualty_count for c in state.defender_corps)}명)
  * 진형: {", ".join(f"{c.corps_name}({c.current_formation})" for c in state.defender_corps)}
  * 사기: {state.defender_morale.morale}/100 [{state.defender_morale.morale_tier}]

### 3. 이번 작전 틱 발생 사건 로그
{chr(10).join(f"- {log}" for log in latest_logs)}

### 4. 서사 작성 지침 (Strict Rules)
1. 절대로 결정론적 수치(성벽 잔여 내구도, 돌파 여부, 사망자)를 날조하거나 왜곡하지 마십시오.
2. 성벽이 뚫리지 않았는데 성내로 침입했다고 쓰지 마십시오. 해자가 메워지지 않았다면 충차가 성문에 닿지 못했다고 명시하십시오.
3. 3군 진형 상성(방패벽에 튕겨나간 화살, 장창에 찔린 기병의 말)의 역학을 현장감 넘치게 묘사하십시오.
4. 문체는 비장하고 거칠며, 전쟁의 참혹함과 방어군의 결사 항전을 입체적으로 묘사하십시오.
"""
        return prompt
