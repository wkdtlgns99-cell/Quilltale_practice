import pytest
from src.world.state import WorldState, Location, Player, Item
from src.world.trap_engine import TrapEngine, TrapSpec, TrapInstance, TRAP_REGISTRY
from src.world.dungeon_engine import DungeonEngine, DungeonInstance
from src.world.two_pass_engine import TwoPassEngine
from src.world.status_engine import StatusEffectEngine


@pytest.fixture
def test_world():
    state = WorldState()
    state.player.location = "forest_path"
    state.player.health = 100
    state.player.max_health = 100
    state.player.mana = 50
    state.player.max_mana = 50
    state.player.agility = 12
    state.player.perception = 14
    state.player.inventory = ["thieves_tools"]

    # Surface Forest Location
    forest = Location(
        id="forest_path",
        name="깊은 숲길",
        description="이끼 낀 고목과 덤불이 우거진 숲길",
        exits={},
        terrain="forest",
        location_category="surface",
        danger_level=20,
        monster_density=30,
        npc_density=10
    )
    state.locations["forest_path"] = forest

    # Dungeon Entrance Location
    dungeon_entrance = Location(
        id="catacomb_entrance",
        name="지하 납골당 입구",
        description="음산한 지하 묘지로 이어지는 석조 입구",
        exits={},
        terrain="mountains",
        location_category="surface",
        danger_level=35,
        monster_density=40,
        npc_density=5
    )
    state.locations["catacomb_entrance"] = dungeon_entrance

    # Hidden Realm Location
    hidden_realm = Location(
        id="void_rift_sanctuary",
        name="심연의 균열 비경",
        description="공간이 뒤틀린 차원의 틈새 성소",
        exits={},
        terrain="all",
        location_category="hidden_realm",
        danger_level=95,
        monster_density=75,
        npc_density=0
    )
    state.locations["void_rift_sanctuary"] = hidden_realm

    return state


def test_contextual_trap_matching(test_world):
    """Test that traps strictly match terrain and category concepts with traits."""
    # Surface Forest traps
    forest_traps = TrapEngine.get_contextual_trap_specs("surface", "forest")
    assert any(t.id == "surface_bear_trap" for t in forest_traps)
    assert any(t.id == "surface_falling_log" for t in forest_traps)

    # Dungeon traps
    dungeon_traps = TrapEngine.get_contextual_trap_specs("dungeon", "mountains")
    assert any(t.id == "dungeon_crushing_ceiling" for t in dungeon_traps)
    assert any(t.id == "dungeon_poison_gas_vent" for t in dungeon_traps)

    # Hidden Realm traps
    hidden_traps = TrapEngine.get_contextual_trap_specs("hidden_realm", "all")
    assert any(t.id == "hidden_void_displacement" for t in hidden_traps)
    assert any(t.id == "hidden_abyssal_hysteria" for t in hidden_traps)

    # Check rule 6 traits
    for spec in TRAP_REGISTRY.values():
        assert len(spec.traits) > 0


def test_trap_detection_perception(test_world):
    """Test perception-based trap discovery and status transition to revealed."""
    player = test_world.player
    loc = test_world.locations["forest_path"]

    # Mount bear trap in forest
    inst = TrapEngine.spawn_trap_for_location(test_world, "forest_path", "surface_bear_trap")
    assert inst is not None
    assert inst.status == "hidden"
    assert inst.instance_id in loc.traps

    # High perception search reveals trap
    player.perception = 18
    results = TrapEngine.detect_traps_in_location(player, "forest_path", test_world, is_active_search=True)
    assert len(results) >= 1
    assert inst.status == "revealed"
    assert "포착했습니다" in results[0]["message_ko"]


def test_trap_disarm_mechanics(test_world, monkeypatch):
    """Test disarm success with thieves tools and immediate trigger on failure."""
    from src.world.dice import DiceEngine
    player = test_world.player
    inst = TrapEngine.spawn_trap_for_location(test_world, "forest_path", "surface_bear_trap")
    inst.status = "revealed"

    # Deterministic success with high roll and thieves tools
    monkeypatch.setattr(DiceEngine, "roll_d20", lambda: 15)
    player.agility = 18
    res = TrapEngine.disarm_trap(player, inst.instance_id, test_world, tool_item_id="thieves_tools")
    assert res["success"]
    assert inst.status == "disarmed"

    # Deterministic failure with low roll (roll=2) -> disarm fails and triggers trap
    inst.status = "revealed"
    monkeypatch.setattr(DiceEngine, "roll_d20", lambda: 2)
    player.agility = 6
    fail_res = TrapEngine.disarm_trap(player, inst.instance_id, test_world)
    assert not fail_res["success"]
    assert fail_res["triggered"]
    assert inst.status == "triggered"


def test_trap_trigger_and_reflex_save(test_world, monkeypatch):
    """Test damage, status effects (bleeding), and noise generation on trigger."""
    from src.world.dice import DiceEngine
    player = test_world.player
    player.health = 100
    player.agility = 10

    # Low roll (roll=5): fail dodge -> full damage and bleeding status
    monkeypatch.setattr(DiceEngine, "roll_d20", lambda: 5)
    inst = TrapEngine.spawn_trap_for_location(test_world, "forest_path", "surface_bear_trap")
    res = TrapEngine.trigger_trap(player, inst.instance_id, test_world)

    assert res["triggered"]
    assert res["damage_dealt"] == 16
    assert not res["is_dodged"]
    assert player.health == 84
    assert "bleeding" in res["inflicted_status"]
    assert StatusEffectEngine.has_status(player, "bleeding")
    assert res["noise_db"] == 25

    # High roll (roll=20): dodge -> half damage (8) and no status
    inst2 = TrapEngine.spawn_trap_for_location(test_world, "forest_path", "surface_bear_trap")
    monkeypatch.setattr(DiceEngine, "roll_d20", lambda: 20)
    res_dodge = TrapEngine.trigger_trap(player, inst2.instance_id, test_world)
    assert res_dodge["is_dodged"]
    assert res_dodge["damage_dealt"] == 8


def test_hidden_realm_void_teleport_trap(test_world):
    """Test reality-bending hidden realm trap teleporting player back to entrance."""
    player = test_world.player
    player.location = "void_rift_sanctuary"

    inst = TrapEngine.spawn_trap_for_location(test_world, "void_rift_sanctuary", "hidden_void_displacement")
    res = TrapEngine.trigger_trap(player, inst.instance_id, test_world)

    assert res["triggered"]
    assert any("공간 왜곡" in log for log in res["special_logs"])
    # Teleported back to start or root
    assert player.location != "void_rift_sanctuary"


def test_dungeon_instance_depth_scaling(test_world):
    """Test multi-floor dungeon generation with depth-scaled danger, monster density, and traps."""
    dungeon = DungeonEngine.create_dungeon_instance(
        test_world,
        surface_location_id="catacomb_entrance",
        dungeon_name_ko="고대 지하 납골당",
        theme="catacomb",
        core_element="undead",
        max_depth=3
    )

    assert dungeon.max_depth == 3
    assert len(dungeon.floors) == 3

    # Check depth scaling: Floor 1 vs Floor 3
    f1 = dungeon.floors[1]
    f3 = dungeon.floors[3]
    assert f1.floor_danger_level < f3.floor_danger_level
    assert f3.is_boss_floor

    # Rooms registered in test_world.locations
    f1_room_ids = list(f1.rooms.keys())
    assert f1_room_ids[0] in test_world.locations
    r1 = test_world.locations[f1_room_ids[0]]
    assert r1.location_category == "dungeon"
    assert r1.floor_depth == 1

    # Check traps spawned in corridor/crypt rooms
    assert any(len(getattr(test_world.locations[rid], "traps", [])) > 0 for rid in f1.rooms.keys())


def test_dungeon_navigation_descend_ascend(test_world):
    """Test player navigation between dungeon floors and return to surface."""
    dungeon = DungeonEngine.create_dungeon_instance(
        test_world,
        surface_location_id="catacomb_entrance",
        max_depth=2
    )

    player = test_world.player
    player.location = "catacomb_entrance"

    # Descend from surface into B1F
    ok, msg = DungeonEngine.descend_floor(test_world)
    assert ok
    assert test_world.locations[player.location].floor_depth == 1

    # Ascend back to surface
    ok_up, msg_up = DungeonEngine.ascend_floor(test_world)
    assert ok_up
    assert player.location == "catacomb_entrance"
    assert "무사히 귀환" in msg_up


def test_dungeon_trap_save_load_backwards_compatibility():
    """Test legacy location dictionary loads with default category and zero traps."""
    legacy_save = {
        "player": {"name": "옛날 탐험가", "health": 100, "mana": 50, "location": "old_room"},
        "locations": {
            "old_room": {
                "id": "old_room",
                "name": "구식 지상 방",
                "exits": {}
                # location_category, floor_depth, danger_level, traps are absent!
            }
        },
        "npcs": {}
    }

    state = WorldState.from_dict(legacy_save)
    loc = state.locations["old_room"]
    assert loc.location_category == "surface"
    assert loc.floor_depth == 0
    assert loc.danger_level == 20
    assert loc.monster_density == 20
    assert loc.npc_density == 50
    assert loc.traps == []
