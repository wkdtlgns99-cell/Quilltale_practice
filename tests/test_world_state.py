# tests/test_world_state.py

from src.world.state import WorldState
import json


def load_test_state() -> WorldState:
    with open("data/worlds/default.json", encoding="utf-8") as f:
        return WorldState.from_json(f.read())


def test_valid_movement():
    state = load_test_state()
    assert state.player.location == "tavern"
    changes = state.apply_update({"move_player": "north"})
    assert state.player.location == "street"
    assert any("moved" in c for c in changes)


def test_invalid_movement_rejected():
    state = load_test_state()
    changes = state.apply_update({"move_player": "south"})
    # "south" is not a valid exit from tavern
    assert state.player.location == "tavern"
    assert any("REJECTED" in c for c in changes)


def test_valid_item_pickup():
    state = load_test_state()
    changes = state.apply_update({"pickup_item": "dagger"})
    assert "dagger" in state.player.inventory
    assert "dagger" not in state.locations["tavern"].items


def test_invalid_pickup_rejected():
    state = load_test_state()
    # strange_coin is in market, not tavern
    changes = state.apply_update({"pickup_item": "strange_coin"})
    assert "strange_coin" not in state.player.inventory
    assert any("REJECTED" in c for c in changes)


def test_serialisation_roundtrip():
    state = load_test_state()
    state.apply_update({"move_player": "north"})
    state.apply_update({"pickup_item": "dagger"})
    serialised = state.to_json()
    restored = WorldState.from_json(serialised)
    assert restored.player.location == state.player.location
    assert restored.player.inventory == state.player.inventory
    assert restored.turn == state.turn
    assert restored.player.str_stat == state.player.str_stat


def test_context_summary_contains_facts():
    state = load_test_state()
    summary = state.to_context_summary()
    assert "부서진 플라곤" in summary
    assert "north" in summary.lower()
    assert "dagger" in summary.lower()


def test_traits_field_presence_and_serialization():
    from src.world.state import Item, NPC, Skill, Player
    item = Item(id="i1", name="명검", description="", location="loc1", traits=["명품 각인", "예리함"])
    npc = NPC(id="n1", name="마르타", description="", location="loc1", traits=["주정뱅이", "실종된 기사"])
    skill = Skill(id="s1", name="화염구", traits=["원거리 폭발", "화상"])
    player = Player(traits=["불사의 각인", "방랑자"])

    assert item.traits == ["명품 각인", "예리함"]
    assert npc.traits == ["주정뱅이", "실종된 기사"]
    assert skill.traits == ["원거리 폭발", "화상"]
    assert player.traits == ["불사의 각인", "방랑자"]

    # Verify WorldState roundtrip with traits
    ws = WorldState()
    ws.items["i1"] = item
    ws.npcs["n1"] = npc
    ws.skills_db["s1"] = skill
    ws.player = player

    json_str = ws.to_json()
    restored = WorldState.from_json(json_str)

    assert restored.items["i1"].traits == ["명품 각인", "예리함"]
    assert restored.npcs["n1"].traits == ["주정뱅이", "실종된 기사"]
    assert restored.skills_db["s1"].traits == ["원거리 폭발", "화상"]
    assert restored.player.traits == ["불사의 각인", "방랑자"]