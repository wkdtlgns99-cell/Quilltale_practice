"""
Unit and Integration Tests for Black Market Auction Engine (test_auction_engine.py)
"""

import pytest
from src.world.entities import Player, NPC
from src.world.state import WorldState
from src.world.auction_engine import (
    AuctionLot,
    NPCBidder,
    AuctionActionResult,
    BlackMarketAuctionState,
    BlackMarketAuctionEngine,
)


class DummyState:
    """Mock state for standalone auction tests."""
    def __init__(self, gold=1000, strength=18, agility=10, stealth=10):
        self.player = Player(
            name="테스트용병",
            health=100,
            max_health=100,
            mana=50,
            max_mana=50,
            gold=gold,
            strength=strength,
            agility=agility,
            traits=["test_adventurer"]
        )
        self.player.stealth = stealth


def test_rule_5_traits_compliance():
    """Verify that all auction dataclasses have traits: List[str]."""
    lot = AuctionLot(
        lot_id="l1", name="검", description="설명", category="weapon",
        rarity="rare", starting_bid=100, current_bid=100,
        highest_bidder_id="none", highest_bidder_name="none"
    )
    bidder = NPCBidder(npc_id="n1", name="상인", archetype="merchant", budget=500, remaining_budget=500)
    result = AuctionActionResult(
        action_type="bid", success=True, current_lot_id="l1",
        highest_bid=150, highest_bidder_name="플레이어", countdown=3
    )
    auction_state = BlackMarketAuctionState()

    assert isinstance(lot.traits, list)
    assert isinstance(bidder.traits, list)
    assert isinstance(result.traits, list)
    assert isinstance(auction_state.traits, list)


def test_auction_state_serialization_roundtrip():
    """Verify serialization and deserialization of auction state."""
    state = BlackMarketAuctionEngine.initialize_auction()
    data = state.to_dict()
    restored = BlackMarketAuctionState.from_dict(data)

    assert len(restored.active_lots) == len(state.active_lots)
    assert len(restored.bidders) == len(state.bidders)
    assert restored.active_lots[0].name == state.active_lots[0].name
    assert restored.current_lot_index == 0
    assert restored.blacklisted_player is False


def test_player_place_bid_success_and_countdown_reset():
    """Verify player can place a valid bid and resets countdown to 3."""
    dummy = DummyState(gold=1000)
    auction_state = BlackMarketAuctionEngine.initialize_auction()
    current_lot = BlackMarketAuctionEngine.get_current_lot(auction_state)
    assert current_lot is not None

    # Initial starting bid is 250
    result = BlackMarketAuctionEngine.player_place_bid(dummy, auction_state, bid_amount=300)
    assert result.success is True
    assert current_lot.current_bid == 300
    assert current_lot.highest_bidder_id == "player"
    assert current_lot.countdown == 3


def test_player_place_bid_insufficient_gold():
    """Verify player cannot bid with insufficient gold."""
    dummy = DummyState(gold=100)
    auction_state = BlackMarketAuctionEngine.initialize_auction()
    current_lot = BlackMarketAuctionEngine.get_current_lot(auction_state)

    result = BlackMarketAuctionEngine.player_place_bid(dummy, auction_state, bid_amount=300)
    assert result.success is False
    assert "소지 골드가 부족합니다" in result.narration_logs[0]
    assert current_lot.highest_bidder_id != "player"


def test_player_place_bid_too_low():
    """Verify player cannot bid lower than minimum increment."""
    dummy = DummyState(gold=1000)
    auction_state = BlackMarketAuctionEngine.initialize_auction()
    current_lot = BlackMarketAuctionEngine.get_current_lot(auction_state)

    # First bid by player
    BlackMarketAuctionEngine.player_place_bid(dummy, auction_state, bid_amount=300)
    # Next bid must be >= 350 (+50 min_increment)
    result = BlackMarketAuctionEngine.player_place_bid(dummy, auction_state, bid_amount=320)
    assert result.success is False
    assert "호가가 너무 낮습니다" in result.narration_logs[0]


def test_player_intimidate_bidders():
    """Verify high strength/presence intimidates low-resistance bidders."""
    dummy = DummyState(strength=25)  # Very high STR
    auction_state = BlackMarketAuctionEngine.initialize_auction()

    result = BlackMarketAuctionEngine.player_intimidate_bidders(dummy, auction_state)
    assert result.success is True
    # At least Gordan (resistance 10) should be intimidated
    intimidated = [b for b in auction_state.bidders if b.status == "intimidated"]
    assert len(intimidated) >= 1
    assert "입찰을 포기합니다" in result.narration_logs[0]


def test_player_snatch_lot_failure_and_brawl():
    """Verify failed snatch triggers brawl and blacklists player."""
    dummy = DummyState(agility=1, stealth=1)  # Very low agility/stealth -> fails DC 18
    auction_state = BlackMarketAuctionEngine.initialize_auction()

    result = BlackMarketAuctionEngine.player_snatch_lot(dummy, auction_state)
    assert result.success is False
    assert result.brawl_triggered is True
    assert auction_state.blacklisted_player is True
    assert "강탈 발각" in result.narration_logs[0]

    # After blacklisted, cannot place bids
    bid_res = BlackMarketAuctionEngine.player_place_bid(dummy, auction_state, 500)
    assert bid_res.success is False
    assert "경매장 입장 불가" in bid_res.narration_logs[0]


def test_player_snatch_lot_success():
    """Verify successful snatch awards item payload and concludes lot."""
    dummy = DummyState(agility=25, stealth=25)  # Very high -> passes DC 18
    auction_state = BlackMarketAuctionEngine.initialize_auction()
    first_lot = BlackMarketAuctionEngine.get_current_lot(auction_state)
    assert first_lot is not None

    result = BlackMarketAuctionEngine.player_snatch_lot(dummy, auction_state)
    assert result.success is True
    assert result.acquired_item is not None
    assert result.acquired_item["name"] == first_lot.name
    assert first_lot.is_concluded is True
    # Moved to next lot
    assert auction_state.current_lot_index == 1


def test_advance_auction_tick_countdown_and_sold_to_player():
    """Verify countdown decrements 3 -> 2 -> 1 -> 0 (Sold) when no NPC bids."""
    dummy = DummyState(gold=2000)
    auction_state = BlackMarketAuctionEngine.initialize_auction()
    # Intimidate all bidders or set their budget to 0 so they don't counter-bid
    for b in auction_state.bidders:
        b.status = "out_of_budget"

    # Player bids 300
    BlackMarketAuctionEngine.player_place_bid(dummy, auction_state, bid_amount=300)
    lot = BlackMarketAuctionEngine.get_current_lot(auction_state)
    assert lot.countdown == 3

    # Tick 1: countdown becomes 2
    r1 = BlackMarketAuctionEngine.advance_auction_tick(dummy, auction_state)
    assert r1.countdown == 2
    assert "첫 번째 호가" in r1.narration_logs[0]

    # Tick 2: countdown becomes 1
    r2 = BlackMarketAuctionEngine.advance_auction_tick(dummy, auction_state)
    assert r2.countdown == 1
    assert "두 번째 호가" in r2.narration_logs[0]

    # Tick 3: countdown hits 0 -> Sold!
    r3 = BlackMarketAuctionEngine.advance_auction_tick(dummy, auction_state)
    assert r3.countdown == 0
    assert r3.gold_spent == 300
    assert r3.acquired_item is not None
    assert "최종 낙찰되었습니다" in r3.narration_logs[0]
    assert lot.is_concluded is True
    assert auction_state.current_lot_index == 1


def test_auction_status_summary():
    """Verify Korean status summary formatting."""
    auction_state = BlackMarketAuctionEngine.initialize_auction()
    summary = BlackMarketAuctionEngine.get_auction_status_summary(None, auction_state)
    assert "지하 암시장 비밀 경매장" in summary
    assert "칠흑의 피흡수 단검" in summary
    assert "경매봉 카운트다운" in summary


def _setup_world_for_auction():
    from src.world.state import Location, NPC
    state = WorldState()
    state.player = Player(
        name="테스트경매참가자",
        location="black_market_vault",
        health=100,
        gold=1500,
        agility=16,
        strength=16,
        reputation=10,
    )
    state.player.stealth = 14
    state.locations["black_market_vault"] = Location(
        id="black_market_vault",
        name="지하 암시장 비밀 경매장",
        description="어둠침침한 촛불 아래 귀족들과 암상인들이 모여 있는 비밀 경매장.",
        exits={},
        items=[],
        npcs=["npc_guard_01"],
    )
    npc_guard = NPC(
        id="npc_guard_01",
        name="암시장 중장갑 경비병",
        description="도끼를 쥐고 단상을 감시하는 거구의 경비병.",
        location="black_market_vault",
        disposition="neutral",
        health=120,
        max_health=120,
    )
    state.npcs["npc_guard_01"] = npc_guard
    return state


def test_two_pass_engine_auction_live_integration():
    """Verify auction action resolution through TwoPassEngine Pass 1 pipeline."""
    from src.world.two_pass_engine import TwoPassEngine
    state = _setup_world_for_auction()

    # 1. Player bids on current lot
    action = "단상 위의 유물에 350골드를 입찰하며 호가를 부른다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid is True
    assert fact_sheet.auction_summary is not None
    assert "지하 암시장 비밀 경매장" in fact_sheet.auction_summary
    prompt_context = fact_sheet.to_prompt_context()
    assert "지하 암시장 비밀 경매장" in prompt_context
    assert "단상을 울리는 경매사의 망치질" in prompt_context


def test_two_pass_engine_auction_snatch_brawl_integration():
    """Verify failed snatch via Pass 1 triggers brawl and sets NPCs hostile."""
    from src.world.two_pass_engine import TwoPassEngine
    state = _setup_world_for_auction()
    state.player.agility = 1
    state.player.stealth = 1

    action = "단상 위의 경매품을 몰래 낚아채서 훔치려 시도한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid is True
    assert state.npcs["npc_guard_01"].disposition == "hostile"
    assert state.auction_state.blacklisted_player is True


def test_world_state_auction_round_trip():
    """Verify WorldState preserves auction_state across serialization."""
    state = _setup_world_for_auction()
    state.auction_state = BlackMarketAuctionEngine.initialize_auction()
    # Place a bid
    BlackMarketAuctionEngine.player_place_bid(state, state.auction_state, 400)

    state_dict = state.to_dict()
    restored = WorldState.from_dict(state_dict)

    assert restored.auction_state is not None
    lot = BlackMarketAuctionEngine.get_current_lot(restored.auction_state)
    assert lot is not None
    assert lot.current_bid == 400
    assert lot.highest_bidder_id == "player"

