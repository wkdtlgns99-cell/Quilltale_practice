"""Deterministic psychological state and decision layer for Quilltale NPCs.

This module EXTENDS the existing NPC and NPCCognitiveDeductionEngine.  It does
not replace either system and deliberately keeps LLM/RAG outside authoritative
state ownership.

Design contract implemented here:
- Python owns psychological truth and final decisions.
- MemoryRecord is authoritative episodic memory; RAG is retrieval infrastructure.
- Personality, emotion, stress, trauma, relationship, need and goal are distinct.
- NPC perception is gated from WorldState truth.
- Decisions are reproducible for identical state/context.
- Tier routing avoids full simulation for every NPC every tick.
- Decision cache is result reuse only and is version checked.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from hashlib import sha256
import json
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SCHEMA_VERSION = 1


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _clamp01(value: float) -> float:
    return _clamp(value, 0.0, 1.0)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _dc_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return {f.name: _dc_dict(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, dict):
        return {str(k): _dc_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_dc_dict(v) for v in obj]
    return obj


@dataclass
class Identity:
    identity_id: str = ""
    name: str = ""
    age: int = 0
    faction_id: str = ""
    role: str = ""
    occupation: str = ""
    background_summary: str = ""
    origin_id: str = ""
    social_class: str = ""
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION


@dataclass
class PersonalityProfile:
    """Stable tendencies. Values do not represent current emotion."""
    openness: float = 50
    conscientiousness: float = 50
    extraversion: float = 50
    agreeableness: float = 50
    neuroticism: float = 50
    honesty_humility: float = 50
    aggression: float = 50
    impulsivity: float = 50
    empathy: float = 50
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("openness", "conscientiousness", "extraversion", "agreeableness",
                     "neuroticism", "honesty_humility", "aggression", "impulsivity", "empathy"):
            setattr(self, name, _clamp(getattr(self, name)))


@dataclass
class TemperamentProfile:
    baseline_reactivity: float = 50
    emotional_volatility: float = 50
    stress_sensitivity: float = 50
    recovery_speed: float = 50
    impulse_control: float = 50
    threat_reactivity: float = 50
    social_reactivity: float = 50
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for f in fields(self):
            if f.name not in ("traits", "schema_version"):
                setattr(self, f.name, _clamp(getattr(self, f.name)))


@dataclass
class ValueProfile:
    values: Dict[str, float] = field(default_factory=dict)
    priority_order: List[str] = field(default_factory=lambda: ["survival", "family", "loyalty", "honor"])
    value_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        self.values = {k: _clamp(v) for k, v in self.values.items()}


@dataclass
class MotivationEntry:
    type: str
    intensity: float = 50
    priority: float = 0.5
    traits: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.intensity = _clamp(self.intensity)
        self.priority = _clamp01(self.priority)


@dataclass
class MotivationProfile:
    entries: List[MotivationEntry] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION


@dataclass
class NeedState:
    """Need deficit: 0 satisfied, 100 severe deficit."""
    need_values: Dict[str, float] = field(default_factory=dict)
    urgency: Dict[str, float] = field(default_factory=dict)
    last_update_tick: int = 0
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        self.need_values = {k: _clamp(v) for k, v in self.need_values.items()}
        self.urgency = {k: _clamp(v) for k, v in self.urgency.items()}


@dataclass
class PreferenceProfile:
    likes: List[str] = field(default_factory=list)
    dislikes: List[str] = field(default_factory=list)
    preferred_foods: List[str] = field(default_factory=list)
    preferred_environment: List[str] = field(default_factory=list)
    social_preferences: List[str] = field(default_factory=list)
    lifestyle_tags: List[str] = field(default_factory=list)
    risk_preferences: Dict[str, float] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION


@dataclass
class EmotionInstance:
    type: str
    intensity: float = 0
    source: str = ""
    duration_ticks: int = 0
    remaining_ticks: int = 0
    decay_rate: float = 1.0
    trigger: str = ""
    modifiers: Dict[str, float] = field(default_factory=dict)
    created_tick: int = 0

    def __post_init__(self) -> None:
        self.intensity = _clamp(self.intensity)
        self.remaining_ticks = max(0, int(self.remaining_ticks or self.duration_ticks))
        self.duration_ticks = max(0, int(self.duration_ticks))
        self.decay_rate = max(0.0, float(self.decay_rate))


@dataclass
class EmotionState:
    active_emotions: List[EmotionInstance] = field(default_factory=list)
    dominant_emotion: str = "neutral"
    emotional_baseline: Dict[str, float] = field(default_factory=dict)
    last_update_tick: int = 0
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def activate(self, request: Mapping[str, Any], tick: int) -> None:
        emotion = EmotionInstance(
            type=str(request.get("type", "neutral")),
            intensity=float(request.get("activation", 0)),
            source=str(request.get("source", "appraisal")),
            duration_ticks=int(request.get("duration_ticks", 1)),
            remaining_ticks=int(request.get("duration_ticks", 1)),
            decay_rate=float(request.get("decay_rate", 1.0)),
            trigger=str(request.get("trigger", "")),
            modifiers=dict(request.get("modifiers", {})),
            created_tick=tick,
        )
        if emotion.intensity <= 0:
            return
        self.active_emotions.append(emotion)
        self.last_update_tick = tick
        self._recalculate_dominant()

    def decay(self, tick: int) -> None:
        alive: List[EmotionInstance] = []
        for e in self.active_emotions:
            e.remaining_ticks = max(0, e.remaining_ticks - 1)
            e.intensity = _clamp(e.intensity - e.decay_rate)
            if e.remaining_ticks > 0 and e.intensity > 0:
                alive.append(e)
        self.active_emotions = alive
        self.last_update_tick = tick
        self._recalculate_dominant()

    def _recalculate_dominant(self) -> None:
        if not self.active_emotions:
            self.dominant_emotion = "neutral"
            return
        self.dominant_emotion = max(self.active_emotions, key=lambda x: (x.intensity, x.created_tick)).type


@dataclass
class StressState:
    stress: float = 0
    fatigue: float = 0
    pressure: float = 0
    stress_threshold: float = 60
    breakdown_threshold: float = 95
    recovery_rate: float = 2
    accumulation_rate: float = 1
    personality_sensitivity: float = 1
    trauma_amplification: float = 0
    coping_capacity: float = 50
    last_update_tick: int = 0
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("stress", "fatigue", "pressure", "stress_threshold", "breakdown_threshold",
                     "recovery_rate", "accumulation_rate", "personality_sensitivity",
                     "trauma_amplification", "coping_capacity"):
            setattr(self, name, _clamp(getattr(self, name)))


@dataclass
class TraumaEntry:
    trauma_id: str
    name: str = ""
    trigger_conditions: List[str] = field(default_factory=list)
    severity: float = 50
    frequency: float = 0
    emotional_association: List[str] = field(default_factory=list)
    avoidance: float = 50
    coping_style: str = "avoidance"
    stress_amplification: float = 20
    recovery_rate: float = 1
    long_term_influence: float = 50
    behavioral_tendencies: List[str] = field(default_factory=list)
    last_triggered_tick: int = 0
    traits: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for name in ("severity", "frequency", "avoidance", "stress_amplification", "recovery_rate", "long_term_influence"):
            setattr(self, name, _clamp(getattr(self, name)))


@dataclass
class TraumaProfile:
    entries: List[TraumaEntry] = field(default_factory=list)
    active_triggers: List[Dict[str, Any]] = field(default_factory=list)
    global_resilience: float = 50
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def match(self, event: Mapping[str, Any], tick: int) -> List[Dict[str, Any]]:
        text = " ".join(str(event.get(k, "")) for k in ("event", "description", "tags", "source" )).lower()
        matches: List[Dict[str, Any]] = []
        for entry in self.entries:
            patterns = [str(x).lower() for x in entry.trigger_conditions]
            if not patterns:
                continue
            hit_count = sum(1 for p in patterns if p and p in text)
            confidence = _clamp01(hit_count / max(1, len(patterns)))
            if confidence <= 0:
                continue
            intensity = _clamp(confidence * entry.severity)
            matches.append({
                "trauma_id": entry.trauma_id,
                "match_confidence": confidence,
                "activation_intensity": intensity,
                "stress_amplification": entry.stress_amplification * confidence,
                "coping_style": entry.coping_style,
                "behavioral_tendencies": list(entry.behavioral_tendencies),
            })
            entry.last_triggered_tick = tick
        self.active_triggers = matches
        return matches


RELATIONSHIP_AXES = ("trust", "affection", "respect", "fear", "resentment", "dependence", "loyalty", "suspicion", "familiarity")


@dataclass
class RelationshipAxis:
    trust: float = 50
    affection: float = 50
    respect: float = 50
    fear: float = 0
    resentment: float = 0
    dependence: float = 0
    loyalty: float = 50
    suspicion: float = 0
    familiarity: float = 0
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in RELATIONSHIP_AXES:
            setattr(self, name, _clamp(getattr(self, name)))

    def apply(self, delta: Mapping[str, float]) -> Dict[str, float]:
        applied: Dict[str, float] = {}
        for axis, amount in delta.items():
            if axis not in RELATIONSHIP_AXES:
                continue
            old = getattr(self, axis)
            new = _clamp(old + float(amount))
            setattr(self, axis, new)
            applied[axis] = new - old
        return applied


@dataclass
class RelationshipDelta:
    source_entity_id: str
    target_entity_id: str
    event_id: str
    axis_changes: Dict[str, float] = field(default_factory=dict)
    reason: str = ""
    timestamp: int = 0
    confidence: float = 1.0
    traits: List[str] = field(default_factory=list)


@dataclass
class RelationshipMap:
    relationships: Dict[str, RelationshipAxis] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def get(self, entity_id: str) -> RelationshipAxis:
        if entity_id not in self.relationships:
            self.relationships[entity_id] = RelationshipAxis()
        return self.relationships[entity_id]

    def apply_delta(self, delta: RelationshipDelta) -> Dict[str, float]:
        return self.get(delta.target_entity_id).apply(delta.axis_changes)


@dataclass
class MemoryRecord:
    memory_id: str
    event_summary: str = ""
    participants: List[str] = field(default_factory=list)
    location_id: str = ""
    timestamp: int = 0
    emotional_impact: float = 0
    importance: int = 1
    tags: List[str] = field(default_factory=list)
    consequences_observed: List[str] = field(default_factory=list)
    relationship_deltas: Dict[str, Dict[str, float]] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = "direct"
    decay_rate: float = 0.1
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        self.emotional_impact = _clamp(self.emotional_impact, -100, 100)
        self.importance = max(1, min(5, int(self.importance)))
        self.confidence = _clamp01(self.confidence)
        if self.source not in ("direct", "hearsay", "inferred"):
            self.source = "inferred"


@dataclass
class GoalState:
    goal_id: str
    description: str = ""
    goal_type: str = "short"
    priority: float = 0.5
    urgency: float = 0
    progress: float = 0
    deadline_tick: Optional[int] = None
    source_motivation: str = ""
    related_needs: List[str] = field(default_factory=list)
    conflicting_goals: List[str] = field(default_factory=list)
    status: str = "active"
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        self.priority = _clamp01(self.priority)
        self.urgency = _clamp(self.urgency)
        self.progress = _clamp(self.progress)


@dataclass
class SituationContext:
    tick: int = 0
    location_id: str = ""
    nearby_entities: List[str] = field(default_factory=list)
    visible_events: List[Dict[str, Any]] = field(default_factory=list)
    audible_events: List[Dict[str, Any]] = field(default_factory=list)
    known_facts: List[str] = field(default_factory=list)
    perceived_threats: List[Dict[str, Any]] = field(default_factory=list)
    available_actions: List[str] = field(default_factory=list)
    environment_tags: List[str] = field(default_factory=list)


@dataclass
class PerceivedEvent:
    event_id: str
    source: str = ""
    perceived_intensity: float = 0
    certainty: float = 0
    sensory_channel: str = ""
    distance: float = 0
    novelty: float = 0
    threat_signal: float = 0
    goal_relevance: float = 0
    relationship_relevance: float = 0
    traits: List[str] = field(default_factory=list)


@dataclass
class AppraisalResult:
    event_id: str
    threat_score: float = 0
    opportunity_score: float = 0
    goal_obstruction: float = 0
    goal_facilitation: float = 0
    control_score: float = 50
    responsibility_score: float = 0
    blame_score: float = 0
    fairness_score: float = 50
    value_compatibility: float = 50
    relationship_relevance: float = 0
    trauma_match: float = 0
    confidence: float = 1.0
    inferred_other_beliefs: Dict[str, float] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)


@dataclass
class BehavioralProfile:
    risk_tendency: float = 50
    social_tendency: float = 50
    aggression_tendency: float = 50
    cooperation_tendency: float = 50
    avoidance_tendency: float = 50
    authority_compliance: float = 50
    deception_tendency: float = 50
    derived_patterns: List[str] = field(default_factory=list)
    cache_version: int = 0
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION


@dataclass
class NPCPsychologicalState:
    identity: Identity = field(default_factory=Identity)
    personality: PersonalityProfile = field(default_factory=PersonalityProfile)
    temperament: TemperamentProfile = field(default_factory=TemperamentProfile)
    values: ValueProfile = field(default_factory=ValueProfile)
    motivation: MotivationProfile = field(default_factory=MotivationProfile)
    needs: NeedState = field(default_factory=NeedState)
    preferences: PreferenceProfile = field(default_factory=PreferenceProfile)
    emotion: EmotionState = field(default_factory=EmotionState)
    stress: StressState = field(default_factory=StressState)
    trauma: TraumaProfile = field(default_factory=TraumaProfile)
    memories: List[MemoryRecord] = field(default_factory=list)
    goals: List[GoalState] = field(default_factory=list)
    relationships: RelationshipMap = field(default_factory=RelationshipMap)
    behavioral: BehavioralProfile = field(default_factory=BehavioralProfile)
    state_version: int = 0
    memory_version: int = 0
    relationship_version: int = 0
    goal_version: int = 0
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return _dc_dict(self)

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "NPCPsychologicalState":
        """Backward-compatible loader: missing fields default, unknown fields ignored."""
        raw = raw if isinstance(raw, Mapping) else {}

        def make(dc_cls: Any, data: Any) -> Any:
            if not isinstance(data, Mapping):
                return dc_cls()
            valid = {f.name for f in fields(dc_cls)}
            return dc_cls(**{k: v for k, v in data.items() if k in valid})

        out = cls()
        for name, dc_cls in (
            ("identity", Identity), ("personality", PersonalityProfile),
            ("temperament", TemperamentProfile), ("values", ValueProfile),
            ("motivation", MotivationProfile), ("needs", NeedState),
            ("preferences", PreferenceProfile), ("emotion", EmotionState),
            ("stress", StressState), ("trauma", TraumaProfile),
            ("relationships", RelationshipMap), ("behavioral", BehavioralProfile),
        ):
            data = raw.get(name)
            if name == "motivation" and isinstance(data, Mapping):
                entries = [make(MotivationEntry, x) for x in data.get("entries", []) if isinstance(x, Mapping)]
                obj = make(dc_cls, data)
                obj.entries = entries
            elif name == "emotion" and isinstance(data, Mapping):
                obj = make(dc_cls, data)
                obj.active_emotions = [make(EmotionInstance, x) for x in data.get("active_emotions", []) if isinstance(x, Mapping)]
            elif name == "trauma" and isinstance(data, Mapping):
                obj = make(dc_cls, data)
                obj.entries = [make(TraumaEntry, x) for x in data.get("entries", []) if isinstance(x, Mapping)]
            elif name == "relationships" and isinstance(data, Mapping):
                obj = make(dc_cls, data)
                obj.relationships = {str(k): make(RelationshipAxis, v) for k, v in data.get("relationships", {}).items() if isinstance(v, Mapping)}
            else:
                obj = make(dc_cls, data)
            setattr(out, name, obj)

        out.memories = [make(MemoryRecord, x) for x in raw.get("memories", []) if isinstance(x, Mapping)]
        out.goals = [make(GoalState, x) for x in raw.get("goals", []) if isinstance(x, Mapping)]
        for name in ("state_version", "memory_version", "relationship_version", "goal_version", "schema_version"):
            if name in raw:
                setattr(out, name, int(raw[name]))
        return out


@dataclass
class PersonalityTemplate:
    template_id: str
    name: str
    description: str = ""
    big_five_mean: Dict[str, float] = field(default_factory=dict)
    big_five_std: Dict[str, float] = field(default_factory=dict)
    honesty_humility_mean: float = 50
    honesty_humility_std: float = 10
    risk_preference_distribution: Dict[str, float] = field(default_factory=dict)
    social_tendency_baseline: float = 50
    value_priority: List[str] = field(default_factory=list)
    dominant_motivation: str = ""
    secondary_motivations: List[str] = field(default_factory=list)
    temperament_baseline: Dict[str, float] = field(default_factory=dict)
    trauma_susceptibility_tags: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION


class PersonalityTemplateLibrary:
    """Eight required archetypes. No archetype produces identical NPCs by itself."""

    TEMPLATES: Dict[str, PersonalityTemplate] = {
        "cautious_scholar": PersonalityTemplate(
            "cautious_scholar", "Cautious Scholar", "Knowledge-first, risk-sensitive investigator.",
            {"openness": 82, "conscientiousness": 78, "extraversion": 35, "agreeableness": 55, "neuroticism": 55},
            {"openness": 8, "conscientiousness": 9, "extraversion": 12, "agreeableness": 14, "neuroticism": 12},
            72, 9, {"low": 70, "medium": 25, "high": 5}, 38,
            ["knowledge", "safety", "truth"], "knowledge", ["recognition", "safety"],
            {"baseline_reactivity": 45, "stress_sensitivity": 55, "impulse_control": 78}, ["knowledge_loss", "public_failure"],
            ["scholar"]),
        "reckless_adventurer": PersonalityTemplate(
            "reckless_adventurer", "Reckless Adventurer", "Novelty-seeking and action-oriented risk taker.",
            {"openness": 75, "conscientiousness": 35, "extraversion": 78, "agreeableness": 50, "neuroticism": 30},
            {"openness": 12, "conscientiousness": 16, "extraversion": 12, "agreeableness": 15, "neuroticism": 13},
            48, 12, {"low": 10, "medium": 30, "high": 60}, 75,
            ["freedom", "adventure", "recognition"], "adventure", ["wealth", "curiosity"],
            {"baseline_reactivity": 65, "stress_sensitivity": 35, "impulse_control": 30}, ["confinement", "helplessness"], ["risk_taker"]),
        "devoted_knight": PersonalityTemplate(
            "devoted_knight", "Devoted Knight", "Duty and loyalty override personal comfort.",
            {"openness": 45, "conscientiousness": 88, "extraversion": 52, "agreeableness": 68, "neuroticism": 28},
            {"openness": 12, "conscientiousness": 7, "extraversion": 12, "agreeableness": 10, "neuroticism": 10},
            70, 10, {"low": 45, "medium": 45, "high": 10}, 55,
            ["loyalty", "honor", "duty", "survival"], "loyalty", ["honor", "protection"],
            {"baseline_reactivity": 45, "stress_sensitivity": 30, "impulse_control": 85}, ["betrayal", "failure_to_protect"], ["duty_bound"]),
        "cynical_mercenary": PersonalityTemplate(
            "cynical_mercenary", "Cynical Mercenary", "Pragmatic, guarded, transaction-oriented survivor.",
            {"openness": 38, "conscientiousness": 62, "extraversion": 45, "agreeableness": 28, "neuroticism": 48},
            {"openness": 14, "conscientiousness": 12, "extraversion": 15, "agreeableness": 12, "neuroticism": 14},
            38, 11, {"low": 35, "medium": 50, "high": 15}, 43,
            ["wealth", "survival", "autonomy"], "wealth", ["security", "respect"],
            {"baseline_reactivity": 48, "stress_sensitivity": 50, "impulse_control": 62}, ["poverty", "betrayal"], ["pragmatic"]),
        "ambitious_noble": PersonalityTemplate(
            "ambitious_noble", "Ambitious Noble", "Status-conscious planner seeking influence.",
            {"openness": 62, "conscientiousness": 72, "extraversion": 70, "agreeableness": 42, "neuroticism": 38},
            {"openness": 11, "conscientiousness": 10, "extraversion": 12, "agreeableness": 14, "neuroticism": 12},
            66, 10, {"low": 15, "medium": 55, "high": 30}, 70,
            ["power", "status", "legacy"], "ambition", ["wealth", "recognition"],
            {"baseline_reactivity": 50, "stress_sensitivity": 42, "impulse_control": 70}, ["humiliation", "status_loss"], ["status_seeking"]),
        "gentle_healer": PersonalityTemplate(
            "gentle_healer", "Gentle Healer", "Compassionate, harm-averse caretaker.",
            {"openness": 60, "conscientiousness": 70, "extraversion": 45, "agreeableness": 90, "neuroticism": 40},
            {"openness": 12, "conscientiousness": 10, "extraversion": 15, "agreeableness": 6, "neuroticism": 13},
            82, 8, {"low": 70, "medium": 28, "high": 2}, 48,
            ["benevolence", "care", "safety"], "care", ["loyalty", "knowledge"],
            {"baseline_reactivity": 52, "stress_sensitivity": 58, "impulse_control": 74}, ["patient_death", "helplessness"], ["caretaker"]),
        "paranoid_survivor": PersonalityTemplate(
            "paranoid_survivor", "Paranoid Survivor", "Hypervigilant, threat-sensitive survivor.",
            {"openness": 42, "conscientiousness": 55, "extraversion": 22, "agreeableness": 25, "neuroticism": 88},
            {"openness": 15, "conscientiousness": 13, "extraversion": 12, "agreeableness": 14, "neuroticism": 7},
            35, 9, {"low": 65, "medium": 30, "high": 5}, 25,
            ["survival", "safety", "control"], "survival", ["security", "trust"],
            {"baseline_reactivity": 82, "stress_sensitivity": 88, "impulse_control": 55}, ["betrayal", "ambush", "confinement"], ["hypervigilant"]),
        "zealous_inquisitor": PersonalityTemplate(
            "zealous_inquisitor", "Zealous Inquisitor", "Order-driven moral absolutist with strong authority orientation.",
            {"openness": 30, "conscientiousness": 86, "extraversion": 58, "agreeableness": 30, "neuroticism": 45},
            {"openness": 12, "conscientiousness": 8, "extraversion": 13, "agreeableness": 13, "neuroticism": 12},
            58, 10, {"low": 40, "medium": 45, "high": 15}, 60,
            ["order", "faith", "purity", "duty"], "order", ["justice", "recognition"],
            {"baseline_reactivity": 58, "stress_sensitivity": 48, "impulse_control": 80}, ["heresy", "moral_failure"], ["absolutist"]),
    }

    @classmethod
    def get(cls, template_id: str) -> PersonalityTemplate:
        return cls.TEMPLATES[template_id]

    @classmethod
    def ids(cls) -> List[str]:
        return list(cls.TEMPLATES)

    @classmethod
    def build_profile(cls, template_id: str, variation: Optional[Mapping[str, float]] = None) -> PersonalityProfile:
        t = cls.get(template_id)
        variation = variation or {}
        vals = {k: _clamp(v + float(variation.get(k, 0))) for k, v in t.big_five_mean.items()}
        vals["honesty_humility"] = _clamp(t.honesty_humility_mean + float(variation.get("honesty_humility", 0)))
        vals["aggression"] = _clamp(variation.get("aggression", 50))
        vals["impulsivity"] = _clamp(variation.get("impulsivity", 50))
        vals["empathy"] = _clamp(variation.get("empathy", 50))
        return PersonalityProfile(**vals)


class MemoryRepository:
    """Authoritative in-Python memory collection. No vector database is the source of truth."""

    def __init__(self, state: NPCPsychologicalState):
        self.state = state

    def add(self, memory: MemoryRecord) -> MemoryRecord:
        # Semantic duplicate protection without requiring an embedding service.
        normalized = " ".join(memory.event_summary.lower().split())
        for existing in self.state.memories:
            if existing.participants == memory.participants and " ".join(existing.event_summary.lower().split()) == normalized:
                existing.importance = max(existing.importance, memory.importance)
                existing.emotional_impact = max(existing.emotional_impact, memory.emotional_impact, key=abs)
                existing.confidence = max(existing.confidence, memory.confidence)
                self.state.memory_version += 1
                self.state.state_version += 1
                return existing
        self.state.memories.append(memory)
        self.state.memory_version += 1
        self.state.state_version += 1
        return memory

    def decay(self, tick: int) -> None:
        # Decay salience, not existence. Anchored memories do not normally decay.
        for m in self.state.memories:
            if m.importance >= 4:
                continue
            age = max(0, tick - m.timestamp)
            if age and m.decay_rate > 0:
                m.emotional_impact = _clamp(m.emotional_impact - age * m.decay_rate, -100, 100)
        self.state.memory_version += 1

    def rank(self, candidates: Iterable[MemoryRecord], *, tick: int, goal_relevance: Optional[Callable[[MemoryRecord], float]] = None,
             relationship_relevance: Optional[Callable[[MemoryRecord], float]] = None,
             trauma_relevance: Optional[Callable[[MemoryRecord], float]] = None) -> List[MemoryRecord]:
        goal_relevance = goal_relevance or (lambda _: 0.0)
        relationship_relevance = relationship_relevance or (lambda _: 0.0)
        trauma_relevance = trauma_relevance or (lambda _: 0.0)

        def score(m: MemoryRecord) -> Tuple[float, ...]:
            recency = 1.0 / (1.0 + max(0, tick - m.timestamp))
            return (
                m.importance,
                abs(m.emotional_impact),
                recency,
                goal_relevance(m),
                relationship_relevance(m),
                trauma_relevance(m),
                m.confidence,
            )
        return sorted(list(candidates), key=score, reverse=True)


class RAGMemoryAdapter:
    """Adapter for the existing MemoryManager/Qdrant layer.

    Retrieval returns candidate MemoryRecords; it never creates authoritative
    memories. A missing adapter simply returns no candidates.
    """

    def __init__(self, retrieve_fn: Optional[Callable[[str, int], Sequence[Any]]] = None):
        self.retrieve_fn = retrieve_fn

    def retrieve(self, query: str, limit: int = 8) -> List[Any]:
        if not self.retrieve_fn or not query.strip():
            return []
        try:
            return list(self.retrieve_fn(query, limit))
        except Exception:
            return []


class PerceptionEngine:
    @staticmethod
    def perceive(npc: Any, situation: SituationContext, event: Optional[Mapping[str, Any]] = None) -> List[PerceivedEvent]:
        p = getattr(getattr(npc, "psychology", None), "personality", PersonalityProfile())
        stress = getattr(getattr(npc, "psychology", None), "stress", StressState())
        events = list(situation.visible_events) + list(situation.audible_events)
        if event:
            events.append(dict(event))
        out: List[PerceivedEvent] = []
        for i, raw in enumerate(events):
            severity = _clamp(float(raw.get("severity", raw.get("intensity", 50))))
            distance = max(0.0, float(raw.get("distance", 0)))
            attenuation = min(80.0, distance * 2.0)
            sensitivity = 1.0 + ((p.neuroticism - 50) / 500.0 if raw.get("threat", False) else 0)
            intensity = _clamp((severity - attenuation) * sensitivity)
            threshold = _clamp(25 - (p.openness - 50) * 0.05 - (stress.stress - 50) * 0.08, 5, 45)
            if intensity < threshold:
                continue
            certainty = _clamp01(float(raw.get("certainty", 0.8)))
            out.append(PerceivedEvent(
                event_id=str(raw.get("event_id", f"perceived_{situation.tick}_{i}")),
                source=str(raw.get("source", "unknown")),
                perceived_intensity=intensity,
                certainty=certainty,
                sensory_channel=str(raw.get("sensory_channel", "visual")),
                distance=distance,
                novelty=_clamp(float(raw.get("novelty", 50))),
                threat_signal=_clamp(float(raw.get("threat", raw.get("threat_signal", 0)))),
                goal_relevance=_clamp(float(raw.get("goal_relevance", 0))),
                relationship_relevance=_clamp(float(raw.get("relationship_relevance", 0))),
                traits=list(raw.get("tags", [])) if isinstance(raw.get("tags", []), list) else [],
            ))
        return out


class AppraisalEngine:
    @staticmethod
    def evaluate(npc: Any, perceived: PerceivedEvent, situation: SituationContext) -> AppraisalResult:
        psych: NPCPsychologicalState = getattr(npc, "psychology", NPCPsychologicalState())
        p = psych.personality
        values = psych.values
        trauma_matches = psych.trauma.match({"event": " ".join(perceived.traits), "tags": perceived.traits, "source": perceived.source}, situation.tick)
        trauma_match = max((m["match_confidence"] for m in trauma_matches), default=0.0) * 100
        value_alignment = 50.0
        if values.priority_order and perceived.goal_relevance > 0:
            value_alignment += (values.values.get(values.priority_order[0], 50) - 50) * 0.25
        control = _clamp(70 - perceived.threat_signal * 0.45 + (p.conscientiousness - 50) * 0.15)
        threat = _clamp(perceived.threat_signal * (1 + p.neuroticism / 300))
        opportunity = _clamp(perceived.novelty * (p.openness / 100))
        return AppraisalResult(
            event_id=perceived.event_id,
            threat_score=threat,
            opportunity_score=opportunity,
            goal_obstruction=_clamp(perceived.goal_relevance if perceived.threat_signal > 40 else perceived.goal_relevance * 0.4),
            goal_facilitation=_clamp(perceived.goal_relevance if perceived.threat_signal < 30 else 0),
            control_score=control,
            responsibility_score=_clamp(p.conscientiousness),
            blame_score=_clamp((100 - p.agreeableness) * 0.7),
            fairness_score=50,
            value_compatibility=value_alignment,
            relationship_relevance=perceived.relationship_relevance,
            trauma_match=trauma_match,
            confidence=perceived.certainty,
            inferred_other_beliefs={},
        )


@dataclass
class ActionCandidate:
    action_id: str
    target_id: Optional[str] = None
    feasible: bool = True
    capability_ok: bool = True
    world_consistent: bool = True
    goal_compatible: bool = True
    factors: Dict[str, float] = field(default_factory=dict)
    score: float = 0.0
    reason_codes: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)


@dataclass
class DecisionResult:
    selected_action: str
    candidate_scores: Dict[str, float]
    decision_reason: List[str] = field(default_factory=list)
    decision_distribution: Dict[str, float] = field(default_factory=dict)
    trace_id: str = ""
    state_snapshot_version: int = 0
    target_id: Optional[str] = None


class DecisionCache:
    def __init__(self) -> None:
        self._data: Dict[str, DecisionResult] = {}

    @staticmethod
    def key(npc_id: str, situation_hash: str, state_version: int, memory_version: int,
            relationship_version: int, goal_version: int, emotion_version: int = 0,
            trauma_version: int = 0) -> str:
        return _stable_hash({"npc": npc_id, "situation": situation_hash, "state": state_version,
                             "memory": memory_version, "relationship": relationship_version,
                             "goal": goal_version, "emotion": emotion_version, "trauma": trauma_version})

    def get(self, key: str) -> Optional[DecisionResult]:
        return self._data.get(key)

    def put(self, key: str, result: DecisionResult) -> None:
        self._data[key] = result

    def invalidate_npc(self, npc_id: str) -> None:
        # Keys are hashes, so targeted invalidation is represented by dropping all entries
        # for this NPC only through a side index in production. This lightweight cache uses
        # versioned keys, therefore mutation naturally makes old entries unreachable.
        return None

    def clear(self) -> None:
        self._data.clear()


class PsychologyEngine:
    """Main orchestration layer. Existing cognitive engine remains downstream."""

    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3

    def __init__(self, cognitive_engine: Any = None, rag_adapter: Optional[RAGMemoryAdapter] = None):
        self.cognitive_engine = cognitive_engine
        self.rag = rag_adapter or RAGMemoryAdapter()
        self.cache = DecisionCache()
        self._tier2_cache: Dict[str, Dict[str, Any]] = {}

    # ---------- NPC integration ----------
    def ensure_npc(self, npc: Any) -> NPCPsychologicalState:
        """Attach exactly one authoritative psychology state to the existing NPC instance.

        Existing NPCPersonality/MemoryEntry fields remain untouched for compatibility.
        The returned object is the new authoritative psychological layer for new systems.
        """
        current = getattr(npc, "psychology", None)
        if isinstance(current, NPCPsychologicalState):
            return current
        state = self._bootstrap_from_legacy_npc(npc)
        setattr(npc, "psychology", state)
        return state

    def _bootstrap_from_legacy_npc(self, npc: Any) -> NPCPsychologicalState:
        old = getattr(npc, "personality", None)
        # Deterministic mapping from existing 12 axes into the new representation.
        profile = PersonalityProfile(
            openness=_clamp(50 + (getattr(old, "curiosity", 50) - 50) * 0.5),
            conscientiousness=_clamp(getattr(old, "patience", 50)),
            extraversion=_clamp(50 + (getattr(old, "altruism", 50) - 50) * 0.35),
            agreeableness=_clamp(getattr(old, "altruism", 50)),
            neuroticism=_clamp(getattr(old, "neuroticism", 50)),
            honesty_humility=_clamp(100 - getattr(old, "greed", 50)),
            aggression=_clamp(getattr(old, "aggression", 50)),
            impulsivity=_clamp(100 - getattr(old, "patience", 50)),
            empathy=_clamp(getattr(old, "altruism", 50)),
            traits=["derived_from_legacy_npc_personality"],
        )
        needs_old = getattr(npc, "needs", None)
        needs = NeedState({
            "hunger": getattr(needs_old, "hunger", 20),
            "wealth": getattr(needs_old, "wealth", 40),
            "safety": getattr(needs_old, "safety", 30),
            "social": getattr(needs_old, "social", 30),
            "ambition": getattr(needs_old, "ambition", 50),
        }, {})
        relationship = RelationshipAxis(
            trust=getattr(npc, "trust", 50), affection=getattr(npc, "affinity", 50),
            respect=getattr(npc, "respect", 50), fear=getattr(npc, "fear", 0),
            resentment=_clamp(50 - getattr(npc, "affinity", 50)), dependence=0,
            loyalty=getattr(old, "loyalty", 50) if old else 50,
            suspicion=getattr(old, "suspicion", 50) if old else 50,
            familiarity=getattr(npc, "affinity", 0),
        )
        values = ValueProfile(
            values={v: max(0, 100 - i * 12) for i, v in enumerate(getattr(npc, "value_hierarchy", []))},
            priority_order=list(getattr(npc, "value_hierarchy", ["survival", "wealth", "honor", "family", "faith"])),
        )
        state = NPCPsychologicalState(
            identity=Identity(identity_id=getattr(npc, "id", ""), name=getattr(npc, "name", ""),
                              role=getattr(npc, "faction_role", ""), occupation=getattr(npc, "job", ""),
                              faction_id=getattr(npc, "faction_id", ""), background_summary=getattr(npc, "description", "")),
            personality=profile,
            values=values,
            needs=needs,
            relationships=RelationshipMap({"player": relationship}),
            stress=StressState(fatigue=getattr(npc, "fatigue", 0), coping_capacity=50),
        )
        # Preserve existing memory facts as low-risk compatibility imports.
        for idx, m in enumerate(getattr(npc, "memories", []) or []):
            state.memories.append(MemoryRecord(
                memory_id=f"legacy_{getattr(npc, 'id', 'npc')}_{idx}",
                event_summary=getattr(m, "description", str(m)),
                timestamp=int(getattr(m, "turn", 0)),
                emotional_impact=50 if getattr(m, "emotional_tone", "neutral") != "neutral" else 0,
                importance=int(getattr(m, "significance", 1)),
                participants=["player"], source="direct", decay_rate=0,
                traits=["legacy_import"],
            ))
        return state

    # ---------- tier routing ----------
    def classify_tier(self, npc: Any, event: Optional[Mapping[str, Any]], direct_interaction: bool = False) -> int:
        if direct_interaction:
            return self.TIER_3
        if not event:
            return self.TIER_1
        severity = float(event.get("severity", event.get("intensity", 0)))
        critical = bool(event.get("critical", False) or event.get("goal_critical", False) or event.get("trauma_critical", False))
        distance = max(0.0, float(event.get("distance", 0)))
        if critical or severity >= 70:
            return self.TIER_3
        perceived = severity - min(80, distance * 2)
        threshold = 25
        if perceived < threshold:
            return self.TIER_1
        return self.TIER_2

    def route_event(self, npcs: Iterable[Any], event: Optional[Mapping[str, Any]], direct_targets: Optional[Sequence[str]] = None) -> Dict[int, List[Any]]:
        target_ids = set(direct_targets or [])
        routed = {self.TIER_1: [], self.TIER_2: [], self.TIER_3: []}
        for npc in npcs:
            tier = self.classify_tier(npc, event, getattr(npc, "id", "") in target_ids)
            routed[tier].append(npc)
        return routed

    # ---------- appraisal/state ----------
    def process_tier2(self, npc: Any, event: Mapping[str, Any], tick: int) -> Dict[str, Any]:
        psych = self.ensure_npc(npc)
        raw = dict(event)
        perceived = PerceptionEngine.perceive(npc, SituationContext(tick=tick, visible_events=[raw]), raw)
        if not perceived:
            return {"tier": 1, "detected": False}
        appraisal = AppraisalEngine.evaluate(npc, perceived[0], SituationContext(tick=tick))
        psych.emotion.activate({"type": "fear" if appraisal.threat_score >= 60 else "interest", "activation": appraisal.threat_score * 0.35,
                                "duration_ticks": 1, "trigger": perceived[0].event_id}, tick)
        psych.stress.stress = _clamp(psych.stress.stress + max(0, appraisal.threat_score - appraisal.control_score) * 0.08)
        psych.stress.last_update_tick = tick
        psych.state_version += 1
        return {"tier": 2, "detected": True, "appraisal": _dc_dict(appraisal)}

    # ---------- memory ----------
    def build_memory_query(self, psych: NPCPsychologicalState, situation: SituationContext, appraisal: Optional[AppraisalResult]) -> str:
        goals = ", ".join(g.description for g in psych.goals if g.status == "active")
        emotions = ", ".join(f"{e.type}:{e.intensity:.0f}" for e in psych.emotion.active_emotions)
        relationships = ", ".join(
            f"{rid} trust:{rel.trust:.0f} loyalty:{rel.loyalty:.0f} suspicion:{rel.suspicion:.0f}"
            for rid, rel in psych.relationships.relationships.items()
        )
        trauma = ", ".join(t.name for t in psych.trauma.entries)
        threat = appraisal.threat_score if appraisal else 0
        need = ", ".join(f"{k}:{v:.0f}" for k, v in psych.needs.need_values.items())
        return (f"goals={goals}; emotion={emotions}; stress={psych.stress.stress:.0f}; "
                f"relationships={relationships}; trauma={trauma}; threat={threat:.0f}; needs={need}; "
                f"known={','.join(situation.known_facts)}")

    def retrieve_memories(self, psych: NPCPsychologicalState, situation: SituationContext,
                          appraisal: Optional[AppraisalResult], tier: int) -> List[MemoryRecord]:
        if tier != self.TIER_3:
            return []
        repo = MemoryRepository(psych)
        query = self.build_memory_query(psych, situation, appraisal)
        external = self.rag.retrieve(query, 8)
        candidates: List[MemoryRecord] = list(psych.memories)
        for item in external:
            if isinstance(item, MemoryRecord):
                candidates.append(item)
            elif isinstance(item, Mapping):
                try:
                    candidates.append(MemoryRecord.from_dict(item))
                except Exception:
                    pass
        unique = {m.memory_id: m for m in candidates}
        ranked = repo.rank(unique.values(), tick=situation.tick)
        # Low-confidence memories remain retrievable but are not allowed to dominate downstream scoring.
        return ranked[:5]

    # ---------- decision ----------
    def _goal_score(self, psych: NPCPsychologicalState, action: str) -> float:
        score = 0.0
        for g in psych.goals:
            if g.status != "active":
                continue
            relevance = 1.0 if action in g.description.lower() or g.goal_id in action else 0.15
            score += relevance * (g.priority * 60 + g.urgency * 0.4)
        return min(100.0, score)

    def _relationship_score(self, psych: NPCPsychologicalState, action: str, target_id: Optional[str]) -> float:
        if not target_id:
            return 0.0
        r = psych.relationships.get(target_id)
        low = action.lower()
        if any(k in low for k in ("rescue", "protect", "help")):
            return (r.affection * 0.25 + r.loyalty * 0.35 + r.dependence * 0.2 - r.resentment * 0.25)
        if any(k in low for k in ("attack", "confront")):
            return (r.fear * 0.2 + r.resentment * 0.35 + (100-r.trust) * 0.25)
        if any(k in low for k in ("persuade", "negotiate", "talk")):
            return r.trust * 0.3 + r.respect * 0.2 - r.suspicion * 0.25
        return 0.0

    def _trauma_score(self, psych: NPCPsychologicalState, action: str, appraisal: Optional[AppraisalResult]) -> float:
        if not appraisal or appraisal.trauma_match <= 0:
            return 0.0
        # Trigger-specific cost, not a global penalty.
        action_l = action.lower()
        cost = 0.0
        for match in psych.trauma.active_triggers:
            tendencies = " ".join(match.get("behavioral_tendencies", [])).lower()
            if any(x in action_l for x in ("escape", "avoid", "hide")) and "avoid" in tendencies:
                cost -= match["activation_intensity"] * 0.15
            elif "control" in tendencies and any(x in action_l for x in ("control", "extinguish", "secure")):
                cost += match["activation_intensity"] * 0.12
            else:
                cost -= match["activation_intensity"] * 0.08
        return cost

    def score_action(self, npc: Any, action: ActionCandidate, appraisal: Optional[AppraisalResult], target_id: Optional[str]) -> ActionCandidate:
        psych = self.ensure_npc(npc)
        p, e, s = psych.personality, psych.emotion, psych.stress
        if not (action.feasible and action.capability_ok and action.world_consistent and action.goal_compatible):
            action.score = float("-inf")
            return action
        factors = dict(action.factors)
        factors.setdefault("survival", 50)
        factors.setdefault("safety", 50)
        factors.setdefault("goal_progress", self._goal_score(psych, action.action_id))
        factors.setdefault("need_satisfaction", 50)
        factors.setdefault("relationship_preservation", self._relationship_score(psych, action.action_id, target_id))
        factors.setdefault("value_alignment", 50)
        factors.setdefault("emotion_fit", 50)
        factors.setdefault("risk", 50)
        factors.setdefault("resource_cost", 0)
        factors.setdefault("time_cost", 0)
        factors.setdefault("social_cost", 0)
        factors.setdefault("reputation", 50)
        factors.setdefault("information_confidence", appraisal.confidence * 100 if appraisal else 50)
        factors.setdefault("trauma_avoidance", self._trauma_score(psych, action.action_id, appraisal))
        factors.setdefault("opportunity", appraisal.opportunity_score if appraisal else 0)

        score = 0.0
        score += factors["survival"] * (0.8 + p.neuroticism / 500)
        score += factors["safety"] * (0.7 + s.stress / 500)
        score += factors["goal_progress"] * (0.8 + p.conscientiousness / 250)
        score += factors["need_satisfaction"] * 0.7
        score += factors["relationship_preservation"] * (0.5 + p.agreeableness / 250)
        score += factors["value_alignment"] * 0.8
        score += factors["emotion_fit"] * 0.45
        score += factors["opportunity"] * (0.3 + p.openness / 300)
        score += factors["trauma_avoidance"]
        score += factors["information_confidence"] * 0.15
        score -= factors["risk"] * max(0.15, 1.0 - p.impulsivity / 150)
        score -= factors["resource_cost"] * 0.35
        score -= factors["time_cost"] * 0.15
        score -= factors["social_cost"] * (0.2 + (100-p.extraversion) / 500)
        # Personality adjusts weights; it never maps directly to an action rule.
        if any(k in action.action_id.lower() for k in ("plan", "prepare")):
            score += p.conscientiousness * 0.25
        if any(k in action.action_id.lower() for k in ("social", "talk", "negotiate")):
            score += p.extraversion * 0.2
        if any(k in action.action_id.lower() for k in ("help", "rescue", "protect")):
            score += p.empathy * 0.25
        if any(k in action.action_id.lower() for k in ("exploit", "cheat", "steal")):
            score -= p.honesty_humility * 0.25

        # Causal imperfection, not random noise.
        if appraisal and appraisal.confidence < 0.5:
            score += (50 - appraisal.confidence * 100) * (0.3 if "retreat" in action.action_id else -0.05)
            action.reason_codes.append("information_gap")
        if s.stress >= s.stress_threshold:
            score += factors["emotion_fit"] * 0.25
            if "retreat" in action.action_id or "hide" in action.action_id:
                score += s.stress * 0.25
            action.reason_codes.append("stress_narrowing")
        action.score = round(score, 4)
        action.reason_codes.append("psychological_weighting")
        return action

    @staticmethod
    def _normalize(scores: Mapping[str, float]) -> Dict[str, float]:
        finite = {k: v for k, v in scores.items() if v != float("-inf")}
        if not finite:
            return {}
        minimum = min(finite.values())
        shifted = {k: max(0.001, v - minimum + 1.0) for k, v in finite.items()}
        total = sum(shifted.values())
        return {k: round(v / total, 6) for k, v in shifted.items()}

    @staticmethod
    def _select_reproducible(distribution: Mapping[str, float], seed_context: str) -> str:
        """Deterministic selection from the current distribution; no uncontrolled RNG."""
        if not distribution:
            return "idle"
        ordered = sorted(distribution.items())
        digest = sha256(seed_context.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:8], "big") / float(2**64)
        cursor = 0.0
        for action, probability in ordered:
            cursor += probability
            if bucket <= cursor:
                return action
        return ordered[-1][0]

    def decide(self, npc: Any, situation: SituationContext, available_candidates: Sequence[ActionCandidate],
               event: Optional[Mapping[str, Any]] = None, target_id: Optional[str] = None,
               direct_interaction: bool = False) -> DecisionResult:
        psych = self.ensure_npc(npc)
        tier = self.classify_tier(npc, event, direct_interaction)
        if tier < self.TIER_3:
            if tier == self.TIER_2 and event:
                self.process_tier2(npc, event, situation.tick)
            return DecisionResult("no_full_decision", {}, [f"tier_{tier}"], {},
                                  _stable_hash({"npc": getattr(npc, "id", ""), "tick": situation.tick}), psych.state_version)

        # Stage 1/2/3
        perceived = PerceptionEngine.perceive(npc, situation, event)
        appraisal = AppraisalEngine.evaluate(npc, perceived[0], situation) if perceived else None
        if appraisal:
            psych.trauma.match({"event": event or {}, "tags": perceived[0].traits}, situation.tick)
            for req in self._emotion_requests(appraisal):
                psych.emotion.activate(req, situation.tick)
            psych.stress.stress = _clamp(psych.stress.stress + max(0, appraisal.threat_score - appraisal.control_score) * 0.15 + appraisal.trauma_match * 0.08)
            psych.stress.last_update_tick = situation.tick

        # Stage 4/5/6/7/8
        self._evaluate_needs(psych, situation.tick)
        self._evaluate_goals(psych, situation.tick)
        memories = self.retrieve_memories(psych, situation, appraisal, self.TIER_3)
        _ = memories  # evidence source for downstream cognitive engine / trace

        # Cache key is based on current authoritative versions.
        situation_hash = _stable_hash(_dc_dict(situation))
        cache_key = DecisionCache.key(getattr(npc, "id", ""), situation_hash, psych.state_version,
                                      psych.memory_version, psych.relationship_version, psych.goal_version,
                                      psych.emotion.last_update_tick, len(psych.trauma.active_triggers))
        cached = self.cache.get(cache_key)
        if cached and cached.state_snapshot_version == psych.state_version:
            return cached

        # Existing cognitive engine remains downstream. It may add its own inference,
        # hypothesis, motive and micro-leakage context without owning psychological truth.
        if self.cognitive_engine is not None:
            try:
                inference = self._invoke_cognitive_engine(npc, situation)
            except Exception:
                inference = None
        else:
            inference = None

        # Stage 9/10
        candidates = [self._validate_candidate(npc, c, situation, psych) for c in available_candidates]
        scored = [self.score_action(npc, c, appraisal, target_id) for c in candidates if c.feasible]
        score_map = {c.action_id: c.score for c in scored if c.score != float("-inf")}
        distribution = self._normalize(score_map)
        seed = _stable_hash({"npc": getattr(npc, "id", ""), "situation": situation_hash,
                             "state": psych.state_version, "scores": score_map})
        selected = self._select_reproducible(distribution, seed)
        reason = []
        if appraisal and appraisal.trauma_match > 0:
            reason.append("trauma_context")
        if psych.stress.stress >= psych.stress.stress_threshold:
            reason.append("elevated_stress")
        if memories:
            reason.append("retrieved_memory_evidence")
        if inference:
            reason.append("cognitive_engine_inference")
        reason.append("feasibility_filtered")

        result = DecisionResult(selected, score_map, reason, distribution, seed, psych.state_version, target_id)
        self.cache.put(cache_key, result)
        return result

    @staticmethod
    def _emotion_requests(appraisal: AppraisalResult) -> List[Dict[str, Any]]:
        requests = []
        if appraisal.threat_score > 0:
            requests.append({"type": "fear", "activation": appraisal.threat_score * 0.75,
                             "duration_ticks": 2, "trigger": appraisal.event_id})
        if appraisal.goal_obstruction > 60:
            requests.append({"type": "anger", "activation": appraisal.goal_obstruction * 0.45,
                             "duration_ticks": 2, "trigger": appraisal.event_id})
        if appraisal.opportunity_score > 60:
            requests.append({"type": "curiosity", "activation": appraisal.opportunity_score * 0.4,
                             "duration_ticks": 2, "trigger": appraisal.event_id})
        return requests

    @staticmethod
    def _evaluate_needs(psych: NPCPsychologicalState, tick: int) -> None:
        for key, value in list(psych.needs.need_values.items()):
            psych.needs.urgency[key] = _clamp(value * (1 + psych.stress.stress / 300))
        psych.needs.last_update_tick = tick

    @staticmethod
    def _evaluate_goals(psych: NPCPsychologicalState, tick: int) -> None:
        for goal in psych.goals:
            if goal.status != "active" or goal.deadline_tick is None:
                continue
            remaining = goal.deadline_tick - tick
            if remaining <= 0:
                goal.urgency = 100
            elif remaining < 10:
                goal.urgency = max(goal.urgency, 80)

    @staticmethod
    def _validate_candidate(npc: Any, candidate: ActionCandidate, situation: SituationContext,
                            psych: NPCPsychologicalState) -> ActionCandidate:
        if situation.available_actions and candidate.action_id not in situation.available_actions:
            candidate.feasible = False
            candidate.reason_codes.append("not_available_in_world")
        capabilities = getattr(npc, "skills", []) or []
        required = candidate.factors.get("required_capability")
        if required and required not in capabilities:
            candidate.capability_ok = False
            candidate.reason_codes.append("capability_missing")
        return candidate

    def _invoke_cognitive_engine(self, npc: Any, situation: SituationContext) -> Any:
        engine = self.cognitive_engine
        # Intentionally narrow compatibility bridge: do not assume a particular new API.
        if hasattr(engine, "predict_autonomous_action"):
            return engine.predict_autonomous_action(npc)
        if hasattr(engine, "predict_next_intent"):
            return engine.predict_next_intent(npc)
        return None

    # ---------- relationships/state mutation ----------
    def apply_relationship_delta(self, npc: Any, delta: RelationshipDelta) -> Dict[str, float]:
        psych = self.ensure_npc(npc)
        applied = psych.relationships.apply_delta(delta)
        if applied:
            psych.relationship_version += 1
            psych.state_version += 1
        return applied

    def record_memory(self, npc: Any, memory: MemoryRecord) -> MemoryRecord:
        psych = self.ensure_npc(npc)
        return MemoryRepository(psych).add(memory)

    def update_after_action(self, npc: Any, *, tick: int, selected_action: str,
                            emotion_requests: Optional[Sequence[Mapping[str, Any]]] = None,
                            stress_delta: float = 0, goal_updates: Optional[Mapping[str, float]] = None,
                            relationship_delta: Optional[RelationshipDelta] = None,
                            memory: Optional[MemoryRecord] = None) -> None:
        psych = self.ensure_npc(npc)
        # Explicit order prevents Emotion <-> Stress infinite loops.
        if emotion_requests:
            for req in emotion_requests:
                psych.emotion.activate(req, tick)
        if stress_delta:
            psych.stress.stress = _clamp(psych.stress.stress + stress_delta)
            psych.stress.last_update_tick = tick
        if goal_updates:
            for gid, progress in goal_updates.items():
                for goal in psych.goals:
                    if goal.goal_id == gid:
                        goal.progress = _clamp(progress)
                        psych.goal_version += 1
                        break
        if relationship_delta:
            self.apply_relationship_delta(npc, relationship_delta)
        if memory:
            self.record_memory(npc, memory)
        psych.state_version += 1


class LLMProjection:
    """Creates expression-only snapshots. It deliberately omits hidden full state."""

    @staticmethod
    def project(npc: Any, situation: SituationContext, decision: DecisionResult,
                target_id: Optional[str] = None) -> Dict[str, Any]:
        psych = getattr(npc, "psychology", None)
        if not isinstance(psych, NPCPsychologicalState):
            psych = NPCPsychologicalState()
        relevant_relationship = None
        if target_id:
            rel = psych.relationships.get(target_id)
            relevant_relationship = {"trust": round(rel.trust), "affection": round(rel.affection),
                                     "respect": round(rel.respect), "fear": round(rel.fear),
                                     "loyalty": round(rel.loyalty), "suspicion": round(rel.suspicion)}
        expression = {e.type: round(e.intensity) for e in psych.emotion.active_emotions}
        return {
            "npc": {"name": psych.identity.name},
            "situation": {"location": situation.location_id, "events": list(situation.visible_events)},
            "decision": {"selected_action": decision.selected_action, "reason": list(decision.decision_reason)},
            "emotion_expression": expression,
            "relationship": relevant_relationship or {},
            "dialogue_context": {"target": target_id or "", "speech_intent": decision.selected_action},
            "known_facts": list(situation.known_facts),
            "allowed_knowledge_scope": list(situation.known_facts),
        }


class LLMBoundary:
    """Accepts advisory LLM output only through validation; never mutates NPC state directly."""

    def __init__(self, validator: Optional[Callable[[Any, Mapping[str, Any]], bool]] = None):
        self.validator = validator

    def validate_candidate(self, npc: Any, suggestion: Mapping[str, Any], situation: SituationContext) -> Optional[ActionCandidate]:
        action_id = str(suggestion.get("action_id", "")).strip()
        if not action_id:
            return None
        candidate = ActionCandidate(action_id=action_id, target_id=suggestion.get("target_id"))
        if situation.available_actions and action_id not in situation.available_actions:
            return None
        if self.validator and not self.validator(npc, suggestion):
            return None
        return candidate

    @staticmethod
    def parse_social_interpretation(output: Mapping[str, Any]) -> Dict[str, Any]:
        """Returns advisory interpretation only; caller must create an Event/Delta."""
        allowed = {"social_interpretation", "target_id", "event_id", "confidence"}
        return {k: output[k] for k in allowed if k in output}

    @staticmethod
    def reject_state_mutation(output: Mapping[str, Any]) -> Dict[str, Any]:
        forbidden = {"trust", "affection", "respect", "fear", "resentment", "dependence", "loyalty",
                     "suspicion", "familiarity", "add_memory", "state_update", "world_truth"}
        return {"accepted": {k: v for k, v in output.items() if k not in forbidden},
                "rejected_keys": sorted(k for k in output if k in forbidden)}


# Small serialization helpers for existing WorldState integration.
def attach_psychology_to_npc(npc: Any, psychology: Optional[NPCPsychologicalState] = None) -> NPCPsychologicalState:
    state = psychology or PsychologyEngine().ensure_npc(npc)
    setattr(npc, "psychology", state)
    return state


def psychology_to_worldstate_dict(npc: Any) -> Dict[str, Any]:
    state = getattr(npc, "psychology", None)
    return state.to_dict() if isinstance(state, NPCPsychologicalState) else {}


def psychology_from_worldstate_dict(npc: Any, raw: Mapping[str, Any]) -> NPCPsychologicalState:
    state = NPCPsychologicalState.from_dict(raw)
    setattr(npc, "psychology", state)
    return state


__all__ = [
    "SCHEMA_VERSION", "Identity", "PersonalityProfile", "TemperamentProfile", "ValueProfile",
    "MotivationEntry", "MotivationProfile", "NeedState", "PreferenceProfile", "EmotionInstance",
    "EmotionState", "StressState", "TraumaEntry", "TraumaProfile", "RelationshipAxis",
    "RelationshipDelta", "RelationshipMap", "MemoryRecord", "GoalState", "SituationContext",
    "PerceivedEvent", "AppraisalResult", "BehavioralProfile", "NPCPsychologicalState",
    "PersonalityTemplate", "PersonalityTemplateLibrary", "MemoryRepository", "RAGMemoryAdapter",
    "PerceptionEngine", "AppraisalEngine", "ActionCandidate", "DecisionResult", "DecisionCache",
    "PsychologyEngine", "LLMProjection", "LLMBoundary", "attach_psychology_to_npc",
    "psychology_to_worldstate_dict", "psychology_from_worldstate_dict",
]
