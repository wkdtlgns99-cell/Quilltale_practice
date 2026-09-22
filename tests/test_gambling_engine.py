"""
Tests for Gambling Den, Tavern Dice Mini-Games, and Tavern Brawl Engine (gambling_engine.py).
Verifies:
1. Data models compliance with Rule 5 (traits field) & round-trip serialization.
2. Chinchiro hand rank evaluation (Pinzoro, Shigoro, Arashi, Pair, Hifumi, Menashi).
3. High-Low hand evaluation (High, Low, Lucky 7).
4. Fair gameplay progression and gold payouts.
5. Sleight of hand cheat success and roll rigging.
6. Cheating exposure, gold forfeiture, reputation loss, NPC hostile conversion & Tavern Brawl.
7. Blacklist enforcement against repeat cheaters.
8. TwoPassEngine Pass 1 integration and DeterministicFactSheet context rendering.
9. WorldState persistence serialization round-trip.
"""
import pytest
from unittest.mock import patch

from src.world.state import WorldState, Player, Location, NPC
from src.world.gambling_engine import (
    GamblingDenEngine,
    GamblingOutcome,
    PlayerGamblingRecord,
)
from src.world.two_pass_engine import TwoPassEngine


def _setup_world_for_gambling():
    state = WorldState()
    state.player = Player(
        name="테스트도박사",
        location="tavern_hall",
        health=100,
        gold=200,
        agility=14,
        luck=12,
        reputation=10,
    )
    state.locations["tavern_hall"] = Location(
        id="tavern_hall",
        name="떠들썩한 주점 도박장",
        description="도박꾼들과 술꾼들이 왁자지껄하게 주사위를 굴리고 있는 선술집 홀이다.",
        exits={},
        items=[],
        npcs=["npc_gambler_01", "npc_barkeep_01"],
    )
    npc_gambler = NPC(
        id="npc_gambler_01",
        name="애꾸눈 타짜",
        description="능숙한 손놀림으로 주사위를 굴리는 도박꾼.",
        location="tavern_hall",
        disposition="neutral",
    )
    npc_barkeep = NPC(
        id="npc_barkeep_01",
        name="주점 주인 잭",
        description="카운터 뒤에서 험상궂은 눈으로 도박판을 지켜보는 주점 주인.",
        location="tavern_hall",
        disposition="neutral",
    )
    state.npcs["npc_gambler_01"] = npc_gambler
    state.npcs["npc_barkeep_01"] = npc_barkeep
    return state


def test_gambling_data_models_traits_and_serialization():
    """Rule 5: New game data classes MUST include traits: List[str] = field(default_factory=list)."""
    outcome = GamblingOutcome(
        game_type="chinchiro",
        bet_gold=50,
        payout_gold=150,
        net_gold=100,
        player_dice=[1, 1, 1],
        dealer_dice=[2, 2, 4],
        player_hand="핀조로 (1-1-1)",
        dealer_hand="페어 (4의 눈)",
        result="win",
        traits=["대박", "친치로"],
    )
    assert "대박" in outcome.traits
    o_dict = outcome.to_dict()
    assert o_dict["game_type"] == "chinchiro"
    o_restored = GamblingOutcome.from_dict(o_dict)
    assert o_restored.traits == ["대박", "친치로"]
    assert o_restored.net_gold == 100

    record = PlayerGamblingRecord(
        total_games=10,
        wins=6,
        losses=4,
        net_profit=150,
        traits=["타짜_지망생"],
    )
    assert "타짜_지망생" in record.traits
    r_dict = record.to_dict()
    r_restored = PlayerGamblingRecord.from_dict(r_dict)
    assert r_restored.wins == 6
    assert r_restored.traits == ["타짜_지망생"]


def test_chinchiro_hand_evaluation():
    """Verify Chinchiro 3d6 rank evaluation and payout multipliers."""
    # 1-1-1 Pinzoro (5x)
    score, name, mult = GamblingDenEngine.evaluate_chinchiro_hand([1, 1, 1])
    assert score == 100
    assert "핀조로" in name
    assert mult == 5.0

    # 4-5-6 Shigoro (2x)
    score, name, mult = GamblingDenEngine.evaluate_chinchiro_hand([5, 4, 6])
    assert score == 90
    assert "시고로" in name
    assert mult == 2.0

    # Arashi (Triple: 3x)
    score, name, mult = GamblingDenEngine.evaluate_chinchiro_hand([4, 4, 4])
    assert score == 84
    assert "아라시" in name
    assert mult == 3.0

    # Pair with remaining die point
    score, name, mult = GamblingDenEngine.evaluate_chinchiro_hand([3, 5, 3])
    assert score == 65
    assert "5의 눈" in name
    assert mult == 1.0

    # 1-2-3 Hifumi (-2x double loss)
    score, name, mult = GamblingDenEngine.evaluate_chinchiro_hand([2, 1, 3])
    assert score == -50
    assert "히후미" in name
    assert mult == -2.0

    # Menashi (No hand: 0)
    score, name, mult = GamblingDenEngine.evaluate_chinchiro_hand([1, 3, 5])
    assert score == 0
    assert "메나시" in name


def test_high_low_hand_evaluation():
    """Verify High-Low 2d6 evaluation."""
    val, name = GamblingDenEngine.evaluate_high_low_hand([5, 4])
    assert val == 9
    assert "하이" in name

    val, name = GamblingDenEngine.evaluate_high_low_hand([1, 3])
    assert val == 4
    assert "로우" in name

    val, name = GamblingDenEngine.evaluate_high_low_hand([3, 4])
    assert val == 7
    assert "럭키 세븐" in name


def test_play_chinchiro_fair():
    """Test standard round of Chinchiro without cheating."""
    state = _setup_world_for_gambling()
    initial_gold = state.player.gold

    outcome = GamblingDenEngine.play_chinchiro(state, bet_gold=50)
    assert outcome.game_type == "chinchiro"
    assert outcome.bet_gold == 50
    assert len(outcome.player_dice) == 3
    assert len(outcome.dealer_dice) == 3
    assert state.player.gold == initial_gold + outcome.net_gold

    record = state.gambling_record
    assert record.total_games == 1
    assert record.total_games == (record.wins + record.losses + record.draws)


def test_play_high_low_fair():
    """Test standard round of High-Low with prediction."""
    state = _setup_world_for_gambling()
    initial_gold = state.player.gold

    outcome = GamblingDenEngine.play_high_low(state, bet_gold=30, prediction="high")
    assert outcome.game_type == "high_low"
    assert len(outcome.player_dice) == 2
    assert state.player.gold == initial_gold + outcome.net_gold


def test_cheat_success_rigs_rolls():
    """When cheating succeeds, player rigs the dice and claims big winnings."""
    state = _setup_world_for_gambling()
    initial_gold = state.player.gold

    # Mock attempt_cheat to succeed
    with patch.object(GamblingDenEngine, "attempt_cheat", return_value=(True, False, "손기술 성공!")):
        outcome = GamblingDenEngine.play_chinchiro(state, bet_gold=40, cheat_technique="sleight_of_hand")

    assert outcome.is_cheating_attempted is True
    assert outcome.is_caught is False
    assert outcome.player_dice == [1, 1, 1]  # Rigged Pinzoro
    assert outcome.result == "win"
    assert outcome.net_gold > 0
    assert state.player.gold > initial_gold


def test_cheat_caught_triggers_tavern_brawl():
    """When cheating is caught, gold is forfeited, reputation drops, and tavern brawl starts."""
    state = _setup_world_for_gambling()
    initial_reputation = state.player.reputation

    # Mock attempt_cheat to fail (caught!)
    with patch.object(GamblingDenEngine, "attempt_cheat", return_value=(False, True, "사기 적발!")):
        outcome = GamblingDenEngine.play_chinchiro(state, bet_gold=50, cheat_technique="sleight_of_hand")

    assert outcome.result == "caught_cheating"
    assert outcome.is_caught is True
    assert outcome.tavern_brawl_triggered is True
    assert outcome.net_gold == -50

    # Reputation dropped by 15
    assert state.player.reputation == initial_reputation - 15

    # Location blacklisted
    assert "tavern_hall" in state.gambling_record.blacklisted_locations

    # NPCs at tavern became hostile!
    assert state.npcs["npc_gambler_01"].disposition == "hostile"
    assert state.npcs["npc_barkeep_01"].disposition == "hostile"


def test_blacklist_refusal():
    """Blacklisted location refuses further gambling."""
    state = _setup_world_for_gambling()
    state.gambling_record = PlayerGamblingRecord(blacklisted_locations=["tavern_hall"])

    outcome = GamblingDenEngine.play_chinchiro(state, bet_gold=20)
    assert outcome.result == "loss"
    assert "출입 정지" in outcome.narrative_log


def test_two_pass_engine_live_integration():
    """Verify gambling action resolution through TwoPassEngine Pass 1 pipeline."""
    state = _setup_world_for_gambling()

    action = "주점 도박판에 다가가 50골드를 걸고 친치로 주사위를 굴린다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid is True
    assert fact_sheet.gambling_summary is not None
    assert "주점 도박 및 주사위 대결" in fact_sheet.gambling_summary
    prompt_context = fact_sheet.to_prompt_context()
    assert "주점 도박 및 주사위 대결" in prompt_context
    assert "Tavern Brawl" in prompt_context


def test_world_state_serialization_round_trip():
    """Verify WorldState preserves gambling_record across serialization."""
    state = _setup_world_for_gambling()
    state.gambling_record = PlayerGamblingRecord(
        total_games=5,
        wins=3,
        losses=2,
        net_profit=80,
        blacklisted_locations=["shady_alley"],
    )

    state_dict = state.to_dict()
    restored = WorldState.from_dict(state_dict)

    assert restored.gambling_record is not None
    assert restored.gambling_record.total_games == 5
    assert restored.gambling_record.wins == 3
    assert restored.gambling_record.net_profit == 80
    assert "shady_alley" in restored.gambling_record.blacklisted_locations
