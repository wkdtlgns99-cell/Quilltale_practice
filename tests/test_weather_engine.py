import pytest
from src.world.state import WorldState, Location, Player, Item, EnvironmentalMetrics
from src.world.weather_engine import WeatherEngine


def test_weather_elemental_multipliers():
    # Rain
    mult, reason = WeatherEngine.get_elemental_multiplier("fire", "폭우")
    assert mult == 0.5
    assert "반감" in reason

    mult, reason = WeatherEngine.get_elemental_multiplier("lightning", "폭우")
    assert mult == 2.0
    assert "2배" in reason

    # Blizzard
    mult, reason = WeatherEngine.get_elemental_multiplier("ice", "폭설")
    assert mult == 1.3


def test_weather_survival_ticks_hypothermia():
    player = Player(name="방랑자", health=100, body_temperature=34.0)
    loc = Location(id="loc_snow", name="설원", description="눈보라가 치는 설산", exits={})
    env = EnvironmentalMetrics(weather="폭설", temperature_celsius=-10)
    state = WorldState(
        session_id="test_weather_session",
        player=player,
        locations={"loc_snow": loc},
        environment=env
    )

    logs = WeatherEngine.process_turn_survival_ticks(state)
    assert any("저체온증" in l for l in logs)
    assert player.health < 100
    assert player.body_temperature < 34.0
