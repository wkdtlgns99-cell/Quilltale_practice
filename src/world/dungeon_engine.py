"""
Dungeon Exploration & Instance Hierarchy Engine for Quilltale TRPG.
Manages multi-floor subterranean labyrinths, room connectivity, environmental hazards,
depth-scaled monster/NPC densities, and contextual trap integration:
1. Depth Scaling: Deeper floors have higher danger levels (30->90), higher monster densities (40->95%),
   and near-zero NPC presence.
2. Atmospheric Realism: Subterranean darkness (torch requirement), decaying oxygen levels,
   and dungeon core elemental themes (abyss, fire, undead, nature, arcane).
3. Contextual Trap Gating: Automatically deploys dungeon-category traps on every floor.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging

from src.world.state import WorldState, Location, EnvironmentalMetrics
from src.world.trap_engine import TrapEngine

logger = logging.getLogger(__name__)


@dataclass
class DungeonRoom:
    room_id: str
    floor_num: int                 # 1 = B1F, 2 = B2F, etc.
    room_type: str                 # "entrance_hall", "corridor", "crypt_chamber", "armory", "boss_sanctum"
    name_ko: str
    description: str
    danger_level: int              # 1~100
    monster_density: int           # 0~100
    npc_density: int               # 0~100
    oxygen_level: int = 95         # Oxygen percentage
    lighting: str = "칠흑 같은 어둠"
    exits: Dict[str, str] = field(default_factory=dict)
    traps: List[str] = field(default_factory=list)
    monsters: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    is_cleared: bool = False
    # Mandatory traits tag list (Rule 6)
    traits: List[str] = field(default_factory=list)


@dataclass
class DungeonFloor:
    floor_num: int                 # 1 for B1F, 2 for B2F
    name_ko: str
    rooms: Dict[str, DungeonRoom] = field(default_factory=dict)
    depth_modifier: float = 1.0
    floor_danger_level: int = 30
    is_boss_floor: bool = False
    # Mandatory traits tag list (Rule 6)
    traits: List[str] = field(default_factory=list)


@dataclass
class DungeonInstance:
    dungeon_id: str
    name_ko: str
    surface_entrance_location_id: str
    theme: str                     # "catacomb", "sunken_ruin", "abyssal_chasm", "ancient_mine"
    core_element: str              # "abyss", "fire", "undead", "nature", "arcane"
    max_depth: int = 3             # Total subterranean floors
    current_floor: int = 1
    floors: Dict[int, DungeonFloor] = field(default_factory=dict)
    is_conquered: bool = False
    # Mandatory traits tag list (Rule 6)
    traits: List[str] = field(default_factory=list)


class DungeonEngine:
    """
    Deterministic Subterranean Dungeon Generator and Exploration Engine.
    """

    ROOM_NAMES_BY_TYPE: Dict[str, List[str]] = {
        "entrance_hall": ["하강 계단실", "축축한 입구 회랑", "버려진 경비 초소"],
        "corridor": ["석조 아치 복도", "해골 벽면 회랑", "갈림길 통로", "무너진 배수관"],
        "crypt_chamber": ["고대 석관 안치소", "봉인된 납골실", "고문실 잔해", "비전 의식의 방"],
        "armory": ["녹슨 무기고", "연금술 폐허 저장고", "보물 수장고"],
        "boss_sanctum": ["심연의 제단 심층부", "던전 코어 융합실", "군주의 알현실"]
    }

    @classmethod
    def create_dungeon_instance(
        cls,
        state: WorldState,
        surface_location_id: str,
        dungeon_name_ko: str = "잊힌 고대 납골당",
        theme: str = "catacomb",
        core_element: str = "undead",
        max_depth: int = 3
    ) -> DungeonInstance:
        """
        Generates a full subterranean multi-floor dungeon linked to the surface entrance.
        Mounts each room into state.locations as first-class navigable Locations.
        """
        dungeon_id = f"dungeon_{surface_location_id}_{theme}"
        instance = DungeonInstance(
            dungeon_id=dungeon_id,
            name_ko=dungeon_name_ko,
            surface_entrance_location_id=surface_location_id,
            theme=theme,
            core_element=core_element,
            max_depth=max_depth,
            current_floor=1,
            traits=["지하 미궁", f"속성: {core_element}", f"테마: {theme}", f"최대 {max_depth}층"]
        )

        for floor_num in range(1, max_depth + 1):
            is_boss_floor = (floor_num == max_depth)
            base_danger = 25 + (floor_num * 15)       # Depth-scaled danger (40 -> 55 -> 70 -> ...)
            monster_dens = min(95, 30 + (floor_num * 20)) # 50 -> 70 -> 90%
            npc_dens = max(0, 15 - (floor_num * 5))       # 10 -> 5 -> 0%
            oxygen = max(50, 100 - (floor_num * 12))      # 88 -> 76 -> 64%

            floor = DungeonFloor(
                floor_num=floor_num,
                name_ko=f"지하 {floor_num}층 - {dungeon_name_ko}",
                depth_modifier=1.0 + (floor_num * 0.25),
                floor_danger_level=base_danger,
                is_boss_floor=is_boss_floor,
                traits=[f"지하 {floor_num}층", f"위험도 {base_danger}", f"산소 {oxygen}%"]
            )

            # Generate Rooms for this floor: Entrance -> Corridor -> Crypt -> (Boss if final)
            room_types = ["entrance_hall", "corridor", "crypt_chamber"]
            if is_boss_floor:
                room_types.append("boss_sanctum")
            else:
                room_types.append("armory")

            prev_room_id: Optional[str] = None
            for idx, r_type in enumerate(room_types):
                room_id = f"{dungeon_id}_b{floor_num}f_r{idx + 1}"
                r_name = f"[지하 {floor_num}층] {cls.ROOM_NAMES_BY_TYPE[r_type][idx % len(cls.ROOM_NAMES_BY_TYPE[r_type])]}"

                # Subterranean environment
                env = EnvironmentalMetrics(
                    weather="지하 밀실",
                    lighting="칠흑 같은 어둠" if r_type != "entrance_hall" else "희미한 등불",
                    smell="퀴퀴한 곰팡이와 부패한 유황 냄새",
                    noise="불길하게 울리는 수맥 물방울 소리",
                    oxygen_level=oxygen,
                    hazard_level=base_danger
                )

                strata_map = {1: "limestone", 2: "sandstone", 3: "basalt", 4: "granite", 5: "obsidian"}
                assigned_strata = strata_map.get(floor_num, "granite")
                assigned_floor = "weathered_rock" if idx % 2 == 1 else "solid_rock"

                room_loc = Location(
                    id=room_id,
                    name=r_name,
                    description=f"{dungeon_name_ko} 지하 {floor_num}층에 위치한 석조 공간입니다. 서늘한 냉기와 짙은 어둠이 깔려 있습니다.",
                    exits={},
                    terrain="mountains", # Rocky underground
                    location_category="dungeon",
                    dungeon_id=dungeon_id,
                    floor_depth=floor_num,
                    danger_level=base_danger,
                    monster_density=monster_dens,
                    npc_density=npc_dens,
                    rock_strata=assigned_strata,
                    floor_type=assigned_floor,
                    traits=["지하 던전", f"B{floor_num}F", r_type, f"암반: {assigned_strata}", "냉기", "밀실"]
                )

                # Connect exits linearly within the floor
                if prev_room_id:
                    room_loc.exits["back"] = prev_room_id
                    state.locations[prev_room_id].exits["forward"] = room_id

                # Floor transitions: entrance room links upward, final room links downward
                if idx == 0:
                    if floor_num == 1:
                        room_loc.exits["upstairs"] = surface_location_id
                        # Link surface entrance downward
                        surf_loc = state.locations.get(surface_location_id)
                        if surf_loc:
                            surf_loc.exits["dungeon_down"] = room_id
                    else:
                        prev_floor_last_room = f"{dungeon_id}_b{floor_num - 1}f_r4"
                        room_loc.exits["upstairs"] = prev_floor_last_room
                        if prev_floor_last_room in state.locations:
                            state.locations[prev_floor_last_room].exits["downstairs"] = room_id

                state.locations[room_id] = room_loc
                prev_room_id = room_id

                d_room = DungeonRoom(
                    room_id=room_id,
                    floor_num=floor_num,
                    room_type=r_type,
                    name_ko=r_name,
                    description=room_loc.description,
                    danger_level=base_danger,
                    monster_density=monster_dens,
                    npc_density=npc_dens,
                    oxygen_level=oxygen,
                    exits=dict(room_loc.exits),
                    traits=list(room_loc.traits)
                )
                floor.rooms[room_id] = d_room

                # Contextual trap deployment for corridors and crypts
                if r_type in ["corridor", "crypt_chamber", "armory"]:
                    TrapEngine.spawn_trap_for_location(state, room_id)

            instance.floors[floor_num] = floor

        if not hasattr(state, "dungeons"):
            state.dungeons = {}
        state.dungeons[dungeon_id] = instance

        return instance

    @classmethod
    def get_current_dungeon(cls, state: WorldState) -> Optional[DungeonInstance]:
        """Returns the active dungeon instance if the player is currently inside one."""
        curr_loc = state.locations.get(state.player.location)
        if not curr_loc or getattr(curr_loc, "location_category", "surface") != "dungeon":
            return None

        d_id = getattr(curr_loc, "dungeon_id", None)
        if d_id and hasattr(state, "dungeons"):
            return state.dungeons.get(d_id)
        return None

    @classmethod
    def descend_floor(cls, state: WorldState) -> Tuple[bool, str]:
        """
        Attempts to move player deeper into the dungeon (downstairs exit).
        """
        curr_loc = state.locations.get(state.player.location)
        if not curr_loc:
            return False, "현재 위치를 확인할 수 없습니다."

        down_exit = curr_loc.exits.get("downstairs") or curr_loc.exits.get("dungeon_down")
        if not down_exit:
            return False, "더 깊은 지하로 내려가는 계단이나 통로가 없습니다."

        target_loc = state.locations.get(down_exit)
        if not target_loc:
            return False, "지하 통로가 무너져 있어 이동할 수 없습니다."

        state.player.location = down_exit
        target_loc.visited = True
        return True, f"하강 계단을 밟고 어두운 지하 심층 [{target_loc.name}]에 발을 디뎠습니다."

    @classmethod
    def ascend_floor(cls, state: WorldState) -> Tuple[bool, str]:
        """
        Attempts to move player upwards (upstairs exit), potentially escaping to the surface.
        """
        curr_loc = state.locations.get(state.player.location)
        if not curr_loc:
            return False, "현재 위치를 확인할 수 없습니다."

        up_exit = curr_loc.exits.get("upstairs")
        if not up_exit:
            return False, "위층으로 올라가는 계단이나 통로가 없습니다."

        target_loc = state.locations.get(up_exit)
        if not target_loc:
            return False, "상층 통로를 찾을 수 없습니다."

        state.player.location = up_exit
        target_loc.visited = True

        if getattr(target_loc, "location_category", "surface") == "surface":
            return True, f"지하 던전의 숨 막히는 어둠을 뚫고 지상 [{target_loc.name}]으로 무사히 귀환했습니다!"
        return True, f"계단을 타고 위층 [{target_loc.name}]으로 올라왔습니다."
