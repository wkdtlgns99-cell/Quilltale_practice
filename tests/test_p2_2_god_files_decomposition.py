"""
P2-2 God File Decomposition Verification Test Suite.
Tests:
1. Direct imports from src.world.entities (Pure Domain Models).
2. Backward-compatible re-exports from src.world.state.
3. Identity equality between src.world.entities and src.world.state symbols.
4. WorldState serialization/deserialization roundtrip integrity.
5. Entity traits default factory compliance.
"""
from src.world import entities
from src.world import state


def test_entities_direct_import_and_instantiation():
    """Verify pure domain models can be directly imported and instantiated from entities.py."""
    player = entities.Player(
        name="아델",
        location="loc_town",
        health=100,
        max_health=100,
        mana=50,
        max_mana=50,
    )
    assert player.name == "아델"
    assert hasattr(player, "traits")
    assert isinstance(player.traits, list)

    npc = entities.NPC(
        id="npc_1",
        name="마르타",
        description="선술집 주인",
        location="loc_town",
    )
    assert npc.id == "npc_1"
    assert hasattr(npc, "traits")
    assert isinstance(npc.traits, list)

    item = entities.Item(
        id="item_dagger",
        name="단검",
        description="날렵한 단검",
        item_type="weapon",
        location="player",
    )
    assert item.id == "item_dagger"
    assert hasattr(item, "traits")


def test_state_backward_compatible_reexport_identity():
    """Verify all 19 domain entity symbols re-exported from state.py are identical to entities.py."""
    reexported_symbols = [
        "EquipmentSlots",
        "CombatProfile",
        "NPCPersonality",
        "Skill",
        "Title",
        "ItemVisualProfile",
        "Item",
        "MemoryEntry",
        "Faction",
        "FacialDetails",
        "BodyMeasurements",
        "ClothingLayer",
        "NPCVisualDetails",
        "NPCNeeds",
        "NPC",
        "Location",
        "EnvironmentalMetrics",
        "PendingInformation",
        "Player",
        "DISPOSITION_KO_MAP",
    ]
    for sym_name in reexported_symbols:
        assert hasattr(entities, sym_name), f"entities.py missing {sym_name}"
        assert hasattr(state, sym_name), f"state.py missing re-exported {sym_name}"
        assert getattr(entities, sym_name) is getattr(state, sym_name), f"{sym_name} identity mismatch"


def test_world_state_serialization_roundtrip_with_decomposed_entities():
    """Verify WorldState serialization and deserialization integrity across split modules."""
    with open("data/worlds/default.json", encoding="utf-8") as f:
        json_data = f.read()

    ws = state.WorldState.from_json(json_data)
    assert isinstance(ws.player, entities.Player)
    assert isinstance(ws.locations["tavern"], entities.Location)
    for npc in ws.npcs.values():
        assert isinstance(npc, entities.NPC)

    # Serialization roundtrip
    dict_data = ws.to_dict()
    reconstructed = state.WorldState.from_dict(dict_data)
    assert reconstructed.player.name == ws.player.name
    assert reconstructed.player.location == ws.player.location
    assert len(reconstructed.npcs) == len(ws.npcs)
    assert len(reconstructed.items) == len(ws.items)

    # JSON roundtrip
    json_out = ws.to_json()
    reconstructed_json = state.WorldState.from_json(json_out)
    assert reconstructed_json.session_id == ws.session_id
    assert reconstructed_json.player.health == ws.player.health
