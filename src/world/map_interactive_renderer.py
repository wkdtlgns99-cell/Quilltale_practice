"""
Interactive 3D Overworld Map UI Renderer for Quilltale TRPG.
Transforms 5-tier infrastructure & 3D elevation map blueprints into
self-contained, interactive HTML/CSS/SVG/JS representations.

Adheres strictly to SYSTEM_RULES:
- Zero Business Logic in UI (Code_Hygiene Rule 6)
- Explicit UTF-8 handling
- traits: list[str] = field(default_factory=list) on dataclasses
- Fallback paths for missing images / external assets
"""
import base64
import html
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from src.world.map_blueprint_engine import Map3DBlueprint, MapBlueprintEngine, MapZoomLevel
from src.world.state import WorldState

logger = logging.getLogger(__name__)

# Archetype icon mapping for settlement pins
ARCHETYPE_ICONS: dict[str, str] = {
    "capital_metropolis": "🏰",
    "volcanic_settlement": "🌋",
    "monastic_town": "❄️",
    "fishing_cove": "⚓",
    "coastal_port": "⚓",
    "treetop_village": "🌳",
    "oasis_crossroad": "🏜️",
    "underground_excavation": "⛏️",
    "military_fortress": "🛡️",
    "mining_colony": "⛏️",
    "agricultural_hub": "🌾",
    "trade_hub": "⚖️",
    "magic_sanctuary": "🔮",
    "ruins": "🏚️",
    "village": "🏡",
    "town": "🏘️",
    "city": "🏛️",
}

# In-memory image cache to avoid repeated disk reads
_IMAGE_BASE64_CACHE: dict[str, str] = {}


@dataclass
class MapRenderOptions:
    """Configuration options for interactive map rendering."""
    show_roads: bool = True
    show_elevations: bool = True
    clamp_margin_pct: float = 8.0
    container_aspect_ratio: str = "16 / 9"
    traits: list[str] = field(default_factory=list)


class MapInteractiveRenderer:
    """
    Renders an interactive, responsive HTML/CSS/SVG map overlay for Quilltale TRPG.
    Runs 100% deterministically in Python without UI business logic.
    """

    @classmethod
    def get_image_data_uri(cls, image_path_str: str) -> str | None:
        """
        Loads and returns image as base64 data URI with caching.
        Returns None if file is not found or invalid.
        """
        if not image_path_str:
            return None

        if image_path_str in _IMAGE_BASE64_CACHE:
            return _IMAGE_BASE64_CACHE[image_path_str]

        path = Path(image_path_str)
        if not path.is_file():
            # Try resolving relative to repository root
            root_candidate = Path(__file__).resolve().parent.parent.parent / image_path_str
            if root_candidate.is_file():
                path = root_candidate
            else:
                return None

        try:
            raw_bytes = path.read_bytes()
            suffix = path.suffix.lower().lstrip(".")
            mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
            encoded = base64.b64encode(raw_bytes).decode("ascii")
            data_uri = f"data:image/{mime};base64,{encoded}"
            _IMAGE_BASE64_CACHE[image_path_str] = data_uri
            return data_uri
        except Exception as e:
            logger.warning(f"Failed to encode map image '{image_path_str}': {e}")
            return None

    @classmethod
    def normalize_coordinates(
        cls,
        x_km: float,
        y_km: float,
        bounds: tuple[float, float, float, float],
        margin_pct: float = 8.0
    ) -> tuple[float, float]:
        """
        Normalizes world km coordinates (x_km, y_km) into container percentage coordinates (left_pct, top_pct).
        Inverts Y-axis so northern/positive coordinates appear higher (lower top_pct).
        Clamps coordinates between margin_pct and 100 - margin_pct.
        """
        min_x, min_y, max_x, max_y = bounds
        span_x = max(max_x - min_x, 1.0)
        span_y = max(max_y - min_y, 1.0)

        norm_x = (x_km - min_x) / span_x
        norm_y = (y_km - min_y) / span_y

        usable_range = 100.0 - (margin_pct * 2.0)
        left_pct = margin_pct + (norm_x * usable_range)
        top_pct = margin_pct + ((1.0 - norm_y) * usable_range)

        # Clamping
        left_pct = max(margin_pct, min(100.0 - margin_pct, left_pct))
        top_pct = max(margin_pct, min(100.0 - margin_pct, top_pct))

        return round(left_pct, 2), round(top_pct, 2)

    @classmethod
    def _determine_player_settlement(cls, state: WorldState) -> str:
        """Determines which settlement ID the player is currently in or nearest to."""
        player_loc_id = getattr(state.player, "location", "")
        infra = getattr(state, "infrastructure", None)
        if not infra or not getattr(infra, "settlements", None):
            return player_loc_id

        # 1. Direct match in settlements
        if player_loc_id in infra.settlements:
            return player_loc_id

        # 2. Match through facilities
        if player_loc_id in infra.facilities:
            fac = infra.facilities[player_loc_id]
            s_id = getattr(fac, "settlement_id", "")
            if s_id and s_id in infra.settlements:
                return s_id

        # 3. Match by settlement facility list
        for s_id, s in infra.settlements.items():
            fac_list = getattr(s, "facilities", [])
            if player_loc_id in fac_list:
                return s_id

        # 4. Match via Location exits if loc exists
        loc = state.locations.get(player_loc_id) if hasattr(state, "locations") else None
        if loc and hasattr(loc, "exits") and isinstance(loc.exits, dict):
            for exit_id in loc.exits.values():
                if exit_id in infra.settlements:
                    return exit_id
                if exit_id in infra.facilities:
                    s_id = getattr(infra.facilities[exit_id], "settlement_id", "")
                    if s_id and s_id in infra.settlements:
                        return s_id

        # 5. Fallback: default to the first settlement
        return next(iter(infra.settlements.keys()))

    @classmethod
    def render_map_html(
        cls,
        state: WorldState,
        blueprint: Map3DBlueprint | None = None,
        options: MapRenderOptions | None = None
    ) -> str:
        """
        Compiles an interactive 3D map HTML widget with SVG road overlays and clickable pins.
        """
        if options is None:
            options = MapRenderOptions()

        if blueprint is None:
            blueprint = MapBlueprintEngine.generate_blueprint(
                state,
                zoom_level=MapZoomLevel.MACRO_CONTINENT
            )

        active_image_path = getattr(state, "active_map_image", "data/maps/default_overworld.jpg")
        image_data_uri = cls.get_image_data_uri(active_image_path)

        bounds = blueprint.bounds
        settlements = blueprint.settlements_3d
        roads = blueprint.roads_3d
        infra = getattr(state, "infrastructure", None)

        player_settlement_id = cls._determine_player_settlement(state)

        # Build coordinate lookup for settlements
        settlement_coords: dict[str, tuple[float, float]] = {}
        for s in settlements:
            s_id = s.get("id", "")
            x = float(s.get("x_km", 0.0))
            y = float(s.get("y_km", 0.0))
            left_p, top_p = cls.normalize_coordinates(x, y, bounds, options.clamp_margin_pct)
            settlement_coords[s_id] = (left_p, top_p)

        # 1. Build SVG Road Lines
        svg_lines = []
        if options.show_roads and roads:
            for r in roads:
                orig_id = r.get("origin_id", "")
                dest_id = r.get("destination_id", "")
                if orig_id in settlement_coords and dest_id in settlement_coords:
                    x1, y1 = settlement_coords[orig_id]
                    x2, y2 = settlement_coords[dest_id]
                    dist_km = r.get("distance_km", 0.0)
                    slope = r.get("slope_deg", 0.0)
                    orig_name = r.get("origin_name", orig_id)
                    dest_name = r.get("destination_name", dest_id)
                    tooltip = f"{orig_name} ↔ {dest_name} ({dist_km}km, 경사 {slope}°)"
                    line_html = (
                        f'<line x1="{x1}%" y1="{y1}%" x2="{x2}%" y2="{y2}%" '
                        f'stroke="rgba(218, 165, 32, 0.65)" stroke-width="2.5" '
                        f'stroke-dasharray="6,4" stroke-linecap="round">'
                        f'<title>{html.escape(tooltip)}</title>'
                        f'</line>'
                    )
                    svg_lines.append(line_html)

        svg_overlay_html = ""
        if svg_lines:
            svg_overlay_html = (
                f'<svg class="qt-map-svg" style="position: absolute; top:0; left:0; width:100%; height:100%; '
                f'pointer-events: none; z-index: 5;">'
                f'{"".join(svg_lines)}'
                f'</svg>'
            )

        # 2. Build Interactive Pins
        pins_html = []
        for s in settlements:
            s_id = s.get("id", "")
            s_name = s.get("name", "미지의 거점")
            s_type = s.get("settlement_type", "village")
            elev_m = s.get("elevation_m", 100)
            pop = s.get("population", 500)
            sec = s.get("security_level", 50)
            wall = s.get("wall_defense_tier", 1)
            is_player = (s_id == player_settlement_id) or s.get("is_current_player_base", False)

            # Archetype icon
            icon = ARCHETYPE_ICONS.get(s_type, "🏛️")

            # Nation / Region name
            nation_name = "미지"
            region_name = "미개척지"
            if infra:
                n_id = s.get("nation_id", "")
                if n_id and n_id in infra.nations:
                    nation_name = infra.nations[n_id].name
                r_id = s.get("region_id", "")
                if r_id and r_id in infra.regions:
                    region_name = infra.regions[r_id].name

            # Facility names
            facility_names = []
            if infra and s_id in infra.settlements:
                orig_s = infra.settlements[s_id]
                for f_id in getattr(orig_s, "facilities", []):
                    if f_id in infra.facilities:
                        facility_names.append(infra.facilities[f_id].name)

            # Connected road descriptions
            road_descs = []
            for r in roads:
                if r.get("origin_id") == s_id:
                    road_descs.append(f"{r.get('destination_name')} ({r.get('distance_km')}km)")
                elif r.get("destination_id") == s_id:
                    road_descs.append(f"{r.get('origin_name')} ({r.get('distance_km')}km)")

            left_p, top_p = settlement_coords.get(s_id, (50.0, 50.0))

            pin_info = {
                "id": s_id,
                "name": s_name,
                "icon": icon,
                "archetype": s_type,
                "elevation_m": elev_m,
                "population": pop,
                "security": sec,
                "wall_tier": wall,
                "nation": nation_name,
                "region": region_name,
                "is_player": is_player,
                "facilities": facility_names[:6],
                "roads": road_descs[:4],
            }
            json_payload = html.escape(json.dumps(pin_info, ensure_ascii=False), quote=True)

            pin_classes = "qt-map-pin" + (" qt-player-pin" if is_player else "")
            badge_html = '<span class="qt-pin-badge">★ 현재 위치</span>' if is_player else ""

            pin_elem = (
                f'<div class="{pin_classes}" style="left: {left_p}%; top: {top_p}%;" '
                f'data-info="{json_payload}" onclick="qtSelectMapPin(this)">'
                f'<div class="qt-pin-icon-wrap">'
                f'<div class="qt-pin-icon">{icon}</div>'
                f'{badge_html}'
                f'</div>'
                f'<div class="qt-pin-label">{html.escape(s_name)} ({elev_m}m)</div>'
                f'</div>'
            )
            pins_html.append(pin_elem)

        # Background styling
        if image_data_uri:
            bg_style = (
                f'background-image: url("{image_data_uri}"); '
                f'background-size: cover; background-position: center; background-repeat: no-repeat;'
            )
        else:
            bg_style = (
                'background: radial-gradient(ellipse at center, #241c14 0%, #110d0a 100%); '
                'background-size: 100% 100%;'
            )

        html_out = f"""
<div class="qt-interactive-map-wrapper">
  <style>
    .qt-interactive-map-wrapper {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #ded1c1;
      user-select: none;
    }}
    .qt-map-viewport {{
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      min-height: 420px;
      border: 1px solid #5a4832;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.8), 0 4px 15px rgba(0, 0, 0, 0.5);
      {bg_style}
    }}
    .qt-map-grid-overlay {{
      position: absolute;
      top: 0; left: 0; width: 100%; height: 100%;
      background-image: linear-gradient(rgba(218, 165, 32, 0.05) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(218, 165, 32, 0.05) 1px, transparent 1px);
      background-size: 8% 8%;
      pointer-events: none;
      z-index: 2;
    }}
    .qt-map-header-badge {{
      position: absolute;
      top: 10px;
      left: 12px;
      background: rgba(18, 14, 11, 0.85);
      border: 1px solid #7c6244;
      border-radius: 4px;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 600;
      color: #e8d8b8;
      letter-spacing: 0.5px;
      z-index: 20;
      box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }}
    .qt-map-pin {{
      position: absolute;
      transform: translate(-50%, -50%);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275), z-index 0.2s;
      z-index: 10;
    }}
    .qt-map-pin:hover {{
      transform: translate(-50%, -60%) scale(1.18);
      z-index: 50;
    }}
    .qt-pin-icon-wrap {{
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .qt-pin-icon {{
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: rgba(26, 20, 15, 0.92);
      border: 2px solid #d4af37;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.7);
    }}
    .qt-pin-badge {{
      position: absolute;
      top: -16px;
      background: #b8860b;
      color: #fff;
      font-size: 9px;
      font-weight: bold;
      padding: 1px 5px;
      border-radius: 3px;
      white-space: nowrap;
      box-shadow: 0 1px 4px rgba(0,0,0,0.5);
      letter-spacing: 0.3px;
    }}
    .qt-player-pin .qt-pin-icon {{
      border-color: #ffd700;
      background: rgba(55, 30, 12, 0.95);
      box-shadow: 0 0 14px 4px rgba(255, 215, 0, 0.85);
      animation: qt-map-pulse 2s infinite;
    }}
    @keyframes qt-map-pulse {{
      0% {{ box-shadow: 0 0 6px 2px rgba(255, 215, 0, 0.6); }}
      50% {{ box-shadow: 0 0 20px 7px rgba(255, 140, 0, 0.9); }}
      100% {{ box-shadow: 0 0 6px 2px rgba(255, 215, 0, 0.6); }}
    }}
    .qt-pin-label {{
      font-size: 11px;
      font-weight: 500;
      color: #f0e6d6;
      background: rgba(18, 14, 11, 0.9);
      padding: 2px 7px;
      border-radius: 4px;
      margin-top: 4px;
      white-space: nowrap;
      border: 1px solid #5d4934;
      box-shadow: 0 2px 6px rgba(0,0,0,0.6);
      pointer-events: none;
    }}
    .qt-map-inspector {{
      margin-top: 10px;
      padding: 12px 16px;
      background: rgba(22, 17, 13, 0.96);
      border: 1px solid #6b533b;
      border-radius: 6px;
      box-shadow: 0 3px 12px rgba(0, 0, 0, 0.4);
    }}
    .qt-inspector-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #4a3a29;
      padding-bottom: 8px;
      margin-bottom: 8px;
    }}
    .qt-inspector-title {{
      font-size: 14px;
      font-weight: 700;
      color: #ffd700;
    }}
    .qt-inspector-elev {{
      font-size: 12px;
      background: #33261a;
      color: #d6b885;
      padding: 2px 8px;
      border-radius: 4px;
      border: 1px solid #5a432e;
    }}
    .qt-insp-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 6px 12px;
      font-size: 12px;
      color: #c9bcac;
      margin-bottom: 8px;
    }}
    .qt-insp-facs, .qt-insp-roads {{
      font-size: 12px;
      color: #b8a896;
      margin-top: 4px;
      line-height: 1.5;
    }}
    .qt-fast-travel-btn {{
      background: linear-gradient(180deg, #47321e 0%, #2f2113 100%);
      color: #ffd700;
      border: 1px solid #8c6c44;
      border-radius: 4px;
      padding: 6px 14px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-top: 8px;
    }}
    .qt-fast-travel-btn:hover {{
      background: linear-gradient(180deg, #5e4328 0%, #3e2b19 100%);
      border-color: #ffd700;
      box-shadow: 0 0 10px rgba(255, 215, 0, 0.4);
    }}
  </style>

  <div class="qt-map-viewport">
    <div class="qt-map-grid-overlay"></div>
    <div class="qt-map-header-badge">🗺️ 오버월드 지형 청사진 ({html.escape(blueprint.world_name or '대륙 지형')})</div>
    {svg_overlay_html}
    {"".join(pins_html)}
  </div>

  <div id="qt-map-inspector" class="qt-map-inspector">
    <div class="qt-inspector-header">
      <span id="qt-inspector-name" class="qt-inspector-title">거점을 선택하세요</span>
      <span id="qt-inspector-elev" class="qt-inspector-elev">고도 정보</span>
    </div>
    <div id="qt-inspector-body">
      지도의 거점 핀(Pin)을 클릭하면 3D 고도, 소속 국가, 인구, 주요 5계층 시설 및 도로망 연결 상태를 탐색할 수 있습니다.
    </div>
    <div id="qt-inspector-actions" style="display: none;">
      <button class="qt-fast-travel-btn" onclick="qtDeclareMapTravel()">📍 이곳으로 이동 선언</button>
    </div>
  </div>

  <script>
    function qtSelectMapPin(el) {{
      try {{
        var data = JSON.parse(el.getAttribute('data-info'));
        var nameEl = document.getElementById('qt-inspector-name');
        var elevEl = document.getElementById('qt-inspector-elev');
        var bodyEl = document.getElementById('qt-inspector-body');
        var actEl = document.getElementById('qt-inspector-actions');

        if (nameEl) nameEl.innerText = (data.icon || '📍') + ' ' + (data.name || '미지의 거점');
        if (elevEl) elevEl.innerText = '해발 ' + (data.elevation_m || 0) + 'm (Z축 고도)';

        var html = '<div class="qt-insp-grid">'
          + '<div><b>소속:</b> ' + (data.nation || '미소속') + ' · ' + (data.region || '미개척') + '</div>'
          + '<div><b>인구:</b> ' + Number(data.population || 0).toLocaleString() + '명</div>'
          + '<div><b>치안도:</b> ' + (data.security || 50) + ' / 100</div>'
          + '<div><b>방벽 등급:</b> ' + (data.wall_tier || 1) + '급 방벽</div>'
          + '</div>';

        if (data.facilities && data.facilities.length > 0) {{
          html += '<div class="qt-insp-facs"><b>주요 5계층 시설:</b> ' + data.facilities.join(', ') + '</div>';
        }}
        if (data.roads && data.roads.length > 0) {{
          html += '<div class="qt-insp-roads"><b>연결 도로망:</b> ' + data.roads.join(' | ') + '</div>';
        }}

        if (bodyEl) bodyEl.innerHTML = html;
        if (actEl) {{
          actEl.style.display = 'block';
          window.__qtSelectedMapSettlement = data.name;
        }}
      }} catch(err) {{
        console.error('Failed to parse map pin data:', err);
      }}
    }}

    function qtDeclareMapTravel() {{
      var target = window.__qtSelectedMapSettlement || '';
      if (!target) return;
      var actionBox = document.querySelector('.qt-action-box textarea') || document.querySelector('.qt-action-box input');
      if (actionBox) {{
        actionBox.value = target + '(으)로 이동한다';
        actionBox.dispatchEvent(new Event('input', {{ bubbles: true }}));
        actionBox.focus();
      }}
    }}
  </script>
</div>
"""
        return html_out.strip()
