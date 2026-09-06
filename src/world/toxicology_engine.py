"""
Deterministic Toxicology & Potion Tolerance Engine for Quilltale TRPG.
Prevents infinite potion-chugging by modeling cumulative liver toxicity and diminishing returns (tolerance).
Resolves User Decision Q1: Liver toxicity decays with in-game world time, while full tolerance resets upon 8-hour campsite rest.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


@dataclass
class PotionToxicityState:
    liver_toxicity: int = 0               # 누적 간 독성 (0~100)
    potion_tolerance: float = 0.0         # 약물 내성률 (0.0 ~ 0.50, 최대 50% 치유량 감쇄)
    doses_taken: int = 0                  # 연속 복용 횟수
    accumulated_world_minutes: int = 0    # 시간제 대사 추적용 분 카운터
    traits: List[str] = field(default_factory=lambda: ["toxicology", "liver_metabolism"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "liver_toxicity": self.liver_toxicity,
            "potion_tolerance": self.potion_tolerance,
            "doses_taken": self.doses_taken,
            "accumulated_world_minutes": self.accumulated_world_minutes,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PotionToxicityState":
        return cls(
            liver_toxicity=int(data.get("liver_toxicity", 0)),
            potion_tolerance=float(data.get("potion_tolerance", 0.0)),
            doses_taken=int(data.get("doses_taken", 0)),
            accumulated_world_minutes=int(data.get("accumulated_world_minutes", 0)),
            traits=data.get("traits", ["toxicology", "liver_metabolism"]),
        )


class ToxicologyToleranceEngine:
    """
    Deterministic Liver Metabolism, Toxicity Accumulation, and Potion Diminishing Returns.
    """

    @classmethod
    def get_state(cls, character: Any) -> PotionToxicityState:
        """Retrieves or creates PotionToxicityState on character."""
        raw = getattr(character, "toxicity_state", None)
        if raw is None or not isinstance(raw, (dict, PotionToxicityState)):
            state_obj = PotionToxicityState()
            character.toxicity_state = state_obj.to_dict()
            return state_obj
        if isinstance(raw, dict):
            state_obj = PotionToxicityState.from_dict(raw)
            return state_obj
        return raw

    @classmethod
    def sync_state(cls, character: Any, state_obj: PotionToxicityState):
        """Syncs back dataclass state to character dictionary."""
        character.toxicity_state = state_obj.to_dict()

    @classmethod
    def ingest_potion(
        cls,
        character: Any,
        potion_name: str,
        base_heal: int = 30,
        toxicity_increase: int = 25
    ) -> Tuple[int, List[str]]:
        """
        Ingests a restorative potion.
        Applies current tolerance reduction to heal amount, increases liver toxicity and tolerance.
        Triggers nausea (70+) or acute poisoning (100).
        """
        logs = []
        tox_state = cls.get_state(character)

        # 1. Apply tolerance penalty
        tol = tox_state.potion_tolerance
        effective_heal = max(1, int(base_heal * (1.0 - tol)))

        # 2. Heal character
        max_hp = getattr(character, "max_health", 100)
        old_hp = getattr(character, "health", 100)
        character.health = min(max_hp, old_hp + effective_heal)

        # 3. Accumulate toxicity & tolerance
        old_tox = tox_state.liver_toxicity
        new_tox = min(100, old_tox + toxicity_increase)
        tox_state.liver_toxicity = new_tox
        tox_state.doses_taken += 1

        # Tolerance increases by 15% per consecutive dose (max 50%)
        new_tol = min(0.50, round(tol + 0.15, 2))
        tox_state.potion_tolerance = new_tol

        tol_pct = int(tol * 100)
        penalty_str = f" (약물 내성으로 힐량 {tol_pct}% 감쇄됨)" if tol > 0 else ""
        logs.append(
            f"🧪 [{potion_name} 음용] 체력 +{effective_heal} 회복{penalty_str}! "
            f"(현재 HP: {character.health}/{max_hp}, 간 독성: {new_tox}/100, 다음 내성: {int(new_tol * 100)}%)"
        )

        # 4. Toxicity Threshold Checks
        if new_tox >= 100:
            # Acute Toxicology Poisoning
            backlash_hp = 15
            character.health = max(1, character.health - backlash_hp)
            if hasattr(character, "stamina"):
                character.stamina = 0

            logs.append(
                f"🤮 [급성 약물 중독 격발!] 간이 감당할 수 있는 독성 한계치(100)를 초과했습니다!\n"
                f"   * 위장이 격렬하게 뒤틀리며 피와 섞인 약물을 게워냅니다! (-{backlash_hp} HP, 스태미나 0 고갈)\n"
                f"   * ⚠️ [탈진 및 내장 쇼크] 전신에 식은땀이 흐르고 손발이 마비됩니다."
            )
        elif new_tox >= 70:
            logs.append("🤢 [독성 축적 경고: 메스꺼움] 체내에 약물 독소가 위험 수위(70+)에 달해 구역질이 치밀어 오릅니다. (명중/지각 -2)")

        cls.sync_state(character, tox_state)
        return effective_heal, logs

    @classmethod
    def process_time_metabolism(
        cls,
        character: Any,
        elapsed_minutes: int
    ) -> List[str]:
        """
        User Decision Q1: Real in-game world time reduces liver toxicity.
        Every 30 minutes of world time metabolizes 5 liver toxicity.
        Tolerance does not naturally vanish until full 8-hour sleep.
        """
        logs = []
        if elapsed_minutes <= 0:
            return logs

        tox_state = cls.get_state(character)
        if tox_state.liver_toxicity <= 0:
            return logs

        # Calculate toxicity decay
        decay_cycles = elapsed_minutes // 30
        if decay_cycles > 0:
            decay_amount = decay_cycles * 5
            old_tox = tox_state.liver_toxicity
            new_tox = max(0, old_tox - decay_amount)
            tox_state.liver_toxicity = new_tox

            if new_tox < old_tox:
                logs.append(
                    f"🌿 [간 대사 작용] {elapsed_minutes}분의 시간 경과로 체내 약물 독소가 자연 분해되었습니다. "
                    f"(간 독성: {old_tox} ➔ {new_tox}/100)"
                )

        cls.sync_state(character, tox_state)
        return logs

    @classmethod
    def reset_on_full_rest(cls, character: Any) -> List[str]:
        """
        User Decision Q1 (Option B):
        Campsite / Inn 8-hour full rest completely clears accumulated potion tolerance and liver toxicity.
        """
        tox_state = cls.get_state(character)
        if tox_state.liver_toxicity == 0 and tox_state.potion_tolerance == 0.0:
            return []

        old_tox = tox_state.liver_toxicity
        old_tol = int(tox_state.potion_tolerance * 100)

        tox_state.liver_toxicity = 0
        tox_state.potion_tolerance = 0.0
        tox_state.doses_taken = 0
        cls.sync_state(character, tox_state)

        return [
            f"🍃 [간 대사 및 약물 내성 완전 초기화] 8시간의 깊은 숙면을 통해 간이 휴식하고 혈액이 정화되었습니다. "
            f"(간 독성 {old_tox} ➔ 0, 약물 내성 {old_tol}% ➔ 0% 초기화)"
        ]
