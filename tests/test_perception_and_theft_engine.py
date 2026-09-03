import pytest
from src.world.state import WorldState, Player, NPC, Item, Location
from src.world.perception_engine import PerceptionEngine
from src.world.npc_skill_engine import NPCSkillEngine
from src.world.two_pass_engine import TwoPassEngine


@pytest.fixture
def perception_world():
    state = WorldState()
    loc = Location(id="tavern", name="주점", description="북적이는 주점", exits={})
    state.locations["tavern"] = loc
    state.player.location = "tavern"
    state.player.gold = 50
    state.player.perception = 10  # Base perception

    # Thief NPC
    thief = NPC(
        id="thief_jack", name="소매치기 잭", description="골목길의 도적",
        location="tavern", agility=14, gold=5
    )
    thief.personality.greed = 80
    thief.personality.loyalty = 20
    state.npcs["thief_jack"] = thief
    loc.npcs = ["thief_jack"]

    return state


def test_stat_perception_and_modifier(perception_world):
    # Player perception
    perception_world.player.perception = 16
    assert perception_world.player.perception_stat == 16
    assert perception_world.player.per_mod == 3

    # NPC perception
    thief = perception_world.npcs["thief_jack"]
    thief.perception = 14
    assert thief.perception_stat == 14


def test_theft_imperceptible_when_margin_ge_5(perception_world):
    import random
    orig_roll = random.randint
    # Thief rolls high: d20 = 18. Agility 14 (mod +2). Distracted bonus +2. Total = 22
    random.randint = lambda a, b: 18
    try:
        perception_world.player.perception = 10  # Passive DC = 10
        thief = perception_world.npcs["thief_jack"]
        res = PerceptionEngine.evaluate_theft_vs_perception(thief, perception_world.player, is_distracted=True)

        # Margin: 22 - 10 = 12 (>= 5)
        assert res["tier"] == "imperceptible"
        assert res["success"] is True
        assert res["player_noticed"] is False
        assert res["hint_desc"] == ""
        assert "절대 서사에 누설하지 마십시오" in res["gm_directive"]
    finally:
        random.randint = orig_roll


def test_theft_subtle_hint_when_margin_0_to_4(perception_world):
    import random
    orig_roll = random.randint
    # Thief rolls 8. Agility 14 (mod +2). Distracted +2. Total = 12
    random.randint = lambda a, b: 8
    try:
        perception_world.player.perception = 12  # Passive DC = 10 + 1 = 11
        thief = perception_world.npcs["thief_jack"]
        res = PerceptionEngine.evaluate_theft_vs_perception(thief, perception_world.player, is_distracted=True)

        # Margin: 12 - 11 = 1 (0 <= margin < 5)
        assert res["tier"] == "subtle_hint"
        assert res["success"] is True
        assert res["player_noticed"] is False
        assert "마찰감" in res["hint_desc"]
        assert "오감 복선" in res["gm_directive"]
    finally:
        random.randint = orig_roll


def test_theft_caught_when_margin_negative(perception_world):
    import random
    orig_roll = random.randint
    # Thief rolls low: d20 = 2. Agility 14 (+2). Distracted +2. Total = 6
    random.randint = lambda a, b: 2
    try:
        perception_world.player.perception = 16  # Passive DC = 10 + 3 = 13
        thief = perception_world.npcs["thief_jack"]
        res = PerceptionEngine.evaluate_theft_vs_perception(thief, perception_world.player, is_distracted=True)

        # Margin: 6 - 13 = -7 (< 0)
        assert res["tier"] == "caught"
        assert res["success"] is False
        assert res["player_noticed"] is True
        assert "손목" in res["gm_directive"]
    finally:
        random.randint = orig_roll


def test_delayed_discovery_requires_physical_action_not_turn_timer(perception_world):
    # Simulate an unnoticed theft recorded previously
    thief = perception_world.npcs["thief_jack"]
    PerceptionEngine.record_unnoticed_theft(
        perception_world, thief, "금화 15닢", "gold", amount=15
    )
    # Move player to a quiet street where thief is not present
    perception_world.player.location = "street"
    perception_world.locations["street"] = Location(id="street", name="한적한 골목", description="", exits={})

    assert len(perception_world.player.unnoticed_thefts) == 1

    # 1. Non-physical/unrelated actions do NOT discover theft, regardless of turns
    for _ in range(5):
        fact_sheet = TwoPassEngine.compute_pass1("벽에 기대어 조용히 생각에 잠긴다", perception_world)
        assert len(perception_world.player.unnoticed_thefts) == 1
        assert not any("도난 발각" in log for log in fact_sheet.quest_progress_logs)

    # 2. Transaction action triggers discovery!
    fact_sheet2 = TwoPassEngine.compute_pass1("노점상에게 빵 값을 지불한다", perception_world)
    assert len(perception_world.player.unnoticed_thefts) == 0
    assert any("도난 발각" in log for log in fact_sheet2.quest_progress_logs)
    assert any("소매치기 잭" in log for log in fact_sheet2.quest_progress_logs)


def test_delayed_discovery_by_opening_bag(perception_world):
    thief = perception_world.npcs["thief_jack"]
    PerceptionEngine.record_unnoticed_theft(
        perception_world, thief, "[비전서]", "item", item_id="item_book"
    )

    fact_sheet = TwoPassEngine.compute_pass1("가방을 열어 소지품을 확인한다", perception_world)
    assert len(perception_world.player.unnoticed_thefts) == 0
    assert any("도난 발각" in log for log in fact_sheet.quest_progress_logs)
    assert any("[비전서]" in log for log in fact_sheet.quest_progress_logs)
