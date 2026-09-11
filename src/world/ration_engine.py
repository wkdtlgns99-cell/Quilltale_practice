"""
Ration Spoilage & Water Quality Engine for Quilltale TRPG.
Deterministic tracking of food freshness, individual item decay/stack-splitting,
temperature/humidity accelerated spoilage, food preservation (salt, smoke, dry),
water purification, food poisoning, and dysentery epidemic integration.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging
import copy
import random

logger = logging.getLogger(__name__)


@dataclass
class FoodItemStatus:
    freshness: float = 100.0             # 신선도 (100.0: 갓 수확/조리 ~ 0.0: 썩은 폐기물)
    preservation_type: str = "raw"      # "raw" (생식품), "salted" (염장), "smoked" (훈제), "dried" (건조), "sealed" (밀폐/통조림)
    spoilage_rate_per_turn: float = 1.0 # 턴당 기본 부패 감쇄율
    is_spoiled: bool = False            # 39.0 이하 시 쉰내/변색
    is_rotten: bool = False             # 0.0 도달 시 부패/구더기
    origin_name: str = ""               # 원래 아이템 이름
    traits: List[str] = field(default_factory=lambda: ["food", "perishable"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "freshness": self.freshness,
            "preservation_type": self.preservation_type,
            "spoilage_rate_per_turn": self.spoilage_rate_per_turn,
            "is_spoiled": self.is_spoiled,
            "is_rotten": self.is_rotten,
            "origin_name": self.origin_name,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FoodItemStatus":
        return cls(
            freshness=float(data.get("freshness", 100.0)),
            preservation_type=data.get("preservation_type", "raw"),
            spoilage_rate_per_turn=float(data.get("spoilage_rate_per_turn", 1.0)),
            is_spoiled=bool(data.get("is_spoiled", False)),
            is_rotten=bool(data.get("is_rotten", False)),
            origin_name=data.get("origin_name", ""),
            traits=data.get("traits", ["food", "perishable"]),
        )


@dataclass
class PreservationMethodSpec:
    method_id: str
    name_ko: str
    decay_rate_multiplier: float        # 부패 속도 배율 (0.1 = 10배 오래 보존)
    shelf_life_turns_bonus: int         # 유통 기한 보너스 턴수
    required_materials: List[str]       # 필요 재료 (예: ["salt"])
    heat_source_required: bool = False  # 모닥불 등 열원 필요 여부
    traits: List[str] = field(default_factory=list)


PRESERVATION_METHODS: Dict[str, PreservationMethodSpec] = {
    "salt_cure": PreservationMethodSpec(
        method_id="salt_cure",
        name_ko="소금 염장",
        decay_rate_multiplier=0.10,
        shelf_life_turns_bonus=300,
        required_materials=["salt", "rock_salt", "암염", "소금"],
        heat_source_required=False,
        traits=["preservation", "salted", "shelf_life_extended"]
    ),
    "smoking": PreservationMethodSpec(
        method_id="smoking",
        name_ko="장작 훈제",
        decay_rate_multiplier=0.20,
        shelf_life_turns_bonus=200,
        required_materials=["firewood", "장작", "나뭇가지"],
        heat_source_required=True,
        traits=["preservation", "smoked", "wood_flavor"]
    ),
    "drying": PreservationMethodSpec(
        method_id="drying",
        name_ko="태양 건조",
        decay_rate_multiplier=0.15,
        shelf_life_turns_bonus=250,
        required_materials=[],
        heat_source_required=False,
        traits=["preservation", "dried", "lightweight"]
    ),
    "boiling_water": PreservationMethodSpec(
        method_id="boiling_water",
        name_ko="가열 비등 소독",
        decay_rate_multiplier=1.0,
        shelf_life_turns_bonus=0,
        required_materials=[],
        heat_source_required=True,
        traits=["purification", "sterilization", "safe_water"]
    )
}


class RationSpoilageEngine:
    """
    Deterministic Food Spoilage, Individual Item Management, and Water Purification Engine.
    """

    FOOD_KEYWORDS = {
        "bread", "meat", "apple", "ration", "cheese", "soup", "stew",
        "fish", "berry", "jerky", "water", "빵", "고기", "사과", "보존식",
        "치즈", "수프", "스튜", "생선", "열매", "육포", "식수", "물", "물병"
    }

    @classmethod
    def is_food_or_drink(cls, item: Any) -> bool:
        """Determines if an item is a perishable food or drink item."""
        if hasattr(item, "item_type") and item.item_type in ["food", "drink", "ration", "식량", "음식", "식수"]:
            return True
        name_lower = getattr(item, "name", "").lower()
        traits = getattr(item, "traits", [])
        if any(t in ["food", "drink", "perishable", "ration"] for t in traits):
            return True
        return any(k in name_lower for k in cls.FOOD_KEYWORDS)

    @classmethod
    def get_or_create_food_status(cls, item: Any) -> FoodItemStatus:
        """Initializes or retrieves FoodItemStatus for an item."""
        props = getattr(item, "properties", {})
        if "food_status" in props:
            raw_status = props["food_status"]
            if isinstance(raw_status, dict):
                status = FoodItemStatus.from_dict(raw_status)
                props["food_status"] = status
                return status
            elif isinstance(raw_status, FoodItemStatus):
                return raw_status

        # Determine initial decay rate based on name
        name_lower = getattr(item, "name", "").lower()
        decay = 1.0
        pres_type = "raw"
        if "육포" in name_lower or "jerky" in name_lower or "건어" in name_lower or "dried" in name_lower:
            decay = 0.15
            pres_type = "dried"
        elif "염장" in name_lower or "salted" in name_lower:
            decay = 0.10
            pres_type = "salted"
        elif "훈제" in name_lower or "smoked" in name_lower:
            decay = 0.20
            pres_type = "smoked"
        elif "생선" in name_lower or "fish" in name_lower:
            decay = 2.0  # 생선은 매우 빨리 상함
        elif "물" in name_lower or "water" in name_lower:
            decay = 0.2  # 물은 밀폐 수통에선 천천히 오염

        status = FoodItemStatus(
            freshness=100.0,
            preservation_type=pres_type,
            spoilage_rate_per_turn=decay,
            origin_name=getattr(item, "name", "음식")
        )
        props["food_status"] = status
        item.properties = props
        return status

    @classmethod
    def process_turn_spoilage(cls, state: Any, delta_minutes: int = 30) -> List[str]:
        """
        Processes spoilage for all food items in player's inventory and storage.
        Scales with elapsed game time (delta_minutes, default 30m = 1 turn).
        Accelerated by ambient temperature (ThermalEngine) and wetness/rain (WeatherEngine).
        User Rule 1: Individual tracking and stack splitting on spoilage.
        """
        logs = []
        player = getattr(state, "player", None)
        if not player:
            return logs

        # 1. Environmental Spoilage Multipliers
        env_multiplier = 1.0

        # Thermal heat acceleration
        temp = getattr(player, "body_temperature", 36.5)
        if temp >= 39.0:
            env_multiplier *= 2.5
        elif temp >= 37.5:
            env_multiplier *= 1.5

        # Wetness acceleration (곰팡이 및 세균 번식)
        wetness = getattr(player, "wetness", 0.0)
        if wetness >= 75.0:
            env_multiplier *= 2.2
        elif wetness >= 40.0:
            env_multiplier *= 1.4

        time_mult = max(0.1, delta_minutes / 30.0)

        # Iterate over inventory item IDs
        items_dict = getattr(state, "items", {})
        player_inv = list(player.inventory)

        for item_id in player_inv:
            item = items_dict.get(item_id)
            if not item or not cls.is_food_or_drink(item):
                continue

            status = cls.get_or_create_food_status(item)
            if status.is_rotten:
                continue  # Already rotten

            prev_freshness = status.freshness
            decay = status.spoilage_rate_per_turn * env_multiplier * time_mult
            status.freshness = max(0.0, status.freshness - decay)

            # Check Spoilage thresholds
            if status.freshness <= 0.0 and not status.is_rotten:
                status.is_rotten = True
                status.is_spoiled = True
                item.name = f"썩은 폐기물 ({status.origin_name})"
                item.description = f"파리와 구더기가 들끓고 지독한 악취를 풍기는 {status.origin_name}입니다. 먹으면 극심한 식중독과 이질에 걸립니다."
                item.traits = list(set(item.traits + ["rotten", "toxic", "inedible"]))
                logs.append(f"🪰 [식량 완전 부패] 가방 속의 [{status.origin_name}]이(가) 완전히 썩어 폐기물이 되었습니다!")

            elif status.freshness <= 39.0 and not status.is_spoiled:
                status.is_spoiled = True
                item.name = f"상하기 시작한 {status.origin_name}"
                item.description = f"시큼하고 불쾌한 쉰내가 올라오며 색이 변하기 시작한 {status.origin_name}입니다. 섭취 시 식중독 위험이 있습니다."
                item.traits = list(set(item.traits + ["spoiled"]))
                logs.append(f"⚠️ [식량 변질] 가방 속의 [{status.origin_name}]에서 쉰내가 나며 상하기 시작했습니다! (신선도: {status.freshness:.1f}/100)")

            item.properties["food_status"] = status

        return logs

    @classmethod
    def preserve_food(
        cls,
        state: Any,
        target_item: Any,
        method_id: str,
        material_item_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Preserves food item using salt, smoke, or drying.
        User Rule 1: Individual tracking - updates this specific item.
        """
        method = PRESERVATION_METHODS.get(method_id)
        if not method:
            return False, "유효하지 않은 보존 처리 방식입니다."

        if not cls.is_food_or_drink(target_item):
            return False, "식량이나 음료가 아닌 물품은 보존 가공할 수 없습니다."

        status = cls.get_or_create_food_status(target_item)
        if status.is_rotten:
            return False, "이미 썩어버린 음식은 보존 처리할 수 없습니다."

        player = getattr(state, "player", None)

        # Check required materials
        if method.required_materials:
            found_mat_id = None
            for inv_id in player.inventory:
                inv_item = state.items.get(inv_id)
                if inv_item:
                    name_lower = inv_item.name.lower()
                    if any(req in name_lower or req == inv_id for req in method.required_materials):
                        found_mat_id = inv_id
                        break
            if not found_mat_id:
                mat_names = ", ".join(method.required_materials[:2])
                return False, f"보존 처리를 위해 [{mat_names}] 재료가 필요합니다."
            # Consume material item
            player.inventory.remove(found_mat_id)

        # Apply Preservation
        status.preservation_type = method.method_id
        status.spoilage_rate_per_turn = round(status.spoilage_rate_per_turn * method.decay_rate_multiplier, 2)
        status.freshness = min(100.0, status.freshness + 10.0)  # Minor curing freshening
        status.traits = list(set(status.traits + method.traits))

        # Rename item
        if method_id == "salt_cure":
            target_item.name = f"염장된 {status.origin_name}"
        elif method_id == "smoking":
            target_item.name = f"훈제된 {status.origin_name}"
        elif method_id == "drying":
            target_item.name = f"건조된 {status.origin_name}"

        target_item.properties["food_status"] = status
        return True, f"🧂 [{method.name_ko} 완료] [{status.origin_name}]을(를) 성공적으로 가공하여 보존 수명을 {int(1/method.decay_rate_multiplier)}배 연장했습니다!"

    @classmethod
    def purify_water(cls, state: Any, water_item: Any) -> Tuple[bool, str]:
        """Boils and purifies contaminated water."""
        if not cls.is_food_or_drink(water_item) or "물" not in water_item.name and "water" not in water_item.name.lower():
            return False, "물이 아닌 물품은 비등 소독할 수 없습니다."

        status = cls.get_or_create_food_status(water_item)
        status.freshness = 100.0
        status.is_rotten = False
        status.is_spoiled = False
        status.preservation_type = "boiled"
        status.traits = [t for t in status.traits if t not in ["toxic", "contaminated", "dirty"]] + ["pure", "safe_water"]

        water_item.name = "끓여서 식힌 깨끗한 식수"
        water_item.description = "모닥불에 펄펄 끓여 기생충과 역병균을 박멸한 깨끗하고 안전한 음용수입니다."
        water_item.properties["food_status"] = status
        return True, "🔥 [비등 소독 완료] 물을 펄펄 끓여 모든 오염원과 기생충을 박멸했습니다. 안전하게 음용할 수 있습니다."

    @classmethod
    def consume_ration(cls, state: Any, consumer: Any, item: Any) -> List[str]:
        """
        Consumes food or water.
        Triggers hunger relief, stamina, or food poisoning / dysentery if spoiled or rotten.
        """
        logs = []
        if not cls.is_food_or_drink(item):
            logs.append(f"{item.name}은(는) 먹거나 마실 수 있는 물품이 아닙니다.")
            return logs

        status = cls.get_or_create_food_status(item)
        hunger_relief = 25
        stamina_gain = 15

        # 1. Fresh Food (80.0 ~ 100.0)
        if status.freshness >= 80.0:
            if hasattr(consumer, "hunger"):
                consumer.hunger = max(0, consumer.hunger - hunger_relief)
            if hasattr(consumer, "stamina") and hasattr(consumer, "max_stamina"):
                consumer.stamina = min(consumer.max_stamina, consumer.stamina + stamina_gain)
            logs.append(f"🍖 [식사 완료] 신선한 [{item.name}]을(를) 섭취하여 허기가 {hunger_relief} 해소되고 기력이 {stamina_gain} 회복되었습니다.")

        # 2. Stale Food (40.0 ~ 79.9)
        elif status.freshness >= 40.0:
            if hasattr(consumer, "hunger"):
                consumer.hunger = max(0, consumer.hunger - int(hunger_relief * 0.8))
            logs.append(f"🥖 [식사 완료] 조금 눅눅하고 굳은 [{item.name}]을(를) 섭취했습니다. 약간의 텁텁함 외에는 먹을 만합니다.")

        # 3. Spoiled Food (1.0 ~ 39.9) - Food Poisoning Risk
        elif status.freshness > 0.0:
            if hasattr(consumer, "hunger"):
                consumer.hunger = max(0, consumer.hunger - int(hunger_relief * 0.4))
            logs.append(f"🤢 [상한 음식 섭취] 시큼한 쉰내가 진동하는 [{item.name}]을(를) 억지로 삼켰습니다.")
            
            # 60% chance of food poisoning
            if random.random() < 0.60:
                if hasattr(consumer, "health"):
                    consumer.health = max(1, consumer.health - 6)
                if hasattr(consumer, "stamina"):
                    consumer.stamina = max(0, consumer.stamina - 20)
                logs.append(f"🤮 [급성 식중독] 위장이 뒤틀리는 복통과 함께 구토를 일으켜 6의 체력 피해와 20의 기력을 잃었습니다!")

        # 4. Rotten Food (0.0) or Contaminated Water - Severe Dysentery Integration
        else:
            logs.append(f"☠️ [썩은 폐기물 섭취] 썩은 내와 독기가 퍼진 [{item.name}]을(를) 삼키자마자 위장이 타는 듯한 격통이 일어납니다!")
            if hasattr(consumer, "health"):
                consumer.health = max(1, consumer.health - 15)
            if hasattr(consumer, "stamina"):
                consumer.stamina = 0

            # Epidemic integration: Dysentery attempt
            try:
                from src.world.disease_engine import EpidemicEngine
                inf_result = EpidemicEngine.attempt_infection(
                    target=consumer,
                    disease_id="dysentery",
                    state=state,
                    base_dc_bonus=2
                )
                logs.append(f"🦠 {inf_result.message_ko}")
            except Exception as e:
                logger.warning(f"Failed to trigger epidemic dysentery: {e}")

        # Remove consumed item from consumer's inventory
        if hasattr(consumer, "inventory") and item.id in consumer.inventory:
            consumer.inventory.remove(item.id)

        return logs
