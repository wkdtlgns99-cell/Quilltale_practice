"""
6-Tier Macro-to-Micro Realistic World Infrastructure Registry for Quilltale TRPG.
Re-exports all data models from infra_models and template loaders from infra_loader.
"""
from typing import Dict, List, Optional, Any
import logging

from .infra_models import (
    InterTierRoute,
    TransitVehicle,
    LogisticsNetwork,
    AttireHierarchyProfile,
    CuisineProfile,
    CulturalNormsProfile,
    _safe_profile,
    _safe_routes,
    Continent,
    Region,
    Nation,
    FacilityCategory,
    SanitationWaterInfrastructure,
    FoodStorageInfrastructure,
    DefenseSecurityInfrastructure,
    TradeWorkshopsInfrastructure,
    CivicHealthInfrastructure,
    SettlementInfrastructureProfile,
    SettlementYields,
    Settlement,
    BuildingStatus,
    FacilityType,
    Facility,
)

logger = logging.getLogger(__name__)


# =====================================================================
# Infrastructure Hierarchy Registry & Cascading Resolution Manager
# =====================================================================
class InfrastructureRegistry:
    """
    In-memory registry managing the 6-tier macro-to-micro hierarchy.
    Enforces instant O(1) top-down and bottom-up linkage.
    """
    def __init__(self):
        self.continents: Dict[str, Continent] = {}
        self.regions: Dict[str, Region] = {}
        self.nations: Dict[str, Nation] = {}
        self.settlements: Dict[str, Settlement] = {}
        self.facilities: Dict[str, Facility] = {}

    def register_continent(self, continent: Continent) -> None:
        self.continents[continent.id] = continent

    def register_region(self, region: Region) -> None:
        self.regions[region.id] = region
        if region.continent_id in self.continents:
            if region.id not in self.continents[region.continent_id].region_ids:
                self.continents[region.continent_id].region_ids.append(region.id)

    def register_nation(self, nation: Nation) -> None:
        self.nations[nation.id] = nation
        if nation.continent_id in self.continents:
            if nation.id not in self.continents[nation.continent_id].nation_ids:
                self.continents[nation.continent_id].nation_ids.append(nation.id)

    def register_settlement(self, settlement: Settlement) -> None:
        self.settlements[settlement.id] = settlement
        if settlement.nation_id in self.nations:
            if settlement.id not in self.nations[settlement.nation_id].settlement_ids:
                self.nations[settlement.nation_id].settlement_ids.append(settlement.id)
        if settlement.region_id in self.regions:
            if settlement.id not in self.regions[settlement.region_id].settlement_ids:
                self.regions[settlement.region_id].settlement_ids.append(settlement.id)

    def register_facility(self, facility: Facility) -> None:
        self.facilities[facility.id] = facility
        if facility.settlement_id in self.settlements:
            st = self.settlements[facility.settlement_id]
            if facility.id not in st.facility_ids:
                st.facility_ids.append(facility.id)

            ftype = facility.facility_type
            if ftype in ["general_store", "blacksmith_forge", "apothecary_clinic", "tavern_inn"]:
                if facility.id not in st.commercial_shops:
                    st.commercial_shops.append(facility.id)
            if ftype in ["training_ground", "mage_tower_academy"]:
                if facility.id not in st.training_facilities:
                    st.training_facilities.append(facility.id)
            if ftype == "guild_hall":
                if facility.id not in st.guild_halls:
                    st.guild_halls.append(facility.id)
            if ftype == "roving_peddler_stall":
                if facility.id not in st.active_peddlers:
                    st.active_peddlers.append(facility.id)
            if facility.building_status in ["under_construction", "under_repair"]:
                if facility.id not in st.under_construction_facilities:
                    st.under_construction_facilities.append(facility.id)
            elif facility.building_status in ["ruined", "abandoned"]:
                if facility.id not in st.ruined_facilities:
                    st.ruined_facilities.append(facility.id)
            if facility.is_wonder:
                if facility.id not in st.world_wonders:
                    st.world_wonders.append(facility.id)

    # -----------------------------------------------------------------
    # Cascading Bottom-Up Hierarchy Resolution
    # -----------------------------------------------------------------
    def resolve_hierarchy(self, facility_id: str) -> Dict[str, Any]:
        """
        Instant O(1) bottom-up lookup resolving:
        Facility -> Settlement -> Nation & Region -> Continent
        """
        facility = self.facilities.get(facility_id)
        if not facility:
            return {}

        settlement = self.settlements.get(facility.settlement_id)
        nation = self.nations.get(settlement.nation_id) if settlement else None
        region = self.regions.get(settlement.region_id) if settlement else None
        continent_id = nation.continent_id if nation else (region.continent_id if region else "")
        continent = self.continents.get(continent_id) if continent_id else None

        return {
            "facility": facility,
            "settlement": settlement,
            "nation": nation,
            "region": region,
            "continent": continent,
        }

    # -----------------------------------------------------------------
    # Cascading Commercial Calculation (Region Natural Price + Nation Tariff)
    # -----------------------------------------------------------------
    def calculate_effective_price(
        self,
        item_category: str,
        base_price: int,
        facility_id: str,
        buyer_nation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates realistic trade price:
        1. Region Natural Multiplier (abundance vs scarcity)
        2. Nation Import Tariff (if buyer is from a different nation)
        3. Diplomatic modifier (embargo or penalty if at war)
        """
        path = self.resolve_hierarchy(facility_id)
        region: Optional[Region] = path.get("region")
        nation: Optional[Nation] = path.get("nation")

        cat_norm = item_category.strip().lower()
        region_mult = 1.0
        if region and cat_norm in region.natural_price_multipliers:
            region_mult = region.natural_price_multipliers[cat_norm]

        tariff_mult = 1.0
        tariff_applied = 0.0
        diplomatic_status = "domestic"

        if nation and buyer_nation_id and buyer_nation_id != nation.id:
            # Cross-border transaction
            relation = nation.diplomatic_relations.get(buyer_nation_id, "neutral")
            diplomatic_status = relation

            if relation == "at_war":
                # Wartime trade embargo: extreme black-market surcharge or refusal
                tariff_applied = 1.0  # 100% penalty
            elif relation == "hostile":
                tariff_applied = nation.tariff_rate * 2.0
            elif relation == "allied":
                tariff_applied = nation.tariff_rate * 0.5  # Free trade discount
            else:
                tariff_applied = nation.tariff_rate

            tariff_mult = 1.0 + tariff_applied

        final_price = max(1, int(base_price * region_mult * tariff_mult))

        return {
            "base_price": base_price,
            "final_price": final_price,
            "region_multiplier": region_mult,
            "tariff_rate": tariff_applied,
            "tariff_multiplier": tariff_mult,
            "diplomatic_status": diplomatic_status,
            "region_name": region.name if region else "미지의 권역",
            "nation_name": nation.name if nation else "무국적 영지",
        }

    # -----------------------------------------------------------------
    # Cross-Border Checkpoint & Smuggling Verification
    # -----------------------------------------------------------------
    def check_border_entry(
        self,
        player_nation_id: str,
        destination_settlement_id: str,
        player_has_passport: bool,
        inventory_items: List[str]
    ) -> Dict[str, Any]:
        """
        Checks legal entry into a settlement's nation:
        - Passport check if entering from outside and passport is required
        - Contraband detection
        - Diplomatic status check
        """
        settlement = self.settlements.get(destination_settlement_id)
        if not settlement:
            return {"allowed": True, "reason": "정주지 정보 없음 (자유 통행)"}

        nation = self.nations.get(settlement.nation_id)
        if not nation:
            return {"allowed": True, "reason": "국가 소속 없음 (자유 통행)"}

        is_foreign = player_nation_id != nation.id
        relation = nation.diplomatic_relations.get(player_nation_id, "neutral") if is_foreign else "domestic"

        if is_foreign and relation == "at_war":
            return {
                "allowed": False,
                "reason": f"적대 국가 [{nation.name}]와의 전면전 상태로 인해 국경 관문이 전면 봉쇄되었습니다.",
                "confiscated_items": [],
                "alert_level": "전시",
                "is_combat_trigger": True
            }

        if is_foreign and nation.passport_required and not player_has_passport:
            return {
                "allowed": False,
                "reason": f"[{nation.name}]의 정식 국경 통행증(비자)이 없어 입국이 거부되었습니다.",
                "confiscated_items": [],
                "alert_level": nation.military_alert_level,
                "is_combat_trigger": False
            }

        # Contraband check
        contraband_detected = []
        for it in inventory_items:
            it_lower = it.lower()
            for cb in nation.contraband:
                if cb.lower() in it_lower:
                    contraband_detected.append(it)
                    break

        if contraband_detected:
            return {
                "allowed": False,
                "reason": f"[{nation.name}]의 금기/밀수품({', '.join(contraband_detected)})이 관문 수색견에게 적발되었습니다!",
                "confiscated_items": contraband_detected,
                "alert_level": "경계",
                "is_combat_trigger": True
            }

        return {
            "allowed": True,
            "reason": f"[{nation.name}]의 [{settlement.name}] 국경 관문을 정식 통과했습니다.",
            "confiscated_items": [],
            "alert_level": nation.military_alert_level,
            "is_combat_trigger": False
        }

    # -----------------------------------------------------------------
    # Cascading Specialty Goods Resolution (3-Tier Specialties)
    # -----------------------------------------------------------------
    def resolve_specialties(self, settlement_id: str) -> Dict[str, Any]:
        """
        Resolves 3-tier specialty hierarchy for a given settlement:
        1. Local 향토 특산품 (Settlement)
        2. National 제조/전매 특산품 (Nation)
        3. Regional 기후/천연 특산품 (Region)
        """
        settlement = self.settlements.get(settlement_id)
        if not settlement:
            return {"settlement": [], "nation": [], "region": [], "all": []}

        nation = self.nations.get(settlement.nation_id) if settlement.nation_id else None
        region = self.regions.get(settlement.region_id) if settlement.region_id else None

        s_specs = list(settlement.specialties)
        n_specs = list(nation.specialties) if nation else []
        r_specs = list(region.specialties) if region else []

        all_specs = list(dict.fromkeys(s_specs + n_specs + r_specs))

        return {
            "settlement": s_specs,
            "nation": n_specs,
            "region": r_specs,
            "all": all_specs,
            "settlement_name": settlement.name,
            "nation_name": nation.name if nation else "",
            "region_name": region.name if region else ""
        }

    # -----------------------------------------------------------------
    # Cascading Rare Mineral & Natural Resource Resolution (4-Tier)
    # -----------------------------------------------------------------
    def resolve_natural_resources(self, settlement_id: str) -> Dict[str, Any]:
        """
        Resolves 4-tier mineral and rare natural resource hierarchy for a given settlement:
        1. Local 물리 채굴 노드 (Settlement: local_resource_nodes)
        2. National 독점/전매 전략 자원 (Nation: monopoly_strategic_resources)
        3. Regional 지하 희소 광맥 & 고유 생체 자원 (Region: rare_mineral_deposits, endemic_biological_resources, strategic_deposits)
        4. Continental 고유 희귀 근원 자원 (Continent: endemic_continental_resources)
        """
        settlement = self.settlements.get(settlement_id)
        if not settlement:
            return {
                "local_nodes": [],
                "national_monopolies": [],
                "regional_minerals": [],
                "regional_biologicals": [],
                "regional_strategic_deposits": [],
                "continental_endemic": [],
                "all_rare_resources": []
            }

        nation = self.nations.get(settlement.nation_id) if settlement.nation_id else None
        region = self.regions.get(settlement.region_id) if settlement.region_id else None
        continent = None
        if region and region.continent_id:
            continent = self.continents.get(region.continent_id)
        elif nation and nation.continent_id:
            continent = self.continents.get(nation.continent_id)

        local_nodes = list(settlement.local_resource_nodes)
        national_monopolies = list(nation.monopoly_strategic_resources) if nation else []
        regional_minerals = list(region.rare_mineral_deposits) if region else []
        regional_biologicals = list(region.endemic_biological_resources) if region else []
        regional_strategic = list(region.strategic_deposits) if region else []
        continental_endemic = list(continent.endemic_continental_resources) if continent else []

        combined = list(dict.fromkeys(
            local_nodes + national_monopolies + regional_minerals + regional_biologicals + regional_strategic + continental_endemic
        ))

        return {
            "local_nodes": local_nodes,
            "national_monopolies": national_monopolies,
            "regional_minerals": regional_minerals,
            "regional_biologicals": regional_biologicals,
            "regional_strategic_deposits": regional_strategic,
            "continental_endemic": continental_endemic,
            "all_rare_resources": combined,
            "settlement_name": settlement.name,
            "nation_name": nation.name if nation else "",
            "region_name": region.name if region else "",
            "continent_name": continent.name if continent else ""
        }

    # -----------------------------------------------------------------
    # Cascading Bottom-Up Aggregate Calculation (Roll-up)
    # -----------------------------------------------------------------
    def recalculate_totals(self) -> None:
        """
        Recalculates bottom-up aggregate population and area across all tiers:
        Settlements -> Nations & Regions -> Continents.
        """
        # Reset totals
        for nat in self.nations.values():
            nat.population = 0
            nat.area_sq_km = 0.0
        for reg in self.regions.values():
            reg.population = 0
            reg.area_sq_km = 0.0
        for cont in self.continents.values():
            cont.population = 0
            cont.area_sq_km = 0.0

        # Roll-up from settlements
        for s in self.settlements.values():
            if s.nation_id in self.nations:
                self.nations[s.nation_id].population += s.population
                self.nations[s.nation_id].area_sq_km += s.area_sq_km
            if s.region_id in self.regions:
                self.regions[s.region_id].population += s.population
                self.regions[s.region_id].area_sq_km += s.area_sq_km

            # Roll-up to continent (via nation or region)
            cont_id = ""
            if s.nation_id in self.nations and self.nations[s.nation_id].continent_id:
                cont_id = self.nations[s.nation_id].continent_id
            elif s.region_id in self.regions and self.regions[s.region_id].continent_id:
                cont_id = self.regions[s.region_id].continent_id

            if cont_id and cont_id in self.continents:
                self.continents[cont_id].population += s.population
                self.continents[cont_id].area_sq_km += s.area_sq_km

    def get_world_totals(self) -> Dict[str, Any]:
        """Returns total population and area across all continents."""
        self.recalculate_totals()
        total_pop = sum(c.population for c in self.continents.values())
        total_area = sum(c.area_sq_km for c in self.continents.values())
        return {
            "total_population": total_pop,
            "total_area_sq_km": total_area
        }

    # -----------------------------------------------------------------
    # Cascading 5-Dimension Lifestyle Resolution (Attire, Cuisine, Culture, Logistics)
    # -----------------------------------------------------------------
    def resolve_settlement_lifestyle(self, settlement_id: str) -> Dict[str, Any]:
        """
        Cascades and merges lifestyle dimensions (Attire, Cuisine, Culture, Logistics)
        across Settlement -> Nation -> Region -> Continent.
        """
        settlement = self.settlements.get(settlement_id)
        if not settlement:
            return {}

        nation = self.nations.get(settlement.nation_id) if settlement.nation_id else None
        region = self.regions.get(settlement.region_id) if settlement.region_id else None
        continent_id = nation.continent_id if nation else (region.continent_id if region else "")
        continent = self.continents.get(continent_id) if continent_id else None

        def combine_lists(*profiles, attr: str):
            res = []
            for p in profiles:
                if p and hasattr(p, attr):
                    res.extend(getattr(p, attr))
            return list(dict.fromkeys(res))

        def combine_dicts(*profiles, attr: str):
            res = {}
            for p in profiles:
                if p and hasattr(p, attr):
                    res.update(getattr(p, attr))
            return res

        # Attire
        attires = [p for p in [continent.attire if continent else None, region.attire if region else None, nation.attire if nation else None, settlement.attire] if p]
        combined_attire = {
            "labor_lower_class": combine_lists(*attires, attr="labor_lower_class"),
            "middle_practical_class": combine_lists(*attires, attr="middle_practical_class"),
            "upper_ruling_class": combine_lists(*attires, attr="upper_ruling_class"),
            "special_organizations": combine_dicts(*attires, attr="special_organizations"),
        }

        # Cuisine
        cuisines = [p for p in [continent.cuisine if continent else None, region.cuisine if region else None, nation.cuisine if nation else None, settlement.cuisine] if p]
        combined_cuisine = {
            "staples": combine_lists(*cuisines, attr="staples"),
            "proteins_and_salts": combine_lists(*cuisines, attr="proteins_and_salts"),
            "expedition_rations": combine_lists(*cuisines, attr="expedition_rations"),
            "beverages_and_water": combine_lists(*cuisines, attr="beverages_and_water"),
        }

        # Culture
        cultures = [p for p in [continent.culture if continent else None, region.culture if region else None, nation.culture if nation else None, settlement.culture] if p]
        combined_culture = {
            "social_structure": combine_lists(*cultures, attr="social_structure"),
            "faith_and_beliefs": combine_lists(*cultures, attr="faith_and_beliefs"),
            "commercial_customs": combine_lists(*cultures, attr="commercial_customs"),
            "seasonal_events": combine_lists(*cultures, attr="seasonal_events"),
        }

        # Logistics & Vehicles
        vehicles = []
        if nation and nation.logistics:
            vehicles.extend(nation.logistics.transit_vehicles)
        if settlement and settlement.logistics:
            vehicles.extend(settlement.logistics.transit_vehicles)

        return {
            "settlement_name": settlement.name,
            "nation_name": nation.name if nation else "",
            "region_name": region.name if region else "",
            "continent_name": continent.name if continent else "",
            "attire": combined_attire,
            "cuisine": combined_cuisine,
            "culture": combined_culture,
            "transit_vehicles": vehicles,
        }

    # -----------------------------------------------------------------
    # Inter-Tier Route Network Management (Nations, Regions, Continents)
    # -----------------------------------------------------------------
    def register_inter_tier_route(self, route: InterTierRoute, tier: str = "nation") -> None:
        """Registers a cross-border or cross-region route to the corresponding entity."""
        if tier == "continent" and route.origin_id in self.continents:
            self.continents[route.origin_id].continental_routes.append(route)
        elif tier == "region" and route.origin_id in self.regions:
            self.regions[route.origin_id].regional_corridors.append(route)
        elif tier == "nation" and route.origin_id in self.nations:
            self.nations[route.origin_id].international_highways.append(route)

    def find_inter_tier_routes(self, entity_id: str) -> List[InterTierRoute]:
        """Finds all inter-tier routes connected to an entity (continent, region, nation)."""
        routes = []
        for c in self.continents.values():
            for r in c.continental_routes:
                if r.origin_id == entity_id or r.destination_id == entity_id:
                    routes.append(r)
        for reg in self.regions.values():
            for r in reg.regional_corridors:
                if r.origin_id == entity_id or r.destination_id == entity_id:
                    routes.append(r)
        for n in self.nations.values():
            for r in n.international_highways:
                if r.origin_id == entity_id or r.destination_id == entity_id:
                    routes.append(r)
        return routes

    # -----------------------------------------------------------------
    # Deterministic Settlement Resilience & Survival Infrastructure Audit
    # -----------------------------------------------------------------
    def audit_settlement_resilience(self, settlement_id: str) -> Dict[str, Any]:
        """
        Audits settlement survival resilience and community viability based on
        the 5-sector infrastructure profile, active facilities, and environmental metrics.
        Returns deterministic ratings and vulnerability flags for gameplay engines.
        """
        settlement = self.settlements.get(settlement_id)
        if not settlement:
            return {"error": "settlement_not_found"}

        infra = settlement.infrastructure
        vulnerabilities: List[str] = []

        # 1. Water Survival Audit
        water_sources_count = len(infra.sanitation.water_sources)
        water_score = infra.sanitation.water_capacity_rating * 0.5 + min(50.0, water_sources_count * 25.0)
        if water_sources_count == 0 and settlement.self_sufficiency_water < 50:
            vulnerabilities.append("상수원_부재_식수위기")

        # 2. Winter Food Security Audit
        food_months = infra.food.storage_reserve_months
        food_processing_count = len(infra.food.grain_processing) + len(infra.food.communal_cooking_preserving)
        food_score = min(100.0, (food_months / 6.0) * 50.0 + min(50.0, food_processing_count * 25.0))
        if food_months < 1.0:
            vulnerabilities.append("식량비축_부족_겨울기근위험")
        if food_processing_count == 0:
            vulnerabilities.append("곡물가공_시설결여")

        # 3. Epidemic Resilience Audit
        waste_handling = len(infra.sanitation.drainage_and_sewage) + len(infra.sanitation.public_sanitation)
        medical_presence = len(infra.civic.medical_and_relief)
        epidemic_score = (
            infra.sanitation.waste_treatment_rating * 0.3 +
            min(40.0, waste_handling * 15.0) +
            infra.civic.healthcare_rating * 0.3
        )
        if waste_handling == 0 and settlement.hygiene_level < 60:
            vulnerabilities.append("하수시설_미비_역병위험")
        if medical_presence == 0 and settlement.population > 500:
            vulnerabilities.append("의료구호_시설부재")

        # 4. Fire and Defense Safety Audit
        disaster_prep = len(infra.defense.disaster_prevention)
        barrier_count = len(infra.defense.physical_barriers)
        defense_score = (
            infra.defense.fortification_integrity * 0.3 +
            infra.defense.fire_preparedness_rating * 0.3 +
            settlement.security_level * 0.4
        )
        if disaster_prep == 0:
            vulnerabilities.append("방재경보_부재_화재취약")
        if barrier_count == 0 and settlement.wall_defense_tier == 0:
            vulnerabilities.append("물리방벽_전무_침입취약")

        # 5. Civic and Social Vitality Audit
        civic_count = len(infra.civic.governance_and_assembly) + len(infra.civic.faith_and_shrines)
        trade_count = len(infra.trade.artisan_workshops) + len(infra.trade.distribution_hubs)
        vitality_score = (
            infra.civic.social_cohesion_rating * 0.4 +
            infra.trade.production_vitality_rating * 0.4 +
            min(20.0, (civic_count + trade_count) * 5.0)
        )
        if civic_count == 0:
            vulnerabilities.append("공동체의사결정_구심점부재")

        overall_score = round(
            (water_score * 0.25 + food_score * 0.25 + epidemic_score * 0.20 + defense_score * 0.15 + vitality_score * 0.15),
            1
        )

        return {
            "settlement_id": settlement_id,
            "settlement_name": settlement.name,
            "development_tier": settlement.development_tier,
            "water_survival_score": round(water_score, 1),
            "food_reserve_score": round(food_score, 1),
            "epidemic_resilience_score": round(epidemic_score, 1),
            "defense_security_score": round(defense_score, 1),
            "civic_vitality_score": round(vitality_score, 1),
            "overall_resilience_score": overall_score,
            "vulnerabilities": vulnerabilities,
            "is_critical_hazard": len(vulnerabilities) >= 3,
        }

    # -----------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "continents": {k: v.to_dict() for k, v in self.continents.items()},
            "regions": {k: v.to_dict() for k, v in self.regions.items()},
            "nations": {k: v.to_dict() for k, v in self.nations.items()},
            "settlements": {k: v.to_dict() for k, v in self.settlements.items()},
            "facilities": {k: v.to_dict() for k, v in self.facilities.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InfrastructureRegistry":
        reg = cls()
        for k, v in data.get("continents", {}).items():
            reg.continents[k] = Continent.from_dict(v)
        for k, v in data.get("regions", {}).items():
            reg.regions[k] = Region.from_dict(v)
        for k, v in data.get("nations", {}).items():
            reg.nations[k] = Nation.from_dict(v)
        for k, v in data.get("settlements", {}).items():
            reg.settlements[k] = Settlement.from_dict(v)
        for k, v in data.get("facilities", {}).items():
            reg.facilities[k] = Facility.from_dict(v)
        return reg



# Re-export loader at bottom for 100% backward compatibility
from .infra_loader import InfrastructureTemplateLoader

__all__ = [
    "InterTierRoute",
    "TransitVehicle",
    "LogisticsNetwork",
    "AttireHierarchyProfile",
    "CuisineProfile",
    "CulturalNormsProfile",
    "_safe_profile",
    "_safe_routes",
    "Continent",
    "Region",
    "Nation",
    "FacilityCategory",
    "SanitationWaterInfrastructure",
    "FoodStorageInfrastructure",
    "DefenseSecurityInfrastructure",
    "TradeWorkshopsInfrastructure",
    "CivicHealthInfrastructure",
    "SettlementInfrastructureProfile",
    "SettlementYields",
    "Settlement",
    "BuildingStatus",
    "FacilityType",
    "Facility",
    "InfrastructureRegistry",
    "InfrastructureTemplateLoader",
]
