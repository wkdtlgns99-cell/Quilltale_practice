"""
Unit tests for CaveCollapseEngine, Rock Strata, Oxygen Dynamics, and Subterranean Environmental Hazards.
"""
import pytest
from src.world.state import WorldState, Location, Player, EnvironmentalMetrics
from src.world.cave_in_engine import (
    CaveCollapseEngine, CAVE_COLLAPSE_SYSTEM, DUNGEON_ENVIRONMENT_SYSTEMS,
    ROCK_STRATA_REGISTRY, VIBRATION_SOURCES_REGISTRY, COLLAPSE_STAGES_REGISTRY,
    TOXIC_GAS_REGISTRY, WATER_QUALITY_REGISTRY, FLOOR_HAZARD_REGISTRY
)
from src.world.dungeon_engine import DungeonEngine
from src.world.two_pass_engine import TwoPassEngine


@pytest.fixture
def dungeon_world():
    state = WorldState()
    state.player.location = "dungeon_room_1"
    state.player.health = 100
    state.player.max_health = 100
    state.player.agility = 14
    state.player.constitution = 12
    state.environment.oxygen_level = 100

    loc = Location(
        id="dungeon_room_1",
        name="지하 석실 B1F",
        description="축축한 지하 석실입니다.",
        exits={"forward": "dungeon_room_2"},
        location_category="dungeon",
        floor_depth=1,
        rock_strata="limestone",
        structural_integrity=70.0,
        collapse_stage="stable",
        floor_type="solid_rock",
        floor_durability=100.0,
        traits=["지하 던전", "밀실", "습기"]
    )
    state.locations["dungeon_room_1"] = loc

    return state


def test_rock_strata_specs_and_registries():
    """Verify master rock strata data is correctly registered with traits."""
    assert len(ROCK_STRATA_REGISTRY) >= 5
    for strata_id in ["limestone", "granite", "sandstone", "basalt", "obsidian"]:
        assert strata_id in ROCK_STRATA_REGISTRY
        spec = ROCK_STRATA_REGISTRY[strata_id]
        assert spec.base_durability > 0
        assert spec.vibration_resistance > 0
        assert len(spec.traits) > 0

    granite = ROCK_STRATA_REGISTRY["granite"]
    assert granite.vibration_resistance == 90
    assert granite.collapse_risk == "low"

    obsidian = ROCK_STRATA_REGISTRY["obsidian"]
    assert obsidian.magic_damage_multiplier == 2.0


def test_vibration_impact_and_stage_transitions(dungeon_world):
    """Verify vibration damages structural integrity and transitions stages."""
    state = dungeon_world
    loc = state.locations["dungeon_room_1"]
    loc.rock_strata = "limestone"
    loc.structural_integrity = 70.0

    # 1. Fireball impact (circle 3)
    rem_dur, stage, logs = CaveCollapseEngine.apply_vibration(
        loc, "fireball_explosion", magic_circle=3, state=state
    )
    assert rem_dur < 70.0
    assert loc.structural_integrity == rem_dur
    assert any("암반 충격 진동" in l for l in logs)

    # 2. Force reduction to cracking
    loc.structural_integrity = 50.0
    loc.collapse_stage = "cracking"
    rem_dur, stage, logs = CaveCollapseEngine.apply_vibration(
        loc, "fireball_explosion", magic_circle=4, state=state
    )
    # Stage should progress towards partial_collapse
    assert loc.structural_integrity < 50.0

    # 3. Test catastrophic full collapse
    loc.structural_integrity = 10.0
    loc.collapse_stage = "partial_collapse"
    rem_dur, stage, logs = CaveCollapseEngine.apply_vibration(
        loc, "trap_activation", magnitude_override=50.0, state=state
    )
    assert rem_dur <= 0.0
    assert stage == "full_collapse"
    assert any("전면 대붕괴" in l for l in logs)


def test_obsidian_magic_susceptibility(dungeon_world):
    """Verify obsidian rock takes double damage from magical explosions."""
    loc_obsidian = Location(
        id="obsidian_room",
        name="흑요석 석실",
        description="검은 유리질 흑요석으로 둘러싸인 방",
        exits={},
        location_category="dungeon",
        rock_strata="obsidian",
        structural_integrity=85.0
    )
    dungeon_world.locations["obsidian_room"] = loc_obsidian

    CaveCollapseEngine.apply_vibration(loc_obsidian, "fireball_explosion", magic_circle=2, state=dungeon_world)
    # circle 2 impact is 20, vibration resistance 60 -> 20 * (100/60) = 33.3 * 2.0 (magic mult) = ~66.7
    assert loc_obsidian.structural_integrity < 30.0


def test_oxygen_depletion_and_hypoxia_stages(dungeon_world):
    """Verify turn-based oxygen consumption and hypoxia health damage."""
    state = dungeon_world
    loc = state.locations["dungeon_room_1"]

    # Initial 100%
    state.environment.oxygen_level = 100
    state.player.inventory.append("torch")

    # Turn 1
    logs = CaveCollapseEngine.process_turn_environment(state)
    assert state.environment.oxygen_level < 100

    # Test Mild Hypoxia (75%)
    state.environment.oxygen_level = 75
    logs = CaveCollapseEngine.process_turn_environment(state)
    assert any("경도 저산소증" in l for l in logs)

    # Test Moderate Hypoxia (60%)
    state.environment.oxygen_level = 60
    logs = CaveCollapseEngine.process_turn_environment(state)
    assert any("중등도 저산소증" in l for l in logs)

    # Test Severe Hypoxia (40%)
    state.environment.oxygen_level = 40
    prev_hp = state.player.health
    logs = CaveCollapseEngine.process_turn_environment(state)
    assert any("중증 저산소증" in l for l in logs)
    assert state.player.health < prev_hp

    # Test Suffocation (20%)
    state.environment.oxygen_level = 20
    prev_hp = state.player.health
    logs = CaveCollapseEngine.process_turn_environment(state)
    assert any("치명적 질식" in l for l in logs)
    assert state.player.health == prev_hp - 15


def test_ventilation_shaft_opening(dungeon_world):
    """Verify opening ventilation shaft increases oxygen level per turn."""
    state = dungeon_world
    loc = state.locations["dungeon_room_1"]
    state.environment.oxygen_level = 50

    success, msg = CaveCollapseEngine.open_ventilation(loc)
    assert success is True
    assert loc.ventilation_open is True

    # Process turn with ventilation open: party(1) -> -0.2, ventilation -> +2.0 => net positive
    CaveCollapseEngine.process_turn_environment(state)
    assert state.environment.oxygen_level > 50


def test_toxic_gas_exposure(dungeon_world):
    """Verify toxic gas triggers Constitution check and appropriate damage."""
    state = dungeon_world
    loc = state.locations["dungeon_room_1"]
    loc.active_toxic_gas = "sulfur_gas"
    state.player.constitution = 8  # low CON, modifier -1 -> roll 9 < DC 15

    prev_hp = state.player.health
    logs = CaveCollapseEngine.process_turn_environment(state)
    assert any("황화 가스" in l for l in logs)
    assert state.player.health < prev_hp


def test_underground_water_purification():
    """Verify water purification methods deterministically transform water quality."""
    # Holy purification
    res_type, msg, safe = CaveCollapseEngine.purify_water("corpse_contaminated", "holy_purification")
    assert res_type == "clean"
    assert safe is True

    # Boiling contaminated water
    res_type, msg, safe = CaveCollapseEngine.purify_water("stagnant", "boiling")
    assert res_type == "clean"
    assert safe is True

    # Boiling mineral toxic water fails
    res_type, msg, safe = CaveCollapseEngine.purify_water("mineral_toxic", "boiling")
    assert res_type == "mineral_toxic"
    assert safe is False

    # Filtering mineral toxic water succeeds
    res_type, msg, safe = CaveCollapseEngine.purify_water("mineral_toxic", "filtering")
    assert res_type == "clean"
    assert safe is True


def test_backward_compatibility_deserialization():
    """Verify old JSON without new subterranean fields deserializes with correct defaults."""
    raw_loc = {
        "id": "old_room",
        "name": "오래된 방",
        "description": "구버전 데이터",
        "exits": {}
    }
    raw_state = {
        "player": {"location": "old_room"},
        "locations": {"old_room": raw_loc}
    }
    loaded_state = WorldState.from_dict(raw_state)
    loc = loaded_state.locations["old_room"]
    assert loc.rock_strata == "granite"
    assert loc.structural_integrity == 100.0
    assert loc.collapse_stage == "stable"
    assert loc.floor_type == "solid_rock"
    assert loc.ventilation_open is False
    assert loc.water_quality == "clean"


def test_two_pass_engine_dungeon_collapse_integration(dungeon_world):
    """Verify TwoPassEngine executes environmental ticks and ventilation interaction."""
    state = dungeon_world

    # Ventilation interaction in dungeon room
    fs = TwoPassEngine.compute_pass1("환기구를 열어 신선한 공기를 유입시킨다", state)
    loc = state.locations["dungeon_room_1"]
    assert loc.ventilation_open is True
    assert any("환기구 개방" in l for l in fs.status_tick_logs)
