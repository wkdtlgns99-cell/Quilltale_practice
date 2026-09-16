"""
P2-1 God Method Decomposition Verification Test Suite.
Tests modularized sub-methods and end-to-end orchestration for:
- WorldState.apply_update() (5 sub-dispatchers)
- ActionValidator.pre_validate_action() (5 sub-validators)
"""
import pytest
from src.world.state import WorldState, Location, Item
from src.world.validator import ActionValidator


@pytest.fixture
def clean_state():
    with open("data/worlds/default.json", encoding="utf-8") as f:
        state = WorldState.from_json(f.read())
    # Ensure items exist
    state.items["item_potion_1"] = Item(
        id="item_potion_1",
        name="회복 물약",
        description="마시면 생명력이 회복되는 붉은 물약",
        item_type="consumable",
        location="player",
    )
    state.player.inventory.append("item_potion_1")
    state.items["item_sword_99"] = Item(
        id="item_sword_99",
        name="미보유 전설검",
        description="어디에도 없는 전설검",
        item_type="weapon",
        location="loc_nowhere",
    )
    return state


# =========================================================================
# 1. WorldState.apply_update Sub-Method & Orchestration Tests
# =========================================================================

def test_world_state_apply_player_updates(clean_state):
    """Verify _apply_player_updates modifies movement, stats, and records changes."""
    changes = []
    initial_gold = clean_state.player.gold
    update_data = {
        "move_player": "north",
        "add_gold": 50,
    }
    clean_state._apply_player_updates(update_data, changes)
    assert clean_state.player.location == "street"
    assert clean_state.player.gold == initial_gold + 50
    assert any("moved" in c for c in changes)
    assert any("Gold changed" in c for c in changes)


def test_world_state_apply_inventory_and_equipment_updates(clean_state):
    """Verify _apply_inventory_and_equipment_updates drops/picks items."""
    changes = []
    clean_state.player.inventory.append("item_temp")
    clean_state.items["item_temp"] = Item(
        id="item_temp",
        name="임시 아이템",
        description="임시",
        item_type="material",
        location="player",
    )
    update_data = {
        "drop_item": "item_temp",
    }
    clean_state._apply_inventory_and_equipment_updates(update_data, changes)
    assert "item_temp" not in clean_state.player.inventory
    assert any("dropped" in c for c in changes)


def test_world_state_apply_npc_updates(clean_state):
    """Verify _apply_npc_updates updates NPC state and reveals."""
    changes = []
    npc_id = list(clean_state.npcs.keys())[0]
    update_data = {
        "npc_state": {npc_id: {"disposition": "hostile", "alive": False}},
    }
    clean_state._apply_npc_updates(update_data, changes)
    assert clean_state.npcs[npc_id].disposition == "hostile"
    assert clean_state.npcs[npc_id].alive is False


def test_world_state_apply_world_environment_updates(clean_state):
    """Verify _apply_world_environment_updates adds facts and environment entries."""
    changes = []
    update_data = {
        "add_fact": "북쪽 거리에 경비대가 증원되었다.",
    }
    clean_state._apply_world_environment_updates(update_data, changes)
    assert "북쪽 거리에 경비대가 증원되었다." in clean_state.world_facts
    assert any("사실" in c or "Fact" in c or "증원" in c for c in changes)


def test_world_state_apply_subsystem_engine_deltas(clean_state):
    """Verify _apply_subsystem_engine_deltas updates ecological collapse."""
    changes = []
    update_data = {
        "ecological_collapse": {
            "hazard_mutation": "독기 늪지대로 변이",
            "location_id": "tavern"
        }
    }
    clean_state._apply_subsystem_engine_deltas(update_data, changes)
    assert any("[생태계 진공 붕괴]" in f for f in clean_state.world_facts)
    assert any("생태계 연쇄 붕괴" in c for c in changes)


def test_world_state_apply_update_full_orchestration(clean_state):
    """Verify apply_update coordinates all 5 domains cleanly."""
    initial_gold = clean_state.player.gold
    composite_update = {
        "move_player": "north",
        "add_gold": 10,
        "add_fact": "광장에 새로운 소문이 돈다.",
    }
    changes = clean_state.apply_update(composite_update)
    assert clean_state.player.location == "street"
    assert clean_state.player.gold == initial_gold + 10
    assert "광장에 새로운 소문이 돈다." in clean_state.world_facts
    assert len(changes) >= 3


# =========================================================================
# 2. ActionValidator.pre_validate_action Sub-Method & Orchestration Tests
# =========================================================================

def test_validator_physical_blocks(clean_state):
    """Verify _validate_physical_blocks rejects power scaling impossibility and checks injuries."""
    flags = {}
    curr_loc = clean_state.current_location()

    # 1. Impossible power check (matches IMPOSSIBLE_POWER_PATTERNS)
    err = ActionValidator._validate_physical_blocks(
        "지구를 파괴한다", "지구를 파괴한다", clean_state, curr_loc, flags
    )
    assert err is not None
    assert "불가능한 행동" in err

    # 2. Normal valid action
    err_valid = ActionValidator._validate_physical_blocks(
        "주변을 살핀다", "주변을 살핀다", clean_state, curr_loc, flags
    )
    assert err_valid is None


def test_validator_inventory_and_equipment(clean_state):
    """Verify _validate_inventory_and_equipment blocks using unowned items."""
    flags = {}
    curr_loc = clean_state.current_location()

    # Attempt to equip item not owned
    err = ActionValidator._validate_inventory_and_equipment(
        "미보유 전설검을 착용한다", clean_state, curr_loc, flags
    )
    assert err is not None
    assert "존재하지 않는" in err

    # Valid owned item
    err_valid = ActionValidator._validate_inventory_and_equipment(
        "회복 물약을 마신다", clean_state, curr_loc, flags
    )
    assert err_valid is None


def test_validator_target_and_interaction(clean_state):
    """Verify _validate_target_and_interaction blocks talking to dead NPCs."""
    flags = {}
    curr_loc = clean_state.current_location()
    dead_npc = list(clean_state.npcs.values())[0]
    dead_npc.alive = False

    # Dead NPC dialogue block
    err = ActionValidator._validate_target_and_interaction(
        f"{dead_npc.name}에게 말을 건넨다", clean_state, curr_loc, flags
    )
    assert err is not None
    assert "싸늘하게 식어버린" in err


def test_validator_spatial_and_physical_limits(clean_state):
    """Verify _validate_spatial_and_physical_limits flags narrow space long weapon risk."""
    cave_loc = Location(
        id="loc_cave_narrow",
        name="비좁은 바위 통로",
        description="몸을 웅크려야 지나갈 수 있는 좁은 석실이자 동굴입니다.",
        traits=["underground", "narrow"],
        exits={},
    )
    clean_state.locations["loc_cave_narrow"] = cave_loc
    clean_state.player.location = "loc_cave_narrow"
    flags = {}

    err = ActionValidator._validate_spatial_and_physical_limits(
        "대검을 크게 휘두른다", clean_state, cave_loc, flags
    )
    assert err is None
    assert flags.get("spatial_jam_risk") is True


def test_validator_dispatch_action_challenges(clean_state):
    """Verify _dispatch_action_challenges performs deterministic combat dice roll."""
    flags = {}
    curr_loc = clean_state.current_location()
    target_part = ""
    parsed = {"action": "적을 단검으로 공격한다", "dialogue": "", "monologue": "", "raw": ""}

    success, err_msg, dice_res = ActionValidator._dispatch_action_challenges(
        "적을 단검으로 공격한다", "적을 단검으로 공격한다", clean_state, curr_loc, target_part, parsed, flags
    )
    assert success is True
    assert err_msg == ""
    assert dice_res is not None
    assert dice_res.action_type == "전투 공격"


def test_validator_pre_validate_action_end_to_end(clean_state):
    """Verify public pre_validate_action signature and full end-to-end integration."""
    # 1. Invalid power scaling
    is_valid, msg, dice, flags = ActionValidator.pre_validate_action("지구를 파괴한다", clean_state)
    assert is_valid is False
    assert "불가능한 행동" in msg
    assert dice is None

    # 2. Invalid target (dead NPC)
    dead_npc = list(clean_state.npcs.values())[0]
    dead_npc.alive = False
    is_valid, msg, dice, flags = ActionValidator.pre_validate_action(f"{dead_npc.name}에게 말을 건넨다", clean_state)
    assert is_valid is False
    assert "시신은 대답하지 않습니다" in msg

    # 3. Valid combat attack
    dead_npc.alive = True
    is_valid, msg, dice, flags = ActionValidator.pre_validate_action(f"{dead_npc.name}을 향해 단검으로 공격한다", clean_state)
    assert is_valid is True
    assert msg == ""
    assert dice is not None
    assert dice.action_type == "전투 공격"
