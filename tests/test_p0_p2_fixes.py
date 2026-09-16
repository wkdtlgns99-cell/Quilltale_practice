import os
import pytest
from src.world.state import WorldState, Player, Location, Item
from src.agents.player_bot import PlayerBotAgent
from src.llm.claude import ClaudeLLM
from src.world.economy_engine import EconomyEngine
from src.world.status_engine import StatusEffectEngine
from src.world.attack_physics_engine import AttackPhysicsEngine
from app import take_action


def test_player_bot_low_hp_with_potion_no_name_error():
    """P0-1: 플레이어 체력 < 35% 시 Item 미임포트로 인한 NameError가 발생하지 않는지 검증."""
    bot = PlayerBotAgent(persona_key="cautious_scholar")
    state = WorldState()
    state.locations["loc1"] = Location(id="loc1", name="시작의 방", description="아늑한 방", exits={}, items=[], npcs=[])
    state.player.location = "loc1"
    state.player.health = 20
    state.player.max_health = 100
    state.player.inventory = ["hp_potion_1", "unknown_item_999"]
    state.items["hp_potion_1"] = Item(id="hp_potion_1", name="하급 체력 회복 포션", description="포션", location="inventory")

    # NameError 없이 정상적으로 포션 복용 행동이 반환되어야 함
    decision = bot.decide_action(state)
    assert "포션" in decision or "들이킨다" in decision or "태세" in decision


def test_player_bot_low_hp_without_potion_safe():
    """P0-1: 플레이어 체력 < 35%이고 포션이 없을 때 방어 태세 정상 반환 검증."""
    bot = PlayerBotAgent(persona_key="cautious_scholar")
    state = WorldState()
    state.locations["loc1"] = Location(id="loc1", name="시작의 방", description="아늑한 방", exits={}, items=[], npcs=[])
    state.player.location = "loc1"
    state.player.health = 20
    state.player.max_health = 100
    state.player.inventory = ["iron_dagger"]
    state.items["iron_dagger"] = Item(id="iron_dagger", name="철 단검", description="단검", location="inventory")

    decision = bot.decide_action(state)
    assert "방어 태세" in decision or "물러선다" in decision


def test_claude_llm_without_api_key_no_crash(monkeypatch):
    """P0-2, P0-0-1: ANTHROPIC_API_KEY 환경변수가 없을 때 KeyError 없이 초기화되고 에러 응답 반환 검증."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)

    claude = ClaudeLLM()
    assert claude._model == "claude-sonnet-4-6"
    assert claude._client is None
    assert "claude-sonnet-4-6" in claude.candidate_models

    resp = claude.generate("안녕")
    assert "[오류:" in resp.text
    assert "API 키가 설정되지 않아" in resp.text


def test_claude_llm_model_env_override(monkeypatch):
    """P0-2, P0-0-1: ANTHROPIC_MODEL 환경변수로 기본 모델 오버라이드 지원 및 candidate_models 선두 배치 검증."""
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-custom")
    claude = ClaudeLLM()
    assert claude._model == "claude-3-7-sonnet-custom"
    assert claude.candidate_models[0] == "claude-3-7-sonnet-custom"
    assert len(claude.candidate_models) >= 4


def test_claude_llm_fallback_chain_on_error(monkeypatch):
    """P0-0-1: 첫 번째 모델이 404/not_found 등으로 실패할 때 다음 후보 모델로 자동 폴백 검증."""
    from unittest.mock import MagicMock

    claude = ClaudeLLM(api_key="dummy-key")
    assert claude._client is not None

    call_history = []

    def mock_create(**kwargs):
        model = kwargs.get("model")
        call_history.append(model)
        if model == "claude-sonnet-4-6":
            raise RuntimeError("404 model not_found: model is retired")
        # 두 번째 모델(claude-3-7-sonnet-20250219)에서 성공
        mock_msg = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "폴백 성공"
        mock_msg.content = [mock_content]
        return mock_msg

    claude._client.messages.create = mock_create

    resp = claude.generate("테스트 프롬프트")
    assert resp.text == "폴백 성공"
    assert resp.model == "claude-3-7-sonnet-20250219"
    assert call_history[0] == "claude-sonnet-4-6"
    assert call_history[1] == "claude-3-7-sonnet-20250219"



def test_app_take_action_none_state_guarded():
    """P0-3: world_state_json 파싱 실패 시 AttributeError 없이 안전한 에러 안내 및 뷰 반환 검증."""
    invalid_json = "{ corrupted json"
    chat_history = []
    curr_img = None

    results = take_action("앞으로 이동", chat_history, invalid_json, curr_img)
    assert len(results) == 10
    ret_history = results[0]
    assert len(ret_history) == 2
    assert "세계 상태를 불러오지 못했습니다" in ret_history[1]["content"]


def test_economy_engine_remove_poison_cured_check():
    """P2-6: 독 치료 서비스 이용 시 치료 대상 상태이상이 없으면 골드 미차감 및 False 반환 검증."""
    state = WorldState()
    state.player.gold = 100
    
    # 1. 상태이상이 없는 상태에서 해독 서비스 호출
    success, msg = EconomyEngine.use_service(state, "moonlit_apothecary", "remove_poison")
    assert success is False
    assert state.player.gold == 100  # 골드 차감 없어야 함
    assert "치료할 중독 또는 유해 상태이상이 없습니다" in msg

    # 2. 독 상태이상 적용 후 해독 서비스 호출
    StatusEffectEngine.apply_status(state.player, "poison", duration=3)
    assert "poison" in state.player.status_effects

    success2, msg2 = EconomyEngine.use_service(state, "moonlit_apothecary", "remove_poison")
    assert success2 is True
    assert state.player.gold == 60  # 40G 차감
    assert "poison" not in state.player.status_effects
    assert "치료 완료" in msg2


def test_attack_physics_can_draw_bow_overdraw_ratio():
    """P2-7: can_draw_bow에서 allow_overdraw 옵션에 따라 정상적으로 오버드로우 배율(최대 1.2) 반환 검증."""
    # 근력 15(한계 150 lbs), 활 장력 120 lbs -> ratio = 150/120 = 1.25 -> cap 1.2
    can_draw_def, ratio_def, msg_def = AttackPhysicsEngine.can_draw_bow(15, 120.0, allow_overdraw=False)
    assert can_draw_def is True
    assert ratio_def == 1.0
    assert "완전 만작" in msg_def

    can_draw_od, ratio_od, msg_od = AttackPhysicsEngine.can_draw_bow(15, 120.0, allow_overdraw=True)
    assert can_draw_od is True
    assert ratio_od == 1.2
    assert "오버드로우 만작" in msg_od


def test_json_repair_engine_auxiliary_repair():
    """P0-0-4: 보조 LLM 응답 복구 repair_json 검증 (마크다운 코드블록, trailing comma, plain dict 반환)."""
    from src.llm.resilience import JSONRepairEngine

    # 1. 일반 JSON
    res = JSONRepairEngine.repair_json('{"news": "새로운 소문"}')
    assert res == {"news": "새로운 소문"}

    # 2. 마크다운 코드블록 감싸진 JSON
    res_md = JSONRepairEngine.repair_json('```json\n{"news": "광산에서 괴수 출현"}\n```')
    assert res_md == {"news": "광산에서 괴수 출현"}

    # 3. Trailing comma 복구
    res_comma = JSONRepairEngine.repair_json('{"chronicle": "영웅의 여정이 끝났다",}')
    assert res_comma == {"chronicle": "영웅의 여정이 끝났다"}

    # 4. 문자열 내 줄바꿈 unescaped 처리
    res_newline = JSONRepairEngine.repair_json('{"narrative": "첫 줄\n둘째 줄"}')
    assert res_newline is not None
    assert "첫 줄" in res_newline.get("narrative", "")

    # 5. 완전한 비JSON 텍스트 입력 시 None 반환 (크래시 없음)
    res_none = JSONRepairEngine.repair_json("일반 텍스트 에러 메시지")
    assert res_none is None


def test_llm_quota_exhausted_fallback_korean():
    """P0-0-7: repair_and_parse에 영문 예외/쿼터 고갈 에러 주입 시 영문 메시지 서사 유출 차단 및 한국어 폴백 검증."""
    from src.llm.resilience import JSONRepairEngine

    error_msg = "All Gemini models and API keys exhausted. Last error: 429 RESOURCE_EXHAUSTED"
    result = JSONRepairEngine.repair_and_parse(error_msg)

    narration = result.get("narration", "")
    assert "Gemini" not in narration
    assert "exhausted" not in narration
    assert "429" not in narration
    assert "RESOURCE_EXHAUSTED" not in narration
    assert "어지럽게 요동치며" in narration or "상황을" in narration


def test_game_master_process_turn_llm_exception_safe_korean_narration():
    """P0-0-7: GameMasterAgent.process_turn 실행 중 LLM 예외 발생 시 영문 에러 유출 없이 한국어 서사 반환 검증."""
    from src.agents.game_master import GameMasterAgent
    from src.llm.base import BaseLLM, LLMResponse

    class BrokenLLM(BaseLLM):
        def generate(self, prompt: str, system: str = "") -> LLMResponse:
            raise RuntimeError("All Gemini models and API keys exhausted. Last error: 429 RESOURCE_EXHAUSTED")

        def generate_json(self, prompt: str, system: str = "") -> str:
            raise RuntimeError("All Gemini models and API keys exhausted. Last error: 429 RESOURCE_EXHAUSTED")

    gm = GameMasterAgent(llm=BrokenLLM())
    state = WorldState()
    state.locations["loc1"] = Location(id="loc1", name="성문 앞", description="성문", exits={}, items=[], npcs=[])
    state.player.location = "loc1"

    # process_turn 실행 시 크래시 없이 100% 한국어 서사가 반환되어야 함
    result_turn = gm.process_turn("주변을 둘러본다", state)
    narration = result_turn.get("narration", "")

    assert "Gemini" not in narration
    assert "exhausted" not in narration
    assert "429" not in narration
    assert "RESOURCE_EXHAUSTED" not in narration
    assert len(narration) > 0
    # 한국어 포함 확인
    assert any('\uac00' <= ch <= '\ud7a3' for ch in narration)


def test_invalid_action_zero_mutation_guaranteed():
    """P0-0-2 (QT-F01): 무효 행동 시 상태 틱, 환경 피해, 월드 시뮬레이션 등이 전혀 선행 반영되지 않는 0-변이 보장 검증."""
    from src.world.two_pass_engine import TwoPassEngine
    from src.world.status_engine import StatusEffectEngine

    state = WorldState()
    state.locations["loc1"] = Location(id="loc1", name="성문 앞", description="성문", exits={}, items=[], npcs=[])
    state.player.location = "loc1"
    state.player.health = 100
    state.player.max_health = 100
    state.turn = 5

    # 독 상태이상 부여 (정상 틱 진행 시 턴당 HP -10 피해 발생)
    StatusEffectEngine.apply_status(state.player, "poison", duration=3)
    assert "poison" in state.player.status_effects

    # 불가능한 행동 (ActionValidator IMPOSSIBLE_POWER_PATTERNS에서 is_valid=False 기각되는 입력)
    impossible_action = "지구를 파괴한다"

    fact_sheet = TwoPassEngine.compute_pass1(impossible_action, state)

    # 1. 행동 기각 확인
    assert fact_sheet.is_valid is False
    assert fact_sheet.rejection_reason is not None
    assert "인간의 한계" in fact_sheet.rejection_reason or "불가능" in fact_sheet.rejection_reason

    # 2. 플레이어 체력 보존 확인 (선행 독 틱 피해 0-변이)
    assert state.player.health == 100

    # 3. 턴 및 상태이상 지속시간 보존 확인 (틱 카운트다운 미실행)
    assert state.turn == 5
    assert state.player.status_effects["poison"].duration_turns == 3

    # 4. 상태이상 틱 로그 및 사전 계산 델타 공백 확인
    assert len(fact_sheet.status_tick_logs) == 0
    assert fact_sheet.pre_computed_state_delta == {}




