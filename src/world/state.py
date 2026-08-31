"""
WorldState is the ground truth of the Quilltale game world.
Contains full character stats, 5-scale NPC memory, Fog of War for NPC stats,
Korean localization mappings, and deterministic delta state transitions.
"""
from dataclasses import dataclass, field, fields
from typing import Optional, Dict, List, Any
import json

from src.core.config import (
    MAX_STAT_VALUE,
    MIN_STAT_VALUE,
    MIN_REPUTATION_DELTA,
    MAX_REPUTATION_DELTA,
    MIN_REPUTATION_TOTAL,
    MAX_REPUTATION_TOTAL,
    MAX_LEVELUP_STAT_GAIN,
    MAX_RINGS,
    MAX_EARRINGS,
    BASE_CRIT_RATE,
    CRIT_RATE_PER_POINT,
    LUCK_CRIT_BONUS,
    BASE_CRIT_DAMAGE,
    CRIT_DMG_PER_POINT
)

DISPOSITION_KO_MAP = {
    "friendly": "호의적인 태도로 보임",
    "neutral": "특별한 감정 없는 무표정",
    "wary": "경계하며 주시하고 있음",
    "hostile": "노골적인 적대감을 드러냄",
}



@dataclass
class EquipmentSlots:
    weapon: Optional[str] = None
    head: Optional[str] = None
    face: Optional[str] = None
    chest: Optional[str] = None
    legs: Optional[str] = None
    boots: Optional[str] = None
    gloves: Optional[str] = None
    cape: Optional[str] = None
    rings: list[str] = field(default_factory=list)   # max 20
    earrings: list[str] = field(default_factory=list) # max 8


@dataclass
class CombatProfile:
    strengths: str = ""
    weaknesses: str = ""
    preferred_tactics: str = ""
    intel_book: dict = field(default_factory=dict)  # Enemy ID -> Known weaknesses/tactics



@dataclass
class NPCPersonality:
    altruism: int = 50      # 이타심
    greed: int = 50         # 탐욕  
    courage: int = 50       # 용기
    suspicion: int = 50     # 의심도
    loyalty: int = 50       # 충성도
    aggression: int = 50    # 공격성


@dataclass
class Skill:
    id: str
    name: str                           # Korean name
    skill_type: str = 'active'          # 'active' | 'passive' | 'unique'
    is_unique: bool = False
    incantation: str = ''               # Magic incantation text
    incantation_length: int = 0         # 0 = not magic
    scaling_stat: str = 'str'
    scaling_factor: float = 1.0
    effect: dict = field(default_factory=dict)  # {'type': 'reveal_thoughts', ...}
    acquire_difficulty: str = 'common'  # common|rare|epic|legendary
    description: str = ''
    owner_npc_id: str = ''             # For unique skills: original NPC
    mana_cost: int = 0
    cooldown_turns: int = 0
    current_cooldown: int = 0
    element: str = "무속성"             # "화염" | "빙결" | "전격" | "암흑" | "신성" | "공간" | "물리"
    ancient_words: list[str] = field(default_factory=list)  # e.g. ["헬리오스", "아르케"]
    incantation_verse: str = ""         # Poetic/ceremonial incantation verse


@dataclass
class Title:
    id: str
    name: str                           # Korean
    description: str                    # Korean
    stat_bonuses: dict = field(default_factory=dict)  # {'crit_rate': 5, 'strength': 2}
    is_unique: bool = True              # Only 1 holder per world
    acquired_turn: int = 0


@dataclass
class Item:
    id: str
    name: str
    description: str
    location: str                   # location_id or "inventory" or NPC id
    item_type: str = "misc"         # "weapon" | "armor" | "consumable" | "key" | "document" | "misc" | "furniture" | "structure"
    damage: int = 0
    defense: int = 0
    value: int = 0
    scaling_stat: str = "str"       # "str" | "dex" | "int"
    scaling_factor: float = 1.0
    properties: dict = field(default_factory=dict)

    # Physical Object & Environment Interaction Properties
    weight: float = 1.0             # kg (무게)
    size: str = "small"             # "small" (가방 가능), "medium" (손에 들기 가능), "heavy" (괴력 필요), "massive" (건물/기둥)
    required_strength: int = 10     # 들거나 휘두르기 위한 최소 근력 (STR)
    can_store_in_bag: bool = True   # 가방 수납 가능 여부 (small만 True)
    can_wield_as_weapon: bool = True # 즉석 무기 활용 가능 여부
    improvised_damage: int = 2      # 즉석 무기로 사용할 때의 기본 피해량
    document_text: str = ""         # 전단지, 벽보, 서적 등의 읽을 수 있는 본문
    utility_function: str = ""      # 기믹형 유틸리티 기능 (예: "벽 투과 도청", "10분간 짙은 연막 살포", "도어 락픽")
    puzzle_hint: str = ""           # 퍼즐 및 환경 상호작용 힌트

    @property
    def tooltip_text(self) -> str:
        lines = [f"[{self.name}]"]

        type_ko = {
            "weapon": "무기", "armor": "방어구", "consumable": "소모품",
            "key": "열쇠", "document": "문서/서적", "furniture": "가구/기물",
            "structure": "구조물", "misc": "기타",
            "accessory": "악세서리", "ring": "반지", "earring": "귀걸이",
            "amulet": "목걸이", "bracelet": "팔찌", "trinket": "장신구",
            "material": "재료", "tool": "도구", "ingredient": "재료",
            "trophy": "트로피/기념품", "art": "예술품", "currency": "화폐",
        }.get(self.item_type, self.item_type)

        type_line = f"분류: {type_ko}"
        if self.value > 0:
            type_line += f" | 가치: {self.value}G"
        lines.append(type_line)


        stats = []
        if self.damage > 0:
            stats.append(f"공격력 +{self.damage}")
        if self.defense > 0:
            stats.append(f"방어력 +{self.defense}")
        if self.weight > 0:
            stats.append(f"무게: {self.weight}kg")
        if self.required_strength > 10:
            stats.append(f"요구 근력: STR {self.required_strength}")
        if stats:
            lines.append("스탯: " + " | ".join(stats))

        # Attached skills or stat bonuses in properties
        prop_effects = []
        if self.properties:
            for k, v in self.properties.items():
                if k == "granted_skill":
                    if isinstance(v, dict):
                        s_name = v.get("name", "무기 스킬")
                        s_scale = v.get("scaling", "")
                        s_desc = v.get("description", "")
                        scale_str = f" ({s_scale})" if s_scale else ""
                        desc_str = f" - {s_desc}" if s_desc else ""
                        prop_effects.append(f"무기 스킬: [{s_name}]{scale_str}{desc_str}")
                    else:
                        prop_effects.append(f"무기 스킬: [{v}]")
                elif k == "stat_bonuses" and isinstance(v, dict):
                    b_str = ", ".join(f"{bk}+{bv}" for bk, bv in v.items())
                    prop_effects.append(f"능력치: {b_str}")
                elif k == "special_effect":
                    prop_effects.append(f"특수 효과: {v}")
        if self.utility_function:
            prop_effects.append(f"특수 기능: {self.utility_function}")
        if prop_effects:
            lines.append("효과: " + " | ".join(prop_effects))


        if self.document_text:
            clean_doc = self.document_text.replace("═", "").replace("╔", "").replace("╗", "").replace("╚", "").replace("╝", "").replace("╠", "").replace("╣", "").replace("║", "").replace("※", "").strip()
            # Collapse multiple spaces
            clean_doc = " ".join(clean_doc.split())
            if clean_doc:
                lines.append(f"내용: \"{clean_doc[:70]}...\"")

        # Distinct appraisal / inspection text so hover card never duplicates the inventory card body
        inspection = self.appraisal_text
        if inspection:
            lines.append(f"감정: {inspection}")

        return "\n".join(lines)

    @property
    def appraisal_text(self) -> str:
        """Detailed sensory / material / craftsmanship inspection distinct from basic card description."""
        if self.properties and self.properties.get("appraisal"):
            return str(self.properties["appraisal"])
        
        type_appraisals = {
            "weapon": "균형미와 날의 마모도를 보아 실전에서 단련된 병기입니다.",
            "armor": "방어 부위의 이음새가 견고하여 물리적 충격을 흡수하도록 설계되었습니다.",
            "accessory": "은은한 마력의 파동과 섬세한 세공 문양이 돋보이는 장신구입니다.",
            "ring": "착용자의 손가락 마디에 맞물리며 미약한 기운을 발산하는 반지입니다.",
            "earring": "귓가에서 찰랑이며 미세한 마력의 공명을 일으킵니다.",
            "amulet": "목에 걸었을 때 가슴께로 온기가 퍼져나가는 부적입니다.",
            "key": "정교하게 깎인 홈이 특정 자물쇠와의 결합을 암시합니다.",
            "document": "종이의 바램과 잉크의 번짐 정도로 보아 사연이 깃든 기록물입니다.",
            "tool": "정밀하게 가공되어 특정 탐색 및 작업 환경에서 유용하게 기능합니다.",
            "consumable": "개봉 시 즉각적인 약효나 특수 효과를 발휘하도록 밀봉되어 있습니다.",
            "misc": "호기심을 자극하는 독특한 재질과 구조를 갖추고 있습니다."
        }
        return type_appraisals.get(self.item_type, "겉면의 질감과 만듦새에서 세월의 흔적이 느껴집니다.")







@dataclass
class MemoryEntry:
    """
    Episodic memory belonging to an NPC.
    significance: 1 (minor) ~ 5 (world-shaking/permanent anchor)
    """
    turn: int
    description: str
    emotional_tone: str             # "suspicious" | "grateful" | "fearful" | "angry" | "wary" | "neutral"
    significance: int = 1           # 1-5 scale
    is_anchor: bool = False


@dataclass
class Faction:
    id: str
    name: str                           # 국가 또는 세력 이름 (예: "루멘 성왕국", "그림자 상단")
    system: str = "왕정"                # 정치 체제 (왕정, 공화정, 마도정 등)
    power_level: str = "강국"           # 국력/세력 규모 (강대국, 소국, 비밀결사 등)
    ruling_race: str = "인간"           # 지배 종족
    taboos: list[str] = field(default_factory=list) # 사회적/종교적 금기
    relations: dict[str, str] = field(default_factory=dict) # 타 세력과의 관계 {"faction_b": "적대" | "동맹" | "중립"}


@dataclass
class NPCNeeds:
    hunger: int = 20        # 허기 (0: 포만 ~ 100: 아사 위기)
    wealth: int = 40        # 금전욕/생계 (0: 부유 ~ 100: 궁핍)
    safety: int = 30        # 안전/공포 (0: 평온 ~ 100: 극도의 위협)
    social: int = 30        # 대화/소문욕구 (0: 충족 ~ 100: 소문 갈증)
    ambition: int = 50      # 야망/목표 집착도 (0: 나태 ~ 100: 집착)


@dataclass
class NPC:
    id: str
    name: str
    description: str
    location: str                   # location_id
    combat_profile: CombatProfile = field(default_factory=CombatProfile)
    tier: str = "commoner"          # "commoner" (일반) | "intermediate" (중급 네임드) | "legend" (상급/전설 네임드)
    influence_scope: str = "local"  # "local" (마을) | "regional" (영지/길드) | "global" (대륙/국가)
    job: str = "방랑자"              # 직업/역할군 (선술집 주인, 상인, 도적, 마법사 등)
    disposition: str = "neutral"    # "friendly" | "neutral" | "wary" | "hostile"

    # 3D Personality & Causal Visual Story
    desire: str = ""                # 결정적 욕망/동기 (예: "잃어버린 가문의 명예 회복과 막대한 금화")
    weakness: str = ""              # 치명적 약점/지키고자 하는 것 (예: "병든 여동생의 안위", "극심한 고소공포증")
    appearance_story: str = ""      # 인과와 복선이 담긴 외형 묘사 (예: "오른쪽 손가락 두 개가 잘려 나갔고, 검집에 불로 지운 가문 인장이 새겨져 있다")

    # Full 13-Factor Human Persona System
    bonds: dict[str, str] = field(default_factory=dict)         # 인간관계망 {"npc_id": "관계"}
    trauma: str = ""                                            # 과거의 트라우마/후회
    quirk: str = ""                                             # 사소한 신체적 버릇/습관
    taboo: str = ""                                             # 도덕적 선/절대적 금기
    tastes: dict[str, list[str]] = field(default_factory=lambda: {"likes": [], "dislikes": []}) # 취향/호불호
    physical_condition: str = ""                                # 체질/지병/알레르기
    speech_style: str = ""                                      # 말투/방언/억양/입버릇
    daily_routine: str = ""                                     # 생체 리듬/아침형/야행성
    superstitions: str = ""                                     # 개인 징크스/미신/신앙
    self_image_vs_reputation: str = ""                          # 자의식 vs 타인 평판
    hidden_side: str = ""                                       # 숨겨진 이중생활/취미
    education_level: str = ""                                   # 교육 수준/문맹 여부/은어
    financial_state: str = ""                                   # 소비 성향/당장의 부채


    alive: bool = True
    level: int = 1
    health: int = 50
    max_health: int = 50
    mana: int = 30
    max_mana: int = 30
    armor_class: int = 10
    gold: int = 15
    inventory: list[str] = field(default_factory=list)
    equipment: EquipmentSlots = field(default_factory=EquipmentSlots)
    
    # 8 Core Stats (Symmetric with Player)
    strength: int = 10
    agility: int = 10
    intelligence: int = 10
    constitution: int = 10
    wisdom: int = 10
    luck: int = 10
    crit_rate_bonus: int = 0
    crit_damage_bonus: int = 0

    memories: list[MemoryEntry] = field(default_factory=list)
    stats_revealed: bool = False    # Fog of War: Hidden until combat/investigation
    name_revealed: bool = False     # Fog of War: Hidden until player asks/learns name
    alias_ko: str = ""              # Unidentified title (e.g. "선술집 주인", "과묵한 검사")
    is_legacy: bool = False         # True if this NPC is an archived past player
    legacy_id: Optional[str] = None
    age_delta: int = 0              # In-world years passed since original archiving
    personality: NPCPersonality = field(default_factory=NPCPersonality)
    needs: NPCNeeds = field(default_factory=NPCNeeds)
    goal: str = ""                                                # 현재 추구하는 단기/장기 목표
    skills: list[str] = field(default_factory=list)               # skill ids
    titles: list[str] = field(default_factory=list)
    attitude_description: str = ''                                # LLM-generated natural language attitude
    interests: list[str] = field(default_factory=list)             # 관심사 및 주요 탐구 분야
    current_activity: str = ''                                    # 현재 처한 상황 / 행동
    schedule: list[dict] = field(default_factory=list)             # [{"turn": 3, "location": "alley", "activity": "..."}]
    off_screen_logs: list[str] = field(default_factory=list)       # 시야 밖 겪은 사건 로그
    last_seen_turn: int = 0                                       # 플레이어와 마지막 조우 턴
    physical_traces: list[str] = field(default_factory=list)       # 남긴 물리적 흔적
    fatigue: int = 0                                              # 내부 피로도 (0~100)
    reputation: int = 0                                           # 내부 평판
    # BDI (Belief-Desire-Intention) Cognitive Architecture
    beliefs: list[str] = field(default_factory=list)              # 알고 있다고 믿는 사실/오해/풍문
    intention: str = ""                                           # 이번 턴에 취할 구체적 행동 의도
    # 3-Factor Attitude Matrix (Symmetric Cognitive Model)
    affinity: int = 50                                            # 친밀도 (0~100)
    fear: int = 0                                                 # 공포/위압감 (0~100)
    debt: int = 0                                                 # 부채감/은혜의 빚 (-100: 원한 ~ +100: 은혜)
    injuries: list[str] = field(default_factory=list)             # 신체 부위별 부상/장애
    traumas: list[str] = field(default_factory=list)              # 심리적 트라우마/PTSD
    power_dynamic_state: str = "normal"                           # 권력 공백 반응: "normal" | "subservient"(복종/우상화) | "usurper"(찬탈) | "mutiny"(내분)
    morale: int = 100                                             # 전투 사기 (0~100, 30 이하 시 패주/항복 자백 협상)

    # Properties symmetric with Player
    @property
    def str_mod(self) -> int: return (self.strength - 10) // 2
    @property
    def agi_mod(self) -> int: return (self.agility - 10) // 2
    @property
    def int_mod(self) -> int: return (self.intelligence - 10) // 2 + max(0, (self.wisdom - 10) // 2)
    @property
    def effective_crit_rate(self) -> float:
        from src.core.config import BASE_CRIT_RATE, CRIT_RATE_PER_POINT, LUCK_CRIT_BONUS
        return BASE_CRIT_RATE + self.crit_rate_bonus * CRIT_RATE_PER_POINT + max(0, self.luck - 10) * LUCK_CRIT_BONUS
    @property
    def effective_crit_damage(self) -> float:
        from src.core.config import BASE_CRIT_DAMAGE, CRIT_DMG_PER_POINT
        return BASE_CRIT_DAMAGE + self.crit_damage_bonus * CRIT_DMG_PER_POINT
    @property
    def max_mana_effective(self) -> int:
        return self.max_mana + max(0, self.intelligence - 10) * 5

    @property
    def str_stat(self) -> int: return self.strength
    @property
    def dex_stat(self) -> int: return self.agility
    @property
    def con_stat(self) -> int: return self.constitution
    @property
    def int_stat(self) -> int: return self.intelligence
    @property
    def wis_stat(self) -> int: return self.wisdom
    @property
    def cha_stat(self) -> int: return self.luck


    @property
    def display_name_ko(self) -> str:
        """Name shown to player in UI status record. Hidden as ??? until introduced/revealed."""
        if self.name_revealed or self.id in ["player", "narrator"]:
            return self.name
        # alias_ko is set by GM only when player-visible alias is established
        if self.alias_ko:
            return f"??? ({self.alias_ko})"
        # Do NOT use job/tier/lore titles (e.g. "전설의 모험가", "군주") – derive only from
        # purely physical/observable traits the player could notice at a glance.
        # Derive atmospheric alias only from observable surface cues (name phonetics / hints in description)
        desc_lower = (self.description or "").lower()
        if "주인" in self.name or "마르타" in self.name:
            return "??? (술집 주인으로 보이는 인물)"
        if "상인" in self.name:
            return "??? (상인으로 보이는 인물)"
        if "후드" in self.name or "후드" in desc_lower:
            return "??? (후드를 깊이 눌러쓴 인물)"
        if "노인" in self.name or "노파" in self.name:
            return "??? (나이 든 인물)"
        if "소녀" in self.name or "아이" in self.name:
            return "??? (어린 인물)"
        if "기사" in desc_lower or "갑옷" in desc_lower:
            return "??? (갑옷을 입은 인물)"
        if "수상" in desc_lower or "로브" in desc_lower or "망토" in desc_lower:
            return "??? (수상한 인물)"
        # Final fallback: atmospheric impression only, no title/lore leaks
        return "??? (정체를 알 수 없는 인물)"



    @property
    def disposition_ko(self) -> str:
        if self.attitude_description:
            return self.attitude_description
        return DISPOSITION_KO_MAP.get(self.disposition.lower(), f"{self.disposition} 🟡")


    @property
    def impression_ko(self) -> str:
        """Atmospheric physical impression shown before stats are revealed."""
        if not self.alive:
            return "싸늘한 시신"
        
        impressions = []
        if self.max_health >= 70 or self.armor_class >= 14:
            impressions.append("위협적인 살기와 강인한 체구")
        elif self.max_health >= 50 or self.armor_class >= 12:
            impressions.append("다부진 체격")
        elif self.max_health >= 35:
            impressions.append("평범한 체구")
        else:
            impressions.append("왜소하고 병약한 체구")

        if self.personality.suspicion > 70:
            impressions.append("경계하는 눈빛")
        if self.personality.aggression > 70:
            impressions.append("공격적인 기세")
        if self.personality.altruism > 70:
            impressions.append("온화한 인상")
            
        return "와(과) ".join(impressions)

    def relevant_memories(self, max_memories: int = 5) -> list[MemoryEntry]:
        """
        Return the most impactful memories for prompt synthesis.
        Priority: significance (5 to 1) first, then recency.
        """
        sorted_memories = sorted(
            self.memories,
            key=lambda m: (m.significance, m.turn),
            reverse=True,
        )
        return sorted_memories[:max_memories]

    def memory_summary(self) -> str:
        relevant = self.relevant_memories()
        if not relevant:
            return f"{self.name} has no prior memory of interactions with the player."

        lines = [f"{self.name}'s memory of the player:"]
        for m in relevant:
            anchor_tag = " [ANCHOR]" if m.is_anchor or m.significance >= 4 else ""
            lines.append(
                f"  - Turn {m.turn} (Significance {m.significance}/5, {m.emotional_tone}{anchor_tag}): {m.description}"
            )
        return "\n".join(lines)


@dataclass
class Location:
    id: str
    name: str
    description: str
    exits: dict[str, str]           # {"north": "street", "upstairs": "room_21"}
    items: list[str] = field(default_factory=list)
    npcs: list[str] = field(default_factory=list)
    physical_traces: list[dict] = field(default_factory=list) # [{"npc_name": "방랑자", "trace": "젖은 붕대와 탄피", "turn": 3}]
    environmental_hazards: list[str] = field(default_factory=list) # 상호작용 가능한 환경 기믹 (예: ["매달린 샹들리에", "바닥의 기름통", "금이 간 기둥"])
    visited: bool = False




@dataclass
class EnvironmentalMetrics:
    weather: str = "맑음"                   # "맑음", "폭우", "농무", "모래폭풍", "폭설", "산성비"
    lighting: str = "적당한 밝기"            # "칠흑 같은 어둠", "희미한 등불", "적당한 밝기", "눈부신 분광"
    smell: str = "스산한 흙냄새"
    noise: str = "조용한 바람 소리"          # "적막", "바람 소리", "시끌벅적한 소음", "귀를 찢는 굉음"
    oxygen_level: int = 100                 # 산소 농도 (%)
    time_of_day: str = "낮"                 # "새벽", "낮", "황혼", "심야"
    hazard_level: int = 0                   # 환경 위험도 (0~100)
    market_inflation: dict[str, float] = field(default_factory=dict) # 아이템 카테고리별 물가 배율
    scent_trace: str = "청결함"              # 잔류 냄새 흔적 (예: "피비린내 누적", "그을음과 탄내")
    ambient_noise_occlusion: str = "일반"    # 음향 차폐 상태 (예: "폭포 굉음으로 외부 소음 차폐", "두꺼운 철문 차폐")
    temperature_celsius: int = 20           # 환경 온도 (섭씨)

    def to_anchoring_text(self) -> str:
        return (
            f"[🌿 현재 환경 앵커링] 시간: {self.time_of_day} | 날씨: {self.weather} | "
            f"조도: {self.lighting} | 냄새: {self.smell} | 소음: {self.noise} | "
            f"산소 농도: {self.oxygen_level}%"
        )


@dataclass
class PendingInformation:
    event_desc: str = ""                    # 전파되는 사건/소문 내용
    origin_location: str = ""               # 발생지
    target_npcs: list[str] = field(default_factory=list) # 도달할 대상 NPC id들 (비어있으면 전체 지역)
    remaining_turns: int = 2               # 도달까지 남은 턴 딜레이 (0이면 전파 완료)
    fear_distortion_factor: float = 0.5    # 목격자의 공포도 및 전언 거침에 따른 왜곡 배율

    def distort_event(self) -> str:
        """
        Whisper Distortion Engine: Realistically exaggerates and distorts rumors based on fear & transfer.
        """
        base = self.event_desc
        if "처치" in base or "사망" in base or "암살" in base or "살해" in base:
            distortions = [
                f"정체불명의 식인 괴물이 나타나 {base.replace('처치', '토막 내어 먹어 치움')}",
                f"금지된 암흑 교단이 배후에 있는 잔혹한 연쇄 학살 사건 ({base})",
                f"피에 굶주린 광기의 암살자가 {base}"
            ]
            import random
            return random.choice(distortions)
        elif "화염" in base or "폭발" in base:
            return f"대재앙급 화마가 일대를 집어삼키며 {base}"
        return f"[부풀려진 소문] {base}"



@dataclass
class Player:
    name: str = '방랑자'
    location: str = 'start'
    combat_profile: CombatProfile = field(default_factory=CombatProfile)
    inventory: list[str] = field(default_factory=list)
    health: int = 100
    max_health: int = 100
    mana: int = 50
    max_mana: int = 50
    level: int = 1
    exp: int = 0
    gold: int = 20
    stat_points: int = 0               # Unspent stat points
    
    # Core stats
    strength: int = 10          # 근력 - physical damage scaling
    agility: int = 10           # 민첩 - dodge, initiative, DEX weapons  
    intelligence: int = 10      # 지능 - magic damage, mana +5/pt
    constitution: int = 10      # 체력 - HP +10/pt, poison resist
    crit_rate_bonus: int = 0    # bonus points (base is 5% in config)
    crit_damage_bonus: int = 0  # bonus points (base is 150% in config)
    
    # Secondary stats
    wisdom: int = 10            # 지혜 - INT+1, mana regen, incant chars +1
    luck: int = 10              # 행운 - drop rate, crit+0.5%, unique skill chance
    
    # Equipment
    equipment: EquipmentSlots = field(default_factory=EquipmentSlots)
    
    # Skills and titles
    skills: list[str] = field(default_factory=list)   # skill ids
    titles: list[str] = field(default_factory=list)   # title ids
    active_title: Optional[str] = None
    
    # Known magic language vocabulary
    known_magic_words: list[str] = field(default_factory=list)
    
    reputation: int = 0
    known_facts: list[str] = field(default_factory=list)
    fatigue: int = 0                    # 피로도 (0~100)
    time_elapsed_minutes: int = 0       # 누적 인게임 시간 (분)
    injuries: list[str] = field(default_factory=list) # 신체 부위별 부상/장애 (예: ["오른팔 골절 (명중-3)"])
    traumas: list[str] = field(default_factory=list)  # 심리적 트라우마 (예: ["화염 공포증"])
    hygiene_level: int = 100            # 위생도 (0~100, 30 이하 시 체취 누출로 야수 기습 유발)
    body_temperature: float = 36.5      # 심부 체온 (34도 이하 저체온증, 39도 이상 열사병)
    
    @property
    def fatigue_status_ko(self) -> str:
        if self.fatigue >= 80:
            return "탈진 (호흡 곤란, 손떨림 및 마력 통제 극심한 저하)"
        elif self.fatigue >= 50:
            return "피로 (호흡이 가빠지고 몸이 무거움)"
        elif self.fatigue >= 20:
            return "경미한 피로"
        return "양호 (활력 넘침)"

    # Properties
    @property
    def str_stat(self) -> int: return self.strength

    @str_stat.setter
    def str_stat(self, value: int): self.strength = value
    @property
    def dex_stat(self) -> int: return self.agility
    @dex_stat.setter
    def dex_stat(self, value: int): self.agility = value
    @property
    def con_stat(self) -> int: return self.constitution
    @con_stat.setter
    def con_stat(self, value: int): self.constitution = value
    @property
    def int_stat(self) -> int: return self.intelligence
    @int_stat.setter
    def int_stat(self, value: int): self.intelligence = value
    @property
    def wis_stat(self) -> int: return self.wisdom
    @wis_stat.setter
    def wis_stat(self, value: int): self.wisdom = value
    @property
    def cha_stat(self) -> int: return self.luck
    @cha_stat.setter
    def cha_stat(self, value: int): self.luck = value

    @property
    def equipped_weapon(self) -> Optional[str]: return self.equipment.weapon
    @equipped_weapon.setter
    def equipped_weapon(self, value: Optional[str]): self.equipment.weapon = value
    @property
    def equipped_armor(self) -> Optional[str]: return self.equipment.chest
    @equipped_armor.setter
    def equipped_armor(self, value: Optional[str]): self.equipment.chest = value

    @property
    def str_mod(self) -> int: return (self.strength - 10) // 2
    @property  
    def agi_mod(self) -> int: return (self.agility - 10) // 2
    @property
    def int_mod(self) -> int: return (self.intelligence - 10) // 2 + max(0, (self.wisdom - 10) // 2)
    @property
    def effective_crit_rate(self) -> float:
        return BASE_CRIT_RATE + self.crit_rate_bonus * CRIT_RATE_PER_POINT + max(0, self.luck - 10) * LUCK_CRIT_BONUS
    @property
    def effective_crit_damage(self) -> float:
        return BASE_CRIT_DAMAGE + self.crit_damage_bonus * CRIT_DMG_PER_POINT
    @property
    def max_mana_effective(self) -> int:
        return self.max_mana + max(0, self.intelligence - 10) * 5


@dataclass
class WorldState:
    session_id: str = "default_session"
    world_id: str = ""
    world_name: str = "잿빛 변경"
    world_genre: str = "다크 판타지"
    turn: int = 0
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
    history: list[dict] = field(default_factory=list)
    last_dice_result: Optional[dict] = None
    last_npc_action: Optional[dict] = None
    
    # Scenario Tracking
    current_scenario_id: Optional[str] = None
    current_scenario_act: str = "act_1_hook_and_misdirection"

    # Macro World Architecture & Factions
    factions: dict[str, Faction] = field(default_factory=dict)         # 국가 및 주요 세력 DB
    world_lore: dict[str, Any] = field(default_factory=dict)           # 종족/마법체계/기원 등 거시 설정
    environment_states: dict[str, dict] = field(default_factory=dict) # {"tavern": {"door": "broken", "hearth": "burned"}}
    discovered_clues: dict[str, str] = field(default_factory=dict)     # 발견된 단서/비밀 DB
    world_secrets: dict[str, dict] = field(default_factory=dict)       # 비대칭 비밀/진실 DB (GM 비대칭 정보 & 단서 조각)
    dilemmas_faced: list[dict] = field(default_factory=list)           # 플레이어가 겪은 딜레마 선택과 대가 기록

    # In-Game Time & Periodical Publishing System
    start_minute: int = 8 * 60                  # 기본 시작 시각: 1일차 월요일 08:00 (480분)
    last_daily_paper_day: int = 0               # 마지막으로 일간지가 발간된 날짜
    last_weekly_paper_week: int = 0             # 마지막으로 주간지가 발간된 주차
    pending_breaking_news: list[str] = field(default_factory=list) # 호외 발행 대기열
    environment: EnvironmentalMetrics = field(default_factory=EnvironmentalMetrics)
    pending_info_waves: list[PendingInformation] = field(default_factory=list)



    @property
    def total_minutes(self) -> int:
        return self.start_minute + self.player.time_elapsed_minutes

    @property
    def current_day(self) -> int:
        return 1 + (self.total_minutes // (24 * 60))

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
    def time_display_ko(self) -> str:
        return f"{self.current_day}일차 {self.day_of_week_ko}요일 {self.current_hour:02d}:{self.current_minute:02d}"



    def current_location(self) -> Optional[Location]:
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

    def get_equipped_weapon_item(self) -> Optional[Item]:
        wep_id = self.player.equipment.weapon
        if wep_id and wep_id in self.items:
            return self.items[wep_id]
        return None

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
                    description=f"매주 월요일 아침에만 발행되는 두툼한 주간 연대보 양장본이다.",
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

        rumor_block = ""
        if self.world_facts:
            rumor_block = "\nGLOBAL WORLD FACTS / RUMORS:\n" + "\n".join(
                f"- {fact}" for fact in self.world_facts
            )

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
Player Inventory: {inv_str}{memory_block}{rumor_block}{arcane_laws_block}
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

        eq_wep = self.get_equipped_weapon_item()
        wep_str = f"{eq_wep.name} (공격력 +{eq_wep.damage})" if eq_wep else "맨손 (공격력 1)"

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
        if self.player.equipment.chest and self.player.equipment.chest in self.items:
            equipment_lines.append(f"상의: {self.items[self.player.equipment.chest].name}")
        if self.player.equipment.legs and self.player.equipment.legs in self.items:
            equipment_lines.append(f"하의: {self.items[self.player.equipment.legs].name}")
        if self.player.equipment.boots and self.player.equipment.boots in self.items:
            equipment_lines.append(f"신발: {self.items[self.player.equipment.boots].name}")
        if self.player.equipment.gloves and self.player.equipment.gloves in self.items:
            equipment_lines.append(f"장갑: {self.items[self.player.equipment.gloves].name}")
        if self.player.equipment.cape and self.player.equipment.cape in self.items:
            equipment_lines.append(f"망토: {self.items[self.player.equipment.cape].name}")
        for idx, ring in enumerate(self.player.equipment.rings):
            if ring in self.items:
                equipment_lines.append(f"반지{idx+1}: {self.items[ring].name}")
        for idx, earring in enumerate(self.player.equipment.earrings):
            if earring in self.items:
                equipment_lines.append(f"귀걸이{idx+1}: {self.items[earring].name}")
        
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
            ("상의", self.player.equipment.chest),
            ("하의", self.player.equipment.legs),
            ("신발", self.player.equipment.boots),
            ("장갑", self.player.equipment.gloves),
            ("망토", self.player.equipment.cape),
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

  <div class="qt-hud-line">🗡️ <b class='qt-hud-label'>장착 장비:</b> {eq_html}</div>
  <div class="qt-hud-line">💰 <b class='qt-hud-label'>소지금:</b> {self.player.gold} 골드{title_html}</div>
  <div class="qt-hud-line">✨ <b class='qt-hud-label'>스킬:</b> 패시브 {passives}개, 액티브 {actives}개, 고유 {uniques}개</div>
  {dice_block}
  {npc_block}
</div>
"""


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


            html_blocks.append(f"""
            <div class="qt-skill-card">
              <div class="qt-skill-header">
                <span class="qt-hover-tag" data-tooltip="{tt}"><b>{skill.name}</b></span>
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
        needs = NPCNeeds(**data.get("needs", {})) if "needs" in data else NPCNeeds()
        equipment = EquipmentSlots(**data.get("equipment", {})) if "equipment" in data else EquipmentSlots()

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
            strength=data.get("strength", 10),
            agility=data.get("agility", 10),
            intelligence=data.get("intelligence", 10),
            constitution=data.get("constitution", 10),
            wisdom=data.get("wisdom", 10),
            luck=data.get("luck", 10),
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
            financial_state=data.get("financial_state", "")
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
        """
        changes = []


        # 1. Player movement
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
                else:
                    changes.append(f"REJECTED move to {direction} — not a valid exit")
                    break

        # 2. Item pickup
        if "pickup_item" in update:
            item_id = update["pickup_item"]
            loc = self.current_location()
            if loc and item_id in loc.items and item_id in self.items:
                loc.items.remove(item_id)
                self.player.inventory.append(item_id)
                self.items[item_id].location = "inventory"
                changes.append(f"Player picked up {self.items[item_id].name}")
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
                for slot in ["weapon", "head", "face", "chest", "legs", "boots", "gloves", "cape"]:
                    if getattr(self.player.equipment, slot) == item_id:
                        setattr(self.player.equipment, slot, None)
                if item_id in self.player.equipment.rings:
                    self.player.equipment.rings.remove(item_id)
                if item_id in self.player.equipment.earrings:
                    self.player.equipment.earrings.remove(item_id)
                    
                changes.append(f"Player dropped {self.items[item_id].name}")

        # 4. Item equip (new format)
        if "equip_slot" in update:
            item_id = update["equip_slot"].get("item_id")
            slot = update["equip_slot"].get("slot")
            if item_id in self.player.inventory and item_id in self.items:
                item = self.items[item_id]
                if slot in ["weapon", "head", "face", "chest", "legs", "boots", "gloves", "cape"]:
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

        # 5. NPC state updates (alive, disposition, health, stats_revealed)
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
        if "add_location_trace" in update:
            trace_info = update["add_location_trace"]
            target_lid = trace_info.get("location_id", self.player.location)
            if target_lid in self.locations:
                self.locations[target_lid].physical_traces.append({
                    "trace": trace_info.get("trace", ""),
                    "turn": self.turn,
                    "npc_name": trace_info.get("npc_name", "미상")
                })
                changes.append(f"Physical trace left at {self.locations[target_lid].name}")



        # 7. NPC episodic memories (significance 1-5)
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
                    changes.append(
                        f"{npc.name} remembers (Lv.{entry.significance}/5): '{entry.description}'"
                    )

        # 8. Player health delta
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
        if "add_fact" in update:
            fact = update["add_fact"]
            if fact not in self.player.known_facts:
                self.player.known_facts.append(fact)
            if fact not in self.world_facts:
                self.world_facts.append(fact)
            changes.append(f"New world fact recorded: {fact}")
            
        # Grant skill
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

        # Time advanced updates
        if "time_minutes" in update:
            mins = int(update["time_minutes"])
            self.player.time_elapsed_minutes += mins
            changes.append(f"Time advanced by {mins} minutes (Total: {self.player.time_elapsed_minutes}m)")

        # 12. Dynamic Entity Registration & Persistence (Zero Evaporation)
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
            for loc_id, env_dict in update["update_environment"].items():
                for elem_key, val_str in env_dict.items():
                    self.update_environment_state(loc_id, elem_key, val_str)
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
            loc_id = hazard_info.get("location_id", self.player.location)
            hazard_name = hazard_info.get("hazard_name", "환경 기믹")
            effect_desc = hazard_info.get("effect", "발동됨")
            self.update_environment_state(loc_id, f"hazard_{hazard_name}", effect_desc)
            changes.append(f"💥 [환경 상호작용] {hazard_name} 발동: {effect_desc}")

        # 14. Asymmetric Mystery Clue Fragment Revelation
        if "reveal_clue_fragment" in update:
            clue_data = update["reveal_clue_fragment"]
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
            self.dilemmas_faced.append(d_data)
            changes.append(f"⚖️ [딜레마 선택과 대가] {d_data.get('choice_summary', '선택됨')}")

        # 16. Faction Ripple Effect
        if "faction_ripple" in update:
            f_data = update["faction_ripple"]
            fac_id = f_data.get("faction_id")
            delta = int(f_data.get("delta", 0))
            reason = f_data.get("reason", "")
            if fac_id:
                ripple_logs = self.apply_faction_ripple(fac_id, delta, reason)
                changes.extend(ripple_logs)
                

        # Update NPC Attitude Matrix (affinity, fear, debt)
        if "update_npc_attitude" in update:
            for npc_id, att_delta in update["update_npc_attitude"].items():
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
            for npc_id, belief_text in update["add_npc_belief"].items():
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

        # Update Environmental Metrics
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
                loc_id = eco_data.get("location_id", self.player.location)
                self.world_facts.append(f"[생태계 진공 붕괴] {eco_data['hazard_mutation']}")
                changes.append(f"☣️ [생태계 연쇄 붕괴] {eco_data['hazard_mutation']}")


        # 19. Morale & Surrender Threshold
        if "update_npc_morale" in update:
            for nid, m_delta in update["update_npc_morale"].items():
                if nid in self.npcs:
                    self.npcs[nid].morale = max(0, min(100, self.npcs[nid].morale + int(m_delta)))
                    changes.append(f"⚔️ NPC [{self.npcs[nid].name}] 사기 갱신: {self.npcs[nid].morale}/100")

        # 20. Hygiene & Body Temperature
        if "update_hygiene" in update:
            self.player.hygiene_level = max(0, min(100, self.player.hygiene_level + int(update["update_hygiene"])))
            changes.append(f"🧼 플레이어 위생 상태: {self.player.hygiene_level}/100")

        if "update_body_temperature" in update:
            self.player.body_temperature = round(self.player.body_temperature + float(update["update_body_temperature"]), 1)
            changes.append(f"🌡️ 플레이어 체온: {self.player.body_temperature}°C")

        # World ended
        if "world_ended" in update:
            self.active_world_ended = update["world_ended"]
            changes.append(f"World ended state set to: {self.active_world_ended}")

        self.turn += 1
        return changes




    def to_dict(self) -> dict:
        return json.loads(self.to_json())

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "WorldState":
        raw = json.loads(data)
        state = cls()
        state.session_id = raw.get("session_id", "default_session")
        state.world_id = raw.get("world_id", "")
        state.world_name = raw.get("world_name", "잿빛 변경")
        state.world_genre = raw.get("world_genre", "다크 판타지")
        state.turn = raw.get("turn", 0)
        state.world_reputation = raw.get("world_reputation", 0)
        state.world_facts = raw.get("world_facts", [])
        state.world_chronicle = raw.get("world_chronicle", "")
        state.active_world_ended = raw.get("active_world_ended", False)
        state.history = raw.get("history", [])
        state.last_dice_result = raw.get("last_dice_result", None)
        state.last_npc_action = raw.get("last_npc_action", None)
        state.current_scenario_id = raw.get("current_scenario_id", None)
        state.current_scenario_act = raw.get("current_scenario_act", "act_1_hook_and_misdirection")

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
        state.player = Player(
            name=p_name,
            location=p_raw.get("location", "start") if isinstance(p_raw, dict) else "start",
            inventory=p_raw.get("inventory", []) if isinstance(p_raw, dict) else [],
            health=p_raw.get("health", 100) if isinstance(p_raw, dict) else 100,
            max_health=p_raw.get("max_health", 100) if isinstance(p_raw, dict) else 100,
            mana=p_raw.get("mana", 50) if isinstance(p_raw, dict) else 50,
            max_mana=p_raw.get("max_mana", 50) if isinstance(p_raw, dict) else 50,
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
            reputation=max(MIN_REPUTATION_TOTAL, min(MAX_REPUTATION_TOTAL, p_raw.get("reputation", 0))) if isinstance(p_raw, dict) else 0,
            known_facts=p_raw.get("known_facts", []) if isinstance(p_raw, dict) else [],
            combat_profile=safe_init(CombatProfile, p_raw.get("combat_profile", {}) if isinstance(p_raw, dict) else {}),
            equipment=equipment,
            skills=p_raw.get("skills", []) if isinstance(p_raw, dict) else [],
            titles=p_raw.get("titles", []) if isinstance(p_raw, dict) else [],
            active_title=p_raw.get("active_title") if isinstance(p_raw, dict) else None,
            known_magic_words=p_raw.get("known_magic_words", []) if isinstance(p_raw, dict) else [],
            injuries=p_raw.get("injuries", []) if isinstance(p_raw, dict) else [],
            traumas=p_raw.get("traumas", []) if isinstance(p_raw, dict) else []
        )

        # Locations
        state.locations = {}
        for k, v in raw.get("locations", {}).items():
            state.locations[k] = safe_init(
                Location, v,
                id=k, name=k, description="", exits={}, visited=False,
                items=[], npcs=[], environmental_hazards=[]
            )

        # NPCs
        state.npcs = {}
        for k, v in raw.get("npcs", {}).items():
            npc_dict = dict(v) if isinstance(v, dict) else {}
            raw_memories = npc_dict.pop("memories", [])
            p_dict = npc_dict.pop("personality", {})
            personality = safe_init(NPCPersonality, p_dict)
            n_dict = npc_dict.pop("needs", {})
            needs = safe_init(NPCNeeds, n_dict)
            eq_dict = npc_dict.pop("equipment", {})
            equipment = safe_init(EquipmentSlots, eq_dict)
            cp_dict = npc_dict.pop("combat_profile", {})
            combat_profile = safe_init(CombatProfile, cp_dict)

            npc = safe_init(
                NPC, npc_dict,
                id=k, name=k, description="", location=state.player.location,
                personality=personality, needs=needs, equipment=equipment,
                combat_profile=combat_profile,
                job="방랑자", level=1, health=50, max_health=50, mana=30, max_mana=30,
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
                last_seen_turn=0, physical_traces=[], fatigue=0, reputation=0, goal=""
            )
            npc.memories = [safe_init(MemoryEntry, m) for m in raw_memories if isinstance(m, dict)]
            state.npcs[k] = npc

        # Clean up any legacy duplicates in loaded state
        legacy_npcs = [nid for nid, n in state.npcs.items() if getattr(n, "is_legacy", False)]
        if len(legacy_npcs) > 1:
            keep_id = legacy_npcs[-1]
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
        state.world_lore = raw.get("world_lore", {})
        state.environment_states = raw.get("environment_states", {})
        state.discovered_clues = raw.get("discovered_clues", {})
        state.world_secrets = raw.get("world_secrets", {})
        state.dilemmas_faced = raw.get("dilemmas_faced", [])

        # Items
        state.items = {}
        for k, v in raw.get("items", {}).items():
            state.items[k] = safe_init(
                Item, v,
                id=k, name=k, description="", location=state.player.location,
                item_type="misc", damage=0, defense=0, value=0,
                scaling_stat="str", scaling_factor=1.0, properties={},
                weight=1.0, size="small", required_strength=10,
                can_store_in_bag=True, can_wield_as_weapon=True,
                improvised_damage=2, document_text="", utility_function="", puzzle_hint=""
            )

        # In-Game Time Periodical State
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

        return state






