"""
Unit tests for 6-Tier Realistic World Infrastructure System (Step 1).
Tests:
1. Dataclass integrity and serialization for Continent, Region, Nation, Settlement, Facility.
2. InfrastructureRegistry parent-child registration and O(1) bottom-up hierarchy resolution.
3. Cascading price calculation combining Regional natural multipliers and National import tariffs.
4. Cross-border checkpoint inspection (passports, contraband, and wartime blockades).
"""
import pytest
from src.world.infrastructure import (
    Continent, Region, Nation, Settlement, Facility, InfrastructureRegistry,
    BuildingStatus, FacilityType
)
from src.world.geography import RoadConnection, RoadType


def test_5_tier_dataclass_instantiation_and_dict_roundtrip():
    """All 5 tier dataclasses instantiate with rich fields and survive to_dict/from_dict."""
    cont = Continent(
        id="valyria",
        name="발리리아 구 대륙",
        common_language="발리리안 공통어",
        era_background="마법 골드러시 시대",
        plate_name="발리리아 지질 판"
    )
    assert cont.common_language == "발리리안 공통어"
    assert Continent.from_dict(cont.to_dict()).name == "발리리아 구 대륙"

    reg = Region(
        id="reg_frozen_pass",
        name="칼날 산맥 피오르드",
        continent_id="valyria",
        terrain="mountain_mine",
        climate_type="혹한대",
        natural_price_multipliers={"ore": 0.4, "salt": 3.5},
        survival_hazards=["혹한 결빙", "낙석"],
        visibility_meters=30
    )
    assert reg.natural_price_multipliers["ore"] == 0.4
    assert Region.from_dict(reg.to_dict()).terrain == "mountain_mine"

    nation = Nation(
        id="nation_ironforge",
        name="아이언포지 광산왕국",
        continent_id="valyria",
        ruling_system="봉건 왕정",
        tariff_rate=0.15,
        passport_required=True,
        contraband=["흑마법 스크롤", "맹독성 포자"],
        diplomatic_relations={"nation_solis": "hostile", "nation_elf": "allied"}
    )
    assert nation.tariff_rate == 0.15
    assert Nation.from_dict(nation.to_dict()).passport_required is True

    settlement = Settlement(
        id="settle_anvil",
        name="검은 모루 요새마을",
        nation_id="nation_ironforge",
        region_id="reg_frozen_pass",
        settlement_type="mining_camp",
        coordinates=(45.0, 12.0),
        population=1500,
        security_level=80,
        roads={"settle_outpost": RoadConnection(destination_id="settle_outpost", distance_km=8.0, road_type=RoadType.MOUNTAIN_PASS)}
    )
    assert settlement.population == 1500
    assert "settle_outpost" in settlement.roads
    assert Settlement.from_dict(settlement.to_dict()).security_level == 80

    facility = Facility(
        id="fac_forge_01",
        name="녹슨 화로 대장간",
        settlement_id="settle_anvil",
        facility_type="blacksmith",
        npcs=["npc_blacksmith_baran"],
        items=["item_iron_ingot"],
        services={"repair": 0.8, "craft": True}
    )
    assert facility.npcs[0] == "npc_blacksmith_baran"
    assert Facility.from_dict(facility.to_dict()).services["repair"] == 0.8


def test_infrastructure_registry_hierarchy_resolution():
    """Registry correctly links children to parents and resolves full bottom-up hierarchy."""
    reg = InfrastructureRegistry()

    cont = Continent(id="valyria", name="발리리아 구 대륙")
    region = Region(id="reg_mine", name="아이언포지 광산 산맥", continent_id="valyria", natural_price_multipliers={"ore": 0.5, "salt": 3.0})
    nation = Nation(id="nation_dwarf", name="드워프 왕국", continent_id="valyria", tariff_rate=0.10)
    settlement = Settlement(id="town_forge", name="모루 성채", nation_id="nation_dwarf", region_id="reg_mine")
    facility = Facility(id="shop_anvil", name="모루 철물점", settlement_id="town_forge", facility_type="general_store")

    reg.register_continent(cont)
    reg.register_region(region)
    reg.register_nation(nation)
    reg.register_settlement(settlement)
    reg.register_facility(facility)

    # Verify top-down list registration
    assert "reg_mine" in cont.region_ids
    assert "nation_dwarf" in cont.nation_ids
    assert "town_forge" in nation.settlement_ids
    assert "town_forge" in region.settlement_ids
    assert "shop_anvil" in settlement.facility_ids

    # Verify bottom-up instant resolution
    path = reg.resolve_hierarchy("shop_anvil")
    assert path["facility"].name == "모루 철물점"
    assert path["settlement"].name == "모루 성채"
    assert path["nation"].name == "드워프 왕국"
    assert path["region"].name == "아이언포지 광산 산맥"
    assert path["continent"].name == "발리리아 구 대륙"


def test_cascading_commercial_price_calculation():
    """Prices calculate both regional natural resource abundance and international tariffs."""
    reg = InfrastructureRegistry()

    reg.register_continent(Continent(id="valyria", name="발리리아 대륙"))
    reg.register_region(Region(id="reg_mountain", name="산악 지대", continent_id="valyria", natural_price_multipliers={"ore": 0.4, "salt": 3.0}))
    reg.register_nation(Nation(id="nation_dwarf", name="드워프 왕국", continent_id="valyria", tariff_rate=0.20, diplomatic_relations={"nation_human": "neutral", "nation_orc": "at_war", "nation_elf": "allied"}))
    reg.register_settlement(Settlement(id="settle_capital", name="지하 수도", nation_id="nation_dwarf", region_id="reg_mountain"))
    reg.register_facility(Facility(id="fac_market", name="광장 상점", settlement_id="settle_capital"))

    # 1. Domestic transaction (Buyer from same nation): 100G Ore -> 100 * 0.4 = 40G
    price_domestic_ore = reg.calculate_effective_price(
        item_category="ore", base_price=100, facility_id="fac_market", buyer_nation_id="nation_dwarf"
    )
    assert price_domestic_ore["final_price"] == 40
    assert price_domestic_ore["tariff_rate"] == 0.0

    # 2. Domestic Salt: 10G Salt -> 10 * 3.0 = 30G
    price_domestic_salt = reg.calculate_effective_price(
        item_category="salt", base_price=10, facility_id="fac_market", buyer_nation_id="nation_dwarf"
    )
    assert price_domestic_salt["final_price"] == 30

    # 3. Foreign neutral buyer (Human): 100G Ore -> 100 * 0.4 * 1.20 (20% tariff) = 48G
    price_foreign_ore = reg.calculate_effective_price(
        item_category="ore", base_price=100, facility_id="fac_market", buyer_nation_id="nation_human"
    )
    assert price_foreign_ore["final_price"] == 48
    assert price_foreign_ore["tariff_rate"] == 0.20

    # 4. Allied buyer (Elf): 100G Ore -> 100 * 0.4 * (1 + 0.10) (half tariff discount) = 44G
    price_allied_ore = reg.calculate_effective_price(
        item_category="ore", base_price=100, facility_id="fac_market", buyer_nation_id="nation_elf"
    )
    assert price_allied_ore["final_price"] == 44

    # 5. Wartime enemy (Orc): 100% embargo tariff
    price_enemy_ore = reg.calculate_effective_price(
        item_category="ore", base_price=100, facility_id="fac_market", buyer_nation_id="nation_orc"
    )
    assert price_enemy_ore["final_price"] == 80
    assert price_enemy_ore["diplomatic_status"] == "at_war"


def test_border_checkpoint_entry_verification():
    """Border checks enforce passport requirements, detect contraband, and block wartime enemies."""
    reg = InfrastructureRegistry()

    reg.register_nation(Nation(
        id="holy_kingdom",
        name="루멘 성왕국",
        continent_id="c1",
        passport_required=True,
        contraband=["강령술 스크롤", "마약초"],
        diplomatic_relations={"heretic_order": "at_war", "nomad_clan": "neutral"}
    ))
    reg.register_settlement(Settlement(
        id="border_gate",
        name="성왕국 남부 국경 관문",
        nation_id="holy_kingdom",
        region_id="r1"
    ))

    # 1. Foreigner without passport -> Blocked
    res_no_pass = reg.check_border_entry(
        player_nation_id="nomad_clan",
        destination_settlement_id="border_gate",
        player_has_passport=False,
        inventory_items=["여행자 배낭", "비상식량"]
    )
    assert res_no_pass["allowed"] is False
    assert "통행증" in res_no_pass["reason"]

    # 2. Foreigner with passport and clean inventory -> Allowed
    res_allowed = reg.check_border_entry(
        player_nation_id="nomad_clan",
        destination_settlement_id="border_gate",
        player_has_passport=True,
        inventory_items=["여행자 배낭", "비상식량"]
    )
    assert res_allowed["allowed"] is True
    assert "정식 통과" in res_allowed["reason"]

    # 3. Foreigner carrying contraband -> Blocked & Combat trigger
    res_contraband = reg.check_border_entry(
        player_nation_id="nomad_clan",
        destination_settlement_id="border_gate",
        player_has_passport=True,
        inventory_items=["여행자 배낭", "금지된 강령술 스크롤 초본"]
    )
    assert res_contraband["allowed"] is False
    assert res_contraband["is_combat_trigger"] is True
    assert "밀수품" in res_contraband["reason"]
    assert len(res_contraband["confiscated_items"]) == 1

    # 4. Wartime enemy -> Absolute blockade
    res_war = reg.check_border_entry(
        player_nation_id="heretic_order",
        destination_settlement_id="border_gate",
        player_has_passport=True,
        inventory_items=["일반 검"]
    )
    assert res_war["allowed"] is False
    assert "전면전" in res_war["reason"]
    assert res_war["is_combat_trigger"] is True


def test_registry_serialization_roundtrip():
    """Registry survives full to_dict and from_dict serialization."""
    reg = InfrastructureRegistry()
    reg.register_continent(Continent(id="c1", name="대륙1"))
    reg.register_region(Region(id="r1", name="권역1", continent_id="c1"))
    reg.register_nation(Nation(id="n1", name="국가1", continent_id="c1"))
    reg.register_settlement(Settlement(id="s1", name="마을1", nation_id="n1", region_id="r1"))
    reg.register_facility(Facility(id="f1", name="시설1", settlement_id="s1"))

    dumped = reg.to_dict()
    loaded = InfrastructureRegistry.from_dict(dumped)

    assert "c1" in loaded.continents
    assert "r1" in loaded.regions
    assert "n1" in loaded.nations
    assert "s1" in loaded.settlements
    assert "f1" in loaded.facilities

    path = loaded.resolve_hierarchy("f1")
    assert path["continent"].name == "대륙1"
    assert path["settlement"].name == "마을1"


def test_worldstate_infrastructure_integration():
    """WorldState integrates InfrastructureRegistry seamlessly into to_json and from_json."""
    from src.world.state import WorldState

    state = WorldState(world_name="통합 판타지 대륙")
    reg = InfrastructureRegistry()
    reg.register_continent(Continent(id="cont_solis", name="솔리스 대륙"))
    reg.register_region(Region(id="reg_plains", name="솔리스 평야", continent_id="cont_solis"))
    reg.register_nation(Nation(id="nat_solis", name="솔리스 성왕국", continent_id="cont_solis"))
    reg.register_settlement(Settlement(id="settle_capital", name="솔리스 성도", nation_id="nat_solis", region_id="reg_plains"))
    reg.register_facility(Facility(id="fac_inn", name="빛나는 안식처 여관", settlement_id="settle_capital"))

    state.infrastructure = reg

    json_str = state.to_json()
    loaded_state = WorldState.from_json(json_str)

    assert loaded_state.infrastructure is not None
    assert "cont_solis" in loaded_state.infrastructure.continents
    resolved = loaded_state.infrastructure.resolve_hierarchy("fac_inn")
    assert resolved["continent"].name == "솔리스 대륙"
    assert resolved["nation"].name == "솔리스 성왕국"
    assert resolved["settlement"].name == "솔리스 성도"


def test_3_tier_specialties_resolution():
    """Resolves local, national, and regional specialties into a unified hierarchical dictionary."""
    reg = InfrastructureRegistry()

    reg.register_continent(Continent(id="cont_north", name="북부 대륙"))
    reg.register_region(Region(
        id="reg_tundra",
        name="영구동토대",
        continent_id="cont_north",
        specialties=["빙하 소금", "백호 모피", "서리 이끼"]
    ))
    reg.register_nation(Nation(
        id="nat_frost_guard",
        name="서리수호 공국",
        continent_id="cont_north",
        specialties=["냉기 강화 흑철검", "고래 기름 양초"]
    ))
    reg.register_settlement(Settlement(
        id="settle_whale_port",
        name="고래숨결 어촌",
        nation_id="nat_frost_guard",
        region_id="reg_tundra",
        specialties=["훈제 은송어", "빙해 바다표범 가죽"]
    ))

    specs = reg.resolve_specialties("settle_whale_port")

    # Local settlement specialties
    assert "훈제 은송어" in specs["settlement"]
    assert "빙해 바다표범 가죽" in specs["settlement"]

    # National manufactured specialties
    assert "냉기 강화 흑철검" in specs["nation"]
    assert "고래 기름 양초" in specs["nation"]

    # Regional natural/climate specialties
    assert "빙하 소금" in specs["region"]
    assert "백호 모피" in specs["region"]

    # Unified list contains all 6
    assert len(specs["all"]) == 7
    assert specs["settlement_name"] == "고래숨결 어촌"
    assert specs["nation_name"] == "서리수호 공국"
    assert specs["region_name"] == "영구동토대"


def test_bottom_up_population_and_area_rollup():
    """Settlement populations and areas aggregate dynamically to Nation, Region, Continent, and WorldState."""
    from src.world.state import WorldState

    reg = InfrastructureRegistry()
    reg.register_continent(Continent(id="cont_valyria", name="발리리아"))
    reg.register_region(Region(id="reg_plains", name="황금 평야", continent_id="cont_valyria"))
    reg.register_region(Region(id="reg_coast", name="비취 해안", continent_id="cont_valyria"))
    reg.register_nation(Nation(id="nat_kingdom", name="태양 왕국", continent_id="cont_valyria"))

    # Settlement 1: Village in Plains (Pop: 1,200, Area: 25.0 km²)
    s1 = Settlement(
        id="s1", name="밀밭마을", nation_id="nat_kingdom", region_id="reg_plains",
        population=1200, area_sq_km=25.0
    )
    # Settlement 2: Capital in Plains (Pop: 50,000, Area: 120.0 km²)
    s2 = Settlement(
        id="s2", name="태양수도", nation_id="nat_kingdom", region_id="reg_plains",
        population=50000, area_sq_km=120.0
    )
    # Settlement 3: Port in Coast (Pop: 15,000, Area: 40.0 km²)
    s3 = Settlement(
        id="s3", name="비취항구", nation_id="nat_kingdom", region_id="reg_coast",
        population=15000, area_sq_km=40.0
    )

    reg.register_settlement(s1)
    reg.register_settlement(s2)
    reg.register_settlement(s3)

    # Trigger Roll-up
    reg.recalculate_totals()

    # Verify Nation totals: 1,200 + 50,000 + 15,000 = 66,200 pop, 185.0 km²
    nation = reg.nations["nat_kingdom"]
    assert nation.population == 66200
    assert nation.area_sq_km == 185.0

    # Verify Region totals: Plains = 51,200 pop, 145.0 km²; Coast = 15,000 pop, 40.0 km²
    assert reg.regions["reg_plains"].population == 51200
    assert reg.regions["reg_plains"].area_sq_km == 145.0
    assert reg.regions["reg_coast"].population == 15000
    assert reg.regions["reg_coast"].area_sq_km == 40.0

    # Verify Continent totals: 66,200 pop, 185.0 km²
    assert reg.continents["cont_valyria"].population == 66200
    assert reg.continents["cont_valyria"].area_sq_km == 185.0

    # Verify WorldState synchronization
    state = WorldState(infrastructure=reg)
    state.sync_infrastructure_totals()
    assert state.total_population == 66200
    assert state.total_area_sq_km == 185.0


def test_clean_generic_defaults():
    """Verify that Faction, WorldState, NPCVisualDetails, and EnvironmentalMetrics have neutral generic defaults."""
    from src.world.state import Faction, NPCVisualDetails, WorldState, EnvironmentalMetrics

    fac = Faction(id="f1", name="자유 상단")
    assert fac.emblem_animal == ""
    assert fac.flag_colors == []
    assert fac.flag_symbol == ""

    ws = WorldState()
    assert ws.world_name == ""
    assert ws.world_genre == ""
    assert ws.total_population == 0
    assert ws.total_area_sq_km == 0.0

    env = EnvironmentalMetrics()
    assert env.smell == ""
    assert env.noise == ""
    assert env.scent_trace == ""

    vis = NPCVisualDetails()
    assert vis.species == ""
    assert vis.gender == ""
    assert vis.clothing_style == ""
    assert vis.hair_color == ""


def test_inter_tier_route_and_bottlenecks():
    """Verify RouteCategory, RoadConnection bottleneck metadata, and InterTierRoute multi-tier networks."""
    from src.world.geography import RouteCategory
    from src.world.infrastructure import InterTierRoute

    # 1. Settlement road with bottleneck (e.g. mountain canyon gate)
    road = RoadConnection(
        destination_id="town_gorge",
        distance_km=12.0,
        route_category=RouteCategory.BOTTLENECK_PASS,
        is_bottleneck=True,
        bottleneck_type="협곡 관문",
        supply_facilities=["간이 역참", "식수 우물"],
        allowed_transit_types=["foot", "pack_mule"]
    )
    assert road.route_category == RouteCategory.BOTTLENECK_PASS
    assert road.is_bottleneck is True
    assert "간이 역참" in road.supply_facilities

    # 2. Inter-Nation Highway
    highway = InterTierRoute(
        origin_id="nation_ironforge",
        destination_id="nation_solis",
        route_name="중앙 대륙 관문 가도",
        route_category=RouteCategory.TRUNK_HIGHWAY,
        distance_km=150.0,
        travel_medium="land",
        toll_fee=50,
        is_bottleneck=True,
        bottleneck_type="국경 철혈 관문",
        supply_facilities=["제3 국경 역참", "기사단 경비소"]
    )
    assert highway.toll_fee == 50
    assert highway.route_category == RouteCategory.TRUNK_HIGHWAY

    reg = InfrastructureRegistry()
    reg.register_nation(Nation(id="nation_ironforge", name="아이언포지", continent_id="c1"))
    reg.register_inter_tier_route(highway, tier="nation")

    routes = reg.find_inter_tier_routes("nation_ironforge")
    assert len(routes) == 1
    assert routes[0].route_name == "중앙 대륙 관문 가도"


def test_transit_and_logistics_network():
    """Verify TransitVehicle and LogisticsNetwork schemas."""
    from src.world.infrastructure import TransitVehicle, LogisticsNetwork

    v1 = TransitVehicle(
        id="veh_mule_cart",
        name="보강 노새 짐마차",
        category="land",
        base_speed_kmh=8.0,
        cargo_capacity_kg=600.0,
        passenger_capacity=3,
        terrain_compatibility=["paved_highway", "dirt_road"],
        daily_maintenance_cost=5
    )
    v2 = TransitVehicle(
        id="veh_coastal_sloop",
        name="연안 연승 범선",
        category="water",
        base_speed_kmh=14.0,
        cargo_capacity_kg=2500.0,
        passenger_capacity=10,
        terrain_compatibility=["coastal_water", "deep_sea"],
        daily_maintenance_cost=30
    )

    logistics = LogisticsNetwork(
        caravan_routes=[{"name": "북방 대상단로", "interval_days": 14}],
        courier_relays=["제1 역참", "제2 역참"],
        postal_stations=["수도 중앙 전신소"],
        transit_vehicles=[v1, v2]
    )

    dumped = logistics.to_dict()
    loaded = LogisticsNetwork.from_dict(dumped)

    assert len(loaded.transit_vehicles) == 2
    assert loaded.transit_vehicles[0].name == "보강 노새 짐마차"
    assert loaded.transit_vehicles[1].category == "water"
    assert "제1 역참" in loaded.courier_relays


def test_attire_cuisine_culture_generic_defaults():
    """Verify that Attire, Cuisine, and Culture profiles default to empty schemas without hardcoded strings."""
    from src.world.infrastructure import AttireHierarchyProfile, CuisineProfile, CulturalNormsProfile

    attire = AttireHierarchyProfile()
    assert attire.labor_lower_class == []
    assert attire.middle_practical_class == []
    assert attire.upper_ruling_class == []
    assert attire.special_organizations == {}

    cuisine = CuisineProfile()
    assert cuisine.staples == []
    assert cuisine.proteins_and_salts == []
    assert cuisine.expedition_rations == []
    assert cuisine.beverages_and_water == []

    culture = CulturalNormsProfile()
    assert culture.social_structure == []
    assert culture.faith_and_beliefs == []
    assert culture.commercial_customs == []
    assert culture.seasonal_events == []


def test_resolve_settlement_lifestyle_cascading():
    """Verify resolve_settlement_lifestyle cascades and merges attire, cuisine, culture, and logistics."""
    from src.world.infrastructure import (
        AttireHierarchyProfile, CuisineProfile, CulturalNormsProfile, LogisticsNetwork, TransitVehicle
    )

    reg = InfrastructureRegistry()

    # 1. Continent: Macro Culture & Cuisine
    cont = Continent(
        id="cont_north",
        name="북부 대륙",
        cuisine=CuisineProfile(staples=["호밀", "보리"], beverages_and_water=["빙하수"]),
        culture=CulturalNormsProfile(faith_and_beliefs=["오로라 천신 신앙"])
    )

    # 2. Region: Biome-adapted Attire & Cuisine
    region = Region(
        id="reg_tundra",
        name="설원 권역",
        continent_id="cont_north",
        attire=AttireHierarchyProfile(labor_lower_class=["두꺼운 모피 덧옷"]),
        cuisine=CuisineProfile(proteins_and_salts=["고래 염장육", "빙해 바다표범 고기"])
    )

    # 3. Nation: Social Norms, Upper Attire, Logistics
    v_horse = TransitVehicle(id="v_horse", name="전투 군마", category="land", base_speed_kmh=16.0)
    nation = Nation(
        id="nat_frost",
        name="서리 왕국",
        continent_id="cont_north",
        attire=AttireHierarchyProfile(
            upper_ruling_class=["은사 백호 모피 망토"],
            special_organizations={"기사단": "서리철갑 제복"}
        ),
        culture=CulturalNormsProfile(social_structure=["봉건 영주-기사 서약"]),
        logistics=LogisticsNetwork(courier_relays=["왕도 전령소"], transit_vehicles=[v_horse])
    )

    # 4. Settlement: Local Cuisine & Local Festival
    settle = Settlement(
        id="settle_hearth",
        name="모닥불 마을",
        nation_id="nat_frost",
        region_id="reg_tundra",
        cuisine=CuisineProfile(staples=["향토 보리 감자죽"], expedition_rations=["훈제 생선포"]),
        culture=CulturalNormsProfile(seasonal_events=["한겨울 모닥불 축제"])
    )

    reg.register_continent(cont)
    reg.register_region(region)
    reg.register_nation(nation)
    reg.register_settlement(settle)

    lifestyle = reg.resolve_settlement_lifestyle("settle_hearth")

    # Cascaded Cuisine: staples contains both Continent ("호밀", "보리") and Settlement ("향토 보리 감자죽")
    assert "호밀" in lifestyle["cuisine"]["staples"]
    assert "향토 보리 감자죽" in lifestyle["cuisine"]["staples"]
    assert "고래 염장육" in lifestyle["cuisine"]["proteins_and_salts"]
    assert "훈제 생선포" in lifestyle["cuisine"]["expedition_rations"]
    assert "빙하수" in lifestyle["cuisine"]["beverages_and_water"]

    # Cascaded Attire: labor contains Region ("두꺼운 모피 덧옷"), upper contains Nation ("은사 백호 모피 망토")
    assert "두꺼운 모피 덧옷" in lifestyle["attire"]["labor_lower_class"]
    assert "은사 백호 모피 망토" in lifestyle["attire"]["upper_ruling_class"]
    assert lifestyle["attire"]["special_organizations"]["기사단"] == "서리철갑 제복"

    # Cascaded Culture: continent faith + nation structure + settlement seasonal event
    assert "오로라 천신 신앙" in lifestyle["culture"]["faith_and_beliefs"]
    assert "봉건 영주-기사 서약" in lifestyle["culture"]["social_structure"]
    assert "한겨울 모닥불 축제" in lifestyle["culture"]["seasonal_events"]

    # Cascaded Logistics vehicles
    assert len(lifestyle["transit_vehicles"]) == 1
    assert lifestyle["transit_vehicles"][0].name == "전투 군마"


def test_civilization_tiers_in_world_nation_settlement():
    """Verify civilization tiers across Level 0 (WorldState), Level 3 (Nation), Level 4 (Settlement)."""
    from src.world.state import WorldState
    from src.world.infrastructure import Nation, Settlement

    # 1. Level 0: WorldState era
    state = WorldState()
    assert state.civilization_era == ""
    state.civilization_era = "마도 르네상스 제국기"
    state_dict = state.to_dict()
    assert state_dict["civilization_era"] == "마도 르네상스 제국기"
    loaded_state = WorldState.from_dict(state_dict)
    assert loaded_state.civilization_era == "마도 르네상스 제국기"

    # 2. Level 3: Nation civilization level
    nation = Nation(id="nat_empire", name="아르카니아 제국", continent_id="cont_1", civilization_level="마도공학 후기 중세")
    assert nation.civilization_level == "마도공학 후기 중세"
    nat_dict = nation.to_dict()
    assert nat_dict["civilization_level"] == "마도공학 후기 중세"
    assert Nation.from_dict(nat_dict).civilization_level == "마도공학 후기 중세"

    # 3. Level 4: Settlement development tier
    settle = Settlement(id="settle_capital", name="성도 아르카", nation_id="nat_empire", region_id="reg_1", development_tier=5)
    assert settle.development_tier == 5
    settle_dict = settle.to_dict()
    assert settle_dict["development_tier"] == 5
    assert Settlement.from_dict(settle_dict).development_tier == 5


def test_settlement_infrastructure_profile_generic_defaults_and_roundtrip():
    """Verify 5-sector infrastructure defaults are pure generic empty lists and survive roundtrip."""
    from src.world.infrastructure import (
        Settlement,
        SettlementInfrastructureProfile,
        SanitationWaterInfrastructure,
        FoodStorageInfrastructure,
        DefenseSecurityInfrastructure,
        TradeWorkshopsInfrastructure,
        CivicHealthInfrastructure,
    )

    settle = Settlement(id="settle_pure", name="무작위 개척촌", nation_id="n1", region_id="r1")
    infra = settle.infrastructure

    # Strict Anti-Hardcoding: All list fields MUST default to empty lists
    assert infra.sanitation.water_sources == []
    assert infra.sanitation.drainage_and_sewage == []
    assert infra.sanitation.public_sanitation == []
    assert infra.sanitation.waste_and_cemeteries == []
    assert infra.food.grain_processing == []
    assert infra.food.communal_cooking_preserving == []
    assert infra.food.storage_and_reserves == []
    assert infra.food.livestock_facilities == []
    assert infra.defense.physical_barriers == []
    assert infra.defense.access_control == []
    assert infra.defense.disaster_prevention == []
    assert infra.defense.security_posts == []
    assert infra.trade.artisan_workshops == []
    assert infra.trade.distribution_hubs == []
    assert infra.trade.lodging_and_transit == []
    assert infra.civic.medical_and_relief == []
    assert infra.civic.governance_and_assembly == []
    assert infra.civic.faith_and_shrines == []

    # Populate with custom data and verify roundtrip
    infra.sanitation.water_sources = ["천연 용천수", "공동 우물"]
    infra.food.grain_processing = ["수력 물레방아"]
    infra.defense.physical_barriers = ["통나무 목책", "해자"]
    infra.trade.artisan_workshops = ["간이 대장간"]
    infra.civic.governance_and_assembly = ["원로 집회소"]

    settle_dict = settle.to_dict()
    loaded = Settlement.from_dict(settle_dict)

    assert loaded.infrastructure.sanitation.water_sources == ["천연 용천수", "공동 우물"]
    assert loaded.infrastructure.food.grain_processing == ["수력 물레방아"]
    assert loaded.infrastructure.defense.physical_barriers == ["통나무 목책", "해자"]
    assert loaded.infrastructure.trade.artisan_workshops == ["간이 대장간"]
    assert loaded.infrastructure.civic.governance_and_assembly == ["원로 집회소"]


def test_facility_category_and_communal_flag():
    """Verify FacilityCategory enum and communal public flag on Facility."""
    from src.world.infrastructure import Facility, FacilityCategory

    fac_public = Facility(
        id="fac_well_01",
        name="중앙 광장 공용 우물",
        settlement_id="s1",
        category=FacilityCategory.SANITATION_WATER,
        is_communal_public=True
    )
    assert fac_public.category == FacilityCategory.SANITATION_WATER
    assert fac_public.is_communal_public is True

    fac_dict = fac_public.to_dict()
    assert fac_dict["category"] == "sanitation_water"
    assert fac_dict["is_communal_public"] is True

    loaded_fac = Facility.from_dict(fac_dict)
    assert loaded_fac.category == FacilityCategory.SANITATION_WATER
    assert loaded_fac.is_communal_public is True


def test_audit_settlement_resilience_vulnerabilities_and_scores():
    """Verify deterministic audit_settlement_resilience correctly flags hazards and scores."""
    reg = InfrastructureRegistry()

    # Vulnerable Settlement: no water source, low water self-sufficiency, no disaster prep, no waste handling
    vulnerable_settle = Settlement(
        id="settle_ruin",
        name="황폐한 난민촌",
        nation_id="n1",
        region_id="r1",
        population=800,
        self_sufficiency_water=30,
        hygiene_level=40,
        wall_defense_tier=0,
        security_level=20
    )
    vulnerable_settle.infrastructure.food.storage_reserve_months = 0.5  # under 1 month
    reg.register_settlement(vulnerable_settle)

    audit_vuln = reg.audit_settlement_resilience("settle_ruin")
    assert audit_vuln["is_critical_hazard"] is True
    assert "상수원_부재_식수위기" in audit_vuln["vulnerabilities"]
    assert "식량비축_부족_겨울기근위험" in audit_vuln["vulnerabilities"]
    assert "곡물가공_시설결여" in audit_vuln["vulnerabilities"]
    assert "하수시설_미비_역병위험" in audit_vuln["vulnerabilities"]
    assert "의료구호_시설부재" in audit_vuln["vulnerabilities"]
    assert "방재경보_부재_화재취약" in audit_vuln["vulnerabilities"]
    assert "물리방벽_전무_침입취약" in audit_vuln["vulnerabilities"]
    assert audit_vuln["overall_resilience_score"] < 50.0

    # Resilient Fortified Town: fully equipped
    fortified_settle = Settlement(
        id="settle_fort",
        name="철벽의 요새도시",
        nation_id="n1",
        region_id="r1",
        population=3000,
        self_sufficiency_water=95,
        self_sufficiency_food=90,
        hygiene_level=85,
        wall_defense_tier=3,
        security_level=90
    )
    fortified_settle.infrastructure.sanitation.water_sources = ["지하 암반수정 우물", "성내 저수조"]
    fortified_settle.infrastructure.sanitation.drainage_and_sewage = ["암거 배수로"]
    fortified_settle.infrastructure.sanitation.public_sanitation = ["목욕탕"]
    fortified_settle.infrastructure.sanitation.water_capacity_rating = 90
    fortified_settle.infrastructure.sanitation.waste_treatment_rating = 85
    fortified_settle.infrastructure.food.grain_processing = ["성채 대형 풍차"]
    fortified_settle.infrastructure.food.storage_and_reserves = ["지하 빙고", "방화 곡물창고"]
    fortified_settle.infrastructure.food.storage_reserve_months = 12.0
    fortified_settle.infrastructure.food.processing_capacity_rating = 85
    fortified_settle.infrastructure.defense.physical_barriers = ["외성벽", "내성벽", "외곽 해자"]
    fortified_settle.infrastructure.defense.disaster_prevention = ["방화수조", "경보 종탑"]
    fortified_settle.infrastructure.defense.security_posts = ["성문 수비대 초소"]
    fortified_settle.infrastructure.defense.fortification_integrity = 95
    fortified_settle.infrastructure.defense.fire_preparedness_rating = 90
    fortified_settle.infrastructure.trade.artisan_workshops = ["왕립 무기고 대장간"]
    fortified_settle.infrastructure.trade.distribution_hubs = ["성문 하역장"]
    fortified_settle.infrastructure.trade.production_vitality_rating = 85
    fortified_settle.infrastructure.civic.medical_and_relief = ["성채 의원"]
    fortified_settle.infrastructure.civic.governance_and_assembly = ["영주 회의청"]
    fortified_settle.infrastructure.civic.faith_and_shrines = ["기사의 성소"]
    fortified_settle.infrastructure.civic.healthcare_rating = 85
    fortified_settle.infrastructure.civic.social_cohesion_rating = 90
    reg.register_settlement(fortified_settle)

    audit_fort = reg.audit_settlement_resilience("settle_fort")
    assert audit_fort["is_critical_hazard"] is False
    assert len(audit_fort["vulnerabilities"]) == 0
    assert audit_fort["overall_resilience_score"] >= 80.0


def test_macro_micro_civilization_dynamics():
    """Verify macro epoch, regional hazards/deposits, national stability/treasury, and settlement discontent/loyalty."""
    from src.world.state import WorldState
    from src.world.infrastructure import Region, Nation, Settlement, Facility

    # 1. Level 0: WorldState epoch_state
    state = WorldState()
    assert state.epoch_state == "안정기"
    state.epoch_state = "암흑기"
    state_d = state.to_dict()
    assert state_d["epoch_state"] == "암흑기"
    assert WorldState.from_dict(state_d).epoch_state == "암흑기"

    # 2. Level 2: Region natural hazards & strategic deposits
    reg = Region(
        id="reg_volcano",
        name="흑요석 화산 권역",
        continent_id="c1",
        natural_hazards=["화산 폭발", "지진 단층"],
        strategic_deposits=["흑요석 광맥", "초석 동굴"]
    )
    reg_d = reg.to_dict()
    assert reg_d["natural_hazards"] == ["화산 폭발", "지진 단층"]
    assert reg_d["strategic_deposits"] == ["흑요석 광맥", "초석 동굴"]
    loaded_reg = Region.from_dict(reg_d)
    assert loaded_reg.natural_hazards == ["화산 폭발", "지진 단층"]
    assert loaded_reg.strategic_deposits == ["흑요석 광맥", "초석 동굴"]

    # 3. Level 3: Nation stability, treasury, tax, war weariness, strategic stockpiles
    nat = Nation(
        id="nat_war",
        name="철혈 군사왕국",
        continent_id="c1",
        national_treasury=45000,
        tax_rate=0.25,
        national_stability=40,
        war_weariness=65,
        strategic_stockpiles={"철광석": 1200, "군마": 300, "화약": 150}
    )
    nat_d = nat.to_dict()
    assert nat_d["national_treasury"] == 45000
    assert nat_d["tax_rate"] == 0.25
    assert nat_d["national_stability"] == 40
    assert nat_d["war_weariness"] == 65
    assert nat_d["strategic_stockpiles"]["철광석"] == 1200
    loaded_nat = Nation.from_dict(nat_d)
    assert loaded_nat.national_stability == 40
    assert loaded_nat.strategic_stockpiles["화약"] == 150

    # 4. Level 4: Settlement prosperity, treasury, discontent, loyalty
    settle = Settlement(
        id="settle_border",
        name="국경 분쟁 요새마을",
        nation_id="nat_war",
        region_id="reg_volcano",
        prosperity_rating=35,
        treasury=220,
        discontent_level=75,
        loyalty_to_nation=30
    )
    settle_d = settle.to_dict()
    assert settle_d["prosperity_rating"] == 35
    assert settle_d["treasury"] == 220
    assert settle_d["discontent_level"] == 75
    assert settle_d["loyalty_to_nation"] == 30
    loaded_settle = Settlement.from_dict(settle_d)
    assert loaded_settle.discontent_level == 75
    assert loaded_settle.loyalty_to_nation == 30

    # 5. Level 5: Facility daily_maintenance_cost
    fac = Facility(
        id="fac_wall_gate",
        name="국경 철벽 수문",
        settlement_id="settle_border",
        durability=90,
        daily_maintenance_cost=15
    )
    fac_d = fac.to_dict()
    assert fac_d["daily_maintenance_cost"] == 15
    loaded_fac = Facility.from_dict(fac_d)
    assert loaded_fac.daily_maintenance_cost == 15


def test_civ_yields_religion_treaties_espionage_wonders():
    """Verify 6-yield system, religious demographics, diplomatic treaties, counter-intelligence, and wonders."""
    from src.world.state import WorldState
    from src.world.infrastructure import Region, Nation, Settlement, Facility, SettlementYields

    # 1. Level 0: WorldState founded_religions
    state = WorldState()
    assert state.founded_religions == []
    state.founded_religions = ["성광교회", "원시정령신앙", "심연의 찬가"]
    state_d = state.to_dict()
    assert state_d["founded_religions"] == ["성광교회", "원시정령신앙", "심연의 찬가"]
    assert WorldState.from_dict(state_d).founded_religions == ["성광교회", "원시정령신앙", "심연의 찬가"]

    # 2. Level 2: Region natural_wonders
    reg = Region(
        id="reg_grove",
        name="영원의 숲",
        continent_id="c1",
        natural_wonders=["살아 숨쉬는 세계수 분지", "마나 폭포 협곡"]
    )
    reg_d = reg.to_dict()
    assert reg_d["natural_wonders"] == ["살아 숨쉬는 세계수 분지", "마나 폭포 협곡"]
    assert Region.from_dict(reg_d).natural_wonders == ["살아 숨쉬는 세계수 분지", "마나 폭포 협곡"]

    # 3. Level 3: Nation state religion, tolerance, and treaties
    nat = Nation(
        id="nat_holy",
        name="루멘 성왕국",
        continent_id="c1",
        state_religion="성광교회",
        religious_tolerance=10,
        diplomatic_treaties={
            "nat_iron": ["open_borders", "defensive_pact"],
            "nat_evil": ["trade_embargo"]
        }
    )
    nat_d = nat.to_dict()
    assert nat_d["state_religion"] == "성광교회"
    assert nat_d["religious_tolerance"] == 10
    assert nat_d["diplomatic_treaties"]["nat_iron"] == ["open_borders", "defensive_pact"]
    loaded_nat = Nation.from_dict(nat_d)
    assert loaded_nat.state_religion == "성광교회"
    assert loaded_nat.religious_tolerance == 10
    assert loaded_nat.diplomatic_treaties["nat_evil"] == ["trade_embargo"]

    # 4. Level 4: Settlement yields, religious demographics, tension, espionage, wonders
    settle = Settlement(
        id="settle_cathedral",
        name="대성당 성지마을",
        nation_id="nat_holy",
        region_id="reg_grove",
        yields=SettlementYields(
            food=120.5,
            production=85.0,
            gold=210.0,
            science=45.0,
            culture=150.0,
            faith=320.0
        ),
        religious_demographics={"성광교회": 0.85, "원시정령신앙": 0.15},
        sectarian_tension=25,
        counter_intelligence_rating=75,
        world_wonders=["대성당 천공탑"]
    )
    settle_d = settle.to_dict()
    assert settle_d["yields"]["faith"] == 320.0
    assert settle_d["yields"]["food"] == 120.5
    assert settle_d["religious_demographics"]["성광교회"] == 0.85
    assert settle_d["sectarian_tension"] == 25
    assert settle_d["counter_intelligence_rating"] == 75
    assert settle_d["world_wonders"] == ["대성당 천공탑"]

    loaded_settle = Settlement.from_dict(settle_d)
    assert loaded_settle.yields.faith == 320.0
    assert loaded_settle.yields.production == 85.0
    assert loaded_settle.religious_demographics["원시정령신앙"] == 0.15
    assert loaded_settle.sectarian_tension == 25
    assert loaded_settle.counter_intelligence_rating == 75
    assert loaded_settle.world_wonders == ["대성당 천공탑"]

    # 5. Level 5: Facility is_wonder
    wonder_fac = Facility(
        id="fac_spire",
        name="대성당 천공탑",
        settlement_id="settle_cathedral",
        is_wonder=True
    )
    fac_d = wonder_fac.to_dict()
    assert fac_d["is_wonder"] is True
    assert Facility.from_dict(fac_d).is_wonder is True


def test_feudal_roles_and_grand_sim_systems():
    """Verify monarch, lord, bailiff, village head, classes, patrols, relics, and emergency decrees."""
    from src.world.infrastructure import Nation, Settlement

    # 1. Level 3: Nation monarch and dynasty
    nat = Nation(
        id="nat_solis",
        name="솔리스 왕국",
        continent_id="c1",
        monarch_title="태양왕",
        monarch_npc_id="npc_king_solis_iv",
        ruling_dynasty="루멘 혈통",
        dynasty_legitimacy=90
    )
    nat_d = nat.to_dict()
    assert nat_d["monarch_title"] == "태양왕"
    assert nat_d["monarch_npc_id"] == "npc_king_solis_iv"
    assert nat_d["ruling_dynasty"] == "루멘 혈통"
    assert nat_d["dynasty_legitimacy"] == 90
    loaded_nat = Nation.from_dict(nat_d)
    assert loaded_nat.monarch_npc_id == "npc_king_solis_iv"
    assert loaded_nat.ruling_dynasty == "루멘 혈통"

    # 2. Level 4: Settlement lord, bailiff, village head, classes, patrols, relics, emergency decrees
    settle = Settlement(
        id="settle_manor",
        name="밀밭 장원마을",
        nation_id="nat_solis",
        region_id="reg_plains",
        lord_npc_id="npc_lord_aldous",
        lord_dynasty="알도우스 자작 가문",
        bailiff_npc_id="npc_bailiff_milo",
        village_head_npc_id="npc_elder_bran",
        bailiff_villager_affinity=35,
        social_classes_demographics={"nobles": 0.02, "clergy": 0.08, "artisans": 0.15, "peasants": 0.75},
        interest_group_conflicts=["소작농_부역_부담_원한", "영주_곡물_강제징수"],
        patrol_strength=65,
        bandit_threat_level=25,
        masterwork_relics=["성자의 황금 낫", "초대 촌장의 청동 피리"],
        mental_break_risk=20,
        emergency_decrees=["아동노동_징집_금지", "야간_통행_경비제"]
    )
    settle_d = settle.to_dict()
    assert settle_d["lord_npc_id"] == "npc_lord_aldous"
    assert settle_d["lord_dynasty"] == "알도우스 자작 가문"
    assert settle_d["bailiff_npc_id"] == "npc_bailiff_milo"
    assert settle_d["village_head_npc_id"] == "npc_elder_bran"
    assert settle_d["bailiff_villager_affinity"] == 35
    assert settle_d["social_classes_demographics"]["peasants"] == 0.75
    assert "소작농_부역_부담_원한" in settle_d["interest_group_conflicts"]
    assert settle_d["patrol_strength"] == 65
    assert settle_d["bandit_threat_level"] == 25
    assert "성자의 황금 낫" in settle_d["masterwork_relics"]
    assert settle_d["mental_break_risk"] == 20
    assert "야간_통행_경비제" in settle_d["emergency_decrees"]

    loaded_settle = Settlement.from_dict(settle_d)
    assert loaded_settle.bailiff_npc_id == "npc_bailiff_milo"
    assert loaded_settle.village_head_npc_id == "npc_elder_bran"
    assert loaded_settle.bailiff_villager_affinity == 35
    assert loaded_settle.lord_dynasty == "알도우스 자작 가문"
    assert len(loaded_settle.masterwork_relics) == 2
    assert len(loaded_settle.emergency_decrees) == 2


def test_dark_fantasy_and_occupations():
    """Verify monster infestation, curses, cults, black market, bounties, occupations, and guilds."""
    from src.world.infrastructure import Nation, Settlement

    # 1. Level 3: Nation offices and recognized guilds
    nat = Nation(
        id="nat_arcana",
        name="비전 제국",
        continent_id="c1",
        state_offices_and_titles=["대법관", "수석 궁정 연금술사", "황실 심문관"],
        recognized_guilds=["은빛 나침반 상인조합", "미스릴 대장장이 길드"]
    )
    nat_d = nat.to_dict()
    assert "수석 궁정 연금술사" in nat_d["state_offices_and_titles"]
    assert "은빛 나침반 상인조합" in nat_d["recognized_guilds"]
    loaded_nat = Nation.from_dict(nat_d)
    assert "황실 심문관" in loaded_nat.state_offices_and_titles

    # 2. Level 4: Settlement dark fantasy & occupations
    settle = Settlement(
        id="settle_grim",
        name="안개 낀 까마귀 늪지마을",
        nation_id="nat_arcana",
        region_id="reg_swamp",
        monster_infestation_index=65,
        local_curses_and_taboos=["안개 낀 밤 외출 금기", "피의 늪지대 익사자 전설"],
        cultist_infiltrations=["심연의 찬가 지하 집회"],
        underground_black_market=True,
        active_bounties=["늪지 와이번 토벌령", "밀수꾼 바란 생포"],
        common_occupations=["약초꾼", "뗏목 사공", "가죽 무두장이", "밀렵꾼"],
        active_guilds=["약초 채집가 조합", "비밀 암상인 카르텔"]
    )
    settle_d = settle.to_dict()
    assert settle_d["monster_infestation_index"] == 65
    assert "안개 낀 밤 외출 금기" in settle_d["local_curses_and_taboos"]
    assert "심연의 찬가 지하 집회" in settle_d["cultist_infiltrations"]
    assert settle_d["underground_black_market"] is True
    assert "늪지 와이번 토벌령" in settle_d["active_bounties"]
    assert "약초꾼" in settle_d["common_occupations"]
    assert "비밀 암상인 카르텔" in settle_d["active_guilds"]

    loaded_settle = Settlement.from_dict(settle_d)
    assert loaded_settle.monster_infestation_index == 65
    assert loaded_settle.underground_black_market is True
    assert len(loaded_settle.local_curses_and_taboos) == 2
    assert len(loaded_settle.common_occupations) == 4


def test_advanced_grand_simulation_mechanics():
    """Verify D&D planar rifts, EU4 trade nodes/power, CK3 succession laws/crises, Battle Brothers mercenaries/economic cycles, Total War corruptions."""
    from src.world.infrastructure import Region, Nation, Settlement

    # 1. Level 2: Region Planar & Trade Node
    reg = Region(
        id="reg_riftlands",
        name="차원 균열 협곡대",
        continent_id="c1",
        planar_instability=75,
        planar_rifts=["황천의 아스트랄 틈새", "화염 정령계 균열"],
        trade_node_name="동부 대륙 황금 대상로"
    )
    reg_d = reg.to_dict()
    assert reg_d["planar_instability"] == 75
    assert "황천의 아스트랄 틈새" in reg_d["planar_rifts"]
    assert reg_d["trade_node_name"] == "동부 대륙 황금 대상로"

    loaded_reg = Region.from_dict(reg_d)
    assert loaded_reg.planar_instability == 75
    assert len(loaded_reg.planar_rifts) == 2
    assert loaded_reg.trade_node_name == "동부 대륙 황금 대상로"

    # 2. Level 3: Nation Succession, Corruption, Mercenaries
    nat = Nation(
        id="nat_veridia",
        name="베리디아 왕국",
        continent_id="c1",
        succession_law="선거군주제",
        bureaucratic_corruption=35,
        active_mercenary_bands=["칠흑의 까마귀 용병단", "새벽의 방패단"]
    )
    nat_d = nat.to_dict()
    assert nat_d["succession_law"] == "선거군주제"
    assert nat_d["bureaucratic_corruption"] == 35
    assert "칠흑의 까마귀 용병단" in nat_d["active_mercenary_bands"]

    loaded_nat = Nation.from_dict(nat_d)
    assert loaded_nat.succession_law == "선거군주제"
    assert loaded_nat.bureaucratic_corruption == 35
    assert len(loaded_nat.active_mercenary_bands) == 2

    # 3. Level 4: Settlement Trade Power, Economic Cycles, Succession Crisis, Mercenaries, Supernatural Corruption
    settle = Settlement(
        id="settle_crossroads",
        name="교차로 교역 성채",
        nation_id="nat_veridia",
        region_id="reg_riftlands",
        trade_power=85,
        market_economic_trend="호황",
        succession_crisis=True,
        visiting_mercenaries=["외눈박이 한스 유랑단"],
        supernatural_corruption=40
    )
    settle_d = settle.to_dict()
    assert settle_d["trade_power"] == 85
    assert settle_d["market_economic_trend"] == "호황"
    assert settle_d["succession_crisis"] is True
    assert "외눈박이 한스 유랑단" in settle_d["visiting_mercenaries"]
    assert settle_d["supernatural_corruption"] == 40

    loaded_settle = Settlement.from_dict(settle_d)
    assert loaded_settle.trade_power == 85
    assert loaded_settle.market_economic_trend == "호황"
    assert loaded_settle.succession_crisis is True
    assert loaded_settle.visiting_mercenaries == ["외눈박이 한스 유랑단"]
    assert loaded_settle.supernatural_corruption == 40


def test_rpg_immersion_and_law_mechanics():
    """Verify archaeological sites, ideological climate, slavery/serfdom, bounty ledger, distrust, unrest, scandals, and fuel reserves."""
    from src.world.infrastructure import Region, Nation, Settlement

    # 1. Region
    reg = Region(
        id="reg_ancient",
        name="고대 문명 사막",
        continent_id="c1",
        archaeological_sites=["수정 피라미드 발굴터", "선대 마도학회 지하 묘지실"]
    )
    reg_d = reg.to_dict()
    assert "수정 피라미드 발굴터" in reg_d["archaeological_sites"]
    loaded_reg = Region.from_dict(reg_d)
    assert len(loaded_reg.archaeological_sites) == 2

    # 2. Nation
    nat = Nation(
        id="nat_holy",
        name="성스러운 태양 신정국",
        continent_id="c1",
        ideological_climate="신정 근본주의",
        serfdom_or_slavery_legal=True
    )
    nat_d = nat.to_dict()
    assert nat_d["ideological_climate"] == "신정 근본주의"
    assert nat_d["serfdom_or_slavery_legal"] is True
    loaded_nat = Nation.from_dict(nat_d)
    assert loaded_nat.ideological_climate == "신정 근본주의"
    assert loaded_nat.serfdom_or_slavery_legal is True

    # 3. Settlement
    settle = Settlement(
        id="settle_frostfall",
        name="설원 변경 요새마을",
        nation_id="nat_holy",
        region_id="reg_ancient",
        fuel_reserves_days=45,
        political_unrest=25,
        outsider_distrust=75,
        unfree_labor_ratio=0.15,
        bounty_ledger={"fugitive_karl": 300, "witch_elena": 1000},
        hidden_scandals=["영주의 뇌물 장부 은닉", "대사제의 이단 의식 밀회"]
    )
    settle_d = settle.to_dict()
    assert settle_d["fuel_reserves_days"] == 45
    assert settle_d["political_unrest"] == 25
    assert settle_d["outsider_distrust"] == 75
    assert settle_d["unfree_labor_ratio"] == 0.15
    assert settle_d["bounty_ledger"]["fugitive_karl"] == 300
    assert "영주의 뇌물 장부 은닉" in settle_d["hidden_scandals"]

    loaded_settle = Settlement.from_dict(settle_d)
    assert loaded_settle.fuel_reserves_days == 45
    assert loaded_settle.political_unrest == 25
    assert loaded_settle.outsider_distrust == 75
    assert loaded_settle.unfree_labor_ratio == 0.15
    assert loaded_settle.bounty_ledger["witch_elena"] == 1000
    assert len(loaded_settle.hidden_scandals) == 2


def test_tactical_survival_and_security_infiltration():
    """Verify Region toxicity, Nation conscription, Settlement siege/harbor/barrier/epidemics, Facility security/infiltration."""
    from src.world.infrastructure import Region, Nation, Settlement, Facility, FacilityCategory

    # 1. Level 2 Region: Toxicity
    reg = Region(
        id="reg_blight",
        name="부패와 낙진의 황무지",
        continent_id="c1",
        environmental_toxicity=85
    )
    reg_d = reg.to_dict()
    assert reg_d["environmental_toxicity"] == 85
    loaded_reg = Region.from_dict(reg_d)
    assert loaded_reg.environmental_toxicity == 85

    # 2. Level 3 Nation: Conscription Law
    nat = Nation(
        id="nat_militant",
        name="철혈 군국령",
        continent_id="c1",
        conscription_law="총동원령"
    )
    nat_d = nat.to_dict()
    assert nat_d["conscription_law"] == "총동원령"
    loaded_nat = Nation.from_dict(nat_d)
    assert loaded_nat.conscription_law == "총동원령"

    # 3. Level 4 Settlement: Siege, Harbor, Barrier, Local Toxicity Override, Epidemics, Quarantine
    # Case A: Sanctuary village in toxic region (purification barrier active, toxicity overridden to 0)
    settle_sanctuary = Settlement(
        id="settle_sanctuary",
        name="푸른 수정 성역 마을",
        nation_id="nat_militant",
        region_id="reg_blight",
        siege_supplies_days=180,
        harbor_tier=2,
        purification_barrier_tier=3,
        local_toxicity_override=0,
        active_epidemics=["흑사병"],
        quarantine_active=True
    )
    s_d = settle_sanctuary.to_dict()
    assert s_d["siege_supplies_days"] == 180
    assert s_d["harbor_tier"] == 2
    assert s_d["purification_barrier_tier"] == 3
    assert s_d["local_toxicity_override"] == 0
    assert "흑사병" in s_d["active_epidemics"]
    assert s_d["quarantine_active"] is True

    loaded_s = Settlement.from_dict(s_d)
    assert loaded_s.siege_supplies_days == 180
    assert loaded_s.harbor_tier == 2
    assert loaded_s.purification_barrier_tier == 3
    assert loaded_s.local_toxicity_override == 0
    assert loaded_s.active_epidemics == ["흑사병"]
    assert loaded_s.quarantine_active is True

    # Case B: Default settlement with None override
    settle_default = Settlement(id="settle_def", name="일반 마을", nation_id="nat_militant", region_id="reg_blight")
    assert settle_default.local_toxicity_override is None

    # 4. Level 5 Facility: Security Clearance, Infiltration, Interactive Props
    fac = Facility(
        id="fac_vault",
        name="영주성 지하 비밀 보물고",
        settlement_id="settle_sanctuary",
        category=FacilityCategory.CIVIC_COMMUNAL,
        security_clearance_tier=3,
        infiltration_points=["지하 하수도 배수구", "환기구 통로", "비밀 서고 회전문"],
        interactive_props=["샹들리에 도르래", "가연성 기름통", "경종 종루", "독가스 배출 밸브"]
    )
    fac_d = fac.to_dict()
    assert fac_d["security_clearance_tier"] == 3
    assert len(fac_d["infiltration_points"]) == 3
    assert "샹들리에 도르래" in fac_d["interactive_props"]

    loaded_fac = Facility.from_dict(fac_d)
    assert loaded_fac.security_clearance_tier == 3
    assert loaded_fac.infiltration_points == ["지하 하수도 배수구", "환기구 통로", "비밀 서고 회전문"]
    assert len(loaded_fac.interactive_props) == 4


def test_magic_density_syndicate_diplomacy_and_facility_atmosphere():
    """Verify mana density overrides, leylines, crime syndicates, grievances, visiting caravans, wars/truces, and facility atmosphere."""
    from src.world.infrastructure import Region, Nation, Settlement, Facility

    # 1. Level 2 Region: Mana density (0~100)
    reg = Region(
        id="reg_dead_magic",
        name="침묵의 회색 고원",
        continent_id="c1",
        mana_density=5
    )
    reg_d = reg.to_dict()
    assert reg_d["mana_density"] == 5
    loaded_reg = Region.from_dict(reg_d)
    assert loaded_reg.mana_density == 5

    # 2. Level 3 Nation: Active wars and Truce agreements
    nat = Nation(
        id="nat_solaria",
        name="솔라리아 제국",
        continent_id="c1",
        active_wars=["nat_ironforge"],
        truce_agreements={"nat_arcana": 180}
    )
    nat_d = nat.to_dict()
    assert nat_d["active_wars"] == ["nat_ironforge"]
    assert nat_d["truce_agreements"]["nat_arcana"] == 180
    loaded_nat = Nation.from_dict(nat_d)
    assert loaded_nat.active_wars == ["nat_ironforge"]
    assert loaded_nat.truce_agreements["nat_arcana"] == 180

    # 3. Level 4 Settlement: Mana density override, leylines, syndicates, grievances, caravans
    settle = Settlement(
        id="settle_nexus_haven",
        name="비전 지맥 오아시스",
        nation_id="nat_solaria",
        region_id="reg_dead_magic",
        leyline_nexus_tier=3,
        local_mana_density_override=85,
        ruling_crime_syndicate="검은 독사 카르텔",
        underworld_influence=75,
        historical_grievances=["5년 전 국왕군의 우물 독극물 방류", "상인 길드의 소금 독점"],
        visiting_caravans=["실버문 대상단", "비단길 대상연합"],
        caravan_frequency_days=7
    )
    s_d = settle.to_dict()
    assert s_d["leyline_nexus_tier"] == 3
    assert s_d["local_mana_density_override"] == 85
    assert s_d["ruling_crime_syndicate"] == "검은 독사 카르텔"
    assert s_d["underworld_influence"] == 75
    assert len(s_d["historical_grievances"]) == 2
    assert "실버문 대상단" in s_d["visiting_caravans"]
    assert s_d["caravan_frequency_days"] == 7

    loaded_s = Settlement.from_dict(s_d)
    assert loaded_s.leyline_nexus_tier == 3
    assert loaded_s.local_mana_density_override == 85
    assert loaded_s.ruling_crime_syndicate == "검은 독사 카르텔"
    assert loaded_s.underworld_influence == 75
    assert loaded_s.historical_grievances == ["5년 전 국왕군의 우물 독극물 방류", "상인 길드의 소금 독점"]
    assert len(loaded_s.visiting_caravans) == 2
    assert loaded_s.caravan_frequency_days == 7

    # 4. Level 5 Facility: Water supply, Ventilation, Noise, Lighting
    fac = Facility(
        id="fac_catacombs",
        name="지하 납골당 비밀 제단",
        settlement_id="settle_nexus_haven",
        water_supply_type="오염된침출수",
        ventilation_quality=5,
        noise_level=15,
        lighting=10
    )
    f_d = fac.to_dict()
    assert f_d["water_supply_type"] == "오염된침출수"
    assert f_d["ventilation_quality"] == 5
    assert f_d["noise_level"] == 15
    assert f_d["lighting"] == 10

    loaded_fac = Facility.from_dict(f_d)
    assert loaded_fac.water_supply_type == "오염된침출수"
    assert loaded_fac.ventilation_quality == 5
    assert loaded_fac.noise_level == 15
    assert loaded_fac.lighting == 10


def test_elevation_housing_flammability_and_espionage():
    """Verify Settlement elevation/housing/spies and Facility flammability/elevation."""
    from src.world.infrastructure import Settlement, Facility

    # 1. Level 4 Settlement: Elevation, Housing capacity, Spy networks
    settle = Settlement(
        id="settle_citadel_peak",
        name="천공 요새 성도",
        nation_id="nat_solaria",
        region_id="reg_dead_magic",
        elevation_meters=1450,
        population=12000,
        housing_capacity=15000,
        active_spy_networks=["제국 정보부 제3공작조", "검은 독사 첩보망"]
    )
    s_d = settle.to_dict()
    assert s_d["elevation_meters"] == 1450
    assert s_d["housing_capacity"] == 15000
    assert "제국 정보부 제3공작조" in s_d["active_spy_networks"]

    loaded_s = Settlement.from_dict(s_d)
    assert loaded_s.elevation_meters == 1450
    assert loaded_s.housing_capacity == 15000
    assert len(loaded_s.active_spy_networks) == 2

    # 2. Level 5 Facility: Flammability and Elevation level
    fac = Facility(
        id="fac_watchtower_rooftop",
        name="성채 중앙 대망루 꼭대기",
        settlement_id="settle_citadel_peak",
        flammability_rating=75,
        elevation_level=3
    )
    f_d = fac.to_dict()
    assert f_d["flammability_rating"] == 75
    assert f_d["elevation_level"] == 3

    loaded_fac = Facility.from_dict(f_d)
    assert loaded_fac.flammability_rating == 75
    assert loaded_fac.elevation_level == 3


def test_apex_predator_travel_army_insulation_alarm():
    """Verify apex_predator_id, travel_difficulty, standing_army_size, cold_insulation_rating, alarm_level."""
    from src.world.infrastructure import Region, Nation, Settlement, Facility

    # 1. Level 2 Region
    reg = Region(
        id="reg_crystal_dunes",
        name="수정 사막",
        continent_id="cont_aethel",
        apex_predator_id="boss_dune_leviathan",
        travel_difficulty=75,
        resource_regeneration_rate=30,
        nomadic_tribes=["푸른 두건 유목민", "모래 상인단"]
    )
    r_d = reg.to_dict()
    assert r_d["apex_predator_id"] == "boss_dune_leviathan"
    assert r_d["travel_difficulty"] == 75
    assert r_d["resource_regeneration_rate"] == 30
    assert "푸른 두건 유목민" in r_d["nomadic_tribes"]
    r_loaded = Region.from_dict(r_d)
    assert r_loaded.apex_predator_id == "boss_dune_leviathan"
    assert r_loaded.travel_difficulty == 75

    # 2. Level 3 Nation
    nat = Nation(
        id="nat_iron_empire",
        name="철혈 제국",
        continent_id="cont_aethel",
        tax_burden=65,
        standing_army_size=15000,
        border_openness=20
    )
    n_d = nat.to_dict()
    assert n_d["tax_burden"] == 65
    assert n_d["standing_army_size"] == 15000
    assert n_d["border_openness"] == 20
    n_loaded = Nation.from_dict(n_d)
    assert n_loaded.tax_burden == 65
    assert n_loaded.standing_army_size == 15000

    # 3. Level 4 Settlement
    st = Settlement(
        id="st_snowpeak",
        name="설봉 마을",
        nation_id="nat_iron_empire",
        region_id="reg_crystal_dunes",
        cold_insulation_rating=85,
        medical_capacity=30,
        rumor_circulation_rate=70
    )
    s_d = st.to_dict()
    assert s_d["cold_insulation_rating"] == 85
    assert s_d["medical_capacity"] == 30
    assert s_d["rumor_circulation_rate"] == 70
    s_loaded = Settlement.from_dict(s_d)
    assert s_loaded.cold_insulation_rating == 85
    assert s_loaded.medical_capacity == 30

    # 4. Level 5 Facility
    fac = Facility(
        id="fac_treasury_vault",
        name="영주성 지하 보물고",
        settlement_id="st_snowpeak",
        alarm_level=40,
        hidden_compartments=["벽난로 뒤 비밀금고", "해골 받침대 아래 비밀 격실"]
    )
    f_d = fac.to_dict()
    assert f_d["alarm_level"] == 40
    assert len(f_d["hidden_compartments"]) == 2
    f_loaded = Facility.from_dict(f_d)
    assert f_loaded.alarm_level == 40
    assert "벽난로 뒤 비밀금고" in f_loaded.hidden_compartments


def test_comprehensive_realism_and_social_infrastructure():
    """Verify newly added Level 0~5 deep realism and social problem infrastructure fields."""
    from src.world.state import WorldState
    from src.world.infrastructure import Continent, Region, Nation, Settlement, Facility

    # Level 0: WorldState
    ws = WorldState(
        magic_suppression_cycle=85,
        world_threat_level=60
    )
    ws_d = ws.to_dict()
    assert ws_d["magic_suppression_cycle"] == 85
    assert ws_d["world_threat_level"] == 60
    ws_loaded = WorldState.from_dict(ws_d)
    assert ws_loaded.magic_suppression_cycle == 85
    assert ws_loaded.world_threat_level == 60

    # Level 1: Continent
    cont = Continent(
        id="cont_euras",
        name="유라시아 판 대륙",
        continental_treaty="제1차 성역 불침 조약",
        dominant_trade_coalition="황금 삼각 상관 동맹"
    )
    c_d = cont.to_dict()
    assert c_d["continental_treaty"] == "제1차 성역 불침 조약"
    assert c_d["dominant_trade_coalition"] == "황금 삼각 상관 동맹"
    cont_loaded = Continent.from_dict(c_d)
    assert cont_loaded.continental_treaty == "제1차 성역 불침 조약"
    assert cont_loaded.dominant_trade_coalition == "황금 삼각 상관 동맹"

    # Level 2: Region
    reg = Region(
        id="reg_frozen_peaks",
        name="혹한의 칼날설산",
        continent_id="cont_euras",
        regional_champion_npc_id="npc_ice_swordmaster",
        seasonal_temperature_range=(-35, 12),
        foraging_abundance=25,
        wind_direction_degrees=270
    )
    r_d = reg.to_dict()
    assert r_d["regional_champion_npc_id"] == "npc_ice_swordmaster"
    assert tuple(r_d["seasonal_temperature_range"]) == (-35, 12)
    assert r_d["foraging_abundance"] == 25
    assert r_d["wind_direction_degrees"] == 270
    reg_loaded = Region.from_dict(r_d)
    assert reg_loaded.regional_champion_npc_id == "npc_ice_swordmaster"
    assert reg_loaded.seasonal_temperature_range == (-35, 12)
    assert reg_loaded.foraging_abundance == 25
    assert reg_loaded.wind_direction_degrees == 270

    # Level 3: Nation
    nat = Nation(
        id="nat_oceanic_kingdom",
        name="해양 군도 왕국",
        continent_id="cont_euras",
        naval_fleet_strength=120,
        legal_enforcement_efficiency=85,
        espionage_defense=75
    )
    n_d = nat.to_dict()
    assert n_d["naval_fleet_strength"] == 120
    assert n_d["legal_enforcement_efficiency"] == 85
    assert n_d["espionage_defense"] == 75
    nat_loaded = Nation.from_dict(n_d)
    assert nat_loaded.naval_fleet_strength == 120
    assert nat_loaded.legal_enforcement_efficiency == 85
    assert nat_loaded.espionage_defense == 75

    # Level 4: Settlement
    st = Settlement(
        id="st_slum_city",
        name="철광석 하류 빈민도시",
        nation_id="nat_oceanic_kingdom",
        region_id="reg_frozen_peaks",
        blacksmith_tier=2,
        magic_institution_tier=1,
        literacy_rate=15,
        slum_ratio=45,
        paved_road_ratio=30,
        superstition_index=80,
        unemployment_rate=35,
        orphan_vagrant_index=40,
        cartographic_accuracy=20
    )
    s_d = st.to_dict()
    assert s_d["blacksmith_tier"] == 2
    assert s_d["magic_institution_tier"] == 1
    assert s_d["literacy_rate"] == 15
    assert s_d["slum_ratio"] == 45
    assert s_d["paved_road_ratio"] == 30
    assert s_d["superstition_index"] == 80
    assert s_d["unemployment_rate"] == 35
    assert s_d["orphan_vagrant_index"] == 40
    assert s_d["cartographic_accuracy"] == 20
    st_loaded = Settlement.from_dict(s_d)
    assert st_loaded.blacksmith_tier == 2
    assert st_loaded.magic_institution_tier == 1
    assert st_loaded.literacy_rate == 15
    assert st_loaded.slum_ratio == 45
    assert st_loaded.unemployment_rate == 35

    # Level 5: Facility
    fac = Facility(
        id="fac_iron_cellar",
        name="무법지대 철갑 지하창고",
        settlement_id="st_slum_city",
        lock_difficulty=25,
        reinforcement_material="iron_reinforced",
        scent_intensity=70
    )
    f_d = fac.to_dict()
    assert f_d["lock_difficulty"] == 25
    assert f_d["reinforcement_material"] == "iron_reinforced"
    assert f_d["scent_intensity"] == 70
    fac_loaded = Facility.from_dict(f_d)
    assert fac_loaded.lock_difficulty == 25
    assert fac_loaded.reinforcement_material == "iron_reinforced"
    assert fac_loaded.scent_intensity == 70


def test_tactical_survival_curfew_trap_and_ward_infrastructure():
    """Verify surface, campsite, vassal loyalty, curfew, waste, graveyard, inn, traps, wards, patrol, soundproof."""
    from src.world.infrastructure import Region, Nation, Settlement, Facility

    # 1. Level 2 Region: Surface material & campsite viability
    reg = Region(
        id="reg_swamp_depths",
        name="독안개 늪지대",
        continent_id="cont_euras",
        dominant_surface="swamp_marsh",
        campsite_viability=15
    )
    r_d = reg.to_dict()
    assert r_d["dominant_surface"] == "swamp_marsh"
    assert r_d["campsite_viability"] == 15
    reg_loaded = Region.from_dict(r_d)
    assert reg_loaded.dominant_surface == "swamp_marsh"
    assert reg_loaded.campsite_viability == 15

    # 2. Level 3 Nation: Vassal loyalty
    nat = Nation(
        id="nat_feudal_duchy",
        name="분열된 공작령 연합",
        continent_id="cont_euras",
        vassal_loyalty_index=35
    )
    n_d = nat.to_dict()
    assert n_d["vassal_loyalty_index"] == 35
    nat_loaded = Nation.from_dict(n_d)
    assert nat_loaded.vassal_loyalty_index == 35

    # 3. Level 4 Settlement: Curfew, waste, graveyard, inn, entertainment, tax evasion
    st = Settlement(
        id="st_garrison_town",
        name="국경 요새 병영도시",
        nation_id="nat_feudal_duchy",
        region_id="reg_swamp_depths",
        curfew_hour=21,
        waste_management_tier=2,
        graveyard_capacity=250,
        inn_bed_capacity=40,
        entertainment_relief_rating=65,
        tax_evasion_rate=25
    )
    s_d = st.to_dict()
    assert s_d["curfew_hour"] == 21
    assert s_d["waste_management_tier"] == 2
    assert s_d["graveyard_capacity"] == 250
    assert s_d["inn_bed_capacity"] == 40
    assert s_d["entertainment_relief_rating"] == 65
    assert s_d["tax_evasion_rate"] == 25
    st_loaded = Settlement.from_dict(s_d)
    assert st_loaded.curfew_hour == 21
    assert st_loaded.waste_management_tier == 2
    assert st_loaded.graveyard_capacity == 250
    assert st_loaded.inn_bed_capacity == 40
    assert st_loaded.entertainment_relief_rating == 65
    assert st_loaded.tax_evasion_rate == 25

    # 4. Level 5 Facility: Traps, wards, soundproof, patrol, occupancy, emergency exits
    fac = Facility(
        id="fac_arcane_dungeon_vault",
        name="마탑 극비 비전 서고",
        settlement_id="st_garrison_town",
        trap_hazard_rating=85,
        magic_ward_tier=3,
        guard_patrol_interval_turns=2,
        soundproof_rating=90,
        occupancy_limit=8,
        emergency_exits=["비전 룬 텔레포트 게이트", "지하 수로 환기구"]
    )
    f_d = fac.to_dict()
    assert f_d["trap_hazard_rating"] == 85
    assert f_d["magic_ward_tier"] == 3
    assert f_d["guard_patrol_interval_turns"] == 2
    assert f_d["soundproof_rating"] == 90
    assert f_d["occupancy_limit"] == 8
    assert "비전 룬 텔레포트 게이트" in f_d["emergency_exits"]
    fac_loaded = Facility.from_dict(f_d)
    assert fac_loaded.trap_hazard_rating == 85
    assert fac_loaded.magic_ward_tier == 3
    assert fac_loaded.guard_patrol_interval_turns == 2
    assert fac_loaded.soundproof_rating == 90
    assert fac_loaded.occupancy_limit == 8
    assert len(fac_loaded.emergency_exits) == 2


def test_macro_pantheon_manpower_floor_and_haggling_infrastructure():
    """Verify pantheon, calendar, convergence, water, oxygen, manpower, embargoes, haggling, stealth floors."""
    from src.world.state import WorldState
    from src.world.infrastructure import Region, Nation, Settlement, Facility

    # 1. Level 0 WorldState
    ws = WorldState(
        planar_convergence_cycle=70,
        pantheon_deities=["태양신 솔라리스", "심연의 어머니"],
        days_per_month=28,
        months_per_year=13
    )
    ws_d = ws.to_dict()
    assert ws_d["planar_convergence_cycle"] == 70
    assert "태양신 솔라리스" in ws_d["pantheon_deities"]
    assert ws_d["days_per_month"] == 28
    assert ws_d["months_per_year"] == 13
    ws_loaded = WorldState.from_dict(ws_d)
    assert ws_loaded.planar_convergence_cycle == 70
    assert len(ws_loaded.pantheon_deities) == 2
    assert ws_loaded.days_per_month == 28

    # 2. Level 2 Region
    reg = Region(
        id="reg_alpine_crags",
        name="만년설 고산 단애",
        continent_id="cont_c1",
        water_source_reliability=40,
        natural_shelters=["풍식 절벽 틈새", "얼음 동굴"],
        predator_pack_density=60,
        air_pressure_oxygen=50,
        landslide_avalanche_risk=80
    )
    r_d = reg.to_dict()
    assert r_d["water_source_reliability"] == 40
    assert "얼음 동굴" in r_d["natural_shelters"]
    assert r_d["predator_pack_density"] == 60
    assert r_d["air_pressure_oxygen"] == 50
    assert r_d["landslide_avalanche_risk"] == 80
    r_loaded = Region.from_dict(r_d)
    assert r_loaded.water_source_reliability == 40
    assert r_loaded.air_pressure_oxygen == 50
    assert r_loaded.landslide_avalanche_risk == 80

    # 3. Level 3 Nation
    nat = Nation(
        id="nat_theocracy",
        name="성도 기사 교국",
        continent_id="cont_c1",
        foreign_debt_gold=50000,
        military_manpower_pool=80000,
        trade_embargoes=["nat_heretic_empire"],
        magic_prohibition_tier=3,
        casus_belli_ledger={"nat_heretic_empire": "이단 척결 성전"}
    )
    n_d = nat.to_dict()
    assert n_d["foreign_debt_gold"] == 50000
    assert n_d["military_manpower_pool"] == 80000
    assert "nat_heretic_empire" in n_d["trade_embargoes"]
    assert n_d["magic_prohibition_tier"] == 3
    assert n_d["casus_belli_ledger"]["nat_heretic_empire"] == "이단 척결 성전"
    n_loaded = Nation.from_dict(n_d)
    assert n_loaded.foreign_debt_gold == 50000
    assert n_loaded.magic_prohibition_tier == 3
    assert n_loaded.casus_belli_ledger["nat_heretic_empire"] == "이단 척결 성전"

    # 4. Level 4 Settlement
    st = Settlement(
        id="st_caravan_bazaar",
        name="사막 오아시스 바자르",
        nation_id="nat_theocracy",
        region_id="reg_alpine_crags",
        market_haggling_dc=18
    )
    s_d = st.to_dict()
    assert s_d["market_haggling_dc"] == 18
    s_loaded = Settlement.from_dict(s_d)
    assert s_loaded.market_haggling_dc == 18

    # 5. Level 5 Facility
    fac = Facility(
        id="fac_shadow_guild_hideout",
        name="도적 길드 지하 접견실",
        settlement_id="st_caravan_bazaar",
        floor_material="broken_glass",
        light_source_type="candle"
    )
    f_d = fac.to_dict()
    assert f_d["floor_material"] == "broken_glass"
    assert f_d["light_source_type"] == "candle"
    f_loaded = Facility.from_dict(f_d)
    assert f_loaded.floor_material == "broken_glass"
    assert f_loaded.light_source_type == "candle"


def test_facility_lifecycle_and_physical_slots_roundtrip():
    """Facility lifecycle, damage status, construction progress, and Settlement physical slots roundtrip."""
    # Ruined / Under-repair facility
    fac_ruin = Facility(
        id="fac_ruined_forge_01",
        name="무너진 고대 제철소",
        settlement_id="st_iron_city",
        facility_type=FacilityType.BLACKSMITH_FORGE,
        building_status=BuildingStatus.RUINED,
        construction_progress=35,
        repair_cost_materials={"wood": 50, "stone": 80, "iron": 20, "gold": 300},
        destruction_cause="화염 드래곤 브레스 공습",
        scaffolding_accessible=True
    )
    d_fac = fac_ruin.to_dict()
    assert d_fac["facility_type"] == "blacksmith_forge"
    assert d_fac["building_status"] == "ruined"
    assert d_fac["construction_progress"] == 35
    assert d_fac["repair_cost_materials"]["iron"] == 20
    assert d_fac["destruction_cause"] == "화염 드래곤 브레스 공습"
    assert d_fac["scaffolding_accessible"] is True

    fac_loaded = Facility.from_dict(d_fac)
    assert fac_loaded.facility_type == "blacksmith_forge"
    assert fac_loaded.building_status == "ruined"
    assert fac_loaded.construction_progress == 35
    assert fac_loaded.repair_cost_materials["stone"] == 80
    assert fac_loaded.destruction_cause == "화염 드래곤 브레스 공습"
    assert fac_loaded.scaffolding_accessible is True

    # Settlement physical slots
    st = Settlement(
        id="st_iron_city",
        name="철의 성채 대도시",
        nation_id="nat_iron",
        region_id="reg_crags",
        commercial_shops=["fac_store_01", "fac_apothecary_01"],
        training_facilities=["fac_knight_dojo", "fac_mage_academy"],
        active_peddlers=["peddler_potion_seller", "peddler_carpet_merchant"],
        guild_halls=["guild_mercenary_iron", "guild_merchants_league"],
        under_construction_facilities=["fac_watchtower_north"],
        ruined_facilities=["fac_ruined_forge_01"]
    )
    d_st = st.to_dict()
    assert "fac_store_01" in d_st["commercial_shops"]
    assert "fac_mage_academy" in d_st["training_facilities"]
    assert "peddler_potion_seller" in d_st["active_peddlers"]
    assert "guild_mercenary_iron" in d_st["guild_halls"]
    assert "fac_watchtower_north" in d_st["under_construction_facilities"]
    assert "fac_ruined_forge_01" in d_st["ruined_facilities"]

    st_loaded = Settlement.from_dict(d_st)
    assert st_loaded.commercial_shops == ["fac_store_01", "fac_apothecary_01"]
    assert st_loaded.training_facilities == ["fac_knight_dojo", "fac_mage_academy"]
    assert st_loaded.active_peddlers == ["peddler_potion_seller", "peddler_carpet_merchant"]
    assert st_loaded.guild_halls == ["guild_mercenary_iron", "guild_merchants_league"]
    assert st_loaded.under_construction_facilities == ["fac_watchtower_north"]
    assert st_loaded.ruined_facilities == ["fac_ruined_forge_01"]


def test_settlement_and_facility_physical_infrastructure_roundtrip():
    """Settlement town square, gates, moats, watermills, and Facility windows, chimney, cellar roundtrip."""
    # 1. Settlement Physical Infrastructure
    st = Settlement(
        id="st_granary_haven",
        name="곡창의 안식처 요새마을",
        nation_id="nat_solis",
        region_id="reg_plains",
        town_square_features=["단두대", "공고판", "시계탑", "분수대"],
        gate_type="portcullis",
        moat_type="water_moat",
        stable_and_cart_capacity=30,
        watermills_count=4,
        windmills_count=6,
        firefighting_cistern_rating=85,
        quarantine_camp_active=True,
        sewer_network_scale=3,
        pasture_area_hectares=120.5
    )
    d_st = st.to_dict()
    assert d_st["town_square_features"] == ["단두대", "공고판", "시계탑", "분수대"]
    assert d_st["gate_type"] == "portcullis"
    assert d_st["moat_type"] == "water_moat"
    assert d_st["stable_and_cart_capacity"] == 30
    assert d_st["watermills_count"] == 4
    assert d_st["windmills_count"] == 6
    assert d_st["firefighting_cistern_rating"] == 85
    assert d_st["quarantine_camp_active"] is True
    assert d_st["sewer_network_scale"] == 3
    assert d_st["pasture_area_hectares"] == 120.5

    st_loaded = Settlement.from_dict(d_st)
    assert st_loaded.town_square_features == ["단두대", "공고판", "시계탑", "분수대"]
    assert st_loaded.gate_type == "portcullis"
    assert st_loaded.moat_type == "water_moat"
    assert st_loaded.stable_and_cart_capacity == 30
    assert st_loaded.watermills_count == 4
    assert st_loaded.windmills_count == 6
    assert st_loaded.firefighting_cistern_rating == 85
    assert st_loaded.quarantine_camp_active is True
    assert st_loaded.sewer_network_scale == 3
    assert st_loaded.pasture_area_hectares == 120.5

    # 2. Facility Physical Tactical Features
    fac = Facility(
        id="fac_manor_cellar",
        name="영주 저택 지하 비밀 보고",
        settlement_id="st_granary_haven",
        window_security_type="iron_bars",
        chimney_hearth_size="crawlable",
        roof_material_type="slate_tile",
        cover_density=80,
        secret_door_mechanism="book_lever",
        cellar_type="secret_dungeon",
        guard_beast_type="watchdog"
    )
    d_fac = fac.to_dict()
    assert d_fac["window_security_type"] == "iron_bars"
    assert d_fac["chimney_hearth_size"] == "crawlable"
    assert d_fac["roof_material_type"] == "slate_tile"
    assert d_fac["cover_density"] == 80
    assert d_fac["secret_door_mechanism"] == "book_lever"
    assert d_fac["cellar_type"] == "secret_dungeon"
    assert d_fac["guard_beast_type"] == "watchdog"

    fac_loaded = Facility.from_dict(d_fac)
    assert fac_loaded.window_security_type == "iron_bars"
    assert fac_loaded.chimney_hearth_size == "crawlable"
    assert fac_loaded.roof_material_type == "slate_tile"
    assert fac_loaded.cover_density == 80
    assert fac_loaded.secret_door_mechanism == "book_lever"
    assert fac_loaded.cellar_type == "secret_dungeon"
    assert fac_loaded.guard_beast_type == "watchdog"


def test_physical_tactical_infrastructure_roundtrip_all_tiers_and_level_0_crisis():
    """Verify physical elements across L1-L5 and Level 0 global crisis threat fields."""
    from src.world.state import WorldState

    # Level 1: Continent
    cont = Continent(
        id="cont_aethelgard",
        name="에델가르드 대륙",
        dominant_tycoon_npc_id="npc_merchant_mogul_roth",
        continental_chokepoints=["대협곡 철벽 관문", "아주르 해협"],
        tectonic_instability_rating=45,
        continental_forbidden_zones=["신벌의 낙진 대균열"]
    )
    d_cont = cont.to_dict()
    assert d_cont["dominant_tycoon_npc_id"] == "npc_merchant_mogul_roth"
    assert d_cont["continental_chokepoints"] == ["대협곡 철벽 관문", "아주르 해협"]
    assert d_cont["tectonic_instability_rating"] == 45
    assert d_cont["continental_forbidden_zones"] == ["신벌의 낙진 대균열"]
    cont_loaded = Continent.from_dict(d_cont)
    assert cont_loaded.dominant_tycoon_npc_id == "npc_merchant_mogul_roth"
    assert cont_loaded.continental_chokepoints == ["대협곡 철벽 관문", "아주르 해협"]
    assert cont_loaded.tectonic_instability_rating == 45
    assert cont_loaded.continental_forbidden_zones == ["신벌의 낙진 대균열"]

    # Level 2: Region
    reg = Region(
        id="reg_flame_wilds",
        name="홍염의 황야",
        continent_id="cont_aethelgard",
        wildfire_hazard_rating=75,
        foliage_density=80,
        river_crossing_dc=16
    )
    d_reg = reg.to_dict()
    assert d_reg["wildfire_hazard_rating"] == 75
    assert d_reg["foliage_density"] == 80
    assert d_reg["river_crossing_dc"] == 16
    reg_loaded = Region.from_dict(d_reg)
    assert reg_loaded.wildfire_hazard_rating == 75
    assert reg_loaded.foliage_density == 80
    assert reg_loaded.river_crossing_dc == 16

    # Level 3: Nation
    nation = Nation(
        id="nation_valoria",
        name="발로리아 성왕국",
        continent_id="cont_aethelgard",
        national_merchant_leader_id="npc_chancellor_mayer",
        border_barrier_type="great_stone_wall",
        beacon_network_speed_hours=4,
        coin_minting_purity=92
    )
    d_nation = nation.to_dict()
    assert d_nation["national_merchant_leader_id"] == "npc_chancellor_mayer"
    assert d_nation["border_barrier_type"] == "great_stone_wall"
    assert d_nation["beacon_network_speed_hours"] == 4
    assert d_nation["coin_minting_purity"] == 92
    nation_loaded = Nation.from_dict(d_nation)
    assert nation_loaded.national_merchant_leader_id == "npc_chancellor_mayer"
    assert nation_loaded.border_barrier_type == "great_stone_wall"
    assert nation_loaded.beacon_network_speed_hours == 4
    assert nation_loaded.coin_minting_purity == 92

    # Level 4: Settlement
    settle = Settlement(
        id="settle_iron_bastion",
        name="철벽 보루 성채",
        nation_id="nation_valoria",
        region_id="reg_flame_wilds",
        street_lighting_type="magic_crystals",
        battlement_type="machicolations",
        militia_armory_capacity=150
    )
    d_settle = settle.to_dict()
    assert d_settle["street_lighting_type"] == "magic_crystals"
    assert d_settle["battlement_type"] == "machicolations"
    assert d_settle["militia_armory_capacity"] == 150
    settle_loaded = Settlement.from_dict(d_settle)
    assert settle_loaded.street_lighting_type == "magic_crystals"
    assert settle_loaded.battlement_type == "machicolations"
    assert settle_loaded.militia_armory_capacity == 150

    # Level 5: Facility
    fac = Facility(
        id="fac_dungeon_treasury",
        name="지하 미궁 비밀 보관소",
        settlement_id="settle_iron_bastion",
        vent_duct_size="crawlable_human",
        floor_water_depth_cm=15,
        key_holder_npc_id="npc_jailer_garrick"
    )
    d_fac = fac.to_dict()
    assert d_fac["vent_duct_size"] == "crawlable_human"
    assert d_fac["floor_water_depth_cm"] == 15
    assert d_fac["key_holder_npc_id"] == "npc_jailer_garrick"
    fac_loaded = Facility.from_dict(d_fac)
    assert fac_loaded.vent_duct_size == "crawlable_human"
    assert fac_loaded.floor_water_depth_cm == 15
    assert fac_loaded.key_holder_npc_id == "npc_jailer_garrick"

    # Level 0: WorldState Global Crisis & Existential Threat
    ws = WorldState(
        world_threat_level=85,
        global_apocalyptic_threat="심연 군주 바알의 대침공",
        world_crisis_active_stage=4,
        global_nemesis_npc_id="npc_archdemon_baal",
        global_sanctuary_region_id="reg_last_bastion_sanctuary",
        grand_crusade_coalition=["nation_valoria", "nation_ironforge", "holy_templar_order"]
    )
    d_ws = ws.to_dict()
    assert d_ws["global_apocalyptic_threat"] == "심연 군주 바알의 대침공"
    assert d_ws["world_crisis_active_stage"] == 4
    assert d_ws["global_nemesis_npc_id"] == "npc_archdemon_baal"
    assert d_ws["global_sanctuary_region_id"] == "reg_last_bastion_sanctuary"
    assert d_ws["grand_crusade_coalition"] == ["nation_valoria", "nation_ironforge", "holy_templar_order"]

    ws_loaded = WorldState.from_dict(d_ws)
    assert ws_loaded.world_threat_level == 85
    assert ws_loaded.global_apocalyptic_threat == "심연 군주 바알의 대침공"
    assert ws_loaded.world_crisis_active_stage == 4
    assert ws_loaded.global_nemesis_npc_id == "npc_archdemon_baal"
    assert ws_loaded.global_sanctuary_region_id == "reg_last_bastion_sanctuary"
    assert ws_loaded.grand_crusade_coalition == ["nation_valoria", "nation_ironforge", "holy_templar_order"]


def test_realism_combat_memory_tier_fields_roundtrip():
    """Verify newly added combat, memory, and realism fields across tiers 0 to 5."""
    from src.world.state import WorldState

    # Level 0 WorldState
    ws = WorldState(
        universal_gravity_scale=1.2,
        memory_decay_turn_interval=60
    )
    d_ws = ws.to_dict()
    assert d_ws["universal_gravity_scale"] == 1.2
    assert d_ws["memory_decay_turn_interval"] == 60
    ws_loaded = WorldState.from_dict(d_ws)
    assert ws_loaded.universal_gravity_scale == 1.2
    assert ws_loaded.memory_decay_turn_interval == 60

    # Level 1 Continent
    cont = Continent(
        id="cont_north",
        name="북부 혹한 대륙",
        standard_physique_archetype="dwarven_broad"
    )
    d_cont = cont.to_dict()
    assert d_cont["standard_physique_archetype"] == "dwarven_broad"
    cont_loaded = Continent.from_dict(d_cont)
    assert cont_loaded.standard_physique_archetype == "dwarven_broad"

    # Level 2 Region
    reg = Region(
        id="reg_forest",
        name="안개 숲",
        continent_id="cont_north",
        campfire_detection_risk=55,
        watch_shift_visibility_bonus=-20
    )
    d_reg = reg.to_dict()
    assert d_reg["campfire_detection_risk"] == 55
    assert d_reg["watch_shift_visibility_bonus"] == -20
    reg_loaded = Region.from_dict(d_reg)
    assert reg_loaded.campfire_detection_risk == 55
    assert reg_loaded.watch_shift_visibility_bonus == -20

    # Level 3 Nation
    nation = Nation(
        id="nation_iron",
        name="철의 제국",
        continent_id="cont_north",
        ammunition_strategic_control=True,
        refitting_guild_tax_rate=0.12
    )
    d_nation = nation.to_dict()
    assert d_nation["ammunition_strategic_control"] is True
    assert d_nation["refitting_guild_tax_rate"] == 0.12
    nation_loaded = Nation.from_dict(d_nation)
    assert nation_loaded.ammunition_strategic_control is True
    assert nation_loaded.refitting_guild_tax_rate == 0.12

    # Level 4 Settlement
    settle = Settlement(
        id="settle_garrison",
        name="국경 주둔지",
        nation_id="nation_iron",
        region_id="reg_forest",
        fletching_and_ammo_supply_tier=2,
        armor_refitting_forge_tier=3,
        pack_animal_rental_available=True,
        disguise_inspection_strictness=75
    )
    d_settle = settle.to_dict()
    assert d_settle["fletching_and_ammo_supply_tier"] == 2
    assert d_settle["armor_refitting_forge_tier"] == 3
    assert d_settle["pack_animal_rental_available"] is True
    assert d_settle["disguise_inspection_strictness"] == 75
    settle_loaded = Settlement.from_dict(d_settle)
    assert settle_loaded.fletching_and_ammo_supply_tier == 2
    assert settle_loaded.armor_refitting_forge_tier == 3
    assert settle_loaded.pack_animal_rental_available is True
    assert settle_loaded.disguise_inspection_strictness == 75

    # Level 5 Facility
    fac = Facility(
        id="fac_narrow_corridor",
        name="비밀 감옥 지하 회랑",
        settlement_id="settle_garrison",
        ceiling_height_meters=2.1,
        hallway_width_meters=1.2,
        cover_poise_durability=80
    )
    d_fac = fac.to_dict()
    assert d_fac["ceiling_height_meters"] == 2.1
    assert d_fac["hallway_width_meters"] == 1.2
    assert d_fac["cover_poise_durability"] == 80
    fac_loaded = Facility.from_dict(d_fac)
    assert fac_loaded.ceiling_height_meters == 2.1
    assert fac_loaded.hallway_width_meters == 1.2
    assert fac_loaded.cover_poise_durability == 80


def test_cascading_rare_mineral_and_natural_resources_resolution():
    """Verify 4-tier natural resources and rare mineral resolution from Settlement up to Continent."""
    reg = InfrastructureRegistry()

    # 1. Level 1 Continent with endemic continental resources
    cont = Continent(
        id="cont_aethel",
        name="에델가르드 대륙",
        endemic_continental_resources=["미스릴 원석", "고대 세계수 수액"]
    )
    reg.register_continent(cont)

    # 2. Level 2 Region with rare minerals and endemic biology
    region = Region(
        id="reg_volcano",
        name="흑요석 화산 분화구",
        continent_id="cont_aethel",
        strategic_deposits=["천연 초석 동굴"],
        rare_mineral_deposits=["칠흑 오리하르콘 광맥", "천연 고순도 유황"],
        endemic_biological_resources=["화염 도마뱀 기름"]
    )
    reg.register_region(region)

    # 3. Level 3 Nation with monopoly strategic resources & concessions
    nation = Nation(
        id="nation_forge",
        name="화염 대장간 왕국",
        continent_id="cont_aethel",
        monopoly_strategic_resources=["왕실 비전 고농축 마력석"],
        national_mining_concessions={"흑오리하르콘 1광구": "guild_blacksmith_royal"}
    )
    reg.register_nation(nation)

    # 4. Level 4 Settlement with local physical resource nodes
    settlement = Settlement(
        id="settle_mining_camp",
        name="검은 마그마 광산촌",
        nation_id="nation_forge",
        region_id="reg_volcano",
        local_resource_nodes=["제3 심층 갱도", "용암류 흑요석 채석장"],
        resource_depletion_risk=35
    )
    reg.register_settlement(settlement)

    # Verify dict roundtrip
    assert Continent.from_dict(cont.to_dict()).endemic_continental_resources == ["미스릴 원석", "고대 세계수 수액"]
    assert Region.from_dict(region.to_dict()).rare_mineral_deposits == ["칠흑 오리하르콘 광맥", "천연 고순도 유황"]
    assert Region.from_dict(region.to_dict()).endemic_biological_resources == ["화염 도마뱀 기름"]
    assert Nation.from_dict(nation.to_dict()).monopoly_strategic_resources == ["왕실 비전 고농축 마력석"]
    assert Settlement.from_dict(settlement.to_dict()).local_resource_nodes == ["제3 심층 갱도", "용암류 흑요석 채석장"]
    assert Settlement.from_dict(settlement.to_dict()).resource_depletion_risk == 35

    # 5. Cascading 4-Tier Resource Portfolio Resolution
    portfolio = reg.resolve_natural_resources("settle_mining_camp")
    assert portfolio["local_nodes"] == ["제3 심층 갱도", "용암류 흑요석 채석장"]
    assert portfolio["national_monopolies"] == ["왕실 비전 고농축 마력석"]
    assert portfolio["regional_minerals"] == ["칠흑 오리하르콘 광맥", "천연 고순도 유황"]
    assert portfolio["regional_biologicals"] == ["화염 도마뱀 기름"]
    assert portfolio["regional_strategic_deposits"] == ["천연 초석 동굴"]
    assert portfolio["continental_endemic"] == ["미스릴 원석", "고대 세계수 수액"]

    expected_all = [
        "제3 심층 갱도", "용암류 흑요석 채석장",
        "왕실 비전 고농축 마력석",
        "칠흑 오리하르콘 광맥", "천연 고순도 유황",
        "화염 도마뱀 기름",
        "천연 초석 동굴",
        "미스릴 원석", "고대 세계수 수액"
    ]
    assert portfolio["all_rare_resources"] == expected_all
    assert portfolio["settlement_name"] == "검은 마그마 광산촌"
    assert portfolio["nation_name"] == "화염 대장간 왕국"
    assert portfolio["region_name"] == "흑요석 화산 분화구"
    assert portfolio["continent_name"] == "에델가르드 대륙"


def test_high_fantasy_worldbuilding_tier_fields_roundtrip():
    """Verify high-fantasy fields across tiers 0 to 5."""
    from src.world.state import WorldState

    # Level 0 WorldState: cosmic alignment & world soul
    ws = WorldState(
        cosmic_alignment_element="fire",
        world_soul_awakening_ratio=35
    )
    d_ws = ws.to_dict()
    assert d_ws["cosmic_alignment_element"] == "fire"
    assert d_ws["world_soul_awakening_ratio"] == 35
    ws_loaded = WorldState.from_dict(d_ws)
    assert ws_loaded.cosmic_alignment_element == "fire"
    assert ws_loaded.world_soul_awakening_ratio == 35

    # Level 1 Continent: titan remains & leylines
    cont = Continent(
        id="cont_titan",
        name="거신의 대륙",
        ancient_titan_remains=["거신 이미르의 늑골 산맥"],
        leyline_network_scale="wild_surge"
    )
    d_cont = cont.to_dict()
    assert d_cont["ancient_titan_remains"] == ["거신 이미르의 늑골 산맥"]
    assert d_cont["leyline_network_scale"] == "wild_surge"
    cont_loaded = Continent.from_dict(d_cont)
    assert cont_loaded.ancient_titan_remains == ["거신 이미르의 늑골 산맥"]
    assert cont_loaded.leyline_network_scale == "wild_surge"

    # Level 2 Region: draconic presence, elemental affinity, monster stampede
    reg = Region(
        id="reg_dragon_peaks",
        name="용의 둥지 봉우리",
        continent_id="cont_titan",
        draconic_presence_level=2,
        dominant_elemental_affinity="fire",
        monster_stampede_risk=45
    )
    d_reg = reg.to_dict()
    assert d_reg["draconic_presence_level"] == 2
    assert d_reg["dominant_elemental_affinity"] == "fire"
    assert d_reg["monster_stampede_risk"] == 45
    reg_loaded = Region.from_dict(d_reg)
    assert reg_loaded.draconic_presence_level == 2
    assert reg_loaded.dominant_elemental_affinity == "fire"
    assert reg_loaded.monster_stampede_risk == 45

    # Level 3 Nation: court mages, patron boon, airships
    nation = Nation(
        id="nation_arcania",
        name="아르카니아 비공정 제국",
        continent_id="cont_titan",
        court_mage_circle_strength=85,
        national_patron_deity_boon="솔라리스의 태양 방벽",
        airship_dock_count=12
    )
    d_nation = nation.to_dict()
    assert d_nation["court_mage_circle_strength"] == 85
    assert d_nation["national_patron_deity_boon"] == "솔라리스의 태양 방벽"
    assert d_nation["airship_dock_count"] == 12
    nation_loaded = Nation.from_dict(d_nation)
    assert nation_loaded.court_mage_circle_strength == 85
    assert nation_loaded.national_patron_deity_boon == "솔라리스의 태양 방벽"
    assert nation_loaded.airship_dock_count == 12

    # Level 4 Settlement: magical barrier, aerial mount dock, waystone, undead haunting
    settle = Settlement(
        id="settle_skyport",
        name="천공의 성채",
        nation_id="nation_arcania",
        region_id="reg_dragon_peaks",
        magical_barrier_active=True,
        aerial_mount_dock_tier=3,
        teleportation_waystone_active=True,
        undead_haunting_index=20
    )
    d_settle = settle.to_dict()
    assert d_settle["magical_barrier_active"] is True
    assert d_settle["aerial_mount_dock_tier"] == 3
    assert d_settle["teleportation_waystone_active"] is True
    assert d_settle["undead_haunting_index"] == 20
    settle_loaded = Settlement.from_dict(d_settle)
    assert settle_loaded.magical_barrier_active is True
    assert settle_loaded.aerial_mount_dock_tier == 3
    assert settle_loaded.teleportation_waystone_active is True
    assert settle_loaded.undead_haunting_index == 20

    # Level 5 Facility: dungeon depth, core element, sanctification
    fac = Facility(
        id="fac_abyss_dungeon",
        name="심연의 대미궁 입구",
        settlement_id="settle_skyport",
        dungeon_max_depth_floors=25,
        dungeon_core_element="abyss",
        sanctification_rating=10
    )
    d_fac = fac.to_dict()
    assert d_fac["dungeon_max_depth_floors"] == 25
    assert d_fac["dungeon_core_element"] == "abyss"
    assert d_fac["sanctification_rating"] == 10
    fac_loaded = Facility.from_dict(d_fac)
    assert fac_loaded.dungeon_max_depth_floors == 25
    assert fac_loaded.dungeon_core_element == "abyss"
    assert fac_loaded.sanctification_rating == 10


def test_nation_detailed_military_forces_option_c():
    """Verify Option C: structured military branches and custom special units in Nation."""
    # 1. Default values
    nat_default = Nation(id="nat_default", name="기본 왕국", continent_id="c1")
    assert nat_default.standing_army_size == 1000
    assert nat_default.knights_count == 100
    assert nat_default.infantry_count == 600
    assert nat_default.ranged_corps_count == 200
    assert nat_default.cavalry_count == 100
    assert nat_default.siege_engine_count == 10
    assert nat_default.beast_riders_count == 0
    assert nat_default.special_military_units == {}
    assert nat_default.calculate_total_military_power() == 1000

    # 2. Custom military composition (Knights, Infantry, Musketeers, Special Units)
    nat_custom = Nation(
        id="nat_musketeer_kingdom",
        name="발렌시아 화약 왕국",
        continent_id="cont_europa",
        civilization_level="르네상스 초기 화약 문명",
        standing_army_size=1500,
        knights_count=200,
        infantry_count=800,
        ranged_corps_count=400,
        cavalry_count=150,
        siege_engine_count=25,
        beast_riders_count=10,
        special_military_units={
            "왕실 머스킷 총사대": 100,
            "그리폰 공습대": 30,
            "국왕 친위 기사단": 50
        }
    )
    # Sum of ground: 200 + 800 + 400 + 150 + (100 + 30 + 50 = 180) = 1730
    assert nat_custom.calculate_total_military_power() == 1730

    # 3. Serialization (to_dict / from_dict)
    d = nat_custom.to_dict()
    assert d["knights_count"] == 200
    assert d["infantry_count"] == 800
    assert d["ranged_corps_count"] == 400
    assert d["cavalry_count"] == 150
    assert d["siege_engine_count"] == 25
    assert d["beast_riders_count"] == 10
    assert d["special_military_units"] == {
        "왕실 머스킷 총사대": 100,
        "그리폰 공습대": 30,
        "국왕 친위 기사단": 50
    }

    loaded = Nation.from_dict(d)
    assert loaded.knights_count == 200
    assert loaded.infantry_count == 800
    assert loaded.ranged_corps_count == 400
    assert loaded.cavalry_count == 150
    assert loaded.siege_engine_count == 25
    assert loaded.beast_riders_count == 10
    assert loaded.special_military_units["왕실 머스킷 총사대"] == 100
    assert loaded.calculate_total_military_power() == 1730


def test_all_infrastructure_tiers_traits_field():
    """Verify traits field across Continent, Region, Nation, Settlement, and Facility."""
    # 1. Continent traits
    cont = Continent(id="c1", name="신대륙", traits=["가이아의 각성", "마나 과포화", "신비로운 미개척지"])
    assert cont.traits == ["가이아의 각성", "마나 과포화", "신비로운 미개척지"]
    d_cont = cont.to_dict()
    assert d_cont["traits"] == ["가이아의 각성", "마나 과포화", "신비로운 미개척지"]
    loaded_cont = Continent.from_dict(d_cont)
    assert loaded_cont.traits == ["가이아의 각성", "마나 과포화", "신비로운 미개척지"]

    # 2. Region traits
    reg = Region(id="r1", name="망각의 설원", continent_id="c1", traits=["혹한의 불모지", "용의 영지", "영구 동토"])
    assert reg.traits == ["혹한의 불모지", "용의 영지", "영구 동토"]
    d_reg = reg.to_dict()
    assert d_reg["traits"] == ["혹한의 불모지", "용의 영지", "영구 동토"]
    loaded_reg = Region.from_dict(d_reg)
    assert loaded_reg.traits == ["혹한의 불모지", "용의 영지", "영구 동토"]

    # 3. Nation traits
    nat = Nation(id="n1", name="루멘 성왕국", continent_id="c1", traits=["호전적 군국주의", "성기사의 성지", "마녀사냥 중"])
    assert nat.traits == ["호전적 군국주의", "성기사의 성지", "마녀사냥 중"]
    d_nat = nat.to_dict()
    assert d_nat["traits"] == ["호전적 군국주의", "성기사의 성지", "마녀사냥 중"]
    loaded_nat = Nation.from_dict(d_nat)
    assert loaded_nat.traits == ["호전적 군국주의", "성기사의 성지", "마녀사냥 중"]

    # 4. Settlement traits
    setl = Settlement(id="s1", name="해골 골짜기 마을", nation_id="n1", region_id="r1", traits=["무법천지", "대기근", "언데드 소굴"])
    assert setl.traits == ["무법천지", "대기근", "언데드 소굴"]
    d_setl = setl.to_dict()
    assert d_setl["traits"] == ["무법천지", "대기근", "언데드 소굴"]
    loaded_setl = Settlement.from_dict(d_setl)
    assert loaded_setl.traits == ["무법천지", "대기근", "언데드 소굴"]

    # 5. Facility traits
    fac = Facility(id="f1", name="쥐구멍 지하실", settlement_id="s1", traits=["쥐떼 소굴", "밀수꾼 은신처"])
    assert fac.traits == ["쥐떼 소굴", "밀수꾼 은신처"]
    d_fac = fac.to_dict()
    assert d_fac["traits"] == ["쥐떼 소굴", "밀수꾼 은신처"]
    loaded_fac = Facility.from_dict(d_fac)
    assert loaded_fac.traits == ["쥐떼 소굴", "밀수꾼 은신처"]


def test_additional_entities_traits_field():
    """Verify traits field on WorldState, InterTierRoute, TransitVehicle, RoadConnection, Faction, Location."""
    from src.world.state import WorldState, Faction, Location
    from src.world.infrastructure import InterTierRoute, TransitVehicle
    from src.world.geography import RoadConnection

    # 1. WorldState (Level 0)
    ws = WorldState()
    ws.world_traits = ["신들의 침묵", "마나 과포화", "종말 카운트다운"]
    assert ws.traits == ["신들의 침묵", "마나 과포화", "종말 카운트다운"]
    d_ws = ws.to_dict()
    assert d_ws["world_traits"] == ["신들의 침묵", "마나 과포화", "종말 카운트다운"]
    loaded_ws = WorldState.from_dict(d_ws)
    assert loaded_ws.world_traits == ["신들의 침묵", "마나 과포화", "종말 카운트다운"]
    assert loaded_ws.traits == ["신들의 침묵", "마나 과포화", "종말 카운트다운"]

    # 2. InterTierRoute
    route = InterTierRoute(
        origin_id="reg_1",
        destination_id="reg_2",
        route_name="고산 지름길",
        traits=["도적 출몰 가도", "폭설 차단 위험", "초국가 직통"]
    )
    assert route.traits == ["도적 출몰 가도", "폭설 차단 위험", "초국가 직통"]
    d_route = route.to_dict()
    assert d_route["traits"] == ["도적 출몰 가도", "폭설 차단 위험", "초국가 직통"]
    loaded_route = InterTierRoute.from_dict(d_route)
    assert loaded_route.traits == ["도적 출몰 가도", "폭설 차단 위험", "초국가 직통"]

    # 3. TransitVehicle
    veh = TransitVehicle(
        id="veh_airship_01",
        name="비전 부유선",
        traits=["마도 부유", "장갑 보강", "고속 비행"]
    )
    assert veh.traits == ["마도 부유", "장갑 보강", "고속 비행"]
    d_veh = veh.to_dict()
    assert d_veh["traits"] == ["마도 부유", "장갑 보강", "고속 비행"]
    loaded_veh = TransitVehicle.from_dict(d_veh)
    assert loaded_veh.traits == ["마도 부유", "장갑 보강", "고속 비행"]

    # 4. RoadConnection
    road = RoadConnection(
        destination_id="town_b",
        traits=["진흙탕길", "야간 기습 빈발"]
    )
    assert road.traits == ["진흙탕길", "야간 기습 빈발"]

    # 5. Faction
    fac = Faction(
        id="fac_shadow_syndicate",
        name="그림자 상단",
        traits=["비밀주의", "암시장 독점", "냉혹함"]
    )
    assert fac.traits == ["비밀주의", "암시장 독점", "냉혹함"]

    # 6. Location
    loc = Location(
        id="loc_crypt_01",
        name="지하 납골당",
        description="어두운 납골당",
        exits={},
        traits=["칠흑 어둠", "피비린내", "언데드 출몰"]
    )
    assert loc.traits == ["칠흑 어둠", "피비린내", "언데드 출몰"]


# =====================================================================
# Level 0 ~ 2 Template Loader & Hierarchy Pipeline Tests
# =====================================================================
def test_continent_templates_json_integrity():
    """Verify continent_templates.json has 120 complete templates with all rich fields including apex champion and monster."""
    import json
    from src.core.config import TEMPLATES_DIR

    target_file = TEMPLATES_DIR / "continent_templates.json"
    assert target_file.exists(), f"continent_templates.json does not exist at {target_file}"

    with open(target_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 120, f"Expected 120 continents, found {len(data)}"

    required_keys = [
        "id", "name", "description", "common_language", "mortal_species",
        "era_background", "plate_name", "climate_zones", "continental_treaty",
        "dominant_trade_coalition", "continental_chokepoints",
        "tectonic_instability_rating", "continental_forbidden_zones",
        "traits", "compatible_genres", "suggested_regions", "dominant_tycoon_sketch",
        "continental_apex_champion_sketch", "continental_apex_monster_sketch"
    ]

    for c in data:
        for rk in required_keys:
            assert rk in c, f"Continent {c.get('id', 'unknown')} missing required key '{rk}'"
        assert len(c["traits"]) > 0, f"Continent {c['id']} must have non-empty traits"
        assert len(c["compatible_genres"]) > 0, f"Continent {c['id']} must have compatible genres"
        assert len(c["suggested_regions"]) > 0, f"Continent {c['id']} must have suggested regions"
        assert isinstance(c["dominant_tycoon_sketch"], dict), f"Continent {c['id']} dominant_tycoon_sketch must be dict"
        assert isinstance(c["continental_apex_champion_sketch"], dict), f"Continent {c['id']} continental_apex_champion_sketch must be dict"
        assert isinstance(c["continental_apex_monster_sketch"], dict), f"Continent {c['id']} continental_apex_monster_sketch must be dict"
        assert len(c["continental_apex_champion_sketch"]["traits"]) >= 2, f"Continent {c['id']} champion missing traits"
        assert len(c["continental_apex_monster_sketch"]["traits"]) >= 2, f"Continent {c['id']} monster missing traits"


def test_infrastructure_template_loader_continents():
    """InfrastructureTemplateLoader loads and parses all 120 continents into Continent dataclasses."""
    from src.world.infrastructure import InfrastructureTemplateLoader, Continent

    continents = InfrastructureTemplateLoader.load_continent_templates()
    assert len(continents) == 120

    for cid, cont in continents.items():
        assert isinstance(cont, Continent)
        assert cont.id == cid
        assert cont.name
        assert cont.common_language
        assert cont.plate_name
        assert len(cont.traits) >= 1
        assert len(cont.compatible_genres) >= 1
        assert len(cont.suggested_regions) >= 1
        assert isinstance(cont.dominant_tycoon_sketch, dict)
        assert isinstance(cont.continental_apex_champion_sketch, dict)
        assert isinstance(cont.continental_apex_monster_sketch, dict)
        assert len(cont.continental_apex_champion_sketch.get("traits", [])) >= 2
        assert len(cont.continental_apex_monster_sketch.get("traits", [])) >= 2

    # Test serialization round-trip of extended fields
    first_cont = next(iter(continents.values()))
    cont_dict = first_cont.to_dict()
    assert "compatible_genres" in cont_dict
    assert "suggested_regions" in cont_dict
    assert "dominant_tycoon_sketch" in cont_dict
    assert "continental_apex_champion_sketch" in cont_dict
    assert "continental_apex_monster_sketch" in cont_dict
    assert "traits" in cont_dict

    restored = Continent.from_dict(cont_dict)
    assert restored.id == first_cont.id
    assert restored.compatible_genres == first_cont.compatible_genres
    assert restored.suggested_regions == first_cont.suggested_regions
    assert restored.dominant_tycoon_sketch == first_cont.dominant_tycoon_sketch
    assert restored.continental_apex_champion_sketch == first_cont.continental_apex_champion_sketch
    assert restored.continental_apex_monster_sketch == first_cont.continental_apex_monster_sketch
    assert restored.traits == first_cont.traits


def test_continental_apex_champion_and_monster_integrity():
    """Verify all 120 continents possess rich, genre-aligned apex champion and monster sketches with pointer support."""
    from src.world.infrastructure import InfrastructureTemplateLoader, Continent

    continents = InfrastructureTemplateLoader.load_continent_templates()
    assert len(continents) == 120

    for cid, cont in continents.items():
        champ = cont.continental_apex_champion_sketch
        monster = cont.continental_apex_monster_sketch

        # Champion fields
        assert "name" in champ and champ["name"], f"{cid} champion missing name"
        assert "title" in champ and champ["title"], f"{cid} champion missing title"
        assert "traits" in champ and len(champ["traits"]) >= 2, f"{cid} champion missing traits"
        assert "combat_style" in champ and champ["combat_style"], f"{cid} champion missing combat_style"

        # Monster fields
        assert "name" in monster and monster["name"], f"{cid} monster missing name"
        assert "classification" in monster and monster["classification"], f"{cid} monster missing classification"
        assert "traits" in monster and len(monster["traits"]) >= 2, f"{cid} monster missing traits"
        assert "threat_level" in monster and monster["threat_level"], f"{cid} monster missing threat_level"
        assert "description" in monster and monster["description"], f"{cid} monster missing description"

    # Test pointer assignment and roundtrip
    sample = next(iter(continents.values()))
    sample.continental_apex_champion_npc_id = "npc_apex_hero_01"
    sample.continental_apex_monster_id = "monster_apex_leviathan_01"
    
    d = sample.to_dict()
    assert d["continental_apex_champion_npc_id"] == "npc_apex_hero_01"
    assert d["continental_apex_monster_id"] == "monster_apex_leviathan_01"

    restored = Continent.from_dict(d)
    assert restored.continental_apex_champion_npc_id == "npc_apex_hero_01"
    assert restored.continental_apex_monster_id == "monster_apex_leviathan_01"


def test_infrastructure_template_loader_regions():
    """InfrastructureTemplateLoader loads and adapts all 124 region templates with terrain mappings & price multipliers."""
    from src.world.infrastructure import InfrastructureTemplateLoader, Region

    regions = InfrastructureTemplateLoader.load_region_templates(continent_id="test_continent")
    assert len(regions) == 124

    for rid, reg in regions.items():
        assert isinstance(reg, Region)
        assert reg.id == rid
        assert reg.continent_id == "test_continent"
        assert reg.name
        assert reg.terrain in InfrastructureTemplateLoader.TERRAIN_PRICE_MULTIPLIERS
        assert len(reg.natural_price_multipliers) >= 3
        for item_type, mult in reg.natural_price_multipliers.items():
            assert mult > 0.0, f"Multiplier for {item_type} in {rid} should be > 0"
        assert reg.climate_type != ""
        assert reg.dominant_surface != ""
        assert isinstance(reg.mana_density, int) and reg.mana_density >= 0
        assert len(reg.seasonal_temperature_range) == 2
        assert len(reg.traits) >= 1

    # Test adapt_region_template_to_region directly with fallback defaults
    raw_mock = {
        "id": "mock_reg",
        "name": "시험 권역",
        "category": "snow_plateau",
        "description": {"visual": "눈이 쌓인 평원.", "auditory": "바람 소리.", "olfactory": "찬 공기."},
        "environmental_hazards": [{"hazard_name": "동상 위험"}],
        "monsters": ["설원 늑대"]
    }
    adapted = InfrastructureTemplateLoader.adapt_region_template_to_region(raw_mock, continent_id="c_snow")
    assert adapted.id == "mock_reg"
    assert adapted.continent_id == "c_snow"
    assert adapted.terrain == "frozen_tundra"
    assert adapted.climate_type == "혹한대"
    assert adapted.dominant_surface == "ice_sheet"
    assert "눈이 쌓인 평원." in adapted.description
    assert "동상 위험" in adapted.survival_hazards
    assert "설원 늑대" in adapted.common_monsters
    assert "fur" in adapted.natural_price_multipliers
    assert len(adapted.traits) >= 3


def test_cosmology_world_state_injection():
    """InfrastructureTemplateLoader properly injects Level 0 cosmology into WorldState."""
    from src.world.infrastructure import InfrastructureTemplateLoader
    from src.world.state import WorldState

    ws = WorldState()
    cosmo_dict = {
        "id": "cosmo_celestial",
        "world_name": "아스트랄 가이아",
        "genre": "하이 판타지",
        "era_background": "신화적 번영기이자 마도 문명의 여명",
        "cosmology": {
            "sun_and_moons": "루미나스 태양과 두 개의 보랏빛 위성",
            "divine_order": "빛과 정의의 판테온"
        },
        "macro_threat": "차원 균열을 통한 공허 군단의 침공"
    }

    InfrastructureTemplateLoader.inject_cosmology_to_world_state(ws, cosmo_dict)

    assert ws.world_name == "아스트랄 가이아"
    assert ws.world_genre == "하이 판타지"
    assert ws.civilization_era.startswith("신화적 번영기")
    assert ws.epoch_state == "안정기"
    assert "루미나스 태양과 두 개의 보랏빛 위성" in ws.pantheon_deities[0]
    assert "빛과 정의의 판테온" in ws.founded_religions[0]
    assert ws.global_apocalyptic_threat == "차원 균열을 통한 공허 군단의 침공"
    assert ws.world_threat_level == 30
    assert ws.world_crisis_active_stage == 1
    assert "하이 판타지" in ws.world_traits
    assert "거시적 위협 도래" in ws.world_traits
    assert ws.traits == ws.world_traits
    assert ws.cosmology_template == cosmo_dict


def test_assemble_world_upper_layers():
    """InfrastructureTemplateLoader assembles Level 0, Level 1, Level 2 end-to-end into registry."""
    from src.world.infrastructure import InfrastructureTemplateLoader, InfrastructureRegistry
    from src.world.state import WorldState

    # 1. Default assembly (automatic matching)
    ws = WorldState()
    reg = InfrastructureTemplateLoader.assemble_world_upper_layers(ws)

    assert isinstance(reg, InfrastructureRegistry)
    assert ws.infrastructure is reg
    assert len(reg.continents) == 1
    assert len(reg.regions) >= 4

    chosen_cont = next(iter(reg.continents.values()))
    assert len(chosen_cont.region_ids) >= 4
    for rid in chosen_cont.region_ids:
        assert rid in reg.regions
        assert reg.regions[rid].continent_id == chosen_cont.id

    assert len(reg.continents) == 1
    assert len(reg.regions) >= 4
    totals = reg.get_world_totals()
    assert "total_population" in totals
    assert "total_area_sq_km" in totals

    # 2. Targeted assembly with explicit IDs
    ws2 = WorldState()
    reg2 = InfrastructureTemplateLoader.assemble_world_upper_layers(
        ws2,
        cosmo_id="cosmo_01",
        continent_id="continent_aethelgard",
        region_ids=["region_crystal_desert_01", "region_abyssal_maelstrom_01"]
    )
    assert "continent_aethelgard" in reg2.continents
    assert "region_crystal_desert_01" in reg2.regions
    assert "region_abyssal_maelstrom_01" in reg2.regions
    assert reg2.regions["region_crystal_desert_01"].continent_id == "continent_aethelgard"
    assert len(reg2.continents) == 1
    assert len(reg2.regions) == 2


def test_settlement_templates_json_integrity():
    """Validates data/templates/settlement_templates.json for 215 unique settlements and required fields."""
    import json
    from src.core.config import TEMPLATES_DIR

    path = TEMPLATES_DIR / "settlement_templates.json"
    assert path.exists(), "settlement_templates.json must exist"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 215, f"Expected 215 settlements, got {len(data)}"

    seen_ids = set()
    for item in data:
        assert isinstance(item, dict)
        s_id = item.get("id")
        assert s_id, "Settlement must have an id"
        assert s_id not in seen_ids, f"Duplicate settlement id: {s_id}"
        seen_ids.add(s_id)

        assert item.get("name"), f"Settlement {s_id} missing name"
        assert item.get("settlement_type"), f"Settlement {s_id} missing settlement_type"
        assert isinstance(item.get("population"), int), f"Settlement {s_id} population must be int"
        assert isinstance(item.get("security_level"), int), f"Settlement {s_id} security_level must be int"
        assert isinstance(item.get("wall_defense_tier"), int), f"Settlement {s_id} wall_defense_tier must be int"
        assert isinstance(item.get("traits"), list) and len(item["traits"]) >= 1, f"Settlement {s_id} must have traits >= 1"
        assert isinstance(item.get("specialties"), list), f"Settlement {s_id} specialties must be list"
        assert isinstance(item.get("description"), str) and len(item["description"]) > 0, f"Settlement {s_id} missing description"


def test_infrastructure_template_loader_settlements():
    """Validates InfrastructureTemplateLoader.load_settlement_templates and registry binding."""
    from src.world.infrastructure import (
        InfrastructureTemplateLoader, InfrastructureRegistry, Settlement, Nation, Region
    )

    settlements = InfrastructureTemplateLoader.load_settlement_templates()
    assert len(settlements) == 215

    # Check roundtrip serialization of all settlements
    for s_id, s_obj in settlements.items():
        assert isinstance(s_obj, Settlement)
        d = s_obj.to_dict()
        restored = Settlement.from_dict(d)
        assert restored.id == s_id
        assert restored.name == s_obj.name
        assert restored.population == s_obj.population
        assert restored.security_level == s_obj.security_level
        assert len(restored.traits) >= 1

    # Check registry linkage
    reg = InfrastructureRegistry()
    nation = Nation(id="nation_sample", name="샘플 왕국", continent_id="cont_01")
    region = Region(id="region_sample", name="샘플 권역", continent_id="cont_01")
    sample_settle = settlements["settlement_salt_weep_haven"]
    sample_settle.nation_id = "nation_sample"
    sample_settle.region_id = "region_sample"

    reg.register_nation(nation)
    reg.register_region(region)
    reg.register_settlement(sample_settle)

    assert "settlement_salt_weep_haven" in reg.settlements
    assert "settlement_salt_weep_haven" in nation.settlement_ids
    assert "settlement_salt_weep_haven" in region.settlement_ids


def test_nation_templates_json_integrity():
    """Verifies all nation templates in nation_templates.json are valid and well-formed."""
    import json
    from pathlib import Path

    path = Path("data/templates/nation_templates.json")
    assert path.exists(), "nation_templates.json must exist"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 134, f"Expected 134 nation templates, got {len(data)}"

    seen_ids = set()
    for idx, item in enumerate(data):
        assert isinstance(item, dict), f"Nation at index {idx} must be a dict"
        assert "id" in item and item["id"], f"Nation at index {idx} missing id"
        assert "name" in item and item["name"], f"Nation at index {idx} missing name"
        assert "continent_id" in item and item["continent_id"], f"Nation {item['id']} missing continent_id"
        assert item["id"] not in seen_ids, f"Duplicate nation ID: {item['id']}"
        seen_ids.add(item["id"])

        # Mandatory traits rule
        traits = item.get("traits", [])
        assert isinstance(traits, list) and len(traits) >= 1, f"Nation {item['id']} must have >= 1 trait"

        # Species check
        dominant_species = item.get("dominant_species", [])
        assert isinstance(dominant_species, list) and len(dominant_species) >= 1, f"Nation {item['id']} must have >= 1 dominant species"

        # Demographics & Military
        assert isinstance(item.get("population", 0), (int, float))
        assert isinstance(item.get("standing_army_size", 0), int)
        assert item.get("magic_prohibition_tier", 0) in range(0, 6)


def test_infrastructure_template_loader_nations():
    """Validates InfrastructureTemplateLoader.load_nation_templates and registry binding."""
    from src.world.infrastructure import (
        InfrastructureTemplateLoader, InfrastructureRegistry, Nation, Continent
    )

    nations = InfrastructureTemplateLoader.load_nation_templates()
    assert len(nations) == 134

    for n_id, n_obj in nations.items():
        assert isinstance(n_obj, Nation)
        d = n_obj.to_dict()
        restored = Nation.from_dict(d)
        assert restored.id == n_id
        assert restored.name == n_obj.name
        assert restored.population == n_obj.population
        assert restored.standing_army_size == n_obj.standing_army_size
        assert len(restored.traits) >= 1
        assert len(restored.dominant_species) >= 1

    # Check registry linkage
    reg = InfrastructureRegistry()
    cont = Continent(id="continent_azure_archipelago", name="푸른 군도 대륙")
    reg.register_continent(cont)

    sample_nation = nations["nation_silver_harbor_republic"]
    reg.register_nation(sample_nation)

    assert "nation_silver_harbor_republic" in reg.nations
    assert "nation_silver_harbor_republic" in cont.nation_ids


def test_region_templates_json_integrity():
    """Verifies all 61 region templates in region_templates.json are valid, unique, and well-formed."""
    import json
    from pathlib import Path
    from src.world.infrastructure import InfrastructureTemplateLoader, Region

    path = Path("data/templates/region_templates.json")
    assert path.exists(), "region_templates.json must exist"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 124, f"Expected 124 region templates, got {len(data)}"

    seen_ids = set()
    for idx, item in enumerate(data):
        assert isinstance(item, dict), f"Region at {idx} must be dict"
        assert "id" in item and item["id"], f"Region at {idx} missing id"
        assert "name" in item and item["name"], f"Region at {idx} missing name"
        assert item["id"] not in seen_ids, f"Duplicate region ID: {item['id']}"
        seen_ids.add(item["id"])

        # Traits rule
        traits = item.get("traits", [])
        if traits:
            assert isinstance(traits, list) and len(traits) >= 1

    # Verify loading and serialization
    regions = InfrastructureTemplateLoader.load_region_templates(continent_id="cont_test")
    assert len(regions) == 124

    # Verify newly added region with rich nested profile
    crimson = regions.get("region_crimson_caldera")
    assert crimson is not None
    assert crimson.name == "적혈 용암 칼데라"
    assert crimson.terrain == "volcanic"
    assert crimson.dominant_surface == "obsidian_crust"
    assert "태양석 철광맥" in crimson.rare_mineral_deposits
    assert len(crimson.common_monsters) >= 4
    assert len(crimson.cuisine.staples) >= 1
    assert len(crimson.attire.labor_lower_class) >= 1
    assert len(crimson.culture.faith_and_beliefs) >= 1
    assert len(crimson.traits) >= 4

    # Verify Batch 4 region
    frost_peaks = regions.get("region_whispering_frost_peaks")
    assert frost_peaks is not None
    assert frost_peaks.name == "속삭이는 서리 첨봉"
    assert frost_peaks.terrain == "frozen_tundra"
    assert frost_peaks.dominant_surface == "powder_snow"
    assert "블루 아이스 광맥" in frost_peaks.rare_mineral_deposits
    assert len(frost_peaks.traits) >= 4

    # Verify Batch 5 region
    crevasse = regions.get("region_blue_frost_crevasse")
    assert crevasse is not None
    assert crevasse.name == "푸른 서리 빙하 크레바스"
    assert crevasse.terrain == "frozen_tundra"
    assert crevasse.dominant_surface == "blue_ice_sheet"
    assert "청빙 철광맥" in crevasse.rare_mineral_deposits
    assert len(crevasse.traits) >= 4





