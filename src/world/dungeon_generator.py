"""
BSP-Based Procedural 2D Tile Grid & AI Battlemap Blueprint Generator for Quilltale TRPG.
Features:
1. Binary Space Partitioning (BSP): Recursive dungeon area partitioning into distinct chambers.
2. Corridors & Threshold Doors: L-shaped & straight corridor carving with automatic door placements.
3. 3D Spatial & Level Metrics: Ceiling height (Z-axis 2.5m~6.0m), floor strata, and vertical stairs (<, >).
4. Dynamic Lighting & Props: Wall torches, arcane braziers, light radius/color, pillars, altars.
5. Entity Spawns & Traps: Treasure chests (T), floor traps (^), monster spawns (M).
6. BFS Reachability Verification: Ensures 100% path connectivity between entrance and exit stairs.
7. Multi-Target Rendering: ASCII map, Roll20/Foundry VTT JSON spec, and DALL-E/Midjourney prompts.

Pure Python, 100% deterministic, 0-token, 0-GPU, 0ms cost.
"""
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import logging
import random
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 1. Tile Definitions & Data Models
# ──────────────────────────────────────────────

class TileType(str, Enum):
    WALL = "#"            # 암반 / 석조 외벽
    FLOOR = "."           # 방 바닥
    CORRIDOR = "~"        # 연결 통로 / 복도
    DOOR = "+"            # 닫힌 목제/철제 문
    DOOR_OPEN = "/"       # 열린 문
    DOOR_SECRET = "S"     # 숨겨진 비밀문
    STAIRS_UP = "<"       # 상층 / 지상 출구 계단
    STAIRS_DOWN = ">"     # 하층 심도 하강 계단
    CHEST = "T"           # 보물상자 / 궤짝
    TRAP = "^"            # 잠복된 바닥 함정
    MONSTER = "M"         # 몬스터 스폰 지점
    PILLAR = "O"          # 석조 지탱 기둥
    ALTAR = "A"           # 고대 제단 / 성소
    VOID = " "            # 미굴착 공허


WALKABLE_TILES: Set[str] = {
    TileType.FLOOR.value,
    TileType.CORRIDOR.value,
    TileType.DOOR_OPEN.value,
    TileType.STAIRS_UP.value,
    TileType.STAIRS_DOWN.value,
    TileType.CHEST.value,
    TileType.TRAP.value,
    TileType.MONSTER.value,
}


@dataclass
class LightSource:
    x: int
    y: int
    type: str = "wall_torch"           # "wall_torch", "arcane_brazier", "bioluminescent_moss"
    color: str = "#f59e0b"             # Warm orange (#f59e0b), Arcane green (#10b981), Cyan (#06b6d4)
    radius_m: float = 6.0              # Effective radius in meters
    traits: List[str] = field(default_factory=lambda: ["광원", "횃불"])


@dataclass
class DoorData:
    x: int
    y: int
    state: str = "closed"              # "closed", "open", "locked"
    is_secret: bool = False
    connects: List[str] = field(default_factory=list) # connected room IDs
    traits: List[str] = field(default_factory=lambda: ["문", "출입구"])


@dataclass
class GridRoom:
    room_id: str
    name_ko: str
    x: int
    y: int
    w: int
    h: int
    center: Tuple[int, int]
    room_type: str = "chamber"         # "entrance", "corridor", "crypt", "armory", "boss", "shrine"
    ceiling_height_m: float = 3.5
    floor_strata: str = "granite"
    light_sources: List[LightSource] = field(default_factory=list)
    contents: Dict[str, Any] = field(default_factory=dict)
    traits: List[str] = field(default_factory=lambda: ["던전 방", "석조 공간"])


@dataclass
class DungeonGridMap:
    dungeon_id: str
    floor_num: int
    theme: str
    width: int
    height: int
    grid: List[List[str]]
    rooms: List[GridRoom] = field(default_factory=list)
    doors: List[DoorData] = field(default_factory=list)
    stairs_up_pos: Tuple[int, int] = (0, 0)
    stairs_down_pos: Tuple[int, int] = (0, 0)
    chests: List[Tuple[int, int]] = field(default_factory=list)
    traps: List[Tuple[int, int]] = field(default_factory=list)
    monsters: List[Tuple[int, int]] = field(default_factory=list)
    revealed_fog: List[List[bool]] = field(default_factory=list)
    external_ai_prompts: Dict[str, Any] = field(default_factory=dict)
    traits: List[str] = field(default_factory=lambda: ["던전 그리드 맵", "2D 타일맵"])


# ──────────────────────────────────────────────
# 2. BSP (Binary Space Partitioning) Node
# ──────────────────────────────────────────────

class _BSPNode:
    """Internal node for Binary Space Partitioning tree."""
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.left: Optional['_BSPNode'] = None
        self.right: Optional['_BSPNode'] = None
        self.room: Optional[GridRoom] = None

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def split(self, min_size: int, rng: random.Random) -> bool:
        if not self.is_leaf():
            return False

        # Decide split orientation: horizontal or vertical
        # If width is much larger than height, split vertically; and vice versa
        if self.w > self.h and self.w / self.h >= 1.25:
            split_horizontally = False
        elif self.h > self.w and self.h / self.w >= 1.25:
            split_horizontally = True
        else:
            split_horizontally = rng.choice([True, False])

        max_val = (self.h if split_horizontally else self.w) - min_size
        if max_val <= min_size:
            return False  # Too small to split

        split_pos = rng.randint(min_size, max_val)

        if split_horizontally:
            self.left = _BSPNode(self.x, self.y, self.w, split_pos)
            self.right = _BSPNode(self.x, self.y + split_pos, self.w, self.h - split_pos)
        else:
            self.left = _BSPNode(self.x, self.y, split_pos, self.h)
            self.right = _BSPNode(self.x + split_pos, self.y, self.w - split_pos, self.h)

        return True


# ──────────────────────────────────────────────
# 3. BSP Dungeon Generator Engine
# ──────────────────────────────────────────────

class BSPDungeonGenerator:
    """
    100% Deterministic Procedural 2D Dungeon Generator.
    Uses Binary Space Partitioning (BSP) to carve multi-room labyrinths,
    connects them with corridors and doors, and generates AI artwork prompts.
    """

    THEME_DESCRIPTIONS: Dict[str, Dict[str, Any]] = {
        "catacomb": {
            "name_ko": "지하 납골당",
            "strata": "limestone",
            "ambient_light": "#f59e0b",
            "torch_type": "wall_torch",
            "ceiling_base": 3.2,
            "dalle_style": "ancient dark catacomb dungeon, crumbling stone brick walls, scattered sarcophagi and bone dust",
        },
        "sunken_ruin": {
            "name_ko": "수몰된 고대 유적",
            "strata": "granite",
            "ambient_light": "#06b6d4",
            "torch_type": "bioluminescent_moss",
            "ceiling_base": 4.5,
            "dalle_style": "sunken ancient ruins dungeon, flooded mossy stone floors, damp water reflections, cyan glow",
        },
        "abyssal_chasm": {
            "name_ko": "심연의 균열",
            "strata": "obsidian",
            "ambient_light": "#10b981",
            "torch_type": "arcane_brazier",
            "ceiling_base": 6.0,
            "dalle_style": "abyssal chasm dungeon, dark obsidian jagged walls, glowing eldritch green braziers, sulfur mist",
        },
        "ancient_mine": {
            "name_ko": "버려진 고대 광산",
            "strata": "sandstone",
            "ambient_light": "#eab308",
            "torch_type": "wall_torch",
            "ceiling_base": 2.8,
            "dalle_style": "abandoned ancient underground mine, wooden support beams, rusted minecart rails, rough sandstone",
        },
    }

    ROOM_NAMES: Dict[str, List[str]] = {
        "entrance": ["하강 계단실 (입구)", "축축한 입구 회랑", "버려진 경비 초소"],
        "crypt": ["고대 석관 안치소", "봉인된 납골실", "원혼의 묘실", "비전 의식의 방"],
        "armory": ["녹슨 무기고", "연금술 폐허 저장고", "보물 수장고", "석조 기둥 전당"],
        "boss": ["심연의 제단실", "던전 코어 융합실", "군주의 알현실", "지하 군주의 옥좌"],
        "chamber": ["석조 아치 방", "정적의 홀", "갈림길 참실", "무너진 기도실"],
    }

    @classmethod
    def generate(
        cls,
        dungeon_id: str = "dungeon_catacomb_1",
        floor_num: int = 1,
        theme: str = "catacomb",
        width: int = 40,
        height: int = 25,
        min_room_size: int = 5,
        max_splits: int = 3,
        seed: Optional[int] = None,
    ) -> DungeonGridMap:
        """
        Generates a complete 2D DungeonGridMap with rooms, corridors, doors,
        loot, traps, Z-axis heights, and external AI prompts.
        """
        rng = random.Random(seed if seed is not None else (hash(f"{dungeon_id}_{floor_num}") & 0xFFFFFFFF))

        # 1. Initialize grid with solid walls
        grid = [[TileType.WALL.value for _ in range(width)] for _ in range(height)]
        revealed = [[False for _ in range(width)] for _ in range(height)]

        # 2. Build BSP Tree
        root = _BSPNode(1, 1, width - 2, height - 2)
        cls._split_bsp(root, min_room_size + 4, max_splits, rng)

        # 3. Create rooms in leaf nodes
        rooms: List[GridRoom] = []
        cls._create_rooms(root, rooms, theme, floor_num, rng)

        if len(rooms) < 2:
            # Fallback: force create at least 2 rooms
            cls._create_fallback_rooms(rooms, width, height, theme, floor_num)

        # Sort rooms left-to-right / top-to-bottom for predictable progression
        rooms.sort(key=lambda r: (r.center[0] + r.center[1]))

        # Assign room roles: first is entrance, last is boss
        rooms[0].room_type = "entrance"
        rooms[0].name_ko = cls.ROOM_NAMES["entrance"][0]
        if len(rooms) > 1:
            rooms[-1].room_type = "boss"
            rooms[-1].name_ko = cls.ROOM_NAMES["boss"][0]
        if len(rooms) > 2:
            rooms[1].room_type = "crypt"
            rooms[1].name_ko = cls.ROOM_NAMES["crypt"][0]
        if len(rooms) > 3:
            rooms[2].room_type = "armory"
            rooms[2].name_ko = cls.ROOM_NAMES["armory"][0]

        # 4. Carve rooms into grid
        for room in rooms:
            for y in range(room.y, room.y + room.h):
                for x in range(room.x, room.x + room.w):
                    grid[y][x] = TileType.FLOOR.value

        # 5. Connect rooms with corridors via BSP sibling tree connections
        doors: List[DoorData] = []
        cls._connect_rooms(root, grid, doors, width, height, rng)

        # Connect any isolated rooms linearly to ensure tree spanning
        cls._ensure_corridors_connected(rooms, grid, doors, width, height)

        # 6. Place Vertical Stairs (< and >)
        # Entrance room gets stairs_up
        up_x, up_y = rooms[0].x + 1, rooms[0].y + 1
        grid[up_y][up_x] = TileType.STAIRS_UP.value
        stairs_up_pos = (up_x, up_y)
        rooms[0].contents["stairs_up"] = stairs_up_pos

        # Boss room gets stairs_down
        boss_room = rooms[-1]
        down_x, down_y = boss_room.x + boss_room.w - 2, boss_room.y + boss_room.h - 2
        grid[down_y][down_x] = TileType.STAIRS_DOWN.value
        stairs_down_pos = (down_x, down_y)
        boss_room.contents["stairs_down"] = stairs_down_pos

        # 7. Place props & entities: Pillars, Altars, Chests, Traps, Monsters
        chests: List[Tuple[int, int]] = []
        traps: List[Tuple[int, int]] = []
        monsters: List[Tuple[int, int]] = []

        cls._populate_rooms(rooms, grid, chests, traps, monsters, floor_num, rng)

        # 8. Place wall light sources for each room
        theme_cfg = cls.THEME_DESCRIPTIONS.get(theme, cls.THEME_DESCRIPTIONS["catacomb"])
        cls._place_lighting(rooms, theme_cfg, rng)

        # 9. Verify BFS reachability from stairs_up to stairs_down
        path_exists = cls._verify_path(grid, stairs_up_pos, stairs_down_pos, width, height)
        if not path_exists:
            # Force carve direct hallway if BFS fails
            cls._carve_direct_corridor(grid, stairs_up_pos, stairs_down_pos)

        # 10. Generate External AI Prompts (DALL-E 3, Midjourney, SD 1.5, GPT)
        prompts = cls._generate_ai_prompts(
            dungeon_id=dungeon_id,
            floor_num=floor_num,
            theme=theme,
            theme_cfg=theme_cfg,
            rooms=rooms,
            doors=doors,
            width=width,
            height=height,
        )

        return DungeonGridMap(
            dungeon_id=dungeon_id,
            floor_num=floor_num,
            theme=theme,
            width=width,
            height=height,
            grid=grid,
            rooms=rooms,
            doors=doors,
            stairs_up_pos=stairs_up_pos,
            stairs_down_pos=stairs_down_pos,
            chests=chests,
            traps=traps,
            monsters=monsters,
            revealed_fog=revealed,
            external_ai_prompts=prompts,
            traits=["던전 그리드 맵", f"테마: {theme}", f"B{floor_num}F", f"{width}x{height}", f"방 {len(rooms)}개"],
        )

    # ── Internal BSP Generation Helpers ──

    @classmethod
    def _split_bsp(cls, node: _BSPNode, min_size: int, depth: int, rng: random.Random):
        if depth <= 0:
            return
        if node.split(min_size, rng):
            if node.left:
                cls._split_bsp(node.left, min_size, depth - 1, rng)
            if node.right:
                cls._split_bsp(node.right, min_size, depth - 1, rng)

    @classmethod
    def _create_rooms(
        cls,
        node: _BSPNode,
        rooms: List[GridRoom],
        theme: str,
        floor_num: int,
        rng: random.Random
    ):
        if node.is_leaf():
            # Pad inside leaf node (at least 1 tile margin for walls)
            padding = 2
            max_w = node.w - padding * 2
            max_h = node.h - padding * 2
            if max_w >= 4 and max_h >= 4:
                rw = rng.randint(4, max(4, max_w))
                rh = rng.randint(4, max(4, max_h))
                rx = node.x + rng.randint(1, max(1, node.w - rw - 1))
                ry = node.y + rng.randint(1, max(1, node.h - rh - 1))

                room_idx = len(rooms) + 1
                theme_cfg = cls.THEME_DESCRIPTIONS.get(theme, cls.THEME_DESCRIPTIONS["catacomb"])
                center = (rx + rw // 2, ry + rh // 2)

                room = GridRoom(
                    room_id=f"b{floor_num}f_r{room_idx}",
                    name_ko=f"방 {room_idx}",
                    x=rx,
                    y=ry,
                    w=rw,
                    h=rh,
                    center=center,
                    ceiling_height_m=round(theme_cfg["ceiling_base"] + rng.uniform(-0.4, 0.8), 1),
                    floor_strata=theme_cfg["strata"],
                    traits=[f"B{floor_num}F", theme, f"크기 {rw}x{rh}"],
                )
                node.room = room
                rooms.append(room)
        else:
            if node.left:
                cls._create_rooms(node.left, rooms, theme, floor_num, rng)
            if node.right:
                cls._create_rooms(node.right, rooms, theme, floor_num, rng)

    @classmethod
    def _create_fallback_rooms(
        cls, rooms: List[GridRoom], width: int, height: int, theme: str, floor_num: int
    ):
        theme_cfg = cls.THEME_DESCRIPTIONS.get(theme, cls.THEME_DESCRIPTIONS["catacomb"])
        # Room 1: Top-Left
        r1 = GridRoom(
            room_id=f"b{floor_num}f_r1",
            name_ko="입구실",
            x=3,
            y=3,
            w=8,
            h=6,
            center=(7, 6),
            ceiling_height_m=theme_cfg["ceiling_base"],
            floor_strata=theme_cfg["strata"],
            traits=[f"B{floor_num}F", theme, "fallback"],
        )
        # Room 2: Bottom-Right
        r2 = GridRoom(
            room_id=f"b{floor_num}f_r2",
            name_ko="심층 제단실",
            x=width - 12,
            y=height - 10,
            w=9,
            h=7,
            center=(width - 7, height - 6),
            ceiling_height_m=theme_cfg["ceiling_base"] + 1.0,
            floor_strata=theme_cfg["strata"],
            traits=[f"B{floor_num}F", theme, "fallback"],
        )
        rooms.extend([r1, r2])

    @classmethod
    def _connect_rooms(
        cls,
        node: _BSPNode,
        grid: List[List[str]],
        doors: List[DoorData],
        width: int,
        height: int,
        rng: random.Random
    ):
        if node.is_leaf() or not node.left or not node.right:
            return

        cls._connect_rooms(node.left, grid, doors, width, height, rng)
        cls._connect_rooms(node.right, grid, doors, width, height, rng)

        left_room = cls._get_leaf_room(node.left)
        right_room = cls._get_leaf_room(node.right)

        if left_room and right_room:
            cls._carve_l_corridor(grid, left_room.center, right_room.center, doors, width, height)

    @classmethod
    def _get_leaf_room(cls, node: _BSPNode) -> Optional[GridRoom]:
        if node.room:
            return node.room
        if node.left:
            r = cls._get_leaf_room(node.left)
            if r:
                return r
        if node.right:
            return cls._get_leaf_room(node.right)
        return None

    @classmethod
    def _carve_l_corridor(
        cls,
        grid: List[List[str]],
        start: Tuple[int, int],
        end: Tuple[int, int],
        doors: List[DoorData],
        max_w: int,
        max_h: int
    ):
        """Carves L-shaped corridor connecting two points."""
        x1, y1 = start
        x2, y2 = end

        # Horizontal then Vertical
        step_x = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step_x, step_x):
            if 0 < x < max_w - 1 and 0 < y1 < max_h - 1:
                if grid[y1][x] == TileType.WALL.value:
                    grid[y1][x] = TileType.CORRIDOR.value

        step_y = 1 if y2 >= y1 else -1
        for y in range(y1, y2 + step_y, step_y):
            if 0 < x2 < max_w - 1 and 0 < y < max_h - 1:
                if grid[y][x2] == TileType.WALL.value:
                    grid[y][x2] = TileType.CORRIDOR.value

        # Place door at boundary transition (wall between room and corridor)
        door_candidates = [(x1, y1), (x2, y2)]
        for dx, dy in door_candidates:
            if 0 < dx < max_w - 1 and 0 < dy < max_h - 1:
                if grid[dy][dx] == TileType.CORRIDOR.value:
                    # check if adjacent to room floor
                    has_floor = any(
                        grid[dy + oy][dx + ox] == TileType.FLOOR.value
                        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                        if 0 <= dx + ox < max_w and 0 <= dy + oy < max_h
                    )
                    if has_floor:
                        grid[dy][dx] = TileType.DOOR.value
                        doors.append(DoorData(x=dx, y=dy, state="closed"))

    @classmethod
    def _ensure_corridors_connected(
        cls,
        rooms: List[GridRoom],
        grid: List[List[str]],
        doors: List[DoorData],
        width: int,
        height: int
    ):
        """Connects sequential rooms linearly to ensure no disconnected components."""
        for i in range(len(rooms) - 1):
            r_curr = rooms[i]
            r_next = rooms[i + 1]
            cls._carve_l_corridor(grid, r_curr.center, r_next.center, doors, width, height)

    @classmethod
    def _carve_direct_corridor(cls, grid: List[List[str]], start: Tuple[int, int], end: Tuple[int, int]):
        """Emergency fallback: carve direct tunnel between points."""
        x1, y1 = start
        x2, y2 = end
        step_x = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step_x, step_x):
            if grid[y1][x] == TileType.WALL.value:
                grid[y1][x] = TileType.CORRIDOR.value
        step_y = 1 if y2 >= y1 else -1
        for y in range(y1, y2 + step_y, step_y):
            if grid[y][x2] == TileType.WALL.value:
                grid[y][x2] = TileType.CORRIDOR.value

    # ── Room Population & Props ──

    @classmethod
    def _populate_rooms(
        cls,
        rooms: List[GridRoom],
        grid: List[List[str]],
        chests: List[Tuple[int, int]],
        traps: List[Tuple[int, int]],
        monsters: List[Tuple[int, int]],
        floor_num: int,
        rng: random.Random
    ):
        for room in rooms:
            # Skip entrance room for traps/monsters to be player-friendly
            if room.room_type == "entrance":
                # Maybe a single welcome chest in corner
                if rng.random() < 0.4:
                    cx, cy = room.x + 2, room.y + 2
                    if grid[cy][cx] == TileType.FLOOR.value:
                        grid[cy][cx] = TileType.CHEST.value
                        chests.append((cx, cy))
                        room.contents["chest"] = (cx, cy)
                continue

            # Armory / Vault: Pillars & Chests
            if room.room_type == "armory":
                # Place stone pillars if room is large enough
                if room.w >= 6 and room.h >= 6:
                    p1 = (room.x + 2, room.y + 2)
                    p2 = (room.x + room.w - 3, room.y + 2)
                    p3 = (room.x + 2, room.y + room.h - 3)
                    p4 = (room.x + room.w - 3, room.y + room.h - 3)
                    for px, py in [p1, p2, p3, p4]:
                        grid[py][px] = TileType.PILLAR.value
                # Guaranteed 1-2 chests
                for _ in range(rng.randint(1, 2)):
                    tx, ty = room.x + rng.randint(1, room.w - 2), room.y + rng.randint(1, room.h - 2)
                    if grid[ty][tx] == TileType.FLOOR.value:
                        grid[ty][tx] = TileType.CHEST.value
                        chests.append((tx, ty))

            # Crypt: Sarcophagi/Pillars and Traps
            if room.room_type == "crypt":
                trap_x, trap_y = room.center[0], room.center[1]
                if grid[trap_y][trap_x] == TileType.FLOOR.value:
                    grid[trap_y][trap_x] = TileType.TRAP.value
                    traps.append((trap_x, trap_y))
                # 1 monster
                mx, my = room.x + 2, room.y + room.h - 2
                if grid[my][mx] == TileType.FLOOR.value:
                    grid[my][mx] = TileType.MONSTER.value
                    monsters.append((mx, my))

            # Boss room: Altar and Boss Monster
            if room.room_type == "boss":
                ax, ay = room.center[0], room.center[1]
                if grid[ay][ax] == TileType.FLOOR.value:
                    grid[ay][ax] = TileType.ALTAR.value
                # Boss monster next to altar
                mx, my = ax - 1, ay
                if grid[my][mx] == TileType.FLOOR.value:
                    grid[my][mx] = TileType.MONSTER.value
                    monsters.append((mx, my))
                # Boss treasure chest
                bx, by = room.x + 2, room.y + 2
                if grid[by][bx] == TileType.FLOOR.value:
                    grid[by][bx] = TileType.CHEST.value
                    chests.append((bx, by))

            # General chamber: chance of monster or trap
            if room.room_type == "chamber":
                if rng.random() < 0.6:
                    mx = room.x + rng.randint(1, room.w - 2)
                    my = room.y + rng.randint(1, room.h - 2)
                    if grid[my][mx] == TileType.FLOOR.value:
                        grid[my][mx] = TileType.MONSTER.value
                        monsters.append((mx, my))
                if rng.random() < 0.4:
                    tx = room.x + rng.randint(1, room.w - 2)
                    ty = room.y + rng.randint(1, room.h - 2)
                    if grid[ty][tx] == TileType.FLOOR.value:
                        grid[ty][tx] = TileType.TRAP.value
                        traps.append((tx, ty))

    @classmethod
    def _place_lighting(cls, rooms: List[GridRoom], theme_cfg: Dict[str, Any], rng: random.Random):
        for room in rooms:
            # Place 1-2 wall torches on upper or side walls
            torch_x1 = room.x + 1
            torch_y1 = room.y
            room.light_sources.append(
                LightSource(
                    x=torch_x1,
                    y=torch_y1,
                    type=theme_cfg["torch_type"],
                    color=theme_cfg["ambient_light"],
                    radius_m=6.0,
                )
            )
            if room.w >= 6:
                torch_x2 = room.x + room.w - 2
                torch_y2 = room.y
                room.light_sources.append(
                    LightSource(
                        x=torch_x2,
                        y=torch_y2,
                        type=theme_cfg["torch_type"],
                        color=theme_cfg["ambient_light"],
                        radius_m=6.0,
                    )
                )

    # ── Path Reachability Verification (BFS) ──

    @classmethod
    def _verify_path(
        cls,
        grid: List[List[str]],
        start: Tuple[int, int],
        goal: Tuple[int, int],
        width: int,
        height: int
    ) -> bool:
        """BFS flood-fill verifying path exists through walkable tiles from start to goal."""
        queue = deque([start])
        visited = {start}

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == goal:
                return True

            for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + ox, cy + oy
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    tile = grid[ny][nx]
                    # Walkable or door
                    if tile in WALKABLE_TILES or tile == TileType.DOOR.value:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        return False

    # ── External AI Prompt Generation ──

    @classmethod
    def _generate_ai_prompts(
        cls,
        dungeon_id: str,
        floor_num: int,
        theme: str,
        theme_cfg: Dict[str, Any],
        rooms: List[GridRoom],
        doors: List[DoorData],
        width: int,
        height: int
    ) -> Dict[str, Any]:
        """Assembles production-ready prompts for DALL-E 3, Midjourney, SD 1.5, and LLMs."""
        room_descriptions = []
        for r in rooms:
            room_descriptions.append(f"- {r.name_ko} ({r.room_type}): {r.w}x{r.h}m, 천장 높이 {r.ceiling_height_m}m")

        dalle_prompt = (
            f"Top-down 2D tabletop RPG battlemap of a {theme_cfg['dalle_style']} (Floor B{floor_num}F). "
            f"Dimensions: {width}x{height} grid. "
            f"Features distinct chambers connected by narrow stone corridors and heavy doors: "
            f"an entrance hall with ascending stone stairs (<) lit by flickering wall torches, "
            f"a crypt with sarcophagi, an armory with iron chests (T) and stone pillars (O), "
            f"and a boss sanctum with an ancient dark stone altar (A) and descending stairs (>). "
            f"Grimdark fantasy, ambient torchlight reflections on damp cobblestones, top-down orthographic view, "
            f"crisp grid lines, 8k resolution, Roll20 battlemap style."
        )

        midjourney_prompt = (
            f"top-down D&D battlemap, {theme_cfg['dalle_style']}, subterranean dungeon, "
            f"chambers connected by arched corridors, stone stairs, glowing torches, iron chests, "
            f"orthographic overhead view, dark fantasy, highly detailed stone textures, grid overlay --ar 16:9 --v 6.0"
        )

        diffusion_tags = {
            "positive": (
                f"masterpiece, best quality, top-down battlemap, dungeon grid, {theme}, "
                f"{theme_cfg['strata']} floor, ambient occlusion, stone walls, torchlight, 2d tabletop map"
            ),
            "negative": (
                "low quality, blurry, 3d isometric angle, character portraits, modern, text, watermark"
            )
        }

        gm_narrative_brief = (
            f"[던전 B{floor_num}F {theme_cfg['name_ko']} 공간 요약]\n"
            f"- 지질 암반: {theme_cfg['strata']}, 평균 천장 높이: {theme_cfg['ceiling_base']}m\n"
            f"- 방 구성 ({len(rooms)}개소):\n" + "\n".join(room_descriptions) + "\n"
            f"- 출입문: 총 {len(doors)}개소 배치 완료.\n"
            f"*서사 지침*: 방마다 횃불 불빛의 흔들림, 서늘한 지하 외기, 좁은 아치 통로의 폐소공포증을 생생하게 묘사하십시오."
        )

        return {
            "dalle3_prompt": dalle_prompt,
            "midjourney_prompt": midjourney_prompt,
            "diffusion_tags": diffusion_tags,
            "gm_narrative_brief": gm_narrative_brief,
        }

    # ── Utility & Inspection Methods ──

    @classmethod
    def render_ascii(
        cls,
        grid_map: DungeonGridMap,
        player_pos: Optional[Tuple[int, int]] = None,
        apply_fog: bool = False
    ) -> str:
        """Renders the dungeon into a clean ASCII string with optional player (@) and fog."""
        lines = []
        for y in range(grid_map.height):
            row_chars = []
            for x in range(grid_map.width):
                if player_pos and (x, y) == player_pos:
                    row_chars.append("@")
                elif apply_fog and not grid_map.revealed_fog[y][x]:
                    row_chars.append(" ")
                else:
                    row_chars.append(grid_map.grid[y][x])
            lines.append("".join(row_chars))
        return "\n".join(lines)

    @classmethod
    def is_walkable(cls, grid_map: DungeonGridMap, x: int, y: int) -> bool:
        """Checks if a tile can be stepped on by an entity."""
        if 0 <= x < grid_map.width and 0 <= y < grid_map.height:
            tile = grid_map.grid[y][x]
            return tile in WALKABLE_TILES
        return False

    @classmethod
    def inspect_tile(cls, grid_map: DungeonGridMap, x: int, y: int) -> Dict[str, Any]:
        """Returns rich inspection metadata for a given coordinate."""
        if not (0 <= x < grid_map.width and 0 <= y < grid_map.height):
            return {"tile": TileType.VOID.value, "name_ko": "던전 외부 공허", "is_walkable": False}

        tile = grid_map.grid[y][x]
        tile_names = {
            TileType.WALL.value: "단단한 석조 암반 벽",
            TileType.FLOOR.value: "석조 바닥",
            TileType.CORRIDOR.value: "아치형 연결 통로",
            TileType.DOOR.value: "닫힌 석조/목제 문",
            TileType.DOOR_OPEN.value: "열린 문",
            TileType.STAIRS_UP.value: "상층/지상 상승 계단",
            TileType.STAIRS_DOWN.value: "하층 심도 하강 계단",
            TileType.CHEST.value: "보물상자",
            TileType.TRAP.value: "바닥 함정 장치",
            TileType.MONSTER.value: "몬스터 출현 지점",
            TileType.PILLAR.value: "석조 지탱 기둥",
            TileType.ALTAR.value: "고대 석조 제단",
        }

        # Check which room this coordinate belongs to
        parent_room = None
        for r in grid_map.rooms:
            if r.x <= x < r.x + r.w and r.y <= y < r.y + r.h:
                parent_room = r
                break

        return {
            "x": x,
            "y": y,
            "tile": tile,
            "name_ko": tile_names.get(tile, "미지의 타일"),
            "is_walkable": cls.is_walkable(grid_map, x, y),
            "room_id": parent_room.room_id if parent_room else None,
            "room_name": parent_room.name_ko if parent_room else "복도/통로",
            "ceiling_height_m": parent_room.ceiling_height_m if parent_room else 2.5,
        }

    @classmethod
    def reveal_radius(cls, grid_map: DungeonGridMap, center_x: int, center_y: int, radius: int = 5):
        """Reveals fog of war in a circle around the player."""
        for y in range(max(0, center_y - radius), min(grid_map.height, center_y + radius + 1)):
            for x in range(max(0, center_x - radius), min(grid_map.width, center_x + radius + 1)):
                if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                    grid_map.revealed_fog[y][x] = True

    @classmethod
    def reveal_room(cls, grid_map: DungeonGridMap, room_id: str):
        """Reveals all tiles inside a specific room."""
        for r in grid_map.rooms:
            if r.room_id == room_id:
                for y in range(r.y, r.y + r.h):
                    for x in range(r.x, r.x + r.w):
                        grid_map.revealed_fog[y][x] = True
                break

    @classmethod
    def to_dict(cls, grid_map: DungeonGridMap) -> Dict[str, Any]:
        """Serializes the entire DungeonGridMap into a JSON-serializable dictionary."""
        return {
            "dungeon_id": grid_map.dungeon_id,
            "floor_num": grid_map.floor_num,
            "theme": grid_map.theme,
            "dimensions": {"width": grid_map.width, "height": grid_map.height},
            "stairs_up": list(grid_map.stairs_up_pos),
            "stairs_down": list(grid_map.stairs_down_pos),
            "chests": [list(c) for c in grid_map.chests],
            "traps": [list(t) for t in grid_map.traps],
            "monsters": [list(m) for m in grid_map.monsters],
            "rooms": [
                {
                    "room_id": r.room_id,
                    "name_ko": r.name_ko,
                    "rect": {"x": r.x, "y": r.y, "w": r.w, "h": r.h},
                    "center": list(r.center),
                    "ceiling_height_m": r.ceiling_height_m,
                    "floor_strata": r.floor_strata,
                    "room_type": r.room_type,
                    "light_sources": [
                        {"x": l.x, "y": l.y, "type": l.type, "color": l.color, "radius_m": l.radius_m}
                        for l in r.light_sources
                    ],
                    "contents": r.contents,
                    "traits": list(r.traits),
                }
                for r in grid_map.rooms
            ],
            "doors": [
                {"x": d.x, "y": d.y, "state": d.state, "is_secret": d.is_secret, "connects": d.connects}
                for d in grid_map.doors
            ],
            "ascii_preview": cls.render_ascii(grid_map),
            "external_ai_prompts": grid_map.external_ai_prompts,
            "traits": list(grid_map.traits),
        }
