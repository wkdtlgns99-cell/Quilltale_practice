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
    OutfitMechanicsEngine, EncumbranceStatus, ArmorChafingResult, QuickDrawResult, EyewearHazardResult,
    BackpackSpec, BackpackStorageStatus, BACKPACK_SPECS
)
from .stamina_engine import StaminaEngine
from .trap_engine import TrapEngine, TrapSpec, TrapInstance
from .dungeon_engine import DungeonEngine, DungeonInstance, DungeonFloor, DungeonRoom
from .party_sanity_engine import PartySanityEngine, MentalBreakdownSpec, MENTAL_BREAKDOWN_REGISTRY
from .cave_in_engine import (
    CaveCollapseEngine, CAVE_COLLAPSE_SYSTEM, DUNGEON_ENVIRONMENT_SYSTEMS,
    RockStrataSpec, VibrationSourceSpec, CollapseStageSpec
)
from .thermal_engine import (
    ThermalSurvivalEngine, THERMAL_SURVIVAL_SYSTEM, ADDITIONAL_SURVIVAL_ENVIRONMENT_SYSTEMS,
    ThermalClothingSpec, HypothermiaStageSpec, HyperthermiaStageSpec
)
from .disease_engine import (
    EpidemicEngine, EPIDEMIC_SYSTEM, DISEASE_REGISTRY,
    DiseaseSpec, DiseaseStageSpec, ActiveInfection, InfectionAttemptResult
)
from .mana_burn_engine import (
    ManaBurnEngine, EtherMutationSpec, ManaCircuitState, ETHER_MUTATIONS_REGISTRY
)
from .ration_engine import (
    RationSpoilageEngine, FoodItemStatus, PreservationMethodSpec, PRESERVATION_METHODS
)
from .sleep_engine import (
    SleepDeprivationEngine, CircadianClock, StimulantSpec, BeddingQualitySpec,
    STIMULANTS_REGISTRY, BEDDING_REGISTRY
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
    "StaminaEngine",
    "TrapEngine",
    "TrapSpec",
    "TrapInstance",
    "DungeonEngine",
    "DungeonInstance",
    "DungeonFloor",
    "DungeonRoom",
    "PartySanityEngine",
    "MentalBreakdownSpec",
    "MENTAL_BREAKDOWN_REGISTRY",
    "CaveCollapseEngine",
    "CAVE_COLLAPSE_SYSTEM",
    "DUNGEON_ENVIRONMENT_SYSTEMS",
    "RockStrataSpec",
    "VibrationSourceSpec",
    "CollapseStageSpec",
    "ThermalSurvivalEngine",
    "THERMAL_SURVIVAL_SYSTEM",
    "ADDITIONAL_SURVIVAL_ENVIRONMENT_SYSTEMS",
    "ThermalClothingSpec",
    "HypothermiaStageSpec",
    "HyperthermiaStageSpec",
    "EpidemicEngine",
    "EPIDEMIC_SYSTEM",
    "DISEASE_REGISTRY",
    "DiseaseSpec",
    "DiseaseStageSpec",
    "ActiveInfection",
    "InfectionAttemptResult",
    "BackpackSpec",
    "BackpackStorageStatus",
    "BACKPACK_SPECS",
    "ManaBurnEngine",
    "EtherMutationSpec",
    "ManaCircuitState",
    "ETHER_MUTATIONS_REGISTRY",
    "RationSpoilageEngine",
    "FoodItemStatus",
    "PreservationMethodSpec",
    "PRESERVATION_METHODS",
    "SleepDeprivationEngine",
    "CircadianClock",
    "StimulantSpec",
    "BeddingQualitySpec",
    "STIMULANTS_REGISTRY",
    "BEDDING_REGISTRY",
]



