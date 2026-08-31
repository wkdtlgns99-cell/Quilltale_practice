import pytest
from src.world.graph_engine import LivingWorldGraph, PhysicsChemistryMatrix, EcologicalFeedbackLoop
from src.world.state import WorldState, Player, Location
from src.memory.memory_manager import MemoryManager


def test_living_world_graph_load():
    graph = LivingWorldGraph()
    assert len(graph.nodes) == 30, f"Expected 30 nodes, got {len(graph.nodes)}"
    
    whale_node = graph.get_regional_ecosystem("whale_belly_ecosystem")
    assert whale_node is not None
    assert "산성" in whale_node["dominant_elements"]
    assert len(whale_node["monsters"]) > 0


def test_physics_chemistry_matrix_evaluations():
    # 1. Acid + Mineral/Armor
    res1 = PhysicsChemistryMatrix.evaluate_interaction("산성 소화액 투척", "흑요석 골렘 장갑판")
    assert res1 is not None
    assert res1["rule_id"] == "acid_mineral_corrosion"
    assert res1["damage_bonus"] == 1.5

    # 2. Cold + Molten lava
    res2 = PhysicsChemistryMatrix.evaluate_interaction("극저온 빙결 마법", "용암 마그마 핵")
    assert res2 is not None
    assert res2["rule_id"] == "thermal_shock_shatter"
    assert res2["damage_bonus"] == 2.0

    # 3. Fire + Methane gas
    res3 = PhysicsChemistryMatrix.evaluate_interaction("화염구 폭발", "늪지 메탄가스 층")
    assert res3 is not None
    assert res3["rule_id"] == "methane_chain_explosion"
    assert res3["damage_bonus"] == 2.2


def test_cross_regional_synergies():
    graph = LivingWorldGraph()
    inventory = ["산호 내산 단검 (갑옷 부식 특성)", "녹슨 철검"]
    
    # In dwarf magma forge against magma golem
    synergies = graph.find_cross_regional_synergies(
        inventory_item_names=inventory,
        current_region_name="용암 폭포와 드워프 마그마 성채",
        current_monsters=["마그마 코어 중장갑 골렘"]
    )
    assert len(synergies) >= 1
    assert synergies[0]["rule"]["rule_id"] == "acid_mineral_corrosion"


def test_ecological_feedback_loop():
    state = WorldState(world_name="테스트 대륙", player=Player(name="아서"))
    
    # Trigger big explosion in swamp
    impact = EcologicalFeedbackLoop.calculate_feedback(
        action="암플리피코 이그니스 대폭발 시전",
        dice_success=True,
        current_region="끝없이 침몰하는 맹독 늪지",
        state=state
    )
    assert "잿더미 지형으로 영구 변이" in impact["terraforming"]
    assert "연기 기둥" in impact["world_news"]
    assert impact["reputation_delta"] == -5


def test_memory_manager_graph_context_integration():
    mm = MemoryManager()
    context = mm.retrieve_graph_context(
        action="극저온 냉기 화살 시전",
        location_name="용암 폭포와 드워프 마그마 성채",
        location_id="dwarf_magma_forge",
        inventory_items=["산호 내산 단검"],
        monsters=["마그마 코어 중장갑 골렘"]
    )
    assert "물리·화학적 상호작용 법칙" in context
    assert "열충격 급랭 파쇄" in context
    assert "생태계 지식 그래프" in context
