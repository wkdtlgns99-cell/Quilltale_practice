"""
Unit and Integration tests for MapInteractiveRenderer.
Tests:
1. Coordinate normalization and clamping within 16:9 bounds.
2. Base64 map image loading with caching and fallback.
3. Interactive HTML/SVG map compilation with custom pins and archetype icons.
4. Player location detection and pulsating glow highlight.
5. Fast travel script & inspector data binding.
6. WorldState.to_map_html() and MapBlueprintEngine.to_interactive_html() bridges.
7. Dataclass traits compatibility.
"""
import pytest

from src.agents.game_master import GameMasterAgent
from src.llm.base import BaseLLM
from src.world.generator import WorldGenerator
from src.world.map_blueprint_engine import Map3DBlueprint, MapBlueprintEngine, MapZoomLevel
from src.world.map_interactive_renderer import (
    ARCHETYPE_ICONS,
    MapInteractiveRenderer,
    MapRenderOptions,
)
from src.world.state import WorldState


class DummyLLM(BaseLLM):
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return '{"narration": "지도를 펼쳐 주변 지형을 확인합니다."}'

    def generate_json(self, prompt: str, system_prompt: str = "") -> str:
        return '{"name": "테스트"}'


@pytest.fixture
def populated_world_state() -> WorldState:
    """Fixture with a generated world and 6-tier infrastructure."""
    llm = DummyLLM()
    gen = WorldGenerator(llm)
    world_data, _ = gen.generate_new_world()
    state = WorldState.from_dict(world_data)
    return state


def test_coordinate_normalization_and_clamping():
    """Verifies that world (x, y) coordinates correctly map to 8%~92% percentage viewport."""
    bounds = (0.0, 0.0, 100.0, 100.0)

    # Center coordinate
    left_c, top_c = MapInteractiveRenderer.normalize_coordinates(50.0, 50.0, bounds)
    assert left_c == 50.0
    assert top_c == 50.0

    # Origin (bottom-left in Cartesian -> bottom-left in screen viewport: left min, top max)
    left_0, top_0 = MapInteractiveRenderer.normalize_coordinates(0.0, 0.0, bounds)
    assert left_0 == 8.0
    assert top_0 == 92.0

    # Top-right corner (100, 100 -> left max, top min)
    left_1, top_1 = MapInteractiveRenderer.normalize_coordinates(100.0, 100.0, bounds)
    assert left_1 == 92.0
    assert top_1 == 8.0

    # Beyond bounds clamping
    left_neg, top_neg = MapInteractiveRenderer.normalize_coordinates(-999.0, -999.0, bounds)
    assert left_neg == 8.0
    assert top_neg == 92.0

    left_high, top_high = MapInteractiveRenderer.normalize_coordinates(999.0, 999.0, bounds)
    assert left_high == 92.0
    assert top_high == 8.0


def test_map_render_options_traits():
    """Ensures MapRenderOptions includes traits field according to System Rules."""
    opts = MapRenderOptions()
    assert hasattr(opts, "traits")
    assert isinstance(opts.traits, list)


def test_image_data_uri_and_fallback():
    """Verifies cached base64 image data URI encoding and missing image fallback."""
    # Existing default map
    uri = MapInteractiveRenderer.get_image_data_uri("data/maps/default_overworld.jpg")
    assert uri is not None
    assert uri.startswith("data:image/jpeg;base64,")

    # Second call should hit memory cache
    uri_cached = MapInteractiveRenderer.get_image_data_uri("data/maps/default_overworld.jpg")
    assert uri_cached == uri

    # Non-existent file returns None safely
    none_uri = MapInteractiveRenderer.get_image_data_uri("data/maps/non_existent_map_xyz.png")
    assert none_uri is None


def test_render_map_html_structure(populated_world_state):
    """Verifies complete HTML widget generation with pins, SVG lines, and inspector."""
    html_str = MapInteractiveRenderer.render_map_html(populated_world_state)

    assert "qt-interactive-map-wrapper" in html_str
    assert "qt-map-viewport" in html_str
    assert "qt-map-inspector" in html_str
    assert "qt-map-pin" in html_str
    assert "qtSelectMapPin" in html_str
    assert "qtDeclareMapTravel" in html_str
    assert "data-info=" in html_str


def test_player_location_pin_highlight(populated_world_state):
    """Verifies player base settlement pin is rendered with special pulsating badge."""
    html_str = MapInteractiveRenderer.render_map_html(populated_world_state)

    # Should have at least one player pin with pulse styling
    assert "qt-player-pin" in html_str
    assert "★ 현재 위치" in html_str


def test_state_to_map_html_bridge(populated_world_state):
    """Verifies WorldState.to_map_html() returns valid interactive map HTML."""
    html_str = populated_world_state.to_map_html()
    assert isinstance(html_str, str)
    assert len(html_str) > 100
    assert "qt-interactive-map-wrapper" in html_str


def test_map_blueprint_engine_to_interactive_html(populated_world_state):
    """Verifies MapBlueprintEngine.to_interactive_html() helper."""
    html_str = MapBlueprintEngine.to_interactive_html(populated_world_state)
    assert isinstance(html_str, str)
    assert "qt-map-viewport" in html_str
    assert "qt-map-inspector" in html_str


def test_render_with_empty_state():
    """Verifies fallback rendering when state has no infrastructure or locations."""
    empty_state = WorldState()
    html_str = MapInteractiveRenderer.render_map_html(empty_state)
    assert "qt-interactive-map-wrapper" in html_str
    assert "qt-map-viewport" in html_str
