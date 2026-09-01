import pytest
from src.world.state import WorldState, Location, Player, NPC, Item
from src.world.enchant_engine import EnchantEngine


def test_rune_socketing_and_repair():
    sword = Item(
        id="item_blade",
        name="강철 롱소드",
        description="예리한 도검",
        location="inventory",
        item_type="weapon",
        durability=60,
        max_durability=100,
        rune_slots=2
    )
    player = Player(name="검사", gold=100, inventory=["item_blade", "rune_crimson_flame"])
    state = WorldState(
        session_id="test_enchant",
        player=player,
        items={"item_blade": sword}
    )

    # Socket rune
    success, msg = EnchantEngine.socket_rune(state, "item_blade", "rune_crimson_flame")
    assert success is True
    assert "rune_crimson_flame" in sword.socketed_runes
    assert "rune_crimson_flame" not in player.inventory

    # Repair item
    rep_success, rep_msg, cost = EnchantEngine.repair_item(state, "item_blade")
    assert rep_success is True
    assert sword.durability == 100
    assert player.gold < 100


def test_rune_combat_effects_lifesteal():
    sword = Item(
        id="item_blade",
        name="흡혈 검",
        description="피를 탐하는 검",
        location="inventory",
        item_type="weapon",
        socketed_runes=["rune_vampiric_thirst"]
    )
    player = Player(name="검사", health=50, max_health=100)
    target = NPC(id="npc_orc", name="오크", description="거구의 오크", location="arena", health=50)
    state = WorldState(
        session_id="test_enchant",
        player=player,
        npcs={"npc_orc": target},
        items={"item_blade": sword}
    )

    logs = EnchantEngine.evaluate_rune_combat_effects(state, sword, damage_dealt=40, target_npc=target)
    assert any("흡혈" in l for l in logs)
    assert player.health > 50  # Lifesteal healed the player
