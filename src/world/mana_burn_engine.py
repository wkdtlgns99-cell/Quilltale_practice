"""
Mana Burn & Overchanneling Engine for Quilltale TRPG.
Deterministic calculation of spell overchanneling, mana circuit damage/burnout,
life-to-mana conversion (restricted to sacrifice/dark/blood magic),
backlash discharges, and dual-nature ether mutations.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging
import random

logger = logging.getLogger(__name__)


@dataclass
class EtherMutationSpec:
    mutation_id: str
    name_ko: str
    description: str
    positive_effects: Dict[str, Any]
    negative_effects: Dict[str, Any]
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "name_ko": self.name_ko,
            "description": self.description,
            "positive_effects": self.positive_effects,
            "negative_effects": self.negative_effects,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EtherMutationSpec":
        return cls(
            mutation_id=data.get("mutation_id", ""),
            name_ko=data.get("name_ko", ""),
            description=data.get("description", ""),
            positive_effects=data.get("positive_effects", {}),
            negative_effects=data.get("negative_effects", {}),
            traits=data.get("traits", []),
        )


@dataclass
class ManaCircuitState:
    vein_integrity_pct: float = 100.0       # 마나 회로 건전도 (100% 정상 ~ 0% 완전 파열)
    scarred_veins: int = 0                  # 영구 마나 회로 흉터 수 (회로 손상 누적)
    max_mp_penalty: int = 0                 # 회로 파열로 인한 최대 마나 상한 감소치
    burnout_turns: int = 0                  # 과열 마나 침묵 (영창 불가 잔여 턴수)
    stamina_drain_on_cast: int = 0          # 손상된 회로로 마법 시전 시 신경통/기력 소모 페널티
    ether_contamination: float = 0.0        # 에테르 오염도 (0~100)
    active_mutations: List[str] = field(default_factory=list) # 획득한 에테르 변이 ID 목록
    traits: List[str] = field(default_factory=lambda: ["mana_circuit", "arcane_physiology"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vein_integrity_pct": self.vein_integrity_pct,
            "scarred_veins": self.scarred_veins,
            "max_mp_penalty": self.max_mp_penalty,
            "burnout_turns": self.burnout_turns,
            "stamina_drain_on_cast": self.stamina_drain_on_cast,
            "ether_contamination": self.ether_contamination,
            "active_mutations": list(self.active_mutations),
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManaCircuitState":
        return cls(
            vein_integrity_pct=float(data.get("vein_integrity_pct", 100.0)),
            scarred_veins=int(data.get("scarred_veins", 0)),
            max_mp_penalty=int(data.get("max_mp_penalty", 0)),
            burnout_turns=int(data.get("burnout_turns", 0)),
            stamina_drain_on_cast=int(data.get("stamina_drain_on_cast", 0)),
            ether_contamination=float(data.get("ether_contamination", 0.0)),
            active_mutations=list(data.get("active_mutations", [])),
            traits=data.get("traits", ["mana_circuit", "arcane_physiology"]),
        )


# 8대 에테르 변이 스펙 (이중성: 혜택과 페널티의 공존)
ETHER_MUTATIONS_REGISTRY: Dict[str, EtherMutationSpec] = {
    "crystalline_skin": EtherMutationSpec(
        mutation_id="crystalline_skin",
        name_ko="수정질 외피 변이",
        description="피부 밑으로 푸른 비전 수정 결정이 돋아나 신체가 단단해지나, 충격 진동에 극도로 취약해진다.",
        positive_effects={"defense_bonus": 5, "magic_damage_reduction_pct": 20},
        negative_effects={"blunt_damage_multiplier": 1.5, "agility_penalty": 2, "weight_kg": 8.0},
        traits=["ether_mutation", "crystalline", "defense_buff", "blunt_vulnerable"]
    ),
    "mana_leak_aura": EtherMutationSpec(
        mutation_id="mana_leak_aura",
        name_ko="마력 누출 발광체",
        description="체내 마나가 상시 기화되어 반경 3m 내 적에게 지속 에테르 피해를 입히지만, 은신이 불가능해지고 몬스터 어그로가 폭증한다.",
        positive_effects={"passive_ether_pulse_damage": 3},
        negative_effects={"stealth_impossible": True, "aggro_multiplier": 2.0},
        traits=["ether_mutation", "radiant", "stealth_disabled", "offensive_aura"]
    ),
    "arcane_thirst": EtherMutationSpec(
        mutation_id="arcane_thirst",
        name_ko="비전 갈증증",
        description="주문 극대화 능력이 치솟지만, 주기적으로 마나 물약이나 마석을 흡수하지 않으면 극심한 금단 증세로 전신 마비가 온다.",
        positive_effects={"crit_rate_bonus": 15, "crit_damage_bonus": 25},
        negative_effects={"mana_withdrawal_stat_penalty": 3, "daily_mana_consumption_required": 20},
        traits=["ether_mutation", "addiction", "crit_buff", "thirst"]
    ),
    "astral_burn": EtherMutationSpec(
        mutation_id="astral_burn",
        name_ko="성간 에테르 열화",
        description="손끝에서 방출되는 마법 화력이 비약적으로 증폭되나, 체온 조절 능력이 고장나며 치유 마법의 효과를 절반밖에 받지 못한다.",
        positive_effects={"magic_attack_bonus": 8},
        negative_effects={"healing_received_multiplier": 0.5, "fire_damage_multiplier": 1.4},
        traits=["ether_mutation", "offensive_buff", "healing_debuff", "heat_sensitive"]
    ),
    "glass_bones": EtherMutationSpec(
        mutation_id="glass_bones",
        name_ko="유리 골격화",
        description="신체 골격이 마나 전도체 유리화되어 영창 속도와 마나 소모가 감소하지만, 뼈가 부러지기 쉬워져 최대 생명력이 급감한다.",
        positive_effects={"cast_speed_bonus_pct": 30, "mana_cost_discount_pct": 20},
        negative_effects={"max_hp_penalty": 20, "fall_damage_multiplier": 2.0},
        traits=["ether_mutation", "cast_buff", "fragile_bone", "hp_debuff"]
    ),
    "ether_sight": EtherMutationSpec(
        mutation_id="ether_sight",
        name_ko="에테르 동공 개안",
        description="눈동자가 백청색으로 물들어 마력의 흐름과 투명체를 꿰뚫어 보지만, 강한 일광과 섬광에 극도로 취약해진다.",
        positive_effects={"detect_invisibility": True, "darkvision_pct": 100},
        negative_effects={"flash_blindness_turns": 3, "daylight_perception_penalty": 3},
        traits=["ether_mutation", "vision_buff", "light_vulnerable", "spectral_sight"]
    ),
    "blood_mana_conduit": EtherMutationSpec(
        mutation_id="blood_mana_conduit",
        name_ko="혈맥 마나 도관",
        description="혈관과 마나 회로가 융합되어 생명력을 마나로 치환하는 효율이 극대화되나, 신체의 자연 치유가 거의 정지된다.",
        positive_effects={"blood_overchannel_efficiency_multiplier": 2.0, "dark_magic_power_bonus": 6},
        negative_effects={"natural_hp_regen_disabled": True, "bleed_duration_multiplier": 1.5},
        traits=["ether_mutation", "blood_affinity", "sacrifice_buff", "no_natural_regen"]
    ),
    "spectral_limb": EtherMutationSpec(
        mutation_id="spectral_limb",
        name_ko="반투명 영체 팔",
        description="한쪽 팔이 반투명한 영체로 변해 물리 공격을 흘려내지만, 악력과 물리 무기 타격력이 급감한다.",
        positive_effects={"dodge_chance_bonus_pct": 18},
        negative_effects={"physical_attack_penalty": 6, "bow_draw_penalty_lbs": 30},
        traits=["ether_mutation", "dodge_buff", "weak_grip", "spectral"]
    )
}


class ManaBurnEngine:
    """
    Deterministic Mana Burn, Circuit Damage, Overchanneling, and Ether Mutation Engine.
    """

    ALLOWED_SACRIFICE_TRAITS = {
        "blood_magic", "necromancy", "sacrifice", "dark_magic",
        "혈마법", "흑마법", "대가마법", "강령술", "생명치환", "혈맥도관"
    }

    @classmethod
    def get_circuit_state(cls, target: Any) -> ManaCircuitState:
        """Retrieves or initializes target's ManaCircuitState."""
        if not hasattr(target, "mana_burn_state") or target.mana_burn_state is None:
            target.mana_burn_state = ManaCircuitState()
        elif isinstance(target.mana_burn_state, dict):
            target.mana_burn_state = ManaCircuitState.from_dict(target.mana_burn_state)
        return target.mana_burn_state

    @classmethod
    def can_use_life_as_mana(cls, caster: Any) -> Tuple[bool, str]:
        """
        User Rule 4: 생명력을 마나로 치환하는 과충전은 오직 대가 마법, 흑마법, 혈마법 숙련자만 가능.
        """
        # 1. Check caster traits
        caster_traits = set(getattr(caster, "traits", []))
        if caster_traits.intersection(cls.ALLOWED_SACRIFICE_TRAITS):
            return True, "혈맥과 대가의 규율을 이해하고 있어 생명력을 마나로 치환할 수 있습니다."

        # 2. Check caster active mutations
        circuit = cls.get_circuit_state(caster)
        if "blood_mana_conduit" in circuit.active_mutations:
            return True, "에테르 변이 [혈맥 마나 도관]으로 인해 생명력을 마나로 치환할 수 있습니다."

        # 3. Check caster skills
        caster_skills = getattr(caster, "skills", [])
        for s in caster_skills:
            s_lower = str(s).lower()
            if any(k in s_lower for k in ["blood", "sacrifice", "dark", "흑마", "혈마", "대가"]):
                return True, "혈마법 또는 대가 마법의 지식을 통해 생명력을 연소할 수 있습니다."

        return False, "일반 마법사는 생명력을 마나로 치환할 수 없습니다. 오직 대가 마법, 흑마법, 혈마법의 비전이나 혈맥 도관을 지닌 자만이 생명력을 연소할 수 있습니다."

    @classmethod
    def evaluate_overchannel(
        cls,
        caster: Any,
        required_mp: int,
        available_mp: int,
        spell_name: str = "마법"
    ) -> Dict[str, Any]:
        """
        Evaluates attempting to cast a spell with insufficient MP.
        """
        circuit = cls.get_circuit_state(caster)

        # 1. Check burnout silence
        if circuit.burnout_turns > 0:
            return {
                "success": False,
                "reason": "burnout",
                "message_ko": f"⚠️ [마나 회로 과열] 마나 회로가 까맣게 타버려 영창할 수 없습니다! (잔여 침묵: {circuit.burnout_turns}턴)",
                "hp_cost": 0,
                "backlash": False
            }

        shortage = max(0, required_mp - available_mp)
        if shortage == 0:
            return {
                "success": True,
                "reason": "sufficient_mp",
                "message_ko": "마나가 충분하여 정상 영창되었습니다.",
                "hp_cost": 0,
                "backlash": False
            }

        # 2. Life-to-mana conversion qualification check
        can_convert, qualification_msg = cls.can_use_life_as_mana(caster)
        if not can_convert:
            return {
                "success": False,
                "reason": "unqualified_for_life_conversion",
                "message_ko": f"❌ [영창 거부] 마나가 {shortage} 부족합니다. {qualification_msg}",
                "hp_cost": 0,
                "backlash": False
            }

        # 3. Calculate Life (HP) Cost
        # 1 shortage MP = 2 HP loss base, modified by mutation
        hp_multiplier = 2.0
        if "blood_mana_conduit" in circuit.active_mutations:
            hp_multiplier = 1.0  # 50% discount on HP cost

        hp_cost = int(shortage * hp_multiplier)
        current_hp = getattr(caster, "health", 50)

        if current_hp <= hp_cost:
            return {
                "success": False,
                "reason": "fatal_hp_cost",
                "message_ko": f"⚠️ [치명적 대가] 부족한 마나({shortage})를 메우기 위해 필요한 생명력({hp_cost} HP)이 현재 체력({current_hp} HP)을 초과하여 영창 시 즉사합니다!",
                "hp_cost": hp_cost,
                "backlash": False
            }

        # 4. Overchannel Check: d20 + CON/INT vs DC
        # DC = 10 + (shortage // 2)
        dc = 10 + (shortage // 2)
        con_mod = (getattr(caster, "constitution", 10) - 10) // 2
        int_mod = (getattr(caster, "intelligence", 10) - 10) // 2
        roll = random.randint(1, 20)
        total_check = roll + max(con_mod, int_mod)

        is_backlash = (total_check < dc) or (roll == 1)

        return {
            "success": True,
            "reason": "overchannel_executed",
            "message_ko": f"🩸 [생명력 과충전] 부족한 마나 {shortage}을(를) 충당하기 위해 생명력 {hp_cost} HP를 연소합니다! (판정: {roll}+{max(con_mod, int_mod)}={total_check} vs DC {dc})",
            "hp_cost": hp_cost,
            "backlash": is_backlash,
            "shortage": shortage,
            "roll": roll,
            "dc": dc
        }

    @classmethod
    def apply_overchannel_consequences(
        cls,
        caster: Any,
        overchannel_result: Dict[str, Any],
        state: Optional[Any] = None
    ) -> List[str]:
        """
        Applies HP sacrifice, circuit damage, and triggers backlash if failed.
        """
        logs = []
        if not overchannel_result.get("success"):
            return logs

        circuit = cls.get_circuit_state(caster)
        hp_cost = overchannel_result.get("hp_cost", 0)

        # 1. Deduct HP
        if hp_cost > 0:
            caster.health = max(1, caster.health - hp_cost)
            logs.append(f"🩸 {caster.name}의 혈관이 터져 나가며 {hp_cost}의 생명력이 마나로 연소되었습니다. (현재 HP: {caster.health})")

        # 2. Circuit Strain
        shortage = overchannel_result.get("shortage", 0)
        integrity_damage = round(shortage * 2.5, 1)
        circuit.vein_integrity_pct = max(0.0, circuit.vein_integrity_pct - integrity_damage)
        logs.append(f"⚡ [회로 긴장] 마나 회로 건전도가 {integrity_damage}% 감소했습니다. (현재 건전도: {circuit.vein_integrity_pct:.1f}%)")

        # 3. Check Backlash
        if overchannel_result.get("backlash"):
            backlash_logs = cls.trigger_mana_backlash(caster, shortage, state)
            logs.extend(backlash_logs)

        return logs

    @classmethod
    def trigger_mana_backlash(
        cls,
        caster: Any,
        severity: int,
        state: Optional[Any] = None
    ) -> List[str]:
        """
        User Rule 3: 마나 폭주 시 시전자의 몸에 있는 마나 회로가 심각하게 손상됨.
        - Vein integrity drop
        - Max MP penalty
        - Burnout silence turns
        - Ether shockwave to nearby targets
        - Ether contamination accumulation -> Mutation
        """
        circuit = cls.get_circuit_state(caster)
        logs = []

        # 1. Mana Circuit Damage (마나 회로 손상)
        additional_integrity_loss = min(circuit.vein_integrity_pct, 15.0 + severity * 2)
        circuit.vein_integrity_pct = max(0.0, circuit.vein_integrity_pct - additional_integrity_loss)
        circuit.scarred_veins += 1

        mp_penalty = 5 + (severity // 3)
        circuit.max_mp_penalty += mp_penalty
        circuit.burnout_turns = max(circuit.burnout_turns, 2 + (severity // 5))
        circuit.stamina_drain_on_cast += 3

        logs.append(
            f"💥 [마나 폭주: 회로 파열] {caster.name}의 체내 마나 회로가 격렬하게 파열되었습니다! "
            f"(회로 건전도: {circuit.vein_integrity_pct:.1f}%, 누적 흉터: {circuit.scarred_veins}, "
            f"최대 MP -{mp_penalty} 영구 감소, {circuit.burnout_turns}턴간 영창 불가 과열)"
        )

        # 2. Backlash Shockwave Damage
        shockwave_damage = random.randint(4, 8) + (severity // 2)
        caster.health = max(1, caster.health - shockwave_damage)
        logs.append(f"💥 에테르 역류 충격파로 인해 시전자에게 {shockwave_damage}의 직접 파열 피해가 발생했습니다.")

        # If in state and near other actors
        if state and hasattr(state, "party"):
            for comp in state.party.values():
                if comp.alive and comp.name != caster.name:
                    splash = max(1, shockwave_damage // 2)
                    comp.health = max(1, comp.health - splash)
                    logs.append(f"⚠️ 충격파가 튀어 동료 [{comp.name}]에게 {splash}의 비전 파편 피해를 입혔습니다.")

        # 3. Ether Contamination Accumulation (에테르 오염 누적)
        contamination_gain = 15.0 + severity * 1.5
        mut_logs = cls.accumulate_contamination(caster, contamination_gain, state)
        logs.extend(mut_logs)

        return logs

    @classmethod
    def accumulate_contamination(
        cls,
        target: Any,
        amount: float,
        state: Optional[Any] = None
    ) -> List[str]:
        """
        Accumulates ether contamination. When reaching 100.0, triggers an Ether Mutation (이중성).
        """
        circuit = cls.get_circuit_state(target)
        circuit.ether_contamination = min(100.0, circuit.ether_contamination + amount)
        logs = [f"🔮 [에테르 오염] 오염도가 {amount:.1f} 상승하여 {circuit.ether_contamination:.1f}/100.0에 도달했습니다."]

        if circuit.ether_contamination >= 100.0:
            # Trigger Mutation
            available_mutations = [
                m_id for m_id in ETHER_MUTATIONS_REGISTRY.keys()
                if m_id not in circuit.active_mutations
            ]
            if available_mutations:
                chosen_mut_id = random.choice(available_mutations)
                mut_spec = ETHER_MUTATIONS_REGISTRY[chosen_mut_id]
                circuit.active_mutations.append(chosen_mut_id)
                circuit.ether_contamination = 0.0  # Reset after mutating

                # Add mutation traits to target
                target_traits = getattr(target, "traits", [])
                for t in mut_spec.traits:
                    if t not in target_traits:
                        target_traits.append(t)
                target.traits = target_traits

                logs.append(
                    f"☣️ [에테르 변이 발현] 에테르 오염 한계치 도달! {target.name}의 신체에 변이가 일어났습니다: "
                    f"[{mut_spec.name_ko}] - {mut_spec.description}\n"
                    f"  * 혜택: {mut_spec.positive_effects}\n"
                    f"  * 대가/페널티: {mut_spec.negative_effects}"
                )
            else:
                logs.append(f"☣️ {target.name}의 에테르 오염도가 극한에 달했으나 더 이상 변이할 신체 부위가 없습니다.")

        return logs

    @classmethod
    def repair_circuit(
        cls,
        target: Any,
        remedy_type: str = "mana_stabilizer"
    ) -> Tuple[bool, str]:
        """
        Repairs damaged circuits and cools burnout.
        """
        circuit = cls.get_circuit_state(target)
        if remedy_type == "mana_stabilizer":
            circuit.vein_integrity_pct = min(100.0, circuit.vein_integrity_pct + 25.0)
            circuit.burnout_turns = max(0, circuit.burnout_turns - 2)
            circuit.stamina_drain_on_cast = max(0, circuit.stamina_drain_on_cast - 1)
            return True, f"🧪 [마나 안정제 복용] 회로 건전도가 25% 회복되었습니다. (현재: {circuit.vein_integrity_pct:.1f}%)"
        elif remedy_type == "silver_needle_acupuncture":
            circuit.vein_integrity_pct = min(100.0, circuit.vein_integrity_pct + 40.0)
            if circuit.max_mp_penalty > 0:
                circuit.max_mp_penalty = max(0, circuit.max_mp_penalty - 5)
            circuit.burnout_turns = 0
            return True, f"🪡 [은침 회로 소통술] 뒤틀린 마나 혈맥을 정돈하여 회로를 온전히 개방했습니다. (건전도: {circuit.vein_integrity_pct:.1f}%)"
        elif remedy_type == "holy_water_purge":
            reduced = min(circuit.ether_contamination, 35.0)
            circuit.ether_contamination = max(0.0, circuit.ether_contamination - 35.0)
            return True, f"✨ [성수 정화] 축복받은 성수가 에테르 침전물을 녹여내어 오염도가 {reduced:.1f} 감소했습니다."
        return False, "알 수 없는 치료법입니다."
