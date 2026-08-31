"""
Tests for DiceEngine and skill/combat formulas.
"""
from src.world.dice import DiceEngine, DiceCheckResult


def test_stat_modifier():
    assert DiceEngine.stat_modifier(10) == 0
    assert DiceEngine.stat_modifier(11) == 0
    assert DiceEngine.stat_modifier(12) == 1
    assert DiceEngine.stat_modifier(14) == 2
    assert DiceEngine.stat_modifier(18) == 4
    assert DiceEngine.stat_modifier(8) == -1


def test_calculate_skill_damage():
    # Base 6, STR 14 (mod 2), scaling 1.5 -> 6 + 3 - 0 = 9
    dmg = DiceEngine.calculate_skill_damage(base_damage=6, stat_value=14, scaling=1.5, target_defense=0)
    assert dmg == 9

    # With defense 2 -> 9 - 2 = 7
    dmg_def = DiceEngine.calculate_skill_damage(base_damage=6, stat_value=14, scaling=1.5, target_defense=2)
    assert dmg_def == 7


def test_perform_check_structure():
    result = DiceEngine.perform_check(action_type="공격", stat_value=14, dc=10, base_damage=6)
    assert isinstance(result, DiceCheckResult)
    assert 1 <= result.d20_roll <= 20
    assert result.modifier == 2
    assert result.total == result.d20_roll + 2
    assert "주사위" in result.summary_ko
