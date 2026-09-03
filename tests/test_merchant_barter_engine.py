import pytest
from src.world.merchant_barter_engine import (
    MerchantBarterEngine,
    ContrabandTier,
    TERRAIN_PRICE_MULTIPLIERS
)
from src.world.state import WorldState, Location
from src.world.legacy import LegacyManager


def test_10_terrain_price_divergence_and_fallback():
    # 1. Coastal Port: Salt is cheap (0.5x), Ore is expensive (2.0x)
    salt_coastal = MerchantBarterEngine.get_regional_price("salt", 10, "coastal_port")
    assert salt_coastal == 5

    ore_coastal = MerchantBarterEngine.get_regional_price("ore", 20, "coastal_port")
    assert ore_coastal == 40

    # 2. Mountain Mine: Salt is expensive (3.5x), Ore is cheap (0.4x)
    salt_mountain = MerchantBarterEngine.get_regional_price("salt", 10, "mountain_mine")
    assert salt_mountain == 35

    ore_mountain = MerchantBarterEngine.get_regional_price("ore", 20, "mountain_mine")
    assert ore_mountain == 8

    # 3. Volcanic Ridge: Clean water is scarce (5.0x)
    water_volcanic = MerchantBarterEngine.get_regional_price("clean_water", 10, "volcanic_ridge")
    assert water_volcanic == 50

    # 4. Frozen Tundra: Firewood is scarce (4.0x)
    firewood_tundra = MerchantBarterEngine.get_regional_price("firewood", 10, "frozen_tundra")
    assert firewood_tundra == 40

    # 5. Subterranean: Grain is scarce (4.0x)
    grain_underdark = MerchantBarterEngine.get_regional_price("grain", 10, "subterranean")
    assert grain_underdark == 40

    # 6. Desert Oasis: Clean water is scarce (4.0x)
    water_desert = MerchantBarterEngine.get_regional_price("clean_water", 10, "desert_oasis")
    assert water_desert == 40

    # 7. Dense Forest: Wood is cheap (0.4x)
    wood_forest = MerchantBarterEngine.get_regional_price("wood", 25, "dense_forest")
    assert wood_forest == 10

    # 8. Toxic Swamp: Antidote is cheap (0.4x)
    antidote_swamp = MerchantBarterEngine.get_regional_price("antidote", 50, "toxic_swamp")
    assert antidote_swamp == 20

    # 9. Capital Metropolis: Magic scrolls are common (0.7x)
    scroll_capital = MerchantBarterEngine.get_regional_price("magic_scrolls", 100, "capital_metropolis")
    assert scroll_capital == 70

    # 10. Fallback on completely unknown fantasy terrain
    unknown_price = MerchantBarterEngine.get_regional_price("salt", 10, "crystal_celestial_realm")
    assert unknown_price == 10


def test_barter_exchange_persuasion_checks():
    # Player offers goods worth 100G total, wants item worth 90G
    offered = [50, 50]
    wanted = [90]

    # Critical Persuasion (>= 18): 1.25x value -> 125G vs 90G
    res_crit = MerchantBarterEngine.calculate_barter_exchange(offered, wanted, persuasion_roll=19)
    assert res_crit["is_possible"] is True
    assert res_crit["effective_offered_total"] == 125
    assert res_crit["change_gold_due"] == 35

    # Fair Persuasion (12~17): 1.0x value -> 100G vs 90G
    res_fair = MerchantBarterEngine.calculate_barter_exchange(offered, wanted, persuasion_roll=14)
    assert res_fair["is_possible"] is True
    assert res_fair["effective_offered_total"] == 100
    assert res_fair["change_gold_due"] == 10

    # Failed Persuasion (< 12): 0.8x markdown -> 80G vs 90G (Shortfall 10G)
    res_fail = MerchantBarterEngine.calculate_barter_exchange(offered, wanted, persuasion_roll=7)
    assert res_fail["is_possible"] is False
    assert res_fail["effective_offered_total"] == 80
    assert res_fail["shortfall_gold"] == 10


def test_smuggling_checkpoint_inspection(monkeypatch):
    legal_items = [{"id": "bread", "contraband_tier": ContrabandTier.LEGAL}]
    res_legal = MerchantBarterEngine.check_smuggling_checkpoint(legal_items)
    assert res_legal["passed"] is True
    assert res_legal["bounty_added"] == 0

    illicit_items = [
        {"id": "darkweed", "name_ko": "암흑초", "contraband_tier": ContrabandTier.ILLICIT}
    ]

    # Force high roll for stealth success
    monkeypatch.setattr("src.world.dice.DiceEngine.roll_d20", lambda: 20)
    res_success = MerchantBarterEngine.check_smuggling_checkpoint(illicit_items, guard_perception=12, player_stealth_mod=2)
    assert res_success["passed"] is True
    assert res_success["bounty_added"] == 0

    # Force low roll for caught red-handed
    monkeypatch.setattr("src.world.dice.DiceEngine.roll_d20", lambda: 2)
    res_caught = MerchantBarterEngine.check_smuggling_checkpoint(illicit_items, guard_perception=14, player_stealth_mod=0)
    assert res_caught["passed"] is False
    assert "암흑초" in res_caught["confiscated_items"]
    assert res_caught["bounty_added"] == 500


def test_black_market_multipliers():
    base_price = 50

    legal_sell = MerchantBarterEngine.sell_to_black_market(base_price, ContrabandTier.LEGAL)
    assert legal_sell == 25  # 0.5x

    restricted_sell = MerchantBarterEngine.sell_to_black_market(base_price, ContrabandTier.RESTRICTED)
    assert restricted_sell == 150  # 3.0x

    illicit_sell = MerchantBarterEngine.sell_to_black_market(base_price, ContrabandTier.ILLICIT)
    assert illicit_sell == 500  # 10.0x


def test_merchant_credit_debt_and_default():
    ledger = MerchantBarterEngine.record_merchant_debt(
        shop_id="shop_blacksmith",
        principal=200,
        current_turn=10,
        duration_turns=20,
        interest_rate=0.20
    )
    assert ledger.total_due == 240
    assert ledger.due_turn == 30

    # Before due turn
    status_ok = MerchantBarterEngine.check_debt_default(ledger, current_turn=25)
    assert status_ok["defaulted"] is False
    assert status_ok["trigger_enforcer_ambush"] is False

    # After due turn -> Default!
    status_overdue = MerchantBarterEngine.check_debt_default(ledger, current_turn=35)
    assert status_overdue["defaulted"] is True
    assert status_overdue["trigger_enforcer_ambush"] is True
    assert status_overdue["total_due"] == 360  # 240 + 50% penalty (120)


def test_unidentified_item_appraisal():
    # Underpaid
    res_underpaid = MerchantBarterEngine.appraise_unidentified_item(
        raw_name="녹슨 쇠붙이",
        true_name="고대 태양신의 황금 인장",
        true_price=850,
        fee_paid=10,
        required_fee=30
    )
    assert res_underpaid["success"] is False
    assert res_underpaid["price"] == 10

    # Paid properly
    res_appraised = MerchantBarterEngine.appraise_unidentified_item(
        raw_name="녹슨 쇠붙이",
        true_name="고대 태양신의 황금 인장",
        true_price=850,
        fee_paid=30,
        required_fee=30
    )
    assert res_appraised["success"] is True
    assert res_appraised["revealed_name"] == "고대 태양신의 황금 인장"
    assert res_appraised["price"] == 850


def test_coin_clipping_fraud(monkeypatch):
    # 1. Success
    monkeypatch.setattr("src.world.dice.DiceEngine.roll_d20", lambda: 18)
    res_success = MerchantBarterEngine.attempt_coin_clipping(payment_amount=100, merchant_perception=12)
    assert res_success["success"] is True
    assert res_success["gold_dust_value"] == 15
    assert res_success["bounty_added"] == 0

    # 2. Caught
    monkeypatch.setattr("src.world.dice.DiceEngine.roll_d20", lambda: 4)
    res_caught = MerchantBarterEngine.attempt_coin_clipping(payment_amount=100, merchant_perception=14)
    assert res_caught["success"] is False
    assert res_caught["gold_dust_value"] == 0
    assert res_caught["bounty_added"] == 150


def test_legacy_probabilistic_spawn():
    state = WorldState(session_id="test_legacy_prob")
    state.locations = {"tavern": Location(id="tavern", name="주점", description="", exits={})}

    # When spawn_chance is 0.0, it should NEVER spawn
    spawned_never = LegacyManager.spawn_legacy_npcs_to_world(state, spawn_chance=0.0)
    assert spawned_never == []
