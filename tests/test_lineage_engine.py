"""
Tests for Dynasty Lineage & Heir Succession Engine (lineage_engine.py)
and TwoPassEngine integration.
"""
import pytest

from src.world.state import WorldState, Player, Location
from src.world.domain_engine import DomainEngine
from src.world.lineage_engine import (
    LineageEngine,
    BloodlineTrait,
    FamilyMember,
    DynastyLineageState,
    InheritanceReport,
    BLOODLINE_TRAITS_CATALOG,
)
from src.world.two_pass_engine import TwoPassEngine, DeterministicFactSheet


@pytest.fixture
def base_world():
    """Initializes a minimal WorldState with a starting location and player."""
    state = WorldState()
    loc = Location(id="capital_city", name="수도 성도", description="제국의 수도", exits={})
    state.locations["capital_city"] = loc
    state.player = Player(name="아르민", health=100, max_health=100, gold=1000)
    state.player.location = "capital_city"
    return state


# =====================================================================
# 1. Data Model & Rule 5 (traits) Tests
# =====================================================================
def test_bloodline_trait_model_traits():
    """Verifies BloodlineTrait includes traits list per Rule 5."""
    trait = BloodlineTrait(
        trait_id="dragon_blood",
        name="고대 용의 혈통",
        stat_modifiers={"max_health": 30},
        traits=["용족", "체력증가"],
    )
    assert trait.traits == ["용족", "체력증가"]
    d = trait.to_dict()
    assert d["traits"] == ["용족", "체력증가"]
    restored = BloodlineTrait.from_dict(d)
    assert restored.traits == ["용족", "체력증가"]


def test_family_member_model_traits():
    """Verifies FamilyMember includes traits list per Rule 5."""
    member = FamilyMember(
        member_id="member_1",
        name="엘레나 아르민",
        generation=2,
        role="heir",
        traits=["후계자", "마법사"],
    )
    assert member.traits == ["후계자", "마법사"]
    d = member.to_dict()
    assert d["traits"] == ["후계자", "마법사"]
    restored = FamilyMember.from_dict(d)
    assert restored.traits == ["후계자", "마법사"]


def test_dynasty_lineage_state_model_traits():
    """Verifies DynastyLineageState includes traits list per Rule 5."""
    dynasty = DynastyLineageState(
        dynasty_name="윈터펠 가문",
        motto="겨울이 오고 있다",
        traits=["북부명가"],
    )
    assert dynasty.traits == ["북부명가"]
    d = dynasty.to_dict()
    assert d["traits"] == ["북부명가"]
    restored = DynastyLineageState.from_dict(d)
    assert restored.dynasty_name == "윈터펠 가문"


def test_inheritance_report_model_traits():
    """Verifies InheritanceReport includes traits list per Rule 5."""
    report = InheritanceReport(
        predecessor_name="아르민",
        successor_name="에단",
        new_generation=2,
        traits=["가주이양", "제2대"],
    )
    assert report.traits == ["가주이양", "제2대"]
    d = report.to_dict()
    assert d["traits"] == ["가주이양", "제2대"]
    restored = InheritanceReport.from_dict(d)
    assert restored.successor_name == "에단"


# =====================================================================
# 2. Dynasty Founding Tests
# =====================================================================
def test_initialize_dynasty(base_world):
    """Verifies founding a noble dynasty with player as 1st generation head."""
    dynasty = LineageEngine.initialize_dynasty(
        state=base_world,
        dynasty_name="루멘 가문",
        motto="빛으로 어둠을 가른다",
        starter_trait_keys=["titan_physique", "indomitable_will"],
    )
    assert dynasty.dynasty_name == "루멘 가문"
    assert dynasty.current_generation == 1
    assert dynasty.current_head_id in dynasty.family_tree

    founder = dynasty.family_tree[dynasty.current_head_id]
    assert founder.name == "아르민"
    assert founder.role == "head"
    assert founder.is_active_player is True
    assert len(founder.bloodline_traits) == 2

    # Check player stat buffs from starter traits
    assert base_world.player.max_health >= 120
    assert base_world.dynasty_lineage == dynasty


# =====================================================================
# 3. Heir Candidate Generation & Designation Tests
# =====================================================================
def test_generate_heir_candidates_and_designate(base_world):
    """Verifies generating heir candidates and designating the official heir."""
    LineageEngine.initialize_dynasty(base_world, "루멘 가문")

    candidates = LineageEngine.generate_heir_candidates(base_world, count=3)
    assert len(candidates) == 3
    assert candidates[0].generation == 2
    assert candidates[0].role == "heir"

    # Verify dynasty has auto-designated or can manually designate
    dynasty = base_world.dynasty_lineage
    assert dynasty.designated_heir_id is not None

    # Manually designate second candidate
    target_id = candidates[1].member_id
    res = LineageEngine.designate_heir(base_world, target_id)
    assert res["success"] is True
    assert dynasty.designated_heir_id == target_id
    assert res["heir_name"] == candidates[1].name


# =====================================================================
# 4. Voluntary Headship Transfer Tests (No death/retirement required!)
# =====================================================================
def test_transfer_headship_voluntary(base_world):
    """
    Verifies voluntary headship transfer to designated heir:
    - Previous head is preserved as an honored elder (alive).
    - Successor becomes active player character.
    - Domain sovereignty transfers to successor.
    """
    # 1. Setup dynasty and domain
    LineageEngine.initialize_dynasty(base_world, "솔리스 가문")
    DomainEngine.claim_new_domain(base_world, "solis_fort", "솔리스 성채")
    candidates = LineageEngine.generate_heir_candidates(base_world, count=2)
    heir = candidates[0]
    LineageEngine.designate_heir(base_world, heir.member_id)

    # 2. Execute voluntary transfer
    report = LineageEngine.transfer_headship(base_world)
    assert report.predecessor_name == "아르민"
    assert report.successor_name == heir.name
    assert report.new_generation == 2

    # 3. Verify active player identity switched
    assert base_world.player.name == heir.name

    # 4. Verify previous head is now elder and still alive in tree
    dynasty = base_world.dynasty_lineage
    old_head = dynasty.family_tree["member_gen1_head"]
    assert old_head.role == "elder"
    assert old_head.is_active_player is False
    assert "원로" in old_head.traits

    # 5. Verify domain leadership transferred
    pstate = base_world.pioneering_domains["solis_fort"]
    assert pstate.pioneer_leader_id == heir.name


# =====================================================================
# 5. Ancestral Heirloom Registration Tests
# =====================================================================
def test_add_ancestral_heirloom(base_world):
    """Verifies registering a weapon/relic as an ancestral family heirloom."""
    LineageEngine.initialize_dynasty(base_world, "루멘 가문")
    base_world.player.inventory.append("holy_avenger_sword")

    res = LineageEngine.add_ancestral_heirloom(base_world, "holy_avenger_sword")
    assert res["success"] is True
    assert res["prestige_bonus"] == 15

    dynasty = base_world.dynasty_lineage
    assert len(dynasty.ancestral_heirlooms) == 1
    assert dynasty.dynasty_prestige > 150


# =====================================================================
# 6. Status Summary Briefing Tests
# =====================================================================
def test_get_lineage_status_summary(base_world):
    """Verifies deterministic Korean status summary output."""
    LineageEngine.initialize_dynasty(base_world, "황금 사자 가문", motto="포효하는 자가 지배한다")
    summary = LineageEngine.get_lineage_status_summary(base_world)
    assert "가문 혈통 브리핑: 황금 사자 가문" in summary
    assert "포효하는 자가 지배한다" in summary
    assert "현직 가주: 아르민" in summary


# =====================================================================
# 7. TwoPassEngine Live Turn Integration Tests
# =====================================================================
def test_two_pass_engine_found_action_resolution(base_world):
    """Verifies player action '가문 창설 드래곤본 가문' triggers founding in Pass 1."""
    fact_sheet = TwoPassEngine.compute_pass1("가문 창설 드래곤본 가문", base_world)
    assert fact_sheet.is_valid is True
    assert fact_sheet.lineage_summary is not None
    assert "드래곤본 가문" in fact_sheet.lineage_summary
    assert any("가문 창설 선포" in log for log in fact_sheet.lineage_logs)
    assert base_world.dynasty_lineage is not None


def test_two_pass_engine_candidates_action_resolution(base_world):
    """Verifies player action '후계자 후보 확인' lists candidates in Pass 1."""
    LineageEngine.initialize_dynasty(base_world, "드래곤본 가문")
    fact_sheet = TwoPassEngine.compute_pass1("가문 후계자 후보 확인", base_world)
    assert fact_sheet.lineage_summary is not None
    assert any("가문 후계자 후보 명부" in log for log in fact_sheet.lineage_logs)


def test_two_pass_engine_designate_action_resolution(base_world):
    """Verifies player action '후계자 지명' designates heir in Pass 1."""
    LineageEngine.initialize_dynasty(base_world, "드래곤본 가문")
    fact_sheet = TwoPassEngine.compute_pass1("후계자 지명 에단", base_world)
    assert fact_sheet.lineage_summary is not None
    assert any("지명했습니다" in log for log in fact_sheet.lineage_logs)


def test_two_pass_engine_transfer_action_resolution(base_world):
    """Verifies player action '가주 이양' transfers headship in Pass 1."""
    LineageEngine.initialize_dynasty(base_world, "드래곤본 가문")
    fact_sheet = TwoPassEngine.compute_pass1("가주 이양", base_world)
    assert fact_sheet.lineage_summary is not None
    assert any("가주 이양이 완수되었습니다" in log for log in fact_sheet.lineage_logs)


def test_two_pass_engine_to_prompt_context_includes_lineage():
    """Verifies fact_sheet.to_prompt_context() renders lineage summary instructions for LLM."""
    fs = DeterministicFactSheet(action="가문 현황 점검")
    fs.lineage_summary = "=== 🛡️ 가문 혈통 브리핑: 윈터펠 가문 ==="
    fs.lineage_logs = ["🛡️ 에단 후계자 지명"]

    prompt_ctx = fs.to_prompt_context()
    assert "가문 혈통 및 가계도 위계" in prompt_ctx
    assert "윈터펠 가문" in prompt_ctx
    assert "에단 후계자 지명" in prompt_ctx
    assert "명문 가문의 품격" in prompt_ctx
