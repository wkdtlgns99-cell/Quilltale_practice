"""
Integration tests for stealth_engine.py wiring into TwoPassEngine and DeterministicFactSheet.
Verifies physical stealth, detection handling, and eavesdropping within the live Pass 1 turn loop.
"""
import pytest
from src.world.state import WorldState, Location, NPC, Player
from src.world.two_pass_engine import TwoPassEngine, DeterministicFactSheet


def create_stealth_test_state() -> WorldState:
    """Helper to set up a controlled WorldState for stealth wiring tests."""
    state = WorldState()
    loc = Location(
        id="corridor",
        name="어두운 회랑",
        description="희미한 촛불만 켜진 고요한 복도.",
        exits={"north": "chamber"},
        npcs=["guard_corridor"],
        traits=["어둠", "조용함"]
    )
    loc.floor_material = "carpet_soft"  # 푹신한 카펫: 발소리 10dB, 진동 0.2 (극저진동)
    loc.lighting_lux = 5.0              # 칠흑 어둠
    loc.ambient_noise_db = 25.0

    guard = NPC(
        id="guard_corridor",
        name="경비병",
        description="순찰 중인 경비병.",
        location="corridor",
        perception=10,
        disposition="neutral"
    )
    guard.dialogue = "내일 새벽 성문을 열고 비밀 수송대를 통과시킬 것이다."

    state.locations["corridor"] = loc
    state.npcs["guard_corridor"] = guard
    state.player.location = "corridor"
    state.player.agility = 16  # 높은 민첩 (고양이 걸음 완충)
    state.player.is_stealthed = False
    return state


def test_compute_pass1_wires_stealth_success():
    """은신/잠입 액션 시 StealthInfiltrationEngine이 Pass 1 루프에서 정상 호출되어 성공을 팩트시트에 기록하는지 검증."""
    state = create_stealth_test_state()
    action = "발끝으로 살금살금 양탄자 위를 걸으며 기척을 죽이고 그림자 속에 숨어든다."

    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid is True
    assert fact_sheet.stealth_summary is not None
    assert "정적" in fact_sheet.stealth_summary or "성공" in fact_sheet.stealth_summary or "통과" in fact_sheet.stealth_summary
    assert any("잠입 성공" in log for log in fact_sheet.quest_progress_logs)

    # Prompt context check
    prompt_context = fact_sheet.to_prompt_context()
    assert "물리 잠입 및 은신 판정" in prompt_context
    assert fact_sheet.stealth_summary in prompt_context


def test_compute_pass1_wires_stealth_failure_alerts_npc():
    """발각 조건(깨진 유리 위 전력 질주 등) 시 팩트시트에 발각 사실과 적대 전환 델타가 설정되는지 검증."""
    state = create_stealth_test_state()
    curr_loc = state.locations["corridor"]
    curr_loc.floor_material = "broken_glass"
    curr_loc.lighting_lux = 1000.0  # 대낮 조도
    curr_loc.ambient_noise_db = 10.0
    state.player.agility = 6  # 둔한 민첩

    action = "깨진 유리 위를 전력 질주로 달려가며 은신을 시도한다."

    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid is True
    assert fact_sheet.stealth_summary is not None
    assert "🚨 잠입 발각!" in fact_sheet.stealth_summary
    assert any("잠입 발각" in log for log in fact_sheet.quest_progress_logs)

    # State delta check: observer guard marked hostile
    delta = fact_sheet.pre_computed_state_delta
    assert "npc_state" in delta
    assert "guard_corridor" in delta["npc_state"]
    assert delta["npc_state"]["guard_corridor"]["disposition"] == "hostile"


def test_compute_pass1_wires_eavesdropping():
    """도청/엿듣기 액션 시 StealthInfiltrationEngine.evaluate_eavesdropping이 정상 호출되는지 검증."""
    state = create_stealth_test_state()
    action = "문틈 너머로 귀를 기울여 경비병의 밀담을 엿듣는다."

    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid is True
    assert fact_sheet.eavesdrop_summary is not None
    assert any("밀담 도청" in log for log in fact_sheet.quest_progress_logs)

    prompt_context = fact_sheet.to_prompt_context()
    assert "물리 음향 도청 및 밀담 청취" in prompt_context
    assert fact_sheet.eavesdrop_summary in prompt_context


def test_player_is_stealthed_state_persistence():
    """Player.is_stealthed 필드가 apply_update 및 직렬화/역직렬화에서 정상 유지되는지 검증."""
    state = WorldState()
    assert state.player.is_stealthed is False

    # Apply delta
    state.apply_update({"player_stealthed": True})
    assert state.player.is_stealthed is True

    # Round-trip serialization
    json_data = state.to_json()
    loaded_state = WorldState.from_json(json_data)
    assert loaded_state.player.is_stealthed is True

    # Un-stealth
    state.apply_update({"player_stealthed": False})
    assert state.player.is_stealthed is False
