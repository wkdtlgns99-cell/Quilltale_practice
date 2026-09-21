"""
WorldState is the ground truth of the Quilltale game world.
Contains full character stats, 5-scale NPC memory, Fog of War for NPC stats,
Korean localization mappings, and deterministic delta state transitions.
"""
import json
import logging
from dataclasses import dataclass, field, fields
from typing import Any

logger = logging.getLogger(__name__)

from src.core.config import (
    MAX_BRACELETS,
    MAX_EARRINGS,
    MAX_LEVELUP_STAT_GAIN,
    MAX_REPUTATION_DELTA,
    MAX_REPUTATION_TOTAL,
    MAX_RINGS,
    MAX_STAT_VALUE,
    MIN_REPUTATION_DELTA,
    MIN_REPUTATION_TOTAL,
)

# Re-export pure domain entities for 100% backward compatibility
from .entities import (
    DISPOSITION_KO_MAP,
    EquipmentSlots,
    CombatProfile,
    NPCPersonality,
    Skill,
    Title,
    ItemVisualProfile,
    Item,
    MemoryEntry,
    Faction,
    FacialDetails,
    BodyMeasurements,
    ClothingLayer,
    NPCVisualDetails,
    NPCNeeds,
    NPC,
    Location,
    EnvironmentalMetrics,
    PendingInformation,
    Player,
)

@dataclass
class WorldState:
    session_id: str = "default_session"
    world_id: str = ""
    world_name: str = ""
    world_genre: str = ""
    turn: int = 0
    civilization_era: str = ""                                          # Level 0: 전 세계 문명 시대 배경 및 기술 상한선 (예: "중세 판타지", "마도 르네상스")
    epoch_state: str = "안정기"                                         # Level 0: 전 세계 거시적 시대 기류 ("황금기", "안정기", "쇠퇴기", "암흑기")
    founded_religions: list[str] = field(default_factory=list)          # Level 0: 전 세계 창시된 주요 종교/교단 목록 (예: "성광교회", "원시정령신앙")
    total_population: int = 0                                           # Level 0: 전 세계 총 인구
    total_area_sq_km: float = 0.0                                       # Level 0: 전 세계 총 표면적 (km²)
    magic_suppression_cycle: int = 0                                    # Level 0: 마나 조석/에테르 개기일식 주기 (0~100, 100: 마법 완전 불발의 날)
    planar_convergence_cycle: int = 0                                   # Level 0: 차원 대수렴 주기 (0~100, 100: 이계 악마/천상계 차원 문 개방)
    world_threat_level: int = 10                                        # Level 0: 세계적 멸망/대재앙 위협도 (0~100, 심연 침공/마왕 부활/용의 각성)
    global_apocalyptic_threat: str = ""                                 # Level 0: 전 세계적 멸망/재앙 위협 명칭 (예: "마왕군 침공", "영구 빙하기", "심연 차원문 개방")
    world_crisis_active_stage: int = 0                                  # Level 0: 전 인류적 위기/종말 카운트다운 단계 (0: 평화 ~ 5: 완전 파멸 임박)
    global_nemesis_npc_id: str = ""                                     # Level 0: 전 세계 공통의 주적/마왕/파멸의 사도 NPC ID 포인터
    global_sanctuary_region_id: str = ""                                # Level 0: 전 세계 침식 속에서 유일하게 방호된 인류 최후의 성역 권역 ID 포인터
    grand_crusade_coalition: list[str] = field(default_factory=list)    # Level 0: 전 세계 난제 해결을 위해 결성된 초국가 대연합/성전군 세력 목록
    universal_gravity_scale: float = 1.0                                 # Level 0: 세계 물리 중력 계수 (1.0 = 표준, 중량 과적 및 낙하 충격량 배율 기준치)
    memory_decay_turn_interval: int = 50                                 # Level 0: 사소한(1~2급) 에피소딕 기억의 자연 망각/흐려짐 턴 주기
    cosmic_alignment_element: str = "neutral"                           # Level 0: 현재 행성이 통과 중인 우주 성간 속성/천체 정렬 ("neutral", "fire", "void", "holy", "life")
    world_soul_awakening_ratio: int = 0                                 # Level 0: 행성 자체의 영혼/가이아 자아 각성도 (0~100, 높을수록 마나 폭풍 및 지각 변동 증가)
    pantheon_deities: list[str] = field(default_factory=list)           # Level 0: 세계관 주신/신격 목록 (예: ["태양신 솔라리스", "밤의 여신 녹티스"])
    days_per_month: int = 30                                            # Level 0: 천문 역법 - 한 달 일수
    months_per_year: int = 12                                           # Level 0: 천문 역법 - 1년 개월 수
    world_traits: list[str] = field(default_factory=list)               # Level 0: 세계관/행성 거시 요약 특성 태그 (예: ["신들의 침묵", "마나 과포화", "성간 화염 정렬", "종말 임박"])
    locations: dict[str, Location] = field(default_factory=dict)
    npcs: dict[str, NPC] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    skills_db: dict[str, Skill] = field(default_factory=dict)
    titles_db: dict[str, Title] = field(default_factory=dict)
    player: Player = field(default_factory=Player)
    world_reputation: int = 0
    world_facts: list[str] = field(default_factory=list)
    world_news_feed: list[str] = field(default_factory=list)
    world_chronicle: str = ""
    active_world_ended: bool = False
    active_map_image: str = "data/maps/default_overworld.jpg"
    history: list[dict] = field(default_factory=list)
    last_dice_result: dict | None = None
    last_npc_action: dict | None = None
    
    # Scenario Tracking
    current_scenario_id: str | None = None
    current_scenario_act: str = "act_1_hook_and_misdirection"

    # Macro World Architecture & Factions
    infrastructure: Any | None = None                                # Level 1~5 Macro-to-Micro hierarchy registry
    factions: dict[str, Faction] = field(default_factory=dict)         # 국가 및 주요 세력 DB
    cosmology_template: dict[str, Any] = field(default_factory=dict)   # 활성화된 세계관 템플릿 풀 스펙
    world_lore: dict[str, Any] = field(default_factory=dict)           # 세계관 세부 설정 (cosmology_template 동기화)
    power_scale_preset_id: str = "standard_fantasy"                     # 세계관 성장 스케일 프리셋 ID ("low_fantasy", "standard_fantasy", "hyper_inflation", "cultivation")
    environment_states: dict[str, dict] = field(default_factory=dict) # {"tavern": {"door": "broken", "hearth": "burned"}}
    discovered_clues: dict[str, str] = field(default_factory=dict)     # 발견된 단서/비밀 DB
    world_secrets: dict[str, dict] = field(default_factory=dict)       # 비대칭 비밀/진실 DB (GM 비대칭 정보 & 단서 조각)
    # Quests & Living Journal
    quests: dict = field(default_factory=dict)
    # Shops & Economy DB
    shops: dict = field(default_factory=dict)
    # Recipes & Crafting DB
    recipes: dict = field(default_factory=dict)
    # Party & Companions DB
    party: dict = field(default_factory=dict)
    # Puzzles & Dungeon Mechanisms DB
    puzzles: dict = field(default_factory=dict)
    # Bounties & Wanted Board DB
    bounties_board: list[dict] = field(default_factory=list)
    # Celestial & Festival Cycles
    celestial_phase: str = "normal"              # "normal", "celestial_blood_moon", "celestial_solar_eclipse", "celestial_meteor_shower"
    celestial_phase_turns: int = 0               # 남은 지속 턴 수
    active_festival: str | None = None        # "festival_harvest_bounty", "festival_night_of_dead"
    active_festival_turns: int = 0               # 남은 축제 지속 턴 수

    # In-Game Time & Periodical Publishing System
    calendar_epoch_name: str = "제국력"           # 기년법 연호 명칭 (예: "제국력", "성휘력", "태초력")
    start_year: int = 0                         # 0이면 cosmology_template/world_lore 또는 고유 시드 연도 사용
    distances: dict[str, float] = field(default_factory=dict) # 전투 엔티티 간 상대 거리 매트릭스 ("id_a::id_b" -> float meters)
    start_minute: int = 8 * 60                  # 기본 시작 시각: 1일차 월요일 08:00 (480분)
    last_daily_paper_day: int = 0               # 마지막으로 일간지가 발간된 날짜
    last_weekly_paper_week: int = 0             # 마지막으로 주간지가 발간된 주차
    pending_breaking_news: list[str] = field(default_factory=list) # 호외 발행 대기열
    environment: EnvironmentalMetrics = field(default_factory=EnvironmentalMetrics)
    pending_info_waves: list[PendingInformation] = field(default_factory=list)
    active_rumors: list = field(default_factory=list) # 활성화된 지리 도로망 소문 확산 웨이브 목록
    active_campsite: Any = None                         # 활성화된 야영지 상태 (CampsiteState)
    active_weather_anomalies: dict = field(default_factory=dict) # 활성화된 기상 이변 딕셔너리 {anomaly_id: ActiveWeatherAnomaly}
    active_corpses: dict = field(default_factory=dict)           # 활성화된 전장 시체 DB {corpse_id: CorpseInstance or dict}
    active_sieges: dict = field(default_factory=dict)            # 활성화된 공성전 DB {siege_id: SiegeBattleState or dict}
    pending_travel_waypoints: list[str] = field(default_factory=list) # 다중 구간 경로 이동 대기열 [waypoint_loc_id, ...]
    dilemmas_faced: list = field(default_factory=list)  # 플레이어가 직면한 윤리적 딜레마 기록



    @property
    def total_minutes(self) -> int:
        return self.start_minute + self.player.time_elapsed_minutes

    @property
    def current_day(self) -> int:
        return 1 + (self.total_minutes // (24 * 60))

    def get_power_scale_preset(self) -> Any:
        """현재 세계관의 성장 스케일 프리셋(PowerScalePreset) 객체 반환."""
        from src.world.stat_engine import StatEngine
        preset_id = getattr(self, "power_scale_preset_id", None) or "standard_fantasy"
        return StatEngine.get_preset(preset_id)

    @property
    def current_hour(self) -> int:
        return (self.total_minutes % (24 * 60)) // 60

    @property
    def current_minute(self) -> int:
        return self.total_minutes % 60

    @property
    def current_week(self) -> int:
        return 1 + ((self.current_day - 1) // 7)

    @property
    def day_of_week_ko(self) -> str:
        days = ["월", "화", "수", "목", "금", "토", "일"]
        return days[(self.current_day - 1) % 7]

    @property
    def effective_start_year(self) -> int:
        if self.start_year > 0:
            return self.start_year
        if self.cosmology_template and "start_year" in self.cosmology_template:
            try:
                return int(self.cosmology_template["start_year"])
            except (ValueError, TypeError):
                pass
        if self.world_lore and "start_year" in self.world_lore:
            try:
                return int(self.world_lore["start_year"])
            except (ValueError, TypeError):
                pass
        # Deterministic seed based on world_id or world_name
        seed_str = self.world_id or self.world_name or "quilltale_default"
        val = sum(ord(c) * (i + 1) for i, c in enumerate(seed_str))
        return 100 + (val % 2500)

    @property
    def current_year(self) -> int:
        days_per_year = max(1, self.days_per_month * self.months_per_year)
        return self.effective_start_year + ((self.current_day - 1) // days_per_year)

    @property
    def current_month(self) -> int:
        return 1 + (((self.current_day - 1) // max(1, self.days_per_month)) % max(1, self.months_per_year))

    @property
    def current_day_of_month(self) -> int:
        return 1 + ((self.current_day - 1) % max(1, self.days_per_month))

    @property
    def current_season(self) -> str:
        m = self.current_month
        if 3 <= m <= 5:
            return "봄 (해빙기)"
        elif 6 <= m <= 8:
            return "여름 (혹서기)"
        elif 9 <= m <= 11:
            return "가을 (수확기)"
        return "겨울 (혹한기)"

    @property
    def calendar_display_ko(self) -> str:
        return f"{self.calendar_epoch_name} {self.current_year}년 {self.current_month}월 {self.current_day_of_month}일 ({self.day_of_week_ko}요일) {self.current_hour:02d}:{self.current_minute:02d} [{self.current_season}]"

    def get_distance(self, entity_a_id: str, entity_b_id: str, default: float = 5.0) -> float:
        """두 엔티티 간의 상대 거리(미터) 반환 (대칭 거리)."""
        if entity_a_id == entity_b_id:
            return 0.0
        k = f"{min(entity_a_id, entity_b_id)}::{max(entity_a_id, entity_b_id)}"
        return self.distances.get(k, default)

    def set_distance(self, entity_a_id: str, entity_b_id: str, distance_m: float) -> None:
        """두 엔티티 간의 상대 거리(미터) 설정 (대칭 거리)."""
        if entity_a_id == entity_b_id:
            return
        k = f"{min(entity_a_id, entity_b_id)}::{max(entity_a_id, entity_b_id)}"
        self.distances[k] = max(0.0, round(float(distance_m), 2))

    @property
    def time_display_ko(self) -> str:
        return f"{self.current_day}일차 {self.day_of_week_ko}요일 {self.current_hour:02d}:{self.current_minute:02d}"

    @property
    def traits(self) -> list[str]:
        return self.world_traits

    def sync_infrastructure_totals(self) -> None:
        """Rolls up population and area from infrastructure into WorldState."""
        if self.infrastructure and hasattr(self.infrastructure, "get_world_totals"):
            totals = self.infrastructure.get_world_totals()
            self.total_population = totals.get("total_population", 0)
            self.total_area_sq_km = totals.get("total_area_sq_km", 0.0)

    def current_location(self) -> Location | None:
        return self.locations.get(self.player.location)

    def items_in_location(self, location_id: str) -> list[Item]:
        loc = self.locations.get(location_id)
        if not loc:
            return []
        unique_iids = list(dict.fromkeys(loc.items))
        return [self.items[i] for i in unique_iids if i in self.items]

    def npcs_in_location(self, location_id: str) -> list[NPC]:
        loc = self.locations.get(location_id)
        if not loc:
            return []
        unique_nids = list(dict.fromkeys(loc.npcs))
        return [self.npcs[n] for n in unique_nids if n in self.npcs]


    def player_inventory_items(self) -> list[Item]:
        return [self.items[i] for i in self.player.inventory if i in self.items]

    def get_equipped_weapon_item(self) -> Item | None:
        wep_id = self.player.equipment.weapon
        if wep_id and wep_id in self.items:
            return self.items[wep_id]
        return None

    def recalculate_equipment_stats(self, entity: Any = None):
        """Calculates and updates total equipment defense and stat bonuses onto the entity."""
        from src.world.equipment import EquipmentEngine
        target = entity if entity is not None else self.player
        bonuses = EquipmentEngine.calculate_equipment_bonuses(self, target)
        target.equipment_defense = bonuses["total_defense"]
        target.equipment_stat_bonuses = bonuses["stat_bonuses"]
        target.equipment_active_set_bonuses = bonuses.get("active_set_bonuses", [])
        target.equipment_active_traits = bonuses.get("active_traits", [])

    def simulate_npc_needs_and_economy(self) -> list[str]:
        """
        Simulates autonomous needs, consumption, and economy for all alive NPCs (Zero-Token Local Execution).
        - Increases hunger, updates goals based on deficits.
        - NPCs consume healing/food items if injured or starving.
        - Merchants and workers adjust goals and wealth.
        """
        logs = []
        for npc_id, npc in self.npcs.items():
            if not npc.alive:
                continue
            
            # 1. Needs progression
            npc.needs.hunger = min(100, npc.needs.hunger + 1)
            npc.needs.social = min(100, npc.needs.social + 1)
            
            # 2. Consumption / Recovery
            if npc.health < npc.max_health:
                # Check for potion/bandage in inventory
                for item_id in list(npc.inventory):
                    item = self.items.get(item_id)
                    if item and ("포션" in item.name or "붕대" in item.name or "약초" in item.name):
                        heal_amount = 20
                        npc.health = min(npc.max_health, npc.health + heal_amount)
                        npc.inventory.remove(item_id)
                        logs.append(f"NPC {npc.name} used {item.name} (HP: {npc.health}/{npc.max_health})")
                        break
            
            # 3. Goal Adjustment based on urgent needs (GOAP)
            if npc.needs.hunger >= 80:
                npc.goal = "식료품을 구하거나 식당을 찾는 중"
            elif npc.needs.wealth >= 80:
                npc.goal = "수익을 창출하거나 일거리를 모색 중"
            elif npc.needs.safety >= 75:
                npc.goal = "위협을 피해 안전한 은신처 확보 중"
            elif not npc.goal and npc.interests:
                npc.goal = f"{npc.interests[0]}에 집중하는 중"

        return logs

    def exchange_rumors_in_locations(self) -> list[str]:
        """
        Gossip Chain Network: NPCs in the same location exchange high-significance memories/rumors.
        Zero token consumption.
        """
        gossip_logs = []
        for loc_id, loc in self.locations.items():
            loc_npcs = [self.npcs[nid] for nid in loc.npcs if nid in self.npcs and self.npcs[nid].alive]
            if len(loc_npcs) < 2:
                continue

            # Pool top memories from all present NPCs
            for i in range(len(loc_npcs)):
                for j in range(i + 1, len(loc_npcs)):
                    npc_a = loc_npcs[i]
                    npc_b = loc_npcs[j]

                    # A shares with B
                    for mem in npc_a.relevant_memories(max_memories=2):
                        if mem.significance >= 3:
                            # Check if B already knows
                            already_known = any(mem.description in m.description for m in npc_b.memories)
                            if not already_known:
                                shared_entry = MemoryEntry(
                                    turn=self.turn,
                                    description=f"[{npc_a.name}에게 들은 소문] {mem.description}",
                                    emotional_tone=mem.emotional_tone,
                                    significance=max(1, mem.significance - 1),
                                    is_anchor=False
                                )
                                npc_b.memories.append(shared_entry)
                                npc_b.needs.social = max(0, npc_b.needs.social - 20)
                                gossip_logs.append(f"{npc_a.name} shared rumor with {npc_b.name} at {loc.name}")

        return gossip_logs

    def generate_news_poster(self, news_text: str, turn: int) -> Item:
        """
        Creates an interactive readable in-game flyer/poster item from world news
        and posts it only if a dedicated public bulletin board location exists.
        """
        poster_id = f"news_poster_turn_{turn}"
        target_loc_id = "market" if "market" in self.locations else ("tavern" if "tavern" in self.locations else None)
        
        formatted_doc = f"📜 [제{turn}보] [{self.world_name} 치안대보] {news_text}"

        poster_item = Item(
            id=poster_id,
            name=f"【갓 붙은 벽보 (제{turn}보)】",
            description=f"벽에 갓 풀칠되어 붙은 전단지다. 잉크 냄새가 채 가시지 않았으며 '{news_text[:20]}...'라는 문구가 눈에 띈다.",
            location=target_loc_id or "inventory",
            item_type="document",
            weight=0.1,
            size="small",
            required_strength=1,
            can_store_in_bag=True,
            can_wield_as_weapon=False,
            document_text=formatted_doc
        )

        self.items[poster_id] = poster_item
        if target_loc_id and target_loc_id in self.locations:
            if poster_id not in self.locations[target_loc_id].items:
                self.locations[target_loc_id].items.append(poster_id)

        return poster_item

    def check_and_publish_periodicals(self) -> list[Item]:
        """
        In-Game Time Periodical Publishing Engine:
        1. Daily Morning Paper: Published every day at 08:00 AM (local news, weather, notices).
        2. Weekly Gazette: Published every Monday at 08:00 AM (regional politics, major bounties).
        3. Breaking News / Extra Edition: Published the next morning at 08:00 AM after critical world events.
        Only places physical paper items if a designated public hub (market/tavern/library) exists.
        """
        published = []
        target_loc_id = "market" if "market" in self.locations else ("tavern" if "tavern" in self.locations else None)

        # Check if current time is 08:00 AM or later and we haven't published today's papers yet
        if self.current_hour >= 8 and self.last_daily_paper_day < self.current_day:
            day = self.current_day
            dow = self.day_of_week_ko
            self.last_daily_paper_day = day

            # 1. Daily Morning Paper
            recent_gossip = self.world_facts[-1] if self.world_facts else f"{self.world_name} 가도에 짙은 안개가 끼어 통행 주의 요망."
            daily_doc = f"[{self.world_name} 일간 조간보 제{day}일차 ({dow}요일)] 주요 소식: {recent_gossip}"

            daily_item = Item(
                id=f"daily_paper_day_{day}",
                name=f"【{self.world_name} 조간신문 (제{day}일차)】",
                description=f"오늘 아침 8시에 갓 배포된 일간 조간신문이다. 잉크 냄새와 함께 '{dow}요일' 활자가 선명하다.",
                location=target_loc_id or "inventory",
                item_type="document",
                weight=0.1,
                size="small",
                required_strength=1,
                can_store_in_bag=True,
                can_wield_as_weapon=False,
                document_text=daily_doc
            )
            self.items[daily_item.id] = daily_item
            if target_loc_id and target_loc_id in self.locations:
                if daily_item.id not in self.locations[target_loc_id].items:
                    self.locations[target_loc_id].items.append(daily_item.id)
            published.append(daily_item)

            # 2. Weekly Gazette (Published on Monday 08:00 AM)
            week = self.current_week
            if dow == "월" and self.last_weekly_paper_week < week:
                self.last_weekly_paper_week = week
                weekly_doc = f"[{self.world_name} 주간 종합 연대보 제{week}주차] 대륙 정세 및 주요 현상 수배령 공고."

                weekly_item = Item(
                    id=f"weekly_gazette_week_{week}",
                    name=f"【{self.world_name} 주간 연대보 (제{week}주차)】",
                    description="매주 월요일 아침에만 발행되는 두툼한 주간 연대보 양장본이다.",
                    location=target_loc_id or "inventory",
                    item_type="document",
                    weight=0.3,
                    size="small",
                    required_strength=1,
                    can_store_in_bag=True,
                    can_wield_as_weapon=False,
                    document_text=weekly_doc
                )
                self.items[weekly_item.id] = weekly_item
                if target_loc_id and target_loc_id in self.locations:
                    if weekly_item.id not in self.locations[target_loc_id].items:
                        self.locations[target_loc_id].items.append(weekly_item.id)
                published.append(weekly_item)

            # 3. Breaking News / Extra Edition (Next morning after critical events)
            if self.pending_breaking_news:
                breaking_summary = " / ".join(self.pending_breaking_news)
                extra_doc = f"🚨🚨 【긴급 호외 (EXTRA EDITION): 특보】 [{self.world_name} 제{day}일] 사건 전말: {breaking_summary}"

                extra_item = Item(
                    id=f"extra_edition_day_{day}",
                    name=f"【🚨 긴급 호외: 특보 (제{day}일)】",
                    description="붉은 인장이 찍힌 채 나붙은 긴급 호외 전단지다.",
                    location=target_loc_id or "inventory",
                    item_type="document",
                    weight=0.1,
                    size="small",
                    required_strength=1,
                    can_store_in_bag=True,
                    can_wield_as_weapon=False,
                    document_text=extra_doc
                )
                self.items[extra_item.id] = extra_item
                if target_loc_id and target_loc_id in self.locations:
                    if extra_item.id not in self.locations[target_loc_id].items:
                        self.locations[target_loc_id].items.append(extra_item.id)
                published.append(extra_item)
                self.pending_breaking_news.clear()


        return published





    def advance_information_waves(self) -> list[str]:
        """
        Advance information travel delay across regions.
        When remaining_turns hits 0, the event reaches target NPCs' beliefs and world rumors.
        """
        propagated_news = []
        remaining_waves = []
        for wave in self.pending_info_waves:
            wave.remaining_turns -= 1
            if wave.remaining_turns <= 0:
                # Event arrived with human whisper distortion!
                distorted_text = wave.distort_event()
                propagated_news.append(distorted_text)
                if wave.target_npcs:
                    for nid in wave.target_npcs:
                        if nid in self.npcs:
                            self.npcs[nid].beliefs.append(f"[풍문] {distorted_text}")
                else:
                    # Global rumor reached all NPCs
                    for npc in self.npcs.values():
                        npc.beliefs.append(f"[소문] {distorted_text}")
                self.world_facts.append(f"[도달한 소식] {distorted_text}")
            else:
                remaining_waves.append(wave)
        self.pending_info_waves = remaining_waves

        # Geographic Road-Network Rumor Diffusion
        from src.world.rumor_diffusion_engine import RumorDiffusionEngine
        geo_rumors = RumorDiffusionEngine.advance_time_tick(self, elapsed_minutes=0)
        propagated_news.extend(geo_rumors)

        return propagated_news

    def advance_world_simulation(self) -> dict:
        """
        Master tick for the 5-pillar living world ecosystem.
        Runs timeline schedules, needs & economy, and gossip propagation.
        """
        schedule_events = self.advance_npc_schedules()
        economy_events = self.simulate_npc_needs_and_economy()
        gossip_events = self.exchange_rumors_in_locations()
        return {
            "schedules": schedule_events,
            "economy": economy_events,
            "gossip": gossip_events
        }

    def advance_npc_schedules(self) -> list[str]:

        """
        Advances all NPC schedules according to the current world turn.
        Updates NPC locations, records physical traces on previous locations,
        and logs off-screen narrative events.
        """
        events = []
        for npc_id, npc in self.npcs.items():
            if not npc.alive or not npc.schedule:
                continue

            # Find matching schedule for current turn
            active_plan = None
            for plan in npc.schedule:
                if "turn" in plan:
                    if plan["turn"] == self.turn:
                        active_plan = plan
                        break
                elif "turn_start" in plan:
                    turn_start = plan.get("turn_start", 0)
                    turn_end = plan.get("turn_end", 9999)
                    if turn_start <= self.turn <= turn_end:
                        active_plan = plan
                        break


            if active_plan:
                target_loc = active_plan.get("location")
                activity = active_plan.get("activity", "")
                
                # Check if movement is required
                if target_loc and target_loc in self.locations and target_loc != npc.location:
                    old_loc_id = npc.location
                    if old_loc_id in self.locations:
                        old_loc = self.locations[old_loc_id]
                        if npc_id in old_loc.npcs:
                            old_loc.npcs.remove(npc_id)
                        # Leave physical trace in old location
                        trace_desc = active_plan.get("trace_left", f"{npc.display_name_ko}이(가) 서둘러 이동하며 남긴 발자국과 흔적")
                        old_loc.physical_traces.append({
                            "npc_id": npc.id,
                            "npc_name": npc.name,
                            "trace": trace_desc,
                            "turn": self.turn
                        })

                    new_loc = self.locations[target_loc]
                    if npc_id not in new_loc.npcs:
                        new_loc.npcs.append(npc_id)
                    npc.location = target_loc
                    events.append(f"NPC {npc.name} moved to {new_loc.name} for: {activity}")

                if activity:
                    npc.current_activity = activity
                    # Log off-screen event if player is not in the same location
                    if npc.location != self.player.location:
                        log_entry = f"턴 {self.turn} [{self.locations.get(npc.location, Location(id='', name='', description='', exits={})).name}]: {activity}"
                        npc.off_screen_logs.append(log_entry)
                        if len(npc.off_screen_logs) > 10:
                            npc.off_screen_logs = npc.off_screen_logs[-10:]

        # Decay & cap physical traces across all locations (max 10, decay after 15 turns)
        for loc in self.locations.values():
            if loc.physical_traces:
                loc.physical_traces = [
                    t for t in loc.physical_traces
                    if isinstance(t, dict) and (self.turn - t.get("turn", self.turn)) <= 15
                ][-10:]

        return events

    def get_off_screen_context_for_location(self, loc_id: str) -> str:
        """
        Synthesizes off-screen backstory, traces, and timeline status for NPCs in the given location.
        Used by GM to generate realistic reunion narratives.
        """
        lines = []
        loc = self.locations.get(loc_id)
        if not loc:
            return ""

        # Physical traces in location
        if loc.physical_traces:
            recent_traces = loc.physical_traces[-3:]
            lines.append("[현장에 남겨진 물리적 흔적 및 단서]")
            for t in recent_traces:
                lines.append(f"- (턴 {t.get('turn', '?')}) {t.get('trace', '')}")

        # Off-screen NPC backstory summaries
        loc_npcs = self.npcs_in_location(loc_id)
        for npc in loc_npcs:
            if not npc.alive:
                continue
            
            npc_header = f"[{npc.display_name_ko} (진실: {npc.name})의 부재중 타임라인 & 현재 상태]"
            sublines = [npc_header]
            if npc.interests:
                sublines.append(f"  * 관심사/목표: {', '.join(npc.interests)}")
            if npc.current_activity:
                sublines.append(f"  * 현재 처한 상황/행동: {npc.current_activity}")
            if npc.fatigue > 0:
                sublines.append(f"  * 내부 피로도: {npc.fatigue}/100")
            if npc.off_screen_logs:
                sublines.append("  * 플레이어 시야 밖 겪은 사건 기록:")
                for log in npc.off_screen_logs[-3:]:
                    sublines.append(f"    - {log}")
            
            turns_away = self.turn - npc.last_seen_turn if npc.last_seen_turn > 0 else self.turn
            if turns_away > 1:
                sublines.append(f"  * 플레이어와 {turns_away}턴 만에 재회함 (외형/복장/태도 변화로 부재 중 사건을 역산 묘사하십시오)")

            lines.append("\n".join(sublines))

        return "\n\n".join(lines)


    def to_context_summary(self) -> str:
        """Structured deterministic ground-truth block for GM synthesis."""
        loc = self.current_location()
        if not loc:
            return "ERROR: Player location not found."

        loc_items = self.items_in_location(self.player.location)
        loc_npcs = self.npcs_in_location(self.player.location)
        player_items = self.player_inventory_items()

        exits_str = ", ".join(
            f"{d} → {self.locations[lid].name} [id:{lid}]"
            for d, lid in loc.exits.items()
            if lid in self.locations
        ) or "none"

        items_str = ", ".join(f"{i.name} [id:{i.id}]" for i in loc_items) or "none"

        npc_lines = []
        for n in loc_npcs:
            status = "alive" if n.alive else "dead"
            legacy_tag = " (전대 모험가/레거시)" if n.is_legacy else ""
            stat_revealed_str = "StatsRevealed:YES" if n.stats_revealed else "StatsRevealed:NO"
            name_known_str = f"NameKnownToPlayer:YES(호칭:{n.name})" if n.name_revealed else f"NameKnownToPlayer:NO(호칭:{n.job or '술집 주인'} 등 겉보기 역할로만 서술! 실명 '{n.name}' 노출 절대 금지)"
            wep = n.equipment.weapon or "맨손"
            npc_lines.append(
                f"[id:{n.id}] {n.name}{legacy_tag} (직업:{n.job}, {name_known_str}, 무기:{wep}, HP:{n.health}/{n.max_health}, AC:{n.armor_class}, 골드:{n.gold}G, 목표:'{n.goal or n.current_activity}', {n.disposition}, {status}, {stat_revealed_str})"
            )
        npcs_str = ", ".join(npc_lines) or "none"


        inv_str = ", ".join(f"{i.name} [id:{i.id}]" for i in player_items) or "nothing"

        memory_block = ""
        if loc_npcs:
            memory_lines = []
            for npc in loc_npcs:
                if npc.alive:
                    memory_lines.append(f"[id:{npc.id}] {npc.memory_summary()}")
            if memory_lines:
                memory_block = "\nNPC MEMORIES (what present NPCs remember):\n" + "\n".join(memory_lines)

        npc_beliefs_block = ""
        if loc_npcs:
            belief_lines = []
            for npc in loc_npcs:
                if npc.alive and npc.beliefs:
                    for b in npc.beliefs:
                        belief_lines.append(f"  * [{npc.name} / id:{npc.id}의 개인적 시각/믿음]: {b}")
            if belief_lines:
                npc_beliefs_block = "\n[🧠 현장 인물들의 개인적 세계관/역사 인식 & 믿음 (NPC Beliefs & Perspective Bias)]:\n" + "\n".join(belief_lines)

        rumor_block = ""
        if self.world_facts:
            rumor_block = "\nGLOBAL WORLD FACTS / RUMORS:\n" + "\n".join(
                f"- {fact}" for fact in self.world_facts[-10:]
            )

        cosmo_block = ""
        cosmo_data = self.cosmology_template or self.world_lore
        if cosmo_data and isinstance(cosmo_data, dict):
            cosmo_lines = []
            cosmo_sub = cosmo_data.get("cosmology", {})
            if isinstance(cosmo_sub, dict):
                if cosmo_sub.get("sun_and_moons"):
                    cosmo_lines.append(f"  * [천체 현상]: {cosmo_sub['sun_and_moons']}")
                if cosmo_sub.get("mana_origin"):
                    cosmo_lines.append(f"  * [마나 기원]: {cosmo_sub['mana_origin']}")
                if cosmo_sub.get("divine_order"):
                    cosmo_lines.append(f"  * [신들의 질서]: {cosmo_sub['divine_order']}")

            magic_sub = cosmo_data.get("magic_rules", {})
            if isinstance(magic_sub, dict):
                if magic_sub.get("incantation_system"):
                    cosmo_lines.append(f"  * [영창 원리]: {magic_sub['incantation_system']}")
                if magic_sub.get("forbidden_magic"):
                    cosmo_lines.append(f"  * [금지 마법]: {magic_sub['forbidden_magic']}")
                if magic_sub.get("magic_cost"):
                    cosmo_lines.append(f"  * [마법 대가/부작용]: {magic_sub['magic_cost']}")

            curr_sub = cosmo_data.get("currency_and_laws", {})
            if isinstance(curr_sub, dict):
                if curr_sub.get("official_currency"):
                    cosmo_lines.append(f"  * [통용 화폐]: {curr_sub['official_currency']}")
                if curr_sub.get("contraband"):
                    cosmo_lines.append(f"  * [절대 밀수품]: {curr_sub['contraband']}")
                if curr_sub.get("global_laws"):
                    laws_str = " | ".join(curr_sub["global_laws"]) if isinstance(curr_sub["global_laws"], list) else str(curr_sub["global_laws"])
                    cosmo_lines.append(f"  * [세계 법률]: {laws_str}")

            if cosmo_lines:
                cosmo_block = "\n[🌌 세계관 고유 법칙 & 규칙 (Cosmology & Laws)]:\n" + "\n".join(cosmo_lines)

        arcane_laws_block = ""
        arcane_laws = self.world_lore.get("arcane_laws", [])
        if arcane_laws:
            laws_lines = []
            for law in arcane_laws:
                if isinstance(law, dict):
                    name = law.get('name', '')
                    effect = law.get('mechanical_effect', law.get('core_principle', ''))
                    laws_lines.append(f"  * [{name}]: {effect}" if effect else f"  * [{name}]")
                elif isinstance(law, str):
                    laws_lines.append(f"  * {law}")
            arcane_laws_block = "\n[🔮 이 세계의 특수 판타지 생체·물리 법칙 (Arcane Biomechanics)]:\n" + "\n".join(laws_lines)

        factions_block = ""
        if self.factions:
            fac_lines = []
            for f_id, fac in self.factions.items():
                colors_str = "/".join(fac.flag_colors) if fac.flag_colors else "미상"
                motto_str = f", 표어: '{fac.motto}'" if fac.motto else ""
                fac_lines.append(
                    f"  * [{fac.name}] 상징 동물: {fac.emblem_animal} | 깃발 색: {colors_str} | 문양: {fac.flag_symbol}{motto_str} (체제: {fac.system}, {fac.power_level})"
                )
            factions_block = "\n[🚩 국가/세력 깃발 및 상징 문장 (Factions & Heraldry)]:\n" + "\n".join(fac_lines)

        eq_wep = self.get_equipped_weapon_item()
        wep_name = f"{eq_wep.name} (공격력+{eq_wep.damage})" if eq_wep else "맨손 (공격력 1)"

        return f"""WORLD STATE (TURN {self.turn}) — GROUND TRUTH (CANNOT BE CONTRADICTED):
Location: {loc.name} [id:{loc.id}]
Description: {loc.description}
Valid Exits: {exits_str}
Items Here: {items_str}
NPCs Present: {npcs_str}
Player: {self.player.name} (Level {self.player.level}, HP {self.player.health}/{self.player.max_health}, Gold {self.player.gold}, Rep {self.player.reputation})
Player Stats: STR {self.player.strength} (+{self.player.str_mod}), AGI {self.player.agility} (+{self.player.agi_mod}), INT {self.player.intelligence} (+{self.player.int_mod})
Equipped Weapon: {wep_name}
Player Inventory: {inv_str}{memory_block}{npc_beliefs_block}{rumor_block}{cosmo_block}{arcane_laws_block}{factions_block}
"""


    def to_player_summary(self) -> str:
        """100% Korean formatted player status screen for Gradio UI with Fog of War on NPC stats and names."""
        loc = self.current_location()
        if not loc:
            return "현재 위치를 알 수 없습니다."

        loc_items = self.items_in_location(self.player.location)
        loc_npcs = self.npcs_in_location(self.player.location)
        player_items = self.player_inventory_items()

        # Story-driven prominent NPC selection
        recent_narration = self.history[-1].get("narration", "") if self.history else ""
        last_actor_id = self.last_npc_action.get("npc_id", "") if isinstance(self.last_npc_action, dict) else ""

        def npc_prominence_score(npc: NPC) -> int:
            score = 0
            if npc.id == last_actor_id:
                score += 50
            if recent_narration:
                if npc.name in recent_narration:
                    score += 40
                if npc.job and npc.job in recent_narration:
                    score += 30
                if npc.alias_ko and npc.alias_ko in recent_narration:
                    score += 30
            if npc.name_revealed:
                score += 20
            if npc.is_legacy:
                score += 15
            if npc.disposition in ["hostile", "allied"]:
                score += 10
            return score

        if len(loc_npcs) > 2:
            display_npcs = sorted(loc_npcs, key=npc_prominence_score, reverse=True)[:2]
        else:
            display_npcs = loc_npcs

        exits = ", ".join(
            f"**{d}** → {self.locations[lid].name}"
            for d, lid in loc.exits.items()
            if lid in self.locations
        ) or "없음"

        items = ", ".join(i.name for i in loc_items) or "없음"

        # Fog of war formatting for NPCs (Hide true name until introduced)
        npc_lines = []
        for n in display_npcs:
            if not n.alive:
                npc_lines.append(f"{n.display_name_ko} (사망 💀)")
                continue
            legacy_badge = " [전대 모험가] " if (n.is_legacy and n.name_revealed) else " "
            disp_str = n.disposition_ko if n.name_revealed else DISPOSITION_KO_MAP.get(n.disposition.lower(), "무표정 ⚪")
            if n.stats_revealed:
                # Combat / observation revealed true stats
                npc_lines.append(
                    f"{n.display_name_ko}{legacy_badge}({disp_str} | HP:{n.health}/{n.max_health} | 방어:{n.armor_class})"
                )
            else:
                # Fog of War: Show impression only
                npc_lines.append(
                    f"{n.display_name_ko}{legacy_badge}({disp_str} | [{n.impression_ko}])"
                )

        npcs_str = ", ".join(npc_lines) or "없음"



        visited = [
            loc_obj.name for lid, loc_obj in self.locations.items()
            if loc_obj.visited and lid != self.player.location
        ]
        visited_str = ", ".join(visited) if visited else "없음"
        
        equipped = vars(self.player.equipment)
        equipped_ids = set()
        for k, v in equipped.items():
            if isinstance(v, list):
                equipped_ids.update(v)
            elif v:
                equipped_ids.add(v)

        carrying = ", ".join(
            f"{i.name}{' [장착중]' if i.id in equipped_ids else ''}"
            for i in player_items
        ) or "없음"

        dice_log = ""
        if self.last_dice_result:
            dice_log = f"\n\n🎲 **최근 판정:** {self.last_dice_result.get('summary_ko', '')}"

        npc_turn_log = ""
        if self.last_npc_action:
            npc_turn_log = f"\n👥 **주변 인물 행동:** {self.last_npc_action.get('summary_ko', '')}"

        # Equipment slots summary
        equipment_lines = []
        if self.player.equipment.weapon and self.player.equipment.weapon in self.items:
            equipment_lines.append(f"무기: {self.items[self.player.equipment.weapon].name}")
        if self.player.equipment.head and self.player.equipment.head in self.items:
            equipment_lines.append(f"머리: {self.items[self.player.equipment.head].name}")
        if self.player.equipment.face and self.player.equipment.face in self.items:
            equipment_lines.append(f"얼굴: {self.items[self.player.equipment.face].name}")
        if self.player.equipment.neck and self.player.equipment.neck in self.items:
            equipment_lines.append(f"목: {self.items[self.player.equipment.neck].name}")
        if self.player.equipment.chest and self.player.equipment.chest in self.items:
            equipment_lines.append(f"상의: {self.items[self.player.equipment.chest].name}")
        if self.player.equipment.innerwear and self.player.equipment.innerwear in self.items:
            equipment_lines.append(f"이너: {self.items[self.player.equipment.innerwear].name}")
        if self.player.equipment.shoulders and self.player.equipment.shoulders in self.items:
            equipment_lines.append(f"어깨: {self.items[self.player.equipment.shoulders].name}")
        if self.player.equipment.belt and self.player.equipment.belt in self.items:
            equipment_lines.append(f"허리: {self.items[self.player.equipment.belt].name}")
        if self.player.equipment.legs and self.player.equipment.legs in self.items:
            equipment_lines.append(f"하의: {self.items[self.player.equipment.legs].name}")
        if self.player.equipment.boots and self.player.equipment.boots in self.items:
            equipment_lines.append(f"신발: {self.items[self.player.equipment.boots].name}")
        if self.player.equipment.gloves and self.player.equipment.gloves in self.items:
            equipment_lines.append(f"장갑: {self.items[self.player.equipment.gloves].name}")
        if self.player.equipment.cape and self.player.equipment.cape in self.items:
            equipment_lines.append(f"망토: {self.items[self.player.equipment.cape].name}")
        if self.player.equipment.storage and self.player.equipment.storage in self.items:
            equipment_lines.append(f"수납: {self.items[self.player.equipment.storage].name}")
        for idx, ring in enumerate(self.player.equipment.rings):
            if ring in self.items:
                equipment_lines.append(f"반지{idx+1}: {self.items[ring].name}")
        for idx, earring in enumerate(self.player.equipment.earrings):
            if earring in self.items:
                equipment_lines.append(f"귀걸이{idx+1}: {self.items[earring].name}")
        for idx, bracelet in enumerate(getattr(self.player.equipment, "bracelets", [])):
            if bracelet in self.items:
                equipment_lines.append(f"팔찌{idx+1}: {self.items[bracelet].name}")
        
        equipment_str = ", ".join(equipment_lines) if equipment_lines else "없음"
        
        title_str = ""
        if self.player.active_title and self.player.active_title in self.titles_db:
            title_str = f" | 👑 **칭호:** {self.titles_db[self.player.active_title].name}"

        # Skills summary
        passives = sum(1 for s in self.player.skills if s in self.skills_db and self.skills_db[s].skill_type == 'passive')
        actives = sum(1 for s in self.player.skills if s in self.skills_db and self.skills_db[s].skill_type == 'active')
        uniques = sum(1 for s in self.player.skills if s in self.skills_db and self.skills_db[s].skill_type == 'unique')
        skill_str = f"패시브 {passives}개, 액티브 {actives}개, 고유 {uniques}개"

        return (
            f"⚔️ **[턴 {self.turn}] {self.world_name}**\n\n"
            f"📍 **현재 위치:** {loc.name}\n"
            f"{loc.description}\n\n"
            f"🚪 **이동 가능한 경로:** {exits}\n"
            f"📦 **주변 물건:** {items}\n"
            f"👤 **주변 인물:** {npcs_str}\n"
            f"🗺️ **발견한 지역:** {visited_str}\n\n"
            f"--- **캐릭터 정보** ---\n"
            f"❤️ **체력:** {self.player.health} / {self.player.max_health} | 💧 **마나:** {self.player.mana} / {self.player.max_mana_effective} | 🏆 **레벨:** {self.player.level} (EXP: {self.player.exp}/100)\n"
            f"💪 **능력치:** 근력(STR) {self.player.strength} | 민첩(AGI) {self.player.agility} | 지능(INT) {self.player.intelligence} | 체력(CON) {self.player.constitution} | 지혜(WIS) {self.player.wisdom} | 행운(LUK) {self.player.luck}\n"
            f"💥 **치명타율:** {self.player.effective_crit_rate:.1f}% | 🩸 **치명타피해:** {self.player.effective_crit_damage:.1f}%\n"
            f"🗡️ **장착 장비:** {equipment_str}\n"
            f"💰 **소지금:** {self.player.gold} 골드{title_str}\n"
            f"✨ **스킬:** {skill_str}\n"
            f"🎒 **소지품:** {carrying}"
            f"{dice_log}"
            f"{npc_turn_log}"
        )

    def to_player_summary_html(self) -> str:
        """HTML representation with interactive hover tooltip cards for stats and items."""
        loc = self.current_location()
        if not loc:
            return "<div class='qt-panel-content'>현재 위치를 알 수 없습니다.</div>"

        loc_items = self.items_in_location(self.player.location)
        loc_npcs = self.npcs_in_location(self.player.location)

        # Story-driven prominent NPC selection:
        # Prioritize NPCs active in current turn or mentioned in recent narration
        recent_narration = self.history[-1].get("narration", "") if self.history else ""
        last_actor_id = self.last_npc_action.get("npc_id", "") if isinstance(self.last_npc_action, dict) else ""

        def npc_prominence_score(npc: NPC) -> int:
            score = 0
            if npc.id == last_actor_id:
                score += 50
            if recent_narration:
                if npc.name in recent_narration:
                    score += 40
                if npc.job and npc.job in recent_narration:
                    score += 30
                if npc.alias_ko and npc.alias_ko in recent_narration:
                    score += 30
            if npc.name_revealed:
                score += 20
            if npc.is_legacy:
                score += 15
            if npc.disposition in ["hostile", "allied"]:
                score += 10
            return score

        if len(loc_npcs) > 2:
            display_npcs = sorted(loc_npcs, key=npc_prominence_score, reverse=True)[:2]
        else:
            display_npcs = loc_npcs

        exits_html = ", ".join(
            f"<span class='qt-exit-tag'><b>{d}</b> → {self.locations[lid].name}</span>"
            for d, lid in loc.exits.items()
            if lid in self.locations
        ) or "없음"

        items_html = ", ".join(
            f"<span class='qt-hover-tag' data-tooltip='{i.tooltip_text}'>{i.name}</span>"
            for i in loc_items
        ) or "없음"



        npc_htmls = []
        seen_names = set()
        has_legacy = False
        for n in display_npcs:
            if n.is_legacy:
                if has_legacy:
                    continue
                has_legacy = True

            disp_name = n.display_name_ko
            if disp_name in seen_names:
                continue
            seen_names.add(disp_name)

            if not n.alive:
                npc_htmls.append(f"<span class='qt-dead-npc'>{disp_name} (사망 💀)</span>")
                continue

            # Tooltip: only safe observable physical impression, no internal psychology or personality leaks
            tt_lines = [f"인상: {n.impression_ko}"]
            if n.name_revealed and n.attitude_description:
                tt_lines.append(f"태도: {n.attitude_description}")
            if n.stats_revealed:
                tt_lines.append(f"체력: {n.health}/{n.max_health} | 방어: {n.armor_class}")
            tt_content = "&#10;".join(tt_lines)

            # [전대] badge only shown once the NPC identity is revealed to the player
            badge = " <span class='qt-legacy-badge'>[전대]</span>" if (n.is_legacy and n.name_revealed) else ""
            
            # If name is not revealed, show only basic surface disposition (e.g. 경계 🟡), never internal traits
            if n.name_revealed:
                disp_text = n.disposition_ko
            else:
                disp_text = DISPOSITION_KO_MAP.get(n.disposition.lower(), "무표정 ⚪")

            npc_htmls.append(
                f"<span class='qt-hover-tag' data-tooltip='{tt_content}'>{disp_name}{badge} ({disp_text})</span>"
            )

        npcs_html = ", ".join(npc_htmls) or "없음"



        # Equipment formatted with hover cards
        eq_tags = []
        for slot_name, item_id in [
            ("무기", self.player.equipment.weapon),
            ("머리", self.player.equipment.head),
            ("얼굴", self.player.equipment.face),
            ("목", getattr(self.player.equipment, "neck", None)),
            ("어깨", getattr(self.player.equipment, "shoulders", None)),
            ("상의", self.player.equipment.chest),
            ("이너", getattr(self.player.equipment, "innerwear", None)),
            ("허리", getattr(self.player.equipment, "belt", None)),
            ("하의", self.player.equipment.legs),
            ("신발", self.player.equipment.boots),
            ("장갑", self.player.equipment.gloves),
            ("망토", self.player.equipment.cape),
            ("수납", getattr(self.player.equipment, "storage", None)),
        ]:

            if item_id and item_id in self.items:
                item = self.items[item_id]
                tt = f"슬롯: {slot_name}\n" + item.tooltip_text
                eq_tags.append(f"<span class='qt-hover-tag' data-tooltip='{tt}'>{slot_name}: {item.name}</span>")
        for idx, ring_id in enumerate(self.player.equipment.rings):
            if ring_id in self.items:
                item = self.items[ring_id]
                tt = f"슬롯: 반지{idx+1}\n" + item.tooltip_text
                eq_tags.append(f"<span class='qt-hover-tag' data-tooltip='{tt}'>반지{idx+1}: {item.name}</span>")
        for idx, ear_id in enumerate(self.player.equipment.earrings):
            if ear_id in self.items:
                item = self.items[ear_id]
                tt = f"슬롯: 귀걸이{idx+1}\n" + item.tooltip_text
                eq_tags.append(f"<span class='qt-hover-tag' data-tooltip='{tt}'>귀걸이{idx+1}: {item.name}</span>")
        for idx, br_id in enumerate(getattr(self.player.equipment, "bracelets", [])):
            if br_id in self.items:
                item = self.items[br_id]
                tt = f"슬롯: 팔찌{idx+1}\n" + item.tooltip_text
                eq_tags.append(f"<span class='qt-hover-tag' data-tooltip='{tt}'>팔찌{idx+1}: {item.name}</span>")


        if not eq_tags:
            eq_tags.append("<span class='qt-hover-tag' data-tooltip='[맨손]&#10;무기를 쥐지 않은 맨주먹 상태입니다. 공격력은 미미하지만 두 손이 자유롭습니다.'>무기: 맨손</span>")
            eq_tags.append("<span class='qt-hover-tag' data-tooltip='[평복]&#10;거친 천으로 기운 평범한 옷입니다. 방어 효과는 없지만 가볍습니다.'>상의: 평복</span>")

        eq_html = ", ".join(eq_tags)

        passives = sum(1 for s in self.player.skills if s in self.skills_db and self.skills_db[s].skill_type == 'passive')
        actives = sum(1 for s in self.player.skills if s in self.skills_db and self.skills_db[s].skill_type == 'active')
        uniques = sum(1 for s in self.player.skills if s in self.skills_db and self.skills_db[s].skill_type == 'unique')

        title_html = ""
        if self.player.active_title and self.player.active_title in self.titles_db:
            t = self.titles_db[self.player.active_title]
            b_str = ", ".join(f"{k}+{v}" for k, v in t.stat_bonuses.items())
            tt = f"[{t.name}]&#10;{t.description}&#10;효과: {b_str}"
            title_html = f" | 👑 <b class='qt-hud-label'>칭호:</b> <span class='qt-hover-tag' data-tooltip='{tt}'>{t.name}</span>"

        dice_block = ""
        if self.last_dice_result:
            dice_block = f"<div class='qt-dice-log'>🎲 <b class='qt-hud-label'>최근 판정:</b> {self.last_dice_result.get('summary_ko', '')}</div>"

        npc_block = ""
        if self.last_npc_action:
            npc_block = f"<div class='qt-npc-log'>👥 <b class='qt-hud-label'>주변 인물 행동:</b> {self.last_npc_action.get('summary_ko', '')}</div>"

        return f"""
<div class="qt-hud-card">
  <div class="qt-hud-header">⚔️ <b class='qt-hud-label'>[턴 {self.turn}] {self.world_name}</b></div>
  <div class="qt-hud-loc">📍 <b class='qt-hud-label'>현재 위치:</b> {loc.name}</div>
  <div class="qt-hud-desc">{loc.description}</div>
  <div class="qt-hud-line">🚪 <b class='qt-hud-label'>출구:</b> {exits_html}</div>
  <div class="qt-hud-line">📍 <b class='qt-hud-label'>주변 바닥에 놓인 물건:</b> {items_html}</div>
  <div class="qt-hud-line">👤 <b class='qt-hud-label'>주변 인물:</b> {npcs_html}</div>

  <div class="qt-hud-divider"></div>
  <div class="qt-hud-section">✦ 캐릭터 상태 ✦</div>
  <div class="qt-hud-line">
    ❤️ <b class='qt-hud-label'>체력:</b> {self.player.health}/{self.player.max_health} &nbsp;|&nbsp;
    💧 <b class='qt-hud-label'>마나:</b> {self.player.mana}/{self.player.max_mana_effective} &nbsp;|&nbsp;
    🏆 <b class='qt-hud-label'>레벨:</b> {self.player.level} (EXP: {self.player.exp}/100)
  </div>
  <div class="qt-hud-line">
    💪 <b class='qt-hud-label'>스탯:</b> 
    <span class="qt-hover-tag" data-tooltip="[근력 (STR)]&#10;물리 공격력 계수 및 무기 휘두르기 위력에 직접적인 영향을 줍니다.">근력(STR) {self.player.strength}</span> |
    <span class="qt-hover-tag" data-tooltip="[민첩 (AGI)]&#10;회피율, 공격 선제권 및 민첩 계열 무기 위력에 영향을 줍니다.">민첩(AGI) {self.player.agility}</span> |
    <span class="qt-hover-tag" data-tooltip="[지능 (INT)]&#10;마법 공격력 및 최대 마나량(+5/포인트)에 영향을 줍니다.">지능(INT) {self.player.intelligence}</span> |
    <span class="qt-hover-tag" data-tooltip="[체력 (CON)]&#10;최대 체력(HP +10/포인트) 및 상태이상 저항력에 영향을 줍니다.">체력(CON) {self.player.constitution}</span> |
    <span class="qt-hover-tag" data-tooltip="[지혜 (WIS)]&#10;마나 재생 속도 및 턴당 마법 영창 가능 글자수(+1자/포인트)를 늘려줍니다.">지혜(WIS) {self.player.wisdom}</span> |
    <span class="qt-hover-tag" data-tooltip="[행운 (LUK)]&#10;치명타 확률(+0.5%/포인트) 및 적 처치 시 고유 스킬/희귀템 획득률을 높입니다.">행운(LUK) {self.player.luck}</span>
  </div>
  <div class="qt-hud-line">
    💥 <span class="qt-hover-tag" data-tooltip="[치명타율]&#10;공격 시 치명타가 발동할 확률입니다. (기본 5% + 행운 보정치)">치명타율: {self.player.effective_crit_rate:.1f}%</span> &nbsp;|&nbsp;
    🩸 <span class="qt-hover-tag" data-tooltip="[치명타 피해]&#10;치명타 적중 시 가해지는 추가 피해 배율입니다.">치명타 피해: {self.player.effective_crit_damage:.1f}%</span> &nbsp;|&nbsp;
    🫁 <span class="qt-hover-tag" data-tooltip="[신체 컨디션 및 피로도]&#10;격렬한 전투, 장거리 이동, 무리한 영창 시 누적되며&#10;휴식과 야영으로 회복됩니다.&#10;상태: {self.player.fatigue_status_ko}">컨디션: {self.player.fatigue_status_ko.split(' ')[0]}</span>
  </div>
  <div class="qt-hud-line">🔮 <b class='qt-hud-label'>상태이상:</b> {self._get_player_status_html()}</div>

  <div class="qt-hud-line">🗡️ <b class='qt-hud-label'>장착 장비:</b> {eq_html}</div>
  <div class="qt-hud-line">💰 <b class='qt-hud-label'>소지금:</b> {self.player.gold} 골드{title_html}</div>
  <div class="qt-hud-line">✨ <b class='qt-hud-label'>스킬:</b> 패시브 {passives}개, 액티브 {actives}개, 고유 {uniques}개</div>
  {dice_block}
  {npc_block}
</div>
"""

    def _get_player_status_html(self) -> str:
        from src.world.status_engine import StatusEffectEngine
        return StatusEffectEngine.format_status_for_html(self.player)

    def to_quest_journal_html(self) -> str:
        from src.world.quest_engine import QuestEngine
        return QuestEngine.format_journal_html(self)

    def to_shop_html(self, shop_id: str | None = None) -> str:
        from src.world.economy_engine import EconomyEngine
        return EconomyEngine.format_shop_html(self, shop_id=shop_id)

    def to_crafting_html(self) -> str:
        from src.world.crafting_engine import CraftingEngine
        return CraftingEngine.format_crafting_html(self)

    def to_party_html(self) -> str:
        from src.world.party_engine import PartyEngine
        return PartyEngine.format_party_html(self)

    def to_audio_html(self, fact_sheet=None, action="") -> str:
        from src.world.audio_engine import AudioEngine
        audio_data = AudioEngine.determine_turn_audio(self, fact_sheet=fact_sheet, action=action)
        return AudioEngine.format_audio_html(audio_data)

    def to_map_html(self, zoom_level: str = "macro_continent") -> str:
        from src.world.map_interactive_renderer import MapInteractiveRenderer
        return MapInteractiveRenderer.render_map_html(self)


    def to_skills_html(self) -> str:
        """HTML skill book with full details, incantations, and hover tooltips."""
        if not self.player.skills:
            return "<div class='qt-panel-content'>보유한 스킬이 없습니다.<br><small style='color:var(--ink-muted);'>서적을 탐독하거나 스승 NPC의 가르침을 받아 스킬을 습득하세요.</small></div>"

        html_blocks = ["<div class='qt-skill-book'>"]

        # Magic vocabulary info with folding toggle
        from src.core.config import BASE_INCANTATION_CHARS, WISDOM_INCANT_BONUS
        from src.world.incantation import IncantationSystem
        char_limit = BASE_INCANTATION_CHARS + max(0, self.player.wisdom - 10) * WISDOM_INCANT_BONUS
        words = self.player.known_magic_words
        classified = IncantationSystem.classify_magic_words(words)
        words_count = len(words)

        cat_labels = [
            ("modifiers", "⚡ 수식어 (Scale)", "qt-tag-mod", "#fde047", "rgba(234,179,8,0.25)", "#eab308"),
            ("elements", "🔥 1구 원소 (Element)", "qt-tag-elem", "#f87171", "rgba(239,68,68,0.25)", "#ef4444"),
            ("forms", "🏹 2구 형태 (Form)", "qt-tag-form", "#38bdf8", "rgba(14,165,233,0.25)", "#0ea5e9"),
            ("vectors", "💫 3구 기동 (Vector)", "qt-tag-vec", "#c084fc", "rgba(168,85,247,0.25)", "#a855f7"),
            ("triggers", "🎯 결속 (Trigger)", "qt-tag-trig", "#34d399", "rgba(16,185,129,0.25)", "#10b981"),
            ("pacts", "🩸 대가/신격 (Pact)", "qt-tag-pact", "#fb7185", "rgba(244,63,94,0.25)", "#f43f5e"),
            ("custom", "📜 기타 고대어", "qt-tag-custom", "#ffffff", "rgba(30,41,59,0.9)", "#38bdf8"),
        ]

        cat_htmls = []
        for cat_key, label, tag_cls, text_col, bg_col, border_col in cat_labels:
            items = classified.get(cat_key, [])
            if items:
                tags = " ".join(
                    f"<span class='qt-magic-word {tag_cls}' style='color:{text_col} !important; background:{bg_col} !important; border:1.5px solid {border_col} !important; font-size:13px !important; font-weight:bold !important; padding:3px 8px !important; border-radius:4px !important; display:inline-flex !important; align-items:center !important; margin:2px !important;'>"
                    f"<span style='color:{text_col} !important; font-size:13px !important; font-weight:bold !important;'>{it['word']}</span>"
                    f"<span class='qt-magic-role' style='color:#fde047 !important; font-size:12px !important; margin-left:4px !important; font-weight:normal !important;'>({it.get('role', '')})</span>"
                    f"</span>"
                    for it in items
                )
                cat_htmls.append(
                    f"<div class='qt-vocab-row' style='margin-bottom:6px !important; display:flex !important; flex-wrap:wrap !important; align-items:center !important; gap:4px !important;'>"
                    f"<span class='qt-vocab-cat' style='color:#fbbf24 !important; font-size:13px !important; font-weight:bold !important; min-width:110px !important;'>{label}:</span> {tags}"
                    f"</div>"
                )

        vocab_content = "".join(cat_htmls) if cat_htmls else "<div class='qt-vocab-empty' style='color:#ffffff !important; font-size:13px !important;'>습득한 고대어가 없습니다. (도서관 서적 탐독이나 스승 NPC의 가르침으로 습득)</div>"

        html_blocks.append(f"""
        <details class="qt-magic-toggle" open style="background:rgba(15,23,42,0.9) !important; border:1.5px solid #2dd4bf !important; border-radius:6px !important; margin-bottom:8px !important; padding:0 !important;">
          <summary class="qt-magic-summary" style="display:block !important; padding:8px 10px !important; cursor:pointer !important; background:rgba(30,41,59,0.8) !important; user-select:none !important; border-radius:5px 5px 0 0 !important;">
            <div style="display:flex !important; justify-content:space-between !important; align-items:center !important; width:100% !important; margin-bottom:4px !important;">
              <span style="color:#ffffff !important; font-size:14px !important; font-weight:bold !important;">📖 습득한 고대어 사전</span>
              <span style="color:#fde047 !important; font-size:13px !important; font-weight:bold !important;">({words_count}개 체득)</span>
            </div>
            <div style="display:flex !important; justify-content:space-between !important; align-items:center !important; width:100% !important; border-top:1px solid rgba(45,212,191,0.25) !important; padding-top:4px !important;">
              <span style="color:#ffffff !important; font-size:13px !important; font-weight:bold !important;">🗣️ 1턴 영창 한계:</span>
              <span style="color:#2dd4bf !important; font-size:16px !important; font-weight:800 !important; text-shadow:0 0 8px rgba(45,212,191,0.4) !important;">{char_limit}자</span>
            </div>
          </summary>
          <div class="qt-magic-body" style="padding:10px !important; background:rgba(10,15,29,0.7) !important; font-size:13px !important;">
            {vocab_content}
            <div class="qt-magic-tip" style="margin-top:8px !important; padding-top:6px !important; border-top:1px dashed rgba(255,255,255,0.2) !important; color:#ffffff !important; font-size:13px !important; font-weight:bold !important; display:flex !important; align-items:center !important; flex-wrap:wrap !important; gap:4px !important;">
              <span style="color:#ffffff !important;">💡 <b>영창 조합:</b></span> <span style="color:#2dd4bf !important; background:rgba(45,212,191,0.2) !important; border:1px solid #2dd4bf !important; padding:2px 6px !important; font-size:13px !important; border-radius:4px !important; font-weight:bold !important;">[원소] + [형태] + [기동]</span>
            </div>
          </div>
        </details>
        """)


        for sid in self.player.skills:
            skill = self.skills_db.get(sid)
            if not skill:
                continue

            type_badge = {
                'active': '<span class="qt-badge-active">액티브</span>',
                'passive': '<span class="qt-badge-passive">패시브</span>',
                'unique': '<span class="qt-badge-unique">★ 고유</span>',
            }.get(skill.skill_type, f'<span class="qt-badge-active">{skill.skill_type}</span>')

            cost_str = f"마나 소모: {skill.mana_cost}" if skill.skill_type == 'active' else "상시 적용"
            verse_html = f"<div class='qt-incant-verse'>📜 영창문: <i>\"{skill.incantation_verse or skill.incantation}\"</i></div>" if (skill.incantation or skill.incantation_verse) else ""
            words_html = f"<div class='qt-skill-words'>고대어 조합: <b>{', '.join(skill.ancient_words)}</b></div>" if skill.ancient_words else ""

            # Korean labels for skill type, element, scaling stat
            type_ko = {'active': '액티브', 'passive': '패시브', 'unique': '고유', 'magic': '마법'}.get(skill.skill_type, skill.skill_type)
            elem_ko = {
                'fire': '화염', 'water': '수류', 'ice': '빙결', 'lightning': '번개',
                'wind': '바람', 'earth': '대지', 'dark': '암흑', 'light': '빛',
                'poison': '독', 'none': '무속성', 'neutral': '무속성', '': '무속성',
                'holy': '신성', 'shadow': '그림자', 'arcane': '비전', 'nature': '자연',
            }.get((skill.element or '').lower(), skill.element or '무속성')
            stat_ko = {
                'str': '근력', 'strength': '근력', 'agi': '민첩', 'agility': '민첩',
                'int': '지능', 'intelligence': '지능', 'con': '체력', 'constitution': '체력',
                'wis': '지혜', 'wisdom': '지혜', 'luk': '행운', 'luck': '행운',
            }.get((skill.scaling_stat or '').lower(), skill.scaling_stat or 'STR')

            tt = f"[{skill.name}]&#10;유형: {type_ko} ({cost_str})&#10;속성: {elem_ko}&#10;위력 계수: {stat_ko.upper()} × {skill.scaling_factor}&#10;판정 방식: {stat_ko.upper()} 기반 판정"


            card_color = getattr(skill, "color", "#94a3b8") or "#94a3b8"
            html_blocks.append(f"""
            <div class="qt-skill-card" style="border-left: 3.5px solid {card_color} !important;">
              <div class="qt-skill-header">
                <span class="qt-hover-tag" data-tooltip="{tt}"><b style="color:{card_color} !important;">{skill.name}</b></span>
                {type_badge}
                <span class="qt-skill-cost">{cost_str}</span>
              </div>
              <div class="qt-skill-desc">{skill.description}</div>
              {words_html}
              {verse_html}
            </div>
            """)

        html_blocks.append("</div>")
        return "".join(html_blocks)


    def to_inventory_html(self) -> str:
        """HTML inventory list showing all items and equipped states with hover cards."""
        player_items = self.player_inventory_items()
        if not player_items:
            return "<div class='qt-panel-content'>가방이 텅 비어 있습니다.</div>"

        equipped = vars(self.player.equipment)
        equipped_ids = set()
        for k, v in equipped.items():
            if isinstance(v, list):
                equipped_ids.update(v)
            elif v:
                equipped_ids.add(v)

        html_blocks = ["<div class='qt-inv-grid'>"]
        for item in player_items:
            is_eq = item.id in equipped_ids
            eq_badge = "<span class='qt-eq-badge'>[장착중]</span>" if is_eq else ""

            stats_info = []
            if item.damage > 0: stats_info.append(f"공격력 +{item.damage}")
            if item.defense > 0: stats_info.append(f"방어력 +{item.defense}")
            if item.weight > 0: stats_info.append(f"무게 {item.weight}kg")
            if item.properties.get("granted_skill"):
                sk = item.properties.get("granted_skill")
                sk_name = sk.get("name", sk) if isinstance(sk, dict) else sk
                stats_info.append(f"스킬 [{sk_name}]")
            stats_str = f"<div class='qt-item-stats'>{', '.join(stats_info)}</div>" if stats_info else ""


            tt = item.tooltip_text


            html_blocks.append(f"""
            <div class="qt-item-card {'qt-item-equipped' if is_eq else ''}">
              <div class="qt-item-header">
                <span class="qt-hover-tag" data-tooltip="{tt}"><b>{item.name}</b></span>
                {eq_badge}
                <span class="qt-item-val">{item.value}G</span>
              </div>
              <div class="qt-item-desc">{item.description}</div>
              {stats_str}
            </div>
            """)

        html_blocks.append("</div>")
        return "".join(html_blocks)


    def to_map_summary(self) -> str:
        """Map of visited locations only."""
        lines = ["KNOWN MAP (locations the player has visited):"]
        for loc_id, loc in self.locations.items():
            if not loc.visited:
                continue
            exits = ", ".join(
                f"{direction} → {self.locations[lid].name}"
                for direction, lid in loc.exits.items()
                if lid in self.locations
            ) or "no exits"
            lines.append(f"  {loc.name}: {exits}")

    def register_dynamic_npc(self, data: dict) -> NPC:
        """Dynamically registers a newly encountered NPC on-demand and ensures persistence."""
        npc_id = data.get("id") or f"npc_{len(self.npcs) + 1}_{data.get('name', 'unknown')}"
        if npc_id in self.npcs:
            return self.npcs[npc_id]

        p_data = data.get("personality", {})
        personality = NPCPersonality(
            altruism=p_data.get("altruism", 50),
            greed=p_data.get("greed", 50),
            courage=p_data.get("courage", 50),
            suspicion=p_data.get("suspicion", 50),
            loyalty=p_data.get("loyalty", 50),
            aggression=p_data.get("aggression", 50)
        )
        needs = NPCNeeds(**data.get("needs", {})) if "needs" in data and isinstance(data.get("needs"), dict) else NPCNeeds()
        eq_raw = data.get("equipment", {}) if isinstance(data.get("equipment"), dict) else {}
        eq_fields = {f.name for f in fields(EquipmentSlots)}
        equipment = EquipmentSlots(**{k: v for k, v in eq_raw.items() if k in eq_fields})

        v_data = data.get("visual", {})
        if isinstance(v_data, dict):
            valid_v = {f.name for f in fields(NPCVisualDetails)}
            visual = NPCVisualDetails(**{k: v for k, v in v_data.items() if k in valid_v})
            if isinstance(getattr(visual, "face_details", None), dict):
                valid_f = {f.name for f in fields(FacialDetails)}
                visual.face_details = FacialDetails(**{k: v for k, v in visual.face_details.items() if k in valid_f})
            if isinstance(getattr(visual, "body_measurements", None), dict):
                valid_b = {f.name for f in fields(BodyMeasurements)}
                visual.body_measurements = BodyMeasurements(**{k: v for k, v in visual.body_measurements.items() if k in valid_b})
            if isinstance(getattr(visual, "outfit", None), dict):
                valid_o = {f.name for f in fields(ClothingLayer)}
                visual.outfit = ClothingLayer(**{k: v for k, v in visual.outfit.items() if k in valid_o})
        elif isinstance(v_data, NPCVisualDetails):
            visual = v_data
        else:
            visual = NPCVisualDetails()

        npc = NPC(
            id=npc_id,
            name=data.get("name", "이름 모를 인물"),
            description=data.get("description", "평범한 옷차림의 인물이다."),
            location=data.get("location", self.player.location),
            tier=data.get("tier", "commoner"),
            influence_scope=data.get("influence_scope", "local"),
            job=data.get("job", "주민"),
            disposition=data.get("disposition", "neutral"),
            alive=data.get("alive", True),
            level=data.get("level", 1),
            health=data.get("health", 50),
            max_health=data.get("max_health", 50),
            mana=data.get("mana", 30),
            max_mana=data.get("max_mana", 30),
            armor_class=data.get("armor_class", 10),
            gold=data.get("gold", 10),
            inventory=data.get("inventory", []),
            equipment=equipment,
            visual=visual,
            strength=data.get("strength", 10),
            agility=data.get("agility", 10),
            intelligence=data.get("intelligence", 10),
            constitution=data.get("constitution", 10),
            wisdom=data.get("wisdom", 10),
            luck=data.get("luck", 10),
            perception=data.get("perception", 10),
            personality=personality,
            needs=needs,
            goal=data.get("goal", ""),
            skills=data.get("skills", []),
            titles=data.get("titles", []),
            attitude_description=data.get("attitude_description", ""),
            interests=data.get("interests", []),
            current_activity=data.get("current_activity", ""),
            desire=data.get("desire", ""),
            weakness=data.get("weakness", ""),
            appearance_story=data.get("appearance_story", ""),
            bonds=data.get("bonds", {}),
            trauma=data.get("trauma", ""),
            quirk=data.get("quirk", ""),
            taboo=data.get("taboo", ""),
            tastes=data.get("tastes", {"likes": [], "dislikes": []}),
            physical_condition=data.get("physical_condition", ""),
            speech_style=data.get("speech_style", ""),
            daily_routine=data.get("daily_routine", ""),
            superstitions=data.get("superstitions", ""),
            self_image_vs_reputation=data.get("self_image_vs_reputation", ""),
            hidden_side=data.get("hidden_side", ""),
            education_level=data.get("education_level", ""),
            financial_state=data.get("financial_state", ""),
            anatomy_parts=data.get("anatomy_parts", {}),
            harvested_parts=data.get("harvested_parts", [])
        )
        self.npcs[npc_id] = npc
        loc_id = npc.location
        if loc_id in self.locations and npc_id not in self.locations[loc_id].npcs:
            self.locations[loc_id].npcs.append(npc_id)
        return npc


    def register_dynamic_location(self, data: dict) -> Location:
        """Dynamically registers a newly discovered location/room on-demand."""
        loc_id = data.get("id") or f"loc_{len(self.locations) + 1}"
        if loc_id in self.locations:
            return self.locations[loc_id]

        loc = Location(
            id=loc_id,
            name=data.get("name", "미지의 구역"),
            description=data.get("description", "처음 발을 들인 장소다."),
            exits=data.get("exits", {}),
            items=data.get("items", []),
            npcs=data.get("npcs", []),
            visited=data.get("visited", False)
        )
        self.locations[loc_id] = loc
        return loc

    def register_dynamic_item(self, data: dict) -> Item:
        """Dynamically registers a newly discovered item or environment object on-demand."""
        item_id = data.get("id") or f"item_{len(self.items) + 1}"
        if item_id in self.items:
            return self.items[item_id]

        item = Item(
            id=item_id,
            name=data.get("name", "이름 없는 물건"),
            description=data.get("description", "특별할 것 없는 평범한 물건이다."),
            location=data.get("location", self.player.location),
            item_type=data.get("item_type", "misc"),
            damage=data.get("damage", 0),
            defense=data.get("defense", 0),
            value=data.get("value", 0),
            scaling_stat=data.get("scaling_stat", "str"),
            scaling_factor=data.get("scaling_factor", 1.0),
            properties=data.get("properties", {}),
            weight=data.get("weight", 1.0),
            size=data.get("size", "small"),
            required_strength=data.get("required_strength", 10),
            can_store_in_bag=data.get("can_store_in_bag", True),
            can_wield_as_weapon=data.get("can_wield_as_weapon", True),
            improvised_damage=data.get("improvised_damage", 2),
            document_text=data.get("document_text", "")
        )
        self.items[item_id] = item
        if item.location in self.locations and item_id not in self.locations[item.location].items:
            self.locations[item.location].items.append(item_id)
        return item

    def update_environment_state(self, location_id: str, element_key: str, state_value: str) -> None:
        """Updates persistent physical changes to location (broken door, bloodstains, burnt tables)."""
        if location_id not in self.environment_states:
            self.environment_states[location_id] = {}
        self.environment_states[location_id][element_key] = state_value

    def record_clue(self, clue_id: str, description: str) -> None:
        """Records a permanent discovery, secret, or plot clue."""
        self.discovered_clues[clue_id] = description

    def apply_faction_ripple(self, target_faction_id: str, delta: int, reason: str = "") -> list[str]:
        """
        Calculates and propagates ripple effects across factions based on relations.
        e.g., Attacking bandits (+rep with guards, -rep with smugglers -> raises black market prices).
        """
        logs = []
        if target_faction_id not in self.factions:
            return logs

        target_fac = self.factions[target_faction_id]
        logs.append(f"[{target_fac.name}] 평판 {delta:+d} 변화 ({reason})")

        # Propagate ripple to related factions
        for rel_fac_id, rel_type in target_fac.relations.items():
            if rel_fac_id in self.factions:
                rel_fac = self.factions[rel_fac_id]
                if rel_type == "적대":
                    # Opposing faction reacts conversely
                    opp_delta = -int(delta * 0.7)
                    if opp_delta != 0:
                        logs.append(f"🌊 [파벌 나비효과] 적대 관계인 [{rel_fac.name}]의 우호도 {opp_delta:+d} 반작용")
                elif rel_type == "동맹":
                    # Allied faction reacts similarly
                    ally_delta = int(delta * 0.8)
                    if ally_delta != 0:
                        logs.append(f"🌊 [파벌 나비효과] 동맹 관계인 [{rel_fac.name}]의 우호도 {ally_delta:+d} 연쇄 반영")

        return logs

    def apply_update(self, update: dict) -> list[str]:
        """
        Applies a validated delta update to the WorldState.
        Enforces balance thresholds, stat caps, and reveals NPC stats when requested.
        Orchestrates domain-specific handlers for modular state mutations.
        """
        changes: list[str] = []
        if not update or not isinstance(update, dict):
            return changes

        self._apply_player_updates(update, changes)
        self._apply_inventory_and_equipment_updates(update, changes)
        self._apply_npc_updates(update, changes)
        self._apply_world_environment_updates(update, changes)
        self._apply_subsystem_engine_deltas(update, changes)

        return changes

    def _apply_player_updates(self, update: dict, changes: list[str]) -> None:
        """Applies player stats, movement, injuries, status effects, and attributes."""
        if "move_player" in update:
            dest = update["move_player"]
            directions = dest if isinstance(dest, list) else [dest]

            for direction in directions:
                loc = self.current_location()
                if loc and direction in loc.exits and loc.exits[direction] in self.locations:
                    new_loc_id = loc.exits[direction]
                    self.player.location = new_loc_id
                    self.locations[new_loc_id].visited = True
                    changes.append(f"Player moved to {self.locations[new_loc_id].name}")
                elif direction in self.locations:
                    self.player.location = direction
                    self.locations[direction].visited = True
                    changes.append(f"Player moved to {self.locations[direction].name}")
                else:
                    changes.append(f"REJECTED move to {direction} — not a valid exit")
                    break
        if "player" in update and isinstance(update["player"], dict):
            p_dict = update["player"]
            if "location" in p_dict:
                new_loc_id = p_dict["location"]
                if new_loc_id in self.locations:
                    self.player.location = new_loc_id
                    self.locations[new_loc_id].visited = True
                    changes.append(f"Player moved to {self.locations[new_loc_id].name}")
            if "gold" in p_dict:
                self.player.gold = int(p_dict["gold"])
                changes.append(f"Player gold updated: {self.player.gold}")
            if "inventory" in p_dict and isinstance(p_dict["inventory"], list):
                self.player.inventory = list(p_dict["inventory"])
                changes.append(f"Player inventory updated: {len(self.player.inventory)} items")
            if "health" in p_dict:
                self.player.health = max(0, min(self.player.max_health, int(p_dict["health"])))
                changes.append(f"Player health updated: {self.player.health}")
            if "mana" in p_dict:
                self.player.mana = max(0, min(self.player.max_mana, int(p_dict["mana"])))
                changes.append(f"Player mana updated: {self.player.mana}")
            if "mana_burn_state" in p_dict and isinstance(p_dict["mana_burn_state"], dict):
                self.player.mana_burn_state = dict(p_dict["mana_burn_state"])
                changes.append("Player mana circuit state updated")
            if "alcohol_state" in p_dict and isinstance(p_dict["alcohol_state"], dict):
                self.player.alcohol_state = dict(p_dict["alcohol_state"])
                changes.append("Player alcohol state updated")

        if "player_stealthed" in update:
            self.player.is_stealthed = bool(update["player_stealthed"])
            changes.append(f"Player stealth state: {self.player.is_stealthed}")

        if "mana_burn_state" in update and isinstance(update["mana_burn_state"], dict):
            self.player.mana_burn_state = dict(update["mana_burn_state"])
            changes.append("Player mana circuit state updated")

        if "alcohol_state" in update and isinstance(update["alcohol_state"], dict):
            self.player.alcohol_state = dict(update["alcohol_state"])
            changes.append("Player alcohol state updated")

        # 1.5 Pending travel waypoints update
        if "pending_travel_waypoints" in update and isinstance(update["pending_travel_waypoints"], list):
            self.pending_travel_waypoints = list(update["pending_travel_waypoints"])
            changes.append(f"Pending travel waypoints updated: {self.pending_travel_waypoints}")

        # 1.6 Power scale preset update & Stat allocation
        if "power_scale_preset_id" in update and isinstance(update["power_scale_preset_id"], str):
            self.power_scale_preset_id = update["power_scale_preset_id"]
            changes.append(f"Power scale preset updated to: {self.power_scale_preset_id}")

        if "allocate_stat" in update and isinstance(update["allocate_stat"], dict):
            s_name = update["allocate_stat"].get("stat_name", "")
            amt = int(update["allocate_stat"].get("amount", 1))
            preset = self.get_power_scale_preset()
            success = self.player.allocate_stat(s_name, amt, stat_cap=preset.stat_cap)
            if success:
                changes.append(f"Player allocated {amt} points to {s_name} (cap: {preset.stat_cap})")
            else:
                changes.append(f"REJECTED stat allocation to {s_name} — insufficient points or cap reached ({preset.stat_cap})")

        # 2. Item pickup
        if "player_health" in update:
            delta = update["player_health"]
            self.player.health = max(0, min(self.player.max_health, self.player.health + delta))
            changes.append(f"Player health changed by {delta} (Now: {self.player.health}/{self.player.max_health})")

        # 9. Gold and EXP (with Stat Cap check)
        if "add_gold" in update:
            self.player.gold = max(0, self.player.gold + update["add_gold"])
            changes.append(f"Gold changed: {self.player.gold}")

        if "add_exp" in update:
            self.player.exp += update["add_exp"]
            while self.player.exp >= 100:
                self.player.exp -= 100
                self.player.level += 1
                self.player.max_health += 10
                self.player.health = self.player.max_health
                
                # Gain 1 to 2 stat points, clamped to MAX_STAT_VALUE
                stat_gain = min(MAX_LEVELUP_STAT_GAIN, 1)
                self.player.strength = min(MAX_STAT_VALUE, self.player.strength + stat_gain)
                self.player.constitution = min(MAX_STAT_VALUE, self.player.constitution + stat_gain)
                
                self.player.stat_points += 2
                changes.append(f"LEVEL UP! Player is now Level {self.player.level}")

        # 10. Reputation delta (Clamped between MIN_REPUTATION_DELTA and MAX_REPUTATION_DELTA)
        if "reputation_delta" in update:
            raw_delta = update["reputation_delta"]
            clamped_delta = max(MIN_REPUTATION_DELTA, min(MAX_REPUTATION_DELTA, raw_delta))
            self.player.reputation = max(
                MIN_REPUTATION_TOTAL,
                min(MAX_REPUTATION_TOTAL, self.player.reputation + clamped_delta)
            )
            changes.append(f"Player reputation changed by {clamped_delta} to {self.player.reputation}")

        # 11. World fact learned
        if "grant_skill" in update:
            for target_id, skill_id in update["grant_skill"].items():
                if target_id == "player":
                    if skill_id not in self.player.skills:
                        self.player.skills.append(skill_id)
                        changes.append(f"Player acquired skill: {skill_id}")
                elif target_id in self.npcs:
                    if skill_id not in self.npcs[target_id].skills:
                        self.npcs[target_id].skills.append(skill_id)
                        changes.append(f"NPC {self.npcs[target_id].name} acquired skill: {skill_id}")
                        
        # Grant title
        if "grant_title" in update:
            for target_id, title_id in update["grant_title"].items():
                if target_id == "player":
                    if title_id not in self.player.titles:
                        self.player.titles.append(title_id)
                        changes.append(f"Player acquired title: {title_id}")
                elif target_id in self.npcs:
                    if title_id not in self.npcs[target_id].titles:
                        self.npcs[target_id].titles.append(title_id)
                        changes.append(f"NPC {self.npcs[target_id].name} acquired title: {title_id}")
                        
        # Add magic word
        if "add_magic_word" in update:
            word = update["add_magic_word"]
            if word not in self.player.known_magic_words:
                self.player.known_magic_words.append(word)
                changes.append(f"Player learned magic word: {word}")

        # Fatigue updates
        if "fatigue_delta" in update:
            delta = int(update["fatigue_delta"])
            self.player.fatigue = max(0, min(100, self.player.fatigue + delta))
            changes.append(f"Player fatigue updated: {self.player.fatigue}/100")
            if delta < 0:
                from src.world.injury_engine import InjuryEngine
                r_logs = InjuryEngine.progress_rest_healing(self, self.player, rest_turns=1)
                changes.extend(r_logs)

        # Time advanced updates
        if "time_minutes" in update:
            mins = int(update["time_minutes"])
            self.player.time_elapsed_minutes += mins
            changes.append(f"Time advanced by {mins} minutes (Total: {self.player.time_elapsed_minutes}m)")

        # 12. Dynamic Entity Registration & Persistence (Zero Evaporation)
        if "add_player_injury" in update:
            inj = update["add_player_injury"]
            if inj and inj not in self.player.injuries:
                self.player.injuries.append(inj)
                changes.append(f"플레이어 신체 부상: {inj}")

        if "add_player_trauma" in update:
            tra = update["add_player_trauma"]
            if tra and tra not in self.player.traumas:
                self.player.traumas.append(tra)
                changes.append(f"플레이어 트라우마 획득: {tra}")

        if "remove_player_injury" in update:
            rem_inj = str(update["remove_player_injury"]).strip()
            to_remove = [inj for inj in self.player.injuries if rem_inj in inj or inj in rem_inj]
            for inj in to_remove:
                self.player.injuries.remove(inj)
                if inj in self.player.splinted_injuries:
                    del self.player.splinted_injuries[inj]
                changes.append(f"플레이어 신체 부상 완치: {inj}")

        if "splint_player_injury" in update:
            s_data = update["splint_player_injury"]
            inj_name = s_data.get("injury_name")
            turns = s_data.get("turns_needed", 2)
            if inj_name:
                self.player.splinted_injuries[inj_name] = turns
                changes.append(f"플레이어 부목 고정: {inj_name} (완치까지 휴식 {turns}회 필요)")

        if "progress_rest_healing" in update:
            from src.world.injury_engine import InjuryEngine
            rest_turns = int(update["progress_rest_healing"])
            r_logs = InjuryEngine.progress_rest_healing(self, self.player, rest_turns=rest_turns)
            changes.extend(r_logs)

        # 17. Status Effects (Status Effect Engine)
        if "apply_status" in update:
            from src.world.status_engine import StatusEffectEngine
            status_data = update["apply_status"]
            if isinstance(status_data, dict):
                for target_key, s_info in status_data.items():
                    target = self.player if target_key == "player" else self.npcs.get(target_key)
                    if target:
                        if isinstance(s_info, str):
                            msg = StatusEffectEngine.apply_status(target, s_info)
                        elif isinstance(s_info, dict):
                            msg = StatusEffectEngine.apply_status(
                                target,
                                s_info.get("status_id", "poison"),
                                duration=s_info.get("duration"),
                                potency=s_info.get("potency"),
                                stacks=s_info.get("stacks", 1)
                            )
                        else:
                            msg = ""
                        if msg:
                            changes.append(msg)

        if "remove_status" in update:
            from src.world.status_engine import StatusEffectEngine
            status_data = update["remove_status"]
            if isinstance(status_data, dict):
                for target_key, s_ids in status_data.items():
                    target = self.player if target_key == "player" else self.npcs.get(target_key)
                    if target:
                        s_list = s_ids if isinstance(s_ids, list) else [s_ids]
                        for s_id in s_list:
                            if StatusEffectEngine.remove_status(target, str(s_id)):
                                changes.append(f"상태이상 해제: [{getattr(target, 'name', target_key)}] {s_id}")

        # Update Environmental Metrics
        if "update_hygiene" in update:
            self.player.hygiene_level = max(0, min(100, self.player.hygiene_level + int(update["update_hygiene"])))
            changes.append(f"🧼 플레이어 위생 상태: {self.player.hygiene_level}/100")

        if "update_body_temperature" in update:
            self.player.body_temperature = round(self.player.body_temperature + float(update["update_body_temperature"]), 1)
            changes.append(f"🌡️ 플레이어 체온: {self.player.body_temperature}°C")

        # 21. Active Campsite State

    def _apply_inventory_and_equipment_updates(self, update: dict, changes: list[str]) -> None:
        """Applies item pickup, drop, equip, unequip, and destruction."""
        if "pickup_item" in update:
            item_id = update["pickup_item"]
            loc = self.current_location()
            if loc and item_id in loc.items and item_id in self.items:
                item = self.items[item_id]
                from src.world.outfit_engine import OutfitMechanicsEngine

                # Check 1: Can this item be stored in a bag?
                can_store = getattr(item, "can_store_in_bag", True)
                item_size = getattr(item, "size", "small")
                if not can_store or item_size in ["heavy", "massive"] or item.item_type in ["furniture", "structure"]:
                    changes.append(f"REJECTED pickup {item.name} — 너무 거대하거나 구조물 형태여서 가방에 수납할 수 없음 ({item_size})")
                else:
                    # Check 2: Evaluate backpack storage limit with candidate item
                    storage_name = "여행자 배낭"
                    eq = getattr(self.player, "equipment", None)
                    if eq and getattr(eq, "storage", None):
                        s_id = eq.storage
                        if s_id in self.items:
                            storage_name = self.items[s_id].name
                    elif hasattr(self.player, "visual") and self.player.visual and self.player.visual.outfit:
                        if self.player.visual.outfit.bags_storage:
                            storage_name = self.player.visual.outfit.bags_storage[0]

                    spec = OutfitMechanicsEngine.get_backpack_spec(storage_name)

                    candidate_inv = list(self.player.inventory) + [item_id]
                    hypo_weight = sum(getattr(self.items[i], "weight", 1.0) for i in candidate_inv if i in self.items)
                    hypo_vol = sum(OutfitMechanicsEngine.estimate_item_volume_liters(self.items[i]) for i in candidate_inv if i in self.items)

                    if hypo_weight > spec.tear_weight_limit_kg:
                        changes.append(
                            f"REJECTED pickup {item.name} — 가방 적재 한계({spec.tear_weight_limit_kg}kg) 초과 "
                            f"(현재 {round(hypo_weight - getattr(item, 'weight', 1.0), 1)}kg + 아이템 {getattr(item, 'weight', 1.0)}kg)"
                        )
                    elif hypo_vol > spec.volume_liters * 1.5:
                        changes.append(
                            f"REJECTED pickup {item.name} — 가방 최대 용적({spec.volume_liters}L) 초과로 더 이상 들어가지 않음"
                        )
                    else:
                        loc.items.remove(item_id)
                        self.player.inventory.append(item_id)
                        item.location = "inventory"
                        changes.append(f"Player picked up {item.name}")

                        # Trigger storage evaluation for warning / wear status
                        storage_status = OutfitMechanicsEngine.evaluate_backpack_storage(self.player, self)
                        if storage_status.is_overweight or storage_status.is_overfilled_volume or storage_status.is_torn:
                            changes.append(f"🎒 {storage_status.narrative_summary}")
            else:
                changes.append(f"REJECTED pickup {item_id} — not in current location")

        # 3. Item drop
        if "drop_item" in update:
            item_id = update["drop_item"]
            loc = self.current_location()
            if item_id in self.player.inventory and loc:
                self.player.inventory.remove(item_id)
                loc.items.append(item_id)
                self.items[item_id].location = loc.id
                
                # Unequip if equipped
                for slot in ["weapon", "head", "face", "chest", "legs", "boots", "gloves", "cape", "neck", "belt", "shoulders", "storage", "innerwear"]:
                    if getattr(self.player.equipment, slot, None) == item_id:
                        setattr(self.player.equipment, slot, None)
                if item_id in self.player.equipment.rings:
                    self.player.equipment.rings.remove(item_id)
                if item_id in self.player.equipment.earrings:
                    self.player.equipment.earrings.remove(item_id)
                if item_id in getattr(self.player.equipment, "bracelets", []):
                    self.player.equipment.bracelets.remove(item_id)
                self.recalculate_equipment_stats(self.player)
                changes.append(f"Player dropped {self.items[item_id].name}")

        # 4. Item equip (new format)
        if "equip_slot" in update:
            item_id = update["equip_slot"].get("item_id")
            slot = update["equip_slot"].get("slot")
            if item_id in self.player.inventory and item_id in self.items:
                item = self.items[item_id]
                if slot in ["weapon", "head", "face", "chest", "legs", "boots", "gloves", "cape", "neck", "belt", "shoulders", "storage", "innerwear"]:
                    setattr(self.player.equipment, slot, item_id)
                    changes.append(f"Equipped {item.name} to {slot}")
                elif slot == "ring":
                    if len(self.player.equipment.rings) < MAX_RINGS:
                        self.player.equipment.rings.append(item_id)
                        changes.append(f"Equipped {item.name} to ring slot")
                elif slot == "earring":
                    if len(self.player.equipment.earrings) < MAX_EARRINGS:
                        self.player.equipment.earrings.append(item_id)
                        changes.append(f"Equipped {item.name} to earring slot")
                elif slot in ["bracelet", "bracelets"]:
                    if len(getattr(self.player.equipment, "bracelets", [])) < MAX_BRACELETS:
                        self.player.equipment.bracelets.append(item_id)
                        changes.append(f"Equipped {item.name} to bracelet slot")
                self.recalculate_equipment_stats(self.player)

        # 4.5 Item unequip
        if "unequip_slot" in update:
            item_id = update["unequip_slot"].get("item_id")
            slot = update["unequip_slot"].get("slot")
            if slot in ["weapon", "head", "face", "chest", "legs", "boots", "gloves", "cape", "neck", "belt", "shoulders", "storage", "innerwear"]:
                if getattr(self.player.equipment, slot, None) == item_id or not item_id:
                    setattr(self.player.equipment, slot, None)
                    changes.append(f"Unequipped from {slot}")
            elif slot == "ring":
                if item_id in self.player.equipment.rings:
                    self.player.equipment.rings.remove(item_id)
                    changes.append(f"Unequipped ring {item_id}")
                elif not item_id and self.player.equipment.rings:
                    self.player.equipment.rings.pop()
                    changes.append("Unequipped ring")
            elif slot == "earring":
                if item_id in self.player.equipment.earrings:
                    self.player.equipment.earrings.remove(item_id)
                    changes.append(f"Unequipped earring {item_id}")
                elif not item_id and self.player.equipment.earrings:
                    self.player.equipment.earrings.pop()
                    changes.append("Unequipped earring")
            elif slot in ["bracelet", "bracelets"]:
                if item_id in getattr(self.player.equipment, "bracelets", []):
                    self.player.equipment.bracelets.remove(item_id)
                    changes.append(f"Unequipped bracelet {item_id}")
                elif not item_id and getattr(self.player.equipment, "bracelets", []):
                    self.player.equipment.bracelets.pop()
                    changes.append("Unequipped bracelet")
            self.recalculate_equipment_stats(self.player)

        # 4.5 Destroyed items handling (UniversalObjectPhysicsEngine)
        if "destroyed_items" in update and isinstance(update["destroyed_items"], list):
            for d_id in update["destroyed_items"]:
                if d_id in self.items:
                    it = self.items[d_id]
                    it.is_destroyed = True
                    it.durability = 0
                    if "destroyed_object" not in it.traits:
                        it.traits.append("destroyed_object")
                    loc = self.locations.get(it.location)
                    if loc and d_id in loc.items:
                        loc.items.remove(d_id)
                    if d_id in self.player.inventory:
                        self.player.inventory.remove(d_id)
                    changes.append(f"Item {it.name} destroyed")

        # 5. NPC state updates (alive, disposition, health, stats_revealed)

    def _apply_npc_updates(self, update: dict, changes: list[str]) -> None:
        """Applies NPC state, personality, schedule, episodic memory, attitude, and BDI."""
        if "npc_state" in update:
            for npc_id, new_state in update["npc_state"].items():
                if npc_id in self.npcs:
                    npc = self.npcs[npc_id]
                    if "alive" in new_state:
                        npc.alive = new_state["alive"]
                    if "disposition" in new_state:
                        npc.disposition = new_state["disposition"]
                    if "health" in new_state:
                        npc.health = max(0, min(npc.max_health, new_state["health"]))
                        if npc.health <= 0:
                            npc.alive = False
                    if "stats_revealed" in new_state:
                        npc.stats_revealed = new_state["stats_revealed"]
                    if "injuries" in new_state and isinstance(new_state["injuries"], list):
                        npc.injuries = list(new_state["injuries"])
                    if "morale" in new_state:
                        npc.morale = max(0, min(100, new_state["morale"]))
                    changes.append(f"NPC {npc.name} state updated: {new_state}")
                    
        # Update NPC personality
        if "update_npc_personality" in update:
            for npc_id, p_deltas in update["update_npc_personality"].items():
                if npc_id in self.npcs:
                    npc = self.npcs[npc_id]
                    for trait, delta in p_deltas.items():
                        if hasattr(npc.personality, trait):
                            current = getattr(npc.personality, trait)
                            setattr(npc.personality, trait, max(0, min(100, current + delta)))
                    changes.append(f"NPC {npc.name} personality updated")

        # 6. Reveal NPC stats explicitly
        if "reveal_npc_stats" in update:
            for npc_id in update["reveal_npc_stats"]:
                if npc_id in self.npcs:
                    self.npcs[npc_id].stats_revealed = True
                    changes.append(f"NPC {self.npcs[npc_id].name} stats revealed")

        # Reveal NPC names explicitly (e.g. when player asks or introduces)
        if "reveal_npc_name" in update:
            for npc_id in update["reveal_npc_name"]:
                if npc_id in self.npcs:
                    self.npcs[npc_id].name_revealed = True
                    changes.append(f"NPC {self.npcs[npc_id].name} name revealed")

        # Update NPC current activity / situation
        if "update_npc_activity" in update:
            for npc_id, act_str in update["update_npc_activity"].items():
                if npc_id in self.npcs:
                    self.npcs[npc_id].current_activity = act_str
                    changes.append(f"NPC {self.npcs[npc_id].name} activity: {act_str}")

        # Update NPC schedule
        if "update_npc_schedule" in update:
            for npc_id, new_plans in update["update_npc_schedule"].items():
                if npc_id in self.npcs and isinstance(new_plans, list):
                    self.npcs[npc_id].schedule = new_plans
                    changes.append(f"NPC {self.npcs[npc_id].name} schedule modified")

        # Add physical traces to location
        if "npc_memory" in update:
            for npc_id, memory_data in update["npc_memory"].items():
                if npc_id in self.npcs:
                    npc = self.npcs[npc_id]
                    sig = int(memory_data.get("significance", 1))
                    sig = max(1, min(5, sig))
                    is_anchor = sig >= 4 or bool(memory_data.get("is_anchor", False))

                    entry = MemoryEntry(
                        turn=self.turn,
                        description=memory_data.get("description", ""),
                        emotional_tone=memory_data.get("emotional_tone", "neutral"),
                        significance=sig,
                        is_anchor=is_anchor,
                    )
                    npc.memories.append(entry)
                    pruned = npc.prune_memories(self.turn, decay_turns=20)
                    if pruned:
                        changes.append(f"{npc.name} forgot {len(pruned)} minor episodic memories after 20 turns of decay.")
                    changes.append(
                        f"{npc.name} remembers (Lv.{entry.significance}/5): '{entry.description}'"
                    )

        # 8. Player health delta
        if "update_npc_attitude" in update:
            att_updates = update["update_npc_attitude"]
            if isinstance(att_updates, dict):
                for npc_id, att_delta in att_updates.items():
                    if npc_id in self.npcs and isinstance(att_delta, dict):
                        npc = self.npcs[npc_id]
                        if "affinity" in att_delta:
                            npc.affinity = max(0, min(100, npc.affinity + att_delta["affinity"]))
                        if "fear" in att_delta:
                            npc.fear = max(0, min(100, npc.fear + att_delta["fear"]))
                        if "debt" in att_delta:
                            npc.debt = max(-100, min(100, npc.debt + att_delta["debt"]))
                        changes.append(f"NPC [{npc.name}] 태도 변화: 친밀도({npc.affinity}), 공포({npc.fear}), 부채({npc.debt})")

        # Add NPC Belief (BDI)
        if "add_npc_belief" in update:
            b_updates = update["add_npc_belief"]
            if isinstance(b_updates, dict):
                for npc_id, belief_text in b_updates.items():
                    if npc_id in self.npcs and belief_text:
                        self.npcs[npc_id].beliefs.append(str(belief_text))
                    changes.append(f"NPC [{self.npcs[npc_id].name}] 인지 갱신: '{belief_text}'")

        # Update NPC BDI intention/desire
        if "update_npc_bdi" in update:
            for npc_id, bdi_data in update["update_npc_bdi"].items():
                if npc_id in self.npcs and isinstance(bdi_data, dict):
                    npc = self.npcs[npc_id]
                    if "desire" in bdi_data:
                        npc.desire = bdi_data["desire"]
                    if "intention" in bdi_data:
                        npc.intention = bdi_data["intention"]

        # Player Injuries and Traumas
        if "update_npc_morale" in update:
            for nid, m_delta in update["update_npc_morale"].items():
                if nid in self.npcs:
                    self.npcs[nid].morale = max(0, min(100, self.npcs[nid].morale + int(m_delta)))
                    changes.append(f"⚔️ NPC [{self.npcs[nid].name}] 사기 갱신: {self.npcs[nid].morale}/100")

        # 20. Hygiene & Body Temperature

    def _apply_world_environment_updates(self, update: dict, changes: list[str]) -> None:
        """Applies world facts, dynamic entities, hazards, clues, environment metrics, and campsite."""
        if "add_location_trace" in update:
            trace_info = update["add_location_trace"]
            target_lid = trace_info.get("location_id", self.player.location)
            if target_lid in self.locations:
                loc_obj = self.locations[target_lid]
                loc_obj.physical_traces.append({
                    "trace": trace_info.get("trace", ""),
                    "turn": self.turn,
                    "npc_name": trace_info.get("npc_name", "미상")
                })
                loc_obj.physical_traces = [
                    t for t in loc_obj.physical_traces
                    if isinstance(t, dict) and (self.turn - t.get("turn", self.turn)) <= 15
                ][-10:]
                changes.append(f"Physical trace left at {loc_obj.name}")



        # 7. NPC episodic memories (significance 1-5)
        if "add_fact" in update:
            fact = update["add_fact"]
            if fact not in self.player.known_facts:
                self.player.known_facts.append(fact)
            if fact not in self.world_facts:
                self.world_facts.append(fact)
            changes.append(f"New world fact recorded: {fact}")
            
        # Grant skill
        if "create_npc" in update:
            npc_data = update["create_npc"]
            new_npc = self.register_dynamic_npc(npc_data)
            changes.append(f"Dynamically registered NPC: {new_npc.name} (Tier: {new_npc.tier})")

        if "create_location" in update:
            loc_data = update["create_location"]
            new_loc = self.register_dynamic_location(loc_data)
            changes.append(f"Dynamically registered Location: {new_loc.name}")

        if "create_item" in update:
            item_data = update["create_item"]
            new_item = self.register_dynamic_item(item_data)
            changes.append(f"Dynamically registered Item: {new_item.name}")

        if "update_environment" in update:
            env_updates = update["update_environment"]
            if isinstance(env_updates, dict):
                for loc_id, env_dict in env_updates.items():
                    if isinstance(env_dict, dict):
                        for elem_key, val_str in env_dict.items():
                            self.update_environment_state(loc_id, elem_key, str(val_str))
                    elif isinstance(env_dict, str):
                        self.update_environment_state(loc_id, "state", env_dict)
            elif isinstance(env_updates, str):
                self.update_environment_state(self.player.location, "state", env_updates)
            changes.append("Environment physical state updated persistently")

        if "record_clue" in update:
            clue_data = update["record_clue"]
            if isinstance(clue_data, dict):
                for cid, cdesc in clue_data.items():
                    self.record_clue(cid, cdesc)
            changes.append("Discovered clue recorded permanently")

        # 13. Environmental Hazard Triggering (Chandelier cut, oil ignited, ceiling collapsed)
        if "trigger_hazard" in update:
            hazard_info = update["trigger_hazard"]
            if isinstance(hazard_info, dict):
                loc_id = hazard_info.get("location_id", self.player.location)
                hazard_name = hazard_info.get("hazard_name", "환경 기믹")
                effect_desc = hazard_info.get("effect", "발동됨")
                self.update_environment_state(loc_id, f"hazard_{hazard_name}", effect_desc)
                changes.append(f"💥 [환경 상호작용] {hazard_name} 발동: {effect_desc}")

        # 14. Asymmetric Mystery Clue Fragment Revelation
        if "reveal_clue_fragment" in update:
            clue_data = update["reveal_clue_fragment"]
            if isinstance(clue_data, dict):
                secret_id = clue_data.get("secret_id", "main_mystery")
                fragment = clue_data.get("fragment", "")
                if secret_id not in self.world_secrets:
                    self.world_secrets[secret_id] = {"truth": clue_data.get("truth", ""), "clues": [], "solved": False}
                if fragment and fragment not in self.world_secrets[secret_id]["clues"]:
                    self.world_secrets[secret_id]["clues"].append(fragment)
                    changes.append(f"🕵️ [비밀의 단서 조각 획득] ({secret_id}): {fragment}")

        # 15. Meaningful Dilemma Choice & Cost Recording
        if "record_dilemma" in update:
            d_data = update["record_dilemma"]
            if isinstance(d_data, dict):
                self.dilemmas_faced.append(d_data)
                changes.append(f"⚖️ [딜레마 선택과 대가] {d_data.get('choice_summary', '선택됨')}")

        # 16. Faction Ripple Effect
        if "faction_ripple" in update:
            f_data = update["faction_ripple"]
            if isinstance(f_data, dict):
                fac_id = f_data.get("faction_id")
                try:
                    delta = int(f_data.get("delta", 0))
                except (ValueError, TypeError):
                    delta = 0
                reason = f_data.get("reason", "")
                if fac_id:
                    ripple_logs = self.apply_faction_ripple(fac_id, delta, reason)
                    changes.extend(ripple_logs)

        # Update NPC Attitude Matrix (affinity, fear, debt)
        if "update_environment_metrics" in update:
            env_delta = update["update_environment_metrics"]
            if isinstance(env_delta, dict):
                for k, v in env_delta.items():
                    if hasattr(self.environment, k):
                        setattr(self.environment, k, v)
                changes.append(f"환경 수치 갱신: {self.environment.to_anchoring_text()}")

        # Queue Information Travel Delay Wave
        if "queue_information_wave" in update:
            wave_data = update["queue_information_wave"]
            if isinstance(wave_data, dict) and wave_data.get("event_desc"):
                self.pending_info_waves.append(PendingInformation(
                    event_desc=wave_data["event_desc"],
                    origin_location=wave_data.get("origin_location", self.player.location),
                    target_npcs=wave_data.get("target_npcs", []),
                    remaining_turns=wave_data.get("delay_turns", 2)
                ))
                changes.append(f"정보 전파 대기열 등록: '{wave_data['event_desc']}' (지연: {wave_data.get('delay_turns', 2)}턴)")


        # Quest Engine Deltas
        if "active_campsite" in update:
            from src.world.campsite_engine import CampsiteState
            c_val = update["active_campsite"]
            if isinstance(c_val, dict):
                self.active_campsite = CampsiteState.from_dict(c_val)
            elif isinstance(c_val, CampsiteState) or c_val is None:
                self.active_campsite = c_val
            changes.append("⛺ 야영지 상태 동기화")

        # World ended
        if "world_ended" in update:
            self.active_world_ended = update["world_ended"]
            changes.append(f"World ended state set to: {self.active_world_ended}")

        self.turn += 1
        return changes





    def _apply_subsystem_engine_deltas(self, update: dict, changes: list[str]) -> None:
        """Applies quest, economy, shop, crafting, party, and ecological cascade deltas."""
        if "accept_quest" in update:
            from src.world.quest_engine import QuestEngine
            q_id = update["accept_quest"]
            success, msg = QuestEngine.accept_quest(self, str(q_id))
            changes.append(msg)

        if "advance_quest" in update:
            from src.world.quest_engine import QuestEngine
            adv_data = update["advance_quest"]
            if isinstance(adv_data, dict):
                e_type = adv_data.get("type", "condition")
                target = adv_data.get("target", "")
                count = adv_data.get("count", 1)
                q_logs = QuestEngine.progress_event(self, e_type, target, count)
                changes.extend(q_logs)

        if "choose_quest_branch" in update:
            from src.world.quest_engine import QuestEngine
            b_data = update["choose_quest_branch"]
            if isinstance(b_data, dict):
                q_id = b_data.get("quest_id", "")
                c_id = b_data.get("choice_id", "")
                _, _, b_logs = QuestEngine.choose_branch(self, q_id, c_id)
                changes.extend(b_logs)

        if "complete_quest" in update:
            from src.world.quest_engine import QuestEngine
            q_id = update["complete_quest"]
            c_logs = QuestEngine.complete_quest(self, str(q_id))
            changes.extend(c_logs)

        if "fail_quest" in update:
            from src.world.quest_engine import QuestEngine
            f_data = update["fail_quest"]
            q_id = f_data.get("quest_id") if isinstance(f_data, dict) else str(f_data)
            reason = f_data.get("reason", "") if isinstance(f_data, dict) else ""
            f_logs = QuestEngine.fail_quest(self, q_id, reason)
            changes.extend(f_logs)

        # Economy & Shop Deltas
        if "buy_item" in update:
            from src.world.economy_engine import EconomyEngine
            b_info = update["buy_item"]
            if isinstance(b_info, dict):
                s_id = b_info.get("shop_id", "")
                i_id = b_info.get("item_id", "")
                cnt = b_info.get("count", 1)
                is_hag = b_info.get("is_haggled", False)
                _, buy_msg, _ = EconomyEngine.buy_item(self, s_id, i_id, count=cnt, is_haggled=is_hag)
                changes.append(buy_msg)

        if "sell_item" in update:
            from src.world.economy_engine import EconomyEngine
            s_info = update["sell_item"]
            if isinstance(s_info, dict):
                s_id = s_info.get("shop_id", "")
                i_id = s_info.get("item_id", "")
                cnt = s_info.get("count", 1)
                is_hag = s_info.get("is_haggled", False)
                _, sell_msg, _ = EconomyEngine.sell_item(self, s_id, i_id, count=cnt, is_haggled=is_hag)
                changes.append(sell_msg)

        if "use_shop_service" in update:
            from src.world.economy_engine import EconomyEngine
            srv_info = update["use_shop_service"]
            if isinstance(srv_info, dict):
                s_id = srv_info.get("shop_id", "")
                srv_id = srv_info.get("service_id", "")
                _, srv_msg = EconomyEngine.use_service(self, s_id, srv_id)
                changes.append(srv_msg)

        # Crafting & Alchemy Deltas
        if "craft_item" in update:
            from src.world.crafting_engine import CraftingEngine
            c_info = update["craft_item"]
            if isinstance(c_info, dict):
                r_id = c_info.get("recipe_id", "")
                cat_id = c_info.get("catalyst_id")
                _, craft_msg, _ = CraftingEngine.craft_item(self, r_id, catalyst_id=cat_id)
                changes.append(craft_msg)

        if "salvage_item" in update:
            from src.world.crafting_engine import CraftingEngine
            sal_info = update["salvage_item"]
            i_id = sal_info.get("item_id") if isinstance(sal_info, dict) else str(sal_info)
            _, sal_msg, _ = CraftingEngine.salvage_item(self, i_id)
            changes.append(sal_msg)

        # Party & Companion Deltas
        if "recruit_companion" in update:
            from src.world.party_engine import PartyEngine
            c_id = str(update["recruit_companion"])
            _, r_msg, _ = PartyEngine.recruit_companion(self, c_id)
            changes.append(r_msg)

        if "dismiss_companion" in update:
            from src.world.party_engine import PartyEngine
            c_id = str(update["dismiss_companion"])
            _, d_msg, _ = PartyEngine.dismiss_companion(self, c_id)
            changes.append(d_msg)

        if "modify_companion_loyalty" in update:
            from src.world.party_engine import PartyEngine
            m_data = update["modify_companion_loyalty"]
            if isinstance(m_data, dict):
                c_id = m_data.get("companion_id", "")
                delta = m_data.get("delta", 0)
                reason = m_data.get("reason", "")
                l_msg, _ = PartyEngine.modify_loyalty_and_affinity(self, c_id, delta, reason=reason)
                if l_msg:
                    changes.append(l_msg)

        # 17. Power Vacuum & Subservience Dynamic
        if "power_vacuum_reaction" in update:
            p_data = update["power_vacuum_reaction"]
            if isinstance(p_data, dict):
                for nid, dyn_state in p_data.items():
                    if nid in self.npcs:
                        self.npcs[nid].power_dynamic_state = dyn_state
                        changes.append(f"👑 [권력 역학 분기] NPC [{self.npcs[nid].name}] 상태 전이: '{dyn_state}'")

        # 18. Ecological Vacuum Collapse (Trophic Cascade)
        if "ecological_collapse" in update:
            eco_data = update["ecological_collapse"]
            if isinstance(eco_data, dict) and eco_data.get("hazard_mutation"):
                self.world_facts.append(f"[생태계 진공 붕괴] {eco_data['hazard_mutation']}")
                changes.append(f"☣️ [생태계 연쇄 붕괴] {eco_data['hazard_mutation']}")


        # 19. Morale & Surrender Threshold

    def append_history(self, entry: dict) -> None:
        """Append a turn entry to history, auto-archiving turns beyond the 50-turn cap to SQLite."""
        self.history.append(entry)
        if len(self.history) > 50:
            excess = self.history[:-50]
            self.history = self.history[-50:]
            try:
                from src.world.persistence import PersistenceManager
                wid = self.world_id or self.session_id or "default_world"
                PersistenceManager.archive_turns(wid, excess)
            except Exception as e:
                logger.warning(f"Failed to auto-archive history excess: {e}")

    def to_dict(self) -> dict:
        return json.loads(self.to_json())

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "WorldState":
        raw = json.loads(data)
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> "WorldState":
        from src.persistence.migration import SaveMigrationEngine
        raw = SaveMigrationEngine.migrate(raw)
        state = cls()
        state.session_id = raw.get("session_id", "default_session")
        state.world_id = raw.get("world_id", "")
        state.world_name = raw.get("world_name", "")
        state.world_genre = raw.get("world_genre", "")
        state.turn = raw.get("turn", 0)
        state.civilization_era = raw.get("civilization_era", "")
        state.epoch_state = raw.get("epoch_state", "안정기")
        state.founded_religions = raw.get("founded_religions", [])
        state.total_population = raw.get("total_population", 0)
        state.total_area_sq_km = raw.get("total_area_sq_km", 0.0)
        state.magic_suppression_cycle = raw.get("magic_suppression_cycle", 0)
        state.planar_convergence_cycle = raw.get("planar_convergence_cycle", 0)
        state.world_threat_level = raw.get("world_threat_level", 10)
        state.global_apocalyptic_threat = raw.get("global_apocalyptic_threat", "")
        state.world_crisis_active_stage = raw.get("world_crisis_active_stage", 0)
        state.global_nemesis_npc_id = raw.get("global_nemesis_npc_id", "")
        state.global_sanctuary_region_id = raw.get("global_sanctuary_region_id", "")
        state.grand_crusade_coalition = raw.get("grand_crusade_coalition", [])
        state.universal_gravity_scale = raw.get("universal_gravity_scale", 1.0)
        state.memory_decay_turn_interval = raw.get("memory_decay_turn_interval", 50)
        state.cosmic_alignment_element = raw.get("cosmic_alignment_element", "neutral")
        state.world_soul_awakening_ratio = raw.get("world_soul_awakening_ratio", 0)
        state.pantheon_deities = raw.get("pantheon_deities", [])
        state.days_per_month = raw.get("days_per_month", 30)
        state.months_per_year = raw.get("months_per_year", 12)
        state.world_traits = raw.get("world_traits", raw.get("traits", []))
        state.world_reputation = raw.get("world_reputation", 0)
        state.world_facts = raw.get("world_facts", [])
        state.world_news_feed = raw.get("world_news_feed", [])
        state.world_chronicle = raw.get("world_chronicle", "")
        state.active_world_ended = raw.get("active_world_ended", False)
        state.active_map_image = raw.get("active_map_image", "data/maps/default_overworld.jpg")
        state.history = raw.get("history", [])
        state.last_dice_result = raw.get("last_dice_result", None)
        state.last_npc_action = raw.get("last_npc_action", None)
        state.current_scenario_id = raw.get("current_scenario_id", None)
        state.current_scenario_act = raw.get("current_scenario_act", "act_1_hook_and_misdirection")
        state.power_scale_preset_id = raw.get("power_scale_preset_id", "standard_fantasy")

        def safe_init(target_cls, data_dict: dict, **defaults):
            if not isinstance(data_dict, dict):
                data_dict = {}
            valid_fields = {f.name for f in fields(target_cls)}
            merged = {**defaults, **data_dict}
            filtered = {k: v for k, v in merged.items() if k in valid_fields}
            return target_cls(**filtered)

        # Skills DB
        state.skills_db = {}
        for k, v in raw.get("skills_db", {}).items():
            state.skills_db[k] = safe_init(Skill, v, id=k, name=k)

        # Titles DB
        state.titles_db = {}
        for k, v in raw.get("titles_db", {}).items():
            state.titles_db[k] = safe_init(Title, v, id=k, name=k, description="")

        # Player
        p_raw = raw.get("player", {})
        eq_raw = p_raw.get("equipment", {}) if isinstance(p_raw, dict) else {}
        equipment = safe_init(EquipmentSlots, eq_raw)

        p_name = p_raw.get("name", "방랑자") if isinstance(p_raw, dict) else "방랑자"
        p_vis_raw = p_raw.get("visual", {}) if isinstance(p_raw, dict) else {}
        p_visual = safe_init(NPCVisualDetails, p_vis_raw)
        if isinstance(getattr(p_visual, "face_details", None), dict):
            p_visual.face_details = safe_init(FacialDetails, p_visual.face_details)
        if isinstance(getattr(p_visual, "body_measurements", None), dict):
            p_visual.body_measurements = safe_init(BodyMeasurements, p_visual.body_measurements)
        if isinstance(getattr(p_visual, "outfit", None), dict):
            p_visual.outfit = safe_init(ClothingLayer, p_visual.outfit)

        state.player = Player(
            name=p_name,
            location=p_raw.get("location", "start") if isinstance(p_raw, dict) else "start",
            inventory=p_raw.get("inventory", []) if isinstance(p_raw, dict) else [],
            health=p_raw.get("health", 100) if isinstance(p_raw, dict) else 100,
            max_health=p_raw.get("max_health", 100) if isinstance(p_raw, dict) else 100,
            mana=p_raw.get("mana", 50) if isinstance(p_raw, dict) else 50,
            max_mana=p_raw.get("max_mana", 50) if isinstance(p_raw, dict) else 50,
            stamina=p_raw.get("stamina", 100) if isinstance(p_raw, dict) else 100,
            max_stamina=p_raw.get("max_stamina", 100) if isinstance(p_raw, dict) else 100,
            level=p_raw.get("level", 1) if isinstance(p_raw, dict) else 1,
            exp=p_raw.get("exp", 0) if isinstance(p_raw, dict) else 0,
            gold=p_raw.get("gold", 20) if isinstance(p_raw, dict) else 20,
            stat_points=p_raw.get("stat_points", 0) if isinstance(p_raw, dict) else 0,
            strength=min(MAX_STAT_VALUE, p_raw.get("strength", p_raw.get("str_stat", 10))) if isinstance(p_raw, dict) else 10,
            agility=min(MAX_STAT_VALUE, p_raw.get("agility", p_raw.get("dex_stat", 10))) if isinstance(p_raw, dict) else 10,
            intelligence=min(MAX_STAT_VALUE, p_raw.get("intelligence", p_raw.get("int_stat", 10))) if isinstance(p_raw, dict) else 10,
            constitution=min(MAX_STAT_VALUE, p_raw.get("constitution", p_raw.get("con_stat", 10))) if isinstance(p_raw, dict) else 10,
            crit_rate_bonus=p_raw.get("crit_rate_bonus", 0) if isinstance(p_raw, dict) else 0,
            crit_damage_bonus=p_raw.get("crit_damage_bonus", 0) if isinstance(p_raw, dict) else 0,
            wisdom=min(MAX_STAT_VALUE, p_raw.get("wisdom", p_raw.get("wis_stat", 10))) if isinstance(p_raw, dict) else 10,
            luck=min(MAX_STAT_VALUE, p_raw.get("luck", p_raw.get("cha_stat", 10))) if isinstance(p_raw, dict) else 10,
            perception=min(MAX_STAT_VALUE, p_raw.get("perception", p_raw.get("per_stat", 10))) if isinstance(p_raw, dict) else 10,
            reputation=max(MIN_REPUTATION_TOTAL, min(MAX_REPUTATION_TOTAL, p_raw.get("reputation", 0))) if isinstance(p_raw, dict) else 0,
            known_facts=p_raw.get("known_facts", []) if isinstance(p_raw, dict) else [],
            combat_profile=safe_init(CombatProfile, p_raw.get("combat_profile", {}) if isinstance(p_raw, dict) else {}),
            equipment=equipment,
            visual=p_visual,
            skills=p_raw.get("skills", []) if isinstance(p_raw, dict) else [],
            titles=p_raw.get("titles", []) if isinstance(p_raw, dict) else [],
            active_title=p_raw.get("active_title") if isinstance(p_raw, dict) else None,
            known_magic_words=p_raw.get("known_magic_words", []) if isinstance(p_raw, dict) else [],
            injuries=p_raw.get("injuries", []) if isinstance(p_raw, dict) else [],
            unnoticed_thefts=p_raw.get("unnoticed_thefts", []) if isinstance(p_raw, dict) else [],
            traumas=p_raw.get("traumas", []) if isinstance(p_raw, dict) else [],
            traits=p_raw.get("traits", []) if isinstance(p_raw, dict) else [],
            sub_stats=p_raw.get("sub_stats", {}) if isinstance(p_raw, dict) else {},
            poise=float(p_raw.get("poise", 0.0)) if isinstance(p_raw, dict) else 0.0,
            is_stealthed=bool(p_raw.get("is_stealthed", False)) if isinstance(p_raw, dict) else False,
            mana_burn_state=dict(p_raw.get("mana_burn_state", {})) if isinstance(p_raw, dict) else {},
            alcohol_state=dict(p_raw.get("alcohol_state", {})) if isinstance(p_raw, dict) else {}
        )
        from src.world.status_engine import StatusEffect
        raw_p_status = p_raw.get("status_effects", {}) if isinstance(p_raw, dict) else {}
        p_status_dict = {}
        if isinstance(raw_p_status, dict):
            for s_id, s_data in raw_p_status.items():
                if isinstance(s_data, dict):
                    p_status_dict[s_id] = StatusEffect.from_dict(s_data)
                elif isinstance(s_data, StatusEffect):
                    p_status_dict[s_id] = s_data
        state.player.status_effects = p_status_dict

        # Locations
        state.locations = {}
        for k, v in raw.get("locations", {}).items():
            state.locations[k] = safe_init(
                Location, v,
                id=k, name=k, description="", exits={}, visited=False,
                items=[], npcs=[], environmental_hazards=[],
                location_category="surface", dungeon_id=None, floor_depth=0,
                monster_density=20, npc_density=50, danger_level=20, traps=[],
                rock_strata="granite", structural_integrity=100.0, collapse_stage="stable",
                floor_type="solid_rock", floor_durability=100.0, floor_collapse_stage="stable",
                ventilation_open=False, active_toxic_gas=None, water_quality="clean"
            )

        # NPCs
        state.npcs = {}
        for k, v in raw.get("npcs", {}).items():
            npc_dict = dict(v) if isinstance(v, dict) else {}
            raw_memories = npc_dict.pop("memories", [])
            raw_n_status = npc_dict.pop("status_effects", {})
            p_dict = npc_dict.pop("personality", {})
            personality = safe_init(NPCPersonality, p_dict)
            n_dict = npc_dict.pop("needs", {})
            needs = safe_init(NPCNeeds, n_dict)
            eq_dict = npc_dict.pop("equipment", {})
            equipment = safe_init(EquipmentSlots, eq_dict)
            cp_dict = npc_dict.pop("combat_profile", {})
            combat_profile = safe_init(CombatProfile, cp_dict)
            v_dict = npc_dict.pop("visual", {})
            visual = safe_init(NPCVisualDetails, v_dict)
            if isinstance(getattr(visual, "face_details", None), dict):
                visual.face_details = safe_init(FacialDetails, visual.face_details)
            if isinstance(getattr(visual, "body_measurements", None), dict):
                visual.body_measurements = safe_init(BodyMeasurements, visual.body_measurements)
            if isinstance(getattr(visual, "outfit", None), dict):
                visual.outfit = safe_init(ClothingLayer, visual.outfit)

            npc = safe_init(
                NPC, npc_dict,
                id=k, name=k, description="", location=state.player.location,
                personality=personality, needs=needs, equipment=equipment,
                combat_profile=combat_profile, visual=visual,
                job="방랑자", level=1, health=50, max_health=50, mana=30, max_mana=30,
                stamina=100, max_stamina=100,
                armor_class=10, gold=15, strength=10, agility=10, intelligence=10,
                constitution=10, wisdom=10, luck=10, crit_rate_bonus=0, crit_damage_bonus=0,
                stats_revealed=False, is_legacy=False, legacy_id=None, age_delta=0,
                tier="commoner", influence_scope="local", desire="", weakness="",
                appearance_story="", bonds={}, trauma="", quirk="", taboo="",
                tastes={"likes": [], "dislikes": []}, physical_condition="",
                speech_style="", daily_routine="", superstitions="",
                self_image_vs_reputation="", hidden_side="", education_level="",
                financial_state="", skills=[], titles=[], attitude_description="",
                interests=[], current_activity="", schedule=[], off_screen_logs=[],
                last_seen_turn=0, physical_traces=[], fatigue=0, reputation=0, goal="",
                blackmail_secret="", faction_id="", faction_role="", traits=[],
                anatomy_parts={}, harvested_parts=[],
                life_defining_moment="", value_hierarchy=["survival", "wealth", "honor", "family", "faith"],
                coping_mechanism="", public_mask="", moral_justification="",
                micro_leakage_traits=[], risk_tolerance=50, bdi_state={},
                trust=50, respect=50, envy=0, pity=0, dominance=50, curiosity=50, disgust=0,
                emotion_state={}, stress=0, relationship_map={}, archetype_template="",
                eval_tier=1, last_eval_tick=0, decision_cache_key="", decision_cache_result={},
                state_version=0, trauma_runtime={}
            )
            npc.memories = [safe_init(MemoryEntry, m) for m in raw_memories if isinstance(m, dict)]
            n_status_dict = {}
            if isinstance(raw_n_status, dict):
                for s_id, s_data in raw_n_status.items():
                    if isinstance(s_data, dict):
                        n_status_dict[s_id] = StatusEffect.from_dict(s_data)
                    elif isinstance(s_data, StatusEffect):
                        n_status_dict[s_id] = s_data
            npc.status_effects = n_status_dict
            state.npcs[k] = npc

        # Clean up any legacy duplicates in loaded state
        legacy_npcs = [nid for nid, n in state.npcs.items() if getattr(n, "is_legacy", False)]
        if len(legacy_npcs) > 1:
            for remove_id in legacy_npcs[:-1]:
                state.npcs.pop(remove_id, None)
                for loc in state.locations.values():
                    if remove_id in loc.npcs:
                        loc.npcs = [nid for nid in loc.npcs if nid != remove_id]

        # Factions DB
        state.factions = {}
        for k, v in raw.get("factions", {}).items():
            state.factions[k] = safe_init(Faction, v, id=k, name=k)

        # Macro World Lore, Secrets & Dynamic Discovery
        state.cosmology_template = raw.get("cosmology_template", {}) or raw.get("world_lore", {})
        state.world_lore = raw.get("world_lore", {}) or state.cosmology_template
        state.environment_states = raw.get("environment_states", {})
        state.discovered_clues = raw.get("discovered_clues", {})
        state.world_secrets = raw.get("world_secrets", {})
        state.dilemmas_faced = raw.get("dilemmas_faced", [])

        # 6-Tier Infrastructure Registry (Level 1~5)
        if raw.get("infrastructure"):
            try:
                from src.world.infrastructure import InfrastructureRegistry
                if isinstance(raw["infrastructure"], dict):
                    state.infrastructure = InfrastructureRegistry.from_dict(raw["infrastructure"])
                elif isinstance(raw["infrastructure"], InfrastructureRegistry):
                    state.infrastructure = raw["infrastructure"]
            except Exception as e:
                logger.warning(f"Failed to deserialize infrastructure registry: {e}")
                state.infrastructure = None
        else:
            state.infrastructure = None

        # Items
        state.items = {}
        for k, v in raw.get("items", {}).items():
            item_obj = safe_init(
                Item, v,
                id=k, name=k, description="", location=state.player.location,
                item_type="misc", damage=0, defense=0, value=0,
                scaling_stat="str", scaling_factor=1.0, properties={},
                weight=1.0, size="small", required_strength=10,
                can_store_in_bag=True, can_wield_as_weapon=True,
                improvised_damage=2, document_text="", utility_function="", puzzle_hint="",
                draw_weight_lbs=0.0, windup_seconds=0.0, stagger_power=0.0, physics_tags=[],
                traits=[], material="wood", hardness=0.0, flammability=1.0, is_destroyed=False,
                stored_items=[], true_spec_id="", is_identified=True, is_poisonous_lookalike=False,
                origin_target_name=""
            )
            if isinstance(getattr(item_obj, "visual", None), dict):
                item_obj.visual = safe_init(ItemVisualProfile, item_obj.visual)
            state.items[k] = item_obj

        # In-Game Time & Periodical State
        state.calendar_epoch_name = raw.get("calendar_epoch_name", "제국력")
        state.start_year = raw.get("start_year", 0)
        raw_distances = raw.get("distances", {})
        state.distances = {}
        if isinstance(raw_distances, dict):
            for dk, dv in raw_distances.items():
                try:
                    state.distances[str(dk)] = float(dv)
                except (ValueError, TypeError):
                    pass
        state.start_minute = raw.get("start_minute", 8 * 60)
        state.last_daily_paper_day = raw.get("last_daily_paper_day", 0)
        state.last_weekly_paper_week = raw.get("last_weekly_paper_week", 0)
        state.pending_breaking_news = raw.get("pending_breaking_news", [])

        # Environmental Metrics & Pending Info Waves
        env_raw = raw.get("environment", {}) if isinstance(raw.get("environment"), dict) else {}
        state.environment = safe_init(EnvironmentalMetrics, env_raw)
        
        state.pending_info_waves = []
        for w in raw.get("pending_info_waves", []):
            if isinstance(w, dict):
                state.pending_info_waves.append(safe_init(PendingInformation, w))

        # Quests DB
        from src.world.quest_engine import Quest
        state.quests = {}
        raw_quests = raw.get("quests", {})
        if isinstance(raw_quests, dict):
            for q_id, q_data in raw_quests.items():
                if isinstance(q_data, dict):
                    state.quests[q_id] = Quest.from_dict(q_data)
                elif isinstance(q_data, Quest):
                    state.quests[q_id] = q_data
        elif isinstance(raw_quests, list):
            for q_data in raw_quests:
                if isinstance(q_data, dict) and "id" in q_data:
                    state.quests[q_data["id"]] = Quest.from_dict(q_data)
                elif isinstance(q_data, Quest):
                    state.quests[q_data.id] = q_data

        # Shops DB
        from src.world.economy_engine import Shop
        state.shops = {}
        raw_shops = raw.get("shops", {})
        if isinstance(raw_shops, dict):
            for s_id, s_data in raw_shops.items():
                if isinstance(s_data, dict):
                    state.shops[s_id] = Shop.from_dict(s_data)
                elif isinstance(s_data, Shop):
                    state.shops[s_id] = s_data
        elif isinstance(raw_shops, list):
            for s_data in raw_shops:
                if isinstance(s_data, dict) and "id" in s_data:
                    state.shops[s_data["id"]] = Shop.from_dict(s_data)
                elif isinstance(s_data, Shop):
                    state.shops[s_data.id] = s_data

        # Recipes DB
        from src.world.crafting_engine import Recipe
        state.recipes = {}
        for r_id, r_data in raw.get("recipes", {}).items():
            if isinstance(r_data, dict):
                state.recipes[r_id] = Recipe.from_dict(r_data)
            elif isinstance(r_data, Recipe):
                state.recipes[r_id] = r_data

        # Party & Companions DB
        from src.world.party_engine import Companion
        state.party = {}
        for c_id, c_data in raw.get("party", {}).items():
            if isinstance(c_data, dict):
                state.party[c_id] = Companion.from_dict(c_data)
            elif isinstance(c_data, Companion):
                state.party[c_id] = c_data

        # Battlefield Active Corpses DB
        state.active_corpses = raw.get("active_corpses", {})
        # Active Siege Battles DB
        state.active_sieges = raw.get("active_sieges", {})
        # Pending Travel Waypoints
        state.pending_travel_waypoints = raw.get("pending_travel_waypoints", [])

        # Active Campsite
        camp_raw = raw.get("active_campsite")
        if camp_raw:
            from src.world.campsite_engine import CampsiteState
            if isinstance(camp_raw, dict):
                state.active_campsite = CampsiteState.from_dict(camp_raw)
            elif isinstance(camp_raw, CampsiteState):
                state.active_campsite = camp_raw
        else:
            state.active_campsite = None

        return state






