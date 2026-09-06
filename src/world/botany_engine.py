"""
Wild Botany, Herbalism & Poisonous Lookalike Engine for Quilltale TRPG.
Deterministic calculation of terrain plant foraging, botany INT/WIS checks,
dangerous poisonous lookalike misidentification, precise re-identification,
and consumption/remedy effects integrated with EpidemicEngine and RationSpoilageEngine.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging
import random

logger = logging.getLogger(__name__)


@dataclass
class PlantSpec:
    plant_id: str
    name_ko: str
    category: str                         # "medicinal", "edible", "poisonous", "arcane"
    habitat_terrains: List[str]           # forest, mountain, swamp, cave, plains
    forage_dc: int                        # 채집 난이도 DC
    identify_dc: int                      # 정밀 감별 DC
    health_restore: int = 0
    hunger_relief: int = 0
    stamina_restore: int = 0
    poison_damage: int = 0
    inflicted_status: Optional[str] = None
    remedy_for_diseases: List[str] = field(default_factory=list)
    lookalike_poison_id: Optional[str] = None # 외형이 흡사한 맹독 유사종 ID
    description: str = ""
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plant_id": self.plant_id,
            "name_ko": self.name_ko,
            "category": self.category,
            "habitat_terrains": self.habitat_terrains,
            "forage_dc": self.forage_dc,
            "identify_dc": self.identify_dc,
            "health_restore": self.health_restore,
            "hunger_relief": self.hunger_relief,
            "stamina_restore": self.stamina_restore,
            "poison_damage": self.poison_damage,
            "inflicted_status": self.inflicted_status,
            "remedy_for_diseases": self.remedy_for_diseases,
            "lookalike_poison_id": self.lookalike_poison_id,
            "description": self.description,
            "traits": self.traits,
        }


PLANT_REGISTRY: Dict[str, PlantSpec] = {
    # -------------------------------------------------------------
    # 1. 약초 및 식용 식물 (Genuine Plants)
    # -------------------------------------------------------------
    "blood_moss": PlantSpec(
        plant_id="blood_moss",
        name_ko="지혈 이끼",
        category="medicinal",
        habitat_terrains=["forest", "cave", "swamp"],
        forage_dc=11,
        identify_dc=12,
        health_restore=12,
        remedy_for_diseases=["corpse_decay_fever", "blood_leech_parasite"],
        lookalike_poison_id="red_corpse_moss",
        description="습한 바위틈에 자라는 붉은빛 이끼. 상처에 으깨 바르면 피가 즉시 멎고 감염을 억제한다.",
        traits=["herb", "medicinal", "hemostatic", "forest"]
    ),
    "willow_bark": PlantSpec(
        plant_id="willow_bark",
        name_ko="해열 버들껍질",
        category="medicinal",
        habitat_terrains=["forest", "plains", "river"],
        forage_dc=10,
        identify_dc=11,
        health_restore=8,
        stamina_restore=10,
        remedy_for_diseases=["black_plague", "corpse_decay_fever"],
        description="강가 버드나무의 내피. 끓여 마시면 두통과 고열이 씻은 듯이 가라앉는다.",
        traits=["herb", "medicinal", "antipyretic", "fever_cure"]
    ),
    "wild_pine_mushroom": PlantSpec(
        plant_id="wild_pine_mushroom",
        name_ko="자연산 송이버섯",
        category="edible",
        habitat_terrains=["forest", "mountain"],
        forage_dc=13,
        identify_dc=14,
        hunger_relief=30,
        stamina_restore=15,
        lookalike_poison_id="destroying_angel",
        description="깊은 솔숲에서 자라나는 귀한 버섯. 짙은 솔향과 함께 풍부한 영양을 제공한다.",
        traits=["food", "fungus", "edible", "delicious"]
    ),
    "wild_ramson": PlantSpec(
        plant_id="wild_ramson",
        name_ko="산마늘(명이나물)",
        category="edible",
        habitat_terrains=["mountain", "forest"],
        forage_dc=11,
        identify_dc=13,
        hunger_relief=20,
        stamina_restore=10,
        lookalike_poison_id="lily_of_the_valley",
        description="알싸한 마늘 향이 나는 산나물. 피로를 회복하고 기력을 북돋아 준다.",
        traits=["food", "plant", "edible", "invigorating"]
    ),
    "lingzhi_mushroom": PlantSpec(
        plant_id="lingzhi_mushroom",
        name_ko="천년 묵은 영지초",
        category="medicinal",
        habitat_terrains=["mountain", "forest", "cliff"],
        forage_dc=16,
        identify_dc=16,
        health_restore=35,
        stamina_restore=50,
        remedy_for_diseases=["black_plague", "cave_spore_mycosis", "rabies_madness"],
        lookalike_poison_id="poison_fire_coral",
        description="오래된 고목에서 영험한 기운을 머금고 자라는 전설의 명약 버섯.",
        traits=["herb", "legendary", "super_remedy", "panacea"]
    ),
    "abyssal_blue_moss": PlantSpec(
        plant_id="abyssal_blue_moss",
        name_ko="심연 푸른 발광이끼",
        category="arcane",
        habitat_terrains=["cave", "dungeon", "subterranean"],
        forage_dc=14,
        identify_dc=15,
        health_restore=5,
        stamina_restore=20,
        description="지하 깊은 암벽에서 푸른 인광을 내뿜는 마나 이끼. 섭취 시 마나 20을 즉시 회복한다.",
        traits=["herb", "arcane", "mana_recovery", "subterranean"]
    ),

    # -------------------------------------------------------------
    # 2. 맹독성 유사종 (Poisonous Lookalikes)
    # -------------------------------------------------------------
    "red_corpse_moss": PlantSpec(
        plant_id="red_corpse_moss",
        name_ko="시체독 썩은이끼",
        category="poisonous",
        habitat_terrains=["cave", "swamp"],
        forage_dc=12,
        identify_dc=14,
        poison_damage=15,
        inflicted_status="sepsis",
        description="지혈 이끼와 흡사하게 생겼으나 시체의 부패 가스를 먹고 자라 극심한 패혈증을 유발한다.",
        traits=["poison", "lookalike", "toxic", "decay"]
    ),
    "destroying_angel": PlantSpec(
        plant_id="destroying_angel",
        name_ko="독우산광대버섯 (죽음의 천사)",
        category="poisonous",
        habitat_terrains=["forest", "mountain"],
        forage_dc=12,
        identify_dc=15,
        poison_damage=30,
        inflicted_status="severe_poison",
        description="송이버섯과 형태가 매우 흡사한 순백색 버섯. 섭취 시 간세포를 파괴하여 피를 토하게 만든다.",
        traits=["poison", "deadly", "fungus", "lookalike"]
    ),
    "lily_of_the_valley": PlantSpec(
        plant_id="lily_of_the_valley",
        name_ko="은방울꽃 (맹독초)",
        category="poisonous",
        habitat_terrains=["mountain", "forest"],
        forage_dc=11,
        identify_dc=14,
        poison_damage=25,
        inflicted_status="cardiac_arrest",
        description="산마늘의 잎과 100% 동일하게 생긴 잎사귀. 치명적인 강심배당체가 들어있어 심정지를 유발한다.",
        traits=["poison", "deadly", "cardiac_toxin", "lookalike"]
    ),
    "poison_fire_coral": PlantSpec(
        plant_id="poison_fire_coral",
        name_ko="붉은사슴뿔버섯",
        category="poisonous",
        habitat_terrains=["mountain", "forest"],
        forage_dc=15,
        identify_dc=17,
        poison_damage=45,
        inflicted_status="multi_organ_failure",
        description="영지초의 어린 개체와 꼭 닮은 진홍빛 뿔모양 버섯. 단 한 모금으로도 다발성 장기부전을 일으키는 맹독종.",
        traits=["poison", "fatal", "lookalike", "necrosis"]
    )
}


class HerbalismBotanyEngine:
    """
    Deterministic Botany Foraging, Plant Identification, and Poisonous Lookalike Mechanics.
    """

    @classmethod
    def forage(
        cls,
        gatherer: Any,
        location: Any,
        state: Any,
        target_plant_id: Optional[str] = None,
        fixed_roll: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Attempts to forage plants in the current terrain.
        Rolls d20 + INT/WIS mod vs plant forage DC.
        Critical failure (1) or missing DC by 5+ causes gathering a poisonous lookalike!
        """
        # Determine applicable plants for terrain
        loc_terrain = getattr(location, "terrain_type", getattr(location, "location_category", "forest")).lower()
        candidates = [
            p for p in PLANT_REGISTRY.values()
            if p.category in ["medicinal", "edible", "arcane"] and any(t in loc_terrain for t in p.habitat_terrains)
        ]
        if not candidates:
            candidates = [PLANT_REGISTRY["blood_moss"], PLANT_REGISTRY["willow_bark"]]

        if target_plant_id and target_plant_id in PLANT_REGISTRY:
            target_plant = PLANT_REGISTRY[target_plant_id]
        else:
            target_plant = random.choice(candidates)

        # Gatherer Stat check: max(INT, WIS)
        int_mod = (getattr(gatherer, "intelligence", 10) - 10) // 2
        wis_mod = (getattr(gatherer, "wisdom", 10) - 10) // 2
        gather_bonus = max(int_mod, wis_mod)

        roll = random.randint(1, 20) if fixed_roll is None else fixed_roll
        total = roll + gather_bonus

        # 1. Critical Failure (1) or failure by 5+ -> Poisonous Lookalike Trap!
        if (roll == 1 or total < target_plant.forage_dc - 4) and target_plant.lookalike_poison_id:
            poison_spec = PLANT_REGISTRY[target_plant.lookalike_poison_id]
            # Item is registered with the lookalike's disguised name
            item_id = f"item_{poison_spec.plant_id}_{random.randint(100, 999)}"
            plant_item = {
                "id": item_id,
                "name": f"야생에서 캔 {target_plant.name_ko}", # Disguised display name
                "true_spec_id": poison_spec.plant_id,
                "is_identified": False,
                "is_poisonous_lookalike": True,
                "origin_target_name": target_plant.name_ko,
                "traits": list(poison_spec.traits) + ["unidentified", "botany_foraged"]
            }

            msg = (
                f"🌿 [채집 성공?] {gatherer.name}이(가) 풀숲을 헤치며 [{target_plant.name_ko}]을(를) 채집했습니다! "
                f"(판정: {roll}+{gather_bonus}={total} vs DC {target_plant.forage_dc})\n"
                f"   * ⚠️ [식물학 판정 불안정] 식물의 잎맥과 색조가 미묘하게 불길하지만, 겉보기엔 그럴싸해 보입니다."
            )
            return {
                "success": True,
                "is_lookalike": True,
                "plant_data": plant_item,
                "message_ko": msg,
                "roll": roll,
                "total": total
            }

        # 2. Normal Failure
        elif total < target_plant.forage_dc:
            return {
                "success": False,
                "is_lookalike": False,
                "plant_data": None,
                "message_ko": f"🍂 [채집 실패] 주변 수풀을 샅샅이 뒤졌으나 쓸 만한 약초나 식용 식물을 발견하지 못했습니다. (판정: {roll}+{gather_bonus}={total} vs DC {target_plant.forage_dc})",
                "roll": roll,
                "total": total
            }

        # 3. Success -> Genuine Plant
        item_id = f"item_{target_plant.plant_id}_{random.randint(100, 999)}"
        plant_item = {
            "id": item_id,
            "name": target_plant.name_ko,
            "true_spec_id": target_plant.plant_id,
            "is_identified": True,
            "is_poisonous_lookalike": False,
            "origin_target_name": target_plant.name_ko,
            "traits": list(target_plant.traits) + ["botany_foraged"]
        }
        msg = f"🌿 [채집 성공] {gatherer.name}이(가) 신선하고 상태가 훌륭한 [{target_plant.name_ko}]을(를) 채집했습니다! (판정: {roll}+{gather_bonus}={total} vs DC {target_plant.forage_dc})"
        return {
            "success": True,
            "is_lookalike": False,
            "plant_data": plant_item,
            "message_ko": msg,
            "roll": roll,
            "total": total
        }

    @classmethod
    def identify_plant(
        cls,
        identifier: Any,
        plant_item_data: Dict[str, Any],
        fixed_roll: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Precisely inspects a foraged plant to uncover if it's a genuine herb or a deadly lookalike.
        Uses Perception / Intelligence check vs Plant identify_dc.
        """
        true_spec_id = plant_item_data.get("true_spec_id", "")
        spec = PLANT_REGISTRY.get(true_spec_id)
        if not spec:
            return False, "알 수 없는 기괴한 식물 표본입니다."

        per_mod = (getattr(identifier, "perception", 10) - 10) // 2
        int_mod = (getattr(identifier, "intelligence", 10) - 10) // 2
        id_bonus = max(per_mod, int_mod)

        roll = random.randint(1, 20) if fixed_roll is None else fixed_roll
        total = roll + id_bonus

        if total >= spec.identify_dc:
            plant_item_data["is_identified"] = True
            if plant_item_data.get("is_poisonous_lookalike"):
                # Reveal the deception!
                plant_item_data["name"] = f"맹독 식물 [{spec.name_ko}]"
                return True, (
                    f"🔍 [식물 정밀 감별 성공!] 식물학 지식({total} vs DC {spec.identify_dc})으로 검증한 결과, "
                    f"이 식물은 안전한 [{plant_item_data.get('origin_target_name')}]이 아니라 "
                    f"치명적인 맹독 유사종 [{spec.name_ko}]임이 밝혀졌습니다! 먹었다면 즉사할 뻔했습니다!"
                )
            else:
                return True, f"🔍 [식물 정밀 감별 성공] {spec.name_ko}의 잎과 줄기가 완벽히 검증되었습니다. ({spec.description})"
        else:
            return False, f"❓ [감별 실패] 약초 도감과 대조해 보았으나 이 식물이 진짜인지 유사종인지 확신할 수 없습니다. (판정: {total} vs DC {spec.identify_dc})"

    @classmethod
    def consume_plant(
        cls,
        consumer: Any,
        plant_item_data: Dict[str, Any],
        state: Optional[Any] = None
    ) -> List[str]:
        """
        Consumes or brews the plant.
        Applies medicinal benefits, or triggers deadly lookalike toxins.
        """
        logs = []
        true_spec_id = plant_item_data.get("true_spec_id", "")
        spec = PLANT_REGISTRY.get(true_spec_id)
        if not spec:
            logs.append("식물을 섭취했으나 아무런 반응이 없습니다.")
            return logs

        # 1. Poisonous Lookalike Case
        if spec.category == "poisonous" or plant_item_data.get("is_poisonous_lookalike"):
            dmg = spec.poison_damage
            consumer.health = max(1, consumer.health - dmg)
            logs.append(
                f"☠️ [맹독 유사종 중독!] 삼키는 순간 식도가 타들어가고 전신에 극심한 마비가 번집니다! "
                f"이것은 진짜 약초가 아니라 [{spec.name_ko}]이었습니다! ({dmg}의 치명적 독성 피해, 현재 HP: {consumer.health})"
            )
            # Status effect integration
            if spec.inflicted_status:
                logs.append(f"⚠️ [치명적 상태이상] [{spec.name_ko}]의 독소로 인해 [{spec.inflicted_status}] 증세가 격발되었습니다!")

        # 2. Genuine Medicinal / Edible / Arcane Case
        else:
            if spec.health_restore > 0:
                consumer.health = min(getattr(consumer, "max_health", 100), consumer.health + spec.health_restore)
                logs.append(f"💚 [{spec.name_ko} 복용] 상처가 아물며 체력이 {spec.health_restore} 회복되었습니다.")
            if spec.stamina_restore > 0 and hasattr(consumer, "stamina"):
                consumer.stamina = min(getattr(consumer, "max_stamina", 100), consumer.stamina + spec.stamina_restore)
                logs.append(f"⚡ 기력이 {spec.stamina_restore} 충전되었습니다.")
            if spec.hunger_relief > 0 and hasattr(consumer, "hunger"):
                consumer.hunger = max(0, consumer.hunger - spec.hunger_relief)
                logs.append(f"🍖 허기가 {spec.hunger_relief} 해소되었습니다.")
            if spec.plant_id == "abyssal_blue_moss" and hasattr(consumer, "mana"):
                consumer.mana = min(getattr(consumer, "max_mana", 50), consumer.mana + 20)
                logs.append("✨ 신비로운 푸른 마나가 혈맥을 타고 흘러 마나 20이 회복되었습니다.")

        return logs
