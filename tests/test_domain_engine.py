"""
Tests for Domain Pioneering & Settlement Construction Engine (domain_engine.py)
and TwoPassEngine integration.
"""
import pytest
from unittest.mock import MagicMock

from src.world.state import WorldState, Player, Location
from src.world.infra_models import (
    Settlement,
    Facility,
    FacilityCategory,
    BuildingStatus,
)
from src.world.infrastructure import InfrastructureRegistry
from src.world.domain_engine import (
    DomainEngine,
    ConstructionProject,
    DomainPioneeringState,
    DomainTurnSummary,
    BUILDING_TEMPLATES,
)
from src.world.two_pass_engine import TwoPassEngine, DeterministicFactSheet


@pytest.fixture
def base_world():
    """Initializes a minimal WorldState with a starting location and player."""
    state = WorldState()
    loc = Location(id="frontier_post", name="국경 변경지대", description="국경 초소", exits={})
    state.locations["frontier_post"] = loc
    state.player = Player(name="아르민", health=100, max_health=100, gold=1000)
    state.player.location = "frontier_post"
    return state


# =====================================================================
# 1. Data Model & Rule 5 (traits) Tests
# =====================================================================
def test_construction_project_model_traits():
    """Verifies ConstructionProject includes traits list per Rule 5."""
    proj = ConstructionProject(
        project_id="proj_1",
        settlement_id="set_1",
        facility_id="fac_1",
        facility_name="원목 방책",
        facility_type="palisade",
        traits=["방어", "목조"],
    )
    assert proj.traits == ["방어", "목조"]
    d = proj.to_dict()
    assert d["traits"] == ["방어", "목조"]
    restored = ConstructionProject.from_dict(d)
    assert restored.traits == ["방어", "목조"]
    assert restored.status == "in_progress"


def test_domain_pioneering_state_model_traits():
    """Verifies DomainPioneeringState includes traits list per Rule 5 and serializes."""
    pstate = DomainPioneeringState(
        settlement_id="set_1",
        settlement_name="새벽 요새",
        traits=["개척지", "자주령"],
    )
    assert pstate.traits == ["개척지", "자주령"]
    proj = ConstructionProject(
        project_id="proj_1",
        settlement_id="set_1",
        facility_id="fac_1",
        facility_name="대장간",
        facility_type="blacksmith_forge",
        traits=["대장간"],
    )
    pstate.active_projects.append(proj)
    d = pstate.to_dict()
    assert len(d["active_projects"]) == 1
    restored = DomainPioneeringState.from_dict(d)
    assert restored.settlement_name == "새벽 요새"
    assert len(restored.active_projects) == 1
    assert restored.active_projects[0].traits == ["대장간"]


def test_domain_turn_summary_model_traits():
    """Verifies DomainTurnSummary includes traits list per Rule 5."""
    summary = DomainTurnSummary(
        settlement_id="set_1",
        turn=5,
        food_delta=12.5,
        population_change=3,
        current_population=28,
        traits=["풍년", "성장기"],
    )
    assert summary.traits == ["풍년", "성장기"]
    d = summary.to_dict()
    assert d["traits"] == ["풍년", "성장기"]
    restored = DomainTurnSummary.from_dict(d)
    assert restored.current_population == 28


# =====================================================================
# 2. Domain Pioneering Claim Tests
# =====================================================================
def test_claim_new_domain(base_world):
    """Verifies establishing a new sovereign player domain."""
    settlement = DomainEngine.claim_new_domain(
        state=base_world,
        settlement_id="domain_frontier_post",
        settlement_name="새벽의 변경 요새",
        settlement_type="pioneer_outpost",
    )
    assert settlement.id == "domain_frontier_post"
    assert settlement.name == "새벽의 변경 요새"
    assert settlement.lord_npc_id == "아르민"
    assert settlement.population == 25
    assert settlement.treasury == 300
    assert "플레이어영지" in settlement.traits

    # Verify state tracking
    assert "domain_frontier_post" in base_world.pioneering_domains
    pstate = DomainEngine.get_pioneering_state(base_world, "domain_frontier_post")
    assert pstate.settlement_name == "새벽의 변경 요새"
    assert pstate.pioneer_leader_id == "아르민"


def test_claim_existing_settlement_ownership_transfer(base_world):
    """Verifies claiming sovereignty over an existing settlement transfers lord title."""
    reg = DomainEngine.ensure_registry(base_world)
    existing = Settlement(
        id="iron_mine_village",
        name="철광석 마을",
        nation_id="neutral",
        region_id="mountains",
        lord_npc_id="former_lord",
    )
    reg.register_settlement(existing)

    claimed = DomainEngine.claim_new_domain(
        state=base_world,
        settlement_id="iron_mine_village",
        settlement_name="철광석 마을",
    )
    assert claimed.lord_npc_id == "아르민"
    assert "플레이어영지" in claimed.traits


# =====================================================================
# 3. Facility Construction Tests
# =====================================================================
def test_start_construction_success_with_player_gold(base_world):
    """Verifies starting construction pays from player gold and registers project."""
    DomainEngine.claim_new_domain(base_world, "domain_1", "솔리스 요새")
    base_world.player.gold = 500

    # Build palisade (cost 80G)
    res = DomainEngine.start_construction(base_world, "domain_1", "palisade")
    assert res["success"] is True
    assert base_world.player.gold == 420
    assert res["facility_name"] == "원목 방책"
    assert res["turns_required"] == 2

    # Verify facility registered in registry
    reg = base_world.infrastructure
    set1 = reg.settlements["domain_1"]
    assert len(set1.facility_ids) == 1
    assert len(set1.under_construction_facilities) == 1
    fac_id = set1.facility_ids[0]
    fac = reg.facilities[fac_id]
    assert fac.building_status == BuildingStatus.UNDER_CONSTRUCTION.value
    assert fac.construction_progress == 0


def test_start_construction_duplicate_prevention(base_world):
    """Verifies duplicate construction of the same ongoing facility is prevented."""
    DomainEngine.claim_new_domain(base_world, "domain_1", "솔리스 요새")
    base_world.player.gold = 500

    res1 = DomainEngine.start_construction(base_world, "domain_1", "watchtower")
    assert res1["success"] is True

    # Attempt to build second watchtower while first is in progress
    res2 = DomainEngine.start_construction(base_world, "domain_1", "watchtower")
    assert res2["success"] is False
    assert "이미" in res2["reason"]


def test_start_construction_insufficient_funds(base_world):
    """Verifies construction fails when both player and domain treasury lack gold."""
    DomainEngine.claim_new_domain(base_world, "domain_1", "가난한 요새")
    base_world.player.gold = 10
    reg = base_world.infrastructure
    reg.settlements["domain_1"].treasury = 20

    res = DomainEngine.start_construction(base_world, "domain_1", "stone_wall")  # cost 250G
    assert res["success"] is False
    assert "자금 부족" in res["reason"]


# =====================================================================
# 4. Turn Simulation & Tick Progression Tests
# =====================================================================
def test_advance_domain_tick_construction_completion(base_world):
    """Verifies 턴 경과로 공사가 진행되고 완공 시 스탯 보너스가 영구 적용된다."""
    DomainEngine.claim_new_domain(base_world, "domain_1", "바람 성채")
    base_world.player.gold = 500

    # Start watchtower (2 turns)
    DomainEngine.start_construction(base_world, "domain_1", "watchtower")
    set1 = base_world.infrastructure.settlements["domain_1"]
    initial_security = set1.security_level

    # Turn 1
    sum1 = DomainEngine.advance_domain_tick(base_world, "domain_1")
    assert len(sum1.completed_buildings) == 0
    pstate = DomainEngine.get_pioneering_state(base_world, "domain_1")
    assert pstate.active_projects[0].turns_remaining == 1

    # Turn 2: Completes!
    sum2 = DomainEngine.advance_domain_tick(base_world, "domain_1")
    assert "경계 망루" in sum2.completed_buildings
    assert set1.security_level == initial_security + 15
    assert len(set1.under_construction_facilities) == 0

    # Facility is operational
    fac_id = set1.facility_ids[0]
    fac = base_world.infrastructure.facilities[fac_id]
    assert fac.building_status == BuildingStatus.OPERATIONAL.value
    assert fac.construction_progress == 100


def test_advance_domain_tick_population_growth_and_famine(base_world):
    """Verifies surplus food invites settlers while deficit causes famine and unrest."""
    DomainEngine.claim_new_domain(base_world, "domain_1", "농경 요새")
    set1 = base_world.infrastructure.settlements["domain_1"]
    set1.population = 20
    set1.housing_capacity = 50
    set1.yields.food = 30.0  # consumption is 20 * 0.5 = 10, surplus = +20

    sum_growth = DomainEngine.advance_domain_tick(base_world, "domain_1")
    assert sum_growth.population_change > 0
    assert set1.population > 20

    # Induce famine
    set1.yields.food = 0.0
    initial_discontent = set1.discontent_level
    sum_famine = DomainEngine.advance_domain_tick(base_world, "domain_1")
    assert sum_famine.population_change < 0
    assert set1.discontent_level > initial_discontent
    assert any("기근" in ev for ev in sum_famine.events_triggered)


# =====================================================================
# 5. Taxation & Governance Tests
# =====================================================================
def test_collect_taxes_and_adjust_tax_rate(base_world):
    """Verifies tax rate setting and revenue collection."""
    DomainEngine.claim_new_domain(base_world, "domain_1", "세무 요새")
    set1 = base_world.infrastructure.settlements["domain_1"]
    set1.population = 40
    base_world.player.gold = 100

    # Standard tax (10%): 40 * 2.0 * 0.10 = 8G
    res = DomainEngine.collect_taxes(base_world, "domain_1")
    assert res["success"] is True
    assert res["tax_collected"] == 8
    assert base_world.player.gold == 108

    # Set exorbitant tax rate (30%)
    rate_res = DomainEngine.set_tax_rate(base_world, "domain_1", 0.30)
    assert rate_res["success"] is True
    assert rate_res["new_tax_rate"] == 0.30

    # Collect high tax: causes discontent
    prev_discontent = set1.discontent_level
    res2 = DomainEngine.collect_taxes(base_world, "domain_1")
    assert res2["tax_collected"] == 24  # 40 * 2.0 * 0.30 = 24G
    assert set1.discontent_level > prev_discontent


# =====================================================================
# 6. Status Briefing Tests
# =====================================================================
def test_get_domain_status_summary(base_world):
    """Verifies human-readable deterministic Korean summary output."""
    DomainEngine.claim_new_domain(base_world, "domain_1", "태양의 방패 영지")
    summary = DomainEngine.get_domain_status_summary(base_world, "domain_1")
    assert "영지 브리핑: 태양의 방패 영지" in summary
    assert "거주 인구: 25명" in summary
    assert "영주: 아르민" in summary
    assert "영지 금고: 300G" in summary


# =====================================================================
# 7. TwoPassEngine Live Turn Integration Tests
# =====================================================================
def test_two_pass_engine_claim_action_resolution(base_world):
    """Verifies player action '영지 개척 새벽녘 개척지' triggers domain claiming in Pass 1."""
    fact_sheet = TwoPassEngine.compute_pass1("영지 개척 새벽녘 개척지", base_world)
    assert fact_sheet.is_valid is True
    assert fact_sheet.domain_summary is not None
    assert "새벽녘 개척지" in fact_sheet.domain_summary
    assert any("영지 개척 선포" in log for log in fact_sheet.domain_logs)
    assert "domain_frontier_post" in base_world.pioneering_domains


def test_two_pass_engine_build_action_resolution(base_world):
    """Verifies player action '대장간 건축 착공' triggers building construction in Pass 1."""
    # First claim
    DomainEngine.claim_new_domain(base_world, "domain_frontier_post", "변경 요새")
    base_world.player.gold = 600

    fact_sheet = TwoPassEngine.compute_pass1("대장간 건축 착공", base_world)
    assert fact_sheet.domain_summary is not None
    assert any("대장간" in log for log in fact_sheet.domain_logs)
    assert base_world.player.gold < 600


def test_two_pass_engine_tax_action_resolution(base_world):
    """Verifies player action '세금 징수' collects taxes in Pass 1."""
    DomainEngine.claim_new_domain(base_world, "domain_frontier_post", "번영 요새")
    init_gold = base_world.player.gold

    fact_sheet = TwoPassEngine.compute_pass1("주민들에게 세금 징수", base_world)
    assert fact_sheet.domain_summary is not None
    assert base_world.player.gold > init_gold
    assert any("세금" in log for log in fact_sheet.domain_logs)


def test_two_pass_engine_to_prompt_context_includes_domain():
    """Verifies fact_sheet.to_prompt_context() renders domain summary instructions for LLM."""
    fs = DeterministicFactSheet(action="영지 현황 확인")
    fs.domain_summary = "=== 🏰 영지 브리핑: 솔리스 요새 ==="
    fs.domain_logs = ["🏰 대장간 완공"]

    prompt_ctx = fs.to_prompt_context()
    assert "영지 개척 및 거점 자치 통치" in prompt_ctx
    assert "솔리스 요새" in prompt_ctx
    assert "대장간 완공" in prompt_ctx
    assert "군주로서의 위엄" in prompt_ctx
