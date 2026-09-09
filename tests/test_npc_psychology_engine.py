import unittest
from types import SimpleNamespace

from src.world.npc_psychology_engine import (
    ActionCandidate,
    DecisionCache,
    EmotionState,
    LLMBoundary,
    LLMProjection,
    MemoryRecord,
    NPCPsychologicalState,
    PersonalityTemplateLibrary,
    PsychologyEngine,
    RelationshipDelta,
    SituationContext,
)


class NPCPsychologyEngineTests(unittest.TestCase):
    def make_npc(self):
        return SimpleNamespace(
            id="npc_01",
            name="테스트 NPC",
            job="기사",
            faction_id="faction_01",
            faction_role="기사",
            description="테스트용 NPC",
            skills=["rescue", "retreat", "talk"],
            personality=SimpleNamespace(
                altruism=80, greed=20, courage=70, suspicion=30, loyalty=90,
                aggression=40, patience=70, cunning=30, pride=50, rationality=70,
                neuroticism=30, deceit=20,
            ),
            needs=SimpleNamespace(hunger=20, wealth=20, safety=30, social=30, ambition=50),
            value_hierarchy=["loyalty", "survival", "honor"],
            memories=[], fatigue=0, trust=70, affinity=80, respect=75, fear=10,
        )

    def test_required_templates_exist(self):
        expected = {
            "cautious_scholar", "reckless_adventurer", "devoted_knight", "cynical_mercenary",
            "ambitious_noble", "gentle_healer", "paranoid_survivor", "zealous_inquisitor",
        }
        self.assertEqual(set(PersonalityTemplateLibrary.ids()), expected)

    def test_memory_round_trip_and_anchor(self):
        state = NPCPsychologicalState()
        memory = MemoryRecord("m1", "동료가 불길 속에서 사망했다", ["npc_01", "companion"],
                              "village", 10, 90, 5, source="direct")
        state.memories.append(memory)
        restored = NPCPsychologicalState.from_dict(state.to_dict())
        self.assertEqual(restored.memories[0].memory_id, "m1")
        self.assertEqual(restored.memories[0].importance, 5)

    def test_emotion_is_not_stress(self):
        emotion = EmotionState()
        emotion.activate({"type": "fear", "activation": 80, "duration_ticks": 2}, 1)
        self.assertEqual(len(emotion.active_emotions), 1)
        self.assertEqual(NPCPsychologicalState().stress.stress, 0)

    def test_relationship_is_multi_axis(self):
        npc = self.make_npc()
        engine = PsychologyEngine()
        engine.ensure_npc(npc)
        delta = RelationshipDelta("player", "player", "betrayal", {"trust": -30, "suspicion": 25, "resentment": 20})
        applied = engine.apply_relationship_delta(npc, delta)
        rel = npc.psychology.relationships.get("player")
        self.assertEqual(applied["trust"], -30)
        self.assertEqual(rel.suspicion, 25)
        self.assertEqual(rel.resentment, 20)
        self.assertEqual(rel.affection, 80)

    def test_same_state_is_reproducible(self):
        npc = self.make_npc()
        engine = PsychologyEngine()
        situation = SituationContext(tick=3, location_id="village", known_facts=["fire"],
                                      visible_events=[{"event_id": "fire", "severity": 75, "threat": 80, "distance": 0}],
                                      available_actions=["rescue", "retreat"])
        candidates = [ActionCandidate("rescue", "companion", factors={"survival": 40}),
                      ActionCandidate("retreat", None, factors={"survival": 80})]
        first = engine.decide(npc, situation, candidates, event=situation.visible_events[0], direct_interaction=True)
        # Reset only transient cache-bearing state by using a fresh engine but identical NPC state.
        npc2 = self.make_npc()
        engine2 = PsychologyEngine()
        second = engine2.decide(npc2, situation, [ActionCandidate("rescue", "companion", factors={"survival": 40}),
                                                   ActionCandidate("retreat", None, factors={"survival": 80})],
                                event=situation.visible_events[0], direct_interaction=True)
        self.assertEqual(first.selected_action, second.selected_action)
        self.assertEqual(first.candidate_scores, second.candidate_scores)

    def test_impossible_candidate_rejected(self):
        npc = self.make_npc()
        engine = PsychologyEngine()
        situation = SituationContext(tick=1, location_id="room", available_actions=["talk"])
        result = engine.decide(npc, situation, [ActionCandidate("locked_door")],
                               event={"event_id": "talk", "severity": 80}, direct_interaction=True)
        self.assertEqual(result.selected_action, "idle")

    def test_llm_cannot_mutate_state(self):
        rejected = LLMBoundary.reject_state_mutation({"trust": 0, "dialogue": "I forgive you"})
        self.assertIn("trust", rejected["rejected_keys"])
        self.assertEqual(rejected["accepted"]["dialogue"], "I forgive you")

    def test_projection_does_not_dump_full_state(self):
        npc = self.make_npc()
        engine = PsychologyEngine()
        situation = SituationContext(tick=1, location_id="village", known_facts=["visible fact"])
        result = engine.decide(npc, situation, [ActionCandidate("talk")],
                               event={"event_id": "talk", "severity": 80}, direct_interaction=True)
        projection = LLMProjection.project(npc, situation, result, "player")
        self.assertNotIn("world_state", projection)
        self.assertIn("selected_action", projection["decision"])

    def test_cache_key_changes_with_version(self):
        a = DecisionCache.key("npc", "situation", 1, 1, 1, 1)
        b = DecisionCache.key("npc", "situation", 1, 2, 1, 1)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
