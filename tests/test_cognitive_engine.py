"""
Tests for NPCCognitiveDeductionEngine, 10-Factor Attitude Matrix,
12-Axis Personality, and 20-Factor Persona in Quilltale TRPG Engine.
"""
import pytest
from src.world.state import WorldState, NPC, Player, Item, NPCPersonality
from src.world.cognitive_engine import (
    NPCCognitiveDeductionEngine,
    HypothesisEvidence,
    HypothesisValidationResult,
    PredictedNPCAction,
    MicroLeakageObservation,
)


@pytest.fixture
def base_world():
    state = WorldState()
    state.player = Player(
        name="테스터",
        location="inn_room",
        gold=50,
        inventory=["healing_herb_01"]
    )
    state.items["poison_vial_01"] = Item(
        id="poison_vial_01",
        name="비상 독약병",
        item_type="consumable",
        description="치명적인 독약",
        location="inn_room"
    )
    state.items["healing_herb_01"] = Item(
        id="healing_herb_01",
        name="약초",
        item_type="consumable",
        description="평범한 회복 약초",
        location="inn_room"
    )
    return state


def test_npc_personality_and_attitude_expansion():
    """Verifies that 12-axis personality, 10-factor attitude, and traits are initialized properly."""
    npc = NPC(id="innkeeper_01", name="바텐더 톰", description="선술집 주인", location="inn_room")
    
    # 6 Core + 6 Extended Personality Axes
    assert npc.personality.altruism == 50
    assert npc.personality.patience == 50
    assert npc.personality.cunning == 50
    assert npc.personality.pride == 50
    assert npc.personality.rationality == 50
    assert npc.personality.neuroticism == 50
    assert npc.personality.deceit == 50
    assert isinstance(npc.personality.traits, list)

    # 10-Factor Attitude Matrix
    assert npc.affinity == 50
    assert npc.fear == 0
    assert npc.debt == 0
    assert npc.trust == 50
    assert npc.respect == 50
    assert npc.envy == 0
    assert npc.pity == 0
    assert npc.dominance == 50
    assert npc.curiosity == 50
    assert npc.disgust == 0

    # Extended Persona Fields
    assert npc.life_defining_moment == ""
    assert "survival" in npc.value_hierarchy
    assert npc.coping_mechanism == ""
    assert npc.public_mask == ""
    assert npc.moral_justification == ""
    assert isinstance(npc.micro_leakage_traits, list)
    assert npc.risk_tolerance == 50


def test_hypothesis_validation_refutes_innocent_npc(base_world):
    """
    Tests Anti-Yes-Man: When player falsely accuses an innocent, altruistic tavern keeper
    of planning to poison them, the engine MUST refute with CONTRADICTED/IMPOSSIBLE and ground evidence.
    """
    innkeeper = NPC(
        id="innkeeper_01",
        name="톰",
        description="온화한 선술집 주인",
        location="inn_room",
        job="주모",
        personality=NPCPersonality(altruism=80, aggression=15, cunning=20, deceit=10),
        taboo="무고한 손님 살상 금지",
        desire="마을 사람들에게 따뜻한 술과 안식처 제공",
        inventory=["healing_herb_01"] # No poison
    )
    innkeeper.trust = 75
    innkeeper.respect = 70
    innkeeper.beliefs = ["플레이어는 매너 좋은 여행자다"]

    result = NPCCognitiveDeductionEngine.evaluate_player_hypothesis(
        innkeeper, "저 주모가 내 술에 독을 타서 살해하려 한다!", base_world
    )

    assert result.target_npc_id == "innkeeper_01"
    assert result.hypothesis_category == "poison"
    assert result.verdict in ["IMPOSSIBLE", "CONTRADICTED"]
    assert result.plausibility_score <= 25
    assert len(result.contradicting_evidence) >= 3
    contra_texts = " ".join(e.evidence_text for e in result.contradicting_evidence)
    assert "이타심" in contra_texts
    assert "금기" in contra_texts
    assert "인벤토리에 독극물" in contra_texts
    assert "[안티 예스맨 절대 지침]" in result.gm_anti_yesman_verdict


def test_hypothesis_validation_confirms_guilty_thief(base_world):
    """
    Tests Reality Check Confirmation: When player suspects a greedy, indebted rogue
    of planning to pickpocket them, the engine validates with PLAUSIBLE / HIGHLY_LIKELY.
    """
    thief = NPC(
        id="rogue_jack",
        name="칼잡이 잭",
        description="수상한 부랑자",
        location="inn_room",
        job="도적",
        personality=NPCPersonality(greed=90, altruism=20, cunning=80, deceit=75),
        desire="오늘 밤 갚아야 할 막대한 도박 빚 청산",
        financial_state="사채업자에게 쫓기는 극심한 빚",
        inventory=[]
    )
    thief.trust = 20
    thief.affinity = 30

    result = NPCCognitiveDeductionEngine.evaluate_player_hypothesis(
        thief, "저 도적이 내 주머니의 금화를 훔치려고 각을 재고 있다", base_world
    )

    assert result.target_npc_id == "rogue_jack"
    assert result.hypothesis_category == "theft"
    assert result.verdict in ["PLAUSIBLE", "HIGHLY_LIKELY", "CONFIRMED"]
    assert result.plausibility_score >= 65
    assert len(result.supporting_evidence) >= 2
    supp_texts = " ".join(e.evidence_text for e in result.supporting_evidence)
    assert "탐욕" in supp_texts
    assert "빚" in supp_texts or "부채" in supp_texts
    assert "[현실 추리 수긍 지침]" in result.gm_anti_yesman_verdict or "[결정적 팩트 확인 지침]" in result.gm_anti_yesman_verdict


def test_autonomous_next_intent_prediction(base_world):
    """Verifies that NPC's next plan is deterministically predicted and synchronized to intention."""
    # Case 1: Panic & Flight on extreme fear
    coward = NPC(
        id="scared_scout",
        name="정찰병 릭",
        description="패닉에 빠진 병사",
        location="inn_room",
        health=10,
        fear=85
    )
    action1 = NPCCognitiveDeductionEngine.predict_autonomous_next_intent(coward, base_world)
    assert action1.action_type == "escape"
    assert "도주" in coward.intention
    assert len(action1.leaked_clues) > 0

    # Case 2: Greedy Theft on high greed and debt
    greedy_thief = NPC(
        id="thief_bob",
        name="소매치기 밥",
        description="굶주린 부랑자",
        location="inn_room",
        personality=NPCPersonality(greed=85),
        financial_state="빚에 쪼들림"
    )
    action2 = NPCCognitiveDeductionEngine.predict_autonomous_next_intent(greedy_thief, base_world)
    assert action2.action_type == "theft"
    assert "소매치기" in greedy_thief.intention
    assert "탐욕" in action2.motive_chain

    # Case 3: Grudge & Assassination
    vengeful = NPC(
        id="vengeful_knight",
        name="복수자 켄",
        description="원한 품은 몰락 기사",
        location="inn_room",
        debt=-80,
        personality=NPCPersonality(aggression=80),
        taboo=""
    )
    action3 = NPCCognitiveDeductionEngine.predict_autonomous_next_intent(vengeful, base_world)
    assert action3.action_type == "assassinate"
    assert "급습" in vengeful.intention or "비수" in vengeful.intention


def test_micro_leakage_detection(base_world):
    """Verifies contested roll for detecting micro-leakage body language."""
    suspicious_npc = NPC(
        id="suspicious_merchant",
        name="상인 그레고리",
        description="수상한 거래상",
        location="inn_room",
        fear=75,
        micro_leakage_traits=["손을 비비며 억지 미소를 지음", "눈동자가 심하게 떨림"]
    )

    obs = NPCCognitiveDeductionEngine.check_micro_leakage(
        suspicious_npc, player_perception=20, state=base_world
    )
    assert isinstance(obs, MicroLeakageObservation)
    assert obs.npc_id == "suspicious_merchant"
    assert len(obs.traits) > 0


def test_attitude_update():
    """Verifies safe modification and clamping of 10-factor attitude matrix."""
    npc = NPC(id="noble_01", name="귀족 카엘", description="오만한 귀족", location="inn_room")
    
    new_trust = NPCCognitiveDeductionEngine.update_attitude(npc, "trust", 30)
    assert new_trust == 80
    assert npc.trust == 80

    new_trust_over = NPCCognitiveDeductionEngine.update_attitude(npc, "trust", 50)
    assert new_trust_over == 100

    new_debt = NPCCognitiveDeductionEngine.update_attitude(npc, "debt", -70)
    assert new_debt == -70
    assert npc.debt == -70


def test_external_llm_prompt_generation():
    """Verifies that external AI prompt is correctly formatted with all 12 axes and 10 attitudes."""
    npc = NPC(
        id="cultist_leader",
        name="광신도 교주",
        description="광기에 찬 교주",
        location="inn_room",
        job="사제",
        personality=NPCPersonality(altruism=10, greed=70, deceit=85, cunning=80),
        life_defining_moment="어릴 적 이단 심문관에게 부모를 잃음",
        public_mask="자비로운 치유자",
        taboo="심연의 신에 대한 모독"
    )
    prompt = NPCCognitiveDeductionEngine.generate_external_llm_prompt(
        npc, hypothesis_text="이 자는 제물을 바치기 위해 의식을 준비하고 있다"
    )
    assert "광신도 교주" in prompt
    assert "Altruism: 10" in prompt
    assert "Deceit: 85" in prompt
    assert "자비로운 치유자" in prompt
    assert "어릴 적 이단 심문관" in prompt
    assert "Player Hypothesis:" in prompt
    assert "Strict Anti-Yes-Man reality check applies" in prompt


def test_world_state_serialization_compatibility():
    """Verifies that adding 10-factor attitude and 12-axis personality preserves 100% save/load round-trip."""
    original_state = WorldState()
    npc = NPC(
        id="npc_test_roundtrip",
        name="시험용 인물",
        description="호환성 테스트",
        location="inn_room",
        personality=NPCPersonality(altruism=77, patience=88, cunning=33),
        trust=65,
        respect=82,
        envy=12,
        life_defining_moment="불타는 수도원 탈출",
        risk_tolerance=70
    )
    original_state.npcs["npc_test_roundtrip"] = npc

    saved_dict = original_state.to_dict()
    loaded_state = WorldState.from_dict(saved_dict)

    loaded_npc = loaded_state.npcs["npc_test_roundtrip"]
    assert loaded_npc.name == "시험용 인물"
    assert loaded_npc.personality.altruism == 77
    assert loaded_npc.personality.patience == 88
    assert loaded_npc.personality.cunning == 33
    assert loaded_npc.trust == 65
    assert loaded_npc.respect == 82
    assert loaded_npc.envy == 12
    assert loaded_npc.life_defining_moment == "불타는 수도원 탈출"
    assert loaded_npc.risk_tolerance == 70


def test_process_npc_cognitive_turn_bounty_hunter_ambush(base_world):
    """Verifies that a greedy/courageous mercenary attacks a wanted player on movement."""
    base_world.player.bounties = {"city_watch": 350}
    base_world.player.disguise = ""

    mercenary = NPC(
        id="merc_karl",
        name="용병 칼",
        description="냉혹한 현상금 사냥꾼",
        location="inn_room",
        job="용병",
        personality=NPCPersonality(greed=80, courage=75, aggression=70)
    )

    outcome = NPCCognitiveDeductionEngine.process_npc_cognitive_turn(
        mercenary, base_world, player_action="골목으로 이동한다"
    )

    assert outcome is not None
    assert outcome["action_type"] == "bounty_hunter_ambush"
    assert outcome["total_bounty"] == 350
    assert mercenary.disposition == "hostile"
    assert "350G" in outcome["summary_ko"]


def test_process_npc_cognitive_turn_snitch(base_world):
    """Verifies that a greedy but cowardly NPC secretly reports a wanted player to guards."""
    base_world.player.bounties = {"kingdom": 500}
    base_world.player.disguise = ""

    cowardly_snitch = NPC(
        id="snitch_pete",
        name="밀고자 피트",
        description="눈치 빠른 부랑배",
        location="inn_room",
        job="부랑자",
        personality=NPCPersonality(greed=85, courage=25, altruism=20)
    )
    cowardly_snitch.trust = 20
    cowardly_snitch.affinity = 20

    outcome = NPCCognitiveDeductionEngine.process_npc_cognitive_turn(
        cowardly_snitch, base_world, player_action="여관 주방을 살펴본다"
    )

    assert outcome is not None
    assert outcome["action_type"] == "bounty_snitch"
    assert "밀고" in outcome["summary_ko"]
    assert any("밀고 발생" in news for news in base_world.pending_breaking_news)


def test_process_npc_cognitive_turn_friendly_warning(base_world):
    """Verifies that an ally NPC warns a wanted player instead of turning them in."""
    base_world.player.bounties = {"city_watch": 400}
    base_world.player.disguise = ""

    loyal_friend = NPC(
        id="friend_elena",
        name="엘레나",
        description="충직한 약초상",
        location="inn_room",
        job="약초상",
        personality=NPCPersonality(altruism=85, loyalty=90, greed=10)
    )
    loyal_friend.affinity = 80
    loyal_friend.trust = 85

    outcome = NPCCognitiveDeductionEngine.process_npc_cognitive_turn(
        loyal_friend, base_world, player_action="가방을 정리한다"
    )

    assert outcome is not None
    assert outcome["action_type"] == "friendly_warning"
    assert "사냥꾼" in outcome["summary_ko"]
    assert loyal_friend.disposition != "hostile"


def test_process_npc_cognitive_turn_cunning_scheme(base_world):
    """Verifies that high cunning NPC schemes indirectly rather than brute forcing."""
    cunning_npc = NPC(
        id="cunning_schemer",
        name="책사 레이븐",
        description="교활한 정보상",
        location="inn_room",
        job="정보상",
        personality=NPCPersonality(cunning=85, greed=60, altruism=30)
    )
    outcome = NPCCognitiveDeductionEngine.process_npc_cognitive_turn(
        cunning_npc, base_world, player_action="지도를 유심히 살핀다"
    )
    assert outcome is not None
    assert outcome["action_type"] == "cunning_scheme"
    assert "간접 공작" in outcome["summary_ko"]


def test_process_npc_cognitive_turn_deceitful_misdirection(base_world):
    """Verifies that high deceit NPC feeds the player false information."""
    deceitful_npc = NPC(
        id="deceitful_liar",
        name="사기꾼 잭",
        description="능청스러운 협잡꾼",
        location="inn_room",
        job="사기꾼",
        personality=NPCPersonality(deceit=90, greed=40, altruism=20)
    )
    outcome = NPCCognitiveDeductionEngine.process_npc_cognitive_turn(
        deceitful_npc, base_world, player_action="남쪽 던전으로 가는 길을 묻는다"
    )
    assert outcome is not None
    assert outcome["action_type"] == "deceitful_misdirection"
    assert "거짓 정보" in outcome["summary_ko"]


def test_process_npc_cognitive_turn_impulsive_hostility(base_world):
    """Verifies that low patience NPC quickly turns hostile under tension."""
    impatient_npc = NPC(
        id="impatient_brute",
        name="다혈질 보그",
        description="성미 급한 용병",
        location="inn_room",
        job="용병",
        personality=NPCPersonality(patience=20, aggression=65)
    )
    outcome = NPCCognitiveDeductionEngine.process_npc_cognitive_turn(
        impatient_npc, base_world, player_action="검을 어루만지며 노려본다"
    )
    assert outcome is not None
    assert outcome["action_type"] == "impulsive_hostility"
    assert outcome["disposition_changed"] == "hostile"
    assert impatient_npc.disposition == "hostile"

