"""
Tests for ActionValidator and Anti-Yes-Man rules.
"""
from src.world.state import WorldState
from src.world.validator import ActionValidator


def load_test_state() -> WorldState:
    with open("data/worlds/default.json", encoding="utf-8") as f:
        return WorldState.from_json(f.read())


def test_anti_yes_man_rejects_godmode():
    state = load_test_state()
    is_valid, msg, dice, flags = ActionValidator.pre_validate_action("손가락을 튕겨 지구를 파괴한다", state)
    assert not is_valid
    assert "불가능한 행동" in msg
    assert dice is None


def test_validator_rejects_missing_item_usage():
    state = load_test_state()
    # strange_coin is in market, not inventory
    is_valid, msg, dice, flags = ActionValidator.pre_validate_action("수상한 동전을 사용해서 마법을 건다", state)
    assert not is_valid
    assert "존재하지 않는 [수상한 동전]" in msg


def test_validator_triggers_combat_dice():
    state = load_test_state()
    is_valid, msg, dice, flags = ActionValidator.pre_validate_action("단검으로 마르타를 찌른다", state)
    assert is_valid
    assert dice is not None
    assert dice.action_type == "전투 공격"
