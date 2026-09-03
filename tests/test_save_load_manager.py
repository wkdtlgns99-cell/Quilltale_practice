import pytest
import shutil
from pathlib import Path
from src.world.state import WorldState, Player, Location, NPC
from src.world.save_load_manager import SaveLoadManager, SaveSlotMeta


@pytest.fixture
def temp_saves_dir(tmp_path):
    """Fixture to ensure tests run in an isolated temporary save directory."""
    test_dir = tmp_path / "test_saves"
    SaveLoadManager.set_saves_directory(test_dir)
    yield test_dir
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.fixture
def rich_state():
    state = WorldState(
        session_id="test_save_session",
        world_name="테라 아르카나",
        world_genre="다크 판타지",
        turn=12
    )
    loc = Location(id="loc_capital", name="솔리스 수도 성문", description="거대한 성문", exits={})
    state.locations = {"loc_capital": loc}

    state.player.name = "에이든"
    state.player.level = 4
    state.player.gold = 350
    state.player.location = "loc_capital"
    state.player.strength = 14
    state.player.perception = 16
    state.player.injuries = ["오른팔 골절 (명중-3)"]
    state.player.time_elapsed_minutes = 240  # 4 hours

    npc = NPC(id="npc_guard", name="성문 경비대장", description="엄격한 경비대장", location="loc_capital")
    state.npcs = {"npc_guard": npc}

    return state


def test_save_and_load_roundtrip_integrity(temp_saves_dir, rich_state):
    # 1. Save game to slot_1
    success, msg = SaveLoadManager.save_game(rich_state, slot_id="slot_1", slot_name="수도 첫 방문")
    assert success is True
    assert "수도 첫 방문" in msg

    # 2. Load game from slot_1
    loaded_state, load_msg = SaveLoadManager.load_game("slot_1")
    assert loaded_state is not None
    assert "에이든" in load_msg
    assert loaded_state.player.name == "에이든"
    assert loaded_state.player.level == 4
    assert loaded_state.player.gold == 350
    assert loaded_state.player.location == "loc_capital"
    assert loaded_state.player.perception == 16
    assert loaded_state.player.injuries == ["오른팔 골절 (명중-3)"]
    assert loaded_state.turn == 12


def test_instant_metadata_listing(temp_saves_dir, rich_state):
    SaveLoadManager.save_game(rich_state, slot_id="slot_1", slot_name="슬롯 1")
    
    # Advance state slightly and save to slot_2
    rich_state.turn = 15
    rich_state.player.level = 5
    SaveLoadManager.save_game(rich_state, slot_id="slot_2", slot_name="슬롯 2")

    slots = SaveLoadManager.list_slots()
    assert len(slots) == 2
    slot_ids = [s.slot_id for s in slots]
    assert "slot_1" in slot_ids
    assert "slot_2" in slot_ids

    # Check metadata fields without loading full state
    s2_meta = next(s for s in slots if s.slot_id == "slot_2")
    assert s2_meta.player_level == 5
    assert s2_meta.turn_count == 15
    assert s2_meta.location_name == "솔리스 수도 성문"


def test_corrupted_file_bak_recovery(temp_saves_dir, rich_state):
    # Initial save
    SaveLoadManager.save_game(rich_state, slot_id="slot_1")

    # Second save creates the .bak file
    rich_state.player.gold = 500
    SaveLoadManager.save_game(rich_state, slot_id="slot_1")

    # Deliberately corrupt world_state.json
    state_file = temp_saves_dir / "slot_1" / "world_state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        f.write("<<<CORRUPTED BROKEN JSON DATA>>>")

    # Load should catch the corruption and recover from .bak
    loaded_state, msg = SaveLoadManager.load_game("slot_1")
    assert loaded_state is not None
    assert "복구 완료" in msg
    assert loaded_state.player.name == "에이든"


def test_quicksave_and_quickload(temp_saves_dir, rich_state):
    success, _ = SaveLoadManager.quick_save(rich_state)
    assert success is True

    # Mutate rich_state
    rich_state.player.gold = 0
    assert rich_state.player.gold == 0

    # Quickload
    restored_state, msg = SaveLoadManager.quick_load()
    assert restored_state is not None
    assert restored_state.player.gold == 350


def test_autosave(temp_saves_dir, rich_state):
    success, msg = SaveLoadManager.auto_save(rich_state)
    assert success is True
    assert "Autosave" in msg

    loaded_state, _ = SaveLoadManager.load_game("autosave")
    assert loaded_state is not None
    assert loaded_state.turn == 12


def test_delete_slot_and_missing_slot(temp_saves_dir, rich_state):
    SaveLoadManager.save_game(rich_state, slot_id="slot_to_delete")
    assert (temp_saves_dir / "slot_to_delete").exists()

    deleted = SaveLoadManager.delete_slot("slot_to_delete")
    assert deleted is True
    assert not (temp_saves_dir / "slot_to_delete").exists()

    # Load non-existent slot
    missing_state, err = SaveLoadManager.load_game("non_existent_slot")
    assert missing_state is None
    assert "데이터가 없습니다" in err
