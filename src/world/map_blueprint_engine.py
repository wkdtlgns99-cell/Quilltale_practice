"""
Deterministic 5-Tier 3D Elevation Map Blueprint Engine for Quilltale TRPG.
Compiles 6-tier infrastructure (Continents, Regions, Nations, Settlements, Facilities)
and 3D elevation relief (Z-axis heightmap) into:
1. Multi-scale LOD viewports (Macro Continent, Meso Regional Roads, Micro Settlement Facilities).
2. ASCII topographical relief preview with elevation contours.
3. Executable prompt for external AI (GPT / DALL-E 3) to generate precise maps.
4. Stable Diffusion 1.5 / LoRA positive and negative prompt tags.
5. Unity 2D-3D HD-2D scene graph specification (nodes, edges, heights).
"""
import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from src.world.state import WorldState


class MapZoomLevel(str, Enum):
    MACRO_CONTINENT = "macro_continent"              # 거시: 대륙 윤곽, 권역 바이옴, 국가 국경선
    MESO_REGION_ROADS = "meso_region_roads"          # 중시: 권역/국가 3D 지형, 도로망 경사도, 마을 핀
    MICRO_SETTLEMENT_FACILITIES = "micro_settlement" # 미시: 정주지 내 5계층 시설 3D 층수 및 조감도


TERRAIN_ELEVATION_DEFAULTS: dict[str, tuple[int, int]] = {
    "coastal": (0, 30),
    "ocean": (0, 10),
    "swamp": (20, 90),
    "plains": (80, 250),
    "forest": (120, 450),
    "hills": (350, 850),
    "mountains": (850, 2800),
    "desert": (150, 500),
    "tundra": (300, 1100),
    "volcanic": (1200, 3400),
}

FACILITY_ELEVATION_LABELS: dict[int, str] = {
    -2: "지하 2층 (심층 카타콤/하수도/비밀 던전)",
    -1: "지하 1층 (저장고/지하실/비밀 통로)",
    0: "지상 1층 (본관/홀/공방/가두 점포)",
    1: "지상 2층 (객실/거처/창고)",
    2: "지상 3층 (망루/옥상 테라스/발코니)",
    3: "최상층 (첨탑/마탑 관측실/신호대)",
}


@dataclass
class ElevationTopologyPoint:
    x_km: float
    y_km: float
    elevation_m: int
    terrain_type: str = "plains"
    slope_deg: float = 0.0
    symbol: str = "."
    traits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Map3DBlueprint:
    world_name: str
    zoom_level: MapZoomLevel
    target_id: str | None = None
    target_name: str | None = None
    bounds: tuple[float, float, float, float] = (0.0, 0.0, 100.0, 100.0) # (min_x, min_y, max_x, max_y)
    elevation_range_m: tuple[int, int] = (0, 1000)                        # (min_z, max_z)
    continents: list[dict[str, Any]] = field(default_factory=list)
    regions: list[dict[str, Any]] = field(default_factory=list)
    nations: list[dict[str, Any]] = field(default_factory=list)
    settlements_3d: list[dict[str, Any]] = field(default_factory=list)
    roads_3d: list[dict[str, Any]] = field(default_factory=list)
    facilities_3d: list[dict[str, Any]] = field(default_factory=list)
    ascii_relief_preview: str = ""
    gpt_executable_prompt: str = ""
    diffusion_tags: dict[str, str] = field(default_factory=dict)
    unity_hd2d_spec: dict[str, Any] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["zoom_level"] = self.zoom_level.value
        return d


class MapBlueprintEngine:
    """
    Deterministic 5-Tier 3D Elevation Blueprint & Prompt Assembly Engine.
    """

    @classmethod
    def generate_blueprint(
        cls,
        state: WorldState,
        zoom_level: MapZoomLevel = MapZoomLevel.MACRO_CONTINENT,
        target_id: str | None = None
    ) -> Map3DBlueprint:
        """
        Main entrypoint: Generates a complete 3D Map Blueprint based on current WorldState.
        """
        world_name = getattr(state, "world_name", "미지의 세계")
        infra = getattr(state, "infrastructure", None)

        blueprint = Map3DBlueprint(
            world_name=world_name,
            zoom_level=zoom_level,
            target_id=target_id,
            traits=["3D 지도 청사진", f"줌: {zoom_level.value}", f"세계: {world_name}"]
        )

        if not infra:
            cls._build_fallback_blueprint(state, blueprint)
            cls._finalize_blueprint_outputs(state, blueprint)
            return blueprint

        if zoom_level == MapZoomLevel.MACRO_CONTINENT:
            cls._build_macro_continent(state, infra, blueprint)
        elif zoom_level == MapZoomLevel.MESO_REGION_ROADS:
            cls._build_meso_region_roads(state, infra, blueprint, target_id)
        elif zoom_level == MapZoomLevel.MICRO_SETTLEMENT_FACILITIES:
            cls._build_micro_settlement_facilities(state, infra, blueprint, target_id)

        cls._finalize_blueprint_outputs(state, blueprint)
        return blueprint

    @classmethod
    def _get_effective_coords_and_elevation(
        cls,
        s: Any,
        idx: int = 0
    ) -> tuple[tuple[float, float], int]:
        """Calculates realistic procedural spatial coordinates and 3D elevation if unassigned."""
        coords = getattr(s, "coordinates", (0.0, 0.0))
        elev = getattr(s, "elevation_meters", 100)

        if not coords or coords == (0.0, 0.0):
            angle = idx * 2.39996
            radius = 16.0 + (idx * 11.5)
            coords = (round(50.0 + radius * math.cos(angle), 1), round(50.0 + radius * math.sin(angle), 1))

        if elev <= 100:
            s_type = getattr(s, "settlement_type", "village")
            type_elev = {
                "fishing_cove": 15,
                "coastal_port": 25,
                "underground_excavation": 70,
                "oasis_crossroad": 130,
                "farming_village": 180,
                "village": 210,
                "capital_metropolis": 280,
                "treetop_village": 390,
                "fortress_citadel": 680,
                "mining_camp": 940,
                "monastic_town": 1250,
                "volcanic_settlement": 1680,
            }
            elev = type_elev.get(s_type, 160 + ((idx * 97) % 550))

        return coords, elev

    @classmethod
    def _build_macro_continent(cls, state: WorldState, infra: Any, blueprint: Map3DBlueprint):
        """Macro View: Continents, Geographic Regions, Nations, and Major Hubs."""
        min_x, max_x = 0.0, 100.0
        min_y, max_y = 0.0, 100.0
        min_z, max_z = 0, 3000

        # Continents
        for c in infra.continents.values():
            blueprint.continents.append({
                "id": c.id,
                "name": c.name,
                "common_tongue": getattr(c, "continental_common_tongue", "공통어"),
                "tectonic_plates": getattr(c, "tectonic_plates", []),
                "weather_fronts": getattr(c, "weather_fronts", []),
                "area_sq_km": getattr(c, "area_sq_km", 1000000.0),
                "traits": list(getattr(c, "traits", []))
            })

        # Regions with estimated elevation ranges
        for r in infra.regions.values():
            terrain = getattr(r, "terrain_classification", "plains")
            z_range = TERRAIN_ELEVATION_DEFAULTS.get(terrain, (100, 500))
            blueprint.regions.append({
                "id": r.id,
                "name": r.name,
                "continent_id": getattr(r, "continent_id", ""),
                "terrain": terrain,
                "elevation_range_m": z_range,
                "climate": getattr(r, "climate_band", "온대"),
                "hazards": getattr(r, "environmental_hazards", []),
                "traits": list(getattr(r, "traits", []))
            })

        # Nations
        for n in infra.nations.values():
            blueprint.nations.append({
                "id": n.id,
                "name": n.name,
                "continent_id": getattr(n, "continent_id", ""),
                "capital_id": getattr(n, "capital_settlement_id", ""),
                "political_system": getattr(n, "political_system", "왕정"),
                "currency": getattr(n, "currency_name", "골드"),
                "tariff_rate": getattr(n, "tariff_rate", 0.1),
                "traits": list(getattr(n, "traits", []))
            })

        # Settlements with 3D coordinates
        x_coords, y_coords, z_coords = [], [], []
        for idx, s in enumerate(infra.settlements.values()):
            coords, elev = cls._get_effective_coords_and_elevation(s, idx)
            x_coords.append(coords[0])
            y_coords.append(coords[1])
            z_coords.append(elev)

            blueprint.settlements_3d.append({
                "id": s.id,
                "name": s.name,
                "nation_id": getattr(s, "nation_id", ""),
                "region_id": getattr(s, "region_id", ""),
                "settlement_type": getattr(s, "settlement_type", "village"),
                "x_km": coords[0],
                "y_km": coords[1],
                "elevation_m": elev,
                "population": getattr(s, "population", 1000),
                "wall_defense_tier": getattr(s, "wall_defense_tier", 1),
                "security_level": getattr(s, "security_level", 50),
                "traits": list(getattr(s, "traits", []))
            })

        if x_coords and y_coords:
            min_x, max_x = min(x_coords) - 10.0, max(x_coords) + 10.0
            min_y, max_y = min(y_coords) - 10.0, max(y_coords) + 10.0
        if z_coords:
            min_z, max_z = min(z_coords), max(z_coords)

        blueprint.bounds = (round(min_x, 1), round(min_y, 1), round(max_x, 1), round(max_y, 1))
        blueprint.elevation_range_m = (min_z, max_z)

        # Connect inter-settlement 3D roads
        cls._collect_roads_3d(infra, blueprint)

    @classmethod
    def _build_meso_region_roads(cls, state: WorldState, infra: Any, blueprint: Map3DBlueprint, target_id: str | None):
        """Meso View: Regional road network, slopes, elevation differences, and settlement hubs."""
        active_loc_id = state.player.location
        active_settlement = None

        if target_id and target_id in infra.settlements:
            active_settlement = infra.settlements[target_id]
        elif target_id and target_id in infra.nations:
            pass
        else:
            for s_id, s in infra.settlements.items():
                if active_loc_id == s_id or (hasattr(s, "facilities") and active_loc_id in s.facilities):
                    active_settlement = s
                    break

        target_nation_id = getattr(active_settlement, "nation_id", None) if active_settlement else None
        if not target_nation_id and infra.nations:
            target_nation_id = next(iter(infra.nations.keys()))

        target_nation = infra.nations.get(target_nation_id)
        blueprint.target_id = target_nation_id
        blueprint.target_name = target_nation.name if target_nation else "국경 지대"

        x_coords, y_coords, z_coords = [], [], []

        for idx, (s_id, s) in enumerate(infra.settlements.items()):
            if target_nation_id and getattr(s, "nation_id", "") != target_nation_id:
                continue

            coords, elev = cls._get_effective_coords_and_elevation(s, idx)
            x_coords.append(coords[0])
            y_coords.append(coords[1])
            z_coords.append(elev)

            blueprint.settlements_3d.append({
                "id": s.id,
                "name": s.name,
                "nation_id": getattr(s, "nation_id", ""),
                "region_id": getattr(s, "region_id", ""),
                "settlement_type": getattr(s, "settlement_type", "village"),
                "x_km": coords[0],
                "y_km": coords[1],
                "elevation_m": elev,
                "population": getattr(s, "population", 1000),
                "wall_defense_tier": getattr(s, "wall_defense_tier", 1),
                "is_current_player_base": (active_settlement and s.id == active_settlement.id),
                "traits": list(getattr(s, "traits", []))
            })

        if x_coords and y_coords:
            min_x, max_x = min(x_coords) - 5.0, max(x_coords) + 5.0
            min_y, max_y = min(y_coords) - 5.0, max(y_coords) + 5.0
        else:
            min_x, min_y, max_x, max_y = 0.0, 0.0, 100.0, 100.0
        min_z = min(z_coords) if z_coords else 0
        max_z = max(z_coords) if z_coords else 1000

        blueprint.bounds = (round(min_x, 1), round(min_y, 1), round(max_x, 1), round(max_y, 1))
        blueprint.elevation_range_m = (min_z, max_z)

        cls._collect_roads_3d(infra, blueprint, filter_nation_id=target_nation_id)

    @classmethod
    def _build_micro_settlement_facilities(cls, state: WorldState, infra: Any, blueprint: Map3DBlueprint, target_id: str | None):
        """Micro View: 3D Facilities inside a settlement with elevation tiers (-2 to +3)."""
        active_loc_id = state.player.location
        chosen_settlement = None

        if target_id and target_id in infra.settlements:
            chosen_settlement = infra.settlements[target_id]
        else:
            if active_loc_id in infra.settlements:
                chosen_settlement = infra.settlements[active_loc_id]
            elif active_loc_id in infra.facilities:
                fac = infra.facilities[active_loc_id]
                chosen_settlement = infra.settlements.get(fac.settlement_id)

            if not chosen_settlement and infra.settlements:
                chosen_settlement = next(iter(infra.settlements.values()))

        if not chosen_settlement:
            return

        blueprint.target_id = chosen_settlement.id
        blueprint.target_name = chosen_settlement.name
        base_elev = getattr(chosen_settlement, "elevation_meters", 100)
        blueprint.elevation_range_m = (base_elev - 20, base_elev + 50)

        fac_ids = getattr(chosen_settlement, "facilities", [])
        if not fac_ids:
            fac_ids = [fid for fid, f in infra.facilities.items() if getattr(f, "settlement_id", "") == chosen_settlement.id]

        for idx, fid in enumerate(fac_ids):
            f = infra.facilities.get(fid)
            if not f:
                continue

            elev_lvl = getattr(f, "elevation_level", 0)
            absolute_m = base_elev + (elev_lvl * 5)
            elev_label = FACILITY_ELEVATION_LABELS.get(elev_lvl, f"{elev_lvl}층")

            angle = (idx * (2 * math.pi / max(1, len(fac_ids))))
            radius_m = 30 + (idx % 3) * 25
            rel_x = round(radius_m * math.cos(angle), 1)
            rel_y = round(radius_m * math.sin(angle), 1)

            blueprint.facilities_3d.append({
                "id": f.id,
                "name": f.name,
                "category": getattr(f.category, "value", str(f.category)),
                "facility_type": getattr(f, "facility_type", "general_store"),
                "relative_coords_m": (rel_x, rel_y),
                "elevation_level": elev_lvl,
                "elevation_label": elev_label,
                "absolute_elevation_m": absolute_m,
                "npcs": list(getattr(f, "npcs", [])),
                "is_player_here": (active_loc_id == f.id),
                "traits": list(getattr(f, "traits", []))
            })

    @classmethod
    def _collect_roads_3d(cls, infra: Any, blueprint: Map3DBlueprint, filter_nation_id: str | None = None):
        """Calculates 3D road trajectories, distances, and elevation slopes."""
        visited_pairs = set()

        settlement_keys = list(infra.settlements.keys())
        settlement_idx_map = {s_id: idx for idx, s_id in enumerate(settlement_keys)}

        for s_id, s in infra.settlements.items():
            if filter_nation_id and getattr(s, "nation_id", "") != filter_nation_id:
                continue

            s_idx = settlement_idx_map.get(s_id, 0)
            origin_coords, origin_z = cls._get_effective_coords_and_elevation(s, s_idx)
            roads = getattr(s, "roads", {})

            for dest_id, r in roads.items():
                dest_s = infra.settlements.get(dest_id)
                if not dest_s:
                    continue
                if filter_nation_id and getattr(dest_s, "nation_id", "") != filter_nation_id:
                    continue

                pair_key = tuple(sorted([s_id, dest_id]))
                if pair_key in visited_pairs:
                    continue
                visited_pairs.add(pair_key)

                dest_idx = settlement_idx_map.get(dest_id, 0)
                dest_coords, dest_z = cls._get_effective_coords_and_elevation(dest_s, dest_idx)

                dist_km = getattr(r, "distance_km", 5.0)
                delta_z = dest_z - origin_z
                horizontal_dist_m = max(dist_km * 1000.0, 100.0)
                slope_deg = round(math.atan2(abs(delta_z), horizontal_dist_m) * (180.0 / math.pi), 1)

                r_type = getattr(r.road_type, "value", str(r.road_type)) if hasattr(r, "road_type") else "dirt_road"
                r_cat = getattr(r.route_category, "value", str(r.route_category)) if hasattr(r, "route_category") else "branch_road"

                blueprint.roads_3d.append({
                    "origin_id": s_id,
                    "origin_name": s.name,
                    "origin_3d": (origin_coords[0], origin_coords[1], origin_z),
                    "destination_id": dest_id,
                    "destination_name": dest_s.name,
                    "destination_3d": (dest_coords[0], dest_coords[1], dest_z),
                    "distance_km": dist_km,
                    "delta_elevation_m": delta_z,
                    "slope_degree": slope_deg,
                    "road_type": r_type,
                    "route_category": r_cat,
                    "hazard_level": getattr(r, "hazard_level", 20),
                    "toll_fee": getattr(r, "toll_fee", 0),
                    "traits": list(getattr(r, "traits", []))
                })

    @classmethod
    def _build_fallback_blueprint(cls, state: WorldState, blueprint: Map3DBlueprint):
        """Fallback builder for basic WorldState without full 6-tier infrastructure."""
        for idx, (loc_id, loc) in enumerate(state.locations.items()):
            coords = getattr(loc, "coordinates", (float(idx * 15), float((idx % 3) * 20)))
            elev = 100 + (idx * 50)
            blueprint.settlements_3d.append({
                "id": loc_id,
                "name": loc.name,
                "x_km": coords[0],
                "y_km": coords[1],
                "elevation_m": elev,
                "is_current_player_base": (state.player.location == loc_id),
                "traits": list(getattr(loc, "traits", []))
            })

    @classmethod
    def _finalize_blueprint_outputs(cls, state: WorldState, blueprint: Map3DBlueprint):
        """Assembles ASCII Relief Preview, GPT Executable Prompt, SD 1.5 Tags, and Unity Spec."""
        blueprint.ascii_relief_preview = cls._generate_ascii_relief(blueprint)
        blueprint.gpt_executable_prompt = cls._compile_gpt_prompt(state, blueprint)
        blueprint.diffusion_tags = cls._compile_sd_lora_tags(blueprint)
        blueprint.unity_hd2d_spec = cls._compile_unity_spec(blueprint)

    @classmethod
    def _generate_ascii_relief(cls, blueprint: Map3DBlueprint, grid_w: int = 42, grid_h: int = 14) -> str:
        """Generates an ASCII 3D relief contour map preview."""
        grid = [["·" for _ in range(grid_w)] for _ in range(grid_h)]
        min_x, min_y, max_x, max_y = blueprint.bounds
        dx = max(max_x - min_x, 1.0)
        dy = max(max_y - min_y, 1.0)

        for r in range(grid_h):
            for c in range(grid_w):
                elev_ratio = (r / grid_h)
                if elev_ratio > 0.8:
                    grid[r][c] = "≈"
                elif elev_ratio < 0.2:
                    grid[r][c] = "^"

        for rd in blueprint.roads_3d:
            x1, y1, _ = rd["origin_3d"]
            x2, y2, _ = rd["destination_3d"]
            c1 = int(((x1 - min_x) / dx) * (grid_w - 1))
            r1 = int(((y1 - min_y) / dy) * (grid_h - 1))
            c2 = int(((x2 - min_x) / dx) * (grid_w - 1))
            r2 = int(((y2 - min_y) / dy) * (grid_h - 1))
            mid_c = (c1 + c2) // 2
            mid_r = (r1 + r2) // 2
            if 0 <= mid_r < grid_h and 0 <= mid_c < grid_w:
                grid[mid_r][mid_c] = "="

        if blueprint.zoom_level == MapZoomLevel.MICRO_SETTLEMENT_FACILITIES:
            center_r, center_c = grid_h // 2, grid_w // 2
            grid[center_r][center_c] = "★"
            for fac in blueprint.facilities_3d:
                rel_x, rel_y = fac["relative_coords_m"]
                fc = max(0, min(grid_w - 1, center_c + int(rel_x // 15)))
                fr = max(0, min(grid_h - 1, center_r + int(rel_y // 15)))
                lvl = fac["elevation_level"]
                grid[fr][fc] = "▲" if lvl > 0 else ("▼" if lvl < 0 else "■")
        else:
            for s in blueprint.settlements_3d:
                c = max(0, min(grid_w - 1, int(((s["x_km"] - min_x) / dx) * (grid_w - 1))))
                r = max(0, min(grid_h - 1, int(((s["y_km"] - min_y) / dy) * (grid_h - 1))))
                grid[r][c] = "★" if s.get("is_current_player_base") else "●"

        header = f"=== [3D 등고선 지형 릴리프: {blueprint.world_name} ({blueprint.zoom_level.value})] ===\n"
        legend = "기호: ★ 플레이어/거점 | ● 마을 | ▲ 고지대/망루 | ▼ 지하/하수도 | = 도로망 | ^ 산맥 | ≈ 저지대/수계\n"
        elev_info = f"고도 범위: 해발 {blueprint.elevation_range_m[0]}m ~ {blueprint.elevation_range_m[1]}m\n"
        body = "\n".join("".join(row) for row in grid)
        return f"{header}{legend}{elev_info}\n{body}\n"

    @classmethod
    def _compile_gpt_prompt(cls, state: WorldState, blueprint: Map3DBlueprint) -> str:
        """
        Compiles an exhaustive, copy-pasteable prompt for ChatGPT / DALL-E / Claude
        to accurately draw the multi-scale fantasy map with 3D elevation.
        """
        prompt_lines = [
            f"# [MAP DRAWING SPECIFICATION & PROMPT] {blueprint.world_name}",
            "",
            "## 1. 역할 및 작화 지침 (Role & Visual Style)",
            "- 당신은 정밀 판타지 지도 제작자(Cartographer)이자 3D 건축 조감도 제도사입니다.",
            "- 아래 제공된 [수학적 3D 지형 및 인프라 좌표 팩트시트]를 100% 엄수하여 사실적이고 입체적인 판타지 지도를 작화하십시오.",
            "- **시각 양식**: 옥토패스 트래블러 풍 2D-3D HD-2D 또는 고전 양피지 지도(Vintage Cartography with Isometric 3D Relief Shading).",
            "- **고도 표현**: 해발 고도(Z-axis meters)에 따라 산맥의 융기, 협곡의 깊이, 등고선(Contour lines), 지형 그림자(Hillshading)를 입체적으로 렌더링하십시오.",
            "",
            f"## 2. 줌 레벨 스펙: {blueprint.zoom_level.value}",
            f"- 대상 영역: {blueprint.target_name or blueprint.world_name}",
            f"- 수평 좌표 범위: X [{blueprint.bounds[0]}km ~ {blueprint.bounds[2]}km], Y [{blueprint.bounds[1]}km ~ {blueprint.bounds[3]}km]",
            f"- 수직 고도 범위: Z 해발 [{blueprint.elevation_range_m[0]}m ~ {blueprint.elevation_range_m[1]}m]",
            ""
        ]

        if blueprint.zoom_level == MapZoomLevel.MACRO_CONTINENT:
            prompt_lines.append("## 3. 대륙 및 권역 거시 지형 배치 (Continents & Biomes)")
            for r in blueprint.regions:
                prompt_lines.append(f"- 권역 [{r['name']}]: 지형={r['terrain']}, 기후={r['climate']}, 고도범위={r['elevation_range_m'][0]}~{r['elevation_range_m'][1]}m, 특성={', '.join(r['traits'][:3])}")
            prompt_lines.append("\n## 4. 국가 국경 및 주요 거점 3D 좌표 (Nations & Capitals)")
            for n in blueprint.nations:
                prompt_lines.append(f"- 국가 [{n['name']}]: 정치={n['political_system']}, 관세율={int(n['tariff_rate']*100)}%, 화폐={n['currency']}")
            for s in blueprint.settlements_3d[:8]:
                prompt_lines.append(f"- 거점 [{s['name']}]: 좌표=({s['x_km']}km, {s['y_km']}km, 해발 {s['elevation_m']}m), 격={s['settlement_type']}, 인구={s['population']}")

        elif blueprint.zoom_level == MapZoomLevel.MESO_REGION_ROADS:
            prompt_lines.append(f"## 3. 국가/권역 [{blueprint.target_name}] 내부 정주지 3D 고도 배치 (Settlements)")
            for s in blueprint.settlements_3d:
                pin_mark = " (★ 플레이어 현재 위치)" if s.get("is_current_player_base") else ""
                wall_tier = s.get("wall_defense_tier", "기본 방벽")
                prompt_lines.append(f"- 마을 [{s['name']}]{pin_mark}: 좌표=({s['x_km']}km, {s['y_km']}km), 해발={s['elevation_m']}m, 성벽등급={wall_tier}")
            prompt_lines.append("\n## 4. 지형을 따라 굽이치는 3D 도로망 및 경사도 (Road Slopes & Hazards)")
            for rd in blueprint.roads_3d:
                prompt_lines.append(f"- 도로 [{rd['origin_name']} -> {rd['destination_name']}]: 유형={rd['road_type']}, 거리={rd['distance_km']}km, 고도차={rd['delta_elevation_m']}m, 경사각={rd['slope_degree']}도, 위험도={rd['hazard_level']}")

        elif blueprint.zoom_level == MapZoomLevel.MICRO_SETTLEMENT_FACILITIES:
            prompt_lines.append(f"## 3. 정주지 [{blueprint.target_name}] 내부 5계층 시설 입체 조감도 (Facility 3D Layers)")
            for f in blueprint.facilities_3d:
                pin_mark = " (★ 플레이어 위치)" if f.get("is_player_here") else ""
                prompt_lines.append(f"- 시설 [{f['name']}]{pin_mark}: 상대좌표=({f['relative_coords_m'][0]}m, {f['relative_coords_m'][1]}m), 층수={f['elevation_label']} (해발 {f['absolute_elevation_m']}m), 유형={f['facility_type']}, 상주NPC={', '.join(f['npcs']) if f['npcs'] else '주민'}")

        prompt_lines.append("\n## 5. DALL-E 3 전용 프롬프트 (Image Generation Prompt)")
        dalle_style = "isometric 3d topographical fantasy map" if blueprint.zoom_level != MapZoomLevel.MICRO_SETTLEMENT_FACILITIES else "isometric bird's-eye view 3d architectural layout"
        dalle_prompt = (
            f"masterpiece, {dalle_style}, {blueprint.world_name} fantasy realm, "
            f"detailed elevation relief shading, mountain ridges, winding travel roads, medieval settlements, "
            f"subtle contour lines, hand-drawn vintage cartography style, high dynamic range, crisp linework, parchment tone."
        )
        prompt_lines.append(f"`{dalle_prompt}`")

        prompt_lines.append("\n## 6. 작화 실행 요청")
        prompt_lines.append("위 좌표와 고도 팩트시트를 엄격히 준수하여 지도 렌더링 설명 및 완성형 DALL-E 이미지를 생성해 주십시오.")

        return "\n".join(prompt_lines)

    @classmethod
    def _compile_sd_lora_tags(cls, blueprint: Map3DBlueprint) -> dict[str, str]:
        """Compiles Stable Diffusion 1.5 / LoRA tag pairs."""
        zoom_tag = "continental overworld map" if blueprint.zoom_level == MapZoomLevel.MACRO_CONTINENT else ("regional highway elevation map" if blueprint.zoom_level == MapZoomLevel.MESO_REGION_ROADS else "isometric settlement town layout")
        positive = (
            f"masterpiece, best quality, (fantasy cartography:1.3), {zoom_tag}, (isometric 3d view:1.2), "
            f"elevation relief, shaded mountains, winding roads, medieval settlements, parchment texture, "
            f"topographical contour lines, sharp lineart, highly detailed, soft warm lighting"
        )
        negative = (
            "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, "
            "cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, modern"
        )
        return {
            "positive_prompt": positive,
            "negative_prompt": negative,
            "recommended_steps": "28",
            "cfg_scale": "7.5",
            "sampler": "DPM++ 2M Karras"
        }

    @classmethod
    def _compile_unity_spec(cls, blueprint: Map3DBlueprint) -> dict[str, Any]:
        """Compiles Unity 2D-3D HD-2D compatible JSON node-edge-elevation data."""
        return {
            "world_name": blueprint.world_name,
            "zoom_level": blueprint.zoom_level.value,
            "bounds": blueprint.bounds,
            "elevation_range_m": blueprint.elevation_range_m,
            "settlements": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "position": [s["x_km"], s["elevation_m"] * 0.01, s["y_km"]],
                    "type": s.get("settlement_type", "village")
                }
                for s in blueprint.settlements_3d
            ],
            "roads": [
                {
                    "origin": rd["origin_id"],
                    "destination": rd["destination_id"],
                    "road_type": rd["road_type"],
                    "slope_degree": rd["slope_degree"],
                    "distance_km": rd["distance_km"]
                }
                for rd in blueprint.roads_3d
            ],
            "facilities": [
                {
                    "id": f["id"],
                    "name": f["name"],
                    "local_position": [f["relative_coords_m"][0], f["elevation_level"] * 3.0, f["relative_coords_m"][1]],
                    "floor_level": f["elevation_level"]
                }
                for f in blueprint.facilities_3d
            ]
        }

    @classmethod
    def to_interactive_html(
        cls,
        state: WorldState,
        zoom_level: MapZoomLevel = MapZoomLevel.MACRO_CONTINENT
    ) -> str:
        """Convenience bridge to MapInteractiveRenderer."""
        from src.world.map_interactive_renderer import MapInteractiveRenderer
        blueprint = cls.generate_blueprint(state, zoom_level=zoom_level)
        return MapInteractiveRenderer.render_map_html(state, blueprint=blueprint)

