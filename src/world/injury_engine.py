"""
Deterministic Injury and Treatment Engine for Quilltale TRPG.
Categorizes anatomical injuries into 4 severity tiers:
1. LIGHT (찰과상, 타박상): Cured immediately by standard bandages.
2. MODERATE (열상, 뇌진탕, 근육파열): Requires poultice/herbs + bandage + rest.
3. SEVERE_FRACTURE (골절, 관절 탈구, 인대 파열):
   - Cannot be cured by red potions or simple bandages (Anti-Yes-Man rejection).
   - Requires splint fixation + extended rest, or professional surgery by a doctor NPC.
4. CRITICAL_PERMANENT (실명, 절단): Irreversible through normal medicine. Requires high miracles or prosthetic limbs.
"""
from enum import Enum
from typing import Tuple, List, Dict, Any, Optional
import logging
from src.world.state import WorldState, Item, Player, NPC

logger = logging.getLogger(__name__)


class InjurySeverity(str, Enum):
    LIGHT = "light"
    MODERATE = "moderate"
    SEVERE_FRACTURE = "severe_fracture"
    CRITICAL_PERMANENT = "critical_permanent"


class InjuryEngine:
    SEVERITY_KEYWORDS: Dict[InjurySeverity, List[str]] = {
        InjurySeverity.CRITICAL_PERMANENT: ["실명", "절단", "결손", "안구 손실"],
        InjurySeverity.SEVERE_FRACTURE: ["골절", "파열", "탈구", "부러", "관절 손상", "경추 손상", "치명상"],
        InjurySeverity.MODERATE: ["뇌진탕", "열상", "중상", "근육", "타박/뇌진탕", "관통상", "화상"],
        InjurySeverity.LIGHT: ["찰과상", "타박상", "자상", "긁힘", "가벼운"]
    }

    @classmethod
    def classify_injury(cls, injury_name: str) -> InjurySeverity:
        """Classifies an injury string into one of 4 severity tiers."""
        inj_lower = injury_name.lower()
        for severity in [InjurySeverity.CRITICAL_PERMANENT, InjurySeverity.SEVERE_FRACTURE, InjurySeverity.MODERATE]:
            if any(k in inj_lower for k in cls.SEVERITY_KEYWORDS[severity]):
                return severity
        return InjurySeverity.LIGHT

    @classmethod
    def can_treat_with_item(cls, injury_name: str, item: Item) -> Tuple[bool, str]:
        """
        Anti-Yes-Man validation: Determines if an item can legally treat the given injury.
        Returns (can_treat: bool, message_ko: str).
        """
        severity = cls.classify_injury(injury_name)
        iname = item.name.lower()
        iprops = item.properties or {}
        itype = item.item_type.lower()

        is_potion = "포션" in iname or "물약" in iname or itype == "consumable" and ("회복" in iname or "치유" in iname)
        is_bandage = "붕대" in iname or iprops.get("bandage", False)
        is_splint = "부목" in iname or iprops.get("splint", False)
        is_poultice = "연고" in iname or "약초" in iname or iprops.get("poultice", False)

        # 1. Potions cannot fix structural bone/tendon injuries or permanent dismemberment
        if is_potion:
            if severity in [InjurySeverity.SEVERE_FRACTURE, InjurySeverity.CRITICAL_PERMANENT]:
                return False, (
                    f"⚠️ [{item.name}]은(는) 체력(HP)을 채워줄 뿐, "
                    f"부러진 뼈나 파열된 힘줄을 맞추지 못합니다! (골절 치료 불가 — 부목 고정이나 의사의 수술이 필요합니다)"
                )
            if severity == InjurySeverity.MODERATE:
                return False, f"⚠️ [{item.name}]만으로는 벌어진 상처를 봉합할 수 없습니다. 붕대나 지혈 처치가 필요합니다."

        # 2. Simple bandages cannot stabilize severe fractures
        if is_bandage and not is_splint:
            if severity == InjurySeverity.SEVERE_FRACTURE:
                return False, (
                    f"⚠️ 단순 붕대만으로는 골절된 뼈({injury_name})를 고정할 수 없습니다! "
                    f"단단한 [부목(splint)]으로 고정하거나 전문 외과의를 찾아가야 합니다."
                )
            if severity == InjurySeverity.CRITICAL_PERMANENT:
                return False, f"⚠️ 영구 결손/실명({injury_name})은 붕대로 회복될 수 없는 불가역적 상해입니다."

        # 3. Splint is specifically for bone fractures / joint dislocations
        if is_splint:
            if severity == InjurySeverity.LIGHT:
                return False, f"경미한 외상({injury_name})에는 거추장스러운 부목이 필요하지 않습니다. 붕대로 충분합니다."

        # 4. Critical permanent dismemberment cannot be cured by ordinary mundane items
        if severity == InjurySeverity.CRITICAL_PERMANENT:
            return False, f"⚠️ 영구 결손/실명({injury_name})은 일반 약재로 회복되지 않습니다. 최고위 기적이나 기계 의수가 필요합니다."

        return True, "치료 가능한 적합한 의료 도구입니다."

    @classmethod
    def apply_item_treatment(
        cls,
        state: WorldState,
        target: Any,
        injury_name: str,
        item: Item
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Applies item treatment onto target. Returns (success, message_ko, state_delta_mod).
        """
        can_treat, reason = cls.can_treat_with_item(injury_name, item)
        if not can_treat:
            return False, reason, {}

        severity = cls.classify_injury(injury_name)
        iname = item.name.lower()
        delta_mod: Dict[str, Any] = {}

        # Light injury: Cured instantly
        if severity == InjurySeverity.LIGHT:
            return True, f"[{item.name}]을(를) 사용해 [{injury_name}] 상처를 깨끗이 소독하고 지혈했습니다. (완치)", {"cured": True}

        # Moderate injury: Cured if bandage/poultice
        if severity == InjurySeverity.MODERATE:
            return True, f"[{item.name}]을(를) 상처에 단단히 둘러 [{injury_name}]의 통증을 완화하고 지혈했습니다. (완치)", {"cured": True}

        # Severe fracture with Splint: Enters splinted recovery state (requires rest)
        if severity == InjurySeverity.SEVERE_FRACTURE:
            # Set splinted state (requires 2 rest turns)
            if hasattr(target, "splinted_injuries"):
                target.splinted_injuries[injury_name] = 2
            return True, (
                f"[{item.name}]을(를) 덧대어 [{injury_name}] 부위를 단단히 부목 고정했습니다. "
                f"이제 무리한 행동을 삼가고 여관이나 캠프에서 휴식을 취하면 뼈가 붙을 것입니다."
            ), {"splinted": True, "turns_needed": 2}

        return False, "치료 효과가 미미합니다.", {}

    @classmethod
    def apply_doctor_surgery(
        cls,
        state: WorldState,
        doctor_npc: NPC,
        target: Any,
        injury_name: str,
        fee: int = 50
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Doctor NPC conducts professional surgery/bone setting.
        Requires patient to pay gold fee. Instantly cures fractures and moderate wounds.
        """
        target_gold = getattr(target, "gold", 0)
        target_name = getattr(target, "name", "환자")

        if target_gold < fee:
            return False, f"[{doctor_npc.name}] 의사가 치료를 거절합니다: '치료비 {fee} 골드가 부족하오. ({target_name} 소지: {target_gold}G)'", {}

        severity = cls.classify_injury(injury_name)
        if severity == InjurySeverity.CRITICAL_PERMANENT:
            return False, f"[{doctor_npc.name}] 의사가 고개를 젓습니다: '이런 실명/절단 상처는 내 메스로는 살려낼 수 없소. 신전의 성자나 기적을 찾아가시오.'", {}

        # Surgery success
        surgery_desc = "어긋난 뼈를 맞추고 쇠심과 단단한 붕대로 완벽히 정골 수술을 마쳤습니다" if severity == InjurySeverity.SEVERE_FRACTURE else "깊게 찢어진 환부를 봉합하고 약초 즙을 발라 완치했습니다"
        msg = f"[{doctor_npc.name}] 의사에게 {fee} 골드를 지불하고 수술을 받았습니다. {surgery_desc}! ([{injury_name}] 완치)"

        delta_mod = {
            "gold_cost": fee,
            "cured": True,
            "injury_name": injury_name
        }
        return True, msg, delta_mod

    @classmethod
    def progress_rest_healing(cls, state: WorldState, target: Any, rest_turns: int = 1) -> List[str]:
        """
        Progresses healing of splinted fractures during resting (inn, camp).
        """
        logs = []
        if not hasattr(target, "splinted_injuries") or not target.splinted_injuries:
            return logs

        cured_injuries = []
        for inj, rem_turns in list(target.splinted_injuries.items()):
            new_rem = rem_turns - rest_turns
            if new_rem <= 0:
                cured_injuries.append(inj)
                del target.splinted_injuries[inj]
                if inj in target.injuries:
                    target.injuries.remove(inj)
                logs.append(f"🦴 편안한 휴식을 취하며 부목으로 고정된 [{inj}]의 뼈가 단단히 맞붙었습니다! (골절 완치)")
            else:
                target.splinted_injuries[inj] = new_rem
                logs.append(f"부목 고정 중인 [{inj}] 부위가 서서히 유합되고 있습니다. (완치까지 휴식 {new_rem}회 남음)")

        return logs
