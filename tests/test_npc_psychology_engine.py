"""
Comprehensive Unit Tests for NPC Psychology Subsystems (Phase 4-8)
Validates:
1. 8 Archetype personality templates, deep-copy safety, and seeded variance
2. 14-Factor multi-emotion triggering, personality sensitivity, decay, and action modifiers
3. Independent psychological stress (0-100), 5 stages, and persona-aligned breakdown behavior
4. Causal trauma trigger matching, stress amplification, and fear escalation
5. Multi-entity 9-axis relationship matrix, cache invalidation threshold, and legacy player attitude sync
"""
import pytest
from src.world.state import NPC, NPCPersonality
from src.world.psychology_engine import (
    PERSONALITY_TEMPLATES, apply_personality_template,
    EmotionEngine, VALID_EMOTIONS, StressEngine,
    TraumaEngine, STANDARD_TRAUMA_REGISTRY,
    RelationshipEngine, CANONICAL_RELATIONSHIP_AXES
)


def test_personality_templates_and_variance():
    """Verify all 8 templates exist and generate distinct individual variance without template mutation."""
    assert len(PERSONALITY_TEMPLATES) == 8
    assert "cautious_scholar" in PERSONALITY_TEMPLATES
    assert "zealous_inquisitor" in PERSONALITY_TEMPLATES

    scholar_base = PERSONALITY_TEMPLATES["cautious_scholar"].personality_axes["rationality"]

    npc1 = NPC(id="scholar_1", name="학자 1", description="", location="library")
    npc2 = NPC(id="scholar_2", name="학자 2", description="", location="library")

    apply_personality_template(npc1, "cautious_scholar", seed_variance=10)
    apply_personality_template(npc2, "cautious_scholar", seed_variance=99)

    # Both are scholars, but individual scores differ slightly due to seeded variance
    assert npc1.archetype_template == "cautious_scholar"
    assert npc2.archetype_template == "cautious_scholar"
    assert abs(npc1.personality.rationality - scholar_base) <= 10
    assert abs(npc2.personality.rationality - scholar_base) <= 10
    assert (npc1.personality.altruism != npc2.personality.altruism or
            npc1.personality.greed != npc2.personality.greed or
            npc1.personality.rationality != npc2.personality.rationality)

    # Global template remains untouched
    assert PERSONALITY_TEMPLATES["cautious_scholar"].personality_axes["rationality"] == scholar_base


def test_emotion_simulation_and_decay():
    """Verify emotion triggering, personality scaling, concurrent states, decay, and action modifiers."""
    npc_neurotic = NPC(id="neurotic_npc", name="불안한 자", description="", location="inn")
    npc_neurotic.personality.neuroticism = 90
    npc_neurotic.personality.courage = 20

    npc_stoic = NPC(id="stoic_npc", name="냉철한 자", description="", location="inn")
    npc_stoic.personality.neuroticism = 10
    npc_stoic.personality.courage = 85

    # Trigger same fear event
    res1 = EmotionEngine.trigger_emotion(npc_neurotic, "fear", 30, source="scary_noise", duration=3)
    res2 = EmotionEngine.trigger_emotion(npc_stoic, "fear", 30, source="scary_noise", duration=3)

    # Neurotic NPC feels stronger fear than stoic
    assert res1["intensity"] > res2["intensity"]
    assert "fear" in npc_neurotic.emotion_state

    # Add concurrent excitement and anger
    EmotionEngine.trigger_emotion(npc_neurotic, "excitement", 25, source="gold_found", duration=2)
    EmotionEngine.trigger_emotion(npc_neurotic, "anger", 50, source="insult", duration=4)

    assert len(npc_neurotic.emotion_state) == 3
    dominant_emo, dom_int = EmotionEngine.get_dominant_emotion(npc_neurotic)
    assert dominant_emo in ("fear", "anger")
    assert dom_int >= 35

    # Action modifiers reflect fear/anger
    mods = EmotionEngine.get_action_modifiers(npc_neurotic)
    assert mods["attack"] > 0 or mods["escape"] > 0

    # Test tick decay
    expired = EmotionEngine.decay_emotions(npc_neurotic)
    # Intensity should decrease
    assert npc_neurotic.emotion_state["anger"]["intensity"] < 50


def test_stress_accumulation_and_breakdown():
    """Verify stress scaling, 5 stages, recovery, and persona-aligned breakdown behavior."""
    npc = NPC(id="stressed_guard", name="경비병", description="", location="gate")
    npc.personality.aggression = 85
    npc.personality.courage = 60
    npc.personality.neuroticism = 40

    assert StressEngine.get_stress_stage(npc.stress) == "normal"

    # Accumulate stress
    StressEngine.add_stress(npc, 35, "overwork")
    assert StressEngine.get_stress_stage(npc.stress) in ("normal", "reactive")

    StressEngine.add_stress(npc, 60, "siege_attack")
    assert npc.stress >= 70
    assert StressEngine.get_stress_stage(npc.stress) in ("impaired", "severe_distortion", "breakdown")

    # Push to breakdown (>= 90)
    StressEngine.add_stress(npc, 50, "fatal_pressure")
    assert npc.stress >= 90
    assert StressEngine.get_stress_stage(npc.stress) == "breakdown"

    # Aggressive guard exhibits homicidal rage in breakdown
    breakdown_act = StressEngine.evaluate_breakdown_behavior(npc)
    assert breakdown_act == "homicidal_rage"

    # Stress recovery
    StressEngine.recover_stress(npc, 60, "peaceful_rest")
    assert npc.stress < 50
    assert StressEngine.get_stress_stage(npc.stress) in ("normal", "reactive")


def test_trauma_activation_chain():
    """Verify trauma matching against event keywords, fear induction, and avoidance bias."""
    npc = NPC(id="traumatized_veteran", name="참전용사", description="", location="tavern")
    npc.traumas.append("fire_disaster")

    # Irrelevant event: no activation
    res_none = TraumaEngine.evaluate_trauma_trigger(npc, "평화로운 시냇물 소리가 들린다.")
    assert res_none is None

    # Relevant event: flame / fire
    res_fire = TraumaEngine.evaluate_trauma_trigger(npc, "주점 한구석에서 거대한 불길과 검은 연기가 치솟았다!")
    assert res_fire is not None
    assert res_fire["trauma_tag"] == "fire_disaster"
    assert res_fire["avoidance_action"] == "escape"

    # Verify stress and fear were raised
    assert npc.stress > 0
    assert "fear" in npc.emotion_state
    assert npc.trauma_runtime["fire_disaster"]["intensity"] > 0

    # Recover trauma
    TraumaEngine.recover_trauma(npc, "fire_disaster", recovery_amount=20)
    assert npc.trauma_runtime["fire_disaster"]["intensity"] <= 15


def test_relationship_engine_and_legacy_sync():
    """Verify multi-axis relationship deltas, version bump on delta >= 5, and player attitude synchronization."""
    npc = NPC(
        id="merchant_garrick",
        name="상인 가릭",
        description="",
        location="market",
        trust=45,
        affinity=50,
        respect=50,
        fear=10
    )

    # 1. Player relationship initialized from legacy fields
    rel_player = RelationshipEngine.get_or_create_relationship(npc, "player")
    assert rel_player["trust"] == 45
    assert rel_player["affection"] == 50
    assert rel_player["fear"] == 10

    initial_version = npc.state_version

    # 2. Small delta (< 5): does NOT bump state_version
    RelationshipEngine.apply_relationship_delta(
        npc, "player", {"trust": 2}, reason="small polite greeting"
    )
    assert npc.state_version == initial_version
    assert npc.trust == 47

    # 3. Large delta (>= 5): BUMPS state_version (cache invalidation)
    RelationshipEngine.apply_relationship_delta(
        npc, "player", {"trust": 15, "affection": 10, "fear": -5}, reason="saved from bandits"
    )
    assert npc.state_version > initial_version
    assert npc.trust == 62
    assert npc.affinity == 60
    assert npc.fear == 5

    # 4. Third-party NPC relationship (independent of player fields)
    RelationshipEngine.apply_relationship_delta(
        npc, "rival_merchant", {"resentment": 40, "suspicion": 30}, reason="undercut prices"
    )
    rel_rival = npc.relationship_map["rival_merchant"]
    assert rel_rival["resentment"] == 40
    assert rel_rival["suspicion"] > 0
    # Player trust remains unaffected
    assert npc.trust == 62
