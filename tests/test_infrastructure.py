import pytest
from src.llm.resilience import JSONRepairEngine, ResilientLLMRunner
from src.engine.profiler import EngineProfiler, TurnTelemetry
from src.persistence.migration import SaveMigrationEngine


def test_json_repair_trailing_commas_and_markdown():
    broken_markdown_json = """```json
    {
        "narration": "선술집에 들어섭니다.",
        "state_update": {},
        "scene_changed": false,
    }
    ```"""
    parsed = JSONRepairEngine.repair_and_parse(broken_markdown_json)
    assert parsed["narration"] == "선술집에 들어섭니다."
    assert parsed["scene_changed"] is False


def test_profiler_telemetry():
    cost = EngineProfiler.calculate_cost(prompt_tokens=1000, completion_tokens=200)
    assert cost > 0

    telem = TurnTelemetry(
        turn=1,
        pass1_duration_ms=10.5,
        llm_duration_ms=1200.0,
        pass2_duration_ms=5.0,
        prompt_tokens=1000,
        completion_tokens=200,
        estimated_cost_krw=cost
    )
    hud = EngineProfiler.format_telemetry_hud(telem)
    assert "지연 시간" in hud
    assert "토큰" in hud


def test_save_migration_v1_to_v3():
    v1_save = {
        "save_version": 1,
        "player": {"name": "방랑자"},
        "npcs": {"npc_bob": {"name": "밥"}},
        "items": {"item_sword": {"name": "검"}}
    }
    migrated = SaveMigrationEngine.migrate(v1_save)
    assert migrated["save_version"] == 3
    assert "party" in migrated
    assert "bounties" in migrated["player"]
    assert "visual" in migrated["npcs"]["npc_bob"]
    assert "durability" in migrated["items"]["item_sword"]
