"""
World module for Quilltale TRPG Engine.
"""
from .state import (
    WorldState, Location, NPC, Item, Player, MemoryEntry, DISPOSITION_KO_MAP,
    Skill, Title, EquipmentSlots, NPCPersonality, EnvironmentalMetrics, PendingInformation,
    ClothingLayer, NPCVisualDetails, FacialDetails, BodyMeasurements, ItemVisualProfile
)
from .dice import DiceEngine, DiceCheckResult
from .validator import ActionValidator
from .persistence import PersistenceManager
from .legacy import LegacyManager
from .generator import WorldGenerator
from .skills import SkillSystem
from .incantation import IncantationSystem
from .chronicle import ChronicleManager
from .graph_engine import (
    LivingWorldGraph, PhysicsChemistryMatrix, EcologicalFeedbackLoop, EcologicalVacuumCollapse
)

from .stat_engine import StatEngine
from .attack_physics_engine import AttackPhysicsEngine, AttackPhysicsResult
from .combat_time_track_engine import CombatDistanceManager, ActionTimeTrackEngine, CombatAction, InterruptEvent
from .time_calendar_engine import TimeCalendarEngine, DAILY_ACTION_DURATIONS
from .stealth_engine import StealthInfiltrationEngine, StealthAttemptResult, EavesdropAttemptResult
from .equipment import EquipmentEngine, EquipmentSet, EquipmentSetBonus
from .harvest_engine import AnatomyHarvestEngine, MonsterPart, PartAttackResult, HarvestOutcome
from .outfit_engine import (
    OutfitMechanicsEngine, EncumbranceStatus, ArmorChafingResult, QuickDrawResult, EyewearHazardResult
)

__all__ = [
    "WorldState",
    "Location",
    "NPC",
    "Item",
    "Player",
    "MemoryEntry",
    "DISPOSITION_KO_MAP",
    "Skill",
    "Title",
    "EquipmentSlots",
    "NPCPersonality",
    "EnvironmentalMetrics",
    "PendingInformation",
    "DiceEngine",
    "DiceCheckResult",
    "ActionValidator",
    "PersistenceManager",
    "LegacyManager",
    "WorldGenerator",
    "SkillSystem",
    "IncantationSystem",
    "ChronicleManager",
    "LivingWorldGraph",
    "PhysicsChemistryMatrix",
    "EcologicalFeedbackLoop",
    "EcologicalVacuumCollapse",
    "StatEngine",
    "AttackPhysicsEngine",
    "AttackPhysicsResult",
    "CombatDistanceManager",
    "ActionTimeTrackEngine",
    "CombatAction",
    "InterruptEvent",
    "TimeCalendarEngine",
    "DAILY_ACTION_DURATIONS",
    "StealthInfiltrationEngine",
    "StealthAttemptResult",
    "EavesdropAttemptResult",
    "EquipmentEngine",
    "EquipmentSet",
    "EquipmentSetBonus",
    "AnatomyHarvestEngine",
    "MonsterPart",
    "PartAttackResult",
    "HarvestOutcome",
    "ClothingLayer",
    "NPCVisualDetails",
    "FacialDetails",
    "BodyMeasurements",
    "ItemVisualProfile",
    "OutfitMechanicsEngine",
    "EncumbranceStatus",
    "ArmorChafingResult",
    "QuickDrawResult",
    "EyewearHazardResult",
]



