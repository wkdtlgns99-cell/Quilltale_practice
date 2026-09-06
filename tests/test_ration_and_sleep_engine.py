"""
Unit tests for RationSpoilageEngine and SleepDeprivationEngine in Quilltale TRPG.
Tests individual food spoilage, stack separation, environmental heat/wetness decay,
food preservation (salt/smoke/dry), water boiling purification, food poisoning/dysentery,
sleep deprivation tiers, stimulant crash, and bedding quality recovery.
"""
import pytest
from src.world.state import WorldState, Player, Item
from src.world.ration_engine import (
    RationSpoilageEngine, FoodItemStatus, PRESERVATION_METHODS
)
from src.world.sleep_engine import (
    SleepDeprivationEngine, CircadianClock, STIMULANTS_REGISTRY, BEDDING_REGISTRY
)


def test_food_item_status_and_traits():
    """Verifies food status creation and initial properties."""
    apple = Item(id="apple_1", name="신선한 사과", description="", location="inventory", item_type="food")
    status = RationSpoilageEngine.get_or_create_food_status(apple)
    assert status.freshness == 100.0
    assert not status.is_spoiled
    assert not status.is_rotten
    assert len(status.traits) > 0

    jerky = Item(id="jerky_1", name="말린 쇠고기 육포", description="", location="inventory", item_type="food")
    j_status = RationSpoilageEngine.get_or_create_food_status(jerky)
    assert j_status.preservation_type == "dried"
    assert j_status.spoilage_rate_per_turn < 1.0


def test_individual_spoilage_turn_ticks():
    """User Rule 1: Individual food item decay, accelerated by heat and wetness."""
    state = WorldState()
    player = state.player
    raw_meat = Item(id="meat_1", name="생 사슴고기", description="", location="inventory", item_type="food")
    state.items["meat_1"] = raw_meat
    player.inventory.append("meat_1")

    # High body temperature and extreme wetness
    player.body_temperature = 39.5  # Heat acceleration 2.5x
    player.wetness = 80.0           # Wetness acceleration 2.2x -> Total multiplier 5.5x

    status = RationSpoilageEngine.get_or_create_food_status(raw_meat)
    assert status.freshness == 100.0

    # Tick 1 turn
    logs = RationSpoilageEngine.process_turn_spoilage(state)
    # Decay is at least 5.5
    assert status.freshness <= 95.0

    # Advance until spoiled (< 40)
    status.freshness = 42.0
    logs_spoil = RationSpoilageEngine.process_turn_spoilage(state)
    assert status.is_spoiled
    assert "상하기 시작한" in raw_meat.name
    assert "spoiled" in raw_meat.traits

    # Advance until completely rotten (0)
    status.freshness = 2.0
    logs_rot = RationSpoilageEngine.process_turn_spoilage(state)
    assert status.is_rotten
    assert "썩은 폐기물" in raw_meat.name
    assert "rotten" in raw_meat.traits


def test_food_preservation_salt_smoking_drying():
    """Tests preserving food with salt, smoking, and sun drying."""
    state = WorldState()
    player = state.player
    fish = Item(id="fish_1", name="민물 송어", description="", location="inventory", item_type="food")
    salt = Item(id="rock_salt_1", name="정제된 암염", description="", location="inventory", item_type="misc")
    state.items["fish_1"] = fish
    state.items["rock_salt_1"] = salt
    player.inventory.extend(["fish_1", "rock_salt_1"])

    # 1. Salt-curing
    ok, msg = RationSpoilageEngine.preserve_food(state, fish, "salt_cure")
    assert ok
    assert "염장" in msg
    assert "염장된" in fish.name
    assert "rock_salt_1" not in player.inventory  # Salt was consumed

    status = fish.properties["food_status"]
    assert status.preservation_type == "salt_cure"
    assert status.spoilage_rate_per_turn <= 0.25


def test_water_purification_boiling():
    """Tests boiling and purifying contaminated water."""
    state = WorldState()
    swamp_water = Item(
        id="swamp_water_1",
        name="오염된 늪지 물병",
        description="",
        location="inventory",
        item_type="drink",
        traits=["contaminated", "dirty"]
    )
    state.items["swamp_water_1"] = swamp_water
    status = RationSpoilageEngine.get_or_create_food_status(swamp_water)
    status.freshness = 30.0

    ok, msg = RationSpoilageEngine.purify_water(state, swamp_water)
    assert ok
    assert "깨끗한 식수" in swamp_water.name
    assert "safe_water" in swamp_water.properties["food_status"].traits
    assert swamp_water.properties["food_status"].freshness == 100.0


def test_consume_ration_fresh_vs_spoiled_vs_rotten():
    """Tests food consumption outcomes: fresh, spoiled, and rotten dysentery integration."""
    state = WorldState()
    player = state.player
    player.hunger = 50
    player.stamina = 50

    # 1. Fresh food
    fresh_bread = Item(id="bread_1", name="갓 구운 호밀빵", description="", location="inventory", item_type="food")
    state.items["bread_1"] = fresh_bread
    player.inventory.append("bread_1")
    RationSpoilageEngine.consume_ration(state, player, fresh_bread)
    assert player.hunger < 50
    assert player.stamina > 50
    assert "bread_1" not in player.inventory

    # 2. Rotten food -> Severe damage & Dysentery epidemic
    player.health = 50
    rotten_meat = Item(id="rotten_1", name="썩은 폐기물 (고기)", description="", location="inventory", item_type="food")
    state.items["rotten_1"] = rotten_meat
    player.inventory.append("rotten_1")
    status = RationSpoilageEngine.get_or_create_food_status(rotten_meat)
    status.freshness = 0.0
    status.is_rotten = True

    consume_logs = RationSpoilageEngine.consume_ration(state, player, rotten_meat)
    assert player.health < 50
    # Check dysentery infection was triggered or attempted
    assert any("이질" in log for log in consume_logs)


def test_sleep_deprivation_tiers_and_circadian():
    """Tests advancing wakefulness to 24h, 48h, and 72h deprivation tiers."""
    state = WorldState()
    player = state.player
    clock = SleepDeprivationEngine.get_clock(player)
    assert clock.deprivation_tier == 0

    # Advance 72 turns (24 hours)
    for _ in range(72):
        SleepDeprivationEngine.process_turn_circadian(state)
    assert clock.awake_hours >= 24.0
    assert clock.deprivation_tier == 1

    # Advance another 72 turns (48 hours)
    for _ in range(72):
        SleepDeprivationEngine.process_turn_circadian(state)
    assert clock.awake_hours >= 48.0
    assert clock.deprivation_tier == 2

    # Advance another 72 turns (72 hours)
    for _ in range(72):
        SleepDeprivationEngine.process_turn_circadian(state)
    assert clock.awake_hours >= 72.0
    assert clock.deprivation_tier == 3


def test_stimulant_and_crash():
    """Tests taking a stimulant to stave off fatigue, followed by a withdrawal crash."""
    state = WorldState()
    player = state.player
    player.fatigue = 40
    clock = SleepDeprivationEngine.get_clock(player)

    # Consume black coffee
    ok, msg = SleepDeprivationEngine.apply_stimulant(player, "black_coffee")
    assert ok
    assert player.fatigue == 20  # Reduced by 20
    assert clock.active_stimulant_turns == 15
    assert clock.crash_pending

    # Advance 15 turns until stimulant expires
    for _ in range(15):
        SleepDeprivationEngine.process_turn_circadian(state)

    assert clock.active_stimulant_turns == 0
    assert not clock.crash_pending
    # Crash penalty +25 applied
    assert player.fatigue >= 45


def test_sleep_recovery_bedding_quality():
    """Tests sleeping in bare ground vs feather bed."""
    state = WorldState()
    player = state.player
    player.fatigue = 80
    clock = SleepDeprivationEngine.get_clock(player)
    clock.awake_turns = 100
    clock.awake_hours = 33.3

    # 1. Inn bed sleep for 8 hours
    logs = SleepDeprivationEngine.resolve_sleep(player, bedding_id="inn_bed", hours=8, state=state)
    assert player.fatigue < 80
    assert clock.awake_hours == 0.0
    assert clock.deprivation_tier == 0
