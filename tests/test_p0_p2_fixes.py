from src.world.state import WorldState, Location, Item
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


def test_world_facts_summary_sliced():
    """P0-0-3: world_facts가 대량 누적되어도 to_context_summary()에는 최근 10개만 전달되어 토큰 폭발 방지 검증."""
    state = WorldState()
    state.locations["loc1"] = Location(id="loc1", name="중앙 광장", description="광장", exits={}, items=[], npcs=[])
    state.player.location = "loc1"
    state.world_facts = [f"소문 {i}" for i in range(25)]

    summary = state.to_context_summary()
    assert "소문 24" in summary
    assert "소문 15" in summary
    # 0~14번 소문은 프롬프트 요약에서 제외되어야 함
    assert "소문 0" not in summary
    assert "소문 14" not in summary


def test_physical_traces_decay_and_cap():
    """P0-0-3: physical_traces가 15턴 초과 시 자동 소멸(감쇄)되고 최대 10개로 캡되는지 검증."""
    state = WorldState()
    loc = Location(id="loc1", name="골목길", description="어두운 골목", exits={}, items=[], npcs=[])
    state.locations["loc1"] = loc
    state.player.location = "loc1"
    state.turn = 20

    # 오래된 흔적 (턴 1: 19턴 전 -> 15턴 초과로 소멸 대상)
    # 최신 흔적 (턴 10, 15, 20: 15턴 이내 -> 유지)
    loc.physical_traces = [
        {"trace": "오래된 발자국", "turn": 1, "npc_name": "괴한"},
        {"trace": "최근 핏자국 1", "turn": 10, "npc_name": "괴한"},
        {"trace": "최근 핏자국 2", "turn": 15, "npc_name": "괴한"},
        {"trace": "방금 떨어진 동전", "turn": 20, "npc_name": "괴한"},
    ]

    # advance_world_simulation 호출 시 감쇄 로직 작동
    state.advance_world_simulation()

    trace_names = [t["trace"] for t in loc.physical_traces]
    assert "오래된 발자국" not in trace_names
    assert "최근 핏자국 1" in trace_names
    assert "최근 핏자국 2" in trace_names
    assert "방금 떨어진 동전" in trace_names

    # 12개 흔적 추가 시 10개 캡 확인
    loc.physical_traces = [{"trace": f"흔적 {i}", "turn": state.turn, "npc_name": "누군가"} for i in range(12)]
    state.advance_world_simulation()
    assert len(loc.physical_traces) == 10
    assert loc.physical_traces[0]["trace"] == "흔적 2"


def test_history_50_turn_cap_and_sqlite_archive(tmp_path, monkeypatch):
    """P0-0-3: state.append_history로 50턴 초과 시 초과분이 SQLite 아카이브로 이관되고 full history 복원 가능한지 검증."""
    from src.world.persistence import PersistenceManager
    db_file = tmp_path / "test_quilltale.db"
    monkeypatch.setattr(PersistenceManager, "DB_PATH", db_file)

    state = WorldState()
    state.world_id = "test_world_archive_01"

    # 60개 턴 기록 순차 추가
    for t in range(1, 61):
        state.append_history({
            "turn": t,
            "action": f"행동 {t}",
            "narration": f"서사 {t}",
        })

    # 메모리 state.history는 정확히 최근 50개 유지 (턴 11 ~ 60)
    assert len(state.history) == 50
    assert state.history[0]["turn"] == 11
    assert state.history[-1]["turn"] == 60

    # 초과분 10개(턴 1~10)는 SQLite 아카이브에 안전하게 보존
    archived = PersistenceManager.get_archived_turns("test_world_archive_01")
    assert len(archived) == 10
    assert archived[0]["turn"] == 1
    assert archived[-1]["turn"] == 10

    # get_full_history 호출 시 1~60턴 전체가 누락 없이 순서대로 복원
    full_history = PersistenceManager.get_full_history("test_world_archive_01", state.history)
    assert len(full_history) == 60
    assert full_history[0]["turn"] == 1
    assert full_history[59]["turn"] == 60


def test_save_migration_list_trimming_and_archive(tmp_path, monkeypatch):
    """P0-0-3: SaveMigrationEngine이 구버전 세이브의 초과 리스트를 트리밍하고 초과 턴을 SQLite로 이관하는지 검증."""
    from src.persistence.migration import SaveMigrationEngine
    from src.world.persistence import PersistenceManager
    db_file = tmp_path / "migration_test.db"
    monkeypatch.setattr(PersistenceManager, "DB_PATH", db_file)

    raw_save = {
        "save_version": 2,
        "world_id": "migrated_world_01",
        "world_facts": [f"팩트 {i}" for i in range(40)],
        "npcs": {
            "npc1": {
                "name": "상인",
                "off_screen_logs": [f"로그 {i}" for i in range(15)],
            }
        },
        "locations": {
            "loc1": {
                "name": "광장",
                "physical_traces": [{"trace": f"흔적 {i}", "turn": i} for i in range(18)],
            }
        },
        "history": [{"turn": i, "action": f"행동 {i}", "narration": f"서사 {i}"} for i in range(1, 61)],
    }

    migrated = SaveMigrationEngine.migrate(raw_save)

    assert migrated["save_version"] == 3
    # world_facts 30개 캡
    assert len(migrated["world_facts"]) == 30
    assert migrated["world_facts"][-1] == "팩트 39"

    # off_screen_logs 10개 캡
    assert len(migrated["npcs"]["npc1"]["off_screen_logs"]) == 10
    assert migrated["npcs"]["npc1"]["off_screen_logs"][-1] == "로그 14"

    # physical_traces 10개 캡
    assert len(migrated["locations"]["loc1"]["physical_traces"]) == 10

    # history 50개 캡 및 초과분 10개 SQLite 아카이브 확인
    assert len(migrated["history"]) == 50
    assert migrated["history"][0]["turn"] == 11
    archived = PersistenceManager.get_archived_turns("migrated_world_01")
    assert len(archived) == 10
    assert archived[0]["turn"] == 1


def test_player_bot_no_dead_item_import():
    """P0-0-8: player_bot.py 모듈에 미사용 죽은 Item import가 존재하지 않는지 검증."""
    import src.agents.player_bot as pb_mod
    # Item이 전역 네임스페이스에 노출되지 않아야 함
    assert "Item" not in pb_mod.__dict__
    # PlayerBotAgent 인스턴스 정상 생성
    bot = pb_mod.PlayerBotAgent(persona_key="cautious_scholar")
    assert bot is not None


def test_npc_skill_engine_overdraw_wiring(monkeypatch):
    """P0-0-8: npc_skill_engine이 원거리 스킬/무기 사용 시 allow_overdraw 진입점과 정상 연결되는지 검증."""
    from src.world.npc_skill_engine import NPCSkillEngine
    from src.world.state import WorldState, NPC, Item, EquipmentSlots, Skill
    from src.world.dice import DiceEngine

    # d20 굴림 15로 고정하여 명중 보장
    monkeypatch.setattr(DiceEngine, "roll_d20", lambda: 15)

    state = WorldState()
    state.player.health = 100
    state.player.max_health = 100

    # 근력 18인 궁수 NPC (한계 장력 = 18 * 5 = 90 lbs)
    npc = NPC(
        id="archer_01",
        name="정예 저격수",
        description="노련한 활잡이",
        location="loc1",
        health=50,
        max_health=50,
        strength=18,
        agility=16,
        disposition="hostile"
    )
    npc.equipment = EquipmentSlots(weapon="composite_bow")
    state.npcs["archer_01"] = npc

    # 60 lbs 활 (근력 18의 90 lbs 대비 여유 있으므로 오버드로우 시 ratio = min(1.2, 90/60) = 1.2)
    bow = Item(
        id="composite_bow",
        name="강화 합성궁",
        description="강력한 활",
        location="equipment",
        damage=8,
        draw_weight_lbs=60.0,
        physics_tags=["projectile"]
    )
    state.items["composite_bow"] = bow

    # 1. 강궁 스킬 사용 시 -> allow_overdraw=True 적용되어 1.2x 오버드로우 발동
    strong_skill = Skill(
        id="overdraw_shot",
        name="강궁 저격 사격",
        role_type="single_attack",
        resource_type="none",
        resource_cost=0,
        cooldown_turns=2,
    )
    state.skills_db["overdraw_shot"] = strong_skill
    npc.skills = ["overdraw_shot"]

    res_overdraw = NPCSkillEngine.process_npc_combat_turn(npc, state, player_ac=10)
    assert "오버드로우" in res_overdraw["summary_ko"]
    assert "1.20x" in res_overdraw["summary_ko"] or "배율" in res_overdraw["summary_ko"]

    # 2. 일반 사격 스킬 사용 시 -> 기본 만작(1.0x) 유지
    normal_skill = Skill(
        id="normal_shot",
        name="일반 화살 사격",
        role_type="single_attack",
        resource_type="none",
        resource_cost=0,
        cooldown_turns=0,
    )
    state.skills_db["normal_shot"] = normal_skill
    npc.skills = ["normal_shot"]

    res_normal = NPCSkillEngine.process_npc_combat_turn(npc, state, player_ac=10)
    assert "완전 만작" in res_normal["summary_ko"]
    assert "오버드로우" not in res_normal["summary_ko"]


