"""
Unit tests for ThermalSurvivalEngine, clothing insulation, wetness physics,
hypothermia and hyperthermia stages, and campfire mechanics.
"""
import pytest
from src.world.state import WorldState, Location, Player, Item, EnvironmentalMetrics
from src.world.thermal_engine import (
    ThermalSurvivalEngine,
    THERMAL_SURVIVAL_SYSTEM,
    ADDITIONAL_SURVIVAL_ENVIRONMENT_SYSTEMS,
    CLOTHING_INSULATION_REGISTRY,
    HYPOTHERMIA_STAGES_REGISTRY,
    HYPERTHERMIA_STAGES_REGISTRY,
    ThermalClothingSpec,
    HypothermiaStageSpec,
    HyperthermiaStageSpec
)
from src.world.weather_engine import WeatherEngine


@pytest.fixture
def survival_world():
    state = WorldState()
    state.player.location = "wilderness_1"
    state.player.health = 100
    state.player.max_health = 100
    state.player.body_temperature = 36.5
    state.player.wetness = 0.0
    state.player.thermal_status = "normal"
    state.player.fatigue = 0

    loc = Location(
        id="wilderness_1",
        name="눈 덮인 고원",
        description="매서운 칼바람이 부는 눈 덮인 고원 지대입니다.",
        exits={},
        traits=["snow", "mountain", "cold"]
    )
    state.locations["wilderness_1"] = loc
    return state


def test_master_thermal_registries_and_traits():
    """Verify master clothing and thermal hazard registries with traits."""
    # Clothing registry
    for cid in ["fur_coat", "oilskin_cloak", "heavy_plate", "linen_tunic"]:
        assert cid in CLOTHING_INSULATION_REGISTRY
        spec = CLOTHING_INSULATION_REGISTRY[cid]
        assert len(spec.traits) > 0
        assert spec.name_ko

    fur = CLOTHING_INSULATION_REGISTRY["fur_coat"]
    assert fur.insulation == 8.0
    assert fur.wetness_protection == 30.0

    oilskin = CLOTHING_INSULATION_REGISTRY["oilskin_cloak"]
    assert oilskin.wetness_protection == 100.0

    plate = CLOTHING_INSULATION_REGISTRY["heavy_plate"]
    assert plate.insulation == -3.0
    assert plate.heat_resistance == -5.0

    # Hypothermia registry
    for stage_id in ["mild", "moderate", "severe", "fatal"]:
        assert stage_id in HYPOTHERMIA_STAGES_REGISTRY
        h_spec = HYPOTHERMIA_STAGES_REGISTRY[stage_id]
        assert len(h_spec.traits) > 0
        assert h_spec.name_ko

    # Hyperthermia registry
    for h_id in ["heat_exhaustion", "heat_cramps", "heat_stroke", "multi_organ_failure"]:
        assert h_id in HYPERTHERMIA_STAGES_REGISTRY
        hp_spec = HYPERTHERMIA_STAGES_REGISTRY[h_id]
        assert len(hp_spec.traits) > 0
        assert hp_spec.name_ko


def test_clothing_net_insulation_calculation(survival_world):
    """Test net insulation, waterproofing, and heat resistance calculation."""
    player = survival_world.player

    # Naked / default
    net_ins, wet_prot, heat_res = ThermalSurvivalEngine.calculate_net_insulation(player, survival_world)
    assert net_ins == 1.0
    assert wet_prot == 0.0

    # Equip fur coat
    fur_item = Item(id="fur_coat_1", name="극지방 늑대 모피 외투", description="따뜻한 늑대 모피 외투", location="inventory", item_type="armor", traits=["fur"])
    survival_world.items["fur_coat_1"] = fur_item
    player.equipment.chest = "fur_coat_1"

    net_ins, wet_prot, heat_res = ThermalSurvivalEngine.calculate_net_insulation(player, survival_world)
    assert net_ins == 9.0  # base 1.0 + 8.0
    assert wet_prot == 30.0
    assert heat_res == -2.0

    # Add oilskin cloak
    oil_item = Item(id="oilskin_1", name="선원의 유포 망토", description="방수성이 뛰어난 유포 망토", location="inventory", item_type="cape", traits=["oilskin"])
    survival_world.items["oilskin_1"] = oil_item
    player.equipment.cape = "oilskin_1"

    net_ins, wet_prot, heat_res = ThermalSurvivalEngine.calculate_net_insulation(player, survival_world)
    assert net_ins == 12.0  # 1.0 + 8.0 + 3.0
    assert wet_prot == 100.0  # Max protection cap


def test_wetness_and_wind_chill_in_blizzard(survival_world):
    """Test wetness accumulation, rain protection, and wind chill acceleration."""
    state = survival_world
    state.environment.weather = "폭설 및 강풍"
    state.environment.temperature_celsius = -15
    state.environment.wind_level = "strong_wind"

    # Start with 80% wetness
    state.player.wetness = 80.0
    state.player.body_temperature = 36.5

    logs = ThermalSurvivalEngine.process_turn_thermal_survival(state)
    assert state.player.body_temperature < 36.5
    # Heat loss was accelerated by wetness (>=75%: 5x) and strong wind (1.8x)
    assert any("저체온증" in log for log in logs)


def test_hypothermia_stages_and_damage(survival_world):
    """Test damage and status effect transition across hypothermia stages."""
    state = survival_world
    state.environment.weather = "혹한"
    state.environment.temperature_celsius = -20

    # Moderate hypothermia: 34.0°C
    state.player.body_temperature = 34.2
    logs = ThermalSurvivalEngine.process_turn_thermal_survival(state)
    assert state.player.thermal_status == "moderate"
    assert state.player.health == 96  # 100 - 4
    assert any("중등도 저체온증" in log for log in logs)

    # Severe hypothermia: 32.0°C
    state.player.body_temperature = 32.5
    logs = ThermalSurvivalEngine.process_turn_thermal_survival(state)
    assert state.player.thermal_status in ["severe", "moderate"]
    assert state.player.health < 96

    # Fatal hypothermia: 28.0°C
    state.player.body_temperature = 29.5
    logs = ThermalSurvivalEngine.process_turn_thermal_survival(state)
    assert state.player.thermal_status == "fatal"
    assert any("치명적 저체온증" in log for log in logs)


def test_heatstroke_and_steel_armor(survival_world):
    """Test desert heatwave, plate armor thermal conductivity, and hyperthermia."""
    state = survival_world
    state.environment.weather = "사막의 살인적 폭염"
    state.environment.temperature_celsius = 45

    # Equip heavy steel plate
    plate_item = Item(id="plate_1", name="기사의 강철 판금 갑옷", description="무거운 강철 판금 갑옷", location="inventory", item_type="armor", traits=["steel"])
    state.items["plate_1"] = plate_item
    state.player.equipment.chest = "plate_1"

    # Initial body temperature
    state.player.body_temperature = 38.0
    logs = ThermalSurvivalEngine.process_turn_thermal_survival(state)

    assert state.player.body_temperature > 38.0
    assert state.player.thermal_status in ["heat_exhaustion", "heat_cramps"]

    # Reach Heat Stroke: 40.0°C
    state.player.body_temperature = 40.0
    state.player.health = 100
    state.player.fatigue = 0
    logs = ThermalSurvivalEngine.process_turn_thermal_survival(state)

    assert state.player.thermal_status in ["heat_stroke", "multi_organ_failure"]
    assert state.player.health < 100
    assert state.player.fatigue >= 10


def test_campfire_drying_and_normalization(survival_world):
    """Test lighting campfire dries wetness and normalizes hypothermia."""
    state = survival_world
    state.environment.weather = "흐림"
    state.environment.temperature_celsius = 5
    state.player.wetness = 60.0
    state.player.body_temperature = 34.5

    # Light campfire
    success, msg = ThermalSurvivalEngine.light_campfire(state)
    assert success is True
    assert state.environment.has_heat_source is True
    assert state.player.wetness == 45.0  # 60 - 15
    assert state.player.body_temperature == 35.0  # 34.5 + 0.5

    # Process turn with campfire active under shelter/cloudy
    logs = ThermalSurvivalEngine.process_turn_thermal_survival(state)
    assert state.player.wetness == 35.0  # 45 - 10
    assert state.player.body_temperature == 35.5  # 35.0 + 0.5


def test_weather_engine_integration(survival_world):
    """Verify WeatherEngine seamlessly delegates survival ticks to ThermalSurvivalEngine."""
    state = survival_world
    state.environment.weather = "폭설과 짙은 안개"
    state.environment.temperature_celsius = -10
    state.player.body_temperature = 35.5

    logs = WeatherEngine.process_turn_survival_ticks(state)
    assert any("저체온증" in log for log in logs)
    assert any("농무 시야 제한" in log for log in logs)
