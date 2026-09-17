"""
Tests for P2-5: LLM JSON Repair Pipeline Unification (JSONRepairEngine).
Verifies AST literal_eval fallback, resilient parsing across auxiliary LLM methods,
generate_world_news_tick integration, list cap policies, and eval_runner judge resilience.
"""
from unittest.mock import MagicMock
from src.llm.resilience import JSONRepairEngine
from src.world.state import WorldState, Location, Player, NPC
from src.agents.game_master import GameMasterAgent
from eval_runner import judge_memory_utilisation, judge_factual_consistency


def test_repair_json_ast_single_quote_fallback():
    """Verify JSONRepairEngine.repair_json successfully parses Python-style single-quoted dict strings."""
    single_quoted = "{'news': '광산 마을에 거대한 상단이 당도했습니다.', 'source': '상인 알드릭'}"
    res = JSONRepairEngine.repair_json(single_quoted)
    assert res is not None
    assert isinstance(res, dict)
    assert res.get("news") == "광산 마을에 거대한 상단이 당도했습니다."
    assert res.get("source") == "상인 알드릭"


def test_repair_and_parse_ast_single_quote_fallback():
    """Verify JSONRepairEngine.repair_and_parse handles single-quoted dicts without falling back to error text."""
    single_quoted_narration = "{'narration': '짙은 안개 속에서 차가운 칼날이 번뜩입니다.', 'scene_changed': True}"
    result = JSONRepairEngine.repair_and_parse(single_quoted_narration)
    assert result is not None
    assert "짙은 안개 속에서 차가운 칼날이 번뜩입니다." in result["narration"]
    assert result["scene_changed"] is True


def test_repair_json_malformed_variations():
    """Verify repair_json handles markdown blocks, trailing commas, and unescaped newlines."""
    # 1. Markdown codeblock
    md_text = "```json\n{\"chronicle\": \"불타는 성채의 최후\", \"survivors\": 12}\n```"
    res_md = JSONRepairEngine.repair_json(md_text)
    assert res_md is not None
    assert res_md.get("chronicle") == "불타는 성채의 최후"

    # 2. Trailing commas
    trailing = '{"items": ["단검", "회복약",], "gold": 150,}'
    res_trailing = JSONRepairEngine.repair_json(trailing)
    assert res_trailing is not None
    assert res_trailing.get("gold") == 150

    # 3. Unescaped newlines inside string
    un_newlines = '{"summary": "첫 번째 문장입니다.\n두 번째 문장입니다."}'
    res_newlines = JSONRepairEngine.repair_json(un_newlines)
    assert res_newlines is not None
    assert "첫 번째" in res_newlines.get("summary", "")

    # 4. Completely invalid text returns None without exception
    assert JSONRepairEngine.repair_json("502 Bad Gateway: Server Error") is None
    assert JSONRepairEngine.repair_json("") is None


def test_generate_world_news_tick_with_markdown_fence():
    """Verify generate_world_news_tick repairs markdown-fenced LLM response and updates feed and facts."""
    state = WorldState(
        turn=10,
        world_name="아르카나",
        world_genre="다크 판타지",
        player=Player(name="용사", location="tavern"),
        locations={"tavern": Location(id="tavern", name="선술집", description="낡은 선술집", exits={})},
    )
    npc = NPC(id="marta", name="마르타", description="선술집 바텐더", location="tavern")
    npc.off_screen_logs = ["골목길에서 정체불명의 도적단이 목격되었습니다."]
    state.npcs["marta"] = npc

    mock_llm = MagicMock()
    mock_llm.generate_json.return_value = "```json\n{\"news\": \"골목길 도적단이 왕실 마차를 습격했다는 흉흉한 소문이 돕니다.\"}\n```"

    gm = GameMasterAgent(llm=mock_llm)
    news = gm.generate_world_news_tick(state)

    assert news == "골목길 도적단이 왕실 마차를 습격했다는 흉흉한 소문이 돕니다."
    assert any("골목길 도적단" in item for item in state.world_news_feed)
    assert any("골목길 도적단" in item for item in state.world_facts)


def test_generate_world_news_tick_no_logs_returns_none():
    """Verify generate_world_news_tick returns None immediately if no NPCs have off-screen logs."""
    state = WorldState(
        turn=10,
        world_name="아르카나",
        world_genre="판타지",
        player=Player(name="용사", location="tavern"),
        locations={"tavern": Location(id="tavern", name="선술집", description="낡은 선술집", exits={})},
    )
    mock_llm = MagicMock()
    gm = GameMasterAgent(llm=mock_llm)

    news = gm.generate_world_news_tick(state)
    assert news is None
    assert mock_llm.generate_json.call_count == 0


def test_generate_world_news_tick_cap_limits():
    """Verify world_news_feed and world_facts are strictly capped at 30 items."""
    state = WorldState(
        turn=10,
        world_name="아르카나",
        world_genre="판타지",
        player=Player(name="용사", location="tavern"),
        locations={"tavern": Location(id="tavern", name="선술집", description="낡은 선술집", exits={})},
    )
    npc = NPC(id="barkeep", name="주모", description="여관 주인", location="tavern")
    npc.off_screen_logs = ["활동 로그"]
    state.npcs["barkeep"] = npc

    state.world_news_feed = [f"구 소식 {i}" for i in range(35)]
    state.world_facts = [f"구 사실 {i}" for i in range(35)]

    mock_llm = MagicMock()
    mock_llm.generate_json.return_value = '{"news": "새로운 세계적 대사건 발생!"}'

    gm = GameMasterAgent(llm=mock_llm)
    gm.generate_world_news_tick(state)

    assert len(state.world_news_feed) <= 30
    assert len(state.world_facts) <= 30
    assert "(턴 10) 새로운 세계적 대사건 발생!" in state.world_news_feed[-1]


def test_process_turn_wires_world_news_on_10th_turn():
    """Verify process_turn invokes generate_world_news_tick on 10th turn and decorates narration."""
    state = WorldState(
        turn=9,  # apply_update will increment to 10
        world_name="아르카나",
        world_genre="판타지",
        player=Player(name="용사", location="tavern"),
        locations={"tavern": Location(id="tavern", name="선술집", description="낡은 선술집", exits={})},
    )
    npc = NPC(id="guard", name="경비병", description="초소 경비병", location="tavern")
    npc.off_screen_logs = ["성문 경비가 대폭 강화되었습니다."]
    state.npcs["guard"] = npc

    mock_llm = MagicMock()
    # First call: GM turn generation, second call: world news tick
    mock_llm.generate_json.side_effect = [
        '{"narration": "선술집 문을 열고 밖으로 나섭니다.", "state_update": {}}',
        '{"news": "성문 경비가 삼엄해져 여행자들의 불만이 고조되고 있습니다."}',
    ]

    mock_mem = MagicMock()
    gm = GameMasterAgent(llm=mock_llm, memory_manager=mock_mem)
    turn_res = gm.process_turn("밖으로 나간다", state)

    assert state.turn == 10
    assert "선술집 문을 열고 밖으로 나섭니다." in turn_res["narration"]
    assert "세간에 떠도는 소문" in turn_res["narration"]
    assert "성문 경비가 삼엄해져" in turn_res["narration"]
    assert len(state.world_news_feed) == 1


def test_eval_runner_judges_resilient_to_markdown():
    """Verify eval_runner judge functions parse markdown-fenced LLM responses cleanly."""
    mock_llm = MagicMock()
    mock_llm.generate_json.side_effect = [
        "```json\n{\"reflects_memory\": true, \"confidence\": 0.95, \"reason\": \"상호작용 반영됨\"}\n```",
        "```json\n{\"is_consistent\": true, \"confidence\": 0.90, \"violation\": \"\"}\n```",
    ]

    mock_mem = MagicMock()
    mock_mem.turn = 1
    mock_mem.emotional_tone = "wary"
    mock_mem.significance = 3
    mock_mem.description = "플레이어의 위협적인 태도"

    res_mem = judge_memory_utilisation(mock_llm, "서사 내용", [mock_mem], "마르타")
    assert res_mem["reflects_memory"] is True
    assert res_mem["confidence"] == 0.95

    res_fact = judge_factual_consistency(mock_llm, "서사 내용", "세계 사실 컨텍스트")
    assert res_fact["is_consistent"] is True
    assert res_fact["violation"] == ""


def test_world_state_from_dict_restores_world_news_feed():
    """Verify WorldState.from_dict preserves world_news_feed roundtrip."""
    raw = {
        "world_name": "테스트계",
        "turn": 10,
        "world_news_feed": ["(턴 10) 남부 항구 무역선 침몰"],
        "world_facts": ["[소문] 남부 항구 무역선 침몰"],
    }
    state = WorldState.from_dict(raw)
    assert state.world_news_feed == ["(턴 10) 남부 항구 무역선 침몰"]
    assert state.world_facts == ["[소문] 남부 항구 무역선 침몰"]
