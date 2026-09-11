"""
Tests for WorldPowerScalePresets: Low Fantasy, Standard Fantasy, Hyper Inflation, Cultivation.
"""
import pytest
from src.world.state import WorldState, Player
from src.world.stat_engine import StatEngine, PowerScalePreset, POWER_SCALE_PRESETS
from src.world.two_pass_engine import TwoPassEngine


def load_test_state() -> WorldState:
    with open("data/worlds/default.json", encoding="utf-8") as f:
        return WorldState.from_json(f.read())


def test_power_scale_presets_metadata_and_traits():
    """Verify all 4 presets exist and comply with rule 6 traits requirement."""
    assert len(POWER_SCALE_PRESETS) >= 4
    for p_id in ["low_fantasy", "standard_fantasy", "hyper_inflation", "cultivation"]:
        preset = StatEngine.get_preset(p_id)
        assert isinstance(preset, PowerScalePreset)
        assert preset.id == p_id
        assert len(preset.traits) > 0
        assert preset.max_level > 0
        assert preset.stat_cap > 0


def test_power_scale_auto_detection():
    """Verify automatic genre-based preset detection."""
    # Explicit key
    p1 = StatEngine.detect_preset_for_world({"power_scale": "hyper_inflation"})
    assert p1.id == "hyper_inflation"

    # Cultivation / Wuxia genre
    p2 = StatEngine.detect_preset_for_world({}, world_genre="선협 무협 서사")
    assert p2.id == "cultivation"

    # Low fantasy / Dark fantasy genre
    p3 = StatEngine.detect_preset_for_world({}, world_genre="다크 판타지 생존")
    assert p3.id == "low_fantasy"

    # Standard fantasy default
    p4 = StatEngine.detect_preset_for_world({}, world_genre="정통 왕도 기사도")
    assert p4.id == "standard_fantasy"


def test_low_fantasy_growth_and_stat_cap():
    """Verify Low Fantasy: max level 16, 1 stat point, stat cap 30."""
    preset = StatEngine.get_preset("low_fantasy")
    player = Player(name="용병", level=15, exp=0, stat_points=5, strength=29)

    # Allocate within cap
    success = player.allocate_stat("strength", amount=1, stat_cap=preset.stat_cap)
    assert success is True
    assert player.strength == 30
    assert player.stat_points == 4

    # Allocate exceeding cap -> rejected
    rejected = player.allocate_stat("strength", amount=1, stat_cap=preset.stat_cap)
    assert rejected is False
    assert player.strength == 30
    assert player.stat_points == 4

    # Level up to max level 16
    req_exp = StatEngine.calculate_required_exp(15, preset)
    res = player.add_exp(req_exp, preset)
    assert res["leveled_up"] is True
    assert res["current_level"] == 16
    assert player.level == 16

    # Attempt to exceed max level 16 -> level does not increase
    res2 = player.add_exp(999999, preset)
    assert player.level == 16


def test_hyper_inflation_growth_and_scaling():
    """Verify Hyper Inflation: max level 300, 5 stat points per level, damage scale 50.0."""
    preset = StatEngine.get_preset("hyper_inflation")
    player = Player(name="전사", level=1, exp=0, stat_points=0, max_health=100, health=100)

    req_exp = StatEngine.calculate_required_exp(1, preset)
    res = player.add_exp(req_exp, preset)
    assert res["leveled_up"] is True
    assert player.level == 2
    assert player.stat_points == 5
    assert player.max_health >= 125

    scaled_dmg = StatEngine.calculate_scaled_damage(base_damage=10.0, stat_val=20, preset=preset)
    assert scaled_dmg >= 500.0  # 10.0 * 2.0 * 50.0 = 1000.0


def test_cultivation_breakthrough_and_realm_progression():
    """Verify Cultivation: 0 stat points per level, 10x stat explosion on breakthrough."""
    preset = StatEngine.get_preset("cultivation")
    player = Player(
        name="수도자",
        level=1,
        exp=0,
        stat_points=0,
        strength=10,
        agility=10,
        constitution=10,
        intelligence=10,
    )

    req_exp = StatEngine.calculate_required_exp(1, preset)
    res = player.add_exp(req_exp, preset)
    assert res["leveled_up"] is True
    assert player.level == 2
    # 0 stat points per level
    assert player.stat_points == 0
    # 10x stat explosion!
    assert player.strength == 100
    assert player.agility == 100
    assert player.constitution == 100
    assert player.intelligence == 100
    # Realm assigned
    assert "current_realm" in player.sub_stats
    assert player.sub_stats["current_realm"] == "축기기 (築基期)"
    assert any("축기기" in t for t in player.traits)


def test_world_state_power_scale_serialization_and_apply_update():
    """Verify WorldState serialization and apply_update integration."""
    state = load_test_state()
    assert state.power_scale_preset_id == "standard_fantasy"

    # Switch preset via apply_update
    logs = state.apply_update({"power_scale_preset_id": "low_fantasy"})
    assert state.power_scale_preset_id == "low_fantasy"
    assert any("Power scale preset updated" in log for log in logs)

    # Allocate stat via apply_update with cap
    state.player.stat_points = 5
    state.player.strength = 29
    alloc_logs = state.apply_update({"allocate_stat": {"stat_name": "strength", "amount": 1}})
    assert state.player.strength == 30
    assert any("Player allocated 1 points to strength" in log for log in alloc_logs)

    # Exceed cap
    reject_logs = state.apply_update({"allocate_stat": {"stat_name": "strength", "amount": 1}})
    assert state.player.strength == 30
    assert any("REJECTED stat allocation" in log for log in reject_logs)

    # Round-trip JSON serialization
    raw_json = state.to_json()
    loaded_state = WorldState.from_json(raw_json)
    assert loaded_state.power_scale_preset_id == "low_fantasy"
    assert loaded_state.get_power_scale_preset().id == "low_fantasy"


def test_two_pass_engine_integration_fact_sheet_power_scale():
    """Verify Live Turn Path: TwoPassEngine.compute_pass1 reads and exposes power scale summary."""
    state = load_test_state()
    state.power_scale_preset_id = "low_fantasy"

    fact_sheet = TwoPassEngine.compute_pass1("주변을 살펴본다", state)
    assert fact_sheet.power_scale_summary is not None
    assert "로우 판타지" in fact_sheet.power_scale_summary
    assert "최대 Lv.16" in fact_sheet.power_scale_summary

    prompt_ctx = fact_sheet.to_prompt_context()
    assert "[세계관 성장 규격 및 위계 (Power Scale)]" in prompt_ctx
    assert "로우 판타지" in prompt_ctx
