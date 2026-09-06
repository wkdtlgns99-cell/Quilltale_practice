"""
Deterministic Equipment Engine for Quilltale TRPG.
Calculates:
1. Aggregated equipment stats and total defense (AC bonus) across all 10 slots.
2. Dynamic stat bonuses (STR, AGI, INT, CON, WIS, LUK, Crit) from weapons, armors, and accessories.
3. Body part hit mapping to equipment slots and armor durability consumption.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging
from src.world.state import WorldState, Item, Player, NPC
from src.world.enchant_engine import EnchantEngine

logger = logging.getLogger(__name__)


@dataclass
class EquipmentSetBonus:
    threshold: int                                      # 요구 부위 개수 (2, 3, 4, 5 등)
    name_ko: str                                        # 세트 효과명 (예: "철벽의 맹세")
    stat_bonuses: Dict[str, int] = field(default_factory=dict)
    defense: int = 0
    damage: int = 0
    traits: List[str] = field(default_factory=list)     # 세트 효과 특성 태그
    passive_description: str = ""                       # 플레이어 표시용 패시브 효과 설명


@dataclass
class EquipmentSet:
    set_id: str
    name_ko: str                                        # 세트 명칭 (예: "왕실 근위대 세트")
    category: str                                       # "rare_general" | "monster_material" | "legendary_relic"
    description_ko: str = ""
    bonuses: Dict[int, EquipmentSetBonus] = field(default_factory=dict) # {2: EquipmentSetBonus, 4: EquipmentSetBonus}
    traits: List[str] = field(default_factory=lambda: ["장비 세트", "시너지 효과"])


class EquipmentEngine:
    TRAITS: List[str] = [
        "10슬롯 장비 스탯 집계",
        "희귀 및 몬스터 세트 효과 연산",
        "부위 피격 방어구 내구도 소모",
        "물리 피해 경감"
    ]
    traits: List[str] = field(default_factory=lambda: [
        "10슬롯 장비 스탯 집계",
        "희귀 및 몬스터 세트 효과 연산",
        "부위 피격 방어구 내구도 소모",
        "물리 피해 경감"
    ])

    EQUIPMENT_SET_REGISTRY: Dict[str, EquipmentSet] = {
        # === 1. 희귀 일반 장비 세트 (Rare / Epic General Sets) ===
        "set_royal_guard": EquipmentSet(
            set_id="set_royal_guard",
            name_ko="왕실 근위대 세트",
            category="rare_general",
            description_ko="왕실을 수호하는 직속 정예 근위 기사단의 정통 판금 중갑 세트.",
            bonuses={
                2: EquipmentSetBonus(
                    threshold=2,
                    name_ko="근위병의 규율",
                    stat_bonuses={"constitution": 2, "strength": 1},
                    defense=6,
                    traits=["경직 저항"],
                    passive_description="방어력 +6, 체력 +2, 근력 +1, 피격 시 경직 시간 단축"
                ),
                4: EquipmentSetBonus(
                    threshold=4,
                    name_ko="철벽의 맹세",
                    stat_bonuses={"constitution": 5, "strength": 3},
                    defense=16,
                    traits=["넉백 완전 면역", "철벽 수호"],
                    passive_description="방어력 +16, 근력 +3, 체력 +5, 넉백 및 밀림 완전 면역"
                )
            },
            traits=["왕실 근위대", "철벽 방어", "기사단 제식"]
        ),
        "set_shadow_assassin": EquipmentSet(
            set_id="set_shadow_assassin",
            name_ko="그림자 암살자 세트",
            category="rare_general",
            description_ko="어둠 속에서 소리 없이 대상을 암살하는 흑막 자객단의 칠흑 가죽 세트.",
            bonuses={
                2: EquipmentSetBonus(
                    threshold=2,
                    name_ko="소리 없는 발걸음",
                    stat_bonuses={"agility": 3, "crit_rate": 5},
                    defense=2,
                    damage=3,
                    traits=["발소리 감쇠 -10dB"],
                    passive_description="민첩 +3, 치명타율 +5%, 은신 중 이동 발소리 -10dB 감쇠"
                ),
                4: EquipmentSetBonus(
                    threshold=4,
                    name_ko="암습의 극의",
                    stat_bonuses={"agility": 7, "crit_damage": 25},
                    defense=4,
                    damage=8,
                    traits=["기습 필살", "그림자 은신"],
                    passive_description="민첩 +7, 공격력 +8, 치명타 피해 +25%, 기습 공격 시 확정 추가타"
                )
            },
            traits=["그림자 은신", "암살자 제식", "치명타 특화"]
        ),
        "set_ancient_arcanist": EquipmentSet(
            set_id="set_ancient_arcanist",
            name_ko="고대 비전 학자 세트",
            category="rare_general",
            description_ko="고대 제국의 순수 에테르 회로가 직조된 비전 로브 및 학자 장구류.",
            bonuses={
                2: EquipmentSetBonus(
                    threshold=2,
                    name_ko="에테르 감응",
                    stat_bonuses={"intelligence": 4, "max_mana": 30},
                    defense=2,
                    traits=["마력 회복 촉진"],
                    passive_description="지능 +4, 마나 최대치 +30, 마력 자연 회복력 향상"
                ),
                4: EquipmentSetBonus(
                    threshold=4,
                    name_ko="비전의 진리",
                    stat_bonuses={"intelligence": 10, "wisdom": 5, "max_mana": 80},
                    defense=5,
                    damage=6,
                    traits=["영창 단축 30%", "마나 절약 20%"],
                    passive_description="지능 +10, 지혜 +5, 영창 시간 30% 단축 및 스킬 소모 마나 20% 절감"
                )
            },
            traits=["고대 비전", "영창 단축", "에테르 마도"]
        ),
        "set_iron_wall_gladiator": EquipmentSet(
            set_id="set_iron_wall_gladiator",
            name_ko="강철벽 검투사 세트",
            category="rare_general",
            description_ko="피비린내 나는 콜로세움 모래밭에서 수백 번의 사선을 넘긴 투기장의 흉갑 세트.",
            bonuses={
                2: EquipmentSetBonus(
                    threshold=2,
                    name_ko="혈전의 투기",
                    stat_bonuses={"strength": 2, "constitution": 2},
                    defense=4,
                    damage=4,
                    traits=["투기 각성"],
                    passive_description="공격력 +4, 근력 +2, 체력 +2"
                ),
                4: EquipmentSetBonus(
                    threshold=4,
                    name_ko="콜로세움의 패왕",
                    stat_bonuses={"strength": 6, "constitution": 4, "crit_rate": 8},
                    defense=10,
                    damage=12,
                    traits=["처형 본능", "반격의 태세"],
                    passive_description="공격력 +12, 근력 +6, 빈사 상태(HP 30% 이하) 적 공격 시 치명타율 +20%"
                )
            },
            traits=["검투사", "처형 본능", "근접 난타"]
        ),
        "set_elven_ranger": EquipmentSet(
            set_id="set_elven_ranger",
            name_ko="엘프 순찰대 세트",
            category="rare_general",
            description_ko="깊은 수해의 가호를 받아 나뭇잎처럼 가볍고 바람처럼 빠른 순찰자의 녹색 가죽 세트.",
            bonuses={
                2: EquipmentSetBonus(
                    threshold=2,
                    name_ko="숲의 감각",
                    stat_bonuses={"agility": 2, "perception": 3},
                    defense=3,
                    damage=2,
                    traits=["야간 시야", "발자국 추적"],
                    passive_description="민첩 +2, 감각(지각) +3, 어둠 속 시야 확보"
                ),
                4: EquipmentSetBonus(
                    threshold=4,
                    name_ko="바람을 가르는 사수",
                    stat_bonuses={"agility": 6, "perception": 5, "crit_rate": 8},
                    defense=6,
                    damage=8,
                    traits=["백발백중", "곡사 명중 보정"],
                    passive_description="민첩 +6, 감각 +5, 치명타율 +8%, 원거리 활 사거리 +20%"
                )
            },
            traits=["엘프 사수", "정밀 사격", "자연 위장"]
        ),

        # === 2. 몬스터 소재 제작 세트 (Monster Material Craft Sets) ===
        "set_thunder_catfish": EquipmentSet(
            set_id="set_thunder_catfish",
            name_ko="뇌격 흑액 메기 세트",
            category="monster_material",
            description_ko="늪지대의 지배자 뇌격 흑액 메기의 발전 기관과 단단한 비늘을 무두질해 제작한 절연 세트.",
            bonuses={
                2: EquipmentSetBonus(
                    threshold=2,
                    name_ko="전격 저항 및 축전",
                    stat_bonuses={"max_mana": 20},
                    defense=4,
                    traits=["전격 저항 50%", "미세 방전"],
                    passive_description="전격 계통 피해 50% 반감 및 마나 최대치 +20"
                ),
                4: EquipmentSetBonus(
                    threshold=4,
                    name_ko="뇌전의 군주",
                    stat_bonuses={"max_mana": 50, "intelligence": 3},
                    defense=10,
                    damage=5,
                    traits=["전격 완전 흡수", "정전기 반격 충격파"],
                    passive_description="전격 피해를 흡수하여 마나로 전환하며 피격 시 25% 확률로 뇌격 방전 반격"
                )
            },
            traits=["뇌격 메기 소재", "전격 면역", "정전기 반격"]
        ),
        "set_dread_wyvern": EquipmentSet(
            set_id="set_dread_wyvern",
            name_ko="공포의 비룡 세트",
            category="monster_material",
            description_ko="화염 협곡을 지배하는 비룡의 단단한 용린과 날개 피막으로 단조한 붉은 중갑 세트.",
            bonuses={
                2: EquipmentSetBonus(
                    threshold=2,
                    name_ko="비룡의 가호",
                    stat_bonuses={"constitution": 2},
                    defense=6,
                    traits=["화염 경감 30%"],
                    passive_description="화염 피해 30% 경감 및 체력 +2"
                ),
                4: EquipmentSetBonus(
                    threshold=4,
                    name_ko="하늘의 지배자",
                    stat_bonuses={"constitution": 4, "strength": 3, "crit_damage": 15},
                    defense=14,
                    damage=8,
                    traits=["용의 위압감", "공중 기습 강화"],
                    passive_description="치명타 피해 +15%, 공격력 +8, 근력 +3, 적의 사기 10 저하"
                )
            },
            traits=["비룡 소재", "화염 내성", "용의 포효"]
        ),
        "set_abyssal_carapace": EquipmentSet(
            set_id="set_abyssal_carapace",
            name_ko="심해 갑각수 세트",
            category="monster_material",
            description_ko="심해의 고압을 견뎌낸 거대 갑각수의 외골격을 분쇄 가공하여 만든 중장갑.",
            bonuses={
                2: EquipmentSetBonus(
                    threshold=2,
                    name_ko="견고한 갑각",
                    stat_bonuses={"constitution": 3},
                    defense=8,
                    traits=["수중 행동 원활", "타격 내성"],
                    passive_description="방어력 +8, 체력 +3, 둔기 피해 20% 경감"
                ),
                4: EquipmentSetBonus(
                    threshold=4,
                    name_ko="심해의 난공불락",
                    stat_bonuses={"constitution": 6},
                    defense=20,
                    damage=0,
                    traits=["단단한 외골격", "충격 반사"],
                    passive_description="방어력 +20, 피격 시 공격자에게 충격 피해 4 반사"
                )
            },
            traits=["심해 갑각", "초고방어력", "충격 반사"]
        )
    }

    BODY_PART_SLOT_MAP: Dict[str, str] = {
        "머리": "head",
        "목": "neck",
        "눈": "face",
        "얼굴": "face",
        "가슴": "chest",
        "몸통": "chest",
        "심장": "chest",
        "배": "chest",
        "등": "cape",
        "어깨": "shoulders",
        "허리": "belt",
        "팔": "gloves",
        "손": "gloves",
        "손목": "gloves",
        "다리": "legs",
        "무릎": "legs",
        "관절": "legs",
        "허벅지": "legs",
        "발": "boots",
        "발목": "boots",
        "수납": "storage",
        "속옷": "innerwear"
    }

    @classmethod
    def get_equipped_items(cls, state: WorldState, entity: Any = None) -> List[Item]:
        """Returns all equipped Item objects for the entity (defaults to Player)."""
        target = entity if entity is not None else state.player
        if not hasattr(target, "equipment") or not target.equipment:
            return []

        eq = target.equipment
        single_slots = [
            "weapon", "head", "face", "chest", "legs", "boots", "gloves", "cape",
            "neck", "belt", "shoulders", "storage", "innerwear"
        ]
        equipped_item_ids: List[str] = []

        for s in single_slots:
            item_id = getattr(eq, s, None)
            if item_id:
                equipped_item_ids.append(item_id)

        # Multi-slots (rings, earrings, bracelets)
        for r_id in getattr(eq, "rings", []):
            if r_id:
                equipped_item_ids.append(r_id)
        for e_id in getattr(eq, "earrings", []):
            if e_id:
                equipped_item_ids.append(e_id)
        for b_id in getattr(eq, "bracelets", []):
            if b_id:
                equipped_item_ids.append(b_id)

        return [state.items[i_id] for i_id in equipped_item_ids if i_id in state.items]

    @classmethod
    def calculate_equipment_bonuses(cls, state: WorldState, entity: Any = None) -> Dict[str, Any]:
        """
        Calculates total defense, damage bonuses, and stat modifiers from all equipped items.
        """
        items = cls.get_equipped_items(state, entity)
        total_defense = 0
        total_damage = 0
        stat_bonuses: Dict[str, int] = {
            "strength": 0,
            "agility": 0,
            "intelligence": 0,
            "constitution": 0,
            "wisdom": 0,
            "luck": 0,
            "perception": 0,
            "crit_rate": 0,
            "crit_damage": 0,
            "max_health": 0,
            "max_mana": 0
        }

        equipped_sets: Dict[str, int] = {}

        for item in items:
            total_defense += getattr(item, "defense", 0)
            total_damage += getattr(item, "damage", 0)

            # Check properties for stat bonuses
            props = getattr(item, "properties", {}) or {}
            item_stat_mods = props.get("stat_bonuses", {})
            if isinstance(item_stat_mods, dict):
                for stat_k, stat_v in item_stat_mods.items():
                    # Normalize key
                    norm_k = stat_k.lower()
                    if norm_k in ["str", "strength", "근력"]:
                        stat_bonuses["strength"] += int(stat_v)
                    elif norm_k in ["agi", "dex", "agility", "민첩"]:
                        stat_bonuses["agility"] += int(stat_v)
                    elif norm_k in ["int", "intelligence", "지능"]:
                        stat_bonuses["intelligence"] += int(stat_v)
                    elif norm_k in ["con", "constitution", "체력", "건강"]:
                        stat_bonuses["constitution"] += int(stat_v)
                    elif norm_k in ["wis", "wisdom", "지혜"]:
                        stat_bonuses["wisdom"] += int(stat_v)
                    elif norm_k in ["luk", "luck", "cha", "행운", "매력"]:
                        stat_bonuses["luck"] += int(stat_v)
                    elif norm_k in ["per", "perception", "감각", "지각"]:
                        stat_bonuses["perception"] += int(stat_v)
                    elif norm_k in ["crit", "crit_rate", "치명타"]:
                        stat_bonuses["crit_rate"] += int(stat_v)
                    elif norm_k in ["crit_dmg", "crit_damage"]:
                        stat_bonuses["crit_damage"] += int(stat_v)
                    elif norm_k in ["hp", "max_hp", "max_health", "체력최대치"]:
                        stat_bonuses["max_health"] += int(stat_v)
                    elif norm_k in ["mp", "mana", "max_mana", "마나최대치"]:
                        stat_bonuses["max_mana"] += int(stat_v)

            # Check for set equipment identifier
            s_id = props.get("set_id") or getattr(item, "set_id", None)
            if s_id:
                equipped_sets[s_id] = equipped_sets.get(s_id, 0) + 1

        active_set_bonuses: List[Dict[str, Any]] = []
        active_traits: List[str] = []

        # Calculate set bonuses for all equipped sets
        for set_id, count in equipped_sets.items():
            eq_set = cls.EQUIPMENT_SET_REGISTRY.get(set_id)
            if not eq_set:
                continue

            for th in sorted(eq_set.bonuses.keys()):
                if count >= th:
                    bonus = eq_set.bonuses[th]
                    total_defense += bonus.defense
                    total_damage += bonus.damage
                    for stat_k, stat_v in bonus.stat_bonuses.items():
                        norm_k = stat_k.lower()
                        if norm_k in ["str", "strength", "근력"]:
                            stat_bonuses["strength"] += int(stat_v)
                        elif norm_k in ["agi", "dex", "agility", "민첩"]:
                            stat_bonuses["agility"] += int(stat_v)
                        elif norm_k in ["int", "intelligence", "지능"]:
                            stat_bonuses["intelligence"] += int(stat_v)
                        elif norm_k in ["con", "constitution", "체력", "건강"]:
                            stat_bonuses["constitution"] += int(stat_v)
                        elif norm_k in ["wis", "wisdom", "지혜"]:
                            stat_bonuses["wisdom"] += int(stat_v)
                        elif norm_k in ["luk", "luck", "cha", "행운", "매력"]:
                            stat_bonuses["luck"] += int(stat_v)
                        elif norm_k in ["per", "perception", "감각", "지각"]:
                            stat_bonuses["perception"] += int(stat_v)
                        elif norm_k in ["crit", "crit_rate", "치명타"]:
                            stat_bonuses["crit_rate"] += int(stat_v)
                        elif norm_k in ["crit_dmg", "crit_damage"]:
                            stat_bonuses["crit_damage"] += int(stat_v)
                        elif norm_k in ["hp", "max_hp", "max_health", "체력최대치"]:
                            stat_bonuses["max_health"] += int(stat_v)
                        elif norm_k in ["mp", "mana", "max_mana", "마나최대치"]:
                            stat_bonuses["max_mana"] += int(stat_v)

                    for tr in bonus.traits:
                        if tr not in active_traits:
                            active_traits.append(tr)

                    active_set_bonuses.append({
                        "set_id": set_id,
                        "set_name_ko": eq_set.name_ko,
                        "category": eq_set.category,
                        "threshold": th,
                        "bonus_name_ko": bonus.name_ko,
                        "passive_description": bonus.passive_description,
                        "defense": bonus.defense,
                        "damage": bonus.damage,
                        "stat_bonuses": dict(bonus.stat_bonuses),
                        "traits": list(bonus.traits)
                    })

        return {
            "total_defense": total_defense,
            "total_damage": total_damage,
            "stat_bonuses": stat_bonuses,
            "equipped_count": len(items),
            "equipped_sets": equipped_sets,
            "active_set_bonuses": active_set_bonuses,
            "active_traits": active_traits
        }

    @classmethod
    def get_active_set_bonuses(cls, state: WorldState, entity: Any = None) -> List[Dict[str, Any]]:
        """Returns all active set bonuses for the entity."""
        res = cls.calculate_equipment_bonuses(state, entity)
        return res.get("active_set_bonuses", [])

    @classmethod
    def get_slot_for_body_part(cls, target_part: str) -> str:
        """Maps specific targeted anatomy to equipment slot."""
        clean_part = target_part.strip().lower()
        return cls.BODY_PART_SLOT_MAP.get(clean_part, "chest")

    @classmethod
    def apply_armor_durability_and_mitigation(
        cls,
        state: WorldState,
        entity: Any,
        incoming_damage: int,
        target_part: str = ""
    ) -> Tuple[int, List[str]]:
        """
        Consumes durability of the targeted armor piece and slightly mitigates damage.
        Returns (mitigated_damage: int, logs: List[str]).
        """
        logs: List[str] = []
        if not hasattr(entity, "equipment") or not entity.equipment:
            return incoming_damage, logs

        slot = cls.get_slot_for_body_part(target_part) if target_part else "chest"
        item_id = getattr(entity.equipment, slot, None)
        # Fallback to chest if specific slot is empty
        if not item_id and slot != "chest":
            item_id = getattr(entity.equipment, "chest", None)

        if not item_id or item_id not in state.items:
            return incoming_damage, logs

        armor_item = state.items[item_id]
        # Durability loss
        dur_warn = EnchantEngine.consume_durability(armor_item, loss=1)
        if dur_warn:
            logs.append(dur_warn)

        # Damage reduction based on armor defense
        armor_def = getattr(armor_item, "defense", 0)
        mitigated = max(1, incoming_damage - (armor_def // 2))
        if armor_def > 0 and incoming_damage > mitigated:
            logs.append(f"[{armor_item.name}]이(가) 충격을 흡수하여 피해 {incoming_damage - mitigated} 경감 (내구도 -1)")

        return mitigated, logs
