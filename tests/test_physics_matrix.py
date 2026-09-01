"""
Unit tests for PhysicsMatrixEngine.
Verifies fast pure-Python elemental and chemical matrix matching without vector DB.
"""
import pytest
from src.world.physics_matrix import PhysicsMatrixEngine, PHYSICS_RULES


def test_physics_matrix_methane_explosion():
    reactions = PhysicsMatrixEngine.evaluate(
        action_text="이그니스 화염구를 발사한다",
        environment_text="지하 늪지대 유황가스와 기름 웅덩이",
    )
    assert len(reactions) >= 1
    explosion = next((r for r in reactions if r.rule_id == "methane_chain_explosion"), None)
    assert explosion is not None
    assert explosion.damage_bonus >= 2.0
    assert explosion.status_to_apply == "burn"
    assert explosion.status_duration > 0


def test_physics_matrix_acid_corrosion():
    reactions = PhysicsMatrixEngine.evaluate(
        action_text="산성 소화액을 강철 갑옷 골렘에게 뿌린다",
        environment_text="석실 내부",
    )
    corrosion = next((r for r in reactions if r.rule_id == "acid_mineral_corrosion"), None)
    assert corrosion is not None
    assert corrosion.tag == "방어구 파괴"
    assert corrosion.status_to_apply == "corrosion"


def test_physics_matrix_thermal_shock():
    reactions = PhysicsMatrixEngine.evaluate(
        action_text="글라키에 냉기를 뿜어 용암 벽을 얼린다",
        environment_text="화산 분화구",
    )
    shatter = next((r for r in reactions if r.rule_id == "thermal_shock_shatter"), None)
    assert shatter is not None
    assert shatter.damage_bonus == 2.0


def test_physics_matrix_formatting():
    reactions = PhysicsMatrixEngine.evaluate(action_text="이그니스 불꽃을 던져 메탄 가스를 폭파한다")
    formatted = PhysicsMatrixEngine.format_reactions_for_prompt(reactions)
    assert "[🔬 물리/화학/환경 상호작용 법칙 적용" in formatted
    assert "유기물 연쇄 기화 폭발" in formatted
