import pytest
from src.world.state import WorldState, Location, Player, NPC
from src.agents.player_bot import PlayerBotAgent


def test_player_bot_heuristic_decisions():
    loc = Location(
        id="loc_tavern",
        name="주점",
        description="사람들이 붐비는 선술집",
        exits={"north": "loc_market"},
        npcs=["npc_guard"]
    )
    guard = NPC(id="npc_guard", name="치안대원", description="갑옷을 입은 경비", location="loc_tavern", disposition="neutral")
    player = Player(name="테스트봇", location="loc_tavern", health=100, max_health=100)
    state = WorldState(
        session_id="test_bot_session",
        player=player,
        locations={"loc_tavern": loc},
        npcs={"npc_guard": guard}
    )

    bot = PlayerBotAgent(persona_key="curious_scholar")
    action = bot.decide_action(state)
    assert isinstance(action, str)
    assert len(action) > 2


def test_player_bot_combat_reaction_to_hostile():
    loc = Location(id="loc_forest", name="어두운 숲", description="괴물이 출몰하는 숲", exits={}, npcs=["npc_goblin"])
    monster = NPC(id="npc_goblin", name="산적 고블린", description="도끼를 든 적", location="loc_forest", disposition="hostile", alive=True)
    player = Player(name="전사봇", location="loc_forest", health=100, max_health=100)
    state = WorldState(
        session_id="test_bot_session",
        player=player,
        locations={"loc_forest": loc},
        npcs={"npc_goblin": monster}
    )

    bot = PlayerBotAgent(persona_key="aggressive_warrior")
    action = bot.decide_action(state)
    assert "고블린" in action or "공격" in action or "베어" in action
