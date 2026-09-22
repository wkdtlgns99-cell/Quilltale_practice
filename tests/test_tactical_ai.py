"""
Unit tests for Monster Tactical AI / Behavior Tree Engine (tactical_ai.py).
Tests cover all 5 behavior patterns:
  1. Self-Preservation (flee, call_help, heal_self, berserker_rage)
  2. Ranged Kiting (kite_away, take_cover)
  3. Exploit Vulnerability (focus fire on debuffed player)
  4. Vanguard Guard (guard_ally / intercept)
  5. Standard Fallback (None → delegate to NPCSkillEngine)
  + Archetype classification
  + TacticalDecision traits field presence
  + Integration through NPCSkillEngine.process_npc_combat_turn
"""
import copy
import pytest

from src.world.state import WorldState
from src.world.entities import (
    NPC, NPCPersonality, CombatProfile, Player, Location,
    EquipmentSlots, Item,
)
from src.world.tactical_ai import (
    MonsterTacticsEngine, TacticalArchetype, TacticalDecision,
)
from src.world.status_engine import StatusEffectEngine, StatusEffect


# ── Helper: minimal world state factory ──

def _make_state(
    player_hp: int = 100,
    player_max_hp: int = 100,
    player_statuses: dict | None = None,
    npc_list: list[NPC] | None = None,
) -> WorldState:
    """Create a minimal WorldState for tactical AI testing."""
    player = Player(
        name="TestPlayer",
        location="loc_1",
        health=player_hp,
        max_health=player_max_hp,
        mana=50,
        max_mana=50,
        stamina=100,
        max_stamina=100,
        gold=100,
        level=5,
        exp=0,
        inventory=[],
        equipment=EquipmentSlots(),
        status_effects=player_statuses or {},
    )

    loc = Location(
        id="loc_1",
        name="전투 현장",
        description="테스트용 전투 장소",
        exits={"north": "loc_2"},
        npcs=[],
        items=[],
    )

    state = WorldState(
        player=player,
        locations={"loc_1": loc, "loc_2": Location(id="loc_2", name="도주처", description="", exits={}, npcs=[], items=[])},
        npcs={},
        items={},
        quests={},
        turn=5,
    )

    if npc_list:
        for npc in npc_list:
            state.npcs[npc.id] = npc
            loc.npcs.append(npc.id)

    return state


def _make_hostile_npc(
    npc_id: str = "goblin_1",
    name: str = "고블린 졸병",
    job: str = "졸개",
    hp: int = 50,
    max_hp: int = 50,
    courage: int = 50,
    aggression: int = 50,
    strength: int = 10,
    agility: int = 10,
    preferred_tactics: str = "",
    traits: list[str] | None = None,
    inventory: list[str] | None = None,
) -> NPC:
    return NPC(
        id=npc_id,
        name=name,
        description=f"{name} 테스트 NPC",
        location="loc_1",
        job=job,
        disposition="hostile",
        health=hp,
        max_health=max_hp,
        strength=strength,
        agility=agility,
        personality=NPCPersonality(courage=courage, aggression=aggression),
        combat_profile=CombatProfile(preferred_tactics=preferred_tactics),
        traits=traits or [],
        inventory=inventory or [],
    )


# ══════════════════════════════════════════════
# Test Group 1: Archetype Classification
# ══════════════════════════════════════════════

class TestArchetypeClassification:
    def test_archer_mage_by_job(self):
        npc = _make_hostile_npc(job="궁수")
        assert MonsterTacticsEngine.determine_archetype(npc) == TacticalArchetype.ARCHER_MAGE

    def test_vanguard_tank_by_job(self):
        npc = _make_hostile_npc(job="방패 기사")
        assert MonsterTacticsEngine.determine_archetype(npc) == TacticalArchetype.VANGUARD_TANK

    def test_berserker_by_job(self):
        npc = _make_hostile_npc(job="광전사")
        assert MonsterTacticsEngine.determine_archetype(npc) == TacticalArchetype.BERSERKER_BRUTE

    def test_coward_by_job(self):
        npc = _make_hostile_npc(job="고블린 졸개")
        assert MonsterTacticsEngine.determine_archetype(npc) == TacticalArchetype.COWARD_MINION

    def test_skirmisher_by_job(self):
        npc = _make_hostile_npc(job="암살자")
        assert MonsterTacticsEngine.determine_archetype(npc) == TacticalArchetype.SKIRMISHER

    def test_generalist_fallback(self):
        npc = _make_hostile_npc(job="일반 전사", courage=60, aggression=50)
        assert MonsterTacticsEngine.determine_archetype(npc) == TacticalArchetype.GENERALIST

    def test_high_aggression_becomes_berserker(self):
        npc = _make_hostile_npc(job="도시 병사", courage=60, aggression=85)
        assert MonsterTacticsEngine.determine_archetype(npc) == TacticalArchetype.BERSERKER_BRUTE

    def test_low_courage_becomes_coward(self):
        npc = _make_hostile_npc(job="평범한 도시민", courage=20, aggression=30)
        assert MonsterTacticsEngine.determine_archetype(npc) == TacticalArchetype.COWARD_MINION

    def test_traits_based_classification(self):
        npc = _make_hostile_npc(job="병사", traits=["궁수", "원거리 사격"])
        assert MonsterTacticsEngine.determine_archetype(npc) == TacticalArchetype.ARCHER_MAGE


# ══════════════════════════════════════════════
# Test Group 2: CC Stunned (Node 0)
# ══════════════════════════════════════════════

class TestCCStunned:
    def test_stunned_npc_cannot_act(self):
        npc = _make_hostile_npc()
        state = _make_state(npc_list=[npc])
        StatusEffectEngine.apply_status(npc, "stun", duration=2, potency=0)
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is not None
        assert decision.action_type == "cc_stunned"
        assert decision.is_success is False
        assert "tactical_ai" in decision.traits

    def test_paralyzed_npc_cannot_act(self):
        npc = _make_hostile_npc()
        state = _make_state(npc_list=[npc])
        StatusEffectEngine.apply_status(npc, "paralysis", duration=1, potency=0)
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is not None
        assert decision.action_type == "cc_stunned"


# ══════════════════════════════════════════════
# Test Group 3: Self-Preservation (Node 1)
# ══════════════════════════════════════════════

class TestSelfPreservation:
    def test_coward_flees_at_low_hp(self):
        """Coward with HP ≤ 25% and courage < 40 should flee."""
        npc = _make_hostile_npc(
            job="고블린 졸개", hp=10, max_hp=50, courage=20
        )
        state = _make_state(npc_list=[npc])
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is not None
        assert decision.action_type == "flee"
        assert "self_preservation" in decision.traits
        assert decision.extra.get("flee_distance_m", 0) > 0

    def test_berserker_rages_instead_of_flee(self):
        """Berserker at HP ≤ 25% should rage, not flee."""
        npc = _make_hostile_npc(
            job="광전사", hp=10, max_hp=50, courage=80, aggression=90
        )
        state = _make_state(npc_list=[npc])
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is not None
        assert decision.action_type == "berserker_rage"
        assert decision.extra.get("rage_bonus_pct") == 50

    def test_npc_calls_help_with_allies(self):
        """Low-HP NPC with allied hostiles should call for help."""
        npc = _make_hostile_npc(
            npc_id="goblin_1", name="고블린 병사", job="도적", hp=8, max_hp=50, courage=35
        )
        ally = _make_hostile_npc(
            npc_id="goblin_2", name="고블린 궁수", job="궁수", hp=40, max_hp=50
        )
        state = _make_state(npc_list=[npc, ally])
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is not None
        assert decision.action_type == "call_help"
        assert "goblin_2" in decision.extra.get("ally_ids", [])

    def test_npc_heals_self_with_potion(self):
        """NPC at low HP with healing potion should use it before fleeing."""
        potion = Item(
            id="potion_heal_1",
            name="체력 회복 포션",
            description="붉은 물약",
            location="inventory",
            item_type="consumable",
            value=25,
            traits=["치유"],
        )
        npc = _make_hostile_npc(
            job="도적", hp=10, max_hp=50, courage=35,
            inventory=["potion_heal_1"],
        )
        state = _make_state(npc_list=[npc])
        state.items["potion_heal_1"] = potion
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is not None
        assert decision.action_type == "heal_self"
        assert npc.health > 10  # HP increased
        assert "potion_heal_1" not in npc.inventory  # consumed

    def test_healthy_npc_does_not_flee(self):
        """NPC with HP > 25% should not trigger self-preservation."""
        npc = _make_hostile_npc(hp=40, max_hp=50, courage=20)
        state = _make_state(npc_list=[npc])
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        # Should be None (standard attack fallback) since HP > 25%
        assert decision is None


# ══════════════════════════════════════════════
# Test Group 4: Ranged Kiting (Node 2)
# ══════════════════════════════════════════════

class TestRangedKiting:
    def test_archer_kites_when_close(self):
        """Archer archetype at ≤ 8m distance should kite away."""
        npc = _make_hostile_npc(npc_id="archer_1", name="고블린 궁수", job="궁수")
        state = _make_state(npc_list=[npc])
        # Manually set distance to within melee/close range
        state.set_distance(npc.id, "player", 5.0)
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is not None
        assert decision.action_type in ("kite_away", "take_cover")
        assert "ranged_kiting" in decision.traits

    def test_archer_takes_cover_behind_ally(self):
        """Archer near melee with a tank ally should take cover."""
        archer = _make_hostile_npc(npc_id="archer_1", name="고블린 궁수", job="궁수")
        tank = _make_hostile_npc(npc_id="tank_1", name="오크 방패병", job="방패 기사")
        state = _make_state(npc_list=[archer, tank])
        state.set_distance(archer.id, "player", 4.0)
        decision = MonsterTacticsEngine.evaluate_tactical_turn(archer, state)
        assert decision is not None
        assert decision.action_type == "take_cover"
        assert decision.extra.get("cover_ally_id") == "tank_1"
        assert decision.extra.get("evasion_bonus") == 2

    def test_archer_at_safe_distance_no_kiting(self):
        """Archer at 15m should NOT kite."""
        npc = _make_hostile_npc(job="궁수")
        state = _make_state(npc_list=[npc])
        state.set_distance(npc.id, "player", 15.0)
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is None  # standard attack fallback


# ══════════════════════════════════════════════
# Test Group 5: Exploit Vulnerability (Node 3)
# ══════════════════════════════════════════════

class TestExploitVulnerability:
    def test_exploit_stunned_player(self):
        """NPC should exploit a stunned player with boosted damage."""
        npc = _make_hostile_npc(job="암살자", strength=15, agility=15)
        stun_effect = StatusEffect(
            id="stun", name="기절",
            effect_type="action_block", is_action_block=True,
            duration_turns=2,
        )
        state = _make_state(
            player_hp=80, player_max_hp=100,
            player_statuses={"stun": stun_effect},
            npc_list=[npc],
        )
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is not None
        assert decision.action_type in ("exploit_status", "exploit_status_miss")
        assert "exploit_vulnerability" in decision.traits

    def test_no_exploit_on_healthy_player(self):
        """Player without debuffs → no exploit, standard attack."""
        npc = _make_hostile_npc(job="암살자", strength=15)
        state = _make_state(player_hp=80, npc_list=[npc])
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is None


# ══════════════════════════════════════════════
# Test Group 6: Vanguard Guard (Node 4)
# ══════════════════════════════════════════════

class TestVanguardGuard:
    def test_tank_guards_wounded_ally(self):
        """Tank should guard a wounded hostile ally (HP ≤ 30%)."""
        tank = _make_hostile_npc(npc_id="tank_1", name="오크 수호자", job="방패 기사")
        wounded = _make_hostile_npc(
            npc_id="goblin_1", name="부상 고블린", job="졸개",
            hp=10, max_hp=50
        )
        state = _make_state(npc_list=[tank, wounded])
        decision = MonsterTacticsEngine.evaluate_tactical_turn(tank, state)
        assert decision is not None
        assert decision.action_type == "guard_ally"
        assert decision.extra.get("ward_target_id") == "goblin_1"
        assert "vanguard_intercept" in decision.traits

    def test_tank_guards_ranged_ally(self):
        """Tank should guard an archer ally even if healthy."""
        tank = _make_hostile_npc(npc_id="tank_1", name="철갑 기사", job="방패 기사")
        archer = _make_hostile_npc(npc_id="archer_1", name="궁수", job="궁수", hp=40, max_hp=50)
        state = _make_state(npc_list=[tank, archer])
        decision = MonsterTacticsEngine.evaluate_tactical_turn(tank, state)
        assert decision is not None
        assert decision.action_type == "guard_ally"
        assert decision.extra.get("ward_target_id") == "archer_1"

    def test_tank_no_guard_when_alone(self):
        """Tank alone (no allies to protect) → standard attack."""
        tank = _make_hostile_npc(npc_id="tank_1", job="방패 기사")
        state = _make_state(npc_list=[tank])
        decision = MonsterTacticsEngine.evaluate_tactical_turn(tank, state)
        assert decision is None


# ══════════════════════════════════════════════
# Test Group 7: TacticalDecision traits compliance
# ══════════════════════════════════════════════

class TestTraitsCompliance:
    def test_tactical_decision_has_traits_field(self):
        """Rule 5: All game data classes must have traits field."""
        td = TacticalDecision(
            action_type="test", npc_id="n1", npc_name="T", summary_ko="test"
        )
        assert hasattr(td, "traits")
        assert isinstance(td.traits, list)

    def test_all_decisions_include_tactical_ai_trait(self):
        """Every tactical decision from the engine should have 'tactical_ai' trait."""
        npc = _make_hostile_npc(job="고블린 졸개", hp=5, max_hp=50, courage=10)
        state = _make_state(npc_list=[npc])
        decision = MonsterTacticsEngine.evaluate_tactical_turn(npc, state)
        assert decision is not None
        assert "tactical_ai" in decision.traits


# ══════════════════════════════════════════════
# Test Group 8: Integration through NPCSkillEngine
# ══════════════════════════════════════════════

class TestNPCSkillEngineIntegration:
    def test_tactical_decision_returns_compatible_dict(self):
        """NPCSkillEngine.process_npc_combat_turn should return a dict with
        tactical action_type when tactical AI fires."""
        from src.world.npc_skill_engine import NPCSkillEngine

        npc = _make_hostile_npc(
            job="고블린 졸개", hp=5, max_hp=50, courage=10
        )
        state = _make_state(npc_list=[npc])
        result = NPCSkillEngine.process_npc_combat_turn(npc, state, player_ac=12)
        assert result is not None
        assert "action_type" in result
        assert "summary_ko" in result
        assert "npc_id" in result
        # Should be a tactical action, not a standard skill attack
        assert result["action_type"] in {
            "flee", "call_help", "heal_self", "berserker_rage", "cc_stunned",
            "kite_away", "take_cover", "exploit_status", "exploit_status_miss",
            "guard_ally",
        }

    def test_standard_attack_when_no_tactical_trigger(self):
        """Healthy generalist NPC with no special conditions → standard attack path."""
        from src.world.npc_skill_engine import NPCSkillEngine

        npc = _make_hostile_npc(
            job="일반 전사", hp=45, max_hp=50, courage=60, aggression=50,
            strength=14,
        )
        state = _make_state(npc_list=[npc])
        result = NPCSkillEngine.process_npc_combat_turn(npc, state, player_ac=10)
        assert result is not None
        # Standard attack (no tactical override)
        assert result["action_type"] in {
            "skill_attack_hit", "skill_attack_miss",
        }


# ══════════════════════════════════════════════
# Test Group 9: Dead / non-hostile guard
# ══════════════════════════════════════════════

class TestGuardConditions:
    def test_dead_npc_returns_none(self):
        npc = _make_hostile_npc(hp=0)
        npc.alive = False
        state = _make_state(npc_list=[npc])
        assert MonsterTacticsEngine.evaluate_tactical_turn(npc, state) is None

    def test_non_hostile_returns_none(self):
        npc = _make_hostile_npc()
        npc.disposition = "neutral"
        state = _make_state(npc_list=[npc])
        assert MonsterTacticsEngine.evaluate_tactical_turn(npc, state) is None
