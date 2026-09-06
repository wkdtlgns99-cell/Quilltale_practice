"""
Unit tests for ToxicologyToleranceEngine in Quilltale TRPG.
Tests potion diminishing returns (tolerance), acute liver toxicity threshold at 100,
User Decision Q1 world time metabolism, and 8-hour rest full reset.
"""
import pytest
from src.world.state import Player
from src.world.toxicology_engine import (
    ToxicologyToleranceEngine, PotionToxicityState
)


@pytest.fixture
def wounded_player():
    return Player(
        name="전사 바란",
        health=20,
        max_health=100,
        stamina=80,
        max_stamina=100
    )


def test_toxicology_specs_and_traits():
    """Verifies state dataclass and traits."""
    state_obj = PotionToxicityState()
    assert len(state_obj.traits) > 0
    assert "toxicology" in state_obj.traits
    assert state_obj.liver_toxicity == 0
    assert state_obj.potion_tolerance == 0.0


def test_potion_diminishing_returns_and_tolerance_growth(wounded_player):
    """
    Tests chugging consecutive potions accumulates tolerance:
    Dose 1: 0% tolerance -> full 30 HP
    Dose 2: 15% tolerance -> 25 HP
    Dose 3: 30% tolerance -> 21 HP
    """
    # Dose 1: 0% tolerance
    heal1, logs1 = ToxicologyToleranceEngine.ingest_potion(
        wounded_player, "치유 물약", base_heal=30, toxicity_increase=25
    )
    assert heal1 == 30
    assert wounded_player.health == 50
    st1 = ToxicologyToleranceEngine.get_state(wounded_player)
    assert st1.liver_toxicity == 25
    assert st1.potion_tolerance == 0.15

    # Dose 2: 15% tolerance
    heal2, logs2 = ToxicologyToleranceEngine.ingest_potion(
        wounded_player, "치유 물약", base_heal=30, toxicity_increase=25
    )
    assert heal2 == 25  # int(30 * 0.85) = 25
    assert wounded_player.health == 75
    st2 = ToxicologyToleranceEngine.get_state(wounded_player)
    assert st2.liver_toxicity == 50
    assert st2.potion_tolerance == 0.30
    assert any("약물 내성으로 힐량 15% 감쇄됨" in l for l in logs2)


def test_acute_toxicology_poisoning_at_100(wounded_player):
    """
    Tests 4th consecutive potion exceeds 100 liver toxicity, triggering acute poisoning:
    backlash damage (-15 HP), vomiting, and stamina drained to 0.
    """
    st = ToxicologyToleranceEngine.get_state(wounded_player)
    st.liver_toxicity = 80
    st.potion_tolerance = 0.30
    ToxicologyToleranceEngine.sync_state(wounded_player, st)

    heal, logs = ToxicologyToleranceEngine.ingest_potion(
        wounded_player, "강력 치유 물약", base_heal=40, toxicity_increase=25
    )
    # 80 + 25 = 105 -> Capped at 100 -> Acute Poisoning triggered!
    st_after = ToxicologyToleranceEngine.get_state(wounded_player)
    assert st_after.liver_toxicity == 100
    assert any("급성 약물 중독 격발" in l for l in logs)
    assert any("스태미나 0 고갈" in l for l in logs)
    assert wounded_player.stamina == 0


def test_world_time_metabolism_decay(wounded_player):
    """
    User Decision Q1:
    In-game world time naturally metabolizes liver toxicity (5 per 30 minutes).
    Tolerance stays until full rest.
    """
    st = ToxicologyToleranceEngine.get_state(wounded_player)
    st.liver_toxicity = 40
    st.potion_tolerance = 0.30
    ToxicologyToleranceEngine.sync_state(wounded_player, st)

    # 60 minutes elapse (2 decay cycles * 5 = -10 toxicity)
    logs = ToxicologyToleranceEngine.process_time_metabolism(wounded_player, elapsed_minutes=60)
    assert len(logs) > 0
    assert any("간 대사 작용" in l for l in logs)
    st_after = ToxicologyToleranceEngine.get_state(wounded_player)
    assert st_after.liver_toxicity == 30  # 40 - 10
    # Tolerance remains intact
    assert st_after.potion_tolerance == 0.30


def test_campsite_full_rest_complete_reset(wounded_player):
    """
    User Decision Q1 (Option B):
    8-hour full sleep at campsite completely resets both liver toxicity and potion tolerance!
    """
    st = ToxicologyToleranceEngine.get_state(wounded_player)
    st.liver_toxicity = 75
    st.potion_tolerance = 0.45
    ToxicologyToleranceEngine.sync_state(wounded_player, st)

    reset_logs = ToxicologyToleranceEngine.reset_on_full_rest(wounded_player)
    assert len(reset_logs) > 0
    assert any("간 대사 및 약물 내성 완전 초기화" in l for l in reset_logs)

    st_cleared = ToxicologyToleranceEngine.get_state(wounded_player)
    assert st_cleared.liver_toxicity == 0
    assert st_cleared.potion_tolerance == 0.0
    assert st_cleared.doses_taken == 0
