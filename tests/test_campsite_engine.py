"""
Unit tests for CampsiteRestEngine in Quilltale TRPG.
Tests campsite setup, campfire mechanics, sentry shifts, perimeter trap perception contests,
and night ambush resolution with fatigue/circadian recovery.
"""
import pytest
from src.world.state import WorldState, Player, NPC, Location
from src.world.campsite_engine import (
    CampsiteRestEngine, CampsiteState, SentryShift, NightAmbushSpec, NIGHT_AMBUSH_REGISTRY
)


@pytest.fixture
def base_world():
    state = WorldState()
    state.locations["wild_forest"] = Location(
        id="wild_forest",
        name="야생의 숲",
        description="어둠과 야수가 도사리는 깊은 숲.",
        exits={},
        traits=["forest", "wilderness"]
    )
    state.player = Player(
        name="탐험가 로렌",
        location="wild_forest",
        health=40,
        max_health=50,
        stamina=20,
        max_stamina=100,
        fatigue=60,
        perception=14
    )
    state.npcs["companion_kael"] = NPC(
        id="companion_kael",
        name="용병 카엘",
        description="듬직한 용병 동료.",
        location="wild_forest",
        health=50,
        max_health=50,
        stamina=30,
        max_stamina=100,
        fatigue=50,
        perception=12
    )
    return state


def test_campsite_specs_and_traits():
    """Verifies all campsite classes and ambush specs have traits."""
    assert len(NIGHT_AMBUSH_REGISTRY) >= 4
    for a_id, spec in NIGHT_AMBUSH_REGISTRY.items():
        assert isinstance(spec, NightAmbushSpec)
        assert len(spec.traits) > 0
        assert "ambush" in spec.traits

    camp = CampsiteState(location_id="wild_forest")
    assert len(camp.traits) > 0
    assert "campsite" in camp.traits


def test_setup_campsite(base_world):
    """Tests campsite establishment with bedding and perimeter traps."""
    success, msg = CampsiteRestEngine.setup_campsite(
        base_world,
        has_tent=True,
        has_perimeter_traps=True
    )
    assert success
    assert "야영지 구축 완료" in msg
    camp = CampsiteRestEngine.get_campsite(base_world)
    assert camp is not None
    assert camp.has_tent is True
    assert camp.has_perimeter_traps is True


def test_light_campfire_and_predator_aggro(base_world):
    """Tests lighting campfire increases warmth and predator aggro rate."""
    CampsiteRestEngine.setup_campsite(base_world)
    camp = CampsiteRestEngine.get_campsite(base_world)
    initial_aggro = camp.aggro_risk

    success, msg = CampsiteRestEngine.light_campfire(base_world, duration_minutes=180)
    assert success
    assert camp.campfire_active is True
    assert camp.campfire_minutes_remaining == 180
    assert camp.aggro_risk > initial_aggro


def test_assign_sentry_shifts(base_world):
    """Tests configuring sentry shifts for party members."""
    CampsiteRestEngine.setup_campsite(base_world)
    shifts = [
        {"shift_number": 1, "companion_id": "player", "companion_name": "탐험가 로렌"},
        {"shift_number": 2, "companion_id": "companion_kael", "companion_name": "용병 카엘"},
    ]
    logs = CampsiteRestEngine.assign_sentry_shifts(base_world, shifts)
    assert len(logs) == 2
    camp = CampsiteRestEngine.get_campsite(base_world)
    assert len(camp.sentry_shifts) == 2


def test_resolve_campsite_night_safe(base_world):
    """Tests an undisturbed night: fatigue and stamina recover, sleep clock advances."""
    CampsiteRestEngine.setup_campsite(base_world, has_tent=True)
    res = CampsiteRestEngine.resolve_campsite_night(
        base_world,
        hours=8,
        bedding_id="fur_bedroll",
        fixed_ambush=False
    )
    assert res["rest_completed"] is True
    assert res["ambush_triggered"] is False
    assert any("평화로운 밤" in l for l in res["logs"])


def test_perimeter_trap_detection_and_alarm(base_world):
    """
    User Decision: Traps are NOT 100% detection.
    Intruder Perception vs Trap DC contest determines if bypassed or triggered.
    """
    CampsiteRestEngine.setup_campsite(
        base_world,
        has_tent=True,
        has_perimeter_traps=True
    )
    camp = CampsiteRestEngine.get_campsite(base_world)
    camp.perimeter_trap_detect_dc = 15

    # 1. Intruder fails perception check -> Trap is tripped and alarm rings
    res_tripped = CampsiteRestEngine.resolve_campsite_night(
        base_world,
        hours=8,
        fixed_ambush=True,
        fixed_trap_roll=3  # Low roll -> trips trap!
    )
    assert res_tripped["ambush_triggered"] is True
    assert any("방어 덫 작동" in l for l in res_tripped["logs"])
    assert res_tripped["is_surprise_attack"] is False  # Alarm alerted the camp!

    # 2. Expert infiltrator bypasses trap silently -> Sentry check needed
    res_bypassed = CampsiteRestEngine.resolve_campsite_night(
        base_world,
        hours=8,
        fixed_ambush=True,
        fixed_trap_roll=20,  # High roll -> bypasses trap
        fixed_sentry_roll=1  # Sentry fails -> surprise attack!
    )
    assert res_bypassed["ambush_triggered"] is True
    assert any("함정 간파" in l for l in res_bypassed["logs"])
    assert res_bypassed["is_surprise_attack"] is True  # Ambush succeeded!
