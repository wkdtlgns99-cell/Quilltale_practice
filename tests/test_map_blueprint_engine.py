"""
Comprehensive Unit and Integration Tests for MapBlueprintEngine (5-Tier 3D Elevation Blueprint).
Tests:
1. Macro continent blueprint generation (Continents, Regions, Nations).
2. Meso regional roads blueprint (3D coordinates, slopes, elevation differences).
3. Micro settlement facilities blueprint (3D elevation levels -2 to +3).
4. GPT executable prompt compilation and LoRA SD 1.5 prompt tag generation.
5. ASCII 3D relief contour map preview.
6. Unity 2D-3D HD-2D JSON scene graph specification.
7. TwoPassEngine live turn action resolution (action: "지도 확인").
8. GameMasterAgent export_map_blueprint interface.
"""
import pytest

from src.agents.game_master import GameMasterAgent
from src.llm.base import BaseLLM
from src.world.generator import WorldGenerator
from src.world.map_blueprint_engine import (
    ElevationTopologyPoint,
    Map3DBlueprint,
    MapBlueprintEngine,
    MapZoomLevel,
)
from src.world.state import WorldState
from src.world.two_pass_engine import TwoPassEngine


class DummyLLM(BaseLLM):
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return '{"narration": "양피지 지도를 펼치자 대륙의 산맥과 가도가 한눈에 들어옵니다."}'

    def generate_json(self, prompt: str, system_prompt: str = "") -> str:
        return '{"name": "테스트"}'


@pytest.fixture
def assembled_world_state() -> WorldState:
    """Creates a realistic WorldState with full 6-tier infrastructure."""
    llm = DummyLLM()
    gen = WorldGenerator(llm)
    world_data, _ = gen.generate_new_world()
    state = WorldState.from_dict(world_data)
    return state


def test_macro_continent_blueprint_generation(assembled_world_state):
    """Verifies macro viewport with continents, regions, nations, and 3D bounds."""
    bp = MapBlueprintEngine.generate_blueprint(
        assembled_world_state,
        zoom_level=MapZoomLevel.MACRO_CONTINENT
    )

    assert isinstance(bp, Map3DBlueprint)
    assert bp.zoom_level == MapZoomLevel.MACRO_CONTINENT
    assert len(bp.continents) >= 1
    assert len(bp.regions) >= 1
    assert len(bp.nations) >= 1
    assert len(bp.settlements_3d) >= 1
    assert len(bp.roads_3d) >= 1
    assert bp.elevation_range_m[1] >= bp.elevation_range_m[0]
    assert len(bp.traits) > 0


def test_meso_road_network_blueprint_elevation(assembled_world_state):
    """Verifies meso regional viewport with 3D road trajectories, elevation deltas, and slope angles."""
    bp = MapBlueprintEngine.generate_blueprint(
        assembled_world_state,
        zoom_level=MapZoomLevel.MESO_REGION_ROADS
    )

    assert bp.zoom_level == MapZoomLevel.MESO_REGION_ROADS
    assert len(bp.settlements_3d) >= 1
    assert len(bp.roads_3d) >= 1

    # Check 3D road fields
    for road in bp.roads_3d:
        assert "origin_3d" in road
        assert len(road["origin_3d"]) == 3
        assert "destination_3d" in road
        assert len(road["destination_3d"]) == 3
        assert "slope_degree" in road
        assert road["slope_degree"] >= 0.0
        assert "distance_km" in road
        assert road["distance_km"] > 0.0


def test_micro_settlement_facilities_3d_layers(assembled_world_state):
    """Verifies micro viewport with 3D facility layers (-2 underground to +3 tower)."""
    bp = MapBlueprintEngine.generate_blueprint(
        assembled_world_state,
        zoom_level=MapZoomLevel.MICRO_SETTLEMENT_FACILITIES
    )

    assert bp.zoom_level == MapZoomLevel.MICRO_SETTLEMENT_FACILITIES
    assert bp.target_name is not None
    assert len(bp.facilities_3d) >= 1

    for fac in bp.facilities_3d:
        assert "relative_coords_m" in fac
        assert len(fac["relative_coords_m"]) == 2
        assert "elevation_level" in fac
        assert -2 <= fac["elevation_level"] <= 3
        assert "elevation_label" in fac
        assert "absolute_elevation_m" in fac


def test_gpt_executable_prompt_and_sd_tags(assembled_world_state):
    """Verifies executable prompt compilation and SD 1.5 / LoRA tag outputs."""
    bp = MapBlueprintEngine.generate_blueprint(
        assembled_world_state,
        zoom_level=MapZoomLevel.MACRO_CONTINENT
    )

    # GPT prompt
    prompt = bp.gpt_executable_prompt
    assert "[MAP DRAWING SPECIFICATION & PROMPT]" in prompt
    assert "DALL-E 3" in prompt
    assert "해발" in prompt
    assert "좌표" in prompt

    # SD 1.5 tags
    tags = bp.diffusion_tags
    assert "positive_prompt" in tags
    assert "negative_prompt" in tags
    assert "fantasy cartography" in tags["positive_prompt"]
    assert "isometric 3d view" in tags["positive_prompt"]


def test_ascii_relief_preview_output(assembled_world_state):
    """Verifies ASCII 3D relief contour map preview generation."""
    bp = MapBlueprintEngine.generate_blueprint(
        assembled_world_state,
        zoom_level=MapZoomLevel.MESO_REGION_ROADS
    )

    ascii_map = bp.ascii_relief_preview
    assert "3D 등고선 지형 릴리프" in ascii_map
    assert "기호:" in ascii_map
    assert "고도 범위:" in ascii_map
    assert len(ascii_map.splitlines()) >= 10


def test_unity_hd2d_spec_serialization(assembled_world_state):
    """Verifies Unity HD-2D scene graph JSON specification."""
    bp = MapBlueprintEngine.generate_blueprint(
        assembled_world_state,
        zoom_level=MapZoomLevel.MACRO_CONTINENT
    )

    spec = bp.unity_hd2d_spec
    assert "world_name" in spec
    assert "settlements" in spec
    assert "roads" in spec
    assert "facilities" in spec

    d = bp.to_dict()
    assert d["zoom_level"] == "macro_continent"
    assert "unity_hd2d_spec" in d


def test_live_pass1_map_inspection_resolution(assembled_world_state):
    """Verifies TwoPassEngine.compute_pass1 resolves map inspection action."""
    action = "대륙 지형도와 지도를 확인한다"
    p1 = TwoPassEngine.compute_pass1(action, assembled_world_state)

    assert p1.is_valid is True
    assert p1.map_blueprint_summary is not None
    assert "3D 지형 설계도" in p1.map_blueprint_summary
    assert p1.map_blueprint_prompt is not None

    # Prompt context includes map instructions
    context = p1.to_prompt_context()
    assert "3D 지형 지도 및 인프라 설계도" in context
    assert "GPT 작화 지침 프리뷰" in context


def test_game_master_export_map_blueprint(assembled_world_state):
    """Verifies GameMasterAgent.export_map_blueprint across all 3 zoom levels."""
    llm = DummyLLM()
    gm = GameMasterAgent(llm)

    macro_bp = gm.export_map_blueprint(assembled_world_state, "macro")
    assert macro_bp.zoom_level == MapZoomLevel.MACRO_CONTINENT

    meso_bp = gm.export_map_blueprint(assembled_world_state, "meso")
    assert meso_bp.zoom_level == MapZoomLevel.MESO_REGION_ROADS

    micro_bp = gm.export_map_blueprint(assembled_world_state, "micro")
    assert micro_bp.zoom_level == MapZoomLevel.MICRO_SETTLEMENT_FACILITIES


def test_elevation_topology_point_dataclass():
    """Verifies ElevationTopologyPoint dataclass with mandatory traits."""
    pt = ElevationTopologyPoint(
        x_km=12.5,
        y_km=34.0,
        elevation_m=450,
        terrain_type="hills",
        slope_deg=8.5,
        traits=["완만한 구릉", "초소 설치 적합"]
    )
    d = pt.to_dict()
    assert d["elevation_m"] == 450
    assert "완만한 구릉" in d["traits"]
