import pytest
from src.world.state import WorldState, Player, NPC, Item, Location
from src.world.validator import ActionValidator
from src.world.two_pass_engine import TwoPassEngine
from src.world.injury_engine import InjuryEngine, InjurySeverity


@pytest.fixture
def injury_world():
    state = WorldState()
    loc = Location(id="clinic", name="마을 진료소", description="약초 냄새가 풍기는 진료소", exits={})
    state.locations["clinic"] = loc
    state.player.location = "clinic"
    state.player.gold = 100
    state.player.health = 50
    state.player.max_health = 100
    state.player.fatigue = 50

    # Medical items
    state.items["potion_red"] = Item(
        id="potion_red", name="빨간 회복 물약", description="", location="inventory",
        item_type="consumable", value=15
    )
    state.items["bandage_linen"] = Item(
        id="bandage_linen", name="리넨 붕대", description="", location="inventory",
        item_type="consumable", properties={"bandage": True}, value=5
    )
    state.items["splint_wood"] = Item(
        id="splint_wood", name="나무 부목", description="", location="inventory",
        item_type="consumable", properties={"splint": True}, value=20
    )

    state.player.inventory = ["potion_red", "bandage_linen", "splint_wood"]

    # Doctor NPC
    doctor = NPC(
        id="npc_doctor", name="외과의 파레", description="노련한 마을 외과의이자 치료사",
        location="clinic", health=60, max_health=60
    )
    state.npcs["npc_doctor"] = doctor
    loc.npcs = ["npc_doctor"]

    return state


def test_potion_cannot_heal_bone_fracture_anti_yes_man(injury_world):
    injury_world.player.injuries = ["다리 골절/힘줄 파열"]

    # Player tries to drink potion to heal bone fracture
    valid, msg, _, _ = ActionValidator.pre_validate_action("빨간 회복 물약으로 다리 골절을 치료한다", injury_world)
    assert valid is False
    assert "골절 치료 불가" in msg or "부러진 뼈" in msg
    assert "다리 골절/힘줄 파열" in injury_world.player.injuries


def test_bandage_cannot_heal_severe_fracture(injury_world):
    injury_world.player.injuries = ["다리 골절/힘줄 파열"]

    # Simple bandage is not a splint
    valid, msg, _, _ = ActionValidator.pre_validate_action("리넨 붕대로 다리 골절을 감싸 치료한다", injury_world)
    assert valid is False
    assert "부목" in msg or "고정할 수 없습니다" in msg


def test_bandage_cures_light_injury(injury_world):
    injury_world.player.injuries = ["팔 타박상"]

    valid, msg, _, flags = ActionValidator.pre_validate_action("리넨 붕대로 팔 타박상을 감싸 치료한다", injury_world)
    assert valid is True
    assert flags.get("treatment_intent") is not None

    fact_sheet = TwoPassEngine.compute_pass1("리넨 붕대로 팔 타박상을 감싸 치료한다", injury_world)
    assert fact_sheet.is_valid is True
    assert "remove_player_injury" in fact_sheet.pre_computed_state_delta

    injury_world.apply_update(fact_sheet.pre_computed_state_delta)
    # Injury removed, bandage consumed
    assert "팔 타박상" not in injury_world.player.injuries
    assert "bandage_linen" not in injury_world.player.inventory


def test_splint_and_rest_heals_fracture(injury_world):
    injury_world.player.injuries = ["다리 골절/힘줄 파열"]

    valid, msg, _, flags = ActionValidator.pre_validate_action("나무 부목을 대고 다리 골절을 고정한다", injury_world)
    assert valid is True
    assert flags["treatment_intent"]["type"] == "item"

    fact_sheet = TwoPassEngine.compute_pass1("나무 부목을 대고 다리 골절을 고정한다", injury_world)
    injury_world.apply_update(fact_sheet.pre_computed_state_delta)

    # Fracture is now splinted (still in injuries, but tracking rest turns)
    assert "splint_wood" not in injury_world.player.inventory
    assert len(injury_world.player.splinted_injuries) > 0

    # Rest turn 1 (reduce fatigue)
    injury_world.apply_update({"fatigue_delta": -20})
    assert "다리 골절/힘줄 파열" in injury_world.player.injuries  # Still needs 1 more rest

    # Rest turn 2 (reduce fatigue) -> Healed!
    injury_world.apply_update({"fatigue_delta": -20})
    assert "다리 골절/힘줄 파열" not in injury_world.player.injuries
    assert len(injury_world.player.splinted_injuries) == 0


def test_doctor_npc_surgery_success(injury_world):
    injury_world.player.injuries = ["다리 골절/힘줄 파열"]
    assert injury_world.player.gold == 100

    valid, msg, _, flags = ActionValidator.pre_validate_action("외과의에게 다리 골절 수술을 부탁한다", injury_world)
    assert valid is True
    assert flags["treatment_intent"]["type"] == "doctor"

    fact_sheet = TwoPassEngine.compute_pass1("외과의에게 다리 골절 수술을 부탁한다", injury_world)
    assert "remove_player_injury" in fact_sheet.pre_computed_state_delta

    injury_world.apply_update(fact_sheet.pre_computed_state_delta)
    # 50 gold fee deducted, fracture instantly cured
    assert injury_world.player.gold == 50
    assert "다리 골절/힘줄 파열" not in injury_world.player.injuries


def test_doctor_refuses_if_poor(injury_world):
    injury_world.player.injuries = ["다리 골절/힘줄 파열"]
    injury_world.player.gold = 10  # Poor

    doc = injury_world.npcs["npc_doctor"]
    success, msg, _ = InjuryEngine.apply_doctor_surgery(injury_world, doc, injury_world.player, "다리 골절/힘줄 파열", fee=50)
    assert success is False
    assert "부족" in msg
