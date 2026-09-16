"""
Pure Domain Entities and Data Models for Quilltale World.
Defines Player, NPC, Location, Item, Skill, Equipment, and related data structures.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

from src.core.config import (
    BASE_CRIT_DAMAGE,
    BASE_CRIT_RATE,
    CRIT_DMG_PER_POINT,
    CRIT_RATE_PER_POINT,
    LUCK_CRIT_BONUS,
)

DISPOSITION_KO_MAP = {
    "friendly": "호의적인 태도로 보임",
    "neutral": "특별한 감정 없는 무표정",
    "wary": "경계하며 주시하고 있음",
    "hostile": "노골적인 적대감을 드러냄",
}

@dataclass
class EquipmentSlots:
    weapon: str | None = None
    head: str | None = None
    face: str | None = None
    chest: str | None = None
    legs: str | None = None
    boots: str | None = None
    gloves: str | None = None
    cape: str | None = None
    neck: str | None = None                        # 목걸이/초커/부적/펜던트
    belt: str | None = None                        # 허리띠/전술 벨트/탄띠/하네스
    shoulders: str | None = None                   # 견갑/어깨 장식/털 숄
    storage: str | None = None                     # 백팩/수납 가방/파우치
    innerwear: str | None = None                   # 갬비슨/속옷/은신 타이즈
    rings: list[str] = field(default_factory=list)      # max 20
    earrings: list[str] = field(default_factory=list)   # max 8
    bracelets: list[str] = field(default_factory=list)  # max 4 (팔찌/시계/아대)
    traits: list[str] = field(default_factory=lambda: ["장비 슬롯", "착용 슬롯", "의장 세분화"])



@dataclass
class CombatProfile:
    strengths: str = ""
    weaknesses: str = ""
    preferred_tactics: str = ""
    intel_book: dict = field(default_factory=dict)  # Enemy ID -> Known weaknesses/tactics



@dataclass
class NPCPersonality:
    # 6 Core Personality Metrics
    altruism: int = 50      # 이타심
    greed: int = 50         # 탐욕  
    courage: int = 50       # 용기
    suspicion: int = 50     # 의심도
    loyalty: int = 50       # 충성도
    aggression: int = 50    # 공격성

    # 6 Extended Psychological Axes
    patience: int = 50      # 인내심 (vs 충동성)
    cunning: int = 50       # 교활함 (vs 우직함)
    pride: int = 50         # 자존심/오만 (vs 겸양/굴신)
    rationality: int = 50   # 이성/논리 (vs 감정/격정)
    neuroticism: int = 50   # 신경증/불안 (vs 정서안정)
    deceit: int = 50        # 기만/위선 (vs 솔직함)

    traits: list[str] = field(default_factory=list) # 요약 특성 태그 목록


@dataclass
class Skill:
    # 1. 기본 식별 & 계통 (Identification & School)
    id: str
    name: str                                           # 스킬명 (예: "음혈부두술: 저주의 못", "화산파 육합검결")
    category: str = "physical"                          # 22대 계통:
    # 1. 일반 원소마법(70%): elemental_magic (구 arcane_magic 호환)
    # 2. 희귀/금기: blood_magic, dark_magic, sacrifice_toll, necromancy, alchemy, divination, summoning, runic, pact_binding, oneiric, mnemonic
    # 3. 초월/규칙파괴: spatiotemporal, conceptual, celestial, causality, logos_word
    # 4. 비-마법 이능: divine_arts (구 divine/holy_miracle), shamanic_curse (구 curse_voodoo, 혼령/자연령/토템 통합), martial_qi, physical, martial_arts, subterfuge, taming, psionics
    skill_type: str = "active"                          # active(능동) | passive(상시) | toggle(유지) | reaction(반격) | unique
    role_type: str = "single_attack"                    # single_attack | aoe_attack | heal | buff | debuff_curse | defense_guard | summon | utility
    tier: str = "common"                                # common(기초) | uncommon(숙련) | rare(비전) | epic(절기) | legendary(신화/오의)
    acquire_difficulty: str = "common"                  # 하위 호환용 난이도
    is_unique: bool = False                             # 세계 유일 스킬 여부
    owner_npc_id: str = ""                              # 고유 스킬 원본 소유자 NPC ID

    # 2. 기술 위계 & 합체기 (Rank & Joint Combo)
    rank_type: str = "normal"                           # normal(일반기) | special(비기/특수기) | ultimate(궁극기) | joint_combo(합체기)
    joint_partner_id: str = ""                          # 합체기 대상 동료/NPC ID
    joint_requirements: dict = field(default_factory=dict) # 합체기 발동 조건 (예: {"min_affinity": 60, "partner_present": True})

    # 3. 소모 자원 & 대가 (Cost & Catalyst)
    resource_type: str = "mana"                         # mana | stamina | qi | hp | corpse | reagent | faith | sanity
    resource_cost: int = 0                              # 소모량
    mana_cost: int = 0                                  # 하위 호환용 마나 소모량
    catalyst_required: str = ""                         # 필요 촉매/도구 (예: "부두 인형", "희생양의 피", "비수")
    recoil_or_side_effect: str = ""                     # 시전자 반동 (예: "시전 후 1턴간 탈진", "광기 +1")
    backfire_risk: float = 0.0                          # 대실패 자폭/역류 확률 (0.0 ~ 1.0)
    backfire_description: str = ""                      # 자폭 시 효과

    # 4. 시전 방식 & 쿨다운 (Execution & Constraints)
    cast_behavior: str = "instant"                      # instant(즉발) | charging(기 모으기) | channeling(집중) | delayed(지연)
    cast_time_turns: int = 0                            # 시전 턴수 (0 = 즉발)
    cooldown_turns: int = 0                             # 재사용 대기시간
    current_cooldown: int = 0                           # 현재 남은 쿨다운
    required_weapon: str = "무관"                       # 필요 무기군 (예: "장검", "지팡이", "활", "맨손", "무관")
    required_stance: str = ""                           # 선행 자세/태세

    # 5. 명중 & 사거리/범위 (Targeting & Range)
    hit_type: str = "dice_roll"                         # guaranteed_hit(확정 명중) | dice_roll(주사위 판정) | guided_homing(유도)
    target_type: str = "single_enemy"                   # self | single_enemy | single_ally | all_enemies | all_allies | ground_area | summon_slot
    range: str = "melee"                                # melee(근접) | short(근거리) | medium(중거리) | long(원거리) | global(전역)
    area_shape: str = "single"                          # single | cone(부채꼴) | line(직선) | circle(원형) | room(방 전체)
    area_radius_meters: float = 0.0                     # 범위 반경 (m)

    # 6. 피해/수치 & 물리 연산 (Mechanics & Scaling)
    damage_delivery: str = "single_burst"               # single_burst(단타) | multi_hit(연타) | dot_periodic(도트) | delayed_burst(지연) | reflect(반사)
    hit_count: int = 1                                  # 연타 타수
    base_value: int = 0                                 # 기본 피해/회복량
    scaling_stat: str = "str"                           # str | dex | int | wis | con | cha
    scaling_factor: float = 1.0                         # 스탯 배율
    element: str = "물리"                               # 물리 | 화염 | 빙결 | 전격 | 산성 | 신성 | 암흑 | 독 | 영혼 | 비전
    armor_penetration: float = 0.0                      # 방어 관통률 (0.0 ~ 1.0)
    effect: dict = field(default_factory=dict)          # 세부 효과 딕셔너리 (하위 호환)

    # 7. 처형 & 조건부 폭딜 (Execution Condition)
    execution_condition: dict = field(default_factory=dict) # 처형/조건부 보너스 (예: {"threshold_hp_pct": 20, "multiplier": 3.0})

    # 8. 위치 이동 & 군중 제어 (Displacement & CC)
    displacement: dict = field(default_factory=dict)        # 위치 이동 (예: {"type": "knockback", "distance_m": 5})
    inflicted_status: list[dict] = field(default_factory=list) # 상태이상 (예: [{"status": "bleeding", "duration": 3}])

    # 9. 원소/환경/날씨 연계 (Synergy & Weather/Terrain)
    synergy_tags: list[str] = field(default_factory=list)   # 연계 태그 (예: ["oil_ignite", "water_electrocute"])
    environmental_gimmick: str = ""                         # 환경 기믹 (예: "기름 점화", "수면 결빙")
    weather_terrain_synergy: dict = field(default_factory=dict) # 날씨/지형 반응 (예: {"rain": {"power_mult": 1.5}})

    # 10. 치명타 & 자원 흡수 (Crit & Drain)
    crit_multiplier_bonus: float = 0.0                  # 치명타 피해 보너스 배율
    guaranteed_crit_condition: str = ""                 # 확정 치명타 조건 (예: "stealth_ambush")
    lifesteal_pct: float = 0.0                          # 피해량 대비 HP 흡혈률
    mana_drain_pct: float = 0.0                         # 마나 흡수율

    # 11. 지속시간 & 스택 중첩 (Duration & Stacks)
    duration_turns: int = 0                             # 지속 턴수 (0 = 즉시 종료)
    max_stacks: int = 1                                 # 최대 중첩 스택 수
    current_stacks: int = 0                             # 현재 스택

    # 12. 숙련도 & 경지 (Mastery Progression)
    mastery_level: int = 1                              # 1성(초출) ~ 4성(오의)
    mastery_exp: int = 0                                # 숙련도 누적 경험치
    max_mastery_level: int = 4                          # 최대 경지

    # 13. 소음도 & 사회적 금기 (Noise & Social Taboo)
    noise_level: str = "normal"                         # silent(무소음) | quiet(속삭임) | normal(일반) | loud(굉음)
    is_forbidden: bool = False                          # 금기/불법 스킬 여부
    taboo_reason: str = ""                              # 금기 이유

    # 14. 서사 & 연출 (Flavor & GM Narration)
    description: str = ""                               # 스킬 상세 설명
    incantation: str = ""                               # 하위 호환용 영창 텍스트
    incantation_length: int = 0                         # 하위 호환용 영창 길이
    ancient_words: list[str] = field(default_factory=list) # 고대어 어휘 목록
    incantation_verse: str = ""                         # 하위 호환용 영창 구절
    incantation_or_formula: str = ""                    # 영창/심법/공식 본문
    visual_fx_description: str = ""                     # AI GM 연출 묘사 지문
    color: str = "#94a3b8"                              # 스킬 고유 테마 색상 (HEX 코드, UI/스킬북 배지/효과 연출용)
    traits: list[str] = field(default_factory=list)     # 스킬 요약 특성 태그 목록 (예: ["광역 결빙", "즉발 반격", "비기"])

    def get_visual_description(self, caster: Any = None, infused_with_mana: bool = False) -> str:
        """
        Returns narrative visual description and color/form aesthetics based on category and mana:
        - Dark Magic (흑마법): strictly black (칠흑빛/흑색).
        - Blood Magic (혈마법): strictly red (선홍빛/적색).
        - Physical Skills (물리 스킬): base grey/silver/white (회색/은색/백색). If mana-infused: caster's personal mana color.
        - Mana/Elemental Skills (마나/원소 스킬): elemental theme color + caster's personal mana color aura.
        - Others: default category/element aesthetic.
        """
        if not caster:
            return self.visual_fx_description or f"[{self.name}]의 {self.element} 기운이 뿜어져 나옵니다."

        caster_name = getattr(caster, "name", "시전자")
        caster_mana = getattr(caster, "mana_color", "푸른빛 에테르")
        caster_hex = getattr(caster, "mana_color_hex", "#38bdf8")

        cat = (getattr(self, "category", "") or "").lower()
        elem = (getattr(self, "element", "") or "").lower()
        name_l = (self.name or "").lower()
        base_desc = self.visual_fx_description or f"{self.element} 마력"

        # 1. 흑마법 (Dark/Necromancy/Shadow): 무조건 흑색
        if any(kw in cat or kw in elem or kw in name_l for kw in ["dark", "abyss", "shadow", "necromancy", "흑마법", "암흑", "사령", "칠흑", "저주"]):
            self.color = "#0f172a"
            return f"{caster_name}의 손끝에서 모든 빛을 집어삼키는 칠흑빛(흑색)의 불길한 마력이 소용돌이치며, [{self.name}]의 {base_desc}이(가) 어둠의 형상으로 발현됩니다."

        # 2. 혈마법 (Blood/Hemomancy): 무조건 빨간색
        if any(kw in cat or kw in elem or kw in name_l for kw in ["blood", "hemomancy", "혈마법", "혈액", "흡혈", "핏빛"]):
            self.color = "#dc2626"
            return f"{caster_name}의 혈관에서 뿜어져 나오는 짙은 선홍빛(빨간색) 피의 마력이 응결되어, [{self.name}]의 {base_desc}이(가) 잔혹한 핏빛 궤적으로 작렬합니다."

        # 3. 물리 스킬 (Physical Skills)
        # 3. 원소 및 특수 마법 색상 매핑 (11대 일반원소 + 4대 특수마법 + 순수마력)
        element_colors = {
            # 일반 원소 (11종)
            "fire": ("주황빛과 진홍빛 불꽃", "#f97316"),
            "화염": ("주황빛과 진홍빛 불꽃", "#f97316"),
            "불": ("주황빛과 진홍빛 불꽃", "#f97316"),
            "water": ("깊고 푸른 수류", "#0284c7"),
            "수류": ("깊고 푸른 수류", "#0284c7"),
            "물": ("깊고 푸른 수류", "#0284c7"),
            "wind": ("투명하게 일렁이는 비취빛 풍압", "#10b981"),
            "바람": ("투명하게 일렁이는 비취빛 풍압", "#10b981"),
            "earth": ("묵직하고 단단한 황갈색 암석 기운", "#a16207"),
            "대지": ("묵직하고 단단한 황갈색 암석 기운", "#a16207"),
            "땅": ("묵직하고 단단한 황갈색 암석 기운", "#a16207"),
            "lightning": ("눈부신 황금빛 뇌격과 청자색 스파크", "#eab308"),
            "뇌격": ("눈부신 황금빛 뇌격과 청자색 스파크", "#eab308"),
            "번개": ("눈부신 황금빛 뇌격과 청자색 스파크", "#eab308"),
            "ice": ("서늘한 빙백빛 한기", "#38bdf8"),
            "빙결": ("서늘한 빙백빛 한기", "#38bdf8"),
            "얼음": ("서늘한 빙백빛 한기", "#38bdf8"),
            "light": ("눈부시게 순결한 황금빛 성광", "#fef08a"),
            "신성": ("눈부시게 순결한 황금빛 성광", "#fef08a"),
            "빛": ("눈부시게 순결한 황금빛 성광", "#fef08a"),
            "darkness": ("모든 빛을 삼키는 칠흑빛 어둠", "#1e1b4b"),
            "암흑": ("모든 빛을 삼키는 칠흑빛 어둠", "#1e1b4b"),
            "어둠": ("모든 빛을 삼키는 칠흑빛 어둠", "#1e1b4b"),
            "wood": ("생명력이 용솟음치는 녹갈색 수목 줄기", "#15803d"),
            "목둔": ("생명력이 용솟음치는 녹갈색 수목 줄기", "#15803d"),
            "나무": ("생명력이 용솟음치는 녹갈색 수목 줄기", "#15803d"),
            "식물": ("생명력이 용솟음치는 녹갈색 수목 줄기", "#15803d"),
            "metal": ("차갑고 날카로운 백은빛 쇳가루와 강철 광채", "#94a3b8"),
            "금속": ("차갑고 날카로운 백은빛 쇳가루와 강철 광채", "#94a3b8"),
            "쇠": ("차갑고 날카로운 백은빛 쇳가루와 강철 광채", "#94a3b8"),
            "철": ("차갑고 날카로운 백은빛 쇳가루와 강철 광채", "#94a3b8"),
            "poison": ("불길하게 피어오르는 보랏빛 맹독 연무", "#7e22ce"),
            "독": ("불길하게 피어오르는 보랏빛 맹독 연무", "#7e22ce"),
            "맹독": ("불길하게 피어오르는 보랏빛 맹독 연무", "#7e22ce"),
            # 특수 마법 (4종)
            "sonic": ("공기를 찢는 투명한 고주파 파동과 파쇄 진동", "#06b6d4"),
            "음파": ("공기를 찢는 투명한 고주파 파동과 파쇄 진동", "#06b6d4"),
            "spatiotemporal": ("시공간의 좌표가 일그러지는 흑백 아지랑이 잔상", "#6366f1"),
            "시공간": ("시공간의 좌표가 일그러지는 흑백 아지랑이 잔상", "#6366f1"),
            "gravity": ("공간을 짓누르고 왜곡하는 보랏빛 중력장 왜곡 구체", "#4c1d95"),
            "중력": ("공간을 짓누르고 왜곡하는 보랏빛 중력장 왜곡 구체", "#4c1d95"),
            "void_chaos": ("마력을 소멸시키고 무작위 원소를 폭발시키는 검붉은 공허혼돈의 심연", "#0f172a"),
            "공허": ("마력을 소멸시키고 무작위 원소를 폭발시키는 검붉은 공허혼돈의 심연", "#0f172a"),
            "혼돈": ("마력을 소멸시키고 무작위 원소를 폭발시키는 검붉은 공허혼돈의 심연", "#0f172a"),
            "공허혼돈": ("마력을 소멸시키고 무작위 원소를 폭발시키는 검붉은 공허혼돈의 심연", "#0f172a"),
            # 무속성 순수 마력
            "arcane": ("영롱하고 투명한 청백색 순수 에테르 파륜", "#60a5fa"),
            "순수마력": ("영롱하고 투명한 청백색 순수 에테르 파륜", "#60a5fa"),
            "에테르": ("영롱하고 투명한 청백색 순수 에테르 파륜", "#60a5fa"),
        }
        is_elemental = elem in element_colors or cat in ["elemental_magic", "arcane_magic", "원소마법", "특수마법"]
        is_physical = (
            (cat in ["physical", "martial_arts", "subterfuge", "순수무예", "격투무술", "암습/은밀"] and not is_elemental) or
            elem in ["physical", "none", "물리", "타격", "참격", "관통", "체술"] or
            (getattr(self, "resource_type", "") == "stamina" and not is_elemental)
        )
        if is_physical and not (getattr(self, "mana_cost", 0) > 0 or infused_with_mana):
            # 순수 물리: 기본 회색, 은색, 백색
            self.color = "#e2e8f0"
            return f"{caster_name}의 날카로운 기합과 함께 서늘한 은백색(회색·은색·백색) 칼바람 궤적이 대기를 가르며, [{self.name}]의 {base_desc}이(가) 묵직한 물리적 파괴력으로 내리꽂힙니다."
        elif is_physical and (getattr(self, "mana_cost", 0) > 0 or infused_with_mana):
            # 물리 + 마나 부여: 시전자 고유 마나 색상
            self.color = caster_hex
            return f"{caster_name}의 무구에 본인의 고유한 '{caster_mana}' 기운이 휘감기며, [{self.name}]의 {base_desc} 위로 화려한 마나의 잔상이 뿜어져 나옵니다."

        # 4. 마나/원소 스킬: 속성 색깔 + 본인 마나 색깔 혼합
        elem_name, elem_hex = element_colors.get(elem, ("찬란한 원소 마력", "#a855f7"))
        self.color = elem_hex
        return f"{caster_name}의 고유한 '{caster_mana}' 기운이 {elem_name}과(와) 한데 뒤섞여, [{self.name}]의 {base_desc}이(가) 시전자만의 독특한 색조와 소용돌이치는 마력의 형상으로 격발됩니다."


@dataclass
class Title:
    id: str
    name: str                           # Korean
    description: str                    # Korean
    stat_bonuses: dict = field(default_factory=dict)  # {'crit_rate': 5, 'strength': 2}
    is_unique: bool = True              # Only 1 holder per world
    acquired_turn: int = 0


@dataclass
class ItemVisualProfile:
    """
    Granular visual anatomy and finish profile for weapons, armor, and gear.
    Prevents visual drift in AI image generation across turns.
    """
    blade_or_head: str = ""          # 날/타격부 형상 (예: "혈조(Fuller)가 파인 양날 직검", "완만한 곡선의 단면도", "육중한 쐐기형 강철 해머 헤드")
    guard_and_hilt: str = ""         # 코등이/가드/손잡이 (예: "황동 사자 머리 가드와 흑가죽 손잡이", "원형 흑철 코등이")
    finish_and_material: str = ""    # 마감/재질 (예: "물결치는 다마스쿠스 강철 무늬", "거친 단조 흑철", "고대 룬 각인 은도금")
    glow_or_aura: str = ""           # 마력 오라/발광 (예: "칼날을 타고 흐르는 은은한 푸른빛 에테르 기운", "불꽃 아지랑이")
    sheath_appearance: str = ""      # 칼집/거치대 외형 (예: "놋쇠 띠를 두른 흑가죽 칼집", "금속 보강 목재 칼집")
    wear_condition: str = ""         # 마모 상태 (예: "면도날처럼 시퍼렇게 연마된 날", "거친 교전의 미세한 이 빠짐")
    traits: list[str] = field(default_factory=lambda: ["무기 조형", "칼날 형상", "장비 디테일"])

    def to_korean_summary(self) -> str:
        parts = []
        if self.blade_or_head:
            parts.append(f"날/헤드: {self.blade_or_head}")
        if self.guard_and_hilt:
            parts.append(f"가드/손잡이: {self.guard_and_hilt}")
        if self.finish_and_material:
            parts.append(f"재질: {self.finish_and_material}")
        if self.glow_or_aura:
            parts.append(f"오라: {self.glow_or_aura}")
        if self.sheath_appearance:
            parts.append(f"칼집: {self.sheath_appearance}")
        if self.wear_condition:
            parts.append(f"상태: {self.wear_condition}")
        return " | ".join(parts) if parts else ""

    def to_prompt_keywords(self) -> str:
        kw = []
        if self.blade_or_head:
            b_map = {
                "혈조": "double-edged straight blade with deep fuller groove",
                "직검": "straight double-edged blade",
                "곡도": "curved single-edge blade",
                "해머": "heavy flanged warhammer head",
                "도끼": "bearded battleaxe head",
                "창": "leaf-shaped spearhead",
            }
            mapped = next((v for k, v in b_map.items() if k in self.blade_or_head), self.blade_or_head)
            kw.append(mapped)
        if self.guard_and_hilt:
            g_map = {
                "사자": "lion-headed ornate brass crossguard and leather-wrapped hilt",
                "십자": "steel crossguard with leather grip",
                "코등이": "circular iron tsuba guard",
            }
            mapped = next((v for k, v in g_map.items() if k in self.guard_and_hilt), self.guard_and_hilt)
            kw.append(mapped)
        if self.finish_and_material:
            f_map = {
                "다마스쿠스": "flowing damascus steel wave patterns",
                "흑철": "rough forged dark iron finish",
                "룬": "ancient glowing runic engravings on silver blade",
                "은도금": "silver-plated mirror finish",
            }
            mapped = next((v for k, v in f_map.items() if k in self.finish_and_material), self.finish_and_material)
            kw.append(mapped)
        if self.glow_or_aura:
            a_map = {
                "푸른": "ethereal faint blue aura radiating along the blade",
                "화염": "flickering flame aura radiating heat distortion",
                "칠흑": "wisps of dark shadowy smoke clinging to blade",
            }
            mapped = next((v for k, v in a_map.items() if k in self.glow_or_aura), self.glow_or_aura)
            kw.append(mapped)
        if self.sheath_appearance:
            s_map = {
                "흑가죽": "black leather scabbard with brass fittings",
                "목재": "polished hardwood scabbard with steel bands",
            }
            mapped = next((v for k, v in s_map.items() if k in self.sheath_appearance), self.sheath_appearance)
            kw.append(mapped)
        if self.wear_condition:
            w_map = {
                "면도날": "razor-sharp polished edge",
                "이 빠짐": "battle-worn notched edge with faint scratch marks",
                "녹슨": "weathered rusted surface with ancient wear",
            }
            mapped = next((v for k, v in w_map.items() if k in self.wear_condition), self.wear_condition)
            kw.append(mapped)
        return ", ".join(kw) if kw else ""


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
    weight: float = 1.0             # kg (내부 실제 물리 무게)
    weight_revealed: bool = False   # 관찰/감정 성공 시 실제 kg 노출 (무게 안개)
    size: str = "small"             # "small" (가방 가능), "medium" (손에 들기 가능), "heavy" (괴력 필요), "massive" (건물/기둥)
    required_strength: int = 10     # 들거나 휘두르기 위한 최소 근력 (STR)
    can_store_in_bag: bool = True   # 가방 수납 가능 여부 (small만 True)
    can_wield_as_weapon: bool = True # 즉석 무기 활용 가능 여부
    improvised_damage: int = 2      # 즉석 무기로 사용할 때의 기본 피해량
    document_text: str = ""         # 전단지, 벽보, 서적 등의 읽을 수 있는 본문
    utility_function: str = ""      # 기믹형 유틸리티 기능 (예: "벽 투과 도청", "10분간 짙은 연막 살포", "도어 락픽")
    puzzle_hint: str = ""           # 퍼즐 및 환경 상호작용 힌트

    # Durability & Rune Sockets
    durability: int = 100           # 현재 내구도 (0~100)
    max_durability: int = 100       # 최대 내구도
    rune_slots: int = 0             # 룬 소켓 구멍 개수 (0~3)
    socketed_runes: list[str] = field(default_factory=list) # 각인된 룬 ID 목록
    traits: list[str] = field(default_factory=list) # 아이템 요약 특성 태그 목록 (예: ["명품 장인의 각인", "고대 유물", "밀수품"])

    # Material Physics & Universal Object Durability
    material: str = "wood"          # "wood" | "stone" | "paper" | "glass" | "cloth" | "leather" | "metal" | "precious_metal" | "clay" | "flesh" | "structure_wood" | "structure_stone"
    hardness: float = 0.0           # 0.0이면 재질 기본값 상속 (피해 감쇠치)
    flammability: float = 1.0       # 인화율 배율 (1.0 = 표준, 3.0 = 종이/초인화, 0.0 = 불연성)
    is_destroyed: bool = False      # 내구도 0 도달 시 파괴 여부
    stored_items: list[str] = field(default_factory=list) # 상자/가구/보관함 내부 수납 아이템 ID 목록

    # Physical Combat Mechanics
    draw_weight_lbs: float = 0.0          # 활/쇠뇌 장력 (lbs, 예: 40~150 lbs)
    windup_seconds: float = 0.0           # 공격 준비 선딜레이 초 (0.0이면 무기 종류별 기본값)
    stagger_power: float = 0.0            # 피격 저지력/경직 유발 수치
    physics_tags: list[str] = field(default_factory=list) # 물리 태그 (예: ["thrust", "slash", "blunt", "jab", "straight", "projectile"])
    visual: ItemVisualProfile | None = None # 무기/장비 조형 및 마감 프로필

    # Botany & Herbalism Mechanics
    true_spec_id: str = ""          # 야생 식물학 고유 도감 ID
    is_identified: bool = True      # 정밀 감별 완료 여부
    is_poisonous_lookalike: bool = False # 외형 위장 맹독 유사종 여부
    origin_target_name: str = ""    # 채집 시도했던 원래 목표 식물명

    @property
    def display_weight(self) -> str:
        """Fog of War for Weight: returns descriptive weight estimation unless precisely inspected."""
        if self.weight_revealed:
            return f"{self.weight:.1f}kg (정밀 확인됨)"
        if self.weight < 1.0:
            return "깃털처럼 가벼움 (1kg 미만 추정)"
        elif self.weight < 5.0:
            return "가볍게 손에 쥘 만함 (1~5kg 추정)"
        elif self.weight < 15.0:
            return "묵직한 무게감 (5~15kg 추정)"
        elif self.weight < 40.0:
            return "두 손으로 들어야 할 만큼 무거움 (15~40kg 추정)"
        return "괴력이 없으면 꿈쩍도 안 할 정도로 육중함 (40kg 이상 추정)"

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
            stats.append(f"무게: {self.display_weight}")
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

        if self.visual:
            v_sum = self.visual.to_korean_summary()
            if v_sum:
                lines.append(f"조형: {v_sum}")

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

    def to_korean_visual_summary(self) -> str:
        """Returns a sensory Korean summary of the item's visual anatomy and finish."""
        if self.visual:
            v_sum = self.visual.to_korean_summary()
            if v_sum:
                return f"[{self.name}] {v_sum}"
        return f"[{self.name}] {self.description}"

    def to_image_prompt_keywords(self) -> str:
        """Returns English prompt keywords for the item's visual profile."""
        if self.visual:
            v_kw = self.visual.to_prompt_keywords()
            if v_kw:
                return f"{self.name}, {v_kw}"
        return f"detailed {self.item_type} {self.name}"







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
    participants: list[str] = field(default_factory=list)          # 관련 인물 ID 목록 (플레이어, 타 NPC)
    location_id: str = ""                                          # 기억 발생 장소 ID
    tags: list[str] = field(default_factory=list)                 # 심리/사건 분류 태그 (combat, betrayal, gift 등)
    relationship_deltas: dict[str, dict[str, int]] = field(default_factory=dict) # 타겟 ID -> 태도 변화 내역
    confidence: float = 1.0                                        # 기억 신뢰도/확신 (0.0~1.0)
    source: str = "direct_observation"                             # 기억 출처 (direct_observation, rumor, deduction, lie)
    decay_rate: float = 1.0                                        # 망각 감쇠율 배율
    traits: list[str] = field(default_factory=lambda: ["episodic_memory", "psychological_trace"]) # 요약 특성 태그



@dataclass
class Faction:
    id: str
    name: str                           # 국가 또는 세력 이름 (예: "루멘 성왕국", "그림자 상단")
    system: str = "왕정"                # 정치 체제 (왕정, 공화정, 마도정 등)
    power_level: str = "강국"           # 국력/세력 규모 (강대국, 소국, 비밀결사 등)
    ruling_race: str = ""               # 지배 지성체 종족 (인간, 엘프, 드워프, 오크, 수인 등)
    taboos: list[str] = field(default_factory=list) # 사회적/종교적 금기
    relations: dict[str, str] = field(default_factory=dict) # 타 세력과의 관계 {"faction_b": "적대" | "동맹" | "중립"}
    
    # 깃발 및 상징/문장 (Heraldry & Visual Identity)
    emblem_animal: str = ""             # 대표 상징 동물/환수 (예: "두 머리 독수리", "심해 크라켄", "검은 늑대")
    flag_colors: list[str] = field(default_factory=list) # 깃발 색상 (예: ["진홍색", "금색"], ["칠흑색", "은색"])
    flag_symbol: str = ""               # 깃발 문양 형상 (예: "태양을 관통하는 은빛 검", "톱니바퀴와 닻")
    motto: str = ""                     # 세력 표어/가언 (예: "피와 쇠로 영광을", "어둠 속에서 진실을 본다")
    headquarters_location: str = ""     # 본거지/수도 위치 ID
    traits: list[str] = field(default_factory=list) # 세력 요약 특성 태그 (예: ["호전적", "비밀주의", "상업 중심"])


@dataclass
class FacialDetails:
    """
    Granular facial feature details for deterministic visual consistency in AI image generation.
    Anchors micro-features: eyelids, eyelashes, eyebrows, nose bridge, lips, cheeks/jaw, ears.
    """
    eye_lids: str = ""        # 눈꺼풀: "무쌍(monolid)", "인아웃라인 쌍꺼풀", "아웃라인 짙은 쌍꺼풀", "속쌍꺼풀"
    eye_lashes: str = ""      # 속눈썹: "길고 짙은 속눈썹", "풍성한 속눈썹", "자연스러운 속눈썹", "짧은 속눈썹"
    eyebrows: str = ""        # 눈썹: "단정한 완만한 아치형", "짙은 송충이 눈썹", "날카로운 일자 눈썹", "가늘고 고운 눈썹"
    nose_bridge: str = ""     # 콧대: "오똑하고 곧은 높은 콧대", "날렵한 버선코", "낮고 둥근 복코", "강인한 매부리코", "작고 아담한 코"
    lips_and_mouth: str = ""  # 입술/입: "도톰하고 붉은 앵두 입술", "얇고 단호한 일자 입술", "입꼬리가 살짝 올라간 입매", "도톰한 아랫입술"
    cheeks_and_jaw: str = ""  # 볼살/턱선: "통통한 볼살(젖살)", "갸름하고 날렵한 V라인 턱선", "각진 강인한 사각턱", "광대뼈가 살짝 드러난 슬림한 볼"
    ear_shape: str = ""       # 귀 모양: "둥근 귓바퀴", "끝이 뾰족한 엘프형 귀", "작고 밀착된 귀"
    traits: list[str] = field(default_factory=lambda: ["이목구비", "안면 조형", "얼굴 디테일"])

    def to_korean_summary(self) -> str:
        parts = []
        if self.nose_bridge:
            parts.append(f"콧대: {self.nose_bridge}")
        if self.eye_lids or self.eye_lashes or self.eyebrows:
            eye_feats = [f for f in [self.eyebrows, self.eye_lids, self.eye_lashes] if f]
            parts.append(f"눈매: {', '.join(eye_feats)}")
        if self.lips_and_mouth:
            parts.append(f"입술: {self.lips_and_mouth}")
        if self.cheeks_and_jaw:
            parts.append(f"얼굴형: {self.cheeks_and_jaw}")
        if self.ear_shape:
            parts.append(f"귀: {self.ear_shape}")
        return " | ".join(parts) if parts else ""

    def to_prompt_keywords(self) -> str:
        kw = []
        if self.eye_lids:
            lid_map = {
                "무쌍": "monolid eyes",
                "속쌍": "subtle hooded eyelids",
                "인아웃": "delicate in-out double eyelids",
                "아웃라인": "distinct parallel double eyelids",
                "쌍꺼풀": "double eyelids",
            }
            mapped = next((v for k, v in lid_map.items() if k in self.eye_lids), self.eye_lids)
            kw.append(mapped)
        if self.eye_lashes:
            lash_map = {
                "길": "long dark eyelashes",
                "풍성": "dense lush eyelashes",
                "짧": "short subtle eyelashes",
            }
            mapped = next((v for k, v in lash_map.items() if k in self.eye_lashes), self.eye_lashes)
            kw.append(mapped)
        if self.eyebrows:
            brow_map = {
                "아치": "neat arched eyebrows",
                "송충이": "thick bushy eyebrows",
                "일자": "straight sharp eyebrows",
                "가는": "slender delicate eyebrows",
                "가늘": "slender delicate eyebrows",
            }
            mapped = next((v for k, v in brow_map.items() if k in self.eyebrows), self.eyebrows)
            kw.append(mapped)
        if self.nose_bridge:
            nose_map = {
                "오똑": "high defined straight nose bridge",
                "버선": "refined dainty upturned nose",
                "복코": "soft rounded nose tip",
                "매부리": "prominent aquiline hooked nose",
                "작은": "petite delicate nose",
                "아담": "petite delicate nose",
            }
            mapped = next((v for k, v in nose_map.items() if k in self.nose_bridge), self.nose_bridge)
            kw.append(mapped)
        if self.lips_and_mouth:
            lip_map = {
                "앵두": "plump reddish cherry lips",
                "도톰": "full plump lips",
                "얇": "thin decisive lips",
                "올라간": "slight natural upturned smile corners",
            }
            mapped = next((v for k, v in lip_map.items() if k in self.lips_and_mouth), self.lips_and_mouth)
            kw.append(mapped)
        if self.cheeks_and_jaw:
            jaw_map = {
                "젖살": "soft youthful round cheeks with baby fat",
                "통통": "soft youthful cheeks",
                "v라인": "sharp slender V-line jawline",
                "갸름": "slender delicate jawline",
                "사각": "strong chiseled square jaw",
                "광대": "high sculpted cheekbones",
            }
            mapped = next((v for k, v in jaw_map.items() if k in self.cheeks_and_jaw.lower()), self.cheeks_and_jaw)
            kw.append(mapped)
        if self.ear_shape:
            ear_map = {
                "엘프": "pointed elven ears",
                "뾰족": "tapered pointed ears",
                "밀착": "compact ears close to head",
            }
            mapped = next((v for k, v in ear_map.items() if k in self.ear_shape), self.ear_shape)
            kw.append(mapped)
        return ", ".join(kw) if kw else ""


@dataclass
class BodyMeasurements:
    """
    Detailed physical proportions and skeletal measurements for visual consistency.
    Anchors head ratio, shoulder width, bust size, waist-hip ratio (S-curve), leg length, muscle definition.
    """
    head_ratio: float = 7.5          # 등신비 (예: 6.5, 7.0, 7.5, 8.0, 8.5등신)
    shoulder_width: str = ""         # 어깨 너비: "넓은 직각 어깨", "가냘프고 좁은 어깨", "역삼각형 벌크 어깨", "자연스러운 표준 어깨"
    bust_size: str = ""              # 흉부: "슬렌더(A컵/평평함)", "자연스러운 볼륨(B~C컵)", "풍만한 볼륨감(D~E컵)", "다부진 대흉근"
    waist_hip_ratio: str = ""        # 허리-골반 S라인: "잘록한 허리와 도드라진 골반 S라인(WHR 0.68)", "슬림 스트레이트 라인", "넓은 골반과 탄탄한 하체"
    leg_length_ratio: str = ""       # 다리 길이: "상하체 4:6 비율의 긴 롱다리", "균형 잡힌 표준 비율(5:5)", "단단하고 굵직한 하체"
    muscle_definition: str = ""      # 근육 데피니션: "선명한 복근과 잔근육", "린매스(슬림 근육)", "매끄럽고 부드러운 유선형", "벌크업 근육질", "왜소하고 마른 체형"
    traits: list[str] = field(default_factory=lambda: ["신체 치수", "체형 비율", "골격 규격"])

    def to_korean_summary(self) -> str:
        parts = []
        if self.head_ratio > 0:
            parts.append(f"{self.head_ratio:.1f}등신")
        if self.shoulder_width:
            parts.append(f"어깨: {self.shoulder_width}")
        if self.bust_size:
            parts.append(f"흉부: {self.bust_size}")
        if self.waist_hip_ratio:
            parts.append(f"골반/허리: {self.waist_hip_ratio}")
        if self.leg_length_ratio:
            parts.append(f"다리비율: {self.leg_length_ratio}")
        if self.muscle_definition:
            parts.append(f"근육: {self.muscle_definition}")
        return " | ".join(parts) if parts else ""

    def to_prompt_keywords(self) -> str:
        kw = []
        if self.head_ratio > 0:
            kw.append(f"{self.head_ratio:.1f} head-to-body proportion")
        if self.shoulder_width:
            s_map = {
                "넓은": "broad square shoulders",
                "직각": "crisp straight shoulders",
                "가냘": "narrow delicate shoulders",
                "좁은": "slender narrow shoulders",
                "역삼각": "broad athletic V-taper shoulders",
            }
            mapped = next((v for k, v in s_map.items() if k in self.shoulder_width), self.shoulder_width)
            kw.append(mapped)
        if self.bust_size:
            b_map = {
                "풍만": "voluptuous well-endowed bust",
                "d~e": "full bust size D-cup",
                "e컵": "curvaceous bust size E-cup",
                "b~c": "moderate natural bust size C-cup",
                "슬렌더": "slender petite chest A-cup",
                "평평": "flat slender chest",
                "대흉근": "defined muscular pectoral chest",
            }
            mapped = next((v for k, v in b_map.items() if k in self.bust_size.lower()), self.bust_size)
            kw.append(mapped)
        if self.waist_hip_ratio:
            w_map = {
                "잘록": "hourglass figure with narrow waist and curvy hips (0.68 WHR)",
                "s라인": "pronounced feminine S-curve hips and slim waist",
                "스트레이트": "slim straight waistline",
                "넓은 골반": "wide feminine hips and toned lower body",
            }
            mapped = next((v for k, v in w_map.items() if k in self.waist_hip_ratio.lower()), self.waist_hip_ratio)
            kw.append(mapped)
        if self.leg_length_ratio:
            l_map = {
                "롱다리": "long slender legs with 4:6 upper-to-lower body ratio",
                "4:6": "long graceful legs with 4:6 golden proportion",
                "5:5": "balanced standard leg proportions",
                "굵직": "thick sturdy legs",
            }
            mapped = next((v for k, v in l_map.items() if k in self.leg_length_ratio), self.leg_length_ratio)
            kw.append(mapped)
        if self.muscle_definition:
            m_map = {
                "복근": "toned defined abs and lean muscular definition",
                "잔근육": "lean athletic muscle tone",
                "린매스": "lean toned physique",
                "유선형": "smooth soft streamline body",
                "벌크업": "bulky heavily-muscled build",
                "왜소": "slender delicate frame",
            }
            mapped = next((v for k, v in m_map.items() if k in self.muscle_definition), self.muscle_definition)
            kw.append(mapped)
        return ", ".join(kw) if kw else ""


@dataclass
class ClothingLayer:
    """
    Ultra-detailed 5-layer visual & functional outfit structure.
    Encompasses:
    1. Body ornaments (arms/wrists, ankle/legs, face/head, neck)
    2. Layered & functional garments (innerwear, base upper/lower, waist layer/corset/harness, outerwear)
    3. Back & shoulder decorations (shoulders/pauldrons, capes/cloaks/shawls)
    4. Footwear & leg accessories (shoes/boots, socks/stockings)
    5. Storage & gear mounts (backpacks/pouches, scabbards/holsters/quivers)
    6. Garment visual profile (fabrics, color palette, fit silhouette, inner silhouette reveal)
    """
    # 1. 신체 특정 부위 장식 (Body Ornaments & Accessories)
    head_face: list[str] = field(default_factory=list)      # 안경, 단안경(모노클), 안대, 선글라스, 코걸이, 귀걸이
    neck_acc: list[str] = field(default_factory=list)       # 목걸이, 초커, 부적, 펜던트, 스카프
    arms_wrists: list[str] = field(default_factory=list)    # 팔찌, 시계, 뱅글, 아대(손목 보호대), 장갑, 완갑
    ankle_legs: list[str] = field(default_factory=list)     # 발찌, 가터벨트, 레그 워머, 가죽 각반(Greaves)

    # 2. 레이어드 및 기능성 의류 (Layered & Functional Garments)
    innerwear: list[str] = field(default_factory=list)      # 속옷, 보디수트, 은신 타이즈, 갬비슨(누비옷)
    base_upper: str = ""                                    # 셔츠, 블라우스, 튜닉
    base_lower: str = ""                                    # 바지, 슬랙스, 스커트
    waist_layer: str = ""                                   # 조끼(Vest), 코르셋, 뷔스티에, 멜빵(서스펜더), 전술 하네스, 허리띠/탄띠
    outerwear: str = ""                                     # 코트, 로브, 판금 흉갑, 재킷

    # 3. 등 및 어깨 장식 (Back & Shoulder Silhouettes)
    shoulders: str = ""                                     # 견갑(Pauldrons), 털 숄(Fur wrap)
    cape_back: str = ""                                     # 숏망토, 롱망토, 판초, 머플러

    # 4. 신발 및 풋웨어 보조 (Footwear & Legwear)
    footwear: str = ""                                      # 가죽 부츠, 군화, 샌들, 구두
    socks_stockings: str = ""                               # 니삭스, 오버니삭스, 가터 스타킹, 망사 스타킹, 면양말

    # 5. 수납 및 장비 악세서리 (Storage & Weapon Mounts)
    bags_storage: list[str] = field(default_factory=list)   # 백팩, 크로스백, 허벅지 파우치, 벨트 주머니(Pouch)
    weapon_mounts: list[str] = field(default_factory=list)  # 칼집(Scabbard), 권총집(Holster), 화살통(Quiver)

    # 6. 의복 정밀 재질, 컬러, 핏 및 비침 프로필 (Visual Garment Consistency)
    fabric_materials: dict[str, str] = field(default_factory=dict) # 부위별 원단 재질 {"outer": "두꺼운 양모", "inner": "실크"}
    color_palette: list[str] = field(default_factory=list)         # 색상 팔레트 ["칠흑빛(#1a1a1a)", "은사 자수"]
    fit_silhouette: str = ""                                       # 핏: "몸에 밀착되는 슬림핏/스킨타이트", "루즈핏", "코르셋핏"
    inner_silhouette_reveal: str = "none"                          # 속옷 실루엣 비침: "none", "faint_underwear_line", "subtle_bra_contour", "visible_panty_line", "corset_ribs_ridge"
    wear_condition: str = ""                                       # 마모/상태: "새것처럼 윤기 흐름", "오랜 방랑의 흙먼지와 해진 밑단"

    # 요약 특성 태그 (의무 탑재)
    traits: list[str] = field(default_factory=lambda: ["복식 레이어", "외형 디테일", "장비 실루엣", "의복 질감", "이너웨어 비침"])

    def to_korean_summary(self) -> str:
        """Constructs an atmospheric, natural Korean summary string of the layered outfit."""
        sections = []

        # 겉옷 & 이너웨어
        garment_parts = []
        if self.outerwear:
            garment_parts.append(f"겉옷: {self.outerwear}")
        if self.base_upper or self.base_lower:
            base_str = " / ".join(filter(None, [self.base_upper, self.base_lower]))
            garment_parts.append(f"의복: {base_str}")
        if self.waist_layer:
            garment_parts.append(f"허리/조끼: {self.waist_layer}")
        if self.innerwear:
            garment_parts.append(f"이너: {', '.join(self.innerwear)}")
        if garment_parts:
            sections.append(" | ".join(garment_parts))

        # 등 및 어깨
        silhouette_parts = []
        if self.shoulders:
            silhouette_parts.append(f"어깨: {self.shoulders}")
        if self.cape_back:
            silhouette_parts.append(f"등: {self.cape_back}")
        if silhouette_parts:
            sections.append(" | ".join(silhouette_parts))

        # 장신구류
        acc_parts = []
        if self.head_face:
            acc_parts.append(f"머리/안면: {', '.join(self.head_face)}")
        if self.neck_acc:
            acc_parts.append(f"목: {', '.join(self.neck_acc)}")
        if self.arms_wrists:
            acc_parts.append(f"손목/팔: {', '.join(self.arms_wrists)}")
        if self.ankle_legs:
            acc_parts.append(f"다리/발목: {', '.join(self.ankle_legs)}")
        if acc_parts:
            sections.append(" | ".join(acc_parts))

        # 신발 및 양말
        foot_parts = []
        if self.socks_stockings:
            foot_parts.append(self.socks_stockings)
        if self.footwear:
            foot_parts.append(self.footwear)
        if foot_parts:
            sections.append(f"발: {'에 '.join(foot_parts) if len(foot_parts) > 1 else foot_parts[0]}")

        # 수납 및 무기 거치대
        gear_parts = []
        if self.bags_storage:
            gear_parts.append(f"수납: {', '.join(self.bags_storage)}")
        if self.weapon_mounts:
            gear_parts.append(f"거치: {', '.join(self.weapon_mounts)}")
        if gear_parts:
            sections.append(" | ".join(gear_parts))

        # 정밀 재질, 컬러, 핏 및 속옷 비침
        style_parts = []
        if self.fabric_materials:
            mats = ", ".join(f"{k}: {v}" for k, v in self.fabric_materials.items())
            style_parts.append(f"원단: {mats}")
        if self.color_palette:
            style_parts.append(f"색상: {', '.join(self.color_palette)}")
        if self.fit_silhouette:
            style_parts.append(f"핏: {self.fit_silhouette}")
        if self.inner_silhouette_reveal and self.inner_silhouette_reveal != "none":
            reveal_ko_map = {
                "faint_underwear_line": "얇고 밀착된 옷감 너머 은은한 속옷 라인",
                "subtle_bra_contour": "딱 붙는 상의 위로 은근하게 드러나는 브라 윤곽",
                "visible_panty_line": "달라붙는 하의 위로 살짝 드러나는 팬티 라인",
                "corset_ribs_ridge": "의상 위로 비치는 코르셋 뼈대 굴곡 자국",
            }
            r_ko = reveal_ko_map.get(self.inner_silhouette_reveal, self.inner_silhouette_reveal)
            style_parts.append(f"비침: {r_ko}")
        if self.wear_condition:
            style_parts.append(f"상태: {self.wear_condition}")
        if style_parts:
            sections.append(" | ".join(style_parts))

        return " ❖ ".join(sections) if sections else "수수한 평복"

    def to_prompt_keywords(self) -> str:
        """Constructs rich English prompt keywords for AI image generation."""
        keywords = []
        if self.color_palette:
            keywords.append(f"color palette of {', '.join(self.color_palette)}")
        if self.fabric_materials:
            mats = ", ".join(f"{k} made of {v}" for k, v in self.fabric_materials.items())
            keywords.append(f"crafted from {mats}")
        if self.fit_silhouette:
            fit_map = {
                "스킨타이트": "skin-tight form-fitting silhouette",
                "슬림": "slim form-fitting silhouette",
                "루즈": "flowing loose-fitting silhouette",
                "오버": "oversized relaxed silhouette",
                "코르셋": "tight-laced hourglass corset silhouette",
            }
            mapped_fit = next((v for k, v in fit_map.items() if k in self.fit_silhouette), self.fit_silhouette)
            keywords.append(mapped_fit)
        if self.outerwear:
            keywords.append(f"wearing {self.outerwear}")
        if self.base_upper or self.base_lower:
            bases = [b for b in [self.base_upper, self.base_lower] if b]
            keywords.append(f"dressed in {' with '.join(bases)}")
        if self.waist_layer:
            keywords.append(f"{self.waist_layer}")
        if self.innerwear:
            keywords.append(f"layered over {', '.join(self.innerwear)}")
        if self.inner_silhouette_reveal and self.inner_silhouette_reveal != "none":
            reveal_en_map = {
                "faint_underwear_line": "faint underwear seam line visible through form-fitting fabric",
                "subtle_bra_contour": "subtle contour of innerwear bra straps visible under skin-tight top",
                "visible_panty_line": "subtle panty line contour showing through tight leggings",
                "corset_ribs_ridge": "faint corset boning ridges showing under dress",
            }
            mapped_reveal = reveal_en_map.get(self.inner_silhouette_reveal, self.inner_silhouette_reveal)
            keywords.append(mapped_reveal)
        if self.shoulders:
            keywords.append(f"{self.shoulders} on shoulders")
        if self.cape_back:
            keywords.append(f"{self.cape_back}")
        if self.head_face:
            keywords.append(f"wearing {', '.join(self.head_face)}")
        if self.neck_acc:
            keywords.append(f"{', '.join(self.neck_acc)} around neck")
        if self.arms_wrists:
            keywords.append(f"{', '.join(self.arms_wrists)}")
        if self.ankle_legs:
            keywords.append(f"{', '.join(self.ankle_legs)}")
        if self.socks_stockings:
            keywords.append(f"{self.socks_stockings}")
        if self.footwear:
            keywords.append(f"{self.footwear}")
        if self.bags_storage:
            keywords.append(f"carrying {', '.join(self.bags_storage)}")
        if self.weapon_mounts:
            keywords.append(f"equipped with {', '.join(self.weapon_mounts)}")
        if self.wear_condition:
            keywords.append(f"fabric condition: {self.wear_condition}")
        return ", ".join(keywords) if keywords else "simple traveler clothing"


@dataclass
class NPCVisualDetails:
    """
    Ultra-detailed visual anatomy for high-fidelity narration and AI Image Generation (Flux/SD).
    Supports granular species, life stages (child/teen/adult/elder), and body archetypes.
    """
    species: str = ""                            # 종족 (예: "인간", "엘프", "드워프", "수인(늑대/고양이)", "오크", "용족", "하프엘프")
    life_stage: str = ""                         # 연령 및 생애 주기 (예: "어린아이(남아)", "청소년 소녀", "성인 남성", "노인")
    build_archetype: str = ""                    # 골격/체형 유형 (예: "왜소하고 마른 체형", "근육질의 탄탄한 체형")
    height_cm: int = 0                           # 신장 (cm 단위)
    age_apparent: str = ""                       # 겉보기 나이 (예: "7~8세", "10대 중반", "20대 초반", "40대 중반", "70대 노인")
    gender: str = ""                             # 성별 (남성, 여성, 불명 등)
    height_and_build: str = ""                   # 체구 상세 묘사
    hair_color: str = ""                         # 머리 색상 (예: "칠흑빛 흑발", "은백색", "녹슨 구릿빛 붉은 머리", "백금발")
    hair_style: str = ""                         # 헤어스타일 (예: "뒤로 묶은 꽁지머리", "단정한 단발", "포마드 올백")
    eye_color: str = ""                          # 눈동자 색상 (예: "호박색(Amber)", "차가운 은회색", "벽안(푸른 눈)")
    eye_shape: str = ""                          # 눈매/크기 (예: "날카로운 삼백안", "처진 강아지상 눈매", "크고 또렷한 눈")
    skin_tone: str = ""                          # 피부 톤/질감 (예: "햇볕에 그을린 구릿빛", "창백한 백옥 피부")
    facial_features: list[str] = field(default_factory=list) # 고유 얼굴 특징 (예: ["뺨의 옅은 주근깨", "왼쪽 눈썹을 가로지르는 흉터"])
    clothing_style: str = ""                     # 의복/복식 (예: "기름때 묻은 가죽 조끼", "은사 사제 로브")
    distinctive_accessories: list[str] = field(default_factory=list) # 특이 소품/장신구 (예: ["외눈 안경", "놋쇠 나침반 목걸이"])
    posture_and_vibe: str = ""                   # 자세와 분위기 (예: "초조하게 손을 비비는 태도", "호기심 어린 눈망울")
    outfit: ClothingLayer = field(default_factory=ClothingLayer) # 5레이어 초정밀 복식 및 장비 구조체
    face_details: FacialDetails = field(default_factory=FacialDetails) # 세부 안면 이목구비 조형
    body_measurements: BodyMeasurements = field(default_factory=BodyMeasurements) # 신체 치수 및 골격 규격
    traits: list[str] = field(default_factory=lambda: ["해부학적 외형", "시각적 디테일", "복식 레이어", "신체 치수", "안면 조형"])



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

    # Extended 20-Factor Deep Human Persona System
    life_defining_moment: str = ""                                # 생애 결정적 분기점 (과거 결정적 사건)
    value_hierarchy: list[str] = field(default_factory=lambda: ["survival", "wealth", "honor", "family", "faith"]) # 가치관 우선순위
    coping_mechanism: str = ""                                    # 한계 상황 스트레스 대처 기제
    public_mask: str = ""                                         # 사회적 가면 (겉으로 연기하는 가짜 인격)
    moral_justification: str = ""                                 # 악행/선택 시 자기합리화 논리
    micro_leakage_traits: list[str] = field(default_factory=list) # 무의식적 거짓말/속내 누출 복선 버릇
    risk_tolerance: int = 50                                      # 위험 감수성 (0: 극안전 ~ 100: 도박성)
    bdi_state: dict = field(default_factory=dict)                 # 고도화 BDI 세부 계획 및 신념 메타데이터


    alive: bool = True
    level: int = 1
    health: int = 50
    max_health: int = 50
    mana: int = 30
    max_mana: int = 30
    stamina: int = 100
    max_stamina: int = 100
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
    perception: int = 10        # 감각/지각 (Perception) - 도난/기습/함정/위화감 감지
    crit_rate_bonus: int = 0
    crit_damage_bonus: int = 0
    mage_circle: int = 1        # 마법사 서클/클래스 (1~10클래스)

    @property
    def perception_stat(self) -> int: return self.perception
    @property
    def per_stat(self) -> int: return self.perception

    memories: list[MemoryEntry] = field(default_factory=list)
    stats_revealed: bool = False    # Fog of War: Hidden until combat/investigation
    name_revealed: bool = False     # Fog of War: Hidden until player asks/learns name
    alias_ko: str = ""              # Unidentified title (e.g. "선술집 주인", "과묵한 검사")
    is_legacy: bool = False         # True if this NPC is an archived past player
    legacy_id: str | None = None
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
    # 10-Factor Attitude Matrix (Symmetric Cognitive Model)
    affinity: int = 50                                            # 친밀도 (0~100)
    fear: int = 0                                                 # 공포/위압감 (0~100)
    debt: int = 0                                                 # 부채감/은혜의 빚 (-100: 원한 ~ +100: 은혜)
    trust: int = 50                                               # 신뢰도 (0~100)
    respect: int = 50                                             # 존경 vs 경멸 (0~100)
    envy: int = 0                                                 # 질투/시기 (0~100)
    pity: int = 0                                                 # 동정/연민 (0~100)
    dominance: int = 50                                           # 지배욕 vs 복종심 (0~100)
    curiosity: int = 50                                           # 호기심/탐구욕 (0~100)
    disgust: int = 0                                              # 도덕적/생리적 혐오감 (0~100)
    injuries: list[str] = field(default_factory=list)             # 신체 부위별 부상/장애
    traumas: list[str] = field(default_factory=list)              # 심리적 트라우마/PTSD
    power_dynamic_state: str = "normal"                           # 권력 공백 반응: "normal" | "subservient"(복종/우상화) | "usurper"(찬탈) | "mutiny"(내분)
    morale: int = 100                                             # 전투 사기 (0~100, 30 이하 시 패주/항복 자백 협상)
    active_infections: dict = field(default_factory=dict)         # disease_id -> ActiveInfection
    status_effects: dict = field(default_factory=dict)            # status_id -> StatusEffect
    visual: NPCVisualDetails = field(default_factory=NPCVisualDetails) # 고유 외형 해부학적 데이터
    blackmail_secret: str = ""                                    # 숨겨진 치부/약점/비리
    faction_id: str = ""                                          # 소속 세력/단체 ID
    faction_role: str = ""                                        # 세력 내 직책/신분
    mana_color: str = "창백한 푸른빛 에테르"                     # 개인 마나/오라 고유 색상 및 성질
    mana_color_hex: str = "#38bdf8"
    traits: list[str] = field(default_factory=list)               # NPC 요약 특성 태그 목록 (예: ["외눈 흉터", "주정뱅이", "실종된 기사"])
    anatomy_parts: dict = field(default_factory=dict)             # 부위 파괴용 신체 해부학적 부위 딕셔너리 {part_id: MonsterPart 또는 dict}
    harvested_parts: list[str] = field(default_factory=list)      # 이미 해체/갈무리 완료된 부위 ID 목록
    mana_burn_state: dict = field(default_factory=dict)           # 마나 회로 손상도 및 에테르 변이 상태
    circadian: dict = field(default_factory=dict)                 # 수면 결핍 및 생체 각성 시계 상태
    toxicity_state: dict = field(default_factory=dict)            # 간 독성 및 포션 내성 상태
    alcohol_state: dict = field(default_factory=dict)             # 혈중 알코올 및 취기/숙취 상태
    posture_state: dict = field(default_factory=dict)             # 체간/강인도 및 가드 브레이크 상태
    pupil_state: dict = field(default_factory=dict)               # 동공 조도 암적응/명적응 상태
    # NPC Psychology Architecture (Master Brief Spec)
    emotion_state: dict = field(default_factory=dict)             # 활성 복합 감정 인스턴스 {emotion_name: {intensity, source, duration, decay}}
    stress: int = 0                                               # 심리적 스트레스 (0~100, 피로도/사기와 독립)
    relationship_map: dict[str, dict] = field(default_factory=dict) # 다자간 9축 관계 맵 {entity_id: {trust, affection, respect, fear, resentment, dependence, loyalty, suspicion, familiarity}}
    archetype_template: str = ""                                  # 성격 템플릿 아키타입 참조 ID (디버그/초기화 전용)
    eval_tier: int = 1                                            # 3-Tier 평가 라우팅 상태 (1: 루틴, 2: 국소 감지, 3: 직접 상호작용)
    last_eval_tick: int = 0                                       # 마지막 평가 틱/턴
    decision_cache_key: str = ""                                  # 결정 캐시 검증 키
    decision_cache_result: dict = field(default_factory=dict)     # 결정 캐시된 최근 판단 결과
    state_version: int = 0                                        # 심리 상태 변경 버전 카운터 (캐시 무효화용)
    trauma_runtime: dict = field(default_factory=dict)            # 런타임 트라우마 활성화 상태 {trauma_tag: {active, intensity, ...}}


    def to_image_prompt_keywords(self) -> str:
        """Generates rich, consistent English keywords for AI image generation (Flux, Stable Diffusion, etc.)."""
        v = self.visual
        features_parts = list(v.facial_features) if v.facial_features else []
        if hasattr(v, "face_details") and v.face_details:
            f_kw = v.face_details.to_prompt_keywords()
            if f_kw:
                features_parts.append(f_kw)
        features_en = ", ".join(features_parts) if features_parts else "detailed facial features"

        body_parts = []
        if v.height_cm > 0:
            body_parts.append(f"{v.height_cm}cm")
        if v.build_archetype:
            body_parts.append(v.build_archetype)
        if hasattr(v, "body_measurements") and v.body_measurements:
            b_kw = v.body_measurements.to_prompt_keywords()
            if b_kw:
                body_parts.append(b_kw)
        body_en = " ".join(body_parts) if body_parts else "medium build"

        acc_en = ", ".join(v.distinctive_accessories) if v.distinctive_accessories else "detailed accessories"
        outfit_en = v.outfit.to_prompt_keywords() if (hasattr(v, "outfit") and v.outfit and any([
            v.outfit.outerwear, v.outfit.base_upper, v.outfit.base_lower,
            v.outfit.waist_layer, v.outfit.innerwear, v.outfit.shoulders,
            v.outfit.cape_back, v.outfit.footwear, v.outfit.bags_storage,
            v.outfit.weapon_mounts, v.outfit.head_face, v.outfit.neck_acc,
            v.outfit.arms_wrists, v.outfit.ankle_legs, v.outfit.socks_stockings,
            getattr(v.outfit, "fabric_materials", None), getattr(v.outfit, "color_palette", None),
            getattr(v.outfit, "fit_silhouette", ""), getattr(v.outfit, "inner_silhouette_reveal", "") != "none"
        ])) else (f"wearing {v.clothing_style}" if v.clothing_style else "wearing traveler clothing")
        return (
            f"cinematic fantasy portrait of {v.species} {v.life_stage} {self.job}, {v.age_apparent}, "
            f"{body_en}, {v.hair_color} {v.hair_style}, {v.eye_shape} with {v.eye_color} eyes, "
            f"{v.skin_tone}, {features_en}, {outfit_en}, {acc_en}, {v.posture_and_vibe}, "
            f"highly detailed face, realistic skin texture, intricate clothing folds, volumetric lighting, masterpiece, 8k"
        )

    def to_korean_visual_summary(self) -> str:
        """Returns a high-density sensory Korean summary of the NPC's physical appearance."""
        v = self.visual
        feat_parts = []
        if v.facial_features:
            feat_parts.append(f"특징: {', '.join(v.facial_features)}")
        face_str = v.face_details.to_korean_summary() if (hasattr(v, "face_details") and v.face_details) else ""
        if face_str:
            feat_parts.append(face_str)
        acc_str = f"소품: {', '.join(v.distinctive_accessories)}" if v.distinctive_accessories else ""
        if acc_str:
            feat_parts.append(acc_str)
        extras = " | ".join(filter(None, feat_parts))
        extras_part = f" ({extras})" if extras else ""

        species_str = f"{v.species} {v.life_stage}".strip() if (v.species or v.life_stage) else "인물"
        height_str = f"{v.height_cm}cm " if v.height_cm > 0 else ""
        build_str = v.build_archetype or "보통 체형"
        body_str = v.body_measurements.to_korean_summary() if (hasattr(v, "body_measurements") and v.body_measurements) else ""
        if body_str:
            build_str = f"{build_str}[{body_str}]"
        age_str = f"(겉보기 {v.age_apparent})" if v.age_apparent else ""
        hair_str = f"{v.hair_color} {v.hair_style}".strip() if (v.hair_color or v.hair_style) else ""
        eye_str = f"{v.eye_shape}({v.eye_color} 눈동자)" if (v.eye_shape and v.eye_color) else (f"{v.eye_color} 눈동자" if v.eye_color else (v.eye_shape or ""))
        skin_str = v.skin_tone or ""
        outfit_summary = v.outfit.to_korean_summary() if (hasattr(v, "outfit") and v.outfit and any([
            v.outfit.outerwear, v.outfit.base_upper, v.outfit.base_lower,
            v.outfit.waist_layer, v.outfit.innerwear, v.outfit.shoulders,
            v.outfit.cape_back, v.outfit.footwear, v.outfit.bags_storage,
            v.outfit.weapon_mounts, v.outfit.head_face, v.outfit.neck_acc,
            v.outfit.arms_wrists, v.outfit.ankle_legs, v.outfit.socks_stockings,
            getattr(v.outfit, "fabric_materials", None), getattr(v.outfit, "color_palette", None),
            getattr(v.outfit, "fit_silhouette", ""), getattr(v.outfit, "inner_silhouette_reveal", "") != "none"
        ])) else (v.clothing_style or "")

        parts = [
            f"{height_str}{build_str}{age_str}".strip(),
            hair_str,
            eye_str,
            skin_str,
            outfit_summary
        ]
        desc_core = ", ".join(filter(None, parts)) or "보통 체형"
        return f"[{species_str} / {self.job}] {desc_core}{extras_part}"

    # Properties symmetric with Player
    @property
    def effective_strength(self) -> int:
        from src.world.status_engine import StatusEffectEngine
        return max(1, self.strength + StatusEffectEngine.get_effective_stat_modifiers(self).get("strength", 0))

    @property
    def effective_agility(self) -> int:
        from src.world.status_engine import StatusEffectEngine
        return max(1, self.agility + StatusEffectEngine.get_effective_stat_modifiers(self).get("agility", 0))

    @property
    def effective_intelligence(self) -> int:
        from src.world.status_engine import StatusEffectEngine
        return max(1, self.intelligence + StatusEffectEngine.get_effective_stat_modifiers(self).get("intelligence", 0))

    @property
    def str_mod(self) -> int: return (self.effective_strength - 10) // 2
    @property
    def agi_mod(self) -> int: return (self.effective_agility - 10) // 2
    @property
    def int_mod(self) -> int: return (self.effective_intelligence - 10) // 2 + max(0, (self.wisdom - 10) // 2)
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
        penalty = 0
        if hasattr(self, "mana_burn_state") and isinstance(self.mana_burn_state, dict):
            penalty = self.mana_burn_state.get("max_mp_penalty", 0)
        return max(0, self.max_mana + max(0, self.intelligence - 10) * 5 - penalty)
    @property
    def max_stamina_effective(self) -> int:
        from src.world.stamina_engine import StaminaEngine
        return StaminaEngine.calculate_max_stamina(self)
    @property
    def stamina_regen_effective(self) -> int:
        from src.world.stamina_engine import StaminaEngine
        return StaminaEngine.calculate_regen_rate(self)

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

    def prune_memories(self, current_turn: int, decay_turns: int = 20) -> list[MemoryEntry]:
        """
        Prunes insignificant memories (significance 1-2) after decay_turns of no interaction.
        Significance >= 3 or is_anchor=True are kept indefinitely.
        Returns list of removed memories.
        """
        kept: list[MemoryEntry] = []
        removed: list[MemoryEntry] = []
        for m in self.memories:
            if m.is_anchor or m.significance >= 3 or (current_turn - m.turn) <= decay_turns:
                kept.append(m)
            else:
                removed.append(m)
        self.memories = kept
        return removed

    def get_recent_off_screen_logs(self, max_logs: int = 5) -> list[str]:
        """Deterministic reader for off-screen activity logs."""
        return self.off_screen_logs[-max_logs:] if self.off_screen_logs else []

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
    visited: bool = False
    coordinates: tuple[float, float] = (0.0, 0.0) # (X_km, Y_km)
    terrain: str = "plains"                        # "plains", "mountains", "forest", "swamp", "urban", "desert"
    security_level: int = 50                       # 치안도 (0~100)
    roads: dict = field(default_factory=dict)      # destination_id -> RoadConnection
    location_category: str = "surface"             # "surface", "dungeon", "hidden_realm"
    dungeon_id: str | None = None               # 귀속된 던전 인스턴스 ID (있는 경우)
    floor_depth: int = 0                           # 층수 심도 (0: 지상, 1~N: 지하 층수)
    monster_density: int = 20                      # 몬스터 출현 밀집도 (0~100)
    npc_density: int = 50                          # 일반 주민/NPC 밀집도 (0~100)
    danger_level: int = 20                         # 위험도 등급 (0~100)
    traps: list[str] = field(default_factory=list) # 해당 구역에 설치/잠복된 함정 인스턴스 ID 목록
    traits: list[str] = field(default_factory=list) # 장소 요약 특성 태그 (예: ["어둠", "피비린내", "엄폐물 풍부"])
    rock_strata: str = "granite"                    # 암반 지질 ("limestone", "granite", "sandstone", "basalt", "obsidian")
    structural_integrity: float = 100.0             # 암반 구조적 내구도 (0.0~120.0)
    collapse_stage: str = "stable"                  # 낙반 붕괴 단계 ("stable", "cracking", "partial_collapse", "full_collapse")
    floor_type: str = "solid_rock"                  # 지면 유형 ("solid_rock", "weathered_rock", "rotten_wood", "thin_crust", "ice_floor")
    floor_durability: float = 100.0                 # 지면 내구도
    floor_collapse_stage: str = "stable"            # 지면 균열/붕괴 상태 ("stable", "crack", "partial_break", "full_break")
    ventilation_open: bool = False                  # 환기구 개방 여부
    active_toxic_gas: str | None = None          # 활성 유독 가스 ("carbon_dioxide", "sulfur_gas", "corpse_gas", "spore_cloud")
    water_quality: str = "clean"                    # 지하수 수질 ("clean", "stagnant", "sewage", "corpse_contaminated", "mineral_toxic")




@dataclass
class EnvironmentalMetrics:
    weather: str = "맑음"                   # "맑음", "폭우", "농무", "모래폭풍", "폭설", "산성비"
    lighting: str = "적당한 밝기"            # "칠흑 같은 어둠", "희미한 등불", "적당한 밝기", "눈부신 분광"
    smell: str = ""
    noise: str = ""
    oxygen_level: int = 100                 # 산소 농도 (%)
    time_of_day: str = "낮"                 # "새벽", "낮", "황혼", "심야"
    hazard_level: int = 0                   # 환경 위험도 (0~100)
    market_inflation: dict[str, float] = field(default_factory=dict) # 아이템 카테고리별 물가 배율
    scent_trace: str = ""                   # 잔류 냄새 흔적 (예: "피비린내 누적", "그을음과 탄내")
    ambient_noise_occlusion: str = "일반"    # 음향 차폐 상태 (예: "폭포 굉음으로 외부 소음 차폐", "두꺼운 철문 차폐")
    temperature_celsius: int = 20           # 환경 온도 (섭씨)

    def to_anchoring_text(self) -> str:
        parts = [
            f"시간: {self.time_of_day}",
            f"날씨: {self.weather}",
            f"조도: {self.lighting}",
        ]
        if self.smell:
            parts.append(f"냄새: {self.smell}")
        if self.noise:
            parts.append(f"소음: {self.noise}")
        parts.append(f"산소 농도: {self.oxygen_level}%")
        return "[🌿 현재 환경 앵커링] " + " | ".join(parts)


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
    stamina: int = 100
    max_stamina: int = 100
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
    perception: int = 10        # 감각/지각 - 기습/소매치기/복선/위화감/함정 탐지
    
    # Equipment
    equipment: EquipmentSlots = field(default_factory=EquipmentSlots)
    
    # Skills and titles
    skills: list[str] = field(default_factory=list)   # skill ids
    titles: list[str] = field(default_factory=list)   # title ids
    active_title: str | None = None
    
    # Known magic language vocabulary
    known_magic_words: list[str] = field(default_factory=list)
    
    reputation: int = 0
    regional_reputation: dict[str, int] = field(default_factory=dict) # 지역별 국소 명성 {loc_id: rep}
    known_facts: list[str] = field(default_factory=list)
    fatigue: int = 0                    # 피로도 (0~100)
    time_elapsed_minutes: int = 0       # 누적 인게임 시간 (분)
    injuries: list[str] = field(default_factory=list) # 신체 부위별 부상/장애 (예: ["오른팔 골절 (명중-3)"])
    splinted_injuries: dict[str, int] = field(default_factory=dict) # 부목 고정된 골절 부상 및 완치까지 필요한 휴식 횟수
    unnoticed_thefts: list[dict] = field(default_factory=list) # 아직 눈치채지 못한 도난 내역
    traumas: list[str] = field(default_factory=list)  # 심리적 트라우마 (예: ["화염 공포증"])
    hygiene_level: int = 100            # 위생도 (0~100, 30 이하 시 체취 누출로 야수 기습 유발)
    body_temperature: float = 36.5      # 심부 체온 (34도 이하 저체온증, 39도 이상 열사병)
    wetness: float = 0.0                # 젖음 수치 (0.0: 완전 건조 ~ 100.0: 완전 침수)
    thermal_status: str = "normal"      # 체온 상태 ("normal", "mild_hypothermia", "moderate_hypothermia", "severe_hypothermia", "fatal_hypothermia", "heat_exhaustion", "heat_cramps", "heat_stroke", "multi_organ_failure")
    active_infections: dict = field(default_factory=dict) # disease_id -> ActiveInfection
    status_effects: dict = field(default_factory=dict) # status_id -> StatusEffect
    
    # Bounty & Disguise
    bounties: dict[str, int] = field(default_factory=dict) # 세력별 수배 현상금 {"faction_lumen": 1500}
    disguise: str | None = None                         # 착용 중인 변장 도구 (예: "까마귀 가면과 검은 로브")
    active_alias: str | None = None                     # 통성명용 가명 (예: "외눈의 방랑자 잭")
    mana_color: str = "푸른빛 에테르"                            # 개인 마나/오라 고유 색상 및 성질
    mana_color_hex: str = "#38bdf8"
    traits: list[str] = field(default_factory=list)        # 플레이어 요약 특성 태그 목록 (예: ["불사의 각인", "고대어 해독가"])
    sub_stats: dict[str, float] = field(default_factory=dict) # 무한 확장 서브스탯 딕셔너리
    poise: float = 0.0                                     # 기본 강인도 (피격 저지력 내성)
    equipment_defense: int = 0
    equipment_stat_bonuses: dict = field(default_factory=dict)
    equipment_active_set_bonuses: list = field(default_factory=list)
    equipment_active_traits: list[str] = field(default_factory=list)
    mage_circle: int = 1                                   # 마법사 서클/클래스 (1~10클래스, 영창 고대어 단어 수 상한선 결정)
    mana_burn_state: dict = field(default_factory=dict)    # 마나 회로 손상도 및 에테르 변이 상태
    circadian: dict = field(default_factory=dict)          # 수면 결핍 및 생체 각성 시계 상태
    toxicity_state: dict = field(default_factory=dict)     # 간 독성 및 포션 내성 상태
    alcohol_state: dict = field(default_factory=dict)      # 혈중 알코올 및 취기/숙취 상태
    posture_state: dict = field(default_factory=dict)      # 체간/강인도 및 가드 브레이크 상태
    pupil_state: dict = field(default_factory=dict)        # 동공 조도 암적응/명적응 상태
    is_stealthed: bool = False                             # 물리 은신/잠입 성공 상태
    visual: NPCVisualDetails = field(default_factory=NPCVisualDetails)
    
    @property
    def max_incantation_words(self) -> int:
        """Maximum ancient words combinable in a single spell incantation based on mage circle."""
        # 1-class = 2 words ([원소] + [기동])
        # 2-class = 3 words ([원소] + [형태] + [기동])
        # 3-class = 4 words ... up to 10-class = 10 words
        return min(10, max(2, self.mage_circle + 1))

    @property
    def outfit(self) -> ClothingLayer:
        return self.visual.outfit

    def to_korean_visual_summary(self) -> str:
        """Returns a high-density sensory Korean summary of the Player's physical appearance and outfit."""
        v = self.visual
        outfit_summary = v.outfit.to_korean_summary() if (hasattr(v, "outfit") and v.outfit and any([
            v.outfit.outerwear, v.outfit.base_upper, v.outfit.base_lower,
            v.outfit.waist_layer, v.outfit.innerwear, v.outfit.shoulders,
            v.outfit.cape_back, v.outfit.footwear, v.outfit.bags_storage,
            v.outfit.weapon_mounts, v.outfit.head_face, v.outfit.neck_acc,
            v.outfit.arms_wrists, v.outfit.ankle_legs, v.outfit.socks_stockings,
            getattr(v.outfit, "fabric_materials", None), getattr(v.outfit, "color_palette", None),
            getattr(v.outfit, "fit_silhouette", ""), getattr(v.outfit, "inner_silhouette_reveal", "") != "none"
        ])) else (v.clothing_style or "평범한 모험가 복장")
        title_str = f"[{self.active_title}] " if self.active_title else ""
        body_str = v.body_measurements.to_korean_summary() if (hasattr(v, "body_measurements") and v.body_measurements) else ""
        face_str = v.face_details.to_korean_summary() if (hasattr(v, "face_details") and v.face_details) else ""
        phys_parts = [p for p in [body_str, face_str] if p]
        phys_summary = f" ({' / '.join(phys_parts)})" if phys_parts else ""
        return f"{title_str}{self.name}{phys_summary} - {outfit_summary}"

    def to_image_prompt_keywords(self) -> str:
        """Generates rich keywords for AI image generation of Player."""
        v = self.visual
        outfit_en = v.outfit.to_prompt_keywords() if (hasattr(v, "outfit") and v.outfit) else "traveler clothing"
        body_en = v.body_measurements.to_prompt_keywords() if (hasattr(v, "body_measurements") and v.body_measurements) else ""
        face_en = v.face_details.to_prompt_keywords() if (hasattr(v, "face_details") and v.face_details) else ""
        parts = [f"cinematic fantasy portrait of protagonist {self.name}"]
        if body_en:
            parts.append(body_en)
        if face_en:
            parts.append(face_en)
        parts.append(outfit_en)
        parts.append("volumetric lighting, highly detailed, 8k")
        return ", ".join(parts)

    @property
    def fatigue_status_ko(self) -> str:
        if self.fatigue >= 80:
            return "탈진 (호흡 곤란, 주사위 판정 -3 디메리트, 마력 통제 저하)"
        elif self.fatigue >= 50:
            return "피로 (호흡 가쁨, 주사위 판정 -1 디메리트)"
        elif self.fatigue >= 20:
            return "경미한 피로"
        elif self.fatigue == 0:
            return "양호 (피로도 0: 완벽한 휴식, 주사위 판정 +1 메리트)"
        return "양호 (활력 넘침)"

    @property
    def max_stamina_effective(self) -> int:
        from src.world.stamina_engine import StaminaEngine
        return StaminaEngine.calculate_max_stamina(self)

    @property
    def stamina_regen_effective(self) -> int:
        from src.world.stamina_engine import StaminaEngine
        return StaminaEngine.calculate_regen_rate(self)

    @property
    def stamina_status_ko(self) -> str:
        ratio = self.stamina / max(1, self.max_stamina_effective)
        if ratio <= 0.0:
            return "탈진 (신체 행동 불능 및 방어력 약화)"
        elif ratio <= 0.25:
            return "헐떡임 (기력 바닥, 무거운 기술 사용 불가)"
        elif ratio <= 0.6:
            return "숨참 (호흡 가쁨)"
        return "완전 (기력 충만)"

    equipment_defense: int = 0
    equipment_stat_bonuses: dict = field(default_factory=dict)

    # Effective Stats with Status Effects & Equipment
    @property
    def effective_strength(self) -> int:
        from src.world.status_engine import StatusEffectEngine
        eq_b = self.equipment_stat_bonuses.get("strength", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        return max(1, self.strength + StatusEffectEngine.get_effective_stat_modifiers(self).get("strength", 0) + eq_b)

    @property
    def effective_agility(self) -> int:
        from src.world.status_engine import StatusEffectEngine
        eq_b = self.equipment_stat_bonuses.get("agility", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        alc_penalty = 0
        if hasattr(self, "alcohol_state") and isinstance(self.alcohol_state, dict):
            if self.alcohol_state.get("intoxication_stage", 0) >= 2:
                alc_penalty = 3
        return max(1, self.agility + StatusEffectEngine.get_effective_stat_modifiers(self).get("agility", 0) + eq_b - alc_penalty)

    @property
    def effective_constitution(self) -> int:
        from src.world.status_engine import StatusEffectEngine
        eq_b = self.equipment_stat_bonuses.get("constitution", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        return max(1, self.constitution + StatusEffectEngine.get_effective_stat_modifiers(self).get("constitution", 0) + eq_b)

    @property
    def effective_intelligence(self) -> int:
        from src.world.status_engine import StatusEffectEngine
        eq_b = self.equipment_stat_bonuses.get("intelligence", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        alc_penalty = 0
        if hasattr(self, "alcohol_state") and isinstance(self.alcohol_state, dict):
            if self.alcohol_state.get("has_hangover", False):
                alc_penalty = 2
        return max(1, self.intelligence + StatusEffectEngine.get_effective_stat_modifiers(self).get("intelligence", 0) + eq_b - alc_penalty)

    # Properties
    @property
    def str_stat(self) -> int: return self.effective_strength

    @str_stat.setter
    def str_stat(self, value: int): self.strength = value
    @property
    def dex_stat(self) -> int: return self.effective_agility
    @dex_stat.setter
    def dex_stat(self, value: int): self.agility = value
    @property
    def con_stat(self) -> int: return self.effective_constitution
    @con_stat.setter
    def con_stat(self, value: int): self.constitution = value
    @property
    def int_stat(self) -> int: return self.effective_intelligence
    @int_stat.setter
    def int_stat(self, value: int): self.intelligence = value
    @property
    def wis_stat(self) -> int:
        eq_b = self.equipment_stat_bonuses.get("wisdom", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        return self.wisdom + eq_b
    @wis_stat.setter
    def wis_stat(self, value: int): self.wisdom = value
    @property
    def cha_stat(self) -> int:
        eq_b = self.equipment_stat_bonuses.get("luck", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        return self.luck + eq_b
    @cha_stat.setter
    def cha_stat(self, value: int): self.luck = value

    @property
    def perception_stat(self) -> int: return self.effective_perception
    @property
    def per_stat(self) -> int: return self.effective_perception
    @property
    def per_mod(self) -> int: return (self.effective_perception - 10) // 2
    @property
    def effective_perception(self) -> int:
        eq_b = self.equipment_stat_bonuses.get("perception", 0) + self.equipment_stat_bonuses.get("per", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        base = self.perception + eq_b
        if hasattr(self, "status_effects") and self.status_effects:
            for eff in self.status_effects.values():
                if getattr(eff, "stat_debuffs", None) and "perception" in eff.stat_debuffs:
                    base += eff.stat_debuffs["perception"]
        if hasattr(self, "alcohol_state") and isinstance(self.alcohol_state, dict):
            if self.alcohol_state.get("has_hangover", False):
                base -= 2
        return max(1, base)

    def get_effective_reputation(self, location_id: str) -> int:
        """Returns perceived reputation in a specific location: local + int(global * 0.75)."""
        local_rep = self.regional_reputation.get(location_id, 0)
        return local_rep + int(self.reputation * 0.75)

    @property
    def equipped_weapon(self) -> str | None: return self.equipment.weapon
    @equipped_weapon.setter
    def equipped_weapon(self, value: str | None): self.equipment.weapon = value
    @property
    def equipped_armor(self) -> str | None: return self.equipment.chest
    @equipped_armor.setter
    def equipped_armor(self, value: str | None): self.equipment.chest = value

    @property
    def str_mod(self) -> int: return (self.effective_strength - 10) // 2
    @property  
    def agi_mod(self) -> int: return (self.effective_agility - 10) // 2
    @property
    def int_mod(self) -> int: return (self.effective_intelligence - 10) // 2 + max(0, (self.wis_stat - 10) // 2)
    @property
    def effective_crit_rate(self) -> float:
        eq_crit = self.equipment_stat_bonuses.get("crit_rate", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        return BASE_CRIT_RATE + (self.crit_rate_bonus + eq_crit) * CRIT_RATE_PER_POINT + max(0, self.luck - 10) * LUCK_CRIT_BONUS
    @property
    def effective_crit_damage(self) -> float:
        eq_crit_dmg = self.equipment_stat_bonuses.get("crit_damage", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        return BASE_CRIT_DAMAGE + (self.crit_damage_bonus + eq_crit_dmg) * CRIT_DMG_PER_POINT
    @property
    def max_mana_effective(self) -> int:
        eq_mana = self.equipment_stat_bonuses.get("max_mana", 0) if hasattr(self, "equipment_stat_bonuses") else 0
        penalty = 0
        if hasattr(self, "mana_burn_state") and isinstance(self.mana_burn_state, dict):
            penalty = self.mana_burn_state.get("max_mp_penalty", 0)
        return max(0, self.max_mana + eq_mana + max(0, self.intelligence - 10) * 5 - penalty)

    base_armor_class: int = 10

    @property
    def armor_class(self) -> int:
        eq_def = getattr(self, "equipment_defense", 0)
        alc_bonus = 0
        if hasattr(self, "alcohol_state") and isinstance(self.alcohol_state, dict):
            if self.alcohol_state.get("intoxication_stage", 0) >= 2:
                alc_bonus = 2
        return self.base_armor_class + self.agi_mod + eq_def + alc_bonus

    @armor_class.setter
    def armor_class(self, value: int):
        eq_def = getattr(self, "equipment_defense", 0)
        self.base_armor_class = value - self.agi_mod - eq_def

    # Realistic Physical & Combat Properties
    @property
    def movement_speed_mps(self) -> float:
        """이동 속도 (m/s). 민첩 10=4.5m/s (조깅), 민첩 15=10.5m/s (인간 정점/우사인 볼트 최고 속도)."""
        base = 4.5 + (self.effective_agility - 10) * 1.2
        return max(1.0, round(base, 2))

    @property
    def max_draw_weight_lbs(self) -> float:
        """최대 당길 수 있는 활 장력 (lbs). 근력 10=50 lbs, 근력 15=150 lbs (영국 장궁병 정점)."""
        base = 50.0 + (self.effective_strength - 10) * 20.0
        return max(10.0, round(base, 1))

    @property
    def windup_multiplier(self) -> float:
        """선딜레이 배율. 민첩 10=1.0, 민첩 15=0.5 (선딜레이 50% 단축)."""
        base = 1.0 - (self.effective_agility - 10) * 0.1
        return max(0.2, round(base, 2))

    @property
    def incantation_speed_multiplier(self) -> float:
        """영창 속도 배율. 지혜 10=1.0, 지혜 15=0.5 (영창 시간 50% 단축)."""
        base = 1.0 - (self.wis_stat - 10) * 0.1
        return max(0.2, round(base, 2))

    @property
    def effective_poise(self) -> float:
        """유효 강인도 (체질 + 방어구 무게/방어력 보정)."""
        base = self.poise + max(0, self.effective_constitution - 10) * 2.0
        eq_def = getattr(self, "equipment_defense", 0)
        return max(0.0, round(base + eq_def * 0.5, 1))

    def allocate_stat(self, stat_name: str, amount: int = 1, stat_cap: Optional[int] = None) -> bool:
        """자유 분배 스탯 포인트를 7대 핵심 스탯에 투자 (세계관 스탯 상한 stat_cap 검증 지원)."""
        if amount <= 0 or self.stat_points < amount:
            return False
        stat_map = {
            "strength": "strength", "근력": "strength", "str": "strength",
            "agility": "agility", "민첩": "agility", "dex": "agility", "agi": "agility",
            "constitution": "constitution", "체질": "constitution", "체력": "constitution", "con": "constitution",
            "intelligence": "intelligence", "지능": "intelligence", "int": "intelligence",
            "wisdom": "wisdom", "지혜": "wisdom", "wis": "wisdom",
            "perception": "perception", "감각": "perception", "인지": "perception", "per": "perception",
            "luck": "luck", "행운": "luck", "luk": "luck",
        }
        target_field = stat_map.get(stat_name.lower())
        if not target_field or not hasattr(self, target_field):
            return False
        current_val = getattr(self, target_field)
        if stat_cap is not None and current_val + amount > stat_cap:
            return False
        setattr(self, target_field, current_val + amount)
        self.stat_points -= amount
        return True

    def add_exp(self, amount: int, power_scale_preset: Optional[Any] = None) -> dict:
        """경험치를 획득하고 필요 시 레벨업 처리 (PowerScalePreset 연동)."""
        if amount <= 0:
            return {"leveled_up": False, "levels_gained": 0, "current_level": self.level, "exp": self.exp}

        from src.world.stat_engine import StatEngine
        preset = power_scale_preset or StatEngine.get_preset("standard_fantasy")
        max_lvl = getattr(preset, "max_level", 50)
        pts_per_lvl = getattr(preset, "stat_points_per_level", 3)
        hp_base = getattr(preset, "hp_gain_per_level", 5)
        mp_base = getattr(preset, "mp_gain_per_level", 3)
        breakthrough_mult = getattr(preset, "breakthrough_multiplier", 1.0)
        stat_cap = getattr(preset, "stat_cap", 100)
        realm_names = getattr(preset, "realm_names", [])

        self.exp += amount
        levels_gained = 0
        while self.level < max_lvl:
            req = StatEngine.calculate_required_exp(self.level, preset)
            if self.exp >= req:
                self.exp -= req
                self.level += 1
                levels_gained += 1
                self.stat_points += pts_per_lvl
                hp_gain = hp_base + (self.effective_constitution // 3)
                mp_gain = mp_base + (self.effective_intelligence // 3)
                self.max_health += hp_gain
                self.max_mana += mp_gain
                self.health = self.max_health
                self.mana = self.max_mana

                # 선협/무협 경지 돌파 특수 효과
                if breakthrough_mult > 1.0:
                    for s_field in ["strength", "agility", "constitution", "intelligence", "wisdom", "perception", "luck"]:
                        cur = getattr(self, s_field, 10)
                        setattr(self, s_field, min(stat_cap, int(cur * breakthrough_mult)))
                    if realm_names and self.level - 1 < len(realm_names):
                        new_realm = realm_names[self.level - 1]
                        self.sub_stats["current_realm"] = new_realm
                        self.traits = [t for t in self.traits if not t.startswith("경지:")]
                        self.traits.append(f"경지: {new_realm}")
            else:
                break

        if self.level >= max_lvl:
            req_cap = StatEngine.calculate_required_exp(self.level, preset)
            if self.exp > req_cap:
                self.exp = req_cap

        return {
            "leveled_up": levels_gained > 0,
            "levels_gained": levels_gained,
            "current_level": self.level,
            "exp": self.exp,
            "stat_points": self.stat_points,
            "max_health": self.max_health,
            "max_mana": self.max_mana,
            "power_scale": getattr(preset, "id", "standard_fantasy"),
            "current_realm": self.sub_stats.get("current_realm", "") if breakthrough_mult > 1.0 else None,
        }


