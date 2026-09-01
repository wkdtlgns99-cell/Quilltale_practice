import json
import pytest
from pathlib import Path
from src.world.state import WorldState, Location
from src.world.generator import WorldGenerator


def test_arcane_physics_template_json():
    path = Path("data/templates/arcane_physics_template.json")
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        templates = json.load(f)
    assert len(templates) >= 65
    ids = [t["id"] for t in templates]
    assert "mana_depletion_arcanocraving" in ids
    assert "soul_strain_identity_fade" in ids
    assert "shadow_detachment_weightlessness" in ids
    assert "observer_collapse_focal_anchor" in ids
    assert "nomenclatural_theft" in ids
    assert "rigor_mortis_deferral" in ids
    assert "mendacity_silt_respiratory_choke" in ids


def test_arcane_laws_in_context_summary():
    state = WorldState(world_name="아케인 테스트 대륙")
    state.locations["start"] = Location(id="start", name="시작 장소", description="테스트", exits={})
    state.player.location = "start"

    state.world_lore["arcane_laws"] = [
        {
            "name": "그림자 박리 및 분리증",
            "mechanical_effect": "은신 남용 시 미끄러짐 판정"
        },
        {
            "name": "언령 축적 및 혀의 석회화",
            "mechanical_effect": "연속 영창 시 혀 결정화 및 글자수 감소"
        }
    ]

    summary = state.to_context_summary()
    assert "[🔮 이 세계의 특수 판타지 생체·물리 법칙 (Arcane Biomechanics)]" in summary
    assert "그림자 박리 및 분리증" in summary
    assert "언령 축적 및 혀의 석회화" in summary


def test_deterministic_physics_matrix_evaluation():
    from src.world.physics_matrix import PhysicsMatrixEngine

    reactions = PhysicsMatrixEngine.evaluate(
        action_text="과충전 마나를 쏟아부어 지팡이에 과부하를 건다",
        environment_text="석실 내부",
    )
    overheat = next((r for r in reactions if r.rule_id == "mana_overheat_bleed"), None)
    assert overheat is not None
    assert overheat.status_to_apply == "bleed"
    assert overheat.damage_bonus == 1.5




