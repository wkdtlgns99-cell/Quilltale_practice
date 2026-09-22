"""
Diablo-style Procedural Loot & Affix Generator for Quilltale TRPG.
Features:
1. 5-Tier Rarity System: Common (White), Magic (Blue), Rare (Yellow), Epic (Purple), Unique (Orange).
2. Procedural Affix System: Combines Prefixes (damage, defense, elements) and Suffixes (stats, crit, utility).
3. Level & Tier Stat Scaling: Multiplies base and affix stats based on dungeon depth and monster level.
4. Rune Sockets: Allocates 0 to 3 rune/gem sockets based on item rarity.
5. Salvage / Disenchanting: Recovers magic dust, upgrade ingots, and rune fragments from unwanted loot.
6. Seamless EquipmentEngine Integration: Encodes stat bonuses into item.properties["stat_bonuses"].

Pure Python, 100% deterministic, 0-token, 0-GPU, 0ms cost.
"""
from dataclasses import dataclass, field
from enum import Enum
import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from src.world.entities import Item

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 1. Rarity & Data Models
# ──────────────────────────────────────────────

class ItemRarity(str, Enum):
    COMMON = "common"     # 일반 (White) - 기본 스탯, 옵션 0개, 소켓 0개
    MAGIC = "magic"       # 마법 (Blue) - 옵션 1~2개, 소켓 0~1개
    RARE = "rare"         # 희귀 (Yellow) - 옵션 3~4개, 소켓 1~2개
    EPIC = "epic"         # 영웅 (Purple) - 옵션 4~5개, 소켓 1~2개 보장
    UNIQUE = "unique"     # 유니크 (Orange) - 고유 전설 옵션 4~6개, 소켓 2~3개 보장


RARITY_COLORS: Dict[str, str] = {
    ItemRarity.COMMON.value: "#9ca3af",   # Gray / White
    ItemRarity.MAGIC.value: "#38bdf8",    # Blue
    ItemRarity.RARE.value: "#facc15",     # Yellow / Gold
    ItemRarity.EPIC.value: "#c084fc",     # Purple
    ItemRarity.UNIQUE.value: "#fb923c",   # Orange
}

RARITY_NAMES_KO: Dict[str, str] = {
    ItemRarity.COMMON.value: "일반",
    ItemRarity.MAGIC.value: "마법",
    ItemRarity.RARE.value: "희귀",
    ItemRarity.EPIC.value: "영웅",
    ItemRarity.UNIQUE.value: "유니크",
}


@dataclass
class ItemAffix:
    name: str
    affix_type: str                    # "prefix" | "suffix"
    stat_bonuses: Dict[str, int] = field(default_factory=dict)
    bonus_damage: int = 0
    bonus_defense: int = 0
    bonus_crit_rate: int = 0
    bonus_crit_damage: int = 0
    bonus_health: int = 0
    bonus_mana: int = 0
    special_effect: str = ""
    traits: List[str] = field(default_factory=lambda: ["아이템 접사"])


@dataclass
class BaseItemTemplate:
    base_id: str
    name: str
    item_type: str                     # "weapon", "armor", "accessory"
    category: str                      # "sword", "bow", "staff", "dagger", "plate", "leather", "robe", "ring", "amulet"
    base_damage: int = 0
    base_defense: int = 0
    base_value: int = 10
    scaling_stat: str = "str"
    scaling_factor: float = 1.0
    material: str = "iron"
    traits: List[str] = field(default_factory=lambda: ["베이스 장비"])


@dataclass
class UniqueItemTemplate:
    unique_id: str
    name: str
    item_type: str
    category: str
    damage: int
    defense: int
    value: int
    scaling_stat: str
    stat_bonuses: Dict[str, int]
    special_effect: str
    lore_description: str
    traits: List[str] = field(default_factory=lambda: ["유니크 전설 장비"])


# ──────────────────────────────────────────────
# 2. Affix & Template Databases
# ──────────────────────────────────────────────

PREFIX_POOL: List[ItemAffix] = [
    # Weapon Offensive Prefixes
    ItemAffix(name="야만적인", affix_type="prefix", stat_bonuses={"str": 3}, bonus_damage=3, traits=["물리 공격", "근력"]),
    ItemAffix(name="날카로운", affix_type="prefix", bonus_damage=2, bonus_crit_rate=5, traits=["치명타", "칼날"]),
    ItemAffix(name="묵직한", affix_type="prefix", bonus_damage=4, traits=["둔기", "충격"]),
    ItemAffix(name="마도사의", affix_type="prefix", stat_bonuses={"int": 4}, bonus_mana=25, traits=["마법", "지능"]),
    ItemAffix(name="화염의", affix_type="prefix", bonus_damage=3, special_effect="타격 시 화염 화상", traits=["화염", "원소"]),
    ItemAffix(name="서리깃든", affix_type="prefix", bonus_damage=2, special_effect="타격 시 냉기 감속", traits=["냉기", "원소"]),
    ItemAffix(name="뇌전의", affix_type="prefix", bonus_damage=4, bonus_crit_damage=10, special_effect="번개 감전 방전", traits=["전격", "원소"]),
    ItemAffix(name="흡혈의", affix_type="prefix", bonus_damage=1, special_effect="피해의 5% 생명력 흡수", traits=["흡혈", "암흑"]),
    ItemAffix(name="무자비한", affix_type="prefix", bonus_damage=5, traits=["처형", "관통"]),
    ItemAffix(name="처형인의", affix_type="prefix", bonus_damage=3, bonus_crit_rate=8, traits=["단두", "치명타"]),

    # Armor & Accessory Defensive / Utility Prefixes
    ItemAffix(name="견고한", affix_type="prefix", stat_bonuses={"con": 2}, bonus_defense=4, traits=["방어", "체력"]),
    ItemAffix(name="수호의", affix_type="prefix", bonus_defense=5, bonus_health=20, traits=["방호", "생명력"]),
    ItemAffix(name="강철의", affix_type="prefix", bonus_defense=3, traits=["철벽", "금속"]),
    ItemAffix(name="은빛", affix_type="prefix", stat_bonuses={"wis": 3}, bonus_defense=2, traits=["성광", "정화"]),
    ItemAffix(name="축복받은", affix_type="prefix", stat_bonuses={"wis": 2, "luk": 2}, bonus_health=15, traits=["신성", "축복"]),
    ItemAffix(name="불굴의", affix_type="prefix", stat_bonuses={"con": 4}, bonus_defense=4, traits=["인내", "불굴"]),
    ItemAffix(name="비전의", affix_type="prefix", stat_bonuses={"int": 3}, bonus_mana=30, traits=["비전", "마나"]),
    ItemAffix(name="그림자의", affix_type="prefix", stat_bonuses={"agi": 3}, bonus_defense=2, traits=["은신", "민첩"]),
    ItemAffix(name="거인의", affix_type="prefix", stat_bonuses={"str": 4, "con": 3}, bonus_health=35, traits=["거인", "생명력"]),
    ItemAffix(name="치유의", affix_type="prefix", bonus_health=40, special_effect="턴당 체력 재생 +3", traits=["재생", "치유"]),
]

SUFFIX_POOL: List[ItemAffix] = [
    # Stats & Combat Suffixes
    ItemAffix(name="의 힘", affix_type="suffix", stat_bonuses={"str": 3}, traits=["근력"]),
    ItemAffix(name="의 민첩함", affix_type="suffix", stat_bonuses={"agi": 3}, traits=["민첩"]),
    ItemAffix(name="의 지혜", affix_type="suffix", stat_bonuses={"wis": 3}, traits=["지혜"]),
    ItemAffix(name="의 건강", affix_type="suffix", stat_bonuses={"con": 3}, bonus_health=25, traits=["체력"]),
    ItemAffix(name="의 학살자", affix_type="suffix", bonus_damage=3, bonus_crit_damage=20, traits=["학살", "치명타"]),
    ItemAffix(name="의 광전사", affix_type="suffix", stat_bonuses={"str": 3}, bonus_damage=3, traits=["광포", "돌진"]),
    ItemAffix(name="의 티탄", affix_type="suffix", stat_bonuses={"con": 4}, bonus_defense=4, traits=["티탄", "내구"]),
    ItemAffix(name="의 폭풍", affix_type="suffix", bonus_damage=2, bonus_crit_rate=6, traits=["폭풍", "번개"]),
    ItemAffix(name="의 파멸", affix_type="suffix", bonus_damage=5, traits=["파멸", "암흑"]),
    ItemAffix(name="의 수호자", affix_type="suffix", bonus_defense=4, bonus_health=30, traits=["수호", "보호"]),
    ItemAffix(name="의 암살자", affix_type="suffix", stat_bonuses={"agi": 3}, bonus_crit_rate=7, traits=["암살", "급소"]),
    ItemAffix(name="의 행운", affix_type="suffix", stat_bonuses={"luk": 5}, traits=["행운", "드랍"]),
    ItemAffix(name="의 예리함", affix_type="suffix", bonus_crit_damage=25, traits=["예리", "출혈"]),
    ItemAffix(name="의 인내", affix_type="suffix", stat_bonuses={"con": 3}, bonus_defense=3, traits=["인내", "방어"]),
    ItemAffix(name="의 영생", affix_type="suffix", bonus_health=50, special_effect="턴당 체력 재생 +5", traits=["불사", "생명"]),
    ItemAffix(name="의 맹독", affix_type="suffix", bonus_damage=2, special_effect="타격 시 치명적 중독", traits=["독성", "암살"]),
    ItemAffix(name="의 관통", affix_type="suffix", bonus_damage=3, special_effect="방어도 25% 무시", traits=["관통", "물리"]),
    ItemAffix(name="의 에테르", affix_type="suffix", stat_bonuses={"int": 3}, bonus_mana=40, traits=["에테르", "마법"]),
    ItemAffix(name="의 신성", affix_type="suffix", stat_bonuses={"wis": 4}, bonus_damage=2, special_effect="언데드 대상 추가 피해", traits=["신성", "성광"]),
    ItemAffix(name="의 혈투", affix_type="suffix", stat_bonuses={"str": 2, "agi": 2}, bonus_damage=3, traits=["투쟁", "전투"]),
]

BASE_ITEM_POOL: List[BaseItemTemplate] = [
    # Weapons
    BaseItemTemplate(base_id="base_dagger", name="단검", item_type="weapon", category="dagger", base_damage=6, base_value=15, scaling_stat="dex", scaling_factor=1.2, material="steel"),
    BaseItemTemplate(base_id="base_shortsword", name="숏소드", item_type="weapon", category="sword", base_damage=8, base_value=25, scaling_stat="str", scaling_factor=1.2, material="iron"),
    BaseItemTemplate(base_id="base_longsword", name="롱소드", item_type="weapon", category="sword", base_damage=12, base_value=40, scaling_stat="str", scaling_factor=1.5, material="steel"),
    BaseItemTemplate(base_id="base_greatsword", name="대검", item_type="weapon", category="sword", base_damage=16, base_value=60, scaling_stat="str", scaling_factor=1.8, material="steel"),
    BaseItemTemplate(base_id="base_battleaxe", name="배틀액스", item_type="weapon", category="axe", base_damage=14, base_value=50, scaling_stat="str", scaling_factor=1.6, material="iron"),
    BaseItemTemplate(base_id="base_warhammer", name="워해머", item_type="weapon", category="mace", base_damage=15, base_value=55, scaling_stat="str", scaling_factor=1.7, material="steel"),
    BaseItemTemplate(base_id="base_shortbow", name="단궁", item_type="weapon", category="bow", base_damage=9, base_value=30, scaling_stat="dex", scaling_factor=1.3, material="wood"),
    BaseItemTemplate(base_id="base_longbow", name="장궁", item_type="weapon", category="bow", base_damage=13, base_value=50, scaling_stat="dex", scaling_factor=1.6, material="wood"),
    BaseItemTemplate(base_id="base_wand", name="마법봉", item_type="weapon", category="wand", base_damage=7, base_value=35, scaling_stat="int", scaling_factor=1.4, material="wood"),
    BaseItemTemplate(base_id="base_staff", name="비전 스태프", item_type="weapon", category="staff", base_damage=11, base_value=55, scaling_stat="int", scaling_factor=1.7, material="wood"),

    # Armors
    BaseItemTemplate(base_id="base_leather_armor", name="가죽 갑옷", item_type="armor", category="leather", base_defense=5, base_value=30, material="leather"),
    BaseItemTemplate(base_id="base_chainmail", name="사슬 갑옷", item_type="armor", category="chain", base_defense=9, base_value=50, material="iron"),
    BaseItemTemplate(base_id="base_plate_armor", name="판금 흉갑", item_type="armor", category="plate", base_defense=14, base_value=80, material="steel"),
    BaseItemTemplate(base_id="base_mage_robe", name="마도사의 로브", item_type="armor", category="robe", base_defense=3, base_value=45, material="cloth"),
    BaseItemTemplate(base_id="base_iron_shield", name="강철 방패", item_type="armor", category="shield", base_defense=7, base_value=40, material="steel"),
    BaseItemTemplate(base_id="base_helm", name="철투구", item_type="armor", category="helm", base_defense=4, base_value=25, material="iron"),
    BaseItemTemplate(base_id="base_boots", name="판금 장화", item_type="armor", category="boots", base_defense=3, base_value=20, material="steel"),
    BaseItemTemplate(base_id="base_gloves", name="가죽 장갑", item_type="armor", category="gloves", base_defense=2, base_value=15, material="leather"),

    # Accessories
    BaseItemTemplate(base_id="base_silver_ring", name="은반지", item_type="accessory", category="ring", base_value=35, material="precious_metal"),
    BaseItemTemplate(base_id="base_ruby_necklace", name="루비 목걸이", item_type="accessory", category="necklace", base_value=50, material="precious_metal"),
    BaseItemTemplate(base_id="base_jade_bracelet", name="비취 팔찌", item_type="accessory", category="bracelet", base_value=40, material="precious_metal"),
    BaseItemTemplate(base_id="base_leather_belt", name="가죽 허리띠", item_type="accessory", category="belt", base_defense=1, base_value=20, material="leather"),
]

UNIQUE_ITEM_POOL: List[UniqueItemTemplate] = [
    UniqueItemTemplate(
        unique_id="unique_soul_reaper",
        name="영혼 수확자의 대낫",
        item_type="weapon",
        category="scythe",
        damage=24,
        defense=0,
        value=350,
        scaling_stat="dex",
        stat_bonuses={"dex": 6, "str": 4, "crit_rate": 12, "crit_damage": 35},
        special_effect="적 처치 시 적의 영혼을 흡수하여 체력 15% 즉시 회복",
        lore_description="지하 묘지의 고대 사신이 휘두르던 저주받은 대낫. 칼날 주위로 옅은 보랏빛 유령 안개가 피어오릅니다.",
        traits=["유니크 무기", "영혼 흡수", "사신의 유산"],
    ),
    UniqueItemTemplate(
        unique_id="unique_aegis_of_valor",
        name="용기의 아이기스",
        item_type="armor",
        category="shield",
        damage=0,
        defense=22,
        value=320,
        scaling_stat="con",
        stat_bonuses={"con": 8, "str": 4, "max_health": 60},
        special_effect="완전 방어 성공 시 전방 5m 내 모든 적에게 성광 충격파 방출",
        lore_description="태양신 솔라리스의 축복이 깃든 황금 방패. 어둠 속에서도 눈부신 광휘를 뿜어냅니다.",
        traits=["유니크 방어구", "성광 방패", "태양의 축복"],
    ),
    UniqueItemTemplate(
        unique_id="unique_sunfire_bow",
        name="태양화염의 명궁",
        item_type="weapon",
        category="bow",
        damage=20,
        defense=0,
        value=300,
        scaling_stat="dex",
        stat_bonuses={"dex": 7, "crit_rate": 10, "crit_damage": 30},
        special_effect="화살이 태양 화염탄으로 치환되어 적중 지점 반경 3m 폭발 피해",
        lore_description="엘프 명궁 아르텔이 고룡의 뼈를 깎아 만든 장궁. 시위를 당길 때마다 열풍이 몰아칩니다.",
        traits=["유니크 무기", "태양화염", "폭발 사격"],
    ),
    UniqueItemTemplate(
        unique_id="unique_archmage_mantle",
        name="대마도사의 성운 로브",
        item_type="armor",
        category="robe",
        damage=0,
        defense=12,
        value=280,
        scaling_stat="int",
        stat_bonuses={"int": 9, "wis": 5, "max_mana": 80},
        special_effect="마법 주문 시전 시 마나 소모량 25% 감소 및 쿨다운 1턴 단축",
        lore_description="은하의 성운 조각을 직조하여 만든 전설적인 마도 로브. 입은 자의 마나 회로를 영구히 확장합니다.",
        traits=["유니크 방어구", "성운 로브", "마나 절감"],
    ),
    UniqueItemTemplate(
        unique_id="unique_shadow_fang",
        name="그림자 송곳니 단검",
        item_type="weapon",
        category="dagger",
        damage=16,
        defense=0,
        value=260,
        scaling_stat="dex",
        stat_bonuses={"dex": 8, "crit_rate": 15, "crit_damage": 45},
        special_effect="은신 상태에서 공격 시 100% 치명타 및 출혈 상태이상 확정 부여",
        lore_description="어둠의 길드 최고 암살자만이 계승하던 흑요석 단검. 빛을 전혀 반사하지 않습니다.",
        traits=["유니크 무기", "암살 특화", "흑요석 칼날"],
    ),
    UniqueItemTemplate(
        unique_id="unique_frost_mourn",
        name="서리한탄의 대검",
        item_type="weapon",
        category="sword",
        damage=26,
        defense=4,
        value=380,
        scaling_stat="str",
        stat_bonuses={"str": 7, "con": 5, "crit_damage": 25},
        special_effect="타격 시 대상의 관절을 1턴간 빙결 동결시켜 행동 차단",
        lore_description="영구 빙하기의 극한 속에서 벼려낸 차가운 대검. 베어낸 적의 피가 공중에서 얼어붙습니다.",
        traits=["유니크 무기", "빙결 대검", "영구 동결"],
    ),
    UniqueItemTemplate(
        unique_id="unique_titan_heart",
        name="티탄의 심장 반지",
        item_type="accessory",
        category="ring",
        damage=0,
        defense=6,
        value=240,
        scaling_stat="con",
        stat_bonuses={"con": 6, "str": 4, "max_health": 50},
        special_effect="체력이 25% 이하로 떨어지면 3턴간 피해 50% 흡수 보호막 발동",
        lore_description="고대 거인의 심장석을 가공해 만든 육중한 반지. 착용자의 생명력을 고동치게 만듭니다.",
        traits=["유니크 장신구", "긴급 보호막", "티탄의 권능"],
    ),
]


# ──────────────────────────────────────────────
# 3. Procedural Loot Generator Engine
# ──────────────────────────────────────────────

class LootGenerator:
    """
    Deterministic Procedural Loot and Item Generator.
    Generates items with rarity-scaled affixes, sockets, and stat bonuses.
    """

    @classmethod
    def determine_rarity(cls, level: int = 1, luck: int = 10, rng: Optional[random.Random] = None) -> ItemRarity:
        """
        Calculates item rarity based on entity level and Luck (LUK) stat.
        Luck boosts Magic/Rare/Epic/Unique drop chances.
        """
        r = rng if rng else random.Random()
        luck_bonus = max(0, (luck - 10) * 0.5)

        # Weights out of 1000
        # Common: 600 -> 350, Magic: 250 -> 350, Rare: 110 -> 180, Epic: 35 -> 80, Unique: 5 -> 40
        w_unique = min(80, int(5 + (level * 1.5) + luck_bonus * 2.0))
        w_epic = min(150, int(35 + (level * 3.0) + luck_bonus * 2.5))
        w_rare = min(250, int(110 + (level * 5.0) + luck_bonus * 3.0))
        w_magic = min(400, int(250 + (level * 4.0) + luck_bonus * 2.0))
        w_common = max(100, 1000 - (w_unique + w_epic + w_rare + w_magic))

        roll = r.randint(1, 1000)
        if roll <= w_unique:
            return ItemRarity.UNIQUE
        elif roll <= w_unique + w_epic:
            return ItemRarity.EPIC
        elif roll <= w_unique + w_epic + w_rare:
            return ItemRarity.RARE
        elif roll <= w_unique + w_epic + w_rare + w_magic:
            return ItemRarity.MAGIC
        return ItemRarity.COMMON

    @classmethod
    def generate_item(
        cls,
        level: int = 1,
        rarity: Optional[ItemRarity] = None,
        category_filter: Optional[str] = None,
        location: str = "inventory",
        seed: Optional[int] = None,
    ) -> Item:
        """
        Generates a single procedural item with rolled affixes, sockets, and scaled stats.
        """
        rng = random.Random(seed if seed is not None else random.randint(1, 99999999))

        # 1. Determine Rarity if not forced
        if rarity is None:
            rarity = cls.determine_rarity(level=level, luck=10, rng=rng)

        # 2. Check for Unique Item Generation
        if rarity == ItemRarity.UNIQUE:
            unique_candidates = UNIQUE_ITEM_POOL
            if category_filter:
                unique_candidates = [u for u in UNIQUE_ITEM_POOL if u.item_type == category_filter or u.category == category_filter]
                if not unique_candidates:
                    unique_candidates = UNIQUE_ITEM_POOL
            chosen_unique = rng.choice(unique_candidates)
            return cls._build_unique_item(chosen_unique, level, location, rng)

        # 3. Select Base Item Template
        candidates = BASE_ITEM_POOL
        if category_filter:
            filtered = [b for b in BASE_ITEM_POOL if b.item_type == category_filter or b.category == category_filter]
            if filtered:
                candidates = filtered
        base_tmpl = rng.choice(candidates)

        # 4. Affix Slot Counts by Rarity
        # Common: 0, Magic: 1~2, Rare: 3~4, Epic: 4~5
        if rarity == ItemRarity.COMMON:
            num_prefixes, num_suffixes = 0, 0
        elif rarity == ItemRarity.MAGIC:
            num_prefixes = rng.choice([0, 1])
            num_suffixes = 1 if num_prefixes == 0 else rng.choice([0, 1])
        elif rarity == ItemRarity.RARE:
            num_prefixes = rng.randint(1, 2)
            num_suffixes = rng.randint(1, 2)
        else: # EPIC
            num_prefixes = 2
            num_suffixes = rng.randint(2, 3)

        # 5. Roll Prefixes & Suffixes
        chosen_prefixes: List[ItemAffix] = rng.sample(PREFIX_POOL, min(num_prefixes, len(PREFIX_POOL)))
        chosen_suffixes: List[ItemAffix] = rng.sample(SUFFIX_POOL, min(num_suffixes, len(SUFFIX_POOL)))

        # 6. Compose Item Name
        p_name = chosen_prefixes[0].name if chosen_prefixes else ""
        s_name = chosen_suffixes[0].name if chosen_suffixes else ""
        item_name = f"{p_name} {base_tmpl.name} {s_name}".strip()
        item_name = " ".join(item_name.split()) # clean spaces

        # 7. Level Scaling Factor
        scale_mult = 1.0 + ((level - 1) * 0.15)

        # 8. Aggregate Stats
        final_damage = int(base_tmpl.base_damage * scale_mult) if base_tmpl.base_damage > 0 else 0
        final_defense = int(base_tmpl.base_defense * scale_mult) if base_tmpl.base_defense > 0 else 0
        final_value = int(base_tmpl.base_value * scale_mult)

        stat_bonuses: Dict[str, int] = {}
        special_effects: List[str] = []
        affix_traits: List[str] = []

        all_affixes = chosen_prefixes + chosen_suffixes
        for affix in all_affixes:
            final_damage += int(affix.bonus_damage * scale_mult)
            final_defense += int(affix.bonus_defense * scale_mult)
            final_value += int(20 * scale_mult)

            for s_k, s_v in affix.stat_bonuses.items():
                scaled_v = max(1, int(s_v * scale_mult))
                stat_bonuses[s_k] = stat_bonuses.get(s_k, 0) + scaled_v

            if affix.bonus_crit_rate > 0:
                stat_bonuses["crit_rate"] = stat_bonuses.get("crit_rate", 0) + affix.bonus_crit_rate
            if affix.bonus_crit_damage > 0:
                stat_bonuses["crit_damage"] = stat_bonuses.get("crit_damage", 0) + affix.bonus_crit_damage
            if affix.bonus_health > 0:
                stat_bonuses["max_health"] = stat_bonuses.get("max_health", 0) + int(affix.bonus_health * scale_mult)
            if affix.bonus_mana > 0:
                stat_bonuses["max_mana"] = stat_bonuses.get("max_mana", 0) + int(affix.bonus_mana * scale_mult)
            if affix.special_effect:
                special_effects.append(affix.special_effect)
            affix_traits.extend(affix.traits)

        # 9. Rune Sockets
        # Common: 0, Magic: 0~1, Rare: 1~2, Epic: 1~2, Unique: 2~3
        if rarity == ItemRarity.COMMON:
            rune_slots = 0
        elif rarity == ItemRarity.MAGIC:
            rune_slots = rng.choice([0, 1])
        elif rarity == ItemRarity.RARE:
            rune_slots = rng.randint(1, 2)
        else: # EPIC
            rune_slots = rng.randint(1, 2)

        # 10. Assemble Item Traits
        color_hex = RARITY_COLORS[rarity.value]
        rarity_ko = RARITY_NAMES_KO[rarity.value]
        traits = [
            f"등급: {rarity_ko}",
            f"레벨 {level}",
            base_tmpl.category,
            f"소켓 {rune_slots}개",
        ] + list(set(affix_traits))[:5]

        # 11. Description with Affixes & Sockets
        stats_desc_parts = []
        if final_damage > 0:
            stats_desc_parts.append(f"공격력 +{final_damage}")
        if final_defense > 0:
            stats_desc_parts.append(f"방어도 +{final_defense}")
        for sk, sv in stat_bonuses.items():
            stats_desc_parts.append(f"{sk.upper()} +{sv}")
        if special_effects:
            stats_desc_parts.append(f"특수효과: {', '.join(special_effects)}")

        desc_text = (
            f"[{rarity_ko} 등급 {base_tmpl.name}] 레벨 {level} 요구. "
            f"{', '.join(stats_desc_parts)}. (소켓: {rune_slots}구멍)"
        )

        item_uid = f"loot_{base_tmpl.base_id}_{rng.randint(10000, 99999)}"

        return Item(
            id=item_uid,
            name=item_name,
            description=desc_text,
            location=location,
            item_type=base_tmpl.item_type,
            damage=final_damage,
            defense=final_defense,
            value=final_value,
            scaling_stat=base_tmpl.scaling_stat,
            scaling_factor=base_tmpl.scaling_factor,
            properties={
                "rarity": rarity.value,
                "rarity_color": color_hex,
                "level": level,
                "stat_bonuses": stat_bonuses,
                "special_effects": special_effects,
                "prefixes": [p.name for p in chosen_prefixes],
                "suffixes": [s.name for s in chosen_suffixes],
                "base_category": base_tmpl.category,
            },
            rune_slots=rune_slots,
            material=base_tmpl.material,
            traits=traits,
        )

    @classmethod
    def _build_unique_item(
        cls, tmpl: UniqueItemTemplate, level: int, location: str, rng: random.Random
    ) -> Item:
        scale_mult = 1.0 + ((level - 1) * 0.15)
        final_damage = int(tmpl.damage * scale_mult) if tmpl.damage > 0 else 0
        final_defense = int(tmpl.defense * scale_mult) if tmpl.defense > 0 else 0
        final_value = int(tmpl.value * scale_mult)

        scaled_stat_bonuses = {}
        for sk, sv in tmpl.stat_bonuses.items():
            scaled_stat_bonuses[sk] = max(1, int(sv * scale_mult))

        rune_slots = rng.randint(2, 3)
        item_uid = f"loot_{tmpl.unique_id}_{rng.randint(1000, 9999)}"

        return Item(
            id=item_uid,
            name=tmpl.name,
            description=f"[유니크] {tmpl.lore_description} (특수효과: {tmpl.special_effect})",
            location=location,
            item_type=tmpl.item_type,
            damage=final_damage,
            defense=final_defense,
            value=final_value,
            scaling_stat=tmpl.scaling_stat,
            scaling_factor=1.8,
            properties={
                "rarity": ItemRarity.UNIQUE.value,
                "rarity_color": RARITY_COLORS[ItemRarity.UNIQUE.value],
                "level": level,
                "stat_bonuses": scaled_stat_bonuses,
                "special_effects": [tmpl.special_effect],
                "is_unique": True,
                "base_category": tmpl.category,
            },
            rune_slots=rune_slots,
            material="mythril",
            traits=list(tmpl.traits) + [f"소켓 {rune_slots}개", f"레벨 {level}"],
        )

    # ── Live Game Loop Drop Rollers ──

    @classmethod
    def roll_monster_drop(
        cls,
        monster_npc: Any,
        player_luck: int = 10,
        seed: Optional[int] = None
    ) -> List[Item]:
        """
        Rolls 1~3 procedural loot drops when a hostile NPC is killed.
        High-tier monsters guarantee higher rarity items.
        """
        rng = random.Random(seed if seed is not None else random.randint(1, 999999))
        m_level = getattr(monster_npc, "level", 1) or 1
        m_tier = getattr(monster_npc, "tier", "commoner")

        drops: List[Item] = []

        # Number of drops
        num_drops = 1
        if m_tier in ["intermediate", "elite"]:
            num_drops = rng.choice([1, 2])
        elif m_tier in ["legend", "boss"]:
            num_drops = rng.randint(2, 3)

        for _ in range(num_drops):
            # Bosses guarantee at least Rare
            forced_rarity = None
            if m_tier in ["legend", "boss"]:
                forced_rarity = rng.choice([ItemRarity.RARE, ItemRarity.EPIC, ItemRarity.UNIQUE])

            item = cls.generate_item(
                level=m_level,
                rarity=forced_rarity,
                location="inventory",
                seed=rng.randint(1, 9999999)
            )
            drops.append(item)

        return drops

    @classmethod
    def roll_chest_loot(
        cls,
        floor_num: int = 1,
        dungeon_theme: str = "catacomb",
        player_luck: int = 10,
        seed: Optional[int] = None
    ) -> List[Item]:
        """
        Rolls 1~2 procedural loot items when opening a dungeon treasure chest (T).
        Deeper floors guarantee higher level and rarity items.
        """
        rng = random.Random(seed if seed is not None else random.randint(1, 999999))
        chest_level = max(1, floor_num * 2)

        # Deeper floors get rarity bias
        forced_rarity = None
        if floor_num >= 3:
            forced_rarity = rng.choice([ItemRarity.RARE, ItemRarity.EPIC])
        elif floor_num >= 2:
            forced_rarity = rng.choice([ItemRarity.MAGIC, ItemRarity.RARE])

        num_items = rng.randint(1, 2)
        loot: List[Item] = []
        for _ in range(num_items):
            item = cls.generate_item(
                level=chest_level,
                rarity=forced_rarity,
                location="inventory",
                seed=rng.randint(1, 9999999)
            )
            loot.append(item)

        return loot

    # ── Equipment Salvage / Disenchanting ──

    @classmethod
    def salvage_item(cls, item: Item) -> Dict[str, Any]:
        """
        Disenchants/salvages an item into crafting components based on its rarity.
        Returns recovered gold value, magic dust, and crafting fragments.
        """
        props = getattr(item, "properties", {}) or {}
        rarity_str = props.get("rarity", ItemRarity.COMMON.value)

        gold_recovered = max(5, int(item.value * 0.4))
        magic_dust = 0
        upgrade_ingots = 0
        rune_fragments = 0

        if rarity_str == ItemRarity.MAGIC.value:
            magic_dust = 2
            upgrade_ingots = 1
        elif rarity_str == ItemRarity.RARE.value:
            magic_dust = 5
            upgrade_ingots = 3
            rune_fragments = 1
        elif rarity_str == ItemRarity.EPIC.value:
            magic_dust = 10
            upgrade_ingots = 6
            rune_fragments = 3
        elif rarity_str == ItemRarity.UNIQUE.value:
            magic_dust = 25
            upgrade_ingots = 12
            rune_fragments = 8
        else: # COMMON
            upgrade_ingots = 1

        summary_ko = (
            f"[{item.name}] 분해 완료! "
            f"금화 {gold_recovered}닢, 마법 가루 {magic_dust}개, "
            f"강화 주괴 {upgrade_ingots}개, 룬 파편 {rune_fragments}개 회수."
        )

        return {
            "salvaged_item_id": item.id,
            "salvaged_item_name": item.name,
            "rarity": rarity_str,
            "gold_recovered": gold_recovered,
            "magic_dust": magic_dust,
            "upgrade_ingots": upgrade_ingots,
            "rune_fragments": rune_fragments,
            "summary_ko": summary_ko,
            "traits": ["장비 분해", "재료 회수"],
        }
