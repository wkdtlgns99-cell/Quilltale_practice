"""
Unit tests for EconomyEngine, Shop management, item buying/selling,
haggling, services, restock, and WorldState integration.
"""
import pytest
from src.world.state import WorldState, Player, Location, NPC, Item
from src.world.economy_engine import EconomyEngine, Shop, ShopItem
from src.world.status_engine import StatusEffectEngine


def test_load_shop_templates():
    shops = EconomyEngine.load_templates()
    assert len(shops) >= 5
    assert "moonlit_apothecary" in shops
    assert "iron_bell_forge" in shops
    assert "astral_archive" in shops
    assert "silent_tavern" in shops


def test_item_unlock_conditions():
    state = WorldState()
    state.player.level = 5
    state.player.reputation = 5
    state.player.intelligence = 10

    shop = EconomyEngine.get_shop_template("moonlit_apothecary")
    greater_potion = next(i for i in shop.inventory if i.item_id == "greater_healing_potion")

    # Player rep 5 < 15 required
    unlocked, reason = EconomyEngine.check_item_unlock(greater_potion, state)
    assert unlocked is False
    assert "평판" in reason

    # Raise rep to 20
    state.player.reputation = 20
    unlocked2, _ = EconomyEngine.check_item_unlock(greater_potion, state)
    assert unlocked2 is True


def test_buy_item_success_and_gold_check():
    state = WorldState()
    state.player.gold = 100
    state.player.location = "old_town_alley"

    # Buy moonleaf (base 18 * buy_rate 1.3 = 23G)
    success, msg, data = EconomyEngine.buy_item(state, "moonlit_apothecary", "moonleaf", count=2)
    assert success is True
    assert "moonleaf" in state.player.inventory
    assert state.player.inventory.count("moonleaf") == 2
    assert state.player.gold < 100

    # Try buying item with insufficient gold
    state.player.gold = 0
    success2, msg2, _ = EconomyEngine.buy_item(state, "moonlit_apothecary", "moonleaf", count=1)
    assert success2 is False
    assert "골드 부족" in msg2


def test_sell_item_success():
    state = WorldState()
    state.player.gold = 10
    state.player.inventory = ["iron_dagger", "iron_dagger"]
    state.items["iron_dagger"] = Item(id="iron_dagger", name="철 단검", description="단검", value=40, location="inventory")

    success, msg, data = EconomyEngine.sell_item(state, "iron_bell_forge", "iron_dagger", count=1)
    assert success is True
    assert state.player.inventory.count("iron_dagger") == 1
    assert state.player.gold > 10  # received gold (40 * 0.65 = 26G)


def test_haggling_logic():
    state = WorldState()
    state.player.luck = 18  # high luck modifier
    shop = EconomyEngine.get_shop_template("moonlit_apothecary")

    success, msg, mult = EconomyEngine.perform_haggle(state, shop)
    assert mult <= 1.0


def test_use_shop_services():
    state = WorldState()
    state.player.gold = 200
    StatusEffectEngine.apply_status(state.player, "poison", duration=3)
    assert "poison" in state.player.status_effects

    # Use remove_poison service at moonlit_apothecary (costs 40G)
    success, msg = EconomyEngine.use_service(state, "moonlit_apothecary", "remove_poison")
    assert success is True
    assert "poison" not in state.player.status_effects
    assert state.player.gold == 160


def test_restock_turn_ticks():
    state = WorldState()
    shop = EconomyEngine.get_shop_template("moonlit_apothecary")
    shop.inventory[0].stock = 0  # moonleaf sold out
    shop.inventory[0].max_stock = 5
    shop.restock_interval_turns = 2
    state.shops["moonlit_apothecary"] = shop

    # Tick 1
    EconomyEngine.restock_turn_ticks(state, delta_turns=1)
    assert shop.inventory[0].stock == 0

    # Tick 2 (interval reached -> stock restocked)
    EconomyEngine.restock_turn_ticks(state, delta_turns=1)
    assert shop.inventory[0].stock == 1


def test_world_state_apply_update_economy():
    state = WorldState()
    state.player.gold = 300

    # Buy via update
    state.apply_update({
        "buy_item": {
            "shop_id": "moonlit_apothecary",
            "item_id": "moonleaf",
            "count": 1
        }
    })
    assert "moonleaf" in state.player.inventory


def test_serialization_round_trip():
    state = WorldState()
    shop = EconomyEngine.get_shop_template("moonlit_apothecary")
    shop.merchant_gold = 777
    state.shops["moonlit_apothecary"] = shop

    json_str = state.to_json()
    loaded = WorldState.from_json(json_str)

    assert "moonlit_apothecary" in loaded.shops
    assert loaded.shops["moonlit_apothecary"].merchant_gold == 777
    assert loaded.shops["moonlit_apothecary"].shop_name == "달빛 약초원"


def test_shop_html_and_prompt_formatting():
    state = WorldState()
    loc = Location(id="start", name="선술집", description="선술집", exits={}, npcs=["innkeeper_mara"])
    state.locations["start"] = loc
    state.player.location = "start"

    html = state.to_shop_html()
    assert "침묵의 선술집" in html or "상점" in html

    prompt_ctx = EconomyEngine.format_shop_context_for_prompt(state)
    assert "침묵의 선술집" in prompt_ctx or "상점" in prompt_ctx
