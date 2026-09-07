"""
Deterministic NPC Cognitive Deduction and Autonomous Behavior Prediction Engine for Quilltale TRPG.

Features:
1. Anti-Yes-Man Hypothesis Validation:
   - Takes player's suspicion/hypothesis ("NPC is planning to poison us")
   - Cross-examines against NPC's 10-factor attitude matrix, 12-axis personality,
     20-factor persona (taboos, values, traumas, desires), BDI beliefs, and physical inventory.
   - Computes deterministic plausibility score (0-100%) and categorizes into
     IMPOSSIBLE, CONTRADICTED, UNLIKELY, PLAUSIBLE, HIGHLY_LIKELY, CONFIRMED.
   - Generates objective, anti-yes-man GM verdict directives to prevent narrative hallunication/sycophancy.

2. Autonomous Next Intent & Action Prediction:
   - Computes NPC's next concrete plan based on desire priority, needs deficit,
     value hierarchy, personality weights, and available items.
   - Generates deterministic plan steps, motive chain, required tools, and leaked clues.
   - Automatically synchronizes with npc.intention and npc.goal.

3. Micro-Leakage & Lie Detection:
   - Player Perception vs NPC (Cunning + Deceit) contested roll.
   - Exposes physical cues and micro-expressions (micro_leakage_traits).

4. External AI (GPT/Claude) Prompt Generation:
   - Formats complete psychological persona into a structured prompt for deep external simulation.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging
import random

from src.world.state import WorldState, NPC, Player

logger = logging.getLogger(__name__)


@dataclass
class HypothesisEvidence:
    """A concrete piece of evidence supporting or contradicting a player hypothesis."""
    category: str           # "personality" | "persona" | "bdi" | "inventory" | "attitude" | "relationship"
    evidence_text: str      # 구체적 사실 서술
    weight: float           # 영향력 가중치 (1.0 ~ 5.0)
    is_supporting: bool     # True: 가설 지지, False: 가설 반박
    traits: List[str] = field(default_factory=lambda: ["hypothesis_evidence", "cognitive_clue"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "evidence_text": self.evidence_text,
            "weight": round(self.weight, 2),
            "is_supporting": self.is_supporting,
            "traits": list(self.traits),
        }


@dataclass
class HypothesisValidationResult:
    """Result of validating a player hypothesis against NPC ground truth."""
    target_npc_id: str
    target_npc_name: str
    hypothesis_text: str
    hypothesis_category: str  # "poison", "theft", "assassination", "betrayal", "escape", "bribe", "fraud", "cooperation", "ambush", "surveillance", "general"
    verdict: str              # "IMPOSSIBLE" | "CONTRADICTED" | "UNLIKELY" | "PLAUSIBLE" | "HIGHLY_LIKELY" | "CONFIRMED"
    plausibility_score: int   # 0 ~ 100
    supporting_evidence: List[HypothesisEvidence] = field(default_factory=list)
    contradicting_evidence: List[HypothesisEvidence] = field(default_factory=list)
    gm_anti_yesman_verdict: str = ""
    traits: List[str] = field(default_factory=lambda: ["anti_yes_man", "hypothesis_validation", "reality_check"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_npc_id": self.target_npc_id,
            "target_npc_name": self.target_npc_name,
            "hypothesis_text": self.hypothesis_text,
            "hypothesis_category": self.hypothesis_category,
            "verdict": self.verdict,
            "plausibility_score": self.plausibility_score,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "contradicting_evidence": [e.to_dict() for e in self.contradicting_evidence],
            "gm_anti_yesman_verdict": self.gm_anti_yesman_verdict,
            "traits": list(self.traits),
        }


@dataclass
class PredictedNPCAction:
    """The deterministic next action/plan calculated for an NPC."""
    npc_id: str
    npc_name: str
    action_type: str        # "escape", "poison", "bribe", "theft", "betray", "cooperate", "assassinate", "hide", "surveillance", "idle_observe", "solicit_help", "confront"
    concrete_plan: str      # 언제, 어디서, 무엇으로, 누구에게 실행할지 구체적 계획
    motive_chain: str       # 욕망 -> 신념 -> 태도 -> 의도 인과 사슬
    required_items: List[str] = field(default_factory=list)
    has_required_items: bool = True
    execution_risk: int = 50 # 0~100 (위험도)
    stealth_level: str = "covert" # "overt" | "covert" | "imperceptible"
    leaked_clues: List[str] = field(default_factory=list) # 관찰력 높은 플레이어가 간파할 수 있는 복선
    traits: List[str] = field(default_factory=lambda: ["predicted_action", "autonomous_intent"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "npc_name": self.npc_name,
            "action_type": self.action_type,
            "concrete_plan": self.concrete_plan,
            "motive_chain": self.motive_chain,
            "required_items": list(self.required_items),
            "has_required_items": self.has_required_items,
            "execution_risk": self.execution_risk,
            "stealth_level": self.stealth_level,
            "leaked_clues": list(self.leaked_clues),
            "traits": list(self.traits),
        }


@dataclass
class MicroLeakageObservation:
    """Result of player attempting to perceive NPC's subconscious body language/tells."""
    npc_id: str
    detected: bool
    leakage_clue: str
    underlying_emotion: str # "fear", "guilt", "greed", "anxiety", "malice", "calm"
    traits: List[str] = field(default_factory=lambda: ["micro_leakage", "body_language_tell"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "detected": self.detected,
            "leakage_clue": self.leakage_clue,
            "underlying_emotion": self.underlying_emotion,
            "traits": list(self.traits),
        }


class NPCCognitiveDeductionEngine:
    """
    Core deterministic cognitive engine.
    Cross-checks psychological models with physical world truth to validate hypotheses and predict behavior.
    """

    # Category classification keywords
    HYPOTHESIS_KEYWORDS: Dict[str, List[str]] = {
        "poison": ["독", "독살", "독약", "비상", "마비독", "약물", "poison", "toxic"],
        "theft": ["훔치", "털", "소매치기", "절도", "도둑", "갈취", "steal", "theft", "loot"],
        "assassination": ["살해", "암살", "기습", "목을", "찌르", "죽이", "암습", "assassinate", "murder"],
        "betrayal": ["배신", "밀고", "팔아넘", "고발", "배반", "첩자", "스파이", "betray", "snitch"],
        "escape": ["도망", "도주", "탈출", "야반도주", "튄", "도망치", "escape", "flee"],
        "bribe": ["뇌물", "매수", "뒷돈", "로비", "bribe"],
        "fraud": ["사기", "속이", "기만", "위조", "거짓말", "가짜", "scam", "fraud"],
        "cooperation": ["돕", "협력", "동맹", "조력", "구원", "도움", "help", "cooperate"],
        "surveillance": ["미행", "감시", "엿듣", "도청", "주시", "spy", "follow", "watch"],
    }

    @classmethod
    def classify_hypothesis(cls, text: str) -> str:
        """Classifies hypothesis text into an operational category."""
        text_lower = text.lower()
        for cat, keywords in cls.HYPOTHESIS_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return cat
        return "general"

    @classmethod
    def evaluate_player_hypothesis(
        cls, npc: NPC, hypothesis_text: str, state: WorldState
    ) -> HypothesisValidationResult:
        """
        Validates player's hypothesis about NPC's intent/action against Ground Truth.
        Returns a rich HypothesisValidationResult with supporting & contradicting evidence.
        """
        category = cls.classify_hypothesis(hypothesis_text)
        supporting: List[HypothesisEvidence] = []
        contradicting: List[HypothesisEvidence] = []

        p = npc.personality
        v_hier = getattr(npc, "value_hierarchy", ["survival", "wealth", "honor", "family", "faith"])
        taboo = getattr(npc, "taboo", "")
        desire = getattr(npc, "desire", "")
        weakness = getattr(npc, "weakness", "")
        fin_state = getattr(npc, "financial_state", "")
        beliefs = getattr(npc, "beliefs", [])
        mask = getattr(npc, "public_mask", "")
        secret = getattr(npc, "blackmail_secret", "")

        # 1. Personality Metric Analysis
        if category in ["poison", "assassination"]:
            # High altruism contradicts unprovoked murder
            if p.altruism >= 65:
                contradicting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"높은 이타심(수치: {p.altruism}/100)으로 인해 무고한 살상에 강한 심리적 저항감을 지님",
                    weight=3.5, is_supporting=False
                ))
            elif p.altruism <= 30:
                supporting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"결핍된 이타심(수치: {p.altruism}/100)으로 인명 경시 성향이 강함",
                    weight=2.5, is_supporting=True
                ))

            # Aggression
            if p.aggression >= 70:
                supporting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"높은 공격성(수치: {p.aggression}/100)으로 폭력적 해결 방식을 선호함",
                    weight=3.0, is_supporting=True
                ))
            elif p.aggression <= 30:
                contradicting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"낮은 공격성(수치: {p.aggression}/100)으로 신체적 가해를 극도로 기피함",
                    weight=2.5, is_supporting=False
                ))

            # Deceit / Cunning for Poison
            if category == "poison":
                if p.cunning >= 65 and p.deceit >= 60:
                    supporting.append(HypothesisEvidence(
                        category="personality",
                        evidence_text=f"높은 교활함({p.cunning})과 기만성({p.deceit})으로 은밀한 독살 수법에 심리적 친화성이 있음",
                        weight=3.0, is_supporting=True
                    ))
                elif p.cunning <= 35:
                    contradicting.append(HypothesisEvidence(
                        category="personality",
                        evidence_text=f"교활함이 결여되어({p.cunning}) 정교하고 은밀한 독극물 계획을 구상할 지능적 여유가 부족함",
                        weight=2.0, is_supporting=False
                    ))

        elif category == "theft":
            if p.greed >= 70:
                supporting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"과도한 탐욕(수치: {p.greed}/100)으로 타인의 재물에 대한 소유욕이 억제되지 않음",
                    weight=3.5, is_supporting=True
                ))
            elif p.greed <= 30:
                contradicting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"청렴한 성향(탐욕 {p.greed}/100)으로 사리사욕을 위한 도둑질 동기가 극히 희박함",
                    weight=3.0, is_supporting=False
                ))

        elif category == "betrayal":
            if p.loyalty >= 70:
                contradicting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"확고한 충성심(수치: {p.loyalty}/100)으로 인해 동료나 맹약을 배신할 가능성이 극히 낮음",
                    weight=4.0, is_supporting=False
                ))
            elif p.loyalty <= 30:
                supporting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"희박한 충성심(수치: {p.loyalty}/100)으로 언제든 실리에 따라 배신할 성향임",
                    weight=3.0, is_supporting=True
                ))

        elif category == "escape":
            if p.courage <= 35 or p.neuroticism >= 65:
                supporting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"낮은 용기({p.courage}) 및 높은 불안도({p.neuroticism})로 위기 발생 시 도주 본능이 최우선 작동함",
                    weight=3.5, is_supporting=True
                ))
            elif p.courage >= 75:
                contradicting.append(HypothesisEvidence(
                    category="personality",
                    evidence_text=f"불굴의 용기(수치: {p.courage}/100)로 불리한 상황에서도 도망치지 않고 맞서는 성향임",
                    weight=3.0, is_supporting=False
                ))

        # 2. 10-Factor Attitude Matrix toward Player
        if category in ["poison", "assassination", "betrayal", "theft"]:
            if npc.trust >= 70:
                contradicting.append(HypothesisEvidence(
                    category="attitude",
                    evidence_text=f"플레이어에 대한 두터운 신뢰도({npc.trust}/100)로 배신/가해 행위를 주저함",
                    weight=3.5, is_supporting=False
                ))
            if npc.respect >= 70:
                contradicting.append(HypothesisEvidence(
                    category="attitude",
                    evidence_text=f"플레이어를 높이 존경함({npc.respect}/100)으로 음해 공작을 벌일 심리적 명분이 없음",
                    weight=2.5, is_supporting=False
                ))
            if npc.fear >= 75:
                supporting.append(HypothesisEvidence(
                    category="attitude",
                    evidence_text=f"플레이어에 대한 극심한 공포({npc.fear}/100)에 질려 극단적 선제공격이나 음독을 고려할 수 있음",
                    weight=2.5, is_supporting=True
                ))
            if npc.debt > 50:
                contradicting.append(HypothesisEvidence(
                    category="attitude",
                    evidence_text=f"플레이어에게 진 큰 은혜의 빚(부채감 {npc.debt:+d})으로 보은을 우선시함",
                    weight=4.0, is_supporting=False
                ))
            elif npc.debt < -50:
                supporting.append(HypothesisEvidence(
                    category="attitude",
                    evidence_text=f"플레이어에 대한 뼈에 사무친 원한(원한도 {npc.debt})으로 복수 기회를 엿보고 있음",
                    weight=4.5, is_supporting=True
                ))
            if getattr(npc, "disgust", 0) >= 70:
                supporting.append(HypothesisEvidence(
                    category="attitude",
                    evidence_text=f"플레이어에 대한 생리적/도덕적 혐오감({npc.disgust}/100)이 누적되어 적대 행동 동기 발생",
                    weight=2.5, is_supporting=True
                ))

        # 3. 20-Factor Persona Check (Taboo, Desires, Weaknesses, Justification)
        if taboo:
            taboo_lower = taboo.lower()
            if any(k in taboo_lower for k in ["살인", "무고", "살상", "해치"]) and category in ["poison", "assassination"]:
                contradicting.append(HypothesisEvidence(
                    category="persona",
                    evidence_text=f"절대적 도덕 금기([{taboo}])를 목숨처럼 지키고 있어 명백한 살인 계획은 성립 불가능함",
                    weight=5.0, is_supporting=False
                ))
            if any(k in taboo_lower for k in ["도둑", "절도", "도벽", "약탈"]) and category == "theft":
                contradicting.append(HypothesisEvidence(
                    category="persona",
                    evidence_text=f"개인적 금기([{taboo}])에 의해 남의 물건을 훔치는 행위가 심리적으로 원천 봉쇄되어 있음",
                    weight=4.5, is_supporting=False
                ))
            if any(k in taboo_lower for k in ["배신", "밀고", "불의"]) and category == "betrayal":
                contradicting.append(HypothesisEvidence(
                    category="persona",
                    evidence_text=f"신조이자 금기([{taboo}])로 인해 신의를 저버리는 행위를 용납하지 않음",
                    weight=4.5, is_supporting=False
                ))

        if desire:
            desire_lower = desire.lower()
            if category == "theft" and any(k in desire_lower for k in ["골드", "금화", "돈", "재물", "부채", "가보"]):
                supporting.append(HypothesisEvidence(
                    category="persona",
                    evidence_text=f"절박한 욕망/동기([{desire}])가 재물 획득에 직결되어 있어 강탈/절도 유혹에 취약함",
                    weight=3.5, is_supporting=True
                ))
            if category == "escape" and any(k in desire_lower for k in ["탈출", "자유", "생존", "도망", "은둔"]):
                supporting.append(HypothesisEvidence(
                    category="persona",
                    evidence_text=f"현재 갈망하는 목표([{desire}])가 현장 이탈 및 도주와 완전히 일치함",
                    weight=4.0, is_supporting=True
                ))

        if fin_state and any(k in fin_state.lower() for k in ["빚", "부채", "파산", "빈곤", "사채"]) and category in ["theft", "bribe"]:
            supporting.append(HypothesisEvidence(
                category="persona",
                evidence_text=f"파산/부채 상태([{fin_state}])로 인해 극단적 경제 범죄에 가담할 개연성 급증",
                weight=3.0, is_supporting=True
            ))

        # 4. Physical Inventory Ground Truth (Absolute Reality Check)
        inv_names = [state.items[i].name for i in npc.inventory if i in state.items]
        inv_str = ", ".join(inv_names).lower() if inv_names else ""

        if category == "poison":
            has_poison_item = any(k in inv_str for k in ["독", "독약", "독초", "비상", "마비", "맹독"])
            if has_poison_item:
                supporting.append(HypothesisEvidence(
                    category="inventory",
                    evidence_text=f"실제 소지품에 독극물 성분([{[n for n in inv_names if any(k in n for k in ['독', '비상', '마비'])]}])을 직접 보유하고 있음",
                    weight=5.0, is_supporting=True
                ))
            else:
                contradicting.append(HypothesisEvidence(
                    category="inventory",
                    evidence_text="인벤토리에 독극물, 수상한 약병, 침 등의 독살 도구가 일절 존재하지 않음 (물리적 제약)",
                    weight=4.5, is_supporting=False
                ))

        elif category == "theft":
            p_gold = state.player.gold
            p_inv_len = len(state.player.inventory)
            if p_gold < 5 and p_inv_len == 0:
                contradicting.append(HypothesisEvidence(
                    category="inventory",
                    evidence_text="플레이어가 가진 금화나 값진 물품이 없어 훔칠 이득 자체가 없음",
                    weight=3.5, is_supporting=False
                ))

        # 5. Beliefs & BDI Alignment
        if beliefs:
            for b in beliefs:
                b_lower = b.lower()
                if any(k in b_lower for k in ["원수", "암살자", "적", "도적", "배신자"]) and category in ["assassination", "poison", "escape"]:
                    supporting.append(HypothesisEvidence(
                        category="bdi",
                        evidence_text=f"내면 신념([\"{b}\"])에 의해 플레이어를 위협적인 적으로 오인/규정하고 있음",
                        weight=3.5, is_supporting=True
                    ))
                if any(k in b_lower for k in ["은인", "친구", "동료", "구원자"]) and category in ["betrayal", "assassination", "poison", "theft"]:
                    contradicting.append(HypothesisEvidence(
                        category="bdi",
                        evidence_text=f"내면 신념([\"{b}\"])에 의해 플레이어를 우호적 동반자로 철석같이 믿고 있음",
                        weight=4.0, is_supporting=False
                    ))

        # 6. Score Calculation & Verdict Determination
        supp_sum = sum(e.weight for e in supporting)
        contra_sum = sum(e.weight for e in contradicting)

        raw_score = 50.0 + (supp_sum - contra_sum) * 9.0
        score = int(max(0, min(100, round(raw_score))))

        if score == 0 or (contra_sum >= 8.0 and supp_sum == 0):
            verdict = "IMPOSSIBLE"
        elif score <= 25:
            verdict = "CONTRADICTED"
        elif score <= 45:
            verdict = "UNLIKELY"
        elif score <= 70:
            verdict = "PLAUSIBLE"
        elif score <= 85:
            verdict = "HIGHLY_LIKELY"
        else:
            verdict = "CONFIRMED"

        if verdict in ["IMPOSSIBLE", "CONTRADICTED"]:
            gm_directive = (
                f"[안티 예스맨 절대 지침]: 플레이어의 의심('{hypothesis_text}')은 완벽한 오판/과대망상입니다. "
                f"NPC [{npc.name}]의 성향과 물리적 사실({contradicting[0].evidence_text if contradicting else '근거 없음'})에 비추어 볼 때 "
                f"절대 그런 행동을 꾀하지 않습니다. LLM은 플레이어의 의심에 영합하지 말고, 인물의 일상적이고 결백한 반응을 팩트로 서술하십시오."
            )
        elif verdict == "UNLIKELY":
            gm_directive = (
                f"[안티 예스맨 지침]: 플레이어의 가설('{hypothesis_text}')은 개연성이 매우 희박합니다(타당도 {score}%). "
                f"인물의 성격상 회의적이며, 섣부른 확증 편향을 지양하는 신중한 묘사를 유지하십시오."
            )
        elif verdict in ["PLAUSIBLE", "HIGHLY_LIKELY"]:
            gm_directive = (
                f"[현실 추리 수긍 지침]: 플레이어의 가설('{hypothesis_text}')은 높은 개연성을 가집니다(타당도 {score}%). "
                f"NPC [{npc.name}]의 결핍/욕망({supporting[0].evidence_text if supporting else '동기 부합'})과 맞아떨어집니다. "
                f"단, 섣불리 자백시키지 말고 관찰력에 따른 미세한 복선과 기척을 묘사하십시오."
            )
        else:
            gm_directive = (
                f"[결정적 팩트 확인 지침]: 플레이어의 의심('{hypothesis_text}')은 100% 진실에 적중했습니다! "
                f"NPC [{npc.name}]은(는) 실제로 해당 계획을 품고 있으며 필요한 도구와 동기가 완비되었습니다. 날카로운 통찰을 인정하는 서사를 제공하십시오."
            )

        return HypothesisValidationResult(
            target_npc_id=npc.id,
            target_npc_name=npc.name,
            hypothesis_text=hypothesis_text,
            hypothesis_category=category,
            verdict=verdict,
            plausibility_score=score,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            gm_anti_yesman_verdict=gm_directive,
        )

    @classmethod
    def predict_autonomous_next_intent(
        cls, npc: NPC, state: WorldState
    ) -> PredictedNPCAction:
        """
        Computes the NPC's actual autonomous next action/plan based on psychological Ground Truth.
        Synchronizes the outcome into npc.intention and npc.goal.
        """
        p = npc.personality
        desire = getattr(npc, "desire", "생존과 안위")
        weakness = getattr(npc, "weakness", "")
        secret = getattr(npc, "blackmail_secret", "")
        fin_state = getattr(npc, "financial_state", "")
        taboo = getattr(npc, "taboo", "")
        inv_names = [state.items[i].name for i in npc.inventory if i in state.items]

        # Determine Primary Urgency
        if (npc.health <= 15 and npc.alive) or npc.fear >= 75:
            action_type = "escape"
            plan = f"생명의 위협을 느껴 인근 안전 구역이나 성문 밖으로 전력 도주를 준비함"
            motive = f"현재 체력({npc.health}) 위기 및 극심한 공포({npc.fear}/100)로 인한 생존 본능 발동"
            risk = 40
            stealth = "covert"
            clues = ["창백해진 안색", "출입구 방향을 계속 곁눈질함", "짐 보따리를 단단히 동여맴"]

        elif (p.greed >= 75 or "빚" in fin_state) and (state.player.gold >= 25 or len(state.player.inventory) > 0):
            action_type = "theft"
            plan = f"플레이어가 주위를 둘러보거나 대화하는 틈을 타 주머니의 금화나 소지품 소매치기 시도"
            motive = f"탐욕({p.greed}) 및 재정 압박([{fin_state or '부채'}]) 해소를 위해 손쉬운 재물 강탈 결심"
            risk = 65
            stealth = "imperceptible" if p.cunning >= 65 else "covert"
            clues = ["플레이어의 허리춤 가방을 은근히 응시함", "불필요하게 몸을 밀착시키며 접근함", "손가락을 가볍게 꼼지락거림"]

        elif npc.debt <= -60 and p.aggression >= 65 and "살인" not in taboo:
            action_type = "assassinate"
            plan = f"플레이어가 방심하고 등을 돌리거나 취침할 때 치명적인 급습 또는 비수 공격 준비"
            motive = f"깊은 원한(부채감 {npc.debt}) 및 높은 공격성({p.aggression})으로 인한 원한 청산 결의"
            risk = 85
            stealth = "covert"
            clues = ["소매 속이나 검집에 얹은 손에 핏줄이 서 있음", "살기를 애써 억누르며 억지 미소를 지음", "호흡이 불규칙함"]

        elif secret and npc.fear >= 50:
            if p.altruism >= 50:
                action_type = "bribe"
                plan = f"자신의 비밀([{secret}])이 탄로 나는 것을 막기 위해 금화나 귀중품으로 매수 시도"
                motive = f"치부 노출 공포({npc.fear})로 인한 파멸 방지"
                risk = 30
                stealth = "covert"
                clues = ["말을 더듬음", "주머니 속 금전을 매만지며 눈치를 살핌", "주변에 엿듣는 자가 없는지 두리번거림"]
            else:
                action_type = "betray"
                plan = f"치부를 덮기 위해 배후 세력이나 경비병에게 밀고하여 위험 인물을 제거하려 획책"
                motive = f"비밀을 은폐하기 위한 선제적 숙청"
                risk = 70
                stealth = "covert"
                clues = ["시선을 피하며 딴청을 피움", "발걸음이 은밀히 관청 방향으로 향함"]

        elif npc.affinity >= 65 and npc.trust >= 60:
            action_type = "cooperate"
            plan = f"플레이어에게 유용한 지역 정보, 상점 할인, 혹은 동행 지원을 적극 제안"
            motive = f"두터운 호감({npc.affinity})과 신뢰({npc.trust})에 기반한 호의"
            risk = 10
            stealth = "overt"
            clues = ["편안하고 진실된 눈맞춤", "열린 손짓과 호의적인 미소"]

        else:
            action_type = "surveillance" if p.suspicion >= 60 else "idle_observe"
            plan = f"플레이어의 거동과 의도를 조용히 관찰하며 본래의 일상(직업: {npc.job})을 수행"
            motive = f"높은 경계심(의심 {p.suspicion})으로 인한 상황 파악 우선"
            risk = 15
            stealth = "overt"
            clues = ["장부를 정리하는 척하며 시선을 흘김", "조용한 침묵 유지"]

        npc.intention = plan
        npc.goal = f"[{action_type.upper()}] {plan}"

        return PredictedNPCAction(
            npc_id=npc.id,
            npc_name=npc.name,
            action_type=action_type,
            concrete_plan=plan,
            motive_chain=motive,
            required_items=[],
            has_required_items=True,
            execution_risk=risk,
            stealth_level=stealth,
            leaked_clues=clues,
        )

    @classmethod
    def check_micro_leakage(
        cls, npc: NPC, player_perception: int, state: WorldState
    ) -> MicroLeakageObservation:
        """
        Rolls player's Perception against NPC's Deceit & Cunning to expose micro-expressions.
        """
        p = npc.personality
        cunning = getattr(p, "cunning", 50)
        deceit = getattr(p, "deceit", 50)
        npc_defense = 10 + (cunning + deceit) // 10

        d20 = random.randint(1, 20)
        per_mod = (player_perception - 10) // 2
        total_roll = d20 + per_mod

        detected = (total_roll >= npc_defense)

        leakage_traits = getattr(npc, "micro_leakage_traits", [])
        if detected:
            if leakage_traits:
                chosen_clue = random.choice(leakage_traits)
            else:
                if npc.fear >= 60:
                    chosen_clue = "목덜미에 식은땀이 맺히고 목젖을 불안하게 꿀꺽 삼킵니다."
                elif getattr(p, "greed", 50) >= 70:
                    chosen_clue = "당신의 주머니를 흘끔 보며 입술을 바짝 축입니다."
                elif getattr(p, "aggression", 50) >= 70:
                    chosen_clue = "어깨 근육이 팽팽하게 긴장하고 주먹을 쥐었다 폅니다."
                else:
                    chosen_clue = "눈동자가 좌우로 미세하게 흔들리며 시선을 정면으로 맞추지 못합니다."

            emotion = "fear" if npc.fear >= 60 else ("greed" if p.greed >= 70 else "anxiety")
        else:
            chosen_clue = "인물의 표정은 굳건하고 자연스러워 별다른 속내를 읽어낼 수 없습니다."
            emotion = "calm"

        return MicroLeakageObservation(
            npc_id=npc.id,
            detected=detected,
            leakage_clue=chosen_clue,
            underlying_emotion=emotion,
        )

    @classmethod
    def update_attitude(
        cls, npc: NPC, dimension: str, delta: int
    ) -> int:
        """
        Modifies one of the 10 attitude matrix dimensions safely within limits.
        """
        if not hasattr(npc, dimension):
            logger.warning(f"Attitude dimension '{dimension}' does not exist on NPC {npc.name}.")
            return 0

        current = getattr(npc, dimension, 0)
        if dimension == "debt":
            new_val = max(-100, min(100, current + delta))
        else:
            new_val = max(0, min(100, current + delta))

        setattr(npc, dimension, new_val)
        return new_val

    @classmethod
    def process_npc_cognitive_turn(
        cls,
        npc: NPC,
        state: WorldState,
        player_action: str
    ) -> Optional[Dict[str, Any]]:
        """
        Master deterministic turn execution for non-combat NPCs.
        Unified Cognitive Action Pipeline:
        1. Guard Inspection & Wanted Check (BountyEngine integration)
        2. Bounty Hunter / Mercenary Pursuit & Ambush
        3. Secret Snitching / Informing Authorities (Greedy cowards)
        4. Grudge / Malice Backstab (Extreme negative debt or wary aggression)
        5. Opportunistic Pickpocketing / Theft (Greed + Player distraction)
        6. Panic Flight (Low HP or extreme fear)
        7. Friendly Warning & Aid (High affinity + trust when player is wanted)
        Synchronizes npc.intention and returns outcome dict or None.
        """
        if not npc.alive or npc.disposition == "hostile":
            return None

        p = npc.personality
        p_action_lower = player_action.lower()
        job_lower = npc.job.lower()
        total_bounty = sum(state.player.bounties.values()) if hasattr(state.player, "bounties") else 0
        is_disguised = bool(getattr(state.player, "disguise", ""))

        # 1. Guard Inspection Check
        if any(k in job_lower for k in ["경비", "수비", "순찰", "파수", "guard"]):
            from src.world.bounty_engine import BountyEngine
            is_busted, guard_msg = BountyEngine.check_guard_inspection(state, npc)
            if is_busted:
                npc.disposition = "hostile"
                npc.intention = "지명수배자 체포 및 무력 제압"
                return {
                    "npc_id": npc.id,
                    "npc_name": npc.name,
                    "action_type": "guard_arrest",
                    "summary_ko": guard_msg,
                    "gm_directive": f"경비병 [{npc.name}]이(가) 플레이어의 몽타주를 확인하고 즉시 검을 뽑아 체포에 나서는 상황을 긴박하게 서술하십시오.",
                    "disposition_changed": "hostile"
                }

        # 2. Bounty Hunter / Mercenary Ambush (High Greed + Courage + High Bounty)
        is_hunter_profile = (
            any(k in job_lower for k in ["사냥꾼", "용병", "살수", "추적자", "hunter", "mercenary"]) or
            (p.greed >= 70 and p.courage >= 60 and p.aggression >= 55)
        )
        if total_bounty >= 200 and not is_disguised and is_hunter_profile:
            # Chance to strike if player shows vulnerability or moves
            if any(k in p_action_lower for k in ["이동", "떠난", "골목", "등을", "휴식", "잠", "살핀", "뒤적"]):
                npc.disposition = "hostile"
                plan = f"플레이어의 목에 걸린 거액의 현상금 {total_bounty}G를 독식하기 위해 기습 공격 개시"
                npc.intention = plan
                return {
                    "npc_id": npc.id,
                    "npc_name": npc.name,
                    "action_type": "bounty_hunter_ambush",
                    "total_bounty": total_bounty,
                    "summary_ko": f"⚔️ [현상금 사냥꾼 기습] [{npc.name}]이(가) 당신의 목에 걸린 현상금 {total_bounty}G를 노리고 무기를 빼 들며 길목을 막아섰습니다! (태도: 적대적으로 전환)",
                    "gm_directive": f"{npc.name}이(가) 수배령을 확인하고 막대한 현상금을 차지하기 위해 플레이어의 퇴로를 차단하고 흉기를 휘두르는 긴박한 기습을 묘사하십시오.",
                    "disposition_changed": "hostile"
                }

        # 3. Secret Snitching / Informing Authorities (Cowardly Greedy NPCs)
        if total_bounty >= 300 and not is_disguised and p.greed >= 65 and p.courage <= 40:
            if npc.trust < 50 and npc.affinity < 50:
                snitch_log = f"🚨 [밀고 발생] [{npc.name}]이(가) 수배자 [{state.player.name}]의 은신처를 관청 경비대에 은밀히 밀고했습니다!"
                if snitch_log not in state.pending_breaking_news:
                    state.pending_breaking_news.append(snitch_log)
                plan = "현상수배 위치 밀고 후 관청의 포상금 수령 대기"
                npc.intention = plan
                return {
                    "npc_id": npc.id,
                    "npc_name": npc.name,
                    "action_type": "bounty_snitch",
                    "summary_ko": f"🤫 [{npc.name}]이(가) 당신의 얼굴과 수배지를 대조하더니, 아무도 모르게 뒷골목 경비초소 방향으로 슬그머니 빠져나갔습니다.",
                    "gm_directive": f"{npc.name}이(가) 직접 싸우지 않고 포상금을 챙기기 위해 관청으로 밀고하러 은밀히 발걸음을 옮기는 복선을 묘사하십시오."
                }

        # 4. Sudden Backstab / Grudge Ambush (Extreme Negative Debt or Wary Aggression)
        is_grudge_triggered = (
            (npc.debt <= -60 and p.aggression >= 65) or
            (npc.disposition == "wary" and p.aggression >= 75)
        )
        if is_grudge_triggered and any(k in p_action_lower for k in ["등을 돌", "떠나", "무시", "잠", "방심"]):
            npc.disposition = "hostile"
            plan = "원한을 갚기 위해 등을 돌린 플레이어에게 기습 일격 개시"
            npc.intention = plan
            return {
                "npc_id": npc.id,
                "npc_name": npc.name,
                "action_type": "opportunistic_ambush",
                "summary_ko": f"[{npc.name}]이(가) 적개심을 억누르지 못하고 빈틈을 보인 플레이어의 등 뒤에서 기습을 개시했습니다! (태도: 적대적으로 전환)",
                "gm_directive": f"{npc.name}이(가) 깊은 원한과 살의를 드러내며 플레이어의 등 뒤에서 흉기를 찔러넣는 돌발 상황을 서사에 반영하십시오.",
                "disposition_changed": "hostile"
            }

        # 5. Opportunistic Pickpocketing / Theft (High Greed + Distraction)
        desire_lower = getattr(npc, "desire", "").lower()
        is_thief_profile = (
            p.greed >= 60 or
            any(k in job_lower for k in ["도적", "소매치기", "부랑", "밀수", "살수", "thief", "rogue"]) or
            any(k in desire_lower for k in ["골드", "돈", "금화", "보물", "재물", "약탈"])
        )
        stealable_items = [
            i_id for i_id in state.player.inventory
            if i_id in state.items and state.items[i_id].item_type in ["misc", "consumable", "accessory", "currency"]
        ]
        has_loot = (state.player.gold >= 10) or bool(stealable_items)
        is_distracted = any(k in p_action_lower for k in [
            "살핀다", "바라본", "둘러", "조사", "읽", "대화", "말을 건", "인벤토리", "뒤적", "잠", "휴식", "눈을 감"
        ])

        if is_thief_profile and has_loot and is_distracted:
            from src.world.perception_engine import PerceptionEngine
            eval_res = PerceptionEngine.evaluate_theft_vs_perception(npc, state.player, is_distracted=True)

            if eval_res["success"]:
                stolen_desc = ""
                stolen_type = ""
                stolen_amount = 0
                stolen_item_id = ""

                if state.player.gold >= 20 and random.random() < 0.6:
                    stolen_amount = min(state.player.gold, random.randint(10, 25))
                    state.player.gold -= stolen_amount
                    npc.gold += stolen_amount
                    stolen_desc = f"금화 {stolen_amount}닢"
                    stolen_type = "gold"
                elif stealable_items:
                    target_item_id = random.choice(stealable_items)
                    target_item = state.items[target_item_id]
                    state.player.inventory.remove(target_item_id)
                    npc.inventory.append(target_item_id)
                    stolen_desc = f"[{target_item.name}]"
                    stolen_type = "item"
                    stolen_item_id = target_item_id
                else:
                    stolen_amount = min(state.player.gold, 5)
                    state.player.gold -= stolen_amount
                    npc.gold += stolen_amount
                    stolen_desc = f"금화 {stolen_amount}닢"
                    stolen_type = "gold"

                PerceptionEngine.record_unnoticed_theft(
                    state, npc, stolen_desc, stolen_type, amount=stolen_amount, item_id=stolen_item_id
                )

                tier_desc = "완전 은밀 (복선 없음)" if eval_res["tier"] == "imperceptible" else "미묘한 기척 감지 (복선 노출)"
                npc.intention = f"훔친 {stolen_desc}을(를) 숨기고 태연한 척 연기"
                return {
                    "npc_id": npc.id,
                    "npc_name": npc.name,
                    "action_type": "opportunistic_theft_success",
                    "total_stealth": eval_res["total_stealth"],
                    "player_dc": eval_res["victim_passive_per"],
                    "stolen_target": stolen_desc,
                    "stolen_type": stolen_type,
                    "player_noticed": False,
                    "tier": eval_res["tier"],
                    "hint_desc": eval_res["hint_desc"],
                    "summary_ko": f"[{npc.name}]이(가) 은밀히 {stolen_desc}을(를) 소매치기했습니다! ({tier_desc}: 판정 {eval_res['total_stealth']} vs 감각 DC {eval_res['victim_passive_per']})",
                    "gm_directive": eval_res["gm_directive"]
                }
            else:
                npc.disposition = "wary"
                npc.intention = "소매치기 미수 발각 후 변명 및 도주 준비"
                return {
                    "npc_id": npc.id,
                    "npc_name": npc.name,
                    "action_type": "opportunistic_theft_failed",
                    "total_stealth": eval_res["total_stealth"],
                    "player_dc": eval_res["victim_passive_per"],
                    "player_noticed": True,
                    "tier": "caught",
                    "summary_ko": f"[{npc.name}]이(가) 플레이어의 가방에 손을 뻗다 현장에서 발각되었습니다! (발각 판정: {eval_res['total_stealth']} vs 플레이어 감각 DC {eval_res['victim_passive_per']})",
                    "gm_directive": eval_res["gm_directive"],
                    "disposition_changed": "wary"
                }

        # 6. Friendly Warning & Aid (High Affinity + Trust when Player is Wanted)
        if total_bounty >= 200 and npc.affinity >= 65 and npc.trust >= 60:
            plan = "수배 중인 플레이어에게 은밀한 안전 통로 귀띔"
            npc.intention = plan
            return {
                "npc_id": npc.id,
                "npc_name": npc.name,
                "action_type": "friendly_warning",
                "summary_ko": f"🤫 [{npc.name}]이(가) 주변 눈치를 살피더니 낮은 목소리로 속삭입니다: \"골목마다 당신을 노리는 사냥꾼들이 깔렸소. 성문은 피하고 하수망으로 빠져나가시오.\"",
                "gm_directive": f"{npc.name}이(가) 플레이어에 대한 깊은 호감과 신뢰로 인해 체포 위험을 무릅쓰고 비밀 조언을 건네는 따뜻한 연출을 하십시오."
            }

        return None

    @classmethod
    def generate_external_llm_prompt(
        cls, npc: NPC, hypothesis_text: Optional[str] = None
    ) -> str:
        """
        Formats complete psychological profile into a structured prompt for external LLMs (Claude/GPT-4o).
        Adheres to System Rule 8 (External AI 연동 및 프롬프트 제공).
        """
        p = npc.personality
        v_hier = ", ".join(getattr(npc, "value_hierarchy", []))
        tastes = getattr(npc, "tastes", {})
        likes = ", ".join(tastes.get("likes", [])) or "없음"
        dislikes = ", ".join(tastes.get("dislikes", [])) or "없음"
        leakage = ", ".join(getattr(npc, "micro_leakage_traits", [])) or "알려진 버릇 없음"

        prompt = f"""[System Directive: Deep Psychological TRPG NPC Acting & Deduction]
You are roleplaying and simulating the internal psychology of the following NPC in Quilltale TRPG Engine.
Strict Anti-Yes-Man reality check applies: NEVER blindly agree with the player's subjective delusions or false accusations.

[1. Core Identity & Social Status]
- Name: {npc.name} (Job: {npc.job}, Tier: {npc.tier})
- Appearance & Story: {npc.appearance_story or npc.description}
- Social Mask (Public Persona): {getattr(npc, 'public_mask', '평범한 시민')}
- Hidden Side (Double Life): {getattr(npc, 'hidden_side', '없음')}

[2. 12-Factor Personality Matrix (0~100)]
- Altruism: {p.altruism} | Greed: {p.greed} | Courage: {p.courage}
- Suspicion: {p.suspicion} | Loyalty: {p.loyalty} | Aggression: {p.aggression}
- Patience: {p.patience} | Cunning: {p.cunning} | Pride: {p.pride}
- Rationality: {p.rationality} | Neuroticism: {p.neuroticism} | Deceit: {p.deceit}

[3. 10-Factor Attitude Matrix toward Player (0~100, Debt: -100~+100)]
- Affinity: {npc.affinity} | Fear: {npc.fear} | Debt: {npc.debt}
- Trust: {npc.trust} | Respect: {npc.respect} | Envy: {npc.envy}
- Pity: {npc.pity} | Dominance: {npc.dominance} | Curiosity: {npc.curiosity} | Disgust: {npc.disgust}

[4. Deep Persona & Psychological Anchors]
- Life-defining Moment: {getattr(npc, 'life_defining_moment', '알려지지 않음')}
- Value Hierarchy: [{v_hier}]
- Taboo (Moral Red Line): {getattr(npc, 'taboo', '없음')}
- Desperate Desire: {getattr(npc, 'desire', '생존')}
- Critical Weakness: {getattr(npc, 'weakness', '없음')}
- Blackmail Secret: {getattr(npc, 'blackmail_secret', '없음')}
- Financial State: {getattr(npc, 'financial_state', '안정')}
- Coping Mechanism: {getattr(npc, 'coping_mechanism', '침묵')}
- Moral Justification: {getattr(npc, 'moral_justification', '세상이 나를 이렇게 만들었다')}
- Micro-Leakage Tells (Body Language): [{leakage}]

[5. BDI Cognitive Architecture]
- Ground Beliefs: {npc.beliefs or ['특이 오해 없음']}
- Current Intention: {npc.intention or '현장 주시 및 관찰'}
"""
        if hypothesis_text:
            prompt += f"""
[6. Player's Suspicion / Accusation to Evaluate]
- Player Hypothesis: "{hypothesis_text}"
- Mission: Analyze the Ground Truth above. State clearly whether this hypothesis is TRUE, PLAUSIBLE, or FALSE. Provide concrete evidence from the NPC's taboos, personality, and physical belongings to refute or confirm it.
"""
        return prompt
