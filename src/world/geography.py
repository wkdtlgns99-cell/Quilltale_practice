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


class RoadCondition(str, Enum):
    NORMAL = "normal"                  # 정상 상태
    MUDDY = "muddy"                    # 진흙탕 (폭우 시 비포장 도로)
    FLOODED = "flooded"                # 침수 범람 (폭우 시 수렁길/강변)
    FROZEN_ICE = "frozen_ice"          # 살얼음 빙판길 (폭설/혹한 산길)
    SNOW_DRIFT = "snow_drift"          # 적설/눈길 (폭설 시 일반 도로)
    SANDSTORM = "sandstorm"            # 모래폭풍 (사막/황무지)
    HEAT_HAZE = "heat_haze"            # 아지랑이/폭염 (극심한 더위)


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

ROAD_CONDITION_EFFECTS: Dict[RoadCondition, Dict[str, Any]] = {
    RoadCondition.NORMAL: {
        "name_ko": "정상 도로",
        "speed_mult": 1.0,
        "hazard_bonus": 0,
        "fatigue_bonus": 0,
        "description_ko": "통행에 지장이 없는 온전한 노면 상태입니다."
    },
    RoadCondition.MUDDY: {
        "name_ko": "진흙탕 길",
        "speed_mult": 0.55,
        "hazard_bonus": 15,
        "fatigue_bonus": 1,
        "description_ko": "폭우로 노면이 곤죽처럼 진흙탕이 되어 발이 푹푹 빠지고 마차 바퀴가 헛돕니다."
    },
    RoadCondition.FLOODED: {
        "name_ko": "침수 범람로",
        "speed_mult": 0.30,
        "hazard_bonus": 35,
        "fatigue_bonus": 2,
        "description_ko": "불어난 물로 길이 완전히 물에 잠겨 통행이 극도로 위험하고 지체됩니다."
    },
    RoadCondition.FROZEN_ICE: {
        "name_ko": "살얼음 빙판길",
        "speed_mult": 0.35,
        "hazard_bonus": 40,
        "fatigue_bonus": 1,
        "description_ko": "노면이 빙판으로 얼어붙어 발을 헛디디면 천길 낭떠러지로 추락할 위험이 도사립니다."
    },
    RoadCondition.SNOW_DRIFT: {
        "name_ko": "눈 덮인 길",
        "speed_mult": 0.60,
        "hazard_bonus": 20,
        "fatigue_bonus": 1,
        "description_ko": "발목까지 쌓인 눈더미로 인해 전진하는 데 큰 힘이 소모됩니다."
    },
    RoadCondition.SANDSTORM: {
        "name_ko": "모래바람길",
        "speed_mult": 0.40,
        "hazard_bonus": 30,
        "fatigue_bonus": 2,
        "description_ko": "거센 모래바람으로 시야가 차단되고 호흡이 곤란해집니다."
    },
    RoadCondition.HEAT_HAZE: {
        "name_ko": "아지랑이 열풍로",
        "speed_mult": 0.85,
        "hazard_bonus": 10,
        "fatigue_bonus": 2,
        "description_ko": "살인적인 지열과 아지랑이로 갈증과 탈수가 급격히 가속됩니다."
    }
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


class RouteCategory(str, Enum):
    TRUNK_HIGHWAY = "trunk_highway"        # 간선 도로 (왕도/가도): 대도시 간을 잇는 정규 도로망
    BRANCH_ROAD = "branch_road"            # 지선 도로 (상업로/샛길): 지역 간 물류 이동로
    BOTTLENECK_PASS = "bottleneck_pass"    # 병목 지점 (관문/협곡/국경): 통행세, 검문, 방어 거점
    SUPPLY_WAYSTATION = "supply_waystation" # 보급 지점 (역참/여관/오아시스): 숙박 및 식수 보급소


@dataclass
class RoadConnection:
    destination_id: str
    distance_km: float = 5.0
    road_type: RoadType = RoadType.DIRT_ROAD
    speed_multiplier: float = 1.0
    hazard_level: int = 20
    toll_fee: int = 0
    road_name_ko: str = "비포장 흙길"
    route_category: RouteCategory = RouteCategory.BRANCH_ROAD
    is_bottleneck: bool = False
    bottleneck_type: str = ""                                  # 병목 유형 (예: "관문", "협곡", "국경")
    supply_facilities: List[str] = field(default_factory=list) # 보급 시설 (예: ["역참", "여관", "식수원"])
    allowed_transit_types: List[str] = field(default_factory=list) # 통행 허용 운송수단 범주
    traits: List[str] = field(default_factory=list)            # 도로 연결 요약 특성 태그 (예: ["진흙탕길", "야간 기습 빈발", "협곡 매복지"])

    def __post_init__(self):
        if isinstance(self.route_category, str):
            try:
                self.route_category = RouteCategory(self.route_category)
            except ValueError:
                self.route_category = RouteCategory.BRANCH_ROAD
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
    def get_effective_road_condition(
        cls,
        road: RoadConnection,
        environment: Any = None
    ) -> Dict[str, Any]:
        """
        Determines the dynamic road condition based on current environmental metrics (weather, temperature).
        Returns a dict containing condition metadata, effective speed multiplier, hazard, and narrative warning.
        """
        if not environment:
            base_eff = ROAD_CONDITION_EFFECTS[RoadCondition.NORMAL]
            return {
                "condition": RoadCondition.NORMAL,
                "name_ko": base_eff["name_ko"],
                "description_ko": base_eff["description_ko"],
                "speed_multiplier": road.speed_multiplier,
                "hazard_level": road.hazard_level,
                "fatigue_bonus": 0,
                "warning_ko": ""
            }

        weather = getattr(environment, "weather", "맑음").lower()
        temp = getattr(environment, "temperature_celsius", 20)

        cond = RoadCondition.NORMAL
        warning = ""

        # 1. Rain / Storm / Downpour
        if any(w in weather for w in ["폭우", "호우", "장대비", "비"]):
            if road.road_type == RoadType.SWAMP_TRAIL:
                cond = RoadCondition.FLOODED
                warning = "폭우로 인해 수렁길이 완전히 침수되어 무릎까지 흙탕물이 차올랐습니다."
            elif road.road_type in [RoadType.DIRT_ROAD, RoadType.DENSE_FOREST]:
                cond = RoadCondition.MUDDY
                warning = "폭우로 인해 흙길이 진흙탕으로 변해 발이 푹푹 빠집니다."
            elif road.road_type == RoadType.MOUNTAIN_PASS:
                cond = RoadCondition.MUDDY
                warning = "비바람으로 산비탈이 미끄러워지고 낙석 위험이 증가했습니다."
            else:
                cond = RoadCondition.NORMAL

        # 2. Snow / Blizzard / Freezing cold
        elif any(w in weather for w in ["폭설", "눈보라", "대설", "눈"]) or temp <= 0:
            if road.road_type == RoadType.MOUNTAIN_PASS:
                cond = RoadCondition.FROZEN_ICE
                warning = "혹한과 눈보라로 산길 노면이 살얼음 빙판으로 얼어붙었습니다."
            else:
                cond = RoadCondition.SNOW_DRIFT
                warning = "도로 위에 눈이 두껍게 쌓여 발걸음이 무겁게 지체됩니다."

        # 3. Sandstorm / Dust
        elif any(w in weather for w in ["모래폭풍", "황사", "열풍"]):
            cond = RoadCondition.SANDSTORM
            warning = "거센 모래바람이 길을 덮쳐 시야가 가로막히고 이동이 고통스럽습니다."

        # 4. Extreme Heat
        elif temp >= 35 or "폭염" in weather:
            cond = RoadCondition.HEAT_HAZE
            warning = "지열로 피어오르는 아지랑이와 살인적인 열기로 피로가 극심합니다."

        eff = ROAD_CONDITION_EFFECTS[cond]
        combined_speed_mult = road.speed_multiplier * eff["speed_mult"]
        combined_hazard = road.hazard_level + eff["hazard_bonus"]

        return {
            "condition": cond,
            "name_ko": eff["name_ko"],
            "description_ko": eff["description_ko"],
            "speed_multiplier": combined_speed_mult,
            "hazard_level": combined_hazard,
            "fatigue_bonus": eff["fatigue_bonus"],
            "warning_ko": warning
        }

    @classmethod
    def calculate_segment_travel_hours(
        cls,
        distance_km: float,
        road_type: RoadType = RoadType.DIRT_ROAD,
        travel_mode: str = "foot",
        condition_speed_mult: float = 1.0
    ) -> float:
        """Calculates travel hours for a single road segment with condition modifier."""
        base_speed = TRAVEL_MODE_SPEEDS.get(travel_mode, 4.0)
        speed_mult = ROAD_SPEED_MULTIPLIERS.get(road_type, 1.0)
        effective_speed = max(0.2, base_speed * speed_mult * condition_speed_mult)
        return distance_km / effective_speed

    @classmethod
    def dijkstra_shortest_travel(
        cls,
        state: Any,
        origin_id: str,
        dest_id: str,
        travel_mode: str = "foot",
        environment: Any = None
    ) -> Tuple[float, float, List[str]]:
        """
        Calculates shortest travel time using Dijkstra's algorithm over the road network,
        factoring in dynamic environmental road conditions (rain/mud, ice, snow, etc.).
        Returns (total_travel_hours, total_distance_km, path_location_ids).
        If unreachable, returns (float('inf'), float('inf'), []).
        """
        if origin_id == dest_id:
            return 0.0, 0.0, [origin_id]

        if origin_id not in state.locations or dest_id not in state.locations:
            return float('inf'), float('inf'), []

        env = environment if environment is not None else getattr(state, "environment", None)

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
                cond_info = cls.get_effective_road_condition(road, env)
                cond_speed = ROAD_CONDITION_EFFECTS.get(cond_info["condition"], {}).get("speed_mult", 1.0)
                segment_hours = cls.calculate_segment_travel_hours(
                    road.distance_km, road.road_type, travel_mode, condition_speed_mult=cond_speed
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
        travel_mode: str = "courier",
        environment: Any = None
    ) -> Dict[str, Tuple[float, float, int]]:
        """
        Returns a dict of all reachable locations from origin:
        dest_loc_id -> (travel_hours, distance_km, hop_count)
        """
        reachable: Dict[str, Tuple[float, float, int]] = {origin_id: (0.0, 0.0, 0)}
        if origin_id not in state.locations:
            return reachable

        env = environment if environment is not None else getattr(state, "environment", None)

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
                cond_info = cls.get_effective_road_condition(road, env)
                cond_speed = ROAD_CONDITION_EFFECTS.get(cond_info["condition"], {}).get("speed_mult", 1.0)
                segment_hours = cls.calculate_segment_travel_hours(
                    road.distance_km, road.road_type, travel_mode, condition_speed_mult=cond_speed
                )
                new_hours = hours + segment_hours
                new_km = km + road.distance_km
                if next_id not in visited or new_hours < visited[next_id]:
                    heapq.heappush(pq, (new_hours, new_km, hops + 1, next_id))

        return reachable
