"""
Quilltale TRPG Deterministic NPC Psychology Engine (Master Brief Spec)

This module implements the core psychology subsystems:
1. 8 Archetype Personality Templates with Seeded Variation
2. 14-Factor Concurrent Emotion Simulation & Decay
3. Independent Psychological Stress (0-100) & Persona-aligned Breakdown
4. Contextual Causal Trauma Activation & Recovery
5. Multi-Entity 9-Axis Relationship Matrix with Legacy Player Attitude Projection

Rules Compliance:
- Rule 1, 2: 100% Deterministic Python calculations (Pass 1). No LLM hallucinations.
- Rule 5: Extends existing NPC, NPCPersonality, and WorldState without duplication.
- Rule 6: Every dataclass carries traits: list[str] = field(default_factory=list).
"""
import logging
from dataclasses import dataclass, field
from typing import Any

from src.world.state import NPC

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. 8 ARCHETYPE PERSONALITY TEMPLATES (Section 6)
# ==============================================================================

@dataclass
class PersonalityTemplate:
    """Immutable archetype personality distribution template."""
    id: str
    name_ko: str
    personality_axes: dict[str, int]       # 12 axes baselines (0-100)
    value_hierarchy: list[str]             # default value priority
    dominant_motivation: str               # primary long-term desire
    risk_tolerance: int                    # 0-100
    trauma_susceptibility: list[str]       # tags this archetype is sensitive to
    traits: list[str] = field(default_factory=list)


PERSONALITY_TEMPLATES: dict[str, PersonalityTemplate] = {
    "cautious_scholar": PersonalityTemplate(
        id="cautious_scholar",
        name_ko="신중한 학자",
        personality_axes={
            "altruism": 50, "greed": 40, "courage": 30, "suspicion": 60, "loyalty": 55, "aggression": 20,
            "patience": 75, "cunning": 60, "pride": 50, "rationality": 85, "neuroticism": 45, "deceit": 30
        },
        value_hierarchy=["knowledge", "safety", "autonomy", "honor", "wealth"],
        dominant_motivation="curiosity_safety",
        risk_tolerance=25,
        trauma_susceptibility=["mind_control", "loss_of_manuscripts", "irrational_violence"],
        traits=["신중한_학자", "분석적", "높은_이성", "위험회피"]
    ),
    "reckless_adventurer": PersonalityTemplate(
        id="reckless_adventurer",
        name_ko="무모한 모험가",
        personality_axes={
            "altruism": 60, "greed": 55, "courage": 85, "suspicion": 30, "loyalty": 60, "aggression": 55,
            "patience": 20, "cunning": 40, "pride": 65, "rationality": 40, "neuroticism": 35, "deceit": 25
        },
        value_hierarchy=["freedom", "glory", "adventure", "achievement", "wealth"],
        dominant_motivation="achievement_autonomy",
        risk_tolerance=80,
        trauma_susceptibility=["confinement", "maiming", "humiliation"],
        traits=["무모한_모험가", "스릴추구", "높은_용기", "충동적"]
    ),
    "devoted_knight": PersonalityTemplate(
        id="devoted_knight",
        name_ko="헌신적인 기사",
        personality_axes={
            "altruism": 75, "greed": 25, "courage": 80, "suspicion": 40, "loyalty": 90, "aggression": 45,
            "patience": 65, "cunning": 35, "pride": 70, "rationality": 60, "neuroticism": 30, "deceit": 15
        },
        value_hierarchy=["duty", "honor", "loyalty", "protection", "faith"],
        dominant_motivation="loyalty_meaning",
        risk_tolerance=55,
        trauma_susceptibility=["broken_oath", "dishonor", "failed_protection"],
        traits=["헌신적인_기사", "기사도", "높은_충성", "명예존중"]
    ),
    "cynical_mercenary": PersonalityTemplate(
        id="cynical_mercenary",
        name_ko="냉소적인 용병",
        personality_axes={
            "altruism": 25, "greed": 80, "courage": 60, "suspicion": 75, "loyalty": 40, "aggression": 65,
            "patience": 50, "cunning": 80, "pride": 55, "rationality": 70, "neuroticism": 40, "deceit": 65
        },
        value_hierarchy=["survival", "wealth", "autonomy", "power", "comfort"],
        dominant_motivation="survival_wealth",
        risk_tolerance=60,
        trauma_susceptibility=["betrayal", "starvation", "debt_slavery"],
        traits=["냉소적인_용병", "실리주의", "경계심", "금전집착"]
    ),
    "ambitious_noble": PersonalityTemplate(
        id="ambitious_noble",
        name_ko="야심찬 귀족",
        personality_axes={
            "altruism": 30, "greed": 75, "courage": 50, "suspicion": 65, "loyalty": 45, "aggression": 40,
            "patience": 60, "cunning": 85, "pride": 90, "rationality": 75, "neuroticism": 50, "deceit": 70
        },
        value_hierarchy=["status", "power", "family", "achievement", "wealth"],
        dominant_motivation="status_power",
        risk_tolerance=65,
        trauma_susceptibility=["disgrace", "poverty", "loss_of_title"],
        traits=["야심찬_귀족", "권력욕", "높은_자존심", "모략가"]
    ),
    "gentle_healer": PersonalityTemplate(
        id="gentle_healer",
        name_ko="다정한 치유사",
        personality_axes={
            "altruism": 90, "greed": 20, "courage": 45, "suspicion": 25, "loyalty": 70, "aggression": 10,
            "patience": 85, "cunning": 30, "pride": 40, "rationality": 65, "neuroticism": 45, "deceit": 15
        },
        value_hierarchy=["compassion", "life", "community", "family", "peace"],
        dominant_motivation="belonging_affection",
        risk_tolerance=20,
        trauma_susceptibility=["mass_death", "helpless_patient_loss", "contagion"],
        traits=["다정한_치유사", "이타주의", "높은_인내", "생명존중"]
    ),
    "paranoid_survivor": PersonalityTemplate(
        id="paranoid_survivor",
        name_ko="편집증 생존자",
        personality_axes={
            "altruism": 20, "greed": 50, "courage": 35, "suspicion": 92, "loyalty": 30, "aggression": 50,
            "patience": 40, "cunning": 75, "pride": 40, "rationality": 50, "neuroticism": 88, "deceit": 60
        },
        value_hierarchy=["survival", "safety", "autonomy", "secrecy", "wealth"],
        dominant_motivation="survival_safety",
        risk_tolerance=15,
        trauma_susceptibility=["ambush", "poison", "false_friendship"],
        traits=["편집증_생존자", "극도의_의심", "신경증", "안전제일"]
    ),
    "zealous_inquisitor": PersonalityTemplate(
        id="zealous_inquisitor",
        name_ko="광신적 이단심문관",
        personality_axes={
            "altruism": 35, "greed": 20, "courage": 80, "suspicion": 80, "loyalty": 85, "aggression": 75,
            "patience": 45, "cunning": 65, "pride": 80, "rationality": 70, "neuroticism": 55, "deceit": 40
        },
        value_hierarchy=["faith", "order", "justice", "duty", "truth"],
        dominant_motivation="meaning_purity",
        risk_tolerance=60,
        trauma_susceptibility=["heresy", "demonic_corruption", "sacrilege"],
        traits=["광신적_심문관", "신념형", "단호함", "죄악불관용"]
    )
}


def apply_personality_template(npc: NPC, template_id: str, seed_variance: int = 0) -> None:
    """
    Applies an archetype template to an NPC with deterministic pseudo-variance.
    Never mutates the global template; generates unique per-instance personality.
    """
    import hashlib
    if template_id not in PERSONALITY_TEMPLATES:
        template_id = "cynical_mercenary"
    tmpl = PERSONALITY_TEMPLATES[template_id]
    npc.archetype_template = template_id

    # Cryptographically deterministic variance per NPC instance and seed
    seed_bytes = f"{npc.id}_{template_id}_{seed_variance}".encode()
    digest = hashlib.sha256(seed_bytes).digest()

    def get_var(idx: int) -> int:
        byte_val = digest[idx % len(digest)]
        return (byte_val % 15) - 7  # -7 to +7 variance

    axes = tmpl.personality_axes
    p = npc.personality
    p.altruism = max(0, min(100, axes["altruism"] + get_var(0)))
    p.greed = max(0, min(100, axes["greed"] + get_var(1)))
    p.courage = max(0, min(100, axes["courage"] + get_var(2)))
    p.suspicion = max(0, min(100, axes["suspicion"] + get_var(3)))
    p.loyalty = max(0, min(100, axes["loyalty"] + get_var(4)))
    p.aggression = max(0, min(100, axes["aggression"] + get_var(5)))
    p.patience = max(0, min(100, axes["patience"] + get_var(6)))
    p.cunning = max(0, min(100, axes["cunning"] + get_var(7)))
    p.pride = max(0, min(100, axes["pride"] + get_var(8)))
    p.rationality = max(0, min(100, axes["rationality"] + get_var(9)))
    p.neuroticism = max(0, min(100, axes["neuroticism"] + get_var(10)))
    p.deceit = max(0, min(100, axes["deceit"] + get_var(11)))

    # Synchronize value hierarchy and risk tolerance
    npc.value_hierarchy = list(tmpl.value_hierarchy)
    npc.risk_tolerance = max(0, min(100, tmpl.risk_tolerance + get_var(12)))
    for t in tmpl.traits:
        if t not in npc.traits:
            npc.traits.append(t)



# ==============================================================================
# 2. 14-FACTOR CONCURRENT EMOTION SIMULATION (Section 7.1)
# ==============================================================================

VALID_EMOTIONS = {
    "fear", "anger", "joy", "grief", "disgust", "curiosity",
    "pride", "shame", "guilt", "hope", "contempt", "affection",
    "anxiety", "excitement"
}


class EmotionEngine:
    """Manages multi-emotion lifecycle, personality sensitivity, and decay."""

    @classmethod
    def trigger_emotion(
        cls,
        npc: NPC,
        emotion: str,
        base_intensity: int,
        source: str,
        duration: int = 3,
        decay_rate: float = 1.0
    ) -> dict[str, Any]:
        """
        Triggers or strengthens an emotion, scaled by NPC personality sensitivity.
        Clamps intensity to 0-100.
        """
        if emotion not in VALID_EMOTIONS:
            return {"status": "ignored", "reason": f"invalid emotion {emotion}"}

        # Personality sensitivity scaling
        multiplier = 1.0
        p = npc.personality
        if emotion == "fear":
            multiplier = 0.5 + (p.neuroticism / 100.0) * 0.8 - (p.courage / 100.0) * 0.4
        elif emotion == "anger":
            multiplier = 0.5 + (p.aggression / 100.0) * 0.8 - (p.patience / 100.0) * 0.4
        elif emotion == "curiosity":
            multiplier = 0.6 + (p.rationality / 100.0) * 0.6
        elif emotion == "guilt" or emotion == "shame":
            multiplier = 0.4 + (p.altruism / 100.0) * 0.8 - (p.deceit / 100.0) * 0.3
        elif emotion == "anxiety":
            multiplier = 0.4 + (p.neuroticism / 100.0) * 0.8 + (p.suspicion / 100.0) * 0.3

        effective_intensity = max(5, min(100, int(base_intensity * multiplier)))

        current = npc.emotion_state.get(emotion)
        if current:
            # Blend existing emotion
            new_intensity = min(100, current.get("intensity", 0) + int(effective_intensity * 0.6))
            new_duration = max(current.get("duration", 0), duration)
            npc.emotion_state[emotion] = {
                "intensity": new_intensity,
                "source": source,
                "duration": new_duration,
                "decay": decay_rate
            }
        else:
            npc.emotion_state[emotion] = {
                "intensity": effective_intensity,
                "source": source,
                "duration": duration,
                "decay": decay_rate
            }

        npc.state_version += 1
        return {"emotion": emotion, "intensity": npc.emotion_state[emotion]["intensity"]}

    @classmethod
    def decay_emotions(cls, npc: NPC) -> list[str]:
        """Performs deterministic per-tick emotional decay. Removes expired emotions."""
        expired = []
        for emo, data in list(npc.emotion_state.items()):
            intensity = data.get("intensity", 0)
            duration = data.get("duration", 1)
            decay = data.get("decay", 1.0)

            # Decay intensity
            step_decay = int(10 * decay)
            new_intensity = intensity - step_decay
            new_duration = duration - 1

            if new_intensity <= 0 or new_duration <= 0:
                expired.append(emo)
                del npc.emotion_state[emo]
            else:
                data["intensity"] = new_intensity
                data["duration"] = new_duration

        if expired:
            npc.state_version += 1
        return expired

    @classmethod
    def get_dominant_emotion(cls, npc: NPC) -> tuple[str | None, int]:
        """Returns the dominant emotion (highest intensity) without discarding others."""
        if not npc.emotion_state:
            return None, 0
        sorted_emotions = sorted(
            npc.emotion_state.items(),
            key=lambda item: item[1].get("intensity", 0),
            reverse=True
        )
        top = sorted_emotions[0]
        return top[0], top[1].get("intensity", 0)

    @classmethod
    def get_action_modifiers(cls, npc: NPC) -> dict[str, float]:
        """Translates current emotional state into action category scoring modifiers."""
        mods = {
            "escape": 0.0, "attack": 0.0, "cooperate": 0.0,
            "bribe": 0.0, "theft": 0.0, "betray": 0.0, "hide": 0.0
        }
        for emo, data in npc.emotion_state.items():
            lvl = data.get("intensity", 0) / 100.0
            if emo == "fear":
                mods["escape"] += lvl * 25.0
                mods["hide"] += lvl * 20.0
                mods["attack"] -= lvl * 15.0
            elif emo == "anger":
                mods["attack"] += lvl * 30.0
                mods["cooperate"] -= lvl * 20.0
            elif emo == "anxiety":
                mods["hide"] += lvl * 15.0
                mods["escape"] += lvl * 10.0
            elif emo == "affection":
                mods["cooperate"] += lvl * 25.0
                mods["betray"] -= lvl * 30.0
            elif emo == "contempt":
                mods["cooperate"] -= lvl * 25.0
                mods["betray"] += lvl * 15.0
        return mods


# ==============================================================================
# 3. INDEPENDENT PSYCHOLOGICAL STRESS (0-100) (Section 7.2)
# ==============================================================================

class StressEngine:
    """Manages 0-100 stress accumulation, recovery, and persona-aligned breakdown."""

    @classmethod
    def get_stress_stage(cls, stress: int) -> str:
        """Returns one of 5 stress stages."""
        if stress < 25:
            return "normal"
        elif stress < 50:
            return "reactive"
        elif stress < 75:
            return "impaired"
        elif stress < 90:
            return "severe_distortion"
        else:
            return "breakdown"

    @classmethod
    def add_stress(cls, npc: NPC, amount: int, reason: str = "") -> int:
        """Adds stress modulated by personality neuroticism and patience."""
        if amount <= 0:
            return npc.stress

        neuro_mod = 0.6 + (npc.personality.neuroticism / 100.0) * 0.8
        patience_mitigation = (npc.personality.patience / 100.0) * 0.3
        effective = max(1, int(amount * (neuro_mod - patience_mitigation)))

        old_stress = npc.stress
        npc.stress = min(100, npc.stress + effective)

        if npc.stress != old_stress:
            npc.state_version += 1
        return npc.stress

    @classmethod
    def recover_stress(cls, npc: NPC, amount: int, reason: str = "") -> int:
        """Recovers stress through rest, safety, or successful coping."""
        if amount <= 0:
            return npc.stress

        old_stress = npc.stress
        npc.stress = max(0, npc.stress - amount)

        if npc.stress != old_stress:
            npc.state_version += 1
        return npc.stress

    @classmethod
    def evaluate_breakdown_behavior(cls, npc: NPC) -> str:
        """
        Derives specific breakdown behavior when stress >= 90 based on persona,
        values, and coping mechanisms instead of a generic panic fallback.
        """
        p = npc.personality
        coping = (npc.coping_mechanism or "").lower()

        # Coping match
        if "폭음" in coping or "alcohol" in coping:
            return "binge_drinking_abandon"
        if "기도" in coping or "prayer" in coping:
            return "religious_paralysis_prayer"
        if "도주" in coping or "flight" in coping:
            return "blind_panic_flight"

        # Personality weighting
        if p.aggression >= 70:
            return "homicidal_rage"
        elif p.courage <= 35:
            return "blind_panic_flight"
        elif p.suspicion >= 75:
            return "paranoid_preemptive_strike"
        elif p.altruism <= 30 and p.cunning >= 65:
            return "ruthless_betrayal_escape"
        elif p.neuroticism >= 70:
            return "catatonic_freeze"
        else:
            return "desperate_bargain_surrender"


# ==============================================================================
# 4. CONTEXTUAL CAUSAL TRAUMA ACTIVATION (Section 7.3)
# ==============================================================================

@dataclass
class TraumaSpec:
    """Specification of a trauma trigger condition and psychological fallout."""
    tag: str
    trigger_keywords: list[str]
    fear_increase: int
    stress_increase: int
    avoidance_action: str
    traits: list[str] = field(default_factory=list)


STANDARD_TRAUMA_REGISTRY: dict[str, TraumaSpec] = {
    "fire_disaster": TraumaSpec(
        tag="fire_disaster",
        trigger_keywords=["화염", "폭발", "불길", "연기", "화마", "fire", "flame"],
        fear_increase=40,
        stress_increase=25,
        avoidance_action="escape",
        traits=["화재_공포", "연기_알레르기"]
    ),
    "dungeon_burial": TraumaSpec(
        tag="dungeon_burial",
        trigger_keywords=["낙반", "붕괴", "매몰", "밀실", "암흑", "cave_in", "collapse"],
        fear_increase=45,
        stress_increase=30,
        avoidance_action="escape",
        traits=["폐소공포", "매몰_트라우마"]
    ),
    "betrayal_wound": TraumaSpec(
        tag="betrayal_wound",
        trigger_keywords=["배신", "밀고", "음모", "독살", "기습", "betrayal", "poison"],
        fear_increase=25,
        stress_increase=35,
        avoidance_action="hide",
        traits=["배신_PTSD", "극도의_불신"]
    ),
    "confinement": TraumaSpec(
        tag="confinement",
        trigger_keywords=["감옥", "투옥", "쇠사슬", "수갑", "포박", "jail", "chains"],
        fear_increase=35,
        stress_increase=30,
        avoidance_action="attack",
        traits=["구속_발작", "자유_갈망"]
    )
}


class TraumaEngine:
    """Manages contextual trauma matching, activation, and recovery."""

    @classmethod
    def evaluate_trauma_trigger(cls, npc: NPC, event_text: str) -> dict[str, Any] | None:
        """
        Evaluates whether an event triggers any of the NPC's active traumas.
        Chain: Trigger match -> Stress increase -> Emotion request -> Action bias.
        """
        active_traumas = list(npc.traumas)
        if npc.trauma:
            active_traumas.append(npc.trauma)

        if not active_traumas:
            return None

        event_lower = event_text.lower()
        for trauma_tag in active_traumas:
            spec = STANDARD_TRAUMA_REGISTRY.get(trauma_tag)
            matched_kw = None
            if spec:
                for kw in spec.trigger_keywords:
                    if kw.lower() in event_lower:
                        matched_kw = kw
                        break
            elif trauma_tag.lower() in event_lower:
                matched_kw = trauma_tag

            if matched_kw:
                # Trigger activated
                fear_add = spec.fear_increase if spec else 30
                stress_add = spec.stress_increase if spec else 25
                avoidance = spec.avoidance_action if spec else "escape"

                # Apply effects
                StressEngine.add_stress(npc, stress_add, f"trauma_trigger_{trauma_tag}")
                EmotionEngine.trigger_emotion(
                    npc, "fear", fear_add, f"trauma_{trauma_tag}", duration=4
                )
                EmotionEngine.trigger_emotion(
                    npc, "anxiety", int(fear_add * 0.7), f"trauma_{trauma_tag}", duration=3
                )

                # Record runtime state
                r_state = npc.trauma_runtime.setdefault(trauma_tag, {"intensity": 0, "trigger_count": 0})
                r_state["intensity"] = min(100, r_state.get("intensity", 0) + 30)
                r_state["trigger_count"] = r_state.get("trigger_count", 0) + 1
                npc.state_version += 1

                return {
                    "trauma_tag": trauma_tag,
                    "matched_keyword": matched_kw,
                    "stress_added": stress_add,
                    "fear_added": fear_add,
                    "avoidance_action": avoidance
                }
        return None

    @classmethod
    def recover_trauma(cls, npc: NPC, trauma_tag: str, recovery_amount: int = 15) -> None:
        """Reduces runtime trauma activation through safe exposure or counseling."""
        if trauma_tag in npc.trauma_runtime:
            current = npc.trauma_runtime[trauma_tag].get("intensity", 0)
            new_intensity = max(0, current - recovery_amount)
            npc.trauma_runtime[trauma_tag]["intensity"] = new_intensity
            npc.state_version += 1


# ==============================================================================
# 5. MULTI-ENTITY 9-AXIS RELATIONSHIP SYSTEM (Section 7.4)
# ==============================================================================

CANONICAL_RELATIONSHIP_AXES = [
    "trust", "affection", "respect", "fear", "resentment",
    "dependence", "loyalty", "suspicion", "familiarity"
]


class RelationshipEngine:
    """Manages multi-target 9-axis relationship maps and synchronizes legacy player fields."""

    @classmethod
    def get_or_create_relationship(cls, npc: NPC, target_id: str) -> dict[str, int]:
        """Fetches or initializes the 9-axis relationship dictionary for a target entity."""
        if target_id not in npc.relationship_map:
            # If target is player, initialize from existing legacy fields!
            if target_id in ("player", "플레이어"):
                rel = {
                    "trust": npc.trust,
                    "affection": npc.affinity,
                    "respect": npc.respect,
                    "fear": npc.fear,
                    "resentment": max(0, -npc.debt) if npc.debt < 0 else 0,
                    "dependence": 10,
                    "loyalty": npc.personality.loyalty,
                    "suspicion": npc.personality.suspicion,
                    "familiarity": min(100, npc.last_seen_turn * 5)
                }
            else:
                rel = {
                    "trust": 40, "affection": 40, "respect": 40, "fear": 0,
                    "resentment": 0, "dependence": 0, "loyalty": 30,
                    "suspicion": npc.personality.suspicion, "familiarity": 10
                }
            npc.relationship_map[target_id] = rel
        return npc.relationship_map[target_id]

    @classmethod
    def apply_relationship_delta(
        cls,
        npc: NPC,
        target_id: str,
        deltas: dict[str, int],
        reason: str = "",
        confidence: float = 1.0
    ) -> dict[str, Any]:
        """
        Applies causal deltas to relationship axes, clamping to 0-100.
        Synchronizes legacy player fields if target is player.
        Invalidates cache (bumps state_version) if delta >= 5.
        """
        rel = cls.get_or_create_relationship(npc, target_id)
        applied_deltas = {}
        max_abs_delta = 0

        for axis, delta in deltas.items():
            if axis in rel:
                eff_delta = int(delta * confidence)
                old_val = rel[axis]
                new_val = max(0, min(100, old_val + eff_delta))
                rel[axis] = new_val
                applied_deltas[axis] = new_val - old_val
                max_abs_delta = max(max_abs_delta, abs(applied_deltas[axis]))

        # Invalidation policy: delta >= 5 invalidates cache
        if max_abs_delta >= 5:
            npc.state_version += 1

        # Synchronize legacy player attitude fields (Section 4.4)
        if target_id in ("player", "플레이어"):
            npc.trust = rel["trust"]
            npc.affinity = rel["affection"]
            npc.respect = rel["respect"]
            npc.fear = rel["fear"]

        return {
            "target_id": target_id,
            "applied_deltas": applied_deltas,
            "current_relationship": dict(rel),
            "reason": reason
        }


# ==============================================================================
# 6. EVENT, ACTION CANDIDATE & DECISION RESULT TYPES (Section 5.3 & 10)
# ==============================================================================

@dataclass
class WorldEvent:
    """Normalized psychological stimulus / event payload."""
    id: str
    event_type: str                         # "combat", "noise", "theft", "betrayal", "dialogue", "routine_tick"
    severity: int = 1                       # 1 (minor) ~ 5 (critical)
    location_id: str = ""
    source_id: str = ""
    target_ids: list[str] = field(default_factory=list)
    description: str = ""
    turn: int = 0
    traits: list[str] = field(default_factory=lambda: ["world_event", "psychological_stimulus"])


@dataclass
class ActionCandidate:
    """Ephemeral action candidate evaluated during Tier 3 decision pipeline."""
    action_type: str                        # "escape", "attack", "cooperate", "bribe", "theft", "hide", "surveillance", "idle_observe"
    target_id: str = ""
    utility_score: float = 0.0
    risk_score: float = 0.0
    emotion_fit: float = 0.0
    value_fit: float = 0.0
    relationship_fit: float = 0.0
    total_score: float = 0.0
    is_feasible: bool = True
    feasibility_reason: str = ""
    traits: list[str] = field(default_factory=lambda: ["action_candidate"])


@dataclass
class DecisionResult:
    """Deterministic result of an NPC psychology evaluation turn."""
    npc_id: str
    turn: int
    tier: int                               # 1: Routine (O(1)), 2: Local Sensory (<5ms), 3: Full Pipeline (<200ms)
    selected_action: str
    target_id: str = ""
    concrete_plan: str = ""
    runner_up_actions: list[str] = field(default_factory=list)
    cache_hit: bool = False
    decision_trace: dict[str, Any] = field(default_factory=dict)
    traits: list[str] = field(default_factory=lambda: ["decision_result", "psychology_output"])

    def to_dict(self) -> dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "turn": self.turn,
            "tier": self.tier,
            "selected_action": self.selected_action,
            "target_id": self.target_id,
            "concrete_plan": self.concrete_plan,
            "runner_up_actions": list(self.runner_up_actions),
            "cache_hit": self.cache_hit,
            "decision_trace": dict(self.decision_trace),
            "traits": list(self.traits)
        }


# ==============================================================================
# 7. DECISION CACHE MANAGER (Section 10.2)
# ==============================================================================

class DecisionCacheManager:
    """Manages NPC-local decision caching with granular version invalidation."""

    @classmethod
    def make_cache_key(cls, npc: NPC, event: WorldEvent) -> str:
        import hashlib
        key_raw = f"{npc.id}_{event.event_type}_{event.location_id}_{npc.state_version}_{npc.stress // 10}"
        return hashlib.md5(key_raw.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_decision(cls, npc: NPC, key: str) -> DecisionResult | None:
        if npc.decision_cache_key == key and npc.decision_cache_result:
            res_dict = npc.decision_cache_result
            return DecisionResult(
                npc_id=res_dict.get("npc_id", npc.id),
                turn=res_dict.get("turn", 0),
                tier=res_dict.get("tier", 1),
                selected_action=res_dict.get("selected_action", "idle_observe"),
                target_id=res_dict.get("target_id", ""),
                concrete_plan=res_dict.get("concrete_plan", ""),
                runner_up_actions=res_dict.get("runner_up_actions", []),
                cache_hit=True,
                decision_trace=res_dict.get("decision_trace", {})
            )
        return None

    @classmethod
    def set_cached_decision(cls, npc: NPC, key: str, result: DecisionResult) -> None:
        npc.decision_cache_key = key
        npc.decision_cache_result = result.to_dict()


# ==============================================================================
# 8. MEMORY PSYCHOLOGY BRIDGE (Section 8)
# ==============================================================================

class MemoryPsychologyBridge:
    """Handles psychological salience ranking, deduplication, and decay policies."""

    @classmethod
    def rank_salient_memories(
        cls,
        npc: NPC,
        query_context: str = "",
        target_id: str = "",
        limit: int = 5
    ) -> list[Any]:
        """
        Ranks memories based on significance, emotional intensity, recency, and target relevance.
        Anchors (significance >= 4) receive a permanent baseline score boost.
        """
        if not npc.memories:
            return []

        scored = []
        for mem in npc.memories:
            score = 0.0
            # 1. Significance (1-5 scale)
            score += mem.significance * 20.0
            if mem.is_anchor or mem.significance >= 4:
                score += 50.0  # permanent anchor bonus

            # 2. Relationship relevance
            if target_id and (target_id in mem.participants or target_id in mem.relationship_deltas):
                score += 30.0

            # 3. Contextual relevance
            if query_context and any(word in mem.description for word in query_context.split() if len(word) > 1):
                score += 25.0

            # 4. Confidence scaling
            score *= getattr(mem, "confidence", 1.0)
            scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    @classmethod
    def record_memory_deduplicated(
        cls,
        npc: NPC,
        memory_entry: Any,
        turn_window: int = 5
    ) -> bool:
        """
        Deduplicates memory insertion. If a memory with similar tags and participants exists
        within turn_window, strengthens the existing memory rather than duplicating.
        """
        for existing in reversed(npc.memories):
            if abs(existing.turn - memory_entry.turn) <= turn_window:
                same_part = bool(set(existing.participants) & set(memory_entry.participants)) if existing.participants and memory_entry.participants else False
                same_tags = bool(set(existing.tags) & set(memory_entry.tags)) if existing.tags and memory_entry.tags else False
                if same_part or same_tags:
                    existing.significance = min(5, max(existing.significance, memory_entry.significance))
                    if memory_entry.is_anchor:
                        existing.is_anchor = True
                    return False

        npc.memories.append(memory_entry)
        npc.state_version += 1
        return True


# ==============================================================================
# 9. 12-STAGE DECISION PIPELINE & 3-TIER ROUTER (Section 9, 10, 12)
# ==============================================================================

class PsychologyDecisionPipeline:
    """
    Fixed 12-Stage Deterministic Decision Pipeline & 3-Tier Routing Architecture.
    Wraps NPCCognitiveDeductionEngine without duplication.
    """

    @classmethod
    def classify_tier(cls, npc: NPC, event: WorldEvent) -> int:
        """
        Classifies incoming event into Tier 1, 2, or 3 based on directness and severity.
        Tier 1: Far-off / routine tick -> O(1) decay
        Tier 2: Same location perceivable event (noise, combat, theft) -> < 5ms
        Tier 3: Direct interaction, combat against self, dialogue, trauma trigger -> full 12 stages
        """
        if npc.id in event.target_ids or event.source_id == npc.id:
            return 3
        if event.event_type in ("dialogue", "negotiation", "betrayal", "assassination"):
            return 3
        if event.severity >= 4:
            return 3

        if event.location_id and event.location_id == npc.location:
            return 2
        if event.event_type in ("noise", "theft", "fire", "combat"):
            return 2

        return 1

    @classmethod
    def route_and_process(
        cls,
        npc: NPC,
        event: WorldEvent,
        state: Any | None = None
    ) -> DecisionResult:
        """
        Master decision routing entry point.
        """
        tier = cls.classify_tier(npc, event)
        npc.eval_tier = tier
        npc.last_eval_tick = event.turn

        # ----------------------------------------------------------------------
        # TIER 1: Lightweight routine (O(1))
        # ----------------------------------------------------------------------
        if tier == 1:
            EmotionEngine.decay_emotions(npc)
            StressEngine.recover_stress(npc, 2, "passive_routine")
            return DecisionResult(
                npc_id=npc.id,
                turn=event.turn,
                tier=1,
                selected_action="idle_observe",
                concrete_plan="일상 일과를 유지하며 주변을 가볍게 관찰한다.",
                cache_hit=False,
                decision_trace={"reason": "tier_1_routine_tick"}
            )

        # ----------------------------------------------------------------------
        # TIER 2: Local Sensory (< 5ms)
        # ----------------------------------------------------------------------
        if tier == 2:
            EmotionEngine.decay_emotions(npc)
            if event.severity >= 2:
                StressEngine.add_stress(npc, event.severity * 3, f"local_event_{event.event_type}")
                EmotionEngine.trigger_emotion(npc, "anxiety", 15 * event.severity, "local_commotion", duration=2)

            return DecisionResult(
                npc_id=npc.id,
                turn=event.turn,
                tier=2,
                selected_action="surveillance",
                concrete_plan=f"{event.location_id} 부근의 소란({event.event_type})을 경계하며 상황을 주시한다.",
                cache_hit=False,
                decision_trace={"event_type": event.event_type, "severity": event.severity}
            )

        # ----------------------------------------------------------------------
        # TIER 3: Full 12-Stage Pipeline (< 200ms) with Decision Cache
        # ----------------------------------------------------------------------
        cache_key = DecisionCacheManager.make_cache_key(npc, event)
        cached = DecisionCacheManager.get_cached_decision(npc, cache_key)
        if cached:
            return cached

        res = cls._execute_12_stages(npc, event, state)
        final_cache_key = DecisionCacheManager.make_cache_key(npc, event)
        DecisionCacheManager.set_cached_decision(npc, final_cache_key, res)
        return res

    @classmethod
    def _execute_12_stages(
        cls,
        npc: NPC,
        event: WorldEvent,
        state: Any | None = None
    ) -> DecisionResult:
        trace: dict[str, Any] = {"stages": {}}

        # Stage 1: Situation Analysis
        target_id = event.source_id or ("player" if "player" in event.target_ids else "")
        trace["stages"]["1_situation"] = {"event": event.event_type, "target": target_id}

        # Stage 2: Perception Gate
        perceived_threat = event.severity * 15
        trace["stages"]["2_perception"] = {"threat_level": perceived_threat}

        # Stage 3: Emotional Appraisal & Trauma
        trauma_hit = TraumaEngine.evaluate_trauma_trigger(npc, event.description or event.event_type)
        if event.severity >= 3:
            EmotionEngine.trigger_emotion(npc, "fear" if npc.personality.courage < 50 else "anger", 25 * event.severity, event.event_type)
        dominant_emo, dom_int = EmotionEngine.get_dominant_emotion(npc)
        trace["stages"]["3_emotion"] = {"dominant": dominant_emo, "intensity": dom_int, "trauma": trauma_hit}

        # Stage 4: Need Evaluation
        needs_deficit = {
            "hunger": npc.needs.hunger,
            "wealth": npc.needs.wealth,
            "safety": npc.needs.safety
        }
        trace["stages"]["4_needs"] = needs_deficit

        # Stage 5: Goal Evaluation
        current_goal = npc.goal or npc.desire or "생존 및 이익 확보"
        trace["stages"]["5_goal"] = current_goal

        # Stage 6: Memory Retrieval (Tier 3 only)
        salient_memories = MemoryPsychologyBridge.rank_salient_memories(npc, target_id=target_id, limit=3)
        trace["stages"]["6_memories"] = [m.description for m in salient_memories]

        # Stage 7: Relationship Evaluation
        rel = RelationshipEngine.get_or_create_relationship(npc, target_id) if target_id else {}
        trace["stages"]["7_relationship"] = rel

        # Stage 8: Value Conflict
        top_value = npc.value_hierarchy[0] if npc.value_hierarchy else "survival"
        trace["stages"]["8_values"] = {"top_value": top_value}

        # Stage 9: Candidate Generation & Feasibility
        candidates = [
            ActionCandidate(action_type="escape", target_id=target_id),
            ActionCandidate(action_type="attack", target_id=target_id),
            ActionCandidate(action_type="cooperate", target_id=target_id),
            ActionCandidate(action_type="hide", target_id=target_id),
            ActionCandidate(action_type="bribe", target_id=target_id),
            ActionCandidate(action_type="theft", target_id=target_id),
            ActionCandidate(action_type="idle_observe", target_id=target_id),
        ]
        if npc.gold < 10:
            for c in candidates:
                if c.action_type == "bribe":
                    c.is_feasible = False
                    c.feasibility_reason = "금화 부족"

        # Stage 10: Action Scoring
        emo_mods = EmotionEngine.get_action_modifiers(npc)
        p = npc.personality
        stress_stage = StressEngine.get_stress_stage(npc.stress)

        for c in candidates:
            if not c.is_feasible:
                c.total_score = -999.0
                continue

            score = 50.0

            if c.action_type == "attack":
                score += (p.aggression - 50) * 0.5 + (p.courage - 50) * 0.4
            elif c.action_type == "escape":
                score += (50 - p.courage) * 0.6 + (p.neuroticism - 50) * 0.4
            elif c.action_type == "cooperate":
                score += (p.altruism - 50) * 0.5 + (p.loyalty - 50) * 0.4
            elif c.action_type == "bribe":
                score += (p.cunning - 50) * 0.5 + (50 - p.pride) * 0.3
            elif c.action_type == "theft":
                score += (p.greed - 50) * 0.6 + (p.cunning - 50) * 0.4 - (p.altruism - 50) * 0.4
            elif c.action_type == "hide":
                score += (p.suspicion - 50) * 0.5 + (50 - p.courage) * 0.4

            score += emo_mods.get(c.action_type, 0.0)

            if rel:
                if c.action_type == "cooperate":
                    score += (rel.get("trust", 50) - 50) * 0.4 + (rel.get("affection", 50) - 50) * 0.3
                elif c.action_type == "attack":
                    score += (rel.get("resentment", 0)) * 0.5 + (rel.get("fear", 0) > 60 and -20.0 or 0.0)
                elif c.action_type == "escape":
                    score += (rel.get("fear", 0)) * 0.5

            if trauma_hit and c.action_type == trauma_hit.get("avoidance_action"):
                score += 40.0

            if stress_stage == "breakdown":
                breakdown_act = StressEngine.evaluate_breakdown_behavior(npc)
                if "rage" in breakdown_act and c.action_type == "attack" or "flight" in breakdown_act and c.action_type == "escape" or "freeze" in breakdown_act and c.action_type == "idle_observe":
                    score += 80.0

            c.total_score = score

        # Stage 11: Deterministic Decision Selection
        feasible_candidates = [c for c in candidates if c.is_feasible]
        feasible_candidates.sort(key=lambda x: x.total_score, reverse=True)

        selected = feasible_candidates[0]
        runner_ups = [c.action_type for c in feasible_candidates[1:3]]

        plan_desc = f"{target_id or '주변'}에 대해 {selected.action_type} 행동을 취한다."
        if selected.action_type == "escape":
            plan_desc = "위협을 피해 즉시 안전한 장소로 도주한다."
        elif selected.action_type == "attack":
            plan_desc = f"적대적 대상({target_id})을 향해 선제 공격을 결행한다."
        elif selected.action_type == "cooperate":
            plan_desc = f"{target_id}와 우호적 대화 및 협력 방안을 모색한다."
        elif selected.action_type == "hide":
            plan_desc = "시야를 가리고 은밀히 몸을 숨긴다."

        trace["stages"]["11_selection"] = {
            "selected": selected.action_type,
            "score": round(selected.total_score, 2),
            "runner_ups": runner_ups
        }

        # Stage 12: State Update & Synchronization
        npc.intention = plan_desc
        npc.goal = current_goal

        return DecisionResult(
            npc_id=npc.id,
            turn=event.turn,
            tier=3,
            selected_action=selected.action_type,
            target_id=target_id,
            concrete_plan=plan_desc,
            runner_up_actions=runner_ups,
            cache_hit=False,
            decision_trace=trace
        )

