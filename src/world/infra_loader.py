"""
Infrastructure Template Loader & Procedural Assembler for Quilltale TRPG.
Loads and adapts static JSON templates (cosmology, continent, region, nation, settlement, facility)
and binds living entities (NPCs, shops, quests, monsters, training) into the 6-tier infrastructure.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
import logging
import math
import random

from src.core.config import TEMPLATES_DIR
from src.world.geography import RoadConnection, RouteCategory, RoadType

from .infra_models import (
    InterTierRoute,
    AttireHierarchyProfile,
    CuisineProfile,
    CulturalNormsProfile,
    Continent,
    Region,
    Nation,
    FacilityCategory,
    FacilityType,
    Facility,
    Settlement,
    _safe_profile,
)

if TYPE_CHECKING:
    from .infrastructure import InfrastructureRegistry

logger = logging.getLogger(__name__)

# =====================================================================
# Infrastructure Template Loader Pipeline (Levels 0 ~ 2)
# =====================================================================
class InfrastructureTemplateLoader:
    """
    Loader and adapter pipeline connecting static JSON templates (cosmology, continent, region)
    to Quilltale 6-tier infrastructure data classes (WorldState, Continent, Region).
    """

    CATEGORY_TERRAIN_MAP: Dict[str, str] = {
        "magical_wasteland": "magical_anomaly",
        "arcane_void": "magical_anomaly",
        "arcane_sanctum": "magical_anomaly",
        "rune_crater": "magical_anomaly",
        "spatial_anomaly": "magical_anomaly",
        "temporal_zone": "magical_anomaly",
        "dream_realm": "magical_anomaly",
        "dream_space": "magical_anomaly",
        "emotion_realm": "magical_anomaly",
        "crystal_forest": "magical_anomaly",
        "floating_islands": "magical_anomaly",
        "meteor_crater": "magical_anomaly",
        "enchanted_meadow": "magical_anomaly",
        "snow_plateau": "frozen_tundra",
        "ice_cave": "frozen_tundra",
        "glacial_fjord": "frozen_tundra",
        "aurora_valley": "frozen_tundra",
        "poison_swamp": "swamp_marsh",
        "poison_crypt": "swamp_marsh",
        "poison_wasteland": "swamp_marsh",
        "canyon_spore": "swamp_marsh",
        "mangrove_delta": "swamp_marsh",
        "dark_moor": "swamp_marsh",
        "fungal_gorge": "swamp_marsh",
        "mirror_marsh": "swamp_marsh",
        "high_altitude_marsh": "swamp_marsh",
        "dense_jungle": "dense_forest",
        "ancient_rainforest": "dense_forest",
        "bamboo_forest": "dense_forest",
        "corrupted_forest": "dense_forest",
        "ironwood_forest": "dense_forest",
        "perpetual_twilight_forest": "dense_forest",
        "boreal_forest": "dense_forest",
        "grassland_forest": "plains",
        "storm_steppe": "plains",
        "perpetual_bloom_valley": "plains",
        "blood_red_riverlands": "plains",
        "river_basin": "plains",
        "mountain_pass": "mountain_mine",
        "canyon_badlands": "mountain_mine",
        "fossil_valley": "mountain_mine",
        "misty_highland": "mountain_mine",
        "mesa_plateau": "mountain_mine",
        "volcanic": "volcanic",
        "sulfur_springs": "volcanic",
        "ash_wasteland": "volcanic",
        "ocean": "coastal_port",
        "mystic_lake_basin": "coastal_port",
        "sunken_coast": "coastal_port",
        "tidal_cliffs": "coastal_port",
        "obsidian_coast": "coastal_port",
        "salt_flat": "desert_wasteland",
        "glass_desert": "desert_wasteland",
        "singing_dunes": "desert_wasteland",
        "crystal_caverns": "underground_abyss",
        "hollow_mountain": "underground_abyss",
        "giant_sinkhole": "underground_abyss",
    }

    TERRAIN_PRICE_MULTIPLIERS: Dict[str, Dict[str, float]] = {
        "magical_anomaly": {"crystal": 0.4, "water": 2.5, "food": 2.0, "mana_potion": 0.5, "ore": 1.5},
        "frozen_tundra": {"fur": 0.4, "ice": 0.2, "firewood": 3.0, "food": 2.5, "salt": 1.8},
        "swamp_marsh": {"herbs": 0.4, "poison": 0.3, "clean_water": 3.0, "salt": 2.0, "iron": 1.8},
        "dense_forest": {"timber": 0.3, "herbs": 0.4, "fur": 0.6, "metal": 2.0, "salt": 1.5},
        "mountain_mine": {"ore": 0.4, "iron": 0.5, "gems": 0.6, "food": 2.0, "timber": 1.8},
        "volcanic": {"obsidian": 0.3, "sulfur": 0.2, "metal": 0.5, "water": 4.0, "food": 3.0},
        "coastal_port": {"fish": 0.3, "salt": 0.4, "pearl": 0.5, "timber": 1.5, "ore": 1.6},
        "desert_wasteland": {"water": 4.0, "salt": 0.6, "ice": 5.0, "fur": 0.5, "silk": 1.5},
        "underground_abyss": {"gems": 0.4, "mushrooms": 0.3, "iron": 0.6, "food": 3.5, "cloth": 3.0},
        "plains": {"grain": 0.5, "horses": 0.5, "meat": 0.6, "iron": 1.5, "gems": 2.0},
    }

    @classmethod
    def load_continent_templates(cls, filepath: Optional[Path | str] = None) -> Dict[str, Continent]:
        """Loads and instantiates all Continent dataclass objects from continent_templates.json."""
        target_path = Path(filepath) if filepath else (TEMPLATES_DIR / "continent_templates.json")
        if not target_path.exists():
            logger.warning(f"Continent templates file not found: {target_path}")
            return {}

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        continents: Dict[str, Continent] = {}
        for item in data:
            if isinstance(item, dict) and "id" in item:
                cont = Continent.from_dict(item)
                continents[cont.id] = cont
        return continents

    @classmethod
    def adapt_region_template_to_region(cls, reg_dict: dict, continent_id: str = "") -> Region:
        """
        Transforms a raw region template from region_templates.json into a rich Level 2 Region dataclass.
        Augments missing price multipliers, climate, surface, and traits.
        """
        reg_id = reg_dict.get("id", f"region_{random.randint(1000, 9999)}")
        name = reg_dict.get("name", "미지의 권역")
        category = reg_dict.get("category", "")
        raw_terrain = reg_dict.get("terrain", "")
        if raw_terrain in cls.TERRAIN_PRICE_MULTIPLIERS:
            terrain = raw_terrain
        elif raw_terrain in cls.CATEGORY_TERRAIN_MAP:
            terrain = cls.CATEGORY_TERRAIN_MAP[raw_terrain]
        elif category in cls.CATEGORY_TERRAIN_MAP:
            terrain = cls.CATEGORY_TERRAIN_MAP[category]
        elif category in cls.TERRAIN_PRICE_MULTIPLIERS:
            terrain = category
        else:
            terrain = "plains"

        # Atmospheric description synthesis
        desc_raw = reg_dict.get("description", "")
        if isinstance(desc_raw, dict):
            v = desc_raw.get("visual", "")
            a = desc_raw.get("auditory", "")
            o = desc_raw.get("olfactory", "")
            description = f"{v} {a} {o}".strip()
        else:
            description = str(desc_raw)

        # Climate and temperature range
        if category in ["snow_plateau", "ice_cave", "glacial_fjord"]:
            climate_type = "혹한대"
            temp_range = (-35, 5)
            dominant_surface = "ice_sheet"
            mana_density = 35
        elif category in ["volcanic"]:
            climate_type = "건조 열대"
            temp_range = (15, 52)
            dominant_surface = "cracked_stone"
            mana_density = 70
        elif category in ["dense_jungle", "poison_swamp", "canyon_spore"]:
            climate_type = "열대 습윤"
            temp_range = (18, 38)
            dominant_surface = "deep_mud"
            mana_density = 55
        elif category in ["magical_wasteland", "arcane_void", "arcane_sanctum", "crystal_forest", "spatial_anomaly", "temporal_zone", "dream_realm", "dream_space", "emotion_realm", "rune_crater"]:
            climate_type = "비전 이상대"
            temp_range = (-10, 35)
            dominant_surface = "loose_sand"
            mana_density = 85
        elif category in ["ocean"]:
            climate_type = "해양성 온대"
            temp_range = (5, 30)
            dominant_surface = "deep_mud"
            mana_density = 50
        else:
            climate_type = "온대"
            temp_range = (-5, 28)
            dominant_surface = "dirt"
            mana_density = 50

        # Override with explicit values if present
        if reg_dict.get("climate_type"):
            climate_type = reg_dict["climate_type"]
        if reg_dict.get("dominant_surface"):
            dominant_surface = reg_dict["dominant_surface"]
        if "mana_density" in reg_dict:
            mana_density = reg_dict["mana_density"]
        if "seasonal_temperature_range" in reg_dict:
            temp_range = tuple(reg_dict["seasonal_temperature_range"])

        # Price multipliers
        multipliers = dict(reg_dict.get("natural_price_multipliers", {}))
        if not multipliers:
            multipliers = dict(cls.TERRAIN_PRICE_MULTIPLIERS.get(terrain, cls.TERRAIN_PRICE_MULTIPLIERS.get("plains", {})))

        # Hazards & Monsters
        hazards = []
        if "survival_hazards" in reg_dict and isinstance(reg_dict["survival_hazards"], list):
            hazards.extend(reg_dict["survival_hazards"])
        for h in reg_dict.get("environmental_hazards", []):
            if isinstance(h, dict) and "hazard_name" in h:
                hazards.append(h["hazard_name"])
            elif isinstance(h, str):
                hazards.append(h)
        for w in reg_dict.get("weather_events", []):
            if isinstance(w, dict) and "event_name" in w:
                hazards.append(w["event_name"])

        # Sub-dictionary extractors
        eco = reg_dict.get("ecology", {}) if isinstance(reg_dict.get("ecology"), dict) else {}
        lm_ruins = reg_dict.get("landmarks_and_ruins", {}) if isinstance(reg_dict.get("landmarks_and_ruins"), dict) else {}
        res = reg_dict.get("resources", {}) if isinstance(reg_dict.get("resources"), dict) else {}
        life = reg_dict.get("lifestyle_and_culture", {}) if isinstance(reg_dict.get("lifestyle_and_culture"), dict) else {}

        factions_enc = reg_dict.get("factions_and_encounters", {})
        monsters = list(factions_enc.get("common_monsters", [])) if isinstance(factions_enc, dict) else []
        if not monsters and "monsters" in reg_dict:
            monsters = list(reg_dict["monsters"])
        if not monsters and "common_monsters" in reg_dict:
            monsters = list(reg_dict["common_monsters"])
        if not monsters and "common_monsters" in eco:
            monsters = list(eco["common_monsters"])

        apex_predator = reg_dict.get("apex_predator_id") or eco.get("apex_predator_id", "")
        regional_champ = reg_dict.get("regional_champion_npc_id") or eco.get("regional_champion_npc_id", "")
        nomadic = list(reg_dict.get("nomadic_tribes") or eco.get("nomadic_tribes", []))

        # Visibility parsing
        vis_meters = 50
        vis_stealth = reg_dict.get("visibility_and_stealth", {})
        if isinstance(vis_stealth, dict) and "visibility_range" in vis_stealth:
            vis_str = vis_stealth["visibility_range"]
            digits = "".join(filter(str.isdigit, vis_str.split("m")[0]))
            if digits:
                try:
                    vis_meters = int(digits)
                except ValueError:
                    vis_meters = 50
        elif "visibility_meters" in reg_dict:
            vis_meters = reg_dict["visibility_meters"]

        # Landmarks as natural wonders
        landmarks = []
        for lm in reg_dict.get("landmarks", []):
            if isinstance(lm, dict) and "name" in lm:
                landmarks.append(lm["name"])
            elif isinstance(lm, str):
                landmarks.append(lm)
        if not landmarks and "natural_wonders" in reg_dict:
            landmarks = list(reg_dict["natural_wonders"])
        if not landmarks and "natural_wonders" in lm_ruins:
            landmarks = list(lm_ruins["natural_wonders"])

        arch_sites = list(reg_dict.get("archaeological_sites") or lm_ruins.get("archaeological_sites", []))
        pl_rifts = list(reg_dict.get("planar_rifts") or lm_ruins.get("planar_rifts", []))
        nat_shelters = list(reg_dict.get("natural_shelters") or lm_ruins.get("natural_shelters", []))

        # Rare mineral deposits & biological resources
        rare_minerals = []
        if "rare_mineral_deposits" in reg_dict and reg_dict["rare_mineral_deposits"]:
            rare_minerals = list(reg_dict["rare_mineral_deposits"])
        elif "rare_mineral_deposits" in res and res["rare_mineral_deposits"]:
            rare_minerals = list(res["rare_mineral_deposits"])
        elif terrain == "magical_anomaly":
            rare_minerals = ["심층 마나 수정맥", "비전 유리석"]
        elif terrain == "frozen_tundra":
            rare_minerals = ["만년빙정", "청빙 철광석"]
        elif terrain == "volcanic":
            rare_minerals = ["불꽃 심장석", "흑요석 원석"]
        elif terrain == "mountain_mine":
            rare_minerals = ["오리하르콘 광맥", "고순도 철광맥"]
        elif terrain == "swamp_marsh":
            rare_minerals = ["독안개 유황석", "부패 저항 진균"]
        else:
            rare_minerals = ["천연 광맥"]

        specs = reg_dict.get("specialties") or res.get("specialties") or landmarks or [f"{name} 고유 특산물"]
        endemic_bio = list(reg_dict.get("endemic_biological_resources") or res.get("endemic_biological_resources", []))
        tr_node = reg_dict.get("trade_node_name") or res.get("trade_node_name", "")

        # Culture / Cuisine / Attire mapping
        cuisine_dict = reg_dict.get("cuisine") or life.get("cuisine", {})
        if isinstance(cuisine_dict, dict) and ("staple_food" in cuisine_dict or "delicacy" in cuisine_dict):
            staples = [cuisine_dict["staple_food"]] if cuisine_dict.get("staple_food") else []
            delicacies = [cuisine_dict["delicacy"]] if cuisine_dict.get("delicacy") else []
            taboos = cuisine_dict.get("taboo_food", "")
            cuisine_obj = CuisineProfile(
                staples=staples,
                proteins_and_salts=delicacies,
                expedition_rations=[f"금기: {taboos}"] if taboos else [],
                beverages_and_water=[]
            )
        else:
            cuisine_obj = _safe_profile(CuisineProfile, cuisine_dict)

        attire_dict = reg_dict.get("attire") or life.get("attire", {})
        if isinstance(attire_dict, dict) and ("daily_wear" in attire_dict or "extreme_weather_gear" in attire_dict):
            daily = [attire_dict["daily_wear"]] if attire_dict.get("daily_wear") else []
            extreme = [attire_dict["extreme_weather_gear"]] if attire_dict.get("extreme_weather_gear") else []
            attire_obj = AttireHierarchyProfile(
                labor_lower_class=daily,
                middle_practical_class=[],
                upper_ruling_class=extreme
            )
        else:
            attire_obj = _safe_profile(AttireHierarchyProfile, attire_dict)

        cult_dict = reg_dict.get("culture") or life.get("culture", {})
        if isinstance(cult_dict, dict) and ("animism_and_faith" in cult_dict or "regional_taboo" in cult_dict):
            faith = [cult_dict["animism_and_faith"]] if cult_dict.get("animism_and_faith") else []
            taboo = [cult_dict["regional_taboo"]] if cult_dict.get("regional_taboo") else []
            culture_obj = CulturalNormsProfile(
                faith_and_beliefs=faith,
                commercial_customs=taboo,
                social_structure=[],
                seasonal_events=[]
            )
        else:
            culture_obj = _safe_profile(CulturalNormsProfile, cult_dict)

        # Traits assembly
        traits = list(reg_dict.get("traits", []))
        if not traits:
            traits = [name, terrain, climate_type]
            if hazards:
                traits.append(hazards[0])
            if landmarks:
                traits.append(landmarks[0])

        target_continent_id = continent_id or reg_dict.get("continent_id", "")

        return Region(
            id=reg_id,
            name=name,
            continent_id=target_continent_id,
            terrain=terrain,
            climate_type=climate_type,
            natural_price_multipliers=multipliers,
            survival_hazards=hazards,
            visibility_meters=vis_meters,
            noise_occlusion=reg_dict.get("noise_occlusion", 70 if terrain in ["dense_forest", "underground_abyss", "swamp_marsh"] else 40),
            common_monsters=monsters,
            specialties=specs,
            natural_hazards=reg_dict.get("natural_hazards") or hazards[:2],
            strategic_deposits=reg_dict.get("strategic_deposits") or ["야생 자원 채집지"],
            rare_mineral_deposits=rare_minerals,
            endemic_biological_resources=endemic_bio,
            natural_wonders=landmarks,
            archaeological_sites=arch_sites,
            planar_rifts=pl_rifts,
            natural_shelters=nat_shelters,
            mana_density=mana_density,
            apex_predator_id=apex_predator,
            regional_champion_npc_id=regional_champ,
            seasonal_temperature_range=temp_range,
            campsite_viability=reg_dict.get("campsite_viability", 50),
            foraging_abundance=reg_dict.get("foraging_abundance", 50),
            water_source_reliability=reg_dict.get("water_source_reliability", 70),
            environmental_toxicity=reg_dict.get("environmental_toxicity", 0),
            draconic_presence_level=reg_dict.get("draconic_presence_level", 0),
            dominant_elemental_affinity=reg_dict.get("dominant_elemental_affinity", "neutral"),
            dominant_surface=dominant_surface,
            nomadic_tribes=nomadic,
            trade_node_name=tr_node,
            cuisine=cuisine_obj,
            attire=attire_obj,
            culture=culture_obj,
            traits=traits,
            description=description,
        )

    @classmethod
    def load_region_templates(cls, filepath: Optional[Path | str] = None, continent_id: str = "") -> Dict[str, Region]:
        """Loads and adapts all Region dataclass objects from region_templates.json."""
        target_path = Path(filepath) if filepath else (TEMPLATES_DIR / "region_templates.json")
        if not target_path.exists():
            logger.warning(f"Region templates file not found: {target_path}")
            return {}

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        regions: Dict[str, Region] = {}
        for item in data:
            if isinstance(item, dict) and "id" in item:
                reg = cls.adapt_region_template_to_region(item, continent_id=continent_id)
                regions[reg.id] = reg
        return regions

    @classmethod
    def load_settlement_templates(cls, filepath: Optional[Path | str] = None, nation_id: str = "", region_id: str = "") -> Dict[str, Settlement]:
        """Loads all Settlement dataclass objects from settlement_templates.json."""
        target_path = Path(filepath) if filepath else (TEMPLATES_DIR / "settlement_templates.json")
        if not target_path.exists():
            logger.warning(f"Settlement templates file not found: {target_path}")
            return {}

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        settlements: Dict[str, Settlement] = {}
        for item in data:
            if isinstance(item, dict) and "id" in item:
                s_dict = dict(item)
                if nation_id:
                    s_dict["nation_id"] = nation_id
                if region_id:
                    s_dict["region_id"] = region_id
                st = Settlement.from_dict(s_dict)
                settlements[st.id] = st
        return settlements

    @classmethod
    def load_nation_templates(cls, filepath: Optional[Path | str] = None, continent_id: str = "") -> Dict[str, Nation]:
        """Loads all Nation dataclass objects from nation_templates.json."""
        target_path = Path(filepath) if filepath else (TEMPLATES_DIR / "nation_templates.json")
        if not target_path.exists():
            logger.warning(f"Nation templates file not found: {target_path}")
            return {}

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        nations: Dict[str, Nation] = {}
        for item in data:
            if isinstance(item, dict) and "id" in item:
                n_dict = dict(item)
                if continent_id:
                    n_dict["continent_id"] = continent_id
                nat = Nation.from_dict(n_dict)
                nations[nat.id] = nat
        return nations

    @classmethod
    def load_facility_templates(cls, filepath: Optional[Path | str] = None) -> Dict[str, Facility]:
        """Loads all Facility archetype dataclass objects from facility_templates.json."""
        target_path = Path(filepath) if filepath else (TEMPLATES_DIR / "facility_templates.json")
        if not target_path.exists():
            logger.warning(f"Facility templates file not found: {target_path}")
            return {}

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        facilities: Dict[str, Facility] = {}
        for item in data:
            if isinstance(item, dict) and "id" in item:
                fac = Facility.from_dict(item)
                facilities[fac.id] = fac
        return facilities

    @classmethod
    def inject_cosmology_to_world_state(cls, world_state: Any, cosmo_dict: dict) -> None:
        """Injects Level 0 cosmological laws, era, and pantheon into WorldState."""
        world_state.world_name = cosmo_dict.get("world_name", getattr(world_state, "world_name", ""))
        world_state.world_genre = cosmo_dict.get("genre", getattr(world_state, "world_genre", ""))
        world_state.civilization_era = cosmo_dict.get("era_background", "")[:250]
        world_state.epoch_state = "안정기"

        cosmo = cosmo_dict.get("cosmology", {})
        if isinstance(cosmo, dict):
            sun_moons = cosmo.get("sun_and_moons", "")
            if sun_moons and not getattr(world_state, "pantheon_deities", []):
                world_state.pantheon_deities = [sun_moons[:50]]
            divine = cosmo.get("divine_order", "")
            if divine and not getattr(world_state, "founded_religions", []):
                world_state.founded_religions = [divine[:50]]

        macro_threat = cosmo_dict.get("macro_threat", "")
        if macro_threat:
            world_state.global_apocalyptic_threat = macro_threat[:100]
            world_state.world_threat_level = 30
            world_state.world_crisis_active_stage = 1

        genre = cosmo_dict.get("genre", "정통 판타지")
        traits = [genre, "신성 조약", "마나 지맥 순환"]
        if macro_threat:
            traits.append("거시적 위협 도래")
        world_state.world_traits = traits

        world_state.cosmology_template = cosmo_dict
        world_state.world_lore = cosmo_dict

        from src.world.stat_engine import StatEngine
        detected_preset = StatEngine.detect_preset_for_world(cosmo_dict, getattr(world_state, "world_genre", ""))
        world_state.power_scale_preset_id = detected_preset.id

    @classmethod
    def assemble_world_upper_layers(
        cls,
        world_state: Any,
        cosmo_id: Optional[str] = None,
        continent_id: Optional[str] = None,
        region_ids: Optional[List[str]] = None,
        registry: Optional[InfrastructureRegistry] = None,
    ) -> InfrastructureRegistry:
        """
        End-to-end integration:
        Assembles Level 0 (WorldState) + Level 1 (Continent) + Level 2 (Region),
        registers into InfrastructureRegistry with bi-directional links,
        and executes recalculate_totals().
        """
        if registry is None:
            reg = getattr(world_state, "infrastructure", None)
            if reg is None:
                from .infrastructure import InfrastructureRegistry
                reg = InfrastructureRegistry()
        else:
            reg = registry

        # 1. Level 0: Load & inject cosmology
        cosmo_path = TEMPLATES_DIR / "cosmology_templates.json"
        cosmo_pool = []
        if cosmo_path.exists():
            with open(cosmo_path, "r", encoding="utf-8") as f:
                cosmo_pool = json.load(f)

        chosen_cosmo = None
        if cosmo_id and cosmo_pool:
            chosen_cosmo = next((c for c in cosmo_pool if c.get("id") == cosmo_id), None)
        if not chosen_cosmo and cosmo_pool:
            chosen_cosmo = cosmo_pool[0]

        if chosen_cosmo:
            cls.inject_cosmology_to_world_state(world_state, chosen_cosmo)

        # 2. Level 1: Load & select continent
        continents = cls.load_continent_templates()
        chosen_cont: Optional[Continent] = None
        if continent_id and continent_id in continents:
            chosen_cont = continents[continent_id]
        elif continents:
            # Match by compatible_genres with world_genre if possible
            target_genre = getattr(world_state, "world_genre", "")
            for c in continents.values():
                if any(target_genre in cg or cg in target_genre for cg in c.compatible_genres):
                    chosen_cont = c
                    break
            if not chosen_cont:
                chosen_cont = next(iter(continents.values()))

        if chosen_cont:
            reg.register_continent(chosen_cont)

        # 3. Level 2: Load & attach regions
        cont_id_str = chosen_cont.id if chosen_cont else ""
        all_regions = cls.load_region_templates(continent_id=cont_id_str)

        selected_regions: List[Region] = []
        if region_ids:
            for rid in region_ids:
                if rid in all_regions:
                    selected_regions.append(all_regions[rid])
        elif chosen_cont and chosen_cont.suggested_regions:
            # Match by suggested regions (id, terrain, or substring match)
            for sr in chosen_cont.suggested_regions:
                sr_norm = sr.lower()
                for r in all_regions.values():
                    if r.id == sr or r.terrain == sr or sr_norm in r.name.lower():
                        if r not in selected_regions:
                            selected_regions.append(r)
                            break
            # If not enough, fill up to 4
            if len(selected_regions) < 4:
                for r in all_regions.values():
                    if r not in selected_regions:
                        selected_regions.append(r)
                    if len(selected_regions) >= 4:
                        break
        else:
            selected_regions = list(all_regions.values())[:4]

        for reg_obj in selected_regions:
            reg_obj.continent_id = cont_id_str
            reg.register_region(reg_obj)

        world_state.infrastructure = reg
        reg.recalculate_totals()
        return reg

    @classmethod
    def assemble_settlement_roads(
        cls,
        settlements: Dict[str, Settlement],
        max_connection_distance_km: float = 35.0,
        min_connections: int = 1,
        max_connections: int = 4,
    ) -> int:
        """
        Connects settlements via 2D Euclidean distance into a deterministic road network graph.
        - Calculates pairwise Euclidean distance: dist = sqrt((x1-x2)^2 + (y1-y2)^2).
        - Connects nearest neighbors (min min_connections, max max_connections).
        - Determines RoadType and RouteCategory:
          * Major settlements (capital/fortress) or short distance (<=12km) -> PAVED_HIGHWAY / TRUNK_HIGHWAY
          * Mining camps -> MOUNTAIN_PASS
          * Coastal ports -> DIRT_ROAD (coastal trade)
          * Other -> DIRT_ROAD / BRANCH_ROAD
        - Cross-border roads (origin.nation_id != dest.nation_id):
          * is_bottleneck = True, bottleneck_type = "국경 관문"
          * route_category = BOTTLENECK_PASS, toll_fee = calculated
          * traits includes "국경 검문 관문"
        - Bidirectional symmetry guaranteed (A->B implies B->A).
        Returns total road connections created (undirected count).
        """
        from src.world.geography import ROAD_SPEED_MULTIPLIERS, ROAD_HAZARD_BASE

        s_list = list(settlements.values())
        if len(s_list) < 2:
            return 0

        # Precompute pairwise distances
        pairs = []
        for i in range(len(s_list)):
            for j in range(i + 1, len(s_list)):
                s1 = s_list[i]
                s2 = s_list[j]
                x1, y1 = s1.coordinates if s1.coordinates else (0.0, 0.0)
                x2, y2 = s2.coordinates if s2.coordinates else (0.0, 0.0)
                d = math.hypot(x1 - x2, y1 - y2)
                if d <= 0.0:
                    d = 5.0
                pairs.append((round(d, 1), s1, s2))

        # Sort pairs by distance ascending
        pairs.sort(key=lambda p: p[0])

        connection_counts: Dict[str, int] = {s.id: len(s.roads) for s in s_list}
        connections_made = 0

        def create_connection(s_from: Settlement, s_to: Settlement, dist: float) -> RoadConnection:
            is_cross_border = (
                s_from.nation_id != s_to.nation_id and
                bool(s_from.nation_id) and
                bool(s_to.nation_id)
            )
            is_major_link = (
                s_from.settlement_type in ["capital_metropolis", "fortress_citadel"] and
                s_to.settlement_type in ["capital_metropolis", "fortress_citadel"]
            )
            is_mine = (
                s_from.settlement_type == "mining_camp" or
                s_to.settlement_type == "mining_camp"
            )
            is_port = (
                s_from.settlement_type == "coastal_port" or
                s_to.settlement_type == "coastal_port"
            )

            # Determine road type & category
            if is_major_link or dist <= 12.0:
                rtype = RoadType.PAVED_HIGHWAY
                rcat = RouteCategory.TRUNK_HIGHWAY
                rname = f"{s_from.name}-{s_to.name} 포장 왕도"
                traits = ["왕도 포장 가도", "순찰대 상시 배치", "안전한 대로"]
            elif is_mine:
                rtype = RoadType.MOUNTAIN_PASS
                rcat = RouteCategory.BRANCH_ROAD
                rname = f"{s_from.name}-{s_to.name} 산악 고갯길"
                traits = ["험준한 산길", "낙석 주의", "광석 운송로"]
            elif is_port:
                rtype = RoadType.DIRT_ROAD
                rcat = RouteCategory.BRANCH_ROAD
                rname = f"{s_from.name}-{s_to.name} 해안 교역로"
                traits = ["해안 교역로", "해풍 습기", "물류 가도"]
            else:
                rtype = RoadType.DIRT_ROAD
                rcat = RouteCategory.BRANCH_ROAD
                rname = f"{s_from.name}-{s_to.name} 연락 흙길"
                traits = ["평탄한 흙길", "일반 통행로"]

            # Cross-border bottleneck override
            is_bottleneck = False
            bottleneck_type = ""
            toll = 0
            if is_cross_border:
                rcat = RouteCategory.BOTTLENECK_PASS
                is_bottleneck = True
                bottleneck_type = "국경 관문"
                toll = max(5, int(dist * 0.5))
                rname = f"{s_from.name}-{s_to.name} 국경 관문로"
                traits.extend(["국경 검문 관문", "밀수 단속 구역", "통행증 필수"])

            return RoadConnection(
                destination_id=s_to.id,
                distance_km=dist,
                road_type=rtype,
                speed_multiplier=ROAD_SPEED_MULTIPLIERS.get(rtype, 1.0),
                hazard_level=ROAD_HAZARD_BASE.get(rtype, 20),
                toll_fee=toll,
                road_name_ko=rname,
                route_category=rcat,
                is_bottleneck=is_bottleneck,
                bottleneck_type=bottleneck_type,
                traits=list(dict.fromkeys(traits)),
            )

        # Pass 1: Ensure minimum connections for isolated settlements
        for s in s_list:
            if connection_counts[s.id] < min_connections:
                candidates = []
                for d, s1, s2 in pairs:
                    if s1.id == s.id and s2.id not in s.roads:
                        candidates.append((d, s2))
                    elif s2.id == s.id and s1.id not in s.roads:
                        candidates.append((d, s1))
                candidates.sort(key=lambda c: c[0])
                for d, other in candidates:
                    if connection_counts[s.id] >= min_connections:
                        break
                    s.roads[other.id] = create_connection(s, other, d)
                    other.roads[s.id] = create_connection(other, s, d)
                    connection_counts[s.id] += 1
                    connection_counts[other.id] += 1
                    connections_made += 1

        # Pass 2: Connect neighboring settlements up to max_connections if within max_connection_distance_km
        for d, s1, s2 in pairs:
            if s2.id in s1.roads:
                continue
            if d > max_connection_distance_km:
                continue
            if connection_counts[s1.id] >= max_connections or connection_counts[s2.id] >= max_connections:
                continue

            s1.roads[s2.id] = create_connection(s1, s2, d)
            s2.roads[s1.id] = create_connection(s2, s1, d)
            connection_counts[s1.id] += 1
            connection_counts[s2.id] += 1
            connections_made += 1

        return connections_made

    @classmethod
    def assemble_world_middle_layers(
        cls,
        world_state: Any,
        registry: Optional[InfrastructureRegistry] = None,
        nation_ids: Optional[List[str]] = None,
        settlement_ids: Optional[List[str]] = None,
        settlements_per_nation: int = 4,
        max_connection_distance_km: float = 40.0,
        include_facilities: bool = True,
    ) -> InfrastructureRegistry:
        """
        Assembles Level 3 (Nation) and Level 4 (Settlement) into the infrastructure hierarchy.
        1. Ensures upper layers (Level 0~2) are assembled.
        2. Selects and registers nations compatible with the continent.
        3. Selects and registers settlements, mapping them to nations and regions.
        4. Connects settlements into a deterministic 2D road network (assemble_settlement_roads).
        5. Identifies cross-border roads, binding them to nation international_highways and border_checkpoints.
        6. Recalculates bottom-up population and area totals across all tiers.
        """
        reg = registry or getattr(world_state, "infrastructure", None)
        if not reg or not reg.continents or not reg.regions:
            reg = cls.assemble_world_upper_layers(world_state, registry=reg)

        continent = next(iter(reg.continents.values()))
        cont_id = continent.id

        # 1. Load & Select Nations
        all_nations = cls.load_nation_templates(continent_id=cont_id)
        chosen_nations: List[Nation] = []

        if nation_ids:
            for nid in nation_ids:
                if nid in all_nations:
                    chosen_nations.append(all_nations[nid])
        elif continent.nation_ids:
            for nid in continent.nation_ids:
                if nid in all_nations and all_nations[nid] not in chosen_nations:
                    chosen_nations.append(all_nations[nid])

        if not chosen_nations and all_nations:
            ruling_seen = set()
            for nat in all_nations.values():
                if nat.ruling_system not in ruling_seen:
                    chosen_nations.append(nat)
                    ruling_seen.add(nat.ruling_system)
                if len(chosen_nations) >= 3:
                    break
            if not chosen_nations:
                chosen_nations = list(all_nations.values())[:3]

        for nat in chosen_nations:
            nat.continent_id = cont_id
            reg.register_nation(nat)

        # 2. Load & Select Settlements
        all_settlements = cls.load_settlement_templates()
        active_regions = list(reg.regions.values())
        chosen_settlements: List[Settlement] = []

        if settlement_ids:
            for sid in settlement_ids:
                if sid in all_settlements:
                    chosen_settlements.append(all_settlements[sid])
        else:
            available_settlements = list(all_settlements.values())
            used_ids = set()

            for nat_idx, nat in enumerate(chosen_nations):
                nat_settlements: List[Settlement] = []

                # Find capital first
                for st in available_settlements:
                    if st.id not in used_ids and st.settlement_type == "capital_metropolis":
                        nat_settlements.append(st)
                        used_ids.add(st.id)
                        break

                # Fill satellite settlements
                for st in available_settlements:
                    if len(nat_settlements) >= settlements_per_nation:
                        break
                    if st.id not in used_ids:
                        nat_settlements.append(st)
                        used_ids.add(st.id)

                # Bind nation and region to these settlements
                for s_idx, st in enumerate(nat_settlements):
                    st.nation_id = nat.id
                    target_reg = active_regions[(nat_idx + s_idx) % len(active_regions)]
                    st.region_id = target_reg.id
                    reg.register_settlement(st)
                    chosen_settlements.append(st)

        # If user explicitly passed settlement_ids, register them
        if settlement_ids:
            for idx, st in enumerate(chosen_settlements):
                if (not st.nation_id or st.nation_id not in reg.nations) and chosen_nations:
                    st.nation_id = chosen_nations[idx % len(chosen_nations)].id
                if (not st.region_id or st.region_id not in reg.regions) and active_regions:
                    st.region_id = active_regions[idx % len(active_regions)].id
                reg.register_settlement(st)

        # 3. Assemble 2D Settlement Road Network
        cls.assemble_settlement_roads(
            reg.settlements,
            max_connection_distance_km=max_connection_distance_km,
            min_connections=1,
            max_connections=4,
        )

        # 4. Bind Cross-Border Gates & International Highways
        for s_from in reg.settlements.values():
            if not s_from.nation_id or s_from.nation_id not in reg.nations:
                continue
            nat_from = reg.nations[s_from.nation_id]

            for dest_id, road in s_from.roads.items():
                s_to = reg.settlements.get(dest_id)
                if not s_to or not s_to.nation_id:
                    continue

                if s_from.nation_id != s_to.nation_id:
                    # Register border checkpoint settlement
                    if s_from.id not in nat_from.border_checkpoints:
                        nat_from.border_checkpoints.append(s_from.id)

                    # Register inter-tier highway
                    highway = InterTierRoute(
                        origin_id=nat_from.id,
                        destination_id=s_to.nation_id,
                        route_name=road.road_name_ko,
                        route_category=road.route_category,
                        distance_km=road.distance_km,
                        travel_medium="land",
                        toll_fee=road.toll_fee,
                        is_bottleneck=road.is_bottleneck,
                        bottleneck_type=road.bottleneck_type,
                        traits=list(road.traits),
                        description=f"{s_from.name}({nat_from.name})에서 {s_to.name}으로 통하는 국경 관문 가도",
                    )
                    if not any(h.origin_id == highway.origin_id and h.destination_id == highway.destination_id for h in nat_from.international_highways):
                        nat_from.international_highways.append(highway)

        # 5. Slot & Attach Level 5 Facilities
        if include_facilities:
            cls.assemble_settlement_facilities(reg)

        # 6. Bottom-Up Totals Recalculation
        reg.recalculate_totals()
        world_state.infrastructure = reg
        if hasattr(world_state, "sync_infrastructure_totals"):
            world_state.sync_infrastructure_totals()
        return reg

    @classmethod
    def assemble_settlement_facilities(
        cls,
        registry: InfrastructureRegistry,
        settlement_ids: Optional[List[str]] = None,
        facility_templates: Optional[Dict[str, Facility]] = None,
    ) -> int:
        """
        Slots and attaches Level 5 Facilities to settlements based on scale, type, and local specialties.
        - Loads 14 archetypes from facility_templates.json if not provided.
        - Determines facility composition:
          * Baseline: tavern_inn, general_store, town_hall_manor.
          * capital_metropolis: + blacksmith_forge, apothecary_clinic, training_ground, mage_tower_academy, temple_shrine, guild_hall, guard_post_prison, public_bathhouse.
          * fortress_citadel: + blacksmith_forge, guard_post_prison, training_ground, workshop_mill, temple_shrine.
          * mining_camp: + blacksmith_forge, workshop_mill, dungeon_entrance.
          * coastal_port / fishing_cove: + workshop_mill, temple_shrine, apothecary_clinic.
          * monastic_town: + temple_shrine, apothecary_clinic, mage_tower_academy.
          * oasis_crossroad / nomad_camp: + roving_peddler_stall, guard_post_prison, temple_shrine.
          * treetop_village: + apothecary_clinic, workshop_mill, temple_shrine.
          * farming_village / other: + blacksmith_forge, apothecary_clinic, workshop_mill.
        - Customizes names, services, and inventory using settlement name and specialties.
        - Establishes internal/external exits connecting to the settlement's town square.
        - Populates traits ensuring at least 3 traits per facility.
        - Registers into registry via register_facility (which auto-populates categorized lists).
        Returns total facilities created.
        """
        templates = facility_templates or cls.load_facility_templates()
        tmpl_by_type: Dict[str, Facility] = {}
        for fac in templates.values():
            if fac.facility_type not in tmpl_by_type:
                tmpl_by_type[fac.facility_type] = fac

        target_settlements = [
            s for s in registry.settlements.values()
            if settlement_ids is None or s.id in settlement_ids
        ]

        facilities_created = 0

        for st in target_settlements:
            st_type = st.settlement_type
            pop = st.population
            types_to_add: List[str] = ["tavern_inn", "general_store", "town_hall_manor"]

            if st_type == "capital_metropolis":
                types_to_add.extend([
                    "blacksmith_forge", "apothecary_clinic", "training_ground",
                    "mage_tower_academy", "temple_shrine", "guild_hall",
                    "guard_post_prison", "public_bathhouse"
                ])
            elif st_type == "fortress_citadel":
                types_to_add.extend([
                    "blacksmith_forge", "guard_post_prison", "training_ground",
                    "workshop_mill", "temple_shrine"
                ])
            elif st_type == "mining_camp":
                types_to_add.extend([
                    "blacksmith_forge", "workshop_mill", "dungeon_entrance"
                ])
            elif st_type in ["coastal_port", "fishing_cove"]:
                types_to_add.extend([
                    "workshop_mill", "temple_shrine", "apothecary_clinic"
                ])
            elif st_type == "monastic_town":
                types_to_add.extend([
                    "temple_shrine", "apothecary_clinic", "mage_tower_academy"
                ])
            elif st_type in ["oasis_crossroad", "nomad_camp"]:
                types_to_add.extend([
                    "roving_peddler_stall", "guard_post_prison", "temple_shrine"
                ])
            elif st_type == "treetop_village":
                types_to_add.extend([
                    "apothecary_clinic", "workshop_mill", "temple_shrine"
                ])
            else:
                types_to_add.extend([
                    "blacksmith_forge", "apothecary_clinic", "workshop_mill"
                ])

            # Population & context checks
            if pop >= 10000 and "guard_post_prison" not in types_to_add:
                types_to_add.append("guard_post_prison")
            if pop >= 5000 and "temple_shrine" not in types_to_add:
                types_to_add.append("temple_shrine")

            # Check for dungeon / ruin presence from local curses, scandals or grievances
            combined_lore = " ".join(st.local_curses_and_taboos + st.hidden_scandals + st.historical_grievances)
            has_curse_or_dungeon = any(
                keyword in combined_lore
                for keyword in ["미궁", "던전", "유적", "원혼", "납골당", "폐광", "괴담", "심연"]
            )
            if has_curse_or_dungeon and "dungeon_entrance" not in types_to_add:
                types_to_add.append("dungeon_entrance")

            unique_types = list(dict.fromkeys(types_to_add))

            for ftype in unique_types:
                tmpl = tmpl_by_type.get(ftype)
                fac_id = f"fac_{st.id}_{ftype}"

                if fac_id in registry.facilities:
                    continue

                fac_name = f"{st.name} {tmpl.name if tmpl else ftype}"
                fac_desc = tmpl.description if tmpl else f"{st.name}의 {ftype} 시설"

                items: List[str] = list(tmpl.items) if tmpl else []
                if ftype in ["general_store", "tavern_inn", "roving_peddler_stall"] and st.specialties:
                    items.extend(st.specialties)

                traits: List[str] = list(tmpl.traits) if tmpl else [f"{st.name} 소속 시설", "현지 주민 애용", "안정된 거점"]
                traits.append(f"{st.name} 관할")
                traits = list(dict.fromkeys(traits))

                exits: Dict[str, str] = {
                    "광장": f"{st.name} 중앙 광장",
                    "거리": f"{st.name} 중심가"
                }

                fac = Facility(
                    id=fac_id,
                    name=fac_name,
                    settlement_id=st.id,
                    category=tmpl.category if tmpl else FacilityCategory.TRADE_WORKSHOP,
                    is_communal_public=tmpl.is_communal_public if tmpl else False,
                    is_wonder=tmpl.is_wonder if tmpl else False,
                    facility_type=ftype,
                    building_status="operational",
                    construction_progress=100,
                    occupancy_limit=tmpl.occupancy_limit if tmpl else 20,
                    noise_level=tmpl.noise_level if tmpl else 40,
                    soundproof_rating=tmpl.soundproof_rating if tmpl else 30,
                    floor_material=tmpl.floor_material if tmpl else "wood_creaky",
                    lighting=tmpl.lighting if tmpl else 50,
                    light_source_type=tmpl.light_source_type if tmpl else "torch",
                    water_supply_type=tmpl.water_supply_type if tmpl else "공용우물",
                    ventilation_quality=tmpl.ventilation_quality if tmpl else 50,
                    durability=tmpl.durability if tmpl else 100,
                    daily_maintenance_cost=tmpl.daily_maintenance_cost if tmpl else 5,
                    defense_rating=tmpl.defense_rating if tmpl else 20,
                    flammability_rating=tmpl.flammability_rating if tmpl else 30,
                    trap_hazard_rating=tmpl.trap_hazard_rating if tmpl else 0,
                    magic_ward_tier=tmpl.magic_ward_tier if tmpl else 0,
                    lock_difficulty=tmpl.lock_difficulty if tmpl else 15,
                    reinforcement_material=tmpl.reinforcement_material if tmpl else "wood",
                    scent_intensity=tmpl.scent_intensity if tmpl else 40,
                    ceiling_height_meters=tmpl.ceiling_height_meters if tmpl else 3.0,
                    hallway_width_meters=tmpl.hallway_width_meters if tmpl else 2.2,
                    cover_poise_durability=tmpl.cover_poise_durability if tmpl else 50,
                    dungeon_max_depth_floors=tmpl.dungeon_max_depth_floors if tmpl else 0,
                    dungeon_core_element=tmpl.dungeon_core_element if tmpl else "none",
                    sanctification_rating=tmpl.sanctification_rating if tmpl else 50,
                    services=dict(tmpl.services) if tmpl else {},
                    interactive_props=list(tmpl.interactive_props) if tmpl else ["참나무 탁자", "출입구 빗장"],
                    infiltration_points=list(tmpl.infiltration_points) if tmpl else ["후방 창고문", "환기창"],
                    hidden_compartments=list(tmpl.hidden_compartments) if tmpl else ["바닥 비밀 홈"],
                    items=items,
                    exits=exits,
                    traits=traits,
                    description=fac_desc,
                )
                registry.register_facility(fac)
                facilities_created += 1

        return facilities_created

    @classmethod
    def assemble_full_world(
        cls,
        world_state: Any,
        registry: Optional[InfrastructureRegistry] = None,
        cosmo_id: Optional[str] = None,
        continent_id: Optional[str] = None,
        region_ids: Optional[List[str]] = None,
        nation_ids: Optional[List[str]] = None,
        settlement_ids: Optional[List[str]] = None,
        settlements_per_nation: int = 4,
        max_connection_distance_km: float = 40.0,
        include_facilities: bool = True,
        bind_entities: bool = False,
    ) -> InfrastructureRegistry:
        """
        Master factory assembling the complete 6-Tier Realistic World Infrastructure:
        Level 0 (Cosmology & Laws) -> Level 1 (Continent & Language) -> Level 2 (Region & Climate) ->
        Level 3 (Nation & Tariffs) -> Level 4 (Settlement & 2D Roads) -> Level 5 (Facility & Services).
        """
        reg = registry or getattr(world_state, "infrastructure", None)
        if cosmo_id or continent_id or region_ids or not reg or not reg.continents or not reg.regions:
            reg = cls.assemble_world_upper_layers(
                world_state,
                cosmo_id=cosmo_id,
                continent_id=continent_id,
                region_ids=region_ids,
                registry=reg,
            )

        mid_reg = cls.assemble_world_middle_layers(
            world_state,
            registry=reg,
            nation_ids=nation_ids,
            settlement_ids=settlement_ids,
            settlements_per_nation=settlements_per_nation,
            max_connection_distance_km=max_connection_distance_km,
            include_facilities=include_facilities,
        )

        if bind_entities:
            cls.bind_world_entities(world_state, registry=mid_reg)

        return mid_reg

    # -----------------------------------------------------------------
    # Entity Binding: 1. NPC & Demographics Binding
    # -----------------------------------------------------------------
    @classmethod
    def bind_settlement_npcs(
        cls,
        world_state: Any,
        registry: Optional[InfrastructureRegistry] = None,
        settlement_ids: Optional[List[str]] = None,
    ) -> int:
        """
        Binds resident NPCs to settlement facilities based on racial demographics and facility types.
        Populates world_state.npcs and updates facility.npcs and facility.key_holder_npc_id.
        """
        from src.world.state import NPC
        reg = registry or getattr(world_state, "infrastructure", None)
        if not reg:
            return 0

        target_settlements = [
            s for s in reg.settlements.values()
            if settlement_ids is None or s.id in settlement_ids
        ]

        # Job mapping: (job_title, name_suffix, tier, base_traits, stats, gold)
        JOB_MAP = {
            FacilityType.TAVERN_INN.value: ("선술집 주인", "주모", "commoner", ["마을 소식통", "호탕함", "외지인 경계"], {"str": 11, "con": 12, "wis": 11}, 45),
            FacilityType.GENERAL_STORE.value: ("잡화상인", "잡화상", "commoner", ["흥정의 달인", "계산적", "자물쇠 소지"], {"int": 12, "wis": 12}, 60),
            FacilityType.BLACKSMITH_FORGE.value: ("대장장이", "모루장인", "commoner", ["우직함", "화염 저항", "정밀 단조"], {"str": 14, "con": 13}, 35),
            FacilityType.APOTHECARY_CLINIC.value: ("의원 약초사", "약초사", "commoner", ["약초 감별", "응급 지혈", "침착함"], {"int": 13, "wis": 13}, 25),
            FacilityType.TRAINING_GROUND.value: ("연무장 교관", "수석교관", "intermediate", ["엄격함", "검술 달인", "전투 흉터"], {"str": 15, "agi": 13, "ac": 14}, 30),
            FacilityType.MAGE_TOWER_ACADEMY.value: ("마탑 학자", "비전학사", "intermediate", ["비전 연구", "고대어 해독", "지적 호기심"], {"int": 16, "wis": 14, "mana": 60}, 50),
            FacilityType.TEMPLE_SHRINE.value: ("성소 사제", "주임사제", "commoner", ["신실함", "치유 기도", "금기 엄수"], {"wis": 15, "con": 11}, 20),
            FacilityType.GUILD_HALL.value: ("길드 접수원", "길드원", "commoner", ["의뢰 조율", "정보통", "비밀 엄수"], {"int": 12, "agi": 11}, 40),
            FacilityType.GUARD_POST_PRISON.value: ("경비대장", "수비대장", "intermediate", ["철통 경계", "엄격한 법 집행", "불심검문"], {"str": 14, "con": 13, "ac": 15}, 35),
            FacilityType.PUBLIC_BATHHOUSE.value: ("목욕탕 관리인", "욕장지기", "commoner", ["온천 감정", "소문 경청", "친절함"], {"wis": 11, "cha": 12}, 20),
            FacilityType.ROVING_PEDDLER_STALL.value: ("유랑 행상인", "보따리상", "commoner", ["이국 진귀품", "방랑벽", "흥정 유도"], {"agi": 12, "int": 12}, 50),
            FacilityType.WORKSHOP_MILL.value: ("제재소 장인", "공방장", "commoner", ["목재 가공", "도르래 기술", "근면함"], {"str": 13, "con": 12}, 25),
            FacilityType.DUNGEON_ENTRANCE.value: ("유적 묘지기", "파수꾼", "commoner", ["음산한 분위기", "고대 경고문", "봉인 감시"], {"wis": 14, "int": 11}, 15),
            FacilityType.TOWN_HALL_MANOR.value: ("영주/촌장", "영주", "intermediate", ["영지 행정", "원로원 의장", "정치적 수완"], {"int": 13, "wis": 13, "con": 12}, 120),
        }

        npcs_spawned = 0
        for st in target_settlements:
            primary_species = "인간"
            if st.racial_demographics:
                primary_species = max(st.racial_demographics.items(), key=lambda x: x[1])[0]

            for fac_id in st.facility_ids:
                fac = reg.facilities.get(fac_id)
                if not fac:
                    continue

                existing = [nid for nid in fac.npcs if hasattr(world_state, "npcs") and nid in world_state.npcs]
                if existing:
                    continue

                f_type = fac.facility_type
                info = JOB_MAP.get(f_type, ("시설 관리인", "관리인", "commoner", ["성실함", "현지 적응", "시설 유지"], {}, 20))
                job, suffix, tier, base_traits, stats, gold = info

                npc_id = f"npc_{st.id}_{f_type}_{len(fac.npcs) + 1}"
                npc_name = f"{st.name} {suffix}"
                desc = f"{st.name}의 {fac.name}에 상주하는 {primary_species} {job}."

                npc_traits = list(base_traits)
                if primary_species != "인간":
                    npc_traits.append(f"{primary_species} 혈통")
                if st.traits:
                    npc_traits.append(st.traits[0])

                health = 60 if tier == "intermediate" else 50
                mana = stats.get("mana", 40 if tier == "intermediate" else 30)

                npc = NPC(
                    id=npc_id,
                    name=npc_name,
                    description=desc,
                    location=fac.id,
                    job=job,
                    tier=tier,
                    health=health,
                    max_health=health,
                    mana=mana,
                    max_mana=mana,
                    armor_class=stats.get("ac", 10),
                    gold=gold,
                    strength=stats.get("str", 10),
                    agility=stats.get("agi", 10),
                    intelligence=stats.get("int", 10),
                    constitution=stats.get("con", 10),
                    wisdom=stats.get("wis", 10),
                    faction_id=st.nation_id,
                    traits=npc_traits,
                )

                if hasattr(world_state, "npcs"):
                    world_state.npcs[npc_id] = npc

                if npc_id not in fac.npcs:
                    fac.npcs.append(npc_id)

                if not fac.key_holder_npc_id and f_type in [
                    FacilityType.GENERAL_STORE.value,
                    FacilityType.BLACKSMITH_FORGE.value,
                    FacilityType.TOWN_HALL_MANOR.value,
                    FacilityType.GUARD_POST_PRISON.value,
                ]:
                    fac.key_holder_npc_id = npc_id

                npcs_spawned += 1

        return npcs_spawned

    # -----------------------------------------------------------------
    # Entity Binding: 2. Item & Commercial Inventory Binding
    # -----------------------------------------------------------------
    @classmethod
    def bind_facility_inventories(
        cls,
        world_state: Any,
        registry: Optional[InfrastructureRegistry] = None,
        settlement_ids: Optional[List[str]] = None,
    ) -> int:
        """
        Populates commercial facilities with stock items tailored to settlement & regional specialties.
        Applies cascading regional price multipliers and national tariffs.
        """
        from src.world.state import Item
        reg = registry or getattr(world_state, "infrastructure", None)
        if not reg:
            return 0

        target_settlements = [
            s for s in reg.settlements.values()
            if settlement_ids is None or s.id in settlement_ids
        ]

        items_stocked = 0
        for st in target_settlements:
            region = reg.regions.get(st.region_id)
            specialties = list(st.specialties or [])
            if region and region.specialties:
                specialties.extend(region.specialties)

            for fac_id in st.facility_ids:
                fac = reg.facilities.get(fac_id)
                if not fac:
                    continue

                f_type = fac.facility_type
                if f_type not in [
                    FacilityType.TAVERN_INN.value,
                    FacilityType.GENERAL_STORE.value,
                    FacilityType.BLACKSMITH_FORGE.value,
                    FacilityType.APOTHECARY_CLINIC.value,
                    FacilityType.ROVING_PEDDLER_STALL.value,
                ]:
                    continue

                existing = [iid for iid in fac.items if hasattr(world_state, "items") and iid in world_state.items]
                if existing:
                    continue

                raw_items: List[Tuple[str, str, str, int, dict, List[str]]] = []

                if f_type == FacilityType.TAVERN_INN.value:
                    raw_items.append(("drink", f"{st.name} 특산주", "consumable", 12, {"restore_fatigue": 15}, ["향토 주류", "피로 회복", "향긋함"]))
                    raw_items.append(("ration", f"{st.name} 구운 보존식", "consumable", 15, {"restore_hp": 20}, ["따뜻한 식사", "체력 회복", "염장 가공"]))

                elif f_type == FacilityType.GENERAL_STORE.value:
                    raw_items.append(("rope", "견고한 등반 밧줄", "tool", 20, {"utility": "climb_advantage"}, ["탐험 장비", "마끈 직조"]))
                    raw_items.append(("torch_kit", "방수 횃불 세트", "misc", 15, {"light_duration": 60}, ["조명 도구", "송진 코팅"]))
                    if specialties:
                        spec_name = specialties[0]
                        raw_items.append(("specialty", f"가공된 {spec_name}", "misc", 40, {"trade_good": True}, [f"{st.name} 특산물", "원산지 보증"]))

                elif f_type == FacilityType.BLACKSMITH_FORGE.value:
                    b_tier = max(1, st.blacksmith_tier)
                    dmg = 8 + b_tier * 2
                    def_val = 5 + b_tier
                    raw_items.append(("sword", f"{st.name}산 단련 검", "weapon", 50 * b_tier, {"damage": dmg}, [f"단련도 {b_tier}급", "절삭력", "정밀 단조"]))
                    raw_items.append(("armor", f"{st.name}산 방호 흉갑", "armor", 60 * b_tier, {"defense": def_val}, [f"방호도 {b_tier}급", "이음새 보강", "물리 저항"]))
                    raw_items.append(("repair_kit", "휴대용 모루 수리 키트", "tool", 25, {"repair_durability": 30}, ["무구 수리", "휴대용 공구"]))

                elif f_type == FacilityType.APOTHECARY_CLINIC.value:
                    raw_items.append(("bandage", "소독 지혈 붕대", "consumable", 12, {"stop_bleeding": True}, ["응급 처치", "약초 살균"]))
                    raw_items.append(("healing_salve", "농축 산약초 연고", "consumable", 30, {"restore_hp": 30}, ["외상 치료", "천연 생약"]))
                    if region and (region.environmental_toxicity > 0 or region.survival_hazards):
                        raw_items.append(("antitoxin", "청정 해독 물약", "consumable", 40, {"cure_poison": True}, ["환경 독성 정화", "비전 해독제"]))

                elif f_type == FacilityType.ROVING_PEDDLER_STALL.value:
                    raw_items.append(("curio", "먼 이국의 황동 나침반", "misc", 70, {"navigation_bonus": True}, ["이국 진귀품", "정밀 기계", "희소성"]))
                    raw_items.append(("talisman", "수호의 짐승뼈 부적", "accessory", 55, {"ward_minor": True}, ["토착 주술", "정령의 가호"]))

                for idx, (suffix, iname, itype, base_val, props, itraits) in enumerate(raw_items):
                    item_id = f"item_{st.id}_{fac.id}_{suffix}_{idx + 1}"
                    price_info = reg.calculate_effective_price(itype, base_val, fac.id)
                    eff_price = int(price_info.get("final_price", base_val)) if isinstance(price_info, dict) else int(price_info)

                    item = Item(
                        id=item_id,
                        name=iname,
                        description=f"{fac.name}에서 취급하는 {itype} 품목.",
                        location=fac.id,
                        item_type=itype,
                        value=eff_price,
                        properties=props,
                        traits=itraits,
                    )
                    if itype == "weapon":
                        item.damage = props.get("damage", 8)
                    elif itype == "armor":
                        item.defense = props.get("defense", 5)

                    if hasattr(world_state, "items"):
                        world_state.items[item_id] = item

                    if item_id not in fac.items:
                        fac.items.append(item_id)

                    items_stocked += 1

        return items_stocked

    # -----------------------------------------------------------------
    # Entity Binding: 3. Skill & Magic Training Facility Binding
    # -----------------------------------------------------------------
    @classmethod
    def bind_training_facilities(
        cls,
        world_state: Any,
        registry: Optional[InfrastructureRegistry] = None,
        settlement_ids: Optional[List[str]] = None,
    ) -> int:
        """
        Binds trainable martial skills, magic spells, and phonetic ancient words
        to training grounds and mage tower academies.
        """
        reg = registry or getattr(world_state, "infrastructure", None)
        if not reg:
            return 0

        target_settlements = [
            s for s in reg.settlements.values()
            if settlement_ids is None or s.id in settlement_ids
        ]

        facilities_configured = 0
        for st in target_settlements:
            for fac_id in st.facility_ids:
                fac = reg.facilities.get(fac_id)
                if not fac:
                    continue

                if fac.facility_type == FacilityType.TRAINING_GROUND.value:
                    fac.services["available_skills"] = [
                        "강타(Strike)", "철벽 방패세(Shield Guard)", "회전 베기(Whirlwind Slash)", "전투의 포효(Battle Cry)"
                    ]
                    fac.services["training_cost_gold"] = 25 * max(1, st.development_tier)
                    fac.services["mastery_limit_tier"] = min(4, st.development_tier + 1)
                    facilities_configured += 1

                elif fac.facility_type == FacilityType.MAGE_TOWER_ACADEMY.value:
                    fac.services["available_skills"] = [
                        "화염구(Fireball)", "에테르 방벽(Aether Barrier)", "마력 탐지(Mana Sight)", "비전 섬광(Arcane Flash)"
                    ]
                    # Ancient Magic Phonetic Words adhering to Rule 4
                    fac.services["ancient_words"] = [
                        "바르(발화/열에너지)", "카르(강제/물리운동)", "이그니스(화염)", "모투스(기동)"
                    ]
                    fac.services["training_cost_gold"] = 40 * max(1, st.development_tier)
                    fac.services["mana_density_rating"] = st.local_mana_density_override or 50
                    facilities_configured += 1

        return facilities_configured

    # -----------------------------------------------------------------
    # Entity Binding: 4. Monster & Predator Ecosystem Binding
    # -----------------------------------------------------------------
    @classmethod
    def load_monster_templates(cls, filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
        target_path = filepath or (TEMPLATES_DIR / "monster_templates.json")
        if not target_path.exists():
            return []
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Failed to load monster templates from {target_path}: {e}")
            return []

    @classmethod
    def spawn_monster_from_template(
        cls,
        template_id_or_name: str,
        location_id: str,
        world_state: Any,
        registry: Optional[InfrastructureRegistry] = None,
    ) -> Optional[Any]:
        """
        Deterministic Factory: Converts a monster template into a hostile NPC entity
        and registers it in world_state.npcs.
        """
        from src.world.state import NPC, Item
        templates = cls.load_monster_templates()
        matched = None
        for tmpl in templates:
            if tmpl.get("id") == template_id_or_name or tmpl.get("name") == template_id_or_name:
                matched = tmpl
                break
            if template_id_or_name.lower() in tmpl.get("name", "").lower() or template_id_or_name.lower() in tmpl.get("id", "").lower():
                matched = tmpl
                break

        if not matched and templates:
            matched = templates[0]

        if not matched:
            return None

        stat_prof = matched.get("stat_profile", {})
        hp = stat_prof.get("hp", 60)
        ac = stat_prof.get("ac", 12)
        str_val = stat_prof.get("str", 12)
        agi_val = stat_prof.get("agi", 10)
        int_val = stat_prof.get("int", 8)
        con_val = stat_prof.get("con", 12)

        existing_npcs = getattr(world_state, "npcs", {})
        mob_id = f"mob_{matched.get('id', 'beast')}_{len(existing_npcs) + 1}"
        mob_name = matched.get("name", "야생 마수")
        mob_theme = matched.get("concept_theme", "괴수")
        weakness = matched.get("weakness_exploit", "정밀 타격")

        traits = [mob_theme, f"약점: {weakness[:20]}", "적대 마수", matched.get("tier", "commoner")]

        skills = []
        if matched.get("extractable_skill"):
            skills.append(matched["extractable_skill"])

        mob = NPC(
            id=mob_id,
            name=mob_name,
            description=f"[{mob_theme}] {matched.get('observation_clue', '살기를 뿜어내는 마수.')}",
            location=location_id,
            job="마수/괴수",
            tier=matched.get("tier", "commoner"),
            disposition="hostile",
            health=hp,
            max_health=hp,
            armor_class=ac,
            strength=str_val,
            agility=agi_val,
            intelligence=int_val,
            constitution=con_val,
            skills=skills,
            traits=traits,
        )

        drops = matched.get("drops_and_materials", [])
        for idx, drop_name in enumerate(drops):
            drop_id = f"item_{mob_id}_drop_{idx + 1}"
            loot_item = Item(
                id=drop_id,
                name=drop_name,
                description=f"{mob_name}의 사체에서 채취 가능한 특수 전리품.",
                location=mob_id,
                item_type="material",
                value=30,
                traits=[mob_name, "마수 전리품", "연금술 소재"],
            )
            if hasattr(world_state, "items"):
                world_state.items[drop_id] = loot_item
            mob.inventory.append(drop_id)

        if hasattr(world_state, "npcs"):
            world_state.npcs[mob_id] = mob

        return mob

    @classmethod
    def bind_region_monsters(
        cls,
        world_state: Any,
        registry: Optional[InfrastructureRegistry] = None,
        region_ids: Optional[List[str]] = None,
    ) -> int:
        """
        Maps regional apex predators and terrain-compatible monsters to regions and peripheral settlements.
        """
        reg = registry or getattr(world_state, "infrastructure", None)
        if not reg:
            return 0

        templates = cls.load_monster_templates()
        if not templates:
            return 0

        target_regions = [
            r for r in reg.regions.values()
            if region_ids is None or r.id in region_ids
        ]

        monsters_spawned = 0
        for idx, region in enumerate(target_regions):
            matched_tmpl = None
            if region.apex_predator_id:
                for t in templates:
                    if t.get("id") == region.apex_predator_id:
                        matched_tmpl = t
                        break
            if not matched_tmpl:
                matched_tmpl = templates[idx % len(templates)]

            loc_id = f"loc_{region.id}_wilderness"
            mob = cls.spawn_monster_from_template(matched_tmpl["id"], loc_id, world_state, registry=reg)
            if mob:
                monsters_spawned += 1

        return monsters_spawned

    # -----------------------------------------------------------------
    # Entity Binding: 5. Quest & Notice Board Binding
    # -----------------------------------------------------------------
    @classmethod
    def bind_settlement_quests(
        cls,
        world_state: Any,
        registry: Optional[InfrastructureRegistry] = None,
        settlement_ids: Optional[List[str]] = None,
    ) -> int:
        """
        Binds notice board quests and historical grievance investigations
        to settlements, registering them into world_state.quests.
        """
        from src.world.quest_engine import Quest, QuestStage
        reg = registry or getattr(world_state, "infrastructure", None)
        if not reg:
            return 0

        target_settlements = [
            s for s in reg.settlements.values()
            if settlement_ids is None or s.id in settlement_ids
        ]

        quests_created = 0
        for st in target_settlements:
            giver_id = ""
            for fac_id in st.facility_ids:
                fac = reg.facilities.get(fac_id)
                if fac and fac.npcs:
                    giver_id = fac.npcs[0]
                    break

            # 1. Bounty / Hunt Quest
            q_hunt_id = f"quest_{st.id}_hunt"
            q_hunt = Quest(
                id=q_hunt_id,
                title=f"[{st.name}] 외곽 출몰 마수 토벌령",
                category="hunt",
                giver_npc_id=giver_id,
                description=f"{st.name} 외곽 지대의 마수 출몰로 인한 주민 위협. 수비대 협조 요청.",
                stages=[
                    QuestStage(stage_id=1, type="talk", target=giver_id, description_ko="마을 광장 공고 확인 및 정보 탐문"),
                    QuestStage(stage_id=2, type="kill", target="monster", description_ko="외곽 출몰 마수 처치 및 흔적 확보"),
                ],
                rewards={"gold": 75 * max(1, st.development_tier), "reputation": 10},
                traits=[st.name, "마을 토벌령", "현상수배", "공식 의뢰"],
            )

            if not hasattr(world_state, "quests"):
                world_state.quests = {}

            if q_hunt_id not in world_state.quests:
                world_state.quests[q_hunt_id] = q_hunt
                quests_created += 1

            # 2. Investigation Quest from Scandals or Grievances
            scandals = list(getattr(st, "hidden_scandals", [])) + list(getattr(st, "historical_grievances", []))
            if scandals:
                scandal = scandals[0]
                q_inv_id = f"quest_{st.id}_investigate"
                q_inv = Quest(
                    id=q_inv_id,
                    title=f"[{st.name}] 진상 조사: {scandal[:20]}",
                    category="investigation",
                    giver_npc_id=giver_id,
                    description=f"마을에 떠도는 내막 '{scandal}'의 실체와 배후를 조사하라.",
                    stages=[
                        QuestStage(stage_id=1, type="reach", target="tavern", description_ko="주점 및 골목길에서 소문 탐문"),
                        QuestStage(stage_id=2, type="talk", target=giver_id, description_ko="증거물 확보 및 관련자 대질"),
                    ],
                    rewards={"gold": 60 * max(1, st.development_tier), "reputation": 8},
                    traits=[st.name, "진상 조사", "비밀 탐색", "향토 스캔들"],
                )
                if q_inv_id not in world_state.quests:
                    world_state.quests[q_inv_id] = q_inv
                    quests_created += 1

        return quests_created

    # -----------------------------------------------------------------
    # Entity Binding: Master Pipeline
    # -----------------------------------------------------------------
    @classmethod
    def bind_world_entities(
        cls,
        world_state: Any,
        registry: Optional[InfrastructureRegistry] = None,
        settlement_ids: Optional[List[str]] = None,
        region_ids: Optional[List[str]] = None,
        bind_npcs: bool = True,
        bind_items: bool = True,
        bind_training: bool = True,
        bind_monsters: bool = True,
        bind_quests: bool = True,
    ) -> Dict[str, int]:
        """
        Master integration pipeline binding live entities (NPCs, Shop Items,
        Training Skills, Region Monsters, Notice Quests) into the 6-tier infrastructure.
        """
        reg = registry or getattr(world_state, "infrastructure", None)
        if not reg:
            return {}

        results = {
            "npcs_spawned": 0,
            "items_stocked": 0,
            "training_facilities_configured": 0,
            "monsters_spawned": 0,
            "quests_posted": 0,
        }

        if bind_npcs:
            results["npcs_spawned"] = cls.bind_settlement_npcs(
                world_state, registry=reg, settlement_ids=settlement_ids
            )
        if bind_items:
            results["items_stocked"] = cls.bind_facility_inventories(
                world_state, registry=reg, settlement_ids=settlement_ids
            )
        if bind_training:
            results["training_facilities_configured"] = cls.bind_training_facilities(
                world_state, registry=reg, settlement_ids=settlement_ids
            )
        if bind_monsters:
            results["monsters_spawned"] = cls.bind_region_monsters(
                world_state, registry=reg, region_ids=region_ids
            )
        if bind_quests:
            results["quests_posted"] = cls.bind_settlement_quests(
                world_state, registry=reg, settlement_ids=settlement_ids
            )

        return results



