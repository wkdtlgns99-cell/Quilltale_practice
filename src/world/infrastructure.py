"""
6-Tier Macro-to-Micro Realistic World Infrastructure Engine for Quilltale TRPG.
Hierarchy:
Level 0: World/Cosmology (Ancient Magic Words, Mana Origin, Celestial Cycles - in WorldState)
Level 1: Continent (Tectonic Plate, Common Language, Historical Era)
Level 2: Region (10-Terrain Biome, Natural Price Matrix, Climate & Hazards)
Level 3: Nation (Sovereign Borders, Laws & Taboos, Currency, Tariffs, Diplomacy)
Level 4: Settlement (City/Town/Village, Coordinates, Demographics, Security, Self-Sufficiency)
Level 5: Facility (Shops, Blacksmiths, Academies, Temples, Gates, Taverns, Dungeons)
"""
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
import logging
import random

from src.core.config import TEMPLATES_DIR
from src.world.geography import RoadConnection, RouteCategory

logger = logging.getLogger(__name__)


# =====================================================================
# Supporting Infrastructure Schemas (Generic & Non-Hardcoded)
# =====================================================================
@dataclass
class InterTierRoute:
    origin_id: str
    destination_id: str
    route_name: str = ""
    route_category: RouteCategory = RouteCategory.BRANCH_ROAD
    distance_km: float = 10.0
    travel_medium: str = "land"                         # "land" | "water" | "air" | "magical"
    toll_fee: int = 0
    is_bottleneck: bool = False
    bottleneck_type: str = ""                           # 병목 유형 (예: "관문", "협곡", "국경", "해협")
    supply_facilities: List[str] = field(default_factory=list) # 보급 시설 (예: ["역참", "항구", "오아시스"])
    allowed_transit_types: List[str] = field(default_factory=list) # 통행 허용 운송수단 범주
    traits: List[str] = field(default_factory=list)     # 가도/항로 요약 특성 태그 (예: ["도적 출몰 가도", "폭설 차단 위험", "왕실 순찰로"])
    description: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        if isinstance(self.route_category, RouteCategory):
            d["route_category"] = self.route_category.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "InterTierRoute":
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        if "route_category" in filtered and isinstance(filtered["route_category"], str):
            try:
                filtered["route_category"] = RouteCategory(filtered["route_category"])
            except ValueError:
                filtered["route_category"] = RouteCategory.BRANCH_ROAD
        return cls(**filtered)


@dataclass
class TransitVehicle:
    id: str
    name: str
    category: str = "land"                              # "land" (육상), "water" (수상), "special" (특수/비행/마도)
    base_speed_kmh: float = 4.0
    cargo_capacity_kg: float = 0.0
    passenger_capacity: int = 1
    terrain_compatibility: List[str] = field(default_factory=list) # 주행 가능 지형/수로
    daily_maintenance_cost: int = 0                     # 일일 유지/사료 비용
    traits: List[str] = field(default_factory=list)     # 운송 수단 요약 특성 태그 (예: ["장갑 보강", "마도 부유", "쾌속"])
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TransitVehicle":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class LogisticsNetwork:
    caravan_routes: List[Dict[str, Any]] = field(default_factory=list) # 상단 호위대 순회 경로
    courier_relays: List[str] = field(default_factory=list)            # 전령망 거점/역참 목록
    postal_stations: List[str] = field(default_factory=list)           # 우편/긴급 통신소 목록
    transit_vehicles: List[TransitVehicle] = field(default_factory=list) # 운송 수단/차량 목록

    def to_dict(self) -> dict:
        d = asdict(self)
        d["transit_vehicles"] = [v.to_dict() if hasattr(v, "to_dict") else v for v in self.transit_vehicles]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "LogisticsNetwork":
        vehicles = [TransitVehicle.from_dict(v) if isinstance(v, dict) else v for v in data.get("transit_vehicles", [])]
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__ and k != "transit_vehicles"}
        return cls(transit_vehicles=vehicles, **filtered)


@dataclass
class AttireHierarchyProfile:
    labor_lower_class: List[str] = field(default_factory=list)       # 하층/노동 계층 복식 (내구성 중심 직물, 작업복)
    middle_practical_class: List[str] = field(default_factory=list)  # 중간/실무 계층 복식 (활동성 경갑, 방수 외투)
    upper_ruling_class: List[str] = field(default_factory=list)      # 상류/지배 계층 복식 (고급 섬유, 상징 문장)
    special_organizations: Dict[str, str] = field(default_factory=dict) # 특수 집단 복제 (교단 사제복, 기사단 제복 등)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AttireHierarchyProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CuisineProfile:
    staples: List[str] = field(default_factory=list)                 # 기본 주식 (곡물 가공품, 감자/뿌리채소 등)
    proteins_and_salts: List[str] = field(default_factory=list)      # 단백질 및 염분 (육류, 생선 염장품, 치즈 등)
    expedition_rations: List[str] = field(default_factory=list)      # 원정 및 휴대식 (건빵, 육포, 보존유 등)
    beverages_and_water: List[str] = field(default_factory=list)     # 기호품 및 수자원 (발효주, 향신료, 찻잎, 정수원 등)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CuisineProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CulturalNormsProfile:
    social_structure: List[str] = field(default_factory=list)        # 사회 제도 (주종 관계, 길드 자치 규약 등)
    faith_and_beliefs: List[str] = field(default_factory=list)       # 신앙 체계 (수호신 숭배, 자연 정령관, 장례 금기 등)
    commercial_customs: List[str] = field(default_factory=list)      # 상업 규범 (화폐 규격, 물물교환, 계약 체결 등)
    seasonal_events: List[str] = field(default_factory=list)         # 계절 및 주기 행사 (수확제, 천체 주기 금기일, 성인식 등)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CulturalNormsProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def _safe_profile(profile_cls, val):
    if isinstance(val, dict):
        return profile_cls.from_dict(val)
    elif isinstance(val, profile_cls):
        return val
    return profile_cls()


def _safe_routes(val):
    if not isinstance(val, list):
        return []
    return [InterTierRoute.from_dict(r) if isinstance(r, dict) else r for r in val]


# =====================================================================
# Level 1: Continent (대륙)
# =====================================================================
@dataclass
class Continent:
    id: str
    name: str                                           # 대륙명
    common_language: str = "대륙 공통어"                 # 대륙 공통 필멸자 언어
    mortal_species: List[str] = field(default_factory=list) # 대륙 내 공존하는 의사소통 가능한 휴머노이드 필멸자 지성체 종족 목록 (인간, 엘프, 드워프, 수인, 오크 등)
    era_background: str = ""                            # 대륙 역사 연대기 및 문명 수준
    plate_name: str = ""                                # 지질 판 / 대륙 지형 기반
    climate_zones: List[str] = field(default_factory=list) # 대륙 내 기후대
    region_ids: List[str] = field(default_factory=list) # 소속 지리/기후 권역 ID 목록
    nation_ids: List[str] = field(default_factory=list) # 소속 국가 ID 목록
    population: int = 0                                 # 대륙 총 거주 인구
    area_sq_km: float = 0.0                             # 대륙 총 면적 (km²)
    continental_treaty: str = ""                        # 대륙 전역 공통 불가침/금기 조약 (예: "성역 불침 조약", "대륙 노예무역 전면 금지 조약")
    dominant_trade_coalition: str = ""                  # 대륙 전역 상권을 좌지우지하는 초국가 거대 상인 동맹 (예: "한자동맹", "황금 삼각 상단")
    dominant_tycoon_npc_id: str = ""                    # 대륙 최고 거상/상단 연합 총수 NPC ID 포인터
    continental_apex_champion_npc_id: str = ""          # 대륙 최강자 NPC ID 포인터
    continental_apex_champion_sketch: Dict[str, Any] = field(default_factory=dict) # 대륙 최강자 스케치 프로필 (name, title, traits, combat_style 등)
    continental_apex_monster_id: str = ""               # 대륙 최강 몬스터/개체 ID 포인터
    continental_apex_monster_sketch: Dict[str, Any] = field(default_factory=dict)  # 대륙 최강 몬스터 스케치 프로필 (name, classification, traits, threat_level, description 등)
    continental_chokepoints: List[str] = field(default_factory=list) # 대륙 관문 해협/지협/대협곡 등 전략적 병목 통로 목록
    tectonic_instability_rating: int = 20               # 대륙 판 지질 불안정도 (0~100, 높을수록 화산 분화 및 지진 해일 빈도 증가)
    continental_forbidden_zones: List[str] = field(default_factory=list) # 신벌/낙진/고대 결계로 격리된 대륙 전역 출입 금기 구역
    standard_physique_archetype: str = "humanoid_medium" # 대륙 주류 표준 체형 골격 (노획 장비 리사이징 기준: "humanoid_medium", "dwarven_broad", "beastfolk_large")
    endemic_continental_resources: List[str] = field(default_factory=list) # 대륙 고유 희귀 근원 자원 (다른 대륙엔 없는 고유 자원: 미스릴 원석, 세계수 수액, 용골 화석 등)
    ancient_titan_remains: List[str] = field(default_factory=list) # 대륙을 형성하는 잠든 고대 거신/시조룡의 유해 지형 목록 (예: ["거신 이미르의 늑골 산맥", "세계뱀의 등뼈"])
    leyline_network_scale: str = "medium"               # 대륙 전역을 관통하는 거대 마나 지맥 규모 ("sparse", "medium", "dense", "wild_surge")
    continental_routes: List[InterTierRoute] = field(default_factory=list) # 대륙 간 원양 해로/항로/차원문
    culture: CulturalNormsProfile = field(default_factory=CulturalNormsProfile) # 대륙 단위 문화/신앙 원형
    cuisine: CuisineProfile = field(default_factory=CuisineProfile) # 대륙 식생/식문화 원형
    attire: AttireHierarchyProfile = field(default_factory=AttireHierarchyProfile) # 대륙 복식 양식
    traits: List[str] = field(default_factory=list)     # 대륙 고유 특성 태그 목록 (예: ["가이아의 각성", "마나 과포화", "풍요로운 신대륙"])
    compatible_genres: List[str] = field(default_factory=list) # 호환 세계관 장르 목록 (예: ["정통 하이 판타지", "다크 판타지"])
    suggested_regions: List[str] = field(default_factory=list) # 추천 소속 권역 ID/유형 목록
    dominant_tycoon_sketch: Dict[str, Any] = field(default_factory=dict) # 대륙 최고 거상/상단 스케치 프로필
    description: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["continental_routes"] = [r.to_dict() if hasattr(r, "to_dict") else r for r in self.continental_routes]
        d["culture"] = self.culture.to_dict()
        d["cuisine"] = self.cuisine.to_dict()
        d["attire"] = self.attire.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Continent":
        clean = dict(data)
        clean["continental_routes"] = _safe_routes(data.get("continental_routes", []))
        clean["culture"] = _safe_profile(CulturalNormsProfile, data.get("culture"))
        clean["cuisine"] = _safe_profile(CuisineProfile, data.get("cuisine"))
        clean["attire"] = _safe_profile(AttireHierarchyProfile, data.get("attire"))

        # Normalize compatible_genres (dict or list)
        cg = data.get("compatible_genres", [])
        if isinstance(cg, dict):
            genres = []
            if "primary" in cg and cg["primary"]:
                genres.append(str(cg["primary"]))
            if "sub" in cg and isinstance(cg["sub"], list):
                genres.extend(str(s) for s in cg["sub"] if s)
            clean["compatible_genres"] = genres
        elif isinstance(cg, list):
            clean["compatible_genres"] = [str(g) for g in cg if g]

        # Normalize suggested_regions (dict or list)
        sr = data.get("suggested_regions", [])
        if isinstance(sr, dict):
            clean["suggested_regions"] = [str(v) for v in sr.values() if v]
        elif isinstance(sr, list):
            clean["suggested_regions"] = [str(r) for r in sr if r]

        # Normalize dominant_tycoon_sketch
        ts = data.get("dominant_tycoon_sketch", {})
        if isinstance(ts, dict):
            clean["dominant_tycoon_sketch"] = dict(ts)

        # Normalize continental_apex_champion_sketch
        cs = data.get("continental_apex_champion_sketch", {})
        if isinstance(cs, dict):
            clean["continental_apex_champion_sketch"] = dict(cs)

        # Normalize continental_apex_monster_sketch
        ms = data.get("continental_apex_monster_sketch", {})
        if isinstance(ms, dict):
            clean["continental_apex_monster_sketch"] = dict(ms)

        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


# =====================================================================
# Level 2: Region (지리/기후 권역)
# =====================================================================
@dataclass
class Region:
    id: str
    name: str                                           # 권역명 (예: "칼날 산맥 피오르드", "마력 침식 수정 사막")
    continent_id: str                                   # 소속 대륙 ID
    terrain: str = "plains"                             # 10대 지형 ("coastal_port", "mountain_mine", "frozen_tundra" 등)
    climate_type: str = "온대 습윤"                      # 기후대 ("혹한대", "건조대", "온대", "열대")
    natural_price_multipliers: Dict[str, float] = field(default_factory=dict) # 자연 자원 물가 배율 (소금, 철, 물 등)
    survival_hazards: List[str] = field(default_factory=list) # 환경 위험 (혹한 결빙, 유독 포자, 모래폭풍)
    visibility_meters: int = 50                         # 기본 시야 거리 (m)
    noise_occlusion: int = 50                           # 환경 음향 차폐율 (% 0~100, 0: 완전 열림, 50: 보통, 100: 완전 방음/차폐)
    common_monsters: List[str] = field(default_factory=list) # 생태계 서식 마수 목록
    settlement_ids: List[str] = field(default_factory=list)  # 소속 정주지 ID 목록
    population: int = 0                                 # 권역 내 총 거주 인구
    area_sq_km: float = 0.0                             # 권역 총 면적 (km²)
    specialties: List[str] = field(default_factory=list) # 기후/지형에 따른 권역 전역 천연 특산품/자원 (소금, 철광석, 극지 모피 등)
    natural_hazards: List[str] = field(default_factory=list) # 권역 거대 자연재해 취약성 (대홍수 범람, 화산 분화, 지진 단층, 블리자드)
    strategic_deposits: List[str] = field(default_factory=list) # 천연 전략 자원 매장/서식지 (철광맥, 군마 초원, 초석 동굴, 마력 수정맥)
    rare_mineral_deposits: List[str] = field(default_factory=list) # 지질/지하 희소 광맥 (오리하르콘 광맥, 천연 유황 동굴, 심층 마나 수정맥 등)
    endemic_biological_resources: List[str] = field(default_factory=list) # 기후 고유 희귀 생체/약초 자원 (만년설 설련화, 심연 발광 포자, 화염 도마뱀 쓸개 등)
    natural_wonders: List[str] = field(default_factory=list) # 권역 자연 불가사의 (살아있는 세계수, 마나 폭포 협곡 등)
    planar_instability: int = 0                         # 차원 경계 불안정도 (0~100, 높을수록 이계 생명체 출현 및 마력 왜곡)
    planar_rifts: List[str] = field(default_factory=list) # 권역 내 차원 균열/아스트랄 틈새/정령계 포탈 목록
    archaeological_sites: List[str] = field(default_factory=list) # 권역 내 매장된 고대 문명 유적/던전 발굴터 목록
    environmental_toxicity: int = 0                     # 환경 독성 및 마나 낙진도 (0~100, 높을수록 방호구 없이 진입 시 중독/지속 피해)
    mana_density: int = 50                              # 권역 배경 마나 밀도 (0~100, 0~10: 침묵/마법불발, 11~30: 희박, 31~70: 보통, 71~90: 농축, 91~100: 야생마력)
    apex_predator_id: str = ""                          # 권역 최상위 포식자 몬스터 ID (생태계 먹이사슬 정점)
    regional_champion_npc_id: str = ""                  # 권역 내 필멸자 지성체 최강 NPC ID (은둔 고수/전설의 기사/대마법사)
    seasonal_temperature_range: Tuple[int, int] = (-5, 28) # 연중 최저/최고 기온 편차 (섭씨 ℃, 저체온증/열사병 엔진 기초값)
    foraging_abundance: int = 50                        # 야생 식생 채집 잠재력 (0~100, 0: 사막/황무지, 100: 풍요의 숲)
    water_source_reliability: int = 70                  # 야생 음용수/식수 확보 신뢰도 (0~100, 0: 극심한 갈증/사막, 100: 청정 담수호/하천)
    natural_shelters: List[str] = field(default_factory=list) # 야생 천연 대피처/은신처 목록 (예: ["풍식 절벽 동굴", "고목 밑둥", "바위 틈새"])
    predator_pack_density: int = 30                     # 맹수 무리/늑대 떼 군집도 (0~100, 야간 이동 및 야영 시 기습 확률)
    air_pressure_oxygen: int = 100                      # 산소 기압 및 대기 밀도 (0~100, 100: 평지, 40: 고산병, 10: 질식 위험)
    landslide_avalanche_risk: int = 10                  # 눈사태/산사태/낙석 위험도 (0~100, 폭발/소음 시 환경 붕괴 트리거)
    wind_direction_degrees: int = 0                     # 권역 기본 풍향 (0~359°, 산불/체취 은신/항해 연동)
    travel_difficulty: int = 50                         # 지형 횡단 험준도/이동속도 감속률 (0: 평탄한 대로, 50: 일반 험지, 100: 통행불가 늪/절벽)
    dominant_surface: str = "dirt"                      # 전술 기본 표면 재질 ("dirt", "dry_grass", "deep_mud", "loose_sand", "ice_sheet", "swamp_marsh", "cracked_stone")
    campsite_viability: int = 50                        # 야외 야영/캠핑 적합도 및 안전성 (0~100, 0: 기습 확정/휴식 불가, 100: 천연 바람막이 성소)
    wildfire_hazard_rating: int = 20                    # 산불/대화재 확산 취약도 (0~100, 화염 마법 및 낙뢰 시 연쇄 화재 위험)
    foliage_density: int = 50                           # 야생 수목/식생 밀도 (0~100, 시야 차폐, 화살 궤적 방해, 매복 보너스)
    river_crossing_dc: int = 12                         # 주요 하천/급류 도강 난이도 DC (도보/마차 도강 시 침수 및 유실 판정)
    campfire_detection_risk: int = 30                   # 야영 모닥불/연기 피울 시 야생 맹수/도적 유인 위험도 (0~100, 높을수록 야간 기습 확률 증가)
    watch_shift_visibility_bonus: int = 0               # 권역 지형/시야에 따른 야간 불침번 경계 감시 보정치 (-50: 빽빽한 밀림 ~ +50: 탁 트인 사막)
    draconic_presence_level: int = 0                    # 권역 내 용족/고룡 서식 위협도 (0: 없음, 1: 와이번/유룡, 2: 성룡 영역, 3: 고룡 동면/지배)
    dominant_elemental_affinity: str = "neutral"        # 권역 지배 속성 마나 편향 ("neutral", "fire", "ice", "lightning", "darkness", "holy", "wind", "earth")
    monster_stampede_risk: int = 15                     # 마수 번식기/마나 폭주 시 일어나는 마수 대침공/스탬피드 위험도 (0~100)
    resource_regeneration_rate: int = 50                # 남획 시 자연 자원 회복/재생 주기 속도 (0~100)
    nomadic_tribes: List[str] = field(default_factory=list) # 고정 정착지 없는 방랑 유목 부족/유랑 상단/켄타우로스 무리
    trade_node_name: str = ""                           # 권역이 속한 광역 무역 노드/교역권 명칭 (예: "발트해 무역망", "실크로드 대상로")
    regional_corridors: List[InterTierRoute] = field(default_factory=list) # 권역 간 고개/회랑/지협
    cuisine: CuisineProfile = field(default_factory=CuisineProfile) # 권역 생태계 기반 자연 식재료/식생
    attire: AttireHierarchyProfile = field(default_factory=AttireHierarchyProfile) # 권역 기후 적응형 복식
    culture: CulturalNormsProfile = field(default_factory=CulturalNormsProfile) # 권역 정령/토착 신앙 및 생활 규범
    traits: List[str] = field(default_factory=list)     # 권역 고유 특성 태그 목록 (예: ["혹한의 불모지", "용의 영지", "마력 수정 지대"])
    description: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["regional_corridors"] = [r.to_dict() if hasattr(r, "to_dict") else r for r in self.regional_corridors]
        d["cuisine"] = self.cuisine.to_dict()
        d["attire"] = self.attire.to_dict()
        d["culture"] = self.culture.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Region":
        clean = dict(data)
        clean["regional_corridors"] = _safe_routes(data.get("regional_corridors", []))
        clean["cuisine"] = _safe_profile(CuisineProfile, data.get("cuisine"))
        clean["attire"] = _safe_profile(AttireHierarchyProfile, data.get("attire"))
        clean["culture"] = _safe_profile(CulturalNormsProfile, data.get("culture"))
        if "seasonal_temperature_range" in clean and isinstance(clean["seasonal_temperature_range"], (list, tuple)):
            clean["seasonal_temperature_range"] = tuple(clean["seasonal_temperature_range"])
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


# =====================================================================
# Level 3: Nation (국가/영지)
# =====================================================================
@dataclass
class Nation:
    id: str
    name: str                                           # 국가명 (예: "아이언포지 광산왕국", "루멘 성왕국")
    continent_id: str                                   # 소속 대륙 ID
    dominant_species: List[str] = field(default_factory=list) # 국가 주요 구성 종족 목록 (인간, 엘프, 드워프, 수인 등)
    ruling_system: str = "봉건 왕정"                    # 정치 체제 ("왕정", "공화정", "마법 과두정", "군정", "도적 자치령")
    civilization_level: str = ""                        # 국가 기술/제도 문명 수준 (예: "마도공학 후기 중세", "초기 철기 부족제")
    monarch_title: str = "국왕"                         # 국가 원수 칭호 ("국왕", "황제", "대공", "대사제", "칸")
    monarch_npc_id: str = ""                            # 국가 원수/국왕 NPC ID
    ruling_dynasty: str = ""                            # 통치 왕조/가문명 (예: "루멘 왕조", "아이언포지 혈통")
    dynasty_legitimacy: int = 80                        # 왕조 정통성 (0~100, 낮을수록 찬탈/계승 분쟁 위험)
    succession_law: str = "장자상속"                     # 왕위 계승법 ("장자상속", "선거군주제", "분할상속", "찬탈위기")
    ruling_faction_id: str = ""                         # 통치 세력 ID (Faction ID)
    official_currency: str = "골드"                     # 공식 화폐 단위 ("크라운", "실버", "골드 드라크마")
    currency_exchange_rate: float = 1.0                 # 표준 화폐 대비 환율
    tariff_rate: float = 0.10                           # 국경 수입/수출 관세율 (0.0 ~ 0.5, 기본 10%)
    tax_rate: float = 0.10                              # 기본 내국/영지 세율 (0.0 ~ 0.5, 기본 10%)
    tax_burden: int = 30                                # 국내 세율 체감 수탈도 (0~100, 80 이상 시 민중 봉기/불만 폭증)
    national_treasury: int = 10000                      # 국고 잔고 (국가 화폐 단위)
    foreign_debt_gold: int = 0                          # 외채 및 금융 길드 차입금 (골드, 미상환 시 금융 제재/용병 침공)
    national_stability: int = 70                        # 국가 통치 안정도 (0~100, 낮을수록 내전/쿠데타 위험)
    vassal_loyalty_index: int = 70                      # 지방 영주/봉신 결속도 (0~100, 40 미만 시 전시 징집 거부 및 반란)
    war_weariness: int = 0                              # 전쟁 피로도 (0~100, 높을수록 징집 저항/불만 상승)
    bureaucratic_corruption: int = 0                    # 관료 행정 부패도 (0~100, 높을수록 세금 누수, 횡령, 뇌물)
    strategic_stockpiles: Dict[str, int] = field(default_factory=dict) # 국가 전략 비축물자 (예: {"철광석": 500, "군마": 120, "초석": 80})
    monopoly_strategic_resources: List[str] = field(default_factory=list) # 국가 독점 전매 및 수출 금지 전략 자원 (왕실 비전 초석, 고농축 마력석 등)
    national_mining_concessions: Dict[str, str] = field(default_factory=dict) # 영토 내 주요 광산 채굴권/조계지 장부 (mine_name -> 소유 길드/가문 ID)
    standing_army_size: int = 1000                      # 국가 정규 상비군 총 병력 수 (전쟁 시 동원되는 정규 전투력)
    knights_count: int = 100                            # 정예 기사단 / 중장기병 / 성기사 병력 수
    infantry_count: int = 600                           # 정규 보병 (장창병, 방패병, 검사 등) 병력 수
    ranged_corps_count: int = 200                       # 정규 원거리 병력 (궁병, 석궁병, 총사대 등) 병력 수
    cavalry_count: int = 100                            # 경기병 / 수색 기동대 병력 수
    siege_engine_count: int = 10                        # 공성 병기 수 (투석기, 공성포, 발리스타)
    beast_riders_count: int = 0                         # 마수 / 환수 기병 수 (그리폰, 와이번, 늑대 기병 등)
    special_military_units: Dict[str, int] = field(default_factory=dict) # 국가 고유 특수부대/정예 연대 (예: {"왕실 머스킷 총사대": 80, "흑철 도끼단": 120})
    military_manpower_pool: int = 10000                 # 국가 예비 인력 풀/맨파워 (상비군 손실 시 추가 징집 한계)
    naval_fleet_strength: int = 0                       # 국가 정규 군함 척수 (해양 제해권 및 수송로 호위력)
    legal_enforcement_efficiency: int = 60              # 사법 집행력 (0~100, 0: 법률 사문화/도적 묵인, 100: 무관용 즉결 처형)
    espionage_defense: int = 50                         # 국가 중앙 방첩망 강도 (0~100, 타국 첩보원/암살자 침투 차단율)
    border_openness: int = 50                           # 국경 개방도 (0~100, 0: 완전 쇄국/봉쇄, 50: 일반 통행증 검문, 100: 자유 왕래)
    trade_embargoes: List[str] = field(default_factory=list) # 무역 금수/경제 제재 대상국 ID 목록
    passport_required: bool = False                     # 타국인 통행증/비자 필수 여부
    border_checkpoints: List[str] = field(default_factory=list) # 국경 관문/검문소 시설 ID 목록
    laws: List[str] = field(default_factory=list)       # 국가 성문 법률 목록
    magic_prohibition_tier: int = 0                     # 국가 마법 규제 등급 (0: 자유 시전, 1: 면허증 필수, 2: 전투마법 엄금, 3: 마법사 화형/마녀사냥)
    ideological_climate: str = ""                       # 국가 지배 이념/정치 사상 ("전통 봉건주의", "급진 공화주의", "신정 근본주의", "군국 팽창주의")
    serfdom_or_slavery_legal: bool = False              # 농노제/노예제 합법 여부
    contraband: List[str] = field(default_factory=list) # 국가 금기/밀수품 목록 (예: "흑마법 스크롤", "노예")
    state_religion: str = ""                            # 공식 국교 (없으면 세속/다신교)
    religious_tolerance: int = 50                       # 종교 관용도 (0~100, 0~20: 신정 탄압/이단 심문, 21~50: 보통, 51~80: 온건, 81~100: 자유 다원주의)
    diplomatic_relations: Dict[str, str] = field(default_factory=dict) # target_nation_id -> "allied"|"neutral"|"hostile"|"at_war"
    diplomatic_treaties: Dict[str, List[str]] = field(default_factory=dict) # 타국과의 조약 (target_nation_id -> ["open_borders", "defensive_pact", "vassal_tribute", "trade_embargo"])
    active_wars: List[str] = field(default_factory=list) # 현재 실제 교전 중인 적국 ID 목록
    casus_belli_ledger: Dict[str, str] = field(default_factory=dict) # 타국에 대한 정당한 전쟁 명분 장부 (target_nation_id -> 명분)
    truce_agreements: Dict[str, int] = field(default_factory=dict) # 휴전 조약 장부 (target_nation_id -> 남은 휴전 일수)
    state_offices_and_titles: List[str] = field(default_factory=list) # 국가 공인 주요 관직 및 특수 직책 (예: ["궁정 마법사", "왕실 근위대장", "대법관"])
    recognized_guilds: List[str] = field(default_factory=list) # 국가 공인 대길드 목록 (예: ["상인 연합 길드", "연금술 학회"])
    active_mercenary_bands: List[str] = field(default_factory=list) # 국가 영토 내 활동 중인 대형 공인 용병단 목록
    national_merchant_leader_id: str = ""               # 국가 공인 상단 총수 / 왕실 조달청장 NPC ID 포인터
    border_barrier_type: str = "none"                   # 국경 물리 장벽 체계 ("none", "wooden_palisade_line", "great_stone_wall", "chasm_fortress")
    beacon_network_speed_hours: int = 12                # 국영 봉화대/파발망 신호 전파 속도 (국경 침공 시 수도 전달까지 소요 시간)
    coin_minting_purity: int = 80                       # 조폐국 주화 금/은 순도 (% 0~100, 동전 깎기 및 위조 화폐 판정 기준값)
    ammunition_strategic_control: bool = False          # 국가 전시 철제 화살촉/탄약 민간 유통 통제 여부 (True 시 화살 가격 3배 및 구매 제한)
    refitting_guild_tax_rate: float = 0.05              # 노획 장비 체형 개조/수선 시 국영 대장장이 길드 공임 관세율 (0.0~0.3)
    court_mage_circle_strength: int = 50                # 궁정 마법사단/국영 마도 결사단 규모 및 방어 전력 (0~100)
    national_patron_deity_boon: str = ""                # 국가 수호신전의 국가 단위 신성 가호 축복 (예: "솔라리스의 태양 방벽", "불멸의 강철 축복")
    airship_dock_count: int = 0                         # 국영 공중 마도 비공정 계류장 및 정규 비공정 수
    settlement_ids: List[str] = field(default_factory=list) # 영토 내 정주지 ID 목록
    military_alert_level: str = "평시"                  # 국방 경계 태세 ("평시", "경계", "전시", "계엄령")
    conscription_law: str = "자원병제"                  # 국가 군사 징집/동원 체제 ("모병/용병제", "자원병제", "의무징집제", "총동원령")
    population: int = 0                                 # 국가 총 인구
    area_sq_km: float = 0.0                             # 국가 영토 면적 (km²)
    specialties: List[str] = field(default_factory=list) # 국가 가공/제조/정책 특산품 (국영 포도주, 다마스커스 강철 등)
    international_highways: List[InterTierRoute] = field(default_factory=list) # 국가 간 관문 가도 및 간선 도로
    attire: AttireHierarchyProfile = field(default_factory=AttireHierarchyProfile) # 국가 사회 계층별 복식 규범
    cuisine: CuisineProfile = field(default_factory=CuisineProfile) # 국가 대표 식문화 및 궁중/서민식
    culture: CulturalNormsProfile = field(default_factory=CulturalNormsProfile) # 국가 국교, 성문법, 축제, 주종제도
    logistics: LogisticsNetwork = field(default_factory=LogisticsNetwork) # 국영 전령망 및 상단 물류 체계
    traits: List[str] = field(default_factory=list)     # 국가 고유 특성 태그 목록 (예: ["호전적 군국주의", "성기사의 성지", "화약 문명"])
    description: str = ""

    def calculate_total_military_power(self) -> int:
        """Calculates total regular ground army size including standard corps and special units."""
        standard_sum = (
            self.knights_count
            + self.infantry_count
            + self.ranged_corps_count
            + self.cavalry_count
            + sum(self.special_military_units.values())
        )
        return max(self.standing_army_size, standard_sum)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["international_highways"] = [r.to_dict() if hasattr(r, "to_dict") else r for r in self.international_highways]
        d["attire"] = self.attire.to_dict()
        d["cuisine"] = self.cuisine.to_dict()
        d["culture"] = self.culture.to_dict()
        d["logistics"] = self.logistics.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Nation":
        clean = dict(data)
        clean["international_highways"] = _safe_routes(data.get("international_highways", []))
        clean["attire"] = _safe_profile(AttireHierarchyProfile, data.get("attire"))
        clean["cuisine"] = _safe_profile(CuisineProfile, data.get("cuisine"))
        clean["culture"] = _safe_profile(CulturalNormsProfile, data.get("culture"))
        clean["logistics"] = _safe_profile(LogisticsNetwork, data.get("logistics"))
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


# =====================================================================
# Level 4 & 5 Infrastructure Sectors (Settlement Survival & Community)
# =====================================================================
class FacilityCategory(str, Enum):
    SANITATION_WATER = "sanitation_water"
    FOOD_STORAGE = "food_storage"
    DEFENSE_SAFETY = "defense_safety"
    TRADE_WORKSHOP = "trade_workshop"
    CIVIC_COMMUNAL = "civic_communal"


@dataclass
class SanitationWaterInfrastructure:
    water_sources: List[str] = field(default_factory=list)        # 급수원 (공동 우물, 저수조, 수로, 용천수 등)
    drainage_and_sewage: List[str] = field(default_factory=list)  # 배수로, 퇴비장, 집수지 등
    public_sanitation: List[str] = field(default_factory=list)    # 공동 변소, 세탁터, 목욕탕 등
    waste_and_cemeteries: List[str] = field(default_factory=list) # 공동묘지, 화장터, 폐기장 등
    water_capacity_rating: int = 50                               # 식수 공급 용량 등급 (0~100)
    waste_treatment_rating: int = 50                              # 오물/폐기물 처리 능력 (0~100)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SanitationWaterInfrastructure":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class FoodStorageInfrastructure:
    grain_processing: List[str] = field(default_factory=list)            # 곡물 가공 (방앗간, 풍차 등)
    communal_cooking_preserving: List[str] = field(default_factory=list) # 공동 화덕, 훈제장, 염장 시설 등
    storage_and_reserves: List[str] = field(default_factory=list)        # 미곡창, 빙고, 토굴 등
    livestock_facilities: List[str] = field(default_factory=list)        # 공동 우리, 목초지, 건초창고 등
    storage_reserve_months: float = 3.0                                  # 비축 식량 보관 한계 (월 단위)
    processing_capacity_rating: int = 50                                 # 가공 능력 등급 (0~100)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FoodStorageInfrastructure":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DefenseSecurityInfrastructure:
    physical_barriers: List[str] = field(default_factory=list)   # 목책, 토루, 성벽, 해자 등
    access_control: List[str] = field(default_factory=list)      # 관문, 방책문, 망루 등
    disaster_prevention: List[str] = field(default_factory=list) # 방화수, 모래주머니, 경종 등
    security_posts: List[str] = field(default_factory=list)      # 민병대소, 순찰초소, 유치장 등
    fortification_integrity: int = 50                            # 방벽 건전도 (0~100)
    fire_preparedness_rating: int = 50                           # 방재 대비 태세 (0~100)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DefenseSecurityInfrastructure":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TradeWorkshopsInfrastructure:
    artisan_workshops: List[str] = field(default_factory=list)   # 대장간, 무두질터, 직조공방, 목공소 등
    distribution_hubs: List[str] = field(default_factory=list)   # 장터 광장, 하역장, 물류창고 등
    lodging_and_transit: List[str] = field(default_factory=list) # 마구간 여관, 마차보관소, 주막 등
    production_vitality_rating: int = 50                         # 생산/유통 활성도 (0~100)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TradeWorkshopsInfrastructure":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CivicHealthInfrastructure:
    medical_and_relief: List[str] = field(default_factory=list)      # 약초상, 의원, 격리수용소 등
    governance_and_assembly: List[str] = field(default_factory=list) # 촌장 댁, 마을회관, 공고판 등
    faith_and_shrines: List[str] = field(default_factory=list)       # 사당, 제단, 성소 등
    healthcare_rating: int = 50                                      # 의료 대응력 (0~100)
    social_cohesion_rating: int = 50                                 # 공동체 결속도 (0~100)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CivicHealthInfrastructure":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SettlementInfrastructureProfile:
    sanitation: SanitationWaterInfrastructure = field(default_factory=SanitationWaterInfrastructure)
    food: FoodStorageInfrastructure = field(default_factory=FoodStorageInfrastructure)
    defense: DefenseSecurityInfrastructure = field(default_factory=DefenseSecurityInfrastructure)
    trade: TradeWorkshopsInfrastructure = field(default_factory=TradeWorkshopsInfrastructure)
    civic: CivicHealthInfrastructure = field(default_factory=CivicHealthInfrastructure)

    def to_dict(self) -> dict:
        return {
            "sanitation": self.sanitation.to_dict(),
            "food": self.food.to_dict(),
            "defense": self.defense.to_dict(),
            "trade": self.trade.to_dict(),
            "civic": self.civic.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SettlementInfrastructureProfile":
        if not isinstance(data, dict):
            return cls()
        return cls(
            sanitation=_safe_profile(SanitationWaterInfrastructure, data.get("sanitation")),
            food=_safe_profile(FoodStorageInfrastructure, data.get("food")),
            defense=_safe_profile(DefenseSecurityInfrastructure, data.get("defense")),
            trade=_safe_profile(TradeWorkshopsInfrastructure, data.get("trade")),
            civic=_safe_profile(CivicHealthInfrastructure, data.get("civic")),
        )


@dataclass
class SettlementYields:
    food: float = 0.0                                   # 식량 산출 (인구 부양 및 잉여 비축)
    production: float = 0.0                             # 생산력/망치 (건축, 수리, 장비 제조력)
    gold: float = 0.0                                   # 금화 산출 (상업 및 세수)
    science: float = 0.0                                # 지식 산출 (문해율, 기술/마도공학 도입)
    culture: float = 0.0                                # 문화 산출 (매력도, 예술, 외지인 유입)
    faith: float = 0.0                                  # 신앙 산출 (사원 정화, 영성, 이단 억제)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SettlementYields":
        if not isinstance(data, dict):
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# =====================================================================
# Level 4: Settlement (정주지/마을/도시)
# =====================================================================
@dataclass
class Settlement:
    id: str
    name: str                                           # 마을/도시명 (예: "솔리스 수도 성도", "검은 모루 요새마을")
    nation_id: str                                      # 소속 국가 ID
    region_id: str                                      # 소속 지리/기후 권역 ID
    settlement_type: str = "village"                    # "capital_metropolis", "fortress_citadel", "farming_village", "mining_camp", "coastal_port", "nomad_camp"
    coordinates: Tuple[float, float] = (0.0, 0.0)       # 지도 2D 좌표 (X_km, Y_km)
    elevation_meters: int = 100                         # 정주지 해발 고도 (m, 고산병/한파 및 공성 수비 보너스)
    population: int = 0                                 # 총 거주 인구
    housing_capacity: int = 0                           # 최대 주거 수용 인구 (인구 초과 시 노숙/슬럼화 및 위생 급락)
    area_sq_km: float = 0.0                             # 마을/도시 행정 면적 (km²)
    development_tier: int = 1                           # 정주지 현지 개발도/생활수준 등급 (1~5 등급: 1=오지/벽촌, 3=일반 소도시, 5=수도급 메트로폴리스)
    blacksmith_tier: int = 1                            # 대장간 기술 한계 등급 (0: 원시석기, 1: 청동/연철, 2: 강철/열처리, 3: 미스릴/마도합금)
    magic_institution_tier: int = 0                     # 마법 기관 한계 등급 (0: 없음, 1: 약초방/견습학당, 2: 정규학술원, 3: 고위마탑)
    literacy_rate: int = 30                             # 주민 문해율 (% 0~100, 공고판/마법서/계약서 해독률)
    slum_ratio: int = 0                                 # 빈민가/판자촌 비율 (% 0~100, 역병 확산 및 암흑가 온상)
    paved_road_ratio: int = 20                          # 도로 포장률 (% 0~100, 우천 시 진흙탕화 방지 및 배수)
    superstition_index: int = 60                        # 토착 미신·광신 맹신도 (0~100, 높을수록 마녀사냥/이방인 배척)
    unemployment_rate: int = 10                         # 실업률 (% 0~100, 높을수록 부랑자 급증 및 도적단 포섭)
    orphan_vagrant_index: int = 10                      # 고아 및 부랑자 비율 (0~100, 소매치기/치안 악화)
    cartographic_accuracy: int = 30                     # 지도 정밀도 및 측량 수준 (0~100, 주변 지형 오차율)
    racial_demographics: Dict[str, float] = field(default_factory=dict) # 의사소통 가능한 휴머노이드 필멸자 지성체 구성비 (인간, 엘프, 드워프, 수인, 오크 등)
    security_level: int = 50                            # 치안도 (0~100)
    curfew_hour: int = 22                               # 야간 통행금지 시각 (0: 통금 없음, 22: 22시 이후 야간 배회자 불심검문/체포)
    wall_defense_tier: int = 1                          # 방위 성벽 등급 (0: 목책/없음, 1: 석벽, 2: 겹성벽, 3: 마도 결계 성채)
    siege_supplies_days: int = 90                       # 성채/마을 농성 버팀 비축 군량/식수 잔여 일수
    harbor_tier: int = 0                                # 수운/해운 항만 등급 (0: 내륙/없음, 1: 나루터/어선 부두, 2: 상선 무역항, 3: 대양 심해 군항)
    purification_barrier_tier: int = 0                  # 정화 결계/독성 차단 등급 (0: 없음, 1: 공기 필터/정화림, 2: 마도 정화 돔, 3: 신성 결계 성역)
    local_toxicity_override: Optional[int] = None       # 마을 국소 환경 독성 오버라이드 (None: 권역 독성 상속, 0: 청정 성역, 양수: 국소 오염도)
    leyline_nexus_tier: int = 0                         # 지맥 결절점/마나 샘 등급 (0: 없음, 1: 간이 마나석 샘, 2: 고대 지맥 결절점, 3: 세계수 마력 근원)
    local_mana_density_override: Optional[int] = None   # 마을 국소 마나 밀도 오버라이드 (None: 권역 마나밀도 상속, 0~100 정수 지정 시 지맥/결계 고유 밀도)
    self_sufficiency_food: int = 80                     # 식량 자급율 (% 0~100)
    self_sufficiency_water: int = 90                    # 식수 자급율 (% 0~100)
    fuel_reserves_days: int = 60                        # 혹한기 난방 땔감/석탄 비축 잔여 일수 (0 도달 시 저체온 동사 발생)
    cold_insulation_rating: int = 50                    # 가옥 보온/단열도 (0~100, 혹한기 땔감 소모 완화 및 동사 판정)
    waste_management_tier: int = 1                      # 분뇨 및 오물 처리 등급 (0: 노상투기/방치, 1: 오물구덩이, 2: 정화조/퇴비화, 3: 지하마도하수관)
    hygiene_level: int = 70                             # 위생도 (0~100, 낮을수록 전염병 위험)
    medical_capacity: int = 10                          # 치료소 격리/수용 병상 수 (역병 창궐 및 부상병 발생 시 한계치)
    graveyard_capacity: int = 100                       # 공동묘지/납골당 시체 수용 한도 (초과 시 시체 유기 및 역병/언데드 발생)
    active_epidemics: List[str] = field(default_factory=list) # 현재 마을에 창궐 중인 역병/전염병 목록 (예: ["흑사병", "붉은 반점열"])
    quarantine_active: bool = False                     # 마을 출입 통제/격리 방역령 발효 여부
    inn_bed_capacity: int = 15                          # 마을 전체 여관 객실/침상 수 (부족 시 마구간 노숙/피로도 회복 불가)
    entertainment_relief_rating: int = 50               # 주점/도박/공연 등 스트레스 해소 인프라 등급 (0~100, 멘탈 회복 한도)
    prosperity_rating: int = 50                         # 마을 상권/생활 번영도 (0~100)
    trade_power: int = 10                               # 상권 내 정주지 시장 지배력/영향력 (0~100)
    market_haggling_dc: int = 12                        # 상점 흥정/에누리 기본 난이도 DC (10: 시골 ~ 22: 암시장)
    market_economic_trend: str = "안정"                 # 시장 경기 국면 ("대풍년", "호황", "안정", "물가폭등", "대기근", "전쟁특수")
    rumor_circulation_rate: int = 50                    # 주점·시장 정보 유통 속도 (0~100, 퀘스트/소문/악명 확산율)
    tax_evasion_rate: int = 20                          # 밀수 및 탈세율 (% 0~100, 높을수록 암시장 융성 및 영주 재정난)
    treasury: int = 500                                 # 마을 자치 금고/예산 (골드)
    discontent_level: int = 10                          # 주민 불만도 (0~100, 80 이상 시 폭동/파업 발생)
    political_unrest: int = 0                           # 정치적 소요 및 시민 시위 위험도 (0~100)
    loyalty_to_nation: int = 80                         # 국가/영주에 대한 충성도 (0~100, 0 도달 시 독립 도시 선언)
    outsider_distrust: int = 50                         # 외지인 배척/경계도 (0~100, 높을수록 상점 바가지, 정보 은폐, 대화 거부)
    yields: SettlementYields = field(default_factory=SettlementYields) # 6대 기본 산출량 (식량, 생산력, 금화, 과학, 문화, 신앙)
    religious_demographics: Dict[str, float] = field(default_factory=dict) # 주민 종교/신앙 구성비 (예: {"성광교": 0.7, "자연정령": 0.3})
    sectarian_tension: int = 0                          # 종교/사상 갈등 긴장도 (0~100, 70 이상 시 마녀사냥/종교폭동)
    counter_intelligence_rating: int = 50               # 방첩 및 비밀 침투 방어 등급 (0~100)
    active_spy_networks: List[str] = field(default_factory=list) # 정주지 내 암약 중인 타국/파벌 첩보 조직 목록
    world_wonders: List[str] = field(default_factory=list) # 마을 내 세계 불가사의/기념비적 건조물
    lord_npc_id: str = ""                               # 영지 지배자/영주 NPC ID
    lord_dynasty: str = ""                              # 영주 소속 가문명
    succession_crisis: bool = False                     # 영주 계승권 분쟁/찬탈 위기 진행 여부
    bailiff_npc_id: str = ""                            # 빌리프(Bailiff) - 영주가 파견한 전문 관리인/세무·농경 감독관 (영주의 눈과 귀)
    village_head_npc_id: str = ""                       # 마을 이장/촌장 - 주민 자치 대표자 (갈등 중재 및 자치 회의 주재)
    bailiff_villager_affinity: int = 40                 # 빌리프와 주민 간의 친밀/신뢰도 (0~100, 낮을수록 얄미움/원한)
    social_classes_demographics: Dict[str, float] = field(default_factory=dict) # 계층별 인구 구성비 (귀족, 성직자, 장인, 농민 등)
    unfree_labor_ratio: float = 0.0                     # 전체 인구 중 예속 농노/노예 비율 (0.0~1.0)
    interest_group_conflicts: List[str] = field(default_factory=list) # 계층 간 이해 충돌 목록 (예: ["지주_농민_소작료_분쟁"])
    patrol_strength: int = 50                           # 영주/자경단 순찰대 전력 (0~100)
    bandit_threat_level: int = 10                       # 주변 도적/무법 위협도 (0~100, 50 이상 시 상단 습격)
    visiting_mercenaries: List[str] = field(default_factory=list) # 정주지 여관/주점에 체류 중인 유랑 용병단 목록
    masterwork_relics: List[str] = field(default_factory=list) # 마을 보관 전설적 가보/걸작 유물 목록
    mental_break_risk: int = 10                         # 집단 멘탈 붕괴/광기 위험도 (0~100, 재해/기근 시 상승)
    emergency_decrees: List[str] = field(default_factory=list) # 영주/자치회 비상 생존 법안 목록 (예: ["아동노동_징집", "비상식량_배급"])
    monster_infestation_index: int = 0                  # 마을 주변 마수 침식도 (0~100, 50 이상 시 가축 습격/주민 실종)
    supernatural_corruption: int = 0                    # 심연/마력 폭주/역병에 의한 초자연적 오염도 (0~100)
    local_curses_and_taboos: List[str] = field(default_factory=list) # 향토 전설, 금기 및 토착 저주 (예: ["밤 12시 숲 출입 금기"])
    historical_grievances: List[str] = field(default_factory=list) # 마을 주민들이 대대로 기억하는 역사적 원한/상처 기록
    hidden_scandals: List[str] = field(default_factory=list) # 정주지 지배층/유력자의 은밀한 치부, 스캔들 및 비밀 장부
    cultist_infiltrations: List[str] = field(default_factory=list) # 사교도/광신도 지하 침투 조직 (예: ["심연의 찬가 비밀 결사"])
    underground_black_market: bool = False              # 지하 암시장/장물아비 암약 여부
    ruling_crime_syndicate: str = ""                    # 마을 뒷골목 지배 범죄 조직/카르텔명
    underworld_influence: int = 0                       # 암흑가 장악도 (0~100, 70 이상 시 경비대 진입 통제)
    active_bounties: List[str] = field(default_factory=list) # 마을 게시판 활성 현상수배/퇴마 의뢰 목록
    bounty_ledger: Dict[str, int] = field(default_factory=dict) # 영지 사법부 지명수배 장부 (범죄자_ID -> 현상금 액수)
    common_occupations: List[str] = field(default_factory=list) # 마을 주민 주요 생업/직업군 (예: ["농부", "목동", "대장장이", "약초꾼"])
    active_guilds: List[str] = field(default_factory=list) # 마을 내 활동 길드/직능 단체 (예: ["광부 조합", "사냥꾼 협회"])
    market_day_interval: int = 7                        # 정기 장날 주기 (일 단위, 0: 상설)
    visiting_caravans: List[str] = field(default_factory=list) # 현재 마을에 체류 중인 외부 대형 대상단 목록
    caravan_frequency_days: int = 14                    # 대상단 정기 방문 주기 일수 (0: 상설 무역도시)
    roads: Dict[str, RoadConnection] = field(default_factory=dict) # 마을 간 도로망 (destination_settlement_id -> RoadConnection)
    facility_ids: List[str] = field(default_factory=list) # 마을 내 시설 전체 ID 목록
    commercial_shops: List[str] = field(default_factory=list) # 상점/잡화점/대장간/약초방 등 상업 시설 ID 목록
    training_facilities: List[str] = field(default_factory=list) # 도장/훈련장/마탑/학당 등 무예/마법 수련 시설 ID 목록
    active_peddlers: List[str] = field(default_factory=list) # 현재 정주지에 체류 중인 이동식 보따리 행상인/포장마차 ID 목록
    guild_halls: List[str] = field(default_factory=list) # 상인/모험가/용병 길드 지부 시설 ID 목록
    under_construction_facilities: List[str] = field(default_factory=list) # 현재 신축/복구 공사 중인 시설 ID 목록
    ruined_facilities: List[str] = field(default_factory=list) # 완파/폐허 상태로 방치된 잔해 시설 ID 목록
    town_square_features: List[str] = field(default_factory=list) # 중앙 광장 시설물 (단두대/교수대, 공고판, 시계탑/종루, 분수대 등)
    gate_type: str = "wooden_bar"                       # 성문 방호 유형 ("none", "wooden_bar", "iron_reinforced", "portcullis", "drawbridge_chains")
    moat_type: str = "none"                             # 해자 유형 ("none", "dry_ditch", "water_moat", "spiked_trench")
    stable_and_cart_capacity: int = 10                  # 마구간 계류장 및 마차 보관 수용 정원 (군마/짐마차 주차장)
    watermills_count: int = 0                           # 수력 물레방아 개수 (곡물 제분 및 목재 제재 동력)
    windmills_count: int = 0                            # 풍력 풍차 개수 (제분 및 관개 동력)
    firefighting_cistern_rating: int = 50               # 방화 수조 및 모래 비축소 등급 (0~100, 화재 시 조기 진화 확률)
    quarantine_camp_active: bool = False                # 검역소 & 난민 격리 텐트촌 활성 여부 (역병 및 피난민 유입 격리)
    sewer_network_scale: int = 0                        # 지하 하수도망 규모 (0: 없음, 1: 얕은 노상 배수로, 2: 지하 배수관, 3: 거대 지하 미로/도적 통로)
    pasture_area_hectares: float = 0.0                  # 마을 가축 방목지 면적 (ha, 양/소 방목 울타리, 마수 기습 1차 피해 구역)
    street_lighting_type: str = "none"                  # 가로등/야간 조명망 ("none", "pitch_torches", "whale_oil_lamps", "magic_crystals", 야간 치안 및 은신 DC)
    battlement_type: str = "none"                       # 성벽 총안 및 사격 흉벽 ("none", "wooden_hurdles", "stone_crenels", "machicolations", 공성 방어 보너스)
    militia_armory_capacity: int = 50                   # 마을 공용 무기고 비축 정원 (징집 민병대용 창/갑옷/화살 비축량)
    fletching_and_ammo_supply_tier: int = 1             # 화살/볼트 탄약 공방 보급 등급 (0: 품귀/없음, 1: 일반 화살, 2: 강철 관통살, 3: 마도 폭발 화살)
    armor_refitting_forge_tier: int = 1                 # 이종족 노획 장비 체형 수선 대장간 등급 (0: 불가, 1: 경갑/가죽 수선, 2: 판금 중갑 리사이징, 3: 마도구 개조)
    pack_animal_rental_available: bool = True           # 중량 과적 해소를 위한 노새/짐마차 대여 가능 여부
    disguise_inspection_strictness: int = 40            # 성문/거리 경비병의 복면/가면 착용자 불심검문 엄격도 (0~100, 변장 간파 판정 기준)
    specialties: List[str] = field(default_factory=list) # 마을 고유 향토 특산품 (전통 치즈, 훈제 은송어, 수제 약초주 등)
    local_resource_nodes: List[str] = field(default_factory=list) # 마을 관할 현지 물리적 채굴/채집 노드 (예: ["제1 철광 갱도", "고대 은광맥", "유황 온천", "벌채장"])
    resource_depletion_risk: int = 20                   # 자원 고갈 및 폐광 위험도 (0~100, 100 도달 시 폐광/자원 고갈로 유령마을화)
    magical_barrier_active: bool = False                # 고위 마법 폭격/드래곤 브레스 차단용 도시 광역 마도 결계 돔 가동 여부
    aerial_mount_dock_tier: int = 0                     # 비행 마수 승강장 등급 (0: 없음, 1: 비둘기/매 전령소, 2: 그리폰/히포그리프 마구간, 3: 비공정 계류탑)
    teleportation_waystone_active: bool = False         # 정주지 중앙 공간 전송 마법석/웨이포인트 결절점 활성 여부
    undead_haunting_index: int = 0                      # 야간 영체/원혼/언데드 출몰 및 사령 농도 (0~100, 50 이상 시 야간 횃불 푸르게 변함)
    infrastructure: SettlementInfrastructureProfile = field(default_factory=SettlementInfrastructureProfile) # 5대 생존 및 공동체 인프라
    attire: AttireHierarchyProfile = field(default_factory=AttireHierarchyProfile) # 마을 향토 복식 양식
    cuisine: CuisineProfile = field(default_factory=CuisineProfile) # 마을 향토 요리 및 보급 식수
    culture: CulturalNormsProfile = field(default_factory=CulturalNormsProfile) # 마을 토착 신앙, 길드, 주기 행사
    logistics: LogisticsNetwork = field(default_factory=LogisticsNetwork) # 마을 주둔 마차/가축 및 역참 시설
    traits: List[str] = field(default_factory=list)     # 정주지 고유 특성 태그 목록 (예: ["무법천지", "대기근", "언데드 소굴", "골드러시"])
    description: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["roads"] = {k: asdict(v) if hasattr(v, "__dataclass_fields__") else v for k, v in self.roads.items()}
        d["yields"] = self.yields.to_dict()
        d["infrastructure"] = self.infrastructure.to_dict()
        d["attire"] = self.attire.to_dict()
        d["cuisine"] = self.cuisine.to_dict()
        d["culture"] = self.culture.to_dict()
        d["logistics"] = self.logistics.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Settlement":
        roads_dict = {}
        for k, v in data.get("roads", {}).items():
            if isinstance(v, dict):
                roads_dict[k] = RoadConnection(**{rk: rv for rk, rv in v.items() if rk in RoadConnection.__dataclass_fields__})
            else:
                roads_dict[k] = v
        clean = dict(data)
        clean["roads"] = roads_dict
        coords = clean.get("coordinates")
        if isinstance(coords, list):
            clean["coordinates"] = tuple(coords)
        clean["yields"] = _safe_profile(SettlementYields, data.get("yields"))
        clean["infrastructure"] = _safe_profile(SettlementInfrastructureProfile, data.get("infrastructure"))
        clean["attire"] = _safe_profile(AttireHierarchyProfile, data.get("attire"))
        clean["cuisine"] = _safe_profile(CuisineProfile, data.get("cuisine"))
        clean["culture"] = _safe_profile(CulturalNormsProfile, data.get("culture"))
        clean["logistics"] = _safe_profile(LogisticsNetwork, data.get("logistics"))
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


# =====================================================================
# Level 5: Facility (세부 인프라/시설)
# =====================================================================
class BuildingStatus(str, Enum):
    OPERATIONAL = "operational"             # 정상 가동 중
    UNDER_CONSTRUCTION = "under_construction" # 신축/증축 공사 중
    UNDER_REPAIR = "under_repair"           # 보수/수리 공사 중
    DAMAGED = "damaged"                     # 반파/파손 (기능 일부 제한)
    RUINED = "ruined"                       # 완파/폐허 (기능 완전 정지)
    ABANDONED = "abandoned"                 # 방치/유기 (도적/마수 소굴화)


class FacilityType(str, Enum):
    TAVERN_INN = "tavern_inn"                       # 주점 겸 여관
    GENERAL_STORE = "general_store"                 # 잡화점/만물상
    BLACKSMITH_FORGE = "blacksmith_forge"           # 대장간/제철소
    APOTHECARY_CLINIC = "apothecary_clinic"         # 약초방/의원
    TRAINING_GROUND = "training_ground"             # 연무장/검술도장/병영
    MAGE_TOWER_ACADEMY = "mage_tower_academy"       # 마탑/마법학당/도서관
    TEMPLE_SHRINE = "temple_shrine"                 # 신전/사당/성소
    GUILD_HALL = "guild_hall"                       # 길드 지부/사무소
    GUARD_POST_PRISON = "guard_post_prison"         # 자경단 초소/감옥
    PUBLIC_BATHHOUSE = "public_bathhouse"           # 공중 목욕탕/온천
    ROVING_PEDDLER_STALL = "roving_peddler_stall"   # 이동식 노점/보따리 행상
    WORKSHOP_MILL = "workshop_mill"                 # 방앗간/목공소/제재소
    DUNGEON_ENTRANCE = "dungeon_entrance"           # 지하 납골당/유적 입구
    TOWN_HALL_MANOR = "town_hall_manor"             # 촌장 댁/영주 저택


@dataclass
class Facility:
    id: str
    name: str                                           # 시설명 (예: "황금 사자 주점", "녹슨 화로 대장간", "솔리스 남문 관문")
    settlement_id: str                                  # 소속 마을 ID
    category: FacilityCategory = FacilityCategory.TRADE_WORKSHOP # 시설 기능 분류 (sanitation_water, food_storage, defense_safety, trade_workshop, civic_communal)
    is_communal_public: bool = False                    # 공공 기반시설 여부 (True: 공용 우물/방책/회관, False: 사설 상점/공방/주점)
    is_wonder: bool = False                             # 불가사의/랜드마크 건조물 여부
    facility_type: str = "general_store"                # 시설 세부 유형 (FacilityType 값 또는 "general_store", "blacksmith" 등)
    building_status: str = "operational"                # 건물 가동/공사/파손 상태 ("operational", "under_construction", "under_repair", "damaged", "ruined", "abandoned")
    construction_progress: int = 100                    # 건축/복구 완공 진척도 (% 0~100, 100: 완공 가동, 0: 기초 터)
    repair_cost_materials: Dict[str, int] = field(default_factory=dict) # 복구/완공 필요 자재 및 비용 (예: {"wood": 30, "stone": 20, "iron": 5, "gold": 150})
    destruction_cause: str = ""                         # 파손/붕괴 원인 (예: "화재", "공성 투석", "마수 습격", "노후 방치")
    scaffolding_accessible: bool = False                # 공사 비계/발판 설치 여부 (등반 침투 및 고지대 저격 전술 기믹)
    npcs: List[str] = field(default_factory=list)       # 상주 NPC ID 목록
    items: List[str] = field(default_factory=list)      # 보관/진열 아이템 ID 목록
    services: Dict[str, Any] = field(default_factory=dict) # 제공 서비스 (예: {"rest": 10, "repair": 0.8, "skill_train": ["sword"], "appraisal": 5, "black_market": True})
    exits: Dict[str, str] = field(default_factory=dict) # 시설 내부/외부 방 연결 출구
    emergency_exits: List[str] = field(default_factory=list) # 비상 탈출구/비밀 도주로 목록 (예: ["지하실 비밀 배수관", "집무실 뒤 비밀 회랑"])
    occupancy_limit: int = 20                           # 시설 최대 수용 인원 (초과 시 혼잡/합석/패싸움, 잠입 시 군중 은신 영향)
    noise_level: int = 40                               # 실내 소음도 (0~100 dB/스케일: 0~20 정적, 21~40 조용함, 41~70 보통, 71~100 굉음/혼잡)
    soundproof_rating: int = 30                         # 실내 음향 차폐/방음도 (0~100, 높을수록 실내 전투/비명 외부 유출 차단)
    floor_material: str = "wood_creaky"                 # 실내 바닥 재질 ("carpet_soft", "stone_flagstone", "wood_creaky", "broken_glass", 발소리 은신 DC)
    lighting: int = 50                                  # 실내 조도 (0~100: 0~10 칠흑, 11~30 암흑/희미함, 31~70 보통, 71~100 눈부심)
    light_source_type: str = "torch"                    # 조명 광원 종류 ("none", "torch", "candle", "fireplace", "magic_crystal", 소화/암전 전술 기믹)
    water_supply_type: str = "공용우물"                 # 시설 급수 방식 ("없음", "공용우물", "상수도관", "오염된침출수", "마법성수")
    ventilation_quality: int = 50                       # 시설 환기 및 공기질 (0~100: 0~10 밀폐/질식위험, 11~30 불량/악취, 31~70 보통, 71~100 쾌적/환기양호)
    durability: int = 100                               # 시설 내구도 (0~100)
    daily_maintenance_cost: int = 0                     # 일일 유지보수/수리 비용 (골드/일, 미지불 시 내구도 감소)
    defense_rating: int = 10                            # 방화/방어 등급
    flammability_rating: int = 30                       # 가연성 및 화재 위험도 (0~100, 높을수록 화염 마법 피격 시 화재 확산)
    trap_hazard_rating: int = 0                         # 시설/던전 함정 밀도 및 위험도 (0~100, 백로그 3번 함정 해체 엔진 연동)
    magic_ward_tier: int = 0                            # 대마법 보안 결계 등급 (0: 없음, 1: 텔레포트 차단, 2: 투시/탐지 차단, 3: 침묵/마법 무효화)
    guard_patrol_interval_turns: int = 3                # 경비병 순찰 확인 주기 (턴 단위, 0: 순찰 없음, 3: 3턴마다 방 진입/확인)
    security_clearance_tier: int = 0                    # 보안/경비 인가 등급 (0: 공공 자유 출입, 1: 손님/유료, 2: 직원/경비병 전용, 3: 영주/지배자 극비 구역)
    lock_difficulty: int = 15                           # 출입문/금고 자물쇠 해제 난이도 (DC 0~30, 0: 개방, 10: 걸쇠, 20: 기계식, 30: 마도봉인)
    reinforcement_material: str = "wood"                # 문/벽 물리 파괴 저항 재질 ("wood", "stone", "iron_reinforced", "warded_adamantine")
    alarm_level: int = 0                                # 경비 경보 단계 (0~100, 0: 평온, 50: 침투 발각 경계, 100: 비상 경종 및 전원 교전)
    elevation_level: int = 0                            # 시설 상대 층수/고도 (지하2층 -2, 지상1층 0, 망루/지붕 +3)
    scent_intensity: int = 30                           # 시설 내부 고유 체취/냄새 강도 (0~100, 피/화약/향신료 후각 감지 DC)
    infiltration_points: List[str] = field(default_factory=list) # 시설 잠입/침투 루트 (예: ["지붕 채광창", "주방 환기구", "하수도 배수구", "창고 뒷문"])
    interactive_props: List[str] = field(default_factory=list) # 환경 물리 상호작용 기믹 (예: ["샹들리에 도르래", "가연성 기름통", "경종 종루", "독가스 배출 밸브"])
    hidden_compartments: List[str] = field(default_factory=list) # 시설 내 은닉 격실/비밀 금고/이중 벽장 목록 (도적 잠입/수색 탐색용)
    window_security_type: str = "wooden_shutters"       # 창문 방범 상태 ("none", "wooden_shutters", "iron_bars", "stained_glass_alarm", 침투 DC 직결)
    chimney_hearth_size: str = "narrow"                 # 벽난로/굴뚝 크기 ("none", "narrow", "crawlable", "walkable_furnace", 침투 기믹)
    roof_material_type: str = "wood_shingle"            # 지붕/천장 재질 ("straw_thatch", "wood_shingle", "slate_tile", "lead_sheet", 화재/은신 DC)
    cover_density: int = 50                             # 실내 전술 엄폐물 밀도 (0~100: 0 바닥, 50 탁자/나무통 반엄폐, 80+ 돌기둥 완엄폐)
    secret_door_mechanism: str = "none"                 # 비밀문 작동 메커니즘 ("none", "book_lever", "candle_twist", "floor_pressure_tile", "hidden_keyhole")
    cellar_type: str = "none"                           # 지하실/저장고 유형 ("none", "root_cellar", "wine_vault", "secret_dungeon", "catacomb_connection")
    guard_beast_type: str = "none"                      # 경비견/파수 생명체 ("none", "watchdog", "trained_falcon", "golem_sentry")
    vent_duct_size: str = "none"                        # 환기 배관/덕트 크기 ("none", "grate_narrow", "crawlable_human", 덕트 침투 기믹)
    floor_water_depth_cm: int = 0                       # 바닥 침수/오수 깊이 (cm: 0 건조, 5 찰랑거림/발소리, 30 무릎/감전)
    key_holder_npc_id: str = ""                         # 자물쇠 열쇠 소지자 NPC ID 포인터 (소매치기/협박 탈취 대상)
    ceiling_height_meters: float = 3.0                  # 실내 천장 높이 (m, 2.2m 미만 시 장창/대검 등 거대 무기 휘두름 벽 충돌 튕김 제약)
    hallway_width_meters: float = 2.5                   # 실내 복도/통로 유효 폭 (m, 1.5m 미만 시 찌르기 무기 강제 및 회피 불가)
    cover_poise_durability: int = 50                    # 실내 엄폐물/문짝의 체간 충격량 버팀도 (0~100, 대형 둔기/폭발 피격 시 가드 파괴)
    dungeon_max_depth_floors: int = 0                   # 던전/지하 유적 시설의 최대 지하 심도 층수 (0: 일반 지상 건물, 1~50: 지하 미궁 층수)
    dungeon_core_element: str = "none"                  # 살아있는 던전 핵의 속성 ("none", "abyss", "fire", "arcane", "nature", "undead")
    sanctification_rating: int = 50                     # 시설 신성 축성/정화도 (0~100: 0 사령/저주 소굴, 50 세속 중립, 100 언데드 즉시 정화 성소)
    traits: List[str] = field(default_factory=list)     # 시설 고유 특성 태그 목록 (예: ["쥐떼 소굴", "밀수꾼의 은신처", "성스러운 결계"])
    description: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["category"] = self.category.value if isinstance(self.category, FacilityCategory) else str(self.category)
        d["facility_type"] = self.facility_type.value if isinstance(self.facility_type, FacilityType) else str(self.facility_type)
        d["building_status"] = self.building_status.value if isinstance(self.building_status, BuildingStatus) else str(self.building_status)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Facility":
        clean = dict(data)
        if "category" in clean and isinstance(clean["category"], str):
            try:
                clean["category"] = FacilityCategory(clean["category"])
            except ValueError:
                clean["category"] = FacilityCategory.TRADE_WORKSHOP
        if "facility_type" in clean and isinstance(clean["facility_type"], FacilityType):
            clean["facility_type"] = clean["facility_type"].value
        if "building_status" in clean and isinstance(clean["building_status"], BuildingStatus):
            clean["building_status"] = clean["building_status"].value
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


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
            if facility.id not in self.settlements[facility.settlement_id].facility_ids:
                self.settlements[facility.settlement_id].facility_ids.append(facility.id)

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
        reg = registry or getattr(world_state, "infrastructure", None) or InfrastructureRegistry()

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
