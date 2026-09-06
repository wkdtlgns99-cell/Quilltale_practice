"""
Unit tests for PupilAdaptationEngine (Sensory Physics & Pupil Light Transition).
Verifies User Decision Q2:
- Strictly time-based (seconds)
- Bright (1000 lx) -> Darkness (5 lx): 20.0s adaptation delay, impaired vision
- Pirate Eye-Patch Tactic: Pre-adapted eye under patch swaps immediately (0.0s penalty)
- Pitch Darkness -> Blinding Flash: 2.0s flash blindness without shaded goggles
- Shaded Goggles: Completely blocks flash blindness (0.0s penalty)
- Non-combat adapt_eyes_action safely clears adaptation impairment
"""
import pytest
from src.world.state import Player
from src.world.pupil_adaptation_engine import PupilAdaptationEngine, PupilAdaptationState


@pytest.fixture
def test_player():
    p = Player(name="탐험가", location="dungeon_entrance")
    p.pupil_state = PupilAdaptationState().to_dict()
    return p


def test_bright_to_dark_adaptation_delay(test_player):
    """Transition from daylight (2000 lx) into pitch black cave (5 lx)."""
    success, msg = PupilAdaptationEngine.check_illumination_transition(
        test_player, from_lux=2000.0, to_lux=5.0
    )

    assert success is False
    assert "동공 암적응 지연" in msg
    state = PupilAdaptationEngine.get_state(test_player)
    assert state.is_impaired is True
    assert state.seconds_remaining == 20.0
    assert "20.0초" in state.impairment_reason

    # Tick 10 seconds
    logs = PupilAdaptationEngine.tick_adaptation_seconds(test_player, delta_seconds=10.0)
    state = PupilAdaptationEngine.get_state(test_player)
    assert state.is_impaired is True
    assert state.seconds_remaining == 10.0

    # Tick remaining 10 seconds -> Vision recovered
    logs2 = PupilAdaptationEngine.tick_adaptation_seconds(test_player, delta_seconds=10.0)
    state = PupilAdaptationEngine.get_state(test_player)
    assert state.is_impaired is False
    assert state.seconds_remaining == 0.0
    assert any("시각 회복" in l for l in logs2)


def test_pirate_eye_patch_tactic_instant_dark_adaptation(test_player):
    """Verifies User Q2 Eye Patch Tactic: 0s penalty on dark transition."""
    # Equip eyepatch
    PupilAdaptationEngine.equip_eye_patch(test_player, equip=True)
    state = PupilAdaptationEngine.get_state(test_player)
    assert state.has_eye_patch is True

    # Transition into pitch darkness
    success, msg = PupilAdaptationEngine.check_illumination_transition(
        test_player, from_lux=2500.0, to_lux=3.0
    )

    assert success is True
    assert "안대 전술 (Eye Patch Tactic)" in msg
    assert "지연 0초" in msg

    state_after = PupilAdaptationEngine.get_state(test_player)
    assert state_after.is_impaired is False
    assert state_after.seconds_remaining == 0.0


def test_eye_patch_manual_swap_action(test_player):
    """If already impaired in darkness, swapping eyepatch immediately cures impairment."""
    PupilAdaptationEngine.equip_eye_patch(test_player, equip=True)
    state = PupilAdaptationEngine.get_state(test_player)
    state.is_impaired = True
    state.impairment_reason = "동공 암적응 중"
    state.seconds_remaining = 15.0
    PupilAdaptationEngine.sync_state(test_player, state)

    swap_msg = PupilAdaptationEngine.swap_eye_patch_action(test_player)
    assert "안대 전술" in swap_msg
    assert "암적응 지연 0초" in swap_msg

    state_after = PupilAdaptationEngine.get_state(test_player)
    assert state_after.is_impaired is False
    assert state_after.seconds_remaining == 0.0


def test_pitch_dark_to_flash_blindness_and_goggles(test_player):
    """Darkness into flash: 2.0s blind without goggles, 0s with goggles."""
    # 1. Without goggles
    success, msg = PupilAdaptationEngine.check_illumination_transition(
        test_player, from_lux=5.0, to_lux=4000.0, is_flash=True
    )
    assert success is False
    assert "섬광 눈부심" in msg
    state = PupilAdaptationEngine.get_state(test_player)
    assert state.is_impaired is True
    assert state.seconds_remaining == 2.0

    # 2. With shaded goggles
    PupilAdaptationEngine.equip_shaded_goggles(test_player, equip=True)
    success2, msg2 = PupilAdaptationEngine.check_illumination_transition(
        test_player, from_lux=5.0, to_lux=5000.0, is_flash=True
    )
    assert success2 is True
    assert "차광 고글 (Shaded Goggles)" in msg2
    state2 = PupilAdaptationEngine.get_state(test_player)
    assert state2.is_impaired is False
    assert state2.seconds_remaining == 0.0


def test_adapt_eyes_action_non_combat(test_player):
    """Voluntary waiting action to safely complete dark adaptation."""
    state = PupilAdaptationEngine.get_state(test_player)
    state.is_impaired = True
    state.seconds_remaining = 20.0
    state.impairment_reason = "동공 암적응 중"
    PupilAdaptationEngine.sync_state(test_player, state)

    res = PupilAdaptationEngine.adapt_eyes_action(test_player, wait_seconds=20.0)
    assert "동공 암적응 완료" in res
    state_after = PupilAdaptationEngine.get_state(test_player)
    assert state_after.is_impaired is False
    assert state_after.seconds_remaining == 0.0
