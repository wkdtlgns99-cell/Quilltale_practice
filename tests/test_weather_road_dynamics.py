"""
Unit tests for Weather-Road Dynamics and Environmental Travel Constraints.
Tests:
1. Normal baseline travel speed on paved highway and dirt road under clear weather.
2. Downpour (폭우) causing muddy dirt road and flooded swamp trail (travel time surge & fatigue).
3. Blizzard (폭설) & subzero temperatures turning mountain passes into frozen ice.
4. Dijkstra shortest path dynamically rerouting around flooded/icy roads when weather worsens.
5. In-game player movement in TwoPassEngine correctly computing dynamic road condition logs and fatigue.
"""
import pytest
from src.world.state import WorldState, Location, Player, EnvironmentalMetrics
from src.world.geography import (
    GeographyEngine, RoadType, RoadCondition, RoadConnection,
    ROAD_CONDITION_EFFECTS
)
from src.world.two_pass_engine import TwoPassEngine


def test_clear_weather_road_baseline():
    """Clear weather applies NORMAL road conditions."""
    road = RoadConnection(destination_id="town", distance_km=10.0, road_type=RoadType.DIRT_ROAD)
    env = EnvironmentalMetrics(weather="맑음", temperature_celsius=20)

    cond_info = GeographyEngine.get_effective_road_condition(road, env)
    assert cond_info["condition"] == RoadCondition.NORMAL
    assert cond_info["speed_multiplier"] == 1.0
    assert cond_info["hazard_level"] == road.hazard_level
    assert cond_info["fatigue_bonus"] == 0

    # 10 km on dirt road (4 km/h * 1.0) = 2.5 hours
    hours = GeographyEngine.calculate_segment_travel_hours(
        10.0, RoadType.DIRT_ROAD, travel_mode="foot", condition_speed_mult=cond_info["speed_multiplier"]
    )
    assert pytest.approx(hours, 0.01) == 2.5


def test_downpour_muddy_and_flooded_roads():
    """Downpour turns dirt road to MUDDY and swamp trail to FLOODED."""
    dirt_road = RoadConnection(destination_id="camp", distance_km=10.0, road_type=RoadType.DIRT_ROAD)
    swamp_road = RoadConnection(destination_id="swamp", distance_km=10.0, road_type=RoadType.SWAMP_TRAIL)
    highway = RoadConnection(destination_id="capital", distance_km=10.0, road_type=RoadType.PAVED_HIGHWAY)

    rain_env = EnvironmentalMetrics(weather="폭우", temperature_celsius=18)

    dirt_cond = GeographyEngine.get_effective_road_condition(dirt_road, rain_env)
    assert dirt_cond["condition"] == RoadCondition.MUDDY
    assert dirt_cond["speed_multiplier"] == pytest.approx(1.0 * 0.55)
    assert dirt_cond["fatigue_bonus"] == 1
    assert "진흙탕" in dirt_cond["name_ko"]

    swamp_cond = GeographyEngine.get_effective_road_condition(swamp_road, rain_env)
    assert swamp_cond["condition"] == RoadCondition.FLOODED
    assert swamp_cond["speed_multiplier"] == pytest.approx(0.35 * 0.30)
    assert swamp_cond["fatigue_bonus"] == 2

    # Highway resists rain well
    hw_cond = GeographyEngine.get_effective_road_condition(highway, rain_env)
    assert hw_cond["condition"] == RoadCondition.NORMAL


def test_blizzard_frozen_ice_mountain_pass():
    """Blizzard and subzero weather turns mountain pass into FROZEN_ICE with massive hazards."""
    mtn_road = RoadConnection(destination_id="peak", distance_km=5.0, road_type=RoadType.MOUNTAIN_PASS)
    snow_env = EnvironmentalMetrics(weather="폭설", temperature_celsius=-8)

    mtn_cond = GeographyEngine.get_effective_road_condition(mtn_road, snow_env)
    assert mtn_cond["condition"] == RoadCondition.FROZEN_ICE
    assert mtn_cond["hazard_level"] == mtn_road.hazard_level + 40
    assert "살얼음 빙판길" in mtn_cond["name_ko"]
    assert "얼어붙었습니다" in mtn_cond["warning_ko"]


def test_dijkstra_weather_dynamic_routing():
    """Dijkstra shortest travel calculates realistic delay under storm conditions."""
    state = WorldState()
    loc_a = Location(id="loc_a", name="출발지", description="", exits={"east": "loc_b"})
    loc_b = Location(id="loc_b", name="도착지", description="", exits={"west": "loc_a"})
    state.locations = {"loc_a": loc_a, "loc_b": loc_b}

    loc_a.roads = {
        "loc_b": RoadConnection(destination_id="loc_b", distance_km=10.0, road_type=RoadType.DIRT_ROAD)
    }

    # Clear weather travel hours: 10km / 4km/h = 2.5 hours
    clear_env = EnvironmentalMetrics(weather="맑음", temperature_celsius=20)
    h_clear, km_clear, _ = GeographyEngine.dijkstra_shortest_travel(state, "loc_a", "loc_b", environment=clear_env)
    assert pytest.approx(h_clear, 0.01) == 2.5

    # Rain weather travel hours: 10km / (4 * 0.55 km/h) = ~4.54 hours
    rain_env = EnvironmentalMetrics(weather="폭우", temperature_celsius=15)
    h_rain, km_rain, _ = GeographyEngine.dijkstra_shortest_travel(state, "loc_a", "loc_b", environment=rain_env)
    assert h_rain > h_clear
    assert pytest.approx(h_rain, 0.05) == (10.0 / (4.0 * 0.55))


def test_two_pass_movement_with_weather_road_condition():
    """TwoPassEngine correctly applies weather road condition and fatigue to player state."""
    state = WorldState()
    loc1 = Location(id="village", name="평화로운 마을", description="", exits={"east": "marsh"})
    loc2 = Location(id="marsh", name="수렁 지대", description="", exits={"west": "village"})
    state.locations = {"village": loc1, "marsh": loc2}
    state.player.location = "village"
    state.player.fatigue = 0

    loc1.roads = {
        "marsh": RoadConnection(destination_id="marsh", distance_km=6.0, road_type=RoadType.DIRT_ROAD)
    }

    # Heavy downpour active
    state.environment.weather = "폭우"
    state.environment.temperature_celsius = 15

    fact_sheet = TwoPassEngine.compute_pass1("동쪽 수렁 지대로 걸어 이동한다", state)
    assert fact_sheet.is_valid

    # Check movement resolution in pre_computed_state_delta
    delta = fact_sheet.pre_computed_state_delta
    assert delta["player"]["location"] == "marsh"
    # Muddy road increased travel time and added fatigue bonus
    assert delta["time_minutes"] > 90  # 6km / (4 * 0.55) = ~2.72h (163m)
    assert delta["fatigue_delta"] >= 5

    # Progress logs mention road condition
    progress_str = " ".join(fact_sheet.quest_progress_logs)
    assert "진흙탕" in progress_str
