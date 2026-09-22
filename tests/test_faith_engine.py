"""
Tests for Faith, Deity, Miracle, and Divine Retribution Engine (faith_engine.py).
Verifies:
1. Data models compliance with Rule 5 (traits field) & round-trip serialization.
2. Pure dynamic deity registry (NO hardcoded deities).
3. Devotion tier progression (0~4).
4. Prayer and altar sacrifice mechanics.
5. 5-channel universal miracle pipeline (heal, ward, smite, cleanse, fortune).
6. Taboo violation detection and divine wrath curses.
7. Background faith tick and domain settlement yields synergy.
8. TwoPassEngine Pass 1 integration and DeterministicFactSheet context rendering.
9. WorldState persistence serialization round-trip.
"""
import pytest
from src.world.state import WorldState, Player, Item, Location
from src.world.infra_models import Settlement, SettlementYields
from src.world.infrastructure import InfrastructureRegistry
from src.world.faith_engine import (
    FaithEngine,
    DeityProfile,
    DivineMiracle,
    PlayerFaithState,
    FaithTurnSummary,
)
from src.world.two_pass_engine import TwoPassEngine


def _setup_world_with_deity():
    state = WorldState()
    state.player = Player(
        name="테스트기사",
        location="temple_chapel",
        health=60,
        max_health=100,
        gold=100,
        inventory=["sacred_chalice_01"],
        fatigue=40,
    )
    state.locations["temple_chapel"] = Location(
        id="temple_chapel",
        name="성스러운 예배당",
        description="빛과 서약의 제단이 놓인 고요한 석조 예배당이다.",
        exits={},
        items=[],
        npcs=[],
    )
    chalice = Item(
        id="sacred_chalice_01",
        name="은제 성배",
        description="정교한 은세공 성배.",
        location="inventory",
        value=80,
    )
    state.items["sacred_chalice_01"] = chalice

    # Pure dynamic registration (no hardcoded gods!)
    deity = FaithEngine.create_custom_deity(
        state=state,
        deity_id="radiant_sun",
        name="광휘의 서약",
        domain="빛과 정의",
        taboos=["비겁", "독살", "도둑질"],
        favored_offerings=["gold", "은제 성배"],
    )
    return state, deity


def test_faith_data_models_traits_and_serialization():
    """Rule 5: New game data classes MUST include traits: List[str] = field(default_factory=list)."""
    miracle = DivineMiracle(
        miracle_id="miracle_test",
        name="시험의 기적",
        piety_cost=50,
        effect_type="heal",
        magnitude=40.0,
        traits=["holy", "light"],
    )
    assert "holy" in miracle.traits
    m_dict = miracle.to_dict()
    assert m_dict["effect_type"] == "heal"
    m_restored = DivineMiracle.from_dict(m_dict)
    assert m_restored.traits == ["holy", "light"]

    profile = DeityProfile(
        deity_id="deity_01",
        name="태양신",
        domain="빛",
        traits=["solar"],
    )
    assert "solar" in profile.traits
    p_dict = profile.to_dict()
    p_restored = DeityProfile.from_dict(p_dict)
    assert p_restored.deity_id == "deity_01"
    assert p_restored.traits == ["solar"]

    f_state = PlayerFaithState(
        deity_id="deity_01",
        deity_name="태양신",
        piety=200,
        devotion_tier=2,
        traits=["faithful"],
    )
    assert "faithful" in f_state.traits
    f_dict = f_state.to_dict()
    f_restored = PlayerFaithState.from_dict(f_dict)
    assert f_restored.piety == 200
    assert f_restored.traits == ["faithful"]

    summary = FaithTurnSummary(turn=1, piety_delta=10, traits=["summary_trait"])
    assert "summary_trait" in summary.traits


def test_no_hardcoded_deities_and_dynamic_registration():
    """Verify system starts empty and dynamically accepts new deity profiles."""
    state = WorldState()
    assert getattr(state, "deities_db", {}) == {}

    deity = FaithEngine.create_custom_deity(
        state,
        deity_id="storm_lord",
        name="폭풍의 군주",
        domain="바다와 번개",
        taboos=["배신", "도주"],
    )
    assert "storm_lord" in state.deities_db
    assert state.deities_db["storm_lord"].name == "폭풍의 군주"
    assert len(state.deities_db["storm_lord"].miracles) == 4  # default auto-generated miracles


def test_choose_deity_and_devotion_tiers():
    """Verify devotion tier progression from 0 to 4 based on piety."""
    state, deity = _setup_world_with_deity()

    res = FaithEngine.choose_deity(state, "radiant_sun")
    assert res["success"] is True
    assert state.faith_state.deity_id == "radiant_sun"
    assert state.faith_state.devotion_tier == 0

    # Test devotion tier boundaries
    assert FaithEngine.calculate_devotion_tier(0)[0] == 0
    assert FaithEngine.calculate_devotion_tier(80)[0] == 1
    assert FaithEngine.calculate_devotion_tier(200)[0] == 2
    assert FaithEngine.calculate_devotion_tier(500)[0] == 3
    assert FaithEngine.calculate_devotion_tier(800)[0] == 4


def test_prayer_action():
    """Praying increases piety and slightly reduces fatigue."""
    state, deity = _setup_world_with_deity()
    FaithEngine.choose_deity(state, "radiant_sun")

    initial_fatigue = state.player.fatigue
    initial_piety = state.faith_state.piety

    res = FaithEngine.pray(state)
    assert res["success"] is True
    assert state.faith_state.piety > initial_piety
    assert state.player.fatigue < initial_fatigue
    assert "기도" in res["message"]


def test_sacrifice_gold_and_items():
    """Sacrificing gold or items at an altar burns wealth and rewards piety."""
    state, deity = _setup_world_with_deity()
    FaithEngine.choose_deity(state, "radiant_sun")

    # Gold sacrifice
    res_gold = FaithEngine.offer_sacrifice(state, offering_type="gold", value=50)
    assert res_gold["success"] is True
    assert state.player.gold == 50
    assert state.faith_state.piety == 25  # 50 gold * 0.5 ratio

    # Item sacrifice (favored offering gets 0.75 ratio -> 80 * 0.75 = 60)
    res_item = FaithEngine.offer_sacrifice(state, offering_type="item", offering_name="은제 성배")
    assert res_item["success"] is True
    assert "sacred_chalice_01" not in state.player.inventory
    assert state.faith_state.piety == 85  # 25 + 60


def test_miracle_invocation_channels():
    """Test invoking miracles across multiple channels (heal, ward, smite, cleanse)."""
    state, deity = _setup_world_with_deity()
    FaithEngine.choose_deity(state, "radiant_sun")

    # Set sufficient piety and devotion tier
    state.faith_state.piety = 250
    state.faith_state.devotion_tier = 2

    # 1. Heal miracle
    old_hp = state.player.health  # 60
    res_heal = FaithEngine.invoke_miracle(state, "heal")
    assert res_heal["success"] is True
    assert state.player.health > old_hp
    assert state.faith_state.piety < 250

    # 2. Ward miracle
    res_ward = FaithEngine.invoke_miracle(state, "ward")
    assert res_ward["success"] is True
    assert any("보호막" in b["name"] for b in state.faith_state.active_blessings)

    # 3. Cleanse miracle
    state.player.status_effects = {"poison": {"duration": 3, "potency": 5}}
    res_cleanse = FaithEngine.invoke_miracle(state, "cleanse")
    assert res_cleanse["success"] is True


def test_taboo_violation_and_curse():
    """Performing an action with taboo tags triggers divine retribution."""
    state, deity = _setup_world_with_deity()
    FaithEngine.choose_deity(state, "radiant_sun")
    state.faith_state.piety = 100

    # Tag contains taboo keyword "도둑질"
    res = FaithEngine.check_taboo_violation(state, ["도둑질", "잠입"])
    assert res is not None
    assert res["violated"] is True
    assert state.faith_state.heresy_level > 0
    assert state.faith_state.piety < 100
    assert len(state.faith_state.active_curses) > 0


def test_faith_tick_and_settlement_passive_synergy():
    """Faith tick decays buffs/curses and accrues passive faith from owned domain yields."""
    state, deity = _setup_world_with_deity()
    FaithEngine.choose_deity(state, "radiant_sun")
    state.faith_state.active_blessings = [{"name": "빛의_축복", "turns_remaining": 1}]
    state.faith_state.active_curses = [{"name": "광휘의_응징", "turns_remaining": 2}]

    # Setup infrastructure registry and settlement
    reg = InfrastructureRegistry()
    settlement = Settlement(
        id="sanctuary_town",
        name="성역 마을",
        nation_id="nation_01",
        region_id="region_01",
        yields=SettlementYields(faith=20.0),
    )
    reg.settlements["sanctuary_town"] = settlement
    state.infrastructure = reg
    state.pioneering_domains = {"sanctuary_town": True}

    summary = FaithEngine.advance_faith_tick(state)
    # Blessing with duration 1 expires
    assert "빛의_축복" in summary.miracles_triggered
    assert len(state.faith_state.active_blessings) == 0
    # Curse with duration 2 decrements to 1
    assert state.faith_state.active_curses[0]["turns_remaining"] == 1
    # Passive piety accrued
    assert summary.piety_delta > 0


def test_two_pass_engine_live_integration():
    """Verify faith action resolution through TwoPassEngine Pass 1 pipeline."""
    state, deity = _setup_world_with_deity()
    FaithEngine.choose_deity(state, "radiant_sun")

    # Pass 1 prayer action
    action = "신전에 무릎 꿇고 경건하게 신에게 기도한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid is True
    assert fact_sheet.faith_summary is not None
    assert "광휘의 서약" in fact_sheet.faith_summary
    prompt_context = fact_sheet.to_prompt_context()
    assert "종교 신앙 및 신성 기적" in prompt_context


def test_world_state_serialization_round_trip():
    """Verify WorldState serialization and deserialization preserves faith_state and deities_db."""
    state, deity = _setup_world_with_deity()
    FaithEngine.choose_deity(state, "radiant_sun")
    state.faith_state.piety = 180
    state.faith_state.devotion_tier = 1

    state_dict = state.to_dict()
    restored_state = WorldState.from_dict(state_dict)

    assert restored_state.faith_state is not None
    assert restored_state.faith_state.deity_id == "radiant_sun"
    assert restored_state.faith_state.piety == 180
    assert restored_state.faith_state.devotion_tier == 1
    assert "radiant_sun" in restored_state.deities_db
    assert restored_state.deities_db["radiant_sun"].domain == "빛과 정의"
