"""
Unit tests for AlcoholIntoxicationEngine in Quilltale TRPG.
Tests BAC progression, stages 1-3, User Decision Q3 companion safe escort vs solo street mugging/hypothermia,
and morning hangovers.
"""
import pytest
from src.world.state import WorldState, Player, NPC, Location
from src.world.alcohol_engine import (
    AlcoholIntoxicationEngine, AlcoholDrinkSpec, AlcoholMetabolismState, ALCOHOL_DRINK_REGISTRY
)


@pytest.fixture
def tavern_world():
    state = WorldState()
    state.locations["boar_tavern"] = Location(
        id="boar_tavern",
        name="멧돼지 주점",
        description="시끌벅적한 모험가들의 주점.",
        exits={},
        traits=["tavern", "indoor"]
    )
    state.player = Player(
        name="바드 로키",
        location="boar_tavern",
        gold=100,
        body_temperature=36.5,
        wetness=0.0
    )
    return state


def test_alcohol_specs_and_traits():
    """Verifies drink registry specs have traits and valid fields."""
    assert len(ALCOHOL_DRINK_REGISTRY) >= 4
    for d_id, spec in ALCOHOL_DRINK_REGISTRY.items():
        assert isinstance(spec, AlcoholDrinkSpec)
        assert len(spec.traits) > 0
        assert "alcohol" in spec.traits
        assert spec.bac_increase > 0.0

    st = AlcoholMetabolismState()
    assert len(st.traits) > 0
    assert "alcohol" in st.traits


def test_consume_drink_stages(tavern_world):
    """Tests drinking progresses through mellow (stage 1) to inebriated (stage 2)."""
    drinker = tavern_world.player

    # 1. First drink: Barley ale (BAC +0.03) -> Stage 1 Mellow
    success1, msg1, data1 = AlcoholIntoxicationEngine.consume_drink(
        tavern_world, drinker, "barley_ale"
    )
    assert success1 is True
    assert data1["stage"] == 1
    assert "알딸딸" in msg1

    # 2. Second drink: Spiced wine (BAC +0.06) -> BAC 0.09 -> Stage 2 Inebriated
    success2, msg2, data2 = AlcoholIntoxicationEngine.consume_drink(
        tavern_world, drinker, "spiced_wine"
    )
    assert success2 is True
    assert data2["stage"] == 2
    assert "비틀거림" in msg2


def test_blackout_solo_pickpocket_and_hypothermia(tavern_world):
    """
    User Decision Q3: Solo blackout danger!
    When drinker is alone without companions, 60% chance of pickpocket theft (30% gold),
    plus street alley hypothermia (-1.5℃ body temperature, +25% wetness).
    """
    drinker = tavern_world.player
    drinker.gold = 100
    initial_temp = drinker.body_temperature

    # Heavy drinking: Dwarven firewater x 2 (BAC 0.30) -> Stage 3 Blackout
    AlcoholIntoxicationEngine.consume_drink(tavern_world, drinker, "dwarven_firewater")
    success, msg, data = AlcoholIntoxicationEngine.consume_drink(
        tavern_world, drinker, "dwarven_firewater", fixed_theft_roll=30  # Under 60% -> Theft triggered!
    )
    assert success is True
    assert data["blackout"] is True
    assert "블랙아웃" in msg
    assert "노상 소매치기 피습" in msg
    assert drinker.gold == 59  # 100 - (8*2 drink cost) = 84 -> 30% stolen (25 gold) = 59
    assert drinker.body_temperature < initial_temp  # Hypothermia applied
    assert drinker.wetness >= 25.0


def test_blackout_with_companion_safe_escort(tavern_world):
    """
    User Decision Q3: Companion safe escort!
    When party companions are present in the same tavern, they safely escort the drinker home,
    preventing any theft or cold exposure.
    """
    drinker = tavern_world.player
    drinker.gold = 100

    # Add loyal companion in same tavern
    tavern_world.party["companion_garrick"] = NPC(
        id="companion_garrick",
        name="성기사 가릭",
        description="듬직한 성기사 동료.",
        location="boar_tavern"
    )

    # Chug dwarven firewater x 2 -> Blackout
    AlcoholIntoxicationEngine.consume_drink(tavern_world, drinker, "dwarven_firewater")
    success, msg, data = AlcoholIntoxicationEngine.consume_drink(
        tavern_world, drinker, "dwarven_firewater"
    )
    assert success is True
    assert data["blackout"] is True
    assert "동료의 든든한 호송" in msg
    assert "성기사 가릭" in msg
    # Gold safe (only drink costs deducted: 100 - 16 = 84)
    assert drinker.gold == 84
    assert drinker.wetness == 0.0  # Not abandoned in alley


def test_morning_hangover_resolution(tavern_world):
    """Tests full night of sleep metabolizes BAC to 0 and applies hangover after heavy drinking."""
    drinker = tavern_world.player
    st = AlcoholIntoxicationEngine.get_state(drinker)
    st.blood_alcohol_content = 0.12
    st.intoxication_stage = 2
    AlcoholIntoxicationEngine.sync_state(drinker, st)

    logs = AlcoholIntoxicationEngine.process_morning_hangover(drinker, hours_slept=8)
    assert len(logs) > 0
    assert any("극심한 숙취 발생" in l for l in logs)

    st_after = AlcoholIntoxicationEngine.get_state(drinker)
    assert st_after.blood_alcohol_content == 0.0
    assert st_after.has_hangover is True
    assert st_after.hangover_hours_remaining == 4
