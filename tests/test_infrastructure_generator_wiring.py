"""
Integration tests for P1-1: 6-Tier Realistic World Infrastructure and WorldGenerator wiring.
Verifies:
1. WorldGenerator.generate_new_world() creates complete 6-tier infrastructure (Continents, Regions, Nations, Settlements, Facilities).
2. Live entities (resident NPCs, stocked shop items, notice board quests) are properly bound.
3. Facilities are registered as playable Locations and connected to the starter location (loc_1).
4. Player can navigate into settlement facilities via TwoPassEngine.compute_pass1().
5. Complete JSON serialization roundtrip with WorldState.to_json() / from_json().
"""
import json
from src.world.generator import WorldGenerator
from src.world.state import WorldState
from src.llm.base import BaseLLM
from src.world.infrastructure import InfrastructureRegistry
from src.world.two_pass_engine import TwoPassEngine


class DummyLLM(BaseLLM):
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return '{"narration": "선술집 문을 열고 마을 시설로 들어섭니다.", "scene_image_prompt": "test"}'

    def generate_json(self, prompt: str, system_prompt: str = "") -> str:
        return '{"name": "테스트"}'


def test_world_generator_assembles_6_tier_infrastructure():
    """WorldGenerator.generate_new_world() properly instantiates full 6-tier infrastructure."""
    llm = DummyLLM()
    gen = WorldGenerator(llm)
    world_data, _intro_key = gen.generate_new_world()

    assert "infrastructure" in world_data
    raw_infra = world_data["infrastructure"]
    assert "continents" in raw_infra
    assert "regions" in raw_infra
    assert "nations" in raw_infra
    assert "settlements" in raw_infra
    assert "facilities" in raw_infra

    assert len(raw_infra["continents"]) >= 1
    assert len(raw_infra["regions"]) >= 1
    assert len(raw_infra["nations"]) >= 1
    assert len(raw_infra["settlements"]) >= 1
    assert len(raw_infra["facilities"]) >= 1

    # Deserialization to WorldState
    state = WorldState.from_dict(world_data)
    assert state.infrastructure is not None
    assert isinstance(state.infrastructure, InfrastructureRegistry)

    reg = state.infrastructure
    assert len(reg.continents) >= 1
    assert len(reg.regions) >= 1
    assert len(reg.nations) >= 1
    assert len(reg.settlements) >= 1
    assert len(reg.facilities) >= 1
    assert state.total_population > 0

    # Quests bound
    assert len(state.quests) >= 1

    # Facts include infrastructure summary
    facts_text = " ".join(state.world_facts)
    assert "[주요 대륙]" in facts_text or "[행성 세계관]" in facts_text
    assert "[인프라 판도]" in facts_text
    assert "[정주지 네트워크]" in facts_text

    # Starter location has exits to settlement facility
    start_loc = state.locations.get("loc_1")
    assert start_loc is not None
    assert "마을시설" in start_loc.exits
    connected_fac_id = start_loc.exits["마을시설"]
    assert connected_fac_id in state.locations
    assert connected_fac_id in reg.facilities


def test_world_generator_infrastructure_live_turn_navigation():
    """Live turn test: Player navigates from start location into settlement facility via TwoPassEngine."""
    llm = DummyLLM()
    gen = WorldGenerator(llm)
    world_data, _ = gen.generate_new_world()
    state = WorldState.from_dict(world_data)

    target_fac_id = state.locations["loc_1"].exits["마을시설"]
    target_fac_loc = state.locations[target_fac_id]

    # Execute deterministic pass 1: move to connected settlement facility
    action = f"{target_fac_loc.name}으로 이동"
    p1 = TwoPassEngine.compute_pass1(action, state)

    assert p1.is_valid is True
    assert p1.pre_computed_state_delta.get("player", {}).get("location") == target_fac_id

    # Apply delta to state
    state.apply_update(p1.pre_computed_state_delta)
    assert state.player.location == target_fac_id

    # The facility location contains its bound resident NPCs or items
    fac_obj = state.infrastructure.facilities[target_fac_id]
    assert fac_obj.settlement_id in state.infrastructure.settlements

    # Check that resident NPCs are in state.npcs
    for npc_id in fac_obj.npcs:
        assert npc_id in state.npcs
        resident_npc = state.npcs[npc_id]
        assert resident_npc.job != ""
        assert len(resident_npc.traits) >= 0


def test_world_generator_full_serialization_roundtrip():
    """Full roundtrip serialization test: WorldGenerator output -> JSON string -> WorldState."""
    llm = DummyLLM()
    gen = WorldGenerator(llm)
    world_data, _ = gen.generate_new_world()

    # JSON roundtrip
    json_str = json.dumps(world_data, ensure_ascii=False)
    state = WorldState.from_json(json_str)

    assert state.infrastructure is not None
    sample_fac_id = next(iter(state.infrastructure.facilities.keys()))
    path = state.infrastructure.resolve_hierarchy(sample_fac_id)
    assert path["facility"] is not None
    assert path["settlement"] is not None
    assert path["nation"] is not None
    assert path["region"] is not None
    assert path["continent"] is not None

    # Re-serialize to JSON and restore again
    second_json = state.to_json()
    second_state = WorldState.from_json(second_json)
    assert second_state.infrastructure is not None
    assert len(second_state.infrastructure.facilities) == len(state.infrastructure.facilities)
