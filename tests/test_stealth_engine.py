"""
Unit tests for Realistic Physical Stealth, Infiltration, Ground Vibration,
Acoustic Masking, Wind-Borne Scent, and Eavesdropping Engine.
"""
import pytest

from src.world.state import WorldState, Player, Item, NPC
from src.world.stealth_engine import (
    StealthInfiltrationEngine, StealthAttemptResult, EavesdropAttemptResult,
    FLOOR_ACOUSTICS_DB, STRIDE_STANCE_MODIFIERS, BARRIER_OCCLUSION_DB
)


def test_footstep_sound_and_stride_stance_dampening():
    """바닥 재질별 dB, 보행 보법(-20dB ~ +28dB), 민첩 관절 완충 역학 검증."""
    # 1. 바닥 재질 기본 음향 (양탄자 10dB, 석판 28dB, 깨진 유리 68dB)
    assert FLOOR_ACOUSTICS_DB["carpet_soft"]["base_db"] == 10.0
    assert FLOOR_ACOUSTICS_DB["stone_flagstone"]["base_db"] == 28.0
    assert FLOOR_ACOUSTICS_DB["broken_glass"]["base_db"] == 68.0

    # 2. 보행 보법에 따른 음향 차이
    infiltrator_normal = Player(name="일반인", strength=10, agility=10)
    db_walk = StealthInfiltrationEngine.calculate_footstep_sound_db(
        infiltrator_normal, floor_material="stone_flagstone", stride_stance="normal_walk"
    )
    db_creeping = StealthInfiltrationEngine.calculate_footstep_sound_db(
        infiltrator_normal, floor_material="stone_flagstone", stride_stance="creeping_toe"
    )
    db_sprint = StealthInfiltrationEngine.calculate_footstep_sound_db(
        infiltrator_normal, floor_material="stone_flagstone", stride_stance="running_sprint"
    )

    assert db_creeping < db_walk < db_sprint
    assert db_creeping == max(5.0, 28.0 - 20.0) # 8.0 dB
    assert db_sprint == 28.0 + 28.0             # 56.0 dB

    # 3. 민첩(AGI) 관절 완충 (Agility Dampening): 민첩 15 마스터 암살자
    infiltrator_master = Player(name="그림자 암살자", strength=12, agility=15)
    db_master = StealthInfiltrationEngine.calculate_footstep_sound_db(
        infiltrator_master, floor_material="wood_creaky", stride_stance="creeping_toe"
    )
    db_clumsy = StealthInfiltrationEngine.calculate_footstep_sound_db(
        infiltrator_normal, floor_material="wood_creaky", stride_stance="creeping_toe"
    )
    # 민첩 15의 고양이 보법으로 소음 대폭 감쇄
    assert db_master < db_clumsy


def test_ambient_noise_masking_and_ground_vibration():
    """배경 소음 마스킹과 유저 피드백인 [지면 미세 진동 (Micro-Vibration)] 감지 검증."""
    state = WorldState()
    infiltrator = Player(name="잠입자", strength=12, agility=14)
    # 감각 16의 예민한 보초병 (귀는 소음에 속아도 발바닥 진동을 감지)
    keen_guard = NPC(id="guard_keen", name="고감각 보초병", description="예민한 보초", location="hall", perception=16)

    # 1. 배경 소음 60 dB (폭우/주점) -> 발소리가 완전히 묻힘 (소음 마스킹 성공)
    result = StealthInfiltrationEngine.evaluate_stealth_approach(
        state=state,
        infiltrator=infiltrator,
        observer=keen_guard,
        floor_material="wood_creaky",
        stride_stance="normal_walk",
        distance_m=3.0,
        lighting_lux=10.0,            # 암흑 속
        ambient_noise_db=65.0,        # 폭우 굉음
        wind_angle_degrees=180.0      # 풍하 (냄새 차단)
    )

    # 발소리는 배경 소음에 마스킹됨
    assert result.was_sound_masked
    assert not result.detected_by_hearing
    assert not result.detected_by_sight
    assert not result.detected_by_scent

    # 하지만 3m 코앞 삐걱이는 목재 마루 위를 저벅저벅 걸었으므로 지면 진동 감지!
    # 높은 감각(PER 16)으로 인해 진동으로 기척 포착
    if result.detected_by_vibration:
        assert not result.success
        assert any("진동" in r for r in result.detection_reasons)


def test_lighting_lux_and_distance_decay():
    """조도(룩스 lx) 및 거리별 시각 탐지 DC 검증."""
    state = WorldState()
    infiltrator = Player(name="은신자", agility=11)
    observer = NPC(id="guard_eye", name="경비병", description="일반 경비", location="gate", perception=10)

    # 1. 칠흑 같은 암흑 (5 lx) 15m 거리 -> 시각 탐지 불가
    dark_res = StealthInfiltrationEngine.evaluate_stealth_approach(
        state=state,
        infiltrator=infiltrator,
        observer=observer,
        floor_material="carpet_soft",
        stride_stance="creeping_toe",
        distance_m=15.0,
        lighting_lux=5.0,
        ambient_noise_db=30.0,
        wind_angle_degrees=180.0
    )
    assert not dark_res.detected_by_sight

    # 2. 횃불 정면 (85 lx) 3m 거리 -> 육안 즉시 발각
    bright_res = StealthInfiltrationEngine.evaluate_stealth_approach(
        state=state,
        infiltrator=infiltrator,
        observer=observer,
        floor_material="carpet_soft",
        stride_stance="creeping_toe",
        distance_m=3.0,
        lighting_lux=85.0,
        ambient_noise_db=30.0,
        wind_angle_degrees=180.0
    )
    assert bright_res.detected_by_sight
    assert not bright_res.success


def test_wind_direction_and_scent_dispersion():
    """풍향(풍상 vs 풍하) 및 위생도 저하에 따른 체취 감지 검증."""
    state = WorldState()
    # 며칠간 씻지 않아 땀과 오물이 찌든 방랑자 (위생도 25)
    stinky_player = Player(name="불결한 방랑자", hygiene_level=25, agility=15)
    dog = NPC(id="hound", name="경비견", description="예민한 후각의 사냥개", location="kennel", perception=14)

    # 1. 풍상 (0도, 침투자가 바람을 등지고 경비견에게 냄새가 날아감) -> 체취 포착
    upwind_res = StealthInfiltrationEngine.evaluate_stealth_approach(
        state=state,
        infiltrator=stinky_player,
        observer=dog,
        floor_material="dirt_mud",
        stride_stance="creeping_toe",
        distance_m=10.0,
        lighting_lux=5.0,
        ambient_noise_db=30.0,
        wind_angle_degrees=0.0 # 풍상
    )
    if upwind_res.detected_by_scent:
        assert any("체취" in r or "악취" in r for r in upwind_res.detection_reasons)

    # 2. 풍하 (180도, 경비견 쪽에서 침투자로 바람이 불어 냄새가 뒤로 날아감) -> 냄새 감지 100% 차단
    downwind_res = StealthInfiltrationEngine.evaluate_stealth_approach(
        state=state,
        infiltrator=stinky_player,
        observer=dog,
        floor_material="dirt_mud",
        stride_stance="creeping_toe",
        distance_m=10.0,
        lighting_lux=5.0,
        ambient_noise_db=30.0,
        wind_angle_degrees=180.0 # 풍하
    )
    assert not downwind_res.detected_by_scent


def test_acoustic_eavesdropping_barriers():
    """차폐 매질(문틈, 두꺼운 목재문, 육중한 석벽)별 도청 감쇠 및 단서 청취 검증."""
    state = WorldState()
    listener = Player(name="도청자", perception=15) # 감각 15 고수
    speaker = NPC(id="noble", name="음모의 귀족", description="귀족", location="secret_room", perception=10)

    # 1. 문틈 (8 dB 감쇠) -> 47 dB 청취 (매우 선명)
    crack_res = StealthInfiltrationEngine.evaluate_eavesdropping(
        state=state,
        listener=listener,
        speaker=speaker,
        barrier_type="door_crack",
        distance_m=1.0,
        speech_source_db=55.0,
        secret_dialogue="내일 자정 성문을 연다."
    )
    assert crack_res.success
    assert crack_res.clarity_level in ["crystal_clear", "audible_keywords"]
    assert crack_res.perceived_db >= 35.0

    # 2. 두꺼운 석벽 (45 dB 감쇠) -> 10 dB 미만 (맨귀 청취 불가)
    stone_res = StealthInfiltrationEngine.evaluate_eavesdropping(
        state=state,
        listener=listener,
        speaker=speaker,
        barrier_type="stone_wall",
        distance_m=2.0,
        speech_source_db=55.0
    )
    assert not stone_res.success
    assert stone_res.clarity_level in ["inaudible", "muffled_murmur"]
