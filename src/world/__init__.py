"""
World module for Quilltale TRPG Engine.
"""
from .state import (
    WorldState, Location, NPC, Item, Player, MemoryEntry, DISPOSITION_KO_MAP,
    Skill, Title, EquipmentSlots, NPCPersonality, EnvironmentalMetrics, PendingInformation
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
]



