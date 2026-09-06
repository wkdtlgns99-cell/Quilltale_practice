import pytest
from src.world.state import WorldState, Location, Player, NPC
from src.world.party_engine import Companion, PartyEngine
from src.world.party_sanity_engine import (
    PartySanityEngine, MentalBreakdownSpec, MENTAL_BREAKDOWN_REGISTRY, PERSONALITY_BREAKDOWN_TABLES
)
from src.world.two_pass_engine import TwoPassEngine


@pytest.fixture
def test_world():
    state = WorldState()
    state.player.location = "dark_dungeon_room"
    state.player.health = 100
    state.player.max_health = 100

    # Underground dungeon location with pitch black lighting
    loc = Location(
        id="dark_dungeon_room",
        name="어두운 던전 석실",
        description="빛 한 점 없는 어두운 지하 공간",
        exits={},
        terrain="mountains",
        location_category="dungeon",
        danger_level=60
    )
    state.locations["dark_dungeon_room"] = loc

    # Safe surface town location
    town = Location(
        id="safe_town_inn",
        name="안전한 여관",
        description="따뜻한 모닥불과 술이 있는 마을 여관",
        exits={},
        terrain="urban",
        location_category="surface",
        danger_level=10
    )
    state.locations["safe_town_inn"] = town

    # Companion: Kaelen (Cowardly scout)
    kaelen = Companion(
        companion_id="comp_kaelen",
        name_ko="카엘렌",
        title_ko="겁 많은 정찰병",
        role="scout_rogue",
        personality_type="cowardly",
        stress=0,
        max_stress=100,
        mental_status="normal"
    )
    state.party["comp_kaelen"] = kaelen

    # Companion: Valdor (Brave veteran)
    valdor = Companion(
        companion_id="comp_valdor",
        name_ko="발도르",
        title_ko="용맹한 베테랑",
        role="tank",
        personality_type="brave",
        stress=0,
        max_stress=100,
        mental_status="normal"
    )
    state.party["comp_valdor"] = valdor

    return state


def test_all_15_breakdown_specs_have_traits():
    """Verify that all 15 mental breakdown specs are registered and have traits (Rule 6)."""
    assert len(MENTAL_BREAKDOWN_REGISTRY) == 15
    for spec_id, spec in MENTAL_BREAKDOWN_REGISTRY.items():
        assert len(spec.traits) > 0
        assert spec.name_ko
        assert spec.duration > 0


def test_stress_accumulation_and_cap(test_world):
    """Test stress addition up to 100 cap and proper logging."""
    comp = test_world.party["comp_kaelen"]
    res1 = PartySanityEngine.add_stress(comp, 30, "공포스러운 비명")
    assert comp.stress == 30
    assert not res1["breakdown_triggered"]

    # Add 50 more
    res2 = PartySanityEngine.add_stress(comp, 50, "동료의 부상")
    assert comp.stress == 80
    assert not res2["breakdown_triggered"]


def test_mental_breakdown_trigger_at_100(test_world):
    """Test breakdown trigger at 100 stress, stress reset to 0, and status update."""
    comp = test_world.party["comp_kaelen"]
    comp.stress = 90

    # Add 20 stress -> reaches 100 -> triggers breakdown
    res = PartySanityEngine.add_stress(comp, 20, "치명타 피격")
    assert res["breakdown_triggered"]
    assert comp.stress == 0  # Reset on breakdown
    assert comp.mental_status != "normal"
    assert comp.breakdown_turns_remaining > 0
    assert "멘탈 붕괴" in res["breakdown_result"]["summary_ko"] or "영웅적 각성" in res["breakdown_result"]["summary_ko"]


def test_forced_breakdown_afflictions(test_world):
    """Test forced breakdown resolution for specific afflictions."""
    comp = test_world.party["comp_kaelen"]

    # Force Panic
    res_panic = PartySanityEngine.trigger_breakdown(comp, forced_id="panic")
    assert comp.mental_status == "panic"
    assert comp.breakdown_turns_remaining == 1
    assert not res_panic["is_positive"]

    # Force Heroic Awakening
    res_awakening = PartySanityEngine.trigger_breakdown(comp, forced_id="awakening")
    assert comp.mental_status == "awakening"
    assert comp.breakdown_turns_remaining == 5
    assert res_awakening["is_positive"]
    assert "각성" in res_awakening["summary_ko"]


def test_turn_based_sanity_ticks_underground_and_safe(test_world):
    """Test underground darkness stress gain and safe town stress decay."""
    comp = test_world.party["comp_kaelen"]
    comp.stress = 20

    # 1. In dark underground dungeon: gains +2 stress per turn
    test_world.player.location = "dark_dungeon_room"
    PartySanityEngine.process_turn_sanity(test_world)
    assert comp.stress == 22

    # 2. In safe town: decays -2 stress per turn
    test_world.player.location = "safe_town_inn"
    PartySanityEngine.process_turn_sanity(test_world)
    assert comp.stress == 20

    # 3. Breakdown duration decrement and natural recovery
    comp.mental_status = "freeze"
    comp.breakdown_turns_remaining = 1
    logs = PartySanityEngine.process_turn_sanity(test_world)
    assert comp.breakdown_turns_remaining == 0
    assert comp.mental_status == "normal"
    assert any("평정심을 되찾았습니다" in log for log in logs)


def test_combat_event_stress_triggers(test_world):
    """Test situational event stress triggers across all party members."""
    k = test_world.party["comp_kaelen"]
    v = test_world.party["comp_valdor"]

    # Ally near death (+15)
    PartySanityEngine.trigger_event_stress(test_world, "ally_near_death")
    assert k.stress == 15
    assert v.stress == 15

    # Trap hit (+8)
    PartySanityEngine.trigger_event_stress(test_world, "trap_hit")
    assert k.stress == 23
    assert v.stress == 23


def test_combat_action_filtering_during_breakdown(test_world):
    """Test that companions suffering from panic or freeze cannot act in combat."""
    comp = test_world.party["comp_kaelen"]
    target_npc = NPC(id="orc_foe", name="오크 전사", description="도끼를 든 흉포한 오크", health=50, location="dark_dungeon_room")

    # Normal state: can act
    comp.mental_status = "normal"
    allow_act, _ = PartySanityEngine.filter_companion_combat_intent(comp, "attack")
    assert allow_act

    # Panic state: action disabled, flees
    comp.mental_status = "panic"
    allow_panic, reason_panic = PartySanityEngine.filter_companion_combat_intent(comp, "attack")
    assert not allow_panic
    assert "도주합니다" in reason_panic

    # In actual PartyEngine combat turn, combat log records refusal
    logs = PartyEngine.process_companion_combat_turns(test_world, target_npc=target_npc)
    assert any("도주합니다" in l for l in logs)


def test_companion_save_load_backwards_compatibility():
    """Test legacy companion dictionary without stress fields deserializes with 0 defaults."""
    legacy_companion_dict = {
        "companion_id": "legacy_comp",
        "name_ko": "구버전 용병",
        "title_ko": "방랑자",
        "role": "tank",
        # stress, max_stress, mental_status are absent!
    }

    comp = Companion.from_dict(legacy_companion_dict)
    assert comp.stress == 0
    assert comp.max_stress == 100
    assert comp.mental_status == "normal"
    assert comp.breakdown_turns_remaining == 0
    assert comp.personality_type == "stoic"
    assert comp.traits == []
