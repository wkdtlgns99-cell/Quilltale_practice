"""
Domain Pioneering & Settlement Construction Engine for Quilltale TRPG.
Provides deterministic settlement claim, modular facility construction queues,
population demographics, dynamic taxation, and turn-based settlement simulations.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import logging

from src.world.infra_models import (
    Settlement,
    Facility,
    SettlementYields,
    FacilityCategory,
    BuildingStatus,
    FacilityType,
)
from src.world.infrastructure import InfrastructureRegistry

logger = logging.getLogger(__name__)


# =====================================================================
# 1. Domain Pioneering Data Models (Rule 5: traits list included)
# =====================================================================
@dataclass
class ConstructionProject:
    """Represents a facility construction or upgrade task in a settlement queue."""
    project_id: str
    settlement_id: str
    facility_id: str
    facility_name: str
    facility_type: str
    category: str = "trade_workshop"
    target_tier: int = 1
    total_turns_required: int = 3
    turns_remaining: int = 3
    cost_gold: int = 100
    cost_production: int = 50
    status: str = "in_progress"  # in_progress, completed, cancelled, paused
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ConstructionProject":
        clean = dict(data)
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


@dataclass
class DomainPioneeringState:
    """Manages player pioneering governance, policies, and construction queues."""
    settlement_id: str
    settlement_name: str
    claimed_turn: int = 1
    pioneer_leader_id: str = "player"
    tax_rate: float = 0.10  # 10% standard tax rate
    active_projects: List[ConstructionProject] = field(default_factory=list)
    completed_projects_count: int = 0
    last_tax_collection_turn: int = 0
    total_tax_collected: int = 0
    settler_morale: int = 70  # 0~100
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        d = asdict(self)
        d["active_projects"] = [p.to_dict() if hasattr(p, "to_dict") else p for p in self.active_projects]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "DomainPioneeringState":
        clean = dict(data)
        projects = []
        for p in data.get("active_projects", []):
            if isinstance(p, dict):
                projects.append(ConstructionProject.from_dict(p))
            elif isinstance(p, ConstructionProject):
                projects.append(p)
        clean["active_projects"] = projects
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


@dataclass
class DomainTurnSummary:
    """Deterministic snapshot of a settlement's single turn/day progression."""
    settlement_id: str
    turn: int
    food_delta: float = 0.0
    production_delta: float = 0.0
    gold_income: int = 0
    population_change: int = 0
    current_population: int = 0
    discontent_change: int = 0
    current_discontent: int = 0
    completed_buildings: List[str] = field(default_factory=list)
    events_triggered: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DomainTurnSummary":
        clean = dict(data)
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


# =====================================================================
# 2. Master Facility Catalog & Construction Blueprints
# =====================================================================
BUILDING_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "palisade": {
        "name": "원목 방책",
        "facility_type": "palisade",
        "category": FacilityCategory.DEFENSE_SAFETY,
        "cost_gold": 80,
        "cost_production": 40,
        "turns": 2,
        "description": "외적과 야생 마수의 기습을 막아주는 튼튼한 참나무 방책.",
        "stat_bonuses": {
            "wall_defense_tier": 1,
            "security_level": 15,
            "defense_rating": 25,
            "bandit_threat_delta": -10,
        },
        "traits": ["방어시설", "목조요새"],
    },
    "stone_wall": {
        "name": "견고한 석벽",
        "facility_type": "stone_wall",
        "category": FacilityCategory.DEFENSE_SAFETY,
        "cost_gold": 250,
        "cost_production": 120,
        "turns": 4,
        "description": "공성 병기와 대형 마수의 돌격을 저지하는 화강암 성벽.",
        "stat_bonuses": {
            "wall_defense_tier": 2,
            "security_level": 30,
            "defense_rating": 50,
            "bandit_threat_delta": -25,
        },
        "traits": ["성벽", "방어시설", "화강암"],
    },
    "watchtower": {
        "name": "경계 망루",
        "facility_type": "watchtower",
        "category": FacilityCategory.DEFENSE_SAFETY,
        "cost_gold": 100,
        "cost_production": 50,
        "turns": 2,
        "description": "원거리 시야를 확보하여 기습을 사전에 경보하는 고지대 감시 망루.",
        "stat_bonuses": {
            "security_level": 15,
            "patrol_strength": 15,
            "bandit_threat_delta": -15,
        },
        "traits": ["조기경보", "원거리시야"],
    },
    "communal_well": {
        "name": "공용 식수 우물",
        "facility_type": "communal_well",
        "category": FacilityCategory.SANITATION_WATER,
        "cost_gold": 60,
        "cost_production": 30,
        "turns": 1,
        "description": "깨끗한 지하 암반수를 공급하여 수인성 전염병을 막는 공동 우물.",
        "stat_bonuses": {
            "self_sufficiency_water": 25,
            "hygiene_level": 15,
            "water_capacity_rating": 20,
        },
        "traits": ["상수도", "위생시설"],
    },
    "granary": {
        "name": "비축 미곡창",
        "facility_type": "granary",
        "category": FacilityCategory.FOOD_STORAGE,
        "cost_gold": 120,
        "cost_production": 60,
        "turns": 2,
        "description": "겨울 기근과 흉작을 견디기 위해 곡물을 안전하게 건조 비축하는 대형 창고.",
        "stat_bonuses": {
            "storage_reserve_months": 3.0,
            "self_sufficiency_food": 15,
            "food_yield": 5.0,
        },
        "traits": ["식량비축", "기근예방"],
    },
    "farmland": {
        "name": "개간 농경지",
        "facility_type": "farmland",
        "category": FacilityCategory.FOOD_STORAGE,
        "cost_gold": 100,
        "cost_production": 40,
        "turns": 2,
        "description": "주민들의 주식인 밀과 보리를 재배하여 식량 자급을 달성하는 비옥한 농지.",
        "stat_bonuses": {
            "food_yield": 25.0,
            "self_sufficiency_food": 20,
            "housing_capacity": 15,
        },
        "traits": ["농업", "식량생산"],
    },
    "blacksmith_forge": {
        "name": "개척지 대장간",
        "facility_type": "blacksmith_forge",
        "category": FacilityCategory.TRADE_WORKSHOP,
        "cost_gold": 180,
        "cost_production": 70,
        "turns": 3,
        "description": "농기구와 무기, 갑옷을 주조하고 수리하여 영지 생산력을 견인하는 제철 화로.",
        "stat_bonuses": {
            "production_yield": 15.0,
            "blacksmith_tier": 1,
            "prosperity_rating": 10,
        },
        "traits": ["생산시설", "무기제조", "대장간"],
    },
    "tavern_inn": {
        "name": "모험가 주점 겸 여관",
        "facility_type": "tavern_inn",
        "category": FacilityCategory.TRADE_WORKSHOP,
        "cost_gold": 140,
        "cost_production": 50,
        "turns": 2,
        "description": "유랑 용병과 상인들의 피로를 풀고 정보와 소문이 모여드는 활기찬 주점.",
        "stat_bonuses": {
            "gold_yield": 20.0,
            "inn_bed_capacity": 10,
            "entertainment_relief_rating": 20,
            "discontent_delta": -5,
            "rumor_circulation_rate": 20,
        },
        "traits": ["상업", "여관", "정보수집"],
    },
    "apothecary_clinic": {
        "name": "약초원 및 치료소",
        "facility_type": "apothecary_clinic",
        "category": FacilityCategory.CIVIC_COMMUNAL,
        "cost_gold": 130,
        "cost_production": 40,
        "turns": 2,
        "description": "야생 약초를 재배하고 부상병과 역병 환자를 격리 치료하는 의료 구호소.",
        "stat_bonuses": {
            "hygiene_level": 20,
            "medical_capacity": 10,
            "healthcare_rating": 25,
            "discontent_delta": -5,
        },
        "traits": ["의료", "위생", "구호시설"],
    },
    "barracks_training": {
        "name": "자경단 훈련소 및 병영",
        "facility_type": "training_ground",
        "category": FacilityCategory.DEFENSE_SAFETY,
        "cost_gold": 200,
        "cost_production": 80,
        "turns": 3,
        "description": "영지 청년들을 정예 자경대로 훈련시키고 무기를 비축하는 군사 병영.",
        "stat_bonuses": {
            "security_level": 25,
            "patrol_strength": 30,
            "militia_armory_capacity": 30,
            "bandit_threat_delta": -20,
        },
        "traits": ["군사시설", "자경단", "훈련소"],
    },
    "market_square": {
        "name": "장터 광장",
        "facility_type": "market_square",
        "category": FacilityCategory.TRADE_WORKSHOP,
        "cost_gold": 220,
        "cost_production": 80,
        "turns": 3,
        "description": "인근 마을과 카라반 대상단이 모여들어 특산품을 교환하는 상업 중심지.",
        "stat_bonuses": {
            "gold_yield": 35.0,
            "trade_power": 20,
            "prosperity_rating": 20,
        },
        "traits": ["상업중심", "시장", "물류"],
    },
    "town_hall": {
        "name": "영주관 및 자치회관",
        "facility_type": "town_hall_manor",
        "category": FacilityCategory.CIVIC_COMMUNAL,
        "cost_gold": 280,
        "cost_production": 120,
        "turns": 4,
        "description": "영지 칙령을 선포하고 주민 민원을 수렴하여 통치 정당성을 확립하는 영주 저택.",
        "stat_bonuses": {
            "social_cohesion_rating": 25,
            "loyalty_to_nation": 20,
            "discontent_delta": -10,
            "development_tier": 1,
        },
        "traits": ["정부기관", "영주관", "통치중심"],
    },
}


# =====================================================================
# 3. Domain Pioneering & Construction Engine
# =====================================================================
class DomainEngine:
    """
    Pure deterministic domain pioneering and construction engine.
    Manages land claims, building queues, population demographics, and turn production.
    """

    @staticmethod
    def ensure_registry(state: Any) -> InfrastructureRegistry:
        """Ensures state.infrastructure is instantiated as an InfrastructureRegistry."""
        if state.infrastructure is None:
            state.infrastructure = InfrastructureRegistry()
        elif isinstance(state.infrastructure, dict):
            state.infrastructure = InfrastructureRegistry.from_dict(state.infrastructure)
        return state.infrastructure

    @classmethod
    def claim_new_domain(
        cls,
        state: Any,
        settlement_id: str,
        settlement_name: str,
        settlement_type: str = "pioneer_outpost",
        region_id: str = "wilderness_frontier",
        nation_id: str = "independent",
    ) -> Settlement:
        """
        Declares and initializes a new player domain / outpost.
        Assigns the player as sovereign lord and seeds baseline population.
        """
        reg = cls.ensure_registry(state)

        # Retrieve existing or initialize new settlement
        settlement = reg.settlements.get(settlement_id)
        if settlement is None:
            settlement = Settlement(
                id=settlement_id,
                name=settlement_name,
                nation_id=nation_id,
                region_id=region_id,
                settlement_type=settlement_type,
                population=25,
                housing_capacity=60,
                development_tier=1,
                security_level=40,
                wall_defense_tier=0,
                treasury=300,
                discontent_level=10,
                loyalty_to_nation=90,
                self_sufficiency_food=60,
                self_sufficiency_water=70,
                hygiene_level=60,
                patrol_strength=20,
                bandit_threat_level=30,
                yields=SettlementYields(
                    food=20.0,
                    production=15.0,
                    gold=10.0,
                    science=2.0,
                    culture=2.0,
                    faith=5.0,
                ),
                lord_npc_id=getattr(state.player, "name", "player") or "player",
                lord_dynasty="개척군주",
                traits=["개척지", "플레이어영지"],
            )
            reg.register_settlement(settlement)
        else:
            # Overwrite ownership to player
            settlement.lord_npc_id = getattr(state.player, "name", "player") or "player"
            if "플레이어영지" not in settlement.traits:
                settlement.traits.append("플레이어영지")

        # Initialize or link DomainPioneeringState
        turn = getattr(state, "current_day", 1)
        pstate = DomainPioneeringState(
            settlement_id=settlement_id,
            settlement_name=settlement_name,
            claimed_turn=turn,
            pioneer_leader_id=settlement.lord_npc_id,
            tax_rate=0.10,
            settler_morale=75,
            traits=["자주령", "신규개척지"],
        )

        if not hasattr(state, "pioneering_domains") or state.pioneering_domains is None:
            state.pioneering_domains = {}
        state.pioneering_domains[settlement_id] = pstate

        logger.info(f"Domain claimed: {settlement_name} ({settlement_id}) by {settlement.lord_npc_id}")
        return settlement

    @classmethod
    def start_construction(
        cls,
        state: Any,
        settlement_id: str,
        building_key: str,
    ) -> Dict[str, Any]:
        """
        Starts a new construction project in the target settlement.
        Deducts player gold or settlement treasury, registers under_construction facility.
        """
        reg = cls.ensure_registry(state)
        settlement = reg.settlements.get(settlement_id)
        if not settlement:
            return {"success": False, "reason": f"정주지 [{settlement_id}]를 찾을 수 없습니다."}

        template = BUILDING_TEMPLATES.get(building_key)
        if not template:
            return {"success": False, "reason": f"건축 템플릿 [{building_key}]가 존재하지 않습니다."}

        # Check existing active project for same building type
        pstate = cls.get_pioneering_state(state, settlement_id)
        for proj in pstate.active_projects:
            if proj.facility_type == template["facility_type"] and proj.status == "in_progress":
                return {
                    "success": False,
                    "reason": f"이미 [{template['name']}] 건축 공사가 진행 중입니다.",
                }

        cost_gold = template["cost_gold"]
        cost_prod = template["cost_production"]

        # Check player gold and treasury
        player_gold = getattr(state.player, "gold", 0)
        use_player_gold = False

        if player_gold >= cost_gold:
            state.player.gold -= cost_gold
            use_player_gold = True
        elif settlement.treasury >= cost_gold:
            settlement.treasury -= cost_gold
        else:
            return {
                "success": False,
                "reason": f"건축 자금 부족! (필요: {cost_gold}G, 보유: 플레이어 {player_gold}G, 금고 {settlement.treasury}G)",
            }

        # Generate unique facility ID
        fac_num = len(settlement.facility_ids) + 1
        facility_id = f"fac_{settlement_id}_{building_key}_{fac_num}"

        facility = Facility(
            id=facility_id,
            name=template["name"],
            settlement_id=settlement_id,
            category=template["category"],
            facility_type=template["facility_type"],
            building_status=BuildingStatus.UNDER_CONSTRUCTION.value,
            construction_progress=0,
            repair_cost_materials={"gold": cost_gold, "production": cost_prod},
            traits=list(template.get("traits", [])),
            description=template.get("description", ""),
        )
        reg.register_facility(facility)

        # Register ConstructionProject
        project_id = f"proj_{facility_id}"
        project = ConstructionProject(
            project_id=project_id,
            settlement_id=settlement_id,
            facility_id=facility_id,
            facility_name=template["name"],
            facility_type=template["facility_type"],
            category=template["category"].value if hasattr(template["category"], "value") else str(template["category"]),
            total_turns_required=template["turns"],
            turns_remaining=template["turns"],
            cost_gold=cost_gold,
            cost_production=cost_prod,
            status="in_progress",
            traits=["착공", template["facility_type"]],
        )
        pstate.active_projects.append(project)

        source_str = "플레이어 소지금" if use_player_gold else "영지 금고"
        return {
            "success": True,
            "project_id": project_id,
            "facility_name": template["name"],
            "turns_required": template["turns"],
            "cost_gold": cost_gold,
            "paid_from": source_str,
            "message": f"[{settlement.name}]에 [{template['name']}] 건축 공사를 착공했습니다! (소요: {template['turns']}턴, {cost_gold}G 지불: {source_str})",
        }

    @classmethod
    def advance_domain_tick(
        cls,
        state: Any,
        settlement_id: str,
    ) -> DomainTurnSummary:
        """
        Deterministically simulates 1 turn (or 1 day) of settlement growth:
        - Construction progress ticks down, completes buildings and applies permanent stat bonuses.
        - Food and production yield calculation against consumption.
        - Population immigration / famine emigration.
        - Discontent and morale balance.
        - Triggering random deterministic civic events.
        """
        reg = cls.ensure_registry(state)
        settlement = reg.settlements.get(settlement_id)
        current_turn = getattr(state, "current_day", 1)

        if not settlement:
            return DomainTurnSummary(settlement_id=settlement_id, turn=current_turn)

        pstate = cls.get_pioneering_state(state, settlement_id)
        completed_names: List[str] = []
        events: List[str] = []

        # 1. Construction Progress Tick
        still_active: List[ConstructionProject] = []
        for proj in pstate.active_projects:
            if proj.status == "in_progress":
                proj.turns_remaining -= 1
                fac = reg.facilities.get(proj.facility_id)
                if fac:
                    progress_pct = int(((proj.total_turns_required - proj.turns_remaining) / max(1, proj.total_turns_required)) * 100)
                    fac.construction_progress = min(100, progress_pct)

                if proj.turns_remaining <= 0:
                    proj.status = "completed"
                    proj.turns_remaining = 0
                    pstate.completed_projects_count += 1
                    completed_names.append(proj.facility_name)

                    # Update Facility Status
                    if fac:
                        fac.building_status = BuildingStatus.OPERATIONAL.value
                        fac.construction_progress = 100
                    if fac and fac.id in settlement.under_construction_facilities:
                        settlement.under_construction_facilities.remove(fac.id)

                    # Apply Building Template Permanent Bonuses
                    tmpl = BUILDING_TEMPLATES.get(proj.facility_type)
                    if tmpl:
                        cls._apply_building_bonuses(settlement, tmpl.get("stat_bonuses", {}))
                    events.append(f"건축 완공: [{proj.facility_name}]이(가) 완공되어 본격적인 가동에 들어갔습니다!")
                else:
                    still_active.append(proj)
            else:
                still_active.append(proj)

        pstate.active_projects = still_active

        # 2. Resource & Yield Production
        food_produced = settlement.yields.food
        production_produced = settlement.yields.production
        gold_produced = settlement.yields.gold

        # Food consumption: 0.5 food per population
        food_needed = settlement.population * 0.5
        food_delta = food_produced - food_needed

        # 3. Population Dynamics
        pop_change = 0
        if food_delta >= 0:
            # Food surplus: population can grow if housing permits
            housing_room = settlement.housing_capacity - settlement.population
            if housing_room > 0 and settlement.security_level >= 30:
                # 1 migrant per 5 surplus food, capped by housing room
                growth = max(1, min(housing_room, int(food_delta / 5.0)))
                settlement.population += growth
                pop_change = growth
                events.append(f"이주민 유입: 소문을 듣고 정착민 {growth}명이 영지로 이주해왔습니다. (현재 인구: {settlement.population}명)")
        else:
            # Food deficit: famine
            deficit = abs(food_delta)
            loss = min(settlement.population, max(1, int(deficit / 4.0)))
            settlement.population -= loss
            pop_change = -loss
            settlement.discontent_level = min(100, settlement.discontent_level + 8)
            events.append(f"식량 부족 기근 발생! 식량난으로 주민 {loss}명이 영지를 이탈하거나 굶주리고 있습니다.")

        # 4. Discontent & Morale Simulation
        discontent_delta = 0
        # High tax penalty
        if pstate.tax_rate > 0.20:
            discontent_delta += 4
        elif pstate.tax_rate <= 0.10:
            discontent_delta -= 2

        # Low security or hygiene penalty
        if settlement.security_level < 30:
            discontent_delta += 3
        if settlement.hygiene_level < 30:
            discontent_delta += 3

        # High prosperity or security bonus
        if settlement.prosperity_rating >= 60 and settlement.security_level >= 60:
            discontent_delta -= 2

        settlement.discontent_level = max(0, min(100, settlement.discontent_level + discontent_delta))

        # Civil unrest alert
        if settlement.discontent_level >= 75:
            events.append("경고: 주민 불만도가 극에 달해 폭동과 납세 거부 운동의 조짐이 보입니다!")

        # 5. Treasury Yield Accrual
        daily_treasury_income = max(0, int(gold_produced * 0.5))
        settlement.treasury += daily_treasury_income

        summary = DomainTurnSummary(
            settlement_id=settlement_id,
            turn=current_turn,
            food_delta=round(food_delta, 1),
            production_delta=round(production_produced, 1),
            gold_income=daily_treasury_income,
            population_change=pop_change,
            current_population=settlement.population,
            discontent_change=discontent_delta,
            current_discontent=settlement.discontent_level,
            completed_buildings=completed_names,
            events_triggered=events,
            traits=["정기정산", f"인구_{settlement.population}"],
        )
        return summary

    @classmethod
    def _apply_building_bonuses(cls, settlement: Settlement, bonuses: Dict[str, Any]) -> None:
        """Applies stat bonuses from a completed building template to a Settlement."""
        for k, v in bonuses.items():
            if k == "wall_defense_tier":
                settlement.wall_defense_tier = max(settlement.wall_defense_tier, int(v))
            elif k == "security_level":
                settlement.security_level = min(100, settlement.security_level + int(v))
            elif k == "defense_rating":
                settlement.infrastructure.defense.fortification_integrity = min(
                    100, settlement.infrastructure.defense.fortification_integrity + int(v)
                )
            elif k == "bandit_threat_delta":
                settlement.bandit_threat_level = max(0, settlement.bandit_threat_level + int(v))
            elif k == "patrol_strength":
                settlement.patrol_strength = min(100, settlement.patrol_strength + int(v))
            elif k == "self_sufficiency_water":
                settlement.self_sufficiency_water = min(100, settlement.self_sufficiency_water + int(v))
            elif k == "hygiene_level":
                settlement.hygiene_level = min(100, settlement.hygiene_level + int(v))
            elif k == "water_capacity_rating":
                settlement.infrastructure.sanitation.water_capacity_rating = min(
                    100, settlement.infrastructure.sanitation.water_capacity_rating + int(v)
                )
            elif k == "storage_reserve_months":
                settlement.infrastructure.food.storage_reserve_months += float(v)
            elif k == "self_sufficiency_food":
                settlement.self_sufficiency_food = min(100, settlement.self_sufficiency_food + int(v))
            elif k == "food_yield":
                settlement.yields.food += float(v)
            elif k == "production_yield":
                settlement.yields.production += float(v)
            elif k == "gold_yield":
                settlement.yields.gold += float(v)
            elif k == "housing_capacity":
                settlement.housing_capacity += int(v)
            elif k == "blacksmith_tier":
                settlement.blacksmith_tier = max(settlement.blacksmith_tier, int(v))
            elif k == "prosperity_rating":
                settlement.prosperity_rating = min(100, settlement.prosperity_rating + int(v))
            elif k == "trade_power":
                settlement.trade_power = min(100, settlement.trade_power + int(v))
            elif k == "inn_bed_capacity":
                settlement.inn_bed_capacity += int(v)
            elif k == "entertainment_relief_rating":
                settlement.entertainment_relief_rating = min(100, settlement.entertainment_relief_rating + int(v))
            elif k == "discontent_delta":
                settlement.discontent_level = max(0, settlement.discontent_level + int(v))
            elif k == "rumor_circulation_rate":
                settlement.rumor_circulation_rate = min(100, settlement.rumor_circulation_rate + int(v))
            elif k == "medical_capacity":
                settlement.medical_capacity += int(v)
            elif k == "healthcare_rating":
                settlement.infrastructure.civic.healthcare_rating = min(
                    100, settlement.infrastructure.civic.healthcare_rating + int(v)
                )
            elif k == "militia_armory_capacity":
                settlement.militia_armory_capacity += int(v)
            elif k == "social_cohesion_rating":
                settlement.infrastructure.civic.social_cohesion_rating = min(
                    100, settlement.infrastructure.civic.social_cohesion_rating + int(v)
                )
            elif k == "loyalty_to_nation":
                settlement.loyalty_to_nation = min(100, settlement.loyalty_to_nation + int(v))
            elif k == "development_tier":
                settlement.development_tier = min(5, settlement.development_tier + int(v))

    @classmethod
    def collect_taxes(
        cls,
        state: Any,
        settlement_id: str,
    ) -> Dict[str, Any]:
        """
        Collects taxes from domain residents based on population, wealth, and tax rate.
        Transfers collected gold to player inventory or domain treasury.
        """
        reg = cls.ensure_registry(state)
        settlement = reg.settlements.get(settlement_id)
        if not settlement:
            return {"success": False, "reason": f"정주지 [{settlement_id}]를 찾을 수 없습니다."}

        pstate = cls.get_pioneering_state(state, settlement_id)
        current_turn = getattr(state, "current_day", 1)

        # Tax formula: population * base_per_capita(2.0) * tax_rate
        base_tax = int(settlement.population * 2.0 * pstate.tax_rate)
        tax_collected = max(1, base_tax)

        # Add to player gold
        state.player.gold += tax_collected
        pstate.total_tax_collected += tax_collected
        pstate.last_tax_collection_turn = current_turn

        # High tax causes discontent
        discontent_inc = 0
        if pstate.tax_rate >= 0.25:
            discontent_inc = 8
        elif pstate.tax_rate >= 0.15:
            discontent_inc = 3

        settlement.discontent_level = min(100, settlement.discontent_level + discontent_inc)

        return {
            "success": True,
            "settlement_name": settlement.name,
            "tax_rate_pct": int(pstate.tax_rate * 100),
            "tax_collected": tax_collected,
            "player_total_gold": state.player.gold,
            "discontent_increase": discontent_inc,
            "current_discontent": settlement.discontent_level,
            "message": f"[{settlement.name}]에서 세금 {tax_collected}G를 징수했습니다! (세율: {int(pstate.tax_rate * 100)}%, 현재 불만도: {settlement.discontent_level})",
        }

    @classmethod
    def set_tax_rate(
        cls,
        state: Any,
        settlement_id: str,
        new_tax_rate: float,
    ) -> Dict[str, Any]:
        """Sets the settlement's taxation policy (0.01 to 0.50)."""
        pstate = cls.get_pioneering_state(state, settlement_id)
        rate = max(0.0, min(0.50, round(float(new_tax_rate), 2)))
        pstate.tax_rate = rate
        rate_pct = int(rate * 100)
        return {
            "success": True,
            "settlement_id": settlement_id,
            "new_tax_rate": rate,
            "message": f"영지 세율을 {rate_pct}%로 조정했습니다.",
        }

    @classmethod
    def get_pioneering_state(cls, state: Any, settlement_id: str) -> DomainPioneeringState:
        """Retrieves or creates DomainPioneeringState from state.pioneering_domains."""
        if not hasattr(state, "pioneering_domains") or state.pioneering_domains is None:
            state.pioneering_domains = {}

        pstate = state.pioneering_domains.get(settlement_id)
        if pstate is None:
            reg = cls.ensure_registry(state)
            s = reg.settlements.get(settlement_id)
            s_name = s.name if s else settlement_id
            pstate = DomainPioneeringState(
                settlement_id=settlement_id,
                settlement_name=s_name,
                traits=["개척지"],
            )
            state.pioneering_domains[settlement_id] = pstate
        elif isinstance(pstate, dict):
            pstate = DomainPioneeringState.from_dict(pstate)
            state.pioneering_domains[settlement_id] = pstate

        return pstate

    @classmethod
    def get_domain_status_summary(cls, state: Any, settlement_id: str) -> str:
        """
        Generates a concise Korean deterministic status briefing string for TwoPassEngine.
        """
        reg = cls.ensure_registry(state)
        settlement = reg.settlements.get(settlement_id)
        if not settlement:
            return f"[영지 정보 없음: {settlement_id}]"

        pstate = cls.get_pioneering_state(state, settlement_id)

        # Build active projects list
        active_proj_strs = []
        for p in pstate.active_projects:
            if p.status == "in_progress":
                active_proj_strs.append(f"{p.facility_name}(남은턴:{p.turns_remaining})")

        projects_display = ", ".join(active_proj_strs) if active_proj_strs else "없음"

        wall_names = ["없음", "원목 방책", "석벽", "마도 성채"]
        wall_str = wall_names[settlement.wall_defense_tier] if settlement.wall_defense_tier < len(wall_names) else f"{settlement.wall_defense_tier}단계"

        summary_lines = [
            f"=== 🏰 영지 브리핑: {settlement.name} ===",
            f"- 영주: {settlement.lord_npc_id} (가문: {settlement.lord_dynasty})",
            f"- 거주 인구: {settlement.population}명 / 최대 수용 정원: {settlement.housing_capacity}명",
            f"- 방위 성벽: {wall_str} | 치안도: {settlement.security_level}/100 | 위생도: {settlement.hygiene_level}/100",
            f"- 주민 불만도: {settlement.discontent_level}/100 | 현행 세율: {int(pstate.tax_rate * 100)}%",
            f"- 영지 금고: {settlement.treasury}G | 자급율: 식량 {settlement.self_sufficiency_food}% / 식수 {settlement.self_sufficiency_water}%",
            f"- 턴당 산출: 식량 +{settlement.yields.food:.1f} | 생산력 +{settlement.yields.production:.1f} | 금화 +{settlement.yields.gold:.1f}",
            f"- 진행 중인 공사: {projects_display}",
        ]
        return "\n".join(summary_lines)
