"""
Deterministic Mana Vein Restoration & Arcane Surgery Engine for Quilltale TRPG.
Handles surgical repair, silver-needle acupuncture, herbal vein decoctions,
and divine miracle suturing for damaged mana circuits caused by mana burn/overchanneling.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import random


@dataclass
class VeinSurgerySpec:
    surgery_id: str
    name_ko: str
    required_item_or_skill: str
    base_dc: int
    gold_cost: int
    circuit_integrity_restore: float
    scars_healed: int
    backlash_damage_on_fail: int = 15
    description: str = ""
    traits: List[str] = field(default_factory=lambda: ["vein_surgery", "medical_restoration"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "surgery_id": self.surgery_id,
            "name_ko": self.name_ko,
            "required_item_or_skill": self.required_item_or_skill,
            "base_dc": self.base_dc,
            "gold_cost": self.gold_cost,
            "circuit_integrity_restore": self.circuit_integrity_restore,
            "scars_healed": self.scars_healed,
            "backlash_damage_on_fail": self.backlash_damage_on_fail,
            "description": self.description,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VeinSurgerySpec":
        return cls(
            surgery_id=data.get("surgery_id", ""),
            name_ko=data.get("name_ko", ""),
            required_item_or_skill=data.get("required_item_or_skill", ""),
            base_dc=int(data.get("base_dc", 12)),
            gold_cost=int(data.get("gold_cost", 10)),
            circuit_integrity_restore=float(data.get("circuit_integrity_restore", 15.0)),
            scars_healed=int(data.get("scars_healed", 0)),
            backlash_damage_on_fail=int(data.get("backlash_damage_on_fail", 15)),
            description=data.get("description", ""),
            traits=data.get("traits", ["vein_surgery", "medical_restoration"]),
        )


VEIN_SURGERY_REGISTRY: Dict[str, VeinSurgerySpec] = {
    "silver_needle_acupuncture": VeinSurgerySpec(
        surgery_id="silver_needle_acupuncture",
        name_ko="은침 혈맥 소통술",
        required_item_or_skill="silver_needle",
        base_dc=12,
        gold_cost=15,
        circuit_integrity_restore=15.0,
        scars_healed=0,
        backlash_damage_on_fail=12,
        description="마력 전도율이 높은 순은 침으로 막힌 혈맥을 자극하여 일시적 침묵과 마나 역류를 해소하는 응급 시술.",
        traits=["vein_surgery", "acupuncture", "silver_needle", "emergency", "vein_clearing"]
    ),
    "herbal_vein_decoction": VeinSurgerySpec(
        surgery_id="herbal_vein_decoction",
        name_ko="비전 영지 농축 탕약 요법",
        required_item_or_skill="lingzhi_mushroom",
        base_dc=11,
        gold_cost=25,
        circuit_integrity_restore=25.0,
        scars_healed=0,
        backlash_damage_on_fail=10,
        description="영지초와 지혈 이끼를 달여 복용함으로써 손상된 체내 마나 회로 외벽을 점진적으로 재생시키는 한방 요법.",
        traits=["vein_surgery", "herbalism", "decoction", "medicinal", "regeneration"]
    ),
    "arcane_dialysis_surgery": VeinSurgerySpec(
        surgery_id="arcane_dialysis_surgery",
        name_ko="비전 의사의 에테르 투석 수술",
        required_item_or_skill="arcane_surgery_tools",
        base_dc=15,
        gold_cost=80,
        circuit_integrity_restore=40.0,
        scars_healed=1,
        backlash_damage_on_fail=18,
        description="전문 비전 외과의가 환자의 혈맥을 절개하여 굳어버린 에테르 침전물을 긁어내고 영구 흉터를 제거하는 대수술.",
        traits=["vein_surgery", "surgery", "arcane_dialysis", "scar_removal", "high_tier"]
    ),
    "divine_artery_miracle": VeinSurgerySpec(
        surgery_id="divine_artery_miracle",
        name_ko="성맥 재건의 성령 기적 봉합",
        required_item_or_skill="holy_relic",
        base_dc=14,
        gold_cost=150,
        circuit_integrity_restore=100.0,
        scars_healed=3,
        backlash_damage_on_fail=15,
        description="신전 고위 사제가 신성 에너지를 환자의 전신 혈맥에 직접 주입하여 파열된 마나 회로를 태초의 상태로 되돌리는 기적.",
        traits=["vein_surgery", "divine", "miracle", "full_restoration", "sanctified"]
    )
}


class ManaVeinRestorationEngine:
    """
    Deterministic Mana Circuit Restoration & Arcane Surgery Mechanics.
    Resolves surgery skill checks, success restorations, and User Option B backlash shocks on failure.
    """

    @classmethod
    def get_circuit_state(cls, character: Any) -> Dict[str, Any]:
        """Retrieves or creates mana_burn_state dictionary on character."""
        if not hasattr(character, "mana_burn_state") or not isinstance(character.mana_burn_state, dict):
            character.mana_burn_state = {
                "vein_integrity_pct": 100.0,
                "scarred_veins": 0,
                "burnout_turns": 0,
                "max_mp_penalty": 0,
                "mutations": [],
                "traits": ["mana_circuit", "stable"]
            }
        return character.mana_burn_state

    @classmethod
    def perform_surgery(
        cls,
        state: Any,
        patient: Any,
        practitioner: Any,
        surgery_id: str,
        fixed_roll: Optional[int] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes surgical restoration on patient's damaged mana circuits.
        User Decision Q2: Failure triggers Option B (Arcane Backlash Shock: -15 HP & Mana Spasm).
        """
        spec = VEIN_SURGERY_REGISTRY.get(surgery_id)
        if not spec:
            return False, "존재하지 않는 마나 회로 시술법입니다.", {}

        # 1. Cost check
        gold = getattr(patient, "gold", 0)
        if gold < spec.gold_cost:
            return False, f"❌ [비용 부족] {spec.name_ko}을(를) 받기 위해 {spec.gold_cost} 골드가 필요하지만, 현재 {gold} 골드뿐입니다.", {}

        patient.gold -= spec.gold_cost
        circuit = cls.get_circuit_state(patient)

        # 2. Practitioner Skill check (d20 + max(INT, WIS) mod vs base_dc)
        int_stat = getattr(practitioner, "intelligence", 10)
        wis_stat = getattr(practitioner, "wisdom", 10)
        doc_bonus = max((int_stat - 10) // 2, (wis_stat - 10) // 2)

        roll = random.randint(1, 20) if fixed_roll is None else fixed_roll
        total = roll + doc_bonus

        # 3. Resolution
        if total >= spec.base_dc:
            # Success!
            old_integrity = circuit.get("vein_integrity_pct", 100.0)
            new_integrity = min(100.0, old_integrity + spec.circuit_integrity_restore)
            circuit["vein_integrity_pct"] = round(new_integrity, 1)

            # Heal scarred veins
            old_scars = circuit.get("scarred_veins", 0)
            new_scars = max(0, old_scars - spec.scars_healed)
            circuit["scarred_veins"] = new_scars

            # Reduce MP penalty proportionally
            if spec.scars_healed > 0 and circuit.get("max_mp_penalty", 0) > 0:
                restored_mp = spec.scars_healed * 5
                circuit["max_mp_penalty"] = max(0, circuit["max_mp_penalty"] - restored_mp)
                if hasattr(patient, "max_mana"):
                    patient.max_mana += restored_mp

            # Clear burnout turns
            circuit["burnout_turns"] = 0

            msg = (
                f"🩺 [회로 복구 수술 성공!] {practitioner.name}의 정교한 집도({roll}+{doc_bonus}={total} vs DC {spec.base_dc})로 "
                f"[{spec.name_ko}]이(가) 완벽히 성공했습니다!\n"
                f"   * 회로 건전도: {old_integrity:.1f}% ➔ {new_integrity:.1f}%\n"
                f"   * 영구 회로 흉터: {old_scars}개 ➔ {new_scars}개 (침묵/경직 완전 해제)"
            )
            return True, msg, {
                "success": True,
                "vein_integrity_pct": new_integrity,
                "scarred_veins": new_scars,
                "roll": roll,
                "total": total
            }

        else:
            # User Decision Q2: Option B -> Failure triggers Backlash Shock!
            dmg = spec.backlash_damage_on_fail
            patient.health = max(1, patient.health - dmg)
            circuit["burnout_turns"] = circuit.get("burnout_turns", 0) + 1

            msg = (
                f"💥 [수술 실패: 마나 역류 충격파!] {practitioner.name}의 미숙한 손길({roll}+{doc_bonus}={total} vs DC {spec.base_dc})로 "
                f"환자의 민감한 마나 혈맥을 잘못 건드렸습니다!\n"
                f"   * ⚠️ [급성 마나 발작] 제어되지 못한 에테르가 체내에서 역류하여 환자에게 {dmg}의 극심한 신경 피해를 입혔습니다! "
                f"(현재 HP: {patient.health})\n"
                f"   * 전신 경련으로 인해 1턴간 영창 불능 상태에 빠집니다."
            )
            return False, msg, {
                "success": False,
                "damage_taken": dmg,
                "current_hp": patient.health,
                "roll": roll,
                "total": total
            }

    @classmethod
    def brew_vein_tonic(
        cls,
        state: Any,
        brewer: Any,
        plant_id: str,
        fixed_roll: Optional[int] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Herbalist brews botanical herbs into a restorative vein tonic.
        """
        from src.world.botany_engine import PLANT_REGISTRY
        plant = PLANT_REGISTRY.get(plant_id)
        if not plant or plant.category not in ["medicinal", "arcane"]:
            return False, "마나 회로 치료에 적합하지 않은 식물입니다.", {}

        int_mod = (getattr(brewer, "intelligence", 10) - 10) // 2
        roll = random.randint(1, 20) if fixed_roll is None else fixed_roll
        total = roll + int_mod

        if total >= plant.identify_dc:
            item_data = {
                "id": f"vein_tonic_{plant_id}_{random.randint(100, 999)}",
                "name": f"[{plant.name_ko}] 농축 회로 안정액",
                "surgery_id": "herbal_vein_decoction",
                "circuit_restore": 20.0,
                "traits": ["potion", "vein_tonic", "alchemy", "restorative"]
            }
            return True, f"⚗️ [탕약 조제 성공] {brewer.name}이(가) [{plant.name_ko}]을(를) 정밀 정제하여 고순도 마나 회로 안정액을 완성했습니다!", item_data
        else:
            return False, f"🍂 [탕약 조제 실패] 약재의 유효 성분을 추출하지 못하고 잿물만 남겼습니다. (판정: {total} vs DC {plant.identify_dc})", {}
