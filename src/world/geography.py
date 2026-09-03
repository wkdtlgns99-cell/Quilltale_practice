"""
Deterministic Geography and Road Network Engine for Quilltale TRPG.
Provides:
1. 5 Core Road Types with terrain speed multipliers and ambush hazard ratings.
2. RoadConnection metadata between Locations (distance in km, road type, hazard).
3. Dijkstra shortest travel-time and distance pathfinding.
4. Realistic travel duration based on travel mode (foot, pack mule, carriage, horse, courier relay).
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import heapq
import logging

logger = logging.getLogger(__name__)


class RoadType(str, Enum):
    PAVED_HIGHWAY = "paved_highway"    # 왕도 포장 가도: 1.25x speed, high security, low ambush
    DIRT_ROAD = "dirt_road"            # 일반 비포장 흙길: 1.0x speed (standard)
    MOUNTAIN_PASS = "mountain_pass"    # 험한 산악 고갯길: 0.5x speed (takes 2x longer), rockfall risk
    SWAMP_TRAIL = "swamp_trail"        # 수렁/늪지 수로: 0.35x speed (takes ~3x longer), disease/hazard
    DENSE_FOREST = "dense_forest"      # 울창한 숲길: 0.65x speed, ambush/beast risk


ROAD_SPEED_MULTIPLIERS: Dict[RoadType, float] = {
    RoadType.PAVED_HIGHWAY: 1.25,
    RoadType.DIRT_ROAD: 1.00,
    RoadType.MOUNTAIN_PASS: 0.50,
    RoadType.SWAMP_TRAIL: 0.35,
    RoadType.DENSE_FOREST: 0.65,
}

ROAD_HAZARD_BASE: Dict[RoadType, int] = {
    RoadType.PAVED_HIGHWAY: 5,
    RoadType.DIRT_ROAD: 20,
    RoadType.MOUNTAIN_PASS: 45,
    RoadType.SWAMP_TRAIL: 60,
    RoadType.DENSE_FOREST: 50,
}

# Base speeds in km/h
TRAVEL_MODE_SPEEDS: Dict[str, float] = {
    "foot": 4.0,           # 기본 도보 (4 km/h)
    "pack_mule": 3.5,      # 짐 노새/보따리상 (3.5 km/h)
    "carriage": 10.0,      # 마차 (10 km/h)
    "horse": 16.0,         # 승마 속보 (16 km/h)
    "courier": 25.0,       # 급보 전령 릴레이 (25 km/h)
    "magical_beacon": 200.0 # 마법 봉화/통신 (200 km/h)
}


@dataclass
class RoadConnection:
    destination_id: str
    distance_km: float = 5.0
    road_type: RoadType = RoadType.DIRT_ROAD
    speed_multiplier: float = 1.0
    hazard_level: int = 20
    toll_fee: int = 0
    road_name_ko: str = "비포장 흙길"

    def __post_init__(self):
        if self.speed_multiplier == 1.0 and self.road_type in ROAD_SPEED_MULTIPLIERS:
            self.speed_multiplier = ROAD_SPEED_MULTIPLIERS[self.road_type]
        if self.hazard_level == 20 and self.road_type in ROAD_HAZARD_BASE:
            self.hazard_level = ROAD_HAZARD_BASE[self.road_type]


class GeographyEngine:
    @classmethod
    def get_road(cls, state: Any, origin_id: str, dest_id: str) -> Optional[RoadConnection]:
        """Returns the road connection between origin and destination, or creates a default one if exits exist."""
        if origin_id not in state.locations or dest_id not in state.locations:
            return None

        origin_loc = state.locations[origin_id]
        if hasattr(origin_loc, "roads") and dest_id in origin_loc.roads:
            return origin_loc.roads[dest_id]

        # Fallback: if destination is in exits, construct a deterministic default road
        is_connected = False
        if hasattr(origin_loc, "exits"):
            for direction, target in origin_loc.exits.items():
                if target == dest_id:
                    is_connected = True
                    break

        if is_connected:
            default_road = RoadConnection(
                destination_id=dest_id,
                distance_km=5.0,
                road_type=RoadType.DIRT_ROAD,
                road_name_ko="일반 도로"
            )
            return default_road
        return None

    @classmethod
    def calculate_segment_travel_hours(
        cls,
        distance_km: float,
        road_type: RoadType = RoadType.DIRT_ROAD,
        travel_mode: str = "foot"
    ) -> float:
        """Calculates travel hours for a single road segment."""
        base_speed = TRAVEL_MODE_SPEEDS.get(travel_mode, 4.0)
        speed_mult = ROAD_SPEED_MULTIPLIERS.get(road_type, 1.0)
        effective_speed = max(0.5, base_speed * speed_mult)
        return distance_km / effective_speed

    @classmethod
    def dijkstra_shortest_travel(
        cls,
        state: Any,
        origin_id: str,
        dest_id: str,
        travel_mode: str = "foot"
    ) -> Tuple[float, float, List[str]]:
        """
        Calculates shortest travel time using Dijkstra's algorithm over the road network.
        Returns (total_travel_hours, total_distance_km, path_location_ids).
        If unreachable, returns (float('inf'), float('inf'), []).
        """
        if origin_id == dest_id:
            return 0.0, 0.0, [origin_id]

        if origin_id not in state.locations or dest_id not in state.locations:
            return float('inf'), float('inf'), []

        # Priority queue stores: (total_hours, total_km, current_loc_id, path)
        pq: List[Tuple[float, float, str, List[str]]] = [(0.0, 0.0, origin_id, [origin_id])]
        visited: Dict[str, float] = {}

        while pq:
            hours, km, curr_id, path = heapq.heappop(pq)

            if curr_id == dest_id:
                return hours, km, path

            if curr_id in visited and visited[curr_id] <= hours:
                continue
            visited[curr_id] = hours

            curr_loc = state.locations.get(curr_id)
            if not curr_loc:
                continue

            # Gather all neighbors through roads or exits
            neighbors: Dict[str, RoadConnection] = {}
            if hasattr(curr_loc, "roads") and curr_loc.roads:
                for target_id, r_conn in curr_loc.roads.items():
                    if target_id in state.locations:
                        neighbors[target_id] = r_conn

            if hasattr(curr_loc, "exits") and curr_loc.exits:
                for direction, target_id in curr_loc.exits.items():
                    if target_id in state.locations and target_id not in neighbors:
                        neighbors[target_id] = RoadConnection(
                            destination_id=target_id,
                            distance_km=5.0,
                            road_type=RoadType.DIRT_ROAD
                        )

            for next_id, road in neighbors.items():
                segment_hours = cls.calculate_segment_travel_hours(
                    road.distance_km, road.road_type, travel_mode
                )
                new_hours = hours + segment_hours
                new_km = km + road.distance_km
                if next_id not in visited or new_hours < visited[next_id]:
                    heapq.heappush(pq, (new_hours, new_km, next_id, path + [next_id]))

        return float('inf'), float('inf'), []

    @classmethod
    def get_all_reachable_locations_with_distances(
        cls,
        state: Any,
        origin_id: str,
        travel_mode: str = "courier"
    ) -> Dict[str, Tuple[float, float, int]]:
        """
        Returns a dict of all reachable locations from origin:
        dest_loc_id -> (travel_hours, distance_km, hop_count)
        """
        reachable: Dict[str, Tuple[float, float, int]] = {origin_id: (0.0, 0.0, 0)}
        if origin_id not in state.locations:
            return reachable

        pq: List[Tuple[float, float, int, str]] = [(0.0, 0.0, 0, origin_id)]
        visited: Dict[str, float] = {}

        while pq:
            hours, km, hops, curr_id = heapq.heappop(pq)
            if curr_id in visited and visited[curr_id] <= hours:
                continue
            visited[curr_id] = hours
            reachable[curr_id] = (hours, km, hops)

            curr_loc = state.locations.get(curr_id)
            if not curr_loc:
                continue

            neighbors: Dict[str, RoadConnection] = {}
            if hasattr(curr_loc, "roads") and curr_loc.roads:
                for target_id, r_conn in curr_loc.roads.items():
                    if target_id in state.locations:
                        neighbors[target_id] = r_conn
            if hasattr(curr_loc, "exits") and curr_loc.exits:
                for _, target_id in curr_loc.exits.items():
                    if target_id in state.locations and target_id not in neighbors:
                        neighbors[target_id] = RoadConnection(
                            destination_id=target_id,
                            distance_km=5.0,
                            road_type=RoadType.DIRT_ROAD
                        )

            for next_id, road in neighbors.items():
                segment_hours = cls.calculate_segment_travel_hours(
                    road.distance_km, road.road_type, travel_mode
                )
                new_hours = hours + segment_hours
                new_km = km + road.distance_km
                if next_id not in visited or new_hours < visited[next_id]:
                    heapq.heappush(pq, (new_hours, new_km, hops + 1, next_id))

        return reachable
