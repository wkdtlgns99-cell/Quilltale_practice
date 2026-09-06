"""
Unit tests for WeatherMagicSimulationEngine in Quilltale TRPG.
Tests high-tier weather magic requirements (circle 4+), duration scaling (30m + 15m/circle),
dual-mode combat round ticks, and dual-mode travel exposure ticks (10-minute intervals).
"""
import pytest
from src.world.state import WorldState, Player, Location
from src.world.weather_magic_engine import (
    WeatherMagicSimulationEngine, WeatherMagicSpec, ActiveWeatherAnomaly, WEATHER_MAGIC_REGISTRY
)


@pytest.fixture
def weather_world():
    state = WorldState()
    state.locations["mountain_pass"] = Location(
        id="mountain_pass",
        name="바람의 협곡",
        description="매서운 칼바람이 부는 고지대 협곡.",
        exits={},
        traits=["mountain", "canyon"]
    )
    state.player = Player(
        name="대마법사 이안",
        location="mountain_pass",
        health=50,
        max_health=50,
        mana=100,
        max_mana=100,
        intelligence=18,
        agility=14,
        body_temperature=36.5,
        wetness=0.0
    )
    return state


def test_weather_magic_specs_and_traits():
    """Verifies all high-tier weather spells have traits and require circle 4+."""
    assert len(WEATHER_MAGIC_REGISTRY) >= 6
    for m_id, spec in WEATHER_MAGIC_REGISTRY.items():
        assert isinstance(spec, WeatherMagicSpec)
        assert len(spec.traits) > 0
        assert "weather_magic" in spec.traits
        assert spec.min_circle_required >= 4
        assert spec.base_duration_minutes == 30


def test_cast_weather_magic_circle_restriction(weather_world):
    """
    User Decision: Weather magic is high-tier elemental magic (minimum Circle 4+).
    Apprentice mages (Circle 1-3) cannot alter continental weather.
    """
    apprentice = Player(
        name="견습 마법사 토미",
        location="mountain_pass",
        mana=100,
        traits=["견습_마법사"]  # Circle 1 default
    )
    # Circle 1 tries to cast 4th-circle icicle_rain -> Rejection
    success, msg = WeatherMagicSimulationEngine.cast_weather_magic(
        weather_world, apprentice, "icicle_rain"
    )
    assert not success
    assert "최소 4서클 이상의 마법사만이" in msg

    # Circle 5 archmage casts blizzard_veil -> Success
    archmage = Player(
        name="대마법사 실비아",
        location="mountain_pass",
        mana=100,
        traits=["5서클_대마법사"]
    )
    success5, msg5 = WeatherMagicSimulationEngine.cast_weather_magic(
        weather_world, archmage, "blizzard_veil"
    )
    assert success5
    assert "영창 성공" in msg5
    # Check duration scaling: 30 base + (5 - 4) * 15 = 45 minutes
    anomalies = WeatherMagicSimulationEngine.get_anomalies(weather_world)
    assert len(anomalies) == 1
    anom = list(anomalies.values())[0]
    assert anom.remaining_minutes == 45


def test_combat_weather_tick_damage_and_cover_mitigation(weather_world):
    """
    Dual-mode Combat Resolution:
    Exposed actors take combat damage dice with agility saving throw;
    Cover or shield grants half-damage mitigation.
    """
    # Active hail storm
    archmage = Player(name="시전자", location="mountain_pass", traits=["6서클_현자"])
    WeatherMagicSimulationEngine.cast_weather_magic(weather_world, archmage, "icicle_rain")

    victim = weather_world.player
    initial_hp = victim.health

    # 1. Exposed with no cover
    logs = WeatherMagicSimulationEngine.resolve_combat_weather_tick(
        weather_world,
        victim,
        has_cover_or_shield=False,
        fixed_roll=8
    )
    assert len(logs) > 0
    assert victim.health < initial_hp

    # 2. Behind heavy shield or shelter -> mitigated
    victim.health = 50
    logs_shield = WeatherMagicSimulationEngine.resolve_combat_weather_tick(
        weather_world,
        victim,
        has_cover_or_shield=True,
        fixed_roll=8
    )
    assert any("피격 완화" in l for l in logs_shield)
    assert victim.health == 46  # 8 // 2 = 4 dmg


def test_travel_weather_exposure_cumulative_ticks(weather_world):
    """
    Dual-mode Travel Resolution:
    Converts 40 minutes of travel into 4 ten-minute environment ticks.
    Calculates cumulative damage, wetness gain, and core body temperature loss.
    """
    archmage = Player(name="시전자", location="mountain_pass", traits=["5서클_마법사"], mana=100)
    WeatherMagicSimulationEngine.cast_weather_magic(weather_world, archmage, "blizzard_veil")

    player = weather_world.player
    player.health = 50
    player.body_temperature = 36.5
    player.wetness = 0.0

    logs = WeatherMagicSimulationEngine.resolve_travel_weather_exposure(
        weather_world,
        travel_minutes=40,
        has_shelter=False,
        has_shield_or_coat=False
    )
    assert len(logs) > 0
    # 40 mins // 10 = 4 ticks
    # blizzard_veil: 3 dmg/tick -> 12 dmg; wetness +15/tick -> 60%; temp -1.2/tick -> -4.8C
    assert player.health == 38
    assert player.wetness == 60.0
    assert player.body_temperature == 31.7
    assert any("40분간 이동했습니다" in l for l in logs)


def test_weather_magic_anomaly_expiration(weather_world):
    """Tests anomaly duration countdown and automatic dissipation when time expires."""
    archmage = Player(name="시전자", location="mountain_pass", traits=["4서클_마법사"])
    WeatherMagicSimulationEngine.cast_weather_magic(weather_world, archmage, "icicle_rain")

    anomalies = WeatherMagicSimulationEngine.get_anomalies(weather_world)
    assert len(anomalies) == 1

    # Tick 15 minutes
    logs1 = WeatherMagicSimulationEngine.tick_anomalies(weather_world, delta_minutes=15)
    assert len(anomalies) == 1
    assert list(anomalies.values())[0].remaining_minutes == 15

    # Tick another 15 minutes -> Expired!
    logs2 = WeatherMagicSimulationEngine.tick_anomalies(weather_world, delta_minutes=15)
    assert len(anomalies) == 0
    assert any("기상 마법 소멸" in l for l in logs2)
