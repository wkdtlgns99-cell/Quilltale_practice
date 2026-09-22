"""
Unit and Integration Tests for BSP Procedural 2D Dungeon Generator (dungeon_generator.py).
Validates:
1. BSP recursive partitioning and minimum room generation.
2. Vertical stairs placement (< and >) in valid coordinates.
3. BFS reachability guarantee (start stairs to goal stairs always connected).
4. Walkable tile vs solid wall blocking physics.
5. Rich tile inspection metadata (room affinity, ceiling height).
6. Multi-target rendering (ASCII, player @ position, Fog of War).
7. External AI prompts generation (DALL-E 3, Midjourney, SD 1.5 tags, GM brief).
8. 4 thematic biomes (catacomb, sunken_ruin, abyssal_chasm, ancient_mine).
9. Rule 5 traits compliance on all data structures.
10. Live integration with DungeonEngine and TwoPassEngine.
"""
import pytest
from src.world.dungeon_generator import (
    BSPDungeonGenerator, DungeonGridMap, GridRoom, TileType,
    LightSource, DoorData, WALKABLE_TILES,
)
from src.world.dungeon_engine import DungeonEngine
from src.world.state import WorldState, Location, Player
from src.world.two_pass_engine import TwoPassEngine


# ──────────────────────────────────────────────
# 1. BSP Generation & Structure Tests
# ──────────────────────────────────────────────

class TestBSPGeneration:
    def test_bsp_generates_minimum_rooms(self):
        """Dungeon must have at least 2 distinct rooms (entrance and boss)."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=42)
        assert len(grid_map.rooms) >= 2
        assert grid_map.width == 40
        assert grid_map.height == 25
        assert grid_map.rooms[0].room_type == "entrance"
        assert grid_map.rooms[-1].room_type == "boss"

    def test_stairs_placement_and_validity(self):
        """Stairs up (<) and stairs down (>) must be on valid coordinates within the grid."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=100)
        up_x, up_y = grid_map.stairs_up_pos
        down_x, down_y = grid_map.stairs_down_pos

        assert 0 < up_x < 39 and 0 < up_y < 24
        assert 0 < down_x < 39 and 0 < down_y < 24
        assert (up_x, up_y) != (down_x, down_y)
        assert grid_map.grid[up_y][up_x] == TileType.STAIRS_UP.value
        assert grid_map.grid[down_y][down_x] == TileType.STAIRS_DOWN.value

    def test_bfs_reachability_guarantee(self):
        """A player must be able to walk from stairs_up to stairs_down without hitting solid walls."""
        for test_seed in [1, 7, 42, 99, 1234]:
            grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=test_seed)
            path_exists = BSPDungeonGenerator._verify_path(
                grid_map.grid,
                grid_map.stairs_up_pos,
                grid_map.stairs_down_pos,
                grid_map.width,
                grid_map.height,
            )
            assert path_exists is True, f"Seed {test_seed} failed reachability verification"

    def test_walkable_and_blocking_tiles(self):
        """Floor, corridor, stairs must be walkable; walls must not be walkable."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=55)
        up_x, up_y = grid_map.stairs_up_pos
        assert BSPDungeonGenerator.is_walkable(grid_map, up_x, up_y) is True

        # Edge of map is always a solid wall
        assert BSPDungeonGenerator.is_walkable(grid_map, 0, 0) is False
        assert grid_map.grid[0][0] == TileType.WALL.value


# ──────────────────────────────────────────────
# 2. Tile Inspection & Metadata Tests
# ──────────────────────────────────────────────

class TestTileInspection:
    def test_inspect_tile_inside_room(self):
        """Inspecting a room floor tile should return the parent room's metadata."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=42)
        room = grid_map.rooms[0]
        info = BSPDungeonGenerator.inspect_tile(grid_map, room.center[0], room.center[1])

        assert info["room_id"] == room.room_id
        assert info["room_name"] == room.name_ko
        assert info["is_walkable"] is True
        assert info["ceiling_height_m"] > 2.0

    def test_inspect_outside_bounds(self):
        """Inspecting out-of-bounds coordinates safely returns void tile."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=42)
        info = BSPDungeonGenerator.inspect_tile(grid_map, -5, 999)
        assert info["tile"] == TileType.VOID.value
        assert info["is_walkable"] is False


# ──────────────────────────────────────────────
# 3. Rendering & Fog of War Tests
# ──────────────────────────────────────────────

class TestRenderingAndFog:
    def test_render_ascii_dimensions(self):
        """ASCII output must have matching line count and column width."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=42)
        ascii_text = BSPDungeonGenerator.render_ascii(grid_map)
        lines = ascii_text.splitlines()

        assert len(lines) == 25
        assert all(len(line) == 40 for line in lines)
        assert "<" in ascii_text
        assert ">" in ascii_text

    def test_player_position_in_ascii(self):
        """Passing player_pos must render '@' at the specified coordinates."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=42)
        up_x, up_y = grid_map.stairs_up_pos
        ascii_text = BSPDungeonGenerator.render_ascii(grid_map, player_pos=(up_x, up_y))

        lines = ascii_text.splitlines()
        assert lines[up_y][up_x] == "@"

    def test_fog_of_war_reveal(self):
        """Revealing a radius should unmask the fog of war matrix."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=42)
        assert grid_map.revealed_fog[5][5] is False

        BSPDungeonGenerator.reveal_radius(grid_map, 5, 5, radius=3)
        assert grid_map.revealed_fog[5][5] is True
        assert grid_map.revealed_fog[5][6] is True

    def test_reveal_room(self):
        """Revealing a room unmasks all tiles inside that room."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=42)
        room = grid_map.rooms[0]
        BSPDungeonGenerator.reveal_room(grid_map, room.room_id)

        for y in range(room.y, room.y + room.h):
            for x in range(room.x, room.x + room.w):
                assert grid_map.revealed_fog[y][x] is True


# ──────────────────────────────────────────────
# 4. External AI Prompts & Thematic Biomes
# ──────────────────────────────────────────────

class TestAIPromptsAndThemes:
    def test_ai_prompts_assembled(self):
        """External AI prompts dictionary must contain all required generator outputs."""
        grid_map = BSPDungeonGenerator.generate(width=40, height=25, seed=42)
        prompts = grid_map.external_ai_prompts

        assert "dalle3_prompt" in prompts
        assert "midjourney_prompt" in prompts
        assert "diffusion_tags" in prompts
        assert "gm_narrative_brief" in prompts

        assert "Top-down 2D" in prompts["dalle3_prompt"]
        assert "--ar 16:9" in prompts["midjourney_prompt"]
        assert "positive" in prompts["diffusion_tags"]
        assert "negative" in prompts["diffusion_tags"]

    def test_all_four_thematic_biomes(self):
        """All 4 themes must generate appropriate geological strata and style descriptions."""
        themes = ["catacomb", "sunken_ruin", "abyssal_chasm", "ancient_mine"]
        for t in themes:
            grid_map = BSPDungeonGenerator.generate(theme=t, seed=42)
            assert grid_map.theme == t
            assert len(grid_map.rooms[0].light_sources) >= 1
            assert grid_map.external_ai_prompts["gm_narrative_brief"] != ""


# ──────────────────────────────────────────────
# 5. Rule 5 Traits Compliance & Serialization
# ──────────────────────────────────────────────

class TestTraitsAndSerialization:
    def test_rule_5_traits_compliance(self):
        """All game data classes must have traits: List[str] field."""
        grid_map = BSPDungeonGenerator.generate(seed=42)
        assert hasattr(grid_map, "traits")
        assert isinstance(grid_map.traits, list)

        for room in grid_map.rooms:
            assert hasattr(room, "traits")
            assert isinstance(room.traits, list)
            for light in room.light_sources:
                assert hasattr(light, "traits")
                assert isinstance(light.traits, list)

        for door in grid_map.doors:
            assert hasattr(door, "traits")
            assert isinstance(door.traits, list)

    def test_to_dict_roundtrip(self):
        """to_dict() must return a JSON-compliant dictionary with all nested structures."""
        grid_map = BSPDungeonGenerator.generate(seed=42)
        data = BSPDungeonGenerator.to_dict(grid_map)

        assert data["dungeon_id"] == grid_map.dungeon_id
        assert data["floor_num"] == grid_map.floor_num
        assert len(data["rooms"]) == len(grid_map.rooms)
        assert "ascii_preview" in data
        assert "external_ai_prompts" in data


# ──────────────────────────────────────────────
# 6. Live Engine Integration Tests
# ──────────────────────────────────────────────

class TestLiveEngineIntegration:
    def test_dungeon_engine_create_instance_binds_grid_map(self):
        """DungeonEngine.create_dungeon_instance() must automatically bind grid_map to every floor."""
        loc = Location(id="surface_cave", name="동굴 입구", description="", exits={})
        state = WorldState(locations={"surface_cave": loc})

        instance = DungeonEngine.create_dungeon_instance(
            state, surface_location_id="surface_cave", max_depth=3
        )
        assert len(instance.floors) == 3
        for floor_num in range(1, 4):
            floor = instance.floors[floor_num]
            assert floor.grid_map is not None
            assert isinstance(floor.grid_map, DungeonGridMap)
            assert floor.grid_map.floor_num == floor_num

    def test_dungeon_engine_render_floor_map(self):
        """DungeonEngine.render_floor_map() returns valid ASCII map for active dungeon."""
        loc = Location(id="surface_cave", name="동굴 입구", description="", exits={})
        state = WorldState(locations={"surface_cave": loc})
        instance = DungeonEngine.create_dungeon_instance(state, "surface_cave", max_depth=2)

        # Move player to B1F entrance room
        b1f_room_1 = f"{instance.dungeon_id}_b1f_r1"
        state.player.location = b1f_room_1

        ascii_map = DungeonEngine.render_floor_map(state)
        assert "#" in ascii_map
        assert "<" in ascii_map
        assert ">" in ascii_map

    def test_two_pass_engine_map_inspection(self):
        """Pass 1 action with '던전 지도' must populate dungeon_ascii_map on FactSheet."""
        loc = Location(id="surface_cave", name="동굴 입구", description="", exits={})
        state = WorldState(locations={"surface_cave": loc})
        instance = DungeonEngine.create_dungeon_instance(state, "surface_cave", max_depth=2)
        state.player.location = f"{instance.dungeon_id}_b1f_r1"

        fact_sheet = TwoPassEngine.compute_pass1("던전 지도 확인", state)
        assert fact_sheet.dungeon_ascii_map is not None
        assert "#" in fact_sheet.dungeon_ascii_map
        assert "지하 던전 2D 타일 지도" in fact_sheet.to_prompt_context()
