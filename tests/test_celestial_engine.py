import pytest
from src.world.state import WorldState, Player
from src.world.celestial_engine import CelestialEngine


def test_celestial_cycle_trigger_blood_moon():
    state = WorldState(session_id="test_celestial", player=Player(), turn=25)
    
    logs = CelestialEngine.advance_celestial_turn(state)
    assert any("붉은 달" in l for l in logs)
    assert state.celestial_phase == "celestial_blood_moon"
    assert state.celestial_phase_turns == 3

    mods = CelestialEngine.get_active_modifiers(state)
    assert mods["monster_attack_mult"] == 1.5


def test_festival_harvest_discount():
    state = WorldState(session_id="test_festival", player=Player(), turn=30)
    
    logs = CelestialEngine.advance_celestial_turn(state)
    assert any("수확제" in l for l in logs)
    assert state.active_festival == "festival_harvest_bounty"

    mods = CelestialEngine.get_active_modifiers(state)
    assert mods["shop_discount"] == 0.3
