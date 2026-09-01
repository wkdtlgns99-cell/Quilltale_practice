import pytest
from src.world.state import WorldState, Location, Player
from src.world.puzzle_engine import PuzzleEngine


def test_puzzle_incantation_cipher_solve():
    loc = Location(id="loc_dungeon_depths", name="심연 던전", description="고대 석문이 있는 곳", exits={})
    player = Player(name="마법사", location="loc_dungeon_depths")
    state = WorldState(
        session_id="test_puzzle_session",
        player=player,
        locations={"loc_dungeon_depths": loc}
    )

    action = "석문을 향해 '이그니스 사기타 임팩투스' 고대어를 순서대로 영창한다"
    result = PuzzleEngine.evaluate_puzzle_action(state, action)

    assert result is not None
    assert result["is_solved"] is True
    assert "석문이 열립니다" in result["solve_message"]
    assert state.puzzles["puzzle_ancient_cipher_01"]["solved"] is True
    assert player.exp > 0
    assert len(player.inventory) > 0


def test_puzzle_weight_plate_solve():
    loc = Location(id="loc_ancient_catacomb", name="고대 지하묘지", description="압력판이 있는 묘지", exits={})
    player = Player(name="전사", location="loc_ancient_catacomb", strength=16)
    state = WorldState(
        session_id="test_puzzle_session",
        player=player,
        locations={"loc_ancient_catacomb": loc}
    )

    action = "강력한 힘으로 바닥의 압력판을 세게 밟아 누른다"
    result = PuzzleEngine.evaluate_puzzle_action(state, action)

    assert result is not None
    assert result["is_solved"] is True
    assert state.puzzles["puzzle_weight_plate_01"]["solved"] is True
