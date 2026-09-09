"""
Unit Tests for 12-Stage Psychology Pipeline, 3-Tier Router, and Decision Cache (Phase 9-13)
Validates:
1. Tier 1 (O(1) routine), Tier 2 (Sensory <5ms), Tier 3 (Full 12-stage pipeline)
2. Decision Cache hit and granular version-based invalidation
3. MemoryPsychologyBridge salience ranking and deduplication
4. End-to-end integration through NPCCognitiveDeductionEngine.process_npc_cognitive_turn
"""
import pytest
from src.world.state import WorldState, NPC, MemoryEntry
from src.world.psychology_engine import (
    WorldEvent, ActionCandidate, DecisionResult,
    DecisionCacheManager, MemoryPsychologyBridge, PsychologyDecisionPipeline,
    EmotionEngine, StressEngine, RelationshipEngine
)
from src.world.cognitive_engine import NPCCognitiveDeductionEngine


def test_3_tier_routing():
    """Verify Tier 1, Tier 2, and Tier 3 classification and performance constraints."""
    npc = NPC(id="villager_tom", name="주민 톰", description="", location="village_square")
    npc.stress = 20

    # Tier 1: Far-away routine tick
    ev_tier1 = WorldEvent(
        id="ev_t1", event_type="routine_tick", severity=1,
        location_id="distant_forest", source_id="nature", turn=5
    )
    res1 = PsychologyDecisionPipeline.route_and_process(npc, ev_tier1)
    assert res1.tier == 1
    assert res1.selected_action == "idle_observe"
    assert npc.stress <= 20  # passive stress recovery applied

    # Tier 2: Local commotion in same location
    ev_tier2 = WorldEvent(
        id="ev_t2", event_type="noise", severity=2,
        location_id="village_square", source_id="brawl", turn=6
    )
    res2 = PsychologyDecisionPipeline.route_and_process(npc, ev_tier2)
    assert res2.tier == 2
    assert res2.selected_action == "surveillance"
    assert "anxiety" in npc.emotion_state

    # Tier 3: Direct confrontation with dialogue
    ev_tier3 = WorldEvent(
        id="ev_t3", event_type="dialogue", severity=3,
        location_id="village_square", source_id="player", target_ids=["villager_tom"],
        description="네 비밀을 다 알고 있다.", turn=7
    )
    res3 = PsychologyDecisionPipeline.route_and_process(npc, ev_tier3)
    assert res3.tier == 3
    assert res3.selected_action in ("escape", "hide", "cooperate", "attack")
    assert "stages" in res3.decision_trace
    assert "11_selection" in res3.decision_trace["stages"]
    assert npc.intention != ""


def test_decision_cache_and_invalidation():
    """Verify decision cache hits and invalidation on state mutation (delta >= 5)."""
    npc = NPC(id="guard_hans", name="한스", description="", location="gate")
    ev = WorldEvent(
        id="ev_inspect", event_type="dialogue", severity=3,
        location_id="gate", source_id="player", target_ids=["guard_hans"],
        description="통행증을 보여준다.", turn=10
    )

    # First call: executes pipeline and caches
    res1 = PsychologyDecisionPipeline.route_and_process(npc, ev)
    assert res1.cache_hit is False

    # Second call with same state: CACHE HIT
    res2 = PsychologyDecisionPipeline.route_and_process(npc, ev)
    assert res2.cache_hit is True
    assert res2.selected_action == res1.selected_action

    # Invalidate cache by applying relationship delta >= 5
    RelationshipEngine.apply_relationship_delta(npc, "player", {"trust": 10}, "bribe")
    assert npc.state_version > 0

    # Third call: CACHE MISS (re-evaluates due to invalidated version)
    res3 = PsychologyDecisionPipeline.route_and_process(npc, ev)
    assert res3.cache_hit is False


def test_memory_bridge_ranking_and_deduplication():
    """Verify memory salience ranking favors anchors and deduplication reinforces memories."""
    npc = NPC(id="scholar_elena", name="엘레나", description="", location="archives")

    mem1 = MemoryEntry(
        turn=1, description="도서관 일상 정리", emotional_tone="neutral", significance=1
    )
    mem2 = MemoryEntry(
        turn=3, description="플레이어와 고대 비전을 연구함", emotional_tone="grateful",
        significance=3, participants=["player"]
    )
    mem3 = MemoryEntry(
        turn=5, description="제국의 대화재로 스승을 잃음", emotional_tone="fearful",
        significance=5, is_anchor=True, tags=["fire", "loss"]
    )

    npc.memories.extend([mem1, mem2, mem3])

    # Ranking with query for player
    ranked = MemoryPsychologyBridge.rank_salient_memories(npc, query_context="비전", target_id="player")
    # Both anchor and player relevance should be top
    descriptions = [m.description for m in ranked]
    assert mem3.description in descriptions[:2]
    assert mem2.description in descriptions[:2]

    # Test Deduplication within 5 turn window
    dup_entry = MemoryEntry(
        turn=7, description="비슷한 화재 사건", emotional_tone="fearful",
        significance=3, tags=["fire"]
    )
    initial_count = len(npc.memories)
    was_appended = MemoryPsychologyBridge.record_memory_deduplicated(npc, dup_entry, turn_window=5)
    # Tags overlap with mem3 within 5 turns -> reinforces mem3, does not duplicate
    assert was_appended is False
    assert len(npc.memories) == initial_count


def test_cognitive_engine_master_pipeline_integration():
    """Verify NPCCognitiveDeductionEngine invokes master psychology pipeline on standard turns."""
    from src.world.state import Location
    state = WorldState()
    state.locations["village_inn"] = Location(id="village_inn", name="마을 주점", description="", exits={})
    npc = NPC(id="innkeeper_bob", name="밥", description="주점 주인", location="village_inn")
    npc.personality.altruism = 70
    npc.personality.loyalty = 65
    state.npcs["innkeeper_bob"] = npc
    state.locations["village_inn"].npcs.append("innkeeper_bob")

    # Regular conversational turn
    res = NPCCognitiveDeductionEngine.process_npc_cognitive_turn(
        npc=npc,
        state=state,
        player_action="주점 주인에게 마을 소문에 대해 묻는다."
    )
    assert res is not None
    assert "psychology_" in res["action_type"]
    assert "decision_result" in res
    assert npc.intention != ""


def test_external_llm_prompt_generation_with_psychology():
    """Verify generate_external_llm_prompt embeds emotion, stress, trauma, and expression boundaries."""
    npc = NPC(
        id="noble_vlad", name="블라드 경", description="음산한 귀족", location="mansion",
        stress=80, emotion_state={"fear": {"intensity": 65, "source": "threat", "duration": 3}},
        trauma_runtime={"fire_disaster": {"intensity": 40}}
    )
    prompt = NPCCognitiveDeductionEngine.generate_external_llm_prompt(npc, hypothesis_text="블라드 경이 흡혈귀인가?")
    assert "Real-time Emotional State & Psychological Stress" in prompt
    assert "fear(65)" in prompt
    assert "80/100" in prompt
    assert "fire_disaster" in prompt
    assert "Strict Narrative Expression Boundary" in prompt
    assert "블라드 경이 흡혈귀인가?" in prompt


def test_tier_performance_profiling():
    """Verify tier execution performance matches budget specifications."""
    import time
    npc = NPC(id="perf_npc", name="성능테스트 NPC", description="", location="town")

    # 1. Tier 1 Performance Budget: O(1), 1000 calls < 100ms
    ev_t1 = WorldEvent(id="t1", event_type="routine_tick", location_id="distant", turn=1)
    start = time.perf_counter()
    for _ in range(1000):
        PsychologyDecisionPipeline.route_and_process(npc, ev_t1)
    t1_elapsed = time.perf_counter() - start
    assert t1_elapsed < 0.1  # 1000 calls under 100ms (O(1))

    # 2. Tier 2 Performance Budget: < 5ms per call
    ev_t2 = WorldEvent(id="t2", event_type="noise", location_id="town", severity=2, turn=2)
    start = time.perf_counter()
    for _ in range(100):
        PsychologyDecisionPipeline.route_and_process(npc, ev_t2)
    t2_elapsed = (time.perf_counter() - start) / 100
    assert t2_elapsed < 0.005  # < 5ms per call

    # 3. Tier 3 Performance Budget: < 200ms per call
    ev_t3 = WorldEvent(id="t3", event_type="dialogue", location_id="town", target_ids=["perf_npc"], severity=3, turn=3)
    start = time.perf_counter()
    for _ in range(10):
        # Force cache miss for benchmarking full pipeline
        npc.state_version += 1
        PsychologyDecisionPipeline.route_and_process(npc, ev_t3)
    t3_elapsed = (time.perf_counter() - start) / 10
    assert t3_elapsed < 0.05  # well under 200ms budget (< 50ms)

