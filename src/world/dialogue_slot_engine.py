"""
Deterministic NPC Dialogue Slot Assembly Engine for Quilltale TRPG.

Assembles contextual, personality-aligned dialogue strings deterministically
from psychological facts (archetypes, emotions, stress, traits, and relationships)
without calling external LLM APIs (0 cost, 0.0001s latency).

Rules Compliance:
- Rule 1, 2: 100% Deterministic Python logic.
- Rule 5: New game data classes MUST include traits: list[str] = field(default_factory=list).
- UTF-8 encoding explicit.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from src.world.state import NPC

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE_PATH = Path("data") / "templates" / "dialogue_slots.json"


@dataclass
class DialogueResult:
    """Represents a deterministically assembled dialogue result."""
    speaker_name: str
    gesture: str
    body: str
    tail: str
    full_text: str
    archetype: str
    intent: str
    traits: list[str] = field(default_factory=lambda: ["dialogue_result", "deterministic_slot"])

    def to_dict(self) -> dict[str, str | list[str]]:
        return {
            "speaker_name": self.speaker_name,
            "gesture": self.gesture,
            "body": self.body,
            "tail": self.tail,
            "full_text": self.full_text,
            "archetype": self.archetype,
            "intent": self.intent,
            "traits": list(self.traits),
        }


@dataclass
class IntentRoutingResult:
    """
    Result of classifying dialogue intent and routing decision (0-token slot vs LLM API).
    """
    intent: str
    requires_llm: bool
    confidence: float
    matched_keyword: Optional[str] = None
    target_npc_name: Optional[str] = None
    traits: list[str] = field(default_factory=lambda: ["intent_routing", "deterministic"])

    def to_dict(self) -> dict[str, object]:
        return {
            "intent": self.intent,
            "requires_llm": self.requires_llm,
            "confidence": self.confidence,
            "matched_keyword": self.matched_keyword,
            "target_npc_name": self.target_npc_name,
            "traits": list(self.traits),
        }


class DialogueSlotEngine:
    """
    Deterministic rule-based engine assembling NPC dialogue from template parts
    and routing intent between 0-cost local slots and external LLM APIs.
    """
    _cached_templates: Optional[dict[str, Dict[str, object]]] = None

    @classmethod
    def classify_intent(
        cls,
        action: str,
        present_npc_names: Optional[list[str]] = None,
    ) -> IntentRoutingResult:
        """
        Classifies player dialogue action into either:
        1. Deterministic routine intent (requires_llm=False) -> 0 cost, instant slot assembly.
        2. Deep inquiry / open-ended conversation (requires_llm=True) -> routes to LLM.
        """
        act = (action or "").strip()
        act_lower = act.lower()

        # Identify targeted NPC if names provided
        target_name: Optional[str] = None
        if present_npc_names:
            for name in present_npc_names:
                if name.lower() in act_lower:
                    target_name = name
                    break

        # 1. Deep inquiry / Open-ended reasoning check (Requires LLM)
        deep_keywords = [
            "왜", "어째서", "이유", "비밀", "음모", "배신", "진실", "어떻게 생각",
            "과거", "소문", "배후", "정체", "목적", "알고 싶", "해석", "속셈",
            "동료가 돼라", "내 편이 돼라", "설득한다", "회유한다", "심문한다",
            "why", "secret", "truth", "conspiracy", "betray", "convince", "interrogate"
        ]
        for kw in deep_keywords:
            if kw in act_lower:
                return IntentRoutingResult(
                    intent="deep_inquiry",
                    requires_llm=True,
                    confidence=0.9,
                    matched_keyword=kw,
                    target_npc_name=target_name,
                    traits=["intent_routing", "deep_inquiry", "llm_required"],
                )

        # 2. Threat / Coercion (Deterministic)
        threat_keywords = ["threat", "위협", "칼을 겨", "칼을 뽑", "목에 칼", "죽인다", "죽여", "두고 봐", "해치겠", "덤벼", "박살내"]
        for kw in threat_keywords:
            if kw in act_lower:
                return IntentRoutingResult(
                    intent="threat_reaction",
                    requires_llm=False,
                    confidence=0.95,
                    matched_keyword=kw,
                    target_npc_name=target_name,
                    traits=["intent_routing", "threat_reaction", "deterministic_slot"],
                )

        # 3. Quest Accept (Deterministic)
        quest_accept_keywords = ["수락", "맡겠", "하겠소", "도와주겠", "동의", "accept", "맡겨", "내가 하지", "갈게", "참여하겠", "수락한다"]
        for kw in quest_accept_keywords:
            if kw in act_lower:
                return IntentRoutingResult(
                    intent="quest_accept",
                    requires_llm=False,
                    confidence=0.95,
                    matched_keyword=kw,
                    target_npc_name=target_name,
                    traits=["intent_routing", "quest_accept", "deterministic_slot"],
                )

        # 4. Quest Reject (Deterministic)
        quest_reject_keywords = ["거절", "거부", "싫", "관심 없", "reject", "안 해", "못 해", "바빠", "사양", "거절한다"]
        for kw in quest_reject_keywords:
            if kw in act_lower:
                return IntentRoutingResult(
                    intent="quest_reject",
                    requires_llm=False,
                    confidence=0.95,
                    matched_keyword=kw,
                    target_npc_name=target_name,
                    traits=["intent_routing", "quest_reject", "deterministic_slot"],
                )

        # 5. Quest Offer / Inquiry (Deterministic)
        quest_offer_keywords = ["quest", "의뢰", "일감", "일거리", "부탁", "도움 필요", "할 일", "보상", "일 있"]
        for kw in quest_offer_keywords:
            if kw in act_lower:
                return IntentRoutingResult(
                    intent="quest_offer",
                    requires_llm=False,
                    confidence=0.9,
                    matched_keyword=kw,
                    target_npc_name=target_name,
                    traits=["intent_routing", "quest_offer", "deterministic_slot"],
                )

        # 6. Shop Buy (Deterministic)
        shop_buy_keywords = ["buy", "구매", "사다", "사겠", "얼마", "가격", "구입", "계산", "넘겨", "지불", "산다"]
        for kw in shop_buy_keywords:
            if kw in act_lower:
                return IntentRoutingResult(
                    intent="shop_buy",
                    requires_llm=False,
                    confidence=0.95,
                    matched_keyword=kw,
                    target_npc_name=target_name,
                    traits=["intent_routing", "shop_buy", "deterministic_slot"],
                )

        # 7. Shop Browse (Deterministic)
        shop_browse_keywords = ["둘러", "살피", "구경", "browse", "목록", "상품", "보여줘", "물건 봐", "진열", "상점", "품목"]
        for kw in shop_browse_keywords:
            if kw in act_lower:
                return IntentRoutingResult(
                    intent="shop_browse",
                    requires_llm=False,
                    confidence=0.9,
                    matched_keyword=kw,
                    target_npc_name=target_name,
                    traits=["intent_routing", "shop_browse", "deterministic_slot"],
                )

        # 8. Routine Greeting / Small Talk (Deterministic)
        greeting_keywords = ["안녕", "인사", "반갑", "좋은 아침", "좋은 날", "오랜만", "hello", "hi", "greet", "말을 건다", "대화한다", "말걸기", "talk", "speak"]
        for kw in greeting_keywords:
            if kw in act_lower:
                return IntentRoutingResult(
                    intent="greeting",
                    requires_llm=False,
                    confidence=0.85,
                    matched_keyword=kw,
                    target_npc_name=target_name,
                    traits=["intent_routing", "greeting", "deterministic_slot"],
                )

        # Fallback: If free-form unknown input, route to LLM for safety
        return IntentRoutingResult(
            intent="unknown",
            requires_llm=True,
            confidence=0.5,
            matched_keyword=None,
            target_npc_name=target_name,
            traits=["intent_routing", "unknown", "llm_required"],
        )

    @classmethod
    def load_templates(cls, path: Path | str = DEFAULT_TEMPLATE_PATH) -> dict[str, Dict[str, object]]:
        """Loads and caches dialogue slot templates from JSON."""
        if cls._cached_templates is not None:
            return cls._cached_templates

        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent.parent
            resolved_path = base_dir / path

        if not resolved_path.exists():
            logger.warning("Dialogue slot template file not found at %s. Using fallback empty templates.", resolved_path)
            cls._cached_templates = {"archetype_tones": {}, "gestures": {}, "trait_tails": {}}
            return cls._cached_templates

        with open(resolved_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cls._cached_templates = data
        return cls._cached_templates

    @classmethod
    def reset_cache(cls) -> None:
        """Resets cached templates (useful for testing)."""
        cls._cached_templates = None

    @classmethod
    def _deterministic_index(cls, seed_str: str, max_count: int) -> int:
        """Derives a deterministic index in [0, max_count) using SHA-256 hash."""
        if max_count <= 1:
            return 0
        digest = hashlib.sha256(seed_str.encode("utf-8")).digest()
        value = int.from_bytes(digest[:4], byteorder="big")
        return value % max_count

    @classmethod
    def assemble_dialogue(
        cls,
        npc: NPC,
        intent: str,
        relationship_score: int = 50,
        seed_modifier: int = 0,
        target_name: Optional[str] = None,
    ) -> DialogueResult:
        """
        Deterministically builds a full dialogue utterance based on NPC psychological state.
        
        Args:
            npc: Target NPC containing personality, stress, and emotion_state.
            intent: Interaction intent (e.g. 'greeting', 'shop_browse', 'shop_buy',
                    'quest_offer', 'quest_accept', 'quest_reject', 'threat_reaction').
            relationship_score: 0-100 relationship score with player (defaults to 50 neutral).
            seed_modifier: Optional integer modifier for variation.
            target_name: Optional entity or item name referenced in dialogue.
        """
        templates = cls.load_templates()
        archetype_tones = templates.get("archetype_tones", {})
        gestures_dict = templates.get("gestures", {})
        trait_tails_dict = templates.get("trait_tails", {})

        npc_id = getattr(npc, "id", "unknown_npc")
        npc_name = getattr(npc, "name", "NPC")
        archetype = getattr(npc, "archetype_template", "cautious_scholar") or "cautious_scholar"
        stress = getattr(npc, "stress", 20)
        emotion_state = getattr(npc, "emotion_state", {}) or {}

        # 1. Determine gesture key
        gesture_key = "stress_calm"
        # Check high acute emotions first
        if emotion_state.get("anger", 0) >= 65:
            gesture_key = "anger_high"
        elif emotion_state.get("fear", 0) >= 65:
            gesture_key = "fear_high"
        elif emotion_state.get("greed", 0) >= 70:
            gesture_key = "greed_high"
        elif stress >= 86:
            gesture_key = "stress_breakdown"
        elif stress >= 61:
            gesture_key = "stress_high"
        elif stress >= 31:
            gesture_key = "stress_mild"
        else:
            gesture_key = "stress_calm"

        gesture_options: list[str] = gestures_dict.get(gesture_key, ["(묵묵히 쳐다본다)"])
        g_idx = cls._deterministic_index(f"{npc_id}_gesture_{seed_modifier}_{gesture_key}", len(gesture_options))
        gesture = gesture_options[g_idx]

        # 2. Determine resolved intent key
        resolved_intent = intent
        if intent == "greeting":
            if relationship_score <= 30:
                resolved_intent = "greeting_hostile"
            elif relationship_score >= 70:
                resolved_intent = "greeting_friendly"
            else:
                resolved_intent = "greeting_neutral"

        # 3. Retrieve archetype speech body
        arch_data = archetype_tones.get(archetype, {})
        if not arch_data:
            arch_data = archetype_tones.get("cautious_scholar", {})

        intents_dict = arch_data.get("intents", {})
        body_options: list[str] = intents_dict.get(resolved_intent, intents_dict.get("greeting_neutral", ["무슨 용건이오?"]))
        b_idx = cls._deterministic_index(f"{npc_id}_body_{seed_modifier}_{resolved_intent}", len(body_options))
        body = body_options[b_idx]

        if target_name:
            body = body.replace("{target_name}", target_name)

        # 4. Determine trait tail (suppress benevolent/unrelated tails in hostile or threat contexts)
        p = getattr(npc, "personality", None)
        tail = ""
        tail_candidates: list[tuple[str, int]] = []
        if p is not None and resolved_intent not in ("threat_reaction", "greeting_hostile"):
            if getattr(p, "greed", 0) >= 75:
                tail_candidates.append(("greed_high", getattr(p, "greed", 0)))
            if getattr(p, "suspicion", 0) >= 75:
                tail_candidates.append(("suspicion_high", getattr(p, "suspicion", 0)))
            if getattr(p, "altruism", 0) >= 75:
                tail_candidates.append(("altruism_high", getattr(p, "altruism", 0)))
            if getattr(p, "pride", 0) >= 75:
                tail_candidates.append(("pride_high", getattr(p, "pride", 0)))

        # Pick the most prominent trait if multiple exceed threshold
        if tail_candidates:
            tail_candidates.sort(key=lambda x: x[1], reverse=True)
            chosen_tail_key = tail_candidates[0][0]
            tails_list = trait_tails_dict.get(chosen_tail_key, [])
            if tails_list:
                t_idx = cls._deterministic_index(f"{npc_id}_tail_{seed_modifier}_{chosen_tail_key}", len(tails_list))
                tail = tails_list[t_idx]

        # 5. Assemble full utterance
        if tail:
            full_text = f'{gesture} "{body} {tail}"'
        else:
            full_text = f'{gesture} "{body}"'

        return DialogueResult(
            speaker_name=npc_name,
            gesture=gesture,
            body=body,
            tail=tail,
            full_text=full_text,
            archetype=archetype,
            intent=resolved_intent,
            traits=["dialogue_result", archetype, resolved_intent, gesture_key],
        )
