"""
Unit and Integration Tests for Gladiator Arena Engine (test_arena_engine.py)
"""

import pytest
from src.world.entities import Player
from src.world.state import WorldState
from src.world.arena_engine import (
    GladiatorOpponent,
    ArenaMatch,
    ArenaActionResult,
    GladiatorCareerRecord,
    GladiatorArenaEngine,
)


class DummyArenaState:
    """Mock state for standalone arena engine tests."""
    def __init__(self, gold=500, health=100, strength=14, constitution=12):
        self.player = Player(
            name="검투테스터",
            health=health,
            max_health=100,
            gold=gold,
            strength=strength,
            constitution=constitution,
            reputation=10,
        )
        self.arena_record = GladiatorCareerRecord(traits=["test_gladiator"])
        self.active_arena_match = None


def test_rule_5_traits_compliance():
    """Verify that all arena dataclasses have traits: List[str]."""
    opp = GladiatorOpponent("op1", "검투사", "칭호", "bronze", 1, 50, 50, 10, 2, "단검")
    match = ArenaMatch("m1", "duel", opp, 100, 20)
    result = ArenaActionResult("attack", True)
    record = GladiatorCareerRecord()

    assert isinstance(opp.traits, list)
    assert isinstance(match.traits, list)
    assert isinstance(result.traits, list)
    assert isinstance(record.traits, list)


def test_arena_serialization_roundtrip():
    """Verify serialization and deserialization of arena data models."""
    opp = GladiatorOpponent("op1", "맹수", "사막의 포식자", "bronze", 2, 60, 60, 12, 3, "발톱")
    match = ArenaMatch("m1", "beast_hunt", opp, 120, 25, player_bet=50, odds=2.0)
    
    match_dict = match.to_dict()
    restored = ArenaMatch.from_dict(match_dict)

    assert restored.match_id == "m1"
    assert restored.opponent.name == "맹수"
    assert restored.player_bet == 50
    assert restored.odds == 2.0


def test_match_listing_generation_by_tier():
    """Verify match listings generated for bronze tier."""
    dummy = DummyArenaState()
    matches = GladiatorArenaEngine.generate_match_listing(dummy)
    assert len(matches) == 3
    assert matches[0].opponent.tier == "bronze"
    assert matches[0].entry_fee > 0


def test_start_match_success_and_insufficient_funds():
    """Verify match entry fee and betting deduction."""
    dummy = DummyArenaState(gold=100)
    matches = GladiatorArenaEngine.generate_match_listing(dummy)
    m = matches[0]  # entry fee 15

    # 1. Success
    res = GladiatorArenaEngine.start_match(dummy, m, player_bet=30)
    assert res.success is True
    assert dummy.player.gold == 100 - (15 + 30)  # 55 gold left
    assert dummy.active_arena_match == m

    # 2. Insufficient funds
    dummy.player.gold = 10
    res_fail = GladiatorArenaEngine.start_match(dummy, m, player_bet=50)
    assert res_fail.success is False
    assert "출전 자금이 부족합니다" in res_fail.narration_logs[0]


def test_arena_combat_turn_attack_and_taunt():
    """Verify combat turn exchanges damage and taunt increases crowd favor."""
    dummy = DummyArenaState(gold=500, health=100)
    matches = GladiatorArenaEngine.generate_match_listing(dummy)
    m = matches[0]
    GladiatorArenaEngine.start_match(dummy, m)
    initial_opp_hp = m.opponent.hp
    initial_favor = m.crowd_favor

    # 1. Attack action
    res_atk = GladiatorArenaEngine.resolve_arena_combat_turn(dummy, m, action_type="attack")
    assert res_atk.success is True
    assert m.opponent.hp < initial_opp_hp
    assert res_atk.damage_dealt > 0

    # 2. Taunt action: favor increases significantly
    res_taunt = GladiatorArenaEngine.resolve_arena_combat_turn(dummy, m, action_type="taunt")
    assert res_taunt.success is True
    assert m.crowd_favor > initial_favor
    assert res_taunt.crowd_favor_delta == 25


def test_arena_combat_turn_heavy_strike_and_parry():
    """Verify heavy strike and parry mechanics."""
    dummy = DummyArenaState(gold=500, health=100)
    matches = GladiatorArenaEngine.generate_match_listing(dummy)
    m = matches[0]
    GladiatorArenaEngine.start_match(dummy, m)

    res_parry = GladiatorArenaEngine.resolve_arena_combat_turn(dummy, m, action_type="parry")
    assert res_parry.success is True
    assert "흘리기 및 반격" in res_parry.narration_logs[0]


def test_arena_finishing_verdict_execute():
    """Verify execution increases infamy (-reputation) and gives blood bonus gold."""
    dummy = DummyArenaState(gold=100)
    matches = GladiatorArenaEngine.generate_match_listing(dummy)
    m = matches[0]
    GladiatorArenaEngine.start_match(dummy, m, player_bet=20)
    m.opponent.hp = 0  # Defeated

    res = GladiatorArenaEngine.resolve_finishing_verdict(dummy, m, verdict="execute")
    assert res.success is True
    assert dummy.arena_record.executions == 1
    assert dummy.arena_record.wins == 1
    assert dummy.player.reputation == 5  # 10 - 5
    assert res.purse_won > m.purse_gold  # Base purse + blood bonus
    assert "피의 처형 선언" in res.narration_logs[0]


def test_arena_finishing_verdict_spare():
    """Verify mercy (spare) increases honor (+reputation) and spares count."""
    dummy = DummyArenaState(gold=100)
    matches = GladiatorArenaEngine.generate_match_listing(dummy)
    m = matches[0]
    GladiatorArenaEngine.start_match(dummy, m, player_bet=0)
    m.opponent.hp = 0  # Defeated

    res = GladiatorArenaEngine.resolve_finishing_verdict(dummy, m, verdict="spare")
    assert res.success is True
    assert dummy.arena_record.spares == 1
    assert dummy.player.reputation == 20  # 10 + 10
    assert "고결한 자비 선언" in res.narration_logs[0]


def test_arena_rank_promotion_to_silver():
    """Verify promotion to silver tier when points exceed 100."""
    dummy = DummyArenaState()
    dummy.arena_record.rank_points = 90
    matches = GladiatorArenaEngine.generate_match_listing(dummy)
    m = matches[0]
    GladiatorArenaEngine.start_match(dummy, m)
    m.opponent.hp = 0

    res = GladiatorArenaEngine.resolve_finishing_verdict(dummy, m, verdict="spare")
    assert dummy.arena_record.rank_tier == "silver"
    assert "계급 승급" in res.narration_logs[-1]


def test_arena_status_summary():
    """Verify Korean arena status summary formatting."""
    dummy = DummyArenaState()
    summary = GladiatorArenaEngine.get_arena_status_summary(dummy)
    assert "콜로세움 투기장 전적" in summary
    assert "브론즈" in summary


def _setup_world_for_arena():
    from src.world.state import Location
    state = WorldState()
    state.player = Player(
        name="투기장의검객",
        location="colosseum_pit",
        health=100,
        gold=1000,
        strength=16,
        constitution=14,
        reputation=10,
    )
    state.locations["colosseum_pit"] = Location(
        id="colosseum_pit",
        name="원형 콜로세움 중앙 모래사장",
        description="수천 명의 관중들이 함성을 내지르는 피와 영광의 투기장이다.",
        exits={},
        items=[],
        npcs=[],
    )
    return state


def test_two_pass_engine_arena_start_and_combat_live_integration():
    """Verify arena match start and combat through TwoPassEngine Pass 1 pipeline."""
    from src.world.two_pass_engine import TwoPassEngine
    state = _setup_world_for_arena()

    # 1. Start match
    action_start = "투기장 결투에 출전하여 50골드를 배팅하고 칼을 뽑아든다"
    f1 = TwoPassEngine.compute_pass1(action_start, state)

    assert f1.is_valid is True
    assert f1.arena_summary is not None
    assert "콜로세움 투기장 전적" in f1.arena_summary
    prompt_context = f1.to_prompt_context()
    assert "콜로세움 투기장 결투 및 처형/자비" in prompt_context

    assert state.active_arena_match is not None
    assert state.active_arena_match.is_active is True

    # 2. Combat round attack
    action_attack = "콜로세움 상대 검투사를 향해 전력으로 강타를 내리친다"
    f2 = TwoPassEngine.compute_pass1(action_attack, state)

    assert f2.is_valid is True
    assert f2.arena_summary is not None


def test_two_pass_engine_arena_verdict_live_integration():
    """Verify finishing verdict execution through Pass 1 pipeline."""
    from src.world.two_pass_engine import TwoPassEngine
    state = _setup_world_for_arena()
    # Start match first
    GladiatorArenaEngine.start_match(state, GladiatorArenaEngine.generate_match_listing(state)[0])
    state.active_arena_match.opponent.hp = 0  # Knocked down

    action_verdict = "쓰러진 검투사의 목을 베어 피의 처형을 선언한다"
    f_verdict = TwoPassEngine.compute_pass1(action_verdict, state)

    assert f_verdict.is_valid is True
    assert state.active_arena_match.is_concluded is True
    assert state.active_arena_match.verdict == "execute"
    assert state.arena_record.executions == 1


def test_world_state_arena_serialization_round_trip():
    """Verify WorldState preserves arena_record and active_arena_match across serialization."""
    state = _setup_world_for_arena()
    state.arena_record = GladiatorCareerRecord(
        rank_tier="gold",
        rank_points=320,
        total_fights=12,
        wins=10,
        losses=2,
        executions=4,
        spares=6,
    )
    match = GladiatorArenaEngine.generate_match_listing(state)[0]
    GladiatorArenaEngine.start_match(state, match, player_bet=100)

    state_dict = state.to_dict()
    restored = WorldState.from_dict(state_dict)

    assert restored.arena_record is not None
    assert restored.arena_record.rank_tier == "gold"
    assert restored.arena_record.wins == 10
    assert restored.active_arena_match is not None
    assert restored.active_arena_match.player_bet == 100

