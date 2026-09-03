"""
Tests for LegacyManager: character archiving, lore conversion, and legacy NPC spawning.
"""
from src.world.state import WorldState
from src.world.legacy import LegacyManager
from src.memory.memory_manager import MemoryManager
from src.memory.qdrant_store import QdrantVectorStore
from src.memory.embeddings import JinaEmbedder


def load_test_state() -> WorldState:
    with open("data/worlds/default.json", encoding="utf-8") as f:
        return WorldState.from_json(f.read())


def test_legacy_archive_and_lore_conversion():
    state = load_test_state()
    state.player.name = "엘릭"
    state.player.inventory.append("dagger")
    state.player.reputation = 25
    state.player.known_facts.append("선술집 2층 궤짝에 비밀이 있다")

    # 1. Archive Character
    legacy_data = LegacyManager.archive_character(state, reason="released")
    assert legacy_data["name"] == "엘릭"
    assert legacy_data["reputation"] == 25
    assert "dagger" in legacy_data["inventory_item_ids"]

    # 2. Convert to 3rd-person lore in MemoryManager
    store = QdrantVectorStore(in_memory=True)
    embedder = JinaEmbedder()
    mm = MemoryManager(vector_store=store, embedder=embedder)

    lore_entries = LegacyManager.convert_to_lore_and_index(legacy_data, mm)
    assert len(lore_entries) >= 2
    assert any("엘릭" in entry for entry in lore_entries)
    assert any("선술집 2층 궤짝" in entry for entry in lore_entries)


def test_legacy_npc_spawning():
    state = load_test_state()
    state.player.name = "발도르"
    state.player.location = "market"

    # Archive Valdor
    legacy_data = LegacyManager.archive_character(state, reason="retired")

    # New game state
    new_state = load_test_state()
    spawned = LegacyManager.spawn_legacy_npcs_to_world(new_state, force=True)

    assert any("발도르" in name for name in spawned)

    # Check that the legacy NPC is located in market
    legacy_npc = None
    for npc_id, npc in new_state.npcs.items():
        if "발도르" in npc.name:
            legacy_npc = npc
            break

    assert legacy_npc is not None
    assert legacy_npc.is_legacy
    assert legacy_npc.location == "market"
    assert legacy_npc.id in new_state.locations["market"].npcs
