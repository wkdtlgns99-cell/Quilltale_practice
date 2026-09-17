"""
P2-2 God File Decomposition Verification Test Suite.
Tests:
1. Direct imports from src.world.entities (Pure Domain Models).
2. Backward-compatible re-exports from src.world.state.
3. Identity equality between src.world.entities and src.world.state symbols.
4. WorldState serialization/deserialization roundtrip integrity.
5. Entity traits default factory compliance.
"""
from src.world import entities
from src.world import state


def test_entities_direct_import_and_instantiation():
    """Verify pure domain models can be directly imported and instantiated from entities.py."""
    player = entities.Player(
        name="아델",
        location="loc_town",
        health=100,
        max_health=100,
        mana=50,
        max_mana=50,
    )
    assert player.name == "아델"
    assert hasattr(player, "traits")
    assert isinstance(player.traits, list)

    npc = entities.NPC(
        id="npc_1",
        name="마르타",
        description="선술집 주인",
        location="loc_town",
    )
    assert npc.id == "npc_1"
    assert hasattr(npc, "traits")
    assert isinstance(npc.traits, list)

    item = entities.Item(
        id="item_dagger",
        name="단검",
        description="날렵한 단검",
        item_type="weapon",
        location="player",
    )
    assert item.id == "item_dagger"
    assert hasattr(item, "traits")


def test_state_backward_compatible_reexport_identity():
    """Verify all 19 domain entity symbols re-exported from state.py are identical to entities.py."""
    reexported_symbols = [
        "EquipmentSlots",
        "CombatProfile",
        "NPCPersonality",
        "Skill",
        "Title",
        "ItemVisualProfile",
        "Item",
        "MemoryEntry",
        "Faction",
        "FacialDetails",
        "BodyMeasurements",
        "ClothingLayer",
        "NPCVisualDetails",
        "NPCNeeds",
        "NPC",
        "Location",
        "EnvironmentalMetrics",
        "PendingInformation",
        "Player",
        "DISPOSITION_KO_MAP",
    ]
    for sym_name in reexported_symbols:
        assert hasattr(entities, sym_name), f"entities.py missing {sym_name}"
        assert hasattr(state, sym_name), f"state.py missing re-exported {sym_name}"
        assert getattr(entities, sym_name) is getattr(state, sym_name), f"{sym_name} identity mismatch"


def test_world_state_serialization_roundtrip_with_decomposed_entities():
    """Verify WorldState serialization and deserialization integrity across split modules."""
    with open("data/worlds/default.json", encoding="utf-8") as f:
        json_data = f.read()

    ws = state.WorldState.from_json(json_data)
    assert isinstance(ws.player, entities.Player)
    assert isinstance(ws.locations["tavern"], entities.Location)
    for npc in ws.npcs.values():
        assert isinstance(npc, entities.NPC)

    # Serialization roundtrip
    dict_data = ws.to_dict()
    reconstructed = state.WorldState.from_dict(dict_data)
    assert reconstructed.player.name == ws.player.name
    assert reconstructed.player.location == ws.player.location
    assert len(reconstructed.npcs) == len(ws.npcs)
    assert len(reconstructed.items) == len(ws.items)

    # JSON roundtrip
    json_out = ws.to_json()
    reconstructed_json = state.WorldState.from_json(json_out)
    assert reconstructed_json.session_id == ws.session_id
    assert reconstructed_json.player.health == ws.player.health


def test_infra_models_direct_import_and_instantiation():
    """Verify Phase 2: pure infrastructure models can be directly imported and instantiated from infra_models.py."""
    from src.world import infra_models

    cont = infra_models.Continent(
        id="cont_test",
        name="테스트 대륙",
        description="설명",
    )
    assert cont.id == "cont_test"
    assert hasattr(cont, "traits")
    assert isinstance(cont.traits, list)

    nat = infra_models.Nation(
        id="nat_test",
        name="테스트 왕국",
        continent_id="cont_test",
    )
    assert nat.name == "테스트 왕국"
    assert hasattr(nat, "traits")

    settlement = infra_models.Settlement(
        id="set_test",
        name="테스트 도시",
        nation_id="nat_test",
        region_id="reg_test",
    )
    assert settlement.name == "테스트 도시"
    assert hasattr(settlement, "traits")

    fac = infra_models.Facility(
        id="fac_test",
        name="대장간",
        settlement_id="set_test",
    )
    assert fac.name == "대장간"
    assert hasattr(fac, "traits")


def test_infrastructure_backward_compatible_reexport_identity():
    """Verify Phase 2: all 22 infrastructure models & loader re-exported from infrastructure.py match exactly."""
    from src.world import infra_models
    from src.world import infrastructure
    from src.world.infra_loader import InfrastructureTemplateLoader

    model_symbols = [
        "InterTierRoute",
        "TransitVehicle",
        "LogisticsNetwork",
        "AttireHierarchyProfile",
        "CuisineProfile",
        "CulturalNormsProfile",
        "_safe_profile",
        "_safe_routes",
        "Continent",
        "Region",
        "Nation",
        "FacilityCategory",
        "SanitationWaterInfrastructure",
        "FoodStorageInfrastructure",
        "DefenseSecurityInfrastructure",
        "TradeWorkshopsInfrastructure",
        "CivicHealthInfrastructure",
        "SettlementInfrastructureProfile",
        "SettlementYields",
        "Settlement",
        "BuildingStatus",
        "FacilityType",
        "Facility",
    ]
    for sym_name in model_symbols:
        assert hasattr(infra_models, sym_name), f"infra_models.py missing {sym_name}"
        assert hasattr(infrastructure, sym_name), f"infrastructure.py missing {sym_name}"
        assert getattr(infra_models, sym_name) is getattr(infrastructure, sym_name), f"{sym_name} identity mismatch"

    # Verify Loader & Registry
    assert hasattr(infrastructure, "InfrastructureRegistry")
    assert hasattr(infrastructure, "InfrastructureTemplateLoader")
    assert infrastructure.InfrastructureTemplateLoader is InfrastructureTemplateLoader


def test_infra_loader_direct_import_and_template_loading():
    """Verify Phase 2: infra_loader.py can be directly imported and loads templates cleanly."""
    from src.world.infra_loader import InfrastructureTemplateLoader
    from src.world.infra_models import Continent

    conts = InfrastructureTemplateLoader.load_continent_templates()
    assert isinstance(conts, dict)
    assert len(conts) > 0
    first_cont = next(iter(conts.values()))
    assert isinstance(first_cont, Continent)


def test_infrastructure_registry_standalone_roundtrip():
    """Verify Phase 2: InfrastructureRegistry maintains full dict serialization roundtrip."""
    from src.world.infrastructure import (
        InfrastructureRegistry,
        Continent,
        Nation,
        Settlement,
        Facility,
    )

    reg = InfrastructureRegistry()
    reg.register_continent(Continent(id="c1", name="대륙1"))
    reg.register_nation(Nation(id="n1", name="왕국1", continent_id="c1"))
    reg.register_settlement(Settlement(id="s1", name="수도", nation_id="n1", region_id="r1"))
    reg.register_facility(Facility(id="f1", name="왕궁", settlement_id="s1"))

    d = reg.to_dict()
    restored = InfrastructureRegistry.from_dict(d)

    assert "c1" in restored.continents
    assert "n1" in restored.nations
    assert "s1" in restored.settlements
    assert "f1" in restored.facilities
    assert restored.settlements["s1"].name == "수도"


def test_action_resolvers_direct_import_and_mixins():
    """Verify Phase 3: action resolvers can be directly imported and contain expected resolver methods."""
    from src.world import action_resolvers

    expected_mixins = [
        "MovementResolverMixin",
        "StealthResolverMixin",
        "SurvivalResolverMixin",
        "TacticalCombatResolverMixin",
        "ActionResolversMixin",
    ]
    for mixin_name in expected_mixins:
        assert hasattr(action_resolvers, mixin_name), f"action_resolvers missing {mixin_name}"

    # Verify method allocations
    assert hasattr(action_resolvers.MovementResolverMixin, "resolve_action_movement")
    assert hasattr(action_resolvers.StealthResolverMixin, "resolve_action_eavesdrop")
    assert hasattr(action_resolvers.StealthResolverMixin, "resolve_action_stealth")
    assert hasattr(action_resolvers.SurvivalResolverMixin, "resolve_action_harvest")
    assert hasattr(action_resolvers.SurvivalResolverMixin, "resolve_action_campsite")
    assert hasattr(action_resolvers.SurvivalResolverMixin, "resolve_action_drink")
    assert hasattr(action_resolvers.SurvivalResolverMixin, "resolve_action_botany")
    assert hasattr(action_resolvers.TacticalCombatResolverMixin, "resolve_action_barter")
    assert hasattr(action_resolvers.TacticalCombatResolverMixin, "resolve_action_combat_distance_and_timing")
    assert hasattr(action_resolvers.TacticalCombatResolverMixin, "resolve_action_siege")


def test_two_pass_engine_mixin_inheritance_and_reexport_identity():
    """Verify Phase 3: TwoPassEngine inherits ActionResolversMixin and re-exports symbols cleanly."""
    from src.world import action_resolvers
    from src.world import two_pass_engine

    assert issubclass(two_pass_engine.TwoPassEngine, action_resolvers.ActionResolversMixin)
    assert issubclass(action_resolvers.ActionResolversMixin, action_resolvers.MovementResolverMixin)
    assert issubclass(action_resolvers.ActionResolversMixin, action_resolvers.StealthResolverMixin)
    assert issubclass(action_resolvers.ActionResolversMixin, action_resolvers.SurvivalResolverMixin)
    assert issubclass(action_resolvers.ActionResolversMixin, action_resolvers.TacticalCombatResolverMixin)

    # Verify re-exported identity
    for sym in ["ActionResolversMixin", "MovementResolverMixin", "StealthResolverMixin", "SurvivalResolverMixin", "TacticalCombatResolverMixin"]:
        assert hasattr(two_pass_engine, sym), f"two_pass_engine missing re-exported {sym}"
        assert getattr(two_pass_engine, sym) is getattr(action_resolvers, sym), f"{sym} identity mismatch"

    # All 10 resolvers accessible from TwoPassEngine
    resolvers = [
        "resolve_action_movement",
        "resolve_action_eavesdrop",
        "resolve_action_stealth",
        "resolve_action_harvest",
        "resolve_action_campsite",
        "resolve_action_drink",
        "resolve_action_botany",
        "resolve_action_barter",
        "resolve_action_combat_distance_and_timing",
        "resolve_action_siege",
    ]
    for r in resolvers:
        assert hasattr(two_pass_engine.TwoPassEngine, r), f"TwoPassEngine missing resolver {r}"


def test_action_resolvers_standalone_invocation_parity():
    """Verify Phase 3: resolvers produce identical results whether invoked via Mixin or TwoPassEngine."""
    from src.world.action_resolvers import MovementResolverMixin
    from src.world.two_pass_engine import TwoPassEngine
    from src.world.state import WorldState

    with open("data/worlds/default.json", encoding="utf-8") as f:
        state = WorldState.from_json(f.read())

    action = "남쪽 출구로 걸어 나간다"
    res_direct = MovementResolverMixin.resolve_action_movement(action, state)
    res_engine = TwoPassEngine.resolve_action_movement(action, state)

    # Both must match
    assert res_direct == res_engine
    if res_direct is not None:
        assert "target_location_id" in res_direct


def test_action_resolvers_non_matching_graceful_return():
    """Verify Phase 3: resolvers gracefully return None for unrelated actions without side effects."""
    from src.world.action_resolvers import (
        MovementResolverMixin,
        StealthResolverMixin,
        SurvivalResolverMixin,
        TacticalCombatResolverMixin,
    )
    from src.world.state import WorldState

    with open("data/worlds/default.json", encoding="utf-8") as f:
        state = WorldState.from_json(f.read())

    unrelated_action = "가만히 서서 하늘의 구름을 바라본다"
    assert MovementResolverMixin.resolve_action_movement(unrelated_action, state) is None
    assert StealthResolverMixin.resolve_action_eavesdrop(unrelated_action, state) is None
    assert StealthResolverMixin.resolve_action_stealth(unrelated_action, state) is None
    assert SurvivalResolverMixin.resolve_action_harvest(unrelated_action, state) is None
    assert SurvivalResolverMixin.resolve_action_campsite(unrelated_action, state) is None
    assert SurvivalResolverMixin.resolve_action_drink(unrelated_action, state) is None
    assert SurvivalResolverMixin.resolve_action_botany(unrelated_action, state) is None
    assert TacticalCombatResolverMixin.resolve_action_barter(unrelated_action, state) is None
    assert TacticalCombatResolverMixin.resolve_action_combat_distance_and_timing(unrelated_action, state) is None
    assert TacticalCombatResolverMixin.resolve_action_siege(unrelated_action, state) is None


