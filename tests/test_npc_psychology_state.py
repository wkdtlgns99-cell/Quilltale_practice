"""
Unit tests for NPC Psychology State Data Models (Phase 0-3 DoD Verification)
Validates:
1. MemoryEntry psychological extensions and default safety
2. NPC psychological fields and default safety
3. Backward compatibility with legacy save dictionaries lacking new fields
4. Round-trip serialization and deserialization integrity
5. Rule 6 compliance: traits field existence
"""
import pytest
from src.world.state import WorldState, NPC, MemoryEntry, NPCPersonality, NPCNeeds


def test_memory_entry_psychological_extensions():
    """Verify MemoryEntry supports new psychological fields with safe defaults."""
    mem = MemoryEntry(
        turn=5,
        description="도적들의 습격을 함께 격퇴했다.",
        emotional_tone="grateful",
        significance=3,
        is_anchor=False
    )
    assert mem.participants == []
    assert mem.location_id == ""
    assert mem.tags == []
    assert mem.relationship_deltas == {}
    assert mem.confidence == 1.0
    assert mem.source == "direct_observation"
    assert mem.decay_rate == 1.0
    assert "episodic_memory" in mem.traits

    # Custom assignment
    mem_custom = MemoryEntry(
        turn=10,
        description="성주에게 배신당해 투옥되었다.",
        emotional_tone="fearful",
        significance=4,
        is_anchor=True,
        participants=["lord_albert", "guard_captain"],
        location_id="castle_dungeon",
        tags=["betrayal", "trauma", "imprisonment"],
        relationship_deltas={"lord_albert": {"trust": -80, "fear": 40}},
        confidence=0.95,
        source="direct_observation",
        decay_rate=0.5
    )
    assert mem_custom.is_anchor is True
    assert "lord_albert" in mem_custom.participants
    assert mem_custom.relationship_deltas["lord_albert"]["trust"] == -80


def test_npc_psychological_extensions():
    """Verify NPC dataclass supports new psychological fields with safe defaults."""
    npc = NPC(
        id="npc_test_1",
        name="테스트 NPC",
        description="테스트용 인물",
        location="town_square"
    )
    assert npc.emotion_state == {}
    assert npc.stress == 0
    assert npc.relationship_map == {}
    assert npc.archetype_template == ""
    assert npc.eval_tier == 1
    assert npc.last_eval_tick == 0
    assert npc.decision_cache_key == ""
    assert npc.decision_cache_result == {}
    assert npc.state_version == 0
    assert npc.trauma_runtime == {}
    assert isinstance(npc.traits, list)


def test_legacy_save_backward_compatibility():
    """Verify loading legacy save data lacking new fields succeeds with defaults (Zero KeyError)."""
    legacy_json_dict = {
        "turn": 12,
        "player": {
            "id": "player",
            "name": "방랑자",
            "location": "village_inn",
            "stats": {"strength": 10, "agility": 10}
        },
        "npcs": {
            "bartender_old": {
                "id": "bartender_old",
                "name": "주점 주인",
                "description": "옛날 포맷 NPC",
                "location": "village_inn",
                "personality": {
                    "altruism": 40,
                    "greed": 60,
                    "courage": 30,
                    "suspicion": 50,
                    "loyalty": 40,
                    "aggression": 20
                },
                "needs": {
                    "hunger": 10,
                    "wealth": 70,
                    "safety": 20,
                    "social": 50,
                    "ambition": 40
                },
                "memories": [
                    {
                        "turn": 2,
                        "description": "손님이 술값을 떼어먹고 도망갔다.",
                        "emotional_tone": "angry",
                        "significance": 2,
                        "is_anchor": False
                    }
                ]
            }
        },
        "locations": {
            "village_inn": {
                "id": "village_inn",
                "name": "마을 주점",
                "npcs": ["bartender_old"]
            }
        }
    }

    state = WorldState.from_dict(legacy_json_dict)
    assert "bartender_old" in state.npcs
    npc = state.npcs["bartender_old"]
    
    # Verify legacy fields preserved
    assert npc.personality.greed == 60
    assert npc.needs.wealth == 70
    assert len(npc.memories) == 1
    assert npc.memories[0].description == "손님이 술값을 떼어먹고 도망갔다."
    
    # Verify new psychological extensions automatically defaulted
    assert npc.stress == 0
    assert npc.emotion_state == {}
    assert npc.relationship_map == {}
    assert npc.eval_tier == 1
    assert npc.state_version == 0
    assert npc.trauma_runtime == {}
    assert npc.memories[0].confidence == 1.0
    assert npc.memories[0].source == "direct_observation"
    assert "episodic_memory" in npc.memories[0].traits


def test_roundtrip_serialization_with_psychology():
    """Verify WorldState with rich psychological data preserves all data across to_dict and from_dict."""
    state = WorldState()
    npc = NPC(
        id="noble_cassian",
        name="카시안 경",
        description="오만한 귀족 기사",
        location="court_hall",
        stress=45,
        emotion_state={"anger": {"intensity": 60, "source": "insult", "duration": 5, "decay": 1.0}},
        relationship_map={
            "player": {
                "trust": 30, "affection": 20, "respect": 70, "fear": 10,
                "resentment": 40, "dependence": 0, "loyalty": 25,
                "suspicion": 65, "familiarity": 35
            }
        },
        archetype_template="ambitious_noble",
        eval_tier=3,
        last_eval_tick=12,
        state_version=3,
        trauma_runtime={"fire_disaster": {"active": True, "intensity": 50, "trigger_count": 1}}
    )
    npc.memories.append(MemoryEntry(
        turn=8,
        description="가문의 보검을 플레이어에게 빼앗겼다.",
        emotional_tone="angry",
        significance=4,
        is_anchor=True,
        participants=["player"],
        location_id="armory",
        tags=["loss", "honor", "resentment"],
        relationship_deltas={"player": {"respect": -20, "resentment": 50}},
        confidence=1.0,
        source="direct_observation"
    ))
    state.npcs["noble_cassian"] = npc

    # Serialize to JSON and reload
    serialized = state.to_dict()
    reloaded = WorldState.from_dict(serialized)

    r_npc = reloaded.npcs["noble_cassian"]
    assert r_npc.stress == 45
    assert r_npc.emotion_state["anger"]["intensity"] == 60
    assert r_npc.relationship_map["player"]["suspicion"] == 65
    assert r_npc.archetype_template == "ambitious_noble"
    assert r_npc.eval_tier == 3
    assert r_npc.state_version == 3
    assert r_npc.trauma_runtime["fire_disaster"]["intensity"] == 50
    assert len(r_npc.memories) == 1
    assert r_npc.memories[0].is_anchor is True
    assert "honor" in r_npc.memories[0].tags
    assert r_npc.memories[0].relationship_deltas["player"]["resentment"] == 50
