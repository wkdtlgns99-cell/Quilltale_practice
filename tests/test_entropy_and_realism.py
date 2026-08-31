import pytest
from src.world.graph_engine import PhysicsChemistryMatrix, EcologicalVacuumCollapse
from src.world.state import WorldState, Player, NPC, PendingInformation


def test_entropy_physical_degradation_rules():
    # 1. Confined Heat Trap
    res1 = PhysicsChemistryMatrix.evaluate_interaction("화염구 난사", "밀폐된 석실 내부")
    assert res1 is not None
    assert res1["rule_id"] == "confined_heat_trap"
    assert ("열기 축적" in res1["result_name"]) or ("열사병" in res1["tag"])

    # 2. Kinetic Recoil Strain
    res2 = PhysicsChemistryMatrix.evaluate_interaction("골렘의 초중량 철퇴 강타", "철제 방패로 막기")
    assert res2 is not None
    assert res2["rule_id"] == "kinetic_recoil_strain"
    assert "관절 과부하" in res2["result_name"]


def test_whisper_distortion_engine():
    info = PendingInformation(
        event_desc="골목길에서 도적 1명 처치",
        origin_location="alley",
        remaining_turns=1
    )
    distorted = info.distort_event()
    assert ("식인 괴물" in distorted) or ("연쇄 학살" in distorted) or ("광기의 암살자" in distorted)


def test_ecological_vacuum_collapse():
    state = WorldState(world_name="테스트 대륙")
    collapse = EcologicalVacuumCollapse.evaluate_vacuum_collapse(
        defeated_monster_name="동굴의 맹독 거미 군체",
        current_region="침묵의 동굴",
        state=state
    )
    assert collapse is not None
    assert "흡혈" in collapse["prey_surge"]
    assert "역병" in collapse["hazard_mutation"]


def test_power_vacuum_and_subservience_delta():
    state = WorldState(world_name="산적 요새")
    sub_leader = NPC(id="bandit_2nd", name="스네이크", description="산적단 2인자", location="fort")
    state.npcs["bandit_2nd"] = sub_leader

    delta = {
        "power_vacuum_reaction": {"bandit_2nd": "subservient"},
        "ecological_collapse": {"hazard_mutation": "천적이 사라진 거대 흡혈박쥐 떼 습격"}
    }

    changes = state.apply_update(delta)
    assert sub_leader.power_dynamic_state == "subservient"
    assert any("권력 역학 분기" in c for c in changes)
    assert any("생태계 진공 붕괴" in f for f in state.world_facts)
