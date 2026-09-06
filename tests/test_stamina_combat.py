import pytest
from src.world.state import WorldState, Location, NPC, Item, Skill, Player
from src.world.stamina_engine import StaminaEngine
from src.world.validator import ActionValidator
from src.world.two_pass_engine import TwoPassEngine
from src.world.npc_skill_engine import NPCSkillEngine
from src.world.status_engine import StatusEffectEngine


@pytest.fixture
def test_world():
    state = WorldState()
    state.player.location = "training_ground"
    state.player.health = 100
    state.player.max_health = 100
    state.player.stamina = 100
    state.player.max_stamina = 100
    state.player.constitution = 10
    state.player.agility = 10
    state.player.skills = ["skill_heavy_strike", "skill_whirlwind"]

    loc = Location(
        id="training_ground",
        name="훈련장",
        description="전사들이 단련하는 연병장",
        exits={}
    )
    state.locations["training_ground"] = loc

    # Physical skills with stamina cost
    state.skills_db["skill_heavy_strike"] = Skill(
        id="skill_heavy_strike",
        name="강타",
        category="physical",
        skill_type="active",
        role_type="single_attack",
        tier="common",
        resource_type="stamina",
        resource_cost=25,
        cooldown_turns=1,
        current_cooldown=0,
        base_value=15,
        scaling_stat="str",
        scaling_factor=1.2
    )

    state.skills_db["skill_whirlwind"] = Skill(
        id="skill_whirlwind",
        name="회오리 베기",
        category="physical",
        skill_type="active",
        role_type="aoe_attack",
        tier="rare",
        resource_type="stamina",
        resource_cost=50,
        cooldown_turns=3,
        current_cooldown=0,
        base_value=25,
        scaling_stat="str",
        scaling_factor=1.5
    )

    # Hostile NPC with stamina skill
    target_dummy = NPC(
        id="sparring_partner",
        name="대련 상대",
        description="목검을 든 대련 상대",
        location="training_ground",
        disposition="hostile",
        health=80,
        max_health=80,
        stamina=100,
        max_stamina=100,
        constitution=12,
        agility=12,
        strength=14,
        skills=["skill_heavy_strike"]
    )
    state.npcs["sparring_partner"] = target_dummy

    return state


def test_stamina_capacity_and_stat_scaling(test_world):
    """Test base stamina capacity and CON/AGI stat scaling."""
    player = test_world.player
    # Base 100 with stats = 10
    assert player.max_stamina_effective == 100
    assert StaminaEngine.calculate_max_stamina(player) == 100

    # Increase Constitution and Agility
    player.constitution = 14  # (14 - 10) * 5 = +20
    player.agility = 12       # (12 - 10) * 2 = +4
    assert player.max_stamina_effective == 124

    # Test NPC scaling
    npc = test_world.npcs["sparring_partner"]
    # CON 12 (+10), AGI 12 (+4) -> 114
    assert npc.max_stamina_effective == 114


def test_stamina_consumption_and_tracking(test_world):
    """Test stamina consumption in StaminaEngine and TwoPassEngine integration."""
    player = test_world.player
    player.stamina = 100

    # Direct engine consume
    res = StaminaEngine.consume(player, 30)
    assert res["consumed"] == 30
    assert res["current_stamina"] == 70
    assert player.stamina == 70
    assert not res["triggered_exhaustion"]

    # TwoPassEngine skill execution
    # Player starts at 70: recovers 15 at turn start (70 + 15 = 85), then consumes 25 for skill -> 60
    fact_sheet = TwoPassEngine.compute_pass1(
        action="대련 상대에게 강타 시전",
        state=test_world
    )
    assert fact_sheet.is_valid
    assert player.stamina == 60


def test_stamina_insufficient_rejection(test_world):
    """Test action rejection when entity lacks sufficient stamina."""
    player = test_world.player
    player.stamina = 15

    # Can afford check
    can_cast, reason = StaminaEngine.can_afford(player, 25)
    assert not can_cast
    assert "기력이 부족합니다" in reason

    # Pre-validation check in ActionValidator
    is_valid, msg, _, _ = ActionValidator.pre_validate_action(
        "대련 상대에게 강타 시전",
        test_world
    )
    assert not is_valid
    assert "기력이 부족합니다" in msg


def test_stamina_exhaustion_trigger_and_action_gating(test_world):
    """Test exhaustion status triggered at 0 stamina and gating of heavy actions."""
    player = test_world.player
    player.stamina = 30

    # Consume all remaining stamina
    res = StaminaEngine.consume(player, 30)
    assert res["current_stamina"] == 0
    assert res["triggered_exhaustion"]
    assert StatusEffectEngine.has_status(player, "exhaustion")

    # Exhausted player cannot cast high-cost skills (> 20) even if stamina is partially restored
    player.stamina = 25
    can_cast, reason = StaminaEngine.can_afford(player, 25)
    assert not can_cast
    assert "탈진 상태" in reason


def test_stamina_turn_recovery_and_exhaustion_penalty(test_world):
    """Test natural turn-based recovery and 50% penalty during exhaustion."""
    player = test_world.player
    player.stamina = 50
    player.constitution = 10
    player.agility = 10

    # Normal recovery rate
    normal_regen = StaminaEngine.calculate_regen_rate(player)
    assert normal_regen == StaminaEngine.BASE_REGEN_PER_TURN  # 15

    # Turn recovery
    restored = StaminaEngine.recover_turn(player)
    assert restored == 15
    assert player.stamina == 65

    # Apply exhaustion status
    StatusEffectEngine.apply_status(player, "exhaustion", duration=2)
    penalized_regen = StaminaEngine.calculate_regen_rate(player)
    assert penalized_regen == int(normal_regen * 0.5)  # 7


def test_npc_stamina_integration_and_ai(test_world):
    """Test NPC stamina deduction, availability filtering, and AI conservation."""
    npc = test_world.npcs["sparring_partner"]
    npc.stamina = 100

    # NPC ready skills include heavy strike
    available = NPCSkillEngine.get_available_npc_skills(npc, test_world)
    assert any(s.id == "skill_heavy_strike" for s in available)

    # When NPC lacks stamina, skill is excluded
    npc.stamina = 10
    available_low = NPCSkillEngine.get_available_npc_skills(npc, test_world)
    assert not any(s.id == "skill_heavy_strike" for s in available_low)

    # NPC AI stamina conservation when stamina < 25 and low aggression
    npc.stamina = 20
    npc.personality.aggression = 40
    # Add a cheap 5 stamina skill
    test_world.skills_db["skill_jab"] = Skill(
        id="skill_jab",
        name="잽",
        category="physical",
        skill_type="active",
        role_type="single_attack",
        tier="common",
        resource_type="stamina",
        resource_cost=5,
        base_value=5
    )
    npc.skills.append("skill_jab")
    # Combat turn execution consumes stamina
    outcome = NPCSkillEngine.process_npc_combat_turn(npc, test_world, player_ac=10)
    assert outcome is not None
    assert npc.stamina <= 20


def test_stamina_save_load_backwards_compatibility():
    """Test legacy save deserialization defaults stamina and max_stamina to 100."""
    legacy_save = {
        "player": {
            "name": "구버전 모험가",
            "health": 80,
            "max_health": 100,
            "mana": 40,
            "max_mana": 50
            # stamina & max_stamina are absent!
        },
        "locations": {
            "start": {"id": "start", "name": "시작 지점"}
        },
        "npcs": {
            "old_npc": {
                "id": "old_npc",
                "name": "옛날 상인",
                "health": 50,
                "mana": 30
                # stamina & max_stamina are absent!
            }
        }
    }

    state = WorldState.from_dict(legacy_save)
    assert state.player.stamina == 100
    assert state.player.max_stamina == 100
    assert state.player.max_stamina_effective >= 100

    npc = state.npcs["old_npc"]
    assert npc.stamina == 100
    assert npc.max_stamina == 100
    assert npc.max_stamina_effective >= 100
