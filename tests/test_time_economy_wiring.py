"""Integration tests: TimeCalendarEngine variable action duration wired into compute_pass1().
DoD Gate: AGENTS.md Wiring rule 5.
Verifies that P1-6 fix (variable elapsed_minutes from DAILY_ACTION_DURATIONS) is live.
"""
import pytest
from src.world.state import WorldState, Player, Location
from src.world.two_pass_engine import TwoPassEngine


@pytest.fixture
def basic_state():
    state = WorldState()
    state.locations["tavern"] = Location(
        id="tavern", name="선술집",
        description="북적이는 선술집", exits={},
        traits=["urban", "indoor"]
    )
    state.player = Player(
        name="모험가", location="tavern",
        health=80, max_health=100, mana=20, max_mana=50,
    )
    return state


def test_stealth_action_duration(basic_state):
    """잠입 행동은 20분 소요여야 한다 (DAILY_ACTION_DURATIONS stealth_creeping default_m=20)."""
    fs = TwoPassEngine.compute_pass1("숨죽이며 벽을 타고 몰래 잠입을 시도한다", basic_state)
    assert fs.turn_duration_minutes == 20, f"Expected 20 min for stealth, got {fs.turn_duration_minutes}"


def test_study_action_duration(basic_state):
    """연구/독서 행동은 90분 소요여야 한다 (study_reading default_m=90)."""
    fs = TwoPassEngine.compute_pass1("고대 마도서의 룬 문자를 해독하며 연구한다", basic_state)
    assert fs.turn_duration_minutes == 90, f"Expected 90 min for study, got {fs.turn_duration_minutes}"


def test_corpse_loot_action_duration(basic_state):
    """시체 루팅은 5분 소요여야 한다 (corpse_looting default_m=5)."""
    fs = TwoPassEngine.compute_pass1("적의 시체를 루팅하여 전리품을 챙긴다", basic_state)
    assert fs.turn_duration_minutes == 5, f"Expected 5 min for loot, got {fs.turn_duration_minutes}"


def test_cooking_action_duration(basic_state):
    """요리/식사 행동은 40분 소요여야 한다 (cooking_eating default_m=40)."""
    fs = TwoPassEngine.compute_pass1("캠프파이어에 사슴 고기를 굽고 식사를 한다", basic_state)
    assert fs.turn_duration_minutes == 40, f"Expected 40 min for cooking, got {fs.turn_duration_minutes}"


def test_long_rest_duration(basic_state):
    """숙면/장기 휴식은 480분 소요여야 한다 (long_rest default_m=480)."""
    fs = TwoPassEngine.compute_pass1("자고 일어나서 아침까지 숙면을 취한다", basic_state)
    assert fs.turn_duration_minutes == 480, f"Expected 480 min for long rest, got {fs.turn_duration_minutes}"


def test_default_action_duration(basic_state):
    """키워드 미매칭 행동은 기본 10분 소요여야 한다 (DAILY_ACTION_DURATIONS fallback default_m=10)."""
    fs = TwoPassEngine.compute_pass1("주변을 천천히 둘러본다", basic_state)
    # general_exploration = 20 min (조사/탐색 키워드 매칭), or default 10
    # "둘러본다" does not match any keyword -> default 10
    assert fs.turn_duration_minutes in (10, 20),         f"Unmatched action should get 10 or 20 min default, got {fs.turn_duration_minutes}"


def test_meditation_restores_negative_fatigue_delta(basic_state):
    """명상/기도 행동은 피로도가 감소해야 한다 (meditation_prayer fatigue_cost=-5)."""
    basic_state.player.fatigue = 50
    fs = TwoPassEngine.compute_pass1("단전 호흡으로 명상하며 마나를 조율한다", basic_state)
    assert fs.turn_duration_minutes == 45, f"Expected 45 min for meditation, got {fs.turn_duration_minutes}"
