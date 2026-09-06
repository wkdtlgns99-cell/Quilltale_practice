"""
Unit tests for PosturePoiseEngine (Sekiro-style Posture, Poise, and Guard Break).
Verifies User Decision Q3:
- Multi-source posture buildup: Physical (blocking/unblocked), Magic, and Mental/Terror shock
- Sekiro-style stamina recovery: natural regen * stamina ratio, 2x in guard stance, 0 when stamina exhausted
- Time-based guard break stun: base 1.0s, scales up with combat duration and lower stamina
- Guard break vulnerability: next incoming attack is guaranteed critical hit with +50% bonus damage
"""
import pytest
from src.world.state import Player, NPC
from src.world.poise_engine import PosturePoiseEngine, PosturePoiseState


@pytest.fixture
def test_fighter():
    p = Player(name="검사", constitution=12, stamina=100, max_stamina=100)
    p.poise = 10.0
    p.posture_state = PosturePoiseState().to_dict()
    return p


def test_posture_initialization_and_max(test_fighter):
    state = PosturePoiseEngine.get_state(test_fighter)
    # effective_poise = poise(10.0) + (con(12) - 10)*2.0 = 14.0
    # max_posture = 100.0 + 14.0 * 2.0 = 128.0
    assert state.max_posture == 128.0
    assert state.current_posture_damage == 0.0
    assert not state.is_guard_broken


def test_blocked_vs_unblocked_physical_impact(test_fighter):
    """Blocked attack absorbs HP but heaps 1.6x posture damage."""
    attacker = NPC(id="enemy_boss", name="중갑 기사", description="육중한 갑주를 두른 기사", location="arena", strength=14)

    # 1. Unblocked hit
    is_broken, logs1 = PosturePoiseEngine.apply_physical_impact(
        test_fighter, attacker, weapon_type="blunt", is_blocked=False
    )
    assert not is_broken
    state1 = PosturePoiseEngine.get_state(test_fighter)
    # blunt base 22.0 + (14-10)*1.5 = 28.0
    assert state1.current_posture_damage == 28.0

    # 2. Blocked hit
    is_broken2, logs2 = PosturePoiseEngine.apply_physical_impact(
        test_fighter, attacker, weapon_type="blunt", is_blocked=True
    )
    assert not is_broken2
    state2 = PosturePoiseEngine.get_state(test_fighter)
    # 28.0 + (28.0 * 1.6 = 44.8) = 72.8
    assert state2.current_posture_damage == pytest.approx(72.8, 0.1)
    assert any("방어 충격 흡수" in l for l in logs2)


def test_magic_and_mental_posture_impact(test_fighter):
    """Verifies magic blasts and psychological terror destabilize posture."""
    # Magic blast
    is_broken_mag, m_logs = PosturePoiseEngine.apply_magic_impact(
        test_fighter, spell_element="earth", spell_power=30.0, spell_circle=2
    )
    assert not is_broken_mag
    state = PosturePoiseEngine.get_state(test_fighter)
    # earth mult 1.5 * (30*0.5 + 2*3 = 21) = 31.5
    assert state.current_posture_damage == pytest.approx(31.5, 0.1)

    # Mental shock (User requirement: psychic/terror shock also impacts balance)
    is_broken_men, men_logs = PosturePoiseEngine.apply_mental_impact(
        test_fighter, mental_stress=20.0, fear_source="심연의 공포"
    )
    assert not is_broken_men
    state_after = PosturePoiseEngine.get_state(test_fighter)
    # 31.5 + (20 * 0.6 = 12.0) = 43.5
    assert state_after.current_posture_damage == pytest.approx(43.5, 0.1)
    assert any("정신적 동요와 자세 흔들림" in l for l in men_logs)


def test_sekiro_style_stamina_recovery(test_fighter):
    """Verifies natural recovery scales with stamina, doubles in guard, and stops at 0 stamina."""
    state = PosturePoiseEngine.get_state(test_fighter)
    state.current_posture_damage = 50.0
    PosturePoiseEngine.sync_state(test_fighter, state)

    # Full stamina (100/100): 8.0/sec
    PosturePoiseEngine.recover_posture_time(test_fighter, delta_seconds=2.0)
    state1 = PosturePoiseEngine.get_state(test_fighter)
    # 50.0 - 8.0 * 2.0 = 34.0
    assert state1.current_posture_damage == pytest.approx(34.0, 0.1)

    # In guard stance: 2x acceleration (16.0/sec)
    PosturePoiseEngine.set_blocking_stance(test_fighter, is_blocking=True)
    PosturePoiseEngine.recover_posture_time(test_fighter, delta_seconds=1.0)
    state2 = PosturePoiseEngine.get_state(test_fighter)
    # 34.0 - 16.0 = 18.0
    assert state2.current_posture_damage == pytest.approx(18.0, 0.1)

    # Zero stamina (exhaustion): halts recovery completely
    test_fighter.stamina = 0
    PosturePoiseEngine.recover_posture_time(test_fighter, delta_seconds=5.0)
    state3 = PosturePoiseEngine.get_state(test_fighter)
    assert state3.current_posture_damage == pytest.approx(18.0, 0.1)


def test_guard_break_scaling_stun_duration_and_crit(test_fighter):
    """
    Verifies User Decision Q3:
    - Time-based guard break stun: base 1.0s, scales up with combat duration and lower stamina
    - Critical hit vulnerability during guard break
    """
    state = PosturePoiseEngine.get_state(test_fighter)

    # Case A: Fresh fight (0s), full stamina (100) -> Stun is exactly 1.0s
    state.combat_duration_seconds = 0.0
    test_fighter.stamina = 100
    stun_a = PosturePoiseEngine._calculate_guard_break_stun(test_fighter, state)
    assert stun_a == 1.0

    # Case B: Prolonged fight (120s = +1.0s) with low stamina (20/100 = 80% drained * 1.5 = +1.2s)
    state.combat_duration_seconds = 120.0
    test_fighter.stamina = 20
    stun_b = PosturePoiseEngine._calculate_guard_break_stun(test_fighter, state)
    # 1.0 + 1.0 + 1.2 = 3.2s
    assert stun_b == pytest.approx(3.2, 0.05)

    # Trigger Guard Break with heavy impact
    state.current_posture_damage = state.max_posture - 5.0
    PosturePoiseEngine.sync_state(test_fighter, state)

    is_broken, break_logs = PosturePoiseEngine.apply_physical_impact(
        test_fighter, attacker=None, weapon_type="blunt", is_blocked=True, impact_override=50.0
    )
    assert is_broken is True
    assert any("가드 브레이크 (Guard Break)" in l for l in break_logs)

    state_broken = PosturePoiseEngine.get_state(test_fighter)
    assert state_broken.is_guard_broken is True
    assert state_broken.guard_break_seconds_remaining > 1.0
    assert state_broken.is_blocking_stance is False

    # Next hit deals guaranteed critical damage
    has_crit, crit_bonus, crit_msg = PosturePoiseEngine.consume_guard_break_crit(test_fighter)
    assert has_crit is True
    assert crit_bonus == 0.50
    assert "확정 치명타" in crit_msg

    state_after_crit = PosturePoiseEngine.get_state(test_fighter)
    assert state_after_crit.is_guard_broken is False
