import json
import pytest
from pathlib import Path
from src.world.graph_engine import PhysicsChemistryMatrix
from src.world.state import WorldState, Player, NPC, Location
from src.world.validator import ActionValidator


def test_realism_mechanics_template_json():
    path = Path("data/templates/realism_mechanics_template.json")
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        templates = json.load(f)
    assert len(templates) >= 15
    ids = [t["id"] for t in templates]
    assert "closed_loop_ecosystem" in ids
    assert "material_physics_chemical_chain" in ids
    assert "sensory_occlusion_blind_spots" in ids
    assert "spatial_ergonomics_encumbrance" in ids
    assert "morale_surrender_threshold" in ids
    assert "linguistic_cultural_friction" in ids


def test_advanced_physics_and_physiological_matrix():
    # 1. Wet Conductive Spread
    res1 = PhysicsChemistryMatrix.evaluate_interaction("번개 마법 시전", "비에 젖은 적과 물 웅덩이")
    assert res1 is not None
    assert res1["rule_id"] == "wet_conductive_spread"
    assert "초전도 확산" in res1["result_name"]

    # 2. Oil Flame Wall
    res2 = PhysicsChemistryMatrix.evaluate_interaction("불꽃 투척", "바닥의 기름 웅덩이")
    assert res2 is not None
    assert res2["rule_id"] == "oil_flame_wall"

    # 3. Spatial Weapon Interference
    res3 = PhysicsChemistryMatrix.evaluate_interaction("대검 휘두르기", "좁은 동굴 벽면")
    assert res3 is not None
    assert res3["rule_id"] == "spatial_weapon_interference"

    # 4. Blade Dulling
    res4 = PhysicsChemistryMatrix.evaluate_interaction("도검 참격", "적의 두꺼운 판금 갑옷")
    assert res4 is not None
    assert res4["rule_id"] == "blade_dulling_armor"


def test_validator_spatial_and_suffocation_flags():
    state = WorldState(world_name="검증 테스트")
    state.locations["cave_narrow"] = Location(
        id="cave_narrow",
        name="비좁은 종유석 동굴",
        description="성인 한 명이 간신히 지나갈 만큼 비좁은 암벽 통로다.",
        exits={"out": "start"}
    )
    state.player.location = "cave_narrow"

    # Action targeting narrow space with greatsword
    is_valid, msg, dice_res, flags = ActionValidator.pre_validate_action(
        "양손에 든 거대한 대검을 크게 휘둘러 적을 벤다",
        state
    )
    assert flags.get("spatial_jam_risk") is True

    # Underwater incantation suffocation check
    state.environment.weather = "수중"
    is_valid_2, msg_2, dice_res_2, flags_2 = ActionValidator.pre_validate_action(
        "물속에서 크게 소리쳐 화염 영창 주문을 외운다",
        state
    )
    assert flags_2.get("suffocation_risk") is True


def test_state_morale_hygiene_temperature_deltas():
    state = WorldState(world_name="심리 및 인체 테스트")
    npc = NPC(id="goblin_warrior", name="고블린 전사", description="졸개", location="cave")
    state.npcs["goblin_warrior"] = npc

    delta = {
        "update_npc_morale": {"goblin_warrior": -60},
        "update_hygiene": -40,
        "update_body_temperature": -2.5
    }

    changes = state.apply_update(delta)
    assert npc.morale == 40  # 100 - 60
    assert state.player.hygiene_level == 60  # 100 - 40
    assert state.player.body_temperature == 34.0  # 36.5 - 2.5
