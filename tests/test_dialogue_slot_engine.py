"""
Unit Tests for Deterministic DialogueSlotEngine.

Validates:
1. Template loading and caching from data/templates/dialogue_slots.json
2. 8 Archetype tone and vocabulary alignment
3. Stress and emotion-based physical gestures
4. Relationship-aware greeting resolution (hostile, neutral, friendly)
5. 12-axis personality trait tail attachment
6. 100% Deterministic repeatability with seed
7. Data structure traits compliance (Rule 5)
"""
import pytest
from src.world.state import NPC, WorldState, Player, Location
from src.world.psychology_engine import apply_personality_template
from src.world.dialogue_slot_engine import DialogueSlotEngine


@pytest.fixture
def base_world_state():
    state = WorldState()
    player = Player(
        name="영웅",
        health=100,
        max_health=100,
        mana=50,
        max_mana=50,
        gold=200,
        location="loc_town",
    )
    state.player = player

    scholar = NPC(
        id="npc_scholar",
        name="엘레나",
        description="고문서를 연구하는 학자.",
        location="loc_town",
        disposition="friendly"
    )
    apply_personality_template(scholar, "cautious_scholar")

    loc = Location(
        id="loc_town",
        name="평원의 도서관",
        description="조용한 도서관 마을.",
        terrain="town",
        npcs=["npc_scholar"],
        exits={}
    )
    state.locations["loc_town"] = loc
    state.current_location_id = "loc_town"
    state.npcs["npc_scholar"] = scholar
    return state


def test_dialogue_slot_engine_template_load():
    """Verify templates load from disk with all expected archetypes and gestures."""
    DialogueSlotEngine.reset_cache()
    data = DialogueSlotEngine.load_templates()
    assert "archetype_tones" in data
    assert "gestures" in data
    assert "trait_tails" in data
    assert len(data["archetype_tones"]) >= 8
    assert "cautious_scholar" in data["archetype_tones"]
    assert "cynical_mercenary" in data["archetype_tones"]


def test_greeting_relationship_resolution():
    """Verify greeting changes based on relationship score."""
    npc = NPC(id="guard_dan", name="단", description="경비병", location="gate")
    apply_personality_template(npc, "devoted_knight")
    templates = DialogueSlotEngine.load_templates()["archetype_tones"]["devoted_knight"]["intents"]

    # Hostile
    res_hostile = DialogueSlotEngine.assemble_dialogue(npc, intent="greeting", relationship_score=15)
    assert res_hostile.intent == "greeting_hostile"
    assert res_hostile.body in templates["greeting_hostile"]

    # Neutral
    res_neutral = DialogueSlotEngine.assemble_dialogue(npc, intent="greeting", relationship_score=50)
    assert res_neutral.intent == "greeting_neutral"
    assert res_neutral.body in templates["greeting_neutral"]

    # Friendly
    res_friendly = DialogueSlotEngine.assemble_dialogue(npc, intent="greeting", relationship_score=85)
    assert res_friendly.intent == "greeting_friendly"
    assert res_friendly.body in templates["greeting_friendly"]


def test_stress_and_emotion_gestures():
    """Verify physical gestures match stress levels and acute emotions."""
    npc = NPC(id="scholar_elena", name="엘레나", description="학자", location="library")
    apply_personality_template(npc, "cautious_scholar")

    # Low stress calm
    npc.stress = 10
    npc.emotion_state = {}
    res_calm = DialogueSlotEngine.assemble_dialogue(npc, intent="greeting_neutral")
    assert any(w in res_calm.gesture for w in ["차분", "담담", "느긋", "여유", "미소"])

    # High stress
    npc.stress = 75
    res_high = DialogueSlotEngine.assemble_dialogue(npc, intent="greeting_neutral")
    assert any(w in res_high.gesture for w in ["핏발", "손톱", "움츠", "가쁘", "뒤쪽"])

    # Breakdown
    npc.stress = 95
    res_break = DialogueSlotEngine.assemble_dialogue(npc, intent="greeting_neutral")
    assert any(w in res_break.gesture for w in ["사시나무", "헐떡", "초점", "뒤틀", "비틀", "비명"])

    # Acute anger overriding stress
    npc.stress = 20
    npc.emotion_state = {"anger": 85}
    res_anger = DialogueSlotEngine.assemble_dialogue(npc, intent="greeting_neutral")
    assert any(w in res_anger.gesture for w in ["주먹", "살벌", "일그러", "탁자", "바득"])


def test_trait_tail_attachment():
    """Verify personality traits append appropriate tails."""
    npc = NPC(id="merchant_roth", name="로스", description="상인", location="market")
    apply_personality_template(npc, "cynical_mercenary")

    # Give high greed
    npc.personality.greed = 88
    npc.personality.suspicion = 40
    npc.personality.altruism = 10
    npc.personality.pride = 30

    res = DialogueSlotEngine.assemble_dialogue(npc, intent="quest_offer")
    assert res.tail != ""
    assert any(w in res.tail for w in ["착수금", "보수", "보상", "수고비", "보너스"])

    # Give high suspicion
    npc.personality.greed = 40
    npc.personality.suspicion = 95
    res_susp = DialogueSlotEngine.assemble_dialogue(npc, intent="quest_offer")
    assert any(w in res_susp.tail for w in ["뒤따라", "함정", "엿듣", "숨기는"])


def test_determinism_and_seed_variance():
    """Verify identical inputs yield identical text, while seed modifier varies output."""
    npc = NPC(id="adventurer_leo", name="레오", description="모험가", location="plains")
    apply_personality_template(npc, "reckless_adventurer")

    res1 = DialogueSlotEngine.assemble_dialogue(npc, intent="quest_accept", seed_modifier=42)
    res2 = DialogueSlotEngine.assemble_dialogue(npc, intent="quest_accept", seed_modifier=42)
    assert res1.full_text == res2.full_text

    # Different seeds yield valid outputs
    res3 = DialogueSlotEngine.assemble_dialogue(npc, intent="quest_accept", seed_modifier=999)
    assert isinstance(res3.full_text, str)
    assert len(res3.full_text) > 10


def test_dialogue_result_dataclass_traits():
    """Verify DialogueResult includes traits and to_dict conforms to standard."""
    npc = NPC(id="inquisitor_malik", name="말릭", description="심문관", location="sanctuary")
    apply_personality_template(npc, "zealous_inquisitor")
    res = DialogueSlotEngine.assemble_dialogue(npc, intent="threat_reaction")

    assert "dialogue_result" in res.traits
    assert "zealous_inquisitor" in res.traits
    data = res.to_dict()
    assert data["speaker_name"] == "말릭"
    assert data["archetype"] == "zealous_inquisitor"
    assert data["intent"] == "threat_reaction"
    assert isinstance(data["traits"], list)


def test_dialogue_intent_classification_and_routing():
    """Verify classify_intent categorizes routine vs deep inquiries correctly."""
    from src.world.dialogue_slot_engine import IntentRoutingResult

    # 1. Routine intents (All 0-token, requires_llm=False)
    cases = [
        ("경비병 단에게 인사를 건넨다", "greeting", False),
        ("상점에 진열된 물건을 둘러본다", "shop_browse", False),
        ("강철 장검을 구매하겠다", "shop_buy", False),
        ("그 위험한 의뢰를 수락하겠소", "quest_accept", False),
        ("그런 터무니없는 일은 거절한다", "quest_reject", False),
        ("도움이 필요한 일감이나 의뢰가 있소?", "quest_offer", False),
        ("칼을 겨누며 위협한다", "threat_reaction", False),
    ]
    for action, expected_intent, expected_llm in cases:
        routing = DialogueSlotEngine.classify_intent(action)
        assert routing.intent == expected_intent
        assert routing.requires_llm is expected_llm
        assert "deterministic_slot" in routing.traits or "greeting" in routing.traits

    # 2. Deep inquiry / free-form questions (Requires LLM API)
    deep_cases = [
        "너 어제 밤에 왜 영주를 배신했는가?",
        "이 성 밑에 숨겨진 비밀 통로가 어디인지 말해라",
        "음모의 배후에 누가 있는지 알고 싶다",
        "너의 진짜 목적이 무엇인가?",
    ]
    for deep_act in deep_cases:
        routing = DialogueSlotEngine.classify_intent(deep_act)
        assert routing.intent == "deep_inquiry"
        assert routing.requires_llm is True
        assert "llm_required" in routing.traits

    # 3. IntentRoutingResult dataclass traits & to_dict
    res = IntentRoutingResult(intent="test", requires_llm=False, confidence=0.99)
    assert isinstance(res.traits, list)
    assert res.to_dict()["confidence"] == 0.99


def test_two_pass_engine_dialogue_routing_wiring(base_world_state):
    """Verify TwoPassEngine.compute_pass1 records dialogue routing and requires_llm flag."""
    from src.world.two_pass_engine import TwoPassEngine

    state = base_world_state
    # 1. Routine interaction
    fs_routine = TwoPassEngine.compute_pass1("엘레나에게 인사를 건넨다", state)
    assert fs_routine.dialogue_slot_summary is not None
    assert fs_routine.extra_flags.get("requires_llm") is False
    assert fs_routine.extra_flags.get("dialogue_routing", {}).get("intent") == "greeting"

    # 2. Deep inquiry
    fs_deep = TwoPassEngine.compute_pass1("엘레나에게 왜 그 연구를 비밀로 숨겼는지 캐묻는다", state)
    assert fs_deep.dialogue_slot_summary is not None
    assert fs_deep.extra_flags.get("requires_llm") is True
    assert fs_deep.extra_flags.get("dialogue_routing", {}).get("intent") == "deep_inquiry"


def test_game_master_routine_dialogue_zero_token_bypass(base_world_state):
    """Verify GameMasterAgent serves routine dialogue instantly with 0 LLM calls."""
    from src.agents.game_master import GameMasterAgent
    from src.llm.base import BaseLLM

    call_count = {"count": 0}

    class CountingLLM(BaseLLM):
        def generate(self, prompt: str, system_prompt: str = "") -> str:
            call_count["count"] += 1
            return '{"narration": "LLM response"}'

        def generate_json(self, prompt: str, system_prompt: str = "") -> str:
            call_count["count"] += 1
            return '{"narration": "LLM response"}'

    llm = CountingLLM()
    gm = GameMasterAgent(llm)
    state = base_world_state

    # 1. Routine dialogue: Must NOT invoke LLM generate_json (0 tokens!)
    res_routine = gm.process_turn("엘레나에게 인사를 건넨다", state)
    assert res_routine is not None
    assert call_count["count"] == 0, "Routine dialogue must bypass LLM (0 token cost)"
    assert "엘레나" in res_routine["narration"]

    # 2. Deep inquiry: MUST invoke LLM generate_json
    res_deep = gm.process_turn("엘레나에게 왜 그 연구를 비밀로 숨겼는지 캐묻는다", state)
    assert res_deep is not None
    assert call_count["count"] == 1, "Deep inquiry must route to LLM"


def test_two_pass_engine_dialogue_persona_anchoring_in_prompt(base_world_state):
    """Verify Pass 1 attaches persona anchor and serializes it in prompt context for deep inquiry."""
    from src.world.two_pass_engine import TwoPassEngine

    state = base_world_state
    fs = TwoPassEngine.compute_pass1("엘레나에게 왜 그 연구를 비밀로 숨겼는지 캐묻는다", state)
    assert fs.dialogue_persona_anchor is not None
    pa = fs.dialogue_persona_anchor
    assert pa["name"] == "엘레나"
    assert pa["archetype"] == "cautious_scholar"
    assert pa["archetype_ko"] == "신중한 학자"
    assert len(pa["speech_style"]) > 5
    assert len(pa["gesture"]) > 2

    prompt_ctx = fs.to_prompt_context()
    assert "🎭 [NPC 페르소나 및 화법 앵커링 (PERSONA ANCHORING)]" in prompt_ctx
    assert "엘레나" in prompt_ctx
    assert "신중한 학자" in prompt_ctx


def test_game_master_deep_inquiry_system_prompt_injection(base_world_state):
    """Verify GameMasterAgent injects NPC persona rules into dynamic_system_prompt on deep inquiry."""
    from src.agents.game_master import GameMasterAgent
    from src.llm.base import BaseLLM

    captured = {"system_prompt": ""}

    class SpyLLM(BaseLLM):
        def generate(self, prompt: str, system_prompt: str = "") -> str:
            captured["system_prompt"] = system_prompt
            return '{"narration": "엘레나가 조심스럽게 입을 열었습니다."}'

        def generate_json(self, prompt: str, system_prompt: str = "") -> str:
            captured["system_prompt"] = system_prompt
            return '{"narration": "엘레나가 조심스럽게 입을 열었습니다."}'

    llm = SpyLLM()
    gm = GameMasterAgent(llm)
    state = base_world_state

    gm.process_turn("엘레나에게 왜 그 연구를 비밀로 숨겼는지 캐묻는다", state)
    sys_p = captured["system_prompt"]
    assert "[🎭 대상 NPC 화법 및 페르소나 엄수 규칙]" in sys_p
    assert "엘레나" in sys_p
    assert "신중한 학자" in sys_p


def test_pass2_sanitizer_dialogue_speaker_grounding(base_world_state):
    """Verify sanitize_pass2_result anchors NPC speaker name when LLM completely omits it."""
    from src.world.two_pass_engine import TwoPassEngine

    state = base_world_state
    fs = TwoPassEngine.compute_pass1("엘레나에게 왜 그 연구를 비밀로 숨겼는지 캐묻는다", state)

    # Simulated LLM hallucination: completely omitted who was speaking
    raw_result = {"narration": "그건 오래전 봉인된 금서에 적힌 내용이었소.", "state_update": {}}
    sanitized = TwoPassEngine.sanitize_pass2_result(raw_result, fs, state)

    assert "[엘레나]" in sanitized["narration"]
    assert "그건 오래전 봉인된 금서에 적힌 내용이었소." in sanitized["narration"]


