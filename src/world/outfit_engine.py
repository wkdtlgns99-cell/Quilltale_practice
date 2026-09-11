"""
Deterministic Outfit, Storage, Weapon Mount & Layered Garment Mechanics Engine for Quilltale TRPG.
Deterministically resolves:
1. Storage Gear & Encumbrance: Backpack carry capacity expansion (+15~35kg), weight encumbrance tiers & movement/fatigue penalties.
2. Quick-Slots: Belt pouches / thigh pouches allowing fast item/consumable access.
3. Weapon Mounts: Quivers (0.0s draw delay vs +0.5s without), Scabbards (quick-draw opening crit bonus +30% crit dmg, +10% crit rate).
4. Innerwear & Chafing: Gambeson cushioning heavy plate armor against friction chafing/bruising; stealth tights footstep noise reduction (-6dB).
5. Eyewear Mechanics: Glasses/monocles inspection/appraisal bonuses (+25% appraisal check), glass breakage hazard upon facial critical hits.
6. Synchronizer: Two-way synchronization between EquipmentSlots and 5-layer ClothingLayer visual model.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import logging
import random

from src.world.state import WorldState, Item, Player, NPC, ClothingLayer

logger = logging.getLogger(__name__)


@dataclass
class EncumbranceStatus:
    current_weight_kg: float
    max_carry_weight_kg: float
    backpack_bonus_kg: float
    encumbrance_ratio: float
    status_level: str                       # "light" (<50%), "normal" (50~100%), "heavy" (100~130%), "overburdened" (>130%)
    speed_penalty_mps: float                # 이동 속도 감소치 (m/s)
    fatigue_multiplier: float               # 이동/행동 시 피로도 소모 배율
    can_sprint: bool                        # 전력 질주 가능 여부
    summary_ko: str                         # 한글 상태 요약
    traits: List[str] = field(default_factory=lambda: ["적재 하중", "소지 중량", "가방 용량"])


@dataclass
class ArmorChafingResult:
    has_chafing: bool                       # 갑옷 마찰 쓸림 발생 여부
    reason_ko: str                          # 원인 설명
    penalty_active: bool                    # 디버프 적용 여부
    blunt_mitigation_pct: float             # 갬비슨 충격 흡수 보너스 (10% 등)
    innerwear_name: str                     # 착용 중인 이너웨어 명칭
    armor_name: str                         # 착용 중인 갑옷 명칭
    summary_ko: str                         # 결과 요약
    traits: List[str] = field(default_factory=lambda: ["갑옷 마찰", "이너웨어 완충", "피부 보호"])


@dataclass
class QuickDrawResult:
    eligible: bool                          # 발도술/속사 기습 보너스 적용 가능 여부
    crit_damage_bonus_pct: float            # 치명타 피해량 추가 보너스 (%)
    crit_rate_bonus_pct: float              # 치명타율 추가 보너스 (%)
    weapon_mount_type: str                  # "scabbard" | "holster" | "none"
    summary_ko: str                         # 결과 요약
    traits: List[str] = field(default_factory=lambda: ["발도술", "기습 치명타", "칼집 거치"])


@dataclass
class EyewearHazardResult:
    is_shattered: bool                      # 렌즈 파손 여부
    eyewear_name: str                       # 착용 안경 명칭
    debuff_applied: str                     # 적용된 디버프 명칭
    summary_ko: str                         # 결과 요약
    traits: List[str] = field(default_factory=lambda: ["안면 피격", "안경 파손 위험", "시야 결손"])


@dataclass
class BackpackSpec:
    backpack_id: str
    name_ko: str
    description: str
    volume_liters: float                    # 가방 내부 용적 (L)
    safe_weight_limit_kg: float             # 안전 적재 하중 (kg)
    tear_weight_limit_kg: float             # 파손/찢어짐 한계 하중 (kg)
    max_item_size: str = "small"            # "small", "medium", "heavy"
    traits: List[str] = field(default_factory=list)


@dataclass
class BackpackStorageStatus:
    backpack_name: str
    current_volume_liters: float
    max_volume_liters: float
    current_stored_weight_kg: float
    safe_weight_limit_kg: float
    tear_weight_limit_kg: float
    is_overfilled_volume: bool
    is_overweight: bool
    tear_risk_pct: float
    is_torn: bool
    spilled_item_names: List[str] = field(default_factory=list)
    summary_ko: str = ""
    traits: List[str] = field(default_factory=lambda: ["가방 규격", "용량 한계", "찢어짐 물리"])


BACKPACK_SPECS: Dict[str, BackpackSpec] = {
    "small_daypack": BackpackSpec(
        backpack_id="small_daypack",
        name_ko="소형 전술 배낭",
        description="가벼운 슬링백 또는 소형 데이팩. 작은 생존 도구와 소품만 수납 가능.",
        volume_liters=18.0,
        safe_weight_limit_kg=12.0,
        tear_weight_limit_kg=18.0,
        max_item_size="small",
        traits=["small_bag", "daypack", "tactical", "light"]
    ),
    "medium_traveler_pack": BackpackSpec(
        backpack_id="medium_traveler_pack",
        name_ko="중형 여행자 배낭",
        description="모험가들이 널리 애용하는 표준 가죽 배낭. 중형 장비와 식량 수납 가능.",
        volume_liters=40.0,
        safe_weight_limit_kg=25.0,
        tear_weight_limit_kg=35.0,
        max_item_size="medium",
        traits=["medium_bag", "traveler_pack", "standard"]
    ),
    "military_full_rucksack": BackpackSpec(
        backpack_id="military_full_rucksack",
        name_ko="대형 군장 배낭 (완전군장)",
        description="육군 완전군장 규격의 대용량 군용 배낭. 침낭, 텐트, 중화기 결속 가능.",
        volume_liters=75.0,
        safe_weight_limit_kg=45.0,
        tear_weight_limit_kg=60.0,
        max_item_size="heavy",
        traits=["large_bag", "military_rucksack", "full_kit", "heavy_duty"]
    ),
}


@dataclass
class OutfitMechanicsEngine:
    TRAITS: List[str] = field(default_factory=lambda: [
        "5레이어 복식 의장",
        "수납 가방 하중 확장",
        "허벅지 파우치 퀵슬롯",
        "화살통 즉시 장전",
        "칼집 발도술 기습 크리티컬",
        "갬비슨 판금 마찰 완충",
        "은신 타이즈 소음 감쇠",
        "단안경 감정 보너스 및 파손 위험"
    ])
    traits: List[str] = field(default_factory=lambda: [
        "5레이어 복식 의장",
        "수납 가방 하중 확장",
        "허벅지 파우치 퀵슬롯",
        "화살통 즉시 장전",
        "칼집 발도술 기습 크리티컬",
        "갬비슨 판금 마찰 완충",
        "은신 타이즈 소음 감쇠",
        "단안경 감정 보너스 및 파손 위험"
    ])

    BASE_CARRY_WEIGHT_KG: float = 20.0
    STR_CARRY_FACTOR: float = 3.0
    DEFAULT_BACKPACK_CAPACITY_KG: float = 25.0
    DEFAULT_QUICK_DRAW_CRIT_DMG: float = 30.0
    DEFAULT_QUICK_DRAW_CRIT_RATE: float = 10.0
    DEFAULT_QUIVER_RELOAD_DELAY_PENALTY: float = 0.5
    DEFAULT_APPRAISAL_BONUS_PCT: int = 25
    DEFAULT_STEALTH_TIGHTS_NOISE_REDUCTION_DB: float = 6.0

    @classmethod
    def calculate_carry_capacity(cls, entity: Any, state: WorldState) -> Tuple[float, float, float]:
        """
        Calculates (total_capacity_kg, base_capacity_kg, storage_bonus_kg).
        Base capacity = 20kg + max(0, STR - 10) * 3kg.
        Storage gear (backpack/bag in storage slot or bags_storage) adds +15~35kg.
        """
        str_val = getattr(entity, "effective_strength", getattr(entity, "strength", 10))
        base_capacity = cls.BASE_CARRY_WEIGHT_KG + max(0, str_val - 10) * cls.STR_CARRY_FACTOR

        storage_bonus = 0.0
        # 1. Check storage equipment slot
        eq = getattr(entity, "equipment", None)
        if eq and getattr(eq, "storage", None):
            s_id = eq.storage
            if s_id in state.items:
                s_item = state.items[s_id]
                props = getattr(s_item, "properties", {}) or {}
                storage_bonus = float(props.get("carry_capacity_bonus", cls.DEFAULT_BACKPACK_CAPACITY_KG))
        
        # 2. Check visual outfit bags_storage if no equipment slot item
        if storage_bonus == 0.0 and hasattr(entity, "visual") and entity.visual:
            outfit = getattr(entity.visual, "outfit", None)
            if outfit and outfit.bags_storage:
                for b_name in outfit.bags_storage:
                    b_lower = b_name.lower()
                    if any(kw in b_lower for kw in ["백팩", "배낭", "backpack", "대형 가방"]):
                        storage_bonus = max(storage_bonus, cls.DEFAULT_BACKPACK_CAPACITY_KG)
                    elif any(kw in b_lower for kw in ["크로스백", "행랑", "traveler pouch", "가방"]):
                        storage_bonus = max(storage_bonus, 15.0)

        total_capacity = round(base_capacity + storage_bonus, 1)
        return total_capacity, round(base_capacity, 1), round(storage_bonus, 1)

    @classmethod
    def calculate_inventory_weight(cls, entity: Any, state: WorldState) -> float:
        """Calculates total physical weight (kg) of all inventory and equipped items."""
        total_weight = 0.0
        inv_ids = getattr(entity, "inventory", [])
        for i_id in inv_ids:
            if i_id in state.items:
                total_weight += getattr(state.items[i_id], "weight", 1.0)

        # Equipped items (equipped items carried on body)
        from src.world.equipment import EquipmentEngine
        eq_items = EquipmentEngine.get_equipped_items(state, entity)
        for it in eq_items:
            # Avoid double-counting if item is both in inventory and equipment
            if it.id not in inv_ids:
                total_weight += getattr(it, "weight", 1.0)

        return round(total_weight, 1)

    @classmethod
    def evaluate_encumbrance(cls, entity: Any, state: WorldState) -> EncumbranceStatus:
        """
        Evaluates physical weight vs carry capacity:
        - <= 50%: light (경쾌)
        - 50~100%: normal (적정 적재)
        - 100~130%: heavy (과적, 이동 속도 -1.5m/s, 피로도 1.5배, 전력 질주 불가)
        - > 130%: overburdened (한계 초과, 이동 속도 -3.0m/s, 피로도 2.5배, 서행만 가능)
        """
        total_cap, base_cap, bag_bonus = cls.calculate_carry_capacity(entity, state)
        cur_weight = cls.calculate_inventory_weight(entity, state)
        ratio = round(cur_weight / max(1.0, total_cap), 2)

        if ratio <= 0.5:
            level = "light"
            speed_penalty = 0.0
            fatigue_mult = 1.0
            can_sprint = True
            summary = f"경쾌한 몸놀림 (적재 {cur_weight}kg / 한계 {total_cap}kg, {ratio*100:.0f}%)"
        elif ratio <= 1.0:
            level = "normal"
            speed_penalty = 0.0
            fatigue_mult = 1.0
            can_sprint = True
            summary = f"적정 적재 상태 (적재 {cur_weight}kg / 한계 {total_cap}kg, {ratio*100:.0f}%)"
        elif ratio <= 1.3:
            level = "heavy"
            speed_penalty = 1.5
            fatigue_mult = 1.5
            can_sprint = False
            summary = f"과적 상태 (적재 {cur_weight}kg / 한계 {total_cap}kg, 이동 속도 -1.5m/s, 전력 질주 불가)"
        else:
            level = "overburdened"
            speed_penalty = 3.0
            fatigue_mult = 2.5
            can_sprint = False
            summary = f"한계 초과 과적 (적재 {cur_weight}kg / 한계 {total_cap}kg, 이동 속도 -3.0m/s, 보행만 가능)"

        return EncumbranceStatus(
            current_weight_kg=cur_weight,
            max_carry_weight_kg=total_cap,
            backpack_bonus_kg=bag_bonus,
            encumbrance_ratio=ratio,
            status_level=level,
            speed_penalty_mps=speed_penalty,
            fatigue_multiplier=fatigue_mult,
            can_sprint=can_sprint,
            summary_ko=summary
        )

    @classmethod
    def get_backpack_spec(cls, storage_name: str) -> BackpackSpec:
        """Resolves storage gear name to BackpackSpec."""
        s_lower = storage_name.lower()
        if any(kw in s_lower for kw in ["군장", "완전군장", "rucksack", "military", "대형 군장", "대형 배낭"]):
            return BACKPACK_SPECS["military_full_rucksack"]
        elif any(kw in s_lower for kw in ["소형", "슬링백", "작은", "daypack", "pouch", "전술 배낭", "소형 배낭"]):
            return BACKPACK_SPECS["small_daypack"]
        else:
            return BACKPACK_SPECS["medium_traveler_pack"]

    @classmethod
    def estimate_item_volume_liters(cls, item: Item) -> float:
        """Estimates volume in liters based on properties or physical item size."""
        props = getattr(item, "properties", {}) or {}
        if "volume_liters" in props:
            return float(props["volume_liters"])

        size = getattr(item, "size", "small")
        if size == "small":
            return 1.5
        elif size == "medium":
            return 6.0
        elif size == "heavy":
            return 20.0
        else:
            return 60.0

    @classmethod
    def evaluate_backpack_storage(
        cls,
        entity: Any,
        state: WorldState,
        trigger_action: str = "normal",
        force_tear: Optional[bool] = None
    ) -> BackpackStorageStatus:
        """
        Evaluates backpack storage volume (L), stored weight (kg),
        size fitness, and tear/rupture risk on overload.
        """
        # Find equipped backpack name
        storage_name = "여행자 배낭"
        eq = getattr(entity, "equipment", None)
        if eq and getattr(eq, "storage", None):
            s_id = eq.storage
            if s_id in state.items:
                storage_name = state.items[s_id].name
        elif hasattr(entity, "visual") and entity.visual and entity.visual.outfit:
            if entity.visual.outfit.bags_storage:
                storage_name = entity.visual.outfit.bags_storage[0]

        spec = cls.get_backpack_spec(storage_name)

        # Sum stored unequipped items
        inv_ids = getattr(entity, "inventory", [])
        stored_vol = 0.0
        stored_weight = 0.0
        oversized_items: List[str] = []

        for i_id in inv_ids:
            if i_id in state.items:
                it = state.items[i_id]
                it_vol = cls.estimate_item_volume_liters(it)
                it_wt = getattr(it, "weight", 1.0)
                stored_vol += it_vol
                stored_weight += it_wt

                # Check item size vs backpack max allowed size
                it_size = getattr(it, "size", "small")
                if spec.max_item_size == "small" and it_size in ["medium", "heavy", "massive"]:
                    oversized_items.append(it.name)
                elif spec.max_item_size == "medium" and it_size in ["heavy", "massive"]:
                    oversized_items.append(it.name)

        stored_vol = round(stored_vol, 1)
        stored_weight = round(stored_weight, 1)

        is_overfilled_vol = stored_vol > spec.volume_liters
        is_overweight = stored_weight > spec.safe_weight_limit_kg

        tear_risk = 0.0
        is_torn = False
        spilled_items: List[str] = []

        if stored_weight > spec.tear_weight_limit_kg:
            excess = stored_weight - spec.tear_weight_limit_kg
            base_risk = excess * 6.0
            if trigger_action in ["sprint", "combat", "dodge", "fall", "jump"]:
                base_risk += 35.0
            else:
                base_risk += 10.0
            tear_risk = min(100.0, round(base_risk, 1))

            should_tear = force_tear if force_tear is not None else (tear_risk >= 50.0 and random.random() < (tear_risk / 100.0))
            if should_tear:
                is_torn = True
                # Spill item
                if inv_ids:
                    spill_id = inv_ids[-1]
                    if spill_id in state.items:
                        spilled_items.append(state.items[spill_id].name)
                        loc_id = getattr(entity, "location", "")
                        if loc_id in state.locations:
                            state.locations[loc_id].items.append(spill_id)
                        inv_ids.remove(spill_id)

        summary = f"[{spec.name_ko}] 용적: {stored_vol}/{spec.volume_liters}L, 적재: {stored_weight}/{spec.safe_weight_limit_kg}kg (파손한계: {spec.tear_weight_limit_kg}kg)"
        if is_torn:
            summary += f" ⚠️ 과적으로 가방이 찢어져 바닥에 물품({', '.join(spilled_items)})이 쏟아졌습니다!"
        elif is_overweight:
            summary += f" ⚠️ 하중 초과로 가방 찢어짐 위험 ({tear_risk}%)!"
        elif is_overfilled_vol:
            summary += f" ⚠️ 용적 초과! 가방 지퍼와 끈이 터질 듯 팽창했습니다."

        return BackpackStorageStatus(
            backpack_name=spec.name_ko,
            current_volume_liters=stored_vol,
            max_volume_liters=spec.volume_liters,
            current_stored_weight_kg=stored_weight,
            safe_weight_limit_kg=spec.safe_weight_limit_kg,
            tear_weight_limit_kg=spec.tear_weight_limit_kg,
            is_overfilled_volume=is_overfilled_vol,
            is_overweight=is_overweight,
            tear_risk_pct=tear_risk,
            is_torn=is_torn,
            spilled_item_names=spilled_items,
            summary_ko=summary
        )

    @classmethod
    def get_quick_slots(cls, entity: Any, state: WorldState) -> Dict[str, Any]:
        """
        Evaluates quick-slot availability from waist belts, bandoliers, or thigh pouches.
        Allows instantaneous potion/throwable item access during combat.
        """
        quick_slots_count = 0
        quick_slot_sources: List[str] = []

        eq = getattr(entity, "equipment", None)
        if eq:
            # Check belt slot
            if getattr(eq, "belt", None) and eq.belt in state.items:
                b_item = state.items[eq.belt]
                props = getattr(b_item, "properties", {}) or {}
                slots = props.get("quick_slots", 2)
                quick_slots_count += slots
                quick_slot_sources.append(b_item.name)
            # Check storage slot if thigh pouch or bandolier
            if getattr(eq, "storage", None) and eq.storage in state.items:
                s_item = state.items[eq.storage]
                s_name = s_item.name.lower()
                if any(kw in s_name for kw in ["파우치", "탄띠", "허벅지", "pouch", "bandolier"]):
                    quick_slots_count += 2
                    quick_slot_sources.append(s_item.name)

        # Check visual outfit if not equipped in items
        if quick_slots_count == 0 and hasattr(entity, "visual") and entity.visual:
            outfit = getattr(entity.visual, "outfit", None)
            if outfit:
                for s in outfit.bags_storage:
                    if any(kw in s.lower() for kw in ["허벅지 파우치", "벨트 파우치", "주머니", "탄띠"]):
                        quick_slots_count += 2
                        quick_slot_sources.append(s)

        return {
            "has_quick_slots": quick_slots_count > 0,
            "quick_slot_capacity": quick_slots_count,
            "sources": quick_slot_sources,
            "summary_ko": f"퀵슬롯 {quick_slots_count}칸 활성화 ({', '.join(quick_slot_sources)})" if quick_slots_count > 0 else "퀵슬롯 미보유 (배낭 깊숙이 수납됨)"
        }

    @classmethod
    def calculate_projectile_draw_delay(cls, entity: Any, state: WorldState, weapon_type: str = "bow") -> Tuple[float, str]:
        """
        Calculates bow/crossbow projectile draw delay:
        - With quiver (화살통): 0.0s instant draw delay.
        - Without quiver: +0.5s reload penalty (화살을 바닥이나 배낭에서 뒤적여 꺼내야 함).
        """
        has_quiver = False
        quiver_name = ""

        # Check equipment storage
        eq = getattr(entity, "equipment", None)
        if eq:
            if getattr(eq, "storage", None) and eq.storage in state.items:
                s_item = state.items[eq.storage]
                if "화살통" in s_item.name or "quiver" in s_item.name.lower():
                    has_quiver = True
                    quiver_name = s_item.name

        # Check visual outfit mounts
        if not has_quiver and hasattr(entity, "visual") and entity.visual:
            outfit = getattr(entity.visual, "outfit", None)
            if outfit and outfit.weapon_mounts:
                for wm in outfit.weapon_mounts:
                    if "화살통" in wm or "quiver" in wm.lower():
                        has_quiver = True
                        quiver_name = wm
                        break

        # Check inventory for a carried quiver
        if not has_quiver:
            for i_id in getattr(entity, "inventory", []):
                if i_id in state.items:
                    it = state.items[i_id]
                    if "화살통" in it.name or "quiver" in it.name.lower():
                        has_quiver = True
                        quiver_name = it.name
                        break

        if has_quiver:
            return 0.0, f"화살통 [{quiver_name}] 장착: 화살 즉시 발사 (지연 0.0초)"
        return cls.DEFAULT_QUIVER_RELOAD_DELAY_PENALTY, f"화살통 미장착: 배낭/지면 화살 인출 지연 (+{cls.DEFAULT_QUIVER_RELOAD_DELAY_PENALTY:.1f}초)"

    @classmethod
    def calculate_quick_draw_attack(
        cls,
        entity: Any,
        state: WorldState,
        is_opening_turn: bool = True,
        is_from_stealth: bool = False
    ) -> QuickDrawResult:
        """
        Calculates opening quick-draw (발도술) critical strike bonus:
        Requires weapon sheathed in a scabbard/holster.
        Grants +30% crit damage and +10% crit rate when ambushing or attacking on opening turn!
        """
        has_scabbard = False
        mount_type = "none"

        # Check equipment belt
        eq = getattr(entity, "equipment", None)
        if eq and getattr(eq, "belt", None) and eq.belt in state.items:
            b_item = state.items[eq.belt]
            b_name = b_item.name.lower()
            if any(kw in b_name for kw in ["검집", "칼집", "scabbard", "sheath"]):
                has_scabbard = True
                mount_type = "scabbard"
            elif any(kw in b_name for kw in ["권총집", "홀스터", "holster"]):
                has_scabbard = True
                mount_type = "holster"

        # Check visual outfit
        if not has_scabbard and hasattr(entity, "visual") and entity.visual:
            outfit = getattr(entity.visual, "outfit", None)
            if outfit and outfit.weapon_mounts:
                for wm in outfit.weapon_mounts:
                    wm_lower = wm.lower()
                    if any(kw in wm_lower for kw in ["검집", "칼집", "scabbard", "sheath"]):
                        has_scabbard = True
                        mount_type = "scabbard"
                        break
                    elif any(kw in wm_lower for kw in ["홀스터", "권총집", "holster"]):
                        has_scabbard = True
                        mount_type = "holster"
                        break

        # Check if weapon is sword/blade
        if has_scabbard and (is_opening_turn or is_from_stealth):
            return QuickDrawResult(
                eligible=True,
                crit_damage_bonus_pct=cls.DEFAULT_QUICK_DRAW_CRIT_DMG,
                crit_rate_bonus_pct=cls.DEFAULT_QUICK_DRAW_CRIT_RATE,
                weapon_mount_type=mount_type,
                summary_ko=f"전광석화 발도술 적용! (치명타율 +{cls.DEFAULT_QUICK_DRAW_CRIT_RATE:.0f}%, 치명타 피해 +{cls.DEFAULT_QUICK_DRAW_CRIT_DMG:.0f}%)"
            )

        return QuickDrawResult(
            eligible=False,
            crit_damage_bonus_pct=0.0,
            crit_rate_bonus_pct=0.0,
            weapon_mount_type=mount_type,
            summary_ko="일반 공격 (발도술 기습 조건 미충족)"
        )

    @classmethod
    def check_armor_chafing(cls, entity: Any, state: WorldState) -> ArmorChafingResult:
        """
        Checks heavy metal armor direct skin friction:
        - Wearing plate/chainmail (defense >= 8 or metal keywords) without gambeson causes skin chafing.
        - Wearing gambeson cushions metal armor, eliminates chafing, and absorbs 10% blunt shock!
        """
        eq = getattr(entity, "equipment", None)
        chest_item = None
        if eq and getattr(eq, "chest", None) and eq.chest in state.items:
            chest_item = state.items[eq.chest]

        if not chest_item:
            return ArmorChafingResult(
                has_chafing=False,
                reason_ko="갑옷 미착용",
                penalty_active=False,
                blunt_mitigation_pct=0.0,
                innerwear_name="없음",
                armor_name="없음",
                summary_ko="갑옷 미착용 상태"
            )

        # Check if armor is heavy metal
        armor_def = getattr(chest_item, "defense", 0)
        armor_name = chest_item.name
        is_metal_armor = (
            armor_def >= 8 or
            any(kw in armor_name.lower() for kw in ["판금", "철", "사슬", "플레이트", "강철", "plate", "iron", "steel", "chainmail"])
        )

        if not is_metal_armor:
            return ArmorChafingResult(
                has_chafing=False,
                reason_ko="경갑/일반 의복 착용으로 마찰 부상 위험 없음",
                penalty_active=False,
                blunt_mitigation_pct=0.0,
                innerwear_name="자유",
                armor_name=armor_name,
                summary_ko=f"[{armor_name}] 경갑 착용 (피부 마찰 없음)"
            )

        # Check innerwear
        inner_item = None
        if eq and getattr(eq, "innerwear", None) and eq.innerwear in state.items:
            inner_item = state.items[eq.innerwear]

        has_gambeson = False
        inner_name = "맨몸"

        if inner_item:
            inner_name = inner_item.name
            if any(kw in inner_name.lower() for kw in ["갬비슨", "누비옷", "패딩", "gambeson", "padded"]):
                has_gambeson = True

        if not has_gambeson and hasattr(entity, "visual") and entity.visual:
            outfit = getattr(entity.visual, "outfit", None)
            if outfit and outfit.innerwear:
                for in_g in outfit.innerwear:
                    if any(kw in in_g.lower() for kw in ["갬비슨", "누비옷", "패딩", "gambeson", "padded"]):
                        has_gambeson = True
                        inner_name = in_g
                        break

        if has_gambeson:
            return ArmorChafingResult(
                has_chafing=False,
                reason_ko="갬비슨 누비옷이 금속 판금 마찰을 완벽히 흡수",
                penalty_active=False,
                blunt_mitigation_pct=10.0,
                innerwear_name=inner_name,
                armor_name=armor_name,
                summary_ko=f"[{inner_name}] 완충 효과: [{armor_name}] 마찰 방지 및 둔기 충격 10% 추가 흡수"
            )
        else:
            return ArmorChafingResult(
                has_chafing=True,
                reason_ko="맨몸 또는 얇은 천 위에 직접 착용한 금속 갑옷으로 피부 찰과상 및 마찰 쓸림 발생",
                penalty_active=True,
                blunt_mitigation_pct=0.0,
                innerwear_name=inner_name,
                armor_name=armor_name,
                summary_ko=f"경고: [{armor_name}] 피부 직착용! 갬비슨 부재로 인한 피부 쓸림/찰과상 유발 (매 턴 피로 누적)"
            )

    @classmethod
    def calculate_clothing_noise_reduction(cls, entity: Any, state: WorldState) -> float:
        """
        Calculates footstep noise dB reduction from specialized clothing (e.g. stealth tights).
        Returns noise reduction in dB (e.g. -6.0 dB).
        """
        noise_reduction = 0.0

        # Check innerwear slot
        eq = getattr(entity, "equipment", None)
        if eq and getattr(eq, "innerwear", None) and eq.innerwear in state.items:
            in_item = state.items[eq.innerwear]
            if any(kw in in_item.name.lower() for kw in ["타이즈", "은신", "그림자", "tights", "stealth"]):
                noise_reduction += cls.DEFAULT_STEALTH_TIGHTS_NOISE_REDUCTION_DB

        # Check visual outfit innerwear & socks
        if noise_reduction == 0.0 and hasattr(entity, "visual") and entity.visual:
            outfit = getattr(entity.visual, "outfit", None)
            if outfit:
                for in_g in outfit.innerwear:
                    if any(kw in in_g.lower() for kw in ["타이즈", "은신", "그림자", "tights"]):
                        noise_reduction += cls.DEFAULT_STEALTH_TIGHTS_NOISE_REDUCTION_DB
                        break

        return round(noise_reduction, 1)

    @classmethod
    def calculate_eyewear_appraisal_bonus(cls, entity: Any, state: WorldState) -> Tuple[int, str]:
        """
        Monocle / glasses grant +25% appraisal & observation success bonus.
        """
        has_eyewear = False
        eyewear_name = ""

        eq = getattr(entity, "equipment", None)
        if eq:
            for s in ["face", "head"]:
                item_id = getattr(eq, s, None)
                if item_id and item_id in state.items:
                    it = state.items[item_id]
                    if any(kw in it.name.lower() for kw in ["안경", "단안경", "모노클", "monocle", "glasses"]):
                        has_eyewear = True
                        eyewear_name = it.name
                        break

        if not has_eyewear and hasattr(entity, "visual") and entity.visual:
            outfit = getattr(entity.visual, "outfit", None)
            if outfit and outfit.head_face:
                for hf in outfit.head_face:
                    if any(kw in hf.lower() for kw in ["안경", "단안경", "모노클", "monocle", "glasses"]):
                        has_eyewear = True
                        eyewear_name = hf
                        break

        if has_eyewear:
            return cls.DEFAULT_APPRAISAL_BONUS_PCT, f"[{eyewear_name}] 착용: 정밀 관찰 및 가치 감정 성공률 +{cls.DEFAULT_APPRAISAL_BONUS_PCT}%"
        return 0, "안경 미착용"

    @classmethod
    def evaluate_eyewear_damage(
        cls,
        entity: Any,
        state: WorldState,
        target_part: str,
        is_critical: bool = False,
        shatter_roll: int = 20
    ) -> EyewearHazardResult:
        """
        When receiving an impact/critical hit to the face/head, fragile glass eyewear risks shattering!
        """
        clean_part = target_part.strip().lower()
        if clean_part not in ["머리", "얼굴", "눈", "head", "face", "eye"]:
            return EyewearHazardResult(
                is_shattered=False,
                eyewear_name="",
                debuff_applied="",
                summary_ko="안면 비피격 (안경 안전)"
            )

        has_glass = False
        eyewear_name = ""
        face_slot_item_id = None

        eq = getattr(entity, "equipment", None)
        if eq:
            for s in ["face", "head"]:
                i_id = getattr(eq, s, None)
                if i_id and i_id in state.items:
                    it = state.items[i_id]
                    if any(kw in it.name.lower() for kw in ["안경", "단안경", "모노클", "monocle", "glasses"]):
                        has_glass = True
                        eyewear_name = it.name
                        face_slot_item_id = i_id
                        break

        if not has_glass and hasattr(entity, "visual") and entity.visual:
            outfit = getattr(entity.visual, "outfit", None)
            if outfit and outfit.head_face:
                for hf in outfit.head_face:
                    if any(kw in hf.lower() for kw in ["안경", "단안경", "모노클", "monocle", "glasses"]):
                        has_glass = True
                        eyewear_name = hf
                        break

        if not has_glass:
            return EyewearHazardResult(
                is_shattered=False,
                eyewear_name="",
                debuff_applied="",
                summary_ko="안경 미착용 (파손 위험 없음)"
            )

        # Fragility check: Critical hit or shatter roll <= 35
        if is_critical or shatter_roll <= 35:
            # Shatter eyewear
            if face_slot_item_id and face_slot_item_id in state.items:
                state.items[face_slot_item_id].durability = 0
            return EyewearHazardResult(
                is_shattered=True,
                eyewear_name=eyewear_name,
                debuff_applied="유리 파편 실명 위험 (시야 흐림)",
                summary_ko=f"💥 안면 충격으로 [{eyewear_name}]의 렌즈가 박살났습니다! 날카로운 유리 파편으로 시야가 흐려집니다."
            )

        return EyewearHazardResult(
            is_shattered=False,
            eyewear_name=eyewear_name,
            debuff_applied="",
            summary_ko=f"[{eyewear_name}]이(가) 충격을 가까스로 버텼습니다."
        )

    @classmethod
    def sync_equipment_to_clothing_layer(cls, entity: Any, state: WorldState) -> ClothingLayer:
        """
        Synchronizes entity's EquipmentSlots to entity's 5-layer ClothingLayer.
        Ensures perfect harmony between game mechanics and visual narration/prompts.
        """
        if not hasattr(entity, "visual") or not entity.visual:
            from src.world.state import NPCVisualDetails
            entity.visual = NPCVisualDetails()

        outfit: ClothingLayer = getattr(entity.visual, "outfit", None) or ClothingLayer()
        eq = getattr(entity, "equipment", None)
        if not eq:
            return outfit

        def get_name(item_id: Optional[str]) -> str:
            if item_id and item_id in state.items:
                return state.items[item_id].name
            return ""

        # 1. Body ornaments
        head_name = get_name(getattr(eq, "head", None))
        face_name = get_name(getattr(eq, "face", None))
        hf_list = []
        if head_name: hf_list.append(head_name)
        if face_name: hf_list.append(face_name)
        for e_id in getattr(eq, "earrings", []):
            e_name = get_name(e_id)
            if e_name: hf_list.append(e_name)
        if hf_list:
            outfit.head_face = hf_list

        neck_name = get_name(getattr(eq, "neck", None))
        if neck_name:
            outfit.neck_acc = [neck_name]

        gloves_name = get_name(getattr(eq, "gloves", None))
        aw_list = []
        if gloves_name: aw_list.append(gloves_name)
        for b_id in getattr(eq, "bracelets", []):
            b_name = get_name(b_id)
            if b_name: aw_list.append(b_name)
        for r_id in getattr(eq, "rings", []):
            r_name = get_name(r_id)
            if r_name: aw_list.append(r_name)
        if aw_list:
            outfit.arms_wrists = aw_list

        # 2. Garments
        inner_name = get_name(getattr(eq, "innerwear", None))
        if inner_name:
            outfit.innerwear = [inner_name]

        chest_name = get_name(getattr(eq, "chest", None))
        if chest_name:
            outfit.outerwear = chest_name

        legs_name = get_name(getattr(eq, "legs", None))
        if legs_name:
            outfit.base_lower = legs_name

        belt_name = get_name(getattr(eq, "belt", None))
        if belt_name:
            outfit.waist_layer = belt_name

        # 3. Shoulders & Cape
        shoulders_name = get_name(getattr(eq, "shoulders", None))
        if shoulders_name:
            outfit.shoulders = shoulders_name

        cape_name = get_name(getattr(eq, "cape", None))
        if cape_name:
            outfit.cape_back = cape_name

        # 4. Footwear
        boots_name = get_name(getattr(eq, "boots", None))
        if boots_name:
            outfit.footwear = boots_name

        # 5. Storage & Weapon Mounts
        storage_name = get_name(getattr(eq, "storage", None))
        if storage_name:
            outfit.bags_storage = [storage_name]

        wep_name = get_name(getattr(eq, "weapon", None))
        if wep_name:
            if any(kw in wep_name.lower() for kw in ["검", "도", "sword", "blade", "katana"]):
                outfit.weapon_mounts = [f"{wep_name} 칼집"]
            elif any(kw in wep_name.lower() for kw in ["활", "bow"]):
                outfit.weapon_mounts = [f"{wep_name} 및 화살통"]

        entity.visual.outfit = outfit
        return outfit

    @classmethod
    def build_consistent_character_prompt(cls, entity: Any, state: WorldState) -> str:
        """
        Assembles a deterministic, ultra-consistent AI image generation prompt for a character.
        Fuses:
        1. Biological & Anatomical Anchor (species, age, gender, height, body_measurements, facial_details)
        2. 5-Layer Outfit & Fabric Profile (including innerwear silhouette reveal if form-fitting)
        3. Equipped Weapon Visual Profile (blade shape, hilt, finish, aura, scabbard)
        """
        cls.sync_equipment_to_clothing_layer(entity, state)
        v = getattr(entity, "visual", None)
        if not v:
            return "cinematic fantasy character portrait, highly detailed, 8k"

        # 1. Base Entity Core
        species = getattr(v, "species", "human") or "human"
        life_stage = getattr(v, "life_stage", "")
        job = getattr(entity, "job", "traveler")
        age = getattr(v, "age_apparent", "")
        name = getattr(entity, "name", "Character")
        gender = getattr(v, "gender", "")

        core_parts = [f"cinematic fantasy portrait of {species}"]
        if gender:
            core_parts.append(gender)
        if life_stage:
            core_parts.append(life_stage)
        if job:
            core_parts.append(job)
        if age:
            core_parts.append(f"({age})")
        core_str = " ".join(core_parts)

        # 2. Body Measurements & Proportions
        body_parts = []
        if getattr(v, "height_cm", 0) > 0:
            body_parts.append(f"{v.height_cm}cm tall")
        if getattr(v, "build_archetype", ""):
            body_parts.append(v.build_archetype)
        if hasattr(v, "body_measurements") and v.body_measurements:
            b_kw = v.body_measurements.to_prompt_keywords()
            if b_kw:
                body_parts.append(b_kw)
        body_str = ", ".join(body_parts)

        # 3. Facial & Head Details
        face_parts = []
        if getattr(v, "hair_color", "") or getattr(v, "hair_style", ""):
            face_parts.append(f"{v.hair_color} {v.hair_style}".strip())
        if getattr(v, "eye_shape", "") or getattr(v, "eye_color", ""):
            eye_desc = f"{v.eye_shape} with {v.eye_color} eyes".strip() if (v.eye_shape and v.eye_color) else (v.eye_shape or f"{v.eye_color} eyes")
            face_parts.append(eye_desc)
        if getattr(v, "skin_tone", ""):
            face_parts.append(v.skin_tone)
        if getattr(v, "facial_features", None):
            face_parts.extend(v.facial_features)
        if hasattr(v, "face_details") and v.face_details:
            f_kw = v.face_details.to_prompt_keywords()
            if f_kw:
                face_parts.append(f_kw)
        face_str = ", ".join(face_parts)

        # 4. Outfit & Layered Garments
        outfit_str = v.outfit.to_prompt_keywords() if hasattr(v, "outfit") and v.outfit else "traveler clothing"

        # 5. Weapon Visual Profile
        weapon_parts = []
        eq = getattr(entity, "equipment", None)
        wep_id = getattr(eq, "weapon", None) if eq else None
        if wep_id and wep_id in state.items:
            wep_item = state.items[wep_id]
            if getattr(wep_item, "visual", None) and wep_item.visual:
                w_kw = wep_item.visual.to_prompt_keywords()
                if w_kw:
                    weapon_parts.append(f"wielding {wep_item.name} ({w_kw})")
                else:
                    weapon_parts.append(f"wielding {wep_item.name}")
            else:
                weapon_parts.append(f"wielding {wep_item.name}")
        weapon_str = ", ".join(weapon_parts)

        # 6. Assemble
        all_sections = [core_str]
        if body_str:
            all_sections.append(body_str)
        if face_str:
            all_sections.append(face_str)
        if outfit_str:
            all_sections.append(outfit_str)
        if weapon_str:
            all_sections.append(weapon_str)
        if getattr(v, "posture_and_vibe", ""):
            all_sections.append(v.posture_and_vibe)

        all_sections.append("highly detailed face, sharp focus, volumetric lighting, masterpiece, 8k")
        return ", ".join(all_sections)
