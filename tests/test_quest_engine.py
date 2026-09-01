"""
Unit tests for QuestEngine, Quest tracking, multi-stage progression,
branching narrative choices, time limits, rewards, and WorldState integration.
"""
import pytest
from src.world.state import WorldState, Player, Location, NPC, Item
from src.world.quest_engine import QuestEngine, Quest, QuestStage, QuestChoice, QuestOptional


def test_load_quest_templates():
    templates = QuestEngine.load_templates()
    assert len(templates) >= 10
    assert "quest_wolf_hunt" in templates
    assert "quest_goblin_prisoner" in templates
    assert "quest_cursed_mage" in templates
    assert "quest_clocktower_that_stopped" in templates


def test_quest_prerequisites():
    state = WorldState()
    state.player.level = 1
    state.player.intelligence = 10

    # Low level player attempting high level quest
    high_quest = Quest(
        id="high_q", title="고위 마법사 의뢰", category="investigation",
        prerequisites={"level_min": 10, "stats": {"INT": 14}}
    )
    eligible, reason = QuestEngine.check_prerequisites(high_quest, state)
    assert eligible is False
    assert "레벨" in reason

    # Raise player level and int
    state.player.level = 10
    state.player.intelligence = 14
    eligible2, _ = QuestEngine.check_prerequisites(high_quest, state)
    assert eligible2 is True


def test_quest_accept_and_progress_stages():
    state = WorldState()
    loc = Location(id="start", name="선술집", description="시작 장소", exits={}, npcs=["marta"])
    state.locations["start"] = loc
    state.player.location = "start"

    # Accept wolf hunt quest
    success, msg = QuestEngine.accept_quest(state, "quest_wolf_hunt")
    assert success is True
    assert "quest_wolf_hunt" in state.quests
    quest = state.quests["quest_wolf_hunt"]
    assert quest.status == "active"
    assert quest.current_stage_idx == 0
    assert quest.current_stage.target == "dire_wolf"

    # Kill 2 dire wolves (need 3)
    logs1 = QuestEngine.progress_event(state, "kill", "dire_wolf", count=2)
    assert quest.current_stage_idx == 0
    assert quest.current_stage.current_count == 2
    assert quest.current_stage.completed is False

    # Kill 1 more dire wolf (stage 1 completed!)
    logs2 = QuestEngine.progress_event(state, "kill", "dire_wolf", count=1)
    assert quest.current_stage_idx == 1  # advanced to stage 2 (dire_wolf_alpha)
    assert quest.current_stage.target == "dire_wolf_alpha"

    # Kill alpha wolf (stage 2 completed!)
    logs3 = QuestEngine.progress_event(state, "kill", "dire_wolf_alpha", count=1)
    assert quest.current_stage_idx == 2  # advanced to stage 3 (talk to marta)

    # Report to marta (all stages completed & auto-completed!)
    logs4 = QuestEngine.progress_event(state, "talk", "marta", count=1)
    assert quest.status == "completed"
    assert any("완료" in l for l in logs4)
    assert state.player.gold > 20  # received reward gold


def test_quest_branching_choices():
    state = WorldState()
    state.player.level = 5
    state.player.intelligence = 12
    state.player.gold = 50
    state.player.reputation = 15

    success, msg = QuestEngine.accept_quest(state, "quest_goblin_prisoner")
    assert success is True
    quest = state.quests["quest_goblin_prisoner"]

    # Choose spare goblins branch (requires INT 12)
    success, msg, logs = QuestEngine.choose_branch(state, "quest_goblin_prisoner", "spare_goblins")
    assert success is True
    assert quest.selected_choice_id == "spare_goblins"
    assert quest.status == "completed"
    assert "goblin_trade_token" in state.player.inventory


def test_quest_time_limits_and_failure():
    state = WorldState()
    state.player.level = 5
    state.player.reputation = 20

    QuestEngine.accept_quest(state, "quest_moonflower_gather")
    quest = state.quests["quest_moonflower_gather"]
    assert quest.is_time_limited is True
    assert quest.time_limit_minutes == 720

    # Advance 400 minutes (still active)
    logs1 = QuestEngine.check_turn_time_limits(state, delta_minutes=400)
    assert quest.status == "active"

    # Advance 400 more minutes (800 total >= 720 limit -> fails!)
    logs2 = QuestEngine.check_turn_time_limits(state, delta_minutes=400)
    assert quest.status == "failed"
    assert any("실패" in l for l in logs2)
    assert state.player.reputation < 20  # penalty applied


def test_world_state_apply_update_quest():
    state = WorldState()
    state.player.level = 5

    # Accept via update
    state.apply_update({"accept_quest": "quest_wolf_hunt"})
    assert "quest_wolf_hunt" in state.quests
    assert state.quests["quest_wolf_hunt"].status == "active"

    # Advance via update
    state.apply_update({
        "advance_quest": {
            "type": "kill",
            "target": "dire_wolf",
            "count": 3
        }
    })
    assert state.quests["quest_wolf_hunt"].current_stage_idx == 1


def test_quest_serialization_round_trip():
    state = WorldState()
    QuestEngine.accept_quest(state, "quest_wolf_hunt")
    state.quests["quest_wolf_hunt"].stages[0].current_count = 2

    json_str = state.to_json()
    loaded = WorldState.from_json(json_str)

    assert "quest_wolf_hunt" in loaded.quests
    loaded_q = loaded.quests["quest_wolf_hunt"]
    assert loaded_q.status == "active"
    assert loaded_q.stages[0].current_count == 2
    assert loaded_q.title == "안개 숲의 굶주린 늑대 무리"


def test_quest_html_and_prompt_formatting():
    state = WorldState()
    QuestEngine.accept_quest(state, "quest_wolf_hunt")

    html = state.to_quest_journal_html()
    assert "안개 숲의 굶주린 늑대 무리" in html
    assert "진행 중인 퀘스트" in html

    prompt_ctx = QuestEngine.format_prompt_context(state)
    assert "[📜 현재 진행 중인 퀘스트 목표" in prompt_ctx
    assert "안개 숲" in prompt_ctx
